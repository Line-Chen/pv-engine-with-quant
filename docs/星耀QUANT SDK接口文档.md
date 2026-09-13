---
title: "星耀QUANT SDK接口说明"
source: "星耀QUANT SDK接口文档.docx"
author: "项目组"
doc_modified: "2026-09-10T00:59:04Z"
converted_at: "2026-09-11"
converter: "docx-to-md-converter/pandoc"
---

# 星耀QUANT SDK接口说明

|            |      |
|------------|------|
| 文档编号： |      |
| 版本：     | V1.0 |
| 项目编号： |      |
| 项目经理： |      |
| 保密级别： |      |

![](<星耀QUANT SDK接口文档.assets/image3.jpeg>)

**招商银行**

China Merchants Bank

版权所有不得复制

## 一、QUANT SDK概要

### ◆接口概要
<table>
<tbody>
<tr>
<td><strong>类/对象 &amp; 方法</strong></td>
<td><strong>输入参数（名称:类型；必填）</strong></td>
<td><strong>返回</strong></td>
<td><strong>用途</strong></td>
</tr>
<tr>
<td>Workflow fromTask</td>
<td>taskJson: String; 是</td>
<td>Workflow</td>
<td>通过任务Json生成Workflow对象</td>
</tr>
<tr>
<td>CmbPREngine initBuildRecipe</td>
<td>json:String; 是</td>
<td>InitResult</td>
<td>全量替换曲线CurveRecipe构建配方切片，真实缓存在实例内</td>
</tr>
<tr>
<td>CmbPREngine initCalendar</td>
<td>json:String; 是</td>
<td>InitResult</td>
<td>全量替换节假日及补班日内存表；真实缓存在引擎实例内，并且同步至底层内存缓存中</td>
</tr>
<tr>
<td>CmbPREngine initConventions</td>
<td>json:String; 是</td>
<td>InitResult</td>
<td>全量替换 Convention 惯例配置定义切片；真实缓存在引擎实例内，并且同步至底层内存缓存中</td>
</tr>
<tr>
<td>CmbPREngine initFixing</td>
<td>json:String; 是</td>
<td>InitResult</td>
<td>全量替换 Fixings 定盘行情信息；真实缓存在引擎实例内，以供实际执行工作流时调用</td>
</tr>
<tr>
<td>CmbPREngine initFutureStartDates</td>
<td>json:String; 是</td>
<td>InitResult</td>
<td>全量替换期货标的起始时间列表；真实缓存在引擎实例内，以供执行工作流时组合起始和终止日期</td>
</tr>
<tr>
<td>CmbPREngine initFinished</td>
<td>无;<br />
是(每个实例在run前必须调用)</td>
<td>void</td>
<td>关闭本实例 Init 阶段；此后允许通过 run 方法执行工作流，继续调用 initXxxx 方法会被拒绝</td>
</tr>
<tr>
<td>CmbPREngine resetInit</td>
<td>无; 否</td>
<td>void</td>
<td>清空引擎内和底层内存缓存数据，并重新打开Init阶段允许initXxx方法再次被调用</td>
</tr>
<tr>
<td>CmbPREngine initStatus</td>
<td>无; 否</td>
<td>List&lt;ConfigStatus&gt;</td>
<td>获取Init相关的状态信息，以及EngineSession会话的状态信息</td>
</tr>
<tr>
<td>CmbPREngine run</td>
<td>workflow:Workflow; 是</td>
<td>WorkflowResult</td>
<td>整个任务调度入口，通过返回的WorkflowResult返回所有结果信息</td>
</tr>
</tbody>
</table>

### ◆曲线结果输出样本
<table>
<tbody>
<tr>
<td><strong>字段</strong></td>
<td><strong>类型</strong></td>
<td><strong>含义</strong></td>
<td colspan="2"><strong>强制性</strong></td>
</tr>
<tr>
<td>REQUEST_ID</td>
<td>String</td>
<td>请求ID,同传入的workflow_id</td>
<td>是</td>
<td></td>
</tr>
<tr>
<td>STATIC_SNAPSHOT_ID</td>
<td>String</td>
<td>同传入的static_snapshot_id</td>
<td>否</td>
<td></td>
</tr>
<tr>
<td>MARKET_SNAPSHOT_ID</td>
<td>String</td>
<td>同传入的market_snapshot_id</td>
<td>否</td>
<td></td>
</tr>
<tr>
<td>M_H_REP_DATE</td>
<td>String</td>
<td>同传入的valuation_date：2026-06-30</td>
<td>是</td>
<td></td>
</tr>
<tr>
<td>M_MDS</td>
<td>String</td>
<td>同传入的workflow_id</td>
<td>否</td>
<td></td>
</tr>
<tr>
<td>M_CURRENCY</td>
<td>String</td>
<td>对应currency：USD</td>
<td>是</td>
<td></td>
</tr>
<tr>
<td>M_CURVE</td>
<td>String</td>
<td>对应curveName：USD SOFR</td>
<td>是</td>
<td></td>
</tr>
<tr>
<td>M_TYPE</td>
<td>String</td>
<td>对应instrumentType：Cash Deposit</td>
<td>是</td>
<td></td>
</tr>
<tr>
<td>M_GENERATOR</td>
<td>String</td>
<td>对应instrumentName：USD-CASH-DEPOSIT</td>
<td>是</td>
<td></td>
</tr>
<tr>
<td>M_PILLAR</td>
<td>String</td>
<td>对应tenor：1D</td>
<td>是</td>
<td></td>
</tr>
<tr>
<td>M_PILLARD</td>
<td>String</td>
<td>节点日期序列号：46203</td>
<td>是</td>
<td></td>
</tr>
<tr>
<td>M_DS_FACTOR</td>
<td>String</td>
<td>贴现因子</td>
<td>是</td>
<td></td>
</tr>
<tr>
<td>M_ZC_RATE</td>
<td>String</td>
<td>零息利率</td>
<td>是</td>
<td></td>
</tr>
<tr>
<td>M_FWD_RATE</td>
<td>String</td>
<td>远期利率</td>
<td>是</td>
<td></td>
</tr>
</tbody>
</table>

{

"workflowId": "usd-sofr-1",

"summary": {

"totalTasks": 1,

"succeeded": 1,

"failed": 0,

"cancelled": 0

},

"tasks": \[

{

"id": "USD SOFR",

"type": "BUILD_MODELS",

"status": "SUCCESS",

"error": null,

"resultTable": {

"headers": \[

"REQUEST_ID",

"STATIC_SNAPSHOT_ID",

"MARKET_SNAPSHOT_ID",

"M_H_REP_DATE",

"M_MDS",

"M_CURRENCY",

"M_CURVE",

"M_TYPE",

"M_GENERATOR",

"M_PILLAR",

"M_PILLARD",

"M_ZC_RATE",

"M_DS_FACTOR",

"M_FWD_RATE"

\],

"data": \[

\[

"usd-sofr-1",

"STATIC-20260630-v1",

"MKT-20260630-v2232",

"2025-12-31",

"usd-sofr-1",

"USD",

"USD SOFR",

"RFR FRA",

"SOFR-1B-FRA",

"1D",

"46026",

"0.0131378177",

"0.9998200461",

"0.0131378177"

\]

\]

}

}

\]

}

### ◆波动率曲面结果输出样本

|  |  |  |  |
|----|----|----|----|
| **字段** | **类型** | **含义** | **强制性** |
| REQUEST_ID | String | 请求ID,同传入的workflow_id | 是 |
| STATIC_SNAPSHOT_ID | String | 同传入的static_snapshot_id | 否 |
| MARKET_SNAPSHOT_ID | String | 同传入的market_snapshot_id | 否 |
| M_PAIR | String | 同传入的pair货币对 | 否 |
| M_TYPE | String | Vol | 是 |
| M_GENERATOR | String | 对应instrumentName(同pair货币对)：USD/CNY | 是 |
| M_MATURITY | String | 对应tenor：1Y | 是 |
| M_STRIKE | String | 对应strike: ATM\|CALL10\|PUT 10等 | 是 |
| M_VOL | String | 隐含波动率 | 是 |

