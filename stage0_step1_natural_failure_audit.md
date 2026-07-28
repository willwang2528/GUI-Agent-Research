# 步骤 1：自然失败审计——课题是否有真实问题基础

> 状态：**存在性证据已出现；Step 1 自然行为负担仍为 IN PROGRESS；Step 2 关闭。** OSWorld 2.0 与 InterruptBench 的公开案例描述提供了 update-to-action inconsistency 的现象级证据：更新后的要求与后续持久 UI、计算或最终检查不一致。但作者案例和人工 interruption 不能证明该现象在未干预 GUI 轨迹中的负担，也不能识别 Memory 根因。OSWorld 2.0 的目录总体、盲标分母与 Go/No-Go 规则另见 `stage0f_osworld2_natural_burden_preregistration.md`。

## 1. 本步要证明什么

研究主题暂定为：

> **面向长程 GUI Agent 的行动充分、环境可验证的 Memory / Context。**

步骤 1 只检验下列系统级命题：

> 在真实感长程 GUI / Web 轨迹中，是否存在这样的失败：决定后续动作所必需的状态曾经正确，后来被遗漏、篡改、错配或被新证据推翻，但 Agent 的持久 UI、计划、计算或最终检查仍服从旧状态。

它不负责证明新方法有效，也不把所有长任务失败都叫作 Memory 失败。

### 第一性原理判据

行动状态失败包含两个不同子型：

- **Retention 型：**早期事实后续仍有效，但在使用时被遗漏、污染或错配；
- **Invalidation 型：**早期事实曾经正确，后续新证据使其失效，但依赖它的状态、计划或计算没有被撤销和更新。

一个轨迹只有满足以下条件，才是 unresolved action-state candidate：

1. **真值可审计：**旧事实、新事实及其版本或来源能够从环境和 evaluator 中确定；
2. **行动依赖：**翻转该事实会改变正确动作、动作参数、持久 UI 或 execute / block 决策；
3. **证据路径明确：**Retention 型需证明事实早先被观察；Invalidation 型需证明更新已送达，或存在部署可用的环境 probe；
4. **传播发生断裂：**Agent 的工作状态、UI、计算或检查与可用真值不一致；
5. **错误进入行为：**不一致实际改变后续动作或最终状态，而不仅是语言解释不同；
6. **竞争解释保留：**在干预前不得排除 grounding、monitoring、planning、execution 和 verification。

只有进一步冻结 planner、grounder、action decoder、工具、token 与随机条件，并且只替换正确 Memory 后至少 3/5 replay 被修复，才升级为 `memory-caused`。

## 2. 数据源与分母

本轮只采用 2025–2026 年官方公开资源。直接现象证据来自 2026 年 OSWorld 2.0 与 InterruptBench；MemGUI-Bench 提供历史事实保留候选；MaDS 的 2025 年公开执行记录只作为额外负对照与日志结构审计：

