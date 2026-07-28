# Round 8 — A0 Case Matcher 可识别性对抗

> 时间：2026-07-28  
> 位置：Step 1 measurement design  
> 参与角色：root、formal-spec designer、first-principles red-team、integration auditor  
> 最终裁决：**REJECT MATCHER FREEZE / REVISE MEASUREMENT DESIGN / NO RELIABILITY / NO BLOCK A / NO STEP 1 GO**

## 1. 问题不是“缺少 matching function”

当前 Stage A v2 的 94 个测试证明：

```text
给定 caller-supplied case partition
→ raw/case/path/primary/missingness 五账本可以保持内部一致
```

它不证明：

```text
raw labels
→ 哪些 labels 指向同一个现实事件
→ case denominator
```

当前 validator 只验证：

1. 每条 raw 恰好属于一个自报 case；
2. `case_id` 是该 case raw ids 的 hash；
3. case 内 agreement 与被放入该 case 的 raws 一致。

`matching_sha256` 虽存在于 common schema，但 full-block validator 没有读取或绑定真实 matcher executable。输出也明确是：

```text
SELF_SEALED_CASE_PARTITION_SYNTAX_ONLY
NOT_ESTABLISHED_NO_FROZEN_CASE_MATCHER
```

## 2. Round 1：maximum-cardinality 是否足够

形式设计者最初提出 exact anchor、maximum-cardinality 与 deterministic tie-break。Root 与 red-team 给出两个反例。

### 2.1 Greedy 会直接改变 denominator

令：

```text
A = {a1, a2}
B = {b1, b2}
E = {a1-b1, a1-b2, a2-b1}
```

greedy 若先取 `a1-b1`：

```text
a=1, b=1, c=1
positive agreement = 2a / (2a+b+c) = 0.5
```

maximum matching 取 `a1-b2, a2-b1`：

```text
a=2, b=0, c=0
positive agreement = 1.0
```

所以 maximum-cardinality 是必要条件。

### 2.2 Maximum-cardinality 仍不充分

构造 `K2,2`：

```text
A1=X, A2=Y
B1=X, B2=Y
四条边均 admissible
```

两个 maximum matchings 的 cardinality 都是 2：

```text
aligned: (A1,B1), (A2,B2) → 2 exact agreements
cross:   (A1,B2), (A2,B1) → 0 exact agreements
```

因此：

```text
deterministic tie-break
→ 只能保证 reproducibility
→ 不能赋予 semantic validity
```

只要 optimal matchings 对任一下游 estimand 不同，就不能选一个进入 primary。

## 3. Round 2：exact semantic anchor 是否足够

形式设计者提出用预冻结：

```text
(update evidence atom, target state variable, boundary location)
```

作为 exact match anchor。

Root 与 red-team 反驳：

1. anchor universe 的构造者可能已经替 A0 完成 event detection；
2. 当前截图 evidence pointer 只能定位整份 observation，不能证明 atom 完整；
3. exact-anchor mismatch 会把 referential disagreement 伪装成两个 singleton；
4. 一个 update 影响多个 variables 时，固定原子化会制造虚假多事件；
5. annotator 新发现但不在 anchor universe 的事件可能被静默删除。

形式设计者接受反驳并撤回强版本。最终共识：

- anchor 只能作为 pairwise identity evidence；
- 不能用于过滤 raw roster 或完整 pair universe；
- unanchored discoveries 必须保留；
- anchor-universe completeness 需要独立外部 authority，当前没有。

## 4. Round 3：一对一 matching 的结构边界

red-team 构造 split/merge：

```text
Annotator A: 一个 coarse event {O1,O2}
Annotator B: 两个 atomic events {O1}, {O2}
```

不同处理产生：

```text
三条 raw 合并为一 case → C=1
任取一对 + singleton  → C=2
拆分 A raw            → 制造不存在的 annotation
```

若只有一个 positive，burden 可从 `1/1` 变为 `1/2`。

结论：

