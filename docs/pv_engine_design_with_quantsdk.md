# LV68.06 (PV Engine) 总体设计说明书（含 Quant SDK）

<!-- markdownlint-disable MD013 MD024 -->

## 目录

- 1. 简介
  - 1.1. 项目背景
  - 1.2. 统一术语
- 2. 总体设计思路概述
  - 2.1. 技术栈选型
  - 2.2. 应用架构总体设计思路
  - 2.3. 系统架构总体设计思路
    - 2.3.1. 分布式并行计算架构
    - 2.3.2. 典型PV作业工作流
    - 2.3.3. 节点软隔离与定向调度
- 3. 应用架构总体设计
  - 3.1. 模块划分
  - 3.2. 微服务划分
    - 3.2.1. PV 微服务代码结构
    - 3.2.2. Quant SDK 设计架构
    - 3.2.3. 实时计算 API 微服务（二期能力）
    - 3.2.4. 日终计量批处理流程
  - 3.3. 开放能力设计
- 4. 系统架构总体设计
  - 4.1. 微服务部署和发布策略设计
    - 4.1.1. 子系统与服务单元定级
    - 4.1.2. 彩排验证方案
    - 4.1.3. 本地配置文件与 Secrets 管理
  - 4.2. 数据库部署策略
    - 4.2.1. LV68.18 (RiskDL) RDB（TiDB）
    - 4.2.2. 两阶段数据交换演进
  - 4.3. 云服务选型及架构设计
    - 4.3.1. LV68.18 (RiskDL) MQ（ACS Kafka）
  - 4.4. 外部系统依赖
- 5. 非功能需求分析
  - 5.1. 性能分析
    - 5.1.1. 吞吐保障口径（总设层面）
  - 5.2. 安全分析
- 6. 修订记录

---

# 1. 简介

## 1.1. 项目背景

LV68 市场风险计量体系中，LV68.06 (PV Engine) 负责全资产类别估值与重估值计算，是 FRTB Engine 与 CCR Engine 的估值底座。

PV Engine 的核心职责包括：

1. 风险因子治理与曲线/曲面构建；
2. PV 计算；
3. Sensitivity 计算；
4. PV Array 情景重估（输出情景估值数组，供 FRTB Engine 派生 PL Vector）；
5. 本系统配置管理（模型参数与映射版本治理）。

系统通过 LV68.18 (RiskDL) 提供统一输入快照、结果落库与事件能力；金融计算能力由 Quant SDK 统一提供。PV Engine 采用“管理+计算+Web”微服务架构：`LV68.06@pv-manage-node`、`LV68.06@pv-compute-node`、`LV68.06@pv-web-be`、`LV68.06@pv-web-ui`，其中计算节点运行在物理机计算节点集群；二期规划新增实时计算微服务 `LV68.06@pv-rt-service`（详见 3.2.3）。

涉及系统编号如下：

| 系统编号 | 子系统名称 | 英文简称 | 角色 |
| --- | --- | --- | --- |
| LV68.06 | 市场风险估值计量子系统 | PV Engine | 本文设计对象，负责估值、敏感度、PV Array（情景估值数组）和风险因子计算支撑。 |
| LV68.16 | 市场风险资本计量子系统 | FRTB Engine | 消费 Sensitivity、PV Array 等估值产出，并自行派生 PL Vector。 |
| LV68.17 | 交易对手信用风险内模法计量子系统 | CCR Engine | 通过适配器调用 PV/重估值能力。 |
| LV68.18 | 市场风险计量数据管理子系统 | RiskDL | 为 PV Engine 提供统一快照、结果存储与事件总线。 |

## 1.2. 统一术语

| 术语 | 英文 | 缩写 | 统一口径 |
| --- | --- | --- | --- |
| 定价与估值 | Pricing and Valuation | PV | 金融产品估值计算能力。 |
| 情景估值数组 | PV Array | PV_ARRAY | 各情景重定价后的 PV 序列，PV Engine 输出的估值原料；不含"损益"语义。 |
| 损益向量 | Profit and Loss Vector | PL Vector | 由 FRTB Engine 基于 PV Array 相减派生的损益序列，不在 PV Engine 产出。 |
| PV作业契约 | PV Job Contract | PV_JOB_CONTRACT | FRTB/CCR 通过 LV68.18 (RiskDL) MQ 向 PV 投递计算作业（Job）的统一消息契约；契约含优先级字段，EOD 批处理任务取最高优先级。 |
| PV作业类型 | PV Job Type | JOB_TYPE | `PV_JOB` 的计算类型标识，典型值包括 `PV`、`SENSITIVITY`、`PV_ARRAY`等。 |
| PV作业 | PV Job | PV_JOB | 一次业务计算作业，上层输入为锁定快照与场景；一个 `PV_JOB` 可拆分为多个 `PV_TASK_BUNDLE`。 |
| PV任务包 | PV Task Bundle | PV_TASK_BUNDLE | 管理节点将单个 `PV_JOB` 按目标包时长与复杂度拆分后的调度单元；一个 `PV_TASK_BUNDLE` 由计算节点内 Master 进一步拆分为多个 `PV_TASK`。 |
| PV计算任务 | PV Compute Task | PV_TASK | 计算节点内 Worker 执行的最小计算单元，由 Master 下发并汇总结果。 |
| 量化计算组件 | Quant SDK | QUANT_SDK | PV Engine 进程内 Java 计算库，提供稳定 API 契约、Java Financial Core 主体实现及受控 Native 辅助调用；不作为独立微服务部署。 |
| 管理节点 | Manage Node | LV68.06@pv-manage-node | 承载任务编排、校验、控制与配置治理能力。 |
| 计算节点 | Compute Node | LV68.06@pv-compute-node | 承载曲线构建、PV/Sensitivity/PV Array 重计算，内部采用 Master-Worker 并行架构。 |
| Web 后端微服务 | Web Backend Service | LV68.06@pv-web-be | 承载 Web 后端 API、鉴权与查询聚合。 |
| Web 前端微服务 | Web UI Service | LV68.06@pv-web-ui | 承载 Web 前端静态资源与交互层。 |
| 计算节点进程内缓存 | In-Process Cache | IN_PROCESS_CACHE | 计算节点本地内存缓存，用于复用预构建曲线/曲面及常用中间结果。 |
| 节点注册表 | Node Registry | NODE_REGISTRY | 登记各计算节点管理态（可否接活）与健康态的权威表，作为领取门禁、软隔离与定向调度的判定依据。 |
| 风险数据层 | Risk Data Layer | RiskDL | 市场风险统一数据层，提供快照、结果存储与事件总线能力。 |
| 数据快照契约 | Snapshot Contract | SNAPSHOT_CONTRACT | 跨系统计算任务必须绑定并校验的统一快照上下文，本质目的是保证任务幂等、结果可审计可回放；包含 `td_snapshot_id`、`vtd_snapshot_id`、`md_snapshot_id`、`derived_market_data_version`、`sd_snapshot_id`、`cd_snapshot_id` 及情景字段（`scenario_dataset_id`）。 |
| RDB 接入组件 | Relational Database Access Component | RDB_ACCESS | 由各子系统在本地 Utility 模块维护，以受控直连方式访问 TiDB，统一执行快照校验、幂等控制与审计留痕；并承载 PV Engine Web 后端分布式会话（Session）状态。 |
| MQ 接入组件 | Message Queue Access Component | MQ_ACCESS | 由各子系统在本地 Utility 模块维护，以受控直连方式访问 ACS Kafka，用于作业投递、状态回传、发布订阅与重试治理。 |

