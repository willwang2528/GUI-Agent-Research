# Stage 0F：Step 1 决策与损失卡

> 版本：v0.6，2026-07-28  
> 状态：**DECISION THRESHOLDS PROVISIONALLY SPECIFIED；MEASUREMENT STACK NOT FROZEN；NO CONFIRMATORY RESULT**  
> 适用总体：OSWorld 2.0 `T0-Behavior confirmatory holdout`  
> 作用：判断 published-trajectory phenomenon 是否值得进入 Step 2，不估计部署收益

本卡中的“冻结/预冻结”均指 **provisional freeze target**：只有 measurement schema、validator、dependency lock、input provenance、missingness roster 与本卡共同生成不可变 measurement-stack hash 后，才能升级为 confirmatory frozen。当前不具备该状态。

> 当前执行 verdict：**NO BLOCK A**。本轮仅修订 outcome-blind decision rules，未打开 confirmatory outcome；measurement stack、certificate validator 与 input provenance 尚未整体冻结。

## 1. 为什么需要这张卡

不能在看到阳性率后再决定“多少算重要”。也不能在没有 replay 的 Step 1 中假设某个 Memory 方法能修复多少失败。

本卡只回答一个研究决策：

> 冻结目录中的 `UACF-D` 是否提供足够数量、损失和 candidate interface inventory，使投入 Step 2 的竞争性根因实验有价值；其中纯环境变化是否单独达到保留 Environment-Falsifiable 研究题目的门槛？

它不回答：

- 生产环境风险；
- preventable fraction；
- achievable repair effect；
- 新方法的净收益；
- Memory 或行动契约是否有效。

## 2. Primary candidate-supply gate

Stage 0E 的跨任务根因协议要求至少八个不同 task families 的 published-trajectory candidates。当前没有可靠 family mapping，因此 Step 1 使用更弱、但可审计的前置必要条件：

```text
known_positive_task_ids >= 8
```

其中：

- positive 必须是完整 `UACF-D`，不能用 `EACF-P` 替代；
- 同一 task 的六个模型最多贡献一个 `known_positive_task_id`；
- 8 不是 prevalence、utility 或独立重要性主张，而是后续八任务因果诊断的最小候选供给门；
- `known_positive_units` 与 unit-incidence lower/upper bound 继续完整报告，但不作为与 candidate supply 独立的第二个 GO 条件。

即使达到八个 task ids，若 outcome-blind structural grouping 显示它们来自少于四个 structural groups，仍不能进入 Step 2 的一般性根因主张。

### 2.1 C0-B 的 event-keyed global upper

令 `T` 为冻结的 82 个 held-out task ids。每个被检测到的候选事件必须有稳定且唯一的：

```text
event_key
= (task_id, unit_id, boundary_location_id, adjudicated_event_id)
```

其中 `boundary_location_id` 绑定 candidate action reveal 前的 cutoff ordinal 与净化 prefix payload；`adjudicated_event_id` 绑定 A0 独立冻结的 proposition、排序后的 obligation set、boundary type、schema 与 codebook hash。同一 location 可有多个已裁决 event ids。只有同一 `event_key` 的已观察 phenotype、source、obligation 与 interface 字段可以联合裁决；不同 `event_key` 的字段不得拼接成一个阳性。

对未检测可能性，不枚举假想的自然语言 event。finite hidden-location universe 固定为：

```text
Lambda
= {(task_id, config_id, observation_ordinal):
   task_id in frozen 82-task roster,
   config_id in frozen six-config roster,
   observation_ordinal in the unit's frozen ordinal roster}
```

对每个 location `l in Lambda`，joint completion 只包含以下 sufficient bits：

```text
exists_B[l]
exists_B_and_interface[l]
exists_WORLD_and_B[l]
exists_WORLD_and_B_and_interface[l]

for every canonical obligation o applicable to l's unit:
  exists_B_and_unmet[l, o]
  exists_WORLD_and_B_and_unmet[l, o]
```

每个 joint bit 都表示 **同一潜在 event / decision boundary** 上的联合存在，不是两个 marginal events 的并集。每个 completion 必须满足：

```text
all bits are in {0, 1}

exists_B_and_interface[l] <= exists_B[l]
exists_WORLD_and_B[l] <= exists_B[l]

exists_WORLD_and_B_and_interface[l]
<= exists_B_and_interface[l]

exists_WORLD_and_B_and_interface[l]
<= exists_WORLD_and_B[l]

exists_B_and_unmet[l, o] <= exists_B[l]

exists_WORLD_and_B_and_unmet[l, o]
<= exists_WORLD_and_B[l]

exists_WORLD_and_B_and_unmet[l, o]
<= exists_B_and_unmet[l, o]
```

已确认 direct evidence 把相应 bit 固定为 1；有效 mechanical negative certificate 把其谓词 bit 固定为 0；其余 missing location bits 在上述 joint constraints 内自由完成。task/unit 量由 location bits 的 finite OR 和 canonical-obligation 去重机械派生。禁止将 phenotype、WORLD、interface 或 unmet 的 marginal upper 相乘、相加或跨 location 拼接来构造 joint upper。

### 2.2 Fail-closed negative-certificate artifact

所有 global negative certificate 都必须是 validator 可复算的 artifact，而不是 annotator 的结论字段。每份 task-level artifact 至少包含：

```text
predicate_id
task_id
exact_six_config_ids

for every config:
  unit_id
  unit_ordinal_roster
  unit_ordinal_roster_sha256
  trajectory_hash_chain_root

  for every ordinal in the roster:
    location_id
    disposition
    direct_evidence_pointers
    proof_mode
    verifier_id
    verifier_version
    verifier_output_hash

artifact_schema_version
constraint_set_hash
validator_id
validator_version
validator_output_hash
```

允许的 `disposition` 仅为能机械蕴含目标 bit 为 0 的 `MECHANICALLY_NO_OPPORTUNITY` 或 `MECHANICALLY_PREDICATE_FALSE`。`proof_mode` 必须来自预冻结 mechanical whitelist，并由 direct pointers 与 hash chain 复算；`HUMAN_NOT_FOUND`、`REFERENCE_AGENT_NOT_FOUND`、`SEARCH_RETURNED_NONE`、自由文本解释或“审阅后未发现”都不能签发 negative certificate。

对任一谓词 `q`：

```text
certificate_q(task, config)
= valid artifact and exact roster/hash-chain match
  and every frozen ordinal has a valid mechanical q-false disposition

certificate_q(task)
= AND over the exact six hosted configs certificate_q(task, config)
```

缺 config、缺 ordinal、hash 不匹配、缺 direct pointer、proof mode 不在 whitelist、validator 失败或不存在可验证的 mechanical completeness proof 时，一律 fail closed：

```text
certificate_q = 0
```

分别冻结六类谓词；一种证书不能替代另一种：

```text
q_B                  := exists_B
q_C                  := exists_B_and_interface
q_env                := exists_WORLD_and_B
q_env_interface      := exists_WORLD_and_B_and_interface
q_B_deficit[o]       := exists_B_and_unmet[o]
q_env_deficit[o]     := exists_WORLD_and_B_and_unmet[o]
```

