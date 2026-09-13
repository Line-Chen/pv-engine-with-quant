# MNG-01 冒烟测试报告

| 文档属性 | 内容 |
|----------|------|
| 文档名称 | MNG-01 Job 接入与契约处理 — 冒烟测试报告 |
| 版本 | 6.0 |
| 日期 | 2026-08-18 |
| 系统 / 模块 | 市场风险估值引擎 · Manage Node（pv-engine-manage） |
| 测试性质 | 联调冒烟（**不计入** Jacoco 单元覆盖率） |
| 关联详设 | `docs/MNG-01_Job接入与契约处理_DESIGN.md` |
| 关联单元 | `docs/MNG-01_unit_test_plan.md` / `docs/MNG-01_unit_test_report.md` |
| 单元门禁基线 | 2026-08-18：`mvn test` → **332** green；MNG-01 LINE **100%**（807/807） |
| 本期增补 | MNG-03：受理成功不再按星期几发终态；已建批终态由收口 CAS + Outbox 产生 |

---

## 1. 目的与范围

在真实或准生产依赖下，验证 Manage Node 下列关键路径：

1. 能订阅并消费 `pv.job.contract`（消费组 `manage-pv-job-contract`）；
2. 合法契约可建批写入 `pv_batch`（控制面 `ControlPlaneMybatisRepository` / MyBatis-Plus），**`status=CREATED`**；
3. 合法受理后 **不** 立即发出 `pv.job.result` 终态；`pv_batch` 保持 `CREATED`/`RUNNING`，等 MNG-03 收口；
4. 非法契约拒绝且可观测（日志 + 可发 `pv.job.result` / `REJECTED`，reasonCode 对齐 `MRM0609_*`）；
5. 同一 `jobId` 重复投递不产生重复 batch（job 级幂等）；
6. 同触发幂等键、不同 `jobId` 第二次触发被拒绝（DES-02）；
7. 通过配置分别启用 Spring Kafka 与 ZA21 Kafka，业务结果一致。

**不在本冒烟范围**：计算节点领取闭环、任务包落库、DATA_READY 链路、HA 选主、快照 RDB 就绪深度校验、已冻结的 `/health` 端点。

### 1.1 受理成功后的终态期望（MNG-03）

合法受理成功后 **不得** 因 `businessDate` 星期几发出 `SUCCEEDED/FAILED/TIMEOUT/CANCELLED`。
应观察到：`pv_batch.status` 仍为 `CREATED`（或随后 `RUNNING`），且无对应终态 Outbox。
拒绝（未建批）仍写 `dedup_key=R:{jobId}` 的 Outbox，由发布器发送 `REJECTED`。

---

## 2. 测试环境

| 项 | 值（联调回填） |
|----|---------------|
| JDK | 1.8 |
| 配置 profile | Spring：默认 `application.yml`；Z21：行内按 `pom.xml.z21` / 私服构建 |
| Kafka provider | `pv.manage.kafka.provider=spring` 或 `z21` |
| 构建 | Spring：`mvn package`；Z21：行内私服包构建（外网默认 pom 已不含 z21 profile） |
| Kafka / RiskDL MQ | 地址、topic 是否已建；SASL 密码环境变量 |
| RDB / TiDB schema | `pv_engine.pv_batch`（含 `updated_at`；MyBatis-Plus 注解 Mapper） |
| 实例数 | 冒烟建议 1（便于对账） |

---

## 3. 前置检查

| # | 检查项 | 结果 | 证据 |
|---|--------|------|------|
| 1 | 应用启动成功 | ☐ | 日志 |
| 2 | Spring 路径：监听容器 id=`pvJobContractListener` 已启动；方法签名为 `ConsumerRecord` | ☐ | |
| 3 | Z21 路径：同上 + 北斗追踪注解生效（若有链路平台） | ☐ | |
| 4 | 消费组配置为 `manage-pv-job-contract` | ☐ | |
| 5 | 可向 `pv.job.contract` 投递 JSON | ☐ | |
| 6 | 可查询 `pv_batch` / 可观察 `pv.job.result` | ☐ | |
| 7 | MyBatis Mapper 扫描仅限控制面包（无装配冲突） | ☐ | 启动日志 |
| 8 | 单元门禁已通过（`mvn test`） | ☑ | 见 `docs/MNG-01_unit_test_report.md`（332 / LINE 100%） |

