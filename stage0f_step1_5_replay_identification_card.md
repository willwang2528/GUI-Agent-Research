# Stage 0F：Step 1.5 Replay Identification Card

> 版本：v0.3，2026-07-28  
> 状态：**PROTOCOL THRESHOLDS PROVISIONALLY SPECIFIED / MEASUREMENT STACK NOT FROZEN / NO STEP 1 OUTCOME UNBLINDED**  
> 作用：判定 Step 1 的 candidate interfaces 是否足以支持因果执行，或只能支持 transport experiment  
> 当前结论：**SAME-SYSTEM ELIGIBILITY UNVERIFIED / TRANSPORT ELIGIBILITY PENDING**

## 1. 输入与选择规则

本卡只在 Step 1 产生 `GO_TO_STEP2_PROTOCOL_CONSTRUCTION` 后执行。它不使用新阈值重新解释 Step 1 burden。`BROAD_SCOPE_REJECTED_NARROW_HYPOTHESIS_ONLY` 只允许提出待检验的 narrow hypothesis，不支持任何具体 narrow scope，也不允许在当前 frame 内进入本卡或因果执行；若要执行，必须使用未被当前 development/review 暴露的新数据，另行冻结窄域 sampling frame、coverage thresholds 与 Step 1 preregistration，并从 Step 1 重新裁决，不能在看到当前结果后临时放宽本卡。

选择单位不是裸 task，而是一个不可变的 replay case：

```json
{
  "protocol": "Stage0F-Step1.5-v0.3",
  "task_id": "<task_id>",
  "hosted_config_id": "<hosted_config_id>",
  "boundary_location_id": "<Stage-A pre-action boundary location id>",
  "adjudicated_event_id": "<Stage-A post-freeze semantic event id>",
  "interface_id": "<interface_id>",
  "intervention_api_version": "<exact version>"
}
```

`case_id = SHA256(RFC8785-JCS(case_object 的 UTF-8 bytes))`。`boundary_location_id` 必须来自 current candidate action reveal 前的 rolling-prefix commitment，并绑定 cutoff ordinal 与净化 prefix payload hash；`adjudicated_event_id` 必须在 A0 独立冻结 proposition id、排序后的 obligation ids 与 boundary type 后、且在整个 block 的 A1 reveal 前生成，并引用该 location。同一 location 可以有多个 semantic events。缺少任一 identity、block-level A0 barrier 或 API version 的候选不能进入选择池。不得用 generator provisional semantics、展示标题、网页 URL 或本地路径代替 identity。

令 `k = min(12, positive candidate pool 中不同 task_id 的数量)`。从所有大小为 k、且每个 task 最多一个 case 的子集中施加 coverage constraints：至少 4 个预冻结 structural groups、3 个互斥 site/application sets、2 个 agent model families。若存在满足全部 constraints 的子集，只在这些子集中按 `SHA256("Stage0F-Step1.5-select-v0.3|" + join(sorted(case_id), "|"))` 升序取第一个。

若不存在满足全部 constraints 的子集，冻结诊断子集为依次最大化：

1. 满足的三个 coverage constraints 数量；
2. `min(G/4, 1) + min(S/3, 1) + min(M/2, 1)`；
3. `G + S + M`；
4. 最后以同一 selection hash 的升序打破并列。

这里 G/S/M 分别是子集覆盖的 structural groups、互斥 site/application sets 与 agent model families 数。进入这一诊断分支会预先令 S1.5-E 不可能 PASS，不能在结果后换 case。

screen、manipulation dry-run 与后续 confirmatory causal experiment 使用互不相交的 seed namespaces 和 repeats：

```text
screen seed       = low64(SHA256("Stage0F-Step1.5-screen-v0.3|<case_id>|<repeat>"))
manipulation seed = low64(SHA256("Stage0F-Step1.5-manip-v0.3|<case_id>|<arm>|<repeat>"))
confirmatory seed = low64(SHA256("Stage0F-Step2-confirm-v0.1|<case_id>|<cell>|<repeat>"))
```

`low64` 固定为 digest 前 8 bytes 按 unsigned big-endian 解释。每个 case 固定 5 次 unmodified-control screen repeats。screen 数据与 seed 不得进入 confirmatory effect estimator，也不得作为 confirmatory repeats 重用。confirmatory repeat 数量由 Step 2 的 outcome-blind power/simulation card 独立冻结后才生成 seed list；不得依据 screen 或 manipulation 结果选择 seed、删减 cell 或改变 N。三个阶段的执行顺序分别按各自 unit hash 升序冻结。

## 2. S1.5-A：Hosted identity 与 reconstructed freeze 分离

### A_hosted_identity

对原 published hosted run 审计：

```text
model provider and exact build/version
system/developer prompt bytes
tool schemas and versions
context-construction code and ordering
action space and execution wrapper
budget mode and numeric budget
memory initialization and persistent store
task instruction, evaluator and environment snapshot
```

