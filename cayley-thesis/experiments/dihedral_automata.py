"""Budget sweeps on D8/D16. Exact BFS + validated prism faces + DFA proofs.

Dn here has order 2n. Ordinary relator pool: all cyclically freely reduced
closed words of lengths 3..n, quotient cyclic rotation and inverse reversal.
Every run saves checkpoints; no relation selection uses BFS distances.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from time import perf_counter
import traceback

import relation_search as search
import relation_automata as automata

ROOT = search.ROOT
REPORT = ROOT / "reports/dihedral-automata"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def pack(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def build_source(n, cutoff=6):
    started = perf_counter()
    spec = {"spec": {"family": "dihedral", "n": n}, "generators": [[1, 0], [n - 1, 0], [0, 1]]}
    group, generators, transitions, inverses, identity = search.model(spec)
    model_seconds = perf_counter() - started
    started = perf_counter()
    truth = search.bfs(transitions, identity)
    bfs_seconds = perf_counter() - started
    started = perf_counter()
    construction = [[0] * n, [0, 2, 0, 2]]
    faces = search.surfaces.relator_surface(group, generators, construction)
    validation = search.surfaces.validate_surface(group, generators, faces)
    require(validation["valid"] and validation["genus"] == 0, "Prism surface failed")
    face_relators = sorted({search.canonical(tuple(generators.index(s) for _, s in
                     search.surfaces.darts_of_face(group, generators, face)), inverses) for face in faces}, key=lambda w: (len(w), w))
    surface_seconds = perf_counter() - started
    started = perf_counter()
    pool = search.closed_words(transitions, identity, inverses, n)
    pool_seconds = perf_counter() - started
    require(all(w in pool for w in face_relators), "Face relator missing from ordinary pool")
    started = perf_counter()
    expansions, timings = [], []
    for word in pool:
        clock = perf_counter()
        expansions.append(search.rules_for([word], inverses))
        timings.append(perf_counter() - clock)
    baseline = search.rules_for([], inverses)
    library = sorted(set(baseline).union(*(set(rules) for rules in expansions)), key=lambda r: (len(r[0]), r))
    ids = {rule: i for i, rule in enumerate(library)}
    rule_ids = [[ids[rule] for rule in rules] for rules in expansions]
    library_seconds = perf_counter() - started
    source = {"n": n, "group_order": 2 * n, "spec": spec, "labels": ["r", "r^-1", "s"],
              "elements": group["elements"], "transitions": transitions, "inverses": inverses, "identity": identity,
              "truth_paths": {str(k): word for k, word in truth.items()}, "diameter": max(map(len, truth.values())),
              "face_construction": construction, "faces": [[group["elements"].index(v) for v in face] for face in faces],
              "surface_validation": validation, "relator_pool": pool,
              "pool_length_histogram": dict(Counter(map(len, pool))),
              "face_relator_ids": [pool.index(w) for w in face_relators],
              "short_relator_ids": [i for i, word in enumerate(pool) if len(word) <= cutoff],
              "short_cutoff": cutoff, "rule_library": library, "relator_rule_ids": rule_ids,
              "baseline_rule_ids": [ids[rule] for rule in baseline],
              "costs": {"model_seconds": model_seconds, "bfs_seconds": bfs_seconds,
                        "surface_seconds": surface_seconds, "ordinary_pool_seconds": pool_seconds,
                        "rule_library_seconds": library_seconds, "per_relator_expansion_seconds": timings}}
    return source


def select_rules(source, selected):
    ids = sorted(set(source["baseline_rule_ids"]).union(*(set(source["relator_rule_ids"][i]) for i in selected)))
    return ids, [source["rule_library"][i] for i in ids]


def source_view(source, selected, method, rules):
    return {**{k: source[k] for k in ("labels", "transitions", "identity", "truth_paths", "diameter")},
            "methods": {method: {"relators": [source["relator_pool"][i] for i in selected], "rules": rules}}}


def evaluate(source, selected, stage_id, strategy, check_length):
    started = perf_counter()
    rule_ids, rules = select_rules(source, selected)
    selection_seconds = perf_counter() - started
    view = source_view(source, selected, strategy, rules)
    started = perf_counter()
    result = automata.analyse_method(view, strategy, check_length)
    analysis_seconds = perf_counter() - started
    # Store IDs instead of duplicating potentially 11,000+ long rules per checkpoint.
    del result["rules"], result["relators"]
    finite = result["language"]["finite"]
    U = result["language"]["certificate"].get("max_length")
    result.update({"id": stage_id, "n": source["n"], "strategy": strategy,
        "selected_relator_ids": list(selected), "rule_ids": rule_ids,
        "budget": len(selected), "relator_symbols": sum(len(source["relator_pool"][i]) for i in selected),
        "upper_bound": U, "gap": U - source["diameter"] if finite else None,
        "costs": {"selection_seconds": selection_seconds, "analysis_seconds": analysis_seconds,
                  "measured_stage_seconds": selection_seconds + analysis_seconds,
                  "selected_relator_expansion_seconds": sum(source["costs"]["per_relator_expansion_seconds"][i] for i in selected),
                  "expanded_rules": len(rules), "expanded_rule_symbols": sum(len(a) + len(b) for a, b in rules),
                  "live_dfa_states": len(result["dfa"]["accepting"]), "dfa_states_with_sink": len(result["dfa"]["memory"]),
                  "dfa_serialized_utf8_bytes": len(pack(result["dfa"]).encode("utf-8")),
                  "peak_ram_measured": False,
                  "timing_scope": "analysis includes all-start rule validation, DFA build/classification, bounded pruner regression, and accepted-word/group comparison; excludes shared preprocessing, disk and independent verification."}})
    return result


def group_experiment(source, destination, check_length):
    steps = []
    def add(selected, stage_id, strategy):
        result = evaluate(source, selected, stage_id, strategy, check_length)
        (destination / f"{stage_id}.json").write_text(pack(result), encoding="utf-8")
        steps.append(result)
        return result
    sequences = {}
    for strategy, sequence in (("face_prefix", source["face_relator_ids"]),
                               ("ordinary_shortlex_prefix", list(range(len(source["relator_pool"]))))):
        stage_ids, first_finite = [], None
        for k in range(len(sequence) + 1):
            stage_id = f"{strategy}-k{k:03d}"
            result = add(sequence[:k], stage_id, strategy)
            stage_ids.append(stage_id)
            if result["language"]["finite"]:
                first_finite = k
                break
        sequences[strategy] = {"ordered_relator_ids": sequence, "tested_stage_ids": stage_ids,
                              "first_finite_budget_in_this_order": first_finite,
                              "sum_measured_stage_seconds": sum(s["costs"]["measured_stage_seconds"] for s in steps if s["strategy"] == strategy)}
    short_result = add(source["short_relator_ids"], "ordinary_short_only-all", "ordinary_short_only")
    singleton_ids = []
    for i in range(len(source["relator_pool"])):
        stage_id = f"singleton-{i:03d}"
        add([i], stage_id, "singleton_audit")
        singleton_ids.append(stage_id)
    length4 = [i for i, w in enumerate(source["relator_pool"]) if len(w) == 4]
    require(len(length4) == 1, "This control expects a unique canonical length-4 relator")
    long_ids = [i for i, w in enumerate(source["relator_pool"]) if len(w) == source["n"]]
    matched_ids = []
    for i in long_ids:
        stage_id = f"matched-pair-{i:03d}"
        add([length4[0], i], stage_id, "matched_length_pair")
        matched_ids.append(stage_id)
    singles = [s for s in steps if s["strategy"] == "singleton_audit"]
    pairs = [s for s in steps if s["strategy"] == "matched_length_pair"]
    require(not any(s["language"]["finite"] for s in singles), "Unexpected finite singleton; report minimum logic must be generalized")
    require(any(s["language"]["finite"] for s in pairs), "No finite two-relator witness")
    return {"n": source["n"], "diameter": source["diameter"], "steps": steps, "sequences": sequences,
            "short_only_stage_id": short_result["id"], "singleton_stage_ids": singleton_ids,
            "matched_pair_stage_ids": matched_ids,
            "pool_minimum_certificate": {"minimum_relators_with_common_cancellation": 2,
                "no_finite_singleton_stage_ids": singleton_ids,
                "finite_pair_witness_stage_ids": [s["id"] for s in pairs if s["language"]["finite"]],
                "scope": "Exact only within this complete length<=n canonical pool and this rules_for expansion, with inverse cancellations always included."},
            "matched_pair_counts": {"tested": len(pairs), "finite": sum(s["language"]["finite"] for s in pairs)}}


def report_markdown(groups, sources):
    lines = ["# D8／D16：關係預算、有限語言與成本", "", "Dn 的階數是 2n；固定單位成本生成元 r、r^-1、s。所有結果均使用完整 BFS 與合法球面貼面驗證。", "",
             "| 群 | 階數 | BFS 直徑 | 面排序首次有限 K | 一般短到長排序首次有限 K | 池內真正最少 K | 等長配對有限／全部 |",
             "|---|---:|---:|---:|---:|---:|---|"]
    for group, source in zip(groups, sources):
        counts = group["matched_pair_counts"]
        lines.append(f"| D{group['n']} | {source['group_order']} | {group['diameter']} | {group['sequences']['face_prefix']['first_finite_budget_in_this_order']} | {group['sequences']['ordinary_shortlex_prefix']['first_finite_budget_in_this_order']} | 2 | {counts['finite']}/{counts['tested']} |")
    lines += ["", "## 第一個有限 checkpoint 的原始成本", "",
              "| 群／策略 | K | 關係符號 | 展開規則 | 規則符號 | 活狀態 | DFA 序列化 bytes | U | gap | 該步秒數 | 找到此步累計分析秒數 |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for group in groups:
        for strategy in ("face_prefix", "ordinary_shortlex_prefix"):
            sequence = group["sequences"][strategy]
            step = next(s for s in group["steps"] if s["id"] == sequence["tested_stage_ids"][-1])
            cost = step["costs"]
            lines.append(f"| D{group['n']}/{strategy} | {step['budget']} | {step['relator_symbols']} | {cost['expanded_rules']} | {cost['expanded_rule_symbols']} | {cost['live_dfa_states']} | {cost['dfa_serialized_utf8_bytes']} | {step['upper_bound']} | {step['gap']} | {cost['measured_stage_seconds']:.6f} | {sequence['sum_measured_stage_seconds']:.6f} |")
    lines += ["", "秒數是單次本機觀測，不是穩定加速比；包含驗證／回歸，不是純 DFA 核心時間。另需加上共用前處理及獨立證書檢查成本。序列化 bytes 不等於峰值 RAM。", "",
              "## 共用成本與合法面資料", "", "| 群 | 面數／genus | 普通池大小 | BFS 秒 | 面建構秒 | 普通池建構秒 | 全池規則庫建構秒 |", "|---|---|---:|---:|---:|---:|---:|"]
    for source in sources:
        c, v = source["costs"], source["surface_validation"]
        lines.append(f"| D{source['n']} | {v['face_count']}/{v['genus']} | {len(source['relator_pool'])} | {c['bfs_seconds']:.6f} | {c['surface_seconds']:.6f} | {c['ordinary_pool_seconds']:.6f} | {c['rule_library_seconds']:.6f} |")
    lines += ["", "## 長度公平性與循環", ""]
    for group, source in zip(groups, sources):
        short = next(s for s in group["steps"] if s["id"] == group["short_only_stage_id"])
        cert = short["language"]["certificate"]
        lines.append(f"- D{source['n']} 長度≤{source['short_cutoff']} 普通池全部 {short['budget']} 條：{'有限' if short['language']['finite'] else '無限'}；" +
                     (f"前綴 {automata.label(cert['prefix'], source['labels'])}、循環 {automata.label(cert['cycle'], source['labels'])}。" if not short["language"]["finite"] else f"U={short['upper_bound']}。"))
    lines += ["", "面池固定包含 rsrs 與 r^n；它取得了嚴格短池沒有的長關係。一般完整池也包含同樣兩條，所以面排序的 K 優勢不是一般池最小 K 的劣勢。",
              "同一預算2條、同一總長 n+4 的全量配對中，只有包含 r^n 的配對有限。這是關係選擇敏感性，不是新的拓撲定理。", "",
              "完整的每步 U−D、循環證書、同群元素重複代表、最長字、接受字、規則 ID 與成本都保存為 checkpoint；未證明一般 ML 效益或魔方擴展。"]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--groups", nargs="+", type=int, choices=[8, 16], default=[8, 16])
    parser.add_argument("--max-check-length", type=int, default=3)
    parser.add_argument("--output", type=Path, default=ROOT / "experiments/results/dihedral-automata")
    args = parser.parse_args()
    require(0 <= args.max_check_length <= 5, "Regression bound must be 0..5")
    require(len(set(args.groups)) == len(args.groups), "Duplicate groups")
    run_dir = args.output / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    run_dir.mkdir(parents=True, exist_ok=False)
    started = perf_counter()
    report = {"schema_version": 1, "created_utc": datetime.now(timezone.utc).isoformat(), "parameters": {"groups": args.groups, "max_check_length": args.max_check_length},
              "groups": [], "sources": {}, "source_sha256": {},
              "code_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in
                (Path(__file__), Path(search.__file__), Path(automata.__file__), Path(__file__).with_name("verify_dihedral_automata.py"))}}
    sources = []
    try:
        for n in args.groups:
            directory = run_dir / f"d{n}"
            directory.mkdir()
            source = build_source(n)
            source_path = directory / "source.json"
            source_path.write_text(pack(source), encoding="utf-8")
            report["sources"][str(n)] = str(source_path.relative_to(run_dir))
            report["source_sha256"][str(n)] = hashlib.sha256(source_path.read_bytes()).hexdigest()
            result = group_experiment(source, directory, args.max_check_length)
            report["groups"].append(result)
            sources.append(source)
            print(f"D{n}: {len(result['steps'])} checkpoints; BFS={result['diameter']}; face K={result['sequences']['face_prefix']['first_finite_budget_in_this_order']}; generic K={result['sequences']['ordinary_shortlex_prefix']['first_finite_budget_in_this_order']}", flush=True)
        report["build_experiments_and_checkpoint_seconds"] = perf_counter() - started
        (run_dir / "results.json").write_text(pack(report), encoding="utf-8")
        from verify_dihedral_automata import verify_run
        verification = verify_run(run_dir)
    except Exception:
        (run_dir / "failure.txt").write_text(traceback.format_exc(), encoding="utf-8")
        raise
    summary = report_markdown(report["groups"], sources)
    REPORT.mkdir(parents=True, exist_ok=True)
    for directory in (run_dir, REPORT):
        (directory / "summary.md").write_text(summary, encoding="utf-8")
    (REPORT / "latest-run.json").write_text(json.dumps({"run_directory": str(run_dir.resolve()),
        "status": verification["status"], "results_sha256": verification["results_sha256"],
        "verification_seconds": verification["seconds"]}, indent=2), encoding="utf-8")
    print(run_dir)
    print("PASS: budgets, all singleton and equal-length controls, gap and DFA certificates verified")


if __name__ == "__main__":
    main()