{

  "workflowId": "usd-cny-vol-surface",

  "summary": {

    "totalTasks": 1,

    "succeeded": 1,

    "failed": 0,

    "cancelled": 0,

    "elapsedMillis": 0

  },

  "tasks": \[

    {

      "id": "usd-cny-vol-surface",

      "type": "BUILD_MODELS",

      "status": "SUCCESS",

      "resultTable": {

        "headers": \[

          "REQUEST_ID",

          "STATIC_SNAPSHOT_ID",

          "MARKET_SNAPSHOT_ID",

          "M_PAIR",

          "M_TYPE",

          "M_GENERATOR",

          "M_MATURITY",

          "M_STRIKE",

          "M_VOL"

        \],

        "data": \[

          \[

            "usd-cny-vol-surface",

"STATIC-20260630-v1",

"MKT-20260630-v2232",

            "USD/CNY",

            "Vol",

            "USD/CNY",

            "1Y",

            "ATM",

            "0.072"

          \],

          \[

            "usd-cny-vol-surface",

"STATIC-20260630-v1",

"MKT-20260630-v2232",

            "USD/CNY",

            "Vol",

            "USD/CNY",

            "1Y",

            "CALL 10",

            "0.086"

          \],

          \[

            "usd-cny-vol-surface",

"STATIC-20260630-v1",

"MKT-20260630-v2232",

            "USD/CNY",

            "Vol",

            "USD/CNY",

            "1Y",

            "PUT 10",

            "0.06"

          \]

        \]

      },

      "error": null,

      "elapsedMillis": 0

    }

  \]

}

## 二、核心实体设计
<table>
<tbody>
<tr>
<td>对象</td>
<td>职责</td>
<td>关键字段/方法</td>
</tr>
<tr>
<td>Workflow</td>
<td>工作流 DAG:节点/输入边/快照元信息</td>
<td>fromTask(String)/fromJson(String)、workflowId()、tasks()</td>
</tr>
<tr>
<td>CmbPREngine</td>
<td>引擎门面：<br />
init 生命周期与唯一计算入口 run</td>
<td>initBuildRecipe、initCalendar、initFixing、initFutureStartDates、initConventions、run(Workflow)、sessionState()</td>
</tr>
<tr>
<td>PREngineError</td>
<td>结构化错误(错误码+消息+明细)</td>
<td>code()、wireCode()、message()</td>
</tr>
<tr>
<td>ResultTable</td>
<td>内存结果表({headers, data})</td>
<td>headers()、data()</td>
</tr>
<tr>
<td>TaskResult</td>
<td>单任务结果:状态/错误/结果表/耗时</td>
<td>status()、error()、resultTable()、elapsedMillis()</td>
</tr>
<tr>
<td>WorkflowResult</td>
<td>工作流执行结果</td>
<td>workflowId()、summary()、tasks()</td>
</tr>
</tbody>
</table>

### CmbPREngine 实体设计
引擎会话门面：唯一计算入口 run 与 init 生命周期管理；每实例单线程，同实例并发 run 会被直接拒绝。

CmbPREngine 实体行为设计

|  |  |  |
|----|----|----|
| 返回值类型 | 方法签名 | 描述 |
| InitResult | initBuildRecipe(String json) | 装载曲线、曲面构建配方切片 |
| InitResult | initCalendar(String json) | 装载假日日历数据 |
| InitResult | initConventions(String json) | 装载约定分组并下沉内核约定工厂 |
| InitResult | initFutureStartDates(String json) | 装载期货合约的起始日期列表 |
| InitResult | initFixings(String json) | 装载历史定盘数据信息 |
| void | initFinished() | 封板 init 阶段,会话切到 RUNNING |
| void | resetInit() | 恢复内置默认并重开 init 阶段 |
| List\<InitConfigStatus\> | initStatus() | 各配置项状态快照 |
| EngineSessionStateEnum | sessionState() | 当前会话生命周期状态 |
| WorkflowResult | run(Workflow) | 唯一计算入口:执行工作流 |
| void | close() | 释放引擎,重复调用幂等 |

### EngineSessionStateEnum 实体设计
会话生命周期状态枚举(每实例 EngineSession 的状态机):init 阶段开关与 run 闸门的判定依据。

EngineSessionStateEnum 实体属性设计

|  |  |  |
|----|----|----|
| 属性名 | 字段类型 | 描述 |
| UNINITIALIZED | 枚举常量 | 初始态:允许 Init\*\* 系列,拒绝 run |
| INITIALIZING | 枚举常量 | 初始化中:允许 Init\*\* 系列,拒绝 run(首次 Init\*\* 调用后进入) |
| RUNNING | 枚举常量 | 运行态:拒绝 Init\*\* 系列,允许 run(initFinished 之后) |
| CLOSED | 枚举常量 | 已关闭:拒绝 Init\*\* 系列,拒绝 run(close 之后) |

### InitResult 实体设计
init 装载结果与配置状态快照:切片名/状态/消息/条目数/时间戳。

InitResult 实体行为设计

|                       |                |             |
|-----------------------|----------------|-------------|
| 返回值类型            | 方法签名       | 描述        |
| InitSectionTypeEnum   | getSection()   | 切片名/消息 |
| InitSectionStatusEnum | getStatus()    |             |
| String                | getMessage()   | 结果消息    |
| String                | getTimestamp() | 时间戳      |

### InitConfigStatus 实体设计
单配置项 init 状态快照(不可变值对象)：切片名 / 状态 / 消息 / 条目数 / 时间戳。

InitConfigStatus 实体行为设计

|                       |                   |                |
|-----------------------|-------------------|----------------|
| 返回值类型            | 方法签名          | 描述           |
| InitSectionTypeEnum   | getSection()      | 配置切片名     |
| InitSectionStatusEnum | getStatus()       | 切片状态       |
| String                | getMessage()      | 装载结果消息   |
| String                | getLastReloadAt() | 最近装载时间戳 |
| int                   | getEntryCount()   | 条目数         |

### Workflow 实体设计
工作流 DAG:节点/输入边/快照元信息;JSON 解析入口 fromTask(flat)/fromJson(DAG)。

Workflow 实体属性设计

|            |                   |                      |
|------------|-------------------|----------------------|
| 属性名     | 字段类型          | 描述                 |
| workflowId | String            | 工作流标识           |
| tasks      | List\<TaskInput\> | 任务节点列表         |
| snapshots  | SnapshotRef       | 顶层快照元信息(可空) |

Workflow 实体行为设计

|                 |                       |                     |
|-----------------|-----------------------|---------------------|
| 返回值类型      | 方法签名              | 描述                |
| Workflow        | fromTask(String json) | flat 单任务形态解析 |
| Workflow        | fromJson(String json) | DAG 形态解析        |
| WorkflowBuilder | builder()             | 链式构建器          |

### ErrorCodeEnum 实体设计
结构化错误码枚举：引擎所有异常经 PREngineError(code, message, detail) 携带,wireCode 供线报。

ErrorCodeEnum 实体属性设计

|                               |        |                              |
|-------------------------------|--------|------------------------------|
| 常量/字段名                   | 取值   | 说明                         |
| UNKNOWN                       | 错误码 | 未归类错误                   |
| REFERENCE_DATA_MISSING        | 错误码 | 参考数据缺失                 |
| INIT_INPUT_INVALID            | 错误码 | init 入参非法(解析/校验失败) |
| TASK_TYPE_UNKNOWN             | 错误码 | 未知任务类型                 |
| WORKFLOW_INVALID              | 错误码 | 工作流结构非法               |
| DEPENDENCY_CYCLE              | 错误码 | 曲线依赖成环                 |
| MISSING_MARKET_DATA           | 错误码 | 市场数据缺失                 |
| TABLE_SCHEMA_INVALID          | 错误码 | 结果表结构非法               |
| TABLE_VALUE_INVALID           | 错误码 | 表值非法                     |
| CURVE_CONFIG_NOT_FOUND        | 错误码 | 曲线配置未找到               |
| MISSING_DEPENDENCY            | 错误码 | 依赖曲线未构建               |
| CONVENTION_NOT_FOUND          | 错误码 | 约定未注册                   |
| CALENDAR_NOT_FOUND            | 错误码 | 日历未装载                   |
| EMPTY_QUOTE_SET               | 错误码 | 行情集合为空                 |
| BOOTSTRAP_FAILED              | 错误码 | 曲线引导构建失败             |
| QUALITY_CHECK_FAILED          | 错误码 | 质检门未通过                 |
| CANCELLED_BY_UPSTREAM_FAILURE | 错误码 | 因上游失败级联取消           |

