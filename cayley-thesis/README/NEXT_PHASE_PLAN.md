# 下一階段規劃 v1：從 Cayley surfaces 到 Lean 形式化與資安延伸

撰寫日期：2026-10-10。本文件**補充**而非取代 [RESEARCH_PLAN.md](RESEARCH_PLAN.md)（本學期 16 週排程）與 [PROOF_PLAN.md](PROOF_PLAN.md)（T1–T7 命題）。這裡回答三件事：

1. 「延續三篇 reference → 下學期 spectral clustering + Lean + 密碼／資安」整體是否可行；
2. 學界目前到哪裡；
3. 第一版的**學習方向**與**研究方向**（分開列）。

---

## 0. 一句話結論

**可行，但要改一個連接點。** 「genus／face system 直接推出密碼學安全性」沒有已知理論支撐，不建議當主張。真正嚴謹、且和本專題數學完全同構的橋是：

> **Cayley surface 的 chain complex \(C_2\xrightarrow{B_2}C_1\xrightarrow{B_1}C_0\) 本身就是一個 CSS 量子錯誤更正碼（homological / surface code）。**
> 其參數為 \([[n,k,d]]=[[\,|E|,\ \dim\ker L_1,\ d\,]]\)，而本專題 T2 證明的正是 \(\dim\ker L_1=2g\)，也就是**邏輯 qubit 數 \(k=2g\)**。

因此「在 Lean 中證明 T2」= 「在 Lean 中證明 Cayley surface code 的 logical qubit 數」。這讓三條線（topology、spectral、資安／編碼）由同一個定理串起來。Cayley hash function（碰撞 = relator = face 邊界）作為第二座、較教學性的橋。

---

## 1. 可行性評估

| 組件 | 可行性 | 理由 | 主要風險 |
|---|---|---|---|
| 延續 Brinkmann genus 演算法 | 高 | 已有 rotation system 框架；`((d-1)!)^n` 搜尋 + Aut quotient 已在計畫內 | 只做小圖；不要宣稱改善 NP-complete 問題 |
| 延續 Barthel–Buccoliero（spatial graph 的嵌入曲面） | 中 | 可作為「同一 graph、不同 cellulation」的 3D 實現章節 | 需要 knot／spatial graph 背景，偏離主線，建議只做 1 個例子 |
| 延續 Liu–Zhou（Cayley graph 特徵值） | 高 | T6 閉式譜已在計畫內；本專題的 face-blindness 是它的乾淨對照 | 無 |
| 下學期 spectral clustering（含 Hodge） | 高 | 文獻成熟（Ebli–Spreemann、Schaub et al.），本專題已有 \(L_0,L_1\) | 必須用 projector 比較重根 eigenspace（已列原則） |
| Lean 形式化**部分** lemma | 中高 | mathlib 已有 graph Laplacian、`rank ker lapMatrix = #components`、矩陣秩、有限群表示 | Lean 學習曲線約 6–8 週；rotation system／surface 定義要自己寫 |
| Lean 形式化**全部** T1–T7 | 低 | T3（得到 surface 的拓撲 soundness）、T7（實驗）不適合；Kelner bound 遠超大學專題 | 範圍失控 → 要限定 |
| 延伸到量子碼（CSS／surface code） | 高 | 與 T2 完全同構；hyperbolic surface code 是活躍領域 | 距離 \(d\) 的計算對大圖困難，只做小 catalogue |
| 延伸到古典密碼（Cayley hash） | 中 | 碰撞 ⟺ relator，已有完整文獻與已知攻擊 | 只能做教學／重現已知攻擊，不宜宣稱新密碼系統 |
| 「genus 決定密碼安全性」 | 低 | 無已知定理；genus 不是密碼學安全參數 | 不要寫成研究主張 |

**整體建議**：本學期完成 PROOF_PLAN 的最低可辯護版本（T1+T2+T3+T5）並開始 Lean 入門；下學期主線是「Hodge spectral clustering + Lean 證明 T2 組合版 + Cayley surface codes」，Cayley hash 作為附章。

---

## 2. 學界目前的進度與成就

### 2.1 Graph embedding / genus（Reference 1、2）

