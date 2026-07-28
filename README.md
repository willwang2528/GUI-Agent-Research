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

Round 5 只推进了测量机械层：

- bounds/certificate synthetic mechanics：实现测试 33/33，通过独立 bounded replay 22/22；
- full-block Stage A：实现测试 79/79、Ajv strict 27/27，X58–X60 已修复，尚待 fresh independent replay；
- production measurement、synthetic freeze、Block A 与 Step 1 GO：全部仍未获准；
- Python 3.12.13 解释器已建立，精确依赖安装仍被审批服务内部错误阻塞，当前回归仍来自 Python 3.9.6。

入口：

- 七步状态与关键结论：[`research-ledger/`](research-ledger/)
- 当前可恢复状态：[`research-ledger/CURRENT_GOAL_STATE.json`](research-ledger/CURRENT_GOAL_STATE.json)
- 最新 checkpoint：[`research-ledger/checkpoints/2026-07-28T123302+0800-step1-round5-checkpoint.md`](research-ledger/checkpoints/2026-07-28T123302+0800-step1-round5-checkpoint.md)
- 当前研究契约：[`idea-stage/docs/research_contract.md`](idea-stage/docs/research_contract.md)
- Step 1 预注册：[`stage0f_osworld2_natural_burden_preregistration.md`](stage0f_osworld2_natural_burden_preregistration.md)
- Step 1 决策卡：[`stage0f_step1_decision_card.md`](stage0f_step1_decision_card.md)
- 对抗审计：[`refine-logs/`](refine-logs/)
- 来源 hash 与可获得性审计：[`source_provenance/`](source_provenance/)

Git 只保存研究文本、协议、代码、schema、测试与 manifest。外部仓库、原始轨迹详情页、PDF 和历史压缩备份不上传；其身份由 manifest/hash 锚定。

研究历史目标：[`willwang2528/GUI-Agent-Research`](https://github.com/willwang2528/GUI-Agent-Research) 的 `main`。以包含上述最新 checkpoint 的远端 `main` commit 为恢复入口。
