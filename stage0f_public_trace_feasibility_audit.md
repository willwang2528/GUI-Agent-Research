# Stage 0F：公开轨迹可标注性审计

> 日期：2026-07-22  
> 状态：**PARTIAL PASS FOR STAGE A / BLOCKED FOR INDEPENDENT STAGE B TRUTH**  
> 作用：检查公开 OSWorld 2.0 artifacts 能否支持 Step 1 盲标，不判断 UACF-D 发生率

## 1. 审计对象

本轮只读检查三个不同角色的 catalog records：

| Record | 角色 | Status / score | Steps |
|---|---|---:|---:|
| Task 009 × Claude Opus 4.7 | hash-random ontology pilot | Done / 0.7227 | 225 |
| Task 065 × Claude Opus 4.7 | hash-selected dynamic stress | Done / 1.0000 | 487 |
| Task 035 × MiniMax M3 | 非盲 training case | Done / 0.0000 | 130 |

Task 009、065 的选择在查看各自结果前由 Stage 0F hash 规则冻结；Task 035 是已知作者案例，只能训练 schema。

## 2. 公开 detail API 实际提供什么

三个 records 均提供：

- task id 与 instruction；
- model/config label；
- terminal status、score、step count；
- 每个 normalized step 的 timestamp；
- raw action / raw command / raw response；
- 每一步 screenshot URL；
- final task-level score；
- 指向 trajectory archive 与 gated task source 的链接。

字段级结果：

| Record | normalized steps | 有 screenshot 的 steps | 有 raw action 的 steps | reasoning present | assistant message present |
|---|---:|---:|---:|---:|---:|
| 009 × Opus | 225 | 225 | 225 | 0 | 32 |
| 065 × Opus | 487 | 487 | 487 | 0 | 87 |
| 035 × M3 | 130 | 130 | 130 | 117 | 130 |

因此，公开 monitor 对 observation/action timeline 的恢复能力比只看项目页案例强得多；Stage A 的 prefix、候选动作与 screenshot packet 在技术上可构造。

## 3. reasoning 缺失意味着什么

Opus records 的独立 `reasoning.present` 为 0。raw response 可能含 provider block 或 assistant message，但不能等同于完整内部 state。M3 的公开 record 则包含大量 reasoning text。

这带来两个约束：

1. `UACF-D` 作为外部行为链仍可能被标注；
2. `G / R / P` 的内部根因可观察性随模型不同，不能因为 Opus 没有 reasoning 字段就把缺陷归给 Memory，也不能把 M3 自述当因果真值。

所以 Step 1 的 root-cause 字段必须保留 `compatible / unobserved`；正式根因仍需 Step 2 boundary replay。

## 4. Task 035 显示为什么不能只看最终 score

Task 035 × M3 的 detail record 显示：

- Agent 读取了初始预算、vendor 与明确 reject decisions；
- 之后实际观察并响应了 camera special exception；
- 更晚又观察到 budget 与 approved vendor correction；
- Agent 将 27-inch monitor 从 Rejected 改为 Approved；
- final self-report 声称五个已处理 rows 与当前规则一致；
- catalog final score 仍为 0.0000。

这不能证明 Agent 完成正确。官方论文的行为分析还指出该轨迹遗漏了其他 late obligations，并可能修改了不应修改的 baseline row。它证明的是：

```text
final score = 0
不等于
每一条动态更新都没有被吸收
```

同样，某些更新被正确吸收也不等于整个 task 没有 UACF-D。必须对 changed proposition、dependency、required action、deadline 与 final predicate 逐项标注，不能用任务总分替代。

## 5. 规范真值和 evaluator 的公开性 blocker

官方 task detail 链接指向 `osworld_v2_tasks`。该官方数据集是 gated：公开页面明确说明 task implementations 被门控，以避免 evaluated Agent 在线找到 setup、答案或 evaluator details。

本地 release manifest 虽然引用：

```text
tasks tag = v2026.06.24
task hash manifest count = 108
task hash manifest sha256 = 3312a7df40dbd004c300804f71c57d5a23a083d6c675082fcc34c60a37f9a76c
```

但 hosted detail record 没有逐运行 task hash、evaluator hash 或 verification status。公开代码的 release README 也把 per-run provenance 和 runner verification 描述为应当写入的能力，而不是现有每条 trajectory 的证明。

此外，Task 065 的官方讨论记录显示在发布准备期间修改过 instruction、setup 和 evaluator。这些修订可能已经被 `v2026.06.24` tag 正确冻结，但它们进一步说明不能用 floating `main` 代替 release tag。

在未取得 gated `v2026.06.24` task classes、task hash manifest 与 evaluator replay bundle 前：

- Stage A 可以使用 Agent-visible instruction 与公开 observation/action；
- Stage B 的 normative obligations 可从 instruction 做独立人工定义；
- 但 evaluator secret、setup truth、完整 checkpoint weights 和 episode-specific final truth 不能被称为已独立复现；
- 凡是依赖 gated truth 的 unit 必须标为 `truth-unverified`，并进入 missingness / partial-identification audit。

## 6. 当前判定

| Gate | 判定 | 原因 |
|---|---|---|
| prefix action timeline | **PASS on 3/3 audited records** | normalized actions、timestamps、raw commands 可恢复 |
| per-step visual evidence | **PASS on 3/3** | 每个 normalized step 有 screenshot URL |
| hidden/internal state | **FAIL BY DESIGN** | reasoning coverage 模型相关，且不等于独立 state store |
| model-independent semantic action | **PARTIAL** | raw action 存在；完整意图有时需从 response 推断 |
| release-tagged normative task class | **BLOCKED / GATED** | 未取得 `v2026.06.24` task source |
| independent evaluator truth | **BLOCKED** | 只有 catalog score，缺少逐 task evaluator replay 与人工全覆盖真值 |
| Stage A packet feasibility | **PARTIAL PASS** | 可构造 prefix packet，但须下载并冻结 screenshots |
| Stage B final adjudication | **NOT YET ELIGIBLE** | gated truth 与 evaluator mismatch 仍未排除 |

当前不能开始正式 492-unit held-out burden audit。下一步只能先完成 Block A 48-unit pilot 的 data-availability manifest，并把 `truth-unverified` 作为显式结果，而不是静默 complete-case 删除。

## 7. 官方来源

- [OSWorld 2.0 paper](https://arxiv.org/abs/2606.29537)
- [OSWorld 2.0 trajectory catalog](https://osworld-v2-monitor.xlang.ai/)
- [OSWorld 2.0 trajectory archive](https://huggingface.co/datasets/xlangai/osworld2.0-trajectory/tree/main)
- [OSWorld V2 gated task classes](https://huggingface.co/datasets/xlangai/osworld_v2_tasks)
- [Task 065 task/evaluator update discussion](https://huggingface.co/datasets/xlangai/osworld_v2_tasks/discussions/4)
- [Task 065 selected-definition fixes](https://huggingface.co/datasets/xlangai/osworld_v2_tasks/discussions/12)