---

# 2. 总体设计思路概述

## 2.1. 技术栈选型

LV68.06 (PV Engine) 定位为“高性能分布式估值引擎”，围绕大规模批量计算与快照一致性展开设计。

| 类别 | 选型 | 版本/口径 | 说明 |
| --- | --- | --- | --- |
| 后端框架 | Java + Z21 框架 | JDK 8（暂定）、Z21 6.0.7+ | 任务编排、数据 I/O、节点控制。 |
| 前端框架 | React | 18.x（按行内技术栈清单准入） | 风险因子配置、任务监控、结果查询。 |
| 计算核心 | Quant SDK（Java Financial Core）+ 受控 JNI + `libquantnative.so` | 行内准入 JDK；gcc 仅用于构建唯一 C++ 制品 `libquantnative.so`；当前不使用 Python、CUDA 或 GPU | Java 承担 Curve Construction、Risk Factor、Pricing、Sensitivity 与 PV Array 主体计算；C++ 仅保留 Math Library 与 Calendar Library。 |
| 部署平台 | ACS 原生云平台 + 物理机计算集群 | 生产 BIZ 命名空间（以运维分配为准） | 管理节点容器化，计算节点物理机。 |
| 任务调度 | MQ 驱动 + 内建 ORCHESTRATION | - | PV Engine 不接入波塞冬调度平台；PV_JOB 由 FRTB/CCR 引擎经 LV68.18 (RiskDL) MQ 以 `PV_JOB_CONTRACT` 投递触发，PV 内部任务 DAG（`PV_JOB`→`PV_TASK_BUNDLE`→`PV_TASK`）由内建 ORCHESTRATION 组件完成。 |
| 数据访问 | 子系统 Utility 接入组件 | RDB_ACCESS / MQ_ACCESS | 统一通过本地 Utility 接入组件访问 TiDB、ACS Kafka。PV Engine 无复杂报表下钻等慢查询缓存诉求，不引入 Redis；热路径复用计算节点进程内缓存（`IN_PROCESS_CACHE`），分布式会话（Session）由 RDB 承载。 |

技术原则：

1. 管理节点与计算节点职责分离：管理节点负责控制，计算节点负责重计算；
2. 引擎侧数据访问统一通过本地 Utility 接入组件，以“受控直连”方式访问 RiskDL 数据服务（RDB/MQ）；
3. 跨系统计算任务统一执行快照契约（`SNAPSHOT_CONTRACT`）校验，确保一次任务使用同版本交易、市场、静态与配置数据；
4. 对外估值能力仅通过 LV68.18 (RiskDL) MQ 的 `PV_JOB_CONTRACT` 暴露，不开放临时接口或未经契约约束的直连调用；
5. 系统计算主链路统一采用 Java 实现，并通过批量计算（bulk）、节点内并发（concurrent）、分布式横向扩展（distributed）及计算节点进程内缓存（cache）等全局性能机制保障批处理窗口时效；Math Library 与 Calendar Library 作为统一基础能力，由 Java 通过 JNI 调用 `libquantnative.so`。

## 2.2. 应用架构总体设计思路

PV 应用架构围绕“风险因子构建 + 估值计算 + 敏感度 + PV Array”主能力链建设，公共能力由 Utility 与 Quant SDK 抽象复用。

架构设计要点：

1. 按能力域拆分 4 个微服务：`LV68.06@pv-manage-node`、`LV68.06@pv-compute-node`、`LV68.06@pv-web-be`、`LV68.06@pv-web-ui`；
2. `LV68.06@pv-compute-node` 部署在物理机计算节点集群（`COMPUTE_NODE`）；其余微服务部署在 ACS 容器平台；
3. 外部 `PV_JOB_CONTRACT` 作业经管理节点拆解为 `PV_TASK_BUNDLE`，再由计算节点 Master 拆解为 `PV_TASK`，并携带统一快照上下文（含 `derived_market_data_version` 与场景字段）驱动执行。

## 2.3. 系统架构总体设计思路

围绕批窗时效、高吞吐和稳定性，系统架构按“分层解耦、并行扩展、稳定治理、统一边界”四类原则设计：

1. **架构形态**：采用管理节点（容器部署）+ 计算节点（物理机部署）的分布式计算架构；计算节点内部采用 Master-Worker 并行模型（Master 负责任务拆分与汇总，Worker 并行执行）。
2. **执行与性能**：计算主链路采用 `BULK + CONCURRENT + DISTRIBUTED` 叠加策略；`PV_JOB -> PV_TASK_BUNDLE -> PV_TASK` 采用三层 1:N 拆分，`PV_TASK_BUNDLE` 按“目标包时长 + 尾包控制 + 失败重分配”切分，曲线/曲面采用“分片预构建 -> 集中收集 -> 全量发布 -> 节点加载”，热路径优先使用计算节点进程内缓存。
3. **稳定性治理**：通过租约心跳、任务状态机、超时重派和慢节点治理保障批处理稳定性；发布环节不采用灰度，执行彩排/仿真验证后一次性发布。
4. **数据与部署约束**：数据层统一依赖 LV68.18 (RiskDL)（RDB/MQ），并通过本地 Utility 接入组件受控直连；各子系统遵循“本 schema 读写、跨 schema 只读”的过渡口径，后续按 API 防腐接口能力逐步替换；按 D 级系统部署口径，当前阶段不单独建设异地容灾链路。
5. **优先级调度**：`PV_JOB_CONTRACT` 携带优先级字段，EOD 批处理任务取最高优先级；管理节点优先为高优先级 `PV_JOB` 打包 `PV_TASK_BUNDLE` 并将优先级透传至 bundle，计算节点按优先级优先领取并计算高优先级 bundle，保证 EOD 批窗不被即时试算/补算等低优先级任务挤占。

