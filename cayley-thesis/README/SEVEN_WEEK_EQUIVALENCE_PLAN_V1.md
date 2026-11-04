# 第一版構想：Cayley 圖到曲面的不同等價關係

日期：2026-10-22。此文件為新提案，不取代既有研究計畫，也不宣稱下列實驗已完成。

## 題目與核心問題

建議題目：**從群同構到曲面同胚：Cayley 圖與曲面胞腔分解的等價關係**。

核心問題：固定有限群 G 與對稱生成集 S，令 Γ=Cay(G,S)。不同 rotation systems 所構成的閉連通可定向曲面，如何在「嵌入等價」及「曲面同胚」兩種標準下分類？哪些代數與圖論資訊能保留到曲面，哪些資訊會在忘記標籤、面結構或嵌入後消失？

最小成果是對立方體圖做一個範圍明確、可重現的有限分類，並以定理和反例整理不同等價關係的界線。研究定位為已知理論的具體應用、有限分類與可驗證計算，不預設得到新的一般定理。

## 對象與等價關係

1. 群 G：群同構保留乘法。有限群未指定拓撲時，不能直接討論同胚；若賦予離散拓撲，同胚只保留集合基數。
2. 帶生成集的群 (G,S)：要求群同構 f 滿足 f(S)=T，才能自然誘導 Cayley 圖同構。
3. 抽象圖 Γ：圖同構保留鄰接，但通常忘掉群乘法、生成元標籤與面。
4. 組合嵌入 M=(D,α,σ)：D 為 darts，α 反轉邊，σ 給每個頂點的 cyclic order；面為 φ=σα 的 cycles。
5. 曲面 Σ(M)：把面填入之後得到的拓撲空間。曲面同胚可以不保留原有頂點、邊、面。

定向嵌入等價以 dart 雙射 p 表示：pα₁p⁻¹=α₂ 且 pσ₁p⁻¹=σ₂。不固定方向時，另外容許對整個 connected map 全域反轉 rotation，即比較 σ₂⁻¹。不能把各頂點的獨立反轉都當成相同嵌入。

對固定骨架，以 Aut(Γ) 作用及全域 mirror reversal 取軌道。若要求保留群標籤、生成元顏色或指定群作用，必須另定更嚴格的等價關係；主線採不保留標籤的嵌入等價。

## 三個具體問題

### Q1：同一骨架可以得到不同胚的曲面嗎？

核對既有 D4 立方體骨架 witnesses：六個四邊形面給 V=8、E=12、F=6，故 χ=2；四個六邊形面給 F=4，故 χ=0。完整驗證後分別為球面和環面。這是既有例子的重建與解釋。

### Q2：同胚的曲面可以有不等價的 Cayley 圖胞腔分解嗎？

核對同一 D4 骨架的兩個環面 witnesses：面長 multiset 分別為 {6,6,6,6} 與 {4,4,8,8}。若驗證成立，兩者曲面同胚，但因面長 multiset 不同，不可能是等價的胞腔嵌入。相同 genus 是曲面分類，不是嵌入分類。

進階目標才是尋找同骨架、同 genus、同面長 multiset，仍不等價的例子。既有 A/B candidates 未完成 automorphism quotient，不能預先當成答案。

### Q3：圖同構會保留原來的群嗎？

以 D4（階為 8 的二面體群）與 (Z/2Z)^3 為例。前者取 {r,r⁻¹,s}，後者取標準基底，兩個 Cayley 圖皆為立方體圖，但群不同構。提供明確頂點對應，並用交換性等群不變量證明群不同構。

這也連接群作用：同一抽象圖可以支援不同正則群作用；若不記錄作用，便無法由圖唯一恢復群。群作用是否能延伸到指定曲面，還要檢查它是否保留 rotation／face system；這一項作概念說明，不承諾完整分類。

## 要寫出的理論成果

- 證明：f:G→H 為群同構且 f(S)=T 時，f 誘導 Cay(G,S)→Cay(H,T) 的圖同構。
- 證明：保留 α、σ 的 dart 雙射保留面 cycles，並能延伸成對應曲面胞腔分解間的同胚。
- 引用閉連通可定向曲面分類：Σ₁≅Σ₂ 當且僅當 genus 相同。
- 利用具體例子說明逆向恢復的限制；不把上述三點誤寫為無條件的單一蘊含鏈。

## 計算範圍與驗證

