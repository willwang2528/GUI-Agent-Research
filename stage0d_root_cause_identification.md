# Stage 0D：Step 2 根因识别与课题边界

> **SUPERSEDED STATUS NOTICE（2026-07-22）**：本文件的 Step 2 设计仍可参考，但早期 `Case-level Qualified GO / PARTIAL` 状态已被 Stage 0F 取代。当前 Step 1 仅为 **FRAME-READY / PILOT-ELIGIBLE**，尚未获得 behavioral-burden GO，Step 2 仍关闭。

> 当前裁决：**两个公开案例描述只完成“现象存在”的案例级证明；自然发生率、失败负担与长程依赖尚未证明，所以 Step 1 仍为 PARTIAL。Step 2 不得开始执行，Memory 根因尚未成立。**
>
> 目前最稳健、可观察的研究对象是 **Update-to-Action Consistency Failure（UACF）**：任务相关更新已经送达；在预注册处理窗口内，后续外部动作、artifact 或 commit 仍与更新后的要求不一致。窗口必须事先定义为更新后的固定决策步数、固定时间或首次 commit 之前；`delivered / seen / correctly interpreted` 分别报告，不能把“理论上可获取”与“已经看到”合并。
>
> “行动契约式 Memory”只是候选机制。若实验显示 Agent 在 action-time 能准确报告或使用新事实，但没有修复依赖旧事实的计划和外部产物，课题必须改名为 Dynamic Intent Reconciliation 或 Plan–Artifact Repair。

## 1. 我们的科研主题到底是什么

不是：

```text
给 GUI Agent 增加一个 Memory 模块
```

而是：

```text
在长程 GUI 任务中，环境事实或用户意图发生变化
→ 早期证据和基于它产生的 UI / 计划 / 计算可能失效
→ Agent 应当识别哪些既有 decision、artifact 和 pending obligation 因更新而失效
→ 撤销或补偿旧动作、重算下游结果
→ 在提交前用当前环境证据重新验证
```

研究问题是：这条链为什么会断，断在哪一层，哪一种可部署干预能在相同信息和成本下修复。

只有以下条件同时成立，才能把“持久状态表示是独立因果瓶颈”作为结论；这仍不等于它是唯一自然根因：

1. 新事实已经被观察并正确理解；
2. 自然失败决策点存在跨步持久、可独立读写的 state store，且其内容发生遗漏、过期、错配或覆盖失败；
3. 干预一次写入并跨步读取该 store，而不是在每一步重复注入 prompt；
4. 冻结 grounding、planning、execution、verification、信息、顺序、重复、salience 与预算；
5. 只纠正持久状态就能稳定改变错误行动，并通过预注册的行为 probe 呈现与状态纠正一致的机制证据；
6. 收益不能由额外计划提示、答案泄漏或更高显著性解释。

若只有 prompt 重写或结构化输入有效，最多支持 Context / State Representation，不足以支持 Memory。

## 2. 七个步骤与课题的关系

| 步骤 | 要排除的错误科研结论 | 对课题的作用 |
|---|---|---|
| Step 1：证明现象 | “长任务成功率低，所以一定是 Memory” | 确认公开案例中是否存在可观察的 update-to-action inconsistency；不估计一般发生率 |
| Step 2：识别根因 | “看到旧动作，所以内部一定忘了” | 区分 evidence、grounding、state update、replanning、verification、execution |
| Step 3：挑战现有方法 | “弱 baseline 失败，所以 SOTA 也解决不了” | 在冻结协议上检验被测强组合系统是否仍有 residual；不代表所有现有方法 |
| Step 4：方法验证 | “多个模块一起加强后的提升来自 Memory” | 训练或实现可部署机制，再分别检验充分修复、composite 条件必要性和交互 |
| Step 5：环境证伪 | “让模型再想一次就等于核验环境” | 比较新环境证据与同一旧证据上的 reflection |
| Step 6：等预算审计 | “更多 token、调用和时间带来提升” | 排除资源、覆盖率、延迟、人工接管和特权真值泄漏 |
| Step 7：Go / No-Go | “结果模糊也继续包装原题” | 预先规定保留 Memory、改名或终止课题的条件 |

七步是**课题淘汰漏斗**，用于判断原 Memory 主题是否存活，而不是保证它成立：

