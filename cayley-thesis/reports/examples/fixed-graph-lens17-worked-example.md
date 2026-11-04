# A fixed-graph example: L(17,3) and L(17,4)

## Verified statement

There are two closed, connected, orientable, five-tetrahedron triangulations with exactly the same labeled face pairs and with the following properties:

- Their manifolds are the standard layered lens spaces L(17,3) and L(17,4).
- Both have integral homology (Z, Z/17, 0, Z) and fundamental group Z/17.
- They are not homeomorphic, by the classical lens-space classification.
- Removing their identical final gluing yields two marked solid tori with identical boundary configurations, but different boundary homology inclusion maps.
- Their dual-graph Laplacians coincide, whereas their standard cellular one-dimensional Hodge Laplacians have different spectra.

The construction follows Regina's standard layered lens-space recipe. A standalone verifier checks the explicit quotient data, local links, orientation, chain conditions, and determinantal divisors. This is not a run of Regina's recognition engine. Mathematical identification uses the published construction; non-homeomorphism uses the classification theorem.

## Fixed graph and permutation convention

Let t0,...,t4 be tetrahedra with vertices 0,1,2,3. Let Fi be the face opposite vertex i. A tuple p=abcd means p(0)=a, p(1)=b, p(2)=c, p(3)=d. On Fi, use the affine map induced by p.

The graph is a path of five nodes with doubled path edges and a loop at each endpoint. It is 4-regular, has treewidth 1, and is not a Cayley graph.

| Paired faces | L(17,3): p | L(17,4): p |
|---|---|---|
| t1 F2 -> t0 F0 | 2103 | 1203 |
| t1 F3 -> t0 F1 | 0321 | 3021 |
| t2 F2 -> t1 F0 | 1203 | 1302 |
| t2 F3 -> t1 F1 | 3021 | 2031 |
| t3 F2 -> t2 F0 | 3102 | 2103 |
| t3 F3 -> t2 F1 | 0231 | 0321 |
| t4 F2 -> t3 F0 | 3102 | 1203 |
| t4 F3 -> t3 F1 | 0231 | 3021 |
| t4 F0 -> t4 F1 | 1230 | 1230 |
| t0 F3 -> t0 F2 | 1302 | 1302 |

Reverse face maps are the inverses of the listed maps. Every face is used exactly once. The two displayed assignments differ at eight of ten face maps; no one-map-change or minimality claim is made.

## Layered construction and restricted enumeration

Start from the one-tetrahedron layered solid torus with meridional intersection data (a,b,a+b)=(1,2,3). At each layer choose one of the inverse parameter updates

\[
A:(a,b)\mapsto(a,a+b),\qquad
B:(a,b)\mapsto(b,a+b).
\]

Apply four choices from the base toward the boundary, then use the standard closing fold. The resulting parameters are (p,q)=(2a+b,a). The verifier's words list choices in the opposite order, from top to base.

- Word AABB yields (a,b)=(3,11), hence L(17,3).
- Word ABAA yields (a,b)=(4,9), hence L(17,4).

All 16 four-letter binary words were checked: the resulting lens parameters are

| Word | Lens space | Word | Lens space |
|---|---|---|---|
| AAAA | L(8,1) | BAAA | L(16,5) |
| AAAB | L(13,2) | BAAB | L(23,7) |
| AABA | L(16,3) | BABA | L(24,7) |
| AABB | L(17,3) | BABB | L(27,8) |
| ABAA | L(17,4) | BBAA | L(19,5) |
| ABAB | L(22,5) | BBAB | L(26,7) |
| ABBA | L(19,4) | BBBA | L(25,7) |
| ABBB | L(23,5) | BBBB | L(29,8) |

This is complete only within this 16-assignment layering family, not within all 6^10 assignments of the fixed face-pairing scheme.

## Local topology

For both completed quotients:

\[
(f_0,f_1,f_2,f_3)=(1,6,10,5),\qquad \chi=0.
\]

The single vertex link has (V,E,F)=(12,30,20), Euler characteristic 2, no boundary, and is a connected orientable surface. It is therefore S^2. The checker also verifies the local surface condition at every vertex of the link, orientation consistency on all tetrahedral edges, and global orientability.

Before the final fold, each construction has f-vector (1,7,11,5), two unpaired faces t0 F2 and t0 F3, and a disk vertex link. Their identification as solid tori additionally uses the layered construction; a disk link alone would not establish that global type.

## Exact homology

The cellular chain complex of each completed triangulation is

\[
0\to\mathbb Z^5\xrightarrow{B_3}\mathbb Z^{10}
\xrightarrow{B_2}\mathbb Z^6\xrightarrow{B_1}\mathbb Z\to0.
\]

The verifier checks B1=0, B1 B2=0, B2 B3=0 and computes exact Smith invariant factors through gcds of minors:

\[
\operatorname{SNF}(B_2):1,1,1,1,1,17,
\qquad
\operatorname{SNF}(B_3):1,1,1,1.
\]

Consequently H1=Z/17, H3=Z, and H2=0. For H2, the unit invariant factors of B3 make its image primitive in C2; the quotient ker(B2)/im(B3) is torsion-free and has rank zero.

## Same boundary state, different inclusion maps

