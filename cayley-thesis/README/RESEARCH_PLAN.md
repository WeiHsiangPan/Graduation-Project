# 2026 Fall Research Plan

## 1. Thesis question

本專題研究：對固定有限群與生成集

\[
\Gamma=\operatorname{Cay}(G,S),
\]

不同 orientable cellular face systems \(\mathcal F\)、不同 genus、不同 bottleneck 與不同 symmetry-breaking strength，如何影響 ordinary spectral clustering 與 face-sensitive／Hodge spectral methods？

資料單位固定為

\[
X=(G,S,\mathcal F,c,\omega),
\]

其中 \(c\) 是面系統的 construction witness，\(\omega\) 是可選 edge weights；
未做 asymmetry experiment 時取 \(\omega\equiv1\)。

主要比較不是「genus 是否等於 cluster count」，而是：

1. \(L_0\) 對 face system 的 blindness；
2. dual、incidence、inflated、\(L_1\) 是否增加可解釋的 face／cycle information；
3. symmetry breaking 是否使低頻 eigenspaces 與 clustering 不穩定；
4. genus effect 能否和 conductance、neck width 分離。

## 2. External mathematical anchors

三個正式外部問題與來源見 [THREE_REAL_PROBLEMS.md](THREE_REAL_PROBLEMS.md)：

1. graph genus and embedding enumeration；
2. spectral partitioning on bounded-genus graphs；
3. Cayley-DS and cospectral Cayley graphs。

本學期主線是 1 + 2；3 作為 ordinary spectrum 不足的代數背景。

## 3. Standard surface model

對 inverse-closed \(S\)，dart set 是

\[
D=G\times S,
\qquad
\alpha(g,s)=(gs,s^{-1}).
\]

每個頂點的 cyclic incident-edge order 組成 permutation \(\sigma\)，face permutation 為

\[
\phi=\sigma\alpha.
\]

固定 graph 的 orientable cellular embeddings 由 general local rotation systems 完整描述。三種 construction 必須分開標記：

| type | meaning | completeness |
|---|---|---|
| `relator_orbits` | 從指定 relator words 產生 undirected face orbits，再搜尋一致 orientation | 不完備 |
| `uniform_rotation` | 所有頂點使用同一 cyclic generator order | 只在 uniform Cayley-map subclass 完備 |
| `local_binary_rotation` | cubic graph 每個頂點選 normal／reverse order | 對固定 cubic graph 的 local cyclic orders 完備 |
| `explicit_rotation` | 逐頂點提供任意 cyclic order | 單一 witness；general framework |

對 degree \(d\)、\(n\) vertices，general search size 是

\[
((d-1)!)^n.
\]

這個指數成長是研究 automorphism quotient 的原因，不是程式實作細節。

## 4. Verification levels

### V0 — Witness recorded

Surface 有可重建的 relator words、uniform order、local bits 或 explicit rotations。

### V1 — Topology verified

- connected Cayley skeleton；
- \(S=S^{-1}\)；
- simple face boundaries；
- exact oriented-dart partition；
- one-cycle vertex link；
- \(\chi=V-E+F=2-2g\)。

### V2 — Hodge verified

- \(B_1B_2=0\)；
- \(L_1=B_1^\top B_1+B_2B_2^\top\)；
- \(\dim\ker L_1=2g\)。

### V3 — Equivalence audited

利用 \(\operatorname{Aut}(\Gamma)\) 與 mirror reversal，確認 A/B witnesses 不是同一 embedding 的重新標記。

目前 registry 中 25/25 已達 V2；六個同-profile A/B entries 尚未達 V3。

## 5. Authoritative catalogue

唯一 machine-readable source：

```text
data/surfaces/catalogue.json
```

驗證入口：

```text
handbook/verify_examples.py
```

核心 rotation／relator／validation library：

```text
code/surface_systems.py
```

### 5.1 Main matched sets

#### Set A — Same skeleton, different genus