```text
Step 1：公开案例中是否存在 UACF
→ Step 2：在 reference policy 与预定义干预下，E / G / R / P / A / V 是否可区分
→ Step 3：冻结协议后，被测强系统是否仍有 residual
→ 若持久状态 R 获得独立因果支持：Step 4–7 验证 Memory 机制
→ 若 P / A / V 胜出：Step 4–7 继续，但课题必须改名
```

所以 Step 1–3 回答的是“Memory 题是否值得继续”；只有它存活后，Step 4–7 才能回答候选 Memory 机制为何可能解决。若改名，后续步骤服务于改名后的研究问题。

## 3. Step 2 的第一性原理定义

### 3.1 最小失败单元

一个可识别的失败必须同时绑定：

- 一个 commit decision、动作序列或 required-action omission；
- 一组决定结果是否正确的必要谓词或 obligations；
- 一个改变其 truth、applicability 或 obligation set 的 addition / revision / retraction 事件；
- 一条从更新到行动的传播链；
- 一个由最终环境状态独立评分的语义结果。

可竞争因果结构不能预设所有 Agent 都具有独立 Memory：

```text
U：环境变化或用户意图更新
E_delivery / E_monitoring：外部送达或 Agent 主动 probe
O：Agent 实际得到的 observation
G：observation 的 grounding 结果
R：可选的跨步持久状态表示
P：依赖传播、剩余义务和 replanning
S：Agent 选择的 semantic action
A：semantic action 到 GUI 的物理执行
X：外部 GUI / artifact 状态
V：验证策略；其 observation 可进入下一轮
Y：由最终环境真值与 X 独立决定的语义结果

U → E_delivery → O
environment / X + E_monitoring → O
O → G → P
G → optional R → P
X → P
P → S → A → X_next
G / optional R / P → V_select → E_monitoring_next
environment / X_next + E_monitoring_next → O_next → loop or commit
final environment + X_final → Y
```

只有 `R` 跨步持久、可独立读写并能通过标准接口替换时，才有资格叫 Memory。planner 也可能直接读取 `O / G / transcript`，不存在独立 `R`。

只看到 `Y` 错误或 `X` 中仍有旧值，不能反推出 `R` 错误。旧 GUI 也可能是 `P` 没有生成修复义务、`A` 没有完成执行，或 `V` 验证了错误对象。

### 3.2 当前最强竞争理论

反方提出的更简约解释是 **Obligation-Propagation / Plan–Artifact Repair Failure**：

```text
Agent 知道新事实
→ 但没有识别哪些既有义务和外部 artifact 已失效
→ 没有撤销旧 UI、补偿旧动作或重算下游结果
→ 最终检查继续读取旧 artifact
```

它不需要假设一个不可见的“内部 Memory 已经忘记”变量，且能直接解释当前最强案例：

- Randyland：论文 case study 报告 Agent 明确认可新起点，但没有修改 `From` 字段和重算路线；原始完整模型轨迹未被本轮独立审计；
- OSWorld 2.0 Task 035：官方案例报告部分 late updates 未被一致整合，最终产物和检查依据不完整；当前证据没有闭合每个预算或供应商事实从“看见”到“遗忘”的链；
- OSWorld 2.0 Task 024：成功案例把资金不足编译为暂停、询问和再次验证；
- Task 008：部分事实可跨数百步保持，反驳“长程事实普遍必然丢失”；
- Task 052：移动弹窗是 observation–action latency，不能归入语义 Memory。

两个案例必须分开解释：Randyland 明确报告了“承认更新却没有修改外部状态”；Task 035 只报告了部分动态更新未被一致整合，缺失 approval 也可能从未被读取。它们共同支持 UACF 的现象级证据，但不共同支持“已经知道后忘记”。

## 4. InterruptBench 代码级审计

### 4.1 已核验的公开数据

本地官方仓库版本：`17da111e4858b93c0cab1d88f85e1735fbd1d423`。