### TaskStatusEnum 实体设计
任务执行状态枚举:节点级执行结果。

TaskStatusEnum 实体属性设计

|             |          |                      |
|-------------|----------|----------------------|
| 常量/字段名 | 取值     | 说明                 |
| SUCCESS     | 枚举常量 | 执行成功             |
| FAILED      | 枚举常量 | 执行失败(结构化错误) |
| CANCELLED   | 枚举常量 | 因上游失败级联取消   |

### PREngineError 实体设计
结构化错误与内存结果表:错误码+消息。

PREngineError 实体行为设计

|               |            |                      |
|---------------|------------|----------------------|
| 返回值类型    | 方法签名   | 描述                 |
| ErrorCodeEnum | code()     | 结构化错误码         |
| String        | wireCode() | 线报错误码           |
| String        | message()  | 错误消息             |
| String        | detail()   | 错误消息明细         |
| String        | toString() | 错误文本(含码与消息) |

### ResultTable 实体设计
内存结果表不做文件 I/O;空表由 EMPTY 单例提供。

ResultTable 实体属性设计

|        |                    |              |
|--------|--------------------|--------------|
| 属性名 | 字段类型           | 描述         |
| EMPTY  | static ResultTable | 共享空表单例 |

ResultTable 实体行为设计

|  |  |  |
|----|----|----|
| 返回值类型 | 方法签名 | 描述 |
| ResultTable | ResultTable(List\<String\>, List\<List\<String\>\>) | 构造:列头与数据行,防御性复制为只读 |
| ResultTable | empty() | 空表工厂 |
| List\<String\> | headers() | 返回列头 |
| List\<List\<String\>\> | data() | 返回数据行 |
| boolean | isEmpty() | 是否为空表 |
| boolean | equals(Object) / hashCode() | 值相等与散列 |
| String | toString() | 文本表示 |

### WorkflowSummary 实体设计
工作流汇总计数(不可变值对象):总任务数与成功/失败/取消计数 + 墙钟耗时。

WorkflowSummary 实体行为设计

|            |                 |                |
|------------|-----------------|----------------|
| 返回值类型 | 方法签名        | 描述           |
| int        | totalTasks()    | 任务总数       |
| int        | succeeded()     | 成功任务数     |
| int        | failed()        | 失败任务数     |
| int        | cancelled()     | 取消任务数     |
| long       | elapsedMillis() | 执行耗时(毫秒) |
| String     | toString()      | 汇总文本表示   |

### TaskResult 实体设计
任务与工作流执行结果:状态/错误/结果表/耗时与汇总计数。

TaskResult 实体行为设计

|                    |                                |                  |
|--------------------|--------------------------------|------------------|
| 返回值类型         | 方法签名                       | 描述             |
| TaskResult         | success(String, String, ...)   | 成功结果工厂     |
| TaskResult         | failed(String, String, ...)    | 失败结果工厂     |
| TaskResult         | cancelled(String, String, ...) | 已取消结果工厂   |
| List\<TaskResult\> | tasks()                        | 有序任务结果列表 |
| WorkflowSummary    | summary()                      | 汇总计数         |
| String             | id()                           | 获取任务ID       |
| String             | type()                         | 获取任务类型     |
| TaskStatusEnum     | status()                       | 获取任务状态     |
| ResultTable        | resultTable()                  | 获取任务结果表格 |
| long               | elapsedMillis()                | 获取任务运行耗时 |

### WorkflowResult 实体设计
工作流执行结果:workflow id + 汇总计数 + 有序任务结果列表;由 WorkflowExecutor.execute 一次性产出。

WorkflowResult 实体行为设计

|                    |              |                  |
|--------------------|--------------|------------------|
| 返回值类型         | 方法签名     | 描述             |
| String             | workflowId() | 工作流标识       |
| WorkflowSummary    | summary()    | 汇总计数         |
| List\<TaskResult\> | tasks()      | 有序任务结果列表 |

## 三、QUANT SDK接口明细

### ◆ 完整工作流示例
外部统一入口为 CmbPREngine.run(workflow)，其中workflow入参为Workflow类型的对象实例，可以通过接口通过传入的JSON进行构建。

CmbPREngine.run 首先检查实例状态、workflow 非空以及本实例是否已调用initFinished()，再检查同一实例是否存在并发调用；创建 WorkflowExecutor 实例并执行validateStructure 校验成功后，再执行execute启动工作流。

WorkflowExecutor主要用于确保工作流中的任务是否有对应的具体任务实现实例，同时完成按任务的依赖实现拓扑排序，然后按拓扑排序结果依次执行所有的任务。

当前TaskTypes定义了BUILD_MODELS、PV、PV_RISK或PV_ARRAY四种任务类型。EngineSession 是CmbPREngine的内部控制类实现实例级生命周期控制：initFinished() 后关闭 Init 阶段，首次 run() 幂等装载，close() 幂等释放；前后有依赖的任务经 TaskContext 访问本次运行的共享资源。

BuildCurvesTask用于曲线构建任务使用，通过调用不同的CurveBuildAdapter间接调用底层库构建曲线，通过判断曲线构建配方的create_method、instrumentType等信息决定调用引擎kernal层具体对应的 CurveBuilderAdaptor 去构建不同类型的曲线，再间接调用底层的工厂类最终构建出CNY FR007、CNY :STD / CNY SHIBOR 3M、USD SOFR、CNY FX ONSHORE、USD FX ONSHORE或USD-CNY-FX_VOL等曲线或者波动率曲面模型。

![](<星耀QUANT SDK接口文档.assets/image4.png>)

具体代码实现层面，静态配置由 Init 系列接口传入，而不是放进每日曲线构建 Workflow。推荐调用顺序依次为先创建一CmbPREngine实例→零到多个initXxx(...)→initFinished()→run(workflow)。同一实例在 initFinished() 后不能继续加载配置；需要重新加载时先调用 resetInit()。

initBuildRecipe 对曲线构建配方切片执行全量替换，String 入参为 null 或空白时，对应切片应完全清空所有缓存数据，配置内容为实例级共享，Init 阶段不允许执行工作流。完整 Java SDK 调用顺序样例：

try (CmbPREngine engine = new CmbPREngine()) {

InitResult buildRecipeResult = engine.initBuildRecipe(buildRecipeJson);

InitResult conventionResult = engine.initConventions(conventionJson);

InitResult fixingResult = engine.initFixing(fixingJson);

InitResult futureStartDateResult = engine.initFutureStartDates(futureStartDateJson);

InitResult calendarResult = engine.initCalendar(calendarJson);

engine.initFinished();

Workflow workflow = Workflow.fromTask(buildTaskJson);

WorkflowResult result = engine.run(workflow);

}

### ◆ CmbPREngine initBuildRecipe
请求 JSON 样例已包含CNY FR007、CNY :STD(CNY SHIBOR 3M)、USD SOFR、CNY FX ONSHRE、USD FX ONSHORE、USD-CNY-FX_VOL五种曲线构建和一种波动率曲面构建配方：

{

"buildRecipes": \[

{

"curveName": "CNY FR007",

"currency": "CNY",

"createMethod": "BOOTSTRAP",

"dayCountConvention": "ACT/365"

},

{

"curveName": "CNY SHIBOR 3M",

"currency": "CNY",

"createMethod": "BOOTSTRAP",

"dayCountConvention": "ACT/365"

},

{

"curveName": "USD SOFR",

"currency": "USD",

"createMethod": "BOOTSTRAP",

"dayCountConvention": "ACT/365"

},

{

"curveName": "CNY FX ONSHORE",

"currency": "CNY",

"createMethod": "BOOTSTRAP",

"dayCountConvention": "ACT/365"

},

{

"curveName": "USD FX ONSHORE",

"currency": "USD",

"baseCurve": "CNY FX ONSHORE",

"baseCurveCurrency": "CNY",

"currencyPair": "USD/CNY",

"createMethod": "IMPLY",

"dayCountConvention": "ACT/365"

},

{

"curveName": "USD-CNY-FX_VOL",

"createMethod": "VOL",

"currencyPair": "USD/CNY"

}

\]

}

