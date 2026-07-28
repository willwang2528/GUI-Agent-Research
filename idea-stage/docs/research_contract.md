# Research Contract：Environment-Falsifiable Action-State Memory for Long-Horizon GUI Control

> contract_version: `0.3`  
> date: `2026-07-22`  
> last_updated: `2026-07-28`  
> language: `zh`  
> status: `problem-validation`  
> acceptance_status: `provisional`  
> current_gate: `Step 1 IN PROGRESS`
> paper_reading_protocol: `idea-stage/docs/keshav_three_pass_evidence_protocol.md`

## Selected Research Hypothesis

用户提出的候选中心命题是：

> 长程 GUI 控制的 memory 必须成为可被环境证伪的行动契约；只有当 Agent 知道哪些事实必须仍然为真、为何为真以及错误后如何恢复，Memory 才真正改变能力边界。

这句话当前是**待证伪假设**，不是研究结论。它包含五个需要串行拆开的主张：

1. 长程 GUI 中存在这样的自然行为现象：新证据已送达，但后续动作或产物仍与预先冻结的旧命题相容、与新命题下的规范动作不相容；
2. 该现象造成足够且可测的终态 correctness burden；
3. 其中由外部 world truth 改变触发、而不是 goal change、corrective feedback 或 hidden-fact revelation 触发的纯环境子集也达到预冻结门槛，因而足以支撑 `Environment-Falsifiable` 题名；
4. 根因中存在不能被 grounding、planning、actuation 或 verifier 充分替代解释的 persistent-state / dependency-repair deficit；
5. 可被环境证伪的 typed action contract 在等语义信息、等预算条件下优于普通事实 Memory、完整 flat state 与 generic reflection，并在预冻结难度轴与未见 family 上改变能力 frontier。

任一前置主张失败，后续主张不得继续沿用原题。

## Immutable Problem Anchor

> 在冻结的 multi-step GUI published trajectories 中，是否存在如下可观察表型：decision point 前的 observation/history 出现了与 `p_old` 不相容的 `p_new`；outcome-independent normative schema 表明两者对应不同的正确动作或 obligation；后续可观察 action/artifact 与 `p_old` 相容、与 `p_new` 下的规范动作不相容；并且同一条预冻结 dependency chain 上伴随 terminal correctness deficit？该定义不主张 Agent 内部表示了 `p_old`，也不主张 `p_old` 导致了动作。

这个 Anchor 以问题形式冻结。任何把它缩减为“长轨迹成功率低”、把 multi-step scope 写成长程因果变量，或提前扩张为“Memory 已被证明是根因”的改写都属于 drift。若该表型具有足够目录内负担与 candidate replay interfaces，后续 matched replay 才比较 E/O/G/R/P/S/A/V 及 Environment、Evaluator/Task、Budget/API。

## Three Why Obligations

### Why 1：为什么这是一个重要问题

这里的“重要”只指：该现象在冻结 benchmark holdout 中非孤例、具有可测 correctness burden，并足以供应后续根因实验；它不等于生产、经济或普遍 GUI 风险。必须同时给出：

- 定性证据：可复核的 update → stale dependency → downstream inconsistency 链；
- 定量证据：在预冻结 `T0-Holdout` 中的 candidate supply、correctness burden、结构分散性与 missingness bounds；
- 可实验性证据：至少八个不同 positive task ids 具有 non-privileged candidate replay interface；实际因果执行还需 Step 1.5。

作者 highlighted case、challenge tag、人工 interruption 或平均轨迹更长都不能单独完成证明。

### Why 2：为什么现有方法不行

只有 Step 2 先隔离根因，Step 3 才能在冻结的强组合系统上问 residual。必须比较并控制：

- 当前环境证据是否进入 observation；
- grounding 是否正确；
- persistent state 是否更新且 action-time 可读；
- 受影响 artifact / obligation 是否被传播；
- semantic action、GUI realization 与 post-action verification 是否正确；
- token、动作次数、延迟、模型调用和特权信息是否匹配。

不能用“某篇论文没有 recovery 字段”证明方法无恢复能力，也不能用一个弱 baseline 失败代表全部现有方法失败。

### Why 3：为什么候选 idea 可能可行

现阶段只允许论证**可检验性**，不允许声称有效。候选 idea 可行的最低逻辑是：

1. 环境能够产生会推翻 action-relevant state 的新证据；
2. 预先冻结的旧命题与可外显的 dependent actions / artifacts / obligations 存在 outcome-blind 规范依赖；
3. 失效检测、依赖传播与恢复可以形成可部署干预边界；
4. typed contract 与 flat-complete state 可以在 action-relevant semantic information closure 双向无损相等、更新时机与预算相同的条件下对照；
5. 若 typed contract 无独立增益，实验能够否定“结构本身改变能力边界”。

