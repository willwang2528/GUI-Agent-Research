# Stage-0A：自然 Memory-Dependent Failure 因果审计

> 审计日期：2026-07-22  
> 范围：当前工作区中官方 `MemGUI-Bench` 任务、失败分析页面、公开案例图和分类器实现。  
> 本步骤只回答：公开自然失败是否已经证明“高风险 GUI commit 前存在可通过安全 probe 消除的 action-relevant state 不充分”。不讨论方法设计。

## 1. 结论先行

**Stage-0A 对目标课题给出 No-Go：问题尚未被自然失败数据证明。**

公开案例足以证明一种较弱现象：GUI Agent 有时会在后续动作中使用与先前观察不一致的事实，或者漏写先前观察到的事实。但是：

- 三个被作者标为 memory hallucination 的公开案例中，**0/3 完成了冻结其他组件的 memory intervention replay**，因此没有一个满足本文的 memory-causation 标准；
- 其中 2/3（任务 056、077）是可信的 memory-compatible candidate；任务 063 不能排除 planning、goal tracking 或 termination policy 错误；
- 0/3 涉及高损失或不可逆外部 commit；
- 任务集中虽有 14 个“发送消息”任务，但公开资源没有给出这些任务上 memory-caused unsafe commit 的自然失败数量；
- 论文声称的 `58.9% memory hallucination` 不是可恢复出的 pooled count，而且和公开类别图存在明显不一致，不能作为课题覆盖率依据。

因此，当前证据支持：

> **存在 action-relevant state 丢失或误用的自然候选案例。**

当前证据不支持：

> **该机制在高风险长程 GUI commit 中具有足够自然覆盖率，且安全 pre-commit probe 能因果修复它。**

---

## 2. Memory-Caused 的硬判据

一个失败只有同时满足以下四项，才记为 `memory-caused`：

1. **历史事实可定位：**在轨迹的具体历史步骤中能够找到正确、任务相关的事实或状态；
2. **反事实依赖成立：**后续正确动作确实依赖该历史事实；
3. **commit 当前观测不足：**执行目标动作时，当前 observation 不能重新提供该事实；
4. **干预 replay 成立：**冻结 perception、grounding、planner、action policy 和环境，只将正确 memory 注入同一 commit point，至少 5 次 replay 中有 3 次修复。

第 1–3 项只能把案例提升为 `memory-compatible candidate`。第 4 项才把相关性标签变成因果证据。

另外，目标课题还要求两项额外条件：

5. **高风险 commit：**错误动作产生外部、非对称或难以恢复的损失；
6. **可用 pre-commit probe：**commit 前存在部署时可访问、不会先造成同等损失、且可能改变 commit decision 的证据获取动作。

---

## 3. 分母与统计完整性

### 3.1 公开分母

| 项目 | 公开值 | 可用于什么结论 |
|---|---:|---|
| Agent × task | 11 × 128 | 总体任务机会空间 |
| 失败执行 | 1,265 | 作者用于 failure analysis 的失败分母 |
| 非 timeout 失败 | 343 | 进入细分类别的分母 |
| requires_ui_memory 任务 | 115 / 128（89.8%） | Benchmark 设计上需要跨时刻/跨界面信息 |
| 明确发送消息的任务 | 14 / 128（10.9%） | 存在外部 commit 机会 |
| 发送消息且 requires_ui_memory | 14 / 14 | 高风险机会与 memory dependency 在任务设计上重合 |

“发送消息”14 个任务来自当前官方 CSV 中明确要求打开 Messages 并发送内容的任务：053、054、067、068、073、074、091、092、099、100、117、118、125、126。它们只证明 benchmark 中存在可审计机会，**不证明这些任务已经发生 memory-caused unsafe commit**。

### 3.2 无法给出可信的 memory failure 数量

作者报告：

- timeout 占 1,265 个失败的 72.3%；
- 非 timeout 失败为 343；
- memory hallucination “on average” 为 58.9%。

这三项不能直接组成可信计数：