微服务视角架构如下：

![pv_arch.jpg](images/pv_arch.jpg)

### 2.3.1. 分布式并行计算架构

下图展示 `PV_JOB -> PV_TASK_BUNDLE -> PV_TASK` 三层拆分在“管理节点分布式调度 + 计算节点Master/Worker并行”架构中的执行方式。

![pv_parallel_arch.jpg](images/pv_parallel_arch.jpg)

执行要点：

1. 管理节点负责将 `PV_JOB` 拆解为多个 `PV_TASK_BUNDLE` 并按状态机驱动分发，优先为高优先级 `PV_JOB` 打包并将优先级写入 `PV_TASK_BUNDLE`；
2. 多个计算节点可并行拉取不同 `PV_TASK_BUNDLE`（按优先级优先领取高优先级 bundle），形成节点级分布式并发(distributed)；
3. 单个计算节点内由 Master 将 `PV_TASK_BUNDLE` 拆分为多个 `PV_TASK`，由 Workers 并行计算(concurrent)；
4. Quant SDK 为同类型计算任务提供统一的批量（bulk）接口，由 `pv-compute-node` 按任务类型组织批量请求并调用。批量处理用于减少逐笔接口调用、重复计算上下文构建及任务调度开销，提高单节点吞吐能力和批处理窗口执行效率；
5. 计算节点维护进程内缓存（本地内存缓存），缓存预构建曲线/曲面及常用中间结果，命中时直接复用，避免逐任务远程读取。

### 2.3.2. 典型PV作业工作流

以下流程描述“RiskDL ETL 就绪 -> FRTB/CCR 发起 `PV_JOB` -> 管理节点拆分 `PV_TASK_BUNDLE` -> 计算节点 Master/Worker 并行执行 `PV_TASK` -> 结果回写 RDB -> 发布`PV_JOB`完成事件”的主链路。

![pv_job_workflow.jpg](images/pv_job_workflow.jpg)

执行要点：

1. 外部入口统一走 `PV_JOB_CONTRACT`，携带完整 `SNAPSHOT_CONTRACT`、作业类型（如 `PV`、`SENSITIVITY`等）及优先级（EOD 取最高优先级）；
2. 管理节点按策略拆分并投递 `PV_TASK_BUNDLE`，计算节点按并行机制执行（并行机制详见 2.3.1）；
3. `PV_TASK_BUNDLE` 队列通过 `LV68.18 (RiskDL) RDB` 实现，任务流转由状态机驱动，并通过乐观锁控制并发领取与状态更新；
4. 每个 `PV_TASK_BUNDLE` 完成后由计算节点 Master 立即落库该任务包结果至 `LV68.18 (RiskDL) RDB`；
5. 三层对象（`job_id`、`task_bundle_id`、`task_id`）均需满足幂等约束，防止重复入库、重复累计或状态错乱；
6. 管理节点持续校验 `PV_JOB` 下全部 `PV_TASK_BUNDLE` 的落库状态：全部成功则推进 `PV_JOB` 完成，存在失败则按幂等键重试/补跑。

### 2.3.3. 节点软隔离与定向调度

为支持运维对计算节点做**软隔离**（排空问题节点、暂停其接活）与**定向调度**（指定某节点承担特定任务包），在不改变“拉模型 + 乐观锁领取”机制的前提下，引入节点注册表（`NODE_REGISTRY`）。能力均落在“计算节点领取 `PV_TASK_BUNDLE`”这一既有动作上，对外作业链路（`PV_JOB_CONTRACT`）与作业拆分逻辑无感知。

**前提：单节点串行消费**。计算节点同一时刻只处理一个 `PV_TASK_BUNDLE`——bundle 经 Master 拆为 `PV_TASK` 后已跑满本节点多核，再并领第二个并无空闲算力、徒增争用与内存压力。因此节点仅在手头 bundle 计算完成并落库后才领取下一个，领取循环天然串行。

**节点注册表（`NODE_REGISTRY`）**：落于 `LV68.18 (RiskDL) RDB`，登记各计算节点的状态信息，作为“节点可否接活”的唯一权威来源。核心维度如下（总设层面，字段细节详设确定）：

| 维度 | 含义 | 维护方 |
| --- | --- | --- |
| 管理态（admin state） | `ACTIVE`（正常接活）/ `DRAINING`（软隔离，仅跑完手头 bundle 不领新包）/ `DISABLED`（停用） | 运维/Web 或慢节点治理设置（主动意图） |
| 健康态（health state） | `ALIVE` / `SUSPECT` / `DEAD`，由租约到期与心跳推导 | 节点续租 + 管理节点判定（观测结果） |
| 租约信息 | 租约到期时间、最近心跳时间，用于失联判定 | 节点心跳续租 |

管理态与健康态分离（两者正交，不可合并）：

- **`DRAINING` 与 `DISABLED` 的区别**在于对手头在算 bundle 的处置——`DRAINING` 是过渡态，让当前 bundle 跑完落库后再停（优雅排空，不丢算力），用于计划维护或可疑但仍可算的节点；`DISABLED` 是持久态，明确“别用这台”，正在计算的 bundle 也会被放弃：由管理节点主动回收该节点名下 `CLAIMED` 的 bundle（公共包重派给其他节点重算，定向包按定向调度条款失败处理），原节点若仍将旧结果算完落库，按幂等键拒收/作废；`DISABLED` 只可手动恢复状态。
- **健康态的逻辑作用**不在于挡领取（失联节点本就不会来领），而在于善后与治理联动：节点领取 bundle 后崩溃/失联（租约到期判 `DEAD`）时，触发其名下 `CLAIMED` 的孤儿 bundle 按幂等键回收重派（即 2.3 第 2 点的失败重分配）；`SUSPECT`（心跳变慢/长尾）则作为慢节点治理入口，可自动将该节点管理态置 `DRAINING`。

**软隔离（领取前检查管理态）**：节点每轮领取前（即空闲、准备领下一个 bundle 时）先读回自身管理态决定是否领取：

