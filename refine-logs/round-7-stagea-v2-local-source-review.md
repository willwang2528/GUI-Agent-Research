# Round 7 — Stage A v2 与本地归档源对抗复核

> 时间：2026-07-28  
> 范围：只审查测量机械、协议闭合程度与本地归档字节投影；不测量自然 UACF-D 负担。  
> 最终裁决：**STAGE A V2 SYNTHETIC MECHANICS ACCEPT / PROTOCOL REVISE / LOCAL ARCHIVED BYTES ACCEPT / PRODUCTION REJECT / NO BLOCK A / NO STEP 1 GO**

## 1. 本轮要解决的门槛

Round 6 已证明 Stage A v1 可以在以下情况下错误放行：

1. 两位 A0 labeler 的实质分歧被 consensus-only 表示抹除；
2. 两人共同写出的错误命题可以仅凭 evidence pointer 被当作语义蕴含；
3. rejected disposition 可以删除事件、A1 路径与 denominator。

因此，本轮不是继续增加普通测试，而是要求 Stage A v2 同时保留五类对象：

```text
R = raw-label ledger
C = case ledger
P = A1 path ledger
E = primary estimand roster
M = missingness / unresolved ledger
```

并强制区分：

```text
consensus
blinded_human_resolution
independent_paths
unresolved
```

## 2. 多轮对抗过程

### Round 7-A：v2 迁移

实现方完成 schema、validator、builder 与 fixtures 迁移，加入：

- complete-tuple human resolution；
- raw/case/path/primary/missingness 五账本；
- independent primary 与 sensitivity 分离；
- unresolved case 保留；
- mechanical grounding 与 human grounding 分流；
- substantive rejection fail-closed；
- synthetic mechanical verifier 仅接受固定 typed claim。

第一版达到：

```text
93/93 Stage A tests PASS
28/28 Ajv 2020 strict schemas PASS
py_compile PASS
```

### Round 7-B：独立 spec red-team

独立审查先后提出：

- R04：可能从两份 raw labels 拼出 Frankenstein resolution；
- R07：independent paths 可能因只数 positive paths 而改变 primary denominator；
- 未冻结 case matcher，无法证明 agreement denominator 完整；
- pointer binding 不等于 semantic entailment；
- 缺少 external raw-roster、trusted-time、access 与 role receipts。

实现修订后，审查者又发现 R11：

```text
singleton raw case
→ derived agreement = single_support_no_agreement
→ unresolved branch 却被强制写成 unresolved_disagreement
```

这会令单边支持的 unresolved case 无法被忠实保存。

### Round 7-C：R11 窄修复

最终规则改为：

- unresolved agreement 必须等于从 raw labels 机械推导的 agreement；
- singleton unresolved 必须是 `single_support_no_agreement`；
- paired disagreement unresolved 必须是 `raw_substantive_disagreement`；
- A0 `source_protocol` 从 v0.5 更新为 v0.6。

独立审查者复算 hash、定向复放 R11，并接受这项窄修复；但明确拒绝把它解释为 whole-protocol freeze。

## 3. Stage A v2 最终可执行证据

本轮 root 最终复跑：

```text
94/94 Stage A tests PASS
104/104 Stage A + protocol + detail audit + ARIS snapshot tests PASS
28/28 Ajv 2020 strict schemas PASS
py_compile PASS
```

关键 hash：

| Artifact | SHA-256 |
|---|---|
| Stage A schema bundle（22 schemas 的 canonical bundle） | `e54d495793dce49168e97188cb54b7c50f029c16673d60b128ff7aaa0084e9d6` |
| `tools/validate_stage0f_stage_a_packet.py` | `c014a891f86c0bfba352fcbb06e4f0fcdf3b28e401120617e12d5c86196d679d` |
| `schemas/stage0f_a0_input.schema.json` | `b6ae5b41036b241d29520bc985b77a37c8c86db7d5097f637eb875e3295804df` |
| `tests/test_stage0f_stage_a_validator.py` | `6d6496ca7b70471813bb42931f84f9fae1a49c6530d42c99dcd0b872dcafe1a1` |
| `tests/fixtures/stage0f_negative_cases.json` | `c023df23bafc19cc7d22e1d19d59b3c0f33103ebd66d17e3da03dd76d1cc14de` |

主要反例覆盖：

| Counterexample | Fail-closed code |
|---|---|
| X64 / R01 rejection unavailable | `SEM_A0_REJECTION_UNAVAILABLE` |
| R02 raw fanout | `SEM_A0_RAW_CASE_PARTITION` |
| R04 Frankenstein resolution | `SEM_A0_RESOLUTION_FRANKENSTEIN` |
| R06 path denominator loss | `SEM_A1_EXACT_EVENT_SET` |
| R07/R09/R10 roster corruption | `SEM_A0_CASE_ROSTER` |
| R12 pointer-only mechanical claim | `SEM_MECHANICAL_GROUNDING_INCOMPLETE` |
| R15 shared A1 path aliasing | `SEM_A1_PATH_ALIAS` |

