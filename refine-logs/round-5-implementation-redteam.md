# Round 5：Stage 1 Measurement Implementation Battle

> date: `2026-07-28`  
> reviewer: `stage1_measurement_redteam`  
> independence: fresh / read-only  
> round_1_verdict: **NOT READY**  
> round_2_status: **PENDING IMPLEMENTATION**  
> claim_ceiling: no synthetic freeze、no Block A、no Step 1 GO

## 1. Round 1 已证实的实现缺口

1. 旧 `ARTIFACT_FILES` 不加载或复算 A0 raw-label containers；supporting raw-label ids 可被伪造。
2. 旧 block entry 只验证 barrier schema 后固定 `NOT_READY`，没有加载 manifest、unit bundles、raw labels、adjudications、A1、exposure ledger 或 certificates。
3. validator 中存在被后定义覆盖的旧 task-level PASS 路径；当前不可达，但可能在重构时复活。
4. flat raw-label rows 不能证明两位不同 annotators 各自提交，也不能表达每位 annotator 的合法 zero-event submission。
5. 旧 block schema 强迫每个 location 至少一个 event，与 zero-event location 冲突；单 ref 也不能绑定 same-location multi-event。
6. role registry 只保证数组内部 unique，没有验证 role pools 两两不交、跨 block 永久历史或 delivery/access logs。
7. rolling prefix 没有绑定 current action reveal record，不能证明 commit 发生在当前动作之前；batch atomicity 未证明。
8. `source_unidentifiable` 缺少 reason 与 frozen searched-scope 结构，不能机械区分合法 `SOURCE_UNKNOWN` 和 invalid measurement。

## 2. Production invariants

### P：唯一可信生产入口

- P1：只有 `validate_full_block` 可以产生 production PASS；single-unit、legacy task、component helper 与 CLI fallback 永远不能 PASS。
- P2：PASS 同时证明 duplicate-key、meta/schema、cross-artifact hash、stream/hash-chain、block coverage、roles/exposure、A0/A1 barrier 与 source validity。缺依赖、缺 artifact、未知版本均 fail closed。
- P3：PASS 输出必须绑定 `scope=full_block`、frame hash、manifest hash、barrier hash 与 validator hash。
- P4：源码中不得保留被覆盖或不可达的旧 PASS function。

### B：外部冻结 frame 与 exact coverage

- B1：block roster 来自外部冻结 frame；不得信任调用者自报 count。
- B2：每个 physical unit 从 raw trajectory/hash-chain 复算完整 ordinal roster；location universe 必须与 `(task, config, ordinal)` exact-set equality。
- B3：每个 manifest location 包括 no-event location，必须有两位不同 A0 annotators 的 submission envelopes；每份 envelope 允许 0..N events。
- B4：每个 location 必须有一个 A0-only adjudication container，其 event list 允许 0..N。
- B5：barrier 必须与 manifest location set、submission set、adjudication set、event-id set 和 prefix-chain tips 全等。

### T：时序与 batch atomicity

- T1：stream ledger 显式绑定 `o_k`、commit 和 current `a_k` reveal 的 bytes/hash/time。
- T2：必须验证 `o_k <= decisions <= commit < a_k reveal < o_(k+1)`。
- T3：无法逐 subaction 拦截的 batch 作为一个原子动作；任一 subaction-before-commit 都使 block FAIL。
- T4：最后一个 A0 adjudication 与 A0 barrier seal 之前出现任何 A1 reveal/authorization，使整个 block FAIL。

### R：raw labels 与 multi-event identity

- R1：raw-label id 从冻结 canonical preimage 复算；两份 submission 必须来自两位不同 aliases。
- R2：duplicate raw id 或同一 semantic preimage 仅换 id，均不得重计。
- R3：same location 允许 0..N adjudicated events；每个 event id 独立复算并绑定真实 raw support。
- R4：A1/A1-label 必须一 event 一 path；不能拼接不同 event 的 phenotype、source、obligation 或 interface。

### E：永久角色与 exposure

