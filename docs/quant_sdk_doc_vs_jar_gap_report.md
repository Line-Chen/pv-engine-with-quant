# 星耀 QUANT SDK 接口文档与 jar 对齐差异报告

| 项 | 内容 |
| --- | --- |
| 文档 | `docs/星耀QUANT SDK接口文档.md`（由 `星耀QUANT SDK接口文档.docx` 转换，文档版本 V1.0） |
| 对照制品 | `pv-quant-sdk-api-1.1.0-SNAPSHOT.jar`、`pv-quant-sdk-impl-1.1.0-SNAPSHOT.jar` |
| 制品坐标 | `LV68.06:pv-quant-sdk-api/impl:1.1.0-SNAPSHOT` |
| 核查日期 | 2026-09-13 |
| 核查手段 | `javap` 反汇编 public/private API、jar 目录、本机 `CmbPREngine` 实测（含文档 ①–⑦ 与自造行情） |

**总判断**：文档描述的是目标契约（含 Fixing / 期货起始日 / PV / IMPLY / VOL / FRA / FX）。当前 `1.1.0-SNAPSHOT` 只落地了 **BOOTSTRAP + Cash Deposit/Swap + BUILD_MODELS**。不是集成漏接，是 **文档超前、实现未完成**，另有多处文档内部命名不一致。

---

## 1. 差异总览

| 严重程度 | 数量 | 含义 |
| --- | --- | --- |
| P0 文档有、jar 无（调用即编译失败或 init 失败） | 8 | 门面方法、任务类型、createMethod、惯例类型 |
| P1 枚举/状态已预留、装载器未实现 | 2 | FIXING、FUTURES_START_DATE |
| P2 文档内部自相矛盾或样例不可用 | 8 | 方法名、标题、JSON、惯例缺失 |
| P3 架构口径与制品形态不符 | 4 | QuantSdk 接口、Native、api/impl 分层 |
| 已对齐（供对照） | — | 见第 7 节 |

---

## 2. P0：文档有、当前 jar 没有或拒绝

### 2.1 `CmbPREngine` 门面方法少两个

文档接口概要与实体表均要求：

- `initFixing` / `initFixings(String json)`
- `initFutureStartDates(String json)`

并给出完整调用顺序：

```text
engine.initBuildRecipe(...)
engine.initConventions(...)
engine.initFixing(...)
engine.initFutureStartDates(...)
engine.initCalendar(...)
engine.initFinished()
engine.run(Workflow.fromTask(...))
```

**jar 证据**（`javap -public CmbPREngine`）：

```text
public InitResult initBuildRecipe(String);
public InitResult initCalendar(String);
public InitResult initConventions(String);
public void initFinished();
public void resetInit();
public List<InitConfigStatus> initStatus();
public EngineSessionStateEnum sessionState();
public WorkflowResult run(Workflow);
public void close();
```

没有 `initFixing` / `initFixings` / `initFutureStartDates`。  
`CmbInitializer` 同样只有 `reloadBuildRecipe` / `reloadCalendar` / `reloadConventions` 三套 storage，没有 Fixing / Futures 仓库。

### 2.2 任务类型只有 `BUILD_MODELS`

文档（完整工作流示例）：

> 当前 TaskTypes 定义了 BUILD_MODELS、PV、PV_RISK 或 PV_ARRAY 四种任务类型。

**jar 证据**（`TaskTypes`）：仅常量 `BUILD_MODELS`。  
`TaskFactory.createDefault()` 字节码只 `register("BUILD_MODELS", ...)`。  
api 包内唯一 `ITask` 实现是 `BuildCurvesTask`，没有 PV / Sensitivity / PV Array 任务类。

### 2.3 `createMethod` 只支持 `BOOTSTRAP`

文档 `initBuildRecipe` 样例包含：

| 曲线 | 文档 createMethod |
| --- | --- |
| CNY FR007 / SHIBOR 3M / USD SOFR / CNY FX ONSHORE | `BOOTSTRAP` |
| USD FX ONSHORE | `IMPLY` |
| USD-CNY-FX_VOL | `VOL` |

**jar 证据**（`CreateMethodEnum`）：只有 `BOOTSTRAP`。  
`parse()` 常量字符串为：`CMB supports BOOTSTRAP only.`

**实测**：把文档 6 条配方一次性 init，立刻 `INIT_INPUT_INVALID`：

```text
buildRecipe 'USD-CNY-FX_VOL' currency must be non-blank
```

VOL 配方在文档里本身也不带 `currency`；即便补上 `currency=USD`，`VOL`/`IMPLY` 仍不是合法枚举。必须拆成只含 `BOOTSTRAP` 的配方才能继续。

### 2.4 文档惯例类型与 impl 受理类型不一致

