# Step 6：预算、信息与特权审计

> status: **LOCKED BY STEP 5**

## 要回答的问题

观测增益是否只是额外 token、动作、延迟、retrieval coverage、人工接管、oracle truth、不同 prompt 或不同工具造成。

## 必须匹配

- action-relevant semantic closure；
- observation/evidence prefix；
- prompt、tool/API、模型与 weights；
- payload schema、serialization、visibility、injection timing；
- token、action、wall-time 与 latency tier；
- evaluator 与 adjudicator blindness；
- non-target state fingerprint。

## 当前结论

尚无方法实验，不能进行公平性归因。

## Kill condition

任一关键增益必须依赖 privileged truth、额外信息集或不可匹配预算时，只能报告 package/system effect，不能归因于 Memory representation 或 action contract。
