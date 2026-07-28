# Round 4b 独立反方审计：Global Bounds 与 Joint Completion

> date: `2026-07-28`  
> reviewer: `round4b_bounds_reviewer`  
> review_scope: Round 4 初版修订后的 decision card 与主预注册  
> independence: fresh read-only reviewer  
> verdict_at_review: **REJECT — NO SYNTHETIC PROTOCOL FREEZE / NO BLOCK A**

## 1. 审计结论

| 审计项 | 裁决 | 原因 |
|---|---|---|
| task/interface/deficit global upper 的标量代数 | 条件接受 | 只有 negative certificate 真实可靠时，`T minus N` 与 unit cap 1 才是总体上界 |
| negative certificate 可机械形成 | 拒绝 | 初版缺 artifact、有限 proof mode、validator 与六配置逐项合取规则 |
| hidden location 的标量 upper | 接受 | location slot 可容纳同一 ordinal 的零个、一个或多个潜在事件 |
| `Z_D` / `Z_env_structure` 有限且禁止 stitching | 拒绝 | 初版仍在枚举无界自然语言事件，且只有边际量，不能阻止跨事件拼接 |
| C0-B / C0-C 状态语义 | 拒绝 | valid finite bounds 跨门应为 `INCONCLUSIVE`，不是 measurement failure |
| `SOURCE_UNKNOWN` 与 invalid measurement 的区分 | 语义接受 | factual pointer、reason、search scope 与 A0 multi-label 仍需机械化 |
| narrow design-only 分支 | 拒绝 | broad scope 失败只产生 narrow hypothesis，不识别任何具体 narrow scope |

## 2. 使初版证明失效的反例

### 2.1 Partial identification 不是测量失败

```text
L_B_tasks = 7
U_B_tasks_global = 82
L_B_deficit = 0.9
U_B_deficit_global = 82
```

这些 bounds 可以同时有效、有限且可审计。它们只说明门槛被 bounds 跨越，所以 C0-B 应为 `INCONCLUSIVE`；若写成 `UNIDENTIFIABLE -> MEASUREMENT_BLOCKED`，会把证据不足误写成测量无效。

C0-C 同理：

```text
L_C_interface_tasks = 7
U_C_interface_tasks_global = 82
```

正确结果是 `INCONCLUSIVE`，不是 provenance failure。

### 2.2 单配置 negative 不能排除整个 task

某 task 的 config A 可以被机械证明无机会，但 config B 仍可能有阳性。若 task certificate 不是对准确六个 hosted configs 的 AND，错误实现就可能把整个 task 放入 strict-negative set，导致 global upper 偏低。

human annotator、reference agent 或 search “未发现”都不能证明共同漏检为零，因而不能签发 negative certificate。

### 2.3 无界自然语言事件不能形成 finite completion set

一个 hidden location 可以承载任意多个、任意 proposition id 的假想事件。若协议写“枚举所有 event completions”，completion set 在字面上不是有限集，无法穷举、复算或冻结。

### 2.4 Marginal bits 会制造不存在的 same-event witness

同一 location 可能有两个不同事件：

```text
e1 = B positive + NON_WORLD + no interface
e2 = B negative + PURE_WORLD + interface
```

只保存 `exists_B`、`exists_WORLD` 与 `exists_interface` 三个边际量会错误合成为 `PURE_WORLD + B + interface`。因此必须直接表示 same-event joint sufficient bits，不能乘 marginals 或跨事件拼接。

### 2.5 Broad concentration 不识别具体 narrow scope

一个合法 completion 可集中于 group A，另一个可集中于互斥 group B。两者都拒绝 broad dispersion，但没有共同支持的窄域。因此当前 frame 最多输出：

```text
BROAD_SCOPE_REJECTED_NARROW_HYPOTHESIS_ONLY
```

任何具体 narrow scope 都必须使用新的独立 frame，从 Step 1 重新裁决。

### 2.6 Empty obligation denominator

若 `O_applicable(u)` 为空，deficit ratio 未定义。协议必须要求非空；无法满足时 fixed lower 为 0、upper 为 1，并禁止 deficit-negative certificate。

## 3. 必须完成的最小修复

1. C0-B/C 分别加入真正的 `INCONCLUSIVE`，并与 `UNIDENTIFIABLE` 严格分离。
2. 重新枚举至少 `3 x 4 x 4 x 4 = 192` 个 general-decision states，统一 `BELOW_FROZEN_GATE`。
3. negative certificate 必须包含完整 ordinal roster、hash chain、direct pointers、有限 mechanical proof mode、validator output；task certificate 对六配置取 AND。
4. hidden location 只用 finite joint sufficient bits；joint bit 独立赋值并满足单调约束，不允许由边际量推导。
5. `O_applicable(u)` 必须非空；否则 fail closed。
6. broad scope 失败只产生 narrow hypothesis，不能产生 narrow supported claim。
7. factual labels 每项必须有 direct pointer；`source_unidentifiable` 必须有 nonempty reason 与 evidence-search scope。

## 4. 审计后的 claim ceiling

完成文本修订不等于实现已完成，更不等于现象已证明。新一轮独立实现审计之前，唯一允许的状态是：

```text
FRAME-READY
MEASUREMENT IMPLEMENTATION NOT READY
NO SYNTHETIC PROTOCOL FREEZE
NO BLOCK A
```