文档 `initConventions` 与 run 样例使用的分组名：

`Cash Deposit`、`Swap`、`FRA`、`Overnight Index Future`、`Overnight Index Swap`、`FX Rate`

impl `CmbConventionInitializer.normalizeType` 实际识别的名字（字节码 ldc）：

`Swap` / `SwapConvention`、`CashDeposit` / `CashDepositConvention`、`OvernightIndex`、`RFR Future`、`RFR OIS`、`RfrIndex`

**不在受理列表中**：`FRA`、`FX Rate`、`Overnight Index Future`、`Vol`。

**实测**：

| 输入惯例分组 | HTTP/SDK 结果 |
| --- | --- |
| `Cash Deposit` + `Swap` | 成功（①②⑤） |
| `FRA` | `IllegalArgumentException: Unsupported convention type: FRA`（③） |
| `FX Rate` | `Unsupported convention type: FX Rate`（⑥⑦） |
| `Overnight Index Swap` | init 能过（被 API 层单独收集），run 时 `IR curve doesn't support this product: Overnight Index Swap`（④） |

补充：`CmbInitializer.KernelSyncBridge.syncKernelConventions` 把 `Overnight Index` / `Overnight Index Swap` / `Libor Future` 收进局部 List 后 **没有再注册到内核**（只把 `Libor Index` 注册了）。所以文档的 OIS / Future 惯例即使 init 不报错，也不会进入定价工厂。

### 2.5 内核产品面比文档窄

impl 有 `CMBIrCashDeposit`、`CMBIrVanillaSwap`，以及枚举 `CMBBaseProduct`（含 `RFR_FUTURE`、`RFR_OIS`、`FX_RATE` 等），但 **IR 曲线工厂在加载非 Swap 产品时抛**：

```text
IR curve doesn't support this product:
```

**实测 ④**：文档 USD SOFR（新）Cash + OIS → `BOOTSTRAP_FAILED`。  
去掉 OIS、只用自造 USD Cash（1D 5.33% … 3M 5.15%）→ **SUCCESS**，1D ZC=0.0540242822。  
说明 USD SOFR 曲线能建，OIS/Future 产品未接到 `CMBIrCurveFactory`。

impl 没有 FRA / OIS / Future / FX Vol 的独立产品类（`baseproduct` 仅 Cash + Vanilla Swap）。  
`CMBFxRateConvention` 类存在，但 API 层 `initConventions("FX Rate")` 进不了该工厂。

### 2.6 文档 ①–⑦ 跑通情况（2026-09-13）

| # | 文档标题 | 文档样例 | 自造行情 | 结论 |
| --- | --- | --- | --- | --- |
| ① | CNY FR007 | SUCCESS，16 行 | SUCCESS，ZC 随报价上移 | 真算，已对齐 |
| ② | CNY SHIBOR 3M | SUCCESS，15 行 | SUCCESS，ZC 不同 | 真算，已对齐 |
| ③ | USD SOFR（旧） | init 失败 FRA | 同左 | 惯例/期货起始日未实现 |
| ④ | USD SOFR（新） | run 失败 OIS | 同左；Cash-only 可成功 | OIS 未实现 |
| ⑤ | CNY FX ONSHORE | SUCCESS，7 行 | SUCCESS | 真算（按 IR bootstrap） |
| ⑥ | 标题误作 CNY FX，实为 USD FX | init 失败 FX Rate + IMPLY | 同左 | 未实现 |
| ⑦ | USD-CNY-FX_VOL | init 失败 FX Rate + VOL | 同左 | 未实现 |

自造行情反证「写死」：同一估值日 `2025-12-31`，FR007 O/N 报价 1.3139% → ZC 1.313829%；改成 1.60% → ZC 1.599895%。结果跟着输入变。

原始记录：`scripts/curve_case_results.json`，复现脚本：`scripts/run_curve_cases.py`。

---

## 3. P1：状态位已预留，装载 API 未做

`InitSectionTypeEnum` 含：`CALENDAR`、`CONVENTION`、`BUILD_RECIPE`、`FIXING`、`FUTURES_START_DATE`、`ENGINE_SESSION`。

`InitStatusRecorder.resetAll()` 对 FIXING / FUTURES 的提示语是：

```text
call initFixings to load fixing history
call initFuturesStartDates to load mappings
```

与文档方法名 `initFixing` / `initFutureStartDates` 又不一致。

**实测** `GET /api/quant/init/status`（① 成功后）：

| section | status | 含义 |
| --- | --- | --- |
| BUILD_RECIPE / CALENDAR / CONVENTION | LOADED | 有装载器 |
| FIXING | EMPTY | 无装载方法 |
| FUTURES_START_DATE | EMPTY | 无装载方法 |
| ENGINE_SESSION | LOADED / RUNNING | 会话状态 |

