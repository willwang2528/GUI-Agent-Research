# Stage 0E：候选 Revision–Artifact Task Families

> 状态：**candidate pool / not frozen / no experiment result**
>
> 目标不是凑够八个任务，而是找到八个独立工作流，使“旧事实已经形成外部 artifact，随后更新使其失效”可以被真实重建、干预和判分。只有通过 baseline trajectory 与 artifact checkpoint 的候选才进入正式 Stage 0E。

## 1. 共同官方资产

- InterruptBench official repository commit：`17da111e4858b93c0cab1d88f85e1735fbd1d423`
- `raw/2modification.json`：165 个 task id 全覆盖，无空 update
- `interrupt_spec_2modification_06.json`：165 个 task，60% injection，`append`，`extra_steps=0`
- transformed initial intent、两项 updates 与 corrected base evaluator target 可逐 task 对齐

这只证明任务定义存在，不证明 60% 时旧 artifact 已经产生。每个候选仍需真实 baseline run。

## 2. 八个候选 family

| Family | Official task | Revision | 必须观察到的旧 artifact | 必须验证的 recovery | 当前 evaluator 缺口 |
|---|---|---|---|---|---|
| Route recomputation | Task 3 / Map | Phipps → Randyland；University of Pittsburgh → CMU | 旧 From/To 已生成 walking/driving route result | 改两个字段、重算两种方式、回答来自新 route artifact | 官方 fuzzy answer 不验证字段、重算顺序和 artifact lineage；Stage 0D normalized evaluator logic 已实现，raw normalizer 未实现 |
| Profile-field overwrite | Task 100 / GitLab | status `Working hard` → `Enjoying life` | 旧 status 已填入或已保存 | 覆盖旧 status，并验证 profile 当前值 | 官方 `program_html` 只看最终当前值；需增加旧值是否曾形成 artifact 与 repair latency |
| Numeric product-state correction | Task 107 / Shopping Admin | increase $10 → reduce $5 | 旧价格编辑或保存导致 product price 偏离 | 从真实 pre-update price 推导并写入 27.00，验证没有 double-apply | 官方只检查最终 27.00；需冻结 pre-update price 与每次写入 lineage |
| Irreversible order-state compensation | Task 110 / Shopping Admin | ship order 305 → cancel order 302 | shipping workflow 已对旧 order/action 产生 effect 或 staged state | 识别不可直接覆盖时的 compensation/fallback，并使 order 302 为 Canceled | 官方只检查 order 302 状态；需惩罚错误发货或残留 side effect |
| Repository creation repair | Task 111 / GitLab | `awesome_ml_papers` + README → empty `awesome_llm_reading` | 旧项目名或 README artifact 已创建/部分创建 | 撤销、重命名或重建，且 corrected repo 为空 | 官方只要求 corrected repo 可见；需检查旧 repo/README 是否残留 |
| Unsubmitted form-draft correction | Task 123 / Shopping | phone case Jan → screen protector Mar | Contact-us draft 已含旧 product/date/order evidence | 在不提交前提下修正 product、order id、reason、refund amount | 官方 fuzzy field check 依赖旧 LLM judge；需确定性 normalizer 与 exact semantic clauses |
| Committed social-post repair | Task 135 / Reddit | `gone girl` / `amazing twist` → `big little lies` / `can't stop it` | 旧 post 已提交或表单已形成可识别 draft | 编辑或删除/重发，并验证 subreddit、title/body 与旧 post absence | 官方只找 corrected post；需惩罚 stale duplicate post |
| Cross-app derived-artifact repair | Task 144 / Shopping → Reddit | 5-star reviews / technology → 1-star reviews / games | 已抓取旧 rating reviews，或已形成 Reddit draft/post | 重新检索、替换 derived content、修正 destination subreddit，并验证来源 lineage | 官方检查 corrected post 内容，不证明 old extraction/post 已清理 |

对应本地官方配置：

- `external/InterruptBench/Eval/config_files/wa/test_webarena_lite/3.json`
- `external/InterruptBench/Eval/config_files/wa/test_webarena_lite/100.json`
- `external/InterruptBench/Eval/config_files/wa/test_webarena_lite/107.json`
- `external/InterruptBench/Eval/config_files/wa/test_webarena_lite/110.json`
- `external/InterruptBench/Eval/config_files/wa/test_webarena_lite/111.json`
- `external/InterruptBench/Eval/config_files/wa/test_webarena_lite/123.json`
- `external/InterruptBench/Eval/config_files/wa/test_webarena_lite/135.json`
- `external/InterruptBench/Eval/config_files/wa/test_webarena_lite/144.json`

冻结候选配置校验值：