核心只做立方體圖。每個三價頂點有兩個 cyclic orders，八個頂點共有 2^8=256 個帶標號 rotation systems。枚舉後按 Aut(Γ) 及全域 mirror 取軌道。

分開記錄「所有 orientable cellular maps」及「各面邊界都是 simple cycles 的子類」。一般 cellular embedding 可有重複頂點或重複邊的面邊界；simple-face 是本專案額外限制，不能宣稱它涵蓋所有嵌入。

每筆記錄：rotation witness、面邊界、V/E/F、χ、genus、face-length multiset、simple-face flag、canonical orbit key。若使用現有 face-list 資料，另外驗證 exact dart partition 及每個 vertex link 恰為一個 cycle。

最低檢核：每個 dart 恰出現一次、面長總和為 2E、Euler genus 合法、orbit 大小總和為 256、重新標號後 canonical key 不變、既有球面與環面 witnesses 可重現。只對證明分類完整性必要的部分增加檢核。

以現有 code/surface_systems.py、handbook/verify_examples.py 及 data/surfaces/catalogue.json 為基礎；不把 registry 的歷史驗證標記當成本次已重跑的結果。

## 七週執行表

| 週 | 工作 | 可交付與完成標準 |
|---|---|---|
| 1 | 精讀舊 report、固定名詞與範圍 | 2–3 頁問題陳述；明確區分群、圖、map、曲面及方向約定 |
| 2 | 重建 D4 球面與環面 | 提供 faces／rotations 與完整拓撲檢核；說清 dart 與 vertex link |
| 3 | 枚舉立方體的 256 rotations | 全量原始表；分列所有 maps 與 simple-face 子類 |
| 4 | 實作 Aut(Γ) 與 mirror quotient | 分類表、canonical representatives；orbit coverage 核對 |
| 5 | 整理同 genus 不同 map，完成不同群同圖例子 | 三組核心例子；明確圖同構與群不同構證明 |
| 6 | 寫成初稿 | 定義、兩個命題證明、分類定理引用、方法、結果與限制 |
| 7 | 查錯、重現與口頭報告 | 最終報告、重現指令、10–12 張投影片及反問清單 |

若不到七個完整週，合併第 1、2 週並取消擴充。只有主線完成才做 Q8 或同面長 profile 的進階例子。第四週仍未完成 quotient 時，停止擴群並把分類工具列為優先；即使 quotient 未完成，仍可交付三組已驗證反例與理論整理，但不得宣稱完成嵌入全分類。

## 範圍控制

本輪不以 spectral clustering、廣泛 symmetry breaking、多群大規模搜尋為主線。普通圖 Laplacian 在固定骨架時完全相同，可用一段論述說明其限制。Hodge 方法可作附錄，不以新增光譜實驗為必交成果。

群 G 不是所構造曲面的基本群：例如球面的 π₁ 平凡，環面的 π₁≅Z²，皆不能從 Cayley 頂點群 D4 直接認定。Cayley 圖貼入選定 faces，也不能自動等同標準 presentation complex 或其 universal cover。

圖的幾何實現 |Γ| 可以嵌入曲面，但不會同胚到整個二維曲面。要說的是「嵌入」或「添面構造曲面」；同胚比較的是最後得到的曲面。

## 文獻與本地依據

- 上學期 thesis/Cayley_report.pdf，文字抽取 tmp/cayley_report.txt。
- README/README.md、README/RESEARCH_PLAN.md：後續 vertex-link 修正、既有資料與待完成 quotient。
- SageMath, Genus：https://doc.sagemath.org/html/en/reference/graphs/sage/graphs/genus.html 。Dart permutations、面 cycles 與 Euler 計算。
- Allen Hatcher, Algebraic Topology：https://pi.math.cornell.edu/~hatcher/AT/ATchapters.html 。曲面與基本群背景。

## 可向老師說明的第一版摘要

本學期延續上學期從有限群與 Cayley 圖構造曲面的研究，聚焦於群同構、圖同構、嵌入等價與曲面同胚之間的差異。我將以立方體型 Cayley 圖為核心，利用 rotation systems 枚舉並分類其可定向胞腔嵌入，再比較同骨架不同曲面、同曲面不同胞腔分解，以及不同群產生相同 Cayley 圖的例子。預期成果為精確定義、可證明的命題與反例、一份可重現的有限分類表，以及對原有面系統判準的修正說明。