### ◆ CmbPREngine initCalendar
请求 JSON（真实生效，全量替换）：

{

"calendars": \[

{

"center": "BEJ",

"holidays": \["2026-01-01", "2026-02-17", "2026-02-18"\],

"busDays": \["2026-02-14"\]

},

{

"center": "NYC",

"holidays": \["2026-01-01", "2026-02-17", "2026-02-18"\],

"busDays": \[\]

}

\]

}

### ◆ CmbPREngine initConventions
请求 JSON , 此处已包含CNY FR007、CNY SHIBOR 3M和USD SOFR所需的惯例数据：

{

"Cash Deposit": \[

{

"conventionName": "CNY-CASH-DEPOSIT",

"center": "BEJ",

"description": "Cash Deposit",

"attributes": {

"SettlementOffset": "1B",

"SettlementHolidays": "BEJ",

"Currency": "CNY",

"Notional": "10000000",

"AccrualBasis": "Act/365",

"PaymentBusinessDayConvention": "MF",

"PaymentHolidays": "BEJ",

"TermOverride": "",

"Type": "Cash Deposit"

}

},

{

"conventionName": "SHIBOR",

"center": "BEJ",

"description": "Cash Deposit",

"attributes": {

"SettlementOffset": "1B",

"SettlementHolidays": "BEJ",

"Currency": "CNY",

"Notional": "10000000",

"AccrualBasis": "Act/360",

"PaymentBusinessDayConvention": "MF",

"PaymentHolidays": "BEJ",

"TermOverride": "",

"Type": "Cash Deposit"

}

},

{

"conventionName": "SHIBOR-ON",

"center": "BEJ",

"description": "Cash Deposit",

"attributes": {

"SettlementOffset": "0B",

"SettlementHolidays": "BEJ",

"Currency": "CNY",

"Notional": "10000000",

"AccrualBasis": "Act/360",

"PaymentBusinessDayConvention": "MF",

"PaymentHolidays": "BEJ",

"TermOverride": "1B",

"Type": "Cash Deposit"

}

}

\],

"Swap": \[

{

"conventionName": "CNY-SWAP-QTR-MONEY",

"center": "BEJ",

"description": "Swap",

"attributes": {

"SettlementOffset": "1B",

"SettlementHolidays": "BEJ",

"Currency": "CNY",

"Notional": "10000000",

"LiborIndex": "CNY-SHIBOR-3M",

"AccrualPeriod": "3M",

"AccrualBasis": "Act/365F",

"PaymentBusinessDayConvention": "MF",

"PaymentHolidays": "BEJ",

"Type": "Swap"

}

}

\],

"FRA": \[

{

"conventionName": "SOFR-1B-FRA",

"center": "NYC",

"description": "FRA",

"attributes": {

"SettlementOffset": "0b",

"SettlementHolidays": "USGS",

"Currency": "USD",

"Notional": "1000000",

"LiborIndex": "SOFR-1B",

"AccrualBasis": "Act/365F",

"PaymentBusinessDayConvention": "MF",

"PaymentHolidays": "NYC",

"Type": "FRA"

}

}

\],

"Overnight Index Future": \[

{

"conventionName": "SOFR-FUTURE-3M",

"center": "NYC",

"description": "Overnight Index Future",

"attributes": {

"RateCutOffDaysOffset": "1B",

"Currency": "USD",

"ContractNotional": "1000000",

"OvernightIndex": "SOFR-1B",

"AverageType": "COMPOUND",

"Tenor": "3M",

"PaymentOffset": "2B",

"PaymentBusinessDayConvention": "MF",

"PaymentHolidays": "TARGET",

"BasisPointValue": "25",

"Type": "Overnight Index Future"

}

}

\],

"Overnight Index Swap": \[

{

"conventionName": "SOFR-OIS",

"center": "NYC",

"description": "Overnight Index Swap",

"attributes": {

"SettlementOffset": "2B",

"SettlementHolidays": "NYC",

"Currency": "USD",

"Notional": "1000000",

"OvernightIndex": "SOFR-1B",

"AverageType": "COMPOUND",

"AccrualPeriod": "1Y",

"AccrualBasis": "Act/360",

"RateCutOffDaysOffset": "1B",

"PaymentOffset": "2B",

"PaymentBusinessDayConvention": "MF",

"PaymentHolidays": "NYC",

"Type": "Overnight Index Swap"

}

}

\],

  "FX Rate": \[

    {

      "conventionName": "USD-CNY",

      "attributes": {

        "Id": "USD-CNY",

        "BaseCurrency": "USD",

        "BaseFixingBusDayConv": "F",

        "BaseFixingHolidays": "NYC",

        "BaseFixingOffset": "0b",

        "QuotedCurrency": "CNY",

        "QuotedFixingBusDayConv": "F",

        "SettlementBusDayConv": "F",

        "SettlementHolidays": "NYC+BEJ",

        "QuotedFixingHolidays": "BEJ",

        "QuotedFixingOffset": "2b",

        "Type": "FX Rate"

      }

    }

  \]

}

### ◆ CmbPREngine initFutureStartDates
请求 JSON（真实生效，全量替换）：

{

"futures": \[

{

"futureName": "SOFR-FUTURE-3M",

"startDates": \["2025-12-17", "2026-03-18", "2026--6-17","2026-09-16","2026-12-16"\]

},

{

"futureName": "EURODOLLAR",

"startDates": \["2025-12-17", "2026-03-18", "2026--6-17","2026-09-16","2026-12-16"\]

}

\]

}

### ◆ CmbPREngine initFixing
请求 JSON（真实生效，全量替换）：

其中static_snapshot_id与后续CmbPREngine中执行工作流时传入的static_snapshot_id是能一一对应的，后续取Fixing数据时根据此ID获取，此外针对Fixing数据可能存在的缺失问题的补充模式新增了一个missingFixMode参数，其取值A、B、C分别对应如下方案序号1、2、3。

![](<星耀QUANT SDK接口文档.assets/image5.jpeg>)

{

"static_snapshot_id": "STATIC-20260630-v1",

"fixings": \[

{

"indexName": "USD-CNY",

"missingFixMode": "A\|B\|C",

"historicalData": \[

{ "date": "2026-01-01", "value": 0.02323 },

{ "date": "2026-02-11", "value": 0.03623 },

{ "date": "2026-03-08", "value": 0.02323 },

{ "date": "2026-04-21", "value": 0.04323 },

{ "date": "2026-05-22", "value": 0.02553 },

{ "date": "2026-06-08", "value": 0.03993 }

\]

},

{

"indexName": "EUR-CNY",

"historicalData": \[

{ "date": "2026-01-01", "value": 0.02323 },

{ "date": "2026-02-11", "value": 0.03623 },

{ "date": "2026-03-08", "value": 0.02323 },

{ "date": "2026-04-21", "value": 0.04323 },

{ "date": "2026-05-22", "value": 0.02553 },

{ "date": "2026-06-08", "value": 0.03993 }

\]

}

\]

}

### ◆ CmbPREngine initFinished
无需传参，调用后关闭Init阶段，允许工作流至此执行。

### ◆ CmbPREngine resetInit
无需传参，调用后重新开启Init阶段，不再允许工作流执行。

### ◆ CmbPREngine initStatus
无需传参，获取各个不同的Init阶段的执行状态和相应的数据导入统计数据。

### ◆ CmbPREngine run
需要传入的参数为Workflow对象，支持通过 Workflow.fromTask(json) 的方式构建，也支持通过WorkflowBuilder工具类手动构建，以下通过 Json 格式展示不同类型的曲线或者曲面构建所需的示例，实际使用时通过以下Json先构建Workflow对象再执行 run 方法。

其中 snapshot 相关的信息是可选项，但如果要将关联的数据信息与结果做强绑定则一定要传入，以下样例中如果未传入 snapshot 相关的信息属于正常情况。

#### CNY FR007曲线
其中输入部分的 instumentType 对应惯例 Convention 中的 Cash Deposit 或 Swap ，instrumentName 对应 Id ，也即对应传入的 Convention 配置中的conventionName字段。

其中输入的 quote 对应 Murex 表格中的 M_MID 字段， 其数值对应 Murex 除以100后传入。以0.022为例代表输入的是2.22%。

