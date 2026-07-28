# Stage 0F A0 Pairwise Identity 与 Partial Identification 规范

> status: **DRAFT / REVISE / NOT FROZEN**  
> scientific role: 为 A0 raw case formation 定义可被攻击的上游规范  
> claim ceiling: **NO RELIABILITY / NO BLOCK A / NO STEP 1 GO**

## 1. 第一性问题

两个 raw labels 能否形成同一个 case，取决于它们是否指向同一个原子事件。

这不是纯图算法问题：

```text
现实事件 identity
→ pairwise same-event judgment
→ admissible correspondence graph
→ case partition / bounds
```

Maximum matching 只能在已知边上优化，不能证明边的语义正确。

## 2. 输入冻结

每个合法 location 必须在两份 A0 raw submissions 完成之后、任何 candidate action、A1 或 outcome reveal 之前冻结：

1. 两份独立 raw-envelope rosters `L` 与 `R`，允许为空；
2. 每个 raw envelope 的原始 bytes/ref/hash；
3. parse status、typed semantic projection 或 parse errors；
4. optional identity evidence、atomicity claim 与 unanchored-discovery status；
5. 两个不同 principal commitments；
6. A0 input、schema、codebook、matcher-spec hashes；
7. matcher actors、role history、access ledger；
8. external append-only raw-roster receipt、complete-search attestations 与 trusted time。

若只存在 alias 与本地 hash，authority 必须保持 partial。

## 3. Raw identity envelope

Raw ID 必须绑定：

```text
unit
+ boundary
+ principal commitment
+ original raw bytes hash
+ parse status
+ identity evidence
+ atomicity claim
+ substantive payload or parse-error roster
+ schema/codebook/matcher-spec versions
```

未锚定事件不得删除：

```text
unanchored discovery
→ retained raw envelope
→ identity authority partial
→ unresolved / bounds
```

Raw identity envelope 是 coordinator/verifier artifact，不是 identity reviewer 的可见输入。Reviewer 只能读取由独立 redaction executable 生成的 estimand-blind identity-review packet。

该 packet 可以包含：

- opaque raw-envelope ref；
- pre-action observation evidence atoms 与 fine-grained selectors；
- evidence temporal interval；
- independent atomicity question；
- redaction policy、executable 与 input/output hashes。

它必须排除：

- `p_old`、`p_new`；
- update-source labels；
- normative-action difference；
- affected obligations；
- boundary-type label；
- raw typed projection；
- annotator 的 state-variable statement；
- candidate action、A1 与 outcome。

否则 matching 会条件化于待评估的 substantive agreement，并把 disagreement 变成 singleton。

## 4. Complete pair universe

先区分：

```text
L_all, R_all         = 全部 externally committed raw envelopes
L_typed, R_typed     = parser-valid envelopes
L_invalid, R_invalid = parser-invalid envelopes
```

Typed-invalid envelopes 必须留在 R/M，但不交给 identity reviewer。机械 pair ledger 为：

```text
P_review  = L_typed × R_typed
P_invalid = (L_invalid × R_all) union (L_all × R_invalid)
```

`P_review` 中每个 pair 必须被判断；`P_invalid` 中每个 pair 必须写 `NOT_COMPARABLE_TYPED_INVALID`。两者合并后才覆盖完整 `L_all × R_all`。

以下情况无效：

- 只输出 accepted edges；
- 由 similarity threshold 先过滤 pair；
- 用 anchor roster 删除 unanchored raw；
- 同一 annotator 内建边；
- 同一 raw 出现在多条 selected edges。

## 5. Independent pairwise identity review

每个 `P_review` pair 由两位独立 identity reviewers 判断：

```text
SAME_ATOMIC_EVENT
DIFFERENT_ATOMIC_EVENT
SPLIT_MERGE_OR_NONATOMIC
INSUFFICIENT_IDENTITY_EVIDENCE
```

Reviewers 必须：

- 与 A0 labelers、A0 adjudicator、A1、Stage B 永久隔离；
- 只读取 pre-action A0 artifacts 与 estimand-blind identity-review packets；
- 禁止读取 full raw identity envelope、raw typed projection 或 raw source label bytes；
- 不读取 candidate action、outcome、score、status 或真实模型 identity；
- 各自绑定 principal、input refs/hash、judgment 与 frozen time。

聚合：