- Thomassen (1989)：graph genus 判定為 NP-complete；固定 \(g\) 時有線性時間演算法（Mohar），但無實用實作。
- **Brinkmann (2020, arXiv:2005.08243)**：實用 backtracking 程式 `multi_genus`，可算 genus、列出最小 genus 或指定 genus 的所有 embeddings（排除 labelled mirror）。小於約 80 頂點的稀疏圖才實際可行。**本專題可直接用它作 ground truth 交叉驗證 catalogue**。
- **Barthel–Buccoliero (arXiv:2406.03800, v2 2025-10)**：給定 \(\mathbb R^3\) 中 spatial graph，定義 *leveled*，證明少 level 時一定存在嵌入 \(\mathbb R^3\) 的閉可定向曲面使 graph cellular embed；一般 level 給出演算法並**猜想**所有 connected leveled embeddings 都可行（open）。
- Cayley maps（uniform rotation）有完整的 regular map 分類文獻（Conder 的 regular maps census 到 genus 300 以上），可作為 uniform 類別的對照表。

### 2.2 Cayley graph 頻譜（Reference 3）

- Babai (1979)：Cayley graph 譜由 irreducible representations 決定（本專題 T6 所用）。
- **Liu–Zhou 綜述 (arXiv:1809.09829)**：Cay-DS、cospectral Cayley graphs、整數譜 Cayley graphs 等，Problems 8–14 仍 open；2025 年仍有新的 cospectral non-isomorphic 構造（Ma et al., order \(8p\) metacyclic）。
- 本專題的位置：**同一 graph 不同 face system** 是比 cospectral 更極端的「譜失明」——\(L_0\) 完全相同，這點已由 T1 證明，屬已知事實的乾淨整理，不是新定理；新意在 matched catalogue 與 face-aware operators 的比較。

### 2.3 Hodge Laplacian 與 spectral clustering（下學期新知識）

- Kelner (2006)：bounded genus 圖 \(\lambda_2=O(g/n)\)，spectral partition 有效。
- Lim (2020, *SIAM Review*)「Hodge Laplacians on graphs」；Schaub et al. (2020, *SIAM Review*)「Random walks on simplicial complexes and the normalized Hodge 1-Laplacian」。
- Ebli–Spreemann (2019)：harmonic clustering——以 \(\ker L_1\) 做 edge clustering，是本專題 "\(L_1\) baseline" 的直接前身。
- 2023–2025：Hodge Laplacian 譜的 gradient/curl/harmonic 分離分析、simplicial neural networks 與 cell complex neural networks（Hajij、Bodnar 等）。**尚未看到有人用「同一 Cayley skeleton、不同 face system」做受控比較**——這是本專題可以填的小縫。

### 2.4 Lean / mathlib 現況

- mathlib 有 `SimpleGraph.adjMatrix`、`incMatrix`（無向）、`lapMatrix`，並已證 Laplacian 半正定與 **`rank_ker_lapMatrix_eq_card_ConnectedComponent`**（Laplacian 零空間維度 = 連通分量數）。這就是 T2 中「\(\operatorname{rank}B_1=V-1\)」的現成積木。
- mathlib 有 Hermitian 矩陣譜定理、有限群表示與 character 正交性、有限 abelian 群的 `AddChar`。
- mathlib **沒有**：rotation system、combinatorial maps、cellular surface、Hodge Laplacian、Cheeger 不等式、spectral clustering。→ 這些是本專題可以「自己寫定義 + 證小 lemma」的空間；做出來可整理成小型 Lean library（甚至投稿 mathlib 的部分基礎）。
- 外部專案：`GraphLib`（Lean 4 graph 演算法）、Formal Conjectures（Google DeepMind）等。

### 2.5 密碼學／資安與 Lean

