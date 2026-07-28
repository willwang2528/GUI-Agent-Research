# Round 9 — Identity Redaction Mechanics 可执行对抗（WIP）

> 时间：2026-07-28  
> 位置：Step 1 measurement design  
> 参与角色：root、formal-spec designer、first-principles red-team、integration auditor  
> goal runtime status：**PAUSED / RESUMABLE（未完成、未阻塞）**  
> 当前裁决：**INITIAL L2 CLAIM FALSIFIED / REPAIR IN PROGRESS / TESTS RED / NO SYNTHETIC FREEZE / NO BLOCK A / NO STEP 1 GO**

## 1. 本轮要关闭的根因

Round 8 已证明：maximum-cardinality matching 与 deterministic tie-break 不能从不完整证据中恢复 semantic event identity。Round 9 因而不再直接实现 matcher，而是先验证更上游的命题：

```text
raw identity evidence
→ outcome-blind allowed projection
→ packet-local aliases
→ reviewer-visible transcript
```

目标不是证明 reviewer “看不到任何语义”，而是建立一个更窄、可执行的条件：

> 对两个分别完整有效、允许投影相同而禁止投影不同的 trace，在固定预承诺机制与规范化 alias 后，reviewer-visible virtual transcript 必须相同。

这是一个 2-safety hyperproperty；单个“看起来干净”的 packet 不能证明它。

## 2. 设计 battle 的第一轮共识

三位审计角色共同要求：

1. public packet 不得包含 raw envelope refs/hashes、stable unit/location、input/output projection hashes、自由 ID 或时间戳；
2. packet alias 只能依赖 fresh secret `K/N` 与预承诺的 domain/side/index，不能依赖 raw hash 或 envelope ID；
3. real refs 与 alias binding 只能保存在 coordinator-only sidecar；
4. exact re-execution 与 differential tests 最多支持“在已声明 allowed projection 下的 conditional noninterference”；
5. 不能由本地机制证明 key 不被 grinding、selector 外生、sidecar ACL、reviewer session 隔离、身份真值或自然 burden；
6. 在 complete pair ledger、双 reviewer receipts 与 main barrier 集成之前，只允许 standalone L1/L2 mechanics，不得升级主测量栈。

## 3. 初版实现及其暂时证据

本轮新增或修订了：

- `tools/verify_stage0f_identity_mechanics.py`
- `tools/stage0f_identity_redactor.py`
- identity policy、codebook、manifest、session、sidecar、raw receipt 与 redaction receipt schemas
- raw event identity envelope 与 reviewer packet schemas
- `tests/test_stage0f_identity_mechanics.py`

初版曾得到：

```text
identity mechanics new tests       20/20 PASS
raw-envelope + pair-packet tests   15/15 PASS
combined                           35/35 PASS
```

这个结果已被后续真实攻击推翻，禁止作为 readiness evidence。

## 4. Battle 3：可执行 false-pass

### 4.1 Integration auditor

下列不合法或不充分状态均曾被初版 verifier 接受：

1. session 声明两个 committed slots，但 bundle 只交一个 envelope/receipt；
2. bundle 含额外 stale envelope/receipt，但 verifier 静默忽略；
3. raw 与 redaction receipts 使用 1999/2000 年自报时间；
4. redaction receipt 是指向 bundle 外的 symlink；
5. left/right 使用同一 append channel 与 sequence；
6. session 时间早于 manifest/A0；
7. 声称 complete search，但无外部 receipt；
8. arbitrary envelope version hashes；
9. 两个 slot 复用同一 raw path；
10. typed-invalid envelope 仍进入 reviewer packet；
11. 缺失或 malformed artifact 触发未捕获 exception，而不是结构化 fail-closed。

同时确认了一个窄隔离事实：

- identity schemas 未加入主 `SCHEMA_FILES`；
- main barrier 尚不消费 identity receipt；
- identity bundle 交给主 full validator 会因缺少 full-block artifact 失败；
- 原 Stage A 94/94 回归仍通过。

这只说明 WIP 没有悄悄升级主测量栈，不说明 identity mechanics 成立。

### 4.2 First-principles red-team

red-team 构造并执行了：

1. **allowed-projection laundering**：把 Base64/secret 放进 A0 可见文本，whole-observation selector 会原样暴露；
2. **session-slot grinding**：27 次尝试后选择有利 slot，而 key draw/retry 仍只是自报；
3. **same raw bytes / different principals**：两侧复用相同 bytes，但 self-reported principal 不同；
4. committed-slot omission；
5. 额外 reviewer-visible 文件未进入 transcript；
6. 同一 executable 同时充当 redactor、raw verifier 与 independent verifier；
7. 伪造 chronology。

