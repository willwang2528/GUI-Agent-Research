# Stage 0F：OSWorld 2.0 已发布轨迹行为负担预注册

> 版本：v0.6，2026-07-28  
> 七步位置：**Step 1，仅证明问题现象与负担**  
> 状态：**IN REVISION / MEASUREMENT IMPLEMENTATION NOT READY / 尚未标注 / 尚未获得 Step 1 GO**  
> 禁止结论：Memory 是根因、长程是因果变量、行动契约有效、生产环境发生率

## 0. 当前裁决

OSWorld 2.0 官方目录现在足以定义一个固定的有限总体：6 个模型配置，各 108 个任务，共 648 个 `task × model` 目录轨迹。

但是“目录中每格只有一条轨迹”不能推出“每格在实验基础设施中只启动过一次”。官方论文的行为分析对每个 `model × task` 纳入一条 published trajectory，并同时警告策略与能力混杂，因此只作描述性分析；这句话不能解释为每格只有一次 launch。公开目录和配置接口没有提供 seed、启动次数、失败后重跑、排除或发布选择字段。官方 runner 还具有复跑未完成目录的能力。

因此本阶段严格区分四种目标总体：

| 层级 | 目标总体 | 当前可识别性 | 允许结论 |
|---|---|---|---|
| `T0-Catalog` | 2026-07-22 冻结接口中六个 hosted configs 的 648 个 published artifact records | **可识别** | 目录覆盖、状态与可恢复字段；不代表 launched-run distribution |
| `T0-Behavior` | 648 个 published records 中可由现有轨迹识别的行为负担 | **部分可识别，尚未标注** | 完成可靠标注与 unit-level bounds 后，才可估计目录行为负担 |
| `T1-Run` | 冻结模型、预算、seed 与基础设施后的随机运行分布 | **不可识别** | 需要完整 launch/retry/publication manifest 或自行多 seed 重跑 |
| `T2-Production` | 真实生产 GUI 工作流分布 | **不可识别** | 需要现场采样框，benchmark 不能替代 |

本文件的目标仅是完成 `T0-Behavior` 的预注册并决定是否值得进入 Step 2。即使获得 GO，也不能自动放行 `T1-Run`、`T2-Production` 或 Memory 因果主张。允许的最宽表述是“在冻结的 OSWorld 2.0 已发布轨迹目录中观察到某种行为负担”。

## 1. Step 1 真正要回答的问题

不是：

```text
OSWorld 2.0 成功率很低，所以 GUI Agent 需要 Memory。
```

而是：

```text
在本研究未额外注入 update 的既有 benchmark rollout 中，
是否出现足够重要的 Update-to-Action Consistency Failure，
使后续的竞争性根因实验具有研究价值？
```

这里的“自然”只表示轨迹不是为本课题额外注入 update 后生成。benchmark 作者仍可能在任务设计中安排动态事件；它不表示任务来自生产环境随机抽样。

### 1.1 第一性原理链条

每个候选事件必须能还原以下链：

```text
环境或用户产生与命题 `p_old` 不相容的新证据 `p_new`
→ 证据在 decision point 前已经出现在 Agent 的实际 observation/history 中
→ outcome-independent normative schema 表明 `p_new` 与 `p_old` 对应不同的正确动作或 obligation
→ Agent 到达一个可预注册的 decision point
→ 后续可观察 action、artifact、派生计算、commit/block 或 omission 与 `p_old` 相容、与 `p_new` 下的规范动作不相容
```

如果缺少上述任意一环，只能记录为相邻错误，不能标成目标现象。terminal correctness deficit 是在 UACF-D phenotype 冻结后独立链接的 outcome；它不是 UACF-D 阳性定义的必要组成，因此 candidate supply 与 correctness-burden gate 不循环。

### 1.2 操作定义

primary `UACF-D` 定义为：

> 在预注册的 update opportunity 之后、eligible decision point 之前，改变规范正确动作的新证据 `p_new` 已经出现在 Agent 的实际 observation/history 中；但后续可观察 action、持久 artifact、派生计算、commit/block 决策或 required-action omission 与 `p_old` 相容、与 `p_new` 下的 outcome-blind 规范动作不相容。

该定义不主张 Agent 内部表示了 `p_old`，不主张 `p_old` 支配或导致了后续动作，也不主张伴随的 terminal deficit 可被某种 Memory 方法避免。

`p_old` 不得由后续错误动作反推。它必须在 candidate semantic action 暴露前，仅依据 pre-update observation、user input、已存在 artifact 或 outcome-blind normative schema 冻结，并保存可解析的 evidence pointer 与内容 hash。若只能从 post-update action 推测它，记为 `old_state_hypothesized`，排除出 primary `UACF-D`，只进入 sensitivity appendix。

每个 update opportunity 必须以 factual multi-label 冻结 `update_source_labels`：

```text
world_truth_changed
task_goal_changed
previously_true_fact_newly_revealed
explicit_corrective_feedback
source_unidentifiable
```

标签可多选；除 `source_unidentifiable` 外，每个 factual label 必须绑定独立 direct-evidence pointer。事件来源不得按优先级压成单一 `primary source`，而必须由完整 label set 机械派生为下述四个互斥类别。合法的来源未知 packet 只能使用单元素 `[source_unidentifiable]`，并填写 outcome-blind `source_unknown_reason` 与已检查证据范围；它表示现有可见前缀无法区分来源，不表示 packet 可以缺字段。不得使用 `prior_misinterpretation` 作为事实来源；只有 Agent 在 update 前的显式输出能证明旧解释时，才可把该输出作为独立行为字段记录。

`source_unidentifiable` 与所有 factual source label 互斥；若它与其他标签共存、标签数组为空、或任一 factual label 没有独立 direct-evidence pointer，packet 无效。事件来源冻结为四个互斥类别：

```text
PURE_WORLD:
update_source_labels == [world_truth_changed]

MIXED_WORLD:
world_truth_changed 在 labels 中，且至少还有一个其他 factual source

NON_WORLD:
labels 非空、不含 world_truth_changed、不含 source_unidentifiable

SOURCE_UNKNOWN:
update_source_labels == [source_unidentifiable]
且 source_unknown_reason / evidence-search scope 完整
```

`environment-falsifiable` 的 primary estimand 冻结为 `pure-world-transition`：`update_source_labels` 必须恰好只包含 `world_truth_changed`。包含 goal change、corrective feedback 或 revelation 的混合事件可进入通用 UACF-D 副分析，不进入环境主分析。若纯环境子集未通过决策卡 C0-E，项目必须改名为 `Evidence/Update-to-Action Consistency`，不得继续使用 Environment-Falsifiable 主标题。

下列情况不是 `SOURCE_UNKNOWN`，而是 `INVALID_SOURCE_MEASUREMENT`：label 数组为空、含未知 label、`source_unidentifiable` 与其他 label 共存、任一 factual label 缺 direct-evidence pointer，或来源未知 packet 缺 `source_unknown_reason / evidence-search scope`。它们只进入 measurement missingness，不能进入 pure-world lower、source rate 或 detected roster。为保证 global worst-case upper 不漏掉共同漏检/非法测量，只要尚无合法 strict-negative certificate，对应 task/unit 仍以 measurement-missing placeholder 进入 global upper，但不得伪装成一个合法 source event。修复只能发生在对应 A0 freeze 前；freeze 后不得把非法 packet 人工改成来源未知。

secondary `EACF-P` 定义为：

> 新状态尚未进入 Agent 的实际信息集；但在 decision point 前存在预注册、部署可用、安全且成本受限的 probe，Agent 未执行或未消费该 probe。

`UACF-D` 与 `EACF-P` 必须分开统计。前者是 delivered-evidence propagation failure；后者是 evidence-acquisition / monitoring failure。二者都是行为定义，不是内部 Memory 根因定义。

`EACF-P` 只适用于 probe result 尚未进入实际 observation/history 的情况。若 probe 已执行，结果已经出现在 observation/history，但 Agent 未解析、验证、消费或传播它，该事件进入 `UACF-D`，并将 `G / V / P` 保留为 competing causes；不得继续计入 `EACF-P`。

required-action omission 只有在 outcome 解封前已冻结下列链条时，才可成为 `UACF-D`：

```text
changed proposition
→ dependency edge
→ required action
→ externally defined deadline or commit point
```

