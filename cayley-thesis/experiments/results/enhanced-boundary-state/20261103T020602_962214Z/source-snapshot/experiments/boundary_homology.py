"""Marked boundary-to-interior integral H1 maps for the one-tetrahedron study.

The boundary chain complex and its homology basis use only marked Ce/Cv.
Interior H1=0 or Z is compared modulo its entire automorphism group
(trivial or sign). This module does not claim a general abelian-map normal form.
"""
from __future__ import annotations

from itertools import combinations
import json

import example7_rebuild as core
import one_tetrahedron_census as census
from integer_homology import (checked_matrix, integral_homology, inverse_unimodular, multiply,
                              verify_homology)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def group_type(group):
    return {"free_rank": group["free_rank"], "torsion": list(group["torsion"])}


def parse_face(name):
    tet, face = name.split(":")
    return int(tet[1:]), tuple(map(int, face))


def parse_occurrence(name):
    face, edge = name.split("/")
    t, triple = parse_face(face)
    a, b = map(int, edge)
    require(a < b and a in triple and b in triple, "Boundary occurrence must orient its edge increasingly")
    return t, triple, a, b


def occurrence_name(t, face, a, b):
    return f"t{t}:" + "".join(map(str, face)) + f"/{a}{b}"


def boundary_complex(state):
    """Construct a marked cellular boundary using Ce/Cv and face labels alone."""
    faces = sorted(state["boundary_faces"])
    vertex_groups = sorted(sorted(tuple(v) for v in group) for group in state["Cv"])
    owner = {v: i for i, group in enumerate(vertex_groups) for v in group}
    require(len(owner) == sum(map(len, vertex_groups)), "Duplicate boundary vertex in Cv")
    edge_groups, edge_sign = [], {}
    for a, b, same in core.canonical_ce(state["Ce"]):
        require(a not in edge_sign and b not in edge_sign, "Repeated boundary occurrence in Ce")
        require(a != b, "Ce must pair distinct face-edge occurrences")
        edge_groups.append((a,b))
        edge_sign[a], edge_sign[b] = 1, 1 if same else -1
    edge_groups.sort()
    edge_owner = {x:i for i, group in enumerate(edge_groups) for x in group}
    expected_occurrences, expected_vertices = set(), set()
    for name in faces:
        t, triple = parse_face(name)
        require(tuple(sorted(triple)) == triple and len(set(triple)) == 3, "Invalid marked boundary face")
        expected_vertices.update((t,v) for v in triple)
        expected_occurrences.update(occurrence_name(t,triple,a,b) for a,b in combinations(triple,2))
    require(set(owner) == expected_vertices, "Cv does not cover exactly the boundary vertices")
    require(set(edge_owner) == expected_occurrences, "Ce does not cover exactly the boundary edge occurrences")
    B1 = [[0]*len(edge_groups) for _ in vertex_groups]
    B2 = [[0]*len(faces) for _ in edge_groups]
    for j, group in enumerate(edge_groups):
        t, _, a, b = parse_occurrence(group[0])
        B1[owner[t,a]][j] -= 1
        B1[owner[t,b]][j] += 1
        # Ce must induce the same oriented endpoints from either occurrence.
        t2, _, c, d = parse_occurrence(group[1])
        endpoints = [owner[t2,c],owner[t2,d]]
        if edge_sign[group[1]] == -1:
            endpoints.reverse()
        require(endpoints == [owner[t,a],owner[t,b]], "Ce direction conflicts with Cv endpoints")
    for j, name in enumerate(faces):
        t, triple = parse_face(name)
        a,b,c = triple
        for x,y,sign in ((b,c,1),(a,c,-1),(a,b,1)):
            occurrence = occurrence_name(t,triple,x,y)
            B2[edge_owner[occurrence]][j] += sign*edge_sign[occurrence]
    return {"dimensions":[len(vertex_groups),len(edge_groups),len(faces),0],
            "boundaries":{"1":B1,"2":B2,"3":[[] for _ in faces]},
            "bases":{"vertices":[group[0] for group in vertex_groups],
                     "edges":[group[0] for group in edge_groups],"faces":faces,"tetrahedra":[]},
            "vertex_classes":vertex_groups,"edge_occurrence_classes":edge_groups,
            "edge_occurrence_signs":edge_sign,
            "basis_convention":"Marked Ce/Cv only; lexicographic representative occurrences, increasing local edge/face orientation."}


