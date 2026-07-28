# Round 4 Adversarial Review：Measurement Identity, Missingness, and Causal Gate

> date: `2026-07-28`  
> review_independence: `same-family / role-separated / provisional`  
> objects: preregistration、decision card、Step 1.5、research contract、Stage-A schemas/validator、OSWorld detail availability  
> conservative_verdict: **NOT READY FOR BLOCK-A DRY RUN**  
> outcome_exposure: no real Stage-A packet、A1 label、Stage-B label 或 confirmatory outcome 被打开

## 1. Battle 参与对象

| Role | 任务 | 是否可自我放行 |
|---|---|---|
| `c0e_decision_impl` | C0-E、五维决策与题名上限 | 否 |
| `causal_cards_impl` | C1-R、R×P、C3/C4、Step 1.5 | 否 |
| `stagea_schema_impl` | coordinator/A0/A1/audit schemas、validator、负例 | 否 |
| `osworld_detail_audit` | 48-unit 详情页字段可获得性 | 否；且不得进入 Block A 盲标 |
| `round4_protocol_redteam` | 两轮只读反方审计 | 只给 provisional review |
| `decision_bounds_fix` | global upper 与 structural completion 修订 | 否 |
| root coordinator | 解释批评、提出 rebuttal、合并修订 | 否；已看 Block A provenance |

## 2. Round 1：反方为什么否决

反方没有把“schema 文件存在”当成 measurement valid。它指出四个致命断点：

1. **selection on target action**：generator/reference 可能先看到 stale action，再选择 candidate；A0 后续隐藏 action 无法消除候选集合的 outcome leakage。
2. **semantic identity circularity**：generator 先把 proposition/obligation/boundary 写入 candidate id，而这些字段本应由 A0 独立冻结；opaque hash 仍会锚定 A0 可接受语义。
3. **false optimistic upper**：reference-relative recall 明确不能排除共同漏检，却把 detected roster 当成总体 upper；因此低于门的 NO-GO 不成立。
4. **A0→A1 priming 与 omission 不可判定**：同 task 六模型 barrier 仍允许跨相似 task priming；单个 semantic action 不能证明 required action 在整个 deadline interval 内缺失。

另有十个重大问题：

- invalid source packet 被伪装成 factual source uncertainty；
- pure-world interface/task bounds 缺 same-event containment；
- generic C0-B/C0-C task-level upper 没有机械公式；
- structural dispersion 忽略 unresolved positive/deficit mass；
- “threshold frozen”与“protocol revising”状态冲突；
- `P=absent` 没有共同 consumer，R effect 可能被结构性设为零；
- Step 1.5 用 unknown 覆盖已知 hard FAIL；
- narrow branch 的执行边界不清；
- C3 closure 字段跨文档漂移；
- C4 的“frontier 或 scaling”与“frontier 且 scaling”冲突，且 pointwise CI 可结果后挑难度。

形式枚举显示五维表本身覆盖状态空间；真正错误在于输入量尚未被识别。形式穷尽不能补救错误 estimand。

## 3. Root rebuttal：哪些批评接受，哪些反驳

### 接受并修订

- rolling timeline 固定为 `o_k → commit boundary k → reveal a_k → o_(k+1)`；batch bundle 不可逐项拦截时整体视为一个 action。
- 身份拆为 pre-action `boundary_location_id` 与 A0 后的 semantic event id；generator semantics 不进入 A0。
- detected-roster upper 只作诊断；用于 NO-GO 的 upper 必须是全 82-task/492-unit worst case。
- source unknown 与 invalid measurement 分开。
- R×P 改为共同 consumer API 下的 `identity_no_propagation / flat_scan / dependency_graph_propagation`，每个 P arm 单独 manipulation/isolation。
- hard FAIL 优先输出 `BLOCKED`，unknown 另存 unresolved ledger。
- C3 使用唯一 closure schema；C4 同时要求 scaling interaction 与 frontier extension，并使用 simultaneous uncertainty。

### 提出两项反驳

1. **Block A 可见是否污染 confirmatory preregistration**：root 认为 Block A 是预先固定、永久排除的 development set；只要完整 exposure ledger、B/C/82-task holdout 未解封、final stack 在它们前冻结，Block A 可用于开发而不自动污染 confirmatory evidence。
2. **narrow branch 是否是死路**：root 认为 `NARROW_SCOPE_PROTOCOL_DESIGN_ONLY` 可以是合法终点；当前 frame 只允许写协议，不允许 Step 1.5 execution。未来执行必须使用独立新 frame 和新 preregistration。

## 4. Round 2：反方对 rebuttal 的裁决

反方接受上述两项 rebuttal：

