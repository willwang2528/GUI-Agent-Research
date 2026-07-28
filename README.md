# GUI Agent Memory Research

研究问题：

> 长程 GUI 控制的 memory 是否必须成为可被环境证伪的行动契约；只有当 Agent 知道哪些事实必须仍然为真、为何为真以及失效后如何恢复，Memory 才可能改变能力边界。

当前处于七步研究链的 Step 1：证明问题现象与负担。现阶段结论是：

```text
FRAME-READY
DETAIL-AVAILABILITY-PARTIAL
MEASUREMENT IMPLEMENTATION NOT READY
STAGE A V2 + IDENTITY DRAFT SCHEMA MECHANICS GREEN
PROTOCOL REVISE
LOCAL ARCHIVED BYTES ONLY
MATCHER FREEZE REJECTED
NO STEP 1 GO
NO SYNTHETIC PROTOCOL FREEZE
NO BLOCK-A DRY RUN
```

Round 8 当前推进到可恢复状态：

- bounds/certificate synthetic mechanics：实现测试 33/33，通过独立 bounded replay 22/22；
- Stage A v2：无冻结 aggregator 的 independent paths 已强制 `E=0/M=1`，非法 primary 注入以专用错误拒绝；both-zero location 显式保留 `d=1`；
- matcher 可识别性：greedy 反例把 agreement 从 0.5 改为 1.0；`K2,2` 中两个 maximum matchings 把 exact agreement 从 2 改为 0；因此 maximum-cardinality 与 deterministic tie-break 不等于 semantic identity；
- pairwise partial-identification spec 与两个 draft schema 获得窄接受；但 value-channel leakage、raw identity/hash/selector/atomicity authority、完整 pair ledger、review isolation 与 bounds integration 仍未实现；
- 当前回归：Stage A + identity drafts + protocol/detail/ARIS 118/118；archived adapter + bounds 55/55；
- 证据上限仍是指定 synthetic mechanics：没有 executable redaction、frozen case matcher、human dual identity/entailment records 或 external raw/time/access/role authority，协议继续 `REVISE`；
- OSWorld2 adapter：22/22 tests PASS；只证明当前本地 48 HTML bytes 可投影为 47 replay、1 explicit no-step、9,138 steps；source origin、trusted capture time、screenshot/observation 与 production authority 均未证明；
- production measurement、synthetic freeze、Block A 与 Step 1 GO：全部仍未获准；
- Python 3.12.13 解释器已建立，精确依赖安装仍被审批服务内部错误阻塞，当前回归仍来自 Python 3.9.6。

入口：

- 七步状态与关键结论：[`research-ledger/`](research-ledger/)
- 当前可恢复状态：[`research-ledger/CURRENT_GOAL_STATE.json`](research-ledger/CURRENT_GOAL_STATE.json)
- 最新 checkpoint：[`research-ledger/checkpoints/2026-07-28T145053+0800-step1-round8-checkpoint.md`](research-ledger/checkpoints/2026-07-28T145053+0800-step1-round8-checkpoint.md)
- 当前研究契约：[`idea-stage/docs/research_contract.md`](idea-stage/docs/research_contract.md)
- Step 1 预注册：[`stage0f_osworld2_natural_burden_preregistration.md`](stage0f_osworld2_natural_burden_preregistration.md)
- Step 1 决策卡：[`stage0f_step1_decision_card.md`](stage0f_step1_decision_card.md)
- 对抗审计：[`refine-logs/`](refine-logs/)
- 来源 hash 与可获得性审计：[`source_provenance/`](source_provenance/)

Git 只保存研究文本、协议、代码、schema、测试与 manifest。外部仓库、原始轨迹详情页、PDF 和历史压缩备份不上传；其身份由 manifest/hash 锚定。

研究历史目标：[`willwang2528/GUI-Agent-Research`](https://github.com/willwang2528/GUI-Agent-Research) 的 `main`。本轮将 Round 8 科学快照和最新状态推送到该分支；最终远端验证结果记录在 `research-ledger/CURRENT_GOAL_STATE.json`。恢复时以该 JSON 与其指向的 checkpoint 为准。