def _generator_indices(certificate):
    quotient = certificate["quotient_smith"]
    return ([i for i,d in enumerate(quotient["diagonal"]) if d > 1]
            + list(range(quotient["rank"],quotient["rows"])))


def homology_generator_cycles(homology, degree=1):
    """Columns representing torsion generators followed by free generators."""
    cert = homology["certificates"][f"H{degree}"]
    inverse = inverse_unimodular(cert["quotient_smith"]["U"])
    indices = _generator_indices(cert)
    selected = [[row[i] for i in indices] for row in inverse]
    return multiply(cert["kernel_basis"],selected,len(indices))


def homology_coordinates(homology, cycles, degree=1, columns=None):
    """Represent integral cycles in the certified Smith quotient coordinates."""
    if columns is None:
        columns = len(cycles[0]) if cycles else 0
    cert = homology["certificates"][f"H{degree}"]
    outgoing = cert["outgoing_smith"]
    coordinates = multiply(inverse_unimodular(outgoing["V"]),cycles,columns)
    require(not any(x for row in coordinates[:outgoing["rank"]] for x in row), "Input is not a cycle")
    in_kernel = coordinates[outgoing["rank"]:]
    quotient_coordinates = multiply(cert["quotient_smith"]["U"],in_kernel,columns)
    indices = _generator_indices(cert)
    result = [quotient_coordinates[i][:] for i in indices]
    torsion = homology["groups"][f"H{degree}"]["torsion"]
    for i,order in enumerate(torsion):
        result[i] = [x % order for x in result[i]]
    return result


def canonical_cyclic_map(domain, target, matrix):
    """Exact codomain-basis equivalence for target 0/Z; fixed marked domain."""
    require(not target["torsion"] and target["free_rank"] in (0,1),
            "Canonical map equality is currently implemented only for interior H1=0 or Z")
    columns = domain["free_rank"]+len(domain["torsion"])
    require(len(matrix) == target["free_rank"] and all(len(row)==columns for row in matrix), "Wrong induced map shape")
    normalized = [row[:] for row in matrix]
    sign = 1
    if normalized:
        first = next((x for x in normalized[0] if x),0)
        sign = -1 if first < 0 else 1
        normalized[0] = [sign*x for x in normalized[0]]
    return {"domain":group_type(domain),"target":group_type(target),"matrix":normalized},sign