前四类形成六配置 task-level AND。deficit 类先对每个 `(unit, canonical obligation)` 生成 fail-closed certificate，再按六配置 task-equal 规则聚合；另报的 task-level deficit-negative certificate 必须是六配置中每个适用 obligation certificate 的 AND。human/reference 未发现不能贡献任何一类 certificate。

在上述定义下，对 C0-B 定义：

```text
P_B
= {t in T:
     exists event_key e in task t
     such that e is confirmed UACF-D-positive}

R_B_detected
= {t in T:
     exists detected event_key e in task t
     whose UACF-D status remains legally positive-compatible}

N_B_strict
= {t in T:
     certificate_q_B(t) = 1}

L_B_tasks = |P_B|

U_B_tasks_detected
= |P_B union R_B_detected|

U_B_tasks_global
= |T minus N_B_strict|
```

等价的逐 task global negative certificate 为：

```text
negative_certificate_B(t) = 1
iff certificate_q_B(t) = 1

U_B_tasks_global
= sum over t in T [1 - negative_certificate_B(t)]
```

`N_B_strict = {t: negative_certificate_B(t)=1}`。共同漏检、packet 无效、coverage 不完整、任一 config/ordinal 未覆盖或 task 未审计都使 certificate 为 0。因此必须满足：

```text
0 <= L_B_tasks <= U_B_tasks_detected <= U_B_tasks_global <= 82
```

`U_B_tasks_detected` 只诊断当前 generator/roster 的候选供给，不能触发 `BELOW_FROZEN_GATE`。只有 `U_B_tasks_global < 8` 才能在 task-count 维度支持 NO-GO；这保证共同漏检不会伪装成现象不存在。

## 3. Primary correctness-burden index

### 3.1 冻结 obligation set

对每个 unit，metadata/normative annotators 在看该模型 trajectory outcome、score、status 和作者标签前，从 Agent-visible instruction、运行前冻结的 normative action schema 与 pre-decision state 得到实际适用的 canonical terminal obligation set：

```text
O_applicable(u) = {o_1, o_2, ..., o_k}
```

每个 obligation 必须具有：

- externally checkable predicate；
- applicable scope；
- deadline 或 commit point；
- outcome-independent evidence source；
- 与其他 obligations 的去重规则。

canonicalization 必须以 release-tagged evaluator predicate 或 outcome 前冻结的规则为锚。每个 canonical terminal predicate 最多计数一次；同义改写、父子 predicate、同一 artifact 的中间状态与终态不得重复计数。禁止根据模型轨迹把 obligation 拆细或合并。

primary deficit estimand 要求：

```text
|O_applicable(u)| >= 1
```

无法冻结 obligation set 或得到空集的 unit 不能贡献 known correctness deficit，并进入 missingness audit。该 unit 保留在六配置分母中，且强制：

```text
d_B_lower(u) = 0
d_B_upper_detected(u) = 1
d_B_upper_global(u) = 1

d_env_lower(u) = 0
d_env_upper_detected(u) = 1
d_env_upper_global(u) = 1
```

此时不得签发 `q_B_deficit[o]`、`q_env_deficit[o]` 或任何 unit/task deficit-negative certificate；不存在 denominator 不能被解释成“无 deficit opportunity”。

### 3.2 Unit deficit

对 `task × model` unit，定义 `D_u` 为与已冻结 `UACF-D` dependency edge 相连、并在 final state 仍未满足的 canonical terminal obligations：

```text
terminal_associated_correctness_deficit_unit
= |D_u| / |O_applicable(u)|
```

实际实现必须写成一个 `[0, 1]` 的单值比例；这里换行只为可读性。primary 中：

- `L_max = 1`；
- correctness、artifact contamination 与 downstream omission 不重复计价；
- reversibility、human effort、token、latency 与 financial/safety severity 不加入 primary；
- 如果只能证明同时出现、不能证明因果，字段名保持 `terminal_associated_correctness_deficit`，不得写 `caused_loss` 或 `prevented_loss`。

### 3.3 Task-equal aggregation

避免同一 task 的六个模型把一个模板放大六倍：

```text
terminal_deficit_task
= sum(terminal_associated_correctness_deficit_unit over six hosted configs) / 6

holdout_terminal_associated_correctness_deficit
= sum(terminal_deficit_task over held-out tasks)
```

分母始终是该 task 的六个 hosted configs。unclassifiable config 的 strict-lower unit deficit 固定为 0，optimistic-upper unit deficit 固定为 1；不得删除 missing config 后重算均值。

对 correctness deficit 同样区分 detected-roster diagnostic upper 与 global worst-case upper。对每个 unit：

```text
d_B_lower(u)
= confirmed terminal-associated correctness deficit in u

d_B_upper_detected(u)
= the largest deficit compatible with confirmed plus detected unresolved
   event_key/obligation records in u, deduplicated and capped at 1

for every o in O_applicable(u):
  m_B_lower(u, o)
  = 1 iff a confirmed B-positive dependency edge is associated with
    terminally unmet o

  m_B_upper_global(u, o)
  = m_B_lower(u, o), if certificate_q_B_deficit(u, o) = 1
    otherwise 1

d_B_upper_global(u)
= sum over o in O_applicable(u) m_B_upper_global(u, o)
  / |O_applicable(u)|
```

certificate 与 confirmed positive 冲突时 artifact 无效，不允许把 lower 从 1 改成 0。三者都按六配置 task-equal 规则聚合。只有 `U_B_deficit_global` 可以触发 deficit 维度的 `BELOW_FROZEN_GATE`；`U_B_deficit_detected` 只报告 generator coverage 对结论的敏感性。

```text
L_B_deficit
= task-equal aggregate of d_B_lower

U_B_deficit_detected
= task-equal aggregate of d_B_upper_detected

U_B_deficit_global
= task-equal aggregate of d_B_upper_global

0 <= L_B_deficit <= U_B_deficit_detected <= U_B_deficit_global <= 82
```

primary worth-investigating threshold 冻结为：

```text
strict_lower_holdout_terminal_associated_correctness_deficit >= 1.0 task-equivalent
```

这个阈值要求目标现象至少对应一个完整 task-equivalent 的 terminal associated correctness deficit，而不是大量趋近于零的语言差异。它只是研究筛选阈值，不是 utility、总 loss 或部署经济价值。

### 3.4 C0-B 四值裁决

按优先级匹配一次：

| 优先级 | 条件 | `C0-B` |
|---:|---|---|
| 1 | required lower/global upper 缺失、非有限、违反 lower ≤ upper，finite location universe/hash/provenance 无法验证，或 certificate artifact/validator 规则未冻结 | `UNIDENTIFIABLE` |
| 2 | `L_B_tasks >= 8` 且 `L_B_deficit >= 1.0` | `SUPPORTED` |
| 3 | `U_B_tasks_global < 8` 或 `U_B_deficit_global < 1.0` | `BELOW_FROZEN_GATE` |
| 4 | bounds 有效且 finite，但 strict lower 未全部过门、global upper 也未证伪门槛 | `INCONCLUSIVE` |

`INCONCLUSIVE` 表示问题可识别但 finite bounds 跨门；`UNIDENTIFIABLE` 表示 measurement/bound/provenance 本身无效。二者不得互换。detected-roster upper 不参与第 3 行。