因此“可行”只表示存在干净的因果识别路径，不表示结果必然为正。

## Claim Ladder and Evidence Ceiling

| Claim | 最低证据 | 当前状态 | 当前允许表述 |
|---|---|---|---|
| C0-A：observable phenotype 可可靠识别 | action reveal 前逐 ordinal location commitment、独立 A0 event freeze、full-block A0→A1 barrier、未见 validation、reliability 与 global missingness bounds | PENDING | 只能说已有案例级线索 |
| C0-B：published holdout burden 超过冻结门槛 | ≥8 task ids、strict-lower deficit ≥1.0 | LOCKED | 不得外推生产重要性 |
| C0-C：存在 candidate replay interfaces | ≥8 positive task ids 的 non-privileged interface inventory | LOCKED | 只能开放 Step 2 protocol construction |
| C0-D：catalog structural dispersion | outcome-blind mapping 与 exposure-normalized dispersion/concentration gate | LOCKED | 只证明目录内分散，不证明“不是 exposure 造成”；失败时只允许窄范围根因研究 |
| C0-E：pure-world-transition 子集足以支撑环境主张 | `update_source_labels = [world_truth_changed]` 的冻结子集单独通过决策卡的 supply、burden 与 interface 门；混合 update 不计入 | LOCKED | `SUPPORTED` 才可能保留 `Environment-Falsifiable` 题名；`BELOW_FROZEN_GATE` 强制改名，`INCONCLUSIVE / UNIDENTIFIABLE` 阻断环境题名 |
| Bridge 0→1：同系统 phenotype 可重现或 transport 范围明确 | system/environment identity、control replay、boundary isolation | LOCKED | reconstructed Agent 不得解释原 hosted Agent 内部根因 |
| C1-R：`R→P` boundary payload 的 total downstream effect | 固定 upstream evidence、系统配置、payload schema/serialization/visibility、预算与某一 P arm，只改变 stale vs correct 的预注册 R payload；允许 planner tokens、S/A/V 与 action trajectory 作为下游中介改变 | LOCKED | 只有边界效应成立才支持 Memory track；不得冒充不经 planner/action 的直接效应 |
| C1-P：dependency-repair mechanism 的主效应与 R×P 交互 | 冻结 `R ∈ {stale, correct}` × `P_operator ∈ {identity_no_propagation, flat_scan, dependency_graph_propagation}` factorial；共同 consumer API、相同 R payload/semantic closure，各 cell 保持同一 upstream/config/format/budget | LOCKED | P 单独成立而 R 不成立时改题为 planning/artifact repair；交互必须与主效应分报 |
| C2：强现有系统仍有 residual | 同一 causal estimand、任务分布与 matched budget | LOCKED | 不得声称全部现有方法不行 |
| C3-a：typed representation 在 semantic information closure 下有独立增益 | flat-complete 与 typed-complete 必须双向无损恢复同一 proposition、version、evidence/refutation、dependency、obligation、deadline、uncertainty 与 recovery-option closure，并匹配更新时机和预算 | LOCKED | 只支持“表示/可执行算子在固定分布上的增益”；不得用隐藏的关系、恢复提示或额外真值冒充结构增益，也不构成能力边界证据 |
| C3-b：invalidation、propagation、recovery gate 的作用可分解 | factorial ablation 与交互 | LOCKED | 不得把复合系统整体提升归因于 Memory |
| C4：改变能力边界 | 在预冻结难度轴上估计 slope/interaction 与可解决 frontier/upper limit 的改变，并在预注册未见 structural/task family 上保留；若主张跨模型，还须在未见 model family 保留 | LOCKED | 平均成功率、C3-a 固定分布增益或单一 seen-family 外推均不够；否则最多称 robust performance gain |

前一 claim 只负责解锁后一 claim 与 bridge 的测试，不逻辑蕴含后一 claim。

C1-R 的目标 estimand 冻结为 **`R→P` boundary payload total downstream effect**，而不是“不经过 planner/action 的 R 直接效应”。在同一个 P arm 内，observation/evidence prefix、grounding result、Agent architecture/weights、system/developer prompt template、tool/API version、payload schema、字段顺序与 serialization、payload 的来源/可见性/注入时点、token/action/time budget 必须固定；唯一有意改变的是预注册命题在 R payload 中的 stale/correct value、version 与 validity。由此导致的 planner reasoning tokens、dependent-state propagation、semantic action、GUI realization、verification 与 recovery 变化是合法中介，不能为了“控制 P/S/A/V”而冻结。