---

## 4. 用例矩阵

| 用例 ID | 特性 | 正/异 | 说明 |
|---------|------|-------|------|
| SM-F001-01 | F-001 | 正 | 消费并受理建批；周一日期出站 `SUCCEEDED` |
| SM-F001-02 | F-001 | 边 | （可选）周二日期出站 `CANCELLED` |
| SM-F003-01 | F-003 | 正 | `pv_batch.priority` 符合归一化 |
| SM-F003-02 | F-003 | 异 | 异常优先级归一化 |
| SM-F004-01 | F-004 | 正/异 | 合法受理、非法拒绝 |
| SM-F005-01 | F-005 | 正 | 快照字段齐备受理 |
| SM-F005-02 | F-005 | 异 | 缺必填快照字段拒绝 |
| SM-F006-01 | F-006 | 正 | 重复 jobId 不新建 batch |
| SM-F006-02 | F-006 | 正 | 新 jobId + 不同快照可新建 |
| SM-F006-03 | F-006 | 异 | 新 jobId + 同快照触发拒绝 |
| SM-F004-02 | F-004 | 异 | blank / null 边界（可选） |
| SM-KAFKA-01 | Kafka | 正 | Spring provider 出站 `pv.job.result`（`ConsumerRecord` 入站） |
| SM-KAFKA-02 | Kafka | 正 | Z21 provider 出站语义与 Spring 一致 |
| SM-KAFKA-03 | Kafka | 异 | Broker 不可达时发送失败可观测（不静默） |
| SM-CP-01 | F-CP | 正 | MyBatis upsert 真实库语义与 H2 单测一致 |

**推荐执行顺序**

```text
SM-KAFKA-01（spring）→ SM-F001-01 → SM-CP-01 → SM-F004-01 → SM-F005-01 / SM-F005-02
→ SM-F003-01 / SM-F003-02 → SM-F006-01 / SM-F006-02 / SM-F006-03
→ SM-KAFKA-02（z21，行内）→ SM-KAFKA-03（可选）→ SM-F001-02 / SM-F004-02（可选）
```

---

## 5. 冒烟用例

### 5.1 SM-F001-01 合法 PV 作业受理

| 项 | 内容 |
|----|------|
| 前置 | 启动后 `pvJobContractListener` 容器运行；`provider=spring` 或 `z21` |
| 步骤 | 投递完整 `PvJobContractMessage`（jobType=`PV`，**业务日用周一 `2026-07-20`**，五类快照非空）；见附录 A 合法样例 |
| 期望日志 | `作业契约受理完成 jobId=... batchId=...` |
| 期望 DB | `pv_batch` 新增 1 行：`job_id` 匹配；快照字段落库；`idempotency_key` 非空；**`status=CREATED`**；`total_packs=0`；`triggeredBy` 与 `submittedBy` 一致（样例为 FRTB）；`updated_at` 可写 |
| 期望 MQ | 受理成功后发出 `pv.job.result`：**status=`SUCCEEDED`**（因周一）；**packs 0/0/0/0**；拒绝路径发 `REJECTED` |
| 不期望 | `pv_task_pack` 有行；静默丢弃终态事件；`status=RUNNING`（建批已改为 CREATED） |
| 结果 | ☐ PASS ☐ FAIL |
| 证据 | |
| 说明 | 与 `PvJobIngressAppService` 中 `TODO[MNG-01]` 星期几模拟一致；后续改为异步监听引擎结果后再改期望 |

### 5.1.1 SM-F001-02 周二 CANCELLED（可选）

| 项 | 内容 |
|----|------|
| 步骤 | 将合法样例 `businessDate` 改为 `2026-07-21`，更换 `jobId` 后投递 |
| 期望 MQ | **仅一条**终态：`CANCELLED`，packs 0/0/0/0。不应出现 `FAILED`（`case 2` 已 `break`） |
| 期望 DB | 仍 `status=CREATED`（出站模拟不回写批次终态） |
| 结果 | ☐ PASS ☐ FAIL |
| 证据 | |
| 说明 | 与单元 `ApplicationServicesTest` 星期二断言一致 |

