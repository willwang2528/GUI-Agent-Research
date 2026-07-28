# ARIS Technical Report — Keshav Three-Pass Reading Record

> reading_status: `PASS-1 COMPLETE / PASS-2 CORE-EVIDENCE AUDIT COMPLETE / PASS-3 HARNESS TRANSFER RECONSTRUCTED`  
> read_at: `2026-07-28`  
> paper: `ARIS: Autonomous Research via Adversarial Multi-Agent Collaboration`  
> arXiv: `2605.03042`  
> official_url: `https://arxiv.org/abs/2605.03042`  
> local_pdf: `source_provenance/papers/aris_2605.03042.pdf`

## 1. 身份与证据地位

- Authors: Ruofeng Yang, Yongcan Li, Shuai Li
- Year: 2026
- Type: open-source research-harness technical report
- Venue: arXiv preprint；未正式发表于 CCF-A/B
- Code: `https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep`
- 本课题地位：`METHOD-REFERENCE / NOT CORE GUI-MEMORY EVIDENCE`

它满足 2026 时间要求，但不满足正式高水平 venue 筛选。保留原因是它直接定义了本课题正在采用的研究 harness、跨角色审计和持久化科研状态；不能用来证明 GUI Memory 科学命题。

## 2. Pass 1 — Keshav 5C

### Category

系统架构与早期部署经验报告，不是受控 benchmark 或因果效果论文。

### Context

位于 autonomous research agent、harness engineering、multi-agent debate、self-refinement、persistent research memory 和 scientific assurance 的交叉处。它把“模型能力”与“围绕模型的 harness”分开。

### Correctness

设计逻辑一致，但核心保守假设：

```text
Any long-term task performed by a single agent is unreliable.
```

不是经验证定律。cross-family、adversarial bandit 和 two-player game 的联系是设计 analogy，不是 regret/equilibrium 证明。论文自己明确承认：

- 所有 deployment outcomes 是 observational；
- 没有 controlled evaluation；
- 单次 overnight run 不能证明 cross-family 优于 same-family；
- audit 是 advisory safety net，不是 formal verification；
- reviewer bias 和 over-iteration 可能被放大。

### Contributions

1. 三层 research harness：execution、orchestration、assurance；
2. persistent research wiki 和模块化 Markdown skills；
3. experiment integrity → result-to-claim → paper-claim 三阶段 evidence cascade；
4. executor/reviewer 分离和 fresh zero-context claim audit；
5. prototype self-improvement loop，修改须经 reviewer approval。

### Clarity

架构图、artifact contracts、audit cascade 和 limitations 清楚。最大的限制也写得明确，因此适合作为 workflow reference，而不是效果证据。

## 3. Pass 2 — Claim / Evidence / Ceiling

| Claim | 论文证据 | 证据类型 | 允许上限 |
|---|---|---|---|
| ARIS 可组织完整研究 workflow | 65+ skills、5 workflows、3 tested + 3 adapted platforms | implementation footprint | 工程可用性 |
| review loop 可驱动实验与删减 unsupported claims | 单次约 8 小时 trajectory、4 轮、score 5.0→7.5、20+ experiments | observational case | 一次真实流程可运行 |
| cross-family review 更可靠 | 无 compute-matched controlled comparison | hypothesis / design choice | 不得声称因果优势 |
| evidence cascade 能保证正确 | 报告 common failure checks，但无完整 error-detection benchmark | advisory mechanism | 可降低部分风险，不是形式验证 |
| persistent wiki 改善 long-horizon research | 架构与部署描述，无独立 ablation | mechanism proposal | 可保存状态，不证明提升 |

核心第一性问题不是“论文写得慢”，而是：

```text
长期执行器既生产 artifact 又解释 artifact
→ 后续阶段继承同一 framing 与未核验 claim
→ 可能出现 plausible unsupported success
```

ARIS 的直接机制是把状态外显为 artifacts/claim ledger，并把生产、证据检查和主张审计分给不同角色。

## 4. Pass 3 — 虚拟复现与假设攻击

### 最小虚拟实现

```text
Problem Anchor
→ versioned intermediate artifacts
→ executor produces candidate claim
→ integrity reviewer checks raw evidence/code
→ result-to-claim mapper assigns supported/partial/invalidated
→ fresh reviewer checks manuscript against ledger/raw files
→ unresolved fail blocks downstream claim
```

当前 workspace 已实现的对应物：

- `refine-logs/round-0-problem-anchor.md`
- `idea-stage/docs/research_contract.md`
- `refine-logs/REFINE_STATE.json`
- `refine-logs/EXPOSURE_ROLE_LEDGER.md`
- Round 1–3 adversarial review；
- checkpoint、hash manifest 和可恢复归档。

### ARIS 原设计不足以直接解决本课题的地方

1. 不同模型 family 不等于 outcome-blind；reviewer 仍可能看到泄漏的 task/result identity。
2. fresh thread 不等于 independent evidence；同一公开 URL 可回查 outcome。
3. advisory audit 不会自动阻止错误 claim；本课题需要 fail-closed gate。
4. research wiki 保存历史，不保证旧事实被环境证伪、依赖被传播或动作被修复。
5. ARIS 没有证明跨模型 review、persistent memory 或 audit cascade 的独立因果效应。
6. 单次 reviewer score 变化既不是 scientific quality gold label，也不是 capability boundary。

### 对本课题的有效迁移

| ARIS primitive | 本课题采用 | 必须加强 |
|---|---|---|
| persistent research state | checkpoint、protocol、claim status | typed provenance、invalidity 和 hash-chain |
| modular workflows | 七步 gate | 前一步失败自动锁死后一步 |
| executor/reviewer split | 多 subagent battle | exposure ledger、无网络净化 packet、角色不可复用 |
| evidence-to-claim cascade | Type-A/Type-B、claim ladder | schema-first validator、raw environment evidence、fail-closed verdict |
| fresh claim audit | Round 4 reproduction role | 独立负例与可重运验证器 |

## 5. 对中心 GUI Memory 命题的影响

ARIS 提供的是“如何不让科研过程自我证明”的方法，不是“GUI Agent 为什么需要 Memory”的答案。

它对当前课题最重要的启发是结构同构：

```text
ARIS:
claim 必须绑定仍然有效的 evidence，失效后下游文本必须降级

GUI Agent hypothesis:
action 必须绑定仍然有效的 world propositions，失效后下游 obligations 必须传播并恢复
```

这只是可迁移的 architecture analogy。要把它变成科学贡献，仍必须独立证明：

1. GUI 自然轨迹中存在 pure-world update-to-action burden；
2. persistent state / dependency repair 是不可被其他根因替代的因果边；
3. typed contract 在等信息、等预算下产生独立效应；
4. 效应改变预注册难度轴上的 frontier 或 scaling，而不只是平均成功率。

## 6. 最终裁决

```text
ADOPT:
Problem Anchor
versioned artifacts
role separation
evidence-to-claim gate
fresh adversarial audit
recoverable state

DO NOT ADOPT AS EVIDENCE:
single-agent unreliability as a law
cross-family superiority
reviewer score as quality
observational adoption as causal success
research wiki as proof that Memory works
```