- 管理态为 `ACTIVE` 才发起领取；非 `ACTIVE`（`DRAINING`/`DISABLED`）则本轮不领取、进入等待或收尾；
- 置为 `DRAINING` 后节点不再领新包，手头 bundle 跑完落库即自然空出，实现**优雅排空**（不打断在算任务），与 5.1 的慢节点治理复用同一机制；
- 因单节点串行消费，管理态采用轻量“先查后领”即可、无需与领取强制原子：节点空闲才检查、才领取，即便竞态窗口内多领一个 bundle 也跑完即止，无业务影响。

**定向调度（打包时写定向字段）**：管理节点打包时可在 `PV_TASK_BUNDLE` 写入定向字段（目标 `node_id`），节点领取时据此过滤：

- 定向为空即公共包，任意 `ACTIVE` 节点可领；指定目标节点时仅该节点可领；
- 定向**不回落公共**：定向通常源于目标节点具备特殊能力（如配备 GPU、部署特殊版本、拥有独占量化模型），其他节点无法替代，回落公共会被无相应能力的节点错误领走；故目标节点不可用（`DRAINING`/`DISABLED`/失联）时，该 bundle 不转给其他节点，按任务失败处理并由管理节点告警、运维介入。

**并发约束**：上述软隔离与定向均为节点领取时的过滤条件，与优先级排序（2.3.1 第 2 点）叠加；而 `PV_TASK_BUNDLE` 的归属（`READY`→`CLAIMED`、由谁领走）始终由乐观锁保证并发下不被重复领取，与节点管理态的轻量预检查是两类独立判定。`DISABLED` 回收与 `DEAD` 孤儿回收引发的重派，本质是管理节点受控发起的二次领取，仍走同一归属状态机，配合落库幂等键保证同一 bundle 最终只有一份有效结果。

---

# 3. 应用架构总体设计

## 3.1. 模块划分

| 模块 | 功能 | 详细功能介绍 | 包含组件 | 备注 |
| --- | --- | --- | --- | --- |
| Quant Compute Core Module | 量化计算内核 | 提供 Quant SDK 统一计算入口，由 Java Financial Core 承担 Curve Construction、Risk Factor、Pricing、Sensitivity 与 PV Array 主体计算。 | QUANT_SDK | 计算主链路 |
| Risk Factor Module | 风险因子治理 | 风险因子定义、曲线/曲面构建与映射管理。 | RF_REGISTRY, RF_CURVE, RF_SURFACE, RF_MAPPING | 计算主链路 |
| Pricing Module | 估值编排 | 执行 PV 任务编排、参数装配与结果映射。 | PRICING_PARAMS, PV_CALCULATOR, MODEL_REGISTRY | 计算主链路 |
| Sensitivity Module | 敏感度重估 | 按调用方给定的 bump/shift 规格执行 reshock+重定价，返回原始敏感度数值；不做 bucket 映射与聚合。 | SENSITIVITY_CALCULATOR, SENSITIVITY_REVAL | 计算主链路 |
| PV Array Module | 情景估值数组 | 按调用方给定的 scenario_dataset 执行情景重估，输出 PV Array（情景估值数组）。 | PV_ARRAY | 计算主链路 |
| Utility Module | 公共能力 | 数据校验、任务编排与状态控制。 | DATA_VALIDATOR, ORCHESTRATION, RDB_ACCESS, MQ_ACCESS | 各模块复用 |
| Config Module | 配置管理 | 管理 PV 本系统配置、版本冻结与审计留痕。 | CONFIG_STORE, CONFIG_VERSION, CONFIG_AUDIT | 管理节点治理能力 |
| WebUI Module | 交互能力 | 风险因子治理、任务监控、结果查询。 | WEBUI_API, WEBUI_GUI | 用户操作入口 |

## 3.2. 微服务划分

| 微服务 | 职责范围 | 包含模块与组件 | 数据/云服务依赖 | 应用分类 |
| --- | --- | --- | --- | --- |
| `LV68.06@pv-manage-node` | 作业编排、前置校验、按优先级 `PV_JOB->PV_TASK_BUNDLE` 拆分打包（透传优先级、按需写入定向标识）、节点注册表与软隔离/定向治理、状态汇总与失败重试 | Utility.DATA_VALIDATOR, Utility.ORCHESTRATION, Utility.RDB_ACCESS, Utility.MQ_ACCESS | LV68.18 (RiskDL) RDB/MQ 基础数据服务（通过 Utility 接入组件访问） | 后端服务（容器） |
| `LV68.06@pv-compute-node` | Master-Worker 并行计算、按优先级与节点准入态（含定向）领取 `PV_TASK_BUNDLE`、`PV_TASK_BUNDLE->PV_TASK` 拆分、曲线/曲面构建、PV/Sensitivity/PV Array 重计算 | QuantComputeCore.QUANT_SDK, RiskFactor.RF_CURVE, RiskFactor.RF_SURFACE, Pricing.PRICING_PARAMS, Pricing.PV_CALCULATOR, Pricing.MODEL_REGISTRY, Sensitivity.SENSITIVITY_CALCULATOR, Sensitivity.SENSITIVITY_REVAL, PVArray.PV_ARRAY, Utility.RDB_ACCESS, Utility.MQ_ACCESS | LV68.18 (RiskDL) RDB/MQ 基础数据服务（通过 Utility 接入组件访问） | 后端服务（物理机分布式节点） |
| `LV68.06@pv-web-be` | Web 后端 API、鉴权（分布式会话由 RDB 承载）、任务查询与结果聚合，以及风险因子/配置治理 | WebUI.WEBUI_API, RiskFactor.RF_REGISTRY, RiskFactor.RF_MAPPING, Config.CONFIG_STORE, Config.CONFIG_VERSION, Config.CONFIG_AUDIT, Utility.RDB_ACCESS | LV68.18 (RiskDL) RDB 基础数据服务（通过 Utility 接入组件访问），依赖 `LV68.06@pv-manage-node` | 后端服务（容器） |
| `LV68.06@pv-web-ui` | Web 前端交互、任务监控、结果展示与配置入口 | WebUI.WEBUI_GUI | 依赖 `LV68.06@pv-web-be` | 前端服务（容器） |
| `LV68.06@pv-rt-service`（二期） | 实时计算 API：单笔/小批量同步 PV/Sensitivity 即时试算（详见 3.2.3） | QuantComputeCore.QUANT_SDK, Pricing.PV_CALCULATOR, Sensitivity.SENSITIVITY_CALCULATOR | 入参内联（非快照契约），不依赖 RiskDL 快照链路 | 后端服务（容器，二期） |

