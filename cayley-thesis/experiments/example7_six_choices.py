"""Enumerate six second face maps after Example 7's fixed first gluing.

Full reconstruction is the oracle. This is NOT a Ce/Cv-only update algorithm.
Every run is append-only and contains before/after data, reasons and witnesses.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import importlib.util
from itertools import permutations
import json
from pathlib import Path

import example7_rebuild as core

ROOT = core.ROOT
REPORT = ROOT / "reports/week1-example7-six-choice"
DEFAULT_OUTPUT = ROOT / "experiments/results/example7-six-choice"
NAMES = {"disk": "圓盤", "annulus": "環帶", "mobius_band": "莫比烏斯帶"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def json_value(value):
    return json.loads(json.dumps(value))


def members_text(members):
    return "{" + ",".join(f"t{t}:{v}" for t, v in members) + "}"


def decisions(stage):
    """Report Definition-5 checks separately from optional ambient orientability."""
    reasons = []
    if not stage["edge_orientation_consistent"]:
        reasons.append({"code": "REVERSED_SELF_EDGE", "message": "有原邊被反向識別到自身"})
    link_checks = []
    for link in stage["links"]:
        failed = []
        if not link["is_surface"]:
            failed.append("NOT_A_SURFACE")
        else:
            if not link["orientable"]:
                failed.append("NONORIENTABLE_VERTEX_LINK")
            elif link["genus"] is None:
                failed.append("INVALID_SURFACE_GENUS")
            elif link["genus"] != 0:
                failed.append("POSITIVE_GENUS_VERTEX_LINK")
        evidence = {k: link[k] for k in ("members", "V", "E", "F", "chi", "boundary_components",
                                         "orientable", "genus", "type", "is_surface")}
        for code in failed:
            reasons.append({"code": code, "link_members": link["members"], "evidence": evidence,
                            "message": "頂點 link 必須是可定向 genus=0 的曲面；" +
                                       f"此 link 為 {link['type']}，chi={link['chi']}，b={link['boundary_components']}"})
        link_checks.append({"members": link["members"], "passed": not failed, "failed_checks": failed,
                            "evidence": evidence, "local_vertex_checks": link["local_vertex_checks"],
                            "boundary_cycles": link["boundary_cycles"]})
    accepted = not reasons
    require(accepted == stage["partial_3_manifold_definition5"], "Decision disagrees with full oracle")
    return {"partial_accepted": accepted, "rejection_reasons": reasons, "link_checks": link_checks,
            "ambient_orientable": stage["orientable"],
            "orientable_partial_accepted": accepted and stage["orientable"],
            "orientable_target_additional_reasons": [] if stage["orientable"] else ["AMBIENT_NONORIENTABLE"],
            "manifold_with_boundary_link_test": stage["manifold_with_boundary_link_test"],
            "closed": not stage["boundary_faces"]}


def vertex_merge_trace(second):
    """Individual vertex unions are bookkeeping, NOT intermediate face gluings."""
    vertices = [(t, v) for t in range(2) for v in range(4)]
    relations = [((0, v), (1, v)) for v in (0, 1, 2)]
    result = []
    for a, b in zip(second["source_face"], second["target_face"]):
        pair = ((second["source_tet"], a), (second["target_tet"], b))
        before, _ = core.quotient(vertices, relations)
        relations.append(pair)
        after, _ = core.quotient(vertices, relations)
        result.append({"vertex_pair": pair, "classes_before": before, "classes_after": after,
                       "merged_two_classes": len(after) < len(before)})
    return result


def apex_orientation_trace(glues):
    """Two explicit sign equations for the common apex in choices 123 and 321."""
    equations = []
    for number, (t, f, s, g, p) in enumerate(core.normalize(glues)[0], 1):
        if t != 0 or s != 1 or p[2] != 2:
            continue
        order = [0, 1, 3]
        i, j = order.index(f), order.index(g)
        source_direction = [order[(i + 1) % 3], order[(i + 2) % 3]]
        target_direction = [order[(j + 1) % 3], order[(j + 2) % 3]]
        mapped = [p[v] for v in source_direction]
        relation = -1 if mapped == target_direction else 1
        equations.append({"gluing_number": number, "source_triangle": [0, 2], "target_triangle": [1, 2],
                          "source_boundary_direction": source_direction, "mapped_direction": mapped,
                          "target_boundary_direction": target_direction, "target_sign_over_source": relation})
    if len(equations) != 2:
        return None
    return {"triangle_orientation_order": [0, 1, 3], "equations": equations,
            "consistent": equations[0]["target_sign_over_source"] == equations[1]["target_sign_over_source"],
            "cycle_sign_product": equations[0]["target_sign_over_source"] * equations[1]["target_sign_over_source"],
            "interpretation": "Orientability requires opposite induced directions on each glued small edge."}


def state_key(stage):
    boundary = {"boundary_faces": sorted(stage["boundary_faces"]), "Ce": core.canonical_ce(stage["Ce"]),
                "Cv": sorted(sorted(map(list, group)) for group in stage["Cv"])}
    serialized = json.dumps(boundary, sort_keys=True, separators=(",", ":"))
    return {"boundary_data": boundary, "sha256": hashlib.sha256(serialized.encode()).hexdigest(),
            "scope": "Fixed labeled boundary; no quotient by relabeling; not a topological classification."}


def make_case(target):
    target = tuple(target)
    require(sorted(target) == [1, 2, 3], "Target must permute 123")
    second = {"source_tet": 0, "source_face": [0, 2, 3], "target_tet": 1, "target_face": list(target)}
    stage = core.analyse([core.FIRST, second])
    trace = vertex_merge_trace(second)
    require(trace[-1]["classes_after"] == stage["vertex_classes"], "Merge trace mismatch")
    result = {"choice": "".join(map(str, target)), "glues": [core.FIRST, second],
              "vertex_map": [[a, b] for a, b in zip(second["source_face"], second["target_face"])],
              "vertex_merge_trace": trace, "after": stage, "decision": decisions(stage),
              "boundary_state": state_key(stage)}
    if target in ((1, 2, 3), (3, 2, 1)):
        orientation = apex_orientation_trace(result["glues"])
        apex = next(link for link in stage["links"] if (0, 2) in link["members"])
        require(orientation["consistent"] == apex["orientable"], "Orientation witness mismatch")
        result["apex_orientation_trace"] = orientation
    return result


def verify_case(case):
    expected = make_case(tuple(map(int, case["choice"])))
    require(json_value(expected) == json_value(case), "Saved case or verdict differs from recomputation")


def cross_check_cases(cases):
    """Second implementation for equivalence/links; no claim of full independence."""
    path = ROOT / "reports/examples/fixed_graph_lens17.py"
    spec = importlib.util.spec_from_file_location("existing_lens_checker", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    checks = []
    for case in cases:
        stage = case["after"]
        records, _ = core.normalize(case["glues"])
        other = module.analyse(2, [(t, f, s, tuple(p[i] for i in range(4))) for t, f, s, g, p in records])
        def signature(links, member_key):
            return sorted((sorted(map(tuple, l[member_key])), l["V"], l["E"], l["F"], l["chi"],
                           l["boundary_components"], bool(l["is_surface"])) for l in links)
        require(signature(stage["links"], "members") == signature(other["links"], "corners"), "Link cross-check failed")
        require(json_value(stage["Cv"]) == json_value(other["boundary_state"]["Cv"]), "Cv cross-check failed")
        def occurrence(occ):
            t, f, a, b = occ
            return f"t{t}:" + "".join(str(v) for v in range(4) if v != f) + f"/{a}{b}"
        ce = [[occurrence(a), occurrence(b), flag] for a, b, flag in other["boundary_state"]["Ce"]]
        require(core.canonical_ce(stage["Ce"]) == core.canonical_ce(ce), "Ce cross-check failed")
        require(stage["orientable"] == bool(other["orientable"]), "Ambient orientation cross-check failed")
        require(stage["edge_orientation_consistent"] == bool(other["edge_orientation_consistent"]), "Edge cross-check failed")
        checks.append({"choice": case["choice"], "status": "PASS"})
    return {"status": "PASS", "cases": checks, "implementation": str(path.relative_to(ROOT)),
            "implementation_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "scope": "Ce/Cv, V/E/F/chi/boundary counts/local surface, ambient orientation and edge consistency. Apex orientation has explicit sign witnesses; not Lean."}


def render_summary(cases):
    lines = ["# 六選一貼合實驗：完整重建判定", "", "固定第一次 t0:012↔t1:012；第二次為 t0:023↔t1:perm(123)。不是原文的 t1 自貼。", "",
             "| 選擇 | Partial 通過 | 整體可定向 | 可定向 partial 通過 | 頂點類 | links | 拒絕原因（partial） |",
             "|---|---|---|---|---:|---|---|"]
    for case in cases:
        d, stage = case["decision"], case["after"]
        types = "、".join(NAMES.get(l["type"], l["type"]) for l in stage["links"])
        reasons = ", ".join(r["code"] for r in d["rejection_reasons"]) or "無"
        lines.append(f"| {case['choice']} | {d['partial_accepted']} | {d['ambient_orientable']} | {d['orientable_partial_accepted']} | {len(stage['vertex_classes'])} | {types} | {reasons} |")
    lines += ["", "判準分開：Definition 5 不要求整個空間可定向。231、312 通過 partial，但不通過額外的整體可定向目標。",
              "321 的環帶可以是合法 partial link，不代表底層已是三維流形。六種結果都仍有四個邊界面，均非閉合。", "",
              "完整 Ce/Cv、小三角形資料、局部頂點檢查、邊界圈與理由見 cases/<選擇>.json。"]
    return "\n".join(lines) + "\n"


def render_comparison(cases, before):
    chosen = {case["choice"]: case for case in cases}
    lines = ["# 321 與 123：逐步對照（由實驗產生）", "", "## 共同起點", "",
             "第一次貼合 t0:012↔t1:012；5 個頂點類、6 個邊界面，5 個圓盤 links。", "",
             "此處的 123 指 t0:023↔t1:123，不是先前原文照字面 t1:023↔t1:321。", ""]
    for choice in ("321", "123"):
        case = chosen[choice]
        lines += [f"## 選擇 {choice}", "", "### 1．依序合併頂點（僅是等價類 bookkeeping，不是半張面已完成貼合）", ""]
        for item in case["vertex_merge_trace"]:
            a, b = item["vertex_pair"]
            lines.append(f"- 加入 t{a[0]}:{a[1]} ↔ t{b[0]}:{b[1]} → " + "；".join(members_text(g) for g in item["classes_after"]))
        lines += ["", "### 2．最終 Cv", "", "；".join(members_text(g) for g in case["after"]["Cv"]), "",
                  "### 3．最終 Ce（方向皆以局部編號小到大為準）", "", "| 出現位置 | 出現位置 | 同方向 |", "|---|---|---|"]
        for a, b, same in case["after"]["Ce"]:
            lines.append(f"| {a} | {b} | {same} |")
        apex = next(link for link in case["after"]["links"] if (0, 2) in link["members"])
        lines += ["", "### 4．頂點 2 的 link", "",
                  f"V={apex['V']}、E={apex['E']}、F={apex['F']}、χ={apex['chi']}、b={apex['boundary_components']}；可定向={apex['orientable']}；{NAMES[apex['type']]}。", "",
                  "完整局部小鄰域檢查通過；差別不是曲面破裂，而是方向與邊界圈。", "",
                  "給 L(t0:2) 的三角形方向為 +1；每條貼邊要求兩側誘導方向相反。", ""]
        for eq in case["apex_orientation_trace"]["equations"]:
            lines.append(f"- 第 {eq['gluing_number']} 次貼合要求 L(t1:2) 的方向為 {eq['target_sign_over_source']:+d}。")
        lines.append("")
        lines.append("兩項要求一致，可選全域方向。" if apex["orientable"] else "兩項要求衝突，形成非可定向的 link；這是拒絕證據。")
        lines += ["", "### 5．判定", "", "partial_accepted=" + str(case["decision"]["partial_accepted"])]
        lines.extend("- " + r["code"] + "：" + r["message"] for r in case["decision"]["rejection_reasons"])
        lines.append("")
    lines += ["## 向老師解釋的結論", "", "321 與 123 都保留頂點 2，兩片 link 三角形都給 V/E/F=2/4/2、χ=0；但 321 左右同向貼合，留下兩圈且可定向；123 左右反向貼合，成一圈且非可定向。",
              "所以不能只用 χ=0 或頂點類總數決策。本輪從完整歷史重建 Ce/Cv 與 links；尚未證明只靠 Ce/Cv 的更新器已正確。"]
    return "\n".join(lines) + "\n"


def verify_saved(run_dir, independent=False):
    run_dir = Path(run_dir)
    path = run_dir / "results.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    require(report["before"] == json_value(core.analyse([core.FIRST])), "Before-state mismatch")
    require([c["choice"] for c in report["cases"]] == ["123", "132", "213", "231", "312", "321"], "Missing or duplicate choices")
    for case in report["cases"]:
        verify_case(case)
        saved = json.loads((run_dir / "cases" / f"{case['choice']}.json").read_text(encoding="utf-8"))
        require(saved == case, "Per-choice checkpoint differs from aggregate")
    accepted = [c for c in report["cases"] if c["decision"]["partial_accepted"]]
    expected_counts = {"choices": 6, "partial_accepted": len(accepted),
                       "orientable_partial_accepted": sum(c["decision"]["orientable_partial_accepted"] for c in report["cases"]),
                       "distinct_accepted_labeled_states": len({c["boundary_state"]["sha256"] for c in accepted})}
    require(report["counts"] == expected_counts, "Summary counts mismatch")
    result = {"status": "PASS", "choices": 6, "checked_utc": datetime.now(timezone.utc).isoformat(),
              "results_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
              "checks": ["all maps", "before-state", "saved Ce/Cv and full links", "decisions/reasons", "vertex-merge and orientation traces", "per-case checkpoints", "counts"],
              "scope": "Full-oracle replay, not a Ce/Cv-only update proof."}
    if independent:
        result["cross_check"] = cross_check_cases(report["cases"])
    (run_dir / "verification.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--cross-check", action="store_true", help="Also use existing NumPy implementation")
    parser.add_argument("--verify-run", type=Path, help="Verify an existing run instead of making a new one")
    args = parser.parse_args()
    if args.verify_run:
        result = verify_saved(args.verify_run, args.cross_check)
        print(f"{result['status']}: six persisted cases checked")
        return
    run_dir = args.output / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    (run_dir / "cases").mkdir(parents=True, exist_ok=False)
    before = core.analyse([core.FIRST])
    (run_dir / "before.json").write_text(json.dumps(before, ensure_ascii=False, indent=2), encoding="utf-8")
    cases = []
    for target in permutations([1, 2, 3]):
        case = make_case(target)
        verify_case(case)
        (run_dir / "cases" / f"{case['choice']}.json").write_text(json.dumps(case, ensure_ascii=False, indent=2), encoding="utf-8")
        cases.append(case)
    accepted = [case for case in cases if case["decision"]["partial_accepted"]]
    report = {"schema_version": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
              "scope": "Two labeled tetrahedra, first glue fixed, six maps of one fixed second face pair. Full oracle, not a Ce/Cv-only updater, no global census claim.",
              "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in (Path(__file__), Path(core.__file__))},
              "before": before, "cases": cases,
              "counts": {"choices": len(cases), "partial_accepted": len(accepted),
                         "orientable_partial_accepted": sum(c["decision"]["orientable_partial_accepted"] for c in cases),
                         "distinct_accepted_labeled_states": len({c["boundary_state"]["sha256"] for c in accepted})}}
    if args.cross_check:
        report["cross_check"] = cross_check_cases(cases)
    summary, comparison = render_summary(cases), render_comparison(cases, before)
    (run_dir / "results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "summary.md").write_text(summary, encoding="utf-8")
    (run_dir / "comparison321-123.md").write_text(comparison, encoding="utf-8")
    with (run_dir / "summary.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["choice", "partial_accepted", "ambient_orientable", "orientable_partial_accepted", "rejection_codes"])
        for case in cases:
            d = case["decision"]
            writer.writerow([case["choice"], d["partial_accepted"], d["ambient_orientable"], d["orientable_partial_accepted"],
                             ";".join(r["code"] for r in d["rejection_reasons"])])
    verify_saved(run_dir)
    REPORT.mkdir(parents=True, exist_ok=True)
    for filename, contents in (("summary.md", summary), ("comparison321-123.md", comparison)):
        (REPORT / filename).write_text(contents, encoding="utf-8")
    (REPORT / "latest-run.json").write_text(json.dumps({"run_directory": str(run_dir.resolve()),
        "results_sha256": hashlib.sha256((run_dir / "results.json").read_bytes()).hexdigest(),
        "counts": report["counts"], "cross_checked": args.cross_check}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(run_dir)
    print(json.dumps(report["counts"]))


if __name__ == "__main__":
    main()
