# Representation-Theoretic Spectral Decomposition of Cayley Graphs

**A project-oriented report on Xiaogang Liu and Sanming Zhou, _Eigenvalues of Cayley graphs_ (arXiv:1809.09829v3, 22 April 2022).**

## Abstract

For the purposes of spectral embedding, the central mechanism of this survey is that a Cayley adjacency operator is a group-algebra operator. Finite-group Fourier analysis reduces it to matrices indexed by irreducible representations. Abelian groups give scalar Fourier modes; conjugacy-invariant connection sets also give scalar blocks, by Schur's lemma. The same decomposition determines the graph Laplacian. Invariant spectral subspaces then yield orthogonally equivariant vertex coordinates. The last step is a standard consequence of symmetry, rather than an embedding theorem stated in the survey. The full survey additionally treats integrality, cospectrality, Ramanujan graphs, and other applications.

## Setting and conventions

Let G be a finite group of order N, and let S be a nonempty subset of G excluding the identity, with S=S^{-1} and <S>=G. Set k=|S|. We use the right-step convention: x is adjacent to xs for s in S. Thus

$$
(Af)(x)=\sum_{s\in S}f(xs),\qquad L=kI-A.
$$

This convention is isomorphic to the survey's convention by inversion of vertex labels; formulas below are internally expressed in the right-step convention. Write G-hat for a complete set of irreducible unitary complex representations, and write d_rho and chi_rho for the dimension and character of rho. Spectral unions below are multiset unions. The five statements are numbered for this report, not as in the source.

## Lemma 1 — Regular decomposition and Fourier basis

**Statement.** The regular representation of G contains each irreducible representation rho with multiplicity d_rho. In particular,

$$
\mathbb C[G]\cong\bigoplus_{\rho\in\widehat G}V_\rho^{\oplus d_\rho},
\qquad \sum_{\rho\in\widehat G}d_\rho^2=N.
$$

With counting-measure inner product on C^G, the functions

$$
q_{\rho,ij}(x)=\sqrt{\frac{d_\rho}{N}}\,\rho(x)_{ij}
$$

form an orthonormal basis. Equivalently, Schur orthogonality reads

$$
\frac1N\sum_{x\in G}\rho(x)_{ij}\overline{\sigma(x)_{ab}}
=\frac{\delta_{\rho\sigma}\delta_{ia}\delta_{jb}}{d_\rho}.
$$

**Proof sketch.** Maschke's theorem gives complete reducibility. Character orthogonality gives multiplicity d_rho in the regular representation. Matrix-coefficient orthogonality and the dimension identity give the stated basis.

**Source status.** Standard representation-theoretic background underlying Section 2.2; the report expands the mechanism invoked before the survey's Theorem 2.

## Theorem 2 — Fourier block decomposition of adjacency and Laplacian

**Statement.** For each rho, define the Hermitian matrix

$$
B_\rho=\sum_{s\in S}\rho(s).
$$

There exists a unitary matrix Q such that

$$
Q^*AQ=\bigoplus_{\rho\in\widehat G}
\left(I_{d_\rho}\otimes B_\rho\right),
\qquad
Q^*LQ=\bigoplus_{\rho\in\widehat G}
\left(I_{d_\rho}\otimes(kI_{d_\rho}-B_\rho)\right).
$$

Consequently,

$$
\operatorname{Spec}(A)=\biguplus_{\rho\in\widehat G}
d_\rho\cdot\operatorname{Spec}(B_\rho).
$$

If B_rho v=lambda v, then, for every u in V_rho,

$$
f_{u,v}(x)=u^*\rho(x)v
$$

is an adjacency eigenfunction with eigenvalue lambda and a Laplacian eigenfunction with eigenvalue k-lambda, whenever it is nonzero. Moreover, for every positive integer t,

$$
\operatorname{tr}(B_\rho^t)
=\sum_{s_1,\ldots,s_t\in S}\chi_\rho(s_1\cdots s_t).
$$

**Proof sketch.** Apply A to each matrix coefficient: rho(xs)=rho(x)rho(s), so the second matrix index transforms by B_rho. Lemma 1 supplies d_rho orthogonal copies of this block. Inverse closure gives B_rho^*=B_rho. The Laplacian formula follows from L=kI-A. Expanding B_rho^t and taking its trace gives the character power sums.

**Source status.** Matrix formulation of the mechanism behind Babai's Theorem 2 and Corollary 4 in Section 2.2; the Laplacian conversion is stated in Section 1. The explicit eigenfunction construction is included here as a derivation.

## Theorem 3 — Abelian graphs have character eigenvectors