- \(D_4:g=0,1\)
- \(Q_8:g=1,2,3\)
- \(D_6:g=0,1,2\)
- \(\mathbb Z_4^2:g=1,3\)
- \(D_8:g=0,1,3\)（extension）
- \(S_4:g=0,4\)（audit／stress test）

用途：證明 \(L_0\) 完全相同時，face-sensitive operators 才能看見 cellulation 與 homology 的改變。

#### Set B — Same skeleton and genus, different cellulations

- \(D_4:g=1\)，profiles \(4\times6\) 與 \(2\times4+2\times8\)；
- \(\mathbb Z_3^2:g=1\)，profiles \(9\times4\) 與 \(6\times3+3\times6\)；
- Q8 genus-2 A/B（同 profile，V3 pending）；
- \(\mathbb Z_4^2\) genus-3 A/B（同 profile，V3 pending）；
- \(\mathbb Z_3^2\) mixed A/B（同 profile，V3 pending）。

用途：分辨 genus signal、face-profile signal 與完整 incidence signal。

#### Set C — Same abstract graph, different regular group actions

- \(D_4\) 與 \(\mathbb Z_2^3\) 的 cube skeleton。

用途：區分 abstract graph spectrum 與 group-label／representation structure。

#### Set D — Negative controls

- \(S_3\)
- \(A_4\)

用途：避免從少數成功樣本推論所有有限群都自然產生多 genus families。

## 6. Corrected catalogue summary

| Group | \(|G|\) | degree | V2 surfaces | genus values |
|---|---:|---:|---:|---|
| \(D_4\) | 8 | 3 | 3 | 0, 1 |
| \(Q_8\) | 8 | 4 | 4 | 1, 2, 3 |
| \(D_6\) | 12 | 3 | 3 | 0, 1, 2 |
| \(\mathbb Z_4^2\) | 16 | 4 | 3 | 1, 3 |
| \(\mathbb Z_2^3\) | 8 | 3 | 2 | 0, 1 |
| \(\mathbb Z_3^2\) | 9 | 4 | 3 | 1 |
| \(S_3\) | 6 | 3 | 1 | 0 |
| \(A_4\) | 12 | 3 | 1 | 0 |
| \(D_8\) | 16 | 3 | 3 | 0, 1, 3 |
| \(S_4\) | 24 | 3 | 2 | 0, 4 |

重要修正：

- 舊 `all_valid_embeddings` 只搜尋 uniform rotations，已更名；
- 舊 `example_06_S4` 的 uniform surface 是 genus 4、六個 dodecagons，不是 sphere；
- \(S_4\) sphere 是 Coxeter relator surface，profile \(6\times4+8\times6\)；
- 舊 \(Q_8\) 的四組 pure-order relators 只保證 dart partition，不能取代 vertex-link check；registry 改用通過完整 manifold validation 的 explicit rotation witness；
- 同 profile 的 A/B entries 尚未完成 automorphism quotient，不能先宣稱 inequivalent。

## 7. Asymmetry design

每個 V2 surface 建立三種版本：

### S0 — Symmetric baseline

原始 Cayley skeleton、face system 與等權重。

### S1 — Weighted asymmetry

保持 \((V,E,\mathcal F)\)，設定

\[
w_e=1+\varepsilon\xi_e,
\qquad
\varepsilon\in\{0.01,0.05,0.10,0.20\},
\]

其中 \(\xi_e\) 有界、固定 seed、且 \(w_e>0\)。必須實際計算 weight-preserving automorphism group。

### S2 — Combinatorial asymmetry

使用 nonuniform local rotations、face-preserving subdivisions 或保持 homeomorphism type 的 local flips。每次修改後重新跑 V1/V2 checks。

不得用隨機刪邊或任意填面，因為可能破壞 closed-surface condition 或改變 genus。

## 8. Operators and clustering baselines

### Vertex baseline

\[
L_0=B_1B_1^\top,
\qquad
L_{\mathrm{norm}}=I-D^{-1/2}AD^{-1/2}.
\]

使用低頻 nontrivial eigenspace、row normalization 與 k-means。