C0-E 的 source uncertainty 与 measurement failure 必须分开：schema-valid packet 的 labels 恰为 `[source_unidentifiable]` 且具有 auditable reason/search scope 时派生 `SOURCE_UNKNOWN`；空标签、未知标签、非法组合、缺 direct pointer 或 provenance 的 packet 派生 `INVALID_SOURCE_MEASUREMENT`。后者不是 source category，不能贡献 lower 或 detected source roster；但只要没有合法 global strict-negative certificate，它对应的 task/unit 仍以 measurement-missing placeholder 进入 worst-case upper。

主分析采用 `R ∈ {stale, correct}` × `P_operator ∈ {identity_no_propagation, flat_scan, dependency_graph_propagation}` factorial。三个 P arms 均经同一 versioned consumer API 接收相同 R payload 与相同 action-relevant semantic closure；`identity_no_propagation` 仍消费 R，只不传播依赖。每个 P arm 必须验证 operator identity、closure hash、非目标 fingerprint 与预算。R 的 cell 内 simple effects、P 的主效应和 R×P interaction 分别报告。这个设计能定位边界效应是否依赖 dependency-repair operator，但不自动识别自然 Agent 内部的 latent memory state。

claim ceiling 按干预纯度下调：

1. 只有 stale/correct 的 canonical R payload 语义值改变，且上述 upstream/config/format/visibility/budget 均匹配：可称 `R→P boundary payload total downstream effect`；
2. 若同时改变 payload 来源、可见性、字段、serialization、长度档位、instruction cue、privileged truth 或预算，即使用 padding 也不能把结果归因于 R；最多称 `state-conditioning package effect`，并逐项列出 bundle；
3. 若 bundle 无法完整记录或 factorial cell 不可复现：C1-R = `UNIDENTIFIABLE`。

C3-a 与 C4 是两个不可互换的证据层。`semantic information closure` 要求 flat 与 typed 两臂存在 outcome-blind、可自动验证的双向转换，并由唯一 machine-readable closure schema 逐字段验证 proposition/value、version、evidence、refutation、timestamp、validity condition、dependency edge、obligation、deadline/commit point、uncertainty、recovery option 与 source provenance 全部相等；若 typed arm 多出任一 action-relevant atom、relation 或环境真值，实验测到的是 information-set gain，不是 typed representation gain。validator 必须同时检查 `decode(flat) == canonical_closure`、`decode(typed) == canonical_closure` 及两方向 roundtrip preservation。即使 C3-a 在固定分布上 PASS，也必须另做预注册 difficulty-axis scaling/frontier 估计和 unseen-family confirmatory test，C4 才可能 PASS。

C4 在任何 outcome 前还必须冻结：难度变量及离散层级、成功判据 `tau`、family holdout 规则、slope/interaction estimator、预注册方向与最小 interaction effect `delta_min`、至少一个完整 difficulty level 的最小 frontier extension、simultaneous uncertainty/multiplicity procedure 与 frontier estimator。`frontier` 定义为“从最低难度开始，在 simultaneous lower band 下连续不低于 `tau` 的最大难度层级”；一旦中间 level 失败，不能跳过后在更高 level 重启 frontier。C4 PASS 同时要求 method×difficulty interaction 达到 `delta_min` 与至少一个预注册 level 的 frontier extension，并在未见 structural/task family 的 confirmatory split 上同时保留；extension level 还要求 method lower band ≥ `tau` 且 baseline upper band < `tau`。多个 difficulty axes 必须预先指定 primary axis 或对 axes 做 familywise multiplicity control。若论文声称跨 Agent 架构，还必须在未见 model family 复现。只满足其中一项、使用 pointwise CI 结果后挑 level，或只在 seen family 上平均提升，均停留在 C3/robust-gain ceiling。

## Seven-Step Falsification Funnel