### 5.2 SM-F005-02 缺必填快照拒绝

| 项 | 内容 |
|----|------|
| 步骤 | 去掉 `marketSnapshotId` 再投递（见附录 A 非法样例） |
| 期望日志 | `作业契约已拒绝` |
| 期望 DB | 无新 `pv_batch`（同 jobId 查询计数不变） |
| 期望 MQ | `pv.job.result` status=`REJECTED`，reasonCode 非空（对齐 `MRM0609_*`），batchId 缺省 |
| 结果 | ☐ PASS ☐ FAIL |
| 证据 | |

### 5.3 SM-F004-01 契约解析正反例

| 子场景 | 步骤 | 期望 |
|--------|------|------|
| 正例 | 投递附录 A 合法消息（周一） | 受理完成 + 有 `pv_batch`（CREATED）+ 可观察 `SUCCEEDED` |
| 反例-非法日期 | `businessDate=2026/07/22` 或 `2026-99-99` | 拒绝；不建批；REJECTED 事件 |
| 反例-不支持类型 | `jobType=SENSITIVITY`（当前路由仅 PV） | 拒绝；reason 含不支持类型 |
| 结果 | ☐ PASS ☐ FAIL | |
| 证据 | | |

### 5.4 SM-F005-01 快照字段齐备受理

| 项 | 内容 |
|----|------|
| 步骤 | 投递含 td / md / derived / sd / cd 的合法消息（vtd 可空；业务日周一） |
| 期望 | 受理成功；可建批 CREATED；可观察 `SUCCEEDED` |
| 结果 | ☐ PASS ☐ FAIL |
| 证据 | |

### 5.5 SM-F003-01 / SM-F003-02 优先级

| 用例 | 步骤 | 期望 | 结果 |
|------|------|------|------|
| SM-F003-01 | 投递 `priority=100` 合法 PV | `pv_batch.priority = 100` | ☐ PASS ☐ FAIL |
| SM-F003-02 | 分别投递 `priority=-5`、`priority=999`；可选再投 `priority=150` | 落库约为 `0`、`100`；`150` → `100`；进程不崩溃 | ☐ PASS ☐ FAIL |
| 证据 | | | |

### 5.6 SM-F006-01 Job 级幂等

| 项 | 内容 |
|----|------|
| 步骤 | 与 SM-F001-01 同一 `jobId` 再投递 2～3 次 |
| 期望 DB | 仍仅一行 `pv_batch`（`COUNT(*) WHERE job_id=?` = 1） |
| 期望日志 | 命中 job 幂等 / 受理完成；batchId 与首次相同 |
| 结果 | ☐ PASS ☐ FAIL |
| 证据 | |

### 5.7 SM-F006-02 不同上下文新建

| 项 | 内容 |
|----|------|
| 步骤 | 新 `jobId` + 更换 `marketSnapshotId` |
| 期望 | 生成新 batch（不去重误伤） |
| 结果 | ☐ PASS ☐ FAIL |
| 证据 | |

### 5.8 SM-F006-03 触发上下文幂等拒绝（DES-02）

| 项 | 内容 |
|----|------|
| 步骤 | 不同 `jobId`、相同业务日 + 相同快照集合 |
| 期望 | 第二次拒绝；不新建同幂等键活跃批次 |
| 记录实际行为 | |
| 结果 | ☐ PASS ☐ FAIL |
| 证据 | |

### 5.9 SM-F004-02 blank / null 边界（可选）

| 项 | 内容 |
|----|------|
| 步骤 | 分别投递 blank `jobType`、blank `businessDate`、blank `cdSnapshotId` |
| 期望 | 均拒绝；不建批；发出 REJECTED |
| 结果 | ☐ PASS ☐ FAIL |
| 证据 | |
| 说明 | **不要投递 Kafka value=null 的 tombstone 作为“业务 null 命令”**：`accept(null)` 当前会 NPE。tombstone/`"null"` 由 Handler 跳过，不进入 `accept` |

### 5.10 SM-KAFKA-01 Spring Kafka 路径