### Face-aware baselines

- dual graph；
- vertex-face incidence graph；
- face-inflated graph。

### Hodge baseline

\[
L_1=B_1^\top B_1+B_2B_2^\top.
\]

分開 gradient、curl、harmonic subspaces；如果輸出 vertex clusters，必須明定 edge-to-vertex aggregation rule。

### Directed extension

若使用 \(S\neq S^{-1}\)，不得直接把 nonnormal adjacency eigenvectors 當成 undirected spectral clustering。先檢查 normality，並比較 Hermitian adjacency、magnetic Laplacian 或 singular-vector methods。

## 9. Evaluation matrix

| axis | values |
|---|---|
| genus | 0, 1, 2, 3, 4 |
| weighted asymmetry \(\varepsilon\) | 0, 0.01, 0.05, 0.10, 0.20 |
| neck width | at least 3 controlled levels |
| operators | \(L_0\), dual, incidence, inflated, \(L_1\) |
| random seeds | at least 10 per stochastic setting |
| cluster count | ground truth when available; otherwise declared selection rule |

Metrics：

- topology：Euler characteristic、Betti numbers、Hodge nullity；
- cuts：normalized cut、conductance；
- labels：ARI、NMI（只在有 ground truth 時）；
- stability：eigengap、projector distance、principal angles、variation of information；
- efficiency：construction time、eigensolver time、memory、sparsity。

對重根 eigenspaces，穩定性比較必須使用 whole-subspace projectors，不逐條比較任意 eigenvectors。

## 10. Sixteen-week schedule

| Week | Work | Acceptance criterion |
|---:|---|---|
| 1 | 固定 conventions、registry schema 與 verification levels | README、catalogue、validator 一致 |
| 2 | 整理 `surface_systems.py` API 與 unit tests | relator／uniform／local／explicit constructors 都有 tests |
| 3 | cubic exhaustive enumerator + mirror reduction | D4、S3 完整 rotation counts |
| 4 | automorphism canonicalization | Q8、Z4²、Z3² A/B equivalence table |
| 5 | sparse `SurfaceComplex`、\(B_1,B_2\) | 25 surfaces sparse Hodge checks |
| 6 | \(L_0\)、dual、incidence operators | identical-skeleton regression tests |
| 7 | inflated graph 與 normalized \(L_1\) | operator dimension/rank table |
| 8 | vertex spectral clustering baseline | first matched comparison table |
| 9 | face-aware／Hodge baselines | D4 and Q8 comparison figures |
| 10 | weighted asymmetry S1 | fixed-seed epsilon sweep |
| 11 | projector／principal-angle stability | repeated-eigenvalue-safe metrics |
| 12 | connected-sum synthetic controls | genus and neck width independently varied |
| 13 | full experiment matrix | reproducible configs and raw tables |
| 14 | statistical summary and negative results | confidence intervals and limitations |
| 15 | thesis writing and figure audit | every claim points to data／test |
| 16 | oral-defense package | slides, one-page contribution statement, demo |

## 11. Decision gates

### Gate A — after Week 4

若 automorphism quotient 尚未完成，停止新增有限群，集中 D4、Q8、D6、\(\mathbb Z_4^2\)。

### Gate B — after Week 8

若 dual／incidence baseline 尚未跑通，不開始新 clustering algorithm。

### Gate C — after Week 12

若 genus 與 neck width 未能獨立控制，不做「genus causes clustering」的因果敘述。

## 12. Minimum viable thesis

最低完整成果：

1. V3-audited small Cayley-surface catalogue；
2. topology + Hodge verified data pipeline；
3. ordinary、face-aware、Hodge spectral baselines；
4. controlled symmetry-breaking experiments；
5. genus、bottleneck、eigengap 的條件式結論；
6. 可重現 code、registry、tables 與 limitations。

不要求一定提出全新的 clustering algorithm；一個嚴格證明「ordinary spectrum 對哪些 surface changes 失明、face-aware operators 在何種條件才增加資訊」的結果已構成完整研究貢獻。
