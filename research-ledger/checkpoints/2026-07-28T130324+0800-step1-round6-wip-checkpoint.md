# Step 1 Round 6 — GitHub Sync WIP Checkpoint

> checkpoint_id: `2026-07-28T130324+0800`  
> checkpoint_time: `2026-07-28T13:03:24+08:00`  
> goal_status: `ACTIVE / NOT COMPLETE / NOT BLOCKED`  
> current_step: `STEP 1 IN PROGRESS`  
> claim_ceiling: `FRAME-READY / DETAIL-AVAILABILITY-PARTIAL / MEASUREMENT IMPLEMENTATION NOT READY / NO SYNTHETIC FREEZE / NO BLOCK A / NO STEP 1 GO`

## 1. 下次恢复入口

严格按以下顺序读取：

1. `research-ledger/CURRENT_GOAL_STATE.json`
2. 本文件
3. `refine-logs/round-6-stagea-semantic-adjudication-review.md`
4. `stage0f_production_authority_gap_report.md`
5. `stage0f_osworld2_archived_source_adapter_report.md`
6. `refine-logs/REFINE_STATE.json`

不要重新开始宽泛论文搜索，不要执行 Block A，不要把真实归档可解析、schema 可编译或 synthetic mechanics 当成自然 burden 已成立。

恢复后的第一个原子任务：

```text
迁移 Stage A synthetic builders / fixtures 到 v2 R/C/P/E/M 契约
→ 实现 X62–X64 与 R02/R04/R05/R06/R07/R09/R10/R12/R15
→ 跑完整 Stage A tests + Ajv strict + py_compile
→ 交给未参与实现的 reviewer 再做 executable red-team
```

## 2. 科研主题与七步状态

待证伪命题：

> 长程 GUI 控制的 memory 必须成为可被环境证伪的行动契约；只有当 Agent 知道哪些事实必须仍然为真、为何为真以及错误后如何恢复，Memory 才真正改变能力边界。

| Step | 问题 | 状态 |
|---:|---|---|
| 1 | 自然 GUI 轨迹中是否存在足够重要、分散且可测的目标 burden | **IN PROGRESS** |
| 2 | 目标 burden 的根因是否是不可替代的 memory/context deficit | LOCKED |
| 3 | 2024–2026 强现有方法是否仍留下 residual | LOCKED |
| 4 | 新机制是否必要、充分并能分解 | LOCKED |
| 5 | 环境证伪是否优于等证据 reflection/context refresh | LOCKED |
| 6 | 增益是否独立于 token、动作、延迟和 oracle privilege | LOCKED |
| 7 | 保留、改名或停止；是否改变能力边界 | LOCKED |

## 3. Round 6 battle 得到的第一性原理结论

Stage A v1 的 X58–X60 只能证明局部完整性：

- raw 与 final 的一致性；
- bundle 内声明的时间顺序；
- bundle 内角色区间。

多对象、多轮 argument 又找到三个正交反例：

- X62 `ADJUDICATION_COLLAPSES_TO_CONSENSUS`：用精确共识防 laundering，会让真实的 substantive disagreement 无法被裁决或保留；
- X63 `EVIDENCE_SEMANTIC_NONENTAILMENT`：hash、pointer 和一致标签不能证明 evidence 在语义上蕴含 proposition；
- X64 `REJECTED_EVENT_DENOMINATOR_ERASURE`：保留 raw disposition 仍可删掉 case、A1 path 和统计分母，而 v1 PASS。

因此 Stage A v2 必须区分五个不可替代的账本：

```text
R = immutable raw labels
C = adjudication cases
P = A0→A1 paths
E = primary event rows
M = unresolved / invalid / missingness
```

同时必须把以下四类能力分开：

```text
artifact integrity
adjudication expressiveness
semantic grounding
external production authority
```

任何一个层面的 PASS 都不能推出其他层面成立。

## 4. 当前实现状态

### 4.1 Stage A v2：WIP，不可审计接受

已修改但未完成：

- `schemas/stage0f_block_a0_adjudication.schema.json`
- `schemas/stage0f_block_a0_submissions.schema.json`
- `schemas/stage0f_a0_label.schema.json`
- `schemas/stage0f_block_barrier.schema.json`
- `tools/validate_stage0f_stage_a_packet.py`

已落地的 WIP 方向：

- `consensus | blinded_human_resolution | independent_paths | unresolved`；
- lossless raw disposition、case partition、case/path/unresolved barrier freeze；
- 逐字段 resolution 与 anti-Frankenstein 检查；
- mechanical 与 human grounding 分离；
- case 最多一个 primary row；
- independent A1 path alias 防护；
- typed rejection 保留 denominator。

