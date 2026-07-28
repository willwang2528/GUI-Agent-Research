# Stage 0E：长程 GUI 状态失效的 Boundary-Isolated 根因协议

> 状态：**design draft / not executable / no Memory claim**
>
> 它承接七步中的 Step 2。Stage 0D v0.3 只校准 bundled Prompt instrument；Stage 0E 才尝试区分 Observation、Grounding、Persistent State、Planning、Verification 与 Actuation。没有跨任务真实运行时，Step 2 仍为 HOLD。

## 1. 它要证伪什么

待检验课题不是“加 Memory 能否涨分”，而是：

> 长程 GUI Agent 是否因为缺少可持续更新、可独立读取的任务状态，无法在事实被环境或用户证伪后修复依赖旧事实的外部产物？

竞争解释必须同时存在：

| 假设 | 可观察含义 |
|---|---|
| `H_E` | Agent 没有获得足以发现变化的 observation |
| `H_G` | observation 存在，但 grounding 没提取出任务相关变化 |
| `H_R` | 已提取变化，但跨步持久状态仍保留旧值、缺值或无法在行动时读取 |
| `H_P` | 当前事实正确，但没有找到受影响的计划、GUI artifact 与 repair obligations |
| `H_V` | 修复动作发生，但 Agent 没有选择或消费验证 observation |
| `H_A` | semantic action 正确，物理 click/type/coordinate realization 失败 |
| `H_M` | 多个边界是替代充分原因或联合瓶颈，不存在单一根因 |

任何一个假设均允许胜出。协议不能以保留 Memory 为优化目标。

## 2. 任务族资格

正式确认的独立单位是 base task family，而不是同一任务的 seed、更新位置或表面改写。执行前至少预注册八个异质 GUI task families，覆盖多个网站或桌面应用。

每个 family 的诊断实例必须满足：

1. 初始任务显式给出旧事实；
2. Agent 已基于旧事实写入 GUI 或生成可指纹化 artifact；
3. 用户更新、环境变化或验证 observation 明确使至少一个旧事实失效；
4. 旧 artifact 在 intervention assignment 前仍然存在；
5. 成功必须包含 invalidation detection、artifact repair/recomputation 和 final verification；
6. evaluator 不依赖开放式 LLM judge；
7. 至少有一个 unaffected control，检测错误 invalidation 与过度修复。

任务类型至少覆盖：

- value revision；
- retraction / cancellation；
- environment-driven precondition failure；
- partial completion 后的 scope change；
- verification 发现旧 artifact 已过期。

## 3. 共同时间线

所有 arms 使用同一顺序：

```text
生成或回放共同 prefix
→ update 前 eligibility：旧值已经影响外部 artifact
→ 注入共同 raw update / environment change
→ update 后、assignment 前 checkpoint：旧 artifact 仍存在
→ 随机分配 boundary intervention
→ 移除不允许保留的 source context
→ 延迟至少一个真实 Agent step
→ 继续执行至 task termination 或冻结 decision budget
→ 独立、blind evaluator 判分
```

每个 arm 必须使用 fresh Agent、browser/session 与环境 reset；不得共享 cache、store、hidden state 或结果。共同 prefix 的 URL、task-relevant fields、artifact fingerprint、accessibility tree 和 action hash 必须等价。

## 4. Phase A：Boundary-Isolated Functional Oracle Ladder