- **Cayley hash functions**（Zémor、Tillich–Zémor、Charles–Goren–Lauter）：安全性化約為非交換群的 factorization／representation 問題；**碰撞就是 Cayley graph 上的 relator（閉路）**。LPS hash 已被 Tillich–Zémor 找到碰撞，Petit–Lauter–Quisquater 給出 preimage 攻擊並打破 Morgenstern hash；Petit–Quisquater「Rubik's for Cryptographers」(2013) 是綜述。
- Isogeny 密碼：supersingular isogeny graph 是 Ramanujan 圖；SIDH 2022 被 Castryck–Decru 攻破，但 CSIDH、SQIsign 仍活躍——spectral gap / expander 是其安全性分析工具。
- **量子錯誤更正（資訊保護的量子版）**：Kitaev toric code → hyperbolic surface codes（Breuckmann–Terhal 2016）；qLDPC 突破（Panteleev–Kalachev 2021、Leverrier–Zémor quantum Tanner codes）都建在 **Cayley complexes** 上；Dinur et al. 2021 的 \(c^3\)-LTC 用 left-right Cayley complex。2025–2026 仍有 hyperbolic code 的系統構造與 erasure threshold 研究。surface code 在 genus-\(g\) 曲面上 \(k=2g\)。
- **Lean 中的密碼學形式化**：VCVio（game-based 密碼證明框架）、ArkLib（SNARK：Sum-check、FRI、Fiat–Shamir 的機器驗證，Verified zkEVM 計畫）；Rust→Lean 驗證 pipeline（2026）。這是「Lean × 資安」目前最成熟的產業／學界交會點。

---

## 3. 第一版【學習方向】

目標：下學期開始時，能讀懂上述文獻、能寫 100–300 行的 Lean 證明、能自己算一個 surface code 的參數。

### 3.1 本學期（2026 Fall，剩約 10 週）

| 週 | 主題 | 教材 | 產出（可驗收） |
|---:|---|---|---|
| 6–7 | Lean 入門 | Natural Number Game → *Theorem Proving in Lean 4* ch.1–7 | 完成 NNG；安裝 Lean+mathlib 專案於 `lean/` |
| 8–9 | mathlib 線性代數 | *Mathematics in Lean* ch.9（Linear algebra）；讀 `Mathlib/Combinatorics/SimpleGraph/LapMatrix.lean` 原始碼 | 自己重證「\(x^\top Lx=\sum(x_i-x_j)^2\)」 |
| 8–10 | Cellular homology（補 T2/T3 的數學） | Hatcher §2.2 cellular homology；Mohar–Thomassen *Graphs on Surfaces* ch.3–4；Gross–Tucker ch.3 | 手寫 T2 組合版證明草稿（見 §4.2 L3–L5） |
| 10–11 | 表示論與 Cayley 譜 | Serre *Linear Representations* Part I；Babai 1979；Liu–Zhou §2–4 | 完成 T6 的 \(D_4,Q_8\) 閉式推導 |
| 12–13 | Spectral graph theory | Spielman 講義（Cheeger、Courant–Fischer）；von Luxburg *A Tutorial on Spectral Clustering* | 能解釋為何重根要比 projector |
| 6–9（並行） | **圖同構基礎** | Grohe–Schweitzer, *The Graph Isomorphism Problem*（CACM 2020）；McKay–Piperno, *Practical Graph Isomorphism II*（nauty/Traces）；Godsil–Royle *Algebraic Graph Theory* ch.1–3（automorphism、vertex-transitive、Cayley） | 寫出 `map_iso.py` 並完成 T5 |
| 10–12（並行） | Color refinement / WL 與 CI 問題 | Kiefer 的 WL 綜述；J. Morris 的 CI-problem 講義；Liu–Zhou 中 CI-graph 段落 | 1-WL 實作，跑完 catalogue |
| 14–16 | 量子碼入門 | Nielsen–Chuang ch.10（stabilizer、CSS）；Breuckmann–Terhal 2016 hyperbolic surface codes | 手算 \(\mathbb Z_4^2\) torus surface code 的 \([[n,k,d]]\) |

### 3.2 下學期（2027 Spring）

