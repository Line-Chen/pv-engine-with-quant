# pv-engine 集成 Quant SDK Demo

基于接口文档《星耀QUANT SDK接口说明》和本地 jar（`pv-quant-sdk-api/impl 1.1.0-SNAPSHOT`），用 Spring Boot 2.7 + Java 8 把 `CmbPREngine` 做成可测试的 HTTP 服务。

## 文档与 jar 的真实差异

当前 jar **没有**文档中的这些方法/任务类型，HTTP 层也不会假装它们存在：

| 文档 | 1.1.0-SNAPSHOT jar |
| --- | --- |
| `initFixing` / `initFutureStartDates` | 无对应 public 方法 |
| `PV` / `PV_RISK` / `PV_ARRAY` | `TaskTypes` 仅有 `BUILD_MODELS` |

已对接：`initBuildRecipe`、`initCalendar`、`initConventions`、`initFinished`、`resetInit`、`initStatus`、`sessionState`、`Workflow.fromTask` / `fromJson`、`run`。

推荐调用顺序与文档一致：

`new CmbPREngine()` → 0..n 次 `initXxx` → `initFinished()` → `run(workflow)`

`initFinished()` 之后不能再 init；要重装配置先 `resetInit()`。同一引擎实例禁止并发 `run`，本服务用互斥锁串行化。

## 启动

```powershell
cd c:\codes\gitea\pv-engine-with-quant
mvn test
mvn spring-boot:run
```

服务默认 `http://localhost:8080`。内核 `CMB_HOME`/`CMB_DATA` 指向 `runtime/cmb-home`。

## 最快验证

```powershell
curl http://localhost:8080/api/quant/capabilities
curl -X POST http://localhost:8080/api/quant/run/oneshot/sample/cny-fr007
```

分步调用（与文档生命周期一致）：

```powershell
curl -X POST http://localhost:8080/api/quant/init/build-recipe -H "Content-Type: application/json" --data-binary "@src/main/resources/samples/init-build-recipe.json"
curl -X POST http://localhost:8080/api/quant/init/calendar -H "Content-Type: application/json" --data-binary "@src/main/resources/samples/init-calendar.json"
curl -X POST http://localhost:8080/api/quant/init/conventions -H "Content-Type: application/json" --data-binary "@src/main/resources/samples/init-conventions.json"
curl -X POST http://localhost:8080/api/quant/init/finished
curl -X POST http://localhost:8080/api/quant/run/task -H "Content-Type: application/json" --data-binary "@src/main/resources/samples/task-cny-fr007.json"
```

IDEA 可直接打开 `http/quant-sdk.http`。

## HTTP 接口

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/quant/health` | 健康检查，返回会话状态 |
| GET | `/api/quant/capabilities` | 当前 jar 能力与文档差异 |
| GET | `/api/quant/session` | `UNINITIALIZED` / `INITIALIZING` / `RUNNING` / `CLOSED` |
| GET | `/api/quant/init/status` | 各 init 切片状态 |
| POST | `/api/quant/init/build-recipe` | 全量替换曲线配方，空 body 表示清空 |
| POST | `/api/quant/init/calendar` | 全量替换日历 |
| POST | `/api/quant/init/conventions` | 全量替换惯例 |
| POST | `/api/quant/init/finished` | 封板 init，允许 run |
| POST | `/api/quant/init/reset` | 清空并重开 init |
| POST | `/api/quant/workflow/parse?mode=TASK\|WORKFLOW` | 只解析，不计算 |
| POST | `/api/quant/run/task` | `Workflow.fromTask` + `run` |
| POST | `/api/quant/run/workflow` | `Workflow.fromJson` + `run` |
| POST | `/api/quant/run/oneshot` | 一次请求完成 init + run |
| GET | `/api/quant/samples` | 内置样例名 |
| GET | `/api/quant/samples/{name}` | 取样例 JSON |
| POST | `/api/quant/run/oneshot/sample/cny-fr007` | 用内置 CNY FR007 样例跑通 |

统一响应：

```json
{ "success": true, "code": "OK", "message": "success", "data": {} }
```

生命周期冲突返回 409（`ILLEGAL_STATE` / `ENGINE_BUSY`），入参或 SDK 结构异常返回 400。

样例 JSON 来自接口文档 CNY FR007 一节。曲线计算是否 SUCCESS 取决于内核与行情完整性；HTTP 链路本身以能调用 SDK 并返回 `WorkflowResult` 为准。