- 原始 WebArena-Lite 文件含 165 个 task configs；
- 五个公开 transformed 目录各含 165 个任务配置；
- `interrupt_spec_1update_opus_20/40/60/80.json` 均覆盖相同的 165 个 task id；
- 每份 spec 的 update mode 都是 `append`，`extra_steps` 都是 0；
- `1update` Task 3 的初始 intent 缺少起点，60% 更新为 `Starting from Randyland`；它只能作为 addition-integration 的自然案例锚点，不能测试 supersession；
- `2modification` Task 3 才是当前诊断任务：初始路线为 Phipps Conservatory → University of Pittsburgh，60% 时追加两项显式修订，分别改为 Randyland → Carnegie Mellon University；
- `2modification` 只有在更新前已经使用旧起终点生成路线，并且该旧路线在 raw update 后、arm 注入前仍存在时，才进入分析总体。

本地一致性检查进一步确认：

- 六份 raw update 文件均为 165 条、task id 完整覆盖 0–164、没有空 update；
- `raw/1update.json` 与 `interrupt_spec_1update_06.json` 的 165 个 update 逐项一致，没有 mismatch；
- `raw/2modification.json` 与 `interrupt_spec_2modification_06.json` 同样覆盖 165 个 task，Task 3 的 initial instruction、两项 update、`append` mode、60% 位置和 `extra_steps=0` 在 raw/spec/transformed config 中一致；
- 60% 插入点由 `floor(0.6 × baseline action count)` 得到；
- 论文中的 `1update` Randyland trajectory 未公开；v0.3 的直接执行 blocker 则是本地尚未重新生成 `baseline_trajectory_3_modification`，因此没有 baseline action count、实际 K 或旧路线 artifact 证据。

Task 3 `2modification` 最小资产校验值：

| 资产 | SHA-256 |
|---|---|
| `raw/2modification.json` | `bc715fdb975ffd3fc6165e832eae55add02ed5154ec4e71f62c6cb0e3b9d24e5` |
| `interrupt_spec_2modification_06.json` | `a1620a854134bf2a9154df2df8836c5d7c66de338a5c958e88a7f12a4fd302b2` |
| base task `3.json` | `0c5a71fac6cfcbbb15bae860d88b80b64e74a81aaa6778477d804ce0ee9c40a7` |
| transformed `2modification/3.json` | `d9b58d33e6ffbbf845f90ce78c0dbad2d3c1dabc72692895b9c432e0a6fe99e7` |

### 4.2 replay 不是持续 Agent Memory 的 checkpoint

代码执行链如下：

1. `_save_actions_only` 只保存动作序列、原始动作字段和任务元数据，不保存 hidden state、KV cache 或独立 Memory 对象；
2. interrupt run 调用 `agent.reset` 和 `env.reset`；
3. runner 从初始环境重新执行前 K 个动作；
4. replay 过程中重建 `action_history`；
5. 到 K 后把更新追加到 intent，再调用模型继续执行。

对应代码：

- `Eval/run.py:182–221`：保存和加载 actions-only replay；
- `Eval/run.py:944–978`：Agent、环境和 action history 初始化；
- `Eval/run.py:1000–1045`：回放动作并重建历史；
- `Eval/run.py:1060–1079`：把更新追加或替换进 intent；
- `Eval/agent/agent.py:216–217`：PromptAgent 的 reset 不恢复任何持久内部状态；
- `Eval/agent/prompts/prompt_constructor.py:615–653`：WebRL 从 action history 重建对话。

对 `webrl_id`，action history 使用动作中的 `raw_prediction`，因此过去的推理文本可能被重新放入 prompt；但这仍是文本历史重建，不是原运行内部状态的忠实 continuation。其他 action set 主要保存动作描述，信息边界还会不同。

所以 InterruptBench 可以支持：

> 在 action-prefix replay 实际到达的环境状态和重建历史上，模型能否整合中途追加的任务更新。

代码会在 prefix 提前 STOP 或 terminated 时报告错误，但成功执行 K 个动作并不证明其 hidden site state、DOM timing 或浏览器状态与 baseline 的 K 时刻完全等价。

它不能单独支持：

> 持续运行的 Agent 内部 Memory 因长 horizon 发生了遗忘或污染。

这也是为什么 interrupted / no-interruption 的结果差不能直接解释成 Memory 效应。

## 5. 最小可区分实验

### 5.1 v0.3：单任务 bundled-prompt 诊断

InterruptBench 的 action-prefix replay 不是严格 checkpoint restore。实验必须从同一份通过等价性检查的 prefix reconstruction 分叉；arm 分配发生在旧路线仍存在的验证之后。每个 arm 使用独立 Agent、浏览器和 session，不复用跨 arm cache 或 store，并冻结模型、工具、token、步骤、时间预算和 seed-to-arm 映射。

