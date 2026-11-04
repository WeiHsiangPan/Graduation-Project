# The Core Mathematical Structure of Brinkmann's Genus Algorithm

**Source:** Gunnar Brinkmann, *A Practical Algorithm for the Computation of the Genus*, May 19, 2020, 14-page version in `references/Algorithm for the Computation of the Genus.pdf`.

## Abstract

The paper computes the minimum orientable genus of a finite simple connected graph. Its central contribution is a practical exact search over combinatorial embeddings: maximize the number of faces, use inexpensive face-count upper bounds to obtain genus lower bounds, and construct embeddings incrementally while prioritizing edges that necessarily increase genus. The contribution is the effective combination of valid bounds, search ordering, and inexpensive data operations; it is not a polynomial-time algorithm for general graph genus.

## Setting and notation

Let G=(V,E) be a finite simple connected graph with n=|V|, m=|E|, and at least one edge. Let D be its set of 2m darts. The involution alpha reverses each dart. A rotation system sigma consists of one cyclic order of the outgoing darts at each vertex. Composition acts from right to left. The face permutation is phi=sigma alpha; its orbits are the facial walks. Write F_sigma for their number and g_sigma for the genus of the associated closed orientable cellular embedding. The graph genus gamma(G) is the minimum genus over orientable embeddings.

The five statements below follow the suggested reading order. Only the fourth is the paper's Lemma 2.2; the local assertion in the third is its Remark 2.1. The remaining statements explicitly formulate standard background or consequences used by the algorithm.

## Theorem 1 — Genus optimization is face maximization

Every rotation system sigma determines a closed orientable cellular embedding, and

$$n-m+F_\sigma=2-2g_\sigma.$$

Consequently,

$$\boxed{\gamma(G)=1+\frac{m-n-\max_\sigma F_\sigma}{2}.}$$

**Justification.** Thicken vertices into disks and edges into untwisted bands according to the rotations, then cap every boundary component with a disk. The boundary components correspond to the orbits of sigma alpha. Euler's formula gives the identity. For connected graphs, the minimum orientable genus can be attained by a cellular embedding, so minimizing over rotation systems suffices.

**Role in the paper:** representation and objective, p. 2. The rotation-system correspondence is standard background.

## Lemma 2 — Edge insertion and sound genus pruning

Let H be a connected partial rotation system. Inserting an edge between existing vertices into two chosen corners has the following effects:

$$\Delta g=\begin{cases}0,&\text{the corners belong to the same face},\\1,&\text{the corners belong to distinct faces}.\end{cases}$$

An edge to a new vertex preserves genus. In particular, genus never decreases along an insertion branch.

For an embedded spanning subgraph H of G, call a missing edge e={u,v} **critical** when

$$\forall Q\in F(H),\quad \{u,v\}\nsubseteq V(Q),$$

where V(Q) is the set of vertices on the facial walk Q. Every insertion of a critical edge increases genus by one. Thus, if the current genus equals the allowed upper bound and a critical edge remains, the branch has no admissible completion.

**Proof.** A same-face insertion increases both m and F by one; a distinct-face insertion increases m by one and decreases F by one. An insertion introducing a vertex increases n and m by one and preserves F. Apply Euler's formula. Criticality forces every pair of endpoint corners to lie in distinct faces. Genus monotonicity makes the pruning rule valid even if other edges are inserted first.

**Role in the paper:** insertion strategy and critical-edge pruning, pp. 5–7; stated here as an explicit consequence.

## Theorem 3 — Safe genus lower bounds from relaxed face lengths

For a dart e, let f_sigma(e) be its actual face length. Then

$$F_\sigma=\sum_{e\in D}\frac1{f_\sigma(e)}.$$

If a computable U satisfies F_sigma <= U for every sigma, then

$$\boxed{\gamma(G)\ge\max\left\{0,\left\lceil1+\frac{m-n-U}{2}\right\rceil\right\}.}$$

For the nontrivial reduced graph, assume minimum degree at least three. A facial-like walk is a cyclic sequence of distinct darts with consecutive endpoints matching, allowing immediate reversal exactly at vertices of degree one. Let fw(e) be the shortest length of such a walk containing e. Every facial walk is facial-like, so fw(e) <= f_sigma(e), and fw(e)=fw(alpha(e)).

At a vertex v of degree d, sort the outgoing values as a_1 <= ... <= a_d. If t_1 <= ... <= t_d are the actual face lengths at the d corners at v, then

