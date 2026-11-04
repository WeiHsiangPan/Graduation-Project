單四面體 36 種完整貼合：本週交付

這份實驗直接落實《期中大綱》第 6 頁的第一個有限枚舉範圍。只使用一個帶標記四面體，固定兩對面，完整枚舉每對面的六個仿射頂點對應，共 36 案。

- [交給老師的研究摘要](teacher-report.md)
- [完整 36 案結果表](results-table.md)
- [可用 Excel 開啟的 CSV](results-table.csv)
- [逐步案例講義](walkthrough.md)
- [36 格總覽圖](overview.png)
- [同 Ce/Cv、同末貼合、不同同調的整數證據](boundary-inclusion-witness.json)
- [最新正式結果目錄與雜湊](latest-run.json)

實際範圍與結果：

| 項目 | 結果 |
|---|---:|
| 帶標記貼合選擇 | 36 |
| 通過閉、連通、可定向三維流形判準 | 9 |
| 拒絕 | 27 |
| 通過者 H1=0 | 5 |
| 通過者 H1=Z/4 | 2 |
| 通過者 H1=Z/5 | 2 |
| 通過者的四面體重標號組合類 | 4 |

全部通過者的 H0=H3=Z、H2=0。9 是帶標記案數，4 是組合類數，均不作不同胚流形的計數。拒絕原因可同時出現；資料保留所有原因。

固定配對與記號：

1. t0:012 → t0:perm(013)。
2. t0:023 → t0:perm(123)。

例如 `130-231` 代表第一張面依序 0→1、1→3、2→0；第二張面依序 0→2、2→3、3→1。三元組的順序定義映射，不能把它排序後才解讀。這個 36 案實驗是自行明確指定的單四面體範圍，不涉及 Example 7 的原文／推定版本差異。

pipeline：保存固定輸入 → 枚舉 36 案 → 識別等價閉包 → 完整頂點 links 與局部曲面檢查 → 邊方向與整體可定向性 → 逐案接受／拒絕 → 通過者的整數鏈複形與同調 → 24 種重標號組合去重 → 獨立核對 → 匯出表格。

重跑（在專案根目錄）：

```powershell
python cayley-thesis/experiments/one_tetrahedron_census.py
python cayley-thesis/experiments/verify_one_tetrahedron.py --run <新結果目錄>
python -m unittest discover -s cayley-thesis/experiments -p "test_*.py"
```

主實驗、整數同調與獨立驗證器都只用 Python 標準函式庫。每次建立新的 UTC 時間戳結果目錄，不覆寫前輪。先前兩輪開發結果也保留；正式報告以 latest-run.json 指向且核對通過的版本為準。

選擇性重畫總覽圖需要 Pillow；目前專案的 Manim 環境已有此套件：

```powershell
cayley-thesis/manim-scenes/.venv/Scripts/python.exe cayley-thesis/experiments/draw_one_tetrahedron.py
```

每個 `cases/<ID>.json` 含貼合三元組、完整四頂點排列、首次及最後階段、Ce/Cv、完整 link 的局部檢查、方向方程、反向自識別的有號循環證據，以及通過者的 B1/B2/B3、整數 kernel 與 Smith 變換證書。`results.json` 保存所有個案、總數、組合去重鍵及邊界資訊遺失的證據。

驗證可信度：

- 主實作沿用 Example 7 的等價圖閉包與 link 檢查。
- 另一實作使用 signed union-find、獨立局部 link 檢查及單形邊界建構，逐案核對全部 36 案與首次貼合。
- 同調主實作計算整數 kernel，再商掉 incoming image，保留 U*A*V=D 與 unimodular 變換；另一方法以全部小行列式的 gcd 計算不變因子，交叉核對同調群。
- 這是有限組合與整數運算驗證，尚無 Lean 證明或自動流形辨識。

對大綱的意義：本輪完成單四面體 36 案與通過者整數同調，並提供 Ce/Cv 忘記邊界包含映射的具體證據。本輪找到的是「同狀態、同完成貼合、不同同調」；大綱主問題「同整數同調、不同胚」仍須另外的構造與分類證據。
