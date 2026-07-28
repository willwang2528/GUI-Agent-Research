# ARIS 科研工作流接入说明

> 初始日期：2026-07-22  
> 最近更新：2026-07-28  
> 状态：ACTIVE  
> 目标：把 ARIS 的可恢复、可审计、对抗式科研流程接入当前 GUI Agent Memory 课题，而不是另起一个无关项目。

## 1. 本地源码来源

- 上游仓库：`wanshuiyin/Auto-claude-code-research-in-sleep`
- 本地路径：`external/Auto-claude-code-research-in-sleep`
- 上游 `main` 快照 commit：`53562a7c64cc1d55946cba1fb8a8416137143d14`
- 首次下载归档 SHA-256：`2a91d6e293777cab3b4967d0031569dfd1168fb62c599eab3fc494debb7d44c5`；codeload ZIP bytes 可随重新打包变化，只作为 historical transfer hash
- 本地源码文件数：666
- 可重运 verifier `tools/verify_aris_snapshot.py` 已明确 relative-root 与 byte serialization，并将不可复现的旧值 `9b8ae835...` 替换为 `a6badde78f282f316debe6ef6b7d775ab9085bcc10c84a49c46ba61c3459d6e5`；当前 local snapshot identity 为 **PASS**。该 PASS 只证明本地 666-file content identity，不证明完整 Git history 或上游签名真实性
- 获取方式：官方 GitHub codeload ZIP 快照；本地 Git transport 未能生成有效 refs，因此该目录不是带完整历史的 Git clone。

## 2. ARIS 技术报告与阅读方法来源

ARIS 官方技术报告：

- Title: `ARIS: Autonomous Research via Adversarial Multi-Agent Collaboration`
- Authors: Ruofeng Yang, Yongcan Li, Shuai Li
- Year: 2026
- Status: arXiv technical report；不是正式 CCF-A/B 录用论文
- arXiv: `https://arxiv.org/abs/2605.03042`
- Official PDF: `source_provenance/papers/aris_2605.03042.pdf`
- SHA-256: `2f9e22ebacb7a56b43b9675441ab18465729f2ff6f3d34175560368a116ba382`

论文阅读方法：

- S. Keshav, `How to Read a Paper`, ACM SIGCOMM Computer Communication Review, 37(3):83–84, 2007
- DOI: `https://doi.org/10.1145/1273445.1273458`
- University of Waterloo PDF: `source_provenance/papers/keshav_how_to_read_a_paper.pdf`
- SHA-256: `e3d97831bc19b60af9798bb6f0619b18bb886c0afb6ad3fc7a8b2f97512d32f7`
- 本课题适配协议：`idea-stage/docs/keshav_three_pass_evidence_protocol.md`

ARIS 技术报告的 Keshav 三遍阅读记录见：

`idea-stage/docs/aris_technical_report_keshav_reading.md`

重要边界：ARIS 报告明确说明其部署结果均为 observational，且缺少 controlled evaluation。因此它只能作为研究 harness、assurance 和持久化工作流的方法来源，不能作为 GUI Memory 问题成立、cross-family review 有因果优势或 action contract 有效的科学证据。

## 3. 采用的精华

当前课题只采用六项与科学有效性直接相关的机制：

1. **Problem Anchor**：每轮必须保持同一底层问题，禁止把“长任务难”偷换成“Memory 是根因”。
2. **Claim → Evidence → Gate**：每个结论先写最低证据与反证条件，不以结果后叙事补救。
3. **角色隔离**：执行者不审判自己的协议、标注和实验；审稿代理直接读取原始文件。
4. **Type-A / Type-B 分离**：文件存在、哈希一致、样本数完成属于 Type-A；“问题已证明”“方法有效”属于 Type-B，不由执行者自我放行。
5. **版本化与可恢复状态**：当前科研状态保存在 `refine-logs/REFINE_STATE.json`；每轮批评、修订和原始审稿结果均留痕。
6. **Evidence → Claim Assurance**：实验完整性、result-to-claim 映射和 paper-claim audit 分层执行；本课题进一步把 advisory audit 提升为 fail-closed scientific gate。

