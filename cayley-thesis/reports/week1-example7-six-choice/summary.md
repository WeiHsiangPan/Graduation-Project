# 六選一貼合實驗：完整重建判定

固定第一次 t0:012↔t1:012；第二次為 t0:023↔t1:perm(123)。不是原文的 t1 自貼。

| 選擇 | Partial 通過 | 整體可定向 | 可定向 partial 通過 | 頂點類 | links | 拒絕原因（partial） |
|---|---|---|---|---:|---|---|
| 123 | False | False | False | 3 | 圓盤、莫比烏斯帶、圓盤 | NONORIENTABLE_VERTEX_LINK |
| 132 | True | True | True | 2 | 圓盤、圓盤 | 無 |
| 213 | True | True | True | 2 | 圓盤、圓盤 | 無 |
| 231 | True | False | False | 2 | 圓盤、圓盤 | 無 |
| 312 | True | False | False | 2 | 圓盤、圓盤 | 無 |
| 321 | True | True | True | 3 | 圓盤、圓盤、環帶 | 無 |

判準分開：Definition 5 不要求整個空間可定向。231、312 通過 partial，但不通過額外的整體可定向目標。
321 的環帶可以是合法 partial link，不代表底層已是三維流形。六種結果都仍有四個邊界面，均非閉合。

完整 Ce/Cv、小三角形資料、局部頂點檢查、邊界圈與理由見 cases/<選擇>.json。