当前七个 arm 是：

| Arm | 新增输入 | 只能识别的效应 |
|---|---|---|
| `B` | 无 | 原 Prompt 行为 |
| `B_P0` | 四步 active-control Prompt | 通用四步 Prompt 注入的 bundled effect |
| `U_REPEAT_P0` | 带标签的 initial/update recap + active control | 最近位置上的 labeled recap、聚合与 salience bundled effect |
| `F_P0` | 外部生成的 canonical row-DSL state + active control | 外部 canonicalization、显式 current/superseded、source/provenance 与序列化的 bundled context effect |
| `S_P0` | 与 `F` 等 atom 的 JSON state + active control | row-DSL 与 JSON serialization effect |
| `F_P1` | `F` + task-value-free update-repair Prompt | update/artifact awareness、dependency、undo/recompute/verify 的 bundled Prompt effect |
| `S_P1` | `S` + 同一 repair Prompt | serialization 与 repair-Prompt bundle 的交互 |

因此，预注册对比的含义被严格限制为：

```text
B_P0 - B：generic four-step active-control prompt injection
U_REPEAT_P0 - B_P0：labeled history recap and salience
F_P0 - U_REPEAT_P0：externally supplied canonical-state context
S_P0 - F_P0：row-DSL versus JSON serialization
F_P1 - F_P0、S_P1 - S_P0：task-value-free update-repair prompt bundle
```

这些对比不能被改写成：纯 history repetition、纯 representation structure、Agent 内部 planner、自然失败根因或 Memory 效应。特别是 `F / S` 都是 raw update 后一次性注入的 user-role Prompt；即使有效，也只支持 Context scaffold。

进入 arm 前还必须同时满足：

1. 旧起点和旧终点已被用于路线查询；
2. 已生成依赖旧值的 route artifact；
3. raw update 注入后、arm 注入前，旧 route artifact 仍存在；
4. 冻结 From/To 字段、route DOM hash、mode、计算动作索引、artifact id 与两条 dependency edge；
5. replay 的 URL、accessibility tree、任务字段和 prefix action hash 等价。

记录三个机制一致性 proxy：

1. elicited state report：能否报告 current/superseded 事实；
2. impact-set accuracy：能否识别受影响字段、路线和最终回答；
3. repair completion：能否修改旧 GUI、重算并验证。

这些都是 intervention 后变量，不得筛选或调整 primary analysis，也不能写成正式 mediation。

最窄判别规则：

| 结果 | 允许的结论 |
|---|---|
| `F_P0 - U_REPEAT_P0` 达到预注册最小效应 | 当前冻结 task-prefix 上出现 externally supplied canonical-state context 的候选信号 |
| `S_P0 - F_P0` 达到预注册最小效应 | row-DSL 与 JSON serialization 不同；不能称为结构化 Memory |
| `F_P1 - F_P0` 或 `S_P1 - S_P0` 达到预注册最小效应 | task-value-free update-repair Prompt bundle 改变行为；不能称为 Planner 根因 |
| `(S_P1 - S_P0) - (F_P1 - F_P0)` 非零 | serialization 与 repair Prompt 存在候选交互；不能由“只有一个 arm 成功”替代该对比 |
| 任何 arm 有效 | 仍不能证明自然失败由对应内部模块引起 |

所有候选信号都必须报告 paired effect、exact interval 和全部 discordant pairs。n=10 不允许确认性 support、power、equivalence 或跨任务主张。

该 pilot 在七步中只有一个作用：作为第 2 步的 identifiability calibration / instrument unit test，筛查“显式当前状态供给”和“显式 repair Prompt bundle”是否产生可区分结果。它不能完成第 2 步，更不能直接进入 Memory 方法验证。

### 5.2 后续独立协议：functional oracle boundary ladder

v0.3 只把 `E_STAR / G_STAR / R_STAR / P_GENERIC / P_ORACLE / V_SELECT_STAR / A_STAR` 登记为 **catalog-only**；它们不是当前七 arm pilot 的实验臂，当前 outcome、estimand、readiness 和 decision rules 均不得引用这些 catalog 项。

