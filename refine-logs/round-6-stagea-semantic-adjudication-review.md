# Round 6：Stage A Adjudication 与 Evidence Grounding Battle

> status: **REVISE**  
> scientific ceiling: **NO SYNTHETIC FREEZE / NO BLOCK A / NO STEP 1 GO**  
> scope: Stage A v1 protocol adequacy，不重新审计已接受的 bounds synthetic mechanics

## 1. 初审

fresh reviewer 不调用既有 test 方法，独立构造并重签 clean、X58、X59、X60、合法 source-label disagreement 与 production fail-closed cases：

```text
clean synthetic full block: PASS
X58: SEM_A0_RAW_SUPPORT_SEMANTICS
X59: SEM_A0_CHILD_FREEZE_ORDER
X60: SEM_ROLE_ASSIGNMENT_INTERVAL
source-label disagreement: PASS / MIXED_WORLD
production ontology_block_a: SEM_PRODUCTION_EXTERNAL_AUTHORITY_UNAVAILABLE
```

该结果接受 X58–X60 局部回归防线，但不能自动接受 Stage A protocol。

## 2. 主线程反驳：X62

预注册要求任意 substantive A0 disagreement 在 reveal 前经 source-blind adjudication，或保留两条独立、不可回改的 A0→A1 paths。

主线程构造：

```text
X62-A:
一位 raw p_new 与另一位不同
保留两位 support并重签
→ SEM_A0_RAW_SUPPORT_SEMANTICS

X62-B:
第三方拒绝一位，保留另一位
→ SCHEMA_INSTANCE_INVALID
→ supporting_a0_raw_label_ids / support_semantic_payloads minItems=2
```

fresh reviewer 独立复放后撤回对 Stage A adequacy 的宽泛 `ACCEPT`。

第一性根因：

```text
v1 先要求五个核心字段完全一致
再把一致结果称为 adjudication

因此

adjudication 的输入空间
恰好排除了需要 adjudication 的 substantive disagreement
```

这会形成 consensus-only censoring，改变 reference-event denominator、incidence 与 generator recall。

## 3. 独立反方：X63

另一名 reviewer 构造共同错误但完全自洽的命题：

```text
p_new = PROP-MOON-IS-CHEESE
两位 raw annotators 相同
adjudicator相同
所有 IDs、refs、barriers 与 hashes 重算
evidence pointer 指向真实 observation
source bytes 不含 moon/cheese
```

实际：

```text
valid = true
derived source category = PURE_WORLD
mechanical claim = STRUCTURAL_VALIDATION_ONLY
```

第一性根因：

```text
hash 证明 bytes 未变
pointer 证明引用存在
agreement 证明多人结论相同

均不证明

evidence 蕴含 proposition
或 proposition 改变 normative action
```

## 4. 两个缺口为何正交

```text
只修 X62：
可以完整裁决分歧，但仍可能一致地裁决错误。

只修 X63：
证据可以真实，却仍会因为分歧无法进入协议而被删失。
```

## 5. Stage A v2 最低契约

### 5.1 Disagreement-preserving adjudication

- `adjudication_mode` 至少覆盖 `consensus / blinded_human_resolution / independent_paths / unresolved`；
- 每条 raw label 不可变且恰好处置一次；
- substantive disagreement 保存每个 raw value/hash、resolution、resolved value、adjudicator、rule/codebook hash 与时间；
- 单支持事件不得计入 inter-annotator agreement，但不得从 denominator 静默消失；
- unresolved 与 independent paths 必须进入 barrier、missingness 与 sensitivity audit；
- 删除 resolution、漏 raw、漏 path、reveal 后改判一律 whole-block FAIL。

### 5.2 Evidence grounding 分流

```text
grounding_mode = mechanical | blinded_human
```

mechanical：

- typed predicate；
- immutable source bytes；
- frozen parser/verifier；
- release-tagged task/evaluator rule；
- 可复算 verifier output。

blinded human：

- 两位独立 outcome-blind labels；
- 完整 raw evidence refs；
- X62-compliant adjudication；
- agreement、adjudication rate 与 uncertainty；
- 输出标记 `HUMAN_ADJUDICATED_EVIDENCE`；
- 不得称为机械环境证伪。

