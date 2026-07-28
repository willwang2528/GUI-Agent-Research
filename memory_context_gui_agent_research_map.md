# Memory / Context for GUI Agent：2024–2026 高质量科研地图与研究缺口

> 修订日期：2026-07-21  
> 严格核心时间窗：**2024、2025、2026**  
> 目标：不是综述论文，而是从第一性原理发现可投稿 CCF-A / CCF-B 的新问题。  
> 证据规则：论文信息优先采用会议官网、ACL Anthology、CVF、ICLR、NeurIPS、PMLR、ACM/SIGMOBILE 与 DOI；2026 是正在进行的自然年，引用量只作动态记录，不参与质量判断。

## 0. 本次修订与硬约束

本报告保留原任务的全部要求，并增加三项硬约束：

1. **核心论文池、Top Papers Table、主要论证和最终方向只使用 2024–2026 正式发表论文。**
2. 2023 及更早论文只允许作为“概念来源”在背景中一句带过，不进入核心论文池、不用于证明“当前 SOTA 的局限”。
3. 每篇论文不按摘要复述，而按第一性原理回答：它改变了长程 GUI 控制的哪个必要条件？它保留了什么信息、丢掉了什么信息？在何种反例下仍必然失败？

---

# Part 1: Research Landscape

## 1.1 第一性原理：GUI Agent 的 Memory 到底要解决什么

把 GUI Agent 看成部分可观测控制系统：

```text
hidden environment state: s_t
visible observation:       o_t = Observe(s_t)
agent action:              a_t
state transition:          s_(t+1) ~ T(s_t, a_t)
task goal:                 g
memory state:              m_t = Update(m_(t-1), o_t, a_(t-1))
policy:                    a_t = Policy(g, o_t, m_t)
```

当前截图 `o_t` 通常不是完整状态 `s_t`：它不显示早先填写的值、已关闭页面、账号/权限、后台下载、跨应用副作用、剪贴板内容、隐藏选中项和异步任务。因此 memory 的本质不是“保存聊天记录”，而是用有限预算构造一个对未来决策足够的状态：

```text
在预算 B 下，m_t 应尽可能保留 P(s_t | o_1, a_1, ..., o_t) 中
会改变未来最优动作的部分，并能区分 observed / inferred / stale / uncertain。
```

一个长程 GUI Agent 至少需要满足六个必要条件：

| 必要条件 | 第一性问题 | 缺失后的必然失败 |
|---|---|---|
| State Sufficiency | memory 是否保留了决定未来动作的状态变量？ | 延迟依赖被遗忘，计划在后期无信息可用 |
| Bounded Context | 是否能在固定 token/latency 下工作？ | 轨迹增长导致截断、位置偏差和成本爆炸 |
| Temporal Validity | 记忆是否仍适用于当前 app/version/account/state？ | 旧流程或旧事实被错误复用 |
| Causal Compatibility | 被检索经验的前置条件是否与当前状态相同？ | 语义相似但因果条件不同，产生负迁移 |
| Verification | 推断、摘要和反思能否回到真实 observation 校验？ | 一次错误写入污染后续全部决策 |
| Recovery | effect 不符合预期时能否定位破坏的状态并补偿？ | 长任务成功率随步骤数乘法下降 |

这六项共同决定 Memory / Context 方法是否真正改变能力边界。只增加向量库、摘要器或反思 prompt，通常只优化其中一项。

## 1.2 2024–2026 领域地图

```text
Memory / Context for GUI Agent
|
|-- 2024: 从“看懂界面”走向“保存与复用经验”
|   |-- General computer benchmark: OSWorld
|   |-- Visual grounding foundation: CogAgent, SeeClick
|   |-- App/procedural memory: MobileGPT
|   |-- Abstracted episodic memory: ICAL
|   `-- Context compression / latent state: LongLLMLingua, Memoroids
|
|-- 2025: Memory 进入训练与分层控制回路
|   |-- Experience-augmented planning: Agent S
|   |-- Learned recursive history: GUI-Rise
|   |-- Multi-level reflection: MobileUse
|   |-- Dynamic linked memory: A-Mem
|   `-- Multimodal token/history efficiency: ShowUI
|
`-- 2026: 从“是否使用 memory”走向“memory 应如何组织和调用”
    |-- Program + belief-state context: AgentProg
    |-- UI-drift-aware evolving memory: MAGNET
    |-- Persistent/transient decoupling + on-demand tool: UI-Copilot
    |-- Positive/negative memory + pre-action debate: MaDS
    |-- Reflection + compensation + rollback: LongHorizonUI
    |-- Lossless optical archive: OCR-Memory
    |-- Long-term user intent memory: PersonalAlign
    `-- Multi-platform and human-centric evaluation: MMBench-GUI, Computer Agent Arena
```

## 1.3 发展时间线与真正的能力变化

| 年份 | 表面趋势 | 第一性变化 | 仍未闭合的必要条件 |
|---|---|---|---|
| 2024 | GUI benchmark、grounding、experience memory 兴起 | Agent 开始把过去交互变成可复用的 app knowledge、procedure 或抽象经验 | 经验相似不等于当前状态因果兼容；完整历史无法扩展 |
| 2025 | 历史摘要、分层反思、结构化 memory 被训练 | memory 从外部插件进入 planner/actor 的闭环，开始显式优化 context 成本 | 摘要偏短期效用；反思可能幻觉；事实没有明确有效期和证据 |
| 2026 | 程序化 context、belief state、UI 漂移、按需检索、回退 | 研究开始分离 persistent/transient information，并用程序变量、稳定语义、负面经验与 verifier 组织记忆 | 仍缺统一的 causal contract：哪些事实是未来动作的必要前提、为何仍成立、冲突时应验证什么 |

2026 的 AgentProg、MAGNET、UI-Copilot 和 MaDS 说明，“给 Agent 加 memory”已不是新问题。新的论文必须解释 memory 的**充分性、真实性、有效性与可证伪性**。

## 1.4 GUI Agent 为什么需要 Memory / Context

### Why 1：为什么重要？

1. 当前截图只是局部 observation，不是任务状态。
2. 第 2 步出现的约束可能到第 30 步才决定动作，产生 delayed dependency。
3. GUI 动作会改变环境；提交、删除、覆盖和发送可能不可逆。
4. 两个视觉相似页面可能对应不同账号、权限、对象或后台状态，即 state aliasing。
5. 跨 app 任务必须持续追踪实体与副作用，不能靠单帧 grounding 重建。
6. 任务越长，单步可靠性相乘；即使每步 97% 正确，50 步全对概率也只有约 21.8%。