若 v0.3 显示某些 bundled Prompt treatment 值得继续，完成 Step 2 需要另建独立的 boundary-isolated functional-oracle 协议。下面是该未来协议的候选 arms；`B0 / F_INFO_BOUNDED / O_TRUTH` 是新协议需要额外定义的 reference/composite/privileged ceiling，并不属于 v0.3 catalog：

| Future arm | 替换边界 | 必须控制 |
|---|---|---|
| `B0` | 原 reference policy | 无 |
| `E_STAR` | 固定预注册 probe，返回原始 GUI observation | 配等动作、等延迟 decoy；probe selection 不用 hidden truth |
| `G_STAR` | 同一 raw observation 下，用 observation-bounded transcription 替换 grounder output | 下游只接收一种 G output，不增加第二信息通道 |
| `R_STAR` | 固定同一 G output，用 oracle updater 替换持久 state updater | 只处理该 G output；不从最终环境真值补事实 |
| `P_GENERIC` | 加入 diagnosis-matched、task-value-free repair policy | 不提供 task-specific 当前值、依赖图或答案 |
| `P_ORACLE` | 用 task-specific dependency / obligation plan 替换 planner output | 单列为 planning ceiling，不包装成可部署提示 |
| `V_SELECT_STAR` | 固定规则选择一个验证 probe | probe 结果仍走原 O / G / R / P pipeline |
| `A_STAR` | 保持 Agent 选择的字段和值，只纠正 click / type / coordinate realization | 不纠正错误语义动作、字段或值 |
| `F_INFO_BOUNDED` | 组合所有 deployment-information-bounded oracle | 不使用 final evaluator truth；逐 arm 记录新增信息与行为约束 |
| `O_TRUTH` | 提供 privileged final-state truth | 只估计不可部署上限，不参与根因归因 |

如果 `G / R / P` 最终都只是向同一 prompt 追加文本，它们是 prompt interventions，不是模块级手术。只有通过标准模块接口替换原输出，才可以声称 boundary isolation。`F_INFO_BOUNDED` 可以依赖人工 annotation 与 oracle 计算，因此只是诊断 ceiling，不代表可部署系统。

`V_SELECT_STAR` 会通过新 observation 改变后续多个变量，因此它是合法 policy intervention，不是“只改变 V 后其余保持不变”。`F_INFO_BOUNDED minus X` 也只能检验 **X 在该 oracle composite 内的条件必要性**，不能证明 X 是自然架构的必要模块或原始失败的唯一根因。

单一 arm 修复只能证明一条充分修复路径。预注册 multiple-sufficient-causes 判定：

| 结果 | 判定 |
|---|---|
| `R_STAR` 单独修复，且 `F_INFO_BOUNDED minus R` 明显下降 | R 充分，且在该 full composite 中条件必要 |
| `R_STAR` 单独修复，但 `F_INFO_BOUNDED minus R` 不下降 | R 充分但非必要，存在替代路径 |
| `R_STAR`、`P_ORACLE` 分别单独修复 | `R OR P`：多条替代充分路径 |
| 单独均不修复，`R_STAR + P_GENERIC` 修复 | `R AND P`：联合瓶颈 |
| `R_STAR` 不修复，但 `F_INFO_BOUNDED minus R` 下降 | R 条件必要但非充分 |
| 只有 `F_INFO_BOUNDED` 修复，交互未穷尽 | unresolved composite failure |

多个单 arm 都有效时，不得选择效应最大的一个称为“真正根因”。

## 6. Step 2 与 Step 3 为什么必须串行

Step 2 先在固定 reference policy 上做 identifiability calibration：检验预定义的 `E / G / R / P / V / A` intervention 是否让结果可区分、是否无答案泄漏，以及 semantic evaluator 是否正确。它不是普遍根因证明。

随后冻结：

```text
task generator
task split
intervention
placebo
evaluator
统计阈值
```

Step 3 再冻结被测强组合系统与预算，在不修改 Step 2 任务、标签、oracle 和统计规则的条件下原样复跑。原因是机制相对于 policy 而言：弱 Agent 的 `R` 失败可能被强模型直接解决；边看强系统结果边改 benchmark 会产生 self-serving benchmark。

所以：

- Step 2 只能证明“在该 reference policy 与所定义 intervention 下，结果具有可区分性”；
- Step 3 只能说明被测强组合系统是否仍有 residual，不能代表所有现有方法。

