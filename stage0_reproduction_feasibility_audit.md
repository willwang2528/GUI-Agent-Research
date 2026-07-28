# Stage 0：复现与实验可行性审计

> 审计目标：判断当前工作区与本机环境能否支持步骤 1–4 的公开轨迹分析、冻结组件 replay 和端到端实验；明确每种实验允许得出的证据结论。
>
> 审计日期：2026-07-22

## 1. 结论摘要

当前 Apple Silicon Mac 可以完成：

- MemGUI 任务定义、聚合失败统计和静态案例审计；
- MaDS 精选执行记录的离线结构化分析；
- 不依赖模型的标注协议 pilot；
- 在补充一个冻结多模态模型 API 和少量完整截图后，执行小规模决策级 counterfactual replay。

当前不能完成：

- MemGUI-Bench 官方 Linux/KVM 环境中的端到端实验；
- AgentProg 原论文实验的忠实 memory-only replay；
- LongHorizonUI 官方 offline benchmark 的可复现实验；
- 仅凭三个 memory failure 截图对 memory 失效作因果归因。

核心原因不是单纯“代码跑不起来”，而是公开材料没有同时提供忠实 replay 所需的完整变量。

一个可识别的冻结组件 replay 至少需要：

1. 当时的完整 GUI 观测；
2. 截止该步的动作历史；
3. 组件实际收到的旧 memory 或 belief；
4. 原始 prompt 和输入拼接方式；
5. 固定模型版本、解码参数及模型输出；
6. 动作后的环境结果或独立风险标签。

如果缺少这些变量，离线实验最多能支持机制 plausibility 或决策敏感性结论，不能直接推出端到端任务成功率。

## 2. 本机能力审计

### 2.1 已具备

| 能力 | 当前状态 |
|---|---|
| 操作系统 | macOS 26.2，Apple Silicon ARM64 |
| Python | `/opt/homebrew/bin/python3.11`，版本 3.11.15 |
| Python 环境工具 | `uv 0.11.29` |
| Java | Java 21 |
| Node.js | 已安装 |
| 可用磁盘 | 约 60 GiB |

### 2.2 当前缺失

| 依赖 | 状态 | 影响 |
|---|---|---|
| Docker | 未安装 | 无法启动官方容器环境 |
| ADB / Android SDK | 未安装 | 无法连接 Android 真机或模拟器 |
| QEMU | 未安装 | 无法使用对应虚拟化路径 |
| Xvfb | 未安装 | 无法运行依赖虚拟显示的 Linux GUI 容器 |
| VMware `vmrun` | 未安装 | 无法使用 OSWorld 推荐的 Apple Silicon VMware 路线 |
| Git LFS | 未安装 | MaDS 多数截图仍为 LFS pointer |
| OpenAI/Gemini/Ark API | 环境变量均未配置 | 无法执行模型调用或 agent evaluation |

环境复核命令：

```bash
uname -a
uname -m
sw_vers
command -v python3.11
python3.11 --version
command -v uv
uv --version
command -v docker
command -v adb
command -v qemu-system-x86_64
command -v Xvfb
command -v vmrun
command -v git-lfs
df -h /Users/will/research/gui_agent_memory /private/tmp
```

## 3. 官方项目硬依赖与可复现性

### 3.1 MemGUI-Bench

