# Experiment Tracker

| Run ID | Milestone | Purpose | Scope | Primary output | Priority | Status | Notes |
|---|---|---|---|---|---|---|---|
| S1-M0-01 | M0 | 冻结 catalog frame | 108 × 6 | frame audit | MUST | DONE | 648 catalog cells；不是 launched-run census |
| S1-M0-02 | M0 | 冻结 confirmatory denominator | 82 × 6 | denominator check | MUST | DONE | `N_holdout = 492` |
| S1-M0-03 | M0 | 消除双重阈值口径 | Stage 0F docs | canonical decision source | MUST | DONE | `stage0f_step1_decision_card.md` 为唯一数值源 |
| S1-M1-01 | M1 | 建立 catalog data-availability manifest | Block A 48 units | unit manifest | MUST | DONE | 48/48 catalog cells |
| S1-M1-01b | M1 | 审计 frozen detail-page availability | Block A 48 units | reproducible availability report | MUST | DONE | 48/48 expected pages；47 valid replay、1 explicit no-step；9,138 embedded steps；replay PARTIAL，truth 仍 blocked |
| S1-M1-02a | M1 | 冻结旧版 Stage A schema / leakage linter | synthetic fixtures | schema + validator | MUST | **FAIL / SUPERSEDED** | v0.4 validator 未执行 Draft 2020-12 Schema；Round 3 的 12 类破坏包曾 12/12 被误放行，不能作为测量证据 |
| S1-M1-02c | M1 | 重建 outcome-blind Stage A measurement | synthetic fixtures | full-block frame/stream/raw/A0/A1/exposure/role schemas、schema-first validator、negative matrix | MUST | **ROUND 6 REVISE** | X58–X60 regression 由 fresh replay 接受，但 X62 证明 substantive disagreement 无法 adjudicate/独立保留，X63 证明 evidence pointer 不保证 semantic entailment；v1 是 consensus-only structural fixture，不是合格 measurement |
| S1-M1-02d | M1 | 实现 finite bounds / negative-certificate mechanics | synthetic fixtures | frozen verifier + semantic derivation + joint completion + structural witnesses | MUST | SYNTHETIC ACCEPT / PRODUCTION REJECT | root 33/33 PASS；独立 bounded replay 22/22 PASS，覆盖 X36–X40、X42、X44、X45、X49、X53–X57、X61。真实 adapter、义务/身份投影、pre-outcome mapping receipt、proof semantics 与 trusted large-world solver 缺失 |
| S1-M1-02b | M1 | 生成真实 Stage A blind packets | Block A 48 units | packet set + hashes | MUST | TODO | 必须先冻结整个 Block A 的 A0 raw labels 与 A0-only adjudication，再开放任何 A1；需永久隔离的 fresh roles |
| S1-M1-03 | M1 | 验证双 prefix-only generators | unseen validation units | independent exhaustive reference set + event recall/F1 | MUST | TODO | union 只报 inter-generator coverage；禁止后续 outcome |
| S1-M1-04 | M1 | 随机 non-candidate 抽查 | 实际打开的 reserve units | supplemental leakage/prevalence audit | SHOULD | TODO | 不估计 event recall，不进 PASS gate |
| S1-M2-01 | M2 | ontology development | Block A | codebook v0.1 | MUST | LOCKED | 等待 M1 完成 |
| S1-M3-01 | M3 | unseen validation | Block B | reliability report | MUST | LOCKED | B 足量且通过则只用 B；只有阳性不足且整个 measurement stack 未变才自动 B+C |
| S1-M3-02 | M3 | final unseen validation | Block C | final gate report | MUST | LOCKED | B 解封后任一 measurement-stack artifact 修订，则 primary 只用全程未见 C |
| S1-M4-01 | M4 | confirmatory burden audit | 492 units | unit labels + bounds | MUST | LOCKED | 只有 reliability PASS 后开放 |
| S1-M5-01 | M5 | Step 1 decision | all outputs | C0-A/B/C/D/E + derived decision | MUST | LOCKED | C0-E 单独控制 Environment-Falsifiable 标题；所有结果必须互斥且穷尽 |
| S1-M6-01 | M6 | Step 1.5 replay identification | positive interface candidates | hosted identity + reconstructed freeze + B–E exhaustive verdict | MUST | LOCKED / ROUND-4 REVISE | hard FAIL 优先、R×P common-consumer operators、P manipulation 与 design-only narrow branch 已写入协议；仍需 final stack review |
| S1-M7-01 | M7 | Round 4 adversarial protocol battle | prereg + decision + schemas + validator | fatal-gap ledger + readiness verdict | MUST | ROUND 4B REJECT / NOT READY | Round 4b 又击穿 partial-identification 状态、negative certificate、finite joint completion、zero denominator 与 narrow claim；文本修订不等于 measurement 实现通过 |
| S1-M7-02 | M7 | Round 4c release audit | current NOT_READY checkpoint | bypass + consistency + release-hygiene verdict | MUST | REPOSITORY PASS / SCIENCE REJECT | 可提交当前检查点；不允许 synthetic freeze、Block A、Step 1 GO 或 claim upgrade |
| S1-M7-03 | M7 | Round 5 implementation battle | full-block Stage A + bounds mechanics | executable counterexamples X36–X61 | MUST | PARTIAL ACCEPT / SCIENCE REJECT | bounds synthetic mechanics 获独立 ACCEPT；Stage A X58–X60 regression获 fresh ACCEPT；所有 production、freeze、Block A 与 Step 1 结论继续 REJECT |
| S1-M7-04 | M7 | Round 6 adjudication/grounding battle | Stage A v1 | X62 consensus censoring + X63 semantic non-entailment + X64 denominator erasure | MUST | **REVISE / NO FREEZE** | reviewer 在 root 反例后撤回 protocol ACCEPT；v2 必须分离 raw/case/path/primary/missingness ledgers，保留 substantive disagreement，并区分 mechanical 与 human grounding |
