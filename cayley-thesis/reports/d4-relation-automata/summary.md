# D4 規則自動機：有限／無限接受語言

固定生成元順序 r、r^-1、s；接受字 = 不含任何規則左側子字的操作字。不是預設最短字。

| 輪次 | 方法 | 額外關係 | 活狀態＋拒絕 | 語言 | 字數／證據 | 最長長度 | BFS 直徑 |
|---|---|---|---|---|---|---:|---:|
| single_relation | cancellation_only | 無 | 4+1 | 無限 | 前綴 r；循環 r | — | 3 |
| single_relation | ordinary | r s r s | 6+1 | 無限 | 前綴 r；循環 r | — | 3 |
| single_relation | faces | r r r r | 5+1 | 無限 | 前綴 r；循環 s r | — | 3 |
| full_budget | cancellation_only | 無 | 4+1 | 無限 | 前綴 r；循環 r | — | 3 |
| full_budget | ordinary | r s r s; r r r r | 7+1 | 有限 | 8 | 3 | 3 |
| full_budget | faces | r r r r; r s r s | 7+1 | 有限 | 8 | 3 | 3 |

拒絕狀態的自迴圈不算無限接受語言的證據；只有可達接受狀態的循環才算。

有限性由完整活狀態圖的拓撲順序／循環判定；長度 8 以內的逐字比對只是額外回歸檢查。

## 有限語言的全部字

- full_budget/ordinary：epsilon；r；r^-1；s；r r；r s；r^-1 s；r r s
- full_budget/faces：epsilon；r；r^-1；s；r r；r s；r^-1 s；r r s

完整預算組實際取得兩條 relators：rrrr、rsrs。一般與貼面兩組規則完全相同，不能把有限結果歸功於面來源。

每個有限語言都完整重播至群狀態，與 BFS 的 8 個最短字逐筆比較；此例上界 U=3 與 BFS 下界 3 相合。