impl 内嵌 `tools/IndexFixing_csv/*.csv`（README 写明 2025-07-01～2025-12-31 dummy，不得用于生产）。这些 CSV **没有**接到 `CmbPREngine` 的 init 通路。

---

## 4. P2：文档内部不一致（即使用下一版 jar 也会误导）

| # | 问题 | 证据 |
| --- | --- | --- |
| 1 | 定盘方法三名 | 概要 `initFixing`；实体表 `initFixings`；status 文案 `initFixings` |
| 2 | 期货起始日两名 | 概要 `initFutureStartDates`；status 文案 `initFuturesStartDates` |
| 3 | 返回类型名 | 概要 `List<ConfigStatus>`；实体 `InitConfigStatus`（jar 是后者） |
| 4 | 异常基类名 | 文档 `PREngineException`；jar `AbstractPREngineException` |
| 5 | ⑥ 标题错误 | 标题「CNY FX ONSHORE」，`task_id` 为 `usd-fx-onshore`，行情含 USD FX Spot / Swap point |
| 6 | ④ 惯例不在 init 样例中 | 任务用 `USD-CASH-DEPOSIT`、`USD-SOFR-OIS`；`initConventions` 样例只有 `CNY-*` / `SOFR-OIS` / `SOFR-1B-FRA` |
| 7 | ③ 惯例名对不上 | 任务 `instrumentName=SOFR OIS`，惯例 `conventionName=SOFR-OIS` |
| 8 | 样例数值异常 | ② SHIBOR 6Y=`0.037`（5Y=1.72%、7Y=1.79%，6Y 像把 1.70% 写成 3.70%）；④ 1D=`0.00362`、1W=`0.0362`，数量级不连续 |
| 9 | VOL 配方缺 currency | 文档 VOL 条无 `currency`；jar `BuildRecipeInitEntity` 要求非空 |
| 10 | 转换后的 JSON 非法 | md 中大量 `\[` `\]`、对象尾逗号（如 snapshots 后），不能直接 `fromTask`；docx 原文需再核对 |
| 11 | 配方个数笔误 | 写「五种曲线和一种波动率」却列出 6 条配方（5 条曲线 + 1 条 vol） |
| 12 | InitResult 描述含条目数 | 实体行为表只有 `getSection/getStatus/getMessage/getTimestamp`；`getEntryCount` 在 `InitConfigStatus` 上。jar 与实体表一致 |

---

## 5. P3：架构口径与制品形态

对照总设 `docs/pv_engine_design_with_quantsdk.md` §3.2.2：

| 总设/接口文档口径 | 当前 jar |
| --- | --- |
| `pv-quant-sdk-api` 定义 `QuantSdk` 接口 | **无** `QuantSdk` 类型；门面是 `com.cmb.pvengine.CmbPREngine` |
| `pv-quant-sdk-impl` 提供生产实现 | impl 实际是 `com.cmb.cmbjava.*` 内核（曲线工厂、惯例、日历） |
| `QuantNativeBridge` + `libquantnative.so` | **两个 jar 均无** JNI / `.so` / `.dll`；数学在 `CMBMathAPI`（纯 Java） |
| api 与 impl 稳定契约解耦 | api 的 Maven POM **依赖** impl；api jar 已打进引擎实现类（`CmbPREngine`、`WorkflowExecutor`），不是薄接口包 |
| api POM `mainClass` | 写成 `com.cmb.CmbPREngine`，真实类名是 `com.cmb.pvengine.CmbPREngine` |

这不影响「能不能算 FR007」，但说明版本说明、依赖方式和文档模块图还不能当集成规范用。

---

## 6. 文档样例字段 vs 引擎实际受理（run JSON）

已对齐且实测可用（①②⑤）：

- `task_id` / `task_type=BUILD_MODELS` / `valuation_date`
- `snapshots.static_snapshot_id` / `market_snapshot_id`（可选，会回写结果表）
- `market_input.market_data_set.market_quote[]`：`curveName`、`instrumentType`、`instrumentName`、`tenor`、`quote`

文档写了、当前构建路径用不上或会失败：

| 文档字段/类型 | 当前行为 |
| --- | --- |
| `instrumentType=RFR FRA / RFR Future / RFR Swap` | ③ 在惯例阶段即失败 |
| `instrumentType=Overnight Index Swap` | ④ 构建失败 |
| `instrumentType=FX Spot / Swap point / Vol` | ⑥⑦ 惯例或配方阶段失败 |
| Future 的 `tenor=到期日` + init 起始日 | 无 `initFutureStartDates`，无法拼合约区间 |
| `missingFixMode` A/B/C | 无 `initFixing` |
| 结果表 `M_VOL` / `M_PAIR` / `M_STRIKE` | VOL 跑不通，未实测产出 |

