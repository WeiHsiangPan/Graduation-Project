# Three External Mathematical Problems Connected to This Project

本文件只選三個在正式文獻中明確存在的數學問題，並區分「已知困難度」、「已有基準定理」與「仍在進行的分類問題」。專題不把三者包裝成同一個未解猜想。

## Problem 1 — Graph genus and embedding enumeration

### 標準問題

給定有限圖 Γ 與整數 \(g\)，判定 Γ 是否可 cellularly embedded 到 orientable genus-\(g\) surface；進一步，列舉所有不等價的 cellular embeddings，或求出可實現的 genus spectrum。

Thomassen 證明一般 graph genus decision problem 是 NP-complete。因此，當專題由 \((G,S)\) 建立 Cayley graph 後，想找「所有面系統」並不是單純把 relators 列出來，而是進入一個已知計算困難的 graph-embedding problem。

### 本專題的有限群特例

固定

\[
\Gamma=\operatorname{Cay}(G,S),
\]

以 rotation system

\[
\alpha(g,s)=(gs,s^{-1}),\qquad \phi=\sigma\alpha
\]

列舉 orientable cellular embeddings。研究目標不是解決一般 NP-complete 問題，而是利用 Cayley automorphisms、uniform rotations、local-rotation witnesses 與 canonical labeling，縮小特殊圖族的搜尋空間。

### 可交付成果

- 一個明確區分 uniform 與 general local rotations 的 enumerator；
- 每個 surface 的 machine-readable witness；
- quotient by \(\operatorname{Aut}(\Gamma)\) 後的小型 genus catalogue；
- cubic Cayley graphs 的完整枚舉實驗。

### 文獻

- Carsten Thomassen, [The Graph Genus Problem Is NP-Complete](https://doi.org/10.1016/0196-6774(89)90006-0), *Journal of Algorithms* 10 (1989), 568–576.

## Problem 2 — Spectral partitioning on bounded-genus graphs

### 標準問題

只給 graph、不給 surface embedding，能否僅用 Laplacian eigenvectors 找到 bounded-genus graph 的近最佳 separator？為什麼 spectral partitioning 在 planar／bounded-genus graphs 上有效？

Kelner 對 bounded degree、genus \(g\)、\(n\) 個頂點的圖證明 spectral method 可找到 cut ratio

\[
O\!\left(\sqrt{g/n}\right)
\]

的 separator，並給出

\[
\lambda_2(L)=O(g/n)
\]

型的 tight bound。這是本專題普通 vertex \(L_0\) baseline 的理論基準，而不是本專題要重新宣稱的新定理。

### 本專題要研究的延伸

本專題改問：當同一 Cayley skeleton 配上不同 face systems，或 symmetry 被權重與 local rotations 打破時，普通 \(L_0\) 與 face-aware operators 的表現有何差別？

核心 matched comparison 是

\[
(G,S,\mathcal F_1),\qquad (G,S,\mathcal F_2),
\]

其中 \(L_0\) 完全相同，但 \(L_1\)、dual graph 與 face-incidence operators 不同。

### 可交付成果

- 驗證 genus、neck width、conductance 與 eigengap 必須分開控制；
- 比較 \(L_0\)、dual、inflated 與 Hodge \(L_1\) clustering；
- 以 eigenspace projector 而非單一 eigenvector 衡量擾動穩定性；
- 找出 face-aware method 真正增加資訊的條件，而非主張 genus 等於 cluster count。

### 文獻

- Jonathan A. Kelner, [Spectral Partitioning, Eigenvalue Bounds, and Circle Packings for Graphs of Bounded Genus](https://doi.org/10.1137/S0097539705447244), *SIAM Journal on Computing* 35 (2006), 882–902.

## Problem 3 — Cayley-DS and cospectral Cayley graphs

### 標準問題

若兩個 Cayley graphs 有相同 adjacency spectrum，它們是否必須同構？稱 Cayley graph \(X\) 為 Cay-DS，如果同一群上的任何 Cayley graph 與 \(X\) cospectral 時都必須與 \(X\) 同構；若群上所有 Cayley graphs 都有此性質，稱該群為 Cay-DS group。

一般分類仍未完成。Liu–Zhou 的綜述在 Problems 8–14 明列：對給定群分類 non-isomorphic cospectral Cayley graphs、判定哪些 Cayley graphs／groups 是 Cay-DS。2025 年仍有工作針對 order \(8p\) 的 metacyclic groups 建構新的 cospectral non-isomorphic Cayley graph families，顯示此問題持續活躍。

### 與本專題的關係

本專題先出現一個更強烈的「surface blindness」現象：固定 \((G,S)\) 而改變 \(\mathcal F\) 時，adjacency spectrum 必然不變。因此必須區分：

1. 不同 graph 卻 cospectral：Cay-DS 問題；
2. 同一 graph、不同 surface cellulation：本專題的 face-system 問題。

第二種情況不能靠 \(L_0\) 解決，正好為 dual、incidence 與 Hodge operators 提供必要性。

### 可交付成果

- 對小群 catalogue 計算 representation-theoretic spectra；
- 搜尋不同生成集 \(S_1,S_2\) 的 cospectral pairs；
- 把 graph cospectrality 與 face-system indistinguishability 分成兩張實驗表；
- 測試 face-aware spectra 能否區分相同 skeleton 上的不同 cellulations。

### 文獻

- Xiaogang Liu and Sanming Zhou, [Eigenvalues of Cayley Graphs](https://arxiv.org/abs/1809.09829), 尤其 §4 與 §14 Problems 8–14.
- Xuanlong Ma et al., [Non-Isomorphic Cayley Graphs of Metacyclic Groups of Order \(8p\) with the Same Spectrum](https://doi.org/10.3390/math13121903), *Mathematics* 13 (2025), 1903.

## 專題定位

三個問題對應三個層次：

| 層次 | 外部問題 | 本專題能合理完成的範圍 |
|---|---|---|
| Topology | graph genus／embedding enumeration | 小型 Cayley graphs 的 rotation-system catalogue |
| Algorithms | bounded-genus spectral partitioning | 對稱破壞與 face-aware clustering 的 controlled experiments |
| Algebra | Cay-DS／cospectrality | 小群、不同生成集與不同 face systems 的可重現比較 |

本專題的主線應放在 Problem 1 + Problem 2；Problem 3 作為「為什麼普通 spectrum 可能資訊不足」的外部數學背景與延伸章節。
