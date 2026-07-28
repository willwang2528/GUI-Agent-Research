# Step 2：竞争性根因识别

> status: **LOCKED BY STEP 1**

## 要回答的问题

已观察的 update-to-action failure 是否由 persistent state / dependency repair deficit 造成，而不是由 delivery、observation、grounding、planning、semantic action、actuation、verification、environment、evaluator 或 budget 充分解释。

## 预冻结识别对象

```text
E / O / G / R / P / S / A / V
+ Environment / Evaluator / Budget
```

C1-R 的目标不是“内部 Memory 的直接效应”，而是 `R→P boundary payload total downstream effect`。主设计要求：

```text
R = stale / correct
P_operator =
  identity_no_propagation
  flat_scan
  dependency_graph_propagation
```

三臂使用共同 consumer API、相同 R payload、相同 semantic closure 与预算；planner/action/recovery 是允许变化的下游中介。

## 当前结论

尚无 boundary-isolated replay，不能声称 Memory 是根因。Step 1.5 的 same-system / transport / block verdict 也尚未执行。

## Kill condition

若 grounding、planning、actuation、evaluator 或其他竞争原因在可识别干预下充分解释目标效应，Memory track 必须降级或改题。
