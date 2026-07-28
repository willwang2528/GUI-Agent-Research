# Stage 0C：行动状态失效的跨 Benchmark 证据审计

> **SUPERSEDED STATUS NOTICE（2026-07-22）**：本文件保留早期案例级分析，但其中 `Case-level Qualified GO` 不再是有效门槛，也不得用于开放 Step 2。当前权威状态为 `stage0f_osworld2_natural_burden_preregistration.md` 的 **FRAME-READY / PILOT-ELIGIBLE，Step 1 IN PROGRESS**。

> 当前判定：**Step 1 = Case-level Qualified GO；Memory 因果 = HOLD。**
>
> 当前被支持的是：两篇 2026 预印本的公开案例描述中，任务更新后的要求与后续行动、持久 UI 状态或最终检查出现不一致。该证据不估计一般发生率，也不识别内部根因。
>
> 尚未被证明的是：该现象由 Memory 模块独立造成、具有自然生产流行度，或“行动契约”能够解决它。

## 1. 本轮究竟证明什么

研究对象不是“Agent 能否复述历史”，而是以下行为链是否真实发生：

```text
旧事实曾经正确
→ 新证据使旧事实失效或不完整
→ 新证据已经到达 Agent，或部署时本可被探测
→ 依赖旧事实的 UI 状态、计划或中间计算应当失效
→ Agent 没有完成撤销、更新、重算或外部核验
→ 后续动作或最终检查仍服从旧状态
```

若只能证明前两项，这是 benchmark 设计属性；若能观察到整条行为链，这是行动状态传播与协调失败；只有冻结其他模块、单独修正 Memory 后稳定恢复，才能称为 Memory-caused failure。

本轮证据限定为 2026 年两篇官方公开预印本：