- `MATCH`：所有字段均有原 run 的可审计值，replay 使用的值与其 bytes/version hash 全部匹配。
- `MISMATCH`：至少一个字段有原 run 的可审计值，且 replay 已证实不同。
- `UNKNOWN`：没有已证实 mismatch，但原 run 至少一个关键字段无可审计值。

`UNKNOWN` 只阻断“解释原 hosted Agent”这一 claim，不阻断冻结 reconstructed system 上的 transport estimand。

### A_reconstructed_freeze

对实际将运行的 reconstructed system 独立审计同一字段：

- `PASS`：所有字段在任何 screen/manipulation/confirmatory outcome 之前完成 bytes/version hash 冻结，且每次 run 都可日志复核。
- `FAIL`：至少一个字段已知随 arm、repeat 或运行时间漂移，或已知无法按冻结值执行；该状态优先于同维度内的证据缺失。
- `UNIDENTIFIABLE`：没有已知违反冻结的证据，但因缺失日志/版本工件，无法判定实际运行值是否等于冻结值。

environment fingerprint 不以截图相似代替。task instruction、setup/evaluator version 与所有 task-relevant predicates 必须精确相同；非任务视觉字段可变，但必须在 outcome 前列入 allowlist，并由两位 blind auditor 确认不改变合法 action、probe 或 evaluator predicate。

## 3. S1.5-B：Control reproduction

“重现”指同一可观察 phenotype：预冻结 `p_old`、已送达 `p_new`、同一 normative action change，以及与 `p_old` 相容、与 `p_new` 下规范动作不相容的外部行为。不要求字符级相同 action sequence。

- case-level reproduced：同一 case 的 5 次 screen control 中至少 2 次出现该 phenotype。
- `PASS`：至少 8 个不同 task ids 各有一个 case-level reproduced case，且合计覆盖至少 4 个预冻结 structural groups。
- `FAIL`：完成所有预选 case 的 5 次 control 后，上述数值门未达到。
- `UNIDENTIFIABLE`：因非随机性基础设施丢失、truth/evaluator 不可审计或关键 trace 缺失，无法完成冻结 repeats。

2/5 是候选事件进入因果执行的 reproducibility screen，不是原 published run 的发生率估计，也不是 confirmatory 效应数据。后续 treatment 效应必须使用独立的全部预注册 confirmatory repeats，不能只保留复现的 seed。

## 4. S1.5-C：Intervention implementability

同一 versioned intervention API 必须在至少 8 个 task ids 上支持对称 setter、sham 和 control；同一 versioned consumer API 还必须支持三个预冻结 P operator modes：

```text
control: unmodified boundary payload
sham: serialized and reinserted without changing target state
set-stale: use the same setter to write the preregistered stale target state
set-correct: use the same setter to write the preregistered correct target state

P_operator:
  identity_no_propagation
  flat_scan
  dependency_graph_propagation
```

- R manipulation check：在不执行后续 planner/action 的 dry-run 中，每个 `case × R arm` 精确运行 20 次；`set-stale` 与 `set-correct` 各至少 19/20 次把且只把预注册目标 payload 写成指定值，control/sham 各至少 19/20 次保持目标 payload 不变。
- P manipulation check：每个 `case × P_operator arm` 同样精确运行 20 次；至少 19/20 次必须证明共同 consumer API、R payload hash、semantic-closure hash、visibility/serialization 与预算档位完全相同，且只启用指定 operator。`identity_no_propagation` 仍消费同一 R payload，只禁止依赖传播；它不是“无 consumer”。
- 任一 check 中 crash、timeout、parse error、missing log 与 API no-op 均计入原定 20 次分母并记为失败，不补跑、不替换 seed。
- `PASS`：同一 API 在至少 8 个 reproduced tasks 上达到 manipulation check，且存在 deterministic evaluator 或 treatment-blind adjudication。
- `FAIL`：接口可测但未达数值门，或只能改变 final evaluator 而不能替换 decision boundary。
- `UNIDENTIFIABLE`：接口或目标状态无法从日志中审计。

`19/20 = 0.95` 是 outcome 前冻结的**协议进入阈值**，不是从数据校准出的可靠性结论，也不是 95% 置信下界。结果必须逐 `case × arm` 报告；不得跨 case pooling 掩盖失败。

## 5. S1.5-D：Boundary isolation

每次 replay 必须冻结 R boundary 上游的 observation/evidence prefix、grounding result、Agent architecture/weights、system/developer prompt template、tools/API、非目标 stores、evaluator、payload schema/字段顺序/serialization/来源/可见性/注入时点、动作预算、延迟档位与总 token 档位。R contrast 中只允许预注册命题的 stale/correct value、version 与 validity 改变；长度差用 outcome-blind inert padding 匹配，不允许 treatment 附带额外 instruction、repair hint、privileged truth 或不同预算。

- `PASS`：arms 之间的差异仅限预注册 boundary operation，以及 setter 的 R payload 目标语义值；`set-stale` 与 `set-correct` 调用同一代码路径和 serialization，非目标 fingerprint 匹配率为 1.00，budget 处于同一预冻结档位，且 evaluator/adjudicator 对 arm 盲。
- `FAIL`：直接日志显示干预同时改变了非目标 boundary，无法用 sham 或 factorial arm 分离。
- `UNIDENTIFIABLE`：非目标 boundary 或预算对齐无日志可审计。