## 4. Structural dispersion and concentration gate

在任何 confirmatory trajectory outcome 解封前，必须完成 outcome-blind structural mapping。门槛冻结为：

```text
K_group >= 4
K_site_or_app_set >= 3
K_model_family >= 3
max_exposure_normalized_structural_positive_share < 0.5
max_exposure_normalized_site_app_positive_share < 0.5
max_exposure_normalized_model_family_positive_share < 0.5
max_exposure_normalized_structural_deficit_share < 0.5
max_exposure_normalized_site_app_deficit_share < 0.5
max_exposure_normalized_model_family_deficit_share < 0.5
```

structural group 由三部分构成：

```text
site/application set
+ workflow type
+ action-object dependency pattern
```

structural-group codebook、字段取值集合与归并规则必须在任何 pilot Stage B outcome 解封前冻结。site/application partition 必须互斥：每个 task 按字典序排序的完整 application tuple 只进入一个 `site_or_app_set`，不得将多应用 task 重复计入多组。structural group 也必须是每个 task 唯一所属的互斥 partition。

singleton group 不得丢弃；它们照常进入 exposure、raw mass、rate 和 maximum-share 分母。`K_group`、`K_site_or_app_set` 和 `K_model_family` 仅统计 positive mass 大于零的分区数。无法 outcome-blind 映射的 task 进入显式 `UNMAPPED` bucket 并计入质量报告；任一 holdout task 仍为 `UNMAPPED` 时，C0-D 为 `UNIDENTIFIABLE`，不允许静默排除。

两位 metadata annotators 只能看 instruction 与静态 task metadata；不得看模型轨迹、score、status、作者 challenge tag 或 UACF label。第三方裁决后冻结 mapping 与 hash。

model-family 映射冻结为：

```text
Anthropic = Claude Opus 4.7 + Sonnet 4.6 Max + Sonnet 4.6 Medium
OpenAI = GPT-5.5
MiniMax = MiniMax M3
Qwen = Qwen 3.7-Plus
```

raw positive/deficit mass share、group-specific rate 和 exposure-normalized rate share 必须同时报告；只有最后一者进入 gate。四个 model families 在 492-unit frame 中的配置暴露量为 3:1:1:1，直接要求 raw family share `<0.5` 会使相同 incidence 的零差异情形也失败。

对每套 partition 先冻结每组在 492-unit holdout 中的 exposure：structural group 与 site/app 使用 held-out task-id 数，model family 使用 held-out `task × config` unit 数。对 positive mass 或 deficit mass 分别计算：

```text
rate_g = observed_mass_g / exposure_g
exposure_normalized_share_g = rate_g / sum(rate_h over every frozen partition group h)
```

若所有 `rate_h = 0`，对应 concentration 由 burden gate 处理；若某组 exposure 无法冻结，则该 partition `UNIDENTIFIABLE`。分别计算：

1. structural-group exposure-normalized positive-task share；
2. site/app-set exposure-normalized positive-task share；
3. model-family exposure-normalized positive-unit share；
4. terminal associated correctness deficit 在 structural group、site/app set、model family 三套分区中的 exposure-normalized share。

每一分区的 maximum share 均须小于 0.5。

结构门不能只在 detected/confirmed mass 上点估计。令 `Z_D` 为第 2.1 节全部 finite-location sufficient bits 的 **joint feasible completion set**；每个 completion 必须：

- 对 observed events 保持同一 `event_key` 内 phenotype、obligation 与 task/unit 去重约束；
- 对 hidden locations 只完成 `exists_B`、`exists_B_and_interface` 与逐 obligation `exists_B_and_unmet[o]`，不枚举自然语言 event；
- 满足第 2.1 节全部 monotonic/joint constraints 与 fail-closed certificates；
- 对每个有限 canonical obligation 使用 binary `exists_B_and_unmet[o]` completion，再由有限 non-empty obligation set 机械得到 `0 <= deficit_unit <= 1` 的有理比例；不得引入任意连续 deficit 值；
- 保持六配置 task-equal 聚合和 frozen exposure；
- 把未被完整审计排除的共同漏检纳入可行 positive/deficit mass；
- 不允许从 marginal upper 相乘，或跨 `event_key`/location 拼接 phenotype、deficit 或 interface；
- 与全部已确认标签、strict negatives、missingness roster 和 provenance 一致。

`Z_D` 必须是 finite、non-empty 并可由冻结约束机械生成；逐指标互不相容的 marginal upper 不能代替 joint completions。对每个 `z in Z_D` 完整重算三个 `K` 门和六个 maximum-share 门，记全部通过为 `G_D(z) = true`。C0-D 的稳健裁决为：

```text
UNIDENTIFIABLE
= mapping/exposure or a finite non-empty Z_D cannot be frozen

SUPPORTED
= every z in Z_D satisfies G_D(z)

CONCENTRATED
= every z in Z_D violates at least one frozen gate

INCONCLUSIVE
= exists z_pass and z_fail in Z_D such that
  G_D(z_pass) is true and G_D(z_fail) is false
```

因此，未解析质量存在时，只有 `Z_D` 所有合法 completions 都通过才可写 `SUPPORTED`；可翻转 completion 必须写 `INCONCLUSIVE`，不能写 `CONCENTRATED`。如果可靠 mapping 或 finite non-empty `Z_D` 无法建立，本 gate 判 `UNIDENTIFIABLE`。通过本 gate 也不表示可泛化到未观察 task families、sites 或生产任务。

## 5. Replay-interface candidate gate 与 Step 1.5

至少八个不同 positive task ids 必须各有一个与其 confirmed UACF-D **同一 `event_key`、同一 decision boundary** 的 non-privileged、部署路径可描述 candidate interface inventory entry，满足下列至少一种：

- 可恢复 pre-decision checkpoint；
- 可重建且 fingerprint-equivalent 的 prefix；
- 可替换的 raw observation / grounding / store / planning / actuation / verification boundary；
- 上述至少一种 decision-boundary 替换接口，并且同时存在 deterministic evaluator 或可盲化的 outcome adjudication；只有 final-state evaluator replay 不合格。

只有轨迹截图而没有任何可观察干预边界的 case 可以支持现象负担，但不能让 Step 1 放行因果 Step 2。Step 1 对每个候选只冻结：

```text
candidate_interface_id
candidate_boundary_type
interface_observed
non_privileged_deployment_path_documented
intervention_implementable = NOT_EVALUATED
faithful_replay_verified = NOT_EVALUATED
boundary_isolation_verified = NOT_EVALUATED
```

`interface_observed` 与“部署路径可描述”只构成 candidate inventory，不推出可实现、faithful replay 或 boundary isolation。后三项在 Step 1 必须保持 `NOT_EVALUATED`；Step 1 GO 只开放 Step 2 protocol construction，Step 2 因果执行前还必须通过 `stage0f_step1_5_replay_identification_card.md`。

C0-C 的 same-event task bounds 冻结为：