- 官方代码：[MemGUI-Bench](https://github.com/lgy0404/MemGUI-Bench)
- 本地代码：`external/MemGUI-Bench`

官方运行路径依赖：

- Python 3.12；
- Linux 主机；
- Docker；
- KVM；
- privileged container 权限；
- agent 模型 API；
- step-description 和 final-decision 评测模型 API。

Apple Silicon macOS 不能提供与官方 Linux/KVM 路线等价的执行环境。安装 Docker Desktop 也不能消除虚拟化架构差异。

当前本地可用材料包括：

- `external/MemGUI-Bench/data/memgui-tasks-all.csv`
- `external/MemGUI-Bench/data/memgui-tasks-40.csv`
- `external/MemGUI-Bench/docs/images/failure-analysis/partial-memory-hallucination.png`
- `external/MemGUI-Bench/docs/images/failure-analysis/process-memory-hallucination.png`
- `external/MemGUI-Bench/docs/images/failure-analysis/output-memory-hallucination.png`
- `external/MemGUI-Bench/docs/images/failure-analysis/execution-timeout.png`
- `external/MemGUI-Bench/docs/failure-analysis.html`

这些材料可以支持任务分层、失败分类和标注协议校准，但没有提供静态案例对应的完整旧 memory、原始模型输入、动作序列和对照干预，因此不能构成 memory 失效的因果证明。

完整轨迹压缩包单包约为 21–43 GiB。当前本机仅有约 60 GiB 可用空间，不适合同时下载和解压多个轨迹包，也仍然不能解决 Linux/KVM 和模型 API 缺失。

### 3.2 AgentProg

- 官方代码：[AgentProg](https://github.com/MobileLLM/AgentProg)
- 本地代码：`external/AgentProg`

硬依赖包括：

- Python 3.11+；
- ADB 与 Android 真机或模拟器；
- Gemini 2.5 Pro；
- Ark/UI-TARS 一类 GUI grounding 服务；
- 官方 Docker 路线中的 privileged、Xvfb 和 x86_64 Android emulator。

源码中的 belief state 主要由 `belief_state_str` 和 `plan` 两个字符串组成。更新过程要求模型结合当前截图与已有 belief 重新生成状态。

公开仓库没有发布原实验每一步的：

- 截图与完整 observation；
- 更新前 belief；
- 原始模型回复；
- 固定模型 checkpoint 或不可漂移的 API snapshot；
- belief 修改后的环境结果对照。

因此，可以抽取其 prompt 并构造新的 belief-update probe，但这属于新建的组件诊断实验，不能称为 AgentProg 原实验的忠实 memory-only replay。即使输入保持不变，在线模型 API 漂移也可能造成输出差异。

### 3.3 LongHorizonUI

- 官方代码：[LongHorizonUI](https://github.com/kane2kang/LongHorizonUI)
- 本地代码：`external/LongHorizonUI`

README 描述了 offline screenshot simulation，但当前发布物存在以下阻塞：

- README 要求安装根目录 `requirements.txt`，仓库实际没有该文件；
- 数据集下载地址仍是占位链接；
- 本地 `data/` 不包含 LongGUIBench 的完整截图与任务；
- 部分控制器和检测器仍包含 `pass` 或 `NotImplemented`；
- 模型调用仍需要 OpenAI、Azure OpenAI 或 Gemini Vertex 配置。

因此，当前发布物可以做源码审计，但不能据此复现官方 offline benchmark。

## 4. MaDS 离线记录审计

- 官方代码与数据：[MaDS](https://github.com/PcCin37/MaDS)
- 审计版本：官方仓库 `main` 分支，提交 `99c1bf...`
- 本地审计目录：`external/MaDS`

### 4.1 已核验统计

在 `Data/execution_traces/01_ours_mads` 的 10 个精选案例中：

| 字段 | 数量 |
|---|---:|
| `*_analysis.json` 决策记录 | 127 |
| 含非空 `experiences` | 116 |
| 含非空 `facts` | 93 |
| 含非空 `experience_guidance` | 116 |
| 含 `model_response` | 127 |
| 含 `parsed_action` | 127 |

这些记录通常包含：

- `global_task`
- `current_subtask`
- `history_knowledge`
- `step_experiences`
- `screenshot_path`
- `model_response`
- `parsed_action`
- `absolute_coordinates`

逐步 `step_*.json` 和 `step_log.jsonl` 还包含 action、success、verifier reason、前后截图路径和时间戳。

### 4.2 统计复核命令

```bash
python3.11 - <<'PY'
import collections
import json
import pathlib

root = pathlib.Path("external/MaDS/Data/execution_traces/01_ours_mads")
stats = collections.Counter()

for path in root.rglob("*_analysis.json"):
    record = json.loads(path.read_text())
    memories = record.get("step_experiences") or {}
    stats["total"] += 1
    stats["nonempty_experience"] += bool(memories.get("experiences"))
    stats["nonempty_facts"] += bool(memories.get("facts"))
    stats["nonempty_guidance"] += bool(
        (memories.get("experience_guidance") or "").strip()
    )
    stats["has_model_response"] += bool(
        str(record.get("model_response") or "").strip()
    )
    stats["has_parsed_action"] += bool(record.get("parsed_action"))

print(dict(stats))
PY
```

预期输出：

```text
{
  'total': 127,
  'nonempty_experience': 116,
  'nonempty_facts': 93,
  'nonempty_guidance': 116,
  'has_model_response': 127,
  'has_parsed_action': 127
}
```

截图是否为 Git LFS pointer 可通过以下命令复核：

```bash
file external/MaDS/Data/execution_traces/01_ours_mads/case01/img/screenshot_step2.png
sed -n '1,3p' external/MaDS/Data/execution_traces/01_ours_mads/case01/img/screenshot_step2.png
```

当前返回的是 Git LFS pointer 文本，而不是 PNG 二进制图像。`04_androidarena` 中有 18 个 HTML 文件，部分视觉信息以 base64 形式嵌入 HTML，可用于不依赖 Git LFS 的小规模材料构造。

### 4.3 MaDS 数据仍然不能直接证明什么

MaDS 提供的是每个系统各 10 个定性案例，而不是从完整评测总体中随机采样的自然失败轨迹。因而：

- 可以验证字段、建立 parser 和完善标注协议；
- 可以展示 retrieved memory 如何进入动作决策；
- 不可用这 10 个案例估计总体失败率；
- 不可直接把 memory 与 verifier failure 的相关性写成因果效应；
- 没有配对 intervention 时，不可声称删除或修改 memory 会提高任务成功率。

## 5. 最小可执行 Pilot A

### 5.1 目标

在没有 API、Android 模拟器和完整截图的条件下，验证“行动契约”问题是否具有可操作的标注定义，并找出适合后续干预实验的决策点。

### 5.2 数据

- MaDS 的 127 个逐步 analysis 记录；
- 对应的 step log、verifier reason 和 success；
- MemGUI 三个 memory hallucination 案例；
- MemGUI timeout 案例作为非 memory failure 校准项；
- MemGUI 任务 CSV 用于补充任务类型分层。

### 5.3 标注字段

每个决策点至少标注：

1. 当前动作是否依赖 retrieved memory；
2. memory 中被当成行动前提的具体事实；
3. 该事实是否能从当前 observation 直接验证；
4. Agent 是否在执行前主动 probe；
5. 动作是否可逆以及错误成本；
6. verifier 检查的是局部界面变化还是长期语义目标；
7. 前提失效后是否存在明确 recovery；
8. memory 与当前 app、页面状态和目标是否发生语义错配。

### 5.4 输出

- `memory → implicit commitment → action → verifier outcome` 决策表；
- 可复用标注手册；
- 双人标注一致性；
- 供 Pilot B 使用的高风险决策点列表；
- 静态案例中的替代解释清单。

### 5.5 允许的结论

Pilot A 只能提供描述性机制证据，例如：

> 在公开案例中，可以识别出 retrieved memory 被作为未经验证的行动前提使用的决策点。

Pilot A 不允许报告 memory 的因果失败率或端到端收益。

## 6. 最小可执行 Pilot B

### 6.1 前置条件

- 一个版本可固定的多模态模型 API 或本地 checkpoint；
- 20–30 个具有完整当前截图的决策点；
- 每个决策点的 task、subtask、history 和专家安全动作标签；
- 固定 prompt、temperature、采样次数与 token 预算。

截图可优先从 MaDS 内嵌 HTML 中选择；其余截图仅按需从官方 Git LFS 获取，避免下载完整大包。

### 6.2 配对干预

固定当前截图、当前子任务、动作历史、模型和解码参数，只替换 memory 输入：

1. 原始 retrieved memory；
2. 删除 memory；
3. 修正后的 memory；
4. stale 或 contradictory memory；
5. 契约式 memory：明确必要前提、证据来源、验证操作和失败恢复。

### 6.3 指标

- 直接执行率；
- 主动验证率；
- stale-memory 诱导率；
- 高风险错误行动提交率；
- 可逆动作选择率；
- 与专家 safe-action/probe 标签的一致率；
- token、时延和额外模型调用数。

### 6.4 允许的结论

Pilot B 可以支持：

> 在固定观测和模型的配对决策实验中，改变 memory 表示会改变 Agent 的验证、执行与恢复选择。

它仍然不能单独支持：

> 契约式 memory 提高了长程 GUI 任务的端到端成功率。

该结论必须通过可重置环境中的 live paired evaluation 获得。

## 7. 证据边界

### 7.1 禁止的因果表述

以下表述没有被当前公开材料支持：

> 三个 MemGUI failure 截图证明现有 memory 导致长程 GUI 失败。

原因是没有 memory intervention、无同一状态下的无-memory 对照，也没有排除 grounding、规划、UI 延迟和 verifier 误判等替代解释。

### 7.2 当前允许的表述

静态材料允许写：

> 公开案例显示 memory hallucination 可能进入行动生成链条，因此有必要对 memory 内容进行受控干预。

Pilot B 完成后允许写：

> 在固定 observation 和模型的配对实验中，memory 的真实性、时效性与可验证结构显著影响 action policy。

只有 live paired evaluation 完成后才允许写：

> 契约式 memory 降低了错误行动提交率，并提高了端到端任务成功率。

## 8. Go / No-Go 决策

| 项目 | 决策 | 说明 |
|---|---|---|
| MemGUI 任务与静态失败分类 | Go | 可做任务分层和现象审计 |
| MaDS 观察性机制 Pilot A | Go | 当前本机可以直接运行 |
| 决策级 counterfactual Pilot B | Conditional Go | 需要完整截图和冻结模型 API |
| AgentProg 忠实 memory-only replay | No-Go | 缺原始逐步 belief、观测、模型回复和环境结果 |
| LongHorizonUI 官方 offline benchmark | No-Go | 缺依赖清单、公开数据与完整实现 |
| MemGUI 官方端到端评测 | Current-machine No-Go | 需要 Linux、KVM、Docker、API |
| 用静态案例证明 memory 因果失败 | No-Go | 只能证明现象存在，不能识别因果效应 |

## 9. 推荐的下一步门槛

先执行 Pilot A，不立即实现完整方法。只有同时满足以下门槛，才进入 Pilot B：

- 标注者能稳定识别“必要前提、可观测证据、错误成本和恢复动作”；
- 双人标注一致性达到预先规定的可接受水平；
- 至少获得 20 个具有完整截图和明确专家标签的决策点；
- 配对干预除 memory 外没有改变其他输入；
- 预注册允许报告的结论仅限决策级因果效应。

只有 Pilot B 观察到稳定的 stale-memory 诱导和契约式 memory 缓解效应后，才值得申请 Linux/KVM 机器并进入 MemGUI 或 AndroidWorld 的 live paired evaluation。
