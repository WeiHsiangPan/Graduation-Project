"""Small, exact relation-pruning experiment. Standard library only."""
from __future__ import annotations

import argparse
from collections import Counter, deque
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import sys
import traceback
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
import surface_systems as surfaces


def construct(group, generators, spec):
    kind = spec["type"]
    if kind == "relator_orbits":
        return surfaces.relator_surface(group, generators, spec["words"])
    if kind == "uniform_rotation":
        return surfaces.uniform_rotation_surface(group, generators, spec["order"])
    if kind == "local_binary_rotation":
        return surfaces.local_binary_rotation_surface(group, generators, spec["bits"])
    if kind == "explicit_rotation":
        return surfaces.explicit_rotation_surface(group, generators, spec["orders"])
    raise ValueError(kind)


def model(spec):
    group = surfaces.group_from_spec(spec["spec"])
    generators = tuple(surfaces.freeze(s) for s in spec["generators"])
    elements = group["elements"]
    index = {g: i for i, g in enumerate(elements)}
    transitions = [[index[group["mul"][g, s]] for s in generators] for g in elements]
    inverses = tuple(generators.index(group["inv"][s]) for s in generators)
    return group, generators, transitions, inverses, index[group["identity"]]


def endpoint(word, transitions, identity):
    state = identity
    for move in word:
        state = transitions[state][move]
    return state


def bfs(transitions, identity):
    paths = {identity: ()}
    queue = deque([identity])
    while queue:
        state = queue.popleft()
        for move, following in enumerate(transitions[state]):
            if following not in paths:
                paths[following] = paths[state] + (move,)
                queue.append(following)
    if len(paths) != len(transitions):
        raise ValueError("Disconnected state graph")
    return paths


def variants(word, inverses):
    word = tuple(word)
    reverse = tuple(inverses[s] for s in reversed(word))
    return {w[i:] + w[:i] for w in (word, reverse) for i in range(len(w))}


def canonical(word, inverses):
    return min(variants(word, inverses))


def closed_words(transitions, identity, inverses, max_length):
    """Enumerate cyclically freely reduced closed words, quotient rotations/inversion."""
    pool = set()
    def visit(state, word):
        if len(word) >= 3 and state == identity and word[0] != inverses[word[-1]]:
            pool.add(canonical(word, inverses))
        if len(word) == max_length:
            return
        for move, following in enumerate(transitions[state]):
            if not word or move != inverses[word[-1]]:
                visit(following, word + (move,))
    visit(identity, ())
    return sorted(pool, key=lambda w: (len(w), w))


def rules_for(relators, inverses):
    # Both groups receive inverse cancellation. Orient every equality by shortlex.
    rules = {((s, inverses[s]), ()) for s in range(len(inverses))}
    for relator in relators:
        for word in variants(relator, inverses):
            for split in range(len(word) + 1):
                left = word[:split]
                right = tuple(inverses[s] for s in reversed(word[split:]))
                if left != right:
                    high, low = sorted((left, right), key=lambda w: (len(w), w), reverse=True)
                    rules.add((high, low))
    return sorted(rules, key=lambda pair: (len(pair[0]), pair))


def verify_rules(rules, transitions):
    # Check at EVERY starting vertex, independently of how a rule was generated.
    for left, right in rules:
        if (len(left), left) <= (len(right), right):
            raise ValueError("Rule does not decrease shortlex")
        for start in range(len(transitions)):
            if endpoint(left, transitions, start) != endpoint(right, transitions, start):
                raise ValueError("Rule changes endpoint")


def forbidden_suffix(word, rules):
    return any(len(word) >= len(left) and word[-len(left):] == left for left, _ in rules)