- [MemGUI-Bench 论文](https://arxiv.org/abs/2602.06075)
- [MemGUI-Bench 官方项目页](https://lgy0404.github.io/MemGUI-Bench)
- [MemGUI-Bench 官方代码](https://github.com/lgy0404/MemGUI-Bench)
- [MaDS 官方代码与数据](https://github.com/PcCin37/MaDS)
- [OSWorld 2.0 论文](https://arxiv.org/abs/2606.29537)
- [OSWorld 2.0 官方项目页](https://osworld-v2.xlang.ai/)
- [InterruptBench 论文](https://arxiv.org/abs/2604.00892)
- [InterruptBench 官方代码与数据](https://github.com/HenryPengZou/InterruptBench)
- 本地官方任务表：`external/MemGUI-Bench/data/memgui-tasks-all.csv`
- 本地官方失败案例：`external/MemGUI-Bench/docs/images/failure-analysis/`

对任务表的独立统计结果：

| 指标 | 结果 | 能证明什么 | 不能证明什么 |
|---|---:|---|---|
| 总任务数 | 128 | benchmark 规模 | 自然世界中的失败率 |
| 作者标注 `requires_ui_memory=Y` | 115 / 128 = 89.84% | 该 benchmark 按设计富集了跨时间信息传递任务；本审计尚未独立验证每个任务对 Memory 的必要性 | Agent 的失败一定由 Memory 导致；自然 GUI 工作流中的发生率 |
| 跨应用任务 | 100 / 128 = 78.13% | 信息经常需要跨 UI 空间传递 | 跨应用失败一定是 Memory 失败 |
| Golden steps | 均值 36.19，中位数 32，范围 3–160 | 任务具有显著长程性 | 步数越长就必然出现 Memory 失败 |
| 至少 15 个 Golden steps | 108 / 128 = 84.38% | 大部分任务超出短交互范围 | 这些任务都存在高风险 commit |
| 同时被作者标为 Memory 且至少 15 步 | 107 / 128 = 83.59% | 在这个 Memory 专项 benchmark 内，作者标签与长轨迹高度重合 | 课题已经获得因果证明；该比例不能外推到自然 GUI 工作流 |
| 明确要求发送外部消息 | 14 / 128 = 10.94% | benchmark 中存在可审计的外部 commit 机会，且 14 个均被作者标为 Memory | 这些任务已经发生 memory-caused unsafe commit |

官方失败页报告：failure analysis 涉及 1,265 个失败执行，timeout 占 72.3%，并另称有 343 个 non-timeout failures；还称 memory hallucination “on average” 为 58.9%。这些值不能还原为一致的 pooled count：若 343 是 1,265 的精确补集，timeout 应为 922 / 1,265 = 72.89%；公开文字也没有说明 58.9% 是宏平均、微平均、三类合计还是单一类别。

这组数字是 **Memory-enriched benchmark 内部、由带有 Memory 优先归因规则的 taxonomy 产生的描述性统计**，不能估计自然 prevalence，也不能作为独立根因证据。官方分类器对任意 `0 < IRR < 100` 自动赋予 `partial_memory_hallucination`，其提示还明确要求 `Prioritize Memory Issues`；这会把 OCR、grounding、planning、输出生成等原因吸收到 Memory 标签中。

## 3. 作者挑选的公开 benchmark 失败案例预审

| 案例 | 历史事实 | 后续错误 | 第一性原理判断 | 当前证据等级 |
|---|---|---|---|---|
| 056 `SearchAndCalculate`，UI-TARS-1.5-7B | Step 9 观察到 AAPL = 226.91；Step 6 观察到 NVDA = 169.92 | 计算 75 股 AAPL 时输入 143.92；NVDA 值却使用正确 | 历史值与后续动作参数发生可定位不一致；满足历史可得、行动依赖和当前 observation 不足，但 143.92 的产生位置未知，尚未区分 Memory、数字生成与 action decoding | unresolved M candidate；没有 memory-only replay |
| 077 `CheckAndNotePermissions`，M3A | 来源截图 Step 7 显示 9 个 Wi-Fi control app；Step 9 显示 PiP 列表 | 最终笔记只保留 Wi-Fi 列表 4/9；PiP 列表完整 | 证明来源页面与最终输出不一致，但无法判断九项是否曾进入 Agent 内部表示；视觉读取、列表提取、Memory 保留和输出生成均未排除 | unresolved M / grounding candidate；必须做正确列表注入与 perception 对照 |
| 063 `SearchImageAndDescribe`，UI-TARS-1.5-7B | Agent 找到 Q3 2021 图表并在 thought 中正确保留 Samsung 21%、Apple 14%、Xiaomi 10% | 直接 `finished`，没有打开 Joplin 创建笔记 | 缺失的是剩余子任务而非早期环境事实；原始任务指令仍在 Context，作者的 process-memory 标签吸收了 planning / termination 错误 | planning / premature-termination 负对照 |
| 003 `RecordAndNameAudio`，UI-TARS-1.5-7B | 无关键跨步事实丢失 | 逐字删除默认文件名，17 步耗尽 | 增加步数或改进文本编辑动作即可修复，根因是 action efficiency / timeout | 明确负对照；不得计入 Memory 失败 |

### 案例 056 的必要性分析

如果 AAPL 价格保持为 226.91，正确动作参数是 `75 × 226.91`；如果价格是 143.92，正确动作参数则是 `75 × 143.92`。事实变化会改变动作参数，故满足反事实行动依赖。

但仍缺一项因果证据：向原系统注入格式匹配、来源明确的正确 AAPL 事实，同时冻结 planner、界面与解码器，是否稳定产生正确输入。公开截图没有回答这一点，也不能预设 143.92 已经存在于某个可定位的 Memory 字段。

### 案例 077 的必要性分析

Wi-Fi control 列表的五项遗漏直接改变最终写入动作的内容。PiP 列表在相同 Agent、相同任务和相邻步骤中被完整写入，只能削弱“Agent 完全不会写列表”的解释，不能证明容量或选择性保留缺陷。

但截图无法排除：Step 7 的视觉解析可能从一开始就只提取了四项。因此必须比较：

1. 只修正 Step 7 的视觉解析；
2. 只替换 commit 前 Memory；
3. 两者都不改，只增加输出 token。

谁首次稳定修复，谁才是根因。

## 4. MaDS 观察性 Pilot：新增的是负证据

对 MaDS 官方释放的 127 个决策记录进行字段级审计：116 条包含 experiences，93 条包含 facts，116 条包含 preconditions，127 条包含 provenance；日志 schema 中独立 validity、verification、recovery 键均为 0。

这只能证明发布日志没有把三类语义保存为独立机器可读字段，不能证明 Agent 内部没有相关推理或能力。自由文本和上游模块仍可能包含这些语义。

在 127 个决策中，识别出 7 个 commit-like 机会：4 个进入购买流程、2 个进入支付验证流程、1 个发送评论。已记录的 8 个局部失败均更符合 grounding、actuation 或 action decoding，`memory-caused = 0/8`。由于样本是精选轨迹且截图仅为 Git LFS pointer，这一结果是负证据，不是总体发生率估计。

最强反例是 case01：Step 14、15 两次尺码点击失败被环境 verifier 发现；Step 16 重试成功选中 38 码后，Step 17 才进入 ¥73.90 待支付页面，Step 18 进入验证码页。这说明：没有显式 recovery 字段不等于没有运行时恢复；也没有证据表明错误 Memory 导致了 unsafe payment。

因此，MaDS 推进的是 `trace auditability-gap hypothesis`，不是 `natural-memory-failure hypothesis`。详细审计见 `stage0b_mads_observational_pilot.md`。

## 5. OSWorld 2.0 + InterruptBench：现象存在性的公开案例证据

2026 年两套独立 benchmark 把证据从“历史事实与后续行为不一致的候选”推进到“更新已到达但行动状态没有同步”的直接轨迹观察：

| 证据 | 关键观察 | 允许结论 | 仍未识别 |
|---|---|---|---|
| OSWorld 2.0 Task 035 | 动态审批与采购规则在执行中变化；Agent 注意到部分晚期更新，却过早关闭信息收集，最终以不完整五行工作集检查采购表 | 环境变化能使早期行动状态失效，不完整工作集会传播到持久 artifact 和 final check | 未持续监控、grounding、Memory、planning、verification 各自贡献 |
| InterruptBench Randyland | 更新直接注入且被 Agent 承认；旧 `From` 字段未修改、路线未重算，最终结果仍依赖旧路线 | `acknowledged update–action state divergence` 真实存在；“更新完全未送达”不足以解释该案例 | Memory、依赖识别、GUI field binding、action execution 与 verification 各自贡献 |

OSWorld 2.0 含 108 个长程任务，69.6% 的人类预计操作时间超过一小时，最强 Agent 在 500-step 条件下仅达 20.6% binary completion；超过 163 分钟的 17 个任务中，所有报告模型 binary completion 均为 0。它证明长程完成存在明显能力边界，但不证明状态失效是唯一根因。

InterruptBench 基于 165 个 human-verified WebArena-Lite seed task，为每个任务构造 Addition、Revision、Retraction 三类人工复核更新，共 495 个场景，并在不中断环境状态的情况下把更新注入执行轨迹。位置实验不是统一的“越晚越差”：Haiku 从 20% 位置的 43.64% 降至 80% 位置的 24.24%，DeepSeek 从 30.30% 降至 24.24%，Opus 却从 47.27% 升至 56.97%。因此只能支持模型相关的 timing sensitivity。

两篇论文均为 2026 arXiv 预印本，不是已录用 CCF-A / B 论文；更新和任务来自可控真实感 benchmark，不是生产现场 telemetry。完整证据和第五轮 battle 见 `stage0c_action_state_failure_evidence.md`。

## 6. 当前定性结论

### 已被较强证据支持

1. OSWorld 2.0 与 InterruptBench 提供跨 benchmark 收敛证据：任务更新后，Agent 有时仍基于旧或不完整状态编辑持久 UI、执行派生计算或进行最终检查。
2. InterruptBench 的直接更新注入和 Randyland 失败案例排除了“更新完全没有被提供”和“Agent 完全没有意识到更新”两种简单解释。
3. 被直接观察到的功能性问题应称为 **action-state propagation / reconciliation failure**，而不是 memory-module failure。
4. MemGUI-Bench 继续提供 Retention 型候选，MaDS、OSWorld Task 052、Task 024 和 Task 008 提供必要的 grounding、timing、verification 与成功保持反例。

### 尚未被证据支持

1. **Memory 因果性未证明。**所有公开案例都没有进行冻结组件的 memory-only replay。
2. **独立流行度未证明。**Task 035 和 Randyland 是作者展示案例；495 是场景规模，不是 495 次 stale-state failure。
3. **自然生产流行度未证明。**两套环境是可控 benchmark，不是现场随机分母。
4. **高风险 commit 子问题未证明。**现有案例仍不足以证明发送、支付、删除、授权等 severity 2–3 决策中存在同类根因。
5. **环境可证伪的必要性未证明。**尚未比较部署可用 re-observation、同证据 reflection 和正确 working state 三者的因果效果。
6. **行动契约有效性未证明。**没有 flat-complete、typed-complete 与 typed + gate 的信息匹配实验。

## 7. 步骤 1 判定

| 命题 | 当前判定 | 原因 |
|---|---|---|
| MemGUI-Bench 包含长程历史依赖任务 | **Pass，dataset property only** | 115/128 为作者 Memory 标签，107/128 同时至少 15 步 |
| 公开案例中存在“来源证据—后续行为”不一致 | **Weak Pass，root cause unresolved** | 056、077 可定位不一致，但没有隔离 Memory、perception 与 action decoding |
| MaDS 公开日志存在 trace auditability gap | **Pass，schema property only** | 没有独立 validity / verification / recovery 键；不能推出内部表示缺少相应语义 |
| 动态更新后存在 acknowledged-update / action-state divergence | **P2+ / Strong Pass** | OSWorld 2.0 Task 035 与 InterruptBench Randyland 跨 benchmark 收敛；后者直接注入并被 Agent 承认 |
| 公开案例中存在 update-to-action inconsistency | **Existence-only Pass** | Randyland 与 Task 035 的官方案例描述显示更新后要求与外部动作、产物或检查不一致；不能估计未干预目录轨迹中的负担 |
| 存在 memory-caused 自然失败 | **Not established** | 0/3 公开案例完成冻结组件的 memory-only replay |
| memory-caused failure 具有非忽略自然覆盖率 | **Not established** | 没有盲标随机分母，作者 taxonomy 存在 Memory 优先归因偏置 |
| 高风险 commit 中存在正 EVSI 的环境 probe | **No supporting case** | 0/2 unresolved M candidate 是高风险或不可逆 commit |
| 步骤 1 是否通过 | **IN PROGRESS / NOT GO** | 只证明案例级存在；必须先完成 OSWorld 2.0 固定目录总体的预注册盲标、缺失边界与 utility 判定，才可能进入步骤 2 |

广义 update-to-action inconsistency 与高风险 epistemic commit 是两个不同问题。前者的公开案例证据不能作为后者的自然发生率、重要性或方法必要性证据。案例级现象存在不构成 Step 1 GO；Memory 根因、环境 probe 必要性和行动契约方法均为 `HOLD`。

## 8. 步骤 2 的最小根因证据门

1. 选择可恢复 checkpoint 的 Task 035 family 或 InterruptBench revision family，保存更新前、更新后和提交前状态；
2. 证明原失败在相同 checkpoint 与配置下至少 3/5 稳定复现；
3. 冻结模型、prompt、history、current observation、token、工具、时延与随机设置；
4. 按 `stage0d_root_cause_identification.md` 运行 observation-bounded G-star、独立持久 store 的 R-star、E-star、P-generic / P-oracle、V-select-star 与 A-star；若都只通过统一 prompt 注入，则必须称为 prompt interventions；
5. R-star 只能处理固定 grounding output，不得注入未打开消息、privileged final truth、task-specific dependency 或每步 salience reminder；
6. R-star 稳定修复只证明充分修复路径；还要用 information-matched flat / structured control、`F-info-bounded-oracle minus R` 和 multiple-sufficient-causes 审计判断其独立性与 composite 条件必要性；
7. 若 E-star 首次修复，归为 active monitoring / sensing；若 P-star 或 V-star 首次修复，课题必须相应改名；
8. 对一般性结论，再从完整轨迹中预注册抽取成功与失败，双标 `delivered → acknowledged → dependency invalidated → UI repaired → recomputed → checked` 各阶段的条件失败率。

## 9. 后续可证伪停止条件

满足任一条件，广义课题也应停止或改题：

- 在分层自然样本中，R3 memory-only 干预几乎从不首次修复；
- 大多数候选都在 R1/R2 被修复，说明主因是预算或 grounding；
- 正确 Memory 只能与 oracle plan 一起修复，说明 planning 才是主要瓶颈；
- Memory 缺陷只存在于人为挑选的“记忆任务”，在自然 GUI 工作流中覆盖率接近零；
- 在匹配任务长度与难度后，Memory 标签与失败不再相关。
