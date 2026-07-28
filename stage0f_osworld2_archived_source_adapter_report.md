# Stage 0F：OSWorld 2.0 真实归档源投影适配器

> implementation status: **STABLE_FOR_ROOT_AUDIT**  
> measurement status: **NO BLOCK A / NO STEP 1 GO**  
> claim ceiling: **LOCAL_ARCHIVED_BYTES_LITERAL_PROJECTION_VERIFIED / SOURCE_ORIGIN_AUTHENTICITY_UNVERIFIED / LOCAL_MANIFEST_SELF_SEALED / TRUSTED_CAPTURE_TIME_MISSING / OBSERVATION_ASSET_AUTHORITY_PARTIAL / PRODUCTION_AUTHORITY_INCOMPLETE / NO_BLOCK_A**

## 1. 适配器只证明什么

验证器读取当前 `manifest.json`、`detail_audit.json` 和 48 个归档 HTML 的真实字节，并验证：

- manifest 中登记的 detail audit、旧 availability auditor 与 detail tree 哈希；
- 固定的 8 task × 6 hosted-config 文件总体；
- 每页文件名、task、config、replay root 与 trajectory id 的精确绑定；
- 嵌入 replay payload 只能包含 `steps` 与 `total_steps`；
- `total_steps == len(steps)`；
- step index 必须按 payload 顺序严格等于 `1..N`；
- action 的 `category / label / detail / status`、有序 subactions、timestamp 与 screenshot reference 只做字面投影；
- `050__MiniMax-M3.html` 只能保持显式 no-step，receipt 不为它产生 `steps`、`total_steps` 或 root identity。

验证器实现由 receipt schema 以 parser id、实现路径和精确 SHA-256 本地登记。manifest、schema 与 parser 可以在本地同步重签；即使哈希完全匹配，receipt 也固定标记 `LOCAL_SCHEMA_SELF_REGISTRATION_ONLY` 和 `LOCAL_PARSER_SCHEMA_SELF_SEALED`。该登记不是外部、pre-outcome 或 non-rollback commitment，不能把本地字节真实性升级为官方来源真实性。

## 2. 明确不证明什么

- 本地没有 screenshot bytes；归档 URL 只保留为 reference literal。
- manifest 中的 `source_origin` 和 `fetched_at` 是本地 JSON 字面值，没有官方签名、可信抓取时间或外部 content receipt。
- manifest 与 detail audit 可以在本地同步重签，因此只构成本地一致性，不构成来源 authenticity。
- 验证器没有发起 URL 请求，也没有把 `screenshot_exists=true` 当作资产存在性证明。
- 没有独立标记的 initial pre-action observation。
- timestamp 单调性不证明 screenshot、action 与环境状态的因果或时间对齐。
- 没有 release-tagged task/evaluator authority、outcome truth、UACF-D label、Stage A barrier 或 Block A。

因此 receipt 固定输出：

```text
source_origin_authenticity = SOURCE_ORIGIN_AUTHENTICITY_UNVERIFIED
manifest_authority = LOCAL_MANIFEST_SELF_SEALED
capture_time_authority = TRUSTED_CAPTURE_TIME_MISSING
parser_schema_authority = LOCAL_PARSER_SCHEMA_SELF_SEALED
screenshot_bytes = MISSING_SCREENSHOT_BYTES
screenshot_urls = REFERENCE_ONLY_NOT_FETCHED_OR_VERIFIED
initial_pre_action_observation = MISSING_INITIAL_PRE_ACTION_OBSERVATION
timeline_alignment = TIMELINE_ALIGNMENT_UNPROVEN
production_authority = PRODUCTION_AUTHORITY_INCOMPLETE
block_a = NO_BLOCK_A
```

## 3. 当前真实 48 页结果

| 检查项 | 结果 |
|---|---:|
| receipt valid | `true` |
| archived pages | 48 |
| literal replay pages | 47 |
| explicit no-step pages | 1 |
| projected steps | 9,138 |
| issues | 0 |
| parser status | `LOCAL_HASH_MATCH` |
| receipt SHA-256 | `cc27fe03f762b8257d31e1089770281098f3cd0eba7a767c0ce8f39da14079d2` |
| archive literal projection SHA-256 | `8e2380b5eb436f1dc043ca694a41bfe8cd33e1da3561a4fe48d3eb8bde15473b` |