def iddfs(target, transitions, identity, rules, max_depth):
    counts = Counter(entered=0, generated=0, pruned=0, expanded=0, rule_checks=0)
    def visit(state, word, limit):
        counts["entered"] += 1
        if state == target:
            return word
        if len(word) == limit:
            return None
        counts["expanded"] += 1
        for move, following in enumerate(transitions[state]):
            counts["generated"] += 1
            candidate = word + (move,)
            rejected = False
            for left, _ in rules:
                counts["rule_checks"] += 1
                if len(candidate) >= len(left) and candidate[-len(left):] == left:
                    rejected = True
                    break
            if rejected:
                counts["pruned"] += 1
                continue
            answer = visit(following, candidate, limit)
            if answer is not None:
                return answer
        return None
    started = perf_counter()
    for limit in range(max_depth + 1):
        answer = visit(identity, (), limit)
        if answer is not None:
            return {"word": answer, "distance": len(answer), "counts": dict(counts),
                    "seconds": perf_counter() - started}
    raise ValueError("Search lost a shortest representative")


def counterexample(transitions, identity, rules, truth, max_length):
    # Increasing lengths and lexicographic order: first witness is minimal in this scope.
    examined = 0
    def visit(state, word, length):
        nonlocal examined
        if len(word) == length:
            examined += 1
            if len(word) > len(truth[state]):
                return {"word": word, "endpoint": state, "bfs_word": truth[state],
                        "excess_length": len(word) - len(truth[state])}
            return None
        for move, following in enumerate(transitions[state]):
            candidate = word + (move,)
            if not forbidden_suffix(candidate, rules):
                found = visit(following, candidate, length)
                if found is not None:
                    return found
        return None
    for length in range(max_length + 1):
        found = visit(identity, (), length)
        if found is not None:
            return {"status": "found", "examined_irreducible_words": examined, **found}
    return {"status": "not_found_within_bound", "max_length": max_length,
            "examined_irreducible_words": examined}


