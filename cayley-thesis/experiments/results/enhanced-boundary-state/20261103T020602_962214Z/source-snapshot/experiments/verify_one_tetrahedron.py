"""Independent checks for a persisted fixed-pairing one-tetrahedron census.

This module does not import the census, Example 7 oracle, or homology calculator.
It uses signed union-find, oriented simplex boundary formulae, and exact minors.
The scope is finite combinatorial verification, not manifold recognition or Lean.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from itertools import combinations, permutations, product
from math import gcd
from pathlib import Path
import csv
import hashlib
import json


def require(condition, message):
    if not condition:
        raise ValueError(message)


def parity(sequence):
    return -1 if sum(a > b for i, a in enumerate(sequence) for b in sequence[i + 1:]) % 2 else 1


class SignedUnion:
    """Canonical roots; find(x) returns x = sign * root."""

    def __init__(self, items):
        self.parent = {x: x for x in items}
        self.sign = {x: 1 for x in items}
        self.valid = True

    def find(self, x):
        if self.parent[x] == x:
            return x, 1
        root, sign = self.find(self.parent[x])
        self.sign[x] *= sign
        self.parent[x] = root
        return root, self.sign[x]

    def join(self, a, b, sign=1):
        ra, sa = self.find(a)
        rb, sb = self.find(b)
        if ra == rb:
            self.valid = self.valid and sa == sign * sb
        elif ra < rb:
            self.parent[rb] = ra
            self.sign[rb] = sa * sign * sb
        else:
            self.parent[ra] = rb
            self.sign[ra] = sa * sign * sb

    def groups(self):
        groups = defaultdict(list)
        for x in self.parent:
            groups[self.find(x)[0]].append(x)
        return sorted(sorted(group) for group in groups.values())


def normalize(glues):
    """Validate the exact fixed face-pairing scheme independently."""
    require(len(glues) in (1, 2), "Expected one or two face pairings")
    expected_sources = [(0, 1, 2), (0, 2, 3)]
    expected_targets = [{0, 1, 3}, {1, 2, 3}]
    records = []
    used = set()
    for i, glue in enumerate(glues):
        require(glue["source_tet"] == glue["target_tet"] == 0, "Only t0 is allowed")
        a, b = tuple(glue["source_face"]), tuple(glue["target_face"])
        require(a == expected_sources[i] and set(b) == expected_targets[i] and len(b) == 3,
                "Unexpected fixed face pair or non-bijective target")
        f, g = ({0, 1, 2, 3} - set(a)).pop(), ({0, 1, 2, 3} - set(b)).pop()
        require(f not in used and g not in used and f != g, "Repeated face")
        used.update((f, g))
        p = dict(zip(a, b))
        p[f] = g
        records.append((f, g, p))
    return records


def independent_topology(glues):
    """Reconstruct a one-tetrahedron quotient and every local link condition."""
    records = normalize(glues)
    verts = SignedUnion(range(4))
    edges = SignedUnion(combinations(range(4), 2))
    faces = SignedUnion(range(4))
    corners = SignedUnion((v, w) for v in range(4) for w in range(4) if v != w)
    sides = SignedUnion((v, f) for v in range(4) for f in range(4) if v != f)
    ports = SignedUnion((v, w, f) for v in range(4) for w in range(4)
                        if v != w for f in range(4) if f not in (v, w))
    constraints = []
    ambient_orientable = True
    used_faces = set()
    for f, g, p in records:
        used_faces.update((f, g))
        ambient_orientable &= parity([p[i] for i in range(4)]) == -1
        source = [v for v in range(4) if v != f]
        faces.join(f, g, parity([p[v] for v in source]))
        for a, b in combinations(source, 2):
            pa, pb = p[a], p[b]
            edges.join((a, b), tuple(sorted((pa, pb))), 1 if pa < pb else -1)
        for v in source:
            target_v = p[v]
            verts.join(v, target_v)
            sides.join((v, f), (target_v, g))
            order = [w for w in range(4) if w != v]
            target_order = [w for w in range(4) if w != target_v]
            source_edge = [w for w in order if w != f]
            # Boundary([a,b,c]) = [b,c]-[a,c]+[a,b].
            relation = -((-1) ** (order.index(f) + target_order.index(g))) * parity([p[w] for w in source_edge])
            constraints.append((v, target_v, relation))
            for w in source:
                if w != v:
                    corners.join((v, w), (target_v, p[w]))
                    ports.join((v, w, f), (target_v, p[w], g))
    vertex_groups = verts.groups()
    corner_groups = corners.groups()
    boundary_faces = [f for f in range(4) if f not in used_faces]
    link_data = []
    for group in vertex_groups:
        cv = {corners.find((v, w))[0] for v in group for w in range(4) if w != v}
        se = {sides.find((v, f))[0] for v in group for f in range(4) if f != v}
        incidence = Counter(sides.find((v, f))[0] for v in group for f in range(4) if f != v)
        orientations = SignedUnion(group)
        triangles = SignedUnion(group)
        for a, b, sign in constraints:
            if a in group:
                orientations.join(a, b, sign)
                triangles.join(a, b)
        boundary_edges = []
        for v in group:
            for f in boundary_faces:
                if f != v:
                    boundary_edges.append([corners.find((v, w))[0] for w in range(4) if w not in (v, f)])
        boundary_nodes = {x for e in boundary_edges for x in e}
        boundary = SignedUnion(boundary_nodes)
        boundary_degrees = Counter()
        for a, b in boundary_edges:
            boundary.join(a, b)
            boundary_degrees[a] += 1
            boundary_degrees[b] += 1
        boundary_count = len(boundary.groups())
        local_checks = []
        for corner_group in corner_groups:
            if corner_group[0][0] not in group:
                continue
            intervals = []
            for v, w in corner_group:
                intervals.append([ports.find((v, w, f))[0] for f in range(4) if f not in (v, w)])
            nodes = {node for interval in intervals for node in interval}
            local = SignedUnion(nodes)
            degrees = Counter()
            for a, b in intervals:
                local.join(a, b)
                degrees[a] += 1
                degrees[b] += 1
            connected = len(local.groups()) == 1
            ds = list(degrees.values())
            circle = bool(ds) and all(d == 2 for d in ds)
            interval = ds.count(1) == 2 and all(d in (1, 2) for d in ds)
            valid = connected and (circle or interval)
            local_checks.append({"members": corner_group, "connected": connected,
                                 "degrees": sorted(degrees.values()), "valid": valid})
        connected = len(triangles.groups()) == 1
        surface = connected and all(n in (1, 2) for n in incidence.values()) and all(x["valid"] for x in local_checks) and all(d == 2 for d in boundary_degrees.values())
        V, E, F = len(cv), len(se), len(group)
        chi = V - E + F
        sphere = surface and orientations.valid and chi == 2 and boundary_count == 0
        link_data.append({"members": [[0, v] for v in group], "V": V, "E": E, "F": F, "chi": chi,
                          "boundary_components": boundary_count, "connected": connected,
                          "orientable": orientations.valid, "is_surface": surface,
                          "sphere": sphere, "local_vertex_checks": local_checks})
    all_spheres = all(link["sphere"] for link in link_data)
    manifold = edges.valid and all_spheres and not boundary_faces
    edge_occurrences = defaultdict(list)
    for f in boundary_faces:
        for a, b in combinations([v for v in range(4) if v != f], 2):
            root, sign = edges.find((a, b))
            edge_occurrences[root].append((f, a, b, sign))
    Ce = []
    for occurrences in edge_occurrences.values():
        require(len(occurrences) == 2, "Boundary edge has wrong number of occurrences")
        x, y = sorted(occurrences)
        def name(occ):
            f, a, b, _ = occ
            return "t0:" + "".join(str(v) for v in range(4) if v != f) + f"/{a}{b}"
        Ce.append([name(x), name(y), x[3] == y[3]])
    boundary_vertices = {v for f in boundary_faces for v in range(4) if v != f}
    Cv = [[[0, v] for v in group if v in boundary_vertices] for group in vertex_groups if set(group) & boundary_vertices]
    result = {"vertex_classes": [[[0, v] for v in group] for group in vertex_groups],
              "edge_classes": [[[0, a, b] for a, b in group] for group in edges.groups()],
              "closed": not boundary_faces, "connected": True, "orientable": bool(ambient_orientable),
              "edge_orientation_consistent": edges.valid, "links": link_data,
              "all_links_spheres": all_spheres, "manifold_accepted": manifold,
              "accepted": manifold and bool(ambient_orientable), "Ce": sorted(Ce), "Cv": Cv,
              "boundary_faces": ["t0:" + "".join(str(v) for v in range(4) if v != f) for f in boundary_faces]}
    reasons = []
    if not edges.valid:
        reasons.append(("REVERSED_SELF_EDGE", None))
    reasons.extend(("NONSPHERICAL_VERTEX_LINK", link["members"]) for link in link_data if not link["sphere"])
    if not ambient_orientable:
        reasons.append(("AMBIENT_NONORIENTABLE", None))
    if boundary_faces:
        reasons.insert(0, ("NOT_CLOSED", None))
    result["reasons"] = reasons
    if result["edge_orientation_consistent"]:
        vr, er, fr = [group[0] for group in vertex_groups], [group[0] for group in edges.groups()], [group[0] for group in faces.groups()]
        vi, ei, fi = ({v: i for i, v in enumerate(items)} for items in (vr, er, fr))
        B1 = [[0] * len(er) for _ in vr]
        B2 = [[0] * len(fr) for _ in er]
        B3 = [[0] for _ in fr]
        for j, (a, b) in enumerate(er):
            B1[vi[verts.find(a)[0]]][j] -= 1
            B1[vi[verts.find(b)[0]]][j] += 1
        for j, f in enumerate(fr):
            a, b, c = [v for v in range(4) if v != f]
            for x, y, coefficient in [(b, c, 1), (a, c, -1), (a, b, 1)]:
                r, sign = edges.find((x, y))
                B2[ei[r]][j] += coefficient * sign
        for f in range(4):
            r, sign = faces.find(f)
            B3[fi[r]][0] += ((-1) ** f) * sign
        result["chain_complex"] = {"dimensions": [len(vr), len(er), len(fr), 1],
                                   "boundaries": {"1": B1, "2": B2, "3": B3},
                                   "bases": {"vertices": [[0, v] for v in vr], "edges": [[0, a, b] for a, b in er],
                                             "faces": [[0, f] for f in fr], "tetrahedra": [0]}}
        result["edge_coordinate_vectors"] = {}
        for a, b in combinations(range(4), 2):
            root, sign = edges.find((a, b))
            vector = [0] * len(er)
            vector[ei[root]] = sign
            result["edge_coordinate_vectors"][f"{a}{b}"] = vector
    return result


def determinant(matrix):
    """Leibniz determinant; independent of the calculator's row reductions."""
    n = len(matrix)
    return sum(parity(p) * product_entries(matrix, p) for p in permutations(range(n)))