其中，`LV68.06@pv-compute-node` 在部署时会扩展为多个计算节点实例，并行运行在多台物理机服务器上。

划分依据：

1. 管理与控制逻辑与重计算逻辑资源特征差异显著；
2. 计算节点在批窗时段需要可保障、可独占的大量算力资源，应贴近硬件并最大化多核并发与吞吐；
3. Web 展示层（`LV68.06@pv-web-ui`/`LV68.06@pv-web-be`）与计算控制层解耦，降低发布耦合并隔离前后端变更风险。

## 3.2.1. PV 微服务代码结构

计算与编排类微服务采用四层结构：`adapter`、`application`、`domain`、`infrastructure`；`LV68.06@pv-web-be` 采用三层后端结构；`LV68.06@pv-web-ui` 采用前端工程结构。

| 微服务 | 代码结构口径 |
| --- | --- |
| `LV68.06@pv-manage-node` | 承载管理节点能力（校验、编排、任务治理、配置治理），采用四层结构。 |
| `LV68.06@pv-compute-node` | 承载计算节点能力（曲线/曲面、PV/Sensitivity/PV Array），采用四层结构。`QUANT_SDK` 以 Java Library 方式集成在 `LV68.06@pv-compute-node` 中，通过 Maven 统一管理依赖版本，不作为独立服务部署。Quant SDK 及其内部 Native 依赖随 `pv-compute-node` 统一提测、构建、部署、升级和回退。 |
| `LV68.06@pv-web-be` | 承载 Web 后端 API 与查询聚合能力，采用三层结构。 |
| `LV68.06@pv-web-ui` | 承载 Web 前端交互能力，采用前端工程结构。 |

## 3.2.2. Quant SDK 设计架构

Quant SDK 是 PV Engine 的进程内 Java 金融计算库，以 Java JAR 形式集成到 `pv-compute-node`，由 Worker 同步调用。Quant SDK 内部包括 `pv-quant-sdk-api`、`pv-quant-sdk-impl`、`QuantNativeBridge` 及内部 Native 制品 `libquantnative.so`。主体金融计算由 Java 实现，`libquantnative.so` 仅提供 Math Library 和 Calendar Library 基础能力。

`pv-compute-node` 负责计算任务接收、调度、输入数据获取与准备以及节点资源管理。交易数据、Curve Raw Data、静态/配置数据及相关计算参数按照既定 JSON 格式传入 Quant SDK。Quant SDK 负责 JSON 解析、Schema 校验、金融计算对象构建及计算执行，并将计算结果返回 Worker；Quant SDK 不持久化输入 JSON、业务数据或计算结果，也不承担节点级任务调度职责。

Quant SDK 支持将曲线/曲面的具体期限点，作为风险因子的基础定义。它也支持在最小颗粒度上，对市场风险因子进行识别和计算。在此基础上，可根据具体产品、计算任务及风险计量要求，选择指定的曲线/曲面节点作为风险因子，也可按照期限、区域或其他风险维度进行较大粒度的风险映射与聚合，从而支持不同粒度的敏感度计算及风险结果表达。

下图展示 Quant SDK 数据准备、模型构建与四类计算任务流程：

![pv_quant_sdk_flow.png](images/pv_quant_sdk_flow.png)

Position、Curve Raw Data、静态/配置数据及相关计算参数由 `pv-compute-node` 按任务获取和准备，并按照既定 JSON 格式传入 Quant SDK。每个任务对应一次完整、同步的 Quant SDK 计算调用。Quant SDK 接收到 JSON 计算请求后，完成 JSON 解析和 Schema 校验，并建立本次计算上下文。Quant SDK 的 Java 实现根据 Curve Raw Data、任务类型及模型依赖关系构建所需的曲线、曲面、定价模型及其他金融计算对象，完成计算组织与执行后返回计算结果。

### Quant SDK 内部逻辑架构

Quant SDK 内部按照计算职责划分为以下逻辑层次：

| 层次 | 主要职责 |
| --- | --- |
| 计算请求接入 | 接收 `pv-compute-node`/Worker 传入的计算请求，解析交易数据、市场数据、静态/配置数据、计算参数及任务类型，并建立本次计算上下文。 |
| 计算组织 | 根据计算类型、产品特征、风险因子及模型依赖关系，确定本次计算所需的金融计算对象及执行关系。 |
| 金融计算对象构建 | 根据计算输入及依赖关系构建所需曲线、曲面、定价模型及其他计算对象。 |
| 计算执行 | 基于已构建的金融计算对象执行曲线/曲面构建、PV、Sensitivity、PV Array 等计算。 |
| 结果组织 | 根据计算任务约定组织计算结果，并以内存对象形式返回 `pv-compute-node`/Worker。 |

上述层次属于 Quant SDK 内部逻辑职责划分，不对应独立部署服务。

### 单次调用执行模型

Quant SDK 每次调用接收一个完整的 JSON 计算请求，并以同步方式完成 JSON 解析、Schema 校验、金融计算对象构建及计算执行，随后返回计算结果。计算请求的业务颗粒度由 `pv-compute-node` 决定，可以对应单笔交易、多笔交易、投组级计算，也可以仅执行指定曲线、曲面等金融计算对象的构建，不限定为固定的交易批次。

Quant SDK 采用 Java 模块化设计：`pv-quant-sdk-api` 定义 `QuantSdk` 接口、JSON 输入契约、计算结果类型及操作规格；`pv-quant-sdk-impl` 提供生产计算实现，并根据计算类型及模型依赖关系完成相应计算；`QuantNativeBridge` 负责 Java 与 `libquantnative.so` 之间的 JNI 转换、Library 加载及必要校验。

### 计算能力

| 计算类型 | Quant SDK 主要职责 | 结果形态 |
| --- | --- | --- |
| 曲线/曲面构建 | 根据输入市场数据、静态/配置数据构建所需曲线、曲面及相关计算对象。 | 已构建曲线/曲面 |
| PV | 根据交易及相关模型构建所需金融计算对象，完成产品定价、现金流生成、折现、净现值计算及结果组织。 | 交易级或投组级结果 |
| Sensitivity | 根据交易、风险因子及相关模型依赖完成敏感度/希腊字母计算及结果组织。 | 交易级或投组级结果 |
| PV Array | 根据输入场景及相关金融计算对象执行批量重估，并形成对应的 PV Array 计算结果。 | 交易级或投组级结果 |