这里冻结的是 planner/action **实现、权重与配置**，不是其输出。correct-vs-stale R payload 之后产生的 planner reasoning tokens、dependent-state propagation、semantic action、GUI action sequence、verification 与 recovery 是合法的下游中介，必须允许改变并计入 `R→P boundary payload total downstream effect`。主设计为 `R ∈ {stale, correct}` × `P_operator ∈ {identity_no_propagation, flat_scan, dependency_graph_propagation}` factorial；三个 P arms 通过共同 consumer API 接收相同 R payload 与相同 action-relevant semantic closure，只改变预注册 operator。估计 R 的 cell 内 simple effects、P 主效应和 R×P interaction。

若干预还改变 payload 来源、可见性、schema/serialization、长度档位、instruction cue、privileged truth 或 budget，则本卡最多识别 `state-conditioning package effect`，不能称 R-boundary effect；bundle 无法完整日志化时 C1-R = `UNIDENTIFIABLE`。下游中介自然变化不触发这个降级。

## 6. S1.5-E：Cross-case support

- `PASS`：同一 versioned intervention 同时覆盖至少 8 个 reproduced task ids、4 个 structural groups、3 个互斥 site/application sets 和 2 个 agent model families。
- `FAIL`：完成所有预选 candidate 的 interface audit 后仍低于任一数值门。
- `UNIDENTIFIABLE`：structural mapping、model provenance 或 interface coverage 不可审计。

本门只证明共同干预具有多案例支持，不证明跨家族泛化。真正的 unseen-family 证据留给 C3/C4。

## 7. 互斥、穷尽的派生裁决

每个 B/C/D/E 维度先给出单一状态：出现可审计的硬违反时记 `FAIL`；没有硬违反但关键真值因非随机缺失而无法判定时记 `UNIDENTIFIABLE`；满足全部条件才记 `PASS`。S1.5-C 已冻结的 crash/timeout 等必须按 20 次分母计为 manipulation failure，不能改写成 missingness。

随后按从上到下的优先级只匹配第一条。已知 sufficient hard failure 优先于其他维度的 unknown；unknown 不能抹掉已经成立的阻断证据。所有未识别维度另写入 `additional_unresolved_dimensions`：

| 条件 | `STEP1_5_DECISION` | 最高允许主张 |
|---|---|---|
| `A_reconstructed_freeze = FAIL`，或 B/C/D/E 任一 = `FAIL` | `BLOCKED` | 仅保留 Step 1 观察性结论 |
| 没有任何 `FAIL`，但 `A_reconstructed_freeze = UNIDENTIFIABLE`，或 B/C/D/E 任一 = `UNIDENTIFIABLE` | `UNIDENTIFIABLE` | 不得启动确证性因果执行 |
| `A_reconstructed_freeze = PASS`，B/C/D/E 全部 = `PASS`，且 `A_hosted_identity = MATCH` | `SAME_SYSTEM` | 可执行预注册竞争性根因实验，并把 estimand 限于已匹配 hosted system |
| `A_reconstructed_freeze = PASS`，B/C/D/E 全部 = `PASS`，且 `A_hosted_identity ∈ {MISMATCH, UNKNOWN}` | `TRANSPORT_ONLY` | 只研究冻结 reconstructed system 的 mechanism / transport effect；不解释原 hosted Agent |

四个 completed-audit 裁决 `SAME_SYSTEM / TRANSPORT_ONLY / BLOCKED / UNIDENTIFIABLE` 互斥且穷尽；审计未完成时只记 `PENDING`，不是第五种最终裁决。优先级只用于同时存在多个 failure/unknown 的情形：可审计的 hard failure 先输出 `BLOCKED` 并保留 unresolved ledger；没有 hard failure 时才判断不可识别性，最后判断 hosted identity。不存在 `PARTIAL GO`。不允许在看过 control reproduction 或 manipulation outcome 后改 equivalence fingerprint、case/group 数量、repeats、干预选择、预算档位或真值表。

机械枚举 `A_hosted_identity` 三值、`A_reconstructed_freeze` 三值及 B/C/D/E 各三值的全部 729 个 completed-audit 组合，必须验证每个组合恰好命中一条：当前优先级对应 `BLOCKED=633`、`UNIDENTIFIABLE=93`、`SAME_SYSTEM=1`、`TRANSPORT_ONLY=2`。枚举脚本与 measurement stack 一同冻结；计数变化即视为 decision logic revision。

## 8. Claim ceiling

`SAME_SYSTEM` 或 `TRANSPORT_ONLY` 也不证明 Memory 是根因。它们只证明 C1 的竞争性干预可被识别，并分别限定 same-system 或 transport estimand。

`TRANSPORT_ONLY` 不是失败，但它改变 estimand：研究问题从“原 published trajectory 为什么失败”变为“在冻结 reconstructed system 中，该 mechanism 是否存在”。