{

"schema_version": "1.0",

"task_id": "CNY FR007",

"task_type": "BUILD_MODELS",

"valuation_date": "2025-12-31",

"snapshots": {

"static_snapshot_id": "STATIC-20251331-v1",

"market_snapshot_id": "MKT-20251231-v2232",

},

"market_input": {

"market_data_set": {

"market_quote": \[

{

"curveName": "CNY FR007",

"pair": "",

"instrumentType": "Cash Deposit",

"instrumentName": "CNY-CASH-DEPOSIT",

"tenor": "O/N",

"quote": 0.013139000000000001,

"strike": ""

},

{

"curveName": "CNY FR007",

"pair": "",

"instrumentType": "Cash Deposit",

"instrumentName": "CNY-CASH-DEPOSIT",

"tenor": "1W",

"quote": 0.022000000000000002,

"strike": ""

},

{

"curveName": "CNY FR007",

"pair": "",

"instrumentType": "Cash Deposit",

"instrumentName": "CNY-CASH-DEPOSIT",

"tenor": "2W",

"quote": 0.019,

"strike": ""

},

{

"curveName": "CNY FR007",

"pair": "",

"instrumentType": "Swap",

"instrumentName": "CNY-SWAP-QTR-MONEY",

"tenor": "1M",

"quote": 0.0165125,

"strike": ""

},

{

"curveName": "CNY FR007",

"pair": "",

"instrumentType": "Swap",

"instrumentName": "CNY-SWAP-QTR-MONEY",

"tenor": "3M",

"quote": 0.0157625,

"strike": ""

},

{

"curveName": "CNY FR007",

"pair": "",

"instrumentType": "Swap",

"instrumentName": "CNY-SWAP-QTR-MONEY",

"tenor": "6M",

"quote": 0.01525,

"strike": ""

},

{

"curveName": "CNY FR007",

"pair": "",

"instrumentType": "Swap",

"instrumentName": "CNY-SWAP-QTR-MONEY",

"tenor": "9M",

"quote": 0.015021,

"strike": ""

},

{

"curveName": "CNY FR007",

"pair": "",

"instrumentType": "Swap",

"instrumentName": "CNY-SWAP-QTR-MONEY",

"tenor": "1Y",

"quote": 0.014985,

"strike": ""

},

{

"curveName": "CNY FR007",

"pair": "",

"instrumentType": "Swap",

"instrumentName": "CNY-SWAP-QTR-MONEY",

"tenor": "2Y",

"quote": 0.0151375,

"strike": ""

},

{

"curveName": "CNY FR007",

"pair": "",

"instrumentType": "Swap",

"instrumentName": "CNY-SWAP-QTR-MONEY",

"tenor": "3Y",

"quote": 0.0154195,

"strike": ""

},

{

"curveName": "CNY FR007",

"pair": "",

"instrumentType": "Swap",

"instrumentName": "CNY-SWAP-QTR-MONEY",

"tenor": "4Y",

"quote": 0.0157505,

"strike": ""

},

{

"curveName": "CNY FR007",

"pair": "",

"instrumentType": "Swap",

"instrumentName": "CNY-SWAP-QTR-MONEY",

"tenor": "5Y",

"quote": 0.0161165,

"strike": ""

},

{

"curveName": "CNY FR007",

"pair": "",

"instrumentType": "Swap",

"instrumentName": "CNY-SWAP-QTR-MONEY",

"tenor": "7Y",

"quote": 0.016872,

"strike": ""

},

{

"curveName": "CNY FR007",

"pair": "",

"instrumentType": "Swap",

"instrumentName": "CNY-SWAP-QTR-MONEY",

"tenor": "10Y",

"quote": 0.017932999999999998,

"strike": ""

},

{

"curveName": "CNY FR007",

"pair": "",

"instrumentType": "Swap",

"instrumentName": "CNY-SWAP-QTR-MONEY",

"tenor": "20Y",

"quote": 0.01775,

"strike": ""

},

{

"curveName": "CNY FR007",

"pair": "",

"instrumentType": "Swap",

"instrumentName": "CNY-SWAP-QTR-MONEY",

"tenor": "30Y",

"quote": 0.0172,

"strike": ""

}

\]

}

}

}

#### CNY STD / CNY SHIBOR 3M曲线
其中输入部分的 instumentType 对应惯例 Convention 中的 Cash Deposit 或 Swap ，instrumentName 对应 Id ，也即对应传入的 Convention 配置中的conventionName字段。

其中输入的 quote 对应 Murex 表格中的 M_MID 字段， 其数值对应 Murex 除以100后传入。以0.022为例代表输入的是2.22%。

{

"schema_version": "1.0",

"task_id": "appnew-shibor-3m",

"task_type": "BUILD_MODELS",

"valuation_date": "2025-12-31",

"snapshots": {

"static_snapshot_id": "STATIC-20251231-v1",

"market_snapshot_id": "MKT-20251231-v2232",

},

"market_input": {

"market_data_set": {

"market_quote": \[

{

"curveName": "CNY SHIBOR 3M",

"pair": "",

"instrumentType": "Cash Deposit",

"instrumentName": "SHIBOR",

"tenor": "O/N",

"quote": 0.013269999999999999,

"strike": ""

},

{

"curveName": "CNY SHIBOR 3M",

"pair": "",

"instrumentType": "Cash Deposit",

"instrumentName": "SHIBOR",

"tenor": "1W",

"quote": 0.01956,

"strike": ""

},

{

"curveName": "CNY SHIBOR 3M",

"pair": "",

"instrumentType": "Cash Deposit",

"instrumentName": "SHIBOR",

"tenor": "2W",

"quote": 0.01951,

"strike": ""

},

{

"curveName": "CNY SHIBOR 3M",

"pair": "",

"instrumentType": "Cash Deposit",

"instrumentName": "SHIBOR",

"tenor": "1M",

"quote": 0.015880000000000002,

"strike": ""

},

{

"curveName": "CNY SHIBOR 3M",

"pair": "",

"instrumentType": "Cash Deposit",

"instrumentName": "SHIBOR",

"tenor": "3M",

"quote": 0.016,

"strike": ""

},

{

"curveName": "CNY SHIBOR 3M",

"pair": "",

"instrumentType": "Cash Deposit",

"instrumentName": "SHIBOR",

"tenor": "6M",

"quote": 0.018879999999999997,

"strike": ""

},

{

"curveName": "CNY SHIBOR 3M",

"pair": "",

"instrumentType": "Cash Deposit",

"instrumentName": "SHIBOR",

"tenor": "9M",

"quote": 0.01914,

"strike": ""

},

{

"curveName": "CNY SHIBOR 3M",

"pair": "",

"instrumentType": "Swap",

"instrumentName": "CNY-SWAP-QTR-MONEY",

"tenor": "1Y",

"quote": 0.015774999999999997,

"strike": ""

},

{

"curveName": "CNY SHIBOR 3M",

"pair": "",

"instrumentType": "Swap",

"instrumentName": "CNY-SWAP-QTR-MONEY",

"tenor": "2Y",

"quote": 0.0159425,

"strike": ""

},

{

"curveName": "CNY SHIBOR 3M",

"pair": "",

"instrumentType": "Swap",

"instrumentName": "CNY-SWAP-QTR-MONEY",

"tenor": "3Y",

"quote": 0.016331500000000002,

"strike": ""

},

{

"curveName": "CNY SHIBOR 3M",

"pair": "",

"instrumentType": "Swap",

"instrumentName": "CNY-SWAP-QTR-MONEY",

"tenor": "4Y",

"quote": 0.016683,

"strike": ""

},

{

"curveName": "CNY SHIBOR 3M",

"pair": "",

"instrumentType": "Swap",

"instrumentName": "CNY-SWAP-QTR-MONEY",

"tenor": "5Y",

"quote": 0.017175,

"strike": ""

},

{

"curveName": "CNY SHIBOR 3M",

"pair": "",

"instrumentType": "Swap",

"instrumentName": "CNY-SWAP-QTR-MONEY",

"tenor": "6Y",

"quote": 0.037000000000000005,

"strike": ""

},

{

"curveName": "CNY SHIBOR 3M",

"pair": "",

"instrumentType": "Swap",

"instrumentName": "CNY-SWAP-QTR-MONEY",

"tenor": "7Y",

"quote": 0.017861000000000002,

"strike": ""

},

{

"curveName": "CNY SHIBOR 3M",

"pair": "",

"instrumentType": "Swap",

"instrumentName": "CNY-SWAP-QTR-MONEY",

"tenor": "10Y",

"quote": 0.0186125,

"strike": ""

}

\]

}

}

}

