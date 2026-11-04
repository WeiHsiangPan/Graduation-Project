# 最小可行實驗：一般短關係 vs 貼面關係

這是**已實作的小群實驗**，不是魔方求解器、最小 genus 搜尋器或 Lean 證明。只使用 Python 標準函式庫，不依賴 NumPy，不修改既有 registry。

## 一次跑完

在 repository 根目錄執行：

```powershell
python cayley-thesis/experiments/relation_search.py
```

程式會印出新結果目錄。把該路徑代入獨立驗證器：

```powershell
python cayley-thesis/experiments/verify_run.py <結果目錄>
python -m unittest discover -s cayley-thesis/experiments -p test_relation_search.py -v
```

限制關係預算，進行第二輪對照：

```powershell
python cayley-thesis/experiments/relation_search.py --relators 1
```

改 seed 取得其他一般短關係樣本：

```powershell
python cayley-thesis/experiments/relation_search.py --seed 3 --rounds 3 --relators 1
```

結果目錄使用執行機器的 UTC 時鐘命名；參數與原始輸入、程式 SHA-256 一起保存。每次建立新目錄，不覆蓋前次結果。

## Pipeline 與問題定義

1. 從 `data/surfaces/catalogue.json` 讀取 D4（8 個狀態）、Q8（8）、S4（24）及既有貼面 witness。每個生成元成本為 1，索引順序固定。
2. 在未經剪枝的 Cayley 圖上 BFS，保存從單位元到**所有狀態**的最短路徑。這是本次比較真值，不把歷史 verified 標記當成本輪驗證。
3. 重建每個 surface，重跑 dart partition、vertex link、simple face 與 Euler genus 檢查。本實驗不做 Hodge／浮點光譜驗證，也不證明該 genus 最小。
4. 將面邊界變成生成元索引字。以循環位移及反向取逆去重；只保留長度上限內、依長度及字典序排列的前 K 個。
5. 枚舉相同長度範圍的一般 cyclically freely reduced 閉合字（可重複走訪頂點）。同樣去重，依每個 seed 抽取**與貼面關係完全相同的長度 histogram**。因此原始關係數及總符號數相同。
6. 對每個閉合字的循環位移、反向與切割建立相等操作字，依 shortlex（先長度、再字典序）由大改寫成小。三組都加入逆操作消去。
7. 用同一個 IDDFS，依相同生成元順序搜尋所有目標。若新字尾符合某條規則左側，就剪掉該分支。三組是 `cancellation_only`、`ordinary`、`faces`。
8. 每個解與 BFS 比較；另搜尋最短、再字典序最小的「不可改寫卻非最短」反例，直到指定長度。
9. 每完成一個 surface × seed，立即保存完整 case；整輪完成再保存總表。例外會留下 `failure.txt`，已完成 case 仍保留。

若某 surface 沒有長度上限內的面關係，明確記錄 skipped，不把它算作零成本或成功。長度與數量上限排除的關係數也會保存。

## 為什麼剪枝不應丟掉所有最短解？

每條規則都保持操作結果，並嚴格降低 shortlex。對任意目標，選它所有最短字中 shortlex 最小的一個。若該字包含規則左側，替換後不是變短，就是同長度而字典序更小，兩者都矛盾。因此每個目標至少保留一個最短代表。

這個論證要求：單位成本、規則保留端點、shortlex 排序一致、檢查完整的規則左側。程式逐條檢查規則在**每個起點**都保留端點。它不是「任意局部極小字都是最短」的論證，也不需要宣稱這套規則合流。

## 如何閱讀結果

- `summary.md`：所有目標加總的生成節點數、三組比較、帶生成元標籤的反例。差值為 faces − ordinary，負值才代表這個指標有改善。
- `results.json`：整輪資料、參數、程式雜湊、完整轉移表、BFS 路徑、面、關係、規則、逐目標搜尋計數與解。
- `<surface>-seed<N>.json`：每個已完成 case 的獨立保存副本。
- `counterexample.status=found`：找到明確的不可改寫非最短字；`not_found_within_bound` 只表示指定長度內沒有找到。

`generated` 是嘗試的子節點數，包含被剪枝者；`entered` 是實際進入的節點數；另保存 expanded、pruned、rule_checks、規則符號數與時間。相同原始關係預算**不保證相同展開後規則成本**，必須一起看。節點少也可能因規則掃描昂貴而更慢。

時間分開保存：BFS 與一般關係池建構（共用）、每個 surface 重建與選關係、每組規則建構與檢查、每組搜尋。反例搜尋及額外獨立驗證時間未納入搜尋時間；目前沒有測峰值記憶體。不得只用搜尋秒數宣稱整體更快。

### 獨立驗證器做什麼？

`verify_run.py` 不匯入搜尋器或其 BFS。它從 catalogue 重建群的轉移表，檢查保存的面、面關係來源與每條規則，重播所有解及反例。

距離真值採用證書：保存的路徑給距離上界；單位元標記為 0 且每條邊滿足 `label(v) <= label(u)+1` 給距離下界。上下界相合就證明標記正確，不需信任搜尋器的 BFS 實作。

搜尋計數與時間仍是儀器紀錄，不是形式化證書。驗證器與搜尋器也共用既有的群與曲面核心，並非完全獨立的數學實作。Lean 尚未加入。

## 公平性與研究限制

- 一般關係允許與面關係重疊；保存 overlap，不刻意排除，以免製造偏袒。相同 histogram 能使兩組完全一致。
- 面關係固定選擇；seed 只改變一般關係抽樣。因此多 seed 不是多張獨立圖，也不是統計顯著性證明。
- 關係是在小群完整圖上提取；此處尚未避開狀態枚舉。
- 為隔離操作字規則的效益，IDDFS 不使用全域 visited table；這不代表它比 BFS 更適合小群，更不是與最強魔方求解器的比較。
- 只重建 registry 中的面，不搜尋新嵌入，不證明低 genus 導致更快搜尋。
- 小群全部目標通過不代表四階魔方可行，也不代表 O(sqrt(N))。
- 選關係使用真實 BFS 距離會產生資料洩漏；此版本不這樣做。未來學習規則應另外保留未參與調整的群／生成集。

## 你可以一步步理解的順序

1. 先只跑 `--groups d4 --rounds 1 --relators 1`，讀 identity、labels、transitions 與 truth_paths。
2. 手算 `r r r = r^-1`：只做逆操作消去無法縮短它，但 BFS 能給一步解。
3. 對照一條面邊界 relator 與其 rules，手算兩邊是否同一群元素。
4. 選一個 target，對照三組 word、distance 與 counts。
5. 執行獨立驗證器；用測試確認破壞距離證書會被拒絕。
6. 增加 seed 或縮減關係預算，觀察「何時相同、何時不同」，再討論擴群。

下一個決策依據是：在相近完整成本下，面關係是否持續優於一般短關係。沒有優勢也是有效研究結果，不能刪去。
