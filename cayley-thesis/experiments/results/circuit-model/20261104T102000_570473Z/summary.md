# 電路模型：小群精確實驗

Exact full-graph small-group study; not a cube solver or scalability proof. L1 solved by matching primal/dual certificates, not an independent LP solver. Electrical preprocessing builds the full graph; single-run timings are descriptive. The target-specific O(V^2) lookup is an experimental convenience, not compression.

|群|V|直徑 D|最大 R（精確）|ceil 最大 R|節點 h=0|節點 非終點h=1|節點 ceil R|電阻預處理秒|BFS 秒|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|d4|8|3|5/6|1|115|42|42|0.005233|0.000015|
|q8|8|2|1/2|1|122|31|31|0.005354|0.000013|
|d6|12|4|21/20|2|311|126|108|0.021085|0.000009|
|z4xz4|16|4|2/3|1|911|272|272|0.070024|0.000011|
|z2_cubed|8|3|5/6|1|115|42|42|0.004187|0.000008|
|z3xz3|9|2|5/9|1|182|48|48|0.007560|0.000008|
|s3|6|2|11/15|1|62|21|21|0.001541|0.000006|
|a4|12|3|11/10|2|329|132|90|0.018932|0.000011|
|d8|16|5|31/24|2|739|322|164|0.061650|0.000011|
|s4|24|6|9/7|2|2009|912|525|0.317347|0.000015|

所有目標：電流守恆、精確能量恒等式、R≤距離、ceil(R)可採納且一致、
兩種IDA*最優長度、L1原始/對偶證書皆核對通過。
所有catalogue貼面上的電流環流均精確為0；因此非負面環流懲罰不改變二次模型最優解。
節點差不是總時間加速；預處理、查表與搜尋時間分開保存在results.json。
同一Cayley圖的單源最大距離等於直徑，依據左平移圖自同構。
