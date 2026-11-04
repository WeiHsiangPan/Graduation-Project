"""Exact small-Cayley electrical-flow experiment; Python standard library only.

All undirected edges occur once, with unit resistance and unit move cost.
No full-graph preprocessing cost is hidden as an algorithmic speedup.
"""
from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from fractions import Fraction as F
import hashlib
import json
import sys
from pathlib import Path
from time import perf_counter

import relation_search as source


def solve(matrix, rhs):
    """Exact Gaussian elimination; fail on singular systems."""
    n = len(rhs)
    a = [[F(x) for x in row] + [F(rhs[i])] for i, row in enumerate(matrix)]
    for k in range(n):
        p = next((i for i in range(k, n) if a[i][k]), None)
        if p is None:
            raise ValueError("Singular system")
        a[k], a[p] = a[p], a[k]
        scale = a[k][k]
        a[k] = [v / scale for v in a[k]]
        for i in range(n):
            if i != k and a[i][k]:
                scale = a[i][k]
                a[i] = [x - scale * y for x, y in zip(a[i], a[k])]
    return [row[-1] for row in a]


def graph_edges(transitions):
    edges = sorted({tuple(sorted((u, v))) for u, row in enumerate(transitions)
                    for v in row if u != v})
    if any(u not in transitions[v] for u, row in enumerate(transitions) for v in row):
        raise ValueError("Undirected inverse-closed graph required")
    return edges


def distances(transitions, source_vertex):
    d = [-1] * len(transitions)
    d[source_vertex] = 0
    queue = deque([source_vertex])
    while queue:
        u = queue.popleft()
        for v in transitions[u]:
            if d[v] == -1:
                d[v] = d[u] + 1
                queue.append(v)
    if -1 in d:
        raise ValueError("Disconnected graph")
    return d


def resistance_table(transitions, identity):
    n = len(transitions)
    edges = graph_edges(transitions)
    lap = [[0] * n for _ in range(n)]
    for u, v in edges:
        lap[u][u] += 1
        lap[v][v] += 1
        lap[u][v] -= 1
        lap[v][u] -= 1
    free = [v for v in range(n) if v != identity]
    grounded = [[lap[u][v] for v in free] for u in free]
    potentials, resistances = [], []
    for target in range(n):
        p = [F(0)] * n
        if target != identity:
            values = solve(grounded, [-int(u == target) for u in free])
            for u, value in zip(free, values):
                p[u] = value
        b = [int(u == identity) - int(u == target) for u in range(n)]
        assert all(sum(lap[u][v] * p[v] for v in range(n)) == b[u] for u in range(n))
        energy = sum((p[u] - p[v]) ** 2 for u, v in edges)
        assert energy == p[identity] - p[target]
        potentials.append(p)
        resistances.append(energy)
    return {"potentials": potentials, "resistances": resistances}