裁决：

```text
transport-level private binding exclusion
不推出
visible evidence semantic blindness
```

同样：

```text
two distinct local commitments
不推出
two externally authoritative principals
```

### 4.3 Formal-spec reviewer

formal reviewer 发现：

- policy 初版没有显式包含 selector 派生的 `rendition.text`，但 packet 实际暴露了它；
- exact-string intersection 无法检测 secret substring 或编码泄漏；
- 初版 2-safety 只修改内存中的 invalid envelope，没有重建两个完整有效 trace；
- “independent replay” 实际调用同一 executable；
- manifest 未绑定 runtime/dependencies；
- Python 3.12 venv 缺少 `jsonschema`，当前不能声称 3.12 可执行。

## 5. 已实施但尚未回归完成的 repair

当前工作区已做以下 WIP 修复：

1. 新建独立 `tools/stage0f_identity_redactor.py`，verifier 不导入它并独立重算 projection/alias；
2. policy 显式把 selector 派生的 rendition 纳入 allowed projection；
3. 明确标记 visible-evidence semantic leakage 与 selector provenance 未建立；
4. manifest 增加 codebook、matcher spec、redactor、verifier 与 runtime contract 绑定；
5. bundle inventory 改为 closed inventory，并要求每侧恰好一个 slot；
6. fixed artifact loader 拒绝 symlink，missing/malformed 要转为结构化错误；
7. 增加 local lifecycle ordering、channel separation、typed-valid-only 与 exact version binding；
8. `session_slot_id` 改为从 manifest/A0/session IDs 规范派生，禁止 caller 自由选择；
9. claim 名称收窄为 `L2_SINGLE_EXPLICIT_VALID_PAIR_REDACTION_PASS`；
10. principal independence 收窄为 `LOCAL_DISTINCT_COMMITMENTS_ONLY_NOT_EXTERNAL_AUTHORITY`。

## 6. 当前真实可执行状态

2026-07-28 15:50 +08:00 复跑：

```text
python -m unittest \
  tests.test_stage0f_identity_mechanics \
  tests.test_stage0f_raw_event_identity_envelope \
  tests.test_stage0f_pairwise_identity_review_packet
```

结果：

```text
Ran 35 tests
15 passed
20 errors
```

20 个 errors 的共同直接原因是：`build_alias_sidecar` 已从 11 个位置参数收窄为 10 个，但 fixture 仍传入旧的自由 `session_slot_id`。因此当前代码处于预期的 repair 中间态：

```text
MEASUREMENT IMPLEMENTATION NOT READY
ROUND 9 TESTS RED
NO L2 ACCEPT
```

## 7. 尚未完成的唯一恢复链

下次必须从这里继续，禁止跳过：

1. 更新 fixture 到 canonical `session_slot_id`，并让 packet 由独立 redactor 生成；
2. 断言 redactor hash 与 verifier hash 不同，receipt 的 independent verifier binding 正确；
3. 把 Battle 3 的 omission、extra file、symlink、chronology、same-channel、version、typed-invalid、missing/malformed、slot grinding 全部变成 exact regression tests；
4. 把意外的 `OSError/JSON/type` 异常统一转为结构化 fail-closed；
5. 用两个**完整有效 trace**重建 2-safety counterfactual，包括 sessions、envelopes、raw receipts、sidecar 与 packet；
6. 只比较规范化 virtual reviewer transcript，不把 runtime metadata 假装成已隔离；
7. 复跑 35 tests、Stage A 94 tests、旧组合回归与 adapter/bounds；
8. 绿灯后让三位角色进行 Battle 4 fresh executable attacks；
9. 只有 fresh battle 未发现 false-pass，才考虑是否接受窄 L2 mechanics；仍不得进入 pair ledger、main barrier、Block A 或 Step 2。

## 8. 当前 claim ceiling

```text
FRAME-READY
DETAIL-AVAILABILITY-PARTIAL
MEASUREMENT IMPLEMENTATION NOT READY
ROUND 9 IDENTITY MECHANICS REPAIR IN PROGRESS
INITIAL L2 CLAIM FALSIFIED
LOCAL ARCHIVED BYTES ONLY
NO SYNTHETIC FREEZE
NO BLOCK A
NO STEP 1 GO
```

禁止推断：

```text
independent source files != independent authority
closed inventory != external roster completeness
self-reported chronology != trusted time
allowed projection declared != semantic blindness
valid local pair != natural event identity
tests red != harmless implementation detail
```