| 项 | 内容 |
|----|------|
| 前置 | `application.yml`；`pv.manage.kafka.provider=spring`；默认 `mvn package` |
| 步骤 | 触发一次拒绝路径（缺快照），观察 `pv.job.result`；另触发一次合法受理（周一日期），观察 `SUCCEEDED` |
| 期望 | 消息到达；value 为纯 JSON；status 分别为 `REJECTED` / `SUCCEEDED`；packs 为 0；应用日志无 Bean 装配冲突；Listener 以 `ConsumerRecord` 消费无反序列化异常 |
| 结果 | ☐ PASS ☐ FAIL |
| 证据 | |

### 5.11 SM-KAFKA-02 ZA21 Kafka 路径（行内）

| 项 | 内容 |
|----|------|
| 前置 | 行内按 `pom.xml.z21` 构建；`--spring.profiles.active=z21`；`provider=z21`；真实 `BeeKafkaTemplate` 坐标已替换 |
| 步骤 | 与 SM-KAFKA-01 / SM-F001-01 相同业务输入 |
| 期望 | 建批 / 拒绝 / 出站 topic 与 Spring 路径业务结果一致；监听器 id 仍为 `pvJobContractListener` |
| 结果 | ☐ PASS ☐ FAIL |
| 证据 | |
| 说明 | **外网单元测试无法覆盖本用例**（ZA21 私服依赖）；须行内联调回填。注意：Z21 Listener 若仍为 `String` 入参，与 Spring `ConsumerRecord` 不同，但均应委托 `PvJobContractHandler` |

### 5.12 SM-KAFKA-03 Broker 异常可观测（可选）

| 项 | 内容 |
|----|------|
| 步骤 | 临时错误 bootstrap / 错误密码后触发拒绝出站或受理终态出站 |
| 期望 | 应用侧出现发送失败日志或 IllegalState 包装语义，不静默丢弃业务结果 |
| 结果 | ☐ PASS ☐ FAIL |
| 证据 | |
| 说明 | 单测已用 Mock Future 覆盖超时/中断/失败；本项验证真实 Broker/SASL |

### 5.13 SM-CP-01 控制面 MyBatis 真实库语义

| 项 | 内容 |
|----|------|
| 前置 | 真实 MySQL/TiDB；`pv_batch` 表结构与详设一致（含 `updated_at`） |
| 步骤 | 完成 SM-F001-01 后查库；再对同 `batch_id` 触发一次幂等复用路径 |
| 期望 | upsert / 查询结果与单元 H2 语义一致；无方言报错；时区字段按 **Asia/Shanghai** 解释；`status=CREATED`；必填文本空值落库语义与 `PvBatchConverter` 单测一致 |
| 结果 | ☐ PASS ☐ FAIL |
| 证据 | |
| 说明 | **单元用 H2 近似 MySQL，无法完全替代真实库方言与连接池行为**。不要对不存在的 `batch_id` 调用 `findJobIdByBatchId`：当前实现在 Mapper 返回 null 时会 NPE |

---

## 6. 结果汇总

| 用例 | 结果 | 备注 |
|------|------|------|
| SM-F001-01 合法受理 | | 待联调回填；周一 → `SUCCEEDED`；库 `CREATED`；packs 0 |
| SM-F001-02 周二 CANCELLED | | 可选；仅 `CANCELLED` |
| SM-F005-02 缺快照 | | |
| SM-F004-01 解析正反 | | 含非法日期、不支持类型 |
| SM-F005-01 快照齐备 | | |
| SM-F003-01 priority=100 | | |
| SM-F003-02 异常优先级 | | |
| SM-F006-01 Job 幂等 | | |
| SM-F006-02 不同上下文 | | |
| SM-F006-03 触发幂等 | | |
| SM-F004-02 blank 边界 | | 可选；勿投 tombstone 当业务 null 命令 |
| SM-KAFKA-01 Spring provider | | `ConsumerRecord` 入站 |
| SM-KAFKA-02 Z21 provider | | 行内；单测不可替代 |
| SM-KAFKA-03 Broker 异常 | | 可选 |
| SM-CP-01 MyBatis 真实库 | | |

**通过判据**

