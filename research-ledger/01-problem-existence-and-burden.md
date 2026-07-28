# Step 1：证明问题现象与负担

> status: **IN PROGRESS**  
> decision dimensions: `C0-A / C0-B / C0-C / C0-D / C0-E`  
> current verdict: `FRAME-READY / DETAIL-AVAILABILITY-PARTIAL / MEASUREMENT IMPLEMENTATION NOT READY`

## 要证明的命题

在不为本研究额外注入 update 的 OSWorld 2.0 published trajectories 中，是否存在足够分散且具有可测 terminal correctness burden 的 `UACF-D`；其中 pure-world transition 子集是否单独达到 Environment-Falsifiable 题名门。

## 关键节点

| 日期 | 节点 | 可核验证据 | 结论与上限 |
|---|---|---|---|
| 2026-07-22 | 冻结 catalog frame | 108 tasks × 6 configs = 648 records；排除 development/stress 后 82 × 6 = 492 confirmatory units | 只证明 published-catalog frame，不证明 launched-run distribution |
| 2026-07-28 | 接入 ARIS 与 Keshav protocol | ARIS 666-file verifier PASS；两篇 PDF hash manifest；三遍阅读协议 | ARIS 只作 research harness，不能证明 GUI Memory 命题 |
| 2026-07-28 | Block A detail availability | 48/48 expected pages；47 valid replay；1 explicit no-step；9,138 embedded steps | replay availability `PARTIAL`；不证明 truth、UACF-D 或 faithful replay |
| 2026-07-28 | Round 4 第一轮反方 | candidate-action leakage、semantic-ID circularity、false upper、A0/A1/omission gate 缺口 | `NOT READY FOR BLOCK-A DRY RUN` |
| 2026-07-28 | Round 4 第二轮 battle | Block A development rebuttal 被接受；narrow design-only 被接受；要求 multi-event identity 与 full-block barrier | 修复方向 conceptually accepted，仍未形成可执行 measurement |
| 2026-07-28 | Round 4b global-bound 独立反方 | partial-identification 状态、negative certificate、finite joint completion、zero denominator 与 narrow claim 被反例击穿 | 初版修订被拒绝；`NO SYNTHETIC PROTOCOL FREEZE / NO BLOCK A` |
| 2026-07-28 | Stage A fail-closed 基础实现 | 11 个 closed Draft 2020-12 schemas；47/47 full-suite tests；29 个 one-damage negative fixtures | 只证明组件拒绝已知破坏；full-block ledger 未实现，生产路径固定 `NOT_READY` |
| 2026-07-28 | Round 4c release 独立审计 | 检查 production bypass、decision 修复、claim ceiling、Markdown、凭据与大文件 | 允许提交 NOT_READY 检查点；拒绝 synthetic freeze、Block A 与 Step 1 GO |

## 当前第一性结论

```text
目录和轨迹字段存在
不推出
目标现象存在

synthetic schema tests 通过
不推出
候选选择 outcome-blind

finite-bound 文本被修订
不推出
negative certificate 已可执行

detected roster 很小
不推出
总体 upper 很小
```

所以当前对问题 1 的答案仍是：

> **尚未证明。** 已证明的是可构造有限 catalog frame，并且 47/48 Block A 页面提供可解析 replay；行为现象、pure-world burden 与重要性仍等待有效测量。

## 解锁 Step 2 的最低门

- C0-A measurement reliability 有效；
- C0-B strict lower：至少 8 个 positive task ids 且至少 1.0 task-equivalent deficit；
- C0-C：至少 8 个 same-event candidate-interface task ids；
- C0-D：joint feasible completions 全部通过 structural dispersion；
- C0-E：pure-world supply、deficit、interface lower 同时过门，才能保留 environment track；
- Step 1.5 仍须另行通过，Step 1 GO 不等于因果执行 GO。

## 当前禁止结论

- GUI Agent 已被证明“需要 Memory”；
- Memory 是长期失败根因；
- 行动契约可以避免观测到的 loss；
- benchmark 比例等于生产发生率；
- 平均提升等于能力边界改变。