1. **证明现象**：确认 benchmark-natural UACF-D 的候选数量、correctness burden 和可实验入口；另以 C0-E 单独裁决 pure-world-transition 子集是否足以支撑 `Environment-Falsifiable` 题名。
2. **识别根因**：先通过 Step 1.5 的 same-system reproduction / explicit transport gate，再区分 E/O/G/R/P/S/A/V 及外部 competing causes；Memory 只在 C1-R 的 `R→P` boundary payload total downstream effect 获得支持时存活。
3. **挑战现有方法**：冻结强组合系统与预算，检验 residual，不代表所有方法。
4. **方法验证**：实现最小可部署机制，检验充分性、必要性与交互。
5. **环境证伪**：比较新环境证据与同一旧证据上的 reflection。
6. **等预算审计**：排除 token、动作、延迟、覆盖率、人工接管与特权真值。
7. **Go / No-Go**：预先决定保留 Environment-Falsifiable Memory 题、改名为一般 evidence/update consistency 或 plan/artifact repair，或终止。若要写“改变能力边界”，必须预冻结 update-to-decision lag、intervening subgoals、dependency depth/fan-out、conflicting updates 或 irrelevant-history interference 中至少一个难度轴，证明 scaling slope 或成功 frontier/upper limit 改变，并在预注册 unseen family 保留。

## Literature and Venue Constraints

- 核心论文池只使用 2024、2025、2026 年工作，优先 2025–2026。
- 优先 CCF-A / CCF-B 与高影响力期刊；极具影响力的新方向可以保留 arXiv，但必须显式标注未正式发表。
- 2023 及更早论文只能作为历史背景或概念源，不得替代 2024–2026 的最近对照。
- 每篇核心论文必须从第一性原理回答：解决了哪个状态、信息或决策约束；假设是什么；在 GUI 长程控制中哪个根因仍未被处理。
- 任何进入分析的相关论文都必须执行 `idea-stage/docs/keshav_three_pass_evidence_protocol.md`：Pass 1 的 5C 负责筛选，Pass 2 建立 claim–evidence–limitation 矩阵，Pass 3 虚拟复现并攻击隐含假设；未完成相应 pass 的信息不得冒充深读结论。
- ARIS 技术报告 `arXiv:2605.03042` 是 2026 年未正式发表的 research-harness 报告，只用于研究流程与 assurance 设计，不进入证明 GUI Memory 命题的核心证据池。

## Non-goals

- 不做“增加一个 memory 模块”的系统拼装论文；
- 不把 context window、trajectory length 或 benchmark 难度直接当成 Memory 根因；
- 不以生产风险、可避免损失或经济效益解释公开目录统计；
- 不在 Step 1 前设计复杂 architecture；
- 不声称 action contract 表示本身是首创。

## Current Data and Protocol

- 主要目录：OSWorld 2.0 的 108 tasks × 6 hosted model configs。
- ontology/training/stress exclusions：固定 24-task reserve、Task 035、Task 065。
- primary confirmatory frame：82 tasks × 6 configs = 492 units。
- secondary descriptive frame：648 catalog records；不视为独立 confirmatory evidence。
- 数值决策唯一来源：`stage0f_step1_decision_card.md`。
- 当前结论：`FRAME-READY / DETAIL-AVAILABILITY-PARTIAL / MEASUREMENT IMPLEMENTATION NOT READY`，不是 ontology-pilot PASS，更不是 evidential GO。

## Kill Conditions

满足任一项就停止或改题：

- 在 common-miss mass 已有正式边界时，global worst-case `upper_positive_task_ids < 8`；detected-roster upper 不得触发该 kill；
- global worst-case optimistic-upper correctness burden 小于 1.0 task-equivalent；
- C0-C 的 same-event global worst-case interface-task 上界仍少于 8，使 causal pipeline 被阻断；
- C0-E = `BELOW_FROZEN_GATE` 时停止使用 `Environment-Falsifiable` 题名并强制改名；C0-E = `INCONCLUSIVE / UNIDENTIFIABLE` 时阻断环境题名，只有一般 Evidence/Update-to-Action Consistency 可在自身 gate 已通过时继续；
- Step 2 的 boundary-isolated replay 以直接因果证据支持非 update-specific grounding、planning、actuation 或 evaluator failure 已充分解释目标效应；
- 可识别的 R×P factorial 中，C1-R 的 boundary-payload simple effects 与预注册聚合效应均未获支持；
- typed contract 在 semantic information closure、等更新时机和等预算的 flat state 上没有独立增益。

## Current Decision

- Idea selected：**候选问题已选，方法未选**。
- Baseline reproduced：否。
- Step 1 behavioral burden：未完成。
- Method implementation：禁止启动。
- Next action：Round 4/4b 已冻结 pre-action candidate commitment、location/event identity split、finite joint bounds 与 full-block A0→A1 barrier 的必要条件；Stage A 已实现组件级 fail-closed 基础，但完整 block manifest、A0-only adjudication、永久角色隔离 ledger 与 whole-block leak invalidation 尚未实现。当前明确 `NOT READY FOR BLOCK-A DRY RUN`，不得生成真实 packets。