```text
1:n / n:1 / n:m component
→ 不是 tie-break 问题
→ 是 event atomicity / segmentation 不可识别
→ 整个 component 必须 unresolved + bounds
```

图论上的 mandatory edge 也不能从含 ambiguous、split/merge 或 non-atomic relation 的 component 中抽出来进入 primary。

## 5. Round 4：实现审计发现的两个直接矛盾

### 5.1 Both-zero 被删除

当前 `test_e10_empty_submissions_no_event_location` 允许：

```text
两位 annotator 均提交 empty roster
valid = true
C_cases = 0
agreement = []
```

协议却要求双方均无 event 的合法 location 是 negative agreement。

这会从 negative-agreement denominator 删除 `d`，导致 reliability spectrum bias。

本轮已修复：

- 每个 both-zero location 派生一条 location-level agreement row；
- `case_id=null`，不制造 fake event case；
- `agreement_status=raw_negative_agreement`；
- `agreement_scope=LOCATION_OPPORTUNITY_PRESENCE_ONLY`；
- `a=b=c=0,d=1`；
- authority 仍明确是 `SELF_SEALED_EMPTY_ROSTERS_SYNTAX_ONLY`。

### 5.2 Independent paths 偷带 primary

协议规定：

```text
无预冻结 case-level aggregator
→ independent paths 全部 sensitivity_only
```

但实现曾从既有 final label 的 `p_new` 选择一个 raw 作为 primary，并期待：

```text
E_primary_rows = 1
roles = {primary, sensitivity_only}
```

同一两条 paths 若 A1 分别为 false/true，交换 primary 即可改变主结论，而 R/C/P/A1 数据不变。

本轮已修复：

```text
primary_event_id = null
全部 paths = sensitivity_only
E_primary_rows = 0
```

任何 primary role 注入继续由现有 exact-stage negative test fail closed。

## 6. Typed-invalid 的隐藏不可达状态

当前 submission schema 只允许 schema-valid typed raw；malformed raw 会在进入 R/C/M 前使整个 artifact 失败。

同时，`case_status=typed_invalid` 虽写在 case schema 中，所有 substantive rejection 又先被 `SEM_A0_REJECTION_UNAVAILABLE` 拒绝。

因此当前 typed-invalid 正向路径不可达：

```text
raw bytes
→ schema parse failure
→ raw envelope 未进入 R
→ M denominator 也不存在
```

必须先引入 content-addressed raw envelope，令 parse-invalid bytes 仍具有稳定 ID、error codes 与 M disposition。

## 7. 三方最终共识

### 7.1 不能直接实现的方案

以下方案均被否决：

- embedding similarity threshold；
- exact semantic-payload matching；
- raw-ID lexicographic tie-break 进入 primary；
- caller-supplied candidate edges；
- 在 ambiguous component 中抽一个 canonical matching；
- 用 anchor universe 删除 unanchored discoveries；
- 把 local `matching_sha256` 当作 pre-reveal authority。

### 7.2 必须先建立的上游对象

1. `raw_event_identity_envelope.schema.json`
2. `stage0f_a0_pairwise_identity_partial_identification_spec.md`
3. 两位独立 identity reviewers 的 pairwise judgments；
4. matcher role/exposure isolation；
5. external pre-A0 raw-roster receipt；
6. typed-invalid raw-envelope preservation；
7. split/merge 与 non-unique matching bounds；
8. explicit both-zero location receipt。

### 7.3 当前 claim ceiling

```text
NOT_ESTABLISHED_NO_MATCHABLE_RAW_IDENTITY
NOT_ESTABLISHED_NO_FROZEN_CASE_MATCHER
NO RELIABILITY
NO SYNTHETIC FREEZE
NO BLOCK A
NO STEP 1 GO
```

即使未来 synthetic matcher mechanics 全绿，最多只能得到：

```text
SYNTHETIC_PARTIALLY_IDENTIFIED_MATCHER_MECHANICS_ONLY
```

它仍不能证明自然 UACF-D burden。

## 8. Round 4：规范窄接受，实现继续 REVISE

在 Round 3 的直接反例后，本轮新增：

