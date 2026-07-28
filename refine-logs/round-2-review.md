# Round 2 Adversarial Review

> date: `2026-07-22`  
> review_independence: `same-family`  
> acceptance_status: `provisional`  
> conservative_verdict: `REVISE`

## Review Routes

| Reviewer | Verdict | Strongest remaining rejection |
|---|---|---|
| `oracle_protocol_reviewer` | REVISE | `p_old` 仍可后见构造；update taxonomy 不互斥；Step 1.5 无数值与真值表；C1-R 未必可分离 |
| `aris_fresh_reviewer` | REVISE | union-relative recall 不是事件召回率；随机 step audit 对稀有事件可能假 PASS；B/C 分支和 Step 1.5 存在结果后自由度 |

## Battle Result

第一轮的核心拒稿是 construct circularity；第二轮两位审稿者都认为该问题已经关闭。新的最强拒稿变成 measurement denominator：两个 generator 可以共同漏掉稀有 update opportunity，而 union-relative coverage 和 96 个随机 steps 仍然显得很好。这证明之前的“recall gate”估计了错误的量。

## Required Revisions Applied in v0.4/v0.3

1. `p_old` 必须从 pre-update 证据冻结并带 pointer；post-action 反推只能记 `old_state_hypothesized` 并排除出 primary。
2. update source 改为 factual multi-label 与冻结 primary precedence；`environment-falsifiable` 主分析只使用 `world_truth_changed`。
3. union-relative recall 改名 `inter-generator coverage`；第三方对未见 validation units 完整扫描 prefix，以 source-blind adjudicated reference events 作 recall 分母。
4. canonical event identity 使用 unit 内 `observation_ordinal + proposition + obligation`，不再混用 standard steps 与 batch-tool model steps。
5. B/B+C/C 路径在 Block B outcome 前自动冻结；cluster bootstrap 公式、重复数、seed 与 zero-positive 处理已固定。
6. structural/site partitions 改为互斥；singleton 不丢弃；`K_model_family >= 3`；raw mass、group rate 和 exposure-normalized share 并列报告。
7. 新增 Step 1.5 A–E 独立卡，冻结 identity、control repeats、manipulation、boundary isolation、coverage 与互斥真值表。
8. C1-R 在 planner tokens/instructions/policy 不可分离时只估计 `state-conditioning total effect`，不再冒充 R 的独立效应。
9. Step 1 主预注册删除重复 GO/NO-GO 规则，唯一决策源保留在 Step 1 decision card。

## Current Scientific Status

- observable construct：文本上已关闭第一轮泄漏，但尚未用真实 packets 执行；
- event-level recall protocol：已可定义，尚未执行；
- Step 1.5：已有冻结卡，当前 identity/replay/interface 全部未验证；
- Step 1 evidence：仍为 `IN PROGRESS`，不得宣称 Memory 根因或行动契约有效。