```text
P_C
= {t in T:
     exists one event_key e in task t such that
     e is confirmed UACF-D-positive
     and that same e/decision_boundary_id has a qualifying interface entry}

R_C_detected
= {t in T:
     exists one detected event_key e in task t that remains jointly compatible
     with UACF-D positivity and a qualifying interface at that same boundary}

N_C_strict
= {t in T:
     certificate_q_C(t) = 1}

L_C_interface_tasks = |P_C|

U_C_interface_tasks_detected
= |P_C union R_C_detected|

U_C_interface_tasks_global
= |T minus N_C_strict|
```

逐 task same-event certificate 形式为：

```text
negative_certificate_C(t) = 1
iff certificate_q_C(t) = 1

U_C_interface_tasks_global
= sum over t in T [1 - negative_certificate_C(t)]
```

构造上，`negative_certificate_C(t) >= negative_certificate_B(t)`，即 `N_B_strict` 是 `N_C_strict` 的子集：能严格排除 phenotype 的 task 必然也能排除 same-event phenotype-plus-interface。令：

```text
P_U_global = U_B_tasks_global
I_U_global = U_C_interface_tasks_global
```

必须机械验证：

```text
0
<= L_C_interface_tasks
<= U_C_interface_tasks_detected
<= U_C_interface_tasks_global
<= U_B_tasks_global
<= 82

I_U_global <= P_U_global
U_C_interface_tasks_detected <= U_B_tasks_detected
```

`U_C_interface_tasks_detected` 只诊断已检测 roster，不得触发 `ABSENT`。一个 task 上不同事件的 phenotype 与 interface 不能被拼成 same-event candidate；hidden location 只能使用联合 bit `exists_B_and_interface`。

C0-C 按优先级作四值裁决：

| 优先级 | 条件 | `C0-C` |
|---:|---|---|
| 1 | required same-event lower/global upper 缺失、非有限、违反约束，finite location universe/hash/provenance 无法验证，或 certificate artifact/validator 规则未冻结 | `UNIDENTIFIABLE` |
| 2 | `L_C_interface_tasks >= 8` | `PRESENT` |
| 3 | `U_C_interface_tasks_global < 8` | `ABSENT` |
| 4 | bounds 有效且 finite，但 lower < 8 ≤ global upper | `INCONCLUSIVE` |

`INCONCLUSIVE` 是 valid finite same-event bounds 跨门；`UNIDENTIFIABLE` 是 bound/provenance 无效。detected-roster upper 不参与第 3 行。

## 6. C0-E：pure-world environment gate

### 6.1 事件来源必须互斥且穷尽

`update_source_labels` 的事实标签词表冻结为：

```text
world_truth_changed
task_goal_changed
previously_true_fact_newly_revealed
explicit_corrective_feedback
source_unidentifiable
```

`world_truth_changed` 只有在同一 action-relevant proposition/object 上同时存在有序的 pre-update environment evidence 与 post-update environment evidence，且两者证明环境真值在运行期间发生转变时才成立。仅仅在后续截图中第一次看到一个早已为真的事实属于 `previously_true_fact_newly_revealed`；用户改变目标属于 `task_goal_changed`；纠错消息属于 `explicit_corrective_feedback`。Agent 自己改口、误读或后续错误动作都不能作为 world transition evidence。缺少可核验的 pre/post 环境状态或时间顺序时，不得标成 `PURE_WORLD`。

事件来源类别不是 annotator 可自由选择的第二套标签，而是由已裁决的 `update_source_labels`、逐标签 direct evidence pointer 和 packet validation 机械派生。必须先做 measurement validity 检查，再派生来源类别：

| measurement / 来源结果 | 机械判定 |
|---|---|
| `INVALID_SOURCE_MEASUREMENT` | label set 为空；含词表外标签；`source_unidentifiable` 与其他标签并存；任一 emitted 标签缺 direct pointer / auditable reason record；或 packet schema、event key、provenance 非法 |
| `SOURCE_UNKNOWN` | packet 合法，label set 恰好为 `{source_unidentifiable}`，且该标签的 direct pointer / auditable reason record 通过审计 |
| `PURE_WORLD` | packet 合法，label set 恰好为 `{world_truth_changed}`，且该标签的直接 evidence pointer 通过审计 |
| `MIXED_WORLD` | packet 合法，label set 含 `world_truth_changed`，同时含至少一个其他已识别事实标签，且每个标签的直接 evidence pointer 均通过审计 |
| `NON_WORLD` | packet 合法，label set 不含 `world_truth_changed`，至少含一个其他已识别事实标签，且每个标签的直接 evidence pointer 均通过审计 |

`SOURCE_UNKNOWN` 是四个合法、互斥且穷尽的来源类别之一；它表达“合法 packet 明确记录来源不可判定”。`INVALID_SOURCE_MEASUREMENT` 不是第五个 source category，而是 measurement missingness，必须进入 invalid-packet roster 与质量审计，不能伪装成 source uncertainty。对每个 schema-valid packet，四个合法类别恰好派生一个；schema-invalid packet 不派生来源类别。

Environment-Falsifiable 主分析只纳入 `PURE_WORLD`。`MIXED_WORLD`、`NON_WORLD` 可进入通用 UACF-D 副分析；`SOURCE_UNKNOWN` 与 `INVALID_SOURCE_MEASUREMENT` 都不能贡献 pure-world strict lower bound。只要尚未被合法 strict-negative 证明不可能为 pure-world positive，它们都保留在 global worst-case upper；二者必须分栏报告。不能用“primary source 排序”把 mixed event 重新命名为 pure-world。

### 6.2 Pure-world 联合 lower/upper bounds

所有 pure-world bounds 都在与 C0-B/C0-C 相同的 82-task、492-unit confirmatory holdout 上计算。task id、unit、obligation 和 candidate interface 各自只计一次；同一 task 的六个 hosted configs 不得被当成六个 task。

冻结三个联合量：

```text
L_env_tasks
= number of distinct task ids with at least one
  confirmed UACF-D-positive PURE_WORLD event

L_env_interface_tasks
= number of distinct task ids counted by L_env_tasks that also have at least
  one confirmed PURE_WORLD UACF-D event whose own decision boundary has a
  qualifying C0-C candidate interface inventory entry
```

令 `P_env` 和 `P_env_interface` 分别为上述两个 lower 所计 task 集。再定义：

```text
R_env_detected
= {t in T:
     exists one detected event_key in t that remains jointly compatible with
     PURE_WORLD and UACF-D-positive}

R_env_interface_detected
= {t in T:
     exists one detected event_key in t that remains jointly compatible with
     PURE_WORLD, UACF-D-positive, and a qualifying interface at that same
     decision boundary}

N_env_strict
= {t in T:
     certificate_q_env(t) = 1}

N_env_interface_strict
= {t in T:
     certificate_q_env_interface(t) = 1}

U_env_tasks_detected
= |P_env union R_env_detected|

U_env_interface_tasks_detected
= |P_env_interface union R_env_interface_detected|

U_env_tasks
= |T minus N_env_strict|

U_env_interface_tasks
= |T minus N_env_interface_strict|
```

等价地，逐 task 定义：

```text
negative_certificate_env(t) = 1
iff certificate_q_env(t) = 1

negative_certificate_env_interface(t) = 1
iff certificate_q_env_interface(t) = 1

U_env_tasks
= sum over t in T [1 - negative_certificate_env(t)]

U_env_interface_tasks
= sum over t in T [1 - negative_certificate_env_interface(t)]
```