- Block A 可以开发，但永远不能贡献 primary holdout/reliability evidence；若 B 后改 measurement stack，B 自动降为 development，只能用未见 C；C 后再改 blocking artifact 则无剩余 validation block。
- narrow branch 可以是 design-only 终点，不能恢复 broad GUI claim。

反方同时拒绝了两项初版修复：

### F2 仍需多事件身份

同一 observation ordinal 可能有多个 proposition/obligation。正确层次为：

```text
boundary_location_id
→ zero or more independent A0 raw labels
→ pre-A1 source-blind adjudicated_event_ids
→ A1 references frozen event id
```

`boundary_location_id` 必须绑定净化 prefix payload hash；不能把包含自身 ID 的完整 A0 input hash放进 preimage。A0 disagreement 必须在 action reveal 前解决，或保留互不改写的独立 A0→A1 paths。

### F4 必须升级为 full-block barrier

同 task barrier 防不了相似 task 间 priming。最终要求：

```text
whole block A0 labels + A0-only adjudication frozen
→ BLOCK_A0_BARRIER_FROZEN
→ any A1 reveal
→ all A1 frozen
→ BLOCK_A1_BARRIER_FROZEN
→ any Stage B
```

A0 pool 永远不能担任 A1/Stage B，也永远不能收到 candidate action。

## 5. Global upper 的第一性原理

对 phenomenon `g` 和 held-out task `t`：

```text
P_L_g(t) = 1
iff 至少一个 confirmed g-positive event

P_U_g(t) = 0
iff 存在覆盖六 configs、完整 timeline、完整 opportunity universe、
无 invalid/unresolved 且有 common-miss bound 的 global negative certificate

otherwise P_U_g(t) = 1
```

因此没有 common-miss certificate 时，`U_g_tasks` 可以等于 82。这会降低 NO-GO 能力，但不会把“未检测到”伪装成“不存在”。

interface upper 必须与同一 possible positive event 绑定，并逐 task 满足：

```text
I_L_g(t) <= P_L_g(t)
I_U_g(t) <= P_U_g(t)
```

structural C0-D/C0-E 不能独立给各 group 加上界；必须在共享 task/event/source/interface/deficit 约束的 feasible completion set `Z` 上裁决：

```text
SUPPORTED:
所有 z in Z 都通过 dispersion predicate

CONCENTRATED:
所有 z in Z 都失败

INCONCLUSIVE:
Z 中同时存在 pass completion 与 fail completion

UNIDENTIFIABLE:
provenance/mapping/schema 缺失，无法构造 Z
```

## 6. 当前实现与证据上限

已机械复核：

- ARIS 666-file local snapshot verifier：PASS；只证明本地 content identity。
- OSWorld Block A expected detail frame：48/48。
- embedded replay：47/48；Task 050 × MiniMax 明确 `No step data available`。
- embedded steps：9,138；47/47 有 timestamp/label；45/47 每步有 screenshot URL。
- raw-action blocks：9,138 present，严格 JSON 仅 2/9,138 parseable。

这些结果只证明 local snapshot 和字段可获得性，不证明：

```text
UACF-D
pure-world burden
faithful replay
Memory root cause
action contract efficacy
capability-boundary change
```

Stage-A schema/validator 正在按 Round 4 的 multi-event identity、rolling commit、full-block barrier 与 omission interval 重建。任何旧版 synthetic PASS 都不能覆盖新反例。

## 7. 解除 NOT READY 的最低条件

1. protocol、schemas、validator 对 `boundary_location_id → multiple A0 events → block barrier → A1` 完全一致；
2. rolling-prefix 和 batch-tool 微时序有独立负例；
3. omission interval 的 action-presence ledger 完整且不含 deadline 后 outcome；
4. invalid source、common miss、global task/interface/deficit upper 与 feasible structural completions 可机械执行；
5. Draft 2020-12 meta/schema validation、duplicate-key、semantic/hash-chain/exposure validation全部 fail-closed；
6. project dependency lock 可重建；临时 venv 不能冒充 final freeze；
7. fresh protocol reviewer 与 fresh implementation reviewer 都给出 `READY FOR SYNTHETIC DRY RUN`；之后仍只能先跑 synthetic，不是直接生成真实 Block A packets。

## 8. 当前科学裁决

```text
STEP 1 IN PROGRESS
FRAME-READY
DETAIL-AVAILABILITY-PARTIAL
MEASUREMENT IMPLEMENTATION NOT READY
ROUND 4 NOT READY FOR BLOCK-A DRY RUN
```

本轮最重要的结果不是“方法更完整”，而是阻止了一个错误证明链：

```text
schema passes
does not imply
candidate selection is outcome-blind
does not imply
global absence is identified
does not imply
the GUI Memory problem is established
```