- E1：coordinator、generator、reference、A0 raw、A0 adjudicator、A1 与 Stage B role sets 两两不交。
- E2：当前 registry 必须与 append-only project-wide role-history ledger 对账；`separation_is_permanent=true` 只是声明。
- E3：delivery/access event ledger 必须完整；A0 角色收到任一 action/A1/outcome artifact 时整个 block FAIL。

### S：source validity

- S1：factual labels 每一项必须有 cutoff 前 direct pointer。
- S2：unknown 必须恰为 `{source_unidentifiable}`，并有 nonempty reason code、冻结 searched-scope roster/hash 和 auditable search-result refs。
- S3：先判 packet validity，再机械派生 `PURE_WORLD / MIXED_WORLD / NON_WORLD / SOURCE_UNKNOWN`。
- S4：`INVALID_SOURCE_MEASUREMENT` 不是 source category。

### C：negative certificate

- C1：certificate validity 只能由 validator 派生，不能接受 boolean。
- C2：predicate id 必须属于冻结六类；task certificate 对准确六 configs 取 AND。
- C3：每 config 必须覆盖准确 ordinal roster/hash-chain；每 ordinal 必须有 direct pointer、白名单 proof mode、verifier bytes/hash/version。
- C4：任何缺失使 certificate false；human/reference/search-not-found 永不签发。
- C5：predicate negatives 只能按逻辑蕴含传播；C/interface/environment negative 不能冒充 B-negative。
- C6：certificate 与 confirmed positive 冲突时 certificate invalid，不能把 lower 改成 0。

### J：finite joint completion

- J1：observed records 先按 exact event key 计算 conjunction，再在 location 做 OR。
- J2：hidden state 只包含 decision card 冻结的 finite joint sufficient bits。
- J3：禁止 marginal multiplication、跨 event stitching 或跨 location stitching。
- J4：joint validator 强制 parent-child inequalities、confirmed bit 1 与 certificate bit 0。
- J5：feasible set 必须 finite、nonempty、可复算，并能输出 pass/fail witnesses；空集或 provenance 不全为 `UNIDENTIFIABLE`。

### D：denominator 与 typed bounds

- D1：`O_applicable(u)` 为空或无法冻结时，lower=0、detected/global upper=1，禁止 deficit-negative certificate。
- D2：缺 config 不能把 task mean 分母改成 5；六配置分母保持不变。
- D3：detected/global upper 必须强类型并附 derivation provenance。
- D4：无 certificate 时，即使 detected=0，global task upper 仍为 82。
- D5：C0-B/C 的 valid finite straddle 必须为 `INCONCLUSIVE`。

## 3. Round 2 必须逐项重放的最小反例