Step 2 的 oracle boundary intervention 用于诊断；Step 4 必须是 learned / deployable mechanism 及其 ablation，不能把 oracle 诊断重复包装成新方法。

## 7. 预注册判定门槛

### 7.1 后续 boundary protocol 的单案例筛选 gate

以下门槛不属于 v0.3；它只能在另行冻结的 functional-oracle 协议中使用。同一 prefix reconstruction 使用五个共同 paired seeds：

- `B0` 至少失败 4/5；
- 目标单边界干预至少成功 4/5；
- 信息、动作和延迟匹配的 control 不得产生同等修复；
- 除目标边界外，模型、输入证据、token、工具、步骤、时间和随机设置保持一致。

该未来门槛只用于排除不稳定 intervention 和筛选候选，不能支持正式根因标签。v0.3 当前更窄，只允许报告 `candidate_signal_on_this_frozen_task_prefix`，不允许写“充分修复路径”。

未来 boundary protocol 达到门槛后，最多写：

> X 是该案例的一条充分修复路径。

正式单案例确认至少使用 10 个共同随机种子和 exact paired test；效应区间必须超过预注册的 practical threshold。LLM seed 不作为跨任务统计的独立 family。

### 7.2 跨任务结论

独立统计单位必须是 base task family，不是同一任务的多个 update、位置或 seed；若多个 task 共用模板或网站工作流，还需按更高层 template / site 聚类。建议预注册：

- minimum practically important effect，例如 paired correctness 提升至少 20 个百分点；该阈值必须由风险效用或 pilot power simulation 事先确定；
- family-clustered 95% interval 高于 0，并报告 hierarchical / cluster-level effect；
- held-out family 的方向一致性和 catastrophic negative-transfer rate；
- 固定 update coverage、信息、token、deliberation、probe 与 latency 后仍成立。

### 7.3 何时保留 Memory 题目

本节只能由**另一个 persistent-store + cross-task protocol**执行。v0.3 的 `memory_topic_status` 固定为 `ineligible_not_tested`，不得通过编辑当前协议解锁；所需新协议必须至少具有冻结的 store API / implementation hash、真实 `R_STAR` arm 和 Memory estimand。

必须同时出现：

1. 系统必须暴露或实现独立、跨步持久、可读写的 state store，并能对其内容做一次写入、跨步读取的持久性干预；information-matched prompt / context sensitivity 不能替代该条件；
2. action-time state error rate、状态读取时点和错误定义在看结果前冻结；
3. `R_STAR` 在固定 E / G / P / V / A 接口下具有超过预注册 practical threshold 的独立增益；
4. `F_INFO_BOUNDED minus R` 用于判断 R 在 full composite 内是否条件必要；若不下降，R 仍可作为替代充分修复路径，但不能称为唯一或核心自然根因；
5. structured state 相对命题完全相同的 flat-correct state 仍有增益，才能声称 representation value；
6. elicited report、impact set 与 repair 指标只作为机制一致性证据；没有非侵入式 state store 时不写正式 mediation；
7. 效应在冻结的被测强系统、held-out task family、更新类型和多个 backbone 上保留。

真实系统允许 multiple sufficient causes，因此不要求 E / G / P / V “不能解释全部收益”。

### 7.4 何时立即改名

本节同样不允许由 Task 3 v0.3 单独触发。当前 `topic_rename_decision_allowed_from_task3_alone=false`；只有独立 persistent-store / functional-boundary 协议和跨任务证据才能触发保留或改名判定。

满足以下预注册模式就不应再把 Memory 写成根因：

- 非侵入式 store readout，或多个预注册 action-sensitive probes，在预设 equivalence margin 内均显示状态正确；elicited self-report 单独不足；
- `R_STAR` 的 cluster interval 落在预注册 equivalence margin 内；
- `P_GENERIC` 或 information-matched learned P 相对 `R_STAR` 的 paired effect difference 超过预注册最小幅度，且 cluster interval 高于 0；`P_ORACLE` 只报告 planning ceiling，不参与直接改名比较；
- 错误集中在 impact set、GUI repair 或 recomputation，P 的收益与这些指标方向一致；
- prompt structured state 有效但没有跨步持久 store：改名为 Context / State Representation，而不是 Memory。

此时课题应改为：

