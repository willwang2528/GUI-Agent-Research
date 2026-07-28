# Keshav Three-Pass Evidence Protocol for GUI Agent Memory Research

> protocol_version: `1.0`  
> frozen_at: `2026-07-28`  
> source: S. Keshav, `How to Read a Paper`, ACM SIGCOMM Computer Communication Review 37(3):83–84, 2007  
> DOI: `https://doi.org/10.1145/1273445.1273458`  
> local_source: `source_provenance/papers/keshav_how_to_read_a_paper.pdf`

## 1. 目的

本协议把 Keshav 的三遍阅读法改造成当前课题的证据门。目标不是读更多论文，而是阻止三类错误：

1. 把作者 motivation 当成问题已被证明；
2. 把方法中存在某字段当成它解决了根因；
3. 把平均 benchmark gain 当成长期能力边界变化。

每篇论文的阅读深度必须显式标记为 `PASS-1 / PASS-2 / PASS-3`。没有完成第三遍的论文，不能支撑“隐含假设、可复现根因、方法能力边界”类强结论。

## 2. Pass 0：身份与准入核验

阅读前先独立核验：

- Title；
- Authors；
- Year；
- Conference/Journal；
- CCF Rank 或 `arXiv / not formally published`；
- DOI / arXiv / official PDF；
- Code URL；
- 版本与发布日期；
- 是否属于 2024–2026 核心时间窗。

准入规则：

```text
2024–2026
AND high-quality venue or explicitly justified influential arXiv
AND methodological novelty
AND directly informs long-horizon agent state/context/planning
```

否则标记 `BACKGROUND / METHOD-REFERENCE / DISCARD`，不得进入核心证据池。

## 3. Pass 1：5C 快速筛选

按 Keshav 的顺序读 title、abstract、introduction、section headings、conclusion 和 references 概貌，并回答：

1. **Category**：measurement、causal analysis、benchmark、method、system report 还是 survey？
2. **Context**：它继承哪些理论与系统；真正竞争对象是谁？
3. **Correctness**：核心假设是否表面合理；结论是否超出证据类型？
4. **Contributions**：贡献改变了什么能力或测量边界？
5. **Clarity**：问题、方法、证据、限制是否能在一次阅读中被准确复述？

Pass 1 输出：

```text
KEEP_FOR_PASS_2
BACKGROUND_ONLY
METHOD_REFERENCE_ONLY
DISCARD
```

核心筛选问题：

```text
作者声称的问题
≠ 论文真正测量的问题
≠ 当前 GUI Memory 课题的根因
```

## 4. Pass 2：内容与证据审计

精读正文、图表、实验设置和限制，但暂不陷入证明或实现细节。每个核心 claim 建立：

| Claim | Evidence type | Denominator | Comparison | Causal or observational | Confounders | Claim ceiling |
|---|---|---|---|---|---|---|

必须回答：

- 指标的分母是什么，missingness 如何处理？
- 图中是否有误差条、置信区间、seed 数和统计单位？
- baseline 是否同信息、同预算、同工具、同模型能力？
- 结果是观察相关、干预效应、机制隔离还是仅工程可运行？
- 失败案例是否报告，是否有结果后筛选？
- 是否把 replay availability、字段存在或 reviewer score 当成科学效果？
- 哪些结论是论文直接证据，哪些只是作者推论？

针对当前主题额外记录：

```text
Memory representation
storage
retrieval
update
validity / invalidation
dependency propagation
recovery
action-time accessibility
environment verification
long-horizon scaling evidence
token/context cost
```

## 5. Pass 3：虚拟复现与假设攻击

按 Keshav 的要求，在不照抄作者实现的前提下虚拟重建论文：

1. 写出最小输入、状态、干预、输出和 evaluator。
2. 枚举每个结论依赖的隐含假设。
3. 指定什么 observation 会证伪该 claim。
4. 构造至少一个作者方法会误判的反例。
5. 重建 matched baseline、negative control、ablation 和 missingness rule。
6. 区分信息增益、结构增益、policy 增益、budget 增益和 oracle privilege。
7. 判断机制能否无特权地迁移到 GUI Agent。

Pass 3 的最终链必须是：

```text
重要现象
→ 根因
→ 现有方法为何无法消除根因
→ 新机制改变哪条因果边
→ 哪个实验能证伪新机制
```

若无法重建这条链，只能保留为 engineering inspiration，不能作为 research-gap 证明。

## 6. 每篇论文的强制输出

```text
Title:
Authors:
Year:
Conference/Journal:
CCF Rank:
URL:
Code URL:
Citation:
Reading Pass Reached:
Research Direction:
Main Problem:
First-Principles State Constraint:
Core Method:
Evidence Type:
Why Important:
Why Existing Methods Fail:
Why This Mechanism Could Work:
Assumptions:
Limitation:
Claim Ceiling:
Potential GUI Agent Connection:
Possible Research Opportunity:
Discard Reason:
```

其中三个 Why 必须由论文的可复核证据支持，不能只转述 abstract。

## 7. 文献调研的使用方式

遵循 Keshav 的 survey 策略，但控制论文数量：

1. 每个方向先找 3–5 篇最近、高质量候选，执行 Pass 1；
2. 通过者追踪其共同引用、反复出现的作者和最近顶会工作；
3. 只对能改变当前 claim ladder 的论文执行 Pass 2；
4. 只对核心对照、最强反例和可迁移机制执行 Pass 3；
5. 最终表格保持稀疏，不用大量弱相关论文制造“调研充分”的假象。

## 8. 与七步课题的绑定

| 课题步骤 | 最低阅读深度 |
|---|---|
| Step 1 问题存在性 | measurement/benchmark 论文至少 Pass 2；关键测量论文 Pass 3 |
| Step 2 根因隔离 | Memory/context/planning 强方法全部 Pass 3 |
| Step 3 现有方法 residual | 最强 baseline 的论文+代码 Pass 3 |
| Step 4–6 方法与公平性 | 对照机制、evaluator、budget protocol Pass 3 |
| Step 7 论文主张 | 所有支撑核心 claim 的论文 Pass 3 + citation audit |

## 9. Fail-Closed 规则

- URL、venue、年份或版本未核验：不进入表格。
- 只读摘要：只能标 `PASS-1`。
- 没有检查 denominator / baseline / missingness：不能声称定量证据充分。
- 没有虚拟复现：不能声称找到根因或隐含假设。
- arXiv 系统报告没有 controlled evaluation：只能作为方法来源或待验证新方向。