## 6. Production authority 审计

当前离线可真实实现但不能闭合 production 的只有：

1. archived OSWorld2 HTML → canonical literal replay projection；
2. captured catalog snapshots → 648/492 frame projection。

不能事后补造：

- external temporal receipts；
- platform complete access logs；
- principal identity commitments；
- role-history checkpoint consistency proofs。

仍缺：

- release-tagged task/evaluator authority；
- screenshot bytes与 pre/post alignment；
- task hash manifest；
- structural/obligation pre-outcome commitments。

因此下一顺序是：

```text
Stage A v2 adjudication/grounding
→ real archived-source projection adapter
→ captured catalog universe adapter
→ forward-only temporal/access infrastructure
→ integrated production battle
```

## 7. V2 spec red-team：denominator 不能由 disposition 代替

独立 reviewer 在冻结 v1 快照上构造 X64：

```text
两条 raw labels 保留
→ dispositions 改为 rejected
→ 删除对应 event 与 A1 path
→ A0/A1 counts 同步减一
→ 重签全部 refs/barriers/exposure
→ valid = true
```

因此 v2 必须分别冻结五个集合：

```text
R_l = raw labels
C_l = adjudication cases
P_l = required A0→A1 paths
E_l = unique primary event rows
M_l = unresolved / invalid / missingness records
```

最低不变量：

- 每个 raw 恰好属于一个 case 或 typed-invalid record；
- 每个 case 恰好一种 adjudication mode；
- 每个 required path 恰好一个 A1 label 或显式 missingness；
- 每个 case 最多一个 primary row；
- unresolved 不贡献 positive/negative，但必须进入 upper/sensitivity；
- agreement 从 pre-adjudication raw matcher 重算，不能从 adjudicated events 反推；
- singleton、human-resolved、independent 与 unresolved disagreement 都不能被改写成 consensus。

新增强制反例：

| ID | Mutation | Required result |
|---|---|---|
| V2-R01 | reject 两条 raw、删除 event/A1、减 counts | `SEM_A0_RAW_DENOMINATOR_LOSS` |
| V2-R02 | 同一 raw进入两个 cases/events | `SEM_A0_RAW_PARTITION_FANOUT` |
| V2-R04 | raw A=`(pA,oA)`、raw B=`(pB,oB)`，resolution=`(pA,oB)` | `SEM_A0_RESOLUTION_OUT_OF_SUPPORT` |
| V2-R05 | resolution 晚于 first A1 reveal | `SEM_A0_RESOLUTION_LATE` |
| V2-R06 | independent path缺一路并同步减 count | `SEM_A1_PATH_DENOMINATOR_LOSS` |
| V2-R07 | 两条 independent paths变成两条 primary rows | `SEM_INDEPENDENT_PRIMARY_DOUBLE_COUNT` |
| V2-R09 | unresolved case泄漏正/负结论 | `SEM_UNRESOLVED_PRIMARY_LEAK` |
| V2-R10 | disagreement经裁决后被计为 agreement | `SEM_AGREEMENT_POST_ADJUDICATION_INFLATION` |
| V2-R12 | mechanical mode只有 pointer/hash，没有 verifier execution | `SEM_MECHANICAL_GROUNDING_INCOMPLETE` |
| V2-R15 | independent paths共享 A1 reveal/label | `SEM_INDEPENDENT_PATH_ALIASING` |

即使全部内部不变量通过，production仍需要每位 annotator 在 adjudication 前取得外部不可回退的 raw-roster receipt；否则攻击者仍可在生成 bundle 前先删 raw，再重签整个世界。

## 8. 最终裁决

| 对象 | 裁决 |
|---|---|
| X58–X60 regression mechanics | ACCEPT |
| bounds synthetic mechanics | ACCEPT |
| Stage A v1 protocol adequacy | **REVISE** |
| X62 | CONFIRMED |
| X63 | CONFIRMED |
| X64 | CONFIRMED |
| synthetic measurement freeze | REJECT |
| production measurement | REJECT / FAIL-CLOSED |
| real Block A | REJECT |
| Step 1 | IN PROGRESS / BURDEN UNMEASURED |