certificate validator 必须应用 joint-bit 蕴含关系：

```text
negative_certificate_env(t) >= negative_certificate_B(t)

negative_certificate_env_interface(t)
>= negative_certificate_env(t)

negative_certificate_env_interface(t)
>= negative_certificate_C(t)

certificate_q_env_deficit(u, o)
>= certificate_q_B_deficit(u, o)
```

因此 `N_B_strict` 是 `N_env_strict` 的子集，`N_env_strict` 与 `N_C_strict` 都是 `N_env_interface_strict` 的子集；WORLD/interface 联合条件不可能比其 constituent condition 更宽。`U_env_tasks` 与 `U_env_interface_tasks` 是 **global worst-case joint upper bounds**。未审计 task、coverage 不完整、共同漏检、`SOURCE_UNKNOWN` 和 `INVALID_SOURCE_MEASUREMENT` 只要未被合法 strict-negative 排除，都必须进入相应 global upper。

`U_env_*_detected` 只诊断 detected roster，不能触发 `BELOW_FROZEN_GATE`。hidden locations 必须直接使用 `exists_WORLD_and_B` 与 `exists_WORLD_and_B_and_interface` joint bits；不得把 source、phenotype 与 interface marginal upper 相乘或拼接。已确认且 measurement-valid 的 `MIXED_WORLD` 或 `NON_WORLD` event 自身不进入 pure-world upper；但同 task 中尚未被 fail-closed certificate 排除的 hidden locations 仍保留在 global upper。

对 unit `u`，`d_env_lower(u)` 只包含与 confirmed `PURE_WORLD UACF-D` dependency edge 相连、且 final state 未满足的 canonical terminal obligations。上界分两套：

```text
d_env_upper_detected(u)
= largest deficit compatible with confirmed plus detected unresolved
   same-event source/phenotype/obligation records, deduplicated and capped at 1

for every o in O_applicable(u):
  m_env_lower(u, o)
  = 1 iff a confirmed WORLD-and-B-positive dependency edge is associated
    with terminally unmet o

  m_env_upper_global(u, o)
  = m_env_lower(u, o), if certificate_q_env_deficit(u, o) = 1
    otherwise 1

d_env_upper_global(u)
= sum over o in O_applicable(u) m_env_upper_global(u, o)
  / |O_applicable(u)|
```

certificate 与 confirmed positive 冲突时 artifact 无效。若 unit 可审计但 unresolved，strict lower 为 0；global worst-case upper 最多为冻结的 `L_max = 1`。`|O_applicable(u)| < 1` 时严格执行第 3.1 节的 `lower=0, upper=1, no deficit-negative certificate`。task-equal 聚合冻结为：

```text
L_env_deficit
= sum over held-out task t [
     sum over six hosted configs d_env_lower(t, config) / 6
   ]

U_env_deficit
= sum over held-out task t [
     sum over six hosted configs d_env_upper_global(t, config) / 6
   ]

U_env_deficit_detected
= sum over held-out task t [
     sum over six hosted configs d_env_upper_detected(t, config) / 6
   ]
```

必须机械验证：

```text
0 <= L_env_interface_tasks <= L_env_tasks <= U_env_tasks <= 82
L_env_interface_tasks <= U_env_interface_tasks <= U_env_tasks
L_env_tasks <= L_B_tasks
U_env_tasks <= U_B_tasks_global
L_env_interface_tasks <= L_C_interface_tasks
U_env_interface_tasks <= U_C_interface_tasks_global
L_env_tasks <= U_env_tasks_detected <= U_env_tasks
U_env_tasks_detected <= U_B_tasks_detected
L_env_interface_tasks <= U_env_interface_tasks_detected
U_env_interface_tasks_detected <= U_env_interface_tasks
U_env_interface_tasks_detected <= U_env_tasks_detected
U_env_interface_tasks_detected <= U_C_interface_tasks_detected
0 <= L_env_deficit <= U_env_deficit <= 82 task-equivalent
L_env_deficit <= U_env_deficit_detected <= U_env_deficit
L_env_deficit <= L_B_deficit
U_env_deficit <= U_B_deficit_global
```

完整 finite holdout 与 missingness roster 存在时，`SOURCE_UNKNOWN`、`INVALID_SOURCE_MEASUREMENT` 或 phenotype/interface unresolved 进入 global worst-case upper，因此产生的通常是 `INCONCLUSIVE`，不是自动 `UNIDENTIFIABLE`。只有连固定分母、strict-negative 规则、source evidence provenance、canonical obligation set、`L_max` 或 candidate-interface provenance 都无法形成有限可审计 bound 时，C0-E 才为 `UNIDENTIFIABLE`。

### 6.3 冻结的 protocol thresholds

C0-E 复用已经为通用 phenotype 冻结的最小候选供给、task-equivalent correctness burden 与后续因果协议供给尺度：

```text
T_env_tasks = 8 distinct task ids
T_env_deficit = 1.0 task-equivalent
T_env_interface_tasks = 8 distinct task ids
```

这三个数是 **protocol decision thresholds**：它们在 confirmatory C0-E labels 之前冻结，只说明“是否值得保留环境题并构造后续因果协议”，不是 prevalence、utility、effect size、跨 GUI 泛化或证据已经通过的声明。当前三项均为 `NOT_EVALUATED`。

`L_env_interface_tasks >= 8` 在数值上蕴含 `L_env_tasks >= 8`，但两者仍分别输出：前者诊断后续因果 pipeline 的 candidate-interface supply，后者诊断 pure-world phenotype supply；不得把二者包装成两份独立的重要性证据。

### 6.4 C0-E 四值裁决

按下列优先级匹配一次；在 bounds 有效时四种结果互斥且穷尽：

| 优先级 | 条件 | `C0-E` |
|---:|---|---|
| 1 | 任一 required bound 缺失、非有限、违反 lower ≤ upper，或因分母/provenance/missingness universe/`L_max` 未冻结而无法审计 | `UNIDENTIFIABLE` |
| 2 | `L_env_tasks >= 8` 且 `L_env_deficit >= 1.0` 且 `L_env_interface_tasks >= 8` | `SUPPORTED` |
| 3 | global worst-case `U_env_tasks < 8` 或 `U_env_deficit < 1.0` 或 `U_env_interface_tasks < 8` | `BELOW_FROZEN_GATE` |
| 4 | bounds 有效、所有 global worst-case upper 均达到阈值，但至少一个 strict lower 未达到阈值 | `INCONCLUSIVE` |

`SUPPORTED` 只证明 frozen published holdout 中 pure-world phenotype、associated deficit 与 candidate-interface supply 同时跨过研究筛选门；它不证明 Memory 根因、repairability 或方法有效。

`U_env_tasks_detected`、`U_env_interface_tasks_detected` 与 `U_env_deficit_detected` 不参与第 3 行；无论 detected roster 多小，都不能据此输出 `BELOW_FROZEN_GATE`。

### 6.5 广泛 GUI 标题需要 pure-world structural recomputation