- `stage0f_raw_event_identity_envelope.schema.json`；
- `stage0f_pairwise_identity_review_packet.schema.json`；
- `stage0f_a0_pairwise_identity_partial_identification_spec.md`；
- 9 个 raw-envelope tests 与 5 个 identity-packet tests。

规范文本已关闭五个概念漏洞：

1. reviewer 只读 estimand-blind packet，不读完整 substantive envelope；
2. `L_all/R_all`、typed 与 invalid roster 分离，pair coverage 不丢 raw；
3. bounds 遍历所有 `G_minus ⊆ G ⊆ G_plus` graph completions 及所有合法 correspondences；
4. split/merge component 输出 `SEGMENTATION_ESTIMAND_UNIDENTIFIABLE`，禁止伪造 one-to-one numeric upper；
5. 同一 raw 有多个 `SUPPORTED_SAME` partner 时输出 `CERTAIN_RELATION_NONFUNCTIONAL`，不得由 optimizer 暗选。

formal-spec reviewer 因而给出：

```text
PAIRWISE PARTIAL-IDENTIFICATION SPEC = NARROW ACCEPT
SCHEMA SHAPE MECHANICS = NARROW ACCEPT
IDENTITY AUTHORITY = NOT ESTABLISHED
MATCHER IMPLEMENTATION = ABSENT
MATCHER FREEZE = NO
```

该接受只针对概念规范与封闭 schema shape，不是对可执行 redaction、identity authority、reliability 或 matcher freeze 的接受。

## 9. 可执行反方仍然击穿 reviewer-blindness

red-team 构造 schema-valid packet，把 substantive information 编入允许的值通道：

```text
artifact_id
pair_id
raw_envelope_ref.artifact_id
selector.node_id
atomicity_evidence_ref.artifact_id
projection hashes
```

同样 schema-valid 的攻击还包括：

- left/right 指向同一 raw；
- reversed temporal interval；
- duplicate evidence atoms；
- arbitrary pair id；
- raw envelope 中 reversed text span；
- blank state statement 与任意 statement hash；
- evidence selector 由 substantive labeler 按 `p_new` 选择，形成循环泄漏。

因此 `forbidden_field_names` 只证明字段名闭合，不证明信息流盲化。下一实现必须使用 packet-local CSPRNG aliases，把真实 refs 放入 reviewer 不可见 sidecar，并机械重算：

```text
raw input bytes
→ frozen redactor executable
→ exact identity-only projection
→ reviewer packet bytes
→ packet hash
```

还必须验证 cross-annotator membership、unit/location、interval/selector/cutoff、raw bytes/hash/parser/envelope id 与 reviewer session isolation。

## 10. 本轮可执行修复与验证

当前 validator 已对无冻结 aggregator 的 independent paths 强制：

```text
R=2
C=1
P=2
E=0
M=1
missingness=INDEPENDENT_PATHS_NO_FROZEN_AGGREGATOR
```

注入一个 primary path 会精确失败：

```text
SEM_A0_INDEPENDENT_PRIMARY_WITHOUT_AGGREGATOR
```

Both-zero location 现在显式产生 `d=1` 的 location-opportunity row，不制造 fake event case。最终 root 回归：

```text
Stage A + identity drafts + protocol/detail/ARIS  118/118 PASS
archived adapter + bounds mechanics               55/55 PASS
```

这些结果只关闭 synthetic C-P-E-M 记账漏洞，并验证两个 draft schema 的 shape；两个新 schema 尚未进入主 artifact loader、barrier、pair ledger 或 downstream bounds gate。

## 11. 下一轮顺序

```text
packet-local alias + executable redactor
→ cross-artifact raw-envelope semantic verifier
→ complete L_all × R_all pair ledger
→ dual independent reviewer receipts and session isolation
→ G_minus / G_plus + all-completion bounds
→ independent-path M mandatory bounds consumer
→ role/exposure/barrier integration
→ full executable battle
```

在这条链通过前，不得把 `agreement_completeness`、reliability、Block A 或 Step 1 状态升级。