| Case | Damage | Required result |
|---|---|---|
| E01 | valid single unit 调 production | FAIL `FULL_BLOCK_REQUIRED` |
| E02 | 调 legacy task validator/旧 helper | FAIL；不得出现 PASS |
| E03 | Block A 只含 1 unit 且自报 count=1 | FAIL exact frame roster |
| E04 | 删除一个 config 并把 count 减 1 | FAIL；不得信任 count |
| E05 | 删除一个 ordinal location | FAIL full ordinal coverage |
| E06 | 复制一个 location 维持数量 | FAIL duplicate/exact-set |
| E07 | manifest digest 看似合法但文件缺失或 bytes 改变 | FAIL hash/provenance |
| E08 | 同一 annotator 提交两份 raw submissions | FAIL independence |
| E09 | raw rows 共用 id 或同 semantic preimage 换 ids | FAIL duplicate/ID derivation |
| E10 | 两 annotators 均提交 empty events，adjudication empty | PASS 正向 no-event；省略 location 则 FAIL |
| E11 | same location 有 e1/e2，barrier 少一个或 A1 串接 | FAIL event-set/link |
| E12 | commit 在 current action reveal 之后 | FAIL commit-before-current-action |
| E13 | batch 先执行 subaction 再 commit | FAIL atomic bundle gate |
| E14 | 任一 A1 早于最后 A0 adjudication/barrier seal | whole-block FAIL |
| E15 | A0 alias 同时在 A1/Stage B pool | whole-block FAIL |
| E16 | alias 在历史 block 做过 A1、当前做 A0 | FAIL permanent history |
| E17 | B task certificate 只有 5 configs 或重复 config | certificate=0 |
| E18 | config 少 ordinal、重编号或 roster hash stale | certificate=0 |
| E19 | proof mode 是 human/reference/search-not-found | certificate=0 |
| E20 | verifier hash 有值但 output bytes 缺失/指针 stale | certificate=0 |
| E21 | B-negative 与 confirmed B-positive 冲突 | certificate invalid；lower 保留 1 |
| E22 | C-negative 被传入 B slot | 不得降低 B global upper |
| E23 | same location e1=B+NON_WORLD，e2=not-B+WORLD+I | WORLD-and-B-and-I joint=0 |
| E24 | l1 有 B、l2 有 interface | same-event C witness=0 |
| E25 | e1=WORLD+B+met(o)，e2=NON_WORLD+B+unmet(o) | WORLD-and-B-and-unmet(o)=0 |
| E26 | empty obligations 且提交 deficit certificate | reject cert；lower=0 upper=1 |
| E27 | 缺 config 后按 5 重算 mean | FAIL；仍按 6，missing lower=0 upper=1 |
| E28 | no detections、no certificates | detected upper=0、global upper=82；C0-B 不能 BELOW |
| E29 | C lower=7、global upper=82 | `INCONCLUSIVE` |
| E30 | source labels 为空 | `INVALID_SOURCE_MEASUREMENT` |
| E31 | source unknown 与 factual label 并存 | INVALID |
| E32 | unknown 缺 reason/search scope 或 hash 不匹配 | INVALID |
| E33 | factual label 缺 direct pointer 或指向 cutoff 后 | INVALID |
| E34 | world truth 与 task goal 同时变化 | `MIXED_WORLD`，不得 `PURE_WORLD` |
| E35 | unknown/invalid 且无 strict-negative certificate | lower 不增；global upper 仍保留可能性 |

## 4. READY 门

1. P/B/T/R/E/S/C/J/D invariants 全部存在于 production path。
2. E01–E35 全部重放；还需 valid full-block、valid complete certificate、same-location two-event、valid source-unknown 与 valid mixed-world 正例。
3. clean subprocess CLI 与 direct API verdict 一致。
4. 删除 duplicate/legacy PASS code。
5. certificate exact-six、joint monotonic、no-stitching、zero denominator、lower/detected/global ordering 和 straddle semantics 有枚举或 property tests。
6. fresh reviewer Round 2 逐项裁决后，最多升级为 `READY_FOR_SYNTHETIC_DRY_RUN`。
7. 即使 synthetic ready，仍是 `NO BLOCK A`；真实 Block A 还需 production frame、streaming reveal ledger、sound proof whitelist、永久 role ledger、可重建 dependency lock 与第二位独立 reviewer。

## 5. Round 2 bounds fresh red-team：X36–X40

### 裁决

`OVERALL REJECT / MECHANICS PROTOTYPE ONLY / NO BLOCK A`

Round 2 只在“输入已经可信”的条件下接受 E17–E29/E35 的代数机械性、固定分母、typed bounds 与 verdict 逻辑；它不接受当前输入本身已经由环境证据建立。因此 certificate、joint completion 和 capability-boundary claim 仍不成立。