#### USD SOFR曲线（旧）
其中输入部分的 instumentType 对应支持三种输入， 分别是 RFR FRA、RFR Future、RFR Swap，分别对应惯例 Convention 中的 FRA、 Overnight Index Future 和 Overnight Index Swap ，instrumentName 对应 Id ，也即对应传入的 Convention 配置中的conventionName字段。

其中输入的 quote 对应 Murex 表格中的 M_MID 字段， 其数值对应 Murex 除以100后传入。以0.022为例代表输入的是2.22%。

其中对于RFR Future传入的 tenor 是期货的结束日期，内部会查找 init 阶段传入的起始日期。

{\
"schema_version":"1.0",

"task_id": "usd-sofr-1",

"task_type": "BUILD_MODELS",

"valuation_date": "2026-06-30",

"snapshots": {

"static_snapshot_id": "STATIC-20260630-v1",

"market_snapshot_id": "MKT-20260630-v2232",

},

"market_input": {

"market_data_set": {

"market_quote": \[

{

"curveName": "USD SOFR",

"pair": "",

"instrumentType": "RFR FRA",

"instrumentName": "SOFR-1B-FRA",

"tenor": "1D",

"quote": 0.00362,

"strike": ""

},

{

"curveName": "USD SOFR",

"pair": "",

"instrumentType": "RFR Future",

"instrumentName": "SOFR-FUTURE-3M",

"tenor": "2026-06-26",

"quote": 96.3025,

"strike": ""

},

{

"curveName": "USD SOFR",

"pair": "",

"instrumentType": "RFR Swap",

"instrumentName": "SOFR OIS",

"tenor": "2Y",

"quote": 0.0395345,

"strike": ""

}

\]

}

}

}

#### USD SOFR曲线（新）
其中输入部分的 instumentType 对应支持三种输入， 分别是 Cash Deposit和Overnight Index Swap，instrumentName 对应 Id ，也即对应传入的 Convention 配置中的conventionName字段。

其中输入的 quote 对应 Murex 表格中的 M_MID 字段， 其数值对应 Murex 除以100后传入。以0.022为例代表输入的是2.22%。

{

"schema_version": "1.0",

"task_id": "usd-sofr-1",

"task_type": "BUILD_MODELS",

"valuation_date": "2026-06-30",

"snapshots": {

"static_snapshot_id": "STATIC-20260630-v1",

"market_snapshot_id": "MKT-20260630-v2232"

},

"market_input": {

"market_data_set": {

"market_quote": \[

{

"curveName": "USD SOFR",

"instrumentType": "Cash Deposit",

"instrumentName": "USD-CASH-DEPOSIT",

"tenor": "1D",

"quote": 0.00362

},

{

"curveName": "USD SOFR",

"instrumentType": "Cash Deposit",

"instrumentName": "USD-CASH-DEPOSIT",

"tenor": "1W",

"quote": 0.0362

},

{

"curveName": "USD SOFR",

"instrumentType": "Cash Deposit",

"instrumentName": "USD-CASH-DEPOSIT",

"tenor": "1M",

"quote": 0.0368

},

{

"curveName": "USD SOFR",

"instrumentType": "Cash Deposit",

"instrumentName": "USD-CASH-DEPOSIT",

"tenor": "3M",

"quote": 0.0375

},

{

"curveName": "USD SOFR",

"instrumentType": "Overnight Index Swap",

"instrumentName": "USD-SOFR-OIS",

"tenor": "6M",

"quote": 0.0381

},

{

"curveName": "USD SOFR",

"instrumentType": "Overnight Index Swap",

"instrumentName": "USD-SOFR-OIS",

"tenor": "1Y",

"quote": 0.0387

},

{

"curveName": "USD SOFR",

"instrumentType": "Overnight Index Swap",

"instrumentName": "USD-SOFR-OIS",

"tenor": "2Y",

"quote": 0.0395345

},

{

"curveName": "USD SOFR",

"instrumentType": "Overnight Index Swap",

"instrumentName": "USD-SOFR-OIS",

"tenor": "3Y",

"quote": 0.0398

},

{

"curveName": "USD SOFR",

"instrumentType": "Overnight Index Swap",

"instrumentName": "USD-SOFR-OIS",

"tenor": "5Y",

"quote": 0.0402

},

{

"curveName": "USD SOFR",

"instrumentType": "Overnight Index Swap",

"instrumentName": "USD-SOFR-OIS",

"tenor": "7Y",

"quote": 0.0405

},

{

"curveName": "USD SOFR",

"instrumentType": "Overnight Index Swap",

"instrumentName": "USD-SOFR-OIS",

"tenor": "10Y",

"quote": 0.0408

}

\]

}

}

}

#### CNY FX ONSHORE曲线
其中输入部分的 instumentType 对应惯例 Convention 中的 Cash Deposit 或 Swap ，instrumentName 对应 Id ，也即对应传入的 Convention 配置中的conventionName字段。

其中输入的 quote 对应 Murex 表格中的 M_MID 字段， 其数值对应 Murex 除以100后传入。以0.022为例代表输入的是2.22%。

{

"schema_version": "1.0",

"task_id": "cny-fx-onshore",

"task_type": "BUILD_MODELS",

"valuation_date": "2025-12-31",

"snapshots": {

"static_snapshot_id": "STATIC-20251231-v1",

"market_snapshot_id": "MKT-20251231-v2232",

},

"market_input": {

"market_data_set": {

"market_quote": \[

{

"curveName": "CNY FX ONSHORE",

"instrumentType": "Cash Deposit",

"instrumentName": "SHIBOR-ON",

"tenor": "O/N",

"quote": 0.013139

},

{

"curveName": "CNY FX ONSHORE",

"instrumentType": "Cash Deposit",

"instrumentName": "SHIBOR",

"tenor": "1W",

"quote": 0.022

},

{

"curveName": "CNY FX ONSHORE",

"instrumentType": "Cash Deposit",

"instrumentName": "SHIBOR",

"tenor": "1M",

"quote": 0.0165125

},

{

"curveName": "CNY FX ONSHORE",

"instrumentType": "Swap",

"instrumentName": "CNY-SWAP-QTR-MONEY",

"tenor": "3M",

"quote": 0.0157625

},

{

"curveName": "CNY FX ONSHORE",

"instrumentType": "Swap",

"instrumentName": "CNY-SWAP-QTR-MONEY",

"tenor": "6M",

"quote": 0.01525

},

{

"curveName": "CNY FX ONSHORE",

"instrumentType": "Swap",

"instrumentName": "CNY-SWAP-QTR-MONEY",

"tenor": "9M",

"quote": 0.015021

},

{

"curveName": "CNY FX ONSHORE",

"instrumentType": "Swap",

"instrumentName": "CNY-SWAP-QTR-MONEY",

"tenor": "1Y",

"quote": 0.014985

}

\]

}

}

}

#### CNY FX ONSHORE曲线
其中输入部分的 instumentType 对应惯例 Convention 中的 Cash Deposit 或 Swap ，instrumentName 对应 Id ，也即对应传入的 Convention 配置中的conventionName字段。

其中输入的 quote 对应 Murex 表格中的 M_MID 字段， 其数值对应 Murex 除以100后传入。以0.022为例代表输入的是2.22%。

其中，FX Spot类型传入的是货币对的实时报价，原样传入。

其中，Swap Point类型传入的是外汇掉期点，其数值对应 Murex 后也需要除以100后传入，以0.33为例代表输入的是外汇掉期点是33点。

