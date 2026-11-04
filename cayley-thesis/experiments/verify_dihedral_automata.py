"""Check D8/D16 source completeness and every budget/language certificate.

Does not import the experiment runner or DFA compiler/classifier. Reuses the
separate suffix/cycle/topological certificate checker and the existing surface
validator. Timings are observations, not independently proven speed claims.
"""
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
from time import perf_counter

import relation_search as relations
from verify_relation_automata import verify_method


def require(condition, message):
    if not condition:
        raise ValueError(message)


def endpoint(word, transitions, start=0):
    for symbol in word:
        start = transitions[start][symbol]
    return start


def canonical(word, inverses):
    word = tuple(word)
    reverse = tuple(inverses[s] for s in reversed(word))
    return min(w[i:] + w[:i] for w in (word, reverse) for i in range(len(w)))


def independent_pool(transitions, inverses, n):
    result = set()
    stack = [(0, ())]
    while stack:
        state, word = stack.pop()
        if len(word) >= 3 and state == 0 and word[0] != inverses[word[-1]]:
            result.add(canonical(word, inverses))
        if len(word) < n:
            stack.extend((target, word + (s,)) for s, target in enumerate(transitions[state])
                         if not word or s != inverses[word[-1]])
    return sorted(result, key=lambda w: (len(w), w))