不同计算任务可以共享 Quant SDK 内部的模型构建及依赖解析能力，并根据具体计算场景构建和使用相应的曲线、曲面、定价模型及其他计算对象。

### Java Financial Core 与 Native 辅助能力

Quant SDK 的主体金融计算由 Java 实现，包括曲线/曲面构建、产品模型、现金流生成、折现、PV、Sensitivity、PV Array 及计算结果组织。

Math Library 与 Calendar Library 基础能力由 Java 通过 JNI（Java Native Interface）调用 `libquantnative.so` 实现。JNI 负责 Java 对象及基础类型与 C++ 函数参数、返回值之间的进程内转换，不属于网络通信接口。

`libquantnative.so` 是 Quant SDK 唯一的 C++ 制品，仅包含 Math Library 与 Calendar Library，作为 Quant SDK 的内部依赖，不作为独立模块、独立任务、独立服务或外部接口。日历配置作为 Quant SDK 内部只读静态资源统一管理；其他业务配置按照既定 JSON 格式传入 Quant SDK。`libquantnative.so` 不直接访问数据库或业务配置表。

### 生命周期、缓存与并行边界

Quant SDK 按单次调用建立独立计算上下文，仅在调用期间持有计算对象、buffer 及临时中间数据；计算完成后不保留本次调用的业务状态，也不持久化业务数据，因此从业务数据所有权角度保持无状态。为避免逐笔计算过程中重复访问远程存储及重复构建金融对象，PV Engine 在计算节点进程内设计 L1 本地缓存，按 Snapshot 及版本缓存批次内只读的曲线/曲面对象、市场数据快照、静态及模型配置快照和可复用的定价中间结构。缓存不作为权威数据源，并在批次结束、版本切换或失效后释放或重新构建。该缓存能力目前属于已定义但尚未完成开发的计算节点能力，具体实现技术及参数在详细设计和性能测试阶段确定。

具体 Worker 并发与节点资源控制机制见 2.3.1。

### 输入输出与异常边界

Quant SDK 以 Java Library 的调用方式接收计算请求，并以内存对象的形式返回计算结果。

对于返回交易级的计算结果，单笔交易计算失败不影响其他可正常完成的交易。Quant SDK 返回成功交易的计算结果，同时对失败交易标识相应失败状态及错误信息。

对于返回投组级的计算结果，当其中交易计算失败导致无法形成完整投组级结果时，本次计算整体失败，并将异常信息返回调用方。

Quant SDK 内部计算异常通过 Java 异常或约定的结果对象向 `pv-compute-node` 反馈，由 `pv-compute-node` 按既有任务治理机制执行后续失败处理或重算。

### SDK 版本与发布

生产代码使用行内准入 JDK，依赖通过 Maven 及 BOM 统一管理并锁定版本，开发和质量检查遵循行内 Java 规范。

Quant SDK 独立维护并发布 Maven 制品，以稳定接口及 JSON 契约与 `pv-compute-node` 解耦；契约不变时双方可独立发布，生产使用版本由 `pv-compute-node` 锁定，并随其统一提测、部署和回退。破坏性变更须升级主版本并联动验证，所有计算节点使用同一制品版本。

测试以 Java 单元、契约、基准回归及集成测试为主；Native 部分仅覆盖 JNI、ABI、内存安全和 Math/Calendar 一致性。

## 3.2.3. 实时计算 API 微服务（二期能力）

为满足盘中即时估值、Pre-deal / What-if 试算等低时延、小批量需求，规划在第二年研发期新增实时计算微服务 `LV68.06@pv-rt-service`，定位为将 Quant SDK 能力以同步 API 形式对外暴露。

| 维度 | 口径 |
| --- | --- |
| 定位 | 将 Quant SDK 能力以同步 API 暴露，调用方单笔/小批量直接传入市场数据与交易数据，实时返回 PV / Sensitivity。 |
| 使用场景 | 盘中即时估值、Pre-deal / What-if 试算等非监管即时试算需求。 |
| 交易量口径 | 单笔/小批量、低并发量级，与 EOD 数十亿级大批量跑批链路解耦。 |
| 数据路径 | 入参内联（非快照契约）的同步调用，与快照治理的 EOD 结果链路相互独立，不作为监管口径结果。 |
| 边界 | 仍遵循"纯估值执行器"边界（见 3.3），仅返回 PV/Sensitivity 数值原料，不做聚合裁决。 |
| 研发阶段 | 不在 IMA 监管合规关键路径，排入第二年研发期；本期仅预留能力位，接口契约、容量与限流策略在二期详设确定。 |

## 3.2.4. 日终计量批处理流程

日终计量批由授权调用系统通过 `PV_JOB_CONTRACT` 提交 `PV_JOB`。`pv-manage-node` 完成作业校验、任务拆分和调度；`pv-compute-node` 按任务通过 `RDB_ACCESS` 批量获取 Position、Curve Raw Data 及 Config 等计算输入，按照既定 JSON Contract 组装后同步调用 Quant SDK。Quant SDK 完成 JSON 解析、Schema 校验、金融对象构建及计算，并将结果返回 `pv-compute-node`。任务状态和计算结果通过 `RDB_ACCESS` 写入，进度及完成事件通过 `MQ_ACCESS` 发布，由 `pv-manage-node` 汇总并推进 `PV_JOB` 完成。

## 3.3. 开放能力设计

LV68.06 (PV Engine) 不提供通用对外开放能力，仅保留系统内任务接入能力，边界如下：

1. 统一通过 LV68.18 (RiskDL) MQ 的 `PV_JOB_CONTRACT` 向 LV68.16 (FRTB Engine)、LV68.17 (CCR Engine) 提供估值、敏感度、PV Array 作业接入；
2. 所有调用必须携带完整快照上下文，不支持缺失快照契约的调用；
3. PV Engine 不对外开放通用查询 API 或临时直连能力，数据读写遵循 2.1 节“通过 Utility 接入组件受控直连 RiskDL 数据服务”的统一口径。
4. 二期规划开放实时计算 API（`LV68.06@pv-rt-service`，详见 3.2.3）：仅面向单笔/小批量同步 PV/Sensitivity 即时试算，属上述"通用查询 API"之外的受控同步计算能力，不改变 EOD 经 `PV_JOB_CONTRACT` 的批量链路口径。

能力边界（纯估值执行器口径）：PV Engine 定位为重估值的执行算子，仅按调用方给定的入参产出估值数值原料，对监管/业务口径保持无状态、纯被动，不发起、不定义、不聚合任何口径，以此约束能力不向 FRTB/CCR 领域无序延伸。