| 月 | 主題 | 教材 |
|---|---|---|
| 1 | Hodge Laplacian 與 simplicial spectral methods | Lim 2020；Schaub et al. 2020；Ebli–Spreemann 2019 |
| 1–2 | Lean 進階：Finset/Fintype 組合論證、`Matrix.rank`、`decide`/`native_decide` 做有限證書 | mathlib 原始碼 + Zulip；Lean community 的 *Functional Programming in Lean*（寫 certificate exporter） |
| 2 | Cayley hash 與群上 factorization 問題 | Petit–Quisquater 2013；Tillich–Zémor 2008（LPS collisions） |
| 2 | 同構型密碼：GMW 零知識、code equivalence | Goldreich–Micali–Wigderson 1986；Boneh–Shoup *Graduate Course in Applied Cryptography* Σ-protocol 章；Petrank–Roth 1997；LESS 規格文件與 2026 code-equivalence 綜述 |
| 2–3（選修） | Babai quasi-polynomial GI 的架構 | Babai 2015 arXiv:1512.03547 引言；Helfgott 的 Bourbaki 講稿 |
| 2–3 | qLDPC 與 Cayley complex（只讀概念） | Breuckmann–Eberhardt 2021 qLDPC review；Panteleev–Kalachev 2021 引言 |
| 3（選修） | Lean 密碼形式化 | VCVio、ArkLib 文件與範例 |

---

## 4. 第一版【研究方向】

### 4.1 本學期：根據三篇 reference 的具體目標

**R1. Brinkmann genus 演算法 → catalogue 的外部驗證與完整枚舉（主線）**

- 安裝／重寫 `multi_genus` 等價功能（或直接呼叫其程式），對 catalogue 中 10 個 Cayley skeleton 計算**真正的 minimum genus** 與「每個 genus 的 embedding 數」。
- 與本專題的 relator／uniform／local 三種 construction 比對：哪些 genus 只有 non-uniform rotation 才達得到？→ 直接支撐 T4（completeness 邊界）。
- 對 cubic 小圖（\(D_4,S_3,D_6,A_4\)）完成 genus distribution（每個 genus 的 rotation system 數），quotient by \(\operatorname{Aut}(\Gamma)\) → 完成 T5 / Gate A。
- 驗收：genus distribution 表 + 與 Brinkmann 程式的一致性 diff = 0。

**R2. Liu–Zhou → face-blindness 與 Cay-DS 的對照（主線）**

- 完成 T6：所有 catalogue 群的閉式譜，數值 diff = 0。
- 新增一張表：「不同 \(S\) 的 cospectral pair」（Cay-DS 現象） vs 「同 \(S\) 不同 \(\mathcal F\)」（face-blindness）。
- 對同 skeleton 的 matched pairs 算 \(\operatorname{Spec}(L_1)\)、dual、inflated spectra，檢查哪些 face-aware spectrum 能區分 Set B（同 genus 不同 cellulation）。
- 開放小問題（可寫成猜想 + 數據）：Set B 中是否存在 **\(L_1\)-cospectral 但 inequivalent** 的 face systems？若存在，就是「Hodge 譜也失明」的反例，很有價值。

**R3. Barthel–Buccoliero → 3D 實現（附章，選做）**

- 選 1–2 個 catalogue surface（如 \(D_4\) torus、\(Q_8\) genus 2），判斷其 Cayley skeleton 的某個 spatial embedding 是否 leveled，並用其演算法構造 \(\mathbb R^3\) 中的曲面——讓上學期報告 6.2.1 的「高 genus 視覺化」問題有一個嚴謹替代方案。
- 若時間不足直接放棄，不影響主線。

**本學期 Lean 試點（為下學期鋪路）**：在 Lean 中寫出 T1（face-blindness，幾乎是定義展開）與 \(\ker L_1=\ker B_1\cap\ker B_2^\top\)。

### 4.2 下學期：Spectral clustering × Lean × 資安

**R4. Hodge-aware spectral clustering 的受控比較（主線，延續 RESEARCH_PLAN Week 8–14）**

- 在 matched sets A/B 上比較 \(L_0\)、dual、inflated、\(L_1\)（gradient/curl/harmonic 分開）clustering；harmonic clustering 依 Ebli–Spreemann。
- 主結論形式：「在何種條件下 face-aware operator 嚴格增加資訊」（T1+T2 separation 的實驗延伸），重根一律用 projector distance。

**R5. Lean 形式化：Cayley surface 的組合 Hodge 定理（主線，核心貢獻）**

把 T2 改寫成**純組合**、適合 Lean 的版本，避開需要拓撲空間的 T3：