OSWorld 把研究推进到真实桌面环境；2026 的 MMBench-GUI 进一步显示复杂、跨应用任务仍在 memory、planning 和 adaptive reasoning 上显著退化。[OSWorld](https://proceedings.neurips.cc/paper_files/paper/2024/hash/5d413e48f84dc61244b6be550f1cd8f5-Abstract-Datasets_and_Benchmarks_Track.html)；[MMBench-GUI](https://openaccess.thecvf.com/content/CVPR2026/html/Wang_MMBench-GUI_A_Unified_Hierarchical_Evaluation_Framework_for_Multi-Platform_GUI_Agents_CVPR_2026_paper.html)

### Why 2：为什么仅扩大 context window 不够？

- 容量大不代表模型会使用位于中间的关键事实。
- 原始截图/DOM 随 horizon 线性增长，无关信息也同步增长。
- 旧事实可能已失效；无限 context 只会让真旧状态与新状态共同存在。
- 模型仍需判断“哪条历史是当前动作的因果前提”，这不是容量问题。

### Why 3：为什么新的 Memory 架构可能解决？

如果 memory 从“历史容器”变成以下控制接口：

```text
fact + provenance + confidence + valid scope
action precondition + expected effect
future dependency + invalidation rule
```

那么 agent 才能在有限预算下保留真正决定未来动作的信息，并在事实过期、矛盾或 effect 不符时主动验证和恢复。

## 1.5 可迁移思想与迁移边界

| 领域 | 可迁移原理 | 不能直接照搬的原因 |
|---|---|---|
| POMDP / Robotics | belief state、主动感知、状态估计、闭环校正 | GUI observation 是开放词汇语义对象，且 LLM 会产生语言化伪状态 |
| Program Analysis | 变量、控制流、data dependency、backward slicing | GUI task program 不完整且运行时会出现计划外事件 |
| RL | long-term credit、replay、value of information、failure recovery | GUI 奖励稀疏，真实在线采样昂贵，不可逆动作代价高 |
| RAG / Graph RAG | provenance、多跳关系、冷/热存储 | 文档相关性不等于动作前置条件满足，GUI 事实还会随时间失效 |
| World Model | action effect、反事实、规划 | 纯 LM rollout 会幻想不存在的 UI 状态，必须由真实 observation 校正 |
| Database / Event Sourcing | version、event log、materialized state、rollback | GUI 实体 identity 与动作 effect 不总能被 API 精确观察 |

---

# Part 2: Top Papers Table

## 2.1 严格筛选标准

```text
年份是否为 2024 / 2025 / 2026？
  └─ 否：移出核心池，只能作为历史背景
      是
      ↓
是否正式发表于 CCF-A/B 或高影响力期刊？
  └─ 否：标记观察，不作为核心证据
      是
      ↓
是否改变 GUI / agent memory / context / long-horizon 的关键机制？
  └─ 否：标记 incremental 或 unrelated
      是
      ↓
能否映射到六个必要条件中的至少一个？
  └─ 否：不进入核心池
      是：进入核心论文池
```

## 2.2 Top Papers Table

| Paper | Venue | Year | 第一性问题 | 核心干预 | 尚未解决的根因 | GUI Research Opportunity |
|---|---|---:|---|---|---|---|
| OSWorld | NeurIPS D&B (A) | 2024 | 如何真实测量 computer-use 能力 | 跨 app 可执行环境与 369 个任务 | 总成功率不能诊断 memory omission/staleness | 构建 memory-specific interventions |
| MobileGPT | MobiCom (A) | 2024 | 如何避免每个 app/task 从零探索 | app exploration + hierarchical procedure memory | procedure 缺少版本、前置条件和在线校验 | versioned skill contracts |
| ICAL | NeurIPS (A, Spotlight) | 2024 | 原始 demonstration 如何变为可复用经验 | 抽取因果、状态变化、子目标与视觉证据 | retrieval similarity 不保证当前 precondition 满足 | causal compatibility retrieval |
| LongLLMLingua | ACL (A) | 2024 | 长文本 context 如何降成本并减轻位置偏差 | query-aware compression + reorder | 当前 query relevance 不等于未来 action value | multi-horizon context utility |
| Recurrent RL with Memoroids | NeurIPS (A) | 2024 | 部分可观测轨迹如何形成 latent Markov state | monoid 形式的 recurrent memory | 不处理开放 GUI 语义、事实 provenance 与 drift | 可组合 belief update 理论 |
| Agent S | ICLR (A) | 2025 | computer-use 如何复用经验并层级规划 | narrative/episodic memory + hierarchical planning | 经验可能 stale，缺少状态兼容验证 | verified experience graph |
| GUI-Rise | NeurIPS (A) | 2025 | 多模态历史如何压缩 | recursive history summary + RL | 主要奖励下一步，长期依赖可能被不可逆删除 | counterfactual multi-horizon summary |
| MobileUse | NeurIPS (A) | 2025 | 如何在长任务中反思和恢复 | action/trajectory/global reflection + RoD | 反思判断本身可能无证据、未校准 | uncertainty-triggered verification |
| A-Mem | NeurIPS (A) | 2025 | memory 如何动态组织和演化 | Zettelkasten links + dynamic attributes | 语义连接不表示动作因果、时效和矛盾 | temporal causal memory graph |
| ShowUI | CVPR (A) | 2025 | GUI 视觉 token 与历史如何降冗余 | UI-guided token selection + VLA streaming | 空间 token 重要性不等于跨时间依赖 | spatiotemporal action-conditioned selection |
| AgentProg | MobiSys (B) | 2026 | 长轨迹如何保留必要变量而丢弃噪声 | semantic task program + global belief state | program/schema 可能遗漏计划外未来依赖；belief 无充分校准 | open-world memory contracts |
| MAGNET | ACL (A) | 2026 | UI 更新后 memory 如何继续复用 | stationary semantic memory + procedural memory + evolution | “稳定语义/意图”是假设；频繁访问不等于正确或未过期 | falsifiable validity and drift detection |
| UI-Copilot | ACL (A) | 2026 | 哪些能力应从 actor context 中解耦并按需调用 | persistent/transient decoupling + Retriever/Calculator + TIPO | tool invocation 不证明 retrieved fact 对当前动作因果充分 | evidence-aware tool calling |
| MaDS | ACL (A) | 2026 | 如何避免 grounding error 在不可逆长任务中累积 | dual-layer memory + pre-action debate + negative warnings | debate 共识不等于真实状态；warning 泛化边界不明 | observation-grounded safety contracts |
| LongHorizonUI | ICLR (A) | 2026 | 长任务错误如何检测、补偿和回退 | indexed perception + deep reflection + compensation/rollback | 回退依赖 progress monitoring，但不显式表示被破坏的 hidden state | state-aware reversible execution |
| OCR-Memory | ACL (A) | 2026 | 如何低 token 保存长历史且避免摘要幻觉 | optical archive + locate-and-transcribe | 忠实取回不等于取回了决策所需事实；旧证据仍可能失效 | causal retrieval over lossless evidence |
| MMBench-GUI | CVPR (A) | 2026 | 如何跨平台分层评价 GUI Agent | 六平台、四层能力、EQA 指标 | 没有隔离 delayed dependency、memory contradiction 和 staleness | memory diagnostic benchmark |

## 2.3 核心论文记录与第一性原理诊断

### 2024-P1. OSWorld: Benchmarking Multimodal Agents for Open-Ended Tasks in Real Computer Environments

- **Title:** OSWorld: Benchmarking Multimodal Agents for Open-Ended Tasks in Real Computer Environments
- **Authors:** Tianbao Xie, Danyang Zhang, Jixuan Chen, Xiaochuan Li, Siheng Zhao, Ruisheng Cao, Toh Jing Hua, Zhoujun Cheng, Dongchan Shin, Fangyu Lei, Yitao Liu, Yiheng Xu, Shuyan Zhou, Silvio Savarese, Caiming Xiong, Victor Zhong, Tao Yu
- **Year / Conference / CCF Rank:** 2024 / NeurIPS Datasets and Benchmarks / A
- **URL:** [Official](https://proceedings.neurips.cc/paper_files/paper/2024/hash/5d413e48f84dc61244b6be550f1cd8f5-Abstract-Datasets_and_Benchmarks_Track.html)
- **Code URL:** [xlang-ai/OSWorld](https://github.com/xlang-ai/OSWorld)
- **Citation:** Semantic Scholar 调研快照（2026-07-21）：493
- **Research Direction:** General computer-use benchmark
- **Main Problem:** 缺少真实、跨应用、可复现的桌面任务评测。
- **Core Method:** 真实 OS 环境、369 个任务、执行式评价。
- **Why Important:** 它建立了需要 memory/planning 的真实问题空间，而非只测单屏 grounding。
- **First-Principles Diagnosis:** OSWorld 测最终控制结果，但没有干预 memory；因此相同失败可由没看到、忘记、记错、过期或执行错造成。
- **Limitation:** 不能识别 memory 的必要变量和因果贡献。
- **Potential GUI Agent Connection:** 适合作为 memory 诊断任务的母环境。
- **Possible Research Opportunity:** 对原任务注入可控依赖距离、状态别名、历史干扰、UI drift 和 action failure。

### 2024-P2. MobileGPT: Augmenting LLM with Human-like App Memory for Mobile Task Automation

- **Title:** MobileGPT: Augmenting LLM with Human-like App Memory for Mobile Task Automation
- **Authors:** Sunjae Lee, Junyoung Choi, Jungjae Lee, Munim Hasan Wasi, Hojun Choi, Steven Y. Ko, Sangeun Oh, Insik Shin
- **Year / Conference / CCF Rank:** 2024 / MobiCom / A
- **URL:** [DOI](https://doi.org/10.1145/3636534.3690682)
- **Code URL:** [hchoi256/mobilegpt](https://github.com/hchoi256/mobilegpt)
- **Citation:** 动态引用量未稳定读取
- **Research Direction:** Procedural app memory
- **Main Problem:** 每次重新探索 app 造成高成本，任务复用弱。
- **Core Method:** explore–select–derive–recall，将 app 操作组织成子任务和 primitive actions。
- **Why Important:** 证明 procedural memory 能改变适应速度，而非只增加 prompt 信息。
- **First-Principles Diagnosis:** 它把历史压成可执行 procedure，保留 control flow，丢弃大部分 observation；只有当前环境满足隐含前置条件时才可靠。
- **Limitation:** UI/version/account 变化会破坏 procedure；缺少显式 precondition/effect 与 invalidation。
- **Potential GUI Agent Connection:** 2026 AgentProg/MAGNET 的重要前序机制。
- **Possible Research Opportunity:** 让技能成为可验证、版本化的 memory contract。

### 2024-P3. VLM Agents Generate Their Own Memories (ICAL)

- **Title:** VLM Agents Generate Their Own Memories: Distilling Experience into Embodied Programs of Thought
- **Authors:** Gabriel Sarch, Lawrence Jang, Michael J. Tarr, William W. Cohen, Kenneth Marino, Katerina Fragkiadaki
- **Year / Conference / CCF Rank:** 2024 / NeurIPS Spotlight / A
- **URL:** [Official](https://proceedings.neurips.cc/paper_files/paper/2024/hash/8ac50fd0a4eeeb1f077b17bb7c5353c3-Abstract-Conference.html)
- **Code URL:** [Gabesarch/ICAL](https://github.com/Gabesarch/ICAL)
- **Citation:** 动态引用量未稳定读取
- **Research Direction:** Abstracted multimodal episodic memory
- **Main Problem:** 原始 demonstration 冗余、有噪且难以泛化。
- **Core Method:** 抽取对象状态变化、因果关系、时序子目标和相关视觉证据，形成 programs of thought。
- **Why Important:** 首次把 GUI/embodied experience 从“轨迹复制”推进到“结构抽象”。
- **First-Principles Diagnosis:** 它改善了 memory representation，但读取仍以文本/视觉相似为主；相似轨迹只提供先验，不能证明当前执行条件成立。
- **Limitation:** human feedback 成本；缺少时效、冲突和在线 verification。
- **Potential GUI Agent Connection:** 提供 causal/state-change extraction 基线。
- **Possible Research Opportunity:** 从 task similarity retrieval 改为 precondition/effect compatibility retrieval。

### 2024-P4. LongLLMLingua

- **Title:** LongLLMLingua: Accelerating and Enhancing LLMs in Long Context Scenarios via Prompt Compression
- **Authors:** Huiqiang Jiang, Qianhui Wu, Xufang Luo, Dongsheng Li, Chin-Yew Lin, Yuqing Yang, Lili Qiu
- **Year / Conference / CCF Rank:** 2024 / ACL / A
- **URL:** [ACL Anthology](https://aclanthology.org/2024.acl-long.91/)
- **Code URL:** [microsoft/LLMLingua](https://github.com/microsoft/LLMLingua)
- **Citation:** Semantic Scholar 调研快照（2026-07-21）：367
- **Research Direction:** Query-aware context compression
- **Main Problem:** 长 prompt 计算成本高且存在位置偏差。
- **Core Method:** query-aware token compression、重排和恢复。
- **Why Important:** 说明有效 context 取决于选择策略，而非窗口名义长度。
- **First-Principles Diagnosis:** 它优化“当前 query 的文本相关性”；GUI 事件价值则取决于未来动作，可能当前不相关但二十步后成为必要变量。
- **Limitation:** 缺少 action/state transition 和 multi-horizon utility。
- **Potential GUI Agent Connection:** 强 text-compression baseline。
- **Possible Research Opportunity:** 用 future control loss 而非文本 relevance 学习保留策略。

### 2024-P5. Recurrent Reinforcement Learning with Memoroids

- **Title:** Recurrent Reinforcement Learning with Memoroids
- **Authors:** Steven Morad, Chris Lu, Ryan Kortvelesy, Stephan Liwicki, Jakob Foerster, Amanda Prorok
- **Year / Conference / CCF Rank:** 2024 / NeurIPS / A
- **URL:** [Official](https://proceedings.neurips.cc/paper_files/paper/2024/hash/19f7f755908372efb25826d61959cdf9-Abstract-Conference.html)
- **Code URL:** 官方页未提供稳定代码链接
- **Citation:** 动态引用量未稳定读取
- **Research Direction:** Recurrent memory under partial observability
- **Main Problem:** RNN/Transformer 在 POMDP 长序列中难以高效构造 latent Markov state。
- **Core Method:** 用 monoid 统一线性 recurrent memory 并改进 batching/training。
- **Why Important:** 从理论上把 memory 的目标定义为 latent Markov state，而非历史复述。
- **First-Principles Diagnosis:** 给出了可组合更新结构，但没有解决 GUI 事实如何 typed、verified、versioned。
- **Limitation:** 不处理开放词汇、多模态实体、LLM hallucination 和 GUI drift。
- **Potential GUI Agent Connection:** 为 belief update 的可组合性提供理论参照。
- **Possible Research Opportunity:** 神经-符号 causal memory update。

### 2025-P1. Agent S

- **Title:** Agent S: An Open Agentic Framework that Uses Computers Like a Human
- **Authors:** Saaket Agashe, Jiuzhou Han, Shuyu Gan, Jiachen Yang, Ang Li, Xin Eric Wang
- **Year / Conference / CCF Rank:** 2025 / ICLR / A（按本调研口径）
- **URL:** [ICLR Paper](https://proceedings.iclr.cc/paper_files/paper/2025/file/394c7c30ea87b5c3521b4d9e9d419071-Paper-Conference.pdf)
- **Code URL:** [simular-ai/Agent-S](https://github.com/simular-ai/Agent-S)
- **Citation:** Semantic Scholar 调研快照（2026-07-21）：118
- **Research Direction:** Experience-augmented hierarchical planning
- **Main Problem:** 通用 computer-use 缺少领域经验与长任务层级规划。
- **Core Method:** narrative memory、episodic memory、hierarchical planning 与 ACI。
- **Why Important:** 将 memory 放进真实桌面 planner，而非独立 QA 模块。
- **First-Principles Diagnosis:** 经验减少搜索，但只在当前 state 与历史 state 因果兼容时有效；语义相似无法保证这一点。
- **Limitation:** 缺少 staleness、confidence、contradiction 和前置条件验证。
- **Potential GUI Agent Connection:** desktop episodic-memory 强基线。
- **Possible Research Opportunity:** verified experience graph。

### 2025-P2. GUI-Rise

- **Title:** GUI-Rise: Enhancing GUI Interaction with Recursive Internal State Evolution
- **Authors:** Tao Liu, Chongyu Wang, Rongjie Li, Yingchen Yu, Xuming He, Bai Song
- **Year / Conference / CCF Rank:** 2025 / NeurIPS / A
- **URL:** [Official](https://papers.nips.cc/paper_files/paper/2025/hash/f144ab9985c739a5091ec188a2688644-Abstract-Conference.html)
- **Code URL:** [Leon022/GUI-Rise-code](https://github.com/Leon022/GUI-Rise-code)
- **Citation:** 新论文；引用量仍不稳定
- **Research Direction:** Learned recursive GUI history
- **Main Problem:** action-only history 丢失视觉状态，全截图 history 又会爆炸。
- **Core Method:** 每步递归更新文本 internal state，并以 SFT + GRPO 优化。
- **Why Important:** 直接训练 GUI context management，而非手写摘要 prompt。
- **First-Principles Diagnosis:** 固定长度递归状态是必要方向，但其 history reward 主要依赖下一步动作；信息的长期价值没有被识别，早期遗漏不可逆。
- **Limitation:** short-horizon supervision、无原始证据指针、无 uncertainty/staleness。
- **Potential GUI Agent Connection:** learned summary 核心基线。
- **Possible Research Opportunity:** multi-horizon counterfactual state sufficiency。

### 2025-P3. MobileUse

- **Title:** MobileUse: A Hierarchical Reflection-Driven GUI Agent for Autonomous Mobile Operation
- **Authors:** Ning Li, Xiangmou Qu, Jiamu Zhou, Muning Wen, Kounianhua Du, Xingyu Lou, Qiuying Peng, Jun Wang, Weinan Zhang
- **Year / Conference / CCF Rank:** 2025 / NeurIPS / A
- **URL:** [Official](https://proceedings.neurips.cc/paper_files/paper/2025/hash/3994410d63ec68ce9a66011a34c9a2c4-Abstract-Conference.html)
- **Code URL:** [MadeAgents/mobile-use](https://github.com/MadeAgents/mobile-use)
- **Citation:** 新论文；引用量未稳定读取
- **Research Direction:** Hierarchical reflection and recovery
- **Main Problem:** action-level feedback无法覆盖长任务、冷启动和错误恢复。
- **Core Method:** action/trajectory/global reflection、reflection-on-demand、主动探索。
- **Why Important:** 证明不同时间尺度需要不同反馈，并显式处理反思成本。
- **First-Principles Diagnosis:** reflection 是对 internal state 的二次推断；若没有新 observation，它不能增加真实信息，只能重组已有信息，甚至放大错误。
- **Limitation:** 论文也承认过量反思会增加延迟并产生 hallucinated assessment。
- **Potential GUI Agent Connection:** uncertainty-triggered verification 基线。
- **Possible Research Opportunity:** 只有信息增益为正时才反思/重观察。

### 2025-P4. A-Mem

- **Title:** A-Mem: Agentic Memory for LLM Agents
- **Authors:** Wujiang Xu, Zujie Liang, Kai Mei, Hang Gao, Juntao Tan, Yongfeng Zhang
- **Year / Conference / CCF Rank:** 2025 / NeurIPS / A
- **URL:** [Official](https://proceedings.neurips.cc/paper_files/paper/2025/hash/19909c36f51abc4856b4560aff3d36d6-Abstract-Conference.html)
- **Code URL:** [WujiangXu/A-mem](https://github.com/WujiangXu/A-mem)
- **Citation:** 新论文；引用量未稳定读取
- **Research Direction:** Dynamic structured agent memory
- **Main Problem:** 固定 schema 和孤立 memory chunk 不利于知识演化。
- **Core Method:** Zettelkasten 风格属性、链接和 memory evolution。
- **Why Important:** 让 memory organization 从静态向关系化发展。
- **First-Principles Diagnosis:** semantic link 回答“哪些概念相关”，但 GUI control 需要“哪个事实由何 observation 支持、何时失效、哪个动作依赖它”。
- **Limitation:** 缺少 temporal/causal/provenance/contradiction semantics。
- **Potential GUI Agent Connection:** relational memory baseline。
- **Possible Research Opportunity:** executable temporal causal graph。

### 2025-P5. ShowUI

- **Title:** ShowUI: One Vision-Language-Action Model for GUI Visual Agent
- **Authors:** Kevin Qinghong Lin, Linjie Li, Difei Gao, Zhengyuan Yang, Shiwei Wu, Zechen Bai, Stan Weixian Lei, Lijuan Wang, Mike Zheng Shou
- **Year / Conference / CCF Rank:** 2025 / CVPR / A
- **URL:** [CVF](https://openaccess.thecvf.com/content/CVPR2025/html/Lin_ShowUI_One_Vision-Language-Action_Model_for_GUI_Visual_Agent_CVPR_2025_paper.html)
- **Code URL:** 官方论文页未给出稳定独立链接
- **Citation:** 新论文；引用量未稳定读取
- **Research Direction:** Visual token and VLA-history efficiency
- **Main Problem:** screenshot token 冗余使纯视觉 GUI agent 昂贵。
- **Core Method:** UI-connected graph token selection 与 interleaved VLA streaming；减少 33% 视觉 token。
- **Why Important:** 证明 GUI observation 应按结构选择。
- **First-Principles Diagnosis:** 空间冗余与时间冗余不同；当前画面不重要的 token，可能是跨步 entity identity 的唯一证据。
- **Limitation:** 不评估 temporal delayed dependency 和事实有效性。
- **Potential GUI Agent Connection:** multimodal context-efficiency baseline。
- **Possible Research Opportunity:** joint spatial-temporal causal selection。

### 2026-P1. AgentProg

- **Title:** AgentProg: Empowering Long-Horizon GUI Agents with Program-Guided Context Management
- **Authors:** Shizuo Tian, Hao Wen, Yuxuan Chen, Jiacheng Liu, Shanhui Zhao, Guohong Liu, Ju Ren, Yunxin Liu, Yuanchun Li
- **Year / Conference / CCF Rank:** 2026 / MobiSys / B
- **URL:** [MobiSys Program and Public Review](https://www.sigmobile.org/mobisys/2026/program/)；[arXiv](https://arxiv.org/abs/2512.10371)
- **Code URL:** [MobileLLM/AgentProg](https://github.com/MobileLLM/AgentProg)
- **Citation:** 新近正式发表；引用量不稳定
- **Research Direction:** Program-guided context management / belief state
- **Main Problem:** 长轨迹 context 不断增长，普通压缩无法系统保留关键语义。
- **Core Method:** Semantic Task Program 用变量、控制流和 data flow 组织交互；global belief state 处理部分可观测和计划外变化。
- **Why Important:** 这是 2026 最直接挑战本课题的工作：它已经把“history”改写为“program state”。
- **First-Principles Diagnosis:** backward data dependency 比自然语言摘要更接近决策充分性；但开放 GUI 中未来 dependency 不完全由当前 program 知道。错误 task decomposition 或未建模事件会让必要变量从 schema 中消失。
- **Limitation:** program/schema completeness 假设；belief 的 provenance、calibration、validity 和 contradiction 仍不完整。
- **Potential GUI Agent Connection:** 新方法必须超过的核心 baseline。
- **Possible Research Opportunity:** open-world causal memory contract：允许未知变量、证据追踪、反例触发 schema 扩展。

### 2026-P2. MAGNET

- **Title:** MAGNET: Towards Adaptive GUI Agents with Memory-Driven Knowledge Evolution
- **Authors:** Libo Sun, Jiwen Zhang, Siyuan Wang, Zhongyu Wei
- **Year / Conference / CCF Rank:** 2026 / ACL / A
- **URL:** [ACL Anthology](https://aclanthology.org/2026.acl-long.1299/)
- **Code URL:** [Project](https://craftjarvis-jarvis1.github.io/)
- **Citation:** 2026 新论文；引用量不稳定
- **Research Direction:** Memory evolution under GUI drift
- **Main Problem:** app 更新改变视觉外观和 workflow，使历史数据训练的 agent 失效。
- **Core Method:** stationary memory 把多样视觉映射到稳定功能语义；procedural memory 捕获跨 workflow 的稳定 task intent；按访问频率动态演化。
- **Why Important:** 2026 已明确把 non-stationary GUI 当作 memory 问题，而非纯 grounding 问题。
- **First-Principles Diagnosis:** 方法建立在“功能语义和任务意图比外观稳定”的不变量上；这是合理压缩，但并非所有更新都保持语义。权限、业务规则和危险副作用可能同时改变。
- **Limitation:** 频繁访问只能表示 popularity，不能证明 correctness/freshness；缺少可证伪的 validity contract。
- **Potential GUI Agent Connection:** UI drift 的直接 SOTA baseline。
- **Possible Research Opportunity:** 从 memory evolution 升级为 memory validation/invalidation。

### 2026-P3. UI-Copilot

- **Title:** UI-Copilot: Advancing Long-Horizon GUI Automation via Tool-Integrated Policy Optimization
- **Authors:** Zhengxi Lu, Fei Tang, Guangyi Liu, Jin Ma, Kaitao Song, Xu Tan, Wenqi Zhang, Weiming Lu, Jun Xiao, Yueting Zhuang, Yongliang Shen
- **Year / Conference / CCF Rank:** 2026 / ACL / A
- **URL:** [ACL Anthology](https://aclanthology.org/2026.acl-long.904/)
- **Code URL:** [ZJU-REAL/UI-Copilot](https://github.com/ZJU-REAL/UI-Copilot)
- **Citation:** 2026 新论文；引用量不稳定
- **Research Direction:** On-demand memory/tool invocation
- **Main Problem:** 长任务中的 memory degradation、progress confusion 和 math hallucination 超出单一 actor 内在能力。
- **Core Method:** persistent observation 与 transient context 解耦；轻量 copilot 作为 Retriever/Calculator；TIPO 分别优化工具选择和多轮执行。
- **Why Important:** 把 memory access 从默认塞入 context 改为可学习的 action。
- **First-Principles Diagnosis:** 解耦减少 actor burden，但 Retriever 返回的信息是否是当前动作的必要充分条件仍未被证明；错误调用和错误不调用都属于 epistemic decision。
- **Limitation:** tool-selection reward 不等于 memory truth/causal utility；retrieved item 的时效和冲突未显式处理。
- **Potential GUI Agent Connection:** selective retrieval/tool use 强基线。
- **Possible Research Opportunity:** 用 expected value of information 和 action risk 决定工具调用。

### 2026-P4. MaDS

- **Title:** MaDS: Long-Horizon GUI Automation via Synergizing Dual-Layer Memory and Multi-Round Debate
- **Authors:** Pengchen Chen, Shi Chen, Qiming Ye, Xinli Chen, Xinran Li, Wei Xiang
- **Year / Conference / CCF Rank:** 2026 / ACL / A
- **URL:** [ACL Anthology](https://aclanthology.org/2026.acl-long.1202/)
- **Code URL:** [PcCin37/MaDS](https://github.com/PcCin37/MaDS)
- **Citation:** 2026 新论文；引用量不稳定
- **Research Direction:** Dual-layer memory / pre-execution verification
- **Main Problem:** 低 SNR grounding 和不可逆长流程使错误不断累积。
- **Core Method:** universal prior + scenario experience 双层 memory；multi-round debate；把失败转成 Negative Warnings；MaDS-Benchmark。
- **Why Important:** 同时触及 experience、verification、negative memory 和 process evaluation。
- **First-Principles Diagnosis:** debate 只能降低独立推理错误；若多个 agent 共享同一错误 observation 或 stale memory，重复讨论不会增加真实信息。Negative Warning 也必须限定适用状态，否则会过度回避。
- **Limitation:** consensus 不等于 grounded verification；warning 缺少 causal scope。
- **Potential GUI Agent Connection:** safety/recovery memory 强基线。
- **Possible Research Opportunity:** evidence-producing verifier 和 state-scoped failure contract。

### 2026-P5. LongHorizonUI

- **Title:** LongHorizonUI: A Unified Framework for Robust Long-Horizon Task Automation of GUI Agent
- **Authors:** Bin Kang, Shaoguo Wen, Yifei Bi, Shunlong Wu, Xinbin Yuan, Rui Shao, Junle Wang, Zhuotao Tian
- **Year / Conference / CCF Rank:** 2026 / ICLR / A（按本调研口径）
- **URL:** [ICLR](https://iclr.cc/virtual/2026/poster/10010959)
- **Code URL:** [kane2kang/LongHorizonUI](https://github.com/kane2kang/LongHorizonUI)
- **Citation:** 2026 新论文；引用量不稳定
- **Research Direction:** Long-horizon perception, reflection and rollback
- **Main Problem:** 动态环境中的 grounding degradation、错误累积和不可恢复执行。
- **Core Method:** indexed multimodal perception、multi-level feedback validation、compensatory actions、progress-based rollback；LongGUIBench。
- **Why Important:** 将 recovery 变成体系结构组件，并构建 >15 步任务。
- **First-Principles Diagnosis:** rollback 有效的前提是系统知道哪个状态被破坏、哪个 checkpoint 仍有效；progress scalar/monitor 不能完整表示 hidden state 或跨 app side effect。
- **Limitation:** 缺少显式 causal state delta、irreversibility contract 和 rollback correctness criterion。
- **Potential GUI Agent Connection:** recovery/rollback 强基线。
- **Possible Research Opportunity:** state-aware compensation graph。

### 2026-P6. OCR-Memory

- **Title:** OCR-Memory: Optical Context Retrieval for Long-Horizon Agent Memory
- **Authors:** Jinze Li, Yang Zhang, Xin Yang, Jiayi Qu, Jinfeng Xu, Shuo Yang, Junhua Ding, Edith Cheuk-Han Ngai
- **Year / Conference / CCF Rank:** 2026 / ACL / A
- **URL:** [ACL Anthology](https://aclanthology.org/2026.acl-long.474/)
- **Code URL:** 官方论文页未给出稳定代码链接
- **Citation:** 2026 新论文；引用量不稳定
- **Research Direction:** Optical long-horizon memory
- **Main Problem:** raw trajectory 太贵，摘要/文本检索又损失信息和证据完整性。
- **Core Method:** 把历史渲染成带 visual identifiers 的图像；locate-and-transcribe 先定位再逐字恢复，避免自由生成。
- **Why Important:** 提供低 prompt 开销、可回到原文证据的冷存储方案。
- **First-Principles Diagnosis:** 它改善了 storage fidelity，而不是 state sufficiency；忠实找回旧文本仍无法判断其是否过期、矛盾或是当前 action 的因果前提。
- **Limitation:** retrieval utility、temporal validity、action grounding 未统一。
- **Potential GUI Agent Connection:** 作为 lossless cold-memory layer 很强。
- **Possible Research Opportunity:** causal hot state + optical evidence archive 双层架构。

### 2026-P7. MMBench-GUI

- **Title:** MMBench-GUI: A Unified Hierarchical Evaluation Framework for Multi-Platform GUI Agents
- **Authors:** Xuehui Wang, Zhenyu Wu, JingJing Xie, Zichen Ding, Bowen Yang, Zehao Li, Zhaoyang Liu, Qingyun Li, Xuan Dong, Zhe Chen, Weiyun Wang, Xiangyu Zhao, Jixuan Chen, Haodong Duan, Tianbao Xie, Chenyu Yang, Shiqian Su, Yue Yu, Yanting Zhang, Xiangyu Yue, Weijie Su, Xizhou Zhu, Wei Shen, Jifeng Dai, Wenhai Wang
- **Year / Conference / CCF Rank:** 2026 / CVPR / A
- **URL:** [CVF Open Access](https://openaccess.thecvf.com/content/CVPR2026/html/Wang_MMBench-GUI_A_Unified_Hierarchical_Evaluation_Framework_for_Multi-Platform_GUI_Agents_CVPR_2026_paper.html)
- **Code URL:** [open-compass/MMBench-GUI](https://github.com/open-compass/MMBench-GUI)
- **Citation:** CVF 页面检索快照：1；新论文引用量不稳定
- **Research Direction:** Multi-platform hierarchical evaluation
- **Main Problem:** GUI benchmark 平台碎片化，能力层次和效率难比较。
- **Core Method:** Windows/macOS/Linux/iOS/Android/Web；理解、grounding、automation、collaboration 四层；EQA 同时衡量成功与动作冗余。
- **Why Important:** 2026 证据显示复杂/跨 app 任务暴露 memory、planning、adaptive reasoning 缺陷。
- **First-Principles Diagnosis:** 层级评价能定位能力阶段，但尚未用因果干预区分遗漏、错误写入、stale retrieval 与 recovery failure。
- **Limitation:** 不是 memory-specific benchmark。
- **Potential GUI Agent Connection:** 可作为跨平台诊断母集。
- **Possible Research Opportunity:** Memory Intervention Protocol。

## 2.4 辅助观察与淘汰记录

| Paper | 年份/状态 | 处理 | Discard Reason / 角色 |
|---|---|---|---|
| PersonalAlign / HIM-Agent | ACL 2026 | 辅助方向 | 高质量且与长期用户 memory 相关，但主问题是个性化 implicit intent，不是通用长程执行；用于 Gap 6 |
| Computer Agent Arena | ICLR 2026 | 评测辅助 | 正式论文，证明静态 benchmark 漏掉 long-horizon memory/self-correction；不属于新 memory 方法 |
| MemAgent | ICLR 2026 Oral | context 邻域 | 强 long-context memory 学习，但主要是长文 QA，不直接处理 GUI state/action validity |
| CogAgent / SeeClick | CVPR/ACL 2024 | 基础发展线 | 高质量 grounding 工作；不直接解决 long-horizon memory，故不占核心 memory 论文名额 |
| UI-Genie / GUI-Xplore | NeurIPS/CVPR 2025 | 辅助发展线 | 分别偏 reward/self-improvement 与环境探索，不是本报告 memory/context 核心干预 |
| 2023 及更早的基础论文 | 时间窗外 | 核心池排除 | 不进入本报告论文表、论文卡与主要 gap 证据链 |
| ICLR 2026 Workshop papers | 2026 workshop | 排除 | 用户明确过滤 workshop |
| 仅 arXiv、未确认正式发表的 2026 memory 工作 | 2026 | 观察 | 不用来支撑当前主要结论 |

---

# Part 3: Existing Methods Analysis

## 3.1 第一性原理分析模板

对任何 Memory / Context 方法，不先问“用了什么模块”，而先问五个问题：

```text
1. Decision variable：未来动作真正依赖什么状态变量？
2. Information operation：方法写入、删除、压缩、检索了什么？
3. Sufficiency claim：为何保留下来的信息足够决定未来动作？
4. Truth maintenance：信息如何被 observation 验证、失效和冲突消解？
5. Counterexample：构造什么环境后，该方法仍必然失败？
```

## 3.2 方法族 A：Raw History / Optical Archive

```text
Current Method
  保存截图、DOM、动作与文本；或用 OCR-Memory 视觉化压缩后逐字恢复
↓
What problem it solves
  避免自由摘要丢失原始证据；支持长历史冷存储
↓
Why it works
  information fidelity 高，事实可追溯
↓
Why it fails
  evidence completeness ≠ decision sufficiency；旧证据可能过期；检索仍需知道找什么
↓
Missing capability
  causal dependency、validity、contradiction 和 value-of-information
```

第一性结论：OCR-Memory 解决的是**编码容量**，不是**状态估计**。它很适合作为 cold storage，但不能单独成为 planner 的 working state。[OCR-Memory](https://aclanthology.org/2026.acl-long.474/)

## 3.3 方法族 B：Recursive Summary / Context Compression

```text
Current Method
  LongLLMLingua 按 query 压缩；GUI-Rise 递归更新 internal state
↓
What problem it solves
  固定上下文预算，减少截图/文本历史爆炸
↓
Why it works
  大部分历史对当前动作确实冗余
↓
Why it fails
  被删除信息的未来价值未知；递归摘要错误不可逆
↓
Missing capability
  multi-horizon counterfactual sufficiency + evidence pointer
```

第一性结论：压缩策略实际在回答“哪段历史可以安全遗忘”。若训练目标只看下一步，它没有信息判断十几步后的依赖，因此失败不是模型不够大，而是监督信号错位。[GUI-Rise](https://papers.nips.cc/paper_files/paper/2025/hash/f144ab9985c739a5091ec188a2688644-Abstract-Conference.html)

## 3.4 方法族 C：Episodic / Procedural / Program Memory

```text
Current Method
  ICAL/Agent S 检索经验；MobileGPT 保存 procedure；AgentProg 用程序变量和控制流
↓
What problem it solves
  减少重复探索；把历史压成任务结构和可执行状态
↓
Why it works
  同类任务共享 subgoal、变量和 control flow
↓
Why it fails
  当前 program 不知道所有未来异常；semantic similarity 不保证 precondition 相同
↓
Missing capability
  open-world schema expansion、causal contract、uncertainty 和 validity proof
```

第一性结论：AgentProg 已经比“文本摘要”更接近充分状态，但 program-guided selection 只在 program 正确且完整时成立。开放 GUI 的难点正是计划外弹窗、异步 effect、权限差异和 UI drift。[AgentProg MobiSys 2026](https://www.sigmobile.org/mobisys/2026/program/)

## 3.5 方法族 D：Evolving / Linked Memory

```text
Current Method
  A-Mem 动态链接；MAGNET 学习稳定功能语义和程序意图并持续演化
↓
What problem it solves
  memory 不再是静态 chunk；适应 GUI 外观和 workflow 变化
↓
Why it works
  功能语义和用户意图通常比像素/layout 稳定
↓
Why it fails
  稳定性只是统计假设；高频记忆仍可能错误、过时或改变副作用
↓
Missing capability
  falsifiable invariant、valid-until、version scope、invalidation trigger
```

第一性结论：MAGNET 解决了“如何跨变化复用”，但尚未解决“何时不应复用”。后者对高风险和不可逆动作更重要。[MAGNET](https://aclanthology.org/2026.acl-long.1299/)

## 3.6 方法族 E：On-Demand Retrieval / Reflection / Debate

```text
Current Method
  UI-Copilot 学习调用 Retriever/Calculator；MobileUse 按需反思；MaDS 多轮 debate
↓
What problem it solves
  减少 actor 负担；在困难步骤增加计算和经验
↓
Why it works
  不是每一步都需要完整 memory 或昂贵 reasoning
↓
Why it fails
  多想几次不产生新环境信息；共享错误 observation 时可形成一致的错误
↓
Missing capability
  epistemic uncertainty、expected information gain、evidence-producing tool
```

第一性结论：反思和 debate 是 computation，不是 observation。若瓶颈是缺少/过期状态，正确动作是主动感知或工具查询，而不是继续语言推理。[UI-Copilot](https://aclanthology.org/2026.acl-long.904/)；[MaDS](https://aclanthology.org/2026.acl-long.1202/)

## 3.7 方法族 F：Verifier / Negative Memory / Rollback

```text
Current Method
  MaDS pre-action debate + negative warning；LongHorizonUI feedback validation + rollback
↓
What problem it solves
  防止错误累积，允许从局部失败恢复
↓
Why it works
  长任务必须把 effect monitoring 和 recovery 放入控制回路
↓
Why it fails
  不知道哪个 hidden state 被破坏时，rollback 可能回到视觉相同但语义错误的状态
↓
Missing capability
  state delta、irreversibility、checkpoint validity、compensation contract
```

第一性结论：回退不是“点击返回”。真正的 rollback 必须恢复任务相关状态；已发送邮件、已覆盖文件或已触发后台任务不能通过界面导航逆转。[LongHorizonUI](https://iclr.cc/virtual/2026/poster/10010959)

## 3.8 2024→2026 后仍存在的统一缺口

```text
现有方法不能保证 memory 在当前决策点仍然正确且充分

because

它们分别优化 storage、compression、program structure、retrieval、reflection 或 rollback，
但没有把“事实—证据—有效范围—动作前置条件—预期效果—失效规则”绑定为可执行契约

therefore

新的方法不应再提出一个独立 memory module，也不能只把现有变量、验证和恢复字段重命名为 contract。
真正需要证明的是：在等观测与等验证预算下，Agent 能否发现当前高风险动作尚未证实的必要条件，并选择具有正决策价值的环境 probe。
```

---

# Part 4: Find Research Gap

## Gap 1（条件性首选）：Risk-Calibrated Epistemic Commit Control

- **Research Question:** 在开放 GUI 中，Agent 能否从不完整且可能过期的环境证据中校准某个动作前置条件的违例概率，并在 execute、主动 probe、safe alternative、abstain 与 human confirmation 之间做成本敏感决策？
- **Why Important:** AgentProg 已有 program/belief state，InferAct/MaDS 已有动作前检查，ToolGate 已有 symbolic pre/postcondition，BacktrackAgent/LongHorizonUI 已有 effect verification 与 recovery。剩余问题不是 contract 字段，而是 internal state 是否足以授权真实 GUI 中的高风险动作。
- **Root Cause:** 当两个隐藏状态在 commit 表示下不可区分时，继续 retrieval、summary、reflection 或 debate 不能创造新信息；不可逆动作后的 verifier 又无法挽回首次损失。
- **Existing Limitation:** 现有工作尚未联合校准 action risk、evidence sufficiency、probe information value、verification cost、coverage 与真实不可逆损失；但也没有实证证明 SOTA-Composite 原则上不能做到。
- **Candidate Interface, not the contribution:** 可以用可审计 contract 记录：

```text
Contract = {
  state_variable,
  claim,
  provenance,
  confidence,
  valid_scope(app, version, account, time),
  dependent_actions,
  precondition,
  expected_effect,
  falsifier,
  compensation
}
```

- **Before Method:** 先做自然失败覆盖率审计与 Oracle Ladder，区分 risk detector、contract specification、current-evidence ceiling、best safe probe、semantic outcome、recovery 和 TOCTOU 上限。
- **Experiment Design:** 在 OSWorld、AndroidWorld、LongGUIBench/MMBench-GUI 中构造 matched hidden-state pairs，系统干预 delayed dependency、stale evidence、作用域错配、UI drift、异步 effect、不可逆动作与 TOCTOU；固定 backbone、context、probe、token、tool call 和 latency。
- **Expected Contribution if Stage-0 passes:** risk-conditioned active state disambiguation objective + risk–coverage–cost benchmark，而不是“首个 action contract”。完整证明边界见 [对抗式论证报告](gui_epistemic_commit_control_battle_report.md)。

## Gap 2：Counterfactual Multi-Horizon Memory Utility

- **Research Question:** 如何判断一条 observation 对未来 1/5/20/50 步的决策价值，而不是只判断其与当前 query/action 的相关性？
- **Why Important:** GUI-Rise、LongLLMLingua、ShowUI、AgentProg 都必须删除信息，但都需要一个“安全遗忘”判据。
- **Root Cause:** 事件价值由未来 task dependency 决定；当前 salience/relevance/access frequency 不能代表 delayed utility。
- **Existing Limitation:** GUI-Rise 偏 next-action；MAGNET 的访问频率偏 popularity；AgentProg 依赖当前 program data flow，无法覆盖未建模未来事件。
- **New Idea:** 用 counterfactual deletion/mutation 估计 memory item 被删除后多个 future horizons 的 return drop，并对未知依赖保留 uncertainty reserve。
- **Possible Method:** horizon-conditioned value heads；offline trajectory counterfactual；cold-storage recall；budgeted knapsack/context composer；不确定时保留证据索引而非全文。
- **Experiment Design:** 控制依赖距离和关键事件稀疏度；绘制 task success–horizon–token 曲线；比较 last-k、GUI-Rise、AgentProg 和 oracle dependency graph。
- **Expected Contribution:** 给出 GUI context compression 的长期信息价值定义和训练方法。

## Gap 3：Memory Validity and Contradiction under Semantic Drift

- **Research Question:** 当界面外观、功能语义、权限、业务规则或副作用发生不同层级变化时，memory 如何判断保留、迁移、分叉或废弃？
- **Why Important:** MAGNET 已解决部分 UI drift；继续做“更强 evolution”不够，必须研究错误复用的边界。
- **Root Cause:** memory evolution 将重复/访问当作稳定性代理，但真实环境中高频知识也会突然失效。
- **Existing Limitation:** 缺少 version scope、contradiction graph、change-point detection 与 causal revalidation。
- **New Idea:** hierarchical validity：visual locator、functional semantics、workflow、business rule、side effect 分层版本化；每层都有可验证 invariant 和失效条件。
- **Possible Method:** change-point detector；新旧 memory hypothesis 并存；主动 probing；contract fork/deprecate；基于 effect 的在线校准。
- **Experiment Design:** 对 app 注入 layout、label、workflow、权限、规则、副作用六类 drift；测 positive transfer、negative transfer、stale-memory detection 和修复样本数。
- **Expected Contribution:** 从 UI-drift robustness 推进到可审计的 continual GUI memory。

## Gap 4：Uncertainty-Calibrated Active Verification

- **Research Question:** Agent 应在何时继续推理、何时检索、何时重新观察、何时调用结构化工具、何时请求用户确认？
- **Why Important:** UI-Copilot 已学习 tool invocation，MaDS/MobileUse 已按需增加推理，但它们未统一“缺计算”与“缺信息”。
- **Root Cause:** epistemic uncertainty 与 reasoning uncertainty 混在自然语言 confidence 中，通常未校准。
- **Existing Limitation:** debate 可能共享错误；Retriever 可能返回 stale evidence；每步验证又造成不可接受成本。
- **New Idea:** 把 verification 视为风险敏感的 value-of-information 决策：只有新 observation 能改变 action distribution 且收益高于成本时才调用。
- **Possible Method:** calibrated uncertainty heads、information-gain predictor、action irreversibility cost、tool reliability model、selective abstention。
- **Experiment Design:** 构造同屏异状态、异步 loading、低置信 grounding、错误 memory 与高风险 irreversible action；测 ECE、verification precision、catastrophic action rate 和总成本。
- **Expected Contribution:** 统一 reflection、retrieval、active perception 和 human confirmation。

## Gap 5：State-Correct Recovery and Compensation Memory

- **Research Question:** 发生错误后，Agent 如何恢复任务状态，而不仅是视觉页面或操作进度？
- **Why Important:** LongHorizonUI 和 MaDS 已显示 rollback/negative warning 有效；下一步必须处理跨 app side effect 和不可逆动作。
- **Root Cause:** 线性 action history 不表示 state topology；视觉返回旧页面不代表数据、后台任务和外部副作用已恢复。
- **Existing Limitation:** progress-based rollback、语言 warning 和重新规划缺少 state restoration proof。
- **New Idea:** checkpoint 保存 task-relevant state contracts；动作标注 reversible、compensatable、irreversible；失败后生成 compensation plan，并验证目标 state delta。
- **Possible Method:** state checkpoint graph、failure signature、compensation library、barrier before irreversible action、cross-app effect ledger。
- **Experiment Design:** 注入误发送、误覆盖、下载失败、窗口抢焦、网络重试导致重复提交等故障；测 recovery success、duplicate side effect、state restoration F1 和代价。
- **Expected Contribution:** 把 GUI recovery 从导航回退提升为 transaction-like semantic recovery。

## Gap 6：Long-Term User Memory with Privacy and Intent Uncertainty

- **Research Question:** GUI Agent 如何利用长期用户记录推断隐式意图，同时避免把过时偏好、偶然行为或敏感信息当成稳定意图？
- **Why Important:** PersonalAlign/HIM-Agent 已把长期用户记录引入 GUI；这打开了能力，也扩大了错误自动化和隐私风险。
- **Root Cause:** 行为记录只能提供 preference posterior，不能证明当前意图；跨用户/跨场景检索还有隐私和范围问题。
- **Existing Limitation:** 个性化收益通常按任务结果衡量，较少测 preference staleness、consent、sensitive leakage 与错误主动执行。
- **New Idea:** consent-scoped preference contract、temporal decay、多假设 intent、high-risk confirmation、memory provenance/audit。
- **Possible Method:** Bayesian preference state、purpose-bound retrieval、privacy budget、user-editable memory、counterfactual intent benchmark。
- **Experiment Design:** 偏好反转、共享设备、工作/私人场景切换、敏感记录与模糊指令；测 personalization、false proactive action、privacy violation 和 correction cost。
- **Expected Contribution:** 将 GUI long-term memory 与安全、隐私、可撤销性统一。

## 4.1 方向优先级（相对 2026 SOTA）

| Direction | 相对 2026 新颖性 | 实现难度 | 顶会潜力 | 可证伪性 | 结论 |
|---|---:|---:|---:|---:|---|
| Risk-Calibrated Epistemic Commit Control | 5 | 5 | 5 | 5 | **条件性首选：须先通过 Oracle Stage-0** |
| Counterfactual Multi-Horizon Utility | 5 | 4 | 5 | 5 | 最清晰的算法型备选 |
| Validity/Contradiction under Drift | 4 | 3 | 5 | 5 | 直接承接 MAGNET，需突出语义/副作用 drift |
| Active Verification | 4 | 4 | 5 | 5 | 可作为首选方向关键模块 |
| State-Correct Recovery | 4 | 4 | 5 | 5 | 系统与 planning 贡献强 |
| Private User Memory | 4 | 4 | 4 | 4 | 适合 ACL/CHI/UIST 路线 |

---

# Part 5: Recommend One Best Research Direction

> **2026-07-21 对抗式复审说明：**本节原始“Open-World Causal Memory Contract”提法把表示新颖性和方法可行性说得过强。AgentProg 已覆盖 observation-revisable belief，InferAct/MaDS 已覆盖执行前检查，ToolGate 已覆盖 Hoare-style pre/postcondition 与 verified commit。经实证审计、SOTA 反方和形式化评审各两轮交叉质询后，本节仅保留为早期设计草案，不再代表最终推荐。最终问题、证明边界、Stage-0 与 Go/No-Go 判据见 [对抗式论证报告](gui_epistemic_commit_control_battle_report.md)。

## Proposed Paper Title

**When Is It Safe to Click? Risk-Calibrated Epistemic Commit Control for Long-Horizon GUI Agents**

备选标题：

**Before You Commit: Active State Disambiguation for Irreversible GUI Actions**

## Problem

2026 的 GUI Agent 已经拥有 program-guided context、global belief state、evolving memory、按需 retrieval、pre-execution verification、negative warning、Hoare-style tool contract 和 rollback。缺口不再是“有没有 contract”，而是 symbolic state 是否被真实 GUI 证据支持，以及在高风险 commit 前是否值得主动获取新证据。

因此，Agent 可能：

- 在 AgentProg 的 program 中遗漏计划外但关键的状态变量；
- 在 MAGNET 中高频复用已经改变语义或副作用的知识；
- 在 UI-Copilot 中正确调用 Retriever，却取回 stale/causally irrelevant memory；
- 在 MaDS 中形成共享错误 observation 下的 debate 共识；
- 在 LongHorizonUI 中视觉回退成功，但真实任务状态未恢复。

## Motivation

这些失败不能在现有数据上统一归因为 memory contract 缺失。当前可防守的共同问题是：

> 在动作提交时，Agent 是否有足够证据区分“前置条件成立”与“不成立”；若没有，能否以正净价值主动取证，而不是只对同一 observation 继续推理。

## Observation

1. **Program state 仍是封闭世界。** AgentProg 假设 program/schema 包含未来依赖；真实 GUI 会出现未建模事件。
2. **Memory evolution 不等于 truth maintenance。** 访问频率和跨 UI 一致性不能证明业务语义/副作用未变。
3. **More reasoning 不等于 more information。** debate/reflection 在无新 observation 时无法消除共同 epistemic error。
4. **Rollback 必须恢复语义状态。** 页面、进度和真实外部 effect 是不同层级。
5. **动作依赖提供了 memory 选择的因果监督。** 若某事实被修改/删除会改变未来动作，它才是当前必须保存和验证的状态。

## Hypothesis

当前只能提出条件性假设：在存在可观察但尚未主动获取的 action-relevant evidence 时，若系统能校准动作风险，并选择 EVSI 高于成本的安全 probe，则其 risk–coverage–cost frontier 应优于等预算的 AgentProg/MaDS/ToolGate 组合与 generic verifier。该假设必须先通过 Oracle Ladder；不能预设显式 contract 一定优于 verified belief state。

## Method: OCMC

### 1. Contract Event Encoder

从相邻 observation 和 action 提取：

```text
Event_t = {
  observed_entities,
  action,
  expected_effect,
  observed_effect,
  state_delta,
  source_pointer,
  uncertainty
}
```

严格区分：

- `observed`：截图/DOM/API 直接支持；
- `inferred`：模型推断但未验证；
- `unknown`：当前无法判断；
- `contradicted`：新 observation 与旧 claim 冲突。

### 2. Causal Memory Contract

```text
MemoryContract_i = {
  variable: selected_account,
  claim: "work_account",
  provenance: observation_17.region_4,
  confidence: 0.91,
  valid_scope: {app=v3.2, account_session=42},
  required_by: [send_email_step],
  precondition: session_active,
  expected_effect: recipient_domain == company_domain,
  falsifier: account_badge != work_account,
  compensation: switch_account_and_revalidate
}
```

### 3. Open-World Task Dependency Graph

- 从计划 backward slice 得到下一阶段 must-know variables；
- 不把所有 observation 都塞进 program；只保留影响未来 action 的 dependency；
- 允许新事件创建 unknown variable、扩展 schema 或使旧 contract 失效；
- 对低置信但潜在高损失变量保留冷存储证据指针。

### 4. Risk-Aware Verification Policy

验证决策同时考虑：

```text
Expected Verification Value
= P(memory wrong) × action-loss-if-wrong × information-gain
- verification cost
```

不可逆动作采用更高阈值；普通导航允许低成本近似。

### 5. Effect Monitor and Semantic Recovery

- action 后比较 expected/observed state delta；
- violation 定位到具体 contract，而不是生成泛化反思；
- 根据动作的 reversible/compensatable/irreversible 类型选择 retry、repair、compensate、rollback 或 ask-user；
- rollback 后必须重新验证 contract，不能以返回旧页面作为成功标准。

### 6. Multi-Horizon Counterfactual Training

对 contract 做 delete、mutate、stale、scope-shift、provenance corruption，训练：

```text
L = L_task_return
  + λ1 L_contract_extraction
  + λ2 L_multi_horizon_sufficiency
  + λ3 L_validity_and_contradiction
  + λ4 L_uncertainty_calibration
  + λ5 L_effect_prediction
  + λ6 TokenCost
  + λ7 VerificationCost
```

## Architecture

```text
Screenshot / DOM / A11y / File / Tool Feedback
                         |
                         v
                  Event Encoder
        observed claim + state delta + evidence
                         |
                         v
        Open-World Task Dependency Graph
           /              |               \
     hot contracts   unknown/conflict   cold evidence
           \              |               /
                         v
              Risk-Aware Verifier
          trust / retrieve / re-observe / ask
                         |
                         v
             Hierarchical Planner / Actor
                         |
                         v
             Expected Effect Monitor
             | match              | violation
             v                    v
        contract update    repair / compensate / rollback
```

## Experiment

### Benchmarks

- **基础环境：**OSWorld、AndroidWorld；可加入 LongGUIBench 与 MMBench-GUI 跨平台任务。
- **新诊断套件 OCMC-Diag：**从真实任务派生，不只做 toy benchmark。

| Intervention | 控制变量 | 要测的根因 |
|---|---|---|
| Delayed dependency | 关键事实与使用间隔 5/10/20/40 步 | state sufficiency |
| Unmodeled event | 突然弹窗、权限请求、异步完成 | open-world schema |
| State aliasing | 同截图、不同账号/选中项/后台状态 | belief uncertainty |
| UI drift | layout/label/workflow 变化 | visual/procedural validity |
| Semantic drift | 权限、规则、effect 改变 | contract invalidation |
| Memory corruption | 删除、篡改、过期、矛盾条目 | truth maintenance |
| Action failure | click miss、焦点抢占、网络超时 | effect monitoring |
| Irreversible effect | 发送、覆盖、删除、重复提交 | risk-aware verification/recovery |

### Baselines

1. full history / last-k；
2. LongLLMLingua-style compression；
3. GUI-Rise recursive internal state；
4. Agent S / ICAL episodic retrieval；
5. AgentProg program + belief state；
6. MAGNET evolving memory；
7. UI-Copilot on-demand retriever；
8. MaDS debate/negative warning；
9. LongHorizonUI rollback；
10. oracle symbolic state 上界。

### Metrics

- task success 与 success–horizon degradation slope；
- must-know variable recall / contract precision-recall；
- stale/contradiction detection；
- uncertainty calibration ECE；
- unnecessary verification rate / missed verification rate；
- semantic recovery success / duplicate side-effect rate；
- token、latency、tool calls、success per 1K tokens；
- negative transfer under drift。

### Critical Ablations

- contract 换成 flat textual belief；
- 去掉 provenance；
- 去掉 valid scope/invalidation；
- 去掉 unknown schema expansion；
- multi-horizon loss 换成 next-action loss；
- verifier 换成 self-reflection/debate；
- semantic recovery 换成页面 rollback；
- 全部方法固定 backbone、context budget、视觉分辨率和工具调用预算。

### Falsification Tests

1. 短、完全可观测任务中不应显著优于 AgentProg；否则收益可能只是额外计算。
2. 没有 drift/unknown event 时，contract verification 应自动减少。
3. 若优势不随 horizon 或 hidden-state 强度增长，不能声称解决 long-horizon memory。
4. 若去掉 provenance/validity 对 corruption/drift 无影响，说明 contract 没有真正参与决策。
5. 若页面 rollback 与 semantic recovery 无差异，benchmark 没有测到真实副作用。

## Expected Contribution

以下只在 Stage-0 通过后成立：

1. **新问题定义：**从 context length / memory retrieval 转向 risk-calibrated epistemic commit control。
2. **新学习问题：**发现 action-relevant unknown predicate，并选择具有正 EVSI 的安全环境 probe。
3. **新训练目标：**联合优化 selective risk、coverage、verification cost 与不可逆损失。
4. **新评测：**用可控 intervention 和 Oracle Ladder 分离 risk、observability、probe value、TOCTOU 与 recovery。
5. **可审计接口：**contract 可连接事实、证据、作用域和动作，但它不是单独的方法贡献。

## Target Venue

- **首选：ICLR 2027 / NeurIPS 2027。**适合新的 agent memory formulation、learning objective 和 benchmark。
- **次选：ACL 2027。**若重点是 structured memory、retrieval、tool invocation 和语言反思校验。
- **次选：CVPR 2027。**若重点是 multimodal state delta、entity identity 和 active visual verification。
- **系统路线：MobiSys 2027 / UIST 2027。**若强调跨 app 部署、semantic rollback、延迟与真实用户任务。

## 最终科研链条

```text
发现重要问题
  2026 GUI Agent 已会压缩、检索、演化、执行前检查和回退，但高风险 commit 的 evidence sufficiency 尚未被联合评测
↓
根本原因
  提交表示若不能区分前置条件成立/不成立，内部推理不能创造缺失环境信息；不可逆动作后的验证又太晚
↓
识别现有局限
  AgentProg、InferAct、MaDS、ToolGate、BacktrackAgent 和 LongHorizonUI 已覆盖主要组件，
  但没有联合优化/评测真实 GUI evidence 的 risk、information value、cost 和 coverage
↓
提出解决方向
  Risk-conditioned active state disambiguation + epistemic commit control
↓
实验验证
  自然失败覆盖率审计 + matched causal tasks + SOTA-Composite + Oracle Ladder + risk–coverage–cost frontier
```

对抗式复审后的最终主张是：

> **长程 GUI Agent 的 memory 不必在表示上全部成为行动契约。真正值得研究的是：在有限上下文和部分可观测环境中，Agent 能否维持对当前动作充分的证据状态，并在不可逆 commit 前以风险和成本为条件主动消除关键状态歧义。Contract 只是可审计的控制接口；能力增益必须来自新环境证据、正确校准与更优决策。**

---

## Official Source Index

### 2024

- [OSWorld — NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/hash/5d413e48f84dc61244b6be550f1cd8f5-Abstract-Datasets_and_Benchmarks_Track.html)
- [MobileGPT — MobiCom 2024 DOI](https://doi.org/10.1145/3636534.3690682)
- [ICAL — NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/hash/8ac50fd0a4eeeb1f077b17bb7c5353c3-Abstract-Conference.html)
- [LongLLMLingua — ACL 2024](https://aclanthology.org/2024.acl-long.91/)
- [Memoroids — NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/hash/19f7f755908372efb25826d61959cdf9-Abstract-Conference.html)

### 2025

- [Agent S — ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/file/394c7c30ea87b5c3521b4d9e9d419071-Paper-Conference.pdf)
- [GUI-Rise — NeurIPS 2025](https://papers.nips.cc/paper_files/paper/2025/hash/f144ab9985c739a5091ec188a2688644-Abstract-Conference.html)
- [MobileUse — NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/3994410d63ec68ce9a66011a34c9a2c4-Abstract-Conference.html)
- [A-Mem — NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/19909c36f51abc4856b4560aff3d36d6-Abstract-Conference.html)
- [ShowUI — CVPR 2025](https://openaccess.thecvf.com/content/CVPR2025/html/Lin_ShowUI_One_Vision-Language-Action_Model_for_GUI_Visual_Agent_CVPR_2025_paper.html)

### 2026

- [AgentProg — MobiSys 2026 program/public review](https://www.sigmobile.org/mobisys/2026/program/)
- [MAGNET — ACL 2026](https://aclanthology.org/2026.acl-long.1299/)
- [UI-Copilot — ACL 2026](https://aclanthology.org/2026.acl-long.904/)
- [MaDS — ACL 2026](https://aclanthology.org/2026.acl-long.1202/)
- [OCR-Memory — ACL 2026](https://aclanthology.org/2026.acl-long.474/)
- [PersonalAlign — ACL 2026](https://aclanthology.org/2026.acl-long.1669/)
- [LongHorizonUI — ICLR 2026](https://iclr.cc/virtual/2026/poster/10010959)
- [Computer Agent Arena — ICLR 2026](https://iclr.cc/virtual/2026/poster/10011593)
- [MemAgent — ICLR 2026 Oral](https://iclr.cc/virtual/2026/oral/10007826)
- [MMBench-GUI — CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Wang_MMBench-GUI_A_Unified_Hierarchical_Evaluation_Framework_for_Multi-Platform_GUI_Agents_CVPR_2026_paper.html)

## 检索与证据限制

- 2026 为当前自然年，NeurIPS 2026 等会议尚未形成完整正式 proceedings；因此本报告的 2026 核心证据主要来自已经正式公开的 ICLR 2026、CVPR 2026、ACL 2026 与 MobiSys 2026。
- Google Scholar 在本环境触发反自动化页面；Semantic Scholar API 曾限流。作者、venue、摘要与方法结论以正式页面/PDF为准。
- 2026 引用量尚无比较意义，统一标记为新近论文或使用官方页可见快照，不以搜索片段猜测。
- 2023 论文被机械移出核心池；它们仅作为历史概念来源，不参与当前 gap 的主要证明。