若标题或摘要主张广泛的 GUI environment-falsifiable phenomenon，必须在 `PURE_WORLD` 贡献上完整重算第 4 节结构门：

- 沿用 outcome-blind 冻结的 structural/site-app/model-family mapping 和全 82-task/492-unit exposure，不得只以 pure-world positive tasks 作为 exposure；
- 从 confirmed lower 开始，并把第 2.1 节所有未被合法 certificate 排除的 `exists_WORLD_and_B`、`exists_WORLD_and_B_and_interface` 与 `exists_WORLD_and_B_and_unmet[o]` bits 纳入 finite non-empty joint feasible completion set `Z_env_structure`；
- 复用第 4 节的 `K_group >= 4`、`K_site_or_app_set >= 3`、`K_model_family >= 3` 和六个 `< 0.5` concentration thresholds；
- 每个 completion 对 observed events 保持同一 `event_key` 的联合约束，对 hidden locations 保持第 2.1 节 monotonic/joint constraints、task/unit 去重、global upper、冻结 exposure 和 source measurement validity；不得枚举自然语言 events，也不得从 marginals 相乘或跨 location 拼接；
- 输出派生 scope qualifier：`PURE_WORLD_STRUCTURE = SUPPORTED / CONCENTRATED / INCONCLUSIVE / UNIDENTIFIABLE`；它不是第六个 C0 dimension。

其稳健裁决与 C0-D 相同：

```text
SUPPORTED
= every z in Z_env_structure passes all K and maximum-share gates

CONCENTRATED
= every z in Z_env_structure fails at least one frozen gate

INCONCLUSIVE
= exists z_pass and z_fail in Z_env_structure such that
  z_pass passes every gate and z_fail fails at least one gate

UNIDENTIFIABLE
= mapping/exposure or a finite non-empty Z_env_structure cannot be frozen
```

只有 `C0-E = SUPPORTED` 且 `PURE_WORLD_STRUCTURE = SUPPORTED` 才能保留不限定结构域的 broad GUI environment title。`PURE_WORLD_STRUCTURE = CONCENTRATED` 只拒绝 broad scope，并产生 narrow-scope hypothesis；它不支持任何 narrow scope claim。未来必须在新的独立 frame 与 preregistration 上重过 Step 1，才可能称 narrow scope supported。`INCONCLUSIVE` 必须阻断环境 scope claim等待证据，`UNIDENTIFIABLE` 必须先修 measurement。

## 7. Sensitivity，不能替代 primary

只报告两类 sensitivity flags：

- `safety-dominant`：是否出现不可逆外部发送、删除、授权、支付或身份/合规提交；
- `high-review-cost`：正确处理是否需要多次人工确认或长时间回溯。

它们不使用结果后选择的数值权重，也不允许覆盖 primary correctness-burden index。若 sensitivity 与 primary 呈现不同风险排序，只能并列报告，不能挑选更有利的一套。

probe、human confirmation、never-commit 与 generic reflection 的真实成本和收益只能在 Step 2 设对照；Step 1 不估计。

## 8. 五维裁决与派生决策

Step 1 不把“现象负担”和“当前能否 replay”压成一个总标签，必须分别输出：

```text
C0-A Measurement:
PASS / FAIL / UNIDENTIFIABLE

C0-B Published-holdout burden:
SUPPORTED / BELOW_FROZEN_GATE / INCONCLUSIVE / UNIDENTIFIABLE

C0-C Replay-interface candidates:
PRESENT / ABSENT / INCONCLUSIVE / UNIDENTIFIABLE

C0-D Catalog structural dispersion:
SUPPORTED / CONCENTRATED / INCONCLUSIVE / UNIDENTIFIABLE

C0-E Pure-world environment support:
SUPPORTED / BELOW_FROZEN_GATE / INCONCLUSIVE / UNIDENTIFIABLE

PURE_WORLD_STRUCTURE:
SUPPORTED / CONCENTRATED / INCONCLUSIVE / UNIDENTIFIABLE / NOT_APPLICABLE
```

五维承担两个不同决策，不能压成一个会掩盖改题条件的总标签：

1. C0-A–D 决定通用 UACF-D causal pipeline 是否可构造；
2. C0-E 决定 Environment-Falsifiable 题目能否保留；若要 broad GUI title，还必须通过 `PURE_WORLD_STRUCTURE`。

即使 C0-A–D 放行，C0-E 也不被逻辑蕴含。`GO_TO_STEP2_PROTOCOL_CONSTRUCTION` 不等于 `GO_TO_STEP2_EXECUTION`；后者仍需 Step 1.5。

通用 pipeline 决策按从上到下的优先级匹配；该表对 C0-A–D 互斥且穷尽：

| 条件 | `GENERAL_PIPELINE_DECISION` |
|---|---|
| C0-A–D 任一维为 `UNIDENTIFIABLE` | `MEASUREMENT_BLOCKED` |
| C0-A = `FAIL` | `STOP_AND_REDEFINE_PHENOTYPE` |
| C0-B = `BELOW_FROZEN_GATE` | `STOP_OR_CHANGE_ESTIMAND` |
| C0-B = `INCONCLUSIVE` | `PHENOMENON_EVIDENCE_PENDING`；valid finite burden bounds 跨门，不得写成 measurement failure 或现象不存在 |
| C0-B = `SUPPORTED` 且 C0-C = `ABSENT` | `PHENOMENON_SUPPORTED_BUT_CAUSAL_PIPELINE_BLOCKED` |
| C0-B = `SUPPORTED` 且 C0-C = `INCONCLUSIVE` | `INTERFACE_EVIDENCE_PENDING`；valid finite same-event interface bounds 跨门 |
| C0-B = `SUPPORTED`、C0-C = `PRESENT`、C0-D = `INCONCLUSIVE` | `STRUCTURAL_SCOPE_INCONCLUSIVE_STEP2_PROTOCOL_ONLY`；可构造 case-bound protocol，但不得形成 broad 或已确定 narrow 的结构范围主张 |
| C0-B = `SUPPORTED`、C0-C = `PRESENT`、C0-D = `CONCENTRATED` | `BROAD_SCOPE_REJECTED_NARROW_HYPOTHESIS_ONLY`；不得输出 narrow supported，当前 82-task frame 不得进入 Step 1.5 |
| C0-A/B/C/D = `PASS/SUPPORTED/PRESENT/SUPPORTED` | `GO_TO_STEP2_PROTOCOL_CONSTRUCTION` |

Environment title/project 决策再与 C0-E 合取；同样按从上到下匹配一次：