```text
两位均 SAME
→ DUAL_REVIEWER_CONCORDANT_SAME

两位均 DIFFERENT
→ DUAL_REVIEWER_CONCORDANT_DIFFERENT

其余
→ AMBIGUOUS
```

`DUAL_REVIEWER_CONCORDANT_SAME` 仍不是语义事实。只有独立 evidence/selector verifier、atomicity authority 与 reviewer-independence authority 全部 VERIFIED 时，才能升级为 `SUPPORTED_SAME`。否则该 edge 只进入 upper graph。

第三方 adjudication 不能把 identity disagreement 覆盖成 primary certainty。若同一 raw 对多个 partners 都得到 `SUPPORTED_SAME`，relation 为 nonfunctional conflict；optimizer 不得替 protocol 选择其中一个，整个 component 进入 unresolved。

## 6. Lower 与 upper correspondence graphs

构造：

```text
G_minus = SUPPORTED_SAME edges
G_plus  = SUPPORTED_SAME
          + DUAL_REVIEWER_CONCORDANT_SAME with partial authority
          + AMBIGUOUS edges
```

必须机械验证：

```text
G_minus subset G_plus subset P_review
```

只有无 split/merge/non-atomic flag 且 same relation functional 的 component 才进入 one-to-one graph calculation。若一个 component 含 `SPLIT_MERGE_OR_NONATOMIC`，必须输出：

```text
SEGMENTATION_ESTIMAND_UNIDENTIFIABLE
```

不能用 one-to-one maximum matching 为该 component 生成 numeric event-level agreement upper。

对其余 component 分别计算 maximum-cardinality，并附 minimum vertex-cover certificate。禁止 greedy。

## 7. Tie-break 与 all-optima

UTF-8 raw IDs 可以选出一个 canonical maximum matching，但仅用于：

```text
SENSITIVITY_REPRESENTATIVE_ONLY
```

它不得决定：

- primary case partition；
- adjudication input；
- point agreement；
- primary prevalence；
- E ledger。

`AMBIGUOUS` edge 既可能存在也可能不存在。合法 completion space 为：

```text
all graphs G such that
G_minus subset G subset G_plus
and G satisfies functional/non-segmentation constraints
```

对每个 graph completion 的全部合法 correspondences 计算依赖 pairing 的 estimand `T`：

```text
T_min = minimum over all graph completions and correspondences
T_max = maximum over all graph completions and correspondences
```

不能只枚举固定 `G_plus` 的 maximum matchings；那会遗漏 ambiguous edges 全部为假的 completion。只有 `T_min == T_max` 时才允许报告 point estimate。即使统计量 invariant，也不能把含语义 ambiguity 的 component 升级为 primary event identity。

## 8. Primary-safe component

只有同时满足以下条件才允许 paired primary-eligible case：

```text
component 恰有 1 个 L raw 与 1 个 R raw
唯一 pair 为 SUPPORTED_SAME
两条 raw 均有 typed identity + atomicity authority
无 AMBIGUOUS incident pair
无 split/merge flag
无 typed-invalid 或 unanchored raw
```

其余 component 全部保留：

| Component | Status |
|---|---|
| `1:n` / `n:1` | `SPLIT_MERGE_AMBIGUITY` |
| `n:m` / K2,2 | `PARTNER_IDENTITY_AMBIGUITY` |
| 多 optimum 且 estimand 不同 | `NONUNIQUE_MATCHING` |
| reviewers disagreement | `IDENTITY_JUDGMENT_DISAGREEMENT` |
| identity evidence 不足 | `IDENTITY_AUTHORITY_PARTIAL` |
| 同一 raw 的多个 supported partners | `CERTAIN_RELATION_NONFUNCTIONAL` |
| typed-invalid raw | `TYPED_INVALID_RETAINED` |

整个 ambiguous connected component 进入一个 unresolved case 与 M；不得从中选择一对 primary。

## 9. Singleton

只有某 raw 与另一侧全部 `P_review` pairs 均为 `DUAL_REVIEWER_CONCORDANT_DIFFERENT`，且 reviewer-independence 与 input authority VERIFIED 时，才能成为 certifiable singleton：

```text
L-only → b
R-only → c
```

若存在任一 `AMBIGUOUS`、partial-authority 或 typed-invalid counterpart，该 raw 进入 unresolved component，不得写成 singleton。

