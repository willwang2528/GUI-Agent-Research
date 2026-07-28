# Stage 0F Block A：48-unit Data-Availability Manifest

> manifest_version: `0.2`  
> fetched_at: `2026-07-22T23:10:33+08:00`  
> detail_audited_at: `2026-07-28`  
> source: OSWorld 2.0 official `/api/tasks/brief`、`/api/available-configs` 与冻结详情页快照  
> scope: catalog frame + detail-field availability；不含 outcome truth  
> status: `CATALOG PASS / DETAIL FRAME AUDIT COMPLETE / REPLAY AVAILABILITY PARTIAL / TRUTH BLOCKED`

## 1. 这个 manifest 证明什么

对预注册 Block A 的 8 个 task ids × 6 个 hosted configs：

- 48/48 `T0-Catalog` cells 均存在；
- 每个 cell 的 `trajectory_count = 1`，`selected_trajectory_id = task_id`；
- 47 个 catalog status 为 `Done`，Task 050 × Claude Opus 4.7 为 `Done (Max Steps)`；
- observed steps 范围为 38–500，48 units 合计 9,947 个 index-reported steps；这只是后续截图/packet 成本上界线索，不等于 9,947 个独立 decision points；
- 六个配置的 `max_steps = 500`，但 GPT-5.5 与 Qwen 使用 batch-tool `model_steps`，其余四个使用 standard steps。
- 固定的 8 个 task ids（009、020、024、029、050、066、073、083）× 6 个 hosted config filenames，共 48 个预期详情页文件，48/48 均存在；
- 47/48 页面包含结构有效的 embedded replay，共 9,138 个 steps；这些页面的 replay root 与预期 filename/task/trajectory 绑定一致；
- `050__MiniMax-M3.html` 不含 replay root 或 replay JSON，而是明确显示 `No step data available`；因此详情 frame 审计可以完成，但 replay availability 只能是 `PARTIAL`；
- 47/47 valid replay 的每一步均有 timestamp 与 label；45/47 页面每一步都有 screenshot URL，另外两页各缺 1 个 URL；
- 页面含 9,138 个 raw-action `<pre>` blocks，但当前严格 JSON 解析仅 2/9,138 成功；不能把“block 存在”写成“raw JSON 可用”。

它不证明：

- launched-run、retry、discard 或 publication-selection 完整；
- screenshot URL 可下载、内容哈希正确，或 screenshot/raw-action 字段全部可恢复；
- trajectory 与 release-tagged instruction、task class、evaluator 的逐运行绑定；
- final truth 可独立重放；
- 环境 replay 能成功；
- 任一 unit 是 UACF-D positive、negative 或 no-opportunity。

详情页 replay payload 只含 `steps` 与 `total_steps`，不含 `task_id`、`model_name` 或 `trajectory_id`。因此当前 identity check 的上限只是：页面 root 与固定 filename 一致，root 的 `trajectory_id == task_id`，且 `total_steps == len(steps)`。这不是独立 run provenance。

本文件是 coordinator-only provenance。Stage A/Stage B 标注包不得包含 `catalog_status`、catalog-reported `observed_steps` 总数、last update 或任何 score；A0 为时间门所必需的 redacted prefix records 不属于该禁止项。

## 2. Unit manifest

