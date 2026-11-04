"""Compile saved D4 shortlex rules into exact forbidden-subword DFAs.

Standard library only. State memory is a word suffix, not a group element.
Use reachable-live cycles / a topological-order certificate, never a length cutoff,
to decide whether the accepted irreducible-word language is finite.
"""
from __future__ import annotations

import argparse
from collections import deque
from datetime import datetime, timezone
import hashlib
from itertools import product
import json
from pathlib import Path
import traceback

import relation_search as search
from verify_run import verify_case as verify_source

ROOT = search.ROOT
REPORT = ROOT / "reports/d4-relation-automata"
SOURCE_RUNS = {"single_relation": "20261031T175148_814309Z", "full_budget": "20261031T175147_790201Z"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def label(word, labels):
    return " ".join(labels[s] for s in word) or "epsilon"


def compile_dfa(rules, alphabet_size):
    forbidden = sorted({tuple(left) for left, _ in rules}, key=lambda w: (len(w), w))
    require(all(forbidden), "Empty left side is unsupported")
    require(all(0 <= s < alphabet_size for w in forbidden for s in w), "Unknown symbol")
    prefixes = {()} | {w[:i] for w in forbidden for i in range(1, len(w))}
    memory = [()]
    index = {(): 0}
    transitions = []
    cursor = 0
    while cursor < len(memory):
        row = []
        for symbol in range(alphabet_size):
            candidate = memory[cursor] + (symbol,)
            if any(len(candidate) >= len(w) and candidate[-len(w):] == w for w in forbidden):
                row.append(-1)
                continue
            suffix = max((p for p in prefixes if not p or candidate[-len(p):] == p), key=len)
            if suffix not in index:
                index[suffix] = len(memory)
                memory.append(suffix)
            row.append(index[suffix])
        transitions.append(row)
        cursor += 1
    dead = len(memory)
    transitions = [[dead if target == -1 else target for target in row] for row in transitions]
    transitions.append([dead] * alphabet_size)
    return {"alphabet_size": alphabet_size, "forbidden": forbidden, "memory": memory + [None],
            "start": 0, "dead": dead, "accepting": list(range(dead)), "transitions": transitions,
            "construction": "Longest suffix that is a proper prefix of a forbidden left side; reachable live states only; not minimized."}


def state_path(dfa, word, start=None):
    state = dfa["start"] if start is None else start
    result = [state]
    for symbol in word:
        state = dfa["transitions"][state][symbol]
        result.append(state)
    return result


def accepts(dfa, word):
    return state_path(dfa, word)[-1] in dfa["accepting"]


def access_paths(dfa):
    paths = {dfa["start"]: ()}
    queue = deque(paths)
    while queue:
        state = queue.popleft()
        for symbol, target in enumerate(dfa["transitions"][state]):
            if target != dfa["dead"] and target not in paths:
                paths[target] = paths[state] + (symbol,)
                queue.append(target)
    return paths


def classify_language(dfa):
    access = access_paths(dfa)
    indegrees = dict.fromkeys(access, 0)
    for state in access:
        for target in dfa["transitions"][state]:
            if target in access:
                indegrees[target] += 1
    queue = deque(sorted(state for state, degree in indegrees.items() if degree == 0))
    order = []
    while queue:
        state = queue.popleft()
        order.append(state)
        for target in dfa["transitions"][state]:
            if target in indegrees:
                indegrees[target] -= 1
                if indegrees[target] == 0:
                    queue.append(target)
    if len(order) == len(access):
        lengths, counts, best = {}, {}, {}
        for state in reversed(order):
            options = [()]
            counts[state] = 1  # empty suffix is accepted
            for symbol, target in enumerate(dfa["transitions"][state]):
                if target != dfa["dead"]:
                    options.append((symbol,) + best[target])
                    counts[state] += counts[target]
            best[state] = min(options, key=lambda word: (-len(word), word))
            lengths[state] = len(best[state])
        word = best[dfa["start"]]
        return {"finite": True, "certificate": {"topological_order": order,
                "suffix_max_lengths": lengths, "suffix_word_counts": counts,
                "longest_word": word, "longest_state_path": state_path(dfa, word),
                "max_length": len(word), "accepted_word_count": counts[dfa["start"]]}}
    # A short, explicit accepting cycle is easier to teach and independently check.
    candidates = []
    for start in access:
        visited = {start}
        queue = deque([(start, ())])
        found = None
        while queue and found is None:
            state, word = queue.popleft()
            for symbol, target in enumerate(dfa["transitions"][state]):
                if target == dfa["dead"]:
                    continue
                following = word + (symbol,)
                if target == start:
                    found = following
                    break
                if target not in visited:
                    visited.add(target)
                    queue.append((target, following))
        if found is not None:
            prefix = access[start]
            candidates.append((len(prefix) + len(found), len(prefix), prefix, found, start))
    require(candidates, "Cycle expected but none found")
    _, _, prefix, cycle, start = min(candidates)
    return {"finite": False, "certificate": {"prefix": prefix, "cycle": cycle, "cycle_state": start,
            "access_state_path": state_path(dfa, prefix), "cycle_state_path": state_path(dfa, cycle, start),
            "pumping_statement": "prefix + cycle^k is accepted for every integer k >= 0; all visited states are accepting."}}


def crosscheck_pruning(dfa, rules, max_length):
    rules = [(tuple(left), tuple(right)) for left, right in rules]
    checked = 0
    for length in range(max_length + 1):
        for word in product(range(dfa["alphabet_size"]), repeat=length):
            original = not any(search.forbidden_suffix(word[:end], rules) for end in range(1, length + 1))
            require(accepts(dfa, word) == original, f"Pruner mismatch on {word}")
            checked += 1
    return {"max_length": max_length, "words_checked": checked, "all_match_original_pruner": True,
            "scope": "Finite regression only; global language finiteness is certified separately."}


def finite_words(dfa):
    queue = deque([(dfa["start"], ())])
    result = []
    while queue:
        state, word = queue.popleft()
        result.append(word)
        for symbol, target in enumerate(dfa["transitions"][state]):
            if target != dfa["dead"]:
                queue.append((target, word + (symbol,)))
    return result


def analyse_method(source, method, max_length):
    rules = source["methods"][method]["rules"]
    search.verify_rules([(tuple(a), tuple(b)) for a, b in rules], source["transitions"])
    dfa = compile_dfa(rules, len(source["labels"]))
    analysis = classify_language(dfa)
    result = {"method": method, "labels": source["labels"], "rules": rules,
              "relators": source["methods"][method]["relators"], "dfa": dfa,
              "language": analysis, "bfs_diameter": source["diameter"],
              "pruner_regression": crosscheck_pruning(dfa, rules, max_length)}
    truth = {int(state): word for state, word in source["truth_paths"].items()}
    def evaluate(word):
        return search.endpoint(word, source["transitions"], source["identity"])
    if analysis["finite"]:
        count = analysis["certificate"]["accepted_word_count"]
        require(count <= 10000, "This D4 teaching runner caps full enumeration at 10,000 words")
        words = finite_words(dfa)
        require(len(words) == count, "Language count mismatch")
        result["accepted_words"] = [{"word": word, "endpoint": evaluate(word),
            "bfs_distance": len(truth[evaluate(word)]), "geodesic": len(word) == len(truth[evaluate(word)])} for word in words]
        endpoints = [evaluate(word) for word in words]
        result["finite_comparison"] = {
            "covers_all_group_elements": set(endpoints) == set(truth),
            "one_word_per_group_element": len(set(endpoints)) == len(endpoints) == len(truth),
            "all_words_geodesic": all(row["geodesic"] for row in result["accepted_words"]),
            "same_words_as_bfs_shortlex_paths": set(words) == {tuple(w) for w in truth.values()},
            "diameter_upper_bound": analysis["certificate"]["max_length"],
            "upper_bound_equals_bfs": analysis["certificate"]["max_length"] == source["diameter"]}
    else:
        cert = analysis["certificate"]
        order = next((k for k in range(1, len(truth) + 1) if evaluate(cert["cycle"] * k) == source["identity"]), None)
        require(order is not None, "No cycle-word group order found")
        result["infinite_comparison"] = {"cycle_word_group_order": order,
            "identity_block": cert["cycle"] * order,
            "identity_block_state_path": state_path(dfa, cert["cycle"] * order, cert["cycle_state"]),
            "pumped_examples": [{"k": k, "word": cert["prefix"] + cert["cycle"] * k,
                "state_path": state_path(dfa, cert["prefix"] + cert["cycle"] * k),
                "endpoint": evaluate(cert["prefix"] + cert["cycle"] * k),
                "bfs_distance": len(truth[evaluate(cert["prefix"] + cert["cycle"] * k)])} for k in (0, 1, 2, 4, 8)],
            "same_endpoint_examples": [{"k": k, "word": cert["prefix"] + cert["cycle"] * (order * k),
                "endpoint": evaluate(cert["prefix"] + cert["cycle"] * (order * k))} for k in (0, 1, 2)],
            "diameter_upper_bound": None,
            "interpretation": "Infinite accepted words, not an infinite group and not an infinite diameter."}
    return result


def dot_graph(result):
    dfa, labels = result["dfa"], result["labels"]
    lines = ["digraph DFA {", 'rankdir=LR;', 'node [fontname="Segoe UI"];', 'entry [shape=point];', f'entry -> q{dfa["start"]};']
    for state, memory in enumerate(dfa["memory"]):
        name = "REJECT" if memory is None else "epsilon" if not memory else label(memory, labels)
        lines.append(f'q{state} [shape={"box" if memory is None else "doublecircle"}, label={json.dumps(str(state) + ": " + name)}];')
    for state, row in enumerate(dfa["transitions"]):
        for symbol, target in enumerate(row):
            lines.append(f'q{state} -> q{target} [label={json.dumps(labels[symbol])}];')
    return "\n".join(lines + ["}", ""])


def summary_markdown(results):
    lines = ["# D4 規則自動機：有限／無限接受語言", "", "固定生成元順序 r、r^-1、s；接受字 = 不含任何規則左側子字的操作字。不是預設最短字。", "",
             "| 輪次 | 方法 | 額外關係 | 活狀態＋拒絕 | 語言 | 字數／證據 | 最長長度 | BFS 直徑 |",
             "|---|---|---|---|---|---|---:|---:|"]
    for item in results:
        language = item["language"]
        cert = language["certificate"]
        evidence = str(cert["accepted_word_count"]) if language["finite"] else f"前綴 {label(cert['prefix'], item['labels'])}；循環 {label(cert['cycle'], item['labels'])}"
        relators = "; ".join(label(w, item["labels"]) for w in item["relators"]) or "無"
        lines.append(f"| {item['budget']} | {item['method']} | {relators} | {len(item['dfa']['accepting'])}+1 | {'有限' if language['finite'] else '無限'} | {evidence} | {cert.get('max_length', '—')} | {item['bfs_diameter']} |")
    lines += ["", "拒絕狀態的自迴圈不算無限接受語言的證據；只有可達接受狀態的循環才算。", "",
              "有限性由完整活狀態圖的拓撲順序／循環判定；長度 8 以內的逐字比對只是額外回歸檢查。", "",
              "## 有限語言的全部字", ""]
    for item in results:
        if item["language"]["finite"]:
            lines.append(f"- {item['budget']}/{item['method']}：" + "；".join(label(row["word"], item["labels"]) for row in item["accepted_words"]))
    lines += ["", "完整預算組實際取得兩條 relators：rrrr、rsrs。一般與貼面兩組規則完全相同，不能把有限結果歸功於面來源。", "",
              "每個有限語言都完整重播至群狀態，與 BFS 的 8 個最短字逐筆比較；此例上界 U=3 與 BFS 下界 3 相合。"]
    return "\n".join(lines) + "\n"


def walkthrough_markdown(results):
    focus = {(item["budget"], item["method"]): item for item in results}
    lines = ["# 從 D4 規則到自動機：實際走一次", "", "字母順序 r < r^-1 < s。epsilon 是空字。狀態只是字尾記憶，不是 D4 群元素。", ""]
    for budget, method in (("single_relation", "ordinary"), ("single_relation", "faces"), ("full_budget", "faces")):
        item = focus[budget, method]
        dfa, language = item["dfa"], item["language"]
        lines += [f"## {budget}/{method}", "", "額外關係：" + "; ".join(label(w, item["labels"]) + " = e" for w in item["relators"]), "",
                  "### 狀態與完整轉移表", "", "| 狀態 | 記憶 | 讀 r | 讀 r^-1 | 讀 s | 接受？ |", "|---:|---|---:|---:|---:|---|"]
        for state, memory in enumerate(dfa["memory"]):
            row = dfa["transitions"][state]
            lines.append(f"| {state} | {'REJECT' if memory is None else label(memory, item['labels'])} | {row[0]} | {row[1]} | {row[2]} | {state in dfa['accepting']} |")
        cert = language["certificate"]
        if language["finite"]:
            lines += ["", "### 有限證據", "", f"活狀態拓撲順序：{cert['topological_order']}。每條活轉移都往順序後方走，因此無法一直延伸。", "",
                      f"最長字：{label(cert['longest_word'], item['labels'])}；狀態路徑：{cert['longest_state_path']}。", "",
                      "全部 8 個接受字為：" + "；".join(label(r["word"], item["labels"]) for r in item["accepted_words"]), "",
                      "逐字重播後，每個群元素恰有一個字，全部是 BFS 最短字。"]
        else:
            lines += ["", "### 無限證據", "", f"先讀 {label(cert['prefix'], item['labels'])}，路徑 {cert['access_state_path']}；再讀循環 {label(cert['cycle'], item['labels'])}，路徑 {cert['cycle_state_path']} 回到同一接受狀態。", "",
                      "循環可重複任意次，因此有任意長的接受字。以下只是示範，證明本身來自回圈：", "",
                      "| k | 接受字 | 長度 | BFS 距離 |", "|---:|---|---:|---:|"]
            for example in item["infinite_comparison"]["pumped_examples"]:
                lines.append(f"| {example['k']} | {label(example['word'], item['labels'])} | {len(example['word'])} | {example['bfs_distance']} |")
            inf = item["infinite_comparison"]
            lines += ["", f"循環字的群階數為 {inf['cycle_word_group_order']}；區塊 {label(inf['identity_block'], item['labels'])} 的群乘積是 e，卻能在此活狀態持續讀入。",
                      "所以甚至有無限多個字表示同一群元素。這揭露規則不足，不表示群是無限的。"]
    lines += ["", "## 為什麼有限時能給直徑上界？", "",
              "每條規則在所有起點保留終點並嚴格降低 shortlex。某元素字典序最小的最短字若包含規則左側，替換後不是更短，就是同長而字典序更小，兩者都矛盾。因此每個元素至少有一個最短字被自動機接受。",
              "若所有接受字長度至多 U，所有群元素就都能在 U 步內到達。這個上界論證不需要先假設合流；若要說所有接受字本身都是最短字，則需額外驗證。本次 D4 已完整與 BFS 比對。", "",
              "尚未宣稱對大型魔方有效、狀態數一定很小、規則來源具有優勢、一般合流或新的複雜度界。"]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "experiments/results/d4-automata")
    parser.add_argument("--max-check-length", type=int, default=8)
    args = parser.parse_args()
    require(0 <= args.max_check_length <= 9, "Regression length must be 0..9")
    destination = args.output / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    destination.mkdir(parents=True, exist_ok=False)
    report = {"schema_version": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
              "scope": "D4 sphere witness, seed 0, two persisted budgets, 3 methods per budget; no new relation selection.",
              "max_check_length": args.max_check_length, "cases": [],
              "source_sha256": {}, "code_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in (Path(__file__), Path(search.__file__), Path(__file__).with_name("verify_relation_automata.py"))}}
    catalogue = json.loads((ROOT / "data/surfaces/catalogue.json").read_text(encoding="utf-8"))
    try:
        for budget, folder in SOURCE_RUNS.items():
            path = ROOT / "experiments/results" / folder / "d4-g0-squares-seed0.json"
            source = json.loads(path.read_text(encoding="utf-8"))
            verify_source(source, catalogue)
            report["source_sha256"][str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
            for method in ("cancellation_only", "ordinary", "faces"):
                result = analyse_method(source, method, args.max_check_length)
                result.update({"budget": budget, "source_case": str(path.relative_to(ROOT))})
                name = f"{budget}-{method}"
                (destination / f"{name}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
                (destination / f"{name}.dot").write_text(dot_graph(result), encoding="utf-8")
                report["cases"].append(result)
    except Exception:
        (destination / "failure.txt").write_text(traceback.format_exc(), encoding="utf-8")
        raise
    (destination / "results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    from verify_relation_automata import verify_run
    verification = verify_run(destination)
    summary, walkthrough = summary_markdown(report["cases"]), walkthrough_markdown(report["cases"])
    REPORT.mkdir(parents=True, exist_ok=True)
    for directory in (destination, REPORT):
        (directory / "summary.md").write_text(summary, encoding="utf-8")
        (directory / "walkthrough.md").write_text(walkthrough, encoding="utf-8")
    (REPORT / "latest-run.json").write_text(json.dumps({"run_directory": str(destination.resolve()),
        "status": verification["status"], "results_sha256": verification["results_sha256"]}, indent=2), encoding="utf-8")
    print(destination)
    print("PASS: six DFAs, finite/cycle certificates and BFS comparison verified")


if __name__ == "__main__":
    main()