| 条件 | `ENVIRONMENT_TRACK_DECISION` |
|---|---|
| `GENERAL_PIPELINE_DECISION` 为 `MEASUREMENT_BLOCKED`、`STOP_AND_REDEFINE_PHENOTYPE`、`STOP_OR_CHANGE_ESTIMAND` 或 `PHENOMENON_SUPPORTED_BUT_CAUSAL_PIPELINE_BLOCKED` | `ENVIRONMENT_CAUSAL_PROJECT_BLOCKED`；C0-E 不能救活被 C0-A–D 终止的因果项目 |
| general decision 未终止项目，且 C0-E = `BELOW_FROZEN_GATE` | `FORCED_RENAME_TO_EVIDENCE_UPDATE_TO_ACTION_CONSISTENCY`；禁止 Environment-Falsifiable 主标题 |
| general decision 未终止项目，且 C0-E = `INCONCLUSIVE` | `ENVIRONMENT_TITLE_BLOCKED_PENDING_EVIDENCE`；不得把不确定性写成环境支持 |
| general decision 未终止项目，且 C0-E = `UNIDENTIFIABLE` | `ENVIRONMENT_TITLE_BLOCKED_BY_MEASUREMENT`；先修复 source/bound/provenance |
| C0-E = `SUPPORTED`，但 `GENERAL_PIPELINE_DECISION = PHENOMENON_EVIDENCE_PENDING` | `ENVIRONMENT_PROJECT_PENDING_PHENOMENON_EVIDENCE` |
| C0-E = `SUPPORTED`，但 `GENERAL_PIPELINE_DECISION = INTERFACE_EVIDENCE_PENDING` | `ENVIRONMENT_PROJECT_PENDING_INTERFACE_EVIDENCE` |
| C0-E = `SUPPORTED`，但 `GENERAL_PIPELINE_DECISION = STRUCTURAL_SCOPE_INCONCLUSIVE_STEP2_PROTOCOL_ONLY` | `ENVIRONMENT_STRUCTURAL_SCOPE_BLOCKED_PENDING_EVIDENCE`；不得把可翻转 assignment 写成已知 narrow scope |
| general decision 未终止项目、C0-E = `SUPPORTED`，但 `PURE_WORLD_STRUCTURE = UNIDENTIFIABLE` | `ENVIRONMENT_TITLE_BLOCKED_BY_MEASUREMENT` |
| general decision 未终止项目、C0-E = `SUPPORTED`，但 `PURE_WORLD_STRUCTURE = INCONCLUSIVE` | `ENVIRONMENT_STRUCTURAL_SCOPE_BLOCKED_PENDING_EVIDENCE` |
| `GENERAL_PIPELINE_DECISION = GO_TO_STEP2_PROTOCOL_CONSTRUCTION`、C0-E = `SUPPORTED`、`PURE_WORLD_STRUCTURE = SUPPORTED` | `RETAIN_BROAD_ENVIRONMENT_TITLE` |
| general decision 未终止项目、C0-E = `SUPPORTED`，且 general decision 为 `BROAD_SCOPE_REJECTED_NARROW_HYPOTHESIS_ONLY` 或 `PURE_WORLD_STRUCTURE = CONCENTRATED` | `BROAD_ENVIRONMENT_SCOPE_REJECTED_NARROW_HYPOTHESIS_ONLY`；不得输出 narrow environment scope supported |

这里“general decision 未终止项目”排除首行列出的四个 terminal decisions，包含三个 evidence-pending/design-only decisions、`BROAD_SCOPE_REJECTED_NARROW_HYPOTHESIS_ONLY` 与 `GO_TO_STEP2_PROTOCOL_CONSTRUCTION`。但 **当前 82-task frame 只有 `GO_TO_STEP2_PROTOCOL_CONSTRUCTION` 分支有资格继续接受 Step 1.5 审核**。任何 `*_PENDING` 或 `*_NARROW_HYPOTHESIS_ONLY` 都不得在同一 frame 原地执行。未来若研究 narrow hypothesis，必须先冻结新的独立 sampling frame、阈值、measurement stack 与 preregistration，再从 Step 1 重新裁决；在此之前不能称 narrow scope supported。`PURE_WORLD_STRUCTURE` 在 C0-E 非 `SUPPORTED` 时固定为 `NOT_APPLICABLE`；C0-E 为 `SUPPORTED` 时必须是四个可裁决值之一。上述两个表都按优先级匹配一次，并覆盖所有合法输入状态。因此五维原题的 broad-title 放行条件是：

```text
C0-A/B/C/D/E
= PASS / SUPPORTED / PRESENT / SUPPORTED / SUPPORTED
and PURE_WORLD_STRUCTURE = SUPPORTED
```

grounding、persistent-state use 与 planning 只要仍 observationally compatible，就不改变 C0-B；它们进入 Step 2 竞争实验。

五个 dimensions 的解析规则冻结为：

- **C0-A**：generator audit 与 primary label reliability 全部通过为 `PASS`；在事件数量充足时经过一次允许的修订仍低于数值门为 `FAIL`；因阳性过少、truth/provenance 缺失或 bounds 无法计算为 `UNIDENTIFIABLE`。
- **C0-B**：strict lower 同时满足 ≥8 positive task ids 与 ≥1.0 task-equivalent 为 `SUPPORTED`；任一 **global worst-case upper** 仍低于对应阈值为 `BELOW_FROZEN_GATE`；valid finite bounds 跨门为 `INCONCLUSIVE`；bound/provenance/certificate 无效才为 `UNIDENTIFIABLE`。detected-roster upper 永不触发 NO-GO。
- **C0-C**：至少八个 distinct positive task ids 各有一个与 confirmed positive 同一 `event_key`/decision boundary 的合格 candidate interface 为 `PRESENT`；global worst-case same-event upper 仍少于八个为 `ABSENT`；valid finite lower/global upper 跨门为 `INCONCLUSIVE`；bound/provenance/certificate 无效才为 `UNIDENTIFIABLE`。detected-roster upper 永不触发 `ABSENT`。
- **C0-D**：按第 4 节 joint feasible completion set `Z_D` 裁决；所有 completions 通过为 `SUPPORTED`，所有 completions 失败为 `CONCENTRATED`，同时存在 pass/fail completions 为 `INCONCLUSIVE`，mapping/exposure/finite non-empty `Z_D` 无法冻结为 `UNIDENTIFIABLE`。
- **C0-E**：只按第 6 节 pure-world 联合 bounds 与四值优先级裁决；通用 burden、mixed-world 事件或 source 排序不能替代。

### 8.1 机械穷举自检

2026-07-28 使用仅编码上述 first-match 规则的临时 Python 枚举器完成 outcome-blind 自检，未读取任何 trajectory outcome：

