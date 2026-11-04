"""Complete labeled 6x6 one-tetrahedron census with exact homology certificates.

Fixed face pairs: 012 -> perm(013), 023 -> perm(123). Standard library only.
All 36 cases are retained; acceptance targets closed connected orientable 3-manifolds.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict, deque
import csv
from datetime import datetime, timezone
import hashlib
from itertools import combinations, permutations, product
import json
from pathlib import Path
import time

import example7_rebuild as core
from integer_homology import integral_homology, verify_homology, smith_normal_form

ROOT = core.ROOT
DEFAULT_OUTPUT = ROOT / "experiments/results/one-tetrahedron"
REPORT = ROOT / "reports/one-tetrahedron-36"
FIRST_TARGETS = list(permutations((0, 1, 3)))
SECOND_TARGETS = list(permutations((1, 2, 3)))
REASON_NAMES = {
    "REVERSED_SELF_EDGE": "邊反向自識別",
    "NONSPHERICAL_VERTEX_LINK": "頂點 link 非球面",
    "AMBIENT_NONORIENTABLE": "整體不可定向",
    "NOT_CLOSED": "尚有未配對面", "NOT_CONNECTED": "不連通",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def jsonable(value):
    return json.loads(json.dumps(value))


def text_triple(values):
    return "".join(map(str, values))


def make_glues(first, second):
    require(tuple(first) in FIRST_TARGETS and tuple(second) in SECOND_TARGETS, "Unknown target permutation")
    return [{"source_tet": 0, "source_face": [0, 1, 2], "target_tet": 0, "target_face": list(first)},
            {"source_tet": 0, "source_face": [0, 2, 3], "target_tet": 0, "target_face": list(second)}]


def constraints(glues):
    records, _ = core.normalize(glues, tetrahedra=1)
    edge_constraints, face_constraints, orientation_equations = [], [], []
    for number, (t, f, s, g, p) in enumerate(records, 1):
        for a, b in combinations(sorted(set(range(4)) - {f}), 2):
            edge_constraints.append(((t, a, b), (s, min(p[a], p[b]), max(p[a], p[b])),
                                     1 if p[a] < p[b] else -1))
        image = [p[v] for v in range(4) if v != f]
        face_constraints.append(((t, f), (s, g), core.parity(image)))
        orientation_equations.append({"gluing_number": number, "full_permutation": [p[i] for i in range(4)],
                                      "target_tet_sign_over_source": -core.parity([p[i] for i in range(4)])})
    return records, edge_constraints, face_constraints, orientation_equations


def reversal_witness(edge_constraints):
    """An explicit signed closed walk of product -1, if one exists."""
    adjacency = defaultdict(list)
    for a, b, sign in edge_constraints:
        if a == b and sign == -1:
            return {"closed_walk": [[a, b, sign]], "sign_product": -1}
        adjacency[a].append((b, sign))
        adjacency[b].append((a, sign))
    labels, paths = {}, {}
    for start in sorted(adjacency):
        if start in labels:
            continue
        labels[start], paths[start] = 1, []
        todo = deque([start])
        while todo:
            a = todo.popleft()
            for b, sign in adjacency[a]:
                if b not in labels:
                    labels[b], paths[b] = labels[a] * sign, paths[a] + [[a, b, sign]]
                    todo.append(b)
                elif labels[b] != labels[a] * sign:
                    walk = paths[a] + [[a, b, sign]] + [[y, x, s] for x, y, s in reversed(paths[b])]
                    return {"closed_walk": walk, "sign_product": -1}
    return None


def is_sphere(link):
    return (link["connected"] and link["is_surface"] and link["orientable"]
            and link["chi"] == 2 and link["boundary_components"] == 0)


def decide(after):
    closed, connected = not after["boundary_faces"], after["connected"]
    spherical = all(is_sphere(link) for link in after["links"])
    reasons = []
    for ok, code in ((closed, "NOT_CLOSED"), (connected, "NOT_CONNECTED"),
                     (after["edge_orientation_consistent"], "REVERSED_SELF_EDGE")):
        if not ok:
            reasons.append({"code": code, "message": REASON_NAMES[code]})
    for link in after["links"]:
        if not is_sphere(link):
            reasons.append({"code": "NONSPHERICAL_VERTEX_LINK", "message": REASON_NAMES["NONSPHERICAL_VERTEX_LINK"],
                            "link_members": link["members"], "evidence": {k: link[k] for k in
                            ("V", "E", "F", "chi", "boundary_components", "connected", "is_surface", "orientable")}})
    if not after["orientable"]:
        reasons.append({"code": "AMBIENT_NONORIENTABLE", "message": REASON_NAMES["AMBIENT_NONORIENTABLE"]})
    manifold = closed and connected and after["edge_orientation_consistent"] and spherical
    return {"closed": closed, "connected": connected, "edge_orientation_consistent": after["edge_orientation_consistent"],
            "all_links_spheres": spherical, "orientable": after["orientable"],
            "manifold_accepted": manifold, "accepted": manifold and after["orientable"], "rejection_reasons": reasons}


def chain_complex(glues, after):
    """Oriented quotient cellular matrices with lexicographic local representatives."""
    require(after["edge_orientation_consistent"], "Reversed edges do not define the intended quotient cell basis")
    records, edge_constraints, face_constraints, _ = constraints(glues)
    vertices = after["vertex_classes"]
    edges = after["edge_classes"]
    faces, face_owner = core.quotient([(0, f) for f in range(4)], [(a, b) for a, b, _ in face_constraints])
    vertex_owner = {tuple(x): i for i, group in enumerate(vertices) for x in group}
    edge_owner = {tuple(x): i for i, group in enumerate(edges) for x in group}
    edge_signs, edge_ok = core.signed_labels(list(edge_owner), edge_constraints)
    face_signs, face_ok = core.signed_labels(list(face_owner), face_constraints)
    require(edge_ok and face_ok, "Inconsistent oriented cell basis")
    B1 = [[0] * len(edges) for _ in vertices]
    B2 = [[0] * len(faces) for _ in edges]
    B3 = [[0] for _ in faces]
    for j, group in enumerate(edges):
        t, a, b = group[0]
        B1[vertex_owner[t, a]][j] -= 1
        B1[vertex_owner[t, b]][j] += 1
    for j, group in enumerate(faces):
        t, f = group[0]
        a, b, c = sorted(set(range(4)) - {f})
        for x, y, sign in ((b, c, 1), (a, c, -1), (a, b, 1)):
            B2[edge_owner[t, x, y]][j] += sign * edge_signs[t, x, y]
    for f in range(4):
        B3[face_owner[0, f]][0] += (-1)**f * face_signs[0, f]
    return {"dimensions": [len(vertices), len(edges), len(faces), 1],
            "boundaries": {"1": B1, "2": B2, "3": B3},
            "bases": {"vertices": [group[0] for group in vertices], "edges": [group[0] for group in edges],
                      "faces": [group[0] for group in faces], "tetrahedra": [0]},
            "basis_convention": "Lexicographic local representatives; edge a<b, face vertices ascending, tetrahedron 0123."}


def boundary_state(stage):
    return {"boundary_faces": sorted(stage["boundary_faces"]), "Ce": core.canonical_ce(stage["Ce"]),
            "Cv": sorted(sorted(map(list, group)) for group in stage["Cv"])}


def canonical_relabeling_key(glues):
    """All 24 tetrahedron relabelings, including reversal of each face-pair direction."""
    records, _ = core.normalize(glues, tetrahedra=1)
    candidates = []
    for r in permutations(range(4)):
        inverse_r = [r.index(i) for i in range(4)]
        pairs = []
        for _, f, _, g, p in records:
            q = tuple(r[p[inverse_r[i]]] for i in range(4))
            a, b = r[f], r[g]
            if a > b:
                a, b = b, a
                q = tuple(q.index(i) for i in range(4))
            pairs.append((a, b, *q))
        candidates.append(tuple(sorted(pairs)))
    return min(candidates)


def make_case(first, second):
    started = time.perf_counter()
    glues = make_glues(first, second)
    after_first, after = (core.analyse(glues[:k], tetrahedra=1) for k in (1, 2))
    decision = decide(after)
    _, edges, _, equations = constraints(glues)
    witness = reversal_witness(edges)
    require((witness is None) == after["edge_orientation_consistent"], "Edge witness disagrees with topology")
    case = {"case_id": f"{text_triple(first)}-{text_triple(second)}", "glues": glues,
            "orientation_equations": equations, "after_first": after_first, "after": after,
            "decision": decision, "edge_reversal_witness": witness,
            "first_boundary_state": boundary_state(after_first),
            "relabeling_key": canonical_relabeling_key(glues), "chain_complex": None, "homology": None,
            "homology_status": "NOT_COMPUTED_REJECTED_TARGET"}
    if decision["accepted"]:
        chain = chain_complex(glues, after)
        homology = integral_homology(chain["boundaries"], chain["dimensions"])
        verify_homology(chain["boundaries"], chain["dimensions"], homology)
        case.update(chain_complex=chain, homology=homology, homology_status="EXACT_CERTIFICATE_VERIFIED")
    case["seconds"] = time.perf_counter() - started
    return jsonable(case)


def aggregate(cases):
    accepted = [c for c in cases if c["decision"]["accepted"]]
    reasons = Counter(code for c in cases for code in {r["code"] for r in c["decision"]["rejection_reasons"]})
    h1 = Counter(c["homology"]["groups"]["H1"]["label"] for c in accepted)
    groups = defaultdict(list)
    for case in accepted:
        groups[json.dumps(case["relabeling_key"])].append(case["case_id"])
    return {"assignments": len(cases), "accepted": len(accepted), "rejected": len(cases)-len(accepted),
            "closed": sum(c["decision"]["closed"] for c in cases),
            "connected": sum(c["decision"]["connected"] for c in cases),
            "ambient_orientable": sum(c["decision"]["orientable"] for c in cases),
            "edge_orientation_consistent": sum(c["decision"]["edge_orientation_consistent"] for c in cases),
            "manifold_accepted": sum(c["decision"]["manifold_accepted"] for c in cases),
            "rejection_case_counts_nonexclusive": dict(sorted(reasons.items())),
            "accepted_H1_counts": dict(sorted(h1.items())),
            "accepted_combinatorial_classes": sorted(groups.values()),
            "deduplication_scope": "All 24 vertex relabelings of the single tetrahedron; not homeomorphism classification."}


def compression_witnesses(cases):
    accepted = [case for case in cases if case["decision"]["accepted"]]
    witnesses = []
    for a, b in combinations(accepted, 2):
        if (a["first_boundary_state"] == b["first_boundary_state"] and a["glues"][1] == b["glues"][1]
                and a["homology"]["groups"] != b["homology"]["groups"]):
            witnesses.append({"left_case": a["case_id"], "right_case": b["case_id"],
                              "same_labeled_boundary_state": a["first_boundary_state"], "same_final_gluing": a["glues"][1],
                              "left_homology": a["homology"]["groups"], "right_homology": b["homology"]["groups"],
                              "conclusion": "Ce/Cv alone does not determine final integral homology, even for this common completion."})
    return witnesses


def boundary_inclusion_witness(cases):
    """Exact primitive H1->Z maps explain the common-completion counterexample."""
    by_id = {case["case_id"]: case for case in cases}
    records = []
    for case_id in ("130-231", "301-231"):
        case = by_id[case_id]
        stage = case["after_first"]
        chain = chain_complex(case["glues"][:1], stage)
        homology = integral_homology(chain["boundaries"], chain["dimensions"])
        require(homology["groups"]["H1"]["label"] == "Z", "Partial H1 must be infinite cyclic")
        require(not any(x for row in chain["boundaries"]["1"] for x in row), "Expected a one-vertex partial complex")
        B2 = chain["boundaries"]["2"]
        transpose = [list(row) for row in zip(*B2)]
        smith = smith_normal_form(transpose, len(B2))
        require(len(B2) - smith["rank"] == 1, "Expected one primitive cohomology generator")
        w = [row[-1] for row in smith["V"]]
        _, edge_constraints, _, _ = constraints(case["glues"][:1])
        edges = stage["edge_classes"]
        owner = {tuple(edge): i for i, group in enumerate(edges) for edge in group}
        signs, _ = core.signed_labels(list(owner), edge_constraints)
        def vector(a, b):
            sign = 1 if a < b else -1
            edge = (0, min(a,b), max(a,b))
            result = [0] * len(edges)
            result[owner[edge]] = sign * signs[edge]
            return result
        vectors = {name: vector(a,b) for name,(a,b) in
                   {"x_03":(0,3),"y_13":(1,3),"z_23":(2,3),"edge_02":(0,2)}.items()}
        values = {name:sum(a*b for a,b in zip(w,v)) for name,v in vectors.items()}
        if values["y_13"] < 0:
            w = [-x for x in w]
            values = {name:-value for name,value in values.items()}
        require(values["z_23"] == values["x_03"] + values["y_13"], "Boundary triangle relation failed")
        require(values["edge_02"] == -values["y_13"], "Ce boundary edge relation failed")
        # Common last map 023->231 identifies edge 02 with edge 23.
        relation = [a-b for a,b in zip(vectors["z_23"], vectors["edge_02"])]
        killing = sum(a*b for a,b in zip(w,relation))
        require(killing == values["x_03"] + 2*values["y_13"], "Closing relation failed")
        require(case["homology"]["groups"]["H1"]["torsion"] == [abs(killing)], "Closing torsion mismatch")
        records.append({"case_id":case_id,"partial_chain_complex":chain,"partial_homology":homology,
                        "functional_smith_certificate":smith,"primitive_functional_on_edge_basis":w,
                        "boundary_cycle_vectors":vectors,"boundary_inclusion_to_Z":values,
                        "closing_relation_in_edge_basis":relation,"closing_relation_value":killing})
    require(by_id["130-231"]["first_boundary_state"] == by_id["301-231"]["first_boundary_state"], "Boundary states differ")
    return {"left_case":"130-231","right_case":"301-231",
            "common_boundary_state":by_id["130-231"]["first_boundary_state"],
            "common_completion":by_id["130-231"]["glues"][1],"records":records,
            "boundary_notation":"x=[03], y=[13], z=[23]=x+y; Ce gives [02]=-y and [12]=-x.",
            "closing_relation":"023->231 imposes [02]=[23], hence x+2y=0.",
            "scope":"A finite witness of homology forgotten by Ce/Cv, consistent with legality-only boundary states; no global identification of the partial spaces required."}


def link_text(link):
    kind = "S2" if is_sphere(link) else ("Klein bottle" if link["is_surface"] and not link["orientable"] and link["chi"] == 0 and not link["boundary_components"] else "non-sphere")
    return f"{kind}[{link['V']},{link['E']},{link['F']};chi={link['chi']}]"


def render_table(cases, counts):
    lines = ["# 單四面體 36 種完整貼合：逐案結果", "", "固定 012↔perm(013)、023↔perm(123)。每個 ID 的兩段就是兩個目標頂點三元組；對應依序讀取，不是排序後再貼合。", "",
             f"共 {counts['assignments']} 案：{counts['accepted']} 案通過閉、連通、可定向三維流形判準，{counts['rejected']} 案拒絕。所有 36 案皆完整配對且連通。", "",
             "| 案例 | 全排列 p₁／p₂ | link：V,E,F；χ | 整體可定向 | 邊方向一致 | 判定／原因 | H₁(Z) |",
             "|---|---|---|---|---|---|---|"]
    for case in cases:
        d = case["decision"]
        p = " / ".join(text_triple(e["full_permutation"]) for e in case["orientation_equations"])
        links = "; ".join(link_text(link) for link in case["after"]["links"])
        verdict = "通過" if d["accepted"] else "、".join(REASON_NAMES[code] for code in sorted({r["code"] for r in d["rejection_reasons"]}))
        h1 = case["homology"]["groups"]["H1"]["label"] if case["homology"] else "—"
        lines.append(f"| {case['case_id']} | {p} | {links} | {'是' if d['orientable'] else '否'} | {'是' if d['edge_orientation_consistent'] else '否'} | {verdict} | {h1} |")
    lines += ["", "全排列 p 按 p(0)p(1)p(2)p(3) 記錄；省略的頂點也映到另一面的省略頂點。link 的球面判定另檢查連通、局部曲面、可定向與無邊界，沒有只看 Euler characteristic。",
              "", "## 通過者的整數同調", "", "| 案例 | f₀,f₁,f₂,f₃ | H₀ | H₁ | H₂ | H₃ |", "|---|---|---|---|---|---|"]
    for case in cases:
        if case["homology"]:
            groups = case["homology"]["groups"]
            labels = " | ".join(groups[f"H{k}"]["label"] for k in range(4))
            lines.append(f"| {case['case_id']} | {','.join(map(str,case['chain_complex']['dimensions']))} | {labels} |")
    lines += ["", f"整數同調 H₁ 分布（保留標記案）：{json.dumps(counts['accepted_H1_counts'],ensure_ascii=False)}。",
              f"24 種四面體頂點重標號後，通過者有 {len(counts['accepted_combinatorial_classes'])} 個組合類：", ""]
    lines += ["- " + ", ".join(group) for group in counts["accepted_combinatorial_classes"]]
    lines += ["", "上述去重只判斷四面體貼合資料的組合同構。不同組合類可能同胚；同調相同也不能據此判為同胚。未對這些案例自動命名為球面或 lens space。拒絕案未計算目標流形的整數同調。",
              "", "拒絕原因可重疊，不應相加當成拒絕案總數：" + json.dumps(counts["rejection_case_counts_nonexclusive"],ensure_ascii=False),
              "", "逐案完整資料位於 cases/<ID>.json，包含第一次貼合、Ce/Cv、完整 links、局部頂點檢查、方向方程、反向邊證據，以及通過者的邊界矩陣和整數 Smith 證書。"]
    return "\n".join(lines) + "\n"


def write_csv(path, cases):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["case_id", "first_target", "second_target", "full_permutation_1", "full_permutation_2", "closed", "connected", "ambient_orientable", "edge_orientation_consistent", "links", "accepted", "rejection_codes", "H0", "H1", "H2", "H3", "seconds"])
        for case in cases:
            d = case["decision"]
            h = case["homology"]["groups"] if case["homology"] else {}
            writer.writerow([case["case_id"], *case["case_id"].split("-"),
                *(text_triple(e["full_permutation"]) for e in case["orientation_equations"]),
                d["closed"],d["connected"],d["orientable"],d["edge_orientation_consistent"],
                "; ".join(link_text(l) for l in case["after"]["links"]),d["accepted"],
                ";".join(sorted({r["code"] for r in d["rejection_reasons"]})),
                *(h[f"H{k}"]["label"] if h else "NOT_COMPUTED_REJECTED_TARGET" for k in range(4)),case["seconds"]])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=REPORT)
    args = parser.parse_args()
    started = time.perf_counter()
    run = args.output / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    (run / "cases").mkdir(parents=True, exist_ok=False)
    cases = []
    for first, second in product(FIRST_TARGETS, SECOND_TARGETS):
        case = make_case(first, second)
        (run / "cases" / f"{case['case_id']}.json").write_text(json.dumps(case,ensure_ascii=False,indent=2),encoding="utf-8")
        cases.append(case)
    counts = aggregate(cases)
    report = {"schema_version": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Complete 36 labeled assignments of fixed single-tetrahedron face pairs; no homeomorphism recognition or general FPT claim.",
        "fixed_pairs": [["t0:012","t0:013"],["t0:023","t0:123"]],
        "target": "Closed connected orientable triangulated 3-manifold, integral homology over Z.",
        "source_sha256": {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (Path(__file__),Path(core.__file__),Path(__file__).with_name("integer_homology.py"))},
        "before": core.analyse([],tetrahedra=1), "cases": cases, "counts": counts,
        "compression_witnesses": compression_witnesses(cases),
        "boundary_inclusion_witness": boundary_inclusion_witness(cases), "build_seconds": time.perf_counter()-started}
    (run / "results.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    (run / "compression-witnesses.json").write_text(json.dumps(report["compression_witnesses"],ensure_ascii=False,indent=2),encoding="utf-8")
    (run / "boundary-inclusion-witness.json").write_text(json.dumps(report["boundary_inclusion_witness"],ensure_ascii=False,indent=2),encoding="utf-8")
    table = render_table(cases, counts)
    (run / "results-table.md").write_text(table,encoding="utf-8")
    write_csv(run / "results-table.csv", cases)
    from verify_one_tetrahedron import verify_run
    verification = verify_run(run)
    require(verification["status"] == "PASS", "Independent verification failed")
    args.report_output.mkdir(parents=True,exist_ok=True)
    for name in ("results-table.md", "results-table.csv", "compression-witnesses.json", "boundary-inclusion-witness.json"):
        (args.report_output / name).write_bytes((run / name).read_bytes())
    latest = {"run_directory":str(run.resolve()),"status":"PASS","counts":counts,
              "results_sha256":hashlib.sha256((run / "results.json").read_bytes()).hexdigest()}
    (args.report_output / "latest-run.json").write_text(json.dumps(latest,ensure_ascii=False,indent=2),encoding="utf-8")
    print(run)
    print(json.dumps(counts,ensure_ascii=True))


if __name__ == "__main__":
    main()