| 边界 | PV Engine（白名单·只做这些） | FRTB/CCR（PV 永不触碰·负面清单） |
| --- | --- | --- |
| 估值 | 按快照契约做 PV、曲线/曲面构建 | — |
| 敏感度 | 按调用方给定的 bump/shift 规格执行 reshock+重定价，返回原始敏感度数值 | bump 大小、风险因子→bucket 映射等口径定义 |
| 情景重估 | 按调用方给定的 scenario_dataset 执行情景重估，返回 PV Array | 情景的定义与选择（历史窗口、流动性区间、压力设定）；基于 PV Array 派生 PL Vector |
| 聚合裁决 | 不做 | SBM/DRC/RRAO、VaR/ES/IMCC/SES、EAD/CVA、资本汇总 |
| 分析/报表 | 不做 | 归因、IPV、报表、各类测试裁决 |

---

# 4. 系统架构总体设计

## 4.1. 微服务部署和发布策略设计

LV68.06 (PV Engine) 生产采用“管理节点与 Web 微服务容器化 + 计算节点物理机”部署。按 D 级系统口径，当前阶段采用同城双 AZ 部署，不单独建设异地容灾链路。下表为评审阶段部署基线，后续可按批窗压测动态扩容。

| 微服务 | 部署集群 | 实例数（单链路） | AZ 分布（同城） |
| --- | --- | --- | --- |
| `LV68.06@pv-manage-node` | ACS 原生云平台（生产 BIZ 命名空间，以运维分配为准） | 2 | G01 平湖西业务网九区=1, G01 平湖东业务网九区=1 |
| `LV68.06@pv-compute-node` | 生产物理机计算集群（计算资源池，以运维分配为准） | 4-12（已批复采购，可横向扩容） | 待物理机采购落位后按运维分配确认 |
| `LV68.06@pv-web-be` | ACS 原生云平台（生产 BIZ 命名空间，以运维分配为准） | 2 | G01 平湖西业务网九区=1, G01 平湖东业务网九区=1 |
| `LV68.06@pv-web-ui` | ACS 原生云平台（生产 BIZ 命名空间，以运维分配为准） | 2 | G01 平湖西业务网九区=1, G01 平湖东业务网九区=1 |
| `LV68.06@pv-rt-service`（二期） | ACS 原生云平台（生产 BIZ 命名空间，以运维分配为准） | 二期评估（暂定 2） | 二期落位后按运维分配确认 |

发布策略：遵循 4.1.2 节彩排验证方案执行（不采用灰度发布，ST/UAT 与全链路彩排通过后一次性发布）。

### 4.1.1. 子系统与服务单元定级

| 层级 | 对象 | 定级 |
| --- | --- | --- |
| 系统 | LV68 | D级系统 |
| 子系统 | LV68.06 (PV Engine) | 3级子系统 |
| 服务单元 | `LV68.06@pv-manage-node` | 3级服务单元 |
| 服务单元 | `LV68.06@pv-compute-node` | 3级服务单元 |
| 服务单元 | `LV68.06@pv-web-be` | 3级服务单元 |
| 服务单元 | `LV68.06@pv-web-ui` | 3级服务单元 |
| 服务单元 | `LV68.06@pv-rt-service`（二期） | 3级服务单元 |

定级理由：

1. 非主力估值来源：IMA 监管合规审批落地前，行内估值/PV 计算以 LU73 金融市场核心系统（MUREX）为主力系统，LV68.06 (PV Engine) 定位为并行计量/验证与备份计算能力，属"非唯一关键路径"，按普通子系统治理口径执行，定级为 3 级子系统。
2. 不在面客与动账关键路径：PV 产出为风险计量中间结果（PV/敏感度/PV Array），时效要求为 EOD 批窗，非 7×24 实时联机交易，符合 3 级服务单元常规治理与运行特征。
3. 服务单元默认继承：依据《IT系统分级部署原则》“服务单元默认等于归属子系统等级”口径，各服务单元默认随子系统定为 3 级（含二期新增 `LV68.06@pv-rt-service`）。
4. 治理强度与研发阶段匹配：系统尚处研发与功能快速迭代期，现阶段按 3 级口径管理与同体系聚合计量子系统（FRTB/CCR）保持一致；待功能趋于稳定后可结合实际情况再行评估调整定级。

### 4.1.2. 彩排验证方案

LV68.06 (PV Engine) 按 D 级系统口径采用“ST/UAT 测试 + 测试环境全链路彩排”两段式验证流程；其中 UAT 阶段使用生产脱敏数据进行仿真验证。

| 验证阶段 | 核心要求 |
| --- | --- |
| ST/UAT 测试 | 通过测试中心 ST/UAT 测试，覆盖曲线构建、PV、Sensitivity、PV Array 核心功能、失败重试与异常恢复场景；UAT 阶段使用生产脱敏数据进行仿真验证。 |
| 全链路彩排 | 在测试环境完成全链路彩排（含任务编排、数据读写与结果落库）并留痕。 |

发布门禁（Go/No-Go）：两项验证均通过后方可发布；任一不通过即 No-Go。

回退原则：发布后若出现阻断级异常，立即按预案回退至上一稳定版本，并保留日志与结果差异用于复盘。

### 4.1.3. 本地配置文件与 Secrets 管理

`pv-compute-node` 的本地受控配置文件仅保存应用运行参数及凭据引用，不保存业务数据或明文 Secrets。

## 4.2. 数据库部署策略

LV68.06 (PV Engine) 不自建数据库，统一复用 LV68.18 (RiskDL) RDB。本文仅保留消费侧口径（主要用途、接入方式、治理约束）；数据库产品选型、部署架构与容量评估详见 `general_design_review/riskdl_design_review.md`。

### 4.2.1. LV68.18 (RiskDL) RDB（TiDB）

| 项目 | 设计 |
| --- | --- |
| 主要用途 | 读取输入快照与配置、落库曲线/曲面/PV/Sensitivity/PV Array 结果、记录任务状态与审计信息。 |
| 接入方式 | 统一通过本地 Utility 的 RDB_ACCESS 组件访问。 |
| 关键约束 | 仅允许通过 RDB_ACCESS 受控直连底层库，不得使用临时连接方式；并发控制遵循 RiskDL 任务状态/租约机制。 |

### 4.2.2. 两阶段数据交换演进