1. 如果 343 是 1,265 的精确补集，则 timeout 应为 922，占 **72.9%**，而不是 72.3%；
2. `58.9% on average` 没有说明是 macro average 还是 pooled proportion，论文没有公布对应 memory failure count；
3. 按公开 agent failure distribution 图中可读百分比，逐 Agent 合并 `PMH + ProcMH + OMH` 后的宏平均约为 **85%**（小类别标签重叠会带来轻微读数误差），明显不是 58.9%；58.9% 更接近单独 `ProcMH` 的宏平均；
4. 因而不能用 `343 × 58.9% ≈ 202` 声称有 202 个 memory failure。这只是把一个定义不清的平均数误当 pooled proportion。

### 3.3 分类器本身不是因果标注器

官方实现还有两项会扩大 memory 标签的规则：

- 只要 `0 < IRR < 100`，就自动归类为 `partial_memory_hallucination`；
- LLM 分类 prompt 明确要求 `Prioritize Memory Issues`。

IRR 低只能说明输出保留的信息不完整，不能排除 perception、OCR、planning、action execution、context truncation 或 evaluator error。该分类器没有执行 memory intervention replay，因此作者标签应视为**诊断假设**，而不是因果 ground truth。

---

## 4. 四个公开案例的逐例反事实审计

| Task | 作者标签 | 历史事实可定位 | 后续动作依赖 | commit 当前观测不足 | 3/5 memory replay | Action-state 类型 | 高风险 commit | 可用安全 probe | 审计判定 |
|---|---|---|---|---|---|---|---|---|---|
| 056 SearchAndCalculate | Partial Memory Hallucination | **是**：step 9 为 AAPL 226.91 | **是**：75 股计算依赖价格 | **是**：step 15 Calculator 不显示该价格 | **无数据** | 误用历史事实；无 staleness 证据 | **否**：错误计算/答案，可重做 | **有候选**：检索 step 9 截图/OCR；直接重搜会引入动态价格变化 | **强候选，未因果证明** |
| 063 SearchImageAndDescribe | Process Memory Hallucination | **否**：缺失的是剩余目标/进度，不是一个已定位事实 | 不确定：正确 checklist 会阻止提前结束，但也可能是 planning/termination 错误 | 当前页面不足以证明整个任务完成，但原 instruction 本可提供目标 | **无数据** | 可能是 goal/progress state 丢失 | **否**：仅提前 terminate | 环境 probe 不必要；应先检查内部任务 checklist | **不能归因为 memory** |
| 077 CheckAndNotePermissions | Output Memory Hallucination | **是**：step 7 Wi-Fi 列表 9 项；step 9 PiP 列表 | **是**：最终 Joplin note 直接依赖列表 | **是**：写 note 时当前页面不再显示列表 | **无数据** | Wi-Fi 列表部分丢失；无 staleness 证据 | **否**：本地 note 可编辑 | **有候选**：回看 step 7/9 screenshot，或重访 Settings 后 OCR 对账 | **强候选，未因果证明** |
| 003 RecordAndNameAudio | Timeout | 不适用；任务标记 `requires_ui_memory=N` | 否 | 当前 filename 可见 | 不适用 | action efficiency / text editing | 否 | memory probe 无助 | **负对照：明确排除** |

### 4.1 对任务 056 的反驳

该案例最接近目标问题，因为它满足前三个条件：先观察到正确价格，后续在不可见该价格的 Calculator 页面输入错误价格，并导致错误结果。

但它仍不能证明 memory module 是根因：`143.92` 可能来自 retrieval error，也可能来自数字生成、OCR 后处理、calculator 输入规划或 context truncation。公开结果没有在同一 commit point 注入 `AAPL=226.91` 并冻结其他组件进行 replay。

另外，股票价格是动态事实。最安全的 probe 不是简单重新搜索，因为重新搜索可能得到不同时间点的价格；更合适的是取回带时间戳的 step 9 原始截图/OCR evidence，或者先明确任务要求使用“首次观察值”还是“commit 时最新值”。这说明该案例还涉及 temporal scope，而不是纯粹的 memory capacity。

### 4.2 对任务 063 的反驳

Agent 找到图表后提前宣告完成。作者将其解释为 process memory hallucination，但公开轨迹不能区分：

- 任务目标是否从 context 中丢失；
- planner 是否错误地把“找到图表”当作 terminal subgoal；
- termination policy 是否缺少 completion verifier；
- Agent 是否根本没有建立“搜索 → 抽取 → 写 Joplin”的层级计划。