## 4. 不直接采用的部分

- 不安装或运行全部 ARIS skills；只借用与本课题匹配的工作流契约。
- 不复制 ARIS 的 `CLAUDE.md` 覆盖当前项目。
- 不在 Step 1 通过前运行完整 `research-refine-pipeline`，因为方法和实验计划尚不应被当成稳定对象。
- 当前不运行 `kill-argument`；该流程适合已有论文草稿后的拒稿压力测试，不适合尚在证明问题的阶段。
- 同系列 Codex subagents 的一致意见只记为 `same-family / provisional`，不记为独立跨模型 acceptance。
- 不把 ARIS 的保守假设“single-agent long-horizon research is unreliable”当成经验证定律；不把 bandit/two-player analogy 当成因果或理论证明。
- 不以 ARIS 的一次 8 小时观察性 trajectory、reviewer score 或社区 adoption 证明任何 GUI Memory 科学命题。

## 5. ARIS 与本课题七步的映射

| 本课题步骤 | 科学问题 | ARIS 机制 | 当前状态 |
|---|---|---|---|
| Step 1 | benchmark-natural 的 UACF-D 是否存在且负担足够 | Problem Anchor + preregistration + claim-driven pilot | **IN PROGRESS** |
| Step 2 | E/G/R/P/S/A/V 中哪个边界是根因 | experiment-plan + integrity audit | LOCKED |
| Step 3 | 冻结强系统是否仍有 residual | research-review + matched baseline audit | LOCKED |
| Step 4 | 最小可部署机制是否修复根因 | research-refine | LOCKED |
| Step 5 | 新环境证据是否优于同证据 reflection | novelty isolation + ablation | LOCKED |
| Step 6 | 增益是否来自额外 token、动作、延迟或特权真值 | experiment-audit + result-to-claim | LOCKED |
| Step 7 | 保留 Memory 题、改名或终止 | acceptance gate + hostile review | LOCKED |

## 6. 当前唯一允许推进的工作

1. 先把 `REFINE_STATE` 和 tracker 纠正为 Round 3 `REVISE / validator FAIL`；
2. 不打开 outcome，先完成 prereg v0.6 的 A0/A1 时间门、coordinator sidecar、全 measurement-stack branching、canonical hash、随机数与 matcher；
3. decision card 增加 C0-E；pure-world 环境门未通过时强制改题或阻断环境主张；
4. 修正 C1-R 为 R-boundary total downstream effect，并严格区分 C3-a representation gain 与 C4 capability boundary；
5. 重建 coordinator/A0/A1/audit-event schemas，执行 Draft 2020-12 Schema 后再做跨字段语义验证；
6. 独立负例全部通过后才进入 Round 4 oracle/fresh/reproduction battle；
7. 只有 Round 4 三方都给出 `READY FOR BLOCK-A DRY RUN` 才开放真实 packets；
8. 只有根因桥通过后才创建方法级 `FINAL_PROPOSAL.md`。

## 7. 权威文件

- 活跃研究契约：`idea-stage/docs/research_contract.md`
- 当前问题锚：`refine-logs/round-0-problem-anchor.md`
- Step 1 计划：`refine-logs/PROBLEM_VALIDATION_PLAN.md`
- Step 1 追踪器：`refine-logs/EXPERIMENT_TRACKER.md`
- 数值判定唯一来源：`stage0f_step1_decision_card.md`
- 详细预注册：`stage0f_osworld2_natural_burden_preregistration.md`
- 论文阅读门：`idea-stage/docs/keshav_three_pass_evidence_protocol.md`
- ARIS 报告阅读记录：`idea-stage/docs/aris_technical_report_keshav_reading.md`
- 论文 provenance：`source_provenance/papers/manifest.json`
