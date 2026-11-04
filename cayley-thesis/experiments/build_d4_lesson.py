"""Build an auditable lesson from a persisted, independently checked D4 run."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from verify_run import verify_case

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN = ROOT / "experiments/results/20261031T175148_814309Z"
DEFAULT_OUTPUT = ROOT / "reports/week1-d4-demo"


def trace_search(case, method, target):
    """Replay exact IDDFS ordering, logging why each generated candidate is rejected."""
    transitions = case["transitions"]
    rules = case["methods"][method]["rules"]
    events = []
    counts = Counter(entered=0, generated=0, pruned=0, expanded=0, rule_checks=0)
    def visit(state, word, limit):
        counts["entered"] += 1
        if state == target:
            return word
        if len(word) == limit:
            return None
        counts["expanded"] += 1
        for move, following in enumerate(transitions[state]):
            candidate = word + [move]
            counts["generated"] += 1
            matched = None
            for left, right in rules:
                counts["rule_checks"] += 1
                if len(candidate) >= len(left) and candidate[-len(left):] == left:
                    matched = [left, right]
                    break
            events.append({"limit": limit, "word": candidate, "endpoint": following,
                           "at_depth_limit": len(candidate) == limit, "matched_rule": matched})
            if matched:
                counts["pruned"] += 1
                continue
            result = visit(following, candidate, limit)
            if result is not None:
                return result
        return None
    for limit in range(case["diameter"] + 1):
        answer = visit(case["identity"], [], limit)
        if answer is not None:
            saved = case["methods"][method]["targets"][str(target)]
            if answer != saved["word"] or dict(counts) != saved["counts"]:
                raise ValueError("Trace does not reproduce saved search")
            return {"answer": answer, "counts": dict(counts), "events": events}
    raise ValueError("Trace failed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    catalogue = json.loads((ROOT / "data/surfaces/catalogue.json").read_text(encoding="utf-8"))
    paths = [args.run / f"{surface}-seed0.json" for surface in ("d4-g0-squares", "d4-g1-hexagons")]
    cases = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    for case in cases:
        verify_case(case, catalogue)
    case, torus = cases
    assert case["transitions"] == torus["transitions"]
    assert case["truth_paths"] == torus["truth_paths"]
    # Freeze the concrete lesson assumptions; fail rather than animate stale claims.
    assert case["methods"]["faces"]["relators"] == [[0, 0, 0, 0]]
    assert case["methods"]["ordinary"]["relators"] == [[0, 2, 0, 2]]
    names = ["e", "s", "r", "rs", "r^2", "r^2s", "r^-1", "r^-1s"]
    traces = {method: {str(target): trace_search(case, method, target) for target in range(8)}
              for method in case["methods"]}
    metrics = []
    for method, saved in case["methods"].items():
        total = Counter()
        for result in saved["targets"].values():
            total.update(result["counts"])
        nontrivial = [event for trace in traces[method].values() for event in trace["events"]
                      if event["matched_rule"] and event["matched_rule"][1] != []]
        # More generally distinguish cancellation from all extra rules, including rhs=e.
        cancellation = {tuple(rule[0]) for rule in case["methods"]["cancellation_only"]["rules"]}
        extra = [event for trace in traces[method].values() for event in trace["events"]
                 if event["matched_rule"] and tuple(event["matched_rule"][0]) not in cancellation]
        assert all(event["at_depth_limit"] for event in extra)
        metrics.append({"method": method, **dict(total), "rules": saved["rule_count"],
                        "rule_symbols": saved["rule_symbols"], "extra_prunes": len(extra),
                        "extra_prunes_at_depth_limit": sum(e["at_depth_limit"] for e in extra)})
    assert [m["generated"] for m in metrics] == [49, 49, 49]
    data = {"title": "D4: BFS truth, face relations, pruning and counterexamples",
            "input_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
            "input_directory": str(args.run.relative_to(ROOT)) if args.run.is_relative_to(ROOT) else str(args.run),
            "state_names": names, "case": case, "torus": torus,
            "layers": {str(d): [names[int(k)] for k, word in case["truth_paths"].items() if len(word) == d]
                       for d in range(4)}, "metrics": metrics,
            "traces": traces,
            "trace_check": "All replayed words and counters equal saved results; every extra prune occurs at that iteration's depth limit."}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "d4_lesson_data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# D4 實際數據表（由程式產生）", "", "右乘步行，生成元順序 r, r^-1, s。只選一條長度 4 關係；seed=0。", "",
             "| 狀態 | BFS 距離 | BFS 最短字 |", "|---|---:|---|"]
    def label(word):
        return " ".join(case["labels"][i] for i in word) or "e"
    for state in range(8):
        word = case["truth_paths"][str(state)]
        lines.append(f"| {names[state]} | {len(word)} | {label(word)} |")
    lines += ["", "| 方法 | generated | entered | expanded | pruned | rule_checks | 規則數 | 規則符號數 | 額外剪枝（皆在深度界） |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for m in metrics:
        lines.append("| " + " | ".join(str(m[k]) for k in ("method", "generated", "entered", "expanded", "pruned", "rule_checks", "rules", "rule_symbols", "extra_prunes")) + " |")
    lines += ["", "## 搜尋最遠目標 r^2s：深度界 3 的候選（順序固定）", "",
              "三組都在此輪遇到 rr s 後停止。完整含較淺迭代與其他目標的 trace 在 JSON。", "",
              "| 候選字 | cancellation_only | ordinary | faces |", "|---|---|---|---|"]
    for index, event in enumerate(traces["faces"]["5"]["events"]):
        if event["limit"] != 3:
            continue
        row = [label(event["word"])]
        for method in case["methods"]:
            counterpart = next(e for e in traces[method]["5"]["events"] if e["limit"] == 3 and e["word"] == event["word"])
            rule = counterpart["matched_rule"]
            row.append(f"剪掉：{label(rule[0])} → {label(rule[1])}" if rule else "進入")
        lines.append("| " + " | ".join(row) + " |")
    (args.output / "computed-tables.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(args.output)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