这些 negative fixtures 要求“精确 stage + 精确 code + 仅一个错误”，因此不能用 schema-first 的其他失败伪造绿灯。

### Stage A 现在能证明什么

```text
STRUCTURAL_VALIDATION_ONLY
SYNTHETIC_TYPED_CLAIM_ONLY
UNAVAILABLE_FAIL_CLOSED
NO BLOCK A
```

它证明：在已给定且受控的 synthetic case partition 下，R/C/P/E/M 账本、resolution mode、denominator preservation 与特定 typed-claim 机械检查可以按协议运行。

它仍不能证明：

- 自然轨迹中的 case matcher 完整；
- GUI 语义由截图与任务规则真正蕴含；
- human dual-entailment 独立且盲化；
- raw roster、时间、访问与角色历史来自不可回滚的外部 authority；
- 自然 UACF-D 负担存在。

## 4. 本地归档源 adapter 对抗结果

初版曾使用过强表述 `REAL_ARCHIVED_SOURCE_PROJECTION_VERIFIED`。独立审查指出：

```text
manifest + audit + pages + parser + schema
构成同一个本地 self-sealed loop
```

该闭环没有 publisher signature、immutable release root 或 trusted capture time，因此不能证明来源真实性。

v1.1 将结论降格为：

```text
LOCAL_ARCHIVED_BYTES_LITERAL_PROJECTION_VERIFIED
SOURCE_ORIGIN_AUTHENTICITY_UNVERIFIED
LOCAL_MANIFEST_SELF_SEALED
TRUSTED_CAPTURE_TIME_MISSING
OBSERVATION_ASSET_AUTHORITY_PARTIAL
PRODUCTION_AUTHORITY_INCOMPLETE
NO BLOCK A
```

并加入 duplicate-key、reserved-id/cardinality、symlink、source containment、filename/content swap、step reorder/delete、local reseal 等反例。

本轮 root 与独立审查均复放：

```text
22/22 adapter tests PASS
48 archived HTML pages
47 replay-bearing pages
1 explicit no-step page
9,138 projected steps
Ajv 2020 strict PASS
py_compile PASS
```

关键 hash：

| Artifact | SHA-256 |
|---|---|
| Adapter | `56cd1e9a3149bcd8eb61da825d8e3cb2d9ded4a9d93b9d81b817b5bb72c5e569` |
| Receipt schema | `fe9908dbafd5fa0af5b326d4fb63d61b6e18b36137a0861aef0575ed9b0f3e0f` |
| Tests | `9b5965c628347eb5b5b0f7121594337f7ee6029cecd3d2a0ae19ec2f2dfc9d21` |
| Real local projection | `8e2380b5eb436f1dc043ca694a41bfe8cd33e1da3561a4fe48d3eb8bde15473b` |
| Real local receipt | `cc27fe03f762b8257d31e1089770281098f3cd0eba7a767c0ce8f39da14079d2` |

独立审查只接受“当前 48 份本地 HTML bytes 经固定本地 parser 的 literal projection”，明确拒绝 official source、production authority、Block A 或 Step 1 推断。

## 5. Protocol v0.6 当前闭合程度

v0.6 已写入：

1. full raw semantic preimage；
2. complete-tuple resolution；
3. 唯一允许的 source-label union transform；
4. R/C/P/E/M 定义；
5. pre-adjudication agreement、a/b/c、singleton 与 both-zero；
6. 四种 resolution mode；
7. independent paths 仅作 sensitivity，除非预先冻结 aggregator；
8. substantive rejection fail-closed；
9. mechanical/human grounding 分流；
10. unresolved bounds 与 external receipts。

但协议仍为 `REVISE`，因为当前没有：

- frozen raw-case matcher；
- 两份独立 human evidence-entailment records；
- external raw-roster/trusted-time/access/role receipts；
- production verifier；
- 自然负担测量。

## 6. 本轮裁决

| 对象 | 裁决 |
|---|---|
| Stage A v2 指定 synthetic mechanics | ACCEPT |
| R11 / source-protocol v0.6 窄修复 | ACCEPT |
| whole Stage A protocol freeze | REVISE |
| 当前本地 48 HTML bytes 的 literal projection | ACCEPT |
| source origin / official release authenticity | NOT ESTABLISHED |
| production measurement | REJECT / FAIL-CLOSED |
| synthetic freeze | NO |
| Block A | NO |
| Step 1 GO | NO |

## 7. 下一轮唯一顺序

```text
冻结 A0 raw-case matcher
→ 建立 human dual-entailment 记录
→ 接入 external roster/time/access/role receipts
→ 补 screenshot/initial-observation/task/evaluator authority
→ 在 Python 3.12 精确环境复跑
→ integrated executable battle
→ 再决定是否允许 synthetic dry run
→ 再决定是否生成 Block A
→ 最终用自然证据裁决 Step 1
```

当前最先做的是 matcher，不是继续扩展 literature map，也不是提前提出 action-contract 方法。