| Arm | 唯一允许替换的边界 | 禁止新增的信息或能力 |
|---|---|---|
| `B0` | 无；冻结 reference policy | 无 |
| `E_DECOY` | 与 probe 等动作数和延迟的无信息 observation action | 不返回任务相关新证据 |
| `E_STAR` | 固定部署可用 probe，返回 raw observation | 不解析 observation，不给动作答案 |
| `G_STAR` | 对同一 raw observation 给 observation-bounded transcription | 不读取第二 observation、future state 或 evaluator truth |
| `C_ONE_SHOT` | raw update 后一次注入 canonical current state | 不跨步持久，不给 dependency/repair plan |
| `C_REINJECT` | 每步重新注入与 `C_ONE_SHOT` 同命题状态 | 不使用独立 store；单独核算 token |
| `R_SHAM` | 调用相同 store API，但写入/读取 task-value-free sham payload | 不返回当前任务事实 |
| `R_STAR` | 固定 G output，只替换跨步持久 state updater/read API | 不提供 dependency graph、repair procedure、正确动作或 evaluator answer |
| `P_DIAG_CONTROL` | 告知 update 可能影响旧 artifact | 不给 dependency propagation、undo/recompute 或 recovery algorithm |
| `P_GENERIC` | diagnosis-matched、task-value-free dependency/repair policy | 不给本任务当前值、task-specific graph 或答案 |
| `P_ORACLE` | task-specific dependency/obligation plan | 仅作 planning ceiling；不使用 final truth |
| `V_DECOY` | 与 verification 等动作/延迟的无信息 probe | 不返回任务相关证据 |
| `V_SELECT_STAR` | 固定规则选择一个 deployment-available verification probe | probe 结果仍通过原 G/R/P pipeline |
| `A_STAR` | 只纠正已选择 semantic action 的物理 realization | 不纠正字段、值、action type 或计划 |
| `F_INFO_BOUNDED` | 组合所有 deployment-information-bounded oracle | 不使用 final evaluator truth |
| `F_MINUS_R` | `F_INFO_BOUNDED` 去掉 `R_STAR` | 其余组件与 full arm 完全一致 |
| `R_PLUS_P` | `R_STAR + P_GENERIC` | 不加入 G/V/A oracle |

### 4.1 `R_STAR` 的 Memory 资格

只有同时满足以下条件才叫 persistent-state intervention：

1. store 具有冻结 API、implementation hash、schema 与 write/update/read/evict 语义；
2. update 后只写一次；
3. 原始 update 与 one-shot state 从后续可见 context 中移除；
4. 至少跨一个真实 Agent step 后通过标准 read API 消费；
5. store payload 可被独立导出、替换和审计；
6. 与 `C_ONE_SHOT / C_REINJECT / R_SHAM` 做信息、token、tool-call、latency 和 deliberation 对照；
7. 不包含 task-specific repair plan 或最终动作。

任何一次性 Prompt、历史 recap 或每步 Prompt reinjection 都不能改名为 `R_STAR`。

## 5. Phase B：行动契约假设的可行性诊断

Phase B 只有在 Phase A 显示 `R_STAR` 具有独立候选效应后才执行。它仍是 oracle representation diagnosis，不是最终方法。

| Arm | Store payload | 识别目标 |
|---|---|---|
| `R_FACT` | current/superseded facts + source/version | 持久事实状态效应 |
| `R_CONTRACT_FLAT` | 与 contract arm 等命题的 flat prose | contract information effect |
| `R_CONTRACT_STRUCTURED` | 与 flat arm完全相同命题的 typed contract | serialization/representation effect |

contract 命题最少包括：

```text
fact/value/status/source
artifact identity
artifact depends_on facts
invalidation predicate and evidence
required repair or compensation obligation
verification predicate
recovery/fallback condition
```

三个 arms 使用相同 store API、写入时点、读取时点与 persistence。`R_CONTRACT_FLAT` 和 `R_CONTRACT_STRUCTURED` 的 proposition multiset 必须完全相同；否则只能测 contract information bundle，不能测 representation。

## 6. Outcomes

### 唯一 primary

`contract_consistent_completion`：

1. final GUI fields 使用 current facts；
2. 依赖 superseded facts 的 artifact 已撤销、替换或补偿；
3. 所有受影响计算在最后一次 repair 后重算；
4. final answer/deliverable 只由 repaired artifact 推导；
5. 冻结 verification predicate 通过；
6. 没有 superseded fact 支配最终结果。

### Secondary

- invalidation-detection latency；
- impact-set precision/recall；
- repair completion；
- verification completion；
- token/tool/latency cost；
- unaffected-task false-invalidation rate；
- recovery after failed repair。

`seen`、`correctly_interpreted`、elicited state report 和 impact set 都是 intervention 后变量，不得用于 primary 的筛选、调整或正式 mediation。