| Case | Executable counterexample | Why fatal | Required result |
|---|---|---|---|
| X36 `SELF_ATTESTED_VERIFIER` | 构造任意 `verifier_id`、伪造 `verifier_output`，再由调用方自报 output hash/pointers；当前路径若不执行冻结 verifier，仍可得到 certificate=1、global upper=0 | C3/C4 要求 certificate 来自可复算的证据判定；“调用方声称 verifier 已经通过”与 human assertion 同构 | `proof_mode` 必须映射到冻结 executable/code/config hash；validator 必须读取真实 evidence bytes，实际执行或独立复算 verifier，逐字段比较完整输出；unknown mode、hash mismatch、execution failure、partial output 一律 certificate=0 |
| X37 `SELF_SEALED_TRUNCATED_UNIVERSE` | 从 manifest 删除一个 ordinal，用公开 helper 重新计算 roster/hash-chain 并生成 certificate；若 bounds packet 自己就是 authority，则删除后的五项 universe 会被重新封成“完整” | C2/C3 的 exact-six/exact-ordinal 不能由待验证 packet 自证；否则 completeness 退化成对截断集合的一致性检查 | bounds API/CLI 必须直接绑定并验证外部 full-block frame、location manifest、A0 barrier 与 stream roots；packet 内 count/hash 只能被核对，不能成为 authority。synthetic 测试也必须引用独立冻结的 trusted fixture authority hash |
| X38 `PRE_STITCHED_EVENT_ASSERTION` | 直接提交一行声称同时满足 `B + interface + PURE_WORLD + unmet` 的 `observed_joint_event`，但不给 canonical event preimage 或 Stage A/A1 引用；当前 joint evaluator 若信任该行即可制造 lower | J1 要求 conjunction 来自同一真实 adjudicated event；裸 status row 只是调用方预拼接结论，无法排除跨事件/跨位置 stitching | event key 必须由 `(task_id, unit_id, boundary_location_id, adjudicated_event_id)` 规范派生；B/interface/source/obligation 字段必须从已验证 full-block/A1 refs 机械生成，禁止 caller 提交结论型 joint row |
| X39 `POINTER_SUBSET_COMPLETENESS` | 某 proof mode 的 sufficient evidence set 含两个必需 pointer，删除其中一个并重算 packet hash；若 validator 只要求 submitted pointers 是 frozen roster 的子集，certificate 仍可通过 | C3 的 direct proof 不只是“没有陌生 pointer”，还要求该 proof mode 的充分证据投影完整 | 为每个 proof mode 冻结 exact/sufficient evidence projection rule；验证 required pointer set、对应 bytes、顺序/chain、schema 与 verifier consumption 全部一致。缺任一 required pointer 时 certificate=0 |
| X40 `IR_NOT_STRUCTURAL_COMPLETION` | 用若干自由 0/1 bits 满足 implication，给出 `z_pass`/`z_fail`；若没有 structural/site-app/model 映射、exposure、K/max-share gates 与统计量重算，两个 bit assignment 仍会被当成 completion witness | J5/C0-D 要求枚举的是与实验设计一致的有限结构世界，不是任意布尔赋值；否则 bounds 没有对真实 completion space 的覆盖保证 | completion IR 必须绑定 frozen structural mapping、exposure artifacts、K gate、max-share gate，并从每个 completion 重算完整统计；输出可核验的 pass/fail structural witnesses。变量超过冻结枚举上限且没有受信 solver certificate 时必须 fail closed |

### Round 3 重放门

1. X36–X40 每项必须同时有负例与至少一个真实确定性正例；mock boolean 或 caller-supplied PASS 不算正例。
2. X36 必须证明 validator 确实运行了冻结 executable，且 evidence bytes 的单字节扰动会失败。
3. X37 必须证明同一截断 packet 即使重新自封，也因不匹配外部 frame authority 而失败。
4. X38 必须证明 same-event conjunction 是从 canonical Stage A/A1 records 派生，并重放 E23–E25。
5. X39 必须证明 required pointer set 的删除、替换、乱序与 stale bytes 均失败。
6. X40 必须展示可复算的 structural `z_pass` 与 `z_fail`；大规模实例无 solver certificate 时不得降级为自报 witness。
7. fresh reviewer 逐项给出 `ACCEPT / REJECT` 与实际执行证据；五项全 ACCEPT 前，状态保持 `NOT_READY / NO BLOCK A`。

## 6. Full-block implementation 新反例

