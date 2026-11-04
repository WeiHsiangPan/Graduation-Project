# New-Conversation Starter — 5 November 2026

Copy the following into a new conversation with access to this repository. It is a compact orientation, not a replacement for the complete handoff.

---

We are continuing a research project in:

`C:\Users\user\Documents\GitHub\Graduation-Project`

Please first read:

1. `cayley-thesis/reports/research-handoff-2026-11-05.md`
2. `cayley-thesis/reports/partial-irrep-evaluation.md`
3. `cayley-thesis/reports/weekly-mathematical-pipeline-notes-2026-11-04.md`

My current objective is to exploit the Rubik's Cube group's structure to improve optimal solving algorithms. Small groups are controlled prototypes. Exact cube diameter remains a long-term aspiration, not a result. Continue using four evidence-based roles: advocate, opponent, critical reviewer, and verifier. Do not substitute praise or generic complexity warnings for specific proofs and comparisons.

## Conventions

- Cayley edges are right multiplication `g -> g*s`; left translations preserve them.
- All existing experiments use an inverse-closed generating set and unit move costs.
- Repository `Dn` has order `2n`; D4 has eight elements.
- A Cayley graph, a tetrahedral face-pairing graph, and a triangulation's quotient 1-skeleton are different objects.
- Specifying faces does not change the underlying graph distances or ordinary L0.
- Define the actual cube size, move set, metric, and state encoding before making cube claims.

## Implemented branches

**Relations and automata.** Sound endpoint-preserving, shortlex-decreasing rewrite rules retain at least one shortest representative per state. A finite surviving-word automaton with maximum length U gives diameter <= U. D4/D8/D16 examples attained U=3/5/9, matching BFS. Ordinary relation pools contain the same successful relations; topology has not been proved uniquely beneficial.

**Topological states.** The question is whether equal marked prefix states guarantee equal target invariants under identical continuations. Basic Ce/Cv fails: prefixes 130 and 301 share boundary data and H1=Z but have different boundary inclusion maps. Continuation 231 produces Z/4 versus Z/5. Enrichment by H1(M) and i*:H1(boundary M)->H1(M) separates the witness. Nine one-tetrahedron state-only H1 predictions succeed, but all three eligible prefixes become separate states. Two tetrahedra yield 1296 assignments, 66 accepted completions, 18 supported prefixes, nine shared state groups, and 27 both-accepted common-continuation comparisons with no homology disagreement. This is a prototype, not a general sufficiency/FPT theorem or homeomorphism classification.

**Circuit model.** Minimize ||f||² subject to Bf=delta_s-delta_t. This gives effective resistance R, with R<=distance, so ceil(R) is safe. The L1 flow objective equals distance, but its implementation currently checks BFS-derived primal/dual certificates rather than solving faster. Adding lambda||C^T f||² for face boundaries does not help this model: BC=0 and the electrical flow is B^T p, hence C^T f=0 already.

**Partial irreducibles.** For the implemented real/rational irreducible representations rho with invariant positive Gram H, define (general complex representations require conjugate transpose in place of transpose):

    K = |S|I - sum_s rho(s)
    X^dagger = H^-1 X^T H
    R_rho(g) = dim(rho)/|G| * trace[(I-rho(g)) K^-1 (I-rho(g))^dagger]

For nontrivial irreps, every contribution is nonnegative and their complete sum is R_eff. Partial sums R_T<=R_eff<=distance. Search uses:

    h_T(g,t) = max(1[g != t], ceil(R_T(g^-1*t)))

Partial bounds are not assumed consistent; the current tree IDA* has no global closed/visited table.

## Latest formal results

Formal circuit run:

`cayley-thesis/experiments/results/circuit-model/20261104T102000_570473Z/`

It covers 10 groups, 119 targets, and 25 face systems. Only four groups gain search nodes over free h=1. D4 and Z2³ have the same cube graph and spectrum, so ordinary Cayley spectra do not reveal whether the specified group is nonabelian.

Formal partial-irrep run:

`cayley-thesis/experiments/results/partial-irreps/20261104T171505_843220Z/`

It covers D4, S3, S4: 38 unique targets, 78 arms, 1148 arm–target combinations, five timing repetitions. Earlier partial timestamps are development runs.

D4 and S3: no irrep subset improves over free h=1. S4 counts summed over all targets:

| Method | No relation rules | With relation rules |
|---|---:|---:|
| Free h=1 | 912 | 740 |
| Any singleton irrep | 912 | 740 |
| sign + standard3d, budget sum d²=10 | 862 | 706 |
| standard3d + sign_twist3d, budget18 | 783 | 649 |
| Three higher-dimensional irreps, budget22 | 525 | 467 |
| All nontrivial irreps, budget23 | 525 | 467 |
| Full electrical heuristic | 525 | 467 |

The budget22 set contains standard3d, sign_twist3d, and matching_quotient2d. Its raw resistance differs from complete resistance at 12/24 states, but ceilings agree everywhere. Saving 1/23 of the d² proxy is only 4.35%, not substantial compression. Individual blocks can be useful only in combination because of ceiling thresholds.

Training chooses subsets on even target indices; odd indices are held out. This is same-group holdout, not cross-group generalization.

**No end-to-end speedup:** in the formal S4 run, free h=1 took about 1.453 ms including setup; budget22 about 90.125 ms, or 94.879 ms with rules. Setup includes the full representation factory and audit, selected inverse/contribution tables, and heuristic tables. The code still enumerates all group states. Nodes saved are not runtime saved.

## Code and verification

- `experiments/small_irreps.py`: exact complete D4/S3/S4 representation tables and audits.
- `experiments/partial_irrep_search.py`: exhaustive subsets and matched searches.
- `experiments/verify_partial_irreps.py`: read-only independent replay; does not import the runner, representation constructor, or original circuit solver, but shares existing group/transition definitions.
- `experiments/test_partial_irreps.py`: mathematical tests.

Paths in the code list are under `cayley-thesis/`.

Recorded latest verification: 94 tests passed; formal partial run returned PASS. Do not claim Lean formalization or complete independence of the group definitions.

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -m unittest discover -s cayley-thesis/experiments -p 'test_*.py'
python cayley-thesis/experiments/verify_partial_irreps.py cayley-thesis/experiments/results/partial-irreps/20261104T171505_843220Z
```

The formal partial source hashes match the current implementation. The old circuit source hash differs only because a summary label was corrected from “two” to “three” IDA* variants. Do not rewrite old evidence.

## Recommended next discussion

Focus on eliminating all-state setup: selected representations or verified group actions that can be evaluated directly from an encoded state. Compare with exact distances/pattern databases on the same small abstraction, because these dominate the corresponding resistance bound. Preserve free h=1 and existing relation-pruning controls, include setup/query/memory costs, and freeze choices before testing new groups or generators.

Use the complete handoff's roadmap gates. Keep topology-state sufficiency as a separate branch. Do not infer a cube-diameter proof from successful solving queries, claim novelty without a literature audit, or treat PackingStar's documentary as an algorithm specification. The shared methodological principle is to identify precisely what information survives each transformation and attach checkable evidence to the resulting claim.
