# Relation search experiment

All completed target distances agree with BFS. Timing is observational; no asymptotic claim.

| Surface | Seed | Cancellation only | Ordinary generated | Faces generated | Difference (faces - ordinary) |
|---|---:|---:|---:|---:|---:|
| d4-g0-squares | 0 | 49 | 49 | 49 | +0 |
| d4-g0-squares | 1 | 49 | 49 | 49 | +0 |
| d4-g0-squares | 2 | 49 | 49 | 49 | +0 |
| d4-g1-hexagons | 0 | 49 | 49 | 49 | +0 |
| d4-g1-hexagons | 1 | 49 | 49 | 49 | +0 |
| d4-g1-hexagons | 2 | 49 | 49 | 49 | +0 |
| d4-g1-local | 0 | 49 | 49 | 49 | +0 |
| d4-g1-local | 1 | 49 | 49 | 49 | +0 |
| d4-g1-local | 2 | 49 | 49 | 49 | +0 |
| q8-g1-explicit | 0 | 33 | 33 | 33 | +0 |
| q8-g1-explicit | 1 | 33 | 33 | 33 | +0 |
| q8-g1-explicit | 2 | 33 | 33 | 33 | +0 |
| q8-g2-uniform-a | 0 | 33 | 33 | 33 | +0 |
| q8-g2-uniform-a | 1 | 33 | 33 | 33 | +0 |
| q8-g2-uniform-a | 2 | 33 | 33 | 33 | +0 |
| q8-g2-uniform-b | 0 | 33 | 33 | 33 | +0 |
| q8-g2-uniform-b | 1 | 33 | 33 | 33 | +0 |
| q8-g2-uniform-b | 2 | 33 | 33 | 33 | +0 |
| s4-g0-coxeter | 0 | 1261 | 1003 | 1003 | +0 |
| s4-g0-coxeter | 1 | 1261 | 1003 | 1003 | +0 |
| s4-g0-coxeter | 2 | 1261 | 1003 | 1003 | +0 |

Skipped q8-g3-uniform: no face relation within length bound.
Skipped s4-g4-uniform: no face relation within length bound.

## First saved nongeodesic irreducible word per case/method

These disprove local irreducibility implies shortest; absence within a bound is not a theorem.

| Surface | Seed | Method | Irreducible word | BFS shortest word |
|---|---:|---|---|---|
| d4-g0-squares | 0 | cancellation_only | r r r | r^-1 |
| d4-g0-squares | 1 | cancellation_only | r r r | r^-1 |
| d4-g0-squares | 2 | cancellation_only | r r r | r^-1 |
| d4-g1-hexagons | 0 | cancellation_only | r r r | r^-1 |
| d4-g1-hexagons | 0 | ordinary | r r r | r^-1 |
| d4-g1-hexagons | 0 | faces | r r r | r^-1 |
| d4-g1-hexagons | 1 | cancellation_only | r r r | r^-1 |
| d4-g1-hexagons | 1 | ordinary | r r r | r^-1 |
| d4-g1-hexagons | 1 | faces | r r r | r^-1 |
| d4-g1-hexagons | 2 | cancellation_only | r r r | r^-1 |
| d4-g1-hexagons | 2 | ordinary | r r r | r^-1 |
| d4-g1-hexagons | 2 | faces | r r r | r^-1 |
| d4-g1-local | 0 | cancellation_only | r r r | r^-1 |
| d4-g1-local | 0 | ordinary | r r r | r^-1 |
| d4-g1-local | 0 | faces | r r r | r^-1 |
| d4-g1-local | 1 | cancellation_only | r r r | r^-1 |
| d4-g1-local | 1 | ordinary | r s r | s |
| d4-g1-local | 1 | faces | r r r | r^-1 |
| d4-g1-local | 2 | cancellation_only | r r r | r^-1 |
| d4-g1-local | 2 | ordinary | r s r | s |
| d4-g1-local | 2 | faces | r r r | r^-1 |
| q8-g1-explicit | 0 | cancellation_only | i i i | -i |
| q8-g1-explicit | 0 | ordinary | i i j | -j |
| q8-g1-explicit | 0 | faces | i i j | -j |
| q8-g1-explicit | 1 | cancellation_only | i i i | -i |
| q8-g1-explicit | 1 | ordinary | i i -j | j |
| q8-g1-explicit | 1 | faces | i i j | -j |
| q8-g1-explicit | 2 | cancellation_only | i i i | -i |
| q8-g1-explicit | 2 | ordinary | i i j | -j |
| q8-g1-explicit | 2 | faces | i i j | -j |
| q8-g2-uniform-a | 0 | cancellation_only | i i i | -i |
| q8-g2-uniform-a | 0 | ordinary | i i i | -i |
| q8-g2-uniform-a | 0 | faces | i i j | -j |
| q8-g2-uniform-a | 1 | cancellation_only | i i i | -i |
| q8-g2-uniform-a | 1 | ordinary | i i i | -i |
| q8-g2-uniform-a | 1 | faces | i i j | -j |
| q8-g2-uniform-a | 2 | cancellation_only | i i i | -i |
| q8-g2-uniform-a | 2 | ordinary | i i j | -j |
| q8-g2-uniform-a | 2 | faces | i i j | -j |
| q8-g2-uniform-b | 0 | cancellation_only | i i i | -i |
| q8-g2-uniform-b | 0 | ordinary | i i i | -i |
| q8-g2-uniform-b | 0 | faces | i i j | -j |
| q8-g2-uniform-b | 1 | cancellation_only | i i i | -i |
| q8-g2-uniform-b | 1 | ordinary | i i i | -i |
| q8-g2-uniform-b | 1 | faces | i i j | -j |
| q8-g2-uniform-b | 2 | cancellation_only | i i i | -i |
| q8-g2-uniform-b | 2 | ordinary | i i j | -j |
| q8-g2-uniform-b | 2 | faces | i i j | -j |
| s4-g0-coxeter | 0 | cancellation_only | (12) (34) (12) | (34) |
| s4-g0-coxeter | 0 | ordinary | (23) (34) (23) (12) (34) | (34) (23) (12) |
| s4-g0-coxeter | 0 | faces | (23) (34) (23) (12) (34) | (34) (23) (12) |
| s4-g0-coxeter | 1 | cancellation_only | (12) (34) (12) | (34) |
| s4-g0-coxeter | 1 | ordinary | (23) (34) (23) (12) (34) | (34) (23) (12) |
| s4-g0-coxeter | 1 | faces | (23) (34) (23) (12) (34) | (34) (23) (12) |
| s4-g0-coxeter | 2 | cancellation_only | (12) (34) (12) | (34) |
| s4-g0-coxeter | 2 | ordinary | (23) (34) (23) (12) (34) | (34) (23) (12) |
| s4-g0-coxeter | 2 | faces | (23) (34) (23) (12) (34) | (34) (23) (12) |
