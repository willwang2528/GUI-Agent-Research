# Stage 0F Production Authority Gap Report

> status: **PARTIAL OFFLINE CAPABILITY / NO PRODUCTION CLOSURE**  
> evidence date: `2026-07-28`  
> claim ceiling: **NO SYNTHETIC FREEZE / NO BLOCK A / NO STEP 1 GO**

## 1. 第一性判据

环境可证伪的 measurement 不能只证明 packet 内部一致。它必须同时建立：

```text
published bytes 确实是所声称的环境记录
commit 确实发生在 reveal 之前
所有访问均被完整捕获
语义结论确实由证据或盲化人类测量支持
frame / identity / obligation / mapping universe 未被 outcome 后改写
```

对应五类 authority：

1. content fidelity；
2. temporal precedence；
3. capture completeness；
4. semantic derivation；
5. universe externality。

任一类为 `UNAVAILABLE` 或 `INVALID`，production overall 必须为 false；不能用其余四项补偿。

## 2. 当前真实数据面

- 48/48 frozen OSWorld2 detail HTML pages 存在；
- 47/48 含 replay payload；
- 1/48 是 explicit no-step；
- 共 9,138 steps；
- 47/47 replay pages 有 timestamp 与 action label；
- 45/47 的每一步有 screenshot URL；
- screenshot bytes 未保存，URL 存在不等于 asset verified；
- 9,138 raw-action blocks 中只有 2 个能被当前 strict JSON parser 解析；
- 六份 catalog endpoint snapshots 各含 108 个唯一 task ids；
- 六份 roster 与 instruction 一致；
- snapshot 声称 `benchmark_version=v2026.06.24`；
- 按冻结 split 可得到 82 tasks × 6 configs = 492 units。

这些事实证明 local snapshot availability，不证明官方 release identity、outcome truth、semantic transition 或实验时序。

## 3. 五类 authority

### 3.1 Content fidelity

已有：

- HTML/API bytes；
- per-file SHA-256；
- detail tree hash；
- page root 与 frozen filename identity；
- availability parser。

缺失：

- registered OSWorld2 deployed-page parser；
- deployed grammar 对应的 exact official code revision；
- screenshot bytes；
- URL→captured-byte 的外部 timestamp/notary；
- pre-action observation alignment。

当前可做：

```text
archived HTML bytes
→ registered parser
→ literal replay projection
→ explicit asset/timeline missingness
```

允许的结论：

```text
REAL_ARCHIVED_SOURCE_PROJECTION_VERIFIED
OBSERVATION_ASSET_AUTHORITY_PARTIAL
PRODUCTION_AUTHORITY_INCOMPLETE
```

禁止写成完整 environment observation fidelity。

### 3.2 Temporal precedence

已有：

- self-reported timestamps；
- internal hash chains；
- declared commit/reveal order。

缺失：

- external append-only receipt；
- trusted monotonic clock；
- inclusion/consistency proof；
- nonrollback reveal controller。

当前历史不能离线补证。未来实验必须在任何 annotation/reveal 前先部署 receipt infrastructure。

### 3.3 Capture completeness

已有：

- self-reported exposure ledger；
- alias-level role registry/history。

缺失：

- platform-enforced ACL；
- complete external access log；
- genesis-to-tip checkpoint proof；
- stable principal credentials；
- cross-block role-history consistency proof。

空日志只能证明“没有提交违规记录”，不能证明“没有发生违规读取”。当前历史不能离线补证。

### 3.4 Semantic derivation

已有：

- literal action/timestamp fields；
- A1 closed primitive grammar；
- bounds event-ledger predicate mechanics；
- A0 evidence pointers。

缺失：

- release-tagged task/evaluator bytes；
- task hash manifest；
- screenshot bytes及 pre/post alignment；
- typed state predicate verifier；
- obligation/deadline/applicability projection；
- state→correct-action rule。

当前只能机械处理 literal action/subaction；不能从现有数据机械推出 `p_old`、`p_new`、`PURE_WORLD`、normative difference、terminal deficit 或 no-opportunity。

开放式 GUI semantics 必须走：

```text
two independent outcome-blind human labels
→ disagreement-preserving adjudication
→ reliability / adjudication-rate / uncertainty report
```

并标为 `HUMAN_ADJUDICATED_EVIDENCE`。

### 3.5 Universe externality

已有：

- captured 6 × 108 catalog snapshot；
- six-config identity；
- deterministic 82 × 6 split；
- frozen decision thresholds。

缺失：

- actual task-hash manifest bytes；
- verifiable release tag object；
- task→evaluator mapping；
- outcome-blind structural/site/app mapping receipt；
- canonical obligation denominator；
- single external commitment for config/task/unit/location mappings。

当前只可称 `CAPTURED_CATALOG_SNAPSHOT_AUTHORITY`，不能称 verified official release universe。

## 4. 统一 API 契约

```text
verify_production_authority(
  block_dir,
  authority_dir,
  expected_external_authority_root
) -> {
  content_fidelity: VERIFIED | UNAVAILABLE | INVALID,
  temporal_precedence: VERIFIED | UNAVAILABLE | INVALID,
  capture_completeness: VERIFIED | UNAVAILABLE | INVALID,
  semantic_derivation: VERIFIED | UNAVAILABLE | INVALID,
  universe_externality: VERIFIED | UNAVAILABLE | INVALID,
  overall_valid: boolean
}
```

约束：

```text
overall_valid = true
iff
五项全部 VERIFIED
```

任何状态不得由 caller-supplied boolean 决定，必须来自实际读取、执行和 external commitment matching。

## 5. 最小实现顺序

1. Stage A v2：修复 X62 disagreement censoring 与 X63 grounding overclaim；
2. 真实 archived HTML projection adapter；
3. captured catalog universe adapter；
4. forward-only temporal receipt infrastructure；
5. forward-only ACL/access/principal/role infrastructure；
6. release task/evaluator/screenshot authority；
7. integrated production full-block validator；
8. 最后才接 bounds production mode。

不能先把 synthetic bounds 接到真实数据再补 authority；那只会把内部一致性包装成 research evidence。

## 6. 当前裁决

| 对象 | 裁决 |
|---|---|
| archived HTML → literal replay projection | OFFLINE IMPLEMENTABLE |
| captured catalog → 648/492 frame | OFFLINE IMPLEMENTABLE |
| real temporal precedence for existing history | NOT RECOVERABLE POST HOC |
| complete access/identity/role proof for existing history | NOT RECOVERABLE POST HOC |
| full semantic/obligation derivation | DATA/AUTHORITY MISSING |
| full release universe | PARTIAL |
| production full-block PASS | REJECT / FAIL-CLOSED |
| Block A | REJECT |
| Step 1 | IN PROGRESS / BURDEN UNMEASURED |