$$\boxed{(a_2,a_3,\ldots,a_d,a_d)_i\le t_i\quad(1\le i\le d).}$$

Consequently, a valid upper bound is

$$U_{\rm angle}=\sum_{v\in V}\left(\sum_{j=2}^{d_v}\frac1{a_{v,j}}+\frac1{a_{v,d_v}}\right).$$

**Proof sketch.** Each face of length ell contributes ell terms of 1/ell to the dart identity. At a corner, its actual face length is at least the maximum of the two incident fw values. Any i<d adjacent pairs in a cyclic order of d incident edges involve at least i+1 incident edges. Therefore the i-th smallest corner maximum is at least a_(i+1); the largest is a_d. Summing reciprocal lower bounds gives an upper bound on F_sigma. Euler's formula and integrality give the genus bound.

**Role in the paper:** lower-bound construction, pp. 3–4; the local domination assertion is Remark 2.1. The paper also gives a separate global sorted-vector bound.

## Lemma 4 — Localization of critical edges after the last face split

Suppose an algorithm begins with an embedded spanning tree and inserts missing edges, inserting a noncritical edge only if no critical edge exists. Consider a current partial embedding H containing a cycle. Let the most recent face-splitting insertion have produced faces with vertex sets A and B, recorded immediately after that split. Every currently critical edge e_c satisfies

$$\boxed{|e_c\cap(A\setminus B)|=|e_c\cap(B\setminus A)|=1.}$$

An edge is identified here with its two-element endpoint set.

**Proof.** Immediately before that split there were no critical edges, so e_c had both endpoints in some face. Subsequent insertions only merge faces. If that former face were not the split face, its vertex set would still be contained in a current face, contradicting criticality. Hence e_c is contained in A union B. If it misses A minus B, it is contained in B, again contradicting criticality; the symmetric argument applies to B minus A. These disjoint sets must therefore contain exactly one endpoint each.

**Role in the paper:** Lemma 2.2, p. 7. This is a necessary condition for criticality, not a sufficient one. The historical sets A and B need not remain vertex sets of current faces.

## Theorem 5 — Exactness of increasing-genus search

Let L <= gamma(G) be a valid integer lower bound. For h=L,L+1,..., run a complete search for a rotation system of genus at most h. Suppose corner insertion enumerates all represented extensions, the initial restriction retains every embedding or its mirror, and pruning discards only branches having no admissible completion. Then the first successful value h* satisfies

$$\boxed{h^*=\gamma(G).}$$

**Proof.** At h=gamma(G), completeness ensures that a minimum-genus embedding or its mirror survives. No h<gamma(G) can succeed. Therefore the first successful h is exactly gamma(G).

**Role in the paper:** the increasing-genus strategy appears on p. 3; independent verification is discussed on pp. 11–12. This theorem is a formal reconstruction of the correctness argument, not a separately numbered theorem in the paper.

## Algorithmic interpretation and limitations

The mathematical chain is: rotation system -> faces -> Euler genus -> safe lower bounds and monotone insertion -> exact bounded search. The paper's practical advantage comes from reducing the number of search nodes and the cost per node. Critical edges are prioritized; Lemma 4 cheaply rules out many critical-edge candidates; bitsets accelerate endpoint-in-face tests.

For labeled darts, direct enumeration contains

$$R(G)=\prod_{v\in V}(d_v-1)!$$

rotation systems. Face tracing takes O(n+m) time per complete system, giving the baseline bound O((n+m)R(G)). This describes naive enumeration, not a tight running-time theorem for the paper's optimized algorithm. The paper does not provide a full formal worst-case time or space bound for that implementation. Its practical performance does not remove exponential search behavior.

For implementation, face vertex sets suffice for testing whether an edge has a genus-preserving insertion, but not for enumerating all insertions: a facial walk can visit a vertex more than once, so individual corners must be maintained. A returned embedding proves an upper bound on gamma(G); minimality additionally requires a matching lower bound or complete exclusion of smaller genera.

## Recommended reading sequence

1. Page 2: rotation systems, facial walks, and Euler's formula.
2. Pages 5–7: corner insertion, search ordering, and critical edges.
3. Page 7: Lemma 2.2 and its historical face sets.
4. Pages 3–4: facial-like walks and Remark 2.1.
5. Pages 11–12: independent testing of genus and embedding enumeration.
