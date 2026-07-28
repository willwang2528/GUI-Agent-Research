# Stage 0F Round 4b Bounds Mechanics 实现报告

> date: `2026-07-28`  
> scope: negative certificate、finite joint completion、C0-B/C/E bounds、structural completion mechanics  
> claim ceiling: **SYNTHETIC MECHANICS ONLY / MEASUREMENT IMPLEMENTATION NOT READY / NO SYNTHETIC FREEZE / NO BLOCK A / NO STEP 1 GO**

## 1. 两层结论，禁止混淆

### A. Synthetic trusted authority

本实现以调用方之外给出的 `expected_authority_sha256` 加载 synthetic fixture，
用于验证 X36–X40、X42、X44、X45、X49、X53–X57、X61 的机械抗篡改性质。它最多可在 fresh reviewer
通过后支持 `READY_FOR_SYNTHETIC_DRY_RUN`，不能证明真实 OSWorld frame、source
parser、exposure capture、streaming receipt 或 annotation blindness。

### B. Real full-block production authority

real full-block bounds adapter 尚未完成。当前没有路径把已经 PASS 的
`validate_full_block` 结果逐个重开物理 refs，并独立派生：

- exact `unit_alias ↔ task_id ↔ hosted_config_id/model_family_id ↔ ordinal/location`；
- A0 input 中规范义务集合及跨 ordinal 一致性；
- canonical adjudicated event、A1 phenotype/source/obligation 与独立 interface inventory；
- release-tagged structural/site-app codebook、outcome-blind pre-A1/Stage-B receipt；
- proof evidence projection 与真实 full-block roots。

因此 production 结论固定为 `NO BLOCK A`。synthetic authority 中形似
frame/manifest/barrier 的 hash 只是 fixture commitment，不是已经验证的真实
frame/source/exposure 证据。

## 2. 已实现的 synthetic mechanics

### 2.1 X36：negative proof 不再由调用方自证

- proof mode 绑定 frozen verifier registry、executable SHA-256 和 mode-config
  SHA-256。
- validator 加载真实 evidence bytes，检查 exact pointer object、bytes hash、
  projection role、顺序和 consumption 后，实际启动 frozen executable。
- verifier 完整输出逐字段与 artifact 比较；unknown mode、disabled mode、hash
  mismatch、execution failure、partial/forged output 一律 certificate `0`。
- 当前只有 `DETERMINISTIC_PREDICATE_EVALUATOR_FALSE_V1` enabled；transition
  与 typed-grammar 两种 mode 因缺少 sound raw-evidence semantics 明确 disabled。

### 2.2 X37：bounds packet 不能自封 universe

- API 必须接收由 trusted loader 构造的 `BoundsAuthority`；没有 authority 直接
  `BOUNDS_AUTHORITY_REQUIRED`。
- packet 的 holdout manifest、authority binding、derived event refs 必须与外部
  authority exact-match。
- 删除 ordinal、重新 seal roster/hash chain，或交换 unit identity 后重新 seal，
  仍因不匹配原外部 commitment 而 `UNIDENTIFIABLE`。

这只建立 synthetic fixture tamper resistance；它没有实现 real full-block adapter。

### 2.3 X38：same-event 结论由 source refs 派生

- input schema 禁止 caller 提交 `observed_joint_events`。
- synthetic event 由独立 A0、A1、candidate-interface refs 派生。
- event key 固定为
  `sha256(canonical_json(["stage0f-canonical-event-key-v1", task_id, unit_id, boundary_location_id, adjudicated_event_id]))`；
  evaluator 再次复算 serialization、preimage 和 hash。
- B、interface、source、unmet obligation 只在同一 derived event 内形成
  conjunction，然后在同一 location 做 OR；E23–E25 的跨 event/跨 location
  stitching 继续为 `0`。

### 2.4 X39：proof projection 是 exact sufficient set

- 每个 `(task, config, location, predicate, obligation, mode)` 由 authority 冻结
  ordered pointer IDs。
- 删除、替换、乱序、role/sequence mismatch、stale bytes 均 certificate `0`。
- event ledger 必须与同一组 frozen A0/A1/interface source artifacts 的 primitive
  projection 完全相等，不能由 ledger 自称 complete。

### 2.5 X40：completion witness 是结构世界，不是任意 bit assignment

- structural/site-app exposure 按 task 计；model-family exposure 按 task×config 计。
- `K_group ≥ 4`、`K_site/app ≥ 3`、`K_model ≥ 3`；K 只计 positive-mass partition。
- positive 与 deficit 在 structural/site/model 三类 partition 上分别计算
  exposure-normalized max share，共六项，均严格 `< 0.5`。
- deficit 来自 binary obligation bits；义务集合必须非空，structural/site 采用
  task-equal six-config mean。