1. 阶段一（年内合规审批准备期）：为满足 IMA 监管时限与 EOD 批窗性能要求，采用子系统直连数据库跨 schema 只读作为过渡方案；
2. 阶段二（第二年研发期）：若 API 防腐接口满足 EOD 性能要求，逐步替换跨 schema 读取，实现进一步解耦。

## 4.3. 云服务选型及架构设计

LV68.06 (PV Engine) 统一复用 LV68.18 (RiskDL) 云服务能力（MQ）。本文仅保留消费侧口径（主要用途、接入方式、关键约束、降级策略）；云服务选型、实例架构与规格评估详见 `general_design_review/riskdl_design_review.md`。

> PV Engine 不引入 Redis（KV）：PV Engine 无复杂报表下钻等慢查询缓存诉求，热路径复用计算节点进程内缓存（`IN_PROCESS_CACHE`）；多实例 Web 后端的分布式会话（Session）由 RDB 承载。

### 4.3.1. LV68.18 (RiskDL) MQ（ACS Kafka）

| 项目 | 设计 |
| --- | --- |
| 主要用途 | 事件总线、任务分发、进度通知与结果通知。 |
| 接入方式 | 统一通过本地 Utility 的 MQ_ACCESS 组件访问。 |
| 关键约束 | 消费组与主题治理遵循 RiskDL 统一规范。 |
| 故障处理策略 | MQ 异常不做业务降级切换，依赖 Kafka 多副本 HA 保障可用；异常期间批次中止并告警，恢复后按任务幂等策略重试/补跑。 |

链路要求：

- LV68.06 (PV Engine) 到 LV68.18 (RiskDL) 核心链路优先同机房、次优同城；核心链路网络白名单控制。

## 4.4. 外部系统依赖

| 外部系统 | 依赖内容 | 交互方式 | 关键约束 |
| --- | --- | --- | --- |
| LV68.18 (RiskDL) | 输入快照、配置、结果存储与事件总线 | `RDB_ACCESS` / `MQ_ACCESS` | 必须通过本地 Utility 接入组件受控直连访问，并执行快照契约、幂等控制与审计留痕。 |

---

# 5. 非功能需求分析

## 5.1. 性能分析

LV68.06 (PV Engine) 为重计算引擎，性能目标聚焦批窗时效、扩展效率和稳定性：

1. EOD 批处理（曲线构建 + PV + Sensitivity + PV Array）在夜间批窗内完成，不晚于次日 08:00 收口；
2. 计算节点横向扩容按 `1→2`、`2→4` 场景考核：总体吞吐扩展效率验收基线不低于 60%，设计目标为 70%；
3. 管理节点具备失败重试、任务重派、慢节点治理能力（慢节点可经节点注册表软隔离/排空，详见 2.3.3）；
4. 关键链路（任务下发、结果落库、事件回传）完成端到端压测与留痕；
5. 首次投产前执行性能测试，验证三部分：
   - a) 单节点吞吐能力：测量单个计算节点在饱和负载下、单位时间可完成的 revaluation 计算量（以 SVU/单位时间计量）。测试时单节点内 Master-Worker 跑满多核并发并配合批量（bulk）下发压满 CPU，得到稳定的单节点吞吐基线，作为容量推算基本单元；
   - b) 横向扩展效率：按 `1→2`、`2→4` 场景测量节点增加时的吞吐提升，扩展效率 = 多节点实测总体吞吐 ÷（单节点吞吐 × 节点数），用于检验吞吐是否随节点数近似线性增长并暴露 RDB 任务队列争用、MQ、任务打包分发等共享环节的扩展瓶颈；验收基线≥60%、目标 70%；
   - c) 总体评估：由单节点吞吐能力与横向扩展效率推算总体吞吐量，结合 FRTB/CCR 估算的 EOD revaluation 计算量（以 SVU，single valuation unit 计量）判断是否满足批窗需求；
6. 常态化评估机制：后续每次项目立项由专家评估，若投产内容仅影响功能、不影响性能，则不需要专项性能测试。

### 5.1.1. 吞吐保障口径（总设层面）

1. 具体吞吐机制沿用 2.3.1 的并行计算架构（bulk + concurrent + distributed + 进程内缓存）；
2. 调用批大小、节点内并发度、分片规模按压测结果动态调优，并满足批窗收口要求；
3. 扩容验收以 `1→2`、`2→4` 场景压测结果为准，持续跟踪扩展效率与长尾任务占比。

## 5.2. 安全分析

本系统不涉及敏感数据的采集、传输、存储、使用或销毁。

---

# 6. 修订记录

| 版本 | 状态 | 描述 | 修订人 |
| --- | --- | --- | --- |
| V20260506 | 草稿 | 由整体解决方案架构师起草的四个引擎系统架构设计文档，供内部架构设计团队与开发团队讨论和完善。 | 张强弘 |
| V20260511 | 初稿 | 经内部讨论改进后的架构设计文档，并同步补充开发规范、功能需求和开发规划等附属文档。 | 张强弘 |
| V20260516 | 修订稿 V1.0 | 吸纳银行业务团队、银行 IT 团队与管理咨询团队三方反馈意见后的架构修订版本。 | 张强弘 |
| V20260517 | 修订稿 V1.1 | 在 V1.0 基础上新增总设评审材料，适用范围仅限于行内总设评审。 | 张强弘 |
| V20260519 | 修订稿 V1.2 | 在 V1.1 基础上根据银行 IT 团队的反馈，以及参考《云开发范式》文档，调整总设评审材料。 | 张强弘 |
| V20260610 | 总设定稿 V2.0 | 历经 4 场总设评审与 2 次专题讨论，累计处理评审反馈 21 项，各方达成一致共识后总设封板定稿。 | 张强弘 |
| V20260818 | 修订稿 V2.1 | 补充 Quant SDK 板块说明。 | 王宇青、罗小卫、邵宇辰 |
| V20260819 | 修订稿 V2.2 | 补充配置数据管理方案。 | 王宇青、罗小卫、邵宇辰 |
| V20260823 | 修订稿 V2.31 | 仅针对 Quant SDK 评审问题增补：明确 Java 主体与唯一 Native 制品边界，删除未使用 Python/CUDA 口径，补充 Maven/JNI 说明、代码结构、无状态与缓存边界、版本兼容、固定测试策略、本地配置、与 `pv-compute-node` 统一提测发布及日终 RiskDL JSON 数据交互说明；不调整既有 Diagram 及其他已过审架构口径。 | 王宇青、罗小卫、邵宇辰 |