| 检查项 | 通过 |
|--------|------|
| 合法 PV contract 产生 `pv_batch`（**CREATED**） | ☐ |
| 合法受理（周一日期）可观察 `pv.job.result` / `SUCCEEDED`，packs 全 0 | ☐ |
| 非法 contract 拒绝且无计算 | ☐ |
| 缺快照字段拒绝并可观测 | ☐ |
| priority 归一化落库符合期望 | ☐ |
| 同 jobId 不重复建批 | ☐ |
| 触发幂等拒绝（DES-02） | ☐ |
| Spring provider 出站正常 | ☐ |
| Z21 provider 与 Spring 业务一致（行内） | ☐ |
| MyBatis 真实库 upsert/查询正常 | ☐ |

**总体结论**：☐ PASS（关键路径通过） ☐ FAIL（阻塞联调）

> 说明：本报告为联调执行与回填清单。单元侧已用 Mock / H2 覆盖同等业务场景（见单元测试报告）；冒烟须在真实 Kafka + RDB（及行内 ZA21）上勾选并附证据。单测环境**未连接**真实中间件，上表结果栏保持待回填。

---

## 7. 单元无法覆盖、须冒烟验证的外部依赖说明

| 依赖 | 单元为何覆盖不了 | 冒烟关注点 |
|------|------------------|------------|
| Kafka Broker / 分区 / 位点 | 无真实集群；AckMode.BATCH 由容器托管 | 消费推进、拒绝后是否阻塞分区 |
| SASL / 密码网关 | 凭据与网关仅在环境存在 | 鉴权失败日志、启动失败是否清晰 |
| ZA21 `BeeKafkaTemplate` / `@BeesKafkaTracing` | 行内私服包外网不可解析 | SM-KAFKA-02；链路 businessId |
| MySQL / TiDB | 单测用 H2 方言近似 | SM-CP-01：真实 upsert / 时区 / 连接池 / `updated_at` |
| 北斗链路平台 | 非本仓依赖 | Z21 追踪是否上报 |
| Broker 宕机 / 网络分区 | Mock Future 仅模拟超时与异常回调，无法覆盖真实网络抖动与重平衡 | SM-KAFKA-03 |
| `ConsumerRecord` 容器反序列化 | 单测手工构造 Record，无法覆盖容器 converter / 空 payload 投递细节 | SM-KAFKA-01 |
| Converter 上海时区 vs 会话时区 | H2 不携带生产会话 `time_zone` | SM-CP-01 核对 `created_at`/`updated_at` 墙钟含义 |
| `findJobIdByBatchId` 未命中 NPE | 单测已锁定；真实库查询不存在 batch 会同样 NPE | 联调勿对 miss 的 batch 调该查询，或先修复实现 |

---

## 8. 签署

| 角色 | 姓名 | 日期 | 结论 |
|------|------|------|------|
| 冒烟执行 | | 2026-08-18 | 待联调 |
| 开发确认 | | | |
| 联调对方（FRTB / CCR） | | | |

---

## 附录 A. `PvJobContractMessage` 样例

**合法样例（周一，用于观察 SUCCEEDED）**

```json
{
  "jobId": "JOB-PV-F011-001",
  "jobType": "PV",
  "businessDate": "2026-06-26",
  "priority": 100,
  "submittedBy": "FRTB",
  "tradeSnapshotId": "TD_EOD_202606261813",
  "virtualTradeSnapshotId": null,
  "marketSnapshotId": "MD_EOD_202606261813",
  "derivedMarketDataVersion": "DMV_EOD_202606261813",
  "staticSnapshotId": "SD_EOD_202606261813",
  "cdSnapshotId": "CD_EOD_202606261813",
  "scenarioDatasetId": null,
  "targetNodeId": null,
  "submittedAt": "2026-07-20T02:00:00"
}
```

**非法样例（缺 `marketSnapshotId`）**

```json
{
  "jobId": "JOB-SM-F005-NEG",
  "jobType": "PV",
  "businessDate": "2026-07-20",
  "priority": 100,
  "submittedBy": "FRTB",
  "tradeSnapshotId": "TD_EOD_202606261813",
  "derivedMarketDataVersion": "dmv-20260720-001",
  "staticSnapshotId": "sd-20260720-001",
  "cdSnapshotId": "cd-20260720-001"
}
```