def build_boundary_inclusion(glues, stage):
    require(stage["edge_orientation_consistent"], "Cannot use the intended oriented cell basis when an edge reverses itself")
    state = census.boundary_state(stage)
    boundary = boundary_complex(state)
    interior = census.chain_complex(glues,stage)
    bh = integral_homology(boundary["boundaries"],boundary["dimensions"])
    ih = integral_homology(interior["boundaries"],interior["dimensions"])
    n0,n1,n2,_ = interior["dimensions"]
    b0,b1,b2,_ = boundary["dimensions"]
    vertex_owner = {tuple(v):i for i, group in enumerate(stage["vertex_classes"]) for v in group}
    edge_owner = {tuple(v):i for i, group in enumerate(stage["edge_classes"]) for v in group}
    _,edges,faces,_ = census.constraints(glues)
    signs,edge_ok = core.signed_labels(list(edge_owner),edges)
    face_groups,face_owner = core.quotient([(0,f) for f in range(4)],[(a,b) for a,b,_ in faces])
    face_sign,face_ok = core.signed_labels(list(face_owner),faces)
    require(edge_ok and face_ok,"Inconsistent interior chain orientation")
    J0,J1,J2 = [[0]*b0 for _ in range(n0)],[[0]*b1 for _ in range(n1)],[[0]*b2 for _ in range(n2)]
    for j,v in enumerate(boundary["bases"]["vertices"]):
        J0[vertex_owner[tuple(v)]][j] = 1
    for j,name in enumerate(boundary["bases"]["edges"]):
        t,_,a,b = parse_occurrence(name)
        J1[edge_owner[t,a,b]][j] = signs[t,a,b]
    for j,name in enumerate(boundary["bases"]["faces"]):
        t,triple = parse_face(name)
        f = next(iter(set(range(4))-set(triple)))
        J2[face_owner[t,f]][j] = face_sign[t,f]
    inclusion = {"0":J0,"1":J1,"2":J2}
    verify_chain_inclusion(boundary,interior,inclusion)
    generators = homology_generator_cycles(bh)
    domain,target = bh["groups"]["H1"],ih["groups"]["H1"]
    columns = domain["free_rank"]+len(domain["torsion"])
    images = multiply(J1,generators,columns)
    matrix = homology_coordinates(ih,images,columns=columns)
    key,sign = canonical_cyclic_map(domain,target,matrix)
    result = {"boundary_chain_complex":boundary,"interior_chain_complex":interior,
              "boundary_homology":bh,"interior_homology":ih,"chain_inclusion":inclusion,
              "induced_H1":{"domain":domain,"target":target,"boundary_generator_cycles":generators,
                             "interior_generator_cycles":homology_generator_cycles(ih),"matrix":matrix,
                             "canonical_matrix":key["matrix"],"canonical_target_sign":sign,
                             "group_coordinate_order":"torsion factors >1, then free generators"},
              "canonical_map_key":key,
              "equality_scope":"Fixed marked boundary basis from Ce/Cv; target 0 or Z modulo its automorphisms (sign). No arbitrary-rank map normal-form claim.",
              "uses_future_gluings":False}
    return json.loads(json.dumps(result))


def verify_chain_inclusion(boundary,interior,inclusion):
    require(set(inclusion)=={"0","1","2"},"Chain inclusion degrees differ")
    for k in range(3):
        checked_matrix(inclusion[str(k)],interior["dimensions"][k],boundary["dimensions"][k])
    for k in (1,2):
        columns = boundary["dimensions"][k]
        left = multiply(interior["boundaries"][str(k)],inclusion[str(k)],columns)
        right = multiply(inclusion[str(k-1)],boundary["boundaries"][str(k)],columns)
        require(left==right,f"Chain inclusion condition B{k}*J{k}=J{k-1}*bdB{k} failed")
    return True


def verify_boundary_inclusion(result):
    boundary,interior = result["boundary_chain_complex"],result["interior_chain_complex"]
    bh,ih = result["boundary_homology"],result["interior_homology"]
    verify_homology(boundary["boundaries"],boundary["dimensions"],bh)
    verify_homology(interior["boundaries"],interior["dimensions"],ih)
    verify_chain_inclusion(boundary,interior,result["chain_inclusion"])
    induced = result["induced_H1"]
    require(induced["domain"]==bh["groups"]["H1"] and induced["target"]==ih["groups"]["H1"],"Induced group summaries differ")
    generators = homology_generator_cycles(bh)
    require(induced["boundary_generator_cycles"]==generators,"Boundary H1 generator cycles differ")
    require(induced["interior_generator_cycles"]==homology_generator_cycles(ih),"Interior H1 generator cycles differ")
    columns = induced["domain"]["free_rank"]+len(induced["domain"]["torsion"])
    images = multiply(result["chain_inclusion"]["1"],generators,columns)
    matrix = homology_coordinates(ih,images,columns=columns)
    require(induced["matrix"]==matrix,"Induced H1 map differs")
    key,sign = canonical_cyclic_map(induced["domain"],induced["target"],matrix)
    require(result["canonical_map_key"]==key and induced["canonical_matrix"]==key["matrix"]
            and induced["canonical_target_sign"]==sign,"Canonical marked map differs")
    require(result["uses_future_gluings"] is False,"State cannot use a completion")
    return True