def product_entries(matrix, p):
    value = 1
    for i, j in enumerate(p):
        value *= matrix[i][j]
    return value


def invariant_factors(matrix, rows, cols):
    """Exact determinantal divisors; matrices in this census have <=3 rows."""
    previous, factors = 1, []
    for k in range(1, min(rows, cols) + 1):
        divisor = 0
        for rs in combinations(range(rows), k):
            for cs in combinations(range(cols), k):
                divisor = gcd(divisor, abs(determinant([[matrix[r][c] for c in cs] for r in rs])))
        if not divisor:
            break
        require(divisor % previous == 0, "Invalid determinantal divisors")
        factors.append(divisor // previous)
        previous = divisor
    return factors


def independent_homology(chain):
    """Use the split exact sequence Hk -> coker dk+1 -> im dk (free)."""
    dims, boundaries = chain["dimensions"], chain["boundaries"]
    for k in (1, 2, 3):
        matrix = boundaries[str(k)]
        require(len(matrix) == dims[k - 1] and all(len(row) == dims[k] for row in matrix), "Wrong boundary shape")
    for k in (1, 2):
        a, b = boundaries[str(k)], boundaries[str(k + 1)]
        require(all(sum(a[i][t] * b[t][j] for t in range(dims[k])) == 0
                    for i in range(dims[k - 1]) for j in range(dims[k + 1])), "Chain condition failed")
    factors = {k: invariant_factors(boundaries[str(k)], dims[k - 1], dims[k]) for k in (1, 2, 3)}
    factors[0] = factors[4] = []
    return {f"H{k}": {"free_rank": dims[k] - len(factors[k]) - len(factors[k + 1]),
                       "torsion": [x for x in factors[k + 1] if x > 1]} for k in range(4)}


def multiply(a, b, columns):
    return [[sum(a[i][k] * b[k][j] for k in range(len(a[i]))) for j in range(columns)] for i in range(len(a))]


def matrix_shape(matrix, rows, columns):
    require(isinstance(matrix, list) and len(matrix) == rows and all(isinstance(row, list) and len(row) == columns for row in matrix), "Invalid certificate matrix shape")
    require(all(type(x) is int for row in matrix for x in row), "Noninteger certificate matrix")


def verify_smith_certificate(matrix, rows, columns, cert):
    require(cert["rows"] == rows and cert["columns"] == columns, "Smith certificate shape metadata differs")
    u, v, d = cert["U"], cert["V"], cert["D"]
    matrix_shape(u, rows, rows)
    matrix_shape(v, columns, columns)
    matrix_shape(d, rows, columns)
    require(abs(determinant(u)) == abs(determinant(v)) == 1, "Nonunimodular Smith transformations")
    require(multiply(multiply(u, matrix, columns), v, columns) == d, "Smith multiplication identity failed")
    require(all(x == 0 for i, row in enumerate(d) for j, x in enumerate(row) if i != j), "Nondiagonal Smith matrix")
    diagonal = [d[i][i] for i in range(min(rows, columns))]
    positive = [x for x in diagonal if x]
    require(diagonal == positive + [0] * (len(diagonal) - len(positive)) and all(x > 0 for x in positive), "Smith diagonal signs/order failed")
    require(all(b % a == 0 for a, b in zip(positive, positive[1:])), "Smith divisibility failed")
    require(cert["rank"] == len(positive) and cert["diagonal"] == positive, "Smith summary differs")


def group_label(group):
    free = group["free_rank"]
    pieces = [] if free == 0 else ["Z" if free == 1 else f"Z^{free}"]
    return " + ".join(pieces + [f"Z/{x}" for x in group["torsion"]]) or "0"


def verify_homology_certificate(chain, homology):
    dims = chain["dimensions"]
    maps = {0: [], 4: [[] for _ in range(dims[-1])]}
    maps.update({k: chain["boundaries"][str(k)] for k in (1, 2, 3)})
    require(homology["coefficients"] == "Z" and homology["dimensions"] == dims, "Wrong coefficient/dimension metadata")
    require(homology["chain_checks"] == [{"product": "B1B2", "zero": True}, {"product": "B2B3", "zero": True}], "Chain check metadata differs")
    require(set(homology["certificates"]) == set(homology["groups"]) == {"H0", "H1", "H2", "H3"}, "Missing homology degrees")
    for k, dim in enumerate(dims):
        cert = homology["certificates"][f"H{k}"]
        outgoing = cert["outgoing_smith"]
        verify_smith_certificate(maps[k], dims[k - 1] if k else 0, dim, outgoing)
        rank = outgoing["rank"]
        kernel = [row[rank:] for row in outgoing["V"]]
        require(cert["kernel_basis"] == kernel, "Kernel basis differs from unimodular Smith basis")
        incoming_columns = dims[k + 1] if k < 3 else 0
        inside = cert["incoming_in_kernel"]
        matrix_shape(inside, dim - rank, incoming_columns)
        require(multiply(kernel, inside, incoming_columns) == maps[k + 1], "Incoming kernel coordinates incorrect")
        quotient = cert["quotient_smith"]
        verify_smith_certificate(inside, dim - rank, incoming_columns, quotient)
        group = {"free_rank": dim - rank - quotient["rank"], "torsion": [x for x in quotient["diagonal"] if x > 1]}
        group["label"] = group_label(group)
        require(homology["groups"][f"H{k}"] == group, "Certificate/group summary differs")


def canonical_key(glues):
    records = normalize(glues)
    images = []
    for labels in permutations(range(4)):
        data = []
        for f, g, p in records:
            transformed = {labels[v]: labels[p[v]] for v in range(4)}
            a, b = labels[f], labels[g]
            if a > b:
                transformed = {y: x for x, y in transformed.items()}
                a, b = b, a
            data.append((a, b, *(transformed[v] for v in range(4))))
        images.append(tuple(sorted(data)))
    return [list(pair) for pair in min(images)]


def canonical_boundary(stage):
    return {"boundary_faces": sorted(stage["boundary_faces"]),
            "Ce": sorted([*sorted(row[:2]), row[2]] for row in stage["Ce"]),
            "Cv": sorted(sorted(group) for group in stage["Cv"])}


def verify_orientation_and_reversal(case, independent):
    records = normalize(case["glues"])
    equations = [{"gluing_number": i + 1, "full_permutation": [p[j] for j in range(4)],
                  "target_tet_sign_over_source": -parity([p[j] for j in range(4)])} for i, (_, _, p) in enumerate(records)]
    require(case["orientation_equations"] == equations, "Orientation equations differ")
    allowed = set()
    for f, _, p in records:
        for a, b in combinations([v for v in range(4) if v != f], 2):
            x, y = (0, a, b), (0, *sorted((p[a], p[b])))
            sign = 1 if p[a] < p[b] else -1
            allowed.add((x, y, sign))
            allowed.add((y, x, sign))
    witness = case["edge_reversal_witness"]
    require((witness is None) == independent["edge_orientation_consistent"], "Wrong reversed-edge witness presence")
    if witness:
        walk = witness["closed_walk"]
        require(bool(walk), "Empty reversed-edge walk")
        sign_product = 1
        for i, (a, b, sign) in enumerate(walk):
            require((tuple(a), tuple(b), sign) in allowed, "Witness step is not a gluing constraint")
            require(b == walk[(i + 1) % len(walk)][0], "Witness walk is not closed/continuous")
            sign_product *= sign
        require(sign_product == witness["sign_product"] == -1, "Witness does not reverse an edge")


def compare_case(case):
    other = independent_topology(case["glues"])
    after, decision = case["after"], case["decision"]
    expected_id = "-".join("".join(map(str, glue["target_face"])) for glue in case["glues"])
    require(case["case_id"] == expected_id, "Wrong case ID")
    verify_orientation_and_reversal(case, other)
    require(case["relabeling_key"] == canonical_key(case["glues"]), f"{expected_id}: relabeling key differs")
    if "after_first" in case:
        first = independent_topology(case["glues"][:1])
        saved_first = case["after_first"]
        require(case["first_boundary_state"] == canonical_boundary(first), f"{expected_id}: canonical boundary state differs")
        for key in ("vertex_classes", "edge_classes", "Ce", "Cv", "orientable", "connected", "edge_orientation_consistent", "boundary_faces"):
            require(saved_first[key] == first[key], f"{expected_id}: first-stage mismatch: {key}")
        require(len(saved_first["links"]) == len(first["links"]), f"{expected_id}: first-stage missing link")
        for actual, expected in zip(saved_first["links"], first["links"]):
            for key in ("members", "V", "E", "F", "chi", "boundary_components", "connected", "orientable", "is_surface"):
                require(actual[key] == expected[key], f"{expected_id}: first-stage link mismatch: {key}")
    for key in ("vertex_classes", "edge_classes", "Ce", "Cv", "orientable", "connected", "edge_orientation_consistent"):
        require(after[key] == other[key], f"{expected_id}: topology mismatch: {key}")
    require(after["boundary_faces"] == [], f"{expected_id}: spurious boundary")
    require(len(after["links"]) == len(other["links"]), f"{expected_id}: missing link")
    for actual, expected in zip(after["links"], other["links"]):
        for key in ("members", "V", "E", "F", "chi", "boundary_components", "connected", "orientable", "is_surface"):
            require(actual[key] == expected[key], f"{expected_id}: link mismatch: {key}")
        require(sorted((x["connected"], x["degrees"], x["valid"]) for x in actual["local_vertex_checks"]) ==
                sorted((x["connected"], x["degrees"], x["valid"]) for x in expected["local_vertex_checks"]),
                f"{expected_id}: local link neighbourhoods differ")
    for key in ("closed", "connected", "edge_orientation_consistent", "all_links_spheres", "orientable", "manifold_accepted", "accepted"):
        require(decision[key] == other[key], f"{expected_id}: decision mismatch: {key}")
    reasons = [(r["code"], r.get("link_members")) for r in decision["rejection_reasons"]]
    require(reasons == other["reasons"], f"{expected_id}: rejection reasons differ")
    if other["accepted"]:
        chain = case["chain_complex"]
        require(chain["dimensions"] == other["chain_complex"]["dimensions"], f"{expected_id}: chain dimensions differ")
        require(chain["boundaries"] == other["chain_complex"]["boundaries"], f"{expected_id}: boundary matrices differ")
        require(chain["bases"] == other["chain_complex"]["bases"], f"{expected_id}: chain bases differ")
        expected_groups = independent_homology(other["chain_complex"])
        groups = case["homology"]["groups"]
        require(all(groups[k]["free_rank"] == value["free_rank"] and groups[k]["torsion"] == value["torsion"]
                    for k, value in expected_groups.items()), f"{expected_id}: integral homology differs")
        verify_homology_certificate(chain, case["homology"])
        require(case["homology_status"] == "EXACT_CERTIFICATE_VERIFIED", "Wrong accepted homology status")
    else:
        require(case["homology"] is None, f"{expected_id}: rejected case has manifold homology")
        require(case["chain_complex"] is None and case["homology_status"] == "NOT_COMPUTED_REJECTED_TARGET", "Wrong rejected homology status")
    return {"case_id": expected_id, "status": "PASS", "accepted": other["accepted"]}


def expected_counts(cases):
    accepted = [c for c in cases if c["decision"]["accepted"]]
    reasons = Counter(code for case in cases for code in {r["code"] for r in case["decision"]["rejection_reasons"]})
    h1 = Counter(group_label(c["homology"]["groups"]["H1"]) for c in accepted)
    classes = defaultdict(list)
    for case in accepted:
        classes[json.dumps(canonical_key(case["glues"]))].append(case["case_id"])
    return {"assignments": len(cases), "accepted": len(accepted), "rejected": len(cases) - len(accepted),
            "closed": sum(c["decision"]["closed"] for c in cases),
            "connected": sum(c["decision"]["connected"] for c in cases),
            "ambient_orientable": sum(c["decision"]["orientable"] for c in cases),
            "edge_orientation_consistent": sum(c["decision"]["edge_orientation_consistent"] for c in cases),
            "manifold_accepted": sum(c["decision"]["manifold_accepted"] for c in cases),
            "rejection_case_counts_nonexclusive": dict(sorted(reasons.items())),
            "accepted_H1_counts": dict(sorted(h1.items())),
            "accepted_combinatorial_classes": sorted(classes.values())}


def expected_compression_witnesses(cases):
    witnesses = []
    accepted = [c for c in cases if c["decision"]["accepted"]]
    for a, b in combinations(accepted, 2):
        if (a["first_boundary_state"] == b["first_boundary_state"] and a["glues"][1] == b["glues"][1]
                and a["homology"]["groups"] != b["homology"]["groups"]):
            witnesses.append({"left_case": a["case_id"], "right_case": b["case_id"],
                              "same_labeled_boundary_state": a["first_boundary_state"], "same_final_gluing": a["glues"][1],
                              "left_homology": a["homology"]["groups"], "right_homology": b["homology"]["groups"]})
    return witnesses


def verify_csv(path, cases):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    require(len(rows) == 36, "CSV missing cases")
    for row, case in zip(rows, cases):
        d = case["decision"]
        h = case["homology"]["groups"] if case["homology"] else None
        expected = {"case_id": case["case_id"], "first_target": case["case_id"].split("-")[0],
                    "second_target": case["case_id"].split("-")[1],
                    "closed": str(d["closed"]), "connected": str(d["connected"]),
                    "ambient_orientable": str(d["orientable"]), "edge_orientation_consistent": str(d["edge_orientation_consistent"]),
                    "accepted": str(d["accepted"]),
                    "rejection_codes": ";".join(sorted({r["code"] for r in d["rejection_reasons"]})), "seconds": str(case["seconds"])}
        expected.update({f"full_permutation_{i + 1}": "".join(map(str, eq["full_permutation"])) for i, eq in enumerate(case["orientation_equations"])})
        expected.update({f"H{k}": group_label(h[f"H{k}"]) if h else "NOT_COMPUTED_REJECTED_TARGET" for k in range(4)})
        links = []
        for link in case["after"]["links"]:
            sphere = link["connected"] and link["is_surface"] and link["orientable"] and link["chi"] == 2 and link["boundary_components"] == 0
            kind = "S2" if sphere else ("Klein bottle" if link["is_surface"] and not link["orientable"] and link["chi"] == 0 and not link["boundary_components"] else "non-sphere")
            links.append(f"{kind}[{link['V']},{link['E']},{link['F']};chi={link['chi']}]")
        expected["links"] = "; ".join(links)
        require(row == expected, f"CSV row differs: {case['case_id']}")


def verify_boundary_inclusion(witness, cases):
    by_id = {case["case_id"]: case for case in cases}
    ids = ["130-231", "301-231"]
    require(witness["left_case"] == ids[0] and witness["right_case"] == ids[1], "Wrong inclusion witness cases")
    require([r["case_id"] for r in witness["records"]] == ids, "Wrong inclusion witness record order")
    expected_values = [{"x_03": 2, "y_13": 1, "z_23": 3, "edge_02": -1},
                       {"x_03": 1, "y_13": 2, "z_23": 3, "edge_02": -2}]
    for record, values in zip(witness["records"], expected_values):
        case = by_id[record["case_id"]]
        partial = independent_topology(case["glues"][:1])
        require(witness["common_boundary_state"] == canonical_boundary(partial), "Inclusion witness boundary state differs")
        require(witness["common_completion"] == case["glues"][1], "Inclusion witness completion differs")
        chain = record["partial_chain_complex"]
        require(all(chain[k] == partial["chain_complex"][k] for k in ("dimensions", "boundaries", "bases")), "Partial chain differs")
        verify_homology_certificate(chain, record["partial_homology"])
        groups = independent_homology(chain)
        require(all(record["partial_homology"]["groups"][k]["free_rank"] == value["free_rank"] and record["partial_homology"]["groups"][k]["torsion"] == value["torsion"] for k, value in groups.items()), "Partial integral homology differs")
        require(groups["H1"] == {"free_rank": 1, "torsion": []}, "Partial H1 is not Z")
        B2 = chain["boundaries"]["2"]
        transpose = [list(row) for row in zip(*B2)]
        smith = record["functional_smith_certificate"]
        verify_smith_certificate(transpose, len(transpose), len(B2), smith)
        w = record["primitive_functional_on_edge_basis"]
        require(len(w) == len(B2) and gcd(*w) == 1, "Functional is not primitive")
        require(all(sum(w[i] * B2[i][j] for i in range(len(w))) == 0 for j in range(len(B2[0]))), "Functional does not annihilate face boundaries")
        smith_vector = [row[-1] for row in smith["V"]]
        require(w == smith_vector or w == [-x for x in smith_vector], "Functional differs from certified kernel generator")
        edge_vectors = partial["edge_coordinate_vectors"]
        vectors = {"x_03": edge_vectors["03"], "y_13": edge_vectors["13"], "z_23": edge_vectors["23"], "edge_02": edge_vectors["02"]}
        require(record["boundary_cycle_vectors"] == vectors, "Boundary cycle coordinates differ")
        actual_values = {key: sum(a * b for a, b in zip(w, vector)) for key, vector in vectors.items()}
        require(record["boundary_inclusion_to_Z"] == actual_values == values, "Boundary inclusion values differ")
        relation = [a - b for a, b in zip(vectors["z_23"], vectors["edge_02"])]
        value = sum(a * b for a, b in zip(w, relation))
        require(record["closing_relation_in_edge_basis"] == relation and record["closing_relation_value"] == value, "Closing relation differs")
        require(value == values["x_03"] + 2 * values["y_13"] and case["homology"]["groups"]["H1"]["torsion"] == [abs(value)], "Closing relation does not produce saved torsion")


def verify_run(run_dir):
    run_dir = Path(run_dir)
    path = run_dir / "results.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    root = Path(__file__).resolve().parents[1]
    expected_sources = {"experiments/one_tetrahedron_census.py", "experiments/example7_rebuild.py", "experiments/integer_homology.py"}
    require({name.replace("\\", "/") for name in report["source_sha256"]} == expected_sources, "Source manifest differs")
    for relative, checksum in report["source_sha256"].items():
        require(hashlib.sha256((root / relative).read_bytes()).hexdigest() == checksum, f"Source checksum differs: {relative}")
    cases = report["cases"]
    expected_ids = ["".join(map(str, a)) + "-" + "".join(map(str, b))
                    for a, b in product(permutations((0, 1, 3)), permutations((1, 2, 3)))]
    require([c["case_id"] for c in cases] == expected_ids, "Missing, duplicate, or reordered cases")
    checks = []
    for case in cases:
        saved = json.loads((run_dir / "cases" / (case["case_id"] + ".json")).read_text(encoding="utf-8"))
        require(saved == case, "Per-case file differs from aggregate")
        checks.append(compare_case(case))
    counts = expected_counts(cases)
    require(all(report["counts"][key] == value for key, value in counts.items()), "Aggregate counts/classes differ")
    expected_witnesses = expected_compression_witnesses(cases)
    actual_witnesses = report["compression_witnesses"]
    require([{k: v for k, v in witness.items() if k != "conclusion"} for witness in actual_witnesses] == expected_witnesses, "Compression witness list differs")
    require(json.loads((run_dir / "compression-witnesses.json").read_text(encoding="utf-8")) == actual_witnesses, "Compression witness checkpoint differs")
    verify_boundary_inclusion(report["boundary_inclusion_witness"], cases)
    require(json.loads((run_dir / "boundary-inclusion-witness.json").read_text(encoding="utf-8")) == report["boundary_inclusion_witness"], "Boundary inclusion checkpoint differs")
    verify_csv(run_dir / "results-table.csv", cases)
    by_id = {c["case_id"]: c for c in cases}
    left, right = by_id["130-231"], by_id["301-231"]
    left_first = independent_topology(left["glues"][:1])
    right_first = independent_topology(right["glues"][:1])
    require(left_first["Ce"] == right_first["Ce"] and left_first["Cv"] == right_first["Cv"], "Compression witness states differ")
    require(left["glues"][1] == right["glues"][1], "Compression witness completions differ")
    require(left["homology"]["groups"]["H1"]["torsion"] == [4] and right["homology"]["groups"]["H1"]["torsion"] == [5], "Compression witness homology differs from independent expected data")
    result = {"status": "PASS", "checked_utc": datetime.now(timezone.utc).isoformat(),
              "results_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
              "verifier_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "cases_checked": len(checks), "accepted": sum(c["accepted"] for c in checks),
              "cases": checks,
              "compression_witness": {"left_case": "130-231", "right_case": "301-231", "same_Ce_Cv": True,
                                      "same_completion": True, "H1_torsion_left": [4], "H1_torsion_right": [5]},
              "checks": ["source hashes", "all 36 target permutations", "per-case checkpoints", "signed equivalence classes",
                         "local link circles and orientability", "ambient orientability", "all rejection codes",
                         "oriented simplex boundaries", "chain condition", "integral homology via exact minors",
                         "unimodular Smith/kernel certificates", "edge-reversal closed walks", "all 24 relabelings",
                         "aggregate counts/classes", "compression witnesses", "primitive boundary inclusion and closing relation", "CSV cells"],
              "scope": "Independent finite combinatorial and integer-arithmetic check; no manifold-name recognition or homeomorphism classification."}
    (run_dir / "independent-verification.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    result = verify_run(args.run)
    print(json.dumps({k: v for k, v in result.items() if k != "cases"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
