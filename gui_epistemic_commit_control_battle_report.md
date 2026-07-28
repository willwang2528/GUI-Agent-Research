# 长程 GUI Agent 的 Epistemic Commit Control：三问题对抗式论证报告

> 时间范围：严格限定 2024–2026 年正式论文；ToolGate 虽为 ACL Findings 2026，仅作为不可忽略的 prior-art 威胁，不作为顶会核心支撑。  
> 研究对象：长程 GUI Agent 中的 Memory / Context、状态维护、主动验证和不可逆动作控制。  
> 论证方法：实证审计者、SOTA 最强辩护者、形式化评审者，围绕三个问题各进行两轮主张—反驳—裁决。

---

# 0. 最终结论

原命题：

> 长程 GUI 控制的 memory 必须成为可被环境证伪的行动契约；只有当 Agent 知道哪些事实必须仍然为真、为何为真以及错误后如何恢复，Memory 才真正改变能力边界。

经两轮、多方对抗后，结论是：**该命题的重要直觉成立，但理论措辞、现有工作判断和新颖性主张都过强。**

最终保留的科研问题不是“设计一种新的 contract memory 表示”，而是：

> **在开放、部分可观测的长程 GUI 中，Agent 如何判断当前环境证据是否足以授权一个具有特定前置条件和错误损失的动作；若证据不足，如何根据风险、信息价值、验证成本和可逆性，在 execute、主动 probe、safe alternative、abstain 与 human confirmation 之间决策？**

建议名称：

> **Open-World Risk-Calibrated Epistemic Commit Control**

或更偏方法的问题名：

> **Risk-Conditioned Active State Disambiguation before Irreversible GUI Commitments**

当前研究状态：

| 判断项 | 结论 |
|---|---|
| 长程 GUI 需要 action-sufficient state | 已由理论和 AgentProg 消融较强证明 |
| belief 应允许新环境证据修正 | 条件性成立，且已有强实证支持 |
| post-action detection / recovery 不充分 | 已有直接数据证明“不完美”，但失败根因未被完全归因 |
| 所有 memory 必须成为显式 contract | 不成立 |
| contract 表示具有现有组合无法表达的能力 | 不成立 |
| 现有方法原则上不能主动验证 | 不成立 |
| GUI 中 contract grounding / risk-calibrated commit 尚未解决 | 作为“未被联合评测的问题”成立 |
| revised idea 必然有效 | 尚未证明 |
| revised idea 值得做 Stage-0 Oracle study | 成立，Conditional Go |

最重要的纠偏是：

> **Contract 不创造信息。真正可能改变有限 Agent 能力的是：保存当前 actor 已不可访问的 action-relevant state，暴露尚未证实的动作依赖，触发具有正决策价值的新环境取证，并把新证据转化为风险敏感的 commit 决策。**

---

# 1. Battle 设计与证据规则

## 1.1 三个角色

| 角色 | 责任 |
|---|---|
| 实证审计者 | 只接受论文直接数据、受控消融和明确报告的失败；禁止把架构猜测当实证 |
| SOTA 最强辩护者 | 尽可能证明 AgentProg、MaDS、InferAct、ToolGate 等已经覆盖 idea，防止伪 gap |
| 形式化评审者 | 用 POMDP、信息论、Bayes decision、不可逆动力学构造定理、反例和不可解边界 |

## 1.2 证据等级

- **A：直接因果证据。** 受控消融或直接干预目标组件。
- **B：直接相邻证据。** 论文明确报告相关失败或改进，但未隔离目标根因。
- **C：演绎反例。** 从方法定义可构造失败，但论文没有测量真实发生率。
- **D：猜测。** 不进入论文主张。

## 1.3 两轮对抗摘要

| 问题 | 第一轮冲突 | 第二轮裁决 |
|---|---|---|
| Q1 问题是否真实 | 实证方认为 long-horizon failure 与 recovery 数据支持；反方指出 AgentProg 已有 Predict–Verify–Align；形式方否决“显式 contract 必要” | 原命题 Reject；保留高风险动作前 action-specific evidence sufficiency |
| Q2 为什么现有方法不行 | 实证方逐篇审计；反方构造 SOTA-Composite；形式方给出不可区分性下界 | “缺 contract 组件” Reject；保留 risk-calibrated active disambiguation 的 objective / benchmark gap |
| Q3 为什么 idea 可行 | 实证方给组件证据和 Oracle Ladder；反方攻击 unknown unknown、TOCTOU、成本和过度拒绝；形式方给 Bayes gate 与 EVSI 定理 | Conditional Go，仅批准 Stage-0；不能承诺未来方法成功 |

---

# 2. 问题一：它究竟解决什么，为什么这是一个问题？

## 2.1 先纠正待证明对象

原命题混合了三个不同主张：

1. 长程 GUI 需要保存足以决定未来动作的信息；
2. 这些状态必须能被新环境证据修正；
3. 这些状态必须采用显式“行动契约”表示。

