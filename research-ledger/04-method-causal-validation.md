# Step 4：方法充分性、必要性与机制分解

> status: **LOCKED BY STEP 3**  
> method_selection: `NONE`

## 要回答的问题

若根因成立，最小可部署机制能否改变对应因果边；增益来自 invalidation、dependency propagation、recovery，还是额外信息/提示/operator bundle。

## 最低实验

- sufficiency 与 necessity；
- R × P factorial；
- invalidation / propagation / recovery 分解；
- typed vs flat 使用同一 machine-readable semantic information closure；
- flat↔typed 双向无损，逐字段/关系 hash 相等；
- package effect 与 representation effect 分开。

## 当前结论

没有提出或实现方法。现在设计复杂 architecture 会越过 Step 1–3。

## Kill condition

typed contract 在等信息、等更新时机与等预算的 flat state 上没有独立增益时，representation novelty 不成立。