若 omission 只是根据最终失败回看得出，记为 generic planning failure，不计入 `UACF-D`。错误 block 只有在旧状态明确支持 block、而 decision-time 新证据明确支持 execute/repair 时才计入；仅因不确定性而保守停止不自动构成 `UACF-D`。

以下情况必须排除出 `UACF-D` 阳性：

- 新证据未进入实际 observation/history；若存在合法 probe，转入 `EACF-P`，不计入 `UACF-D`；
- 新事实不会改变正确动作；
- 只有自然语言解释不同，外部行为未受影响；
- evaluator 或任务本身无法确定真值；
- GUI click/type 没有实现 Agent 已正确选择的 semantic action；
- 单纯 step limit、API error 或环境故障导致结束，且此前没有目标行为链；
- 只因为最终失败，事后猜测“可能忘了”。

## 2. 冻结数据框

### 2.1 官方版本

- Benchmark release：`osworld-v2-2026.06.24`
- 官方 tag commit：`2b9b7b4eb73243d557bdbf2998fe18d8e18e19c6`；该 tag 只锚定 release 源码，仍不能证明 hosted trajectory 实际运行时逐文件 provenance
- 本地官方代码 commit：`c261cb57a699bd18db128787ca4e71b749141762`；这是公开代码锚点，不是每条 hosted trajectory 的逐运行 provenance 证明
- Task manifest：108 个任务
- Observation：screenshot
- Action space：pyautogui
- Budget：所有配置的 `max_steps` 字段均为 500，但 budget mode/unit 不同：GPT-5.5 与 Qwen 使用 batch-tool `model_steps`，其余四个配置使用 standard steps；跨模式 trajectory length 不可直接等价比较
- 官方论文：[OSWorld 2.0](https://arxiv.org/abs/2606.29537)
- 官方项目：[OSWorld 2.0 project](https://osworld-v2.xlang.ai/)
- 官方轨迹目录：[OSWorld 2.0 trajectory catalog](https://osworld-v2-monitor.xlang.ai/)
- 官方压缩包：[OSWorld 2.0 trajectory archive](https://huggingface.co/datasets/xlangai/osworld2.0-trajectory/tree/main)

六个配置：

| Config | 任务数 | `Done` | `Done (Max Steps)` | `Error` |
|---|---:|---:|---:|---:|
| Claude Opus 4.7 | 108 | 99 | 8 | 1 |
| GPT-5.5 | 108 | 105 | 3 | 0 |
| Claude Sonnet 4.6 Max | 108 | 98 | 10 | 0 |
| Claude Sonnet 4.6 Medium | 108 | 89 | 19 | 0 |
| MiniMax M3 | 108 | 86 | 22 | 0 |
| Qwen 3.7-Plus | 108 | 92 | 16 | 0 |
| **合计** | **648** | **569** | **78** | **1** |

所有状态都进入抽样框。不能删除 `Error`、max-step、零分、没有 commit、premature stop 或 evaluator-invalid unit；这些都是需要单独标注的结果类型。

### 2.2 当前目录完整性事实

2026-07-22 对官方只读接口的审计结果：

- 每个配置返回 108 个唯一 task id；
- 六个配置合计 648 个 `task × model` cell；
- 每个 cell 的 `trajectory_count = 1`；
- 每个 cell 的 `has_multiple_trajectories = false`；
- 每个 cell 的 `selected_trajectory_id = task id`；
- `/api/available-configs` 只暴露配置与下载路径，不含 `run_id`、`seed`、launch count、retry count、exclusion 或 publication-selection 字段；
- `/api/tasks/brief` 暴露的是当前目录轨迹及状态，不是运行生成清单。

这证明的是 **published-catalog coverage**，不是 **launched-run completeness**。

### 2.3 为什么启动过程仍不可识别

官方 runner 的公开实现使用同一个 `model/domain/task_id` 结果目录：

1. 若目录有 `result.txt`，后续启动将该 task 视为完成并跳过；
2. 若目录没有 `result.txt`，后续启动会删除该 task 目录中的现有文件，再把它视为未完成；
3. 正常到达 evaluator 后才写 `result.txt`；异常路径记录 error，但不在 task 目录生成 `result.txt`；
4. 因此，如果实验被重新启动，异常的旧 task 目录可能被清空后复跑；最终目录本身无法证明此前没有失败尝试。

公开代码还把 task completion/error 追加到运行时 `summary/results.json`。但当前官方目录 API 没有公开这个 summary 的内容，项目页与论文也没有给出全模型的 launch/retry/exclusion manifest。

这不是“官方有意挑选结果”的证据。它只证明从现有发布物无法识别选择机制。

### 2.4 Selection gate

`T1-Run` 只有满足以下任一条件才可解锁：

- 作者提供每个配置的完整 `task × seed × launch` manifest、所有异常尝试、重跑原因、排除记录与发布映射；或
- 我们在冻结 commit、模型版本、prompt、环境、预算和 seed 后自行运行完整概率样本，并保存所有 launch。

在此之前，任何“OSWorld 2.0 上自然发生率”必须改写为“冻结的已发布目录轨迹中的有限总体比例”。

## 3. 分母先于标签

正式审计冻结三个 incidence estimands 和一个 loss outcome：

| Estimand | 分母或聚合单位 | 分子或 outcome | 解释 |
|---|---|---|---|
| A1. Confirmatory unit incidence，primary | 全部 held-out catalog units，包括 no-opportunity | 至少含一个 `UACF-D` 的 units | 不受本体与 stress-set 开发影响的主要 incidence |
| A2. Full-catalog unit incidence，secondary | 全部 648 个 catalog units，包括 no-opportunity | 至少含一个 `UACF-D` 的 units | 最终冻结本体下重标后的目录 census |
| B. Opportunity-conditional burden | 所有可审计 delivered update opportunities | 其中发生 `UACF-D` 的 opportunities | update 已送达后的条件负担 |
| C. Decision-conditional burden | 所有预注册 eligible decision points | 其中满足完整 `UACF-D` 链条的 points | 非目标 decision errors 另表报告 |
| D. Severity-weighted burden | 每个 `task × model` unit | `UACF-D` associated loss 的 sum、max 与 recovery cost | 连续 outcome，不称为分母 |

B、C 同时报告 event-weighted rate，以及先在每个 `task × model` unit 内计算、再等权平均的 unit-weighted rate，避免长轨迹或多机会任务获得不受控的更高权重。

`EACF-P` 使用完全独立的 A/B/C 表，不得与 `UACF-D` 合并。异质性按 model、task 和 outcome-blind mapping 冻结后的 provenance clusters 报告，但异质性不是第四个分母。

Memory-attributable burden 的分母现在不定义。它必须等 Step 2 的 boundary-isolated replay 后才能计算。

### 3.1 不允许的分母替换

- 不能只抽最终失败；
- 不能只抽作者 Dynamic / Implicit / Conflict 标签；
- 不能只抽截图完整、分析文字丰富或被项目页展示的任务；
- 不能把 108 个任务规模当成 108 次 update opportunity；
- 不能把每个模型的同一 task 当成六个独立 task families；
- 不能把 agent steps 当成人类时长代理。

官方只公开“69.6% 的任务人类预计超过一小时”的聚合值，当前公开 task metadata 中没有恢复出每个 task 的人类预计时长。因此 `human time ≥ 1 hour` 不能作为当前 primary subgroup。若作者提供逐 task 时长映射，它只能作为预先冻结的 sensitivity analysis；不能从结果反推长程阈值。

## 4. Pilot 与确认性审计分离

### 4.1 Ontology pilot

pilot 只用于修订本体、标注手册、blind packet 和一致性流程，禁止估计 burden。

冻结字符串：

```text
Stage0F-v0.1|osworld-v2-2026.06.24
```

协议版本已经升级为 v0.2，但为保持既有 deterministic split，故意保留 legacy seed `Stage0F-v0.1`。hash 输入编码冻结为 UTF-8；`task_id` 使用三位零填充字符串；SHA-256 以 lowercase hexadecimal 表示并按 lexical ascending 排序。

对 108 个 task id 计算：

```text
SHA256(seed_string + "|task=" + task_id)
```

按 hash 升序选择前 8 个 task，并包含全部 6 个模型，共 48 个 `task × model` pilot units：

```text
009, 066, 073, 020, 083, 029, 050, 024
```

pilot 不因成功、失败、steps、score 或作者标签改变。pilot 中即使没有 update opportunity，也保留为零机会 unit。该随机 pilot 是流程与 no-opportunity 识别测试，不保证包含阳性。

在构造任何 A0 packet 前，冻结以下 24-task ontology-pilot reserve；它们无论最终是否打开，都永久排除出 primary holdout：

```text
Block A：009, 066, 073, 020, 083, 029, 050, 024
Block B：041, 092, 037, 090, 071, 007, 078, 107
Block C：042, 049, 008, 079, 054, 084, 072, 096
```

三个 blocks 均由同一 Stage0F-v0.1 hash 排名按顺序切分，每个 task 包含全部六个模型。Block A 用于 ontology development；Block B 用于第一次未见 validation；若 B 失败，只允许修订一次手册，再用未见 Block C 做第二次 validation。Block C 仍失败则判 `UNIDENTIFIABLE`，不得继续从 holdout 抽 task 调手册。

8 tasks × 6 models 只是 initial ontology development，不预设样本量充分。在任何 validation block 的 outcome 解封前，先用 development/stress 的 A0/A1 redacted artifacts 检查下列 adequacy 条件：

1. 至少 12 个可审计 delivered update opportunities；
2. opportunities 至少来自 4 个 task ids；
3. 至少覆盖下列四类中的三类：field/value commit、artifact repair/recomputation、required-action omission、execute/block；
4. 所有 A0/A1 字段和时间门都能被两位标注者执行。

若 Block A 与隔离的 training/stress packets 合计仍不能满足 coverage，允许使用 reserve 中的 Block B 做 ontology development，但必须把 Block C 保留为唯一未见 validation。若 Block C 也被用于 development，或 24-task reserve 用完仍不满足 coverage，判定本体 pilot `UNIDENTIFIABLE`，不执行正式 burden audit。这些阈值只证明手册获得最低流程覆盖，不证明 `UACF-D` 阳性、阴性或 rare-label reliability，也不是课题重要性阈值。

为防同 task 和相似 task/template 的行为泄漏，每个实际打开的 block 使用全 block barrier，并永久隔离角色：

1. Block A 的全部 48 units、Block B 的全部 48 units、Block C 的全部 48 units，以及正式 492-unit holdout，各自必须完成本 block 所有 boundary locations 的 A0 raw labels、A0-only adjudication 与 `A0_LABEL_FROZEN`，再写入单一 `BLOCK_A0_BARRIER_FROZEN` manifest；之后才允许开放该 block 的任一 A1；
2. 同一 block 的全部 A1 paths 冻结并写入 `BLOCK_A1_BARRIER_FROZEN` 后，才允许该 block 的任一 Stage B；
3. A0 annotator/adjudicator pool 永远不担任 A1 或 Stage B 角色，也永远收不到 candidate action；A1 pool 只能读取已冻结的 A0 artifacts 与 role-specific reveal。

任一 A1 早于本 block 的全体 A0 freeze，会污染该 block 的 A0 未见性；整个 block 不能进入对应 primary reliability/burden evidence，不能只删除最先泄漏的 task/config。

### 4.2 隔离的 stress / training set

作者展示过的 Task 035 仅作为非盲 training case，不能进入可靠性、burden 或 Step 1 GO。

初版手册冻结后，再从作者 `dynamic_environment` 的 10 个 task ids 中，用下列独立字符串做 hash 排序：

```text
Stage0F-stress-v0.1|osworld-v2-2026.06.24
```

排序第一的 Task 065 × 6 models 作为 quarantined positive-boundary stress set。该选择的 split provenance 可复现，但 trajectory 对应的 instruction/setup/evaluator 版本尚未逐运行绑定，因此当前标记为 `stress-selected / normative-provenance-unverified`。它只能检查 packet 管线，不能验证 normative UACF-D 边界，更不能估计 burden。若 stress set 迫使本体修改，必须升级版本、重新冻结，并保持 confirmatory units 不可见。

### 4.3 Confirmatory holdout

排除固定 24-task ontology-pilot reserve、Task 035 training case 和 Task 065 stress task 后，剩余 82 个 tasks × 6 models，共 492 units，构成预先固定的 `T0-Holdout`。这些 units 才用于主要 Step 1 判定。

24-task reserve 的 144 个 units、6 个 stress units 和 Task 035 的 6 个 training units，在同一最终冻结本体下由未参与手册开发的标注者重新盲标后，可加入 `T0-Full-Catalog` 的 secondary 648-record descriptive census。其 exact count 对冻结编码规则成立，但参与 ontology/training/stress development 的 units 不构成 independent confirmatory evidence。

如果某个 unit 的原始截图、action、时间戳、任务真值或 evaluator 无法恢复，标记 `unclassifiable`，不得静默删除。

## 5. 分层、时间门控的盲标

### 5.0 Prefix-only candidate generation

candidate generation 必须是独立于 A0/A1/Stage B 标注者的 prefix-only streaming procedure。

生成器通过不可回退的 rolling-prefix interface 读取原子化 timeline。标准 GUI step 的唯一合法微时序是：

```text
reveal observation o_k
→ generator/reference 只能看 o_0...o_k 与 a_0...a_(k-1)
→ commit ACCEPT / REJECT for boundary k
→ persist commitment hash + previous-chain hash + monotonic timestamp
→ reveal current semantic action a_k
→ reveal observation o_(k+1)
```

也就是说，commit 必须发生在**当前 candidate action `a_k`** 开放前，不只是下一条 action 前。candidate action 本身及其 embedding、摘要、category、后续 observation、score、evaluator、termination status 和其他模型结果在 commitment 前均不可访问。任何先开放 `a_k`、再提交 boundary-k candidate 的 location 都是 `INVALID_GENERATION_MEASUREMENT`。

对 batch-tool action bundle，若基础设施不能在 bundle 内逐 subaction 拦截，整个 bundle 必须视为一个不可分割 semantic action；唯一 eligible boundary 位于整个 bundle reveal 前。不得先读 bundle 的任一 subaction 再在 bundle 内回填 candidate；需要 bundle 内 decision point 的 unit 在当前测量实现中记为不可审计。

reference auditors 使用同一不可回退的逐 ordinal interface 与同样的 commit-before-reveal gate；“exhaustive scan”只表示不跳过任何 ordinal，不表示可以先读取完整 trajectory 再回填候选。每个 ordinal 的 commitment 都写入 append-only hash-chain；完成整个 trajectory 后不得回改。若每个 unit 只能标一个 point，先由该独立生成器产生完整 location set，再对冻结的 location ids 做 hash selection。A0、A1 与 Stage B 标注者都不能参与候选集合生成。

omission checkpoint 只能来自运行前冻结的 task-visible obligation、外部 commit point 或环境 deadline；不得根据最终缺失动作创建 candidate。

candidate generator 是测量器的一部分，必须单独验证，不能让 A0/A1/Stage-B agreement 掩盖其漏检：

1. 所有实际打开的 reserve units 与正式 holdout units 均由两个互不沟通的 prefix-only generators 独立扫描；两个 generator 的身份、prompt/codebook、顺序和版本在打开 outcome 前冻结；
2. 两者 candidate-location union 进入 A0，不允许执行者按“看起来不像 Memory”删除 union 中的非重复 location；
3. generator A/B 相对 union 的指标统一改名为 `inter-generator coverage`、task coverage 与 agreement F1；它们只诊断两个生成器的分歧，不是 recall，不能使 C0-A PASS；
4. 两位互不沟通的 reference auditors 分别对每个未见 validation unit 的 rolling prefix stream 做逐 ordinal exhaustive scan，不看生成器来源、candidate action、后续 outcome、score 或其他模型结果；两份 reference locations 与 generator A/B union 全部合并后进入独立 A0；
5. A0 全部冻结后，另一位 source-blind adjudicator 才能依据 location、ordinal tolerance 与已冻结 A0 semantics 形成 `adjudicated_reference_event_set`。generator recall 的分母是其中 qualifying opportunities，指标名称固定为 `adjudicated-reference-set event recall`、task-cluster recall 和 event-semantic F1；两个 generator 的 event recall 与 F1 均须至少 0.80。该指标只证明相对冻结 reference process 的测量可靠性，不声称证明零共同漏检；
6. canonical location timestamp 是 unit 内 Agent-visible observation 的零起始序号 `cutoff_observation_ordinal`，不将 standard steps 与 batch-tool model_steps 互换或横向比较。每个 unit 每个 cutoff ordinal 至多有一个 decision boundary location，但同一 location 可在 A0 中产生多个 proposition/obligation events。先对不含任何 location/event id 的净化 A0 prefix payload 取 `a0_prefix_payload_sha256`，再使用 `Stage0F-boundary-location-v1`：

```json
{"namespace":"Stage0F-boundary-location-v1","unit_alias":"<opaque>","cutoff_observation_ordinal":0,"a0_prefix_payload_sha256":"<64hex>"}
```

由此生成的 `boundary_location_id` 只承诺 pre-action location 与实际净化 prefix bytes，不能包含 generator 提出的 proposition、obligation、boundary、source 或 action label，也不能决定 A0 可接受的语义。A0 input 接收该 opaque location id 与对应 prefix；validator 必须从 packet bytes 重算 prefix hash 和 location id，不能形成“input hash 包含 location id”的自引用。

每位 A0 annotator 可在同一 location 独立冻结零个、一个或多个 events。每个 raw label id 必须绑定完整 outcome-blind semantic payload，而不是只绑定 proposition/obligation 的子集：

```json
["Stage0F-a0-raw-label-v1","<unit_alias>","<boundary_location_id>","<schema_bundle_sha256>","<codebook_sha256>","<annotator_alias>",{"p_old_proposition_id":"<id>","p_new_proposition_id":"<id>","update_source_labels":["<sorted-label>"],"normative_action_difference":"<text>","affected_obligation_ids":["<sorted-id>"],"boundary_type":"<enum>","grounding_mode":"mechanical|blinded_human"}]
```

两位 A0 labels 的 disagreement 必须在 candidate action reveal 前、只依据 A0 artifacts 完成 source-blind adjudication；或者为每位 annotator 保留完全独立、永不回改的 A0→A1 path。任何 final substantive tuple 必须完整等于一条已冻结 raw tuple；唯一允许的跨 raw transform 是对 `update_source_labels` 执行预冻结 `sorted_set_union_utf8_v1`。任一其他字段采用不同 raw、final value 不在输入中、transform executable/hash/output 不匹配，均为 `INVALID_MEASUREMENT`，不得由 helper 自动 fallback。

primary 使用 adjudication 路径时，`adjudicated_event_id` 使用：

```json
["Stage0F-adjudicated-event-v1","<boundary_location_id>","<p_old_proposition_id>","<p_new_proposition_id>","<normative_action_difference_sha256>",["<sorted-obligation-id>"],"<boundary_type>","<schema_bundle_sha256>","<codebook_sha256>",["<sorted-supporting-raw-label-id>"]]
```

多个 obligation ids 按 UTF-8 bytes 排序。同一 location 可有多个不同 `adjudicated_event_id`；A1 必须逐 event 引用已冻结 ID。不得用无长度边界字符串拼接代替任一 canonical preimage；A0 semantics 与 generator 的任何 provisional description 不一致时，以 A0/adjudication freeze 为准，不能拒绝 A0 label、人工对齐 ID 或在 A1 后回改；
7. 对每个实际打开的 reserve unit，从不在任何 union/reference candidate 的 ±1 observation window 内的 observation ids 中，以 `Stage0F-noncandidate-audit-v0.2|unit=<unit_id>|observation=<observation_ordinal>` 做 hash 排序抽取前两个；该随机非候选抽查只作 supplemental leakage/prevalence audit，不估计 event recall，不进入 PASS gate。

generator/reference matching 必须在同一 `unit_alias` 内、所有相关 A0 labels/adjudication 已冻结后执行。可匹配边要求 A0 冻结的 `proposition_id`、排序后的 obligation set、`boundary_type` 完全相同，且 `abs(cutoff_observation_ordinal_g - cutoff_observation_ordinal_r) <= 1`。在该二分图上先取最大基数 matching，再最小化总 ordinal distance；仍并列时，按排序后的 `(reference_adjudicated_event_id, generator_adjudicated_event_id)` pair vector 取字典序最小解。禁止 greedy-first-match、以 generator provisional semantics 锚定 A0，或人工挑选冲突 pair。

所有 rolling commitments、生成、reference scan 与抽查记录都写入 append-only hash-chain log，并保存 packet hash、prompt/codebook/code/schema/validator/matching/adjudication/normative-canonicalization version hash 与 timestamp。reference event 不足 8 个或不足 4 个 task ids 时，generator recall 记为 `UNIDENTIFIABLE`，不得用零漏检冒充 PASS。完成这些 gate 前，`prefix-only candidate audit` 不得标记 PASS。

即使上述 reference process 通过，它也不证明零共同漏检。由 detected roster 得到的 upper 只能报告为 `detected_roster_upper`，不得触发 C0-B/C0-C/C0-E 的低于门或 NO-GO。用于否定现象的 global upper 必须按决策卡把所有尚未由合法、outcome-blind 证据排除的 held-out task/unit 纳入 worst case；若 common-miss mass 没有正式上界，结果只能保持 `INCONCLUSIVE / UNIDENTIFIABLE`，不能把未检测到当作不存在。

### 5.1 Coordinator envelope：真实身份与 provenance sidecar

真实 `task_id`、hosted config/model、source URL、原始本地路径、catalog status/score、raw artifact hashes、匿名 alias 映射和各阶段 artifact hashes 只能存在于 coordinator envelope。该 envelope：

- 不得发给 candidate generator、reference auditor、A0/A1 annotator 或 Stage B annotator；这些角色只能接收各自的 redacted artifact，任何额外 identity exposure 必须登记并取消其盲标资格；
- 不得被复制进 annotator packet 的任意嵌套字段、文件名、EXIF、HTML、screenshot path 或 free-text note；
- 为每个 unit 生成一次 128-bit CSPRNG opaque `unit_alias`，不得由 task id/model/source URL 的公开 hash 推导；alias collision 必须机械拒绝；
- 保存 envelope 自身 SHA-256，A0 input 只引用该 hash 和 opaque alias，不含可逆映射；
- 即使 coordinator 已看过 outcome，也不能担任 generator、A0/A1 annotator、Stage B annotator或 reference auditor。

candidate generators、reference auditors、A0/A1 annotators 与 source-blind adjudicator都在无网络、不可复制文本到外部搜索工具的环境工作；其 packet 不得包含可用于搜索公开轨迹的 task id、model name、source URL、真实路径、score、status、result 或其他 hosted config 的输出。Stage B 只能使用 coordinator 生成的 redacted outcome/evaluator artifacts；同样不得获得真实 identity 或外部搜索能力。exact instruction 即使保留给规范判断，也必须在离线界面展示，不能成为回查公开轨迹的搜索键。

### 5.2 Stage A0：normative freeze，禁止 candidate action

每个 annotator 先接收独立 `a0_input`。它只允许包含：

- opaque `unit_alias` 与 coordinator-envelope hash；
- 经净化的 Agent-visible instruction；
- 运行结果产生前冻结的 normative action schema，不含 evaluator secret、episode-specific truth 或由最终 outcome 推导的信息；
- 从 observation ordinal 0 到 A0 cutoff 的完整、连续 prefix；若原始 observation 缺失，必须有显式 missing marker，不得压缩重编号；
- 以 content hash 命名的截图/静态 blob，不含原文件名、URL、路径或 metadata；
- candidate action 之前的 cutoff ordinal、当时部署可用的合法 probe 集合与必要静态应用说明。

A0 明确禁止：

- candidate semantic action、action label、action text 或其 embedding/摘要；
- cutoff 后的 observation/action；
- 最终 score、status、evaluator truth、termination reason；
- task/model/source identity、作者分析、challenge tag、failure/root-cause label；
- 其他模型在同一 task 上的任何信息。

A0 label 必须在 append-only log 中冻结：

1. `p_old`、`p_new` 与各自结构化 evidence pointer；
2. update opportunity 与互斥的 source classification；
3. 最小 necessary precondition 及其翻转是否改变规范动作；
4. outcome-blind normative action difference；
5. 受影响 artifact、dependency edges 与 obligation ids；
6. eligible decision point、A0 cutoff 与合法 probes；
7. A0 时点仍 compatible 的 competing causes；
8. A0 独立冻结的 raw-label preimages/ids；在 action reveal 前完成的 source-blind adjudication preimages 与 `adjudicated_event_id`；不得接收或复用 generator provisional semantics。

结构化 evidence pointer 固定为：

```json
{"artifact_id":"<content-addressed-id>","observation_ordinal":0,"content_sha256":"<64hex>"}
```

`p_old` evidence 必须早于 `p_new` evidence；二者都不得晚于 A0 cutoff，也不得指向 candidate action。若 `p_old` 只能由后续动作推测，必须写 `old_state_hypothesized=true` 并机械导出 `primary_analysis_eligible=false`。A0 input 中只允许 `boundary_location_id`，不得含 generator 的 proposition/obligation/boundary/source 判断或其可验证 commitment hash。A0 raw labels 经 schema、语义和 hash 验证后写入 `A0_RAW_LABEL_FROZEN`；source-blind adjudication 只能查看这些 A0 artifacts，并在 action reveal 前生成一个或多个 `adjudicated_event_id`，再写入 `A0_LABEL_FROZEN`。冻结后任何修改都产生新版本并使旧 A1 path 作废，不能原地覆盖。

#### 5.2.1 五账本与不可互换的统计对象

对每个 location `l`，必须分别冻结：

```text
R_l = 全部 immutable raw-label ids
C_l = adjudication case ids
P_l = 必须到达 A1 的 path/event ids
E_l = case-level primary event rows
M_l = unresolved / typed-invalid / path-missingness records
```

必须同时满足：

```text
每个 raw 恰好属于一个 case 或一个机械可验证的 typed-invalid record
每个 case 恰好属于一种 adjudication mode
每个 required path 恰好有一个 A1 label，或进入显式 missingness
每个 case 最多产生一个 primary row，不论该 row 是 positive 还是 negative
unresolved 不产生 primary boolean，但保留在 denominator、missingness 与 bounds 中
```

`raw disposition coverage`、`case coverage`、`path coverage`、`primary event count` 与 `missingness coverage` 是五个不同命题，任何一个都不能代替其余四个。A0 barrier、A1 barrier 和 validator PASS output 必须同时公开只读的 R/C/P/E/M rosters、pre-adjudication agreement roster 及精确 counts；任何 downstream bounds consumer 只读取 canonical events 而忽略 R/C/P/M，均为无效实现。

#### 5.2.2 Case formation 与 agreement denominator

同一 location 内的 raw case partition 必须由 outcome-blind、预冻结 matcher 机械产生，而不能由 adjudicator 任意拆分或合并。最终 matcher artifact 至少绑定：

- matcher executable 与 hash；
- 全部 candidate edges；
- selected maximum-cardinality matching；
- ordinal/semantic tie-break trace；
- unmatched raw roster；
- 机械重算后的 exact case partition。

当前 v0.6 实现尚无该 matcher，必须输出：

```text
agreement_completeness = NOT_ESTABLISHED_NO_FROZEN_CASE_MATCHER
```

因此当前 synthetic tests 即使通过，也不能作为 agreement reliability 或 measurement-stack freeze 的证据。

agreement 只能由 adjudication 前的 immutable raw roster 计算：

```text
consensus case                  → raw agreement
human-resolved disagreement    → raw disagreement
independent paths              → raw disagreement
paired unresolved              → raw disagreement
singleton raw                  → one-sided disagreement，进入 b 或 c
双方均无 event 的 valid location → negative agreement
```

positive agreement 中的 `a/b/c` 必须来自冻结 matcher 的 raw matched/unmatched records。第三方裁决后的结果不得把 `b/c` 改写为 `a`，也不得把 singleton 或 unresolved 从 denominator 删除。

#### 5.2.3 四种 adjudication mode

| Mode | 合法输入 | A0 输出 | A1/统计角色 |
|---|---|---|---|
| `consensus` | 至少两位独立 annotator 的完整 substantive tuple 一致 | 一个 event | 一个 required path；case 最多一个 primary row |
| `blinded_human_resolution` | 至少两条完整 raw tuple 存在 substantive disagreement | 选择一条完整 raw tuple；仅 source-label set 可做冻结 union | disagreement 仍留在 raw agreement；一个 required path |
| `independent_paths` | disagreement 不做单一裁决，或 singleton 需保留 | 每条 raw 一个不可回改 path | 所有 path 默认为 `sensitivity_only`；无预冻结 case-level aggregator 时不得进入 primary |
| `unresolved` | 无法合法选择、adjudicator abstain 或 authority 不足 | 显式 unresolved record | 不产生 A1 primary event；进入 M 与 bounds |

independent paths 只有在 outcome 前冻结 case-level aggregator 后，才允许把多条 path 聚合为最多一个 case-level primary row。否则所有 path 只进入 sensitivity；path phenotype 分歧、任一路缺失或 path alias 均进入 explicit missingness/invalid measurement，不能选择有利的一路。

substantive raw 不得凭 self-reported rejection hash 从 denominator 删除。在 executable codebook rejection verifier 完成前，`OUT_OF_SCOPE_BY_FROZEN_CODEBOOK` 与 `MALFORMED_TYPED_CLAIM` 一律 fail closed 为 `SEM_A0_REJECTION_UNAVAILABLE`；不能被机械验证的记录必须进入 `unresolved`。

#### 5.2.4 Grounding authority

`adjudication_mode` 与 `grounding_mode` 是两条正交轴。

mechanical grounding 必须实际闭合：

```text
source bytes
→ frozen parser / normalized trajectory
→ typed predicate instance
→ verifier executable and invocation
→ verifier output
→ p_old / p_new
→ release-tagged normative/evaluator rule
→ normative action difference
```

pointer/hash 存在、annotator 一致或 packet 内自报 boolean 都不构成 mechanical entailment。当前实现只允许 `synthetic_test_only` frame 上的固定 typed-claim verifier，并必须输出 `SYNTHETIC_TYPED_CLAIM_ONLY`；production frame 继续 fail closed。

blinded-human grounding 至少需要两份独立、outcome/action-blind 的 evidence-entailment records，分别绑定 principal、完整 evidence refs/hash、proposition judgment、normative-rule judgment、freeze time 与 exposure proof；grounding adjudicator 必须与两位 labeler 分离，且 disagreement 不得覆盖。当前 v0.6 尚未实现双 entailment records，必须输出 `HUMAN_ADJUDICATED_EVIDENCE_AUTHORITY_PARTIAL`，不能称 semantic truth 或 mechanically grounded。

#### 5.2.5 Unresolved、missingness 与外部收据

unresolved case 对 point lower bound 贡献 0，但必须按第 7 节进入 upper/sensitivity。若 event-level hidden-opportunity 上限 `H` 未在 outcome 前冻结，相应 event upper 为 `UNIDENTIFIABLE`；unresolved 不是 strict negative。

本地 hash chain 和时间字段只能证明 packet 内 self-sealed chronology，不能证明真实提交早于 reveal。production 还必须具有 adjudication 前、不可回退的外部 raw-roster receipt，以及 trusted decision/barrier/reveal timestamps、完整 access log 与 principal/role-history checkpoint。没有这些 authority 时，删除 raw 后重签整个 packet 仍无法被本地 validator 发现；因此 production temporal/capture completeness 必须保持 `NOT ESTABLISHED`。

### 5.3 Stage A1：behavior reveal，不能改写 A0

只有 coordinator 验证对应 block 的 `BLOCK_A0_BARRIER_FROZEN` 后，才为其中任一 config 生成独立 `a1_reveal`：

- 精确引用 `a0_input_sha256`、`a0_label_sha256`、`boundary_location_id` 与对应 `adjudicated_event_id`；
- action candidate 只新增 candidate semantic action 及其 action ordinal；
- omission candidate 必须改用 `omission_interval` reveal：包含 A0 已冻结 decision point 到 deadline/commit point（含边界）的完整、连续 action-presence ledger，每个 action 以净化 semantic record 或显式 missing marker 表示；不得只提供“没有执行”的结论；
- 不含 action 后 observation、terminal outcome、score/status/evaluator 或真实 identity。

A1 label 只判断：

- candidate semantic action 是否与 `p_old` compatible；
- 是否与 `p_new` 下的 normative action incompatible；
- 是否存在 semantic-action 层的 ambiguity 或 competing explanation；
- required-action omission 是否能由完整 interval ledger 证明在预冻结 deadline/commit point 前未出现；interval 任一 action 缺失、重编号或 deadline 后信息混入都使该 omission `INVALID_MEASUREMENT`。

A1 不得新增、删除或改写 `p_old`、`p_new`、source labels、normative action difference、dependency edges、obligations 或 evidence pointers。日志顺序必须满足：

```text
A0_INPUT_CREATED
→ A0_RAW_LABEL_FROZEN
→ A0_LABEL_FROZEN
→ BLOCK_A0_BARRIER_FROZEN
→ A1_REVEAL_CREATED
→ A1_LABEL_FROZEN
→ BLOCK_A1_BARRIER_FROZEN
```

hash-chain 缺口、重排、分叉、A0 hash mismatch、A1 早于 block-level A0 barrier、Stage B 早于 block-level A1 barrier，角色池交叉，或 omission interval 不完整，均构成 `INVALID_MEASUREMENT`。对 barrier/role leakage，整个受影响 block 不得进入对应 primary reliability 或 burden evidence。

### 5.4 Stage B：outcome adjudication

A0/A1 全部冻结后，另一组标注者才查看后续轨迹、final state 与 evaluator，判断：

- candidate action 是否执行；
- 是否出现错误 commit、错误 block 或 required-action omission；
- artifact 是否未修复、修复失败或被过度修复；
- severity、recoverability 与可审计 loss；
- 哪些 competing causes 被直接证据排除；
- 哪些原因仍只是 compatible；
- 进入 Step 2 可能需要什么 candidate intervention；
- `interface_observed`、`intervention_implementable`、`faithful_replay_verified` 与 `boundary_isolation_verified` 分开记录；Step 1 只允许前者取观察值，后三项必须保持 `NOT_EVALUATED`，并分别在 Step 1.5 的实际 implementation/replay/isolation gate 后才能改变。

Stage B 禁止填写单一“真正根因”。根因字段只能取：

```text
ruled_out
compatible
boundary_anomaly_observed
causally_supported_by_replay
unidentifiable
```

在 Step 1 中，`causally_supported_by_replay` 必须为空。

### 5.5 决策点不能由结局定义

在满足 prefix-only 生成约束后，point 类型优先级如下：

1. 由 outcome-blind task-structure 标注者依据净化后的任务说明，在看模型轨迹前指定关键 commit；
2. 根据预注册 action taxonomy，对生成器实时接受的所有 eligible points 全部标注；
3. 若成本要求每 unit 只取一个 point，则对 append-only candidate ids 做 hash-random selection。

禁止使用“最后一个错误动作”“导致最终失败的动作”或“最像 Memory failure 的动作”选点。

## 6. 竞争根因本体

每个 candidate 必须是多标签记录，不允许 winner-takes-all：

| Boundary | 必填问题 | 直接证据 |
|---|---|---|
| `E` delivery/monitoring | 变化是否送达；是否有合法 probe；Agent 是否选择了 probe | message、页面访问、probe action |
| `O` observation | Agent 实际收到什么 raw observation | screenshot、a11y、timestamp |
| `G` grounding | entity、value、version、scope 是否被正确提取 | raw observation 与 transcription |
| `R` persistent state | 是否存在独立 store；写入、更新、读取是否可观察 | store dump/API；否则 `R_unobserved` |
| `P` planning/repair | 是否找到 impact set、失效 artifact 与 repair obligation | plan、后续 semantic actions |
| `S` semantic action | Agent 选择的字段、值与 action type 是否正确 | model action intent |
| `A` actuation | semantic action 是否被 GUI 正确实现 | click/type 后环境变化 |
| `V` verification | 是否选择、执行并消费验证 observation | verification action 与 reaction |
| Environment | drift、TOCTOU、session 或不可恢复 side effect | timestamped environment state |
| Budget | step、token、timeout、API failure | runtime logs |
| Evaluator/task | 真值错误、任务歧义、不可满足 | independent task adjudication |

每个候选原因同时记录：

- evidence pointer；
- `ruled_out / compatible / directly_observed`；
- confidence；
- 能区分它的最小 intervention；
- intervention 是否使用 privileged truth；
- 与其他原因是替代充分、联合必要还是未知。

没有可独立读取的 store 时，禁止写“观察到 Memory defect”；最多写 `R-compatible / R-unobserved`。

## 7. Missingness 与部分识别

### 7.1 三类缺失

- `catalog missingness`：预期 648 个 cell 缺失；当前为 0；
- `trajectory missingness`：cell 存在，但 action、截图、时间戳或最终状态缺失；待逐 unit 审计；
- `generation missingness`：launch、retry、discard 或 publication-selection 未公开；当前使 `T1-Run` 不可识别。

### 7.2 `T0-Behavior` 边界

unit-level incidence 的固定边界为：

```text
lower_unit = known_positive_units / N
upper_unit = (known_positive_units + outcome_relevant_unclassifiable_units) / N
```

primary 中 `N = frozen held-out units`；secondary full-catalog census 中 `N = 648`。strict negative 与 no-opportunity 都是已分类状态，不属于 missing。

其中 terminal status 为 `Error` 不自动等于 `unclassifiable`。若 error 之前已经完整观察到 `UACF-D` 链，它可同时标记为 `UACF-D-positive + infrastructure-error`。只有目标链确实无法判定时，才进入 upper bound。

只有 opportunity-conditional 和 eligible-decision estimands 使用对应 eligible denominator，并同时报告该 denominator 相对于 catalog units 的覆盖率。

unit-level bound 不能替代 event-level bound。若 unclassifiable trajectory 中未知 opportunity/decision 的最大数量没有在结果前冻结，B、C 的 event-level missingness 直接标记 `UNIDENTIFIABLE`。

若能仅依据 task schema 和 prefix-only candidate policy，在任何 outcome 解封前为每个缺失 unit 冻结最多 `H` 个候选事件，则才允许使用：

```text
lower_event = known_positive_events
              / (known_observed_events + H × unclassifiable_units)

upper_event = (known_positive_events + H × unclassifiable_units)
              / (known_observed_events + H × unclassifiable_units)
```

Severity-weighted burden 也必须在 confirmatory Stage B 解封前冻结单事件最大损失 `L_max`；否则 upper loss bound 无界，不能用于 GO/NO-GO。

还要分别报告 strict negative 与 no-opportunity，不能把它们合并为 missing。

若 missingness 与 model、task、status、trajectory length 或 site 相关，必须分层报告；不能使用 complete-case percentage 作为 primary。

## 8. 一致性与审计

所有实际打开的 reserve units 均全部双标。Block B/C 的未见 validation 标注者不得参与对应 ontology-development 标注；若 Block B 被转用于 development，则其标注者不得参与 Block C validation。确认性 positive、negative、no-opportunity 和 unclassifiable 也全部双标，不只复核阳性。

报告：

- rare binary label：Gwet AC1、positive agreement、negative agreement；
- multi-label cause：每类 positive agreement 与 macro/micro F1；
- span/decision point：exact match 与 tolerance-window F1；
- ordinal severity：Krippendorff alpha；
- disagreement：保留两位原始标签和第三方 adjudication，不覆盖原值。

上述 reliability 统计必须消费 5.2.2 冻结 matcher 产生的 pre-adjudication raw agreement roster。当前 `NOT_ESTABLISHED_NO_FROZEN_CASE_MATCHER` 状态下，positive/negative agreement、Gwet AC1 及其 bootstrap gate 均不得执行或报告为通过。

第一次未见 validation 使用 Block B。primary reliability gate 冻结为：

```text
opportunity presence / no-opportunity / UACF-D unit incidence：Gwet AC1 >= 0.80
上述 primary binary labels：positive agreement >= 0.70 且 negative agreement >= 0.70
candidate point：tolerance-window F1 >= 0.80
canonical terminal obligations：set F1 >= 0.80
terminal obligation satisfaction / deficit：Krippendorff alpha >= 0.80
```

rare-label positive reliability 还要求未见 validation 中至少出现 4 个不同 positive task ids 与 8 个 positive events；positive agreement 使用 `2a / (2a + b + c)`，其中 `a` 为双方同标阳性的 matched events，`b/c` 为只有一方标阳性的 events。point estimate 至少 0.80，按 task id 有放回抽样 10,000 次的 percentile cluster bootstrap one-sided 95% lower bound 至少 0.60。

bootstrap 实现冻结为 `NumPy 2.5.1` 的 `numpy.random.Generator(numpy.random.PCG64(seed_int))`。seed preimage 是无末尾换行的 UTF-8：

```text
Stage0F-rare-label-cluster-bootstrap-v0.1|measurement_stack_sha256=<64hex>|block=<B|BC|C>
```

取该 preimage 的 SHA-256 全部 32 bytes，以 unsigned big-endian 转为 `seed_int`。task ids 先按 UTF-8 bytes 排序；每个 replicate 抽取与原 task 数相同的 task indices、有放回，并按抽中 multiplicity 纳入该 task 的全部 matched events。zero-positive replicate 的 agreement 按 0 保留。10,000 个 binary64 结果升序排列，one-sided 95% lower bound 固定取零起始 index 499，不插值；gate 用未四舍五入值，报告保留八位小数。

Block B/C 路径在打开 Block B outcome 前自动冻结，不允许结果后选择：

1. Block B 满足上述 positive adequacy 与全部 reliability gates 时，primary reliability 只使用 B；
2. Block B 只因 positive task/event 数量不足而无法识别，且整个 measurement stack 的每个 byte hash 均未改变时，必须自动使用 B+C；
3. Block B 解封后只要修改 measurement stack 中任一 artifact，primary reliability 只使用全程未见的 C，B 只作 development evidence；
4. Block B 在阳性数足够时任一 blocking reliability metric 失败，必须修订 measurement stack 并走第 3 条，不得保留原栈再合并 B+C。

`measurement_stack_sha256` 的输入 manifest 必须按路径 UTF-8 排序，并至少覆盖：

```text
problem anchor
codebook and normative schema
generator/reference/A0/A1/Stage-B prompts
packet schemas
schema validator and semantic validator
cross-document protocol consistency checker
canonical JSON/hash implementation
candidate matcher and tolerance rule
adjudication and missingness rules
bootstrap/RNG implementation and pinned dependency lock
exposure policy and forbidden-field linter
decision card
```

每个 manifest row 使用 `relative_path NUL lowercase_file_sha256 LF`，再对完整 byte stream 取 SHA-256。注释、prompt、schema、validator、matcher、adjudication、canonicalizer 或依赖版本的任何 byte 变化都算 stack revision；不能只检查 codebook。

最终 stack 必须在任何 Block B、Block C 或 82-task confirmatory holdout 的 A1/Stage-B reveal 前写入不可变 `MEASUREMENT_STACK_FROZEN` audit event，并由独立 verifier 重算全部 file hashes、dependency versions 与前一 hash-chain head。当前文件仍在修订，因此只能称“thresholds provisionally specified”，不能称 measurement stack 已冻结。

Block A 是预先冻结且永久排除于 492-unit confirmatory holdout 的 ontology-development set。协议开发者若已查看 Block A trajectory/action，必须登记 exposure，且不得担任 blind generator/annotator；这会使 Block A 只能用于开发，**不会自动污染尚未开放的 Block B/C/82-task confirmatory evidence**。但是 Block A 的任何统计、案例或调参都不得作为 confirmatory 支持，最终 measurement stack 必须在其余 validation/holdout reveal 前重新 hash-freeze。若制定规则的人在 final freeze 前查看 Block B、Block C 或 82-task holdout 的 candidate action/A1/Stage B，则对应未见性被破坏，不能声称 confirmatory preregistration。

达不到 positive task/event 数量时不能把指标记为 1，该 rare-label reliability 记为 `UNIDENTIFIABLE`。quarantined stress set 可帮助修订手册，但不能替代未见 validation。

competing-cause multi-label 的 macro F1 冻结为至少 0.70。若 primary reliability 通过而 cause F1 未通过，可以报告 `T0-Behavior` incidence，但不得以这些标签选择 Step 2 boundary 或通过 GO TO STEP 2。

Block B 未通过时，只允许基于 disagreement 修订一次手册；随后用未见 Block C 重新计算全部 gate。Block C 仍有任一 blocking metric 未通过，则判 `UNIDENTIFIABLE`，不进入正式 holdout burden 计算。本体 pilot 的目标是发现定义能否稳定执行，不是追求漂亮系数。

## 9. 统计与重要性

### 9.1 `T0-Catalog` 是有限目录总体，不伪装成随机运行样本

对任何 Stage B 解封前冻结的 `N_holdout` 个 `T0-Behavior confirmatory` units，以及 648 个 secondary full-catalog units，报告 exact counts 与 proportions，不给暗示 iid sampling 的普通置信区间。由于 24-task ontology-pilot reserve、Task 035 training case 与 Task 065 stress task 已在查看 outcome 前永久排除，固定 `N_holdout = 82 tasks × 6 hosted model configs = 492 units`；后续是否实际打开全部 reserve 都不得改变这个分母。

模型、task 与 provenance cluster 的差异用于描述异质性与检查集中性。六个模型在同一 task 上不是六个独立 task families；同 template/site 的 tasks 也不能假装独立。

当前官方公开 metadata 没有完整的 `task id → template/family/site/apps` 映射。正式 outcome label 解封前，必须由独立 metadata annotators 只依据 task instruction、应用标识和任务模板进行双标归类；他们不得查看模型、轨迹结果、UACF 标签或作者 challenge 标签。codebook、映射、分歧裁决与 hash 冻结后，才允许报告跨 cluster 异质性。若无法建立这种 outcome-blind mapping，只能报告跨 task id 的集中度，不能声称跨 family/site 泛化。

若未来解锁 `T1-Run` 并新增多 seed 运行，才使用 task/family/site clustered hierarchical analysis；seed 只作为 family 内技术重复。

### 9.2 重要性由预冻结 correctness-burden index 定义

不使用“阳性超过 10%”或“severity 至少 2”这种结果后可调的任意阈值。Step 1 的 primary 量只采用 `stage0f_step1_decision_card.md` 中已经冻结的 canonical terminal-obligation correctness deficit：

```text
terminal_associated_correctness_deficit_unit
= |D_u| / |O_applicable(u)|

holdout_terminal_associated_correctness_deficit
= sum(task-level six-config means over held-out tasks)
```

primary research-decision threshold 为 strict-lower `holdout_terminal_associated_correctness_deficit >= 1.0 task-equivalent`。它是 correctness-burden 研究筛选阈值，不是 utility、总损失、可避免损失或部署经济价值。

`coincident_loss_upper_envelope` 只表示与 `UACF-D` 同时出现的观察性 correctness deficit 上界。`achievable repair effect`、preventable fraction、probe policy 的真实收益以及 intervention net headroom 都必须由 Step 2 的 boundary-isolated replay 估计；Step 1 禁止填入或外推这些量。

`safety-dominant` 与 `high-review-cost` 只作为不带结果后权重的 sensitivity flags 并列报告，不能覆盖 primary correctness-burden index，也不能用“至少一套 regime 为正”触发 GO。

以下通用替代方案只能在 Step 2 作为真实对照，不能从已发布观察性轨迹推断收益：

- never commit；
- fixed inspect before commit；
- ask human confirmation；
- generic reflection/context refresh。

如果 canonical obligation set、correctness-burden aggregation 或 worth-investigating threshold 未在 confirmatory UACF-D labels 前冻结，就只能报告描述性 decision curve，不能给 Step 1 binary GO。阈值不能根据阳性率倒推。

## 10. Step 1 判定规则

`stage0f_step1_decision_card.md` 是 Step 1 唯一的数值与派生决策源。本文不复制 GO、NO-GO 或 `UNIDENTIFIABLE` 条件，以免两套规则漂移。Step 1 只能产生 C0-A/B/C/D/E 五维结果及 candidate interface inventory；C0-E 单独决定是否允许保留 Environment-Falsifiable 主标题。Step 1 不判定 faithful replay、intervention implementability 或 causal execution readiness。

当决策卡允许进入 Step 1.5 / Step 2 protocol construction 时，唯一安全表述是：

> 已发布 OSWorld 2.0 目录中的 `UACF-D` 行为负担达到冻结研究门槛，并且存在供 Step 1.5 检查的 candidate interface inventory；是否能执行竞争性根因实验尚未确定。只有 C0-E 支持 pure-world-transition 时才可保留 Environment-Falsifiable 表述，否则必须使用决策卡给出的改名或范围上限。

## 11. Step 1 通过后才能做什么

Step 1 GO 只会生成 published-trajectory candidates 与行为负担证据。Step 2 才检验统一的竞争边界本体：

```text
E：没有获取/监测变化或变化未被交付
O：raw observation 没有包含或保真呈现变化
G：已交付 observation 中的变化没有被正确解析
R：持久状态没有更新或行动时不可读
P：没有找到受影响 artifact 与 repair obligations
S：semantic action 选择错误
A：GUI realization 失败
V：没有验证或没有消费验证结果
Environment：状态漂移、TOCTOU、session 或不可恢复 side effect
Evaluator/Task：规范真值或评估器本身无效
Budget/API：预算终止或基础设施异常
```

Step 1 GO 只开放 Step 2 protocol construction，不直接开放因果执行。执行前必须按 `stage0f_step1_5_replay_identification_card.md` 的 S1.5-A/B/C/D/E 与互斥真值表裁决。若原 hosted model/build 不可恢复，最多进入 reconstructed-agent transport experiment，不得声称解释原 published trajectory 的内部根因。

`C1-R` 的目标 estimand 是 `R→P` boundary payload 的 total downstream effect。stale/correct 两臂必须固定 observation/grounding prefix、agent architecture、weights、prompt template、tools、evaluator、预算、payload schema/位置/长度档位和所有非目标内容；planner、semantic action 和 GUI action 的实现值是中介，不得固定。若 correct arm 同时增加 instruction、repair hint、retrieval coverage、policy code 或预算，只能称 `state-conditioning package effect`。

R 与 dependency repair P 使用预冻结的 factorial：

```text
R ∈ {stale, correct}
P_operator ∈ {
  identity_no_propagation,
  flat_scan,
  dependency_graph_propagation
}
```

三个 P arms 都通过同一个 versioned consumer API 接收同一 R payload、同一 action-relevant semantic closure 与同一可见性/serialization/budget；不存在“没有 consumer 因而 R 结构性无效”的 arm。`identity_no_propagation` 只返回目标 proposition，不传播依赖；`flat_scan` 对同一 closure 的 canonical flat relation list 做扫描；`dependency_graph_propagation` 对等价 typed graph 做预冻结 traversal。每个 P arm 都必须通过 operator-selection、closure-hash、非目标 fingerprint 与 budget manipulation check；任一 arm 改变信息集合、额外提示、真值、格式档位或共同 consumer API 时，只能称 package effect。分别报告 `tau_R(p)`、`tau_P(r)` 与 interaction。即使 R total effect 为正，也只证明 action-time state conditioning 有作用；它不自动证明原 hosted Agent 的 endogenous memory update/retrieval 是失败根因。

`C3-a` 只有在 typed 与 flat 两臂具有相同 semantic information closure 时才可归因为 representation gain。唯一字段集合以 research contract 与后续 machine-readable closure schema 为准，至少覆盖：proposition/value、version、evidence、refutation、timestamp、validity condition、dependency edge、obligation、deadline/commit point、uncertainty、recovery option、source provenance。flat→typed 与 typed→flat 必须在 outcome-blind 条件下双向无损，`decode(flat)`、`decode(typed)` 与两方向 roundtrip 后的逐 semantic atom/relation hash 都等于同一 canonical closure，并匹配 retrieval coverage、ordering、token/latency/action budget、planner 与 update policy。typed arm 独有 deterministic propagation operator 时只能称 `representation + operator package effect`。

`C4` 不能由 C3-a 正结果推出。改变能力边界必须在 outcome 解封前冻结的机制相关 difficulty axis 上**同时**满足 scaling change 与 frontier extension，并在完全未见 task family 复现：

```text
FRONTIER_EXTENSION:
在 simultaneous confidence band 下，
method 从最低难度起连续达到成功门 tau 的最大 level
严格高于 baseline；
至少一个 extension level 上 method lower band >= tau
且 baseline upper band < tau

SCALING_CHANGE:
method × difficulty interaction 通过方向、效应量与 CI 门，
且高难度端达到功能性成功标准
```

simultaneous uncertainty procedure、multiplicity family、单调/非单调处理、`tau`、预注册方向、最小 interaction effect `delta_min` 与至少一个完整 difficulty level 的最小 frontier extension 必须在 outcome 前冻结；frontier 只能取“从最低难度开始连续满足门”的最大 level，不能越过一个失败 level 后在更高 level 重新定义 frontier。多个 difficulty axes 必须冻结 primary axis，或对 axes 使用 familywise multiplicity control。平均提升、平行曲线、只有 frontier 或只有 interaction、pointwise CI 挑选 level，或只在 seen templates 上成立，最多支持 C3-a / robust performance gain；额外 token、oracle truth 或 coverage 造成的曲线变化使 C4 `UNIDENTIFIABLE`。

## 12. 当前 Step 1 状态表

| Gate | 当前状态 | 证据 |
|---|---|---|
| `T0-Catalog` snapshot/config scope 冻结 | **PASS** | 2026-07-22 hosted snapshot、108 tasks、6 configs；各 `max_steps=500`，但 standard steps 与 batch-tool model_steps 不同 |
| hosted trajectory 的逐运行 build/provenance | **UNKNOWN** | 本地公开 commit 与 release manifest 不能逐轨迹证明实际运行代码、环境和 attempt history |
| `T0-Catalog` cell coverage | **PASS** | 648/648 cells，各一条 catalog trajectory |
| launched-run / retry / publication-selection 完整 | **UNKNOWN / T1-Run LOCKED** | 无 run id、seed、launch/retry/exclusion manifest；缺少证明不等于证明官方筛选 |
| 逐 unit replay 可用性 | **PARTIAL** | 48 份本地 archived HTML bytes 可被当前本地 parser 投影；47/48 有 replay JSON，共 9,138 steps；Task 050 × MiniMax 为 explicit no-step。source origin authenticity、trusted capture time、screenshot bytes 与 timeline alignment 均未证明 |
| 逐 unit normative truth / evaluator provenance | **PENDING** | release-tagged task/evaluator truth 尚未逐运行绑定；不能由 replay availability 代替 |
| Stage A outcome-blind measurement implementation | **REVISE / V2 SYNTHETIC MECHANICS GREEN；PROTOCOL NOT FROZEN** | v2 当前 94/94 Stage A tests、28/28 strict schemas 通过，并覆盖 X58–X64 与 R02/R04/R06/R07/R09/R10/R11/R12/R15；但无 frozen case matcher、human dual-entailment records、external raw/time/access/role authority，且 mechanical verifier 仅为 synthetic typed claim |
| 盲标本体可靠 | **PENDING** | 尚未执行 pilot |
| 行为负担 | **PENDING** | 尚未标注，禁止使用作者 challenge tags 代替 |
| research-decision thresholds | **PROVISIONALLY SPECIFIED；MEASUREMENT STACK NOT FROZEN；NOT EXECUTED** | global task/interface/deficit upper 与 joint structural completions 已进入 decision card；只有 schema/validator/dependency lock/manifest 完整并经 fresh review 后才能 freeze |
| Memory 根因 | **INELIGIBLE** | Step 1 不做因果归因 |
| 行动契约有效 | **INELIGIBLE** | 必须等待 Step 2 与等命题表示对照 |
| Step 1 总裁决 | **FRAME-READY / DETAIL-AVAILABILITY-PARTIAL / MEASUREMENT IMPLEMENTATION NOT READY** | 目录 frame 与 detail availability 已审计；packet instrument、ontology reliability 与 burden 均未通过，Step 2 未开放 |

## 13. 复现锚点

2026-07-22 只读接口快照的 SHA-256：

```text
GPT-5.5                 2a0e8ba3f185e42fd1aafd9a3b1de6b45458d8187a4325266890eb95e63760b8
MiniMax M3              5ddcdd0cf5cb7144ff438d3a0acd4999ce66d364b1d88943fbbd2c5a522d9049
Claude Opus 4.7         f61790e30198452f6c764a932f50964542d5515ff4bfa1744f8009d94ea1c967
Qwen 3.7-Plus           65f63fb00556faf5a8ac1737d19a73bd559867a6f3b1e7a514486b33e5da82ad
Claude Sonnet 4.6 Max   c5d623471d30700ac0aa93f3354f4b5daceb4a3848313a4d7e697193ea93bf21
Claude Sonnet 4.6 Med   9673f83393843cbda79eef303b2a786c8d9251b70b00b4b5dc5df9309f3818e3
```

这些 hash 锚定的是 2026-07-22 接口返回内容，不是官方签名，也不能替代作者的 run manifest。