| Task | Model | Budget mode | Catalog status | Observed steps | Last update | Catalog cell |
|---|---|---|---|---:|---|---|
| 009 | Claude Opus 4.7 | standard steps | Done | 225 | 2026-05-29 16:55:10 | PASS |
| 009 | GPT-5.5 | batch-tool model_steps | Done | 94 | 2026-06-10 02:32:48 | PASS |
| 009 | Claude Sonnet 4.6 Max | standard steps | Done | 215 | 2026-06-11 09:57:52 | PASS |
| 009 | Claude Sonnet 4.6 Medium | standard steps | Done | 264 | 2026-06-05 21:12:29 | PASS |
| 009 | MiniMax M3 | standard steps | Done | 115 | 2026-06-09 17:04:25 | PASS |
| 009 | Qwen 3.7-Plus | batch-tool model_steps | Done | 67 | 2026-06-13 14:07:58 | PASS |
| 066 | Claude Opus 4.7 | standard steps | Done | 200 | 2026-05-27 22:54:09 | PASS |
| 066 | GPT-5.5 | batch-tool model_steps | Done | 71 | 2026-06-10 09:18:20 | PASS |
| 066 | Claude Sonnet 4.6 Max | standard steps | Done | 87 | 2026-06-11 13:23:09 | PASS |
| 066 | Claude Sonnet 4.6 Medium | standard steps | Done | 61 | 2026-06-05 22:30:29 | PASS |
| 066 | MiniMax M3 | standard steps | Done | 202 | 2026-06-10 09:58:45 | PASS |
| 066 | Qwen 3.7-Plus | batch-tool model_steps | Done | 67 | 2026-06-13 18:01:16 | PASS |
| 073 | Claude Opus 4.7 | standard steps | Done | 167 | 2026-05-27 22:59:47 | PASS |
| 073 | GPT-5.5 | batch-tool model_steps | Done | 100 | 2026-06-10 10:32:08 | PASS |
| 073 | Claude Sonnet 4.6 Max | standard steps | Done | 91 | 2026-06-11 12:53:41 | PASS |
| 073 | Claude Sonnet 4.6 Medium | standard steps | Done | 123 | 2026-06-05 22:47:18 | PASS |
| 073 | MiniMax M3 | standard steps | Done | 371 | 2026-06-10 12:15:13 | PASS |
| 073 | Qwen 3.7-Plus | batch-tool model_steps | Done | 90 | 2026-06-13 18:26:31 | PASS |
| 020 | Claude Opus 4.7 | standard steps | Done | 68 | 2026-05-29 17:12:45 | PASS |
| 020 | GPT-5.5 | batch-tool model_steps | Done | 81 | 2026-06-10 17:24:34 | PASS |
| 020 | Claude Sonnet 4.6 Max | standard steps | Done | 38 | 2026-06-11 09:32:57 | PASS |
| 020 | Claude Sonnet 4.6 Medium | standard steps | Done | 52 | 2026-06-05 20:49:00 | PASS |
| 020 | MiniMax M3 | standard steps | Done | 52 | 2026-06-11 02:42:05 | PASS |
| 020 | Qwen 3.7-Plus | batch-tool model_steps | Done | 47 | 2026-06-13 03:03:33 | PASS |
| 083 | Claude Opus 4.7 | standard steps | Done | 358 | 2026-05-27 23:57:35 | PASS |
| 083 | GPT-5.5 | batch-tool model_steps | Done | 142 | 2026-06-10 13:05:04 | PASS |
| 083 | Claude Sonnet 4.6 Max | standard steps | Done | 304 | 2026-06-11 13:56:43 | PASS |
| 083 | Claude Sonnet 4.6 Medium | standard steps | Done | 274 | 2026-06-05 23:47:46 | PASS |
| 083 | MiniMax M3 | standard steps | Done | 308 | 2026-06-11 07:21:25 | PASS |
| 083 | Qwen 3.7-Plus | batch-tool model_steps | Done | 213 | 2026-06-13 19:44:09 | PASS |
| 029 | Claude Opus 4.7 | standard steps | Done | 498 | 2026-05-27 21:32:55 | PASS |
| 029 | GPT-5.5 | batch-tool model_steps | Done | 151 | 2026-06-10 04:43:40 | PASS |
| 029 | Claude Sonnet 4.6 Max | standard steps | Done | 366 | 2026-06-11 11:06:48 | PASS |
| 029 | Claude Sonnet 4.6 Medium | standard steps | Done | 430 | 2026-06-06 06:30:35 | PASS |
| 029 | MiniMax M3 | standard steps | Done | 348 | 2026-06-10 03:48:25 | PASS |
| 029 | Qwen 3.7-Plus | batch-tool model_steps | Done | 80 | 2026-06-13 03:54:50 | PASS |
| 050 | Claude Opus 4.7 | standard steps | Done (Max Steps) | 500 | 2026-05-27 22:42:27 | PASS |
| 050 | GPT-5.5 | batch-tool model_steps | Done | 77 | 2026-06-10 06:53:51 | PASS |
| 050 | Claude Sonnet 4.6 Max | standard steps | Done | 427 | 2026-06-11 12:50:31 | PASS |
| 050 | Claude Sonnet 4.6 Medium | standard steps | Done | 330 | 2026-06-05 23:00:38 | PASS |
| 050 | MiniMax M3 | standard steps | Done | 350 | 2026-06-11 14:43:51 | PASS |
| 050 | Qwen 3.7-Plus | batch-tool model_steps | Done | 321 | 2026-06-16 03:22:31 | PASS |
| 024 | Claude Opus 4.7 | standard steps | Done | 391 | 2026-06-08 12:55:04 | PASS |
| 024 | GPT-5.5 | batch-tool model_steps | Done | 114 | 2026-06-10 17:27:31 | PASS |
| 024 | Claude Sonnet 4.6 Max | standard steps | Done | 186 | 2026-06-11 09:53:12 | PASS |
| 024 | Claude Sonnet 4.6 Medium | standard steps | Done | 172 | 2026-06-05 21:02:22 | PASS |
| 024 | MiniMax M3 | standard steps | Done | 464 | 2026-06-09 22:21:41 | PASS |
| 024 | Qwen 3.7-Plus | batch-tool model_steps | Done | 195 | 2026-06-13 03:58:07 | PASS |

