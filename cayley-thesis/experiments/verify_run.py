"""Check saved certificates without importing the search or its BFS implementation."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
import surface_systems as surfaces


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify_case(case, catalogue):
    group_spec = catalogue["groups"][case["group"]]
    group = surfaces.group_from_spec(group_spec["spec"])
    generators = [surfaces.freeze(g) for g in group_spec["generators"]]
    elements = group["elements"]
    index = {g: i for i, g in enumerate(elements)}
    transitions = [[index[group["mul"][g, s]] for s in generators] for g in elements]
    identity = index[group["identity"]]
    require(transitions == case["transitions"] and identity == case["identity"], "Model mismatch")
    faces = [[elements[i] for i in face] for face in case["faces"]]
    validation = surfaces.validate_surface(group, generators, faces)
    require(validation["valid"] and validation["genus"] == case["genus"], "Invalid saved surface")
    surface_spec = next(s for s in catalogue["surfaces"] if s["id"] == case["surface"])
    require(surface_spec["group"] == case["group"] and surface_spec["genus"] == case["genus"], "Surface metadata mismatch")

    def walk(word, start=identity):
        for move in word:
            require(isinstance(move, int) and 0 <= move < len(generators), "Invalid move")
            start = transitions[start][move]
        return start

    paths = {int(k): v for k, v in case["truth_paths"].items()}
    require(set(paths) == set(range(len(elements))), "Incomplete distance certificate")
    distances = {k: len(v) for k, v in paths.items()}
    require(distances[identity] == 0, "Identity distance")
    for state, path in paths.items():
        require(walk(path) == state, "Invalid truth path")
        for following in transitions[state]:
            require(distances[following] <= distances[state] + 1, "Distance edge inequality")
    # Witness paths give d <= label; edge inequalities and label(e)=0 give label <= d.
    require(case["diameter"] == max(distances.values()), "Diameter mismatch")
    methods = case["methods"]
    inverses = [generators.index(group["inv"][s]) for s in generators]
    def canonical(word):
        reverse = [inverses[s] for s in reversed(word)]
        return min(tuple(w[i:] + w[:i]) for w in (word, reverse) for i in range(len(w)))
    face_words = {canonical([generators.index(s) for _, s in
                             surfaces.darts_of_face(group, generators, face)]) for face in faces}
    require(all(tuple(word) in face_words for word in methods["faces"]["relators"]), "Face relation provenance")
    require(Counter(map(len, methods["ordinary"]["relators"])) ==
            Counter(map(len, methods["faces"]["relators"])), "Unmatched relation budgets")
    for name, method in methods.items():
        for word in method["relators"]:
            require(walk(word) == identity, f"Non-closed relator: {name}")
        for left, right in method["rules"]:
            require((len(left), left) > (len(right), right), "Nondecreasing rule")
            for state in range(len(elements)):
                require(walk(left, state) == walk(right, state), "Unsound rule")
        require(set(map(int, method["targets"])) == set(paths), "Missing targets")
        for target, result in method["targets"].items():
            target = int(target)
            require(walk(result["word"]) == target, "Wrong search endpoint")
            require(result["distance"] == len(result["word"]) == distances[target], "Nonoptimal search result")
        require(method["total_generated"] == sum(r["counts"]["generated"] for r in method["targets"].values()), "Count sum mismatch")
        example = method["counterexample"]
        if example["status"] == "found":
            word = example["word"]
            state = walk(word)
            require(state == example["endpoint"], "Counterexample endpoint")
            require(walk(example["bfs_word"]) == state and len(example["bfs_word"]) == distances[state], "Counterexample shortest path")
            require(len(word) > distances[state], "Counterexample is geodesic")
            for left, _ in method["rules"]:
                require(all(word[i:i + len(left)] != left for i in range(len(word) - len(left) + 1)), "Counterexample is reducible")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path, help="Run directory or results.json")
    args = parser.parse_args()
    path = args.run / "results.json" if args.run.is_dir() else args.run
    report = json.loads(path.read_text(encoding="utf-8"))
    catalogue = json.loads((ROOT / "data/surfaces/catalogue.json").read_text(encoding="utf-8"))
    count = 0
    for case in report["cases"]:
        if "methods" in case:
            verify_case(case, catalogue)
            count += 1
    require(count > 0, "No completed cases")
    certificate = {"status": "PASS", "cases": count,
                   "checked_utc": datetime.now(timezone.utc).isoformat(),
                   "results_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                   "verifier_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   "checks": ["model", "surface", "face_relation_provenance", "distance_certificates",
                              "rule_soundness", "all_target_solutions", "saved_counterexamples"],
                   "not_certified": ["timings", "search_counter_instrumentation", "absence_of_counterexamples",
                                     "asymptotic_complexity", "minimum_genus"]}
    (path.parent / "verification.json").write_text(json.dumps(certificate, indent=2), encoding="utf-8")
    print(f"PASS: {count} cases; distance certificates, rules, all target solutions and saved counterexamples")


if __name__ == "__main__":
    main()