{

"schema_version": "1.0",

"task_id": "usd-fx-onshore",

"task_type": "BUILD_MODELS",

"valuation_date": "2025-12-31",

"snapshots": {

"static_snapshot_id": "STATIC-20251231-v1",

"market_snapshot_id": "MKT-20251231-v2232",

},

"market_input": {

"market_data_set": {

"market_quote": \[

{

"curveName": "CNY FX ONSHORE",

"instrumentType": "Cash Deposit",

"instrumentName": "SHIBOR-ON",

"tenor": "O/N",

"quote": 0.013139

},

{

"curveName": "CNY FX ONSHORE",

"instrumentType": "Cash Deposit",

"instrumentName": "SHIBOR",

"tenor": "1W",

"quote": 0.022

},

{

"curveName": "CNY FX ONSHORE",

"instrumentType": "Cash Deposit",

"instrumentName": "SHIBOR",

"tenor": "1M",

"quote": 0.0165125

},

{

"curveName": "CNY FX ONSHORE",

"instrumentType": "Swap",

"instrumentName": "CNY-SWAP-QTR-MONEY",

"tenor": "3M",

"quote": 0.0157625

},

{

"curveName": "CNY FX ONSHORE",

"instrumentType": "Swap",

"instrumentName": "CNY-SWAP-QTR-MONEY",

"tenor": "6M",

"quote": 0.01525

},

{

"curveName": "CNY FX ONSHORE",

"instrumentType": "Swap",

"instrumentName": "CNY-SWAP-QTR-MONEY",

"tenor": "9M",

"quote": 0.015021

},

{

"curveName": "CNY FX ONSHORE",

"instrumentType": "Swap",

"instrumentName": "CNY-SWAP-QTR-MONEY",

"tenor": "1Y",

"quote": 0.014985

},

{

"curveName": "USD FX ONSHORE",

"pair": "USD/CNY",

"instrumentType": "FX Spot",

"instrumentName": "USD/CNY",

"quote": 6.7935

},

{

"curveName": "USD FX ONSHORE",

"pair": "USD/CNY",

"instrumentType": "Swap point",

"instrumentName": "USD/CNY",

"tenor": "1M",

"quote": -0.0125

},

{

"curveName": "USD FX ONSHORE",

"pair": "USD/CNY",

"instrumentType": "Swap point",

"instrumentName": "USD/CNY",

"tenor": "3M",

"quote": -0.0375

},

{

"curveName": "USD FX ONSHORE",

"pair": "USD/CNY",

"instrumentType": "Swap point",

"instrumentName": "USD/CNY",

"tenor": "6M",

"quote": -0.075

},

{

"curveName": "USD FX ONSHORE",

"pair": "USD/CNY",

"instrumentType": "Swap point",

"instrumentName": "USD/CNY",

"tenor": "1Y",

"quote": -0.15

}

\]

}

}

}

#### USD-CNY-FX_VOL波动率曲面
其中输入部分的 instumentType 对应惯例 Convention 中的 Cash Deposit 或 Swap ，instrumentName 对应 Id ，也即对应传入的 Convention 配置中的conventionName字段。

其中输入的 quote 对应 Murex 表格中的 M_MID 字段， 其数值对应 Murex 除以100后传入。以0.022为例代表输入的是2.22%。

其中，FX Spot类型传入的是货币对的实时报价，原样传入。

其中，Swap Point类型传入的是外汇掉期点，其数值对应 Murex 后也需要除以100后传入，以0.33为例代表输入的是外汇掉期点是33点。

{

"schema_version": "1.0",

"task_id": "usd-cny-vol-surface",

"task_type": "BUILD_MODELS",

"valuation_date": "2025-12-31",

"snapshots": {

"static_snapshot_id": "STATIC-20251231-v1",

"market_snapshot_id": "MKT-20251231-v2232",

},

"market_input": {

"market_data_set": {

"market_quote": \[

{

"curveName": "CNY FX ONSHORE",

"instrumentType": "Cash Deposit",

"instrumentName": "SHIBOR-ON",

"tenor": "O/N",

"quote": 0.013139

},

{

"curveName": "CNY FX ONSHORE",

"instrumentType": "Cash Deposit",

"instrumentName": "SHIBOR",

"tenor": "1W",

"quote": 0.022

},

{

"curveName": "CNY FX ONSHORE",

"instrumentType": "Cash Deposit",

"instrumentName": "SHIBOR",

"tenor": "1M",

"quote": 0.0165125

},

{

"curveName": "CNY FX ONSHORE",

"instrumentType": "Swap",

"instrumentName": "CNY-SWAP-QTR-MONEY",

"tenor": "3M",

"quote": 0.0157625

},

{

"curveName": "CNY FX ONSHORE",

"instrumentType": "Swap",

"instrumentName": "CNY-SWAP-QTR-MONEY",

"tenor": "6M",

"quote": 0.01525

},

{

"curveName": "CNY FX ONSHORE",

"instrumentType": "Swap",

"instrumentName": "CNY-SWAP-QTR-MONEY",

"tenor": "9M",

"quote": 0.015021

},

{

"curveName": "CNY FX ONSHORE",

"instrumentType": "Swap",

"instrumentName": "CNY-SWAP-QTR-MONEY",

"tenor": "1Y",

"quote": 0.014985

},

{

"curveName": "USD FX ONSHORE",

"pair": "USD/CNY",

"instrumentType": "FX Spot",

"instrumentName": "USD/CNY",

"quote": 6.7935

},

{

"curveName": "USD FX ONSHORE",

"pair": "USD/CNY",

"instrumentType": "Swap point",

"instrumentName": "USD/CNY",

"tenor": "1M",

"quote": -0.0125

},

{

"curveName": "USD FX ONSHORE",

"pair": "USD/CNY",

"instrumentType": "Swap point",

"instrumentName": "USD/CNY",

"tenor": "3M",

"quote": -0.0375

},

{

"curveName": "USD FX ONSHORE",

"pair": "USD/CNY",

"instrumentType": "Swap point",

"instrumentName": "USD/CNY",

"tenor": "6M",

"quote": -0.075

},

{

"curveName": "USD FX ONSHORE",

"pair": "USD/CNY",

"instrumentType": "Swap point",

"instrumentName": "USD/CNY",

"tenor": "1Y",

"quote": -0.15

},

{

"pair": "USD/CNY",

"instrumentType": "Vol",

"instrumentName": "USD/CNY",

"tenor": "1W",

"quote": 0.062,

"strike": "ATM"

},

{

"pair": "USD/CNY",

"instrumentType": "Vol",

"instrumentName": "USD/CNY",

"tenor": "1M",

"quote": 0.0635,

"strike": "ATM"

},

{

"pair": "USD/CNY",

"instrumentType": "Vol",

"instrumentName": "USD/CNY",

"tenor": "3M",

"quote": 0.065,

"strike": "ATM"

},

{

"pair": "USD/CNY",

"instrumentType": "Vol",

"instrumentName": "USD/CNY",

"tenor": "6M",

"quote": 0.0675,

"strike": "ATM"

},

{

"pair": "USD/CNY",

"instrumentType": "Vol",

"instrumentName": "USD/CNY",

"tenor": "1Y",

"quote": 0.072,

"strike": "ATM"

},

{

"pair": "USD/CNY",

"instrumentType": "Vol",

"instrumentName": "USD/CNY",

"tenor": "2Y",

"quote": 0.078,

"strike": "ATM"

},

{

"pair": "USD/CNY",

"instrumentType": "Vol",

"instrumentName": "USD/CNY",

"tenor": "1M",

"quote": 0.009,

"strike": "RR 25"

},

{

"pair": "USD/CNY",

"instrumentType": "Vol",

"instrumentName": "USD/CNY",

"tenor": "6M",

"quote": 0.011,

"strike": "RR 25"

},

{

"pair": "USD/CNY",

"instrumentType": "Vol",

"instrumentName": "USD/CNY",

"tenor": "1Y",

"quote": 0.012,

"strike": "RR 25"

},

{

"pair": "USD/CNY",

"instrumentType": "Vol",

"instrumentName": "USD/CNY",

"tenor": "1M",

"quote": 0.0035,

"strike": "BFY 25"

},

{

"pair": "USD/CNY",

"instrumentType": "Vol",

"instrumentName": "USD/CNY",

"tenor": "6M",

"quote": 0.0045,

"strike": "BFY 25"

},

{

"pair": "USD/CNY",

"instrumentType": "Vol",

"instrumentName": "USD/CNY",

"tenor": "1Y",

"quote": 0.005,

"strike": "BFY 25"

}

\]

}

}

}