**Statement.** If G is abelian, every irreducible representation is a character chi:G->U(1). The functions N^{-1/2}chi form an orthonormal eigenbasis, with

$$
A\chi=\lambda_\chi\chi,\qquad
\lambda_\chi=\sum_{s\in S}\chi(s),\qquad
L\chi=(k-\lambda_\chi)\chi.
$$

**Proof sketch.** Since chi(xs)=chi(x)chi(s), the adjacency equation follows immediately. Character orthogonality gives the basis.

**Example.** For the cycle on Z_n, n>=3, with S={+1,-1},

$$
\chi_j(x)=e^{2\pi ijx/n},\quad
\lambda_j=2\cos(2\pi j/n).
$$

The real and imaginary parts of chi_1 give regular-polygon coordinates. The associated nonzero Laplacian eigenvalue is 2-2cos(2pi/n).

**Source status.** Lovasz's Theorem 1 and Corollary 3 in Section 2.2, followed there by the circulant and cycle examples.

## Theorem 4 — Conjugacy-invariant connection sets give scalar blocks

**Statement.** Suppose S is a union of conjugacy classes of G. Then

$$
B_\rho=\lambda_\rho I_{d_\rho},\qquad
\lambda_\rho=\frac1{d_\rho}\sum_{s\in S}\chi_\rho(s).
$$

Each rho contributes d_rho^2 dimensions, and the total multiplicity of a numerical eigenvalue lambda is

$$
m(\lambda)=\sum_{\rho:\lambda_\rho=\lambda}d_\rho^2.
$$

**Proof sketch.** Conjugacy invariance makes the group-algebra element sum_{s in S}s central. Hence B_rho commutes with every rho(g). Schur's lemma makes B_rho scalar, and taking traces determines the scalar. The regular decomposition gives multiplicities.

**Source status.** Theorem 5 in Section 2.2, attributed there to Diaconis-Shahshahani and Zieschang, and also implicit in Babai's work. The survey calls these graphs normal Cayley graphs. This usage must be distinguished from normality of the regular subgroup in the graph automorphism group.

**Limitation.** Without conjugacy invariance, (1/d_rho)sum chi_rho(s) is only the mean eigenvalue of B_rho, not a formula for all its eigenvalues.

## Lemma 5 — Invariant spectral subspaces give equivariant coordinates

**Statement.** Let X be a finite undirected graph and H<=Aut(X). Define P_h by (P_h f)(x)=f(h^{-1}x). Let W be an H-invariant real subspace of dimension m, and let the columns of U be an orthonormal basis of W. Then

$$
AP_h=P_hA,\qquad P_hU=UR_h
$$

for orthogonal matrices R_h. In particular, W may be any direct sum of complete adjacency or Laplacian eigenspaces. With column-vector vertex coordinates p(x)=U_{x,:}^{\mathsf T},

$$
p(hx)=R_h p(x).
$$

Thus H acts on the coordinates by Euclidean isometries. If this action is vertex-transitive, all coordinate vectors have the same norm.

**Proof sketch.** Automorphisms commute with adjacency and preserve its eigenspaces. Since W is invariant, P_hU=UR_h, where R_h=U^T P_h U is orthogonal. These restrictions form a representation. Reading the row indexed by hx and transposing proves the coordinate identity. Transitivity then implies equal norms.

**Source status.** The commutation and eigenspace-invariance observation appears at the end of Section 2.3. The coordinate statement is a standard consequence developed here for the project; it is not a numbered embedding theorem in the survey.

**Limitation.** Equivariance does not imply injective vertex coordinates, a faithful geometric group action, crossing-free edges, or a cellular surface embedding. Arbitrary truncation inside a repeated eigenspace can destroy invariance.

## Project interpretation

The computational pipeline is

$$
(G,S)\longrightarrow\{B_\rho\}_{\rho\in\widehat G}
\longrightarrow\text{spectral subspaces}
\longrightarrow\text{equivariant coordinates}.
$$

Start with cyclic groups, then test dihedral groups using Section 3.4.1 and Theorem 51, and finally compare conjugacy-invariant and non-invariant generating sets in small symmetric groups. Verify both the block spectra and coordinate equivariance. To study topology, separately specify relators, faces, or a rotation system and construct the corresponding boundary operators. Vertex spectral data alone do not specify a Cayley complex or its homology.

## Reference

X. Liu and S. Zhou, *Eigenvalues of Cayley Graphs*, The Electronic Journal of Combinatorics 29(2) (2022), #P2.9. https://doi.org/10.37236/8569. Local reading version: arXiv:1809.09829v3. Core reading: Sections 1, 2.1-2.3; optional dihedral application: Section 3.4.1.