def ceiling(q):
    return -(-q.numerator // q.denominator)


def search_ida(transitions, identity, target, inverses, heuristic):
    """IDA*, same generator order and inverse cancellation in both arms.

    No BFS depth bound, visited table, or relator pruning is used.
    """
    generated = expanded = 0
    found_word = None

    def visit(u, depth, bound, last, word):
        nonlocal generated, expanded, found_word
        value = depth + heuristic(u)
        if value > bound:
            return value
        if u == target:
            found_word = word
            return -1
        expanded += 1
        next_bound = float("inf")
        for move, v in enumerate(transitions[u]):
            if last is not None and move == inverses[last]:
                continue
            generated += 1
            result = visit(v, depth + 1, bound, move, word + [move])
            if result == -1:
                return -1
            next_bound = min(next_bound, result)
        return next_bound

    started = perf_counter()
    bound = heuristic(identity)
    while True:
        result = visit(identity, 0, bound, None, [])
        if result == -1:
            return {"distance": len(found_word), "word": found_word,
                    "generated": generated, "expanded": expanded,
                    "seconds": perf_counter() - started}
        if result == float("inf"):
            raise ValueError("No solution")
        bound = result


def certify_l1(transitions, identity, target, path):
    """Shortest path primal flow and 1-Lipschitz distance dual certificate."""
    edges = graph_edges(transitions)
    edge_index = {e: i for i, e in enumerate(edges)}
    flow = [0] * len(edges)
    u = identity
    for move in path:
        v = transitions[u][move]
        flow[edge_index[tuple(sorted((u, v)))]] += 1 if u < v else -1
        u = v
    assert u == target
    divergence = [0] * len(transitions)
    for (u, v), amount in zip(edges, flow):
        divergence[u] += amount
        divergence[v] -= amount
    assert divergence == [int(v == identity) - int(v == target) for v in range(len(transitions))]
    dual = distances(transitions, target)
    assert all(abs(dual[u] - dual[v]) <= 1 for u, v in edges)
    cost = sum(abs(x) for x in flow)
    assert cost == dual[identity] - dual[target] == len(path)
    return {"flow": flow, "dual_potential": dual, "primal_cost": cost,
            "dual_value": dual[identity] - dual[target]}


def run():
    catalogue_path = source.ROOT / "data/surfaces/catalogue.json"
    catalogue = json.loads(catalogue_path.read_text(encoding="utf-8"))
    groups = []
    for key, spec in catalogue["groups"].items():
        started = perf_counter()
        group, generators, transitions, inverses, identity = source.model(spec)
        model_seconds = perf_counter() - started
        started = perf_counter()
        truth = source.bfs(transitions, identity)
        bfs_seconds = perf_counter() - started
        started = perf_counter()
        electrical = resistance_table(transitions, identity)
        electrical_seconds = perf_counter() - started
        r = electrical["resistances"]
        elements = group["elements"]
        index = {g: i for i, g in enumerate(elements)}
        # Left translations preserve right-generator Cayley edges.
        started = perf_counter()
        differences = [[index[group["mul"][group["inv"][g], t]] for t in elements] for g in elements]
        h_tables = [[ceiling(r[differences[u][t]]) for u in range(len(elements))]
                    for t in range(len(elements))]
        lookup_seconds = perf_counter() - started
        cases = []
        for target in range(len(elements)):
            h = h_tables[target]
            target_distances = distances(transitions, target)
            assert all(h[u] <= target_distances[u] for u in range(len(elements)))
            assert all(h[u] <= 1 + h[v] for u, row in enumerate(transitions) for v in row)
            assert r[target] <= len(truth[target])
            baseline = search_ida(transitions, identity, target, inverses, lambda u: 0)
            nonzero = search_ida(transitions, identity, target, inverses, lambda u: int(u != target))
            circuit = search_ida(transitions, identity, target, inverses, lambda u: h[u])
            assert baseline["distance"] == nonzero["distance"] == circuit["distance"] == len(truth[target])
            cases.append({"target": target, "distance": len(truth[target]), "resistance": r[target],
                          "heuristic": ceiling(r[target]), "baseline": baseline, "nonzero": nonzero, "circuit": circuit,
                          "l1_certificate": certify_l1(transitions, identity, target, truth[target])})
        faces_report = []
        for item in catalogue["surfaces"]:
            if item["group"] != key:
                continue
            faces = source.construct(group, generators, item["construction"])
            validation = source.surfaces.validate_surface(group, generators, faces)
            if not validation["valid"]:
                raise ValueError(validation)
            # Gradient line integral telescopes around every oriented face.
            for p in electrical["potentials"]:
                for face in faces:
                    circulation = sum(p[index[face[j]]] - p[index[face[(j + 1) % len(face)]]]
                                      for j in range(len(face)))
                    assert circulation == 0
            faces_report.append({"id": item["id"], "genus": item["genus"],
                                 "faces": [[index[v] for v in face] for face in faces],
                                 "electrical_face_penalty": 0})
        groups.append({"group": key, "vertices": len(elements), "edges": graph_edges(transitions),
                       "transitions": transitions, "identity": identity,
                       "diameter": max(len(w) for w in truth.values()),
                       "resistance_diameter_lower_bound": ceiling(max(r)),
                       "max_resistance": max(r), "potentials": electrical["potentials"],
                       "surfaces": faces_report, "cases": cases,
                       "timing": {"model": model_seconds, "bfs_truth": bfs_seconds,
                                  "electrical_preprocessing": electrical_seconds,
                                  "heuristic_lookup": lookup_seconds},
                       "totals": {arm: {metric: sum(c[arm][metric] for c in cases)
                                         for metric in ("generated", "expanded", "seconds")}
                                  for arm in ("baseline", "nonzero", "circuit")}})
    return {"schema_version": 1, "groups": groups,
            "catalogue_sha256": hashlib.sha256(catalogue_path.read_bytes()).hexdigest(),
            "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "scope": "Exact full-graph small-group study; not a cube solver or scalability proof. "
                     "L1 solved by matching primal/dual certificates, not an independent LP solver. "
                     "Electrical preprocessing builds the full graph; single-run timings are descriptive. "
                     "The target-specific O(V^2) lookup is an experimental convenience, not compression."}


def summary(report):
    lines = ["# 電路模型：小群精確實驗", "", report["scope"], "",
             "|群|V|直徑 D|最大 R（精確）|ceil 最大 R|節點 h=0|節點 非終點h=1|節點 ceil R|電阻預處理秒|BFS 秒|",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for g in report["groups"]:
        lines.append(f'|{g["group"]}|{g["vertices"]}|{g["diameter"]}|{g["max_resistance"]}|'
                     f'{g["resistance_diameter_lower_bound"]}|{g["totals"]["baseline"]["generated"]}|'
                     f'{g["totals"]["nonzero"]["generated"]}|'
                     f'{g["totals"]["circuit"]["generated"]}|{g["timing"]["electrical_preprocessing"]:.6f}|'
                     f'{g["timing"]["bfs_truth"]:.6f}|')
    lines += ["", "所有目標：電流守恆、精確能量恒等式、R≤距離、ceil(R)可採納且一致、",
              "三種IDA*最優長度、L1原始/對偶證書皆核對通過。",
              "所有catalogue貼面上的電流環流均精確為0；因此非負面環流懲罰不改變二次模型最優解。",
              "節點差不是總時間加速；預處理、查表與搜尋時間分開保存在results.json。",
              "同一Cayley圖的單源最大距離等於直徑，依據左平移圖自同構。", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    result = run()
    folder = source.ROOT / "experiments/results/circuit-model" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    folder.mkdir(parents=True)
    (folder / "results.json").write_text(json.dumps(result, default=str, ensure_ascii=False, indent=2), encoding="utf-8")
    (folder / "summary.md").write_text(summary(result), encoding="utf-8")
    print(folder)
    print(summary(result))
