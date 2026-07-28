# Round 0：Problem Anchor 与证据门

> date: `2026-07-22`  
> phase: `problem_anchor_evidence_gate`  
> verdict: `HOLD`  
> review_independence: `same-family`  
> acceptance_status: `provisional`

## Problem Anchor

> 在冻结的 multi-step GUI published trajectories 中，是否存在如下可观察表型：decision point 前的 observation/history 出现了与 `p_old` 不相容的 `p_new`；outcome-independent normative schema 表明两者对应不同的正确动作或 obligation；后续可观察 action/artifact 与 `p_old` 相容、与 `p_new` 下的规范动作不相容；并且同一条预冻结 dependency chain 上伴随 terminal correctness deficit？该定义不主张 Agent 内部表示了 `p_old`，也不主张 `p_old` 导致了动作。

## Anchor Check

- 原问题不是“GUI Agent 长任务是否困难”；该事实即使成立，也不能定位 Memory。
- 原问题不是“现有 memory 是否缺少一个字段”；字段缺失不等于能力缺失。
- Step 1 只要求一个三段可观察链：`p_new` 已进入实际 history、后续外部行为仍与 `p_old` 相容、同一预冻结 dependency chain 上伴随终态义务未满足。
- `environment_transition`、`user_intent_revision`、`delayed_revelation` 与 `correction_of_prior_misinterpretation` 必须分开；不能把所有更新都称为环境证伪。
- “旧状态支配决策”“因此造成损失”和“长程是根因”均留待后续实验，不进入 Step 1 标签定义。
- 当前公开 highlighted cases 只能提示现象存在，不能估计自然目录负担。

## Must-solve Bottleneck

必须判断 action-time 所需状态是否具有三类可审计信息：

1. 哪个命题当前被依赖；
2. 支持该命题的证据与候选失效条件；
3. 命题失效后哪些动作、产物和义务必须撤销、重算或阻断。

但在证明现象负担与 R/P 边界之前，以上只能作为候选 capability decomposition。

## Non-goals

- 不把更长 context、更多 reflection 或更大模型预设为解决方案；
- 不把 OSWorld 2.0 目录比例外推到生产发生率；
- 不估计 action contract 的 preventable fraction；
- 不在当前轮写方法级 `FINAL_PROPOSAL.md`；
- 不用同系列代理的一致意见替代跨模型或实证判定。

## Success Condition for Round 0

Round 0 只在以下 Type-A 条件完成：

- 权威研究契约已写入且可恢复；
- Step 1 分母固定为 492 units；
- 数值阈值只有一个权威来源；
- 下一步 pilot 的输入、输出、盲化和停止条件明确；
- 两个独立角色已经直接审阅原始文件并留痕。

“问题重要”“Memory 是根因”“方法可行”均属于 Type-B 科学结论，不在 Round 0 自我放行。

## Method Thesis

**WITHHELD。** 在 Step 1 GO 之前不冻结方法 thesis。候选 action contract 仅作为之后可被 flat-state 对照否定的研究假设。