### ◆ 异常
附表EXCPTION.A 异常类

|  |  |  |
|----|----|----|
| **异常类** | **触发条件** | **说明** |
| WorkflowInvalidException | 工作流 JSON 无法解析或根节点不是对象；workflow_id 为空；任务节点缺少 id 或 type、id 重复；inputs 指向自身或不存在的节点；params 不是 JSON 对象；使用了已废弃的 camelCase 键名（workflowId、dependsOn）。任何一项出现即判定结构非法，计算不会启动。 | 错误码：WORKFLOW_INVALID。工作流/任务 JSON 结构非法：JSON 不可解析、根节点非对象、workflow_id 缺失、任务节点缺 id/type、id 重复、inputs 自引用或指向未知节点、params 非对象、旧 camelCase 键（workflowId/dependsOn）等。执行前结构校验，计算不会开始。 |
| TaskTypeUnknownException | 任务节点声明的 type 未在任务注册表中登记。多见于前端拼写错误或使用了引擎不支持的构建类型。 | 错误码：TASK_TYPE_UNKNOWN。任务节点声明的 type 未在 TaskRegistry 注册。 |
| DependencyCycleException | 任务依赖图存在环，无法进行拓扑排序。曲线构建计划的依赖解析同样适用。 | 错误码：DEPENDENCY_CYCLE。任务依赖图（或曲线构建依赖）存在环，无法拓扑排序。 |
| InitInputInvalidException | 配置重载请求体不合法：JSON 无法解析；bootstrap/convention 映射条目为空或存在重复项；必填字段（curve_name、currency、create_method、ext_curve_name 等）为空；日历数据包含重复日期或节假日与补班日重叠。校验失败时不会应用任何变更。 | 错误码：INIT_INPUT_INVALID。init/配置重载实体不合法：JSON 不可解析、必填字段缺失或重复等。校验失败不应用任何变更。 |
| MissingMarketDataException | BUILD_MODELS 任务未提供 market_data_set 参数，或行情数据集中找不到 quotes 数据。 | 错误码：MISSING_MARKET_DATA。BUILD_MODELS 未提供 market_data_set，或行情数据缺失。 |
| TableSchemaInvalidException | 行情表结构不合法：缺少 headers/data 数组、表头为空或重复、数据行不是数组、列数不足或缺少必需列（M_CURVE、M_GENERATOR、M_MID）。 | 错误码：TABLE_SCHEMA_INVALID。行情表 schema 非法：headers/data 结构错误、必需列缺失、行与表头列数不一致等。 |
| TableValueInvalidException | 行情表或构建配方中的值不合法：曲线或工具名为空、报价无法解析为数值、曲线缺少币种、FX 波动率行缺少 M_PAIR、create_method 不是 BOOTSTRAP。 | 错误码：TABLE_VALUE_INVALID。行情表或构建配方中的值非法：缺少 currency、数值无效等。 |
| CurveConfigNotFoundException | 按曲线名与工具类型在内置配方目录中找不到构建配置。 | 错误码：CURVE_CONFIG_NOT_FOUND。内置配方目录中找不到对应曲线的构建配置。 |
| MissingDependencyException | 曲线依赖的上游曲线未在同日构建计划中出现，或执行时尚未构建。 | 错误码：MISSING_DEPENDENCY。构建曲线所需的上游曲线/依赖缺失。 |
| ConventionNotFoundException | 内置配方目录中找不到曲线与工具的约定映射。 | 错误码：CONVENTION_NOT_FOUND。找不到曲线/工具的约定映射（convention 配置）。 |
| CalendarNotFoundException | 日历或假日数据缺失；或内核在构建过程中抛出日历/假日类错误（消息含 calendar、holiday、business day 时归入此类）。 | 错误码：CALENDAR_NOT_FOUND。日历/假日数据缺失，或内核抛出的日历类错误（消息含 calendar/holiday/business day）。 |
| EmptyQuoteSetException | 行情数据集中没有任何有效报价行。 | 错误码：EMPTY_QUOTE_SET。行情快照中没有有效报价，无法构建曲线。 |
| BootstrapFailedException | 内核曲线 bootstrap 失败且不属于日历类错误时的兜底归类。 | 错误码：BOOTSTRAP_FAILED。内核曲线 bootstrap 失败（非日历类错误，由内核异常消息归类的兜底）。 |
| QualityCheckFailedException | 构建完成后质量检查未通过：曲线为空、无锚点、工具数超过锚点数、折现因子或零利率超出合理区间。 | 错误码：QUALITY_CHECK_FAILED。曲线构建后的质量检查（QualityGate）未通过。 |

附表EXCPTION.B 异常基类

|  |  |  |
|----|----|----|
| **异常基类** | **触发条件** | **说明** |
| PREngineException | 引擎所有结构化异常的基类，一般不直接抛出，实际抛出的是各错误码专用子类。执行期错误不经过异常，随结果返回。 | 引擎异常基类（未检查异常），携带 PREngineError(code/message/detail)。只有“执行前结构非法”和“初始化失败”走异常抛出，执行期错误不进异常链路。 |
| TaskValidationException | 执行前工作流结构校验异常的基类。API 层捕获后映射为 ZA21 的 OPI4001。 | 执行前工作流结构校验异常的基类（WORKFLOW_INVALID/TASK_TYPE_UNKNOWN/DEPENDENCY_CYCLE 的父类）；appnew API 层 catch 后映射为 ZA21 OPI4001。 |
| InitValidationException | init 配置校验异常的基类。API 层映射为 ZA21 的 OPI4001。 | init 输入校验异常的基类（INIT_INPUT_INVALID 的父类）；appnew API 层映射为 ZA21 OPI4001。 |
| BuildCurveException | 曲线构建执行期异常的基类。被工作流执行器捕获后写入任务结果，不会向外抛出。 | 曲线构建执行期异常的基类；被 WorkflowExecutor 捕获进 TaskResult（FAILED + 错误码），不会逃逸出 execute。 |

附表EXCPTION.C 无结构化错误码的JDK异常

|  |  |  |
|----|----|----|
| **异常类** | **触发条件** | **说明** |
| IllegalStateException | 引擎生命周期使用不当：init 封板后再次初始化、未封板就执行、同一实例并发执行、实例已销毁后继续使用、同一工作流 ID 重复计时等。 | 引擎生命周期违规：init 已封板后再次 init、init 未封板就 run、并发 run、引擎已 dispose、StepTimer 冲突等。不携带结构化错误码。 |
| IllegalArgumentException | 入参校验失败：workflow 为 null、任务类型为空、配方目录为 null、不支持的 create_method 等。 | 参数校验失败：null workflow、空 task type、null catalog 等。不携带结构化错误码。 |
| NoSuchElementException | 任务类型未注册，无法从注册表取出对应工厂。 | 任务 type 未注册。不携带结构化错误码。 |
| AssertionError | 枚举分支覆盖断言触发，属于不可达的防御代码，出现即代表编程错误。 | 枚举全分支覆盖的不可达断言，出现即编程错误。不携带结构化错误码。 |

## 四、惯例Convention数据样本

### 附表Cash Deposit（现金存款类）惯例配置数据
[Conventions\Cash Deposit.xlsx](Conventions/Cash%20Deposit.xlsx)

### 附表Swap（互换类）惯例配置数据
[Conventions\Swap.xlsx](Conventions/Swap.xlsx)

### 附表Overnight Index（隔夜指数类）惯例配置数据
[Conventions\Overnight Index.xlsx](Conventions/Overnight%20Index.xlsx)

### 附表Overnight Index Future（隔夜指数期货类）惯例配置数据
[Conventions\Overnight Index Future.xlsx](Conventions/Overnight%20Index%20Future.xlsx)

### 附表Overnight Index Swap（隔夜指数互换类）惯例配置数据
[Conventions\Overnight Index Swap.xlsx](Conventions/Overnight%20Index%20Swap.xlsx)

### 附表FRA（远期利率协议类）惯例配置数据
[Conventions\FRA.xlsx](Conventions/FRA.xlsx)

### 附表FX Rate（外汇汇率类）惯例配置数据
[Conventions\FX Rate.xlsx](Conventions/FX Rate.xlsx)