前两条可被理论和实证支持；第三条不能成立为必要条件。一个足够好的 belief state、program variables、recurrent latent state 也可能满足决策充分性。

因此，真正要解决的问题应改为：

> **Agent 在高风险或不可逆动作发生前，是否掌握了足以授权该动作的证据？**

它不同于“Agent 当前认为世界是什么状态”。同一份 belief 可能足够授权“打开菜单”，却不足以授权“发送邮件”“覆盖文件”或“提交支付”。

## 2.2 第一性原理证明：为什么长程任务需要 Memory / Context

设两个历史 $h,h'$ 在当前屏幕上产生相同 observation，却要求互斥的正确动作：

$$
o(h)=o(h'),\qquad A^*(h)\cap A^*(h')=\varnothing
$$

如果 Agent 的 memory 表示把二者映射到同一状态：

$$
M(h)=M(h')
$$

任何只依赖 $M$ 的策略都不可能在两个历史上同时正确。

最简单的二值构造是：早期页面显示隐藏 bit $x\in\{0,1\}$，几十步后出现完全相同的提交页；$x=0$ 必须选择 A，$x=1$ 必须选择 B。若 Agent 忘记 $x$，等先验下最大正确率只有 50%。若需要记住 $n$ 个独立 bit，而 memory 全部遗失，完整决策的成功率上限降为 $2^{-n}$。

这证明：**在 observation aliasing 或 delayed dependency 下，action-sufficient information state 是功能必要条件。** 它没有证明必须使用 contract。

## 2.3 定量证据：长程与 memory-intensive GUI 任务确实显著更难

| 论文 | 直接结果 | 能证明什么 | 不能证明什么 |
|---|---|---|---|
| [UI-Copilot, ACL 2026](https://aclanthology.org/2026.acl-long.904/) | MemGUI-Bench 最优轨迹平均 36.2 步，AndroidWorld 为 8.4 步；现有 7B GUI 模型在 MemGUI-Bench 平均性能下降 90.90% | memory-intensive、长轨迹任务形成显著能力下降 | 不能把全部下降归因于 action contract 缺失 |
| [MobileBench-OL, ACL Findings 2026](https://aclanthology.org/2026.findings-acl.668/) | UI-TARS-1.5-7B 从 Base SR 60.97 降到 Long-Horizon SR 15.00，下降 45.97 点 | 长程 online GUI 控制发生巨大退化 | 还混合 grounding、规划和环境变化 |
| [AgentProg, MobiSys 2026](https://www.sigmobile.org/mobisys/2026/program/) | AW-Extend 平均超过 30 步；强基线约 23.7%–36.8%，AgentProg 68.4% | program-structured context 与 belief 对长程任务有巨大价值 | 不能证明剩余 31.6% 失败来自 evidence sufficiency |
| [MMBench-GUI, CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Wang_MMBench-GUI_A_Unified_Hierarchical_Evaluation_Framework_for_Multi-Platform_GUI_Agents_CVPR_2026_paper.html) | 官方分析指出跨应用、复杂协作任务暴露 memory、planning 和 adaptive reasoning 弱点 | 问题跨平台存在，不是单一 benchmark 偶然 | 总成功率不能隔离 memory 根因 |

这些结果充分证明“长程 GUI 是显著困难问题”；它们不足以直接证明“行动契约是根因”。

## 2.4 定量证据：状态维护、验证和恢复具有大幅因果价值

### AgentProg：最强直接证据，也是对原 idea 的最大反证

[AgentProg](https://arxiv.org/html/2512.10371v2) 在 AW-Extend 的受控消融：

| 设置 | AW-Extend SR | 相对完整系统下降 |
|---|---:|---:|
| 完整 AgentProg | 68.4 | — |
| 去掉 Global Belief State | 35.1 | 33.3 点 |
| 去掉 Execution Tree | 39.5 | 28.9 点 |
| 去掉 Explicit Variables | 50.0 | 18.4 点 |

AndroidWorld 上，去掉 Global Belief State 也从 78.0 降至 53.9，下降 24.1 点。

这构成 A 级证据：**结构化变量、控制依赖与 observation-driven belief revision 显著改变长程任务能力。**

但 AgentProg 已经拥有 Predict–Verify–Align、confirmed / hypothesis 区分、关键 hypothesis 主动探索、冲突后 belief invalidation 与 replanning。因此不能再说“现有 memory 不能被环境证伪”。

### BacktrackAgent：post-action verification 有用但覆盖有限

[BacktrackAgent, EMNLP 2025](https://aclanthology.org/2025.emnlp-main.212/) 报告：

- 相对 ReachAgent，task success 提升 7.59 个百分点；
- error detection precision 75.12%，recall 43.58%；
- 在检测到的错误中，recovery accuracy 38.93%；
- 推理速度约降至 generator-only 的 50%。

它直接证明环境结果检测和 backtracking 有价值，也证明通用 post-action verifier 存在大量漏检、恢复失败和明显成本。但不能据此断言“pre-action contract 一定能修复”。

### LongHorizonUI：rollback 不是可靠的语义恢复

[LongHorizonUI, ICLR 2026](https://iclr.cc/virtual/2026/poster/10010959) 报告的 rollback 触发率约为 12.4%–18.6%，触发后成功率约为 69.7%–73.1%，仍有约 27%–30% 的触发案例未恢复，另有 1.8%–2.7% 需要完全重启。

这证明“错误发生后总能恢复”不成立；但论文没有把失败分解为 verifier、checkpoint、planner 或真实不可逆 side effect。

### MobileUse：reflection 可以纠错，也会误判

[MobileUse, NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/3994410d63ec68ce9a66011a34c9a2c4-Abstract-Conference.html) 的 hierarchical reflection 修正 18 个失败任务，correction rate 30.51%，同时 misjudgment 为 7.02%。论文还展示 hallucination-induced reflection 会诱发后续错误。

这支持“自然语言自检不是可靠证据”。

## 2.5 为什么该问题重要：风险并非普通 task failure

普通 benchmark 将以下结果都记为一次失败：

- 点击坐标错误后超时；
- 错发邮件；
- 覆盖错误文件版本；
- 提交错误账户的订单；
- 删除无法恢复的远端数据。

但它们的真实损失完全不同。高风险 GUI 控制需要的是 action-dependent threshold：

$$
\Pr(P_a(S)=1\mid E)\ge 1-\alpha(a)
$$

或：

$$
\mathbb{E}[L(a,S)\mid E]\le\lambda_a
$$

相同的不确定性，对“展开菜单”可以接受，对“发送/支付/删除”可能不可接受。这是一般 global belief accuracy 无法自动回答的决策问题。

## 2.6 Q1 最终判词

### 已证明

1. observation aliasing 和 delayed dependency 下需要 action-sufficient state；
2. 结构化状态与 observation-driven belief revision 对长程 GUI 成功率有大幅因果贡献；
3. post-action verification 与 recovery 有效但远非完美；
4. 高风险动作需要把错误概率与非对称损失共同纳入决策。

### 未证明

1. 剩余长程失败主要来自缺少 action-specific proof obligation；
2. 显式 contract 优于等容量、等预算的 verified belief state；
3. 所有 memory 都必须可证伪；
4. contract 能改变无界 Bayes-optimal Agent 的信息上界。

### 最安全的问题陈述

> **长程 GUI Agent 已能维护可被 observation 修正的结构化 belief；未决问题是，在高损失或不可逆动作发生前，当前证据是否足以授权该动作，以及证据不足时是否值得主动取证或拒绝提交。**

---

# 3. 问题二：为什么现有方法仍不够？

## 3.1 先否决一个错误论证

不能因为每篇论文单独缺一部分，就推出现有能力的组合无法解决问题：

$$
\forall i,\ M_i\text{ 不完整}
\not\Rightarrow
\bigcup_i M_i\text{ 无法解决}
$$

反方构造的最强 SOTA-Composite 已经覆盖原 contract 的几乎所有字段：

| 所需能力 | 2024–2026 prior art |
|---|---|
| program variables、control/data dependency、global belief revision | [AgentProg, MobiSys 2026](https://www.sigmobile.org/mobisys/2026/program/) |
| UI / workflow drift 下的 memory evolution | [MAGNET, ACL 2026](https://aclanthology.org/2026.acl-long.1299/) |
| critical action 执行前拦截 | [InferAct, EMNLP 2025](https://aclanthology.org/2025.emnlp-main.12/) |
| pre-execution review 与 negative warning | [MaDS, ACL 2026](https://aclanthology.org/2026.acl-long.1202/) |
| post-action effect verification | [BacktrackAgent, EMNLP 2025](https://aclanthology.org/2025.emnlp-main.212/)；MobileUse |
| compensation 与 rollback | [LongHorizonUI, ICLR 2026](https://openreview.net/pdf?id=BK7Mk5d4WE) |
| typed trusted state、Hoare pre/postcondition、verified commit | [ToolGate, ACL Findings 2026](https://aclanthology.org/2026.findings-acl.470/) |

尤其是 ToolGate 已经正式提出：

$$
\{P\}\ a\ \{Q\}
$$

- precondition $P$ gate 工具是否可调用；
- postcondition $Q$ gate 结果是否可写入可信状态；
- 只有 verified execution 才能推进 symbolic state。

因此，“首次让 Agent 使用 pre/postcondition action contract”已被 prior art 直接覆盖。

## 3.2 信息论下界：现有内部推理何时必然无效

对候选动作 $a$，存在两个隐藏状态：

$$
s^+:P_a(s^+)=1,\qquad s^-:P_a(s^-)=0
$$

Agent 在 commit 时可访问的表示为 $M$。定义两状态在表示上的 total variation distance：

$$
\eta=TV(P(M\mid s^+),P(M\mid s^-))
$$

等先验下，任何依据 $M$ 判断前置条件是否成立的最小 Bayes error 为：

$$
e^*=\frac{1-\eta}{2}
$$

若错误提交产生不可恢复损失 $L$，任何直接 commit 策略的期望不可恢复损失存在下界：

$$
\mathbb{E}[\text{loss}]\ge L\frac{1-\eta}{2}
$$

对任何不获取新 observation 的变换 $f(M)$，数据处理不等式意味着其状态可分性不能超过原表示。因此，仅对相同 evidence 做：

- retrieval；
- summary；
- reflection；
- multi-agent debate；
- 更长 CoT；
- 多次投票；

都不能从原则上突破该下界。它们可以更好利用已有信息，但不能创造缺失的环境信息。

真正能降低下界的只有：

1. commit 前获取使 $\eta$ 增大的新证据；
2. abstain 或请求用户/外部确认；
3. 选择安全、可逆的替代动作；
4. 把动作变成 dry-run、transaction 或 atomic check-and-commit。

**Contract 本身也不能突破该定理。它只能暴露证据缺口并触发这些选择。**

## 3.3 六类现有方法的根本边界

| 方法类别 | 已解决 | 根本边界 | Contract 是否直接可解 |
|---|---|---|---|
| similarity / learned retrieval | 找到语义相关经验 | 相似不蕴含当前 action precondition compatible；旧经验可能同样相似但作用域不同 | 只有原始证据存在而 retrieval 丢失时可能改善 |
| summary / flat belief | 降低 token 与视觉历史成本 | 固定预算必有 compression collision；已删除的远期依赖不能被后续推理创造 | 可改善选择性保留，不能突破容量下界 |
| reflection / debate | 纠正部分计算或推理错误 | 同一错误 observation 上的共识不增加互信息 | 只有触发新环境证据才改变信息条件 |
| post-action verifier | 检测已发生的 effect mismatch | 对发送、支付、覆盖、发布等首次损失已太晚；纯视觉还可能看不到后台 effect | 只能前置预防，不能事后创造逆操作 |
| rollback | 恢复部分 UI / program state | 非单射或外部动作没有一般逆映射；compensation 不等于 rollback | 可记录 recoverability，但不能创造不存在的 inverse |
| program / evolving memory | 保留计划变量、适应 workflow drift | schema 可能遗漏未知变量；历史频率不能证明当前事实为真 | 只能在 predicate family 覆盖真实依赖时工作 |

## 3.4 四种失败必须分开

| 失败类型 | 定义 | 研究解法 |
|---|---|---|
| 信息不足 | 可用 history / observation 对关键状态完全无区分力 | 新传感器、API、人工确认、abstain；contract 无法推断真值 |
| 表示不足 | 原始证据能区分，但压缩、检索或 schema 把状态合并 | action-relevant state selection / contract 可能修复 |
| 决策规则不足 | 证据已存在，但 policy 没按动作损失使用 | risk-calibrated gate 可能修复 |
| 动力学不足 | 错误动作不可逆、无 recovery action | 只能预防、补偿或改变执行接口 |

如果论文不区分这四类，就会把 perception、memory、planning、risk 和 environment semantics 混为一谈。

## 3.5 现有证据到底证明了什么“不足”

### 已直接证明

- BacktrackAgent 的 verifier recall 43.58%、检测后恢复 38.93%，说明 post-action pipeline 覆盖有限。
- MobileUse 仅修正 30.51% 的失败任务且有 7.02% misjudgment，说明 reflection 不天然可靠。
- LongHorizonUI rollback 仍有约 27%–30% 触发案例未恢复。
- GUI-Rise 的 summary reward 主要看下一步 action correctness，方法目标没有直接监督更远 $t+k$ 的 delayed dependency。[GUI-Rise, NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/f144ab9985c739a5091ec188a2688644-Abstract-Conference.html)

### 仅仅“尚未评测”

- AgentProg 是否会在每个高风险动作前稳定触发足够的 active verification；
- UI-Copilot retrieved fact 的 provenance、freshness 与 action applicability；
- MaDS 在所有 debater 共享 stale / false premise 时的表现；
- MAGNET 面对“高频但已失效”的 memory；
- LongHorizonUI 是否恢复真实跨应用语义状态；
- SOTA-Composite 在等模型、等 token、等 tool call、等 latency 下的整体能力；
- probabilistic GUI contract 是否优于 AgentProg GBS + ToolGate。

这些不能写成“论文已经证明会失败”。

## 3.6 真正保留的最小 gap

ToolGate 的逻辑安全依赖 typed trusted state 与已知 contract。但 GUI 的关键问题发生在此之前：

$$
\hat P_a=1\not\Rightarrow P_a(S)=1
$$

即内部 symbolic precondition 为真，不代表真实 GUI 世界的前置条件为真。如果 state 来自过期截图、错误 OCR、不完整 program、共享错误 debate 或 stale memory，形式系统可以对错误世界模型做出完全正确的逻辑证明。

因此剩余 gap 不是 contract expressivity，而是：

> **Open-world, risk-calibrated epistemic commit control：在像素观测、隐藏状态、跨应用 effect 与 UI drift 下，校准某个动作前置条件的真实违例概率，并成本敏感地选择 execute、主动 probe、safe alternative、abstain 或 human confirmation。**

现有方法拥有所需组件，原则上也可能被训练成这套策略；但没有工作联合优化并受控评测：

- 哪个未知事实导致当前动作风险；
- 哪个 probe 最能区分候选状态；
- 其信息价值是否高于成本；
- 证据不足时应执行、验证还是拒绝；
- 如何在 unseen app、UI drift 和 TOCTOU 下保持 calibration。

## 3.7 Q2 最终判词

### 可以声称

> 现有 2024–2026 工作已覆盖结构化状态、belief revision、执行前检查、执行后验证、memory evolution、rollback 以及符号 contract gate；尚未被联合验证的是：这些机制能否对真实 GUI 环境证据进行动作级风险校准，并选择具有正决策价值的 pre-commit probe。

### 不能声称

- 现有方法没有可证伪 belief；
- 现有方法没有 pre-action verification；
- action contract 是新的表示范式；
- SOTA 原则上不能主动验证；
- 新增一个 JSON / graph contract 就构成能力突破。

---

# 4. 问题三：为什么 revised idea 可能可行？

## 4.1 先限定“可行”的含义

必须区分：

1. **存在性：**在明确假设下，是否存在严格优于固定策略的 authorization + probe policy？
2. **Stage-0 可验证性：**能否在不开发完整方法前，用 oracle 检查真实任务是否有足够 headroom？
3. **可学习性：**模型能否从有限数据学到 predicate、posterior 和 probe value？
4. **可泛化性：**能否跨 app、时间与 UI 版本保持 calibration？

当前只证明了 1，并为 2 建立了实验路径；3 和 4 尚未证明。

## 4.2 建设性存在证明一：risk-calibrated gate

对候选动作 $a$，设隐藏变量：

$$
\theta=P_a(S)\in\{0,1\}
$$

给定 evidence $X$：

$$
p=\Pr(\theta=1\mid X)
$$

正确执行收益为 $R$，错误执行损失为 $L$，abstain / safe alternative 的价值为 $V_z$。执行的期望效用：

$$
V_e(p)=pR-(1-p)L
$$

Bayes-optimal gate：

$$
execute\iff p\ge\tau=\frac{L+V_z}{R+L}
$$

该策略对任意固定执行、固定阻断或不匹配损失的固定 threshold 策略弱优；只要 baseline 在一个正概率集合上采取了唯一非最优动作，就严格更优。

它证明：**若 posterior 可获得且不同动作具有异质损失，risk-aware authorization 存在严格价值。**

## 4.3 建设性存在证明二：active probe 的价值

设 probe $q$ 的成本为 $c_q$，返回新 observation $Y$，posterior 更新为 $p_Y$。定义 Expected Value of Sample Information：

$$
EVSI(q)=
\mathbb E_Y[\max\{V_e(p_Y),V_z\}]
-\max\{V_e(p),V_z\}
$$

由于新信息可以被忽略：

$$
EVSI(q)\ge0
$$

probe 严格提高净效用需要：

1. observation 以正概率让 posterior 穿越 commit threshold；
2. $EVSI(q)>c_q$。

这解释了为什么“每步都验证”不是正确方法：有 mutual information 但不能改变决策的 probe 没有行动价值；成本高于风险降低的 probe 反而降低总效用。

## 4.4 组件级可行性证据

| 子能力 | 2024–2026 证据 | 可支持的结论 |
|---|---|---|
| observation-driven belief revision | AgentProg：GBS 在 AW-Extend 带来 33.3 点、AndroidWorld 带来 24.1 点 | 有限 GUI Agent 能从环境反馈持续修正结构化状态 |
| critical-action preemption | InferAct：critical misalignment detection 相对 baseline 最高提升约 20 Macro-F1 点 | 执行前风险识别可被学习 |
| symbolic pre/postcondition gate | ToolGate：typed state、Hoare gate、verified state update | contract-driven commit control 可被工程实现 |
| selective verification | MobileUse：省略约 85% reflection 时成功率下降不足 1.5%，hierarchical reflection 仍带来明显增益 | 验证存在稀疏调度空间，不必 every-step |
| effect anomaly detection | BacktrackAgent：precision 75.12%，recall 43.58% | 环境结果中存在可学习的异常信号 |
| partial recovery | BacktrackAgent +7.59 点；LongHorizonUI rollback 成功约 70% | 部分错误可被检测和恢复，但非普适 |
| selective memory acquisition | UI-Copilot：AndroidWorld 22.0→39.1 | 按需检索可以明显改变任务表现 |

这些数据证明所需组件不是不可实现的；它们不能证明端到端 joint policy 可学，也不能把各论文增益简单相加。

## 4.5 该 idea 可能失败的根本原因

1. **Unknown unknown。** 若真实依赖变量不在 contract schema，系统不会为它选择 probe。
2. **不可识别状态。** 若所有安全 probe 在 $s^+,s^-$ 下同分布，任何 GUI-only 方法无解。
3. **TOCTOU。** 验证时为真，不代表 commit 时仍为真；需要 atomic check-and-act、version token 或承认 best-effort。
4. **Probe recursion。** probe 本身可能有副作用并需要另一个 probe；必须有 trusted read-only probe set 或有限深度 + human fallback。
5. **过度拒绝。** 永不执行可得到零 unsafe commit；必须同时约束 coverage 和 necessary-action recall。
6. **模块相关错误。** 相同 VLM、截图和 stale memory 驱动的多个 judge 可能一致地错。
7. **错误 contract 传播。** persistent memory 可能把低频错误 obligation 放大到未来任务。
8. **恶意环境证据。** [Popup attack, ACL 2025](https://aclanthology.org/2025.acl-long.411/) 报告平均 attack success 86%、task success 下降 47%，说明 UI observation 不是天然可信来源。
9. **成本。** BacktrackAgent 的速度约下降 50%，risk、probe、gate 和 verifier 叠加可能吞掉收益。
10. **人或事务接口可能更优。** 对极少数不可逆动作，human approval、dry-run、idempotency key、transaction 可能形成更好的 safety–utility frontier。

## 4.6 Stage-0：先证明问题有 headroom，再做方法

### Stage-0A：自然失败覆盖率审计

先从 AndroidWorld / AW-Extend、LongGUIBench、OSWorld 等真实轨迹中盲标：

1. failure 前是否存在 action-specific hidden uncertainty；
2. 是否存在部署时可访问的安全 probe；
3. probe 是否可能改变正确 commit decision；
4. probe 是否比 human confirmation 更便宜；
5. 根因是否确为 evidence insufficiency，而非 grounding / planning。

估计自然覆盖率：

$$
\rho=P(\exists q:EVSI(q)>c_q\mid\text{高风险 residual failure})
$$

如果该比例极低，定理即使成立，研究价值也有限。

### Stage-0B：3×3×3 因果任务设计

| 因子 | 水平 |
|---|---|
| dependency distance | ≤5、10–20、≥30 步 |
| state observability | 当前可见、可由 probe 揭示、GUI 内不可观察 |
| consequence | UI 可回退、语义可补偿、不可逆 |

共 27 个 cell。建议最低：每个 cell 4 个独立任务族，共 108 个模板；每个模板生成 precondition true / false 的 matched pair，并做重复随机执行。正式样本量应根据 pilot 的配对不一致率做 power simulation。

必须包含的压力干预：

- stale memory；
- omitted prerequisite；
- conflicting provenance；
- UI / semantic drift；
- decoy probe；
- delayed / cross-app postcondition；
- verify–commit 间 TOCTOU；
- reversible / compensatable / irreversible effect。

### Stage-0C：强基线

- SOTA-Composite：AgentProg-style state + retrieval + pre-action critic + effect verifier + rollback；
- equal-compute reflection；
- generic calibrated risk gate，无 explicit predicates；
- AgentProg + MaDS；
- ToolGate-GUI：手工 contract + GUI state extractor；
- fixed verify-before-commit；
- ask-user / human confirmation；
- 全部系统匹配 backbone、context、probe、tool call、token、latency 与可观测信息。

### Stage-0D：Oracle Ladder

| 层级 | Oracle 能力 | 回答的问题 |
|---|---|---|
| O0 | Matched SOTA-Composite | 当前最强基线 |
| O1 | commit 时真实 action risk / loss | 是否只缺 risk detector |
| O2 | 精确 pre/postcondition dependency，不给真值 | contract specification 是否有独立价值 |
| O3 | current evidence 下真实 posterior | 不增加 probe 时 calibration / gate 上限 |
| O4 | 最佳安全 probe，扣除真实成本 | active evidence acquisition 是否有净价值 |
| O5 | grounded contract + 当前 predicate truth / unknown | commit control 上限 |
| O6 | 真实 semantic outcome / delayed effect | postcondition observability 瓶颈 |
| O7 | 最佳 compensation / recovery | recovery 上限 |
| O8 | atomic check–commit | TOCTOU 损失上限 |

最关键的差值：

- O1 − O0：authorization 总 headroom；
- O3 − O0：当前 evidence 下只靠 calibration 能回收多少；
- O4 − O3：主动 probe 的净增益；
- O8 − O4：TOCTOU 造成多少不可消除损失。

## 4.7 主要指标与中介机制

### Primary metrics

- severity-weighted unsafe commit rate；
- task completion / necessary-action recall；
- normalized expected utility；
- Bayes decision regret；
- risk–coverage–cost Pareto frontier；
- false block / over-abstention；
- matched-budget success、token、tool call 与 wall-clock latency。

### 必须验证的中介链

```text
必要前置条件召回提高
→ 选择更具区分力的安全 probe
→ 状态可分性 η 提高
→ posterior calibration 改善并正确跨越 threshold
→ matched hidden states 得到不同且正确的 commit 决策
→ unsafe commit 降低
→ 扣除成本与人工负担后净效用提高
```

对应中介指标：

- contract dependency precision / recall；
- omitted-prerequisite detection；
- true / false / unknown macro-F1；
- provenance / freshness accuracy；
- Brier、ECE、reliability diagram；
- discriminative-probe rate、decoy-probe rate；
- 实测 $\Delta\eta$、threshold-crossing rate、EVSI sign accuracy；
- postcondition false accept / false reject；
- semantic recovery residual；
- TOCTOU invalidation rate。

若 final success 提升但这条机制链不成立，不能把收益归因于 epistemic commit control。

## 4.8 Go / No-Go 预注册门槛

以下数值是项目决策阈值，不是文献既有事实。

### Conditional Go → Full Go

同时满足：

1. 自然失败审计中至少 20% 的高风险 residual failures 存在部署可访问、正 EVSI 的安全 probe；
2. full oracle 相对 SOTA-Composite 在 normalized utility 上提升至少 0.10，或高损失 unsafe commit 相对下降至少 50%；
3. oracle probe 对 aliased cases 使 unsafe commit 至少下降 30% relative 或 10 点 absolute；
4. contract / obligation 相比 generic risk gate 仍有至少 5 点成功率或 25% unsafe-commit relative gain；
5. 关键前置条件 recall 至少 80%；
6. learned probe 平均使 $\eta$ 提高至少 0.20；
7. benign completion 下降不超过 3 点，false block 不超过 5%；
8. 平均额外成本不超过 20%；
9. unseen app / unseen obligation 保留至少 70% 的安全收益；
10. 收益随 horizon 和 action loss 显著增强；
11. 删除 contract 但保留同次数 probe 后，收益显著下降；
12. AgentProg + ToolGate + generic verification 不能达到相同 frontier。

### No-Go

任一核心条件出现即停止或改题：

- 自然轨迹中可利用机会 $\rho<10\%$；
- O1 / full-state oracle 相比强基线几乎没有 headroom；
- oracle probe 改善不足 5 点；
- generic risk gate 或 generic inspect 获得超过 80% 的 oracle 增益；
- ToolGate-GUI 已达到 oracle 大部分性能；
- learned obligation recall 低于 70%；
- selected probe 不提高 $\eta$ 或净 $EVSI\le0$；
- 安全收益完全由 abstention / human escalation 解释；
- false block 超过 10%，或 benign completion 损失大于安全收益；
- 匹配 token、tool、latency 后收益消失；
- 加入 TOCTOU 后优势消失；
- 只有 privileged OS/API hidden state 才有效；
- unseen app 上收益保留不足一半；
- human approval 在相同用户负担下有更好的 frontier。

## 4.9 Q3 最终判词

### 现在可以写

> 2024–2026 工作分别证明了 GUI belief revision、critical-action detection、pre-execution review、symbolic pre/postcondition gate、post-action checking 和 partial recovery 的独立可行性。决策论进一步表明：当 action evidence 能使 posterior 穿越风险相关的 commit threshold，且 probe 的 EVSI 大于成本时，风险校准 gate 与主动取证能严格改善动作选择。因此，该方向具有条件性存在证明和清晰的 Stage-0 证伪路径。

### 现在不能写

> 我们的方法能够解决开放世界长程 GUI Agent 的核心问题。

因为还没有证明：

- contract 能覆盖 unknown unknown；
- GUI evidence 能可靠校准 posterior；
- 正 EVSI probe 在自然失败中具有足够覆盖率；
- check 在 commit 时仍有效；
- 收益不是额外 compute、过度拒绝或 ToolGate 迁移造成的；
- oracle gap 能被 learned policy 回收并跨 app 泛化。

---

# 5. 最终推荐方向

## 5.1 推荐研究问题

> **Can a GUI agent learn to acquire the minimum environment evidence needed to authorize an irreversible action, under calibrated risk and equal verification budgets?**

中文：

> **在相同可观测性和验证预算下，GUI Agent 能否学习：为不可逆动作发现尚未证实的必要前提，选择最具决策价值的安全环境 probe，并以校准风险决定提交、继续验证或拒绝？**

## 5.2 暂定论文标题

**When Is It Safe to Click? Risk-Calibrated Epistemic Commit Control for Long-Horizon GUI Agents**

备选：

**Before You Commit: Active State Disambiguation for Irreversible GUI Actions**

## 5.3 第一性科研链条

```text
重要问题
长程 GUI 中，同一当前 observation 可能对应不同隐藏状态；错误 commit 具有非对称且不可逆损失
↓
根本原因
提交时的表示没有证明它能区分“动作前置条件成立/不成立”，内部推理不能创造缺失环境信息
↓
现有方法局限
已有 belief、debate、verifier、rollback 和 contract gate，但缺少对真实 GUI evidence 的联合风险校准与成本敏感主动取证评测
↓
先验可行性
Bayes gate 与 EVSI 给出条件性严格收益；2024–2026 论文证明各子组件可实现
↓
Stage-0 证伪
自然失败覆盖率 + paired causal tasks + SOTA-Composite + Oracle Ladder + risk–coverage–cost frontier
↓
进入方法研究的条件
存在显著 oracle headroom，active probe 有正净价值，learned policy 能在等预算下回收 gap 且不过度拒绝
```

## 5.4 目标贡献应该是什么

若 Stage-0 通过，顶会级贡献不能是“新增一个 memory module”，而应至少包含：

1. 一个从自然失败出发、能分离 risk、observability、probe value、TOCTOU 与 irreversibility 的诊断 benchmark；
2. 一个 risk-conditioned active disambiguation objective，而不是固定频率 verifier；
3. 一条被中介指标验证的因果机制链，而不是只看 task success；
4. 与 AgentProg、InferAct、MaDS、ToolGate、BacktrackAgent、LongHorizonUI 的等预算强组合比较；
5. 明确的适用边界：相对于声明的 predicate family、evidence channel、trusted probe set 和 environment family，而非开放世界绝对安全。

## 5.5 最终研究判断

| 维度 | 评级 | 原因 |
|---|---:|---|
| 问题重要性 | 4/5 | 长程退化和不可逆错误有强相邻证据，但自然 failure coverage 尚未测 |
| 理论清晰度 | 5/5 | 可形式化 action-evidence 下界、Bayes gate、EVSI 与 selective risk |
| 表示新颖性 | 1/5 | AgentProg + ToolGate 已覆盖大部分 contract 表示 |
| 学习问题新颖性 | 4/5 | open-world predicate grounding + risk-conditioned probe selection 尚未被联合解决 |
| 实现难度 | 5/5 | 标注、simulator、TOCTOU、calibration、跨 app 都很难 |
| 实验可证伪性 | 5/5 | Oracle Ladder 和明确 No-Go 条件可提前否决 |
| 当前决策 | **Conditional Go** | 先做 Stage-0，不直接设计大而全方法 |

最终严谨表述：

> **长程 GUI Agent 的 memory 不必在表示上“都成为行动契约”。真正需要研究的是：在有限上下文与部分可观测环境下，Agent 能否维持对当前动作充分的证据状态，并在不可逆 commit 前以风险和成本为条件主动消除关键状态歧义。Contract 可以是可审计的控制接口，但能力增益必须来自新证据、正确校准与更优决策，而不是重新命名 memory。**

---

# 6. 2024–2026 官方来源索引

## 2024

- [OSWorld — NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/hash/5d413e48f84dc61244b6be550f1cd8f5-Abstract-Datasets_and_Benchmarks_Track.html)
- [ICAL — NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/hash/8ac50fd0a4eeeb1f077b17bb7c5353c3-Abstract-Conference.html)

## 2025

- [GUI-Rise — NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/f144ab9985c739a5091ec188a2688644-Abstract-Conference.html)
- [MobileUse — NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/3994410d63ec68ce9a66011a34c9a2c4-Abstract-Conference.html)
- [BacktrackAgent — EMNLP 2025](https://aclanthology.org/2025.emnlp-main.212/)
- [InferAct — EMNLP 2025](https://aclanthology.org/2025.emnlp-main.12/)
- [Attacking Vision-Language Computer Agents via Pop-ups — ACL 2025](https://aclanthology.org/2025.acl-long.411/)

## 2026

- [AgentProg — MobiSys 2026](https://www.sigmobile.org/mobisys/2026/program/)
- [UI-Copilot — ACL 2026](https://aclanthology.org/2026.acl-long.904/)
- [MaDS — ACL 2026](https://aclanthology.org/2026.acl-long.1202/)
- [MAGNET — ACL 2026](https://aclanthology.org/2026.acl-long.1299/)
- [LongHorizonUI — ICLR 2026](https://iclr.cc/virtual/2026/poster/10010959)
- [MMBench-GUI — CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Wang_MMBench-GUI_A_Unified_Hierarchical_Evaluation_Framework_for_Multi-Platform_GUI_Agents_CVPR_2026_paper.html)
- [MobileBench-OL — ACL Findings 2026](https://aclanthology.org/2026.findings-acl.668/)
- [ToolGate — ACL Findings 2026](https://aclanthology.org/2026.findings-acl.470/)
