"""Independent certificate checks; does not import the DFA compiler/classifier."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from itertools import product
import json
from pathlib import Path

from verify_run import verify_case as verify_source

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def contains(word, pattern):
    return any(word[i:i + len(pattern)] == pattern for i in range(len(word) - len(pattern) + 1))


def walk(dfa, word, start=None):
    state = dfa["start"] if start is None else start
    path = [state]
    for symbol in word:
        require(type(symbol) is int and 0 <= symbol < dfa["alphabet_size"], "Invalid input symbol")
        state = dfa["transitions"][state][symbol]
        path.append(state)
    return path


def verify_method(item, source, max_check_length):
    require(item["labels"] == source["labels"], "Alphabet order changed")
    require(item["bfs_diameter"] == source["diameter"], "BFS diameter changed")
    method = source["methods"][item["method"]]
    require(item["rules"] == method["rules"] and item["relators"] == method["relators"], "Rule provenance mismatch")
    forbidden = sorted({tuple(a) for a, b in method["rules"]}, key=lambda w: (len(w), w))
    dfa = item["dfa"]
    memory = [tuple(w) if w is not None else None for w in dfa["memory"]]
    require([tuple(w) for w in dfa["forbidden"]] == forbidden, "Wrong forbidden patterns")
    dead, alphabet = dfa["dead"], len(source["labels"])
    require(dfa["alphabet_size"] == alphabet and dfa["start"] == 0, "Wrong DFA header")
    require(dead == len(memory) - 1 and memory[dead] is None and memory[0] == (), "Wrong sink or start memory")
    require(all(w is not None for w in memory[:dead]) and len(set(memory[:dead])) == dead, "Duplicate/invalid live memory")
    require(dfa["accepting"] == list(range(dead)), "Wrong accepting states")
    rows = dfa["transitions"]
    require(len(rows) == len(memory) and all(len(r) == alphabet for r in rows), "Bad transition dimensions")
    require(all(type(q) is int and 0 <= q <= dead for r in rows for q in r), "Invalid transition target")
    require(rows[dead] == [dead] * alphabet, "Rejecting sink must be absorbing")
    prefixes = {()} | {p[:i] for p in forbidden for i in range(1, len(p))}
    lookup = {w: q for q, w in enumerate(memory[:dead])}
    for state, word in enumerate(memory[:dead]):
        require(word in prefixes and not any(contains(word, p) for p in forbidden), "Bad suffix memory")
        for symbol in range(alphabet):
            candidate = word + (symbol,)
            completes_pattern = any(len(candidate) >= len(p) and candidate[-len(p):] == p for p in forbidden)
            if completes_pattern:
                expected = dead
            else:
                suffix = max((p for p in prefixes if not p or candidate[-len(p):] == p), key=len)
                require(suffix in lookup, "Missing suffix state")
                expected = lookup[suffix]
            require(rows[state][symbol] == expected, "Transition violates suffix invariant")
    reachable, pending = {0}, [0]
    while pending:
        for target in rows[pending.pop()]:
            if target != dead and target not in reachable:
                reachable.add(target)
                pending.append(target)
    require(reachable == set(range(dead)), "Live states must all be reachable")
    # Independent literal-substring reference, not the compiler's prefix/suffix helper.
    checked = 0
    for length in range(max_check_length + 1):
        for word in product(range(alphabet), repeat=length):
            accepted = walk(dfa, word)[-1] != dead
            require(accepted == (not any(contains(word, p) for p in forbidden)), "Literal scanner mismatch")
            checked += 1
    regression = item["pruner_regression"]
    require(regression["max_length"] == max_check_length and regression["words_checked"] == checked and regression["all_match_original_pruner"], "Regression record mismatch")
    truth = {int(k): word for k, word in source["truth_paths"].items()}
    def endpoint(word):
        state = source["identity"]
        for symbol in word:
            state = source["transitions"][state][symbol]
        return state
    cert = item["language"]["certificate"]
    if item["language"]["finite"]:
        order = cert["topological_order"]
        require(len(order) == dead and set(order) == reachable, "Incomplete topological certificate")
        ranks = {q: i for i, q in enumerate(order)}
        max_lengths = {int(k): v for k, v in cert["suffix_max_lengths"].items()}
        counts = {int(k): v for k, v in cert["suffix_word_counts"].items()}
        require(set(max_lengths) == reachable and set(counts) == reachable, "Incomplete DP certificate")
        for state in order:
            successors = [target for target in rows[state] if target != dead]
            require(all(ranks[state] < ranks[target] for target in successors), "Certificate contains a live cycle")
            require(max_lengths[state] == max([0] + [1 + max_lengths[t] for t in successors]), "Wrong longest-path recurrence")
            require(counts[state] == 1 + sum(counts[t] for t in successors), "Wrong language-count recurrence")
        require(cert["max_length"] == max_lengths[0] == len(cert["longest_word"]), "Wrong maximum length")
        path = walk(dfa, cert["longest_word"])
        require(path == cert["longest_state_path"] and dead not in path, "Invalid longest-word witness")
        require(cert["accepted_word_count"] == counts[0] <= 10000, "Wrong or oversized finite count")
        words, pending = [], [(0, ())]
        while pending:
            state, word = pending.pop()
            words.append(word)
            pending.extend((target, word + (symbol,)) for symbol, target in enumerate(rows[state]) if target != dead)
        saved = item["accepted_words"]
        require(len(saved) == len(words) == counts[0] and {tuple(r["word"]) for r in saved} == set(words), "Missing finite accepted words")
        for row in saved:
            e = endpoint(row["word"])
            require(row["endpoint"] == e and row["bfs_distance"] == len(truth[e]), "Wrong endpoint/BFS record")
            require(row["geodesic"] == (len(row["word"]) == len(truth[e])), "Wrong shortest flag")
        endpoints = [endpoint(w) for w in words]
        comparison = {"covers_all_group_elements": set(endpoints) == set(truth),
            "one_word_per_group_element": len(set(endpoints)) == len(endpoints) == len(truth),
            "all_words_geodesic": all(len(w) == len(truth[endpoint(w)]) for w in words),
            "same_words_as_bfs_shortlex_paths": set(words) == {tuple(w) for w in truth.values()},
            "diameter_upper_bound": cert["max_length"], "upper_bound_equals_bfs": cert["max_length"] == source["diameter"]}
        require(comparison == item["finite_comparison"], "Wrong finite comparison")
        require(comparison["covers_all_group_elements"] and cert["max_length"] >= source["diameter"], "Upper bound fails")
    else:
        require(bool(cert["cycle"]), "Empty word is not a pumping loop")
        access = walk(dfa, cert["prefix"])
        cycle = walk(dfa, cert["cycle"], cert["cycle_state"])
        require(access == cert["access_state_path"] and access[-1] == cert["cycle_state"], "Invalid access witness")
        require(cycle == cert["cycle_state_path"] and cycle[0] == cycle[-1], "Invalid cycle witness")
        require(dead not in access + cycle, "Rejecting sink is not an accepting-cycle proof")
        inf = item["infinite_comparison"]
        order = inf["cycle_word_group_order"]
        require(type(order) is int and 1 <= order <= len(truth), "Bad group order")
        require(endpoint(cert["cycle"] * order) == source["identity"] and
                all(endpoint(cert["cycle"] * k) != source["identity"] for k in range(1, order)), "Wrong group order")
        require(inf["identity_block"] == cert["cycle"] * order, "Wrong identity block")
        require(inf["identity_block_state_path"] == walk(dfa, inf["identity_block"], cert["cycle_state"]), "Identity-block path mismatch")
        require([e["k"] for e in inf["pumped_examples"]] == [0, 1, 2, 4, 8], "Missing pumped examples")
        for example in inf["pumped_examples"]:
            word = cert["prefix"] + cert["cycle"] * example["k"]
            require(word == example["word"] and walk(dfa, word) == example["state_path"] and dead not in example["state_path"], "Bad pumped word")
            require(example["endpoint"] == endpoint(word) and example["bfs_distance"] == len(truth[endpoint(word)]), "Bad pumped endpoint")
        require([e["k"] for e in inf["same_endpoint_examples"]] == [0, 1, 2], "Missing same-endpoint examples")
        for example in inf["same_endpoint_examples"]:
            word = cert["prefix"] + cert["cycle"] * (order * example["k"])
            require(example["word"] == word and example["endpoint"] == endpoint(word) == endpoint(cert["prefix"]), "Group repetition mismatch")
        require(inf["diameter_upper_bound"] is None, "Infinite irreducible language gives no finite max-word bound")
    return {"budget": item["budget"], "method": item["method"], "status": "PASS", "words_checked": checked}


def verify_run(directory):
    directory = Path(directory)
    report_path = directory / "results.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    require(type(report["max_check_length"]) is int and 0 <= report["max_check_length"] <= 9, "Invalid check bound")
    catalogue = json.loads((ROOT / "data/surfaces/catalogue.json").read_text(encoding="utf-8"))
    require({(r["budget"], r["method"]) for r in report["cases"]} ==
            {(b, m) for b in ("single_relation", "full_budget") for m in ("cancellation_only", "ordinary", "faces")} and len(report["cases"]) == 6, "Missing or duplicate cases")
    sources, checks = {}, []
    for item in report["cases"]:
        name = item["source_case"]
        path = (ROOT / name).resolve()
        require(path.is_relative_to(ROOT.resolve()), "Source outside project")
        require(hashlib.sha256(path.read_bytes()).hexdigest() == report["source_sha256"][name], "Source hash changed")
        if name not in sources:
            sources[name] = json.loads(path.read_text(encoding="utf-8"))
            verify_source(sources[name], catalogue)
        require(sources[name]["group"] == "d4", "This verifier is scoped to D4")
        checkpoint = json.loads((directory / f"{item['budget']}-{item['method']}.json").read_text(encoding="utf-8"))
        require(checkpoint == item, "Checkpoint differs from aggregate")
        checks.append(verify_method(item, sources[name], report["max_check_length"]))
    certificate = {"status": "PASS", "checked_utc": datetime.now(timezone.utc).isoformat(), "cases": checks,
        "results_sha256": hashlib.sha256(report_path.read_bytes()).hexdigest(),
        "verifier_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "checks": ["source rule soundness and strict shortlex", "global suffix-transition invariant", "live reachability",
                   "literal-substring regression", "accepting cycle or topological/DP certificate", "group replay and BFS comparison"],
        "limitations": ["not Lean", "not DFA minimization", "no general confluence/complexity claim", "shared source/group validator"]}
    (directory / "verification.json").write_text(json.dumps(certificate, ensure_ascii=False, indent=2), encoding="utf-8")
    return certificate


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    result = verify_run(parser.parse_args().run)
    print(f"{result['status']}: 6 DFA language certificates and BFS comparisons checked")
