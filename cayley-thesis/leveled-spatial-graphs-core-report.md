# The Core Mathematical Idea of Leveled Spatial Graphs

**Source:** S. Barthel and F. Buccoliero, *Constructing embedded surfaces for cellular embeddings of leveled spatial graphs*, arXiv:2406.03800v2 (2025), [`references/Constructing embedded surfaces for cellular.pdf`](<references/Constructing embedded surfaces for cellular.pdf>).

## Abstract

The paper asks whether a **given spatial embedding** of a graph \(G\subset S^3\) can lie on a closed orientable surface \(S\subset S^3\) without changing the spatial graph, while every component of \(S\setminus G\) is an open disk. The central device is a *leveled* spatial graph: an unknotted spine separates the graph into fragments with controlled over-under relations. Two levels are placed on a sphere; the remaining fragments are carried by punctured spheres or by cylinders attached as handles. The construction must preserve two independent properties: the surface has no self-intersections in three-space, and the graph cuts the surface into disks. The algorithms provide sufficient certificates of existence, not a complete decision procedure or a minimum-genus algorithm.

## Setting and notation

Let \(G\subset S^3\) be a connected spatial graph. An embedding \(G\subset S\) is **cellular** if every connected component of \(S\setminus G\) is homeomorphic to an open disk. A *leveled* graph has an unknotted cycle \(C\subset G\), called its spine, such that each fragment \(f\) relative to \(C\) can be carried by a disk \(D_f\) with boundary identified with \(C\), the interior of \(D_f\) avoiding \(G\setminus f\) and every other \(D_g\). A Hamiltonian leveled graph has a spine that visits every vertex. In that case, the fragments can be treated as edges and encoded by their cyclic endpoint order, the *spine list*.

Write \(S_i\) for the surface after the \(i\)-th cylinder attachment and \(G_i\subset S_i\) for the graph built so far. A cylinder is the annulus \(P_i\cong S^1\times[0,1]\). Its two boundary circles are attached to face disks of \(S_{i-1}\setminus G_{i-1}\); the faces may be distinct or identical.

## Five central statements from the paper

### 1. Proposition 1 — The four-level existence theorem

**Statement.** Let \(G\subset S^3\) admit a leveled embedding with at most four levels. Then there exists a closed orientable embedded surface \(S\subset\mathbb R^3\) such that \(G\subset S\) and every component of \(S\setminus G\) is an open disk.

**Role.** Put the spine and two levels on an embedded sphere. Attach punctured spheres carrying the third and fourth levels on opposite sides. The resulting surface is embedded and the graph remains cellular. This is an existence theorem for the specified spatial graph; it makes no minimal-genus assertion.

### 2. Lemma 4 — The local test for cellularity

**Statement.** Suppose \(G_{i-1}\subset S_{i-1}\) is a cellular embedding of a Hamiltonian leveled spatial graph, and a cylinder \(P_i\) carrying new fragments \(f_1,\ldots,f_t\) is attached to obtain \(G_i\subset S_i\).

1. If the two ends of \(P_i\) are attached to two distinct face disks of \(S_{i-1}\setminus G_{i-1}\), then \(G_i\subset S_i\) is cellular.
2. If both ends are attached to one face disk \(D\), then \(G_i\subset S_i\) is cellular if and only if some pair among \(f_1,\ldots,f_t\) conflicts **with respect to the cyclic order on \(\partial D\)**.

**Role.** Conflict relative to the original spine is insufficient in the second case: the relevant cyclic order is that of the *current face boundary*. The paper's Example 3 exhibits precisely this distinction.

### 3. Proposition 6 — Face count under a valid attachment

**Statement.** Suppose \(G_{i-1}\subset S_{i-1}\) is cellular with \(n\) faces. Let the new cylinder \(P_i\) carry \(t\) fragments, embedded cellularly in \(P_i\), and suppose the attachment yields a cellular embedding \(G_i\subset S_i\). Then

\[
\#\pi_0(S_i\setminus G_i)=n-2+t.
\]

**Role.** The first spanning fragment cuts the annulus into a disk, and each further fragment adds one disk. The same formula applies whether the cylinder attaches to two distinct faces or, under Lemma 4's condition, twice to one face.

### 4. Theorem 1 — Soundness of Algorithm 1

**Statement.** Let \(G\) be a Hamiltonian leveled spatial graph. If Algorithm 1 terminates successfully on \(G\), then its output is a closed orientable surface \(S\subset\mathbb R^3\), embedded without self-intersections, such that \(G\subset S\) is cellular.

**Role.** The algorithm enumerates partitions of fragments into candidate cylinders, their upper/lower placements, and their endpoint assignments. Its rejection tests enforce admissible cylinder patterns, non-intersection, and the cellularity condition of Lemma 4.

### 5. Theorem 2 — Extension beyond Hamiltonian spines

**Statement.** Let \(G\) be a leveled spatial graph, with no assumption that its spine is Hamiltonian. If Algorithm 2 terminates successfully on \(G\), then its output is a closed orientable embedded surface \(S\subset\mathbb R^3\) on which \(G\) is cellularly embedded.

**Role.** Algorithm 2 contracts suitable edges of a spanning tree to reduce the problem to a Hamiltonian leveled graph, invokes Algorithm 1, and reverses the contractions by vertex splitting and edge subdivision on the constructed surface.

## Logical scope

Theorems 1 and 2 assert **soundness**:

\[
\text{successful termination}\;\Longrightarrow\;\text{an embedded cellular surface exists}.
\]

They do not prove the converse. Failure for one spine does not imply that the spatial graph has no cellular surface; the paper gives examples where a different spine succeeds. The conjecture that an appropriate spine always makes the construction succeed for leveled spatial graphs is left open. Neither the number of levels nor the genus of the constructed surface is the abstract graph's minimum orientable genus.

## Relation to the Cayley-surface project

The project's rotation systems construct cellular embeddings of an **abstract** Cayley graph and supply face systems for Euler-genus and Hodge calculations. This paper starts with a **fixed spatial realization** \(G\subset S^3\) and asks for a compatible embedded surface. If a Cayley graph is first spatially embedded and shown to be leveled, the paper can provide a geometric construction of one face system. It does not enumerate all face systems or study the spectra of the resulting cellulation.
