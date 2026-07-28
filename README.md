# GUI Agent Memory Research

研究问题：

> 长程 GUI 控制的 memory 是否必须成为可被环境证伪的行动契约；只有当 Agent 知道哪些事实必须仍然为真、为何为真以及失效后如何恢复，Memory 才可能改变能力边界。

当前处于七步研究链的 Step 1：证明问题现象与负担。现阶段结论是：

```text
FRAME-READY
DETAIL-AVAILABILITY-PARTIAL
MEASUREMENT IMPLEMENTATION NOT READY
NO STEP 1 GO
NO SYNTHETIC PROTOCOL FREEZE
NO BLOCK-A DRY RUN
```

Round 6 当前推进到可恢复的 WIP：

- bounds/certificate synthetic mechanics：实现测试 33/33，通过独立 bounded replay 22/22；
- Stage A v1：X58–X60 已由 fresh reviewer 复放，但 X62–X64 分别击穿 disagreement adjudication、semantic entailment 与 denominator preservation；
- Stage A v2：schema/validator 已开始迁移到 R/C/P/E/M 五账本与双 grounding mode；builders/fixtures 尚未迁移，当前 79 tests 为 70 failures + 1 error，明确是不可接受的 WIP；
- 真实 OSWorld2 归档源 projection adapter：48 页、47 replay、1 explicit no-step、9,138 steps，12/12 tests PASS；只证明归档 HTML 的 literal projection，不证明完整 production authority；
- production measurement、synthetic freeze、Block A 与 Step 1 GO：全部仍未获准；
- Python 3.12.13 解释器已建立，精确依赖安装仍被审批服务内部错误阻塞，当前回归仍来自 Python 3.9.6。

入口：

- 七步状态与关键结论：[`research-ledger/`](research-ledger/)
- 当前可恢复状态：[`research-ledger/CURRENT_GOAL_STATE.json`](research-ledger/CURRENT_GOAL_STATE.json)
- 最新 checkpoint：[`research-ledger/checkpoints/2026-07-28T130324+0800-step1-round6-wip-checkpoint.md`](research-ledger/checkpoints/2026-07-28T130324+0800-step1-round6-wip-checkpoint.md)
- 当前研究契约：[`idea-stage/docs/research_contract.md`](idea-stage/docs/research_contract.md)
- Step 1 预注册：[`stage0f_osworld2_natural_burden_preregistration.md`](stage0f_osworld2_natural_burden_preregistration.md)
- Step 1 决策卡：[`stage0f_step1_decision_card.md`](stage0f_step1_decision_card.md)
- 对抗审计：[`refine-logs/`](refine-logs/)
- 来源 hash 与可获得性审计：[`source_provenance/`](source_provenance/)

Git 只保存研究文本、协议、代码、schema、测试与 manifest。外部仓库、原始轨迹详情页、PDF 和历史压缩备份不上传；其身份由 manifest/hash 锚定。

研究历史目标：[`willwang2528/GUI-Agent-Research`](https://github.com/willwang2528/GUI-Agent-Research) 的 `main`。恢复时以 `research-ledger/CURRENT_GOAL_STATE.json` 与其中指向的最新 checkpoint 为准。
