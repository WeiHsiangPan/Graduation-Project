"""Exact partial-irrep bounds vs electrical flow and existing shortlex pruning.

Rational, possibly nonorthogonal bases use the invariant Gram adjoint.
No global visited table; admissible but inconsistent partial bounds are allowed.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from fractions import Fraction as F
import hashlib
from itertools import combinations
import json
from pathlib import Path
from statistics import median
import sys
from time import perf_counter

import circuit_model as circuit
import relation_search as source
import small_irreps


def eye(n):
    return [[F(i == j) for j in range(n)] for i in range(n)]


def transpose(a):
    return [list(row) for row in zip(*a)]


def matmul(a, b):
    return [[sum(x * y for x, y in zip(row, col)) for col in zip(*b)] for row in a]


def inverse(a):
    return transpose([circuit.solve(a, col) for col in eye(len(a))])


def build_contribution(rep, generators_indices, order):
    started = perf_counter()
    d = rep["dimension"]
    identity = eye(d)
    matrices = rep["matrices"]
    k = [[len(generators_indices) * identity[i][j] -
          sum(matrices[s][i][j] for s in generators_indices)
          for j in range(d)] for i in range(d)]
    if all(x == 0 for row in k for x in row):
        return [F(0)] * order, {"seconds": perf_counter() - started, "dimension_squared": d*d}
    kinv = inverse(k)
    h = rep["gram"]
    assert matmul(k, kinv) == identity
    assert matmul(transpose(k), h) == matmul(h, k)
    hinv = inverse(h)
    inverse_seconds = perf_counter() - started
    clock = perf_counter()
    values = []
    for matrix in matrices:
        delta = [[identity[i][j] - matrix[i][j] for j in range(d)] for i in range(d)]
        adjoint = matmul(matmul(hinv, transpose(delta)), h)
        product = matmul(matmul(delta, kinv), adjoint)
        value = F(d, order) * sum(product[i][i] for i in range(d))
        assert value >= 0
        values.append(value)
    return values, {"seconds": perf_counter() - started,
                    "inverse_seconds": inverse_seconds,
                    "evaluation_seconds": perf_counter() - clock,
                    "dimension_squared": d*d,
                    "max_fraction_bits": max(max(v.numerator.bit_length(), v.denominator.bit_length()) for v in values)}


def contribution(rep, generators_indices, order):
    return build_contribution(rep, generators_indices, order)[0]


def ida(transitions, identity, target, inverses, heuristic, rules):
    generated = expanded = pruned = rules_checks = 0
    answer = None

    def visit(u, word, bound, last):
        nonlocal generated, expanded, pruned, rules_checks, answer
        estimate = len(word) + heuristic(u)
        if estimate > bound:
            return estimate
        if u == target:
            answer = word
            return -1
        expanded += 1
        next_bound = float("inf")
        for move, v in enumerate(transitions[u]):
            if last is not None and move == inverses[last]:
                continue
            generated += 1
            candidate = word + [move]
            rejected = False
            for left, _ in rules:
                rules_checks += 1
                if len(candidate) >= len(left) and tuple(candidate[-len(left):]) == tuple(left):
                    pruned += 1
                    rejected = True
                    break
            if rejected:
                continue
            result = visit(v, candidate, bound, move)
            if result == -1:
                return -1
            next_bound = min(next_bound, result)
        return next_bound

    started = perf_counter()
    bound = heuristic(identity)
    while True:
        result = visit(identity, [], bound, None)
        if result == -1:
            return {"word": answer, "distance": len(answer), "generated": generated,
                    "expanded": expanded, "pruned": pruned, "rules_checks": rules_checks,
                    "seconds": perf_counter() - started}
        if result == float("inf"):
            raise ValueError("No surviving solution")
        bound = result


def prepare_rules(catalogue, key, group, generators, transitions, inverses):
    started = perf_counter()
    item = next(item for item in catalogue["surfaces"] if item["group"] == key)
    faces = source.construct(group, generators, item["construction"])
    validation = source.surfaces.validate_surface(group, generators, faces)
    assert validation["valid"] and validation["genus"] == item["genus"]
    relators = sorted({source.canonical(tuple(generators.index(s) for _, s in
                       source.surfaces.darts_of_face(group, generators, face)), inverses)
                       for face in faces}, key=lambda w: (len(w), w))
    rules = source.rules_for(relators, inverses)
    build_seconds = perf_counter() - started
    started = perf_counter()
    source.verify_rules(rules, transitions)
    validation_seconds = perf_counter() - started
    # Adjacent inverse moves are already eliminated identically in every arm.
    noncancellation = [(left, right) for left, right in rules
                       if not (len(left) == 2 and not right and left[1] == inverses[left[0]])]
    return {"surface": item["id"], "relators": relators, "rules": noncancellation,
            "build_seconds": build_seconds, "validation_seconds": validation_seconds}


def run_group(catalogue, key, repeats):
    clock = perf_counter()
    group, generators, transitions, inverses, identity = source.model(catalogue["groups"][key])
    model_seconds = perf_counter() - clock
    n = len(transitions)
    elements = group["elements"]
    index = {g: i for i, g in enumerate(elements)}
    generator_indices = [index[s] for s in generators]
    clock = perf_counter()
    library = small_irreps.representations(key, group)
    library_seconds = perf_counter() - clock
    clock = perf_counter()
    representation_audit = small_irreps.validate(library, group)
    rep_audit_seconds = perf_counter() - clock
    clock = perf_counter()
    truth = source.bfs(transitions, identity)
    bfs_seconds = perf_counter() - clock
    clock = perf_counter()
    electrical = circuit.resistance_table(transitions, identity)["resistances"]
    electrical_seconds = perf_counter() - clock
    clock = perf_counter()
    differences = [[index[group["mul"][group["inv"][g], t]] for g in elements] for t in elements]
    difference_seconds = perf_counter() - clock
    rule_data = prepare_rules(catalogue, key, group, generators, transitions, inverses)
    contributions = []
    for rep in library:
        values, cost = build_contribution(rep, generator_indices, n)
        if any(values):
            contributions.append({"name": rep["name"], "dimension": rep["dimension"],
                                  "values": values, "cost": cost})
    assert all(sum(rep["values"][g] for rep in contributions) == electrical[g] for g in range(n))

    heuristic_specs = [{"name": "free_h1", "members": [], "values": [F(0)] * n,
                        "dimension_squared": 0, "representation_seconds": 0},
                       {"name": "full_electrical", "members": [], "values": electrical,
                        "dimension_squared": None, "representation_seconds": electrical_seconds}]
    for count in range(1, len(contributions) + 1):
        for selected in combinations(contributions, count):
            combine_start = perf_counter()
            values = [sum(rep["values"][g] for rep in selected) for g in range(n)]
            combine_seconds = perf_counter() - combine_start
            heuristic_specs.append({"name": "+".join(rep["name"] for rep in selected),
                                    "members": [rep["name"] for rep in selected],
                                    "values": values,
                                    "combination_seconds": combine_seconds,
                                    "dimension_squared": sum(rep["dimension"]**2 for rep in selected),
                                    "representation_seconds": sum(rep["cost"]["seconds"] for rep in selected) + combine_seconds})
    arms = []
    for spec in heuristic_specs:
        clock = perf_counter()
        tables = [[max(int(u != t), circuit.ceiling(spec["values"][differences[t][u]]))
                   for u in range(n)] for t in range(n)]
        table_seconds = perf_counter() - clock
        free = spec["name"] == "free_h1"
        assert all(F(0) <= spec["values"][v] <= electrical[v] <= len(truth[v]) for v in range(n))
        violations = sum(tables[t][u] > 1 + tables[t][v] for t in range(n)
                         for u, row in enumerate(transitions) for v in row)
        for t in range(n):
            distances = circuit.distances(transitions, t)
            assert all(tables[t][u] <= distances[u] for u in range(n))
        for pruning in (False, True):
            selected_rules = rule_data["rules"] if pruning else []
            # Conservative charge: current factory builds every irrep even for a subset.
            library_charge = library_seconds if spec["members"] else 0
            pre_seconds = model_seconds + library_charge + spec["representation_seconds"]
            if not free:
                pre_seconds += difference_seconds + table_seconds
            if pruning:
                pre_seconds += rule_data["build_seconds"] + rule_data["validation_seconds"]
            arms.append({"heuristic": spec["name"], "members": spec["members"],
                         "pruning": pruning, "dimension_squared": spec["dimension_squared"],
                         "raw_values": spec["values"], "tables": tables,
                         "consistency_violations": violations,
                         "preprocessing_seconds": pre_seconds,
                         "combination_seconds": spec.get("combination_seconds", 0),
                         "heuristic_table_seconds": 0 if free else table_seconds,
                         "states_above_h1": sum(max(int(v != identity), circuit.ceiling(spec["values"][v])) > 1 for v in range(n)),
                         "raw_zero_nonidentity": sum(spec["values"][v] == 0 for v in range(n) if v != identity),
                         "cases": [], "sweep_seconds": [], "sweep_wall_seconds": [], "rules": selected_rules})
    # Rotate method order between repetitions; use medians rather than a single timing.
    for repeat in range(repeats):
        shift = repeat % len(arms)
        for arm in arms[shift:] + arms[:shift]:
            sweep_start = perf_counter()
            query_seconds = 0
            for target in range(n):
                h = arm["tables"][target]
                heuristic = (lambda u: int(u != target)) if arm["heuristic"] == "free_h1" else (lambda u: h[u])
                answer = ida(transitions, identity, target, inverses, heuristic, arm["rules"])
                query_seconds += answer["seconds"]
                assert answer["distance"] == len(truth[target])
                assert source.endpoint(answer["word"], transitions, identity) == target
                if repeat == 0:
                    arm["cases"].append({"target": target, **answer, "timings": [answer["seconds"]]})
                else:
                    saved = arm["cases"][target]
                    for metric in ("word", "distance", "generated", "expanded", "pruned", "rules_checks"):
                        assert saved[metric] == answer[metric]
                    saved["timings"].append(answer["seconds"])
            arm["sweep_wall_seconds"].append(perf_counter() - sweep_start)
            arm["sweep_seconds"].append(query_seconds)
    for arm in arms:
        for case in arm["cases"]:
            case["seconds"] = median(case["timings"])
        arm["search_seconds"] = median(arm["sweep_seconds"])
        arm["end_to_end_seconds"] = arm["preprocessing_seconds"] + arm["search_seconds"]
        arm["totals"] = {metric: sum(c[metric] for c in arm["cases"])
                         for metric in ("generated", "expanded", "pruned", "rules_checks")}
        arm["train_generated"] = sum(c["generated"] for c in arm["cases"] if c["target"] % 2 == 0)
        arm["heldout_generated"] = sum(c["generated"] for c in arm["cases"] if c["target"] % 2 == 1)
        arm["table_entries"] = 0 if arm["heuristic"] == "free_h1" else n*n
        del arm["tables"], arm["rules"]
    # Fixed prefixes are an untuned control; train-selected subsets are reported separately.
    fixed_prefixes = []
    ordered = sorted(contributions, key=lambda r: (r["dimension"]**2, r["name"]))
    for size in range(1, len(ordered) + 1):
        members = {r["name"] for r in ordered[:size]}
        for pruning in (False, True):
            arm = next(a for a in arms if a["pruning"] == pruning and set(a["members"]) == members)
            fixed_prefixes.append({"pruning": pruning, "budget": arm["dimension_squared"],
                                   "heuristic": arm["heuristic"], "generated": arm["totals"]["generated"]})
    selections = []
    for pruning in (False, True):
        candidates = [arm for arm in arms if arm["members"] and arm["pruning"] == pruning]
        for budget in sorted({a["dimension_squared"] for a in candidates}):
            eligible = [a for a in candidates if a["dimension_squared"] <= budget]
            winner = min(eligible, key=lambda a: (a["train_generated"], a["dimension_squared"], a["heuristic"]))
            selections.append({"pruning": pruning, "budget": budget, "winner": winner["heuristic"],
                               "train_generated": winner["train_generated"],
                               "heldout_generated": winner["heldout_generated"]})
    return {"group": key, "vertices": n, "elements": elements,
            "transitions": transitions, "inverses": inverses, "identity": identity,
            "truth_paths": {str(k): v for k, v in truth.items()}, "diameter": max(map(len, truth.values())),
            "representations": contributions, "representation_audit": representation_audit,
            "rule_data": rule_data, "arms": arms, "train_selected": selections,
            "fixed_prefixes": fixed_prefixes,
            "timing": {"model": model_seconds, "library_all_reps": library_seconds,
                       "representation_audit": rep_audit_seconds, "bfs": bfs_seconds,
                       "full_electrical": electrical_seconds, "difference_table": difference_seconds},
            "library": library}


def summary(result):
    lines = ["# 部分不可約表示：精確搜尋實驗", "", result["scope"], "",
             "所有表示方法取 max(免費h=1,ceil部分電阻)，各組使用相同IDA*與逆操作消去。", "",
             "|群|方法|關係剪枝|d²預算|生成節點|展開節點|預處理ms|搜尋ms中位數|合計ms|",
             "|---|---|---|---:|---:|---:|---:|---:|---:|"]
    for group in result["groups"]:
        # Full tables and individual targets are in JSON; summary includes every subset.
        for arm in group["arms"]:
            lines.append(f'|{group["group"]}|{arm["heuristic"]}|{arm["pruning"]}|{arm["dimension_squared"]}|'
                         f'{arm["totals"]["generated"]}|{arm["totals"]["expanded"]}|'
                         f'{1000*arm["preprocessing_seconds"]:.3f}|{1000*arm["search_seconds"]:.3f}|'
                         f'{1000*arm["end_to_end_seconds"]:.3f}|')
    lines += ["", "預處理為一次測量，搜尋為重複sweep中位數。表示庫建構成本完整計入各subset；",
              "只計所選表示的逆矩陣/貢獻表成本，屬於已建表示庫後重用的部署估計。",
              "表示factory內建審核已計入表示庫成本；第二次審核、全子集試驗、選擇與真值是實驗成本。",
              "首個catalogue面系統固定選取，不依距離挑選。d²只是成本proxy；非記憶體實測。",
              "train為偶數索引，heldout為奇數索引；只是同群內留出，非跨群泛化。", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--groups", nargs="+", default=["d4", "s3", "s4"])
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be positive")
    catalogue_path = source.ROOT / "data/surfaces/catalogue.json"
    catalogue = json.loads(catalogue_path.read_text(encoding="utf-8"))
    clock = perf_counter()
    result = {"schema_version": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
              "parameters": vars(args),
              "scope": "D4/S3/S4 exact rational irreps, exhaustive nontrivial subsets, "
                       "all identity targets. No cube performance or novelty claim.",
              "groups": [run_group(catalogue, key, args.repeats) for key in args.groups]}
    result["experiment_seconds"] = perf_counter() - clock
    paths = [Path(__file__), Path(small_irreps.__file__), Path(circuit.__file__), Path(source.__file__), catalogue_path]
    result["sha256"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    folder = source.ROOT / "experiments/results/partial-irreps" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    folder.mkdir(parents=True)
    (folder / "results.json").write_text(json.dumps(result, default=str, ensure_ascii=False, indent=2), encoding="utf-8")
    (folder / "summary.md").write_text(summary(result), encoding="utf-8")
    print(folder)
    for group in result["groups"]:
        print(group["group"], "arms", len(group["arms"]), "diameter", group["diameter"])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
