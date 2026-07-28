# Step 1 Round 9 WIP 可恢复检查点

> checkpoint id: `2026-07-28T155000+0800`  
> goal status: **PAUSED / RESUMABLE（未完成、未阻塞）**  
> scientific step: **Step 1 — 证明问题现象与负担**  
> step status: **IN PROGRESS / TESTS RED / NO STEP 1 GO**

## 1. 下次恢复入口

严格按以下顺序读取：

1. `research-ledger/CURRENT_GOAL_STATE.json`
2. 本文件
3. `refine-logs/round-9-identity-mechanics-redteam-wip.md`
4. `tools/verify_stage0f_identity_mechanics.py`
5. `tools/stage0f_identity_redactor.py`
6. `tests/test_stage0f_identity_mechanics.py`
7. `schemas/stage0f_identity_redaction_policy.json`
8. `schemas/stage0f_identity_redaction_verification_receipt.schema.json`
9. `stage0f_a0_pairwise_identity_partial_identification_spec.md`
10. `refine-logs/REFINE_STATE.json`

不要重启 literature survey，不要直接实现 matcher，不要运行真实 Block A，不要进入 Step 2。

## 2. 科研主题与七步锁

当前命题：

> 长程 GUI 控制的 memory 必须成为可被环境证伪的行动契约；只有当 Agent 知道哪些事实必须仍然为真、为何为真以及错误后如何恢复，Memory 才真正改变能力边界。

七步串行链：

1. 证明问题现象与负担；
2. 识别根因；
3. 证明强现有方法仍有 residual；
4. 证明方法必要性、充分性与组件贡献；
5. 证明 environment-falsification 的独特优势；
6. 审计预算、权限与公平性；
7. retain / rename / stop，并裁决是否改变能力边界。

当前只在 Step 1。Steps 2–7 全部锁定。

## 3. 最新科学状态

```text
FRAME-READY
DETAIL-AVAILABILITY-PARTIAL
MEASUREMENT IMPLEMENTATION NOT READY
ROUND 9 IDENTITY MECHANICS REPAIR IN PROGRESS
INITIAL L2 CLAIM FALSIFIED
PROTOCOL REVISE
LOCAL ARCHIVED BYTES ONLY
NO SYNTHETIC FREEZE
NO BLOCK A
NO STEP 1 GO
```

Round 8 的 118/118 与 Round 9 初版的 35/35 均不能证明当前实现 ready。Round 9 初版 35/35 已被三类可执行攻击推翻。

## 4. Round 9 已证明什么

### 4.1 单 artifact 不能证明 blindness

需要验证的是 2-safety 条件：

```text
两个完整有效 traces
+ 相同 allowed projection
+ 不同 forbidden projection
→ 规范化 reviewer transcript 相同
```

单一 packet 的字段名闭合或“未出现明显 secret”都不足以证明该条件。

### 4.2 transport exclusion 不等于 semantic blindness

A0 可见 evidence text 本身可能包含、编码或关联 estimand。因而当前只允许验证：

```text
public packet 不暴露 private binding fields
```

不得升级为：

```text
reviewer 看不到 substantive information
```

### 4.3 self-sealed authority 不等于外部 authority

closed bundle、distinct local commitments、self-reported time 与 local runtime binding 不能证明：

- external raw-roster completeness；
- trusted nonrollback time；
- two real independent principals；
- selector exogeneity；
- sidecar ACL；
- reviewer session isolation；
- key non-grinding；
- natural burden。

## 5. 当前工作区的 repair

已经写入但尚未通过完整回归：

- 独立 redactor executable；
- policy/codebook/runtime manifest bindings；
- closed bundle inventory；
- symlink rejection；
- lifecycle/channel/type/version checks；
- canonical session-slot derivation；
- narrowed L2/authority/independence labels。

当前 35-test 复跑结果：

```text
Ran 35 tests
15 passed
20 errors
```

直接失败点：

```text
tests/test_stage0f_identity_mechanics.py fixture
仍以旧签名向 build_alias_sidecar 传入自由 session_slot_id
```

因此现在不是一个 green checkpoint，而是一个如实保存的 WIP checkpoint。

## 6. 下一步唯一执行序列

1. 修正所有 `build_alias_sidecar(...)` 调用；
2. fixture 改由独立 redactor 生成 packet；
3. 写入 Battle 3 的全部 exact bypass regressions；
4. 完成结构化 fail-closed 异常边界；
5. 用两个完整 valid traces 实现 counterfactual 2-safety；
6. 运行 identity 35 tests；
7. 运行 Stage A 94 tests和全部旧回归；
8. 三位独立角色进行 Battle 4；
9. 根据 fresh attacks 决定窄 L2 是 ACCEPT 还是继续 REVISE。

直到第 9 项结束前：

```text
NO L2 ACCEPT
NO PAIR LEDGER
NO MAIN BARRIER INTEGRATION
NO BLOCK A
NO STEP 1 GO
```

## 7. Git 同步范围

GitHub 保存：

- 研究文本、协议与 checkpoint；
- schemas、tools、tests 与 manifests；
- 七步台账与对抗日志。

继续排除：

- `.venv*`、cache；
- `external/`；
- 本地 raw archived pages；
- PDFs；
- 历史 tar/zip 与备份目录。

这些排除项不会因 GitHub 同步而获得远端备份；其身份只由已跟踪 manifest/hash 记录。