---

## 7. 已经对齐的部分（避免误判为「全错」）

下列与文档一致，且本机可调用：

1. `Workflow.fromTask` / `fromJson` / `builder`
2. `initBuildRecipe` / `initCalendar` / `initConventions` / `initFinished` / `resetInit` / `initStatus` / `sessionState` / `run` / `close`
3. 生命周期：`UNINITIALIZED` → `INITIALIZING` → `RUNNING` → `CLOSED`；未 `initFinished` 不能 `run`；同实例并发 `run` 拒绝
4. `EngineSessionStateEnum`、`TaskStatusEnum`、`ErrorCodeEnum` 常量集合与文档表一致
5. 结果对象：`WorkflowResult` / `WorkflowSummary` / `TaskResult` / `ResultTable` / `PREngineError` 访问器与文档一致
6. 结构化异常子类：`WorkflowInvalidException`、`InitInputInvalidException`、`BootstrapFailedException` 等均在 api jar；执行期曲线错误进 `TaskResult` 而不向外抛（与文档「BuildCurveException 不逃逸」一致）
7. CNY FR007、CNY SHIBOR 3M、CNY FX ONSHORE（按 IR Cash+Swap bootstrap）可算出节点 ZC / DF / FWD，且随行情变化

---

## 8. 建议（给 SDK 与文档两边）

**SDK 下一版若要追上文档：**

1. 补 `initFixing` / `initFutureStartDates`，或从文档和 `InitSectionTypeEnum` 删掉这两项。
2. `CreateMethodEnum` 增加 `IMPLY`、`VOL`，或改文档配方。
3. 惯例分组名统一：要么文档改成 `RFR Future` / `RFR OIS`，要么 `CmbConventionInitializer` 接受文档名；并真正注册 OIS/Future/FX，不要只收集不注册。
4. `CMBIrCurveFactory` 接上 OIS / Future / FX imply / Vol，或文档 ③④⑥⑦ 标明「未发布」。
5. 注册 `PV` / `PV_RISK` / `PV_ARRAY`，或文档改为「当前仅 BUILD_MODELS」。

**文档应立即修订（不改 jar 也能减少误用）：**

1. 标明 **V1.0 契约 vs 1.1.0-SNAPSHOT 已实现范围**。
2. 统一 `initFixing` 命名；⑥ 标题改为 USD FX ONSHORE。
3. 修正 SHIBOR 6Y、SOFR 短端报价；补 USD-CASH-DEPOSIT 惯例；VOL 配方补 `currency`。
4. 推荐调用顺序改为「零到多个 **已实现** 的 initXxx」，不要把未实现方法写进唯一示例。

**集成侧（本仓库 Demo）当前最小可运行顺序：**

```java
try (CmbPREngine engine = new CmbPREngine()) {
    engine.initBuildRecipe(bootstrapRecipeJson);   // 仅 BOOTSTRAP
    engine.initConventions(cashAndSwapJson);       // 仅 Cash Deposit + Swap
    engine.initCalendar(calendarJson);
    engine.initFinished();
    WorkflowResult result = engine.run(Workflow.fromTask(buildTaskJson));
}
```

适用于 CNY FR007 / CNY SHIBOR 3M / CNY FX ONSHORE（IR 贴现），以及 **仅 Cash Deposit 的 USD SOFR**。不要按文档一次性灌入 IMPLY/VOL/FRA/FX Rate。

---

## 9. 证据索引

| 证据 | 位置 |
| --- | --- |
| 门面方法列表 | `javap -public ... CmbPREngine` |
| 无 Fixing/Futures storage | `javap -public ... CmbInitializer` |
| 仅 BUILD_MODELS | `TaskTypes`、`TaskFactory.createDefault` 字节码 |
| 仅 BOOTSTRAP | `CreateMethodEnum.parse` 字符串 `CMB supports BOOTSTRAP only.` |
| 惯例受理名 | `CmbConventionInitializer.normalizeType` ldc |
| OIS/Future 惯例被收集后丢弃 | `CmbInitializer$KernelSyncBridge.syncKernelConventions` |
| IR 不支持 OIS | `CMBIrCurveFactory` 字符串 `IR curve doesn't support this product:` |
| 无 Native | 两 jar 无 `.so`/`.dll`/JNI 类 |
| ①–⑦ 实测 | `scripts/curve_case_results.json` |
| 复现脚本 | `scripts/run_curve_cases.py` |

---

## 10. 修订记录

| 日期 | 说明 |
| --- | --- |
| 2026-09-13 | 首版。对照接口文档 V1.0 与 `1.1.0-SNAPSHOT` 两只 jar，并纳入当日 7 案例实测。 |