| Case | Executable counterexample | Why fatal | Required result |
|---|---|---|---|
| X41 `RAW_STREAM_SELF_ATTESTATION` | 写入任意 raw trajectory bytes，并保持其文件 hash 正确；另行构造与这些 bytes 语义不一致、但 stream/prefix/manifest 三者内部自洽的 ordinal/action/observation projection | raw file hash 只能证明“引用了这份 bytes”，不能证明派生 ledger 忠实描述原始轨迹。若 parser 没有被实际执行，location universe、commit-before-reveal 与后续 certificate 都建立在调用方自编的时间线上 | production validator 必须绑定冻结 parser/verifier 身份，从 raw bytes 实际重建或独立复算受约束 projection，并逐项匹配 stream ledger；parser unknown、execution failure、projection mismatch、raw 单字节或 stream 单字段扰动一律 whole-block FAIL。若当前 raw 格式无法机械解析，production path 必须明确 fail closed |
| X43 `NORMALIZED_RAW_ROOT_SWAP` | 把人工生成的 normalized `block_raw_trajectory` 与 stream 一起改写，使二者仍完全一致；coordinator/source snapshot 只引用这份 normalized artifact，而不是原始发布 bytes，或 validator 从未对原始 bytes 运行 source parser | “normalized raw 与 stream 一致”只证明两个派生 artifact 一致，不能证明它们忠实于环境实际公开的轨迹。攻击者仍可共同改写整个派生世界 | production authority 必须从 coordinator/source snapshot 锁定的原始发布 bytes 开始，运行冻结 source parser 得到 normalized trajectory，再从后者复算 stream/prefix/manifest。synthetic fixture 可以使用明确冻结的 synthetic raw grammar，但不得据此声称真实 source fidelity；真实 parser/bytes 链缺失时 production fail closed |
| X46 `UNLOGGED_EXPOSURE` | A0 actor 实际读取 A1、score、result URL 或其他 outcome artifact，但 coordinator 不把该访问写入 exposure ledger；随后提交一条内部一致、显示“无泄漏”的链 | 验证已有 log 没有违规事件，不等于证明所有访问都被 log 捕获。自报 ledger 的 silence 不能建立 annotation blindness | synthetic 测试只能声称 exposure-ledger mechanics；真实 Block A 必须绑定平台强制 ACL 与不可变、外部可审计的 complete access log/commitment。若无法证明 capture completeness，production exposure validity fail closed，不能以空 ledger PASS |
| X47 `POSTHOC_STREAM_COMMIT` | 先读取完整 trajectory，再回填满足 `observed < decision < commit < action reveal` 的内部 timestamps，重算全部 prefix hashes、manifest 与 barriers | hash chain 证明提交后未改，不证明提交发生在声称时间；自报时间线可在 outcome 已知后整体生成，因此不能建立 generator 的 rolling-prefix blindness | synthetic fixture只能验证时序 grammar。真实 Block A 必须由不可回退 streaming interface 强制 reveal 顺序，并绑定外部 append-only commit receipts、可信单调时钟或等价可审计执行证据；缺失时 production fail closed |
| X48 `TRUNCATED_ROLE_HISTORY` | 删除 actor 在旧 block 中承担 A1/Stage B 等冲突角色的 assignment，从新的首行开始重算 chain/history root，再重签当前 barrier；当前 block 内角色仍互斥 | E16 只能拒绝“仍被提交的冲突记录”。若 history universe 由 packet 自报，永久角色隔离可通过 rollback、删历史或 alternate fork 绕过 | role-history genesis 与历次 chain tip 必须由外部 append-only authority/notary 提供不可回滚 receipt；当前 packet 提供从 trusted checkpoint 到 current tip 的 inclusion/consistency proof。缺 checkpoint、coverage gap、rollback 或 fork 时 whole-block FAIL |
| X50 `OPAQUE_ALIAS_SYBIL` | 同一真实 human/service principal 使用两个 opaque aliases 提交所谓“两位独立”A0 labels，或同时控制 generator A/B；所有 alias strings、role arrays 与 hash chains 均不同 | distinct aliases 只证明字符串不相等，不证明独立性 quantifier 为 2；agreement、coverage 与 blind adjudication 可被一个主体控制 | 真实 Block A 必须由外部 identity/credential authority 签发 privacy-preserving stable principal commitments，按 principal 验证 required slots 不同并跨 block 去重；alias mapping 可以保密，但 commitment/签名必须可验证。缺失时标记 `INDEPENDENCE_UNVERIFIED` 并阻断 primary reliability |
| X51 `WRONG_ROLE_DELIVERY_LAUNDERING` | 在 valid two-event synthetic block 中，把全部 `a0_input_released` 与 `a1_revealed` 的 recipients 改为仅 `coordinator-main`，重算 exposure chain；原 validator 仍返回 `valid=true` | delivery coverage 只按 `(artifact class,id,hash)` 计数，没有绑定谁必须收到。artifact 被 coordinator 看过不能证明 A0 annotators 实际独立提交，也不能证明 A1 annotator只在 barrier 后收到 reveal | required delivery tuple 必须包含 recipient obligation：每个 location 的 A0 input 必须送达该 submissions container 中 exact A0 annotator aliases；每个 A1 reveal 必须送达对应 `a1_label.annotator_alias`。不相关角色、缺任一 recipient、早送或重复替代均 whole-block FAIL |
| X52 `PHASE_EVENT_ARTIFACT_DECOUPLING` | 交换 `block_frame_frozen` 与 `location_manifest_frozen` 两个 exposure events 的 `visible_artifacts`，保持全局 event-type set 与 artifact set 不变并重签链；原 validator 仍 PASS | 分别检查 `seen_types` 和 `required_visible` 的全局集合，只证明“某处出现过事件名、某处出现过 artifact”，不证明该 phase event 冻结了它声称的对象；barrier/gate 也可被同类错配 | 建立 per-event semantic contract：`event_type` 必须 exact 绑定 actor/role、operation、recipient policy、visible artifact class+ref、phase time 与 multiplicity；swap、wrong actor、missing、duplicate 或 artifact/phase mismatch 均 whole-block FAIL |
| X58 `RAW_SUPPORT_SEMANTIC_LAUNDERING` | 把两位 A0 raw submissions 的 `p_new_proposition_id` 同时改为无关 proposition，重算 raw-label ids、support ids、event ids 与全部 refs；adjudicated A0 label仍声称原 `p_new`。原 validator PASS | supporting-id 集合只证明 adjudication引用了两条提交，不证明 raw semantic payload实际支持 adjudicated proposition/obligation/boundary。A0 adjudicator可把一致的无关原始判断“洗”为目标事件 | 对每个 adjudicated event，validator必须按冻结 adjudication rule机械比较两份 raw semantic payload与 adjudicated A0 label：哪些字段要求一致、哪些允许裁决、分歧如何记录。support ids 与 semantic projection必须同时绑定；无支持、字段漂移或未记录分歧 whole-block FAIL |
| X59 `LATE_A0_LABEL_FREEZE` | 把 event-local A0 label `frozen_at` 改到 A0 barrier之后、A1 reveal之前，再更新 adjudication/barrier refs；adjudication container自身时间仍早于 barrier。原 validator PASS | whole-block barrier只取 container freeze time，不取其引用的每个 A0 label freeze time；因此 A0 semantic label可在“已封 A0”后根据后续信息补写 | A0 barrier必须覆盖所有 event-local A0 labels，并验证每个 label `frozen_at <= adjudication.frozen_at <= barrier.sealed_at`；barrier event-freeze时间与 physical label exact-match。任何 late child、parent-before-child或ref更新时间倒置 whole-block FAIL |
| X60 `FUTURE_ROLE_ACTIVATION` | 把 coordinator role-history assignment 的 `effective_from` 改到其 frame/exposure/Stage-B 操作之后，重算 role-history与barrier refs；alias和role字符串仍匹配。原 validator PASS | 检查 alias→role 映射但忽略 role何时生效，会允许尚未被授权的 actor 执行冻结、交付与授权 | 每个 artifact author、seal、delivery/access actor与recipient都必须在 event/created/frozen time 落入其 role assignment有效区间；`effective_from` 不得晚于 first use，`complete_through` 必须覆盖 block close。未来或断档 assignment whole-block FAIL |