| Lemma | 內容 | 難度 | 依賴 |
|---|---|---|---|
| L1 | （T1）\(L_0\) 只依賴 \((G,S)\)，與 \(\mathcal F\) 無關 | 易 | 定義 |
| L2 | rotation system：\(\phi=\sigma\alpha\) 的 orbits 分割 darts；\(\alpha\) 是無不動點 involution | 易–中 | `Equiv.Perm`, `cycleType` |
| L3 | \(\ker(B_1^\top B_1+B_2B_2^\top)=\ker B_1\cap\ker B_2^\top\) | 中 | 半正定矩陣 |
| L4 | 若 \(B_1B_2=0\)，則 \(\dim\ker L_1=E-\operatorname{rank}B_1-\operatorname{rank}B_2\) | 中 | rank–nullity、正交補 |
| L5 | Cayley skeleton 連通 ⇒ \(\operatorname{rank}B_1=V-1\) | 中 | **mathlib `rank_ker_lapMatrix_eq_card_ConnectedComponent`**（需證 \(B_1B_1^\top=\) `lapMatrix`） |
| L6 | 每條邊恰在兩個 face 且方向相反、dual graph 連通 ⇒ \(\operatorname{rank}B_2=F-1\) | 中–難 | L5 套用到 dual graph |
| **Thm** | \(\dim\ker L_1=E-(V-1)-(F-1)=2-\chi=2g\) | 由 L3–L6 組合 | — |
| L7 | （T4.2）uniform rotation ⟺ \(\sigma\) 與所有 left translations 交換 | 中 | 群作用 |
| L8 | （T6 子集）\(\mathbb Z_m\times\mathbb Z_n\) Cayley graph 的特徵值 = character sums | 中–難 | `AddChar`、正交性 |
| M | catalogue 25 個實例的 \(B_1B_2=0\)、\(\dim\ker L_1=2g\) 由 Python 匯出、Lean 以 `decide` 驗證 | 中（工程） | certificate exporter |

- **最低目標**：L1–L5 + M（對 3 個小實例）。**理想目標**：完整 Thm + L7。**延伸**：L8。
- 注意：Thm 的組合版不需要 T3（「得到的空間真的是 surface」）——只需 L6 的組合條件，這是 Lean 可行性的關鍵設計。

**R6. 資安延伸 A：Cayley surface codes（主要延伸，推薦）**

- 對每個 V2 surface 定義 CSS code：qubits = edges，X-stabilizers = vertices（\(B_1\)），Z-stabilizers = faces（\(B_2^\top\)）。
- \(k=\dim\ker L_1=2g\)（**直接由 R5 的 Lean 定理保證**）；距離 \(d=\min(\text{最短非平凡同調圈 in }\Gamma,\ \text{in dual})\)——小圖可暴力計算。
- 研究問題：**同一 Cayley skeleton 上不同 face system 給出的碼，\(k\) 與 \(d\) 如何 trade-off？** \(L_0\) 看不見這個差異（T1），但碼的參數完全不同——這是 face-blindness 在資訊保護上的具體後果，可作為論文亮點。
- 比較對象：toric code（\(\mathbb Z_n^2\)）與 Breuckmann–Terhal 的 hyperbolic codes。
- 驗收：catalogue 的 \([[n,k,d]]\) 表 + 至少一組「同 skeleton、同 \(k\)、不同 \(d\)」或「同 skeleton、不同 \(k\)」的例子。

**R7. 資安延伸 B：Cayley hash 的碰撞與 face（附章）**

- 實作 toy Zémor／Tillich–Zémor hash（小 \(p\) 的 \(SL_2(\mathbb F_p)\)），說明：**碰撞 ⟺ 生成元上的非平凡 relator ⟺ Cayley graph 的閉路**；本專題 relator-orbit face search 本質上就是在找碰撞。
- 用 spectral gap（Liu–Zhou／expander）解釋輸出分布的 mixing；用 girth 解釋短碰撞不存在的下界。
- 定位：教學性重現已知結果 + 說明本專題工具在密碼分析中的角色；**不宣稱新密碼系統**。

---

### 4.3 貫穿兩學期的主軸：圖同構（isomorphism）

本專題幾乎每一層都在問「兩個物件是不是同一個」，但層次不同，必須分開：