- 每个 feasible completion 都重新计算完整统计，输出可核验 assignment、
  statistics 与 assignment hash。
- witness 对每个 partition/bucket 输出 raw positive/deficit mass、raw share、
  exposure、group-specific rate 与 exposure-normalized share；六个 max 可由这些
  有理数 provenance 独立复算。
- synthetic 4-task case 同时产生真实 `z_pass` 和 `z_fail`，所以 verdict 为
  `INCONCLUSIVE`；free variables 超过 frozen enumeration limit 且无 trusted
  solver certificate 时为 `UNIDENTIFIABLE`。

### 2.6 X42：禁止 boolean laundering

- enabled verifier 不读取 `predicate_values[target]=false`、`reachable=false`
  等目标结论。
- 它从 exact complete primitive event ledger 的 `p_old_status`、source labels、
  action assessment、candidate interface 和 obligation assessments 重新计算六类
  target predicate。
- ledger 增加 caller-supplied target boolean，即使重新计算 file hash 和 whole
  authority hash，也因不再是 frozen source projection 而被 loader 拒绝。

### 2.7 X49：structural partition rewrite fail closed

- structural mapping hash 是 external authority binding 的一部分。
- 原 expected authority hash 下，磁盘 remap 直接加载失败；加载后的普通 runtime
  remap 被递归 immutable view 立即拒绝，反射替换则由全量 runtime commitment
  在统计派生前 fail closed。
- 这只证明 commitment 后不可改写。production 仍需要 release-tagged provenance、
  冻结 codebook、独立 outcome-blind adjudication，以及 A1/Stage-B 前的外部 receipt。

### 2.8 X44：obligation denominator 不能由 packet 重签

- packet 将 Config-A 的 `O-PRIMARY` 换成 `O-FAKE` 并重新 seal manifest，
  仍因不匹配 synthetic external authority 而 `UNIDENTIFIABLE`。
- 这只验证 bounds packet 不能覆盖既有 commitment。real full-block adapter 尚未从
  每个 unit 的 A0 input `task_context.obligations` 机械派生、规范排序、去重并验证跨
  ordinal/config 一致性，因此 production obligation denominator 仍未建立。

### 2.9 X45：unit/task/config identity 不能由 packet 重分组

- 两个 tasks 之间交换 unit IDs 并重新 seal manifest，仍因不匹配 synthetic
  external authority 而 `UNIDENTIFIABLE`。
- 这只验证 commitment 后不可重分组。real full-block adapter 尚未从 frame 与
  coordinator envelopes 机械派生并 exact-match
  `unit_alias ↔ task_id ↔ hosted_config_id/model_family_id ↔ ordinal/location`，
  因此 production identity authority 仍未建立。

### 2.10 X53：loaded authority 不能在 runtime 被改写

- `BoundsAuthority` 的 binding、manifest、events、event refs、evidence assets、
  proof projections 和 structural mapping 全部递归冻结为 immutable views。
- 每次 `analyze_packet` 在读取任何 event/bound 前，对上述全量对象、evidence bytes
  hashes 与 current/cached event refs 重算一个 runtime commitment。
- 普通原地 mutation 立即抛出 `TypeError`；即使通过反射替换 private frozen snapshot，
  下一次分析也在派生 lower 之前以 `AUTHORITY_RUNTIME_COMMITMENT_MISMATCH` fail closed。

### 2.11 X54：A1 summary 与 primitive action 只有一个语义源

- grammar 与 phenotype truth table 位于独立 hashed semantic contract；
  loader 与 subprocess verifier 共同调用同一个 pinned interpreter，不再复制两份
  if/else。
- loader 从 `p_old_status + action_assessment` 机械重算 phenotype 与
  `primary_uacf_d_positive`，再 exact-match A1 summary fields。
- summary 声称 `target_positive`、primitive action 实际为 `target_negative` 时，
  即使 A1 bytes/ref/whole authority hash 全部重签，也在 event derivation 前拒绝。
- enabled negative verifier对 primitive event 使用三值逻辑：target `true` 或
  `unresolved` 都不能签 negative；只有完整 ledger 中每个 event 对目标均确定为
  `false` 才能签证。

### 2.12 X55：model-family codebook 不是任意 allowed enum

- exact codebook 冻结为 A/B/C→Anthropic、D→OpenAI、E→MiniMax、F→Qwen，
  并绑定独立 codebook hash。
- 即使把 A/D 对调后重签 structural mapping 与 whole authority hash，只要不与
  exact frozen codebook 相等，loader 即拒绝；evaluator 也重复 exact-match。

### 2.13 X56：malformed action 不能 fall through 为 negative

- primitive action 采用 closed exact grammar：五个 required keys、严格 boolean
  types、`yes/no/unidentifiable` enums，以及 executed/omission 互斥约束。