## 3. Availability matrix

| Field | 48-unit status | Meaning |
|---|---|---|
| catalog cell | 48/48 PASS | brief endpoint returns exactly one selected trajectory per cell |
| instruction shown by current catalog | 48/48 AVAILABLE | not yet bound to the exact historical Agent input |
| catalog status / progress / timestamp | 48/48 AVAILABLE | coordinator metadata only; hidden from annotators |
| fixed detail-page frame | 48/48 AUDITED | all expected filenames present; detail tree SHA-256 is `7aada049e5711fc10f13162660d8e24670ac4cc694f4a01e1ece19f05e8b6d56` |
| embedded replay | 47/48 AVAILABLE, PARTIAL | 47 structurally valid replays; `050__MiniMax-M3.html` explicitly says `No step data available` |
| embedded replay steps | 9,138 AVAILABLE | availability count only; not independent decision points or verified actions |
| step timestamp / label | 47/47 COMPLETE within valid replays | every embedded step has both fields |
| per-step screenshot URL | 45/47 COMPLETE within valid replays | two replay pages each miss one URL; URL presence is not download/hash verification |
| raw-action blocks | 9,138 PRESENT; 2/9,138 JSON-PARSEABLE | current strict auditor cannot treat the remaining blocks as usable JSON |
| page-local identity binding | 47/47 CONSISTENT within valid replays | root matches fixed filename and task trajectory; replay payload itself has no identity fields |
| release-tagged task class | 0/48 VERIFIED | source is gated and current `main` may differ from `v2026.06.24` |
| evaluator hash / replay | 0/48 VERIFIED | independent truth not available from brief API |
| run id / seed / retry history | 0/48 AVAILABLE | `T1-Run` remains locked |

## 4. Current decision

- `S1-M1-01 catalog manifest`：DONE。
- `S1-M1-02c detail availability audit`：DONE；默认 audit 在 48 个 unit 各自为 valid replay 或 explicit-no-step 时 exit 0。
- 使用 `--require-all-replay` 会因 47/48 replay coverage 而 exit 1；这是预期的严格模式结果。
- 旧的 `S1-M1-02a Stage A schema / leakage linter` 结果已被 supersede；它不能由本次 availability audit 代替。
- `S1-M1-02b real Stage A packet set`：仍为 TODO。
- 当前不能解封 Block A outcome annotation，更不能开始 492-unit confirmatory audit。
- 下一步必须单独完成 Stage A schema/semantic/negative-fixture gate、截图内容获取与哈希，以及 release-tagged truth/evaluator provenance。`050__MiniMax-M3.html` 必须保持 `replay-unavailable / truth-unverified`，不得从 catalog status 补写 outcome。

机械复核命令：

```bash
python3 tools/audit_stage0f_detail_pages.py \
  source_provenance/osworld2/raw/detail_pages \
  --output source_provenance/osworld2/detail_audit.json
```
