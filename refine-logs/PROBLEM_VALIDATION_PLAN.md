# Step 1 Problem Validation Plan

**Problem**：公开 OSWorld 2.0 目录中是否存在足够且可实验研究的 UACF-D 行为负担？  
**Date**：2026-07-22  
**Evaluation type**：`published_catalog_observational_audit`  
**Claim ceiling**：只能支持进入竞争性根因实验，不能支持 Memory 根因或方法有效性。

## Claim Map

| Claim | 为什么重要 | 最低说服力证据 | 关联实验块 |
|---|---|---|---|
| C0-A：UACF-D 可可靠识别 | 否则“没有发现”和“无法观察”不可区分 | 盲标协议、未见 validation、rare-label reliability、prefix-only audit | B1、B2 |
| C0-B：目录内负担值得进入 Step 2 | 防止由单个 highlighted case 启动复杂方法 | ≥8 positive task ids、strict-lower correctness deficit ≥1.0 | B3 |
| C0-C：存在候选因果接口 | 没有 interface 就无法构造根因实验 | ≥8 positive task ids 各有 non-privileged candidate interface inventory | B4 |
| C0-D：catalog structural dispersion | 防止 3:1:1:1 模型暴露或单一 site/group 制造表观集中；不做 exposure 根因推断 | outcome-blind 互斥 mapping 与 exposure-normalized concentration | B4 |

## Anti-claims to Rule Out

- 阳性只是 evaluator-invalid、纯 actuation、API error、budget termination 或环境故障；
- 候选由后见 outcome、challenge tag 或未来轨迹泄漏产生；
- 结论只来自单个 task template、site/app 或 model family；
- missing traces 被 complete-case 删除后制造阳性；
- 648 条 hosted catalog trajectories 被错误解释为全部 launched runs 的随机样本。

## Experiment Blocks

### B0：目录与分母冻结

- **Claim tested**：研究总体与可用证据边界可审计。
- **Inputs**：108 tasks、6 hosted configs、公开轨迹字段、snapshot checksum。
- **Success criterion**：648/648 catalog cells 存在；24-task reserve、Task 035、Task 065 在 outcome 前固定排除；`T0-Holdout = 492`。
- **Failure interpretation**：目录 frame 不完整时，Step 1 暂停并重建分母。
- **Status**：PASS for catalog frame；launched-run census 仍 LOCKED。

### B1：Ontology development packet

- **Claim tested**：标注者能在不看未来 outcome 的条件下识别 delivered update opportunity、必要谓词、依赖边与 competing causes。
- **Tasks**：Block A `009, 066, 073, 020, 083, 029, 050, 024`，每 task 六个模型。
- **Blindness**：同 task 的六份 Stage A packet 全部冻结后，才允许看任一 Stage B。
- **Adequacy gate**：至少 12 个 delivered opportunities、来自至少 4 个 task ids、覆盖四类 action 中至少三类，且全部 Stage A 字段可执行。
- **Success criterion**：codebook 可执行；不以阳性率判断成功。
- **Failure interpretation**：按预定规则使用 Block B 开发并保留 Block C；24-task reserve 用尽仍不足则 `UNIDENTIFIABLE`。
- **Priority**：MUST-RUN / NEXT。

### B2：Unseen reliability validation

- **Claim tested**：UACF-D 与 competing-cause 标签在未见数据上可复核。
- **Tasks**：优先 Block B；若仅允许一次手册修订，则 Block C 为最终未见 validation。
- **Metrics**：独立 complete-prefix reference event set 上的 generator event recall/F1、inter-generator coverage（诊断项）、supplemental random non-candidate audit、positive/negative agreement、decision-point overlap、dependency-edge agreement 与 competing-cause macro F1。
- **Success criterion**：严格按主协议的数值 gate；rare-label reliability 还需至少 4 个 positive task ids 与 8 个 positive events；不足时记 `UNIDENTIFIABLE`，不得记 1。
- **Failure interpretation**：Block C 仍有 blocking metric 失败则停止，不进入 held-out burden。
- **Priority**：MUST-RUN。

### B3：492-unit confirmatory burden audit

- **Claim tested**：冻结 published-catalog holdout 中是否存在足够 UACF-D candidate supply 与 correctness burden。
- **Candidate generation**：prefix-only streaming、append-only log、禁止 future outcome 和作者标签。
- **Primary metrics**：`known_positive_task_ids`、unit bounds、strict/optimistic correctness-deficit bounds。
- **Success criterion**：数值只读取 `stage0f_step1_decision_card.md`；不得在结果后修改。
- **Failure interpretation**：分别输出 C0-A/B/C/D；不使用模糊的 qualified GO，也不让 replay 不就绪否定独立成立的 burden。
- **Priority**：MUST-RUN。

### B4：结构分散、missingness 与 replay feasibility

- **Claim tested**：结果不由一个结构簇或一个模型家族垄断，并且候选具有 Step 2 protocol construction 所需的接口线索。
- **Blindness**：structure mapping 只看 instruction 与静态 metadata，在 confirmatory outcome 前冻结。
- **Metrics**：`K_group`、`K_site_or_app_set`、`K_model_family`、三套 positive/deficit concentration、unit-level missingness bounds、replay-feasible task ids。
- **Success criterion**：满足决策卡第 4、5、7 节全部条件，并把 `interface_observed` 与实际 implementable/faithful/isolated replay 分开。
- **Failure interpretation**：mapping 或 bounds 无法识别时输出 `UNIDENTIFIABLE`；没有 candidate interface 时只令 C0-C `ABSENT` 并阻断因果 pipeline，不否定独立成立的 C0-B。
- **Priority**：MUST-RUN。

## Run Order and Gates

| Milestone | 目标 | 输入 | 决策门 | 当前状态 |
|---|---|---|---|---|
| M0 | frame / protocol consistency | Stage 0F files | 492 denominator；无双重阈值 | DONE |
| M1 | 生成 Block A Stage A packets | 48 units | 无 future leakage；packet fields complete | TODO |
| M2 | ontology development | Block A + isolated training/stress | 12/4/3 adequacy；不估 burden | TODO |
| M3 | unseen reliability | Block B / C | reliability gate PASS，否则 UNIDENTIFIABLE | TODO |
| M4 | confirmatory audit | 492-unit holdout | decision card | LOCKED |
| M5 | Step 1 adjudication | B1–B4 outputs | C0-A / C0-B / C0-C / C0-D 四维裁决 | LOCKED |
| M6 | Step 1.5 replay identification | positive interface candidates | `stage0f_step1_5_replay_identification_card.md` 的 A–E 与四种穷尽裁决 | LOCKED |

## Integrity Rules

- 执行 annotation packet 生成的角色不得单独审判盲化是否成立；
- 标注协议审稿者直接读取原始 packet schema 与日志，不接受执行者摘要代替；
- 每个 claimed number 必须追踪到 unit-level artifact；
- 任何 pilot 结果必须标注精确 N、task ids、model configs 与 missing units；
- 观察性共现不得命名为 caused loss、repair effect 或 preventable loss。

## First Three Actions

1. 固化 Block A 的 48-unit data-availability manifest；
2. 生成不含 future outcome 的 Stage A packet schema 和一份 dry-run packet；
3. 由 protocol reviewer 与 reproduction auditor 独立检查盲化、分母、字段可恢复性和执行成本。