| 層次 | 問題 | 專題中出現在 | 複雜度／工具 |
|---|---|---|---|
| I0 graph isomorphism | \(\Gamma\cong\Gamma'\)？ | Set C（\(D_4\) 與 \(\mathbb Z_2^3\) 的 cube）、Cay-DS | 一般 GI：Babai quasi-polynomial（2015）；實務用 nauty/Traces |
| I1 Cayley isomorphism（CI） | \(\operatorname{Cay}(G,S)\cong\operatorname{Cay}(G,T)\) 是否必來自 \(\operatorname{Aut}(G)\)？ | 生成集選擇、Liu–Zhou §CI | CI-group 分類仍未完成（Morris 綜述；Li–Lu–Pálfy） |
| I2 automorphism | \(\operatorname{Aut}(\Gamma)\) | T5 audit、S1 weight-preserving 對稱 | nauty / backtracking |
| I3 **map isomorphism** | 兩個 rotation systems 是否等價（含 mirror） | T5、Set B 的 A/B pairs | **多項式時間**：連通 map 的同構由一個 dart 的像決定，逐一試 \(|D|\) 個起點 → \(O(|D|^2)\) |
| I4 complex / code equivalence | 兩個 face system 給出的 CSS code 是否等價 | R6 | code equivalence；與 GI 有歸約關係（Petrank–Roth） |
| I5 spectral 不變量 vs 同構 | cospectral ⇏ isomorphic | T1、R2、R4 | WL color refinement、\(\operatorname{Spec}(L_0,L_1,L^*,L_{\inf})\) |

**重要的方法改進（直接影響本學期 T5）**：PROOF_PLAN 的 T5 原本是「對 \(\varphi\in\operatorname{Aut}(\Gamma)\) 逐一做 conjugation test」。改用 I3 的 map isomorphism：固定一個 dart \(d_0\)，對每個候選像 \(d\) 沿 \(\sigma,\alpha\) BFS 傳播，矛盾即失敗——不需要先算 \(\operatorname{Aut}(\Gamma)\)，也自然產生 **canonical form**（對所有起點取字典序最小的編碼）。等價 → 輸出 \(\varphi\) 作證書；不等價 → 兩個 canonical form 不同即為證書。

**R8. 同構證書 pipeline（本學期，取代 T5 的 conjugation 實作）**

- `code/map_iso.py`：map canonical form + 同構 witness；mirror 用 \(\sigma^{-1}\) 再跑一次。
- 用 `networkx`（VF2）或 `pynauty` 交叉驗證 I0/I2 結果。
- 驗收：六個 pending A/B entries 全部有 iso witness 或 canonical-form 不同的證書 → V3。

**R9. 「哪些譜不變量能分辨哪些同構類」表（兩學期）**

- 對 catalogue 所有 pairs，列出 \(\operatorname{Spec}(L_0)\)、\(\operatorname{Spec}(L_1)\)、dual、inflated、1-WL、2-WL 各自能否分辨 I0／I3 不同構的物件。
- 這張表把 R2 的開放問題（\(L_1\)-cospectral 但 map 不同構？）系統化，是論文中最清楚的「同構 vs 譜」貢獻。

**R10. 同構 × 密碼學（下學期，資安延伸 C）**

- GMW (1986) 的 **graph isomorphism 零知識證明**是密碼學中最經典的 Σ-protocol；以 Cayley graph pairs 實作 toy 版本。
- 誠實定位：GI 有 quasi-polynomial 演算法，且大多數隨機圖用 color refinement 即可分辨，**GI 本身不是安全假設**；其後量子化身是 **code equivalence / matrix code equivalence**（LESS、MEDS 一類簽章）。注意：LESS 在 NIST 2026-05 的第三輪（NIST IR 8610）已被淘汰，但 code equivalence 相關研究仍持續（2026 年有綜述）。
- 與 R6 銜接：face system 等價 ⇒ CSS code 等價；問「同 skeleton 的不同 face system，其 code 是否等價」就是 I3 → I4 的推進。

**Lean 中的同構 lemma（併入 R5）**

mathlib 已有 `SimpleGraph.Iso`（記號 `G ≃g G'`）、`Iso.symm`、`Iso.trans`，以及 graph 的 automorphism group。

| Lemma | 內容 | 難度 |
|---|---|---|
| I-L1 | 同構圖的 adjacency / Laplacian 經 permutation matrix 相似 ⇒ cospectral | 易–中 |
| I-L2 | cospectral ⇏ isomorphic：以一組具體反例 `decide` 驗證 | 易（有限計算） |
| I-L3 | iso 證書檢查器的 soundness：若 checker 通過，則 \(\varphi\) 是 graph／map isomorphism | 易 |
| I-L4 | 連通 map 的同構由一個 dart 的像唯一決定 | 中 |
| I-L5 | GMW protocol 的 special soundness：兩個不同 challenge 的接受 transcript ⇒ 可組合出 \(G_0\cong G_1\)（用 `Iso.trans`/`symm`） | 易–中，**Lean × 密碼學的理想入門題** |

---

## 5. 決策關卡（延續 RESEARCH_PLAN 的 Gate 精神）

- **Gate L（2027 年 1 月底）**：若 Lean 尚未完成 L3，R5 降級為「L1–L3 + 實例證書 M」，不追 L6。
- **Gate Q（2027 年 3 月）**：若 surface code 距離計算對 \(|E|>48\) 太慢，只報小 catalogue，不擴充群。
- **Gate H（隨時）**：R7 一旦擠壓 R4/R5 時間就砍掉，不影響論文完整性。

## 6. 論文最終結構建議（兩學期合併）

1. 群、rotation system、face system（上學期成果 + T3/T4）
2. Genus distribution、map isomorphism 與 automorphism audit（R1、R8、T5）
3. 頻譜 vs 同構：face-blindness、Cay-DS、WL（R2、R9、T6）
4. Hodge 理論與 spectral clustering（R4、T2）
5. **Lean 形式化：組合 Hodge 定理**（R5）
6. **應用：Cayley surface codes**（R6）＋ 同構型密碼（R10）＋ Cayley hash 附錄（R7）

## 參考文獻（新增部分）

- G. Brinkmann, *A Practical Algorithm for the Computation of the Genus*, arXiv:2005.08243.
- S. Barthel, F. Buccoliero, *Constructing embedded surfaces for cellular embeddings of leveled spatial graphs*, arXiv:2406.03800.
- X. Liu, S. Zhou, *Eigenvalues of Cayley Graphs*, arXiv:1809.09829.
- M. T. Schaub et al., *Random Walks on Simplicial Complexes and the normalized Hodge 1-Laplacian*, arXiv:1807.05044.
- S. Ebli, G. Spreemann, *A notion of harmonic clustering in simplicial complexes*, ICMLA 2019.
- L.-H. Lim, *Hodge Laplacians on Graphs*, SIAM Review 62 (2020).
- N. P. Breuckmann, B. M. Terhal, *Constructions and noise threshold of hyperbolic surface codes*, IEEE Trans. Inf. Theory (2016).
- N. P. Breuckmann, J. N. Eberhardt, *Quantum Low-Density Parity-Check Codes*, PRX Quantum (2021).
- C. Petit, J.-J. Quisquater, *Rubik's for Cryptographers*, Notices AMS (2013)；Tillich–Zémor, *Collisions for the LPS expander graph hash function*, ePrint 2008/173.
- L. Babai, *Graph Isomorphism in Quasipolynomial Time*, arXiv:1512.03547；M. Grohe, P. Schweitzer, *The Graph Isomorphism Problem*, CACM 63 (2020)。
- B. McKay, A. Piperno, *Practical Graph Isomorphism, II*, J. Symb. Comput. 60 (2014)。
- C. H. Li, Z. P. Lu, P. P. Pálfy, *Further restrictions on the structure of finite CI-groups*, J. Algebraic Combin. 26 (2007)。
- O. Goldreich, S. Micali, A. Wigderson, *Proofs that yield nothing but their validity*（GI 零知識, 1986/1991）；E. Petrank, R. Roth, *Is code equivalence easy to decide?*（1997）。
- NIST IR 8610（2026-05）：額外簽章第三輪名單。
- mathlib：`Mathlib/Combinatorics/SimpleGraph/LapMatrix.lean`、`SimpleGraph.Iso`；ArkLib（lean-lang.org/use-cases/arklib）；VCVio。