Singleton：

- 保留在 case/agreement/missingness denominator；
- 不得变成 consensus；
- 不得产生 primary A1 event；
- 不能被 substantive adjudicator 删除。

## 10. Both-zero

若两份 externally committed rosters 与 complete-search attestations 均证明为空：

```text
case count = 0
agreement row count = 1
status = raw_negative_agreement
scope = LOCATION_OPPORTUNITY_PRESENCE_ONLY
a=0,b=0,c=0,d=1
```

`d` 不是开放世界 event-level true-negative count。

若 empty rosters 只有本地 self-sealed authority：

```text
ZERO_ZERO_AUTHORITY_UNESTABLISHED
```

该 row 可用于结构审计，但不得进入 production reliability。

## 11. Positive agreement bounds

对 one-to-one estimand 已定义的 component，分别在全部合法 graph completions/correspondences 上计算：

```text
a_lower = minimum matched-event count
a_upper = maximum matched-event count
b_lower / b_upper = corresponding L-only extrema
c_lower / c_upper = corresponding R-only extrema
```

若 positive mass 非零：

```text
agreement_lower
= 2*a_lower / (2*a_lower + b_upper + c_upper)

agreement_upper
= 2*a_upper / (2*a_upper + b_lower + c_lower)
```

若分母为零，输出：

```text
NOT_APPLICABLE_ZERO_POSITIVE_MASS
```

不能把它记为 1。

## 12. Typed-invalid preservation

Schema-invalid typed projection不能使原始 submission 从 denominator 消失。

必须先保存：

```text
raw bytes/ref/hash
→ raw envelope id
→ parse status + error codes
→ R roster
→ typed-invalid disposition
→ M / bounds
```

Typed-invalid raw 不进入 reviewer correspondence graph，但必须进入 `P_invalid`、raw-envelope coverage、missingness 与 worst-case burden bounds。

## 13. Required output axes

禁止用一个 optimistic 状态隐藏多个 authority：

```text
matcher_mechanics
raw_roster_authority
identity_review_redaction_authority
identity_judgment_authority
atomicity_authority
reviewer_independence_authority
correspondence_identifiability
anchor_universe_authority
primary_reliability_eligibility
```

Downstream agreement 与 prevalence calculator 只能消费 frozen matcher receipt，不得直接消费 adjudicator 自报 `case_roster`。

## 14. Fail-closed registry

至少需要：

```text
HASH_A0_MATCHER_EXECUTABLE
HASH_A0_MATCHER_SPEC
SEM_A0_MATCHER_INPUT_ROSTER
SEM_A0_MATCHER_EDGE_UNIVERSE
SEM_A0_MATCHER_MAX_CARDINALITY
SEM_A0_MATCHER_TIEBREAK
SEM_A0_MATCHER_PARTITION
SEM_A0_MATCHER_AMBIGUITY_STATUS
SEM_A0_MATCHER_RELATION_NONFUNCTIONAL
SEM_A0_MATCHER_NONUNIQUE_PRIMARY_LEAK
SEM_A0_SPLIT_MERGE_PRIMARY_LEAK
SEM_A0_SEGMENTATION_ESTIMAND_BYPASS
SEM_A0_IDENTITY_REVIEW_SUBSTANTIVE_LEAK
SEM_A0_BOTH_ZERO_WITHOUT_AUTHORITY
SEM_A0_RAW_ENVELOPE_COVERAGE
SEM_A0_TYPED_INVALID_ERASURE
SEM_A0_MATCHER_BARRIER_FREEZE
SEM_A0_MATCHER_ORDER
EXPOSURE_A0_MATCHER_CONTRACT
SEM_DOWNSTREAM_AGREEMENT_GATE_BYPASS
```

## 15. 当前裁决

当前没有：

- matchable raw identity envelope；
- estimand-blind identity-review packet；
- independent pairwise identity judgments；
- external raw-roster receipt；
- matcher role/exposure isolation；
- all-optima bounds verifier。

因此：

```text
NOT_ESTABLISHED_NO_MATCHABLE_RAW_IDENTITY
NOT_ESTABLISHED_NO_FROZEN_CASE_MATCHER
NO RELIABILITY
NO BLOCK A
NO STEP 1 GO
```

本文件必须先经独立 executable red-team，才能进入 implementation。
