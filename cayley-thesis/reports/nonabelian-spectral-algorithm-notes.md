# 非交換 Cayley 光譜與電路模型的算法接口

2026-11-04。依據 reference 中 Liu–Zhou, Eigenvalues of Cayley Graphs，尤其 §2.2；並延續本專案單位電阻模型。本文不是完整魔方群光譜的計算結果。

## 1. 精確設定

G 有限，S 不含單位元、inverse-closed 且生成 G，k=|S|；右乘邊 x→xs。A f(x)=sum_s f(xs)，L=kI-A。換計步制即可能換 S，故不能脫離生成集談魔方的唯一光譜。

對每個不可約酉表示 rho，令 d_rho 為維度，M_rho=sum_s rho(s)，K_rho=kI-M_rho。

A 酉等價於 direct_sum_rho (I_d_rho tensor M_rho)，L 同樣分解為 K_rho 的重複塊。

每個 M_rho 的特徵值，按塊內重數再重複 d_rho 次。sum_rho d_rho²=|G|。Abelian 情形所有 d=1；非交換群有高維不可約表示。S inverse-closed 保證每塊 Hermitian、譜為實數。

若 S 是共軛類的聯集，Schur lemma 給 M_rho=[sum_s chi_rho(s)/d_rho] I，此時整塊單一特徵值重數 d_rho²。沒有此條件，character 平均只給 trace(M_rho)/d_rho，不能代替整塊特徵值。對任何指定魔方操作集都需實際檢驗條件，不能由 nonabelian 自動假定。

表示保留乘法次序 rho(ab)=rho(a)rho(b)。同時將全部 rho(s) 換成特徵值或 trace，會遺失生成元之間的相對矩陣位置及非交換乘積資訊。

## 2. 專案 D4 的完整分塊例子

D4 在本專案指階數8。r⁴=s²=e，srs=r^-1，S={r,r^-1,s}。

四個一維表示 rho(r)=a，rho(s)=c，其中 a,c=+/-1。塊是2a+c，給3,1,-1,-3各一次。

一個二維表示 R=[[0,-1],[1,0]]、T=diag(1,-1)，有 R+R^-1=0，因此 M_2=T，塊特徵值+1,-1。此表示在 regular representation 出現兩次。

合併後 adjacency spectrum 為3¹,1³,(-1)³,(-3)¹；Laplacian spectrum 為0¹,2³,4³,6¹。

獨立驗證角色不依賴浮點 eigensolver，以Fraction消去精確核對直接鄰接矩陣各核空間的維度，總和8。

D4 此圖為 C4 square K2，即 Q3；與 catalogue 的 Z2³ 標準生成圖同構。兩者相同譜，最大電阻均5/6。普通未標記圖甚至不能辨識指定群的交換性。這不否定已知群的表示論計算價值。

## 3. 哪些圖性質可分析

Laplacian gap mu2=k-lambda2 反映擴散/分割；分析混合時間需處理二分圖的週期，可採lazy walk P=(I+A/k)/2。本例有lambda_min=-k，非lazy walk不能直接說會收斂。

trace(A^m) 計數長m閉走路；[A^m](e,e) 是長m等於單位元的操作字數。群表示塊可分解這些矩，但計數不是直接列出最有效剪枝關係。

若A有q個不同特徵值，直徑D≤q-1。理由：I,A,...,A^D線性獨立，可在距離D的一對頂點先消去最高次係數，再沿geodesic逐次消去。這是上界，不是通常等號。D4中q4、D3恰取等。

僅有特徵值清單不足以求每個端點距離或電阻；需要譜投影/特徵向量/表示矩陣的端點資訊。普通L0也不包含面系統與genus。

## 4. 電路分解

L^+ 在相同Fourier基底下分塊為 K_rho^+，平凡表示塊取0。非平凡表示的K正定，因圖連通。

R(u,v)=(delta_u-delta_v)^* L^+ (delta_u-delta_v)。若(mu_j,psi_j)為非零Laplacian正交模式，R(u,v)=sum_j |psi_j(u)-psi_j(v)|²/mu_j。

由矩陣係數的Schur正交性推得等價表示公式（右乘約定）：

R(u,v)=1/|G| sum_rho d_rho tr[(rho(u)-rho(v)) K_rho^+ (rho(u)-rho(v))^*]。

這是標準分塊的推論，不是宣稱reference給出新的魔方算法。它允許用表示矩陣查詢電阻而不顯式建立全鄰接矩陣，但仍須負擔所有所用表示的建構與塊求逆成本。

只計選定非平凡表示集合T，定義R_T為上述部分和。每項非負，所以0≤R_T≤R≤d。因此ceil(R_T)仍是合法整數距離下界。它不保證一致性：部分和是平方嵌入距離，不能直接沿用完整有效電阻的三角不等式。IDA*只需可採納性；若用graph-search A*，應允許重新開啟節點，或另外證明一致性。

選表示降低成本也會削弱下界，且取ceiling需精確算術或經證明的誤差下界。此研究候選尚未整合進完整魔方solver，也未證明效能。

獨立驗證角色另以Fraction核對D4全部8個群元素：四個1D貢獻加2D貢獻，逐點恰等於直接電路求解。例如g=r的1D合計5/24、2D貢獻3/8，總和7/12；g=r²s的1D合計1/3、2D貢獻1/2，總和5/6。只取2D時最大下界為3/4，全部表示時最大為5/6，兩者取ceiling均只有1，仍低於真實直徑3。

## 5. 負向控制與成本

全部不同稠密塊的元素數為sum d²=|G|，並非自動變成log|G|。已建好各塊後，稠密分解約sum O(d³)，另有表示評估/轉換成本；不應與稀疏圖最佳算法作不公平比較。

直接候選 h_rho(g,t)=ceil(||I-rho(g^-1t)||op / max_s ||I-rho(s)||op) 在酉表示下可採納且一致（分母0時定義0）。但若有非平凡involution生成元，分母為2、分子至多2，只給0或1。D4二維表示就是此退化情形。這種表示距離不能只因有理論保證就宣稱強。

reference §6的 graph energy=sum_i |lambda_i(A)| 是圖的不變量，與本專案變數f的電流耗散sum f_e²不同。兩者不能互換成同一個最小化目標。

## 6. 四角色結論與下一個驗證

支持：表示論能精確分塊，電路模型有自然接口，少量廉價表示可能避免完整建圖。

反對：同一圖可來自交換/非交換群；角色和譜均不能自動解最短字。完整表示系統可能仍昂貴，下界可能弱。

批判：固定S與計步成本；區分normal和一般Cayley圖；保留重數、特徵子空間與生成元矩陣；部分電阻下界不自動一致；不要將graph energy混為電路能量。

驗證：D4與Z2³的譜、重數、最大有效電阻已精確重算。下一個算法實驗應比較逐步添加表示的成本與下界強度，對照免費h=1、完整電阻與現有關係剪枝，並測未參與選擇的群/查詢。仍需實測才能說改進算法。

來源：https://arxiv.org/html/1809.09829v3#S2.SS2 （§2.2）；本地深入閱讀：../eigenvalues-cayley-core-report.md；電路基準：circuit-model-evaluation.md。