## 7. 判定表

| 结果模式 | 允许的根因结论 | 课题动作 |
|---|---|---|
| 只有 `E_STAR` 或 `V_SELECT_STAR` 修复 | observation/monitoring 路径是候选充分原因 | Memory 课题不成立，转向 active perception/verification |
| 只有 `G_STAR` 修复 | grounding 是候选充分原因 | 转向 update grounding |
| `C_ONE_SHOT` 与 `R_STAR` 等效 | persistence 没有独立价值 | 改为 Context/State Representation |
| `C_REINJECT` 与 `R_STAR` 等效且成本可比 | Memory 优势可由 context refresh 替代 | 不保留 Memory 因果主张 |
| `R_STAR` 独立修复，`F_MINUS_R` 明显下降 | persistent state 是充分路径，且在 full composite 中条件必要 | Memory 课题获得 Step 2 支持 |
| `P_GENERIC` 修复而 `R_STAR` 不修复 | plan–artifact repair 更可能 | 改为 Dynamic Intent Reconciliation / Replanning |
| `R_STAR`、`P_GENERIC` 分别修复 | 替代充分原因 | 不得选择较大效应称唯一根因 |
| 只有 `R_PLUS_P` 修复 | persistent state 与 planning 是联合瓶颈 | 研究联合架构，不做 Memory-only claim |
| 只有 `A_STAR` 修复 | actuation 是候选充分原因 | 转向 grounding-to-action reliability |
| 只有 `F_INFO_BOUNDED` 修复 | composite failure unresolved | 扩展交互，不进入方法阶段 |

Phase B 额外判定：

- `R_CONTRACT_FLAT > R_FACT`：只支持 contract information 的增量价值；
- `R_CONTRACT_STRUCTURED > R_CONTRACT_FLAT`：支持 typed contract representation 的增量价值；
- 两者均不优于 `R_FACT`：行动契约假设不成立；
- 只在 source context 仍可见或零延迟时有效：属于 Context，不属于 Memory；
- unaffected tasks 上 false invalidation 上升：契约机制存在负迁移，不能只报告成功任务。

## 8. 统计边界

- screening seeds 与 confirmation seeds 不重叠；
- paired seed 只是同一 family 内的技术重复，不是独立统计单位；
- primary inference 以 base task family 为单位，并按 template/site 做更高层聚类；
- 预注册唯一 primary estimand，其余使用 hierarchical testing 或 Holm correction；
- 报告 paired effects、exact/cluster intervals、全部 discordant families 与 missingness；
- 不用 post-treatment probe 选择样本；
- 不在 n=10 单任务 pilot 上做 power、equivalence、generalization 或 prevalence claim。

## 9. Step 2 完成门槛

只有以下证据全部存在，Step 2 才能从 HOLD 改为有条件完成：

1. 至少八个独立 revision/artifact families 的冻结 manifest；
2. 每个 family 的 baseline failure、prefix equivalence 与 post-update artifact checkpoint；
3. E/G/R/P/V/A boundary interfaces 的真实实现、hash 与 information-flow audit；
4. persistent store 的单写、移除 source context、跨步读取测试；
5. deterministic raw-trace evaluator 与 blinded audit；
6. 等信息、token、tool、latency、deliberation budget；
7. 预注册统计与 cross-family 结果；
8. multiple-sufficient-causes 判定，而不是 winner-takes-all 归因。

在这些条件满足前，允许的最高结论仍是：

> `2modification` 提供了 revision-artifact 诊断设计；v0.3 提供了 bundled Prompt instrument calibration；Memory、行动契约和自然根因均未被证明。

## 10. 当前 blockers

- 未选择并冻结八个独立 task families；
- Map WebArena 与其他 GUI environments 未运行；
- 没有稳定 baseline failures；
- 没有 boundary-replaceable reference Agent；
- `R_STAR` store API/implementation 不存在；
- raw HTML/action trace normalizer 未实现；
- 模型、seed、token、tool、latency 与 deliberation budgets 未冻结；
- 没有真实跨任务结果。

所以本文件是 **Step 2 的证伪协议草案，不是课题成立证明**。