当前验证：

```text
5 个相关 JSON：可解析
Draft 2020-12/custom schema meta：PASS
validator：语法有效
Stage A v1 修改前基线：79/79 PASS
Stage A v2 WIP + 旧 builders：79 tests，70 failures，1 error
```

测试失败是未迁移 builders/fixtures 的已知 WIP 状态，不是可接受回归，也不能声称 v2 已工作。

### 4.2 真实 OSWorld2 归档源 projection adapter：局部完成

新增：

- `tools/verify_stage0f_osworld2_archived_source.py`
- `schemas/stage0f_osworld2_archived_source_receipt.schema.json`
- `tests/test_stage0f_osworld2_archived_source.py`
- `stage0f_osworld2_archived_source_adapter_report.md`

真实归档验证：

```text
48 archived HTML pages
47 replay-bearing pages
1 explicit no-step page
9,138 projected steps
0 issues
12/12 tests PASS
```

固定声明上限：

```text
REAL_ARCHIVED_SOURCE_PROJECTION_VERIFIED
OBSERVATION_ASSET_AUTHORITY_PARTIAL
PRODUCTION_AUTHORITY_INCOMPLETE
NO_BLOCK_A
```

这只证明已归档 HTML bytes 可被确定性投影。它不证明 screenshot bytes 存在、同动作 pre-observation 存在、发布时序可信、访问日志完整或生产 authority 闭合。

## 5. 目前已证明与未证明

已证明：

- catalog frame 648、confirmatory frame 492 与 detail availability 48/47/1/9138 可复核；
- X62、X63、X64 分别击穿 v1 的 adjudication、semantic entailment 与 denominator preservation；
- OSWorld2 本地归档 HTML 的 literal replay projection 可机械复核；
- bounds/certificate 的指定 synthetic mechanics 已通过实现测试与独立 bounded replay；
- Python 3.12.13 interpreter 与空项目 venv 存在。

未证明：

- 自然轨迹中存在足量 UACF-D burden；
- 现象达到 C0-B/C/D/E；
- Memory 是根因；
- 2024–2026 强现有方法仍有 residual；
- 行动契约方法有效；
- 环境证伪改变能力边界；
- Stage A v2 正确或完备；
- production content、time、access、role、universe authority；
- Python 3.12 精确依赖可执行或可重建。

## 6. 下一步严格顺序

1. 迁移 Stage A v2 builders/fixtures，补齐正控和全部 X62–X64/R 系列负控。
2. 完整执行 Stage A tests、Ajv strict 与 `py_compile`。
3. 让未参与实现的 reviewer 对 v2 做 executable red-team；出现反例继续 `REVISE`。
4. 对归档源 adapter 做独立 mutation audit，并把它接到 production authority 时保持 fail closed。
5. 在 Python 3.12 中安装精确依赖，执行 `pip check` 与全套验证。
6. 建立 content asset、temporal receipt、access/role history、release-tagged universe 等真实 authority。
7. 只有 integrated reviewer 明确许可，才运行 synthetic dry run。
8. 只有预注册门全部通过，才生成真实 Block A packets。
9. 由 Block A 与 confirmatory evidence 决定 Step 1；未 GO 时 Steps 2–7 继续锁定。

## 7. 恢复时禁止误读

```text
archived HTML projection PASS
不推出
production environment authority complete

Stage A v2 schema parses
不推出
Stage A v2 works

implementation mechanics
不推出
natural GUI burden exists

Step 1 IN PROGRESS
不推出
Memory is a root cause
```

## 8. GitHub 同步语义

Git 只保存研究文本、协议、代码、schema、测试与 manifest。以下本地材料按仓库既有规则不上传：

- `external/`
- `source_provenance/osworld2/raw/`
- `source_provenance/papers/*.pdf`
- `.venv*/`
- `goal_backups/`
- caches 与临时输出

它们的身份由已跟踪 manifest/hash 锚定。本 checkpoint 记录的是可恢复研究状态，不冒充完整 1.7 GB 工作区镜像。

本轮已生成内容提交：

```text
e86038d5d6d94b004b95be9bbd226bcebe2bc42d
```

随后执行用户授权的 `git push origin main`，但审批服务在创建 Git 进程前失败：

```text
Unknown parameter: input[13].namespace
```

因此不能声称 GitHub `main` 已更新。记录的本地 `origin/main` 仍是
`4bbc0a365ee0fed121bc3ffef6ea1dd0e8732e40`，且可能过时。不得用其他上传通道绕过该拒绝；下次需在用户重新授权且审批服务恢复后，从记录的 publishing clone 执行：

```text
git push origin main
```

再通过远端 ref 验证结果。