def verify_source(source):
    n = source["n"]
    require(n in (8, 16) and source["group_order"] == 2 * n, "Wrong group convention")
    require(source["labels"] == ["r", "r^-1", "s"] and source["identity"] == 0, "Wrong generator order")
    elements = [[a, b] for a in range(n) for b in (0, 1)]
    transitions = [[2 * ((a + (1 if b == 0 else -1)) % n) + b,
                    2 * ((a - (1 if b == 0 else -1)) % n) + b, 2 * a + (1-b)] for a, b in elements]
    require(elements == source["elements"] and transitions == source["transitions"], "Dihedral model mismatch")
    paths = {int(k): word for k, word in source["truth_paths"].items()}
    require(set(paths) == set(range(2 * n)) and paths[0] == [], "Incomplete BFS certificate")
    distances = {k: len(word) for k, word in paths.items()}
    for state, word in paths.items():
        require(endpoint(word, transitions) == state, "Bad BFS path")
        require(all(distances[t] <= distances[state]+1 for t in transitions[state]), "Distance edge inequality failed")
    require(source["diameter"] == max(distances.values()) == n//2 + 1, "Wrong diameter")
    group = relations.surfaces.make_dihedral(n)
    generators = [(1,0), (n-1,0), (0,1)]
    faces = [[group["elements"][i] for i in face] for face in source["faces"]]
    validation = relations.surfaces.validate_surface(group, generators, faces)
    require(validation["valid"] and validation["genus"] == 0 and validation["face_count"] == n+2, "Bad prism surface")
    require(json.loads(json.dumps(validation)) == source["surface_validation"], "Surface certificate mismatch")
    require(source["inverses"] == [1,0,2], "Bad inverse map")
    pool = independent_pool(transitions, source["inverses"], n)
    require(pool == [tuple(w) for w in source["relator_pool"]], "Relator pool is not complete in the claimed scope")
    face_words = sorted({canonical([generators.index(s) for _, s in relations.surfaces.darts_of_face(group, generators, face)], source["inverses"])
                         for face in faces}, key=lambda w: (len(w), w))
    require(source["face_relator_ids"] == [pool.index(w) for w in face_words], "Face provenance mismatch")
    require(source["short_relator_ids"] == [i for i, w in enumerate(pool) if len(w) <= source["short_cutoff"]], "Short pool mismatch")
    library = [(tuple(a), tuple(b)) for a, b in source["rule_library"]]
    require(library == sorted(set(library), key=lambda r: (len(r[0]), r)), "Rule library duplicates/order")
    relations.verify_rules(library, transitions)
    require(len(source["relator_rule_ids"]) == len(pool), "Missing rule expansion references")
    referenced = set(source["baseline_rule_ids"])
    require([library[i] for i in source["baseline_rule_ids"]] == relations.rules_for([], source["inverses"]), "Bad common cancellation")
    for word, ids in zip(pool, source["relator_rule_ids"]):
        require([library[i] for i in ids] == relations.rules_for([word], source["inverses"]), "Wrong relator-to-rule expansion")
        referenced.update(ids)
    require(referenced == set(range(len(library))), "Unreferenced rules in library")


def verify_group(group, source, directory, bound):
    steps = group["steps"]
    require(len({s["id"] for s in steps}) == len(steps), "Duplicate checkpoint IDs")
    by_id = {s["id"]: s for s in steps}
    for step in steps:
        require(json.loads((directory / f"{step['id']}.json").read_text(encoding="utf-8")) == step, "Checkpoint/aggregate mismatch")
        selected = step["selected_relator_ids"]
        require(len(selected) == len(set(selected)) and all(type(i) is int and 0 <= i < len(source["relator_pool"]) for i in selected), "Invalid selection")
        expected_ids = sorted(set(source["baseline_rule_ids"]).union(*(set(source["relator_rule_ids"][i]) for i in selected)))
        require(expected_ids == step["rule_ids"], "Wrong expanded rule set")
        rules = [source["rule_library"][i] for i in expected_ids]
        relators = [source["relator_pool"][i] for i in selected]
        transient = {**step, "rules": rules, "relators": relators}
        view = {**{k: source[k] for k in ("labels", "transitions", "identity", "truth_paths", "diameter")},
                "methods": {step["method"]: {"rules": rules, "relators": relators}}}
        verify_method(transient, view, bound)
        require(step["budget"] == len(selected) and step["relator_symbols"] == sum(map(len, relators)), "Wrong raw budget")
        U = step["language"]["certificate"].get("max_length")
        require(step["upper_bound"] == U and step["gap"] == (U-source["diameter"] if U is not None else None), "Upper bound/gap mismatch")
        cost = step["costs"]
        require(cost["expanded_rules"] == len(rules) and cost["expanded_rule_symbols"] == sum(len(a)+len(b) for a,b in rules), "Wrong rule costs")
        require(cost["live_dfa_states"] == len(step["dfa"]["accepting"]) and cost["dfa_states_with_sink"] == len(step["dfa"]["memory"]), "Wrong DFA costs")
        encoded = json.dumps(step["dfa"], ensure_ascii=False, separators=(",", ":")).encode()
        require(cost["dfa_serialized_utf8_bytes"] == len(encoded), "Wrong serialized size")
        require(all(cost[k] >= 0 for k in ("selection_seconds", "analysis_seconds", "measured_stage_seconds")), "Negative recorded times")
    for strategy, sequence in group["sequences"].items():
        expected_sequence = source["face_relator_ids"] if strategy == "face_prefix" else list(range(len(source["relator_pool"])))
        require(sequence["ordered_relator_ids"] == expected_sequence, "Wrong sequence order")
        ids = sequence["tested_stage_ids"]
        require([by_id[i]["selected_relator_ids"] for i in ids] == [expected_sequence[:k] for k in range(len(ids))], "Missing budget prefix")
        finite = [k for k, i in enumerate(ids) if by_id[i]["language"]["finite"]]
        require(finite == [len(ids)-1] and sequence["first_finite_budget_in_this_order"] == finite[0], "First finite budget not proven")
    require(by_id[group["short_only_stage_id"]]["selected_relator_ids"] == source["short_relator_ids"], "Wrong short-only control")
    singles = [by_id[i] for i in group["singleton_stage_ids"]]
    require([s["selected_relator_ids"] for s in singles] == [[i] for i in range(len(source["relator_pool"]))], "Singleton audit incomplete")
    require(all(not s["language"]["finite"] for s in singles), "Finite singleton contradicts minimum=2")
    short_id = next(i for i,w in enumerate(source["relator_pool"]) if len(w)==4)
    long_ids = [i for i,w in enumerate(source["relator_pool"]) if len(w)==source["n"]]
    pairs = [by_id[i] for i in group["matched_pair_stage_ids"]]
    require([s["selected_relator_ids"] for s in pairs] == [[short_id,i] for i in long_ids], "Equal-length pair audit incomplete")
    witnesses = [s["id"] for s in pairs if s["language"]["finite"]]
    require(witnesses and group["matched_pair_counts"] == {"tested": len(pairs), "finite": len(witnesses)}, "Bad matched-pair counts")
    minimum = group["pool_minimum_certificate"]
    require(minimum["minimum_relators_with_common_cancellation"] == 2 and minimum["no_finite_singleton_stage_ids"] == group["singleton_stage_ids"] and minimum["finite_pair_witness_stage_ids"] == witnesses, "Minimum certificate mismatch")
    return {"n": source["n"], "status": "PASS", "checkpoints": len(steps), "singleton_audit": len(singles), "matched_pair_audit": len(pairs)}


def verify_run(run_dir):
    started = perf_counter()
    run_dir = Path(run_dir)
    path = run_dir / "results.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    bound = report["parameters"]["max_check_length"]
    require(type(bound) is int and 0 <= bound <= 5, "Bad regression bound")
    require([g["n"] for g in report["groups"]] == report["parameters"]["groups"], "Group list mismatch")
    checks = []
    for group in report["groups"]:
        n = str(group["n"])
        source_path = (run_dir / report["sources"][n]).resolve()
        require(source_path.is_relative_to(run_dir.resolve()), "Source outside run directory")
        require(hashlib.sha256(source_path.read_bytes()).hexdigest() == report["source_sha256"][n], "Source hash mismatch")
        source = json.loads(source_path.read_text(encoding="utf-8"))
        verify_source(source)
        checks.append(verify_group(group, source, source_path.parent, bound))
    verification = {"status": "PASS", "checked_utc": datetime.now(timezone.utc).isoformat(),
                    "groups": checks, "seconds": perf_counter()-started,
                    "results_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "verifier_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    "scope": "Independent dihedral transitions, BFS certificates, complete pool, validated faces, rule provenance, every DFA/cycle/finite/DP proof, gap, singleton minimum and matched-length census. Timing instrumentation not independently proven; not Lean."}
    (run_dir / "verification.json").write_text(json.dumps(verification, ensure_ascii=False, indent=2), encoding="utf-8")
    return verification


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    result = verify_run(parser.parse_args().run)
    print(f"{result['status']}: all dihedral budget certificates checked in {result['seconds']:.3f}s")
