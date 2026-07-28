# GUI Agent Memory：七步科研台账

> ledger_version: `1.0`  
> initialized: `2026-07-28`  
> git_policy: `GitHub main / selected research artifacts only`  
> git_repository: `https://github.com/willwang2528/GUI-Agent-Research`  
> git_repository_status: `ACTIVE — checkpoint history is recorded by commits on main`  
> current_step: `Step 1`  
> current_verdict: `IN PROGRESS / NOT READY FOR BLOCK-A DRY RUN`

本目录是七步研究链的长期入口。GitHub `main` 上的 commit 记录每个关键节点；这里记录“当时能得出什么结论、不能得出什么结论以及下一门是什么”。原始大文件不进入 Git，使用 `source_provenance/` 中的 hash manifest 追溯。台账文件存在或被提交不等于相应科学命题已经得到证明。

## 七步状态

| Step | 科研问题 | 状态 | 当前结论 |
|---:|---|---|---|
| 1 | 问题现象是否存在且负担足够 | **IN PROGRESS** | frame 与 detail availability 已建立；测量实现未通过，问题尚未证明 |
| 2 | 根因是否包含不可替代的 R/P deficit | **LOCKED** | 不允许声称 Memory 是根因 |
| 3 | 强现有方法是否仍有 residual | **LOCKED** | 不允许声称现有方法不行 |
| 4 | 新机制是否充分、必要且可分解 | **LOCKED** | 方法未选，不实现 architecture |
| 5 | 环境证伪是否优于同证据 reflection | **LOCKED** | 尚无干预证据 |
| 6 | 增益是否独立于 token/action/latency/oracle | **LOCKED** | 尚无 matched-budget 实验 |
| 7 | 保留、改名或终止；是否改变能力边界 | **LOCKED** | broad environment title 尚未获支持 |

## 更新规则

每个关键节点必须同时写入：

1. 对应 Step 文件中的日期、证据和 claim ceiling；
2. `refine-logs/` 中的 review/experiment 状态；
3. 一个 Git commit，并同步到 GitHub `main`。

禁止仅凭文件存在、测试通过或 reviewer 同意升级科学结论。只有前一步 gate 通过，下一步才从 `LOCKED` 改为 `IN PROGRESS`。

## 文件索引

- `01-problem-existence-and-burden.md`
- `02-root-cause-identification.md`
- `03-existing-methods-residual.md`
- `04-method-causal-validation.md`
- `05-environment-falsification.md`
- `06-budget-and-privilege-audit.md`
- `07-go-no-go-and-publication-claim.md`