For both partial solid tori the boundary state is exactly

\[
\begin{aligned}
C_e=\{&((t_0:013,01),(t_0:012,01),+),\\
      &((t_0:013,03),(t_0:012,12),-),\\
      &((t_0:013,13),(t_0:012,02),-)\},
\end{aligned}
\]

and Cv has one class containing t0:0,t0:1,t0:2,t0:3. The state refers only to vertices on the unpaired faces.

Choose the common marked boundary basis

\[
x=[t_0:01],\qquad y=[t_0:13],\qquad [t_0:03]=x+y.
\]

These form a basis of H1(boundary;Z)=Z^2. Choosing primitive generators u3,u4 of the solid-torus homology, exact chain computations give

\[
(i_3)_*(x)=14u_3,\quad(i_3)_*(y)=-3u_3,
\]
\[
(i_4)_*(x)=13u_4,\quad(i_4)_*(y)=-4u_4.
\]

Thus

\[
\ker(i_3)_*=\langle3x+14y\rangle,
\qquad
\ker(i_4)_*=\langle4x+13y\rangle.
\]

The primitive meridian classes differ even though the boundary state and the abstract partial homology group agree. The common closing map identifies x with y. Both inclusion maps send x-y to 17 times an interior generator, giving H1=Z/17 after closing.

This is an explicit reason to investigate an enhanced state retaining boundary-to-interior homological data. It is not a proof that this enhancement satisfies all requirements of a general FPT algorithm.

## Fixed graph spectrum versus cellular Hodge spectrum

Count a self-loop twice in the graph adjacency diagonal. The graph Laplacian is

\[
L_\Gamma=\begin{pmatrix}
2&-2&0&0&0\\
-2&4&-2&0&0\\
0&-2&4&-2&0\\
0&0&-2&4&-2\\
0&0&0&-2&2
\end{pmatrix}=2L_{P_5}.
\]

Its common spectrum is

\[
\{0,3-\sqrt5,5-\sqrt5,3+\sqrt5,5+\sqrt5\}.
\]

With standard orthonormal cellular bases, L1=B2 B2^T because B1=0. The exact matrices are

\[
L_1^{(3)}=\begin{pmatrix}
3&0&-2&0&0&0\\0&12&0&0&0&2\\-2&0&4&-2&0&0\\
0&0&-2&4&-2&0\\0&0&0&-2&5&0\\0&2&0&0&0&6
\end{pmatrix},
\]

\[
L_1^{(4)}=\begin{pmatrix}
10&0&0&-2&0&0\\0&3&-2&0&0&0\\0&-2&4&0&0&-2\\
-2&0&0&4&-2&0\\0&0&0&-2&3&0\\0&0&-2&0&0&10
\end{pmatrix}.
\]

Both kernels are zero, consistent with real H1=0. However,

\[
\operatorname{tr}((L_1^{(3)})^2)=278,
\qquad
\operatorname{tr}((L_1^{(4)})^2)=282,
\]

so their Hodge spectra differ exactly, independently of floating-point comparisons. This distinguishes these cellulations; it is not the homeomorphism certificate, since discrete nonzero Hodge spectra depend on cellulation and metric.

## Non-homeomorphism certificate

The unoriented lens-space classification states

\[
L(p,q)\cong L(p,q')\quad\Longleftrightarrow\quad
q'\equiv\pm q^{\pm1}\pmod p.
\]

Since 3^(-1)=6 modulo 17, the orbit of 3 is {3,6,11,14}. It does not contain 4. Hence L(17,3) and L(17,4) are not homeomorphic.

## Representation-theoretic connection

For G=Z/17 and zeta=exp(2 pi i/17), the free linear actions on S3 are given by

\[
\rho_q(k)=\operatorname{diag}(\zeta^k,\zeta^{qk}),\qquad q=3,4.
\]

Their quotient manifolds are L(17,q). This connects the example to group representations, but the five-node face-pairing graph is not the Cayley graph of Z/17. Its own reflection group is C2, which can split the graph Laplacian into symmetric and antisymmetric blocks.

## Scope

- Established here: explicit fixed labeled face pairs, local validation, exact homology, equal boundary states, distinct inclusion maps, equal graph spectrum, distinct cellular Hodge spectra, and a classification-based non-homeomorphism certificate.
- Not established: a global minimal tetrahedron count, a one-gluing-change example, enumeration of every assignment on this graph, a new classification theorem, or a general homology-aware FPT algorithm.

## Reproduction and references

Run `fixed_graph_lens17.py`; it writes `fixed_graph_lens17.json`, containing gluing maps, boundary matrices, edge bases, link checks, states, spectra, and the 16-case restricted enumeration.

- Regina standard example construction: https://github.com/regina-normal/regina/blob/master/engine/triangulation/example3.cpp
- Regina layered solid-torus recipe: https://github.com/regina-normal/regina/blob/master/engine/triangulation/dim3/insertlayered.cpp
- Jaco and Rubinstein, Layered-triangulations of 3-manifolds: https://arxiv.org/abs/math/0603601
- Hatcher, Notes on Basic 3-Manifold Topology, lens-space classification (with a different parameter notation): https://pi.math.cornell.edu/~hatcher/3M/3M.pdf