输入与实现：

| Artifact | SHA-256 |
|---|---|
| `source_provenance/osworld2/manifest.json` | `7b4f7fc576a164357109aa8bb1b4101159a0923df6f29f3870fd0df6618810f6` |
| `source_provenance/osworld2/detail_audit.json` | `7fded94da84bf367146d5fb507cf88b296f196bb178906902b0d6a50f559df6e` |
| `tools/verify_stage0f_osworld2_archived_source.py` | `56cd1e9a3149bcd8eb61da825d8e3cb2d9ded4a9d93b9d81b817b5bb72c5e569` |
| `schemas/stage0f_osworld2_archived_source_receipt.schema.json` | `fe9908dbafd5fa0af5b326d4fb63d61b6e18b36137a0861aef0575ed9b0f3e0f` |
| `tests/test_stage0f_osworld2_archived_source.py` | `9b5965c628347eb5b5b0f7121594337f7ee6029cecd3d2a0ae19ec2f2dfc9d21` |

完整 literal receipt 只生成在临时目录，没有把 `source_provenance/osworld2/raw/` 或派生的逐步字面数据加入 Git。

## 4. 负例与实现验证

22 个单元测试全部通过，覆盖：

- clean fixed-frame literal projection；
- 单字节 page mutation；
- filename content swap；
- task/config/trajectory root swap；
- step deletion；
- step reorder；
- `total_steps` mutation；
- parser bytes mismatch；
- parser registration hash mutation；
- manifest、detail audit、schema 与 embedded replay JSON 的 duplicate-key rejection；
- HTML 属性顺序变化的 benign positive control；
- hidden/duplicate replay root 与 replay data ID；
- `050__MiniMax-M3` 上 hidden reserved data ID；
- source directory containment；
- symlinked source page；
- local manifest/audit reseal 后 projection 会变化，但来源状态仍固定为 unverified/self-sealed；
- missing page；
- no-step trajectory fabrication；
- Ajv 2020 `strict=true` schema compile。

执行记录：

```text
Ran 22 tests in 3.876s
OK
AJV2020_STRICT_PASS
```

真实归档执行命令：

```text
PYTHONPYCACHEPREFIX=/private/tmp/stage0f-osworld2-pycache \
.venv-stage0f/bin/python \
tools/verify_stage0f_osworld2_archived_source.py \
--manifest source_provenance/osworld2/manifest.json \
--detail-audit source_provenance/osworld2/detail_audit.json \
--detail-dir source_provenance/osworld2/raw/detail_pages \
--schema schemas/stage0f_osworld2_archived_source_receipt.schema.json \
--project-root . \
--output /private/tmp/stage0f_osworld2_archived_source_receipt.json
```

## 5. 与 Stage A 的隔离

本实现没有修改 `tools/validate_stage0f_stage_a_packet.py`、Stage A schemas、bounds schemas 或 production PASS 条件。它只把一个已存在但此前未机械闭合的事实变成可复算输入：

```text
归档 HTML bytes
→ 固定 parser identity/hash
→ task/config/root binding
→ ordered literal replay projection
```

后续仍需独立完成 screenshot byte authority、initial/pre-post alignment、release-tagged task/evaluator authority、disagreement-preserving adjudication 与 temporal/access infrastructure，才有资格重新审计 production Stage A。

## 6. 残余外部缺口

当前 adapter 无法通过本地补丁闭合：

1. 官方来源签名或由发布方提供的 immutable content manifest；
2. 可信抓取时间、non-rollback capture receipt 与第三方时间戳；
3. screenshot bytes、逐步 observation bytes 及其内容哈希；
4. initial pre-action observation 与每个 action 的 pre/post 环境对齐；
5. release-tagged task、evaluator、obligation 与 outcome authority；
6. pre-outcome frame/config/structural-mapping commitments；
7. 平台 complete access log、稳定 principal commitment 与 role-history checkpoint；
8. X62 disagreement-preserving adjudication 与 X63 evidence entailment/grounding。

所以真实 48 页回归只证明“当前本地 48 个 HTML 字节能被固定 parser 无歧义地投影”。它不证明这些字节由官网在某一可信时间发布，也不支持 Block A、UACF-D burden 或 Step 1 GO。