```text
Dynamic Intent Reconciliation
Dependency-Aware Replanning
Plan–Artifact Repair for Long-Horizon GUI Agents
```

## 8. 当前可做与不可做

当前本机没有 Docker、WebArena 服务、完整模型轨迹或冻结模型凭据，无法完成端到端因果实验。因此 Step 2 不能被标记完成。

现在可以合法完成：

- 官方代码和数据协议审计；
- 冻结并审计当前七 arm bundled-Prompt diagnostic spec；
- 从官方 task / update spec 构造 synthetic decision probe；
- 实现 normalized-trace 的 deterministic outcome decision logic，并在 synthetic fixtures 上测试；
- 继续实现 raw HTML/action trace normalizer，验证所有 arm 的信息、token、动作和 evaluator 边界；
- 冻结 synthetic decision probe、arm 信息边界和资产 manifest。

获得固定模型后才可以做 offline counterfactual decision replay；当前尚未执行。

offline replay 最多证明：

> 在重复、随机化且固定输入和模型的条件下，prompt / state-input intervention 会因果改变下一输出分布。

它不能证明：

- 原论文自然失败由 Memory 引起；
- Agent 能主动发现动态 GUI 更新；
- grounding 和真实动作执行正确；
- 长程端到端成功率提升；
- 生产环境中的自然失败率。

### 8.1 两个最小复现路径

**OSWorld 2.0 Task 035**

- 轨迹审计：官方索引确认 `website_demo/MiniMax-M3` 模型目录和 website-demo 引入提交 `458824a`；预期单任务路径为 `website_demo/MiniMax-M3/tasks/035`，仍需通过文件树或 selective download 独立确认。确认后只下载该目录，并记录完整 dataset revision、run id 和文件 checksum；
- model-only replay：还需要完整单任务 observation、prompt、working state 和冻结模型；
- full environment replay：还需要 gated task class、evaluator、assets、对应 website commit 和官方 provider image；当前 Mac 无法执行。

轨迹审计只能观察已有失败，不能得到替代 action 之后的新 observation 或最终 evaluator 结果。

Benchmark 有 108 个任务，官方 discussion 描述计划布局为每个模型目录包含 `tasks/001`–`tasks/108`；本环境没有取得 Task 035 的文件级 API 响应，因此尚未独立确认该模型目录是否无缺失运行或命名差异。`458824a` 只是引入 website-demo 的提交，不替代正式 manifest 所需的完整 dataset revision。

**InterruptBench Task 3**

- 本地已有 `2modification` 的 base task、transformed task、raw update 和 60% spec，且四个 SHA-256 与协议一致；
- 论文对应 baseline trajectory 未公开，本地也没有 `trajectories/3.json`；必须先启动 Map WebArena 和浏览器，运行 Stage A 生成旧值路线轨迹；
- Stage B 重新调用 `agent.reset()` 与 task-level `env.reset()`，再回放前 60% actions，并追加两项修订：Phipps Conservatory → Randyland、University of Pittsburgh → Carnegie Mellon University；
- arm 分配前必须证明旧路线在 raw update 后仍然存在，并保存 artifact fingerprint；否则该 run 不是 artifact-repair 诊断实例；
- Task 3 只使用 Map，完整 WebArena 所有站点不是硬前提，但 Map 服务、浏览器环境、模型 endpoint 和起始状态一致性是硬前提。

端到端实验必须额外保存 baseline action count、实际 K、prefix hash、artifact fingerprint、模型版本、prompt、seed-to-arm map、预算、完整 HTML / trace、score JSON 和 evaluator config。当前已经实现并通过 8 个 synthetic 单元测试的只是 normalized-trace decision logic；raw HTML/action trace normalizer 仍未实现，因此 deterministic primary evaluator blocker 仍未解决。当前环境同时缺少 Docker/Map 资产、baseline trajectory、冻结模型和七 arm runner，所以实验不可运行。

## 9. 第十至十一轮 Battle 裁决

第十轮，natural-failure reviewer 用八个配置反例证明 v0.2 validator 会放过错误 Task truth、交叉 supersession、Memory 越界 label、恒真 outcome 和伪造 readiness，裁决为 **FAIL**。oracle reviewer 同时确认 `2modification` 在满足旧产物 inclusion 时是真 revision 诊断，但所有 arms 仍只是 Prompt/Context intervention。

