# Stage 0B：MaDS 观察性 Pilot——它支持的是可审计性缺口，不是 Memory 失败因果性

> 判定：**Step 1 仍为 HOLD / 未通过。** 这批数据证明了发布日志的 schema 与可审计性缺口，但没有发现一个可归因于 Memory 的自然失败，也没有证明 Agent 的内部决策表示缺少相应语义。

## 1. 审计问题

本轮不问“MaDS 是否用了 Memory”，而问三个更严格的问题：

1. Memory 是否显式记录了后续动作所依赖的事实及其来源？
2. 在购买、支付、发送等 commit-like 动作前，记录中是否存在事实有效性、环境复核和失败恢复的可审计接口？
3. 已释放的失败中，是否存在“只修正 Memory 就能修复”的自然候选？

数据来自 [MaDS 官方仓库](https://github.com/PcCin37/MaDS) 的 `Data/execution_traces/01_ours_mads`。本地只读审计脚本为 `stage0_mads_pilot_audit.py`。

## 2. 定量结果

| 指标 | 结果 | 允许的解释 | 禁止的解释 |
|---|---:|---|---|
| 决策记录 | 127 | 可形成字段级观察样本 | 不是随机自然任务分母 |
| 含 `experiences` | 116 / 127 = 91.34% | 系统频繁向决策注入经验 | 经验一定影响了动作 |
| 含 `facts` | 93 / 127 = 73.23% | 系统显式传递部分事实 | facts 已达到行动充分性 |
| 含 `preconditions` | 116 / 127 = 91.34% | schema 已表达经验的适用前提 | 当前环境一定重新验证了前提 |
| 含 provenance | 127 / 127 = 100% | 可追溯经验或事实来源 | 来源仍然有效 |
| 显式 validity 字段 | 0 / 127 | 释放的日志 schema 没有可直接审计的有效期或失效条件字段 | 模型从未在隐式推理中考虑有效性；决策表示一定缺少该能力 |
| 显式 verification 字段 | 0 / 127 | 日志没有把 commit 前环境复核保存为独立结构化字段 | 系统从未看当前画面或从未核对 |
| 显式 recovery 字段 | 0 / 127 | 日志没有把失败后的恢复契约保存为独立结构化字段 | 系统实际上没有重试或恢复 |
| commit-like 决策 | 7，覆盖 4 个案例 | 存在可用于后续干预的决策机会 | 7 个动作都是错误或不可逆 commit |
| 已记录局部失败 | 8 / 127 = 6.30% | 可用于校准失败分类 | 等于任务级失败率 |
| 初步判为 Memory-caused | 0 / 8 | 当前释放证据没有一个 Memory 根因正例 | 自然 GUI 中不存在 Memory 问题 |

7 个 commit-like 决策包括 4 个进入购买、2 个支付流程和 1 个发送评论。它们的模型响应均直接输出点击动作；但“直接点击”不等于“没有验证”，因为模型仍可能使用了当前截图中的证据。

### 2.1 源码能支持的精确边界

官方 `ExperienceRecord` 只有任务描述、关键词、动作流、自由文本 `preconditions`、成功标记、使用元数据和 `source_task_id`；`FactRecord` 只有内容、关键词、自由文本 `source` 和使用元数据。由此可以直接证明：

> MaDS 公开的 typed Memory schema 缺少机器可寻址、可由 controller 直接求值或触发的 validity predicate、命题—环境 evidence binding、verification operator、invalidation / expiry 和 recovery policy 接口。

这是一项 **first-class executable memory-schema operationalization gap**，不是总体能力缺口：

- `preconditions: str` 能承载自然语言条件，但没有 `true / false / unknown` 状态或 evaluator；
- `source` 和 `source_task_id` 是来源标签，不是某命题与具体 observation/version 的证据绑定；
- `last_used_at` 是检索使用时间，不是观察时间、有效期或失效条件；
- 自由文本、当前截图、上游 subtask generator 或模型隐式推理仍可能实现验证；
- case01 已证明没有显式 recovery 字段时，系统仍可能通过 post-action feedback 重试。

因此，源码支持的是“typed interface 没有一等执行接口”，不支持“Memory 无法表达这些语义”或“Agent 没有验证与恢复能力”。

## 3. 八个失败实际上告诉了我们什么

| 类型 | 数量 | 代表案例 | 第一性原理解释 |
|---|---:|---|---|
| grounding / 点击未命中 | 6 | 商品卡片、直播标签、尺码框、不喜欢图标 | 目标元素已在当前状态中，失败发生在定位或执行映射，不需要假设历史事实丢失 |
| actuation | 1 | 向价格输入框输入 `100` 后没有出现文本 | 正确动作意图已知，但工具执行没有产生预期状态变化 |
| action decode / grounding | 1 | 子任务要求点击加入购物车，实际动作为 drag | 当前目标正确，动作类型或解析错误 |

因此，Memory 已被频繁检索与注入，并不意味着观察到的失败就由 Memory 引起。相反，这 8 个失败是步骤 3“排除 grounding、规划、执行和模型混淆”的必要负对照。

## 4. case01 支付链：最有价值的案例为什么仍不是正例

case01 的任务要求选择颜色、选择尺码并进入付款流程：

1. Step 14 和 15 对尺码框的点击没有产生状态变化，post-action verifier 明确判为失败；
2. Step 16 重试同类点击后，verifier 观察到 `38码（现货现发）` 高亮，判为成功；
3. Step 17 进入金额为 ¥73.90 的待支付页；
4. Step 18 进入验证码输入页。

这条链是目标假设的强反例，而不是正例：

- 两次 grounding 失败被环境反馈发现，第三次重试成功，说明即使没有显式 recovery 字段，系统运行时也发生了恢复；
- commit 前所需的颜色、尺码和金额由当前 UI 或紧邻状态提供，没有证据表明某个早期事实被丢失、污染或错误地当作仍然有效；
- 局部 verifier 只证明页面迁移与金额显示符合子任务，不证明订单语义完全正确；
- 进入验证码页也不能证明已经发生不可逆支付或损失。

所以不得从该案例写出“错误 Memory 导致 unsafe payment”。它只能暴露一个审计问题：当前日志没有以独立、机器可检验的字段说明，在 commit 前哪些前提必须为真、由什么环境证据确认、若不成立应如何停止或恢复。相关语义仍可能存在于自由文本、上游 debate、subtask generation 或模型隐式推理中。

## 5. 第三轮 battle 后的判决

三类审稿角色经过第三、第四轮交叉质询后的共识边界：

| 审稿角色 | 最初攻击点 | 最终保留结论 |
|---|---|---|
| 自然失败怀疑论者 | 8 个失败全有更直接的 grounding / actuation 解释 | MaDS 不推进自然 Memory failure；case01 是隐式恢复反例 |
| 因果协议审稿人 | 字段缺失不能直接叫能力或表示缺口 | 只能称公开 schema 的 first-class executable operationalization gap |
| 复现审稿人 | 日志字段统计太弱，必须检查源码与视觉输入 | 源码支持 typed-interface absence；Git LFS 截图缺失阻止 faithful replay |

允许写入论文动机的最强结论是：

> MaDS 的公开轨迹支持 **trace auditability-gap hypothesis**：Memory 日志保存了经验、事实、前提和来源，却没有把 validity、verification 与 recovery 保存为独立机器可读字段，因此研究者无法仅凭发布日志审计一次 commit 是否获得了充分且仍有效的状态证据。

目前禁止写入的结论是：

- 该日志 schema 缺口已经造成自然 Memory failure；
- Agent 的内部决策表示本身缺少 validity、verification 或 recovery；
- 7 个 commit-like 动作都未经任何验证；
- 8 个失败中的任何一个能被 memory-only intervention 修复；
- case01 证明了 stale Memory、错误购买或不可逆损失；
- 增加一个 action-contract 字段就会提升长程成功率。

## 6. 对七步证明链的影响

| 步骤 | 影响 | 判定 |
|---|---|---|
| 1. 自然失败是否存在 | 没有发现 Memory-caused 正例；8 个失败均更像非 Memory 混淆 | **不推进，HOLD** |
| 2. 根因是否是行动状态 | 只发现日志 schema 的可审计性缺口，尚未连接到内部表示或错误动作 | **仅提供测量候选** |
| 3. 排除混淆 | 提供 8 个 grounding / actuation / decode 负对照 | **推进协议设计** |
| 4. 正确状态是否因果修复 | 没有成对 intervention | **未开始** |
| 5. 重观察是否优于同证据反思 | 没有 probe / reflection 对照 | **未开始** |
| 6. 等预算比较 | 没有实验 | **未开始** |
| 7. Go / No-Go | 不能据此放行课题 | **HOLD** |

## 7. 最小下一实验

对完整决策输入可恢复的 commit 点执行冻结策略的成对干预：

1. `R0 Original`：原始 Memory 与原始当前观测；
2. `R2 Grounding repair`：只给出正确 UI 元素定位；
3. `A Actuation repair`：动作与目标不变，只修复执行器；
4. `R3 Correct memory only`：只把已知历史事实替换为正确、来源匹配的值，不增加新环境信息；
5. `R4 Deployable probe`：允许重新打开来源页或读取当前可见状态；
6. `R6 Oracle plan`：提供正确下一步计划，作为 planning 上界。

只有在冻结模型、prompt、当前截图、action decoder、token 和随机种子的条件下，`R3` 首次稳定修复，样本才计为 Memory-caused；若 `R4` 通过获取原 observation 中没有的新信息首次修复，则属于主动感知或状态有效性问题；若 `R2` 首次修复，则属于 grounding。放大截图或重新标出按钮不算主动感知。当前截图为 Git LFS pointer，尚不能完成这一识别实验。

还必须把 representation effect 与 information advantage 分开：使用完全相同的事实、来源、有效期、验证和恢复信息，比较 flat text 与 structured contract；只有 structured contract 更好，才能支持表示效应。若 structured 版本额外获得了当前真值或新环境证据，改善来自信息优势，不能归因于表示。

推荐使用三因素实验，而不是只做“加模块 / 不加模块”：

| 因素 | 水平 |
|---|---|
| 信息完整性 | incomplete / complete |
| 表示 | flat text / typed contract |
| 执行方式 | prompt-only / enforced action gate |

`flat-complete` 与 `structured-complete` 的语义和 token 必须匹配。只有后者更好，才能说明结构本身有价值；若只有 `structured + enforced gate` 更好，贡献来自可执行约束机制，而不是序列化格式。

## 8. 停止条件

若后续随机自然样本继续满足以下情况，应缩题或放弃“Memory 是自然主因”的命题：

- Memory-only 干预几乎从不首次修复；
- 大多数候选在 grounding 或 actuation 修复后消失；
- commit 前所需事实总能从当前页面直接获得，不需要跨时间状态；
- 结构化 validity / verification / recovery 只提升日志可解释性，不改变动作或任务结果。
