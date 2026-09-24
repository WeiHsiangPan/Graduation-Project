"""Verify every machine-readable Cayley-surface witness in the catalogue.

Checks performed for each (G, S, F):

1. group order and inverse-closed connected Cayley skeleton;
2. exact oriented-dart partition and simple face boundaries;
3. one cyclic link at every vertex (the closed-surface manifold check);
4. Euler characteristic and orientable genus;
5. chain condition B1 @ B2 = 0 and dim ker(L1) = 2g;
6. adjacency and vertex-Laplacian spectra, cached per (G, S).

Run from the repository root:

    python handbook/verify_examples.py
    python handbook/verify_examples.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / "code"
CATALOGUE = ROOT / "data" / "surfaces" / "catalogue.json"
if str(CODE) not in sys.path:
    sys.path.insert(0, str(CODE))

from surface_systems import (  # noqa: E402
    explicit_rotation_surface,
    freeze,
    group_from_spec,
    local_binary_rotation_surface,
    relator_surface,
    uniform_rotation_surface,
    validate_surface,
)


def load_catalogue():
    with CATALOGUE.open(encoding="utf-8") as handle:
        return json.load(handle)


def construct_surface(group, generators, construction):
    construction_type = construction["type"]
    if construction_type == "relator_orbits":
        return relator_surface(group, generators, construction["words"])
    if construction_type == "uniform_rotation":
        return uniform_rotation_surface(group, generators, construction["order"])
    if construction_type == "local_binary_rotation":
        return local_binary_rotation_surface(group, generators, construction["bits"])
    if construction_type == "explicit_rotation":
        return explicit_rotation_surface(group, generators, construction["orders"])
    raise ValueError(f"Unknown construction type: {construction_type}")


def adjacency_spectra(group, generators):
    elements = group["elements"]
    index = {element: position for position, element in enumerate(elements)}
    adjacency = np.zeros((len(elements), len(elements)), dtype=float)
    for element in elements:
        for generator in generators:
            adjacency[index[element], index[group["mul"][(element, generator)]]] += 1
    adjacency_eigenvalues = np.linalg.eigvalsh(adjacency)
    laplacian_eigenvalues = len(generators) - adjacency_eigenvalues
    return {
        "adjacency": _spectrum_counter(adjacency_eigenvalues, reverse=True),
        "laplacian": _spectrum_counter(laplacian_eigenvalues),
    }


def _spectrum_counter(values, reverse=False):
    rounded = np.round(values, 8).tolist()
    return dict(Counter(sorted(rounded, reverse=reverse)))


def cellular_matrices(group, generators, faces):
    elements = group["elements"]
    vertex_index = {vertex: position for position, vertex in enumerate(elements)}
    edge_pairs = set()
    for tail in elements:
        for generator in generators:
            head = group["mul"][(tail, generator)]
            edge_pairs.add(tuple(sorted((vertex_index[tail], vertex_index[head]))))
    edges = tuple(sorted(edge_pairs))
    edge_index = {edge: position for position, edge in enumerate(edges)}

    boundary_1 = np.zeros((len(elements), len(edges)), dtype=int)
    for position, (tail, head) in enumerate(edges):
        boundary_1[tail, position] = -1
        boundary_1[head, position] = 1

    boundary_2 = np.zeros((len(edges), len(faces)), dtype=int)
    for face_index, face in enumerate(faces):
        for position, tail_vertex in enumerate(face):
            head_vertex = face[(position + 1) % len(face)]
            tail = vertex_index[tail_vertex]
            head = vertex_index[head_vertex]
            edge = tuple(sorted((tail, head)))
            orientation = 1 if (tail, head) == edge else -1
            boundary_2[edge_index[edge], face_index] += orientation
    return boundary_1, boundary_2


def hodge_checks(group, generators, faces, genus):
    boundary_1, boundary_2 = cellular_matrices(group, generators, faces)
    chain_residual = boundary_1 @ boundary_2
    chain_ok = bool(np.all(chain_residual == 0))
    laplacian_1 = boundary_1.T @ boundary_1 + boundary_2 @ boundary_2.T
    eigenvalues = np.linalg.eigvalsh(laplacian_1.astype(float))
    tolerance = max(laplacian_1.shape) * np.finfo(float).eps * max(1.0, float(np.max(np.abs(eigenvalues))))
    nullity = int(np.count_nonzero(np.abs(eigenvalues) <= tolerance))
    return {
        "chain_ok": chain_ok,
        "hodge_nullity": nullity,
        "expected_hodge_nullity": 2 * genus,
        "hodge_ok": chain_ok and nullity == 2 * genus,
    }


def verify_catalogue():
    catalogue = load_catalogue()
    groups = {}
    spectra_cache = {}
    results = []

    for surface in catalogue["surfaces"]:
        group_id = surface["group"]
        group_record = catalogue["groups"][group_id]
        if group_id not in groups:
            groups[group_id] = group_from_spec(group_record["spec"])
        group = groups[group_id]
        generators = tuple(freeze(group_record["generators"]))
        faces = construct_surface(group, generators, surface["construction"])
        topology = validate_surface(group, generators, faces)
        expected_profile = {int(length): count for length, count in surface["profile"].items()}

        expectation_errors = []
        if len(group["elements"]) != group_record["expected_order"]:
            expectation_errors.append("group order mismatch")
        if topology["genus"] != surface["genus"]:
            expectation_errors.append("genus mismatch")
        if topology["profile"] != expected_profile:
            expectation_errors.append("face profile mismatch")

        hodge = hodge_checks(group, generators, faces, surface["genus"])
        if not hodge["hodge_ok"]:
            expectation_errors.append("Hodge check failed")

        spectrum_key = (group_id, generators)
        if spectrum_key not in spectra_cache:
            spectra_cache[spectrum_key] = adjacency_spectra(group, generators)

        valid = topology["valid"] and not expectation_errors
        results.append(
            {
                "id": surface["id"],
                "group": group_record["display"],
                "valid": valid,
                "V": topology["vertex_count"],
                "E": topology["edge_count"],
                "F": topology["face_count"],
                "chi": topology["chi"],
                "genus": topology["genus"],
                "profile": topology["profile"],
                "construction": surface["construction"]["type"],
                "hodge_nullity": hodge["hodge_nullity"],
                "errors": topology["errors"] + expectation_errors,
                "spectrum": spectra_cache[spectrum_key],
            }
        )
    return results


def print_human_report(results):
    for result in results:
        marker = "OK" if result["valid"] else "FAIL"
        profile = " + ".join(
            f"{count}x{length}" for length, count in result["profile"].items()
        )
        print(
            f"[{marker:4s}] {result['id']:27s} "
            f"V={result['V']:2d} E={result['E']:2d} F={result['F']:2d} "
            f"chi={result['chi']:+2d} g={result['genus']} "
            f"b1={result['hodge_nullity']} faces={profile}"
        )
        for error in result["errors"]:
            print(f"       - {error}")

    print("\nSpectra by Cayley skeleton:")
    shown = set()
    for result in results:
        signature = (result["group"], repr(result["spectrum"]))
        if signature in shown:
            continue
        shown.add(signature)
        print(f"  {result['group']}: Spec(A)={result['spectrum']['adjacency']}")
        print(f"      Spec(L0)={result['spectrum']['laplacian']}")

    passed = sum(result["valid"] for result in results)
    print(f"\n{passed}/{len(results)} SURFACES PASSED")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="emit the verification report as JSON")
    args = parser.parse_args()
    results = verify_catalogue()
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print_human_report(results)
    return 0 if all(result["valid"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