## 7. Bounds verifier semantic soundness 新反例

| Case | Executable counterexample | Why fatal | Required result |
|---|---|---|---|
| X42 `BOOLEAN_LAUNDERED_AS_EVIDENCE` | frozen executable、registry hash 与 subprocess execution 都真实存在，但 verifier 只读取 evidence 中的 `predicate_values[target] = false`、`reachable_opportunity = false` 或等价目标结论字段，然后输出 negative certificate | 代码被真实执行不等于证据蕴含被真实计算。把 caller-supplied boolean 搬进 hashed evidence，仍与 self-attested certificate 同构；它没有证明 complete raw records 排除了目标 event | proof mode 必须从 raw/fullblock-bound、对该 mode 足够且完整的 transition/event records 实际计算目标 predicate。任何直接携带目标 false/no-opportunity 结论的 evidence grammar 都不得进入 sound whitelist；当前阶段若没有这种 verifier，必须禁用相应 mode并令 certificate=0 |
| X44 `OBLIGATION_DENOMINATOR_SELF_REPORT` | 从 bounds manifest 的 `applicable_obligation_ids` 删除已违反义务，或添加虚假义务，再重算 packet 内 hashes；若 evaluator 直接使用该 roster，deficit ratio、certificate applicability 与 structural mass 会被调用方改写 | deficit 的分子与分母都必须绑定预冻结 canonical obligations；自报 denominator 会让同一行为得到任意 burden | obligation roster 必须从已经通过 full-block authority 的 unit A0 input `task_context.obligations` 机械投影、规范排序与去重，并与所有 ordinal/config refs 一致；任何 packet roster 不匹配、重复、漂移或无法建立 applicability 时 fail closed |
| X45 `UNIT_TASK_REASSIGNMENT` | 保持 unit、config 与 ordinal 总数不变，但交换两个 unit 的 `task_id`、hosted config、model family，或把阳性 unit 重新归到另一 task，再重签 bounds packet | task 去重、exact-six AND、task-equivalent 聚合与 structural/model-family shares 都依赖身份映射；只验证总量不能阻止 outcome-dependent regrouping | `unit_alias ↔ task_id ↔ hosted_config_id ↔ model_family_id ↔ ordinal/location` 必须从 full-block frame 与 coordinator envelopes 机械派生并 exact-match；任何 reassignment、duplicate ownership 或 orphan unit 都 fail closed |
| X49 `STRUCTURAL_PARTITION_REWRITE` | 保持 task/unit/config/event 与 positive mass 完全不变且 mapping 100% 覆盖，只把集中于一个组的阳性 tasks 重标到四个 structural groups/三个 app sets，或反向合并，再重算 mapping/exposure hashes | coverage、K 与 share 公式都可以算对，但 outcome-dependent partition shopping 能把 `CONCENTRATED` 改成 `SUPPORTED`；这不同于 X45 的身份交换 | mapping 必须由 release-tagged task/app provenance 与冻结 codebook/procedure机械派生，或由独立 outcome-blind annotators 在任何 A1/Stage B outcome 解封前裁决；mapping hash 必须取得外部 pre-outcome receipt并进入 frame/measurement-stack commitment。post-outcome remap 只能开启新 frame |
| X53 `RUNTIME_AUTHORITY_MUTATION` | 用 trusted loader 得到含 `CONFIRMED_NEGATIVE` event 的 `BoundsAuthority`；不改 authority file、expected hash 或 packet refs，只在内存执行 `authority.events[0].b_status = CONFIRMED_POSITIVE`。原实现把 `L_B_tasks` 从 0 改为 1 且无 integrity issue | constructor deep-copy 不等于 read-only。analyzer 比对的是加载时缓存的 `event_refs`，实际计算却读取可变的 current `events`，因此验证后可篡改 authority | authority 必须递归 immutable，或每次 analyze 对 current holdout/events/evidence/projections/structural content 重算 runtime commitments并与外部 binding exact-match；缓存 ref 与实际消费对象必须同源。任何 load-after mutation 均 fail closed |
| X54 `A1_SUMMARY_ACTION_DIVERGENCE` | 在 externally committed synthetic A1 中令 `primary_uacf_d_positive=true`、`phenotype=target_positive`，但 primitive `action_assessment` 明确与新状态相容、与旧状态不相容；原 event loader 用 summary 计 `L_B`，negative verifier却从 action 计算 B=false | 同一 artifact 存在两套不一致语义源，lower 与 certificate 可对同一事件给相反结论；hash 只能冻结矛盾，不能消除矛盾 | loader 必须从 `p_old_status + primitive action_assessment` 唯一机械派生三值 phenotype/B，并要求任何 summary fields exact-match；true、false、unresolved 必须区分，只有所有 complete events 都确定 false 才可签 negative certificate |
| X55 `MODEL_FAMILY_CODEBOOK_REWRITE` | 保持 configs、units 与 events 不变，在新签 authority 中把一个 Anthropic config 与 OpenAI config 的 family labels 对调；family 值仍属于允许的四个 enum | enum 与 coverage 不能证明 frozen exact codebook。重写 config→family 归属会改变 model-family exposure、K 与 normalized share，形成 outcome-dependent regrouping | config→model-family 必须 exact-match预注册 codebook及其外部 commitment；只验证 family 属于允许集合不够。任何 swap、duplicate family rule 或未知 config 都 fail closed |
| X56 `MALFORMED_ACTION_FAILS_NEGATIVE` | primitive A1 使用空 `action_assessment`，或把 old/new compatibility 写成未定义值，同时把 summary 同步写成 negative；原三值派生的 catch-all `else` 将其当 `target_negative`，complete-ledger verifier可签 q_B negative | malformed/unknown 不是 false。fail-open negative 会错误降低 global upper，直接把 measurement uncertainty伪装成不存在 | primitive action必须经过 closed schema：required keys、boolean types、compatibility enums 与互斥组合全部验证；derivation只对合法完整组合输出 true/false，任何缺失、非法或矛盾必须 authority load FAIL或 unresolved，且不得签 negative certificate |
| X57 `OMISSION_SEMANTICS_DRIFT` | 为修 X56 收紧 grammar 后，bounds 要求 `required_action_omission=true` 时 old/new compatibility 必须为 `unidentifiable`；但上游 StageA 冻结的合法 omission positive 使用 old=`yes`、new=`no`，因此真实合法 event 被拒 | 下游自行重定义上游 label 语义会改变 estimand；fail-closed 不能成为“把合法数据全部拒掉”的借口 | bounds primitive grammar必须 exact复用 StageA A1 schema与 semantic derivation合同；同时重放 valid omission positive control与 malformed negatives。任何跨层规则变更先升级 schema/version与预注册，不能局部补丁漂移 |
| X61 `STRUCTURAL_VERDICT_AFTER_AUTHORITY_FAILURE` | 仅把 packet 的 external `authority_binding.frame_sha256` 改为另一个 schema-valid hash。原 evaluator已将 C0-B/C/E标 `UNIDENTIFIABLE`，却仍枚举 15,625 个 completions 并输出 `C0-D=CONCENTRATED` | structural verdict建立在同一 identity、manifest、events与mapping provenance上；authority已失效后继续计算会输出伪精确的 scope结论，并可能污染总决策 | 建立全局 measurement-validity gate并先于所有 IR/structural裁决。任何 schema、external authority、manifest、event或mapping provenance invalid时，C0-D 与 pure-world structural verdict一律 `UNIDENTIFIABLE`，不输出 scientific witnesses；diagnostic enumeration如保留必须显式非裁决 |