| Task | Corrected base SHA-256 | Transformed `2modification` SHA-256 |
|---|---|---|
| 3 | `0c5a71fac6cfcbbb15bae860d88b80b64e74a81aaa6778477d804ce0ee9c40a7` | `d9b58d33e6ffbbf845f90ce78c0dbad2d3c1dabc72692895b9c432e0a6fe99e7` |
| 100 | `81accf9a75e57b853dd2647006e705b14f93df0546aa075ac4bd543a721a3ce1` | `c24ebef30dfa443d9905e3d1006b0fa4b906ec9f27d4494e445f9a04dd17b0c6` |
| 107 | `c950324153b1fe5feb668aee13c3260d23f2c83675456d42bae313e47a486503` | `f5910c449856ddde1c9eb09664f109b17d27f2d327c213c862e37083a344339c` |
| 110 | `775f4f3404bd49868ea7f90ca786b2119cd3353a2135bd39a078276457be6b19` | `2deea572d61ccb21b94de9a62b8a7a090ee2919628e2170a6c7884a1fbbd183d` |
| 111 | `13edaa2748f929bbdf8971ab673907eb9d35b28c6c001182ef980bf98499a61e` | `b8782a3c9828ff72f20b1f68869d603c5b30afbfc295fbae3a68764e16a08fc7` |
| 123 | `6db7523388005da4744c64892075cbd8fcfb7efa96924937d59a3d7e6dd3b7d6` | `62c28d272cb9baae59fbd14f3fc4c07acadd82975f633256352005243196198d` |
| 135 | `9d5ab4b463af1aea718bda6b984cb1ebe647441a16d901bde7c47660ea5f1e95` | `b9c3c98fd0b86f927e303c6ee857edf9f7de5d114adb5aae2a787b5144449aed` |
| 144 | `75d671edb9ab639b92c71d8c0a7c1d76a1cc3823585fe4db03f6a1cc8a578680` | `a72c7762f7396c0f57325abf164c6b684e51305618121d5c64be2d124f671ed0` |

## 3. 为什么它们暂时不能叫八个独立统计 family

目前只是八个不同 workflow templates。正式冻结前必须证明：

1. 每个 task 在 60% prefix 后稳定产生旧 artifact；
2. raw update 后、arm assignment 前旧 artifact 仍存在；
3. baseline reference policy 在同一 checkpoint 稳定失败，而不是任务本身不可完成；
4. corrected outcome 可由 deterministic evaluator 判定；
5. stale artifact、错误 side effect 和 duplicate artifact 会被显式惩罚；
6. 同网站 family 的共享模板依赖在统计中被建模，不把八个 task id 当作完全独立；
7. 不可逆动作具有 benchmark-sandbox 内的 compensation 定义；
8. 不使用 post-treatment `seen/correctly_interpreted` 筛选运行。

因此“八个候选”不等于“n=8 的确认实验”。

## 4. 跨领域迁移证据，而不是直接 Task family

| Work | Venue/year | 可迁移内容 | 为什么不能直接当 GUI Memory 证据 |
|---|---|---|---|
| SyncMind / SyncBench | ICML 2025 | 24,332 个 out-of-sync instances、21 个 GitHub repositories 和 executable tests，证明环境演化后的恢复可以被独立测量 | 对象是协作式软件工程 Agent，不是 GUI artifact；不能证明 GUI Memory 根因 |
| C-World | ACL 2026 long | Transition Function 可注入 realistic failures/perturbations，适合生成 environment-driven invalidation | 环境由工具/state controller 构造；仍需实现 GUI observation、artifact fingerprint 与 boundary interventions |
| WindowsWorld | Findings ACL 2026 | 181 个跨应用流程、平均 5.0 sub-goals、intermediate inspections，可提供复杂 workflow 模板 | 原 benchmark 主要不是 mid-episode revision；只能作为 family 来源，不能直接回答 stale contract |
| GUI-RobustEval / RoTS | ICML 2026 Spotlight | 1,216 个 executable recovery cases、11 类 error、4 个 error depths，说明 recovery 可被系统化构造 | 官方仓库当前仍标记 benchmark/data/pipeline 为 in preparation；policy-induced error 也不等于用户/环境证伪旧行动契约 |
| WorldGUI | ICLR 2026 withdrawn | 多 initial states 可用于测试非 canonical state | withdrawn submission，按筛选规则不得进入核心论文池 |

官方链接：

- [InterruptBench paper](https://arxiv.org/abs/2604.00892)
- [InterruptBench code](https://github.com/HenryPengZou/InterruptBench)
- [SyncMind, ICML 2025](https://proceedings.mlr.press/v267/guo25l.html)
- [C-World, ACL 2026](https://aclanthology.org/2026.acl-long.2001/)
- [WindowsWorld, Findings ACL 2026](https://aclanthology.org/2026.findings-acl.750/)
- [GUI-RobustEval / RoTS](https://arxiv.org/abs/2605.29447)
- [RoTS code](https://github.com/AlibabaResearch/RoTS)
- [WorldGUI withdrawn submission](https://openreview.net/forum?id=oJZYmlVtwD)

## 5. 当前筛选裁决

```text
Task-definition evidence：PASS
Official corrected targets：PASS
Workflow diversity：candidate PASS
Baseline old-artifact existence：UNRESOLVED
Post-update artifact persistence：UNRESOLVED
End-to-end deterministic stale-artifact evaluators：UNRESOLVED for 8/8 families
Stable baseline failure：UNRESOLVED
Independent-family statistical eligibility：UNRESOLVED
```

所以这些任务只解决了 Stage 0E 的“候选池”问题，没有把 Step 2 从 HOLD 改为完成。