- 缺字段、未知 enum 或矛盾组合在 loader 与 frozen verifier 两侧都 fail closed，
  不再由 default `else` 解释成 `target_negative`。

### 2.14 X57：omission semantics 与 Stage-A contract 对齐

- 保留 exact keys/types/enums 与 executed/omission 互斥，但不增加上游协议没有的
  old/new 限制。
- Stage-A 合法 omission positive control
  `candidate=false, old=yes, new=no, omission=true, deadline=true`
  必须 loader PASS 并派生 `CONFIRMED_POSITIVE`。

### 2.15 X61：measurement provenance 失效后禁止 structural verdict

- authority binding、manifest、event provenance 或其他 measurement input 一旦出现
  `MEASUREMENT_INVALID`，全局门控在 structural completion evaluator 之前生效。
- 两个结构投影均固定输出 `UNIDENTIFIABLE`、`enumeration_complete=false`、
  `completion_count=0`、`pass_witness=null`、`fail_witness=null`；不会枚举由失效
  provenance 派生的 completion space。
- exact mutation 只替换 packet 中一个格式合法但不匹配 authority 的 frame hash；
  B/C/E 和 C0-D/PURE-WORLD 全部 `UNIDENTIFIABLE`，且唯一 measurement issue
  仍是 `EXTERNAL_AUTHORITY_BINDING_MISMATCH`。

## 3. 原有不变量仍保留

- 六类 negative predicate 在 artifact 层独立；只允许冻结的逻辑蕴含产生
  effective closure。
- task certificate 对准确六 configs 取 AND；每 config 覆盖 exact ordinal
  roster，deficit 类再覆盖 exact applicable obligations。
- confirmed positive 不能被 negative certificate 覆盖 strict lower。
- empty/unfreezable obligation：lower `0`、upper `1`、deficit certificate `0`。
- 缺 config 不改变六配置分母。
- detected upper 与 global upper 分型；no detection/no certificate 的
  82-task synthetic frame 仍为 `detected=0, global=82`。
- finite straddle verdict 为 `INCONCLUSIVE`。

## 4. Executable replay map

| Case | 测试 |
|---|---|
| E17–E20 | `test_certificate_one_damage_roster_e17_to_e20` |
| E21–E29、E35 | 对应原有 one-damage / no-stitch / denominator / verdict tests |
| X36 | `test_x36_frozen_executable_and_evidence_bytes_are_enforced` |
| X37 | `test_x37_packet_cannot_reseal_or_reassign_external_universe` |
| X38 | `test_x38_bare_prestitch_row_is_never_an_event_authority` + E23–E25 replay |
| X39 | `test_x39_exact_proof_projection_delete_replace_reorder_stale` |
| X40 | `test_x40_structural_completion_recomputes_pass_and_fail`、`test_x40_large_or_unmapped_structure_fails_closed` |
| X42 | `test_x42_target_boolean_is_not_sound_evidence` |
| X44 | `test_x44_obligation_denominator_cannot_reseal_external_authority` |
| X45 | `test_x45_unit_task_reassignment_cannot_reseal_external_authority` |
| X49 | `test_x49_external_structural_mapping_commitment_rejects_rewrite` |
| X53 | `test_x53_runtime_authority_is_immutable_and_recommitted` |
| X54 | `test_x54_a1_summary_must_equal_primitive_action_semantics` |
| X55 | `test_x55_model_family_codebook_is_exact_not_enum_only` |
| X56 | `test_x56_malformed_action_cannot_become_negative` |
| X57 | `test_x57_omission_semantics_match_stage_a_contract` |
| X61 | `test_x61_measurement_invalid_blocks_structural_enumeration` |
| Schema | Draft 2020-12 validation + Ajv 2020 `strict=true` compile |
| Interface | clean subprocess CLI 与 direct API exact parity |

Fixture roster:

```text
tests/fixtures/stage0f_bounds_negative_cases.json
44 executable one-damage cases
```

专属 suite 共 33 个 test methods；本轮最终结果为 `Ran 33 tests ... OK`。五个
bounds schemas 均通过 Ajv 2020 `strict=true` 实际编译。

## 5. 当前阻塞与允许的下一状态

尚缺 real full-block adapter、真实 proof semantics audit、large-world trusted solver
certificate、release-tagged structural provenance 和独立 fresh reviewer。故当前仍是：

```text
MEASUREMENT IMPLEMENTATION NOT READY
NO SYNTHETIC FREEZE
NO BLOCK A
NO STEP 1 GO
```

即使 33 个 synthetic tests 全绿，也只能提交 fresh audit；不能把绿色 mechanics
测试写成自然负担、环境根因或 action-contract 科研假设已经成立。