这里没有一个具体的历史环境事实，在 commit 点重新注入正确事实即可修复。即使注入原始 instruction，是否完成 Joplin 操作仍取决于 planner。因此该案例不能进入 action-relevant environmental evidence failure 池。

### 4.3 对任务 077 的反驳

该案例也是强候选：Wi-Fi permission 的 9 项列表在 step 7 可见，但最终只写入 4 项；公开图显示 PiP 列表实际被完整保留。它证明**选择性信息损失**，而不是整段任务完全遗忘。

不过，论文正文/转述有时声称 PiP 也仅写 7/9，而公开案例图和 final note 显示 PiP 为完整 9 项。这种内部不一致进一步说明不能把文字标签直接当作 causal annotation。要确认 memory 根因，需要在写 note 前注入结构化 Wi-Fi 列表，并检查至少 3/5 replay 是否恢复为 9/9；同时确认 OCR、Joplin 输入长度和输出截断不变。

---

## 5. 课题成立性所需的最小数量证据

当前可诚实报告的数量是：

| 统计对象 | 数量 / 比例 | 解释 |
|---|---:|---|
| 作者公开的 memory-labeled case studies | 3 | 不是随机样本 |
| 满足前三项、可进入 replay 的 candidate | 2 / 3 | 056、077 |
| 满足完整四项 memory-causation 标准 | **0 / 3** | 都没有 intervention replay |
| candidate 中存在部署可访问 probe | 2 / 2 | 只证明 probe 存在，不证明 EVSI 为正 |
| candidate 中高风险或不可逆 commit | **0 / 2** | 均为可重做的答案/本地 note |
| 公开高风险 message 任务机会 | 14 / 128 | 没有对应自然 failure count |
| stale-memory 自然案例 | **0** | 056 是错误值/时间作用域歧义，不是已证明 staleness |

不能从公开资料估计：

- `P(memory-caused | failure)`；
- `P(memory-caused | high-risk commit failure)`；
- `P(存在正 EVSI safe probe | memory-caused high-risk failure)`；
- memory intervention 的修复率；
- probe 的额外步骤、延迟和任务成功净收益。

---

## 6. Go / No-Go

### 对弱命题

> 长程 GUI Agent 会出现先前观察事实在后续动作中丢失或误用。

**Weak Go。** 任务 056 和 077 是可人工核查的直接候选证据。

### 对目标研究命题

> 高风险 GUI commit 的重要自然失败来源是 action-relevant evidence insufficiency，而且部署时可通过安全 pre-commit probe 因果修复。

**No-Go。** 当前没有一个公开案例同时满足：高风险 commit、完整 memory-causation replay、safe probe 修复。

在继续后续步骤前，Stage-0A 至少需要补齐：

1. 获取 14 个 message 类任务的原始失败 trajectories；
2. 盲标 historical fact、commit point、current-observation sufficiency、loss severity 和候选 probe；
3. 对每个候选执行 5 次冻结组件的 memory injection replay；
4. 只有 `>=3/5` 修复才计为 memory-caused；
5. 在 memory-caused 高风险案例上，再执行 probe/no-probe replay，证明 probe 会改变 decision，而不是只增加 token 或导致 abstain。

如果高风险失败中通过该标准的自然案例太少，研究问题应降级为“长程事实保真与输出核对”，不能继续声称改变高风险 GUI 控制的能力边界。

---

## 7. 可复核来源

- [MemGUI-Bench arXiv](https://arxiv.org/abs/2602.06075)
- [MemGUI-Bench 官方仓库](https://github.com/lgy0404/MemGUI-Bench)
- [官方 failure analysis 页面](https://lgy0404.github.io/MemGUI-Bench/failure-analysis.html)
- 本地任务定义：`external/MemGUI-Bench/data/memgui-tasks-all.csv`
- 本地分类器：`external/MemGUI-Bench/memgui_eval/bad_case/bad_case_agent.py`
- 本地公开案例图：`external/MemGUI-Bench/docs/images/failure-analysis/`

> 证据等级说明：官方仓库在 2026-07-10 公布 MemGUI-Bench 已被 ACM MM 2026 接收；当前可公开核验的论文正文仍是 arXiv 版本。会议接收提升了来源质量，但不消除上述分母、taxonomy construct bias 与缺少因果 replay 的问题，因此它仍不足以单独证明本课题成立。