def run(args, save_case=None):
    raw = (ROOT / "data/surfaces/catalogue.json").read_bytes()
    catalogue = json.loads(raw)
    report = {"schema_version": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
              "parameters": vars(args), "catalogue_sha256": hashlib.sha256(raw).hexdigest(),
              "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in (Path(__file__), Path(__file__).with_name("verify_run.py"), ROOT / "code/surface_systems.py")},
              "scope": "All identity-to-state targets; unit costs; no state duplicate table; IDDFS shortlex pruning. Not a global complexity claim.",
              "cases": []}
    for group_id in args.groups:
        spec = catalogue["groups"][group_id]
        group, generators, transitions, inverses, identity = model(spec)
        started = perf_counter()
        truth = bfs(transitions, identity)
        pool = closed_words(transitions, identity, inverses, args.max_relator_length)
        shared_seconds = perf_counter() - started
        for surface in catalogue["surfaces"]:
            if surface["group"] != group_id:
                continue
            started = perf_counter()
            faces = construct(group, generators, surface["construction"])
            validation = surfaces.validate_surface(group, generators, faces)
            if not validation["valid"] or validation["genus"] != surface["genus"]:
                raise ValueError(f"Invalid surface {surface['id']}: {validation}")
            face_pool = sorted({canonical(tuple(generators.index(s) for _, s in
                                  surfaces.darts_of_face(group, generators, face)), inverses)
                                for face in faces}, key=lambda w: (len(w), w))
            eligible = [w for w in face_pool if len(w) <= args.max_relator_length]
            selected = eligible[:args.relators]
            face_seconds = perf_counter() - started
            if not selected:
                report["cases"].append({"surface": surface["id"], "status": "skipped_no_eligible_face_relators"})
                continue
            histogram = Counter(map(len, selected))
            for round_index in range(args.rounds):
                seed = args.seed + round_index
                rng = random.Random(seed)
                ordinary = []
                for length, count in sorted(histogram.items()):
                    candidates = [w for w in pool if len(w) == length]
                    ordinary.extend(rng.sample(candidates, count))
                case = {"group": group_id, "surface": surface["id"], "genus": validation["genus"],
                        "faces": [[group["elements"].index(v) for v in face] for face in faces],
                        "seed": seed, "validation": validation, "transitions": transitions,
                        "identity": identity, "inverses": inverses, "labels": spec["generator_labels"],
                        "elements": group["elements"], "truth_paths": {str(k): v for k, v in truth.items()},
                        "diameter": max(map(len, truth.values())), "shared_preprocessing_seconds": shared_seconds,
                        "face_preprocessing_seconds": face_seconds, "generic_pool_size": len(pool),
                        "face_relators_excluded_by_length": len(face_pool) - len(eligible),
                        "face_relators_excluded_by_count": len(eligible) - len(selected),
                        "matched_length_histogram": dict(histogram),
                        "relator_overlap": len(set(ordinary) & set(selected)), "methods": {}}
                for name, relators in (("cancellation_only", []), ("ordinary", ordinary), ("faces", selected)):
                    started = perf_counter()
                    rules = rules_for(relators, inverses)
                    verify_rules(rules, transitions)
                    preprocessing_seconds = perf_counter() - started
                    results = {}
                    for target in range(len(transitions)):
                        result = iddfs(target, transitions, identity, rules, case["diameter"])
                        if result["distance"] != len(truth[target]) or endpoint(result["word"], transitions, identity) != target:
                            raise ValueError("BFS comparison failed")
                        results[str(target)] = result
                    case["methods"][name] = {"relators": relators, "rules": rules,
                        "rule_count": len(rules), "rule_symbols": sum(len(a) + len(b) for a, b in rules),
                        "rule_preprocessing_seconds": preprocessing_seconds, "targets": results,
                        "total_generated": sum(r["counts"]["generated"] for r in results.values()),
                        "total_rule_checks": sum(r["counts"]["rule_checks"] for r in results.values()),
                        "search_seconds": sum(r["seconds"] for r in results.values()),
                        "counterexample": counterexample(transitions, identity, rules, truth, args.counterexample_length)}
                report["cases"].append(case)
                if save_case:
                    save_case(case)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--groups", nargs="+", default=["d4", "q8", "s4"])
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-relator-length", type=int, default=6)
    parser.add_argument("--relators", type=int, default=8)
    parser.add_argument("--counterexample-length", type=int, default=6)
    parser.add_argument("--output", default=str(ROOT / "experiments/results"))
    args = parser.parse_args()
    if args.rounds < 1 or args.relators < 1 or not 3 <= args.max_relator_length <= 8 or not 0 <= args.counterexample_length <= 8:
        parser.error("Positive rounds/relators required; relation length 3..8, counterexample length 0..8")
    destination = Path(args.output) / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "parameters.json").write_text(json.dumps(vars(args), indent=2), encoding="utf-8")
    def save_case(case):
        filename = f"{case['surface']}-seed{case['seed']}.json"
        (destination / filename).write_text(json.dumps(case, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        report = run(args, save_case)
    except Exception:
        (destination / "failure.txt").write_text(traceback.format_exc(), encoding="utf-8")
        raise
    (destination / "results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# Relation search experiment", "", "All completed target distances agree with BFS. Timing is observational; no asymptotic claim.", "",
             "| Surface | Seed | Cancellation only | Ordinary generated | Faces generated | Difference (faces - ordinary) |", "|---|---:|---:|---:|---:|---:|"]
    skipped = []
    for case in report["cases"]:
        if "methods" not in case:
            skipped.append(f"Skipped {case['surface']}: no face relation within length bound.")
            continue
        ordinary = case["methods"]["ordinary"]["total_generated"]
        faces = case["methods"]["faces"]["total_generated"]
        baseline = case["methods"]["cancellation_only"]["total_generated"]
        lines.append(f"| {case['surface']} | {case['seed']} | {baseline} | {ordinary} | {faces} | {faces - ordinary:+} |")
    lines.extend(["", *skipped])
    lines.extend(["", "## First saved nongeodesic irreducible word per case/method", "",
                  "These disprove local irreducibility implies shortest; absence within a bound is not a theorem.", "",
                  "| Surface | Seed | Method | Irreducible word | BFS shortest word |", "|---|---:|---|---|---|"])
    for case in report["cases"]:
        for name, method in case.get("methods", {}).items():
            example = method["counterexample"]
            if example["status"] == "found":
                def label(word):
                    return " ".join(case["labels"][s] for s in word) or "identity"
                lines.append(f"| {case['surface']} | {case['seed']} | {name} | {label(example['word'])} | {label(example['bfs_word'])} |")
    (destination / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(destination)


if __name__ == "__main__":
    main()