```text
source measurement/classification:
34 constructed cases -> exactly one result per case

GENERAL_PIPELINE_DECISION:
3 C0-A x 4 C0-B x 4 C0-C x 4 C0-D
= 192 combinations -> exactly one decision per combination

decision counts:
MEASUREMENT_BLOCKED = 138
STOP_AND_REDEFINE_PHENOTYPE = 27
STOP_OR_CHANGE_ESTIMAND = 9
PHENOMENON_EVIDENCE_PENDING = 9
PHENOMENON_SUPPORTED_BUT_CAUSAL_PIPELINE_BLOCKED = 3
INTERFACE_EVIDENCE_PENDING = 3
STRUCTURAL_SCOPE_INCONCLUSIVE_STEP2_PROTOCOL_ONLY = 1
BROAD_SCOPE_REJECTED_NARROW_HYPOTHESIS_ONLY = 1
GO_TO_STEP2_PROTOCOL_CONSTRUCTION = 1

ENVIRONMENT_TRACK_DECISION:
63 admissible
(general decision, C0-E, PURE_WORLD_STRUCTURE)
combinations -> exactly one decision per combination

decision counts:
ENVIRONMENT_CAUSAL_PROJECT_BLOCKED = 28
FORCED_RENAME_TO_EVIDENCE_UPDATE_TO_ACTION_CONSISTENCY = 5
ENVIRONMENT_TITLE_BLOCKED_PENDING_EVIDENCE = 5
ENVIRONMENT_TITLE_BLOCKED_BY_MEASUREMENT = 7
ENVIRONMENT_PROJECT_PENDING_PHENOMENON_EVIDENCE = 4
ENVIRONMENT_PROJECT_PENDING_INTERFACE_EVIDENCE = 4
ENVIRONMENT_STRUCTURAL_SCOPE_BLOCKED_PENDING_EVIDENCE = 6
BROAD_ENVIRONMENT_SCOPE_REJECTED_NARROW_HYPOTHESIS_ONLY = 3
RETAIN_BROAD_ENVIRONMENT_TITLE = 1

C0-E finite-bound grid:
2,475 valid lower/upper tuples -> exactly one of
SUPPORTED / BELOW_FROZEN_GATE / INCONCLUSIVE

invalid-bound sentinel:
exactly UNIDENTIFIABLE

counterexample suite:
14/14 PASS, including
- valid finite B/C straddle -> INCONCLUSIVE
- invalid bound/provenance -> UNIDENTIFIABLE
- detected upper below gate but global upper crosses -> not NO-GO
- I_U_global > P_U_global -> rejected
- marginal WORLD/B/interface splicing -> rejected
- empty obligation set -> lower 0, upper 1, certificate 0
- pass/fail structural completions -> INCONCLUSIVE
- missing config/ordinal/mechanical proof -> certificate 0

result: PASS
```

该自检只证明派生函数在声明域内 single-valued 且 total；不证明 measurement validity、阈值合理性或任何 confirmatory result。detected-roster upper 未作为 NO-GO 分支输入。

### `GO TO STEP 2 PROTOCOL CONSTRUCTION`

若要在原 broad Environment-Falsifiable GUI 题目下进入 Step 2 protocol construction，必须同时满足：

1. `known_positive_task_ids >= 8`；
2. unit-incidence lower/upper bound 已报告，但不伪装成独立于第 1 项的第二个证据门；
3. strict lower `holdout_terminal_associated_correctness_deficit >= 1.0` task-equivalent；
4. 第 4 节 structural dispersion/concentration gate 对 `Z_D` 全部合法 completions 都通过；
5. 至少八个不同 task ids 以同一 confirmed positive `event_key`/decision boundary 通过 replay-interface candidate gate；
6. 关键标注可靠性、prefix-only candidate audit 与 missingness bounds 通过 Stage 0F 主协议；
7. `UACF-D` 与 `EACF-P` 分开，且阳性不由 evaluator-invalid、纯 actuation、API error、budget termination 或 environment failure 充分解释。
8. C0-E 的三个 pure-world strict lower bounds 分别达到 `8 task ids / 1.0 task-equivalent / 8 candidate-interface task ids`；
9. pure-world 子集重算的 structural dispersion/concentration gate 对 `Z_env_structure` 全部合法 completions 都通过。

若只有第 1–7 项通过而 C0-E 任一 global worst-case upper 已低于门槛，只能按表强制改题；若 C0-E 为 `INCONCLUSIVE/UNIDENTIFIABLE`，Environment-Falsifiable title 被阻断。第 8 项通过但第 9 项为确定的 `CONCENTRATED` 时输出 `BROAD_ENVIRONMENT_SCOPE_REJECTED_NARROW_HYPOTHESIS_ONLY`，当前 frame 不进入 Step 1.5；第 9 项为 `INCONCLUSIVE/UNIDENTIFIABLE` 时阻断 scope claim。

### Dimension-specific `NO-GO / NOT-READY`

只有问题可识别时，满足任一项：

- global worst-case `U_B_tasks_global < 8`；
- global worst-case `U_B_deficit_global < 1.0` task-equivalent；
- global worst-case same-event `U_C_interface_tasks_global < 8` 时，`C0-C = ABSENT`，只阻断因果 pipeline，不否定已经支持的 C0-B；
- 对 C0-D 的所有合法 completions 都违反至少一个预冻结 dispersion/concentration gate 时，`C0-D = CONCENTRATED`，派生结果只能是 `BROAD_SCOPE_REJECTED_NARROW_HYPOTHESIS_ONLY`；未来独立 frame 重过 Step 1 前不得声称 narrow supported；若 completions 可翻转则必须为 `INCONCLUSIVE`；
- C0-E 任一 pure-world global worst-case upper 仍低于对应门槛时，环境题强制改名，但不推翻已经由 C0-A–D 支持的通用 UACF-D 现象；
- C0-E 已支持且 pure-world structural recomputation 对所有合法 completions 都失败时，只能输出 `BROAD_ENVIRONMENT_SCOPE_REJECTED_NARROW_HYPOTHESIS_ONLY`；若 completions 可翻转则阻断 scope claim；
- 有直接日志证据表明全部候选都是 evaluator-invalid、纯 actuation、API/environment failure 时，C0-B 可判低于 gate；grounding、persistent-state use 与 planning 仍 observationally compatible 时必须保留到 Step 2，不得在 Step 1 宣称某一项充分解释。

### `UNIDENTIFIABLE`

满足任一项：

- C0-B/C 的 valid finite strict lower 与 global worst-case upper 跨门时必须记为 `INCONCLUSIVE`，不得记为 `UNIDENTIFIABLE`；C0-D 的 `Z_D` 同时存在 pass/fail completions 时必须记为 `INCONCLUSIVE`；C0-E 的有效 finite bounds 跨阈值时必须按第 6.4 节记为 `INCONCLUSIVE`；
- obligation missing/empty 已被第 3.1 节 fail-closed 为 `lower=0, upper=1`，本身不自动成为 `UNIDENTIFIABLE`；只有连该 missingness disposition/provenance 都无法验证，或 final predicate / `UACF-D` measurement 无法形成有效 finite bound 时才为 `UNIDENTIFIABLE`；
- structural mapping 无法在 outcome-blind 条件下冻结；
- candidate generation 存在未来信息泄漏；
- associated loss 上界因 `L_max` 或 missingness 未冻结而无界；
- C0-E 的 finite holdout、strict-negative rule、source evidence provenance 或 joint interface bound 无法形成有限可审计边界；
- 想用 Step 1 估计 repair effect 或 intervention net benefit。

## 9. 解释边界

只有通用 pipeline gate 通过后，安全的通用结论才是：

> 冻结的已发布轨迹中，`UACF-D` 提供了足够数量、观察性 associated correctness deficit 和 candidate interface inventory，值得构造竞争性根因实验协议。

只有 C0-E 另行判为 `SUPPORTED` 后，才可增加“pure-world 子集达到环境题 protocol threshold”；只有 pure-world structural recomputation 也为 `SUPPORTED` 时，才可不限定结构域地保留 broad GUI environment title。当前没有任何 confirmatory C0-E 结果，本文阈值本身不能作为通过证据。

它不能被改写为：

```text
Memory 是根因
行动契约能避免这些损失
真实 GUI 工作流中发生率相同
```
