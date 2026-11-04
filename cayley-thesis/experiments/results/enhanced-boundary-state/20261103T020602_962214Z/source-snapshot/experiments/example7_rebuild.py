"""Exact combinatorial reconstruction of Example 7 (standard library only).

Keep the literal v2 input separate from the figure/table-consistent inference.
Use equivalence graphs, triangle links, local port graphs and signed constraints.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict, deque
from itertools import combinations
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports/week1-example7-demo"
SOURCE_URL = "https://arxiv.org/pdf/1402.3876v2"

FIRST = {"source_tet": 0, "source_face": [0, 1, 2],
         "target_tet": 1, "target_face": [0, 1, 2]}
SECOND_LITERAL = {"source_tet": 1, "source_face": [0, 2, 3],
                  "target_tet": 1, "target_face": [3, 2, 1]}
SECOND_INFERRED = {**SECOND_LITERAL, "source_tet": 0}
EXPECTED_CV = [[[0, 0], [1, 0], [1, 3]], [[0, 1], [0, 3], [1, 1]], [[0, 2], [1, 2]]]
EXPECTED_CE = [
    ["t0:013/03", "t1:013/13", False],
    ["t0:013/01", "t1:013/01", True],
    ["t0:013/13", "t0:123/13", True],
    ["t0:123/12", "t0:123/23", False],
    ["t1:013/03", "t1:023/03", True],
    ["t1:023/02", "t1:023/23", False],
]


def quotient(items, relations):
    """Connected components give equivalence closure; no union-find dependency."""
    adjacency = {item: set() for item in items}
    for a, b in relations:
        adjacency[a].add(b)
        adjacency[b].add(a)
    unseen = set(items)
    groups = []
    while unseen:
        start = min(unseen)
        seen = {start}
        queue = deque([start])
        while queue:
            for nxt in adjacency[queue.popleft()]:
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        groups.append(sorted(seen))
        unseen -= seen
    groups.sort()
    owner = {item: index for index, group in enumerate(groups) for item in group}
    return groups, owner


def signed_labels(items, constraints):
    adjacency = {item: [] for item in items}
    for a, b, sign in constraints:
        adjacency[a].append((b, sign))
        adjacency[b].append((a, sign))
    values = {}
    consistent = True
    for start in sorted(items):
        if start in values:
            continue
        values[start] = 1
        queue = deque([start])
        while queue:
            a = queue.popleft()
            for b, sign in adjacency[a]:
                desired = values[a] * sign
                if b in values:
                    consistent &= values[b] == desired
                else:
                    values[b] = desired
                    queue.append(b)
    return values, consistent


def parity(permutation):
    return (-1) ** sum(a > b for i, a in enumerate(permutation) for b in permutation[i + 1:])


def normalize(glues, tetrahedra=2):
    paired = set()
    records = []
    for glue in glues:
        t, s = glue["source_tet"], glue["target_tet"]
        a, b = glue["source_face"], glue["target_face"]
        if not 0 <= t < tetrahedra or not 0 <= s < tetrahedra:
            raise ValueError("Unknown tetrahedron")
        if len(a) != 3 or len(set(a)) != 3 or len(b) != 3 or len(set(b)) != 3 or not set(a + b) <= set(range(4)):
            raise ValueError("Face map must biject two triples of distinct vertices")
        f, g = next(iter(set(range(4)) - set(a))), next(iter(set(range(4)) - set(b)))
        if (t, f) == (s, g) or (t, f) in paired or (s, g) in paired:
            raise ValueError("Each face can be paired only once, with a distinct face")
        paired.update(((t, f), (s, g)))
        p = dict(zip(a, b))
        p[f] = g
        records.append((t, f, s, g, p))
    return records, paired


def analyse(glues, tetrahedra=2):
    records, paired = normalize(glues, tetrahedra)
    vertices = [(t, v) for t in range(tetrahedra) for v in range(4)]
    corners = [(t, v, w) for t, v in vertices for w in range(4) if w != v]
    sides = [(t, v, f) for t, v in vertices for f in range(4) if f != v]
    ports = [(t, v, w, f) for t, v, w in corners for f in range(4) if f not in (v, w)]
    edges = [(t, a, b) for t in range(tetrahedra) for a, b in combinations(range(4), 2)]
    vrelations, crelations, srelations, prelations, erelations = [], [], [], [], []
    link_orientations, edge_orientations, tet_orientations = [], [], []
    link_side_gluings = []
    for t, f, s, g, p in records:
        tet_orientations.append((t, s, -parity([p[i] for i in range(4)])))
        face = [v for v in range(4) if v != f]
        for v in face:
            vrelations.append(((t, v), (s, p[v])))
            srelations.append(((t, v, f), (s, p[v], g)))
            others = sorted(set(range(4)) - {v})
            target_others = sorted(set(range(4)) - {p[v]})
            i, j = others.index(f), target_others.index(g)
            oriented = [others[(i + 1) % 3], others[(i + 2) % 3]]
            target_oriented = [target_others[(j + 1) % 3], target_others[(j + 2) % 3]]
            mapped = [p[w] for w in oriented]
            sign = -1 if mapped == target_oriented else 1
            link_orientations.append(((t, v), (s, p[v]), sign))
            link_side_gluings.append({"source_triangle": [t, v], "source_side_opposite": f,
                "target_triangle": [s, p[v]], "target_side_opposite": g,
                "corner_map": [[w, p[w]] for w in face if w != v]})
            for w in face:
                if w != v:
                    crelations.append(((t, v, w), (s, p[v], p[w])))
                    prelations.append(((t, v, w, f), (s, p[v], p[w], g)))
        for a, b in combinations(face, 2):
            target = (s, min(p[a], p[b]), max(p[a], p[b]))
            erelations.append(((t, a, b), target))
            edge_orientations.append(((t, a, b), target, 1 if p[a] < p[b] else -1))
    vertex_groups, vertex_owner = quotient(vertices, vrelations)
    corner_groups, corner_owner = quotient(corners, crelations)
    side_groups, side_owner = quotient(sides, srelations)
    _, port_owner = quotient(ports, prelations)
    edge_groups, edge_owner = quotient(edges, erelations)
    edge_signs, edges_consistent = signed_labels(edges, edge_orientations)
    _, orientable = signed_labels(list(range(tetrahedra)), tet_orientations)
    boundary_faces = [(t, f) for t in range(tetrahedra) for f in range(4) if (t, f) not in paired]
    links = []
    for members in vertex_groups:
        member_set = set(members)
        used_corners = {corner_owner[t, v, w] for t, v in members for w in range(4) if w != v}
        used_sides = {side_owner[t, v, f] for t, v in members for f in range(4) if f != v}
        link_connections = [(a[:2], b[:2]) for a, b in srelations if a[:2] in member_set]
        triangles_connected = len(quotient(members, link_connections)[0]) == 1
        constraints = [(a, b, sign) for a, b, sign in link_orientations if a in member_set]
        _, link_orientable = signed_labels(members, constraints)
        incidence = Counter(side_owner[t, v, f] for t, v in members for f in range(4) if f != v)
        boundary_edges = []
        for t, v in members:
            for f in range(4):
                if f != v and (t, f) not in paired:
                    endpoints = sorted(set(range(4)) - {v, f})
                    boundary_edges.append({"side": [t, v, f],
                        "ends": [corner_owner[t, v, w] for w in endpoints]})
        boundary_vertices = {end for edge in boundary_edges for end in edge["ends"]}
        boundary_groups, boundary_owner = quotient(boundary_vertices, [e["ends"] for e in boundary_edges])
        degree = Counter(end for edge in boundary_edges for end in edge["ends"])
        boundary_circles = all(d == 2 for d in degree.values())
        local_checks = []
        for corner_class in sorted(used_corners):
            intervals = []
            for t, v, w in corner_groups[corner_class]:
                endpoints = [port_owner[t, v, w, f] for f in range(4) if f not in (v, w)]
                intervals.append(endpoints)
            local_vertices = {x for interval in intervals for x in interval}
            local_groups = quotient(local_vertices, intervals)[0]
            degrees = Counter(x for interval in intervals for x in interval)
            is_circle = bool(degrees) and all(d == 2 for d in degrees.values())
            is_interval = list(degrees.values()).count(1) == 2 and all(d in (1, 2) for d in degrees.values())
            valid = len(local_groups) == 1 and (is_circle or is_interval)
            local_checks.append({"corner_class": corner_class, "connected": len(local_groups) == 1,
                                 "degrees": sorted(degrees.values()), "valid": valid})
        surface = triangles_connected and boundary_circles and all(n in (1, 2) for n in incidence.values()) and all(c["valid"] for c in local_checks)
        V, E, F = len(used_corners), len(used_sides), len(members)
        chi, b = V - E + F, len(boundary_groups)
        genus = (2 - b - chi) // 2 if surface and link_orientable and 2 - b - chi >= 0 and (2 - b - chi) % 2 == 0 else None
        kind = {0: "sphere", 1: "disk", 2: "annulus"}.get(b, "punctured_sphere") if genus == 0 else "other"
        if surface and not link_orientable and chi == 0 and b == 1:
            kind = "mobius_band"
        links.append({"members": members, "V": V, "E": E, "F": F, "chi": chi,
            "boundary_components": b, "genus": genus, "type": kind, "connected": triangles_connected,
            "orientable": link_orientable, "is_surface": surface, "corner_classes": sorted(used_corners),
            "side_classes": sorted(used_sides), "local_vertex_checks": local_checks,
            "boundary_cycles": [{"corners": group, "sides": [e["side"] for e in boundary_edges
                                if boundary_owner[e["ends"][0]] == k]} for k, group in enumerate(boundary_groups)]})
    occurrences = defaultdict(list)
    for t, f in boundary_faces:
        for a, b in combinations([v for v in range(4) if v != f], 2):
            occurrences[edge_owner[t, a, b]].append((t, f, a, b))
    Ce = []
    for group in occurrences.values():
        if len(group) != 2:
            raise ValueError("Boundary edge does not have two boundary-face occurrences")
        x, y = sorted(group)
        def name(occ):
            t, f, a, b = occ
            return f"t{t}:" + "".join(str(v) for v in range(4) if v != f) + f"/{a}{b}"
        Ce.append([name(x), name(y), edge_signs[x[0], x[2], x[3]] == edge_signs[y[0], y[2], y[3]]])
    boundary_vertices = {(t, v) for t, f in boundary_faces for v in range(4) if v != f}
    Cv = [[v for v in group if v in boundary_vertices] for group in vertex_groups if any(v in boundary_vertices for v in group)]
    partial = edges_consistent and all(link["is_surface"] and link["genus"] == 0 for link in links)
    tet_components = quotient(list(range(tetrahedra)), [(t, s) for t, _, s, _, _ in records])[0]
    return {"glues": glues, "vertex_classes": vertex_groups,
            "boundary_faces": [f"t{t}:" + "".join(str(v) for v in range(4) if v != f) for t, f in boundary_faces],
            "edge_classes": edge_groups, "corner_classes": corner_groups, "side_classes": side_groups,
            "link_side_gluings": link_side_gluings, "links": links,
            "Ce": sorted(Ce), "Cv": Cv, "edge_orientation_consistent": edges_consistent,
            "orientable": orientable, "connected": len(tet_components) == 1,
            "partial_3_manifold_definition5": partial,
            "manifold_with_boundary_link_test": edges_consistent and all(link["is_surface"] and link["type"] in ("sphere", "disk") for link in links)}


def canonical_ce(rows):
    return sorted([*sorted(row[:2]), row[2]] for row in rows)


def build():
    inferred = [analyse([]), analyse([FIRST]), analyse([FIRST, SECOND_INFERRED])]
    literal = analyse([FIRST, SECOND_LITERAL])
    final = inferred[-1]
    # These expectations are checked against calculated equivalence closure, not assigned.
    assert final["vertex_classes"] == [list(map(tuple, group)) for group in EXPECTED_CV]
    assert canonical_ce(final["Ce"]) == canonical_ce(EXPECTED_CE)
    assert sorted(final["boundary_faces"]) == ["t0:013", "t0:123", "t1:013", "t1:023"]
    assert [link["type"] for link in final["links"]] == ["disk", "disk", "annulus"]
    assert final["partial_3_manifold_definition5"] and not final["manifold_with_boundary_link_test"]
    assert literal["vertex_classes"] != final["vertex_classes"]
    apex = next(link for link in final["links"] if link["type"] == "annulus")
    assert (apex["V"], apex["E"], apex["F"], apex["chi"], apex["boundary_components"]) == (2, 4, 2, 0, 2)
    return {"source": SOURCE_URL, "source_sections": ["Example 7, Figure 2 (page 5)", "Definition 8 (pages 5-6)", "Definition 5 (page 4)"],
            "provenance": "Literal v2 text and table-consistent inference are separate; no official erratum claimed.",
            "inferred_stages": inferred, "literal_final": literal,
            "checks": {"matches_published_Ce": True, "matches_published_Cv": True,
                       "literal_matches_published_Ce": canonical_ce(literal["Ce"]) == canonical_ce(EXPECTED_CE),
                       "literal_matches_published_Cv": literal["Cv"] == final["Cv"]},
            "apex_strip": {"triangles": {"t0:2": {"0": [0, 0], "1": [4, 2], "3": [0, 2]},
                                         "t1:2": {"0": [0, 0], "1": [4, 2], "3": [4, 0]}},
                           "first_glue": "diagonal 01 to 01", "second_glue": "left 03 to right 31, bottom-to-bottom and top-to-top",
                           "boundary_cycles": ["top: t0:123", "bottom: t1:023"]},
            "source_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def cross_check(data):
    path = ROOT / "reports/examples/fixed_graph_lens17.py"
    spec = importlib.util.spec_from_file_location("existing_lens_verifier", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    results = []
    cases = [("inferred", stage) for stage in data["inferred_stages"]] + [("literal", data["literal_final"])]
    for name, stage in cases:
        records, _ = normalize(stage["glues"])
        other = module.analyse(2, [(t, f, s, tuple(p[i] for i in range(4))) for t, f, s, g, p in records])
        actual = sorted((sorted(map(tuple, link["members"])), link["V"], link["E"], link["F"], link["chi"], link["boundary_components"], link["is_surface"]) for link in stage["links"])
        expected = sorted((sorted(map(tuple, link["corners"])), link["V"], link["E"], link["F"], link["chi"], link["boundary_components"], bool(link["is_surface"])) for link in other["links"])
        assert actual == expected
        assert stage["edge_orientation_consistent"] == bool(other["edge_orientation_consistent"])
        assert stage["orientable"] == bool(other["orientable"])
        assert stage["Cv"] == other["boundary_state"]["Cv"]
        def old_occurrence(occ):
            t, f, a, b = occ
            return f"t{t}:" + "".join(str(v) for v in range(4) if v != f) + f"/{a}{b}"
        other_ce = [[old_occurrence(a), old_occurrence(b), same] for a, b, same in other["boundary_state"]["Ce"]]
        assert canonical_ce(stage["Ce"]) == canonical_ce(other_ce)
        results.append({"variant": name, "glue_count": len(stage["glues"]), "status": "PASS"})
    return {"status": "PASS", "independent_implementation": str(path.relative_to(ROOT)),
            "implementation_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "cases": results,
            "scope": "links V/E/F/chi/boundary counts/local surface, Ce/Cv, edge consistency and orientation; not a Lean proof"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--cross-check", action="store_true", help="Also use existing NumPy implementation")
    args = parser.parse_args()
    data = build()
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "input-literal-v2.json").write_text(json.dumps({"source": SOURCE_URL,
        "status": "literal transcription of the two gluing instructions", "glues": [FIRST, SECOND_LITERAL]}, indent=2), encoding="utf-8")
    (args.output / "input-figure-consistent-inferred.json").write_text(json.dumps({"source": SOURCE_URL,
        "status": "inference matching published Ce/Cv; NOT an official erratum", "glues": [FIRST, SECOND_INFERRED]}, indent=2), encoding="utf-8")
    (args.output / "example7_data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.cross_check:
        (args.output / "cross-check.json").write_text(json.dumps(cross_check(data), ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# Example 7：程式產生的重建表", "", "原文照字面與圖表一致推定版分開保存；後者不是作者官方勘誤。", "",
             "| 階段 | 頂點類數 | 邊界面數 | link 類型 |", "|---|---:|---:|---|"]
    for i, stage in enumerate(data["inferred_stages"]):
        lines.append(f"| 推定版 {i} 次貼合 | {len(stage['vertex_classes'])} | {len(stage['boundary_faces'])} | " + ", ".join(link["type"] for link in stage["links"]) + " |")
    literal = data["literal_final"]
    lines.append(f"| 原文照字面 2 次貼合 | {len(literal['vertex_classes'])} | {len(literal['boundary_faces'])} | " + ", ".join(link["type"] for link in literal["links"]) + " |")
    lines += ["", "## 推定版最終 links", "", "| 頂點類 | V | E | F | χ | 邊界圈 b | 可定向／曲面 | 類型 |", "|---|---:|---:|---:|---:|---:|---|---|"]
    for link in data["inferred_stages"][-1]["links"]:
        members = ", ".join(f"t{t}:{v}" for t, v in link["members"])
        lines.append(f"| {members} | {link['V']} | {link['E']} | {link['F']} | {link['chi']} | {link['boundary_components']} | {link['orientable']}/{link['is_surface']} | {link['type']} |")
    lines += ["", "## 六筆 Ce（方向以局部頂點編號小到大為準）", "", "| 邊界面／邊 | 邊界面／邊 | 同方向？ |", "|---|---|---|"]
    for a, b, sign in data["inferred_stages"][-1]["Ce"]:
        lines.append(f"| {a} | {b} | {sign} |")
    lines += ["", "## 原文照字面版完整頂點等價類", "", repr(literal["vertex_classes"]),
              "", "## 原文照字面版 Cv（只保留出現在邊界面的局部頂點標記）", "", repr(literal["Cv"]),
              "", "原文照字面版邊界面：" + ", ".join(literal["boundary_faces"]), "",
              "## 不變量之外的檢查", "", "每個 link 另檢查三角形連通、邊入射數、每個頂點的局部 interval/circle、可定向性與邊界圈。不能只憑 χ=0 判環帶。"]
    (args.output / "computed-tables.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(args.output)
    print("PASS: inferred input matches Ce/Cv; literal input differs; all local-link checks completed")
    print([(link["members"], link["V"], link["E"], link["F"], link["type"]) for link in data["inferred_stages"][-1]["links"]])


if __name__ == "__main__":
    main()