v0.3 随后做了三类修正：

1. 从官方 Task 3 资产冻结六个 semantic atoms、old/current relation、研究问题、claim ceiling、estimand metadata、outcome 与 decision rules；
2. 将处理准确改名为 active-control injection、labeled recap、externally supplied canonical-state context、row-DSL vs JSON serialization 与 update-repair Prompt bundle；
3. 拆分 update 前 eligibility 与共同的 update 后、arm 分配前旧产物 checkpoint，并要求 fresh session、跨 arm cache/store 隔离和 evidence-backed readiness。

当前 validator 通过 18 个负向 self-tests，包括错误真值、错误 relation、越界 Memory claim、恒真 outcome、伪造 budget/evaluator/blocker、同义任务泄漏、重复 JSON key 和非 counterbalanced seed-map。`--require-ready` 仍以退出码 2 拒绝执行。

第十一轮，oracle reviewer 的裁决是：

> **PASS WITH FIXES，仅针对“Step 2 前置的单任务因果 Prompt diagnostic pilot”；若把它当作行动契约或 Memory 有效性证据，则是 FAIL。**

reproduction reviewer 独立确认四个 `2modification` 资产与官方仓库一致，但 Map 环境、baseline trajectory、prefix equivalence、模型/seed、raw-trace normalizer、预算、prompt leakage audit 和七 arm runner 尚不存在。机器状态为：

```text
analysis_plan_valid = true
execution_manifest_status = pending
execution_manifest_frozen = false
causal_prompt_pilot_ready = false
cross_task_confirmation_ready = false
memory_experiment_eligible = false
```

七个未解决的 Task 3 blockers 是：

```text
map_webarena
baseline_trajectory_3_modification
prefix_inclusion_and_equivalence
frozen_model_and_seed_support
token_and_deliberation_match
deterministic_primary_evaluator
manual_prompt_leakage_audit
```

因此，截至当前七步进度：

```text
Step 1：PARTIAL；案例级 existence = Qualified GO，自然负担/发生率/长程性 = HOLD
Step 2：PENDING；v0.3 只是预备 identifiability calibration，尚未隔离 E/G/R/P/V/A
Step 3–7：不得开始宣称已验证；只能准备后续独立协议
当前更简约的竞争解释：plan–artifact repair failure
```

当前唯一安全的根因表述是：

> 两篇 2026 预印本的公开案例描述提供了 update-to-action inconsistency 的现象级证据；`2modification` 为受控 revision-artifact diagnostic 提供了可审计设计，但尚无真实 run。现有证据不能区分 update acquisition、Context / State Representation、persistent state、dependency planning、GUI repair 与 verification，也不能估计发生率。只有另一个跨任务、boundary-isolated persistent-store protocol 中的 `R_STAR` 在固定 E/G/P/V/A、信息、salience、token 和工具预算下显示独立因果效应，课题才可保留为 Memory；当前 v0.3 的任何 Prompt 结果都最多支持 Context-level candidate signal。

后续 Step 2 已拆成两个独立产物：

- [Stage 0E boundary-isolated root-cause protocol](stage0e_boundary_isolated_root_cause_protocol.md)：定义 E/G/R/P/V/A、persistent-store 资格、multiple sufficient causes 与 Memory/改名判定；
- [Stage 0E candidate task families](stage0e_candidate_task_families.md)：从官方 `2modification` 资产中筛出八个 revision–artifact workflow 候选，并逐项列出 evaluator 与 baseline blocker。

## 10. 官方来源

- [OSWorld 2.0 paper](https://arxiv.org/abs/2606.29537)
- [OSWorld 2.0 project](https://osworld-v2.xlang.ai/)
- [OSWorld 2.0 code](https://github.com/xlang-ai/OSWorld-V2)
- [InterruptBench paper](https://arxiv.org/abs/2604.00892)
- [InterruptBench code and data](https://github.com/HenryPengZou/InterruptBench)
- [SyncMind, ICML 2025](https://proceedings.mlr.press/v267/guo25l.html)
- [C-World, ACL 2026](https://aclanthology.org/2026.acl-long.2001/)
- [GUI-RobustEval / RoTS official repository, ICML 2026 Spotlight](https://github.com/AlibabaResearch/RoTS)