| 论文 | 年份 | 状态 | 官方资源 | 本轮用途 |
|---|---:|---|---|---|
| OSWorld 2.0: Benchmarking Computer Use Agents on Long-Horizon Real-World Tasks | 2026 | arXiv 预印本，尚无同行评审 venue / CCF rank | [Paper](https://arxiv.org/abs/2606.29537) · [Project](https://osworld-v2.xlang.ai/) · [Code](https://github.com/xlang-ai/OSWorld-V2) · [Trajectories](https://huggingface.co/datasets/xlangai/osworld2.0-trajectory) | 环境侧动态变化、跨应用状态维护、验证失败与正反例 |
| When Users Change Their Mind: Evaluating Interruptible Agents in Long-Horizon Web Navigation | 2026 | arXiv 预印本，尚无同行评审 venue / CCF rank | [Paper](https://arxiv.org/abs/2604.00892) · [Code and data](https://github.com/HenryPengZou/InterruptBench) | 直接注入用户更新，控制“完全没有看到更新”的解释 |

两篇论文满足“2024–2026”时间约束，但不能被包装成 CCF-A / B 已录用论文。使用它们的理由是：它们提供 2026 年才出现的长程动态 GUI 轨迹和公开环境，属于需要跟踪的前沿方向。

## 2. OSWorld 2.0：问题规模，而非 Memory 因果

### 2.1 定量证据

| 指标 | 官方结果 | 能证明什么 | 不能证明什么 |
|---|---:|---|---|
| 长程任务 | 108 | 存在可执行、可评分的长程 GUI 工作流集合 | 108 个任务都发生状态失效 |
| 人类中位操作时间 | 约 1.6 小时 | 工作流确实远长于短 GUI benchmark | 时长本身导致 Memory failure |
| 人类预计超过 1 小时 | 69.6% | 多数任务需要持续协调 | 自然生产任务具有同样比例 |
| 强 Agent 平均步骤 | 超过 250；Opus 4.7 单动作设置 318.4 tool calls | Context、工作状态和验证负担达到数百步 | 多一步必然增加遗忘概率 |
| 最佳 500-step 结果 | 20.6% binary，54.8% partial | Agent 常能取得部分进展，却难以完成全部约束 | 未完成部分都由 Memory 引起 |
| 137–163 分钟任务 | 所有报告模型均低于 10% binary | 完成率与 horizon 强负相关 | horizon 与 Memory 的因果关系 |
| 超过 163 分钟 | 17 个任务中所有报告模型均为 0% binary | 当前系统存在明显长程能力边界 | 状态失效是唯一根因 |
| Recovery + repair 预算 | 所有系统均低于 7% | 当前轨迹很少显式投入错误检测和修复 | 增加修复 token 就一定成功 |

挑战现象标签中，Cross-source Reasoning 为 46/108，Implicit-state Inference 和 Multi-item State Tracking 均为 43/108，Conflict Disambiguation 为 39/108，Dynamic Environment 为 10/108。这些是任务设计覆盖率，不是失败率，也不能相加估计 prevalence。

Dynamic Environment 的原始 binary 结果为：Opus 4.7 30%，Sonnet 4.6 10%，GPT-5.5 30%，Qwen 3.7-Plus 0%，MiniMax M3 0%。该行只有 10 个非随机、带重叠标签的任务；论文也明确要求配合 exposure attribution 解读。因此它只能证明动态状态任务对多个模型困难，不能证明失败根因是 Memory。

行为标注还显示大量竞争性解释：GUI / visual grounding issue 为 20.4%–61.1%，planning or goal drift 为 41.7%–81.5%，final-state exactness failure 为 84.3%–95.4%，premature stop / false done 为 75.0%–83.3%。这些标签可重叠，且来自对既有报告的模型标注与人工复核。它们说明必须做根因排除，不能把高失败率直接归入 Memory。

### 2.2 Task 035：最强环境动态候选

任务要求依据 TeamChat 公告、审批频道和私信填写采购单。执行期间：

1. 初始规则包括硬件单项预算上限 1,000 美元和指定供应商；
2. 后续通知授予一个例外；
3. 更晚的通知把硬件预算上限从 1,000 美元改为 2,000 美元，并把供应商改为 CenTech Solutions；
4. Agent 必须判断哪些已有表格项失效，并更新相应行。

官方项目页展示的失败轨迹包含以下关键节点：

| 节点 | 可观察行为 | 第一性原理解释 |
|---|---|---|
| Step 05 | 捕获初始规则 | 形成早期锚定状态 |
| Step 13 | 注意到动态审批频道通知 | 排除“完全没有动态来源”的简单解释 |
| Step 23 | 发现表格只有一行，但私信中存在更多请求 | 已意识到内部工作集不完整 |
| Step 44 | 明确认出一条新消息很重要 | 至少一个更新进入显式推理 |
| Step 48 | 宣称已经获得全部信息 | 在 source reconciliation 完成前关闭信息收集 |
| Step 51 | 把新消息判为与采购任务无关 | relevance / planning 决策可能阻断更新传播 |
| Step 76 | 宣称五条采购请求均已完成 | 最终检查验证内部五行叙事，而不是外部 source completeness |
| 最终状态 | 缺失已经批准的请求 | 不完整行动状态传播到持久表格和最终验证 |

论文的 exposure attribution 将 MiniMax M3 的 Task 035 在 Dynamic Environment 上标为 `Blocked`：Agent 找到大部分早期规则与部分晚期修正，但没有连贯整合动态更新。

这一案例足以支持：

> 环境语义变化会使早期行动相关事实失效；Agent 即使注意到部分更新，也可能继续让不完整工作状态支配编辑与最终检查。

它仍不能区分四个环节：

```text
E：是否持续监控并实际打开全部更新
G：是否正确读取更新的实体、数值和覆盖关系
M：是否把已正确读取的更新写入并维持在工作状态中
P/V：是否重算受影响项，并用外部真值而非内部叙事进行检查
```

因此，Task 035 是跨模块 action-state reconciliation failure，不是 Memory-only 正例。

### 2.3 必须保留的反例

| 案例 | 观察 | 研究作用 |
|---|---|---|
| Task 024 DS-2019 | Agent 发现 12,000 美元证书低于 18,000 美元要求，暂停签署、调用 `ASK_USER`，并对新证书再次质疑 | 证明 Agent 有时能把证据不足转化为阻断、复核与恢复，验证失败不是必然事件 |
| Task 052 moving popup | 截图后弹窗移动，点击落在旧坐标 | 这是 observation–action latency / TOCTOU 失败，不是语义 Memory failure |
| Task 008 reimbursement | 一条 493-step、五应用轨迹能把早期 account-code 等信息带到后期并提交，得分 0.76；项目页另展示一条 500-step 未提交运行 | 证明部分数百步事实能保持；不同运行不能合并成一个 Memory 失败故事 |
| Task 035 自身 | 至少一条 late exception 被成功整合 | 动态更新不是必然丢失，必须测条件失败率 |

## 3. InterruptBench：控制“更新根本没有到达”

### 3.1 数据和实验范围

InterruptBench 基于 165 个经过人工验证的 WebArena-Lite seed task。论文为每个任务生成 Addition、Revision 和 Retraction 三类更新，共 495 个经过人工复核的合成场景，并测试六个 backbone。默认在对应 baseline 轨迹 60% 位置注入更新，不重置既有环境状态。

本地复核官方仓库 commit `17da111e4858b93c0cab1d88f85e1735fbd1d423`：

- 六个公开 raw JSON 文件均各含 165 条，用于单轮或多轮更新变体；
- 每条记录显式保存 `task_id`、最终 intent、transformed initial intent 与 updates；
- 任务 3 的初始意图缺少起点，注入内容为 `Starting from Randyland`；
- 60% 注入配置在公开 `interrupt_spec` 中可直接核验。

公开仓库支持复核数据构造和注入协议，但没有发布论文全部模型轨迹；因此最终行为结果仍以论文及官方 case study 为主，不应夸大为完全独立复现。

### 3.2 Randyland 案例形成更完整的失败链

任务最终要求比较从 Randyland 到 Carnegie Mellon University 的步行与驾车时间。失败轨迹中：

```text
用户更新明确到达：起点改为 Randyland
→ Agent 在语言层面承认更新
→ UI 的 From 字段仍保持旧起点
→ 路线没有重新计算
→ 最终比较仍依赖旧路线状态
```

正确轨迹则显式撤销旧起点、修改 `From` 字段、触发重计算，再报告新结果。

这个成对案例证明的是 `acknowledged update–action state divergence`：更新已经进入交互上下文甚至显式推理，却没有传播到持久 UI 状态及其下游计算。它比 Task 035 更强地压低了“消息完全未被看到”的解释。

但它仍不能证明“Memory 忘记 Randyland”：

- 语言承认表明该信息当时仍在 Context 中；
- 失败可能发生于依赖识别、计划修订、UI 修复、重新计算或最终验证；
- 论文没有单独替换 Memory 并冻结其余组件。

### 3.3 位置敏感性不是统一的“越晚越差”

| 模型 | 20% 位置成功率 | 80% 位置成功率 | 允许解释 |
|---|---:|---:|---|
| Claude Haiku 4.5 | 43.64% | 24.24% | 该模型对较晚更新更敏感 |
| DeepSeek V3.1 | 30.30% | 24.24% | 存在较弱的晚更新退化 |
| Claude Opus 4.5 | 47.27% | 56.97% | 强模型构成反例，能更好复用进度或局部修复 |

因此只能写“update-position sensitivity is model-dependent”，不能写“更新越晚必然越难”或“长 horizon 普遍导致遗忘”。

论文中的 no-interruption baseline 没有收到完成最终意图所必需的信息，却仍按最终意图评分；作者也把它定义为 lower-bound reference。因此 interrupted 与 no-interruption 的差值不能解释为 Memory 增益或公平的有无更新效应。

## 4. 跨 Benchmark 收敛证明

| 证据维度 | OSWorld 2.0 | InterruptBench | 合并后能证明什么 |
|---|---|---|---|
| 更新来源 | 环境中的 TeamChat / 通知 | 直接用户消息注入 | 问题不局限于单一信息通道 |
| 环境状态 | 多应用采购表和审批来源 | 持久 Web UI 与路线计算 | 更新必须传播到外部状态，而非只修改语言回答 |
| 主要混淆 | 可能没有持续监控全部消息 | 更新已直接送达并被承认 | “完全未暴露”不足以解释全部案例 |
| 失败终点 | 不完整采购表及错误自检 | 旧 From 字段、未重算路线 | 旧状态会影响编辑、计算和最终输出 |
| 反例 | Task 024、Task 008、部分 late exception | 正确 Randyland 轨迹、Opus 晚更新改善 | 该现象可避免，不是任务定义上的必然失败 |

由此可以写出当前最强、仍可防守的结论：

> Across two 2026 long-horizon GUI/Web benchmarks, agents sometimes continue acting on obsolete or incomplete task state after task-relevant updates. The observed failure is an action-state propagation and reconciliation failure; existing evidence does not identify a standalone memory-module cause.

## 5. 证据等级与 Step 1 裁决

| 等级 | 证据要求 | 当前状态 |
|---|---|---|
| P0：任务可能需要状态维护 | 数据集设计中存在跨步依赖 | 已超过 |
| P1：结果与 horizon / dynamic challenge 相关 | 有聚合成功率和分层结果 | 已超过，但仅相关 |
| P2：直接轨迹观察 | 可定位更新、旧状态和后续错误 | OSWorld 2.0 Task 035 达到 |
| P2+：受控更新且跨 benchmark 收敛 | 更新直接注入并观察 persistent-state divergence | InterruptBench + OSWorld 2.0 达到 |
| P3：Memory 因果 | 冻结其余组件，memory-only 修复稳定改变结果 | 未达到 |
| P4：新机制因果 | 等预算下新机制优于信息匹配基线且跨任务复现 | 未开始 |

所以 Step 1 应拆成两个精确判定：

| 命题 | 判定 | 下一动作 |
|---|---|---|
| 两个公开案例中存在 update-to-action inconsistency | **Case-level Qualified GO** | 允许进入 Step 2 identifiability calibration |
| 该现象具有生产自然流行度 | **HOLD** | 需要随机自然轨迹分母或现场 telemetry |
| 该现象由 Memory 模块独立造成 | **HOLD** | Step 2 必须做冻结组件干预 |
| “行动契约”已经被证明必要或有效 | **NO EVIDENCE YET** | 只能在 Step 4–6 检验 |

## 6. Step 2 的最小证据门

下一步不再继续寻找相似案例，而是隔离根因。优先使用 Task 035 family 或 InterruptBench revision family，构建同一 checkpoint 的成对环境：

| Arm | 唯一变化 | 若首次稳定修复，合理归因 |
|---|---|---|
| R0 Original | 原系统 | 复现基线 |
| G-star | 只把已经出现的更新准确转录，不增加新信息 | perception / grounding |
| R-star | 固定同一 grounding output，只通过独立接口替换跨步持久 state updater | persistent state update / retention 的充分修复路径 |
| E-star | Memory 不变，增加一次部署可用的当前规则 probe | active monitoring / sensing |
| P-star | 不提供正确值，只增加“识别受影响依赖并重算”的 obligation | planning / dependency propagation |
| V-star | 不提供正确值，只要求根据外部 source of truth 检查 | verification reference |
| A-star | 直接提供正确最终动作 | downstream policy ceiling |

每个 checkpoint 至少使用五个 paired seeds；原失败至少 3/5 稳定复现。所有 arm 固定模型、prompt、历史、当前 observation、token、工具、时延和随机设置。

关键防污染规则：R-star 只能处理同一条已送达、已 grounding 的 event，并且必须通过独立、跨步持久的 state store 接口执行。把未打开消息、环境最终真值或 planning instruction 直接塞进 prompt，同时改变了 exposure、grounding、salience 和 planning，不能用于 Memory 因果归因。完整修订设计见 `stage0d_root_cause_identification.md`。

## 7. 可证伪停止条件

若出现以下任一结果，应缩题或放弃对应强主张：

- G-star 或 P-generic 完全回收 R-star 的收益：主要瓶颈不是持久状态；
- E-star 通过获取新信息修复，而 R-star 不修复：属于主动感知或有效性检查；
- generic final inspect 与定向 probe 等效：不需要特殊 contract-guided verification；
- 正确 Memory 仍不改变提交：该案例不是 memory-caused；
- flat versioned state 与 structured contract 等效：不存在结构表示增益；
- 正反例中 conditional failure rate 很低或只集中于单一模型、任务或更新类型：一般性不足；
- contract intervention 还能“修复”Task 052 的移动坐标：说明实验偷偷改变了感知、时延或推理预算。

## 8. 第五轮 Battle 共识

三类审稿角色的共同边界是：

```text
Step 1：两个公开案例中的 update-to-action inconsistency = Case-level GO
Step 2：Memory 是否为根因 = HOLD，进入受控诊断
Step 3：grounding、monitoring、planning、verification 混淆必须分别排除
Step 4–6：在完成根因识别前，不得声称行动契约有效
```

本阶段最重要的措辞修正是：研究对象暂时应称为 **Update-to-Action Consistency Failure**。只有 Step 2 证明独立、跨步持久的 R-star 具有信息、提示与预算匹配后的独立效应，才能进一步收窄为 Memory；如果只有 prompt 结构、E-star、P-generic 或 V-select 有效，课题应分别改名为 Context / State Representation、Active Sensing、Plan–Artifact Repair 或 Verification，而不是强行保留 “Memory”。
