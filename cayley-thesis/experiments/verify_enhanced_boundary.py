"""Independent checks of marked boundary-homology enhanced states.

Does not import the enhanced-state builder, boundary-map calculator or Smith
calculator. Reuses the earlier independent simplex and certificate checker.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
from itertools import combinations, permutations
import json
from pathlib import Path

import verify_one_tetrahedron as old

require = old.require
multiply = old.multiply


def inverse(matrix):
    n = len(matrix)
    old.matrix_shape(matrix, n, n)
    a = [[Fraction(x) for x in row] + [Fraction(int(i == j)) for j in range(n)]
         for i, row in enumerate(matrix)]
    for k in range(n):
        pivot = next((i for i in range(k, n) if a[i][k]), None)
        require(pivot is not None, "Singular homology change of basis")
        a[k], a[pivot] = a[pivot], a[k]
        value = a[k][k]
        a[k] = [x / value for x in a[k]]
        for i in range(n):
            if i != k:
                value = a[i][k]
                a[i] = [x - value * y for x, y in zip(a[i], a[k])]
    result = [row[n:] for row in a]
    require(all(x.denominator == 1 for row in result for x in row), "Nonunimodular homology basis")
    return [[int(x) for x in row] for row in result]


def group_data(group):
    return {"free_rank": group["free_rank"], "torsion": group["torsion"]}


def active_coordinates(certificate, dimension):
    quotient = certificate["quotient_smith"]
    return [i for i, value in enumerate(quotient["diagonal"]) if value > 1] + list(range(quotient["rank"], dimension - certificate["outgoing_smith"]["rank"]))


def generator_cycles(chain, homology, k=1):
    cert = homology["certificates"][f"H{k}"]
    kernel = cert["kernel_basis"]
    inside_dimension = chain["dimensions"][k] - cert["outgoing_smith"]["rank"]
    u_inverse = inverse(cert["quotient_smith"]["U"])
    indices = active_coordinates(cert, chain["dimensions"][k])
    selected = [[row[j] for j in indices] for row in u_inverse]
    return multiply(kernel, selected, len(indices))


def cycle_coordinates(chain, homology, cycles, columns, k=1):
    cert = homology["certificates"][f"H{k}"]
    outgoing = cert["outgoing_smith"]
    before = multiply(inverse(outgoing["V"]), cycles, columns)
    require(not any(x for row in before[:outgoing["rank"]] for x in row), "Mapped generator is not a cycle")
    quotient_coordinates = multiply(cert["quotient_smith"]["U"], before[outgoing["rank"]:], columns)
    indices = active_coordinates(cert, chain["dimensions"][k])
    result = [quotient_coordinates[i][:] for i in indices]
    torsion = homology["groups"][f"H{k}"]["torsion"]
    for i, modulus in enumerate(torsion):
        result[i] = [x % modulus for x in result[i]]
    return result


def parse_occurrence(name):
    face, edge = name.split("/")
    tetrahedron, triple = face.split(":")
    require(tetrahedron == "t0", "Unexpected boundary tetrahedron")
    return int(next(v for v in "0123" if v not in triple)), int(edge[0]), int(edge[1])


def independent_boundary_complex(partial):
    state = old.canonical_boundary(partial)
    vertices = state["Cv"]
    vertex_owner = {tuple(vertex): i for i, group in enumerate(vertices) for vertex in group}
    pairs = sorted(state["Ce"], key=lambda row: min(row[:2]))
    reps = [min(row[:2]) for row in pairs]
    edge_owner, edge_sign = {}, {}
    for i, (a, b, same) in enumerate(pairs):
        representative, other = sorted((a, b))
        edge_owner[representative] = edge_owner[other] = i
        edge_sign[representative], edge_sign[other] = 1, 1 if same else -1
    faces = sorted(state["boundary_faces"])
    dims = [len(vertices), len(pairs), len(faces), 0]
    B1 = [[0] * dims[1] for _ in vertices]
    B2 = [[0] * dims[2] for _ in pairs]
    J0 = [[0] * dims[0] for _ in partial["vertex_classes"]]
    J1 = [[0] * dims[1] for _ in partial["edge_classes"]]
    J2 = [[0] * dims[2] for _ in partial["chain_complex"]["bases"]["faces"]]
    interior_vertex_owner = {tuple(v): i for i, group in enumerate(partial["vertex_classes"]) for v in group}
    for i, group in enumerate(vertices):
        J0[interior_vertex_owner[tuple(group[0])]][i] = 1
    for j, representative in enumerate(reps):
        _, a, b = parse_occurrence(representative)
        B1[vertex_owner[0, a]][j] -= 1
        B1[vertex_owner[0, b]][j] += 1
        vector = partial["edge_coordinate_vectors"][f"{a}{b}"]
        for i, value in enumerate(vector):
            J1[i][j] = value
    interior_faces = partial["chain_complex"]["bases"]["faces"]
    for j, name in enumerate(faces):
        triple = [int(v) for v in name.split(":")[1]]
        a, b, c = triple
        for x, y, coefficient in ((b, c, 1), (a, c, -1), (a, b, 1)):
            occurrence = name + f"/{x}{y}"
            B2[edge_owner[occurrence]][j] += coefficient * edge_sign[occurrence]
        opposite = next(v for v in range(4) if v not in triple)
        J2[interior_faces.index([0, opposite])][j] = 1
    chain = {"dimensions": dims, "boundaries": {"1": B1, "2": B2, "3": [[] for _ in faces]},
             "bases": {"vertices": [group[0] for group in vertices], "edges": reps,
                       "faces": faces, "tetrahedra": []},
             'vertex_classes':vertices,'edge_occurrence_classes':[sorted(row[:2]) for row in pairs],
             'edge_occurrence_signs':edge_sign}
    return chain, {"0": J0, "1": J1, "2": J2}


def verify_inclusion(record, glues):
    partial = old.independent_topology(glues)
    require(partial["edge_orientation_consistent"], "Inclusion uses a reversed-edge complex")
    expected_boundary, expected_J = independent_boundary_complex(partial)
    boundary, interior = record["boundary_chain_complex"], record["interior_chain_complex"]
    for field in ("dimensions", "boundaries", "bases"):
        require(boundary[field] == expected_boundary[field], f"Boundary complex differs: {field}")
        require(interior[field] == partial["chain_complex"][field], f"Interior complex differs: {field}")
    for field in ('vertex_classes','edge_occurrence_classes','edge_occurrence_signs'):
        require(boundary[field] == expected_boundary[field], f'Boundary marking differs: {field}')
    J = record["chain_inclusion"]
    require(J == expected_J, "Chain inclusion is not the marked boundary inclusion")
    for k in (1, 2):
        left = multiply(interior["boundaries"][str(k)], J[str(k)], boundary["dimensions"][k])
        right = multiply(J[str(k - 1)], boundary["boundaries"][str(k)], boundary["dimensions"][k])
        require(left == right, "Boundary inclusion is not a chain map")
    for chain, h in ((boundary, record["boundary_homology"]), (interior, record["interior_homology"])):
        old.verify_homology_certificate(chain, h)
        expected = old.independent_homology(chain)
        require(all(group_data(h["groups"][k]) == value for k, value in expected.items()), "Homology differs from exact minors")
    bh, ih = record["boundary_homology"], record["interior_homology"]
    domain, target = bh["groups"]["H1"], ih["groups"]["H1"]
    require(not domain["torsion"] and not target["torsion"] and target["free_rank"] in (0, 1), "Unsupported canonical-map domain")
    domain_generators = generator_cycles(boundary, bh)
    target_generators = generator_cycles(interior, ih)
    induced = record["induced_H1"]
    require(induced["domain"] == domain and induced["target"] == target, "Induced-map group metadata differs")
    require(induced["boundary_generator_cycles"] == domain_generators, "Marked boundary generators differ")
    require(induced["interior_generator_cycles"] == target_generators, "Interior homology generators differ")
    mapped = multiply(J["1"], domain_generators, domain["free_rank"])
    matrix = cycle_coordinates(interior, ih, mapped, domain["free_rank"])
    require(induced["matrix"] == matrix, "Induced H1 map differs")
    canonical = [row[:] for row in matrix]
    if canonical:
        first = next((x for x in canonical[0] if x), 0)
        if first < 0:
            canonical = [[-x for x in canonical[0]]]
    require(induced["canonical_matrix"] == canonical, "Canonical map sign differs")
    expected_key = {"domain": group_data(domain), "target": group_data(target), "matrix": canonical}
    require(record["canonical_map_key"] == expected_key, "Canonical map key differs")
    return {"status": "PASS", "canonical_map_key": expected_key,
            "boundary_generator_cycles": domain_generators, "boundary_state": old.canonical_boundary(partial)}


def state_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()


def eligibility(partial):
    reasons = []
    if not partial['edge_orientation_consistent']:
        reasons.append('REVERSED_SELF_EDGE')
    if any(not (link['connected'] and link['is_surface'] and link['orientable'] and
                ((link['chi'] == 1 and link['boundary_components'] == 1) or
                 (link['chi'] == 2 and link['boundary_components'] == 0))) for link in partial['links']):
        reasons.append('NON_MANIFOLD_VERTEX_LINK')
    if not partial['orientable']:
        reasons.append('AMBIENT_NONORIENTABLE')
    return {'eligible': not reasons, 'reasons': reasons}


def expected_comparisons(histories, source_cases):
    by_id = {case['case_id']: case for case in source_cases}
    rows = []
    for target in permutations((1, 2, 3)):
        for a, b in combinations(histories, 2):
            suffix = ''.join(map(str, target))
            left, right = by_id[a['history_id'] + '-' + suffix], by_id[b['history_id'] + '-' + suffix]
            require(left['glues'][1] == right['glues'][1], 'Compared completions differ')
            included = a['eligibility']['eligible'] and b['eligibility']['eligible']
            both = left['decision']['accepted'] and right['decision']['accepted'] if included else None
            same_homology = left['homology']['groups'] == right['homology']['groups'] if both else None
            same_base = a['base_key'] == b['base_key'] if included else None
            same_enhanced = a['enhanced_key'] == b['enhanced_key'] if included else None
            rows.append({'left_case': left['case_id'], 'right_case': right['case_id'],
                         'completion': left['glues'][1], 'eligible': included,
                         'base_equal': same_base, 'enhanced_equal': same_enhanced,
                         'both_accepted': both, 'homology_equal': same_homology,
                         'base_counterexample': bool(same_base and both and not same_homology),
                         'enhanced_counterexample': bool(same_enhanced and both and not same_homology),
                         'comparison_status':'CHECKED' if included else 'EXCLUDED_INADMISSIBLE_FIRST_STAGE'})
    return rows


def quotient_projection(quotient, n):
    roots = [group[0] for group in quotient.groups()]
    owner = {root:i for i,root in enumerate(roots)}
    projection = [[0]*n for _ in roots]
    for i in range(n):
        root,sign = quotient.find(i)
        projection[owner[root]][i] = sign
    return roots,projection


def independent_boundary_quotient(boundary, gluing):
    dims = boundary['dimensions']
    vertices = old.SignedUnion(range(dims[0]))
    edges = old.SignedUnion(range(dims[1]))
    faces = old.SignedUnion(range(dims[2]))
    source,target = gluing['source_face'],gluing['target_face']
    mapping = dict(zip(source,target))
    vertex_owner = {tuple(v):i for i,g in enumerate(boundary['vertex_classes']) for v in g}
    edge_owner = {name:i for i,g in enumerate(boundary['edge_occurrence_classes']) for name in g}
    edge_sign = boundary['edge_occurrence_signs']
    source_face = 't0:'+''.join(map(str,sorted(source)))
    target_face = 't0:'+''.join(map(str,sorted(target)))
    require({source_face,target_face}==set(boundary['bases']['faces']), 'Closing map does not use both boundary faces')
    for a in sorted(source):
        vertices.join(vertex_owner[0,a],vertex_owner[0,mapping[a]])
    equations = []
    for a,b in combinations(sorted(source),2):
        source_occ = source_face + f'/{a}{b}'
        c,d = mapping[a],mapping[b]
        target_occ = target_face + f'/{min(c,d)}{max(c,d)}'
        sign = edge_sign[source_occ]*edge_sign[target_occ]*(1 if c<d else -1)
        i,j = edge_owner[source_occ],edge_owner[target_occ]
        edges.join(i,j,sign)
        equations.append({'source_occurrence':source_occ,'target_occurrence':target_occ,
                          'source_edge_index':i,'target_edge_index':j,'target_sign_over_source':sign})
    if not edges.valid:
        return {'status':'REJECTED_EDGE_REVERSAL','edge_equations':equations}
    si,ti = boundary['bases']['faces'].index(source_face),boundary['bases']['faces'].index(target_face)
    face_sign = old.parity([mapping[v] for v in sorted(source)])
    faces.join(si,ti,face_sign)
    vr,q0 = quotient_projection(vertices,dims[0])
    er,q1 = quotient_projection(edges,dims[1])
    fr,q2 = quotient_projection(faces,dims[2])
    p1 = multiply(q0,boundary['boundaries']['1'],dims[1])
    p2 = multiply(q1,boundary['boundaries']['2'],dims[2])
    B1 = [[row[i] for i in er] for row in p1]
    B2 = [[row[i] for i in fr] for row in p2]
    require(multiply(B1,q1,dims[1])==p1 and multiply(B2,q2,dims[2])==p2,'Boundary quotient chain map failed')
    quotient = {'dimensions':[len(vr),len(er),len(fr),0],
                'boundaries':{'1':B1,'2':B2,'3':[[] for _ in fr]},
                'bases':{'vertices':[boundary['bases']['vertices'][i] for i in vr],
                         'edges':[boundary['bases']['edges'][i] for i in er],
                         'faces':[boundary['bases']['faces'][i] for i in fr],'tetrahedra':[]}}
    return {'status':'QUOTIENT_BUILT','quotient_chain_complex':quotient,
            'quotient_chain_map':{'0':q0,'1':q1,'2':q2},'edge_equations':equations,
            'face_equation':{'source_index':si,'target_index':ti,'sign':face_sign}}


def verify_prediction(prediction, history, completion):
    augmentation = history['augmentation']
    boundary = augmentation['boundary_chain_complex']
    bh = augmentation['boundary_homology']
    independent = independent_boundary_quotient(boundary,completion)
    require(prediction['uses_completed_history'] is False,'Predictor reports completed-history use')
    require(prediction['edge_equations']==independent['edge_equations'],'Closing edge equations differ')
    assumptions = prediction['assumptions']
    require(assumptions['M_connected'] is True and assumptions['K_connected'] is True and assumptions['K_is_boundary_CW_subcomplex'] is True,'Mayer-Vietoris assumptions differ')
    require(group_data(bh['groups']['H0'])=={'free_rank':1,'torsion':[]},'Boundary is not connected')
    if independent['status']=='REJECTED_EDGE_REVERSAL':
        require(prediction['status']=='REJECTED_EDGE_REVERSAL' and prediction['predicted_H1'] is None,'Reversed quotient must not produce this H1 prediction')
        return None
    require(prediction['status']=='PREDICTED','Valid boundary quotient lacks prediction')
    for key in ('quotient_chain_complex','quotient_chain_map','face_equation'):
        require(prediction[key]==independent[key], f'Boundary quotient evidence differs: {key}')
    chain,h = prediction['quotient_chain_complex'],prediction['quotient_homology']
    old.verify_homology_certificate(chain,h)
    expected_h = old.independent_homology(chain)
    require(all(group_data(h['groups'][k])==v for k,v in expected_h.items()),'Boundary quotient homology differs from minors')
    require(group_data(h['groups']['H0'])=={'free_rank':1,'torsion':[]} and assumptions['Q_connected'] is True,'Boundary quotient is not connected')
    domain = bh['groups']['H1']
    columns = domain['free_rank']+len(domain['torsion'])
    source_cycles = generator_cycles(boundary,bh)
    image = multiply(independent['quotient_chain_map']['1'],source_cycles,columns)
    q_map = cycle_coordinates(chain,h,image,columns)
    require(prediction['induced_q_H1']==q_map,'Induced quotient H1 map differs')
    target = augmentation['induced_H1']['target']
    i_map = augmentation['induced_H1']['canonical_matrix']
    require(prediction['interior_H1_group']==target and prediction['canonical_inclusion_H1']==i_map,'Predictor used different interior group/map')
    qgroup = h['groups']['H1']
    n_m = target['free_rank']
    n_torsion = len(qgroup['torsion'])
    n_q = n_torsion+qgroup['free_rank']
    relations = [[0]*(n_torsion+columns) for _ in range(n_m+n_q)]
    for i,value in enumerate(qgroup['torsion']):
        relations[n_m+i][i] = value
    for j in range(columns):
        for i in range(n_m):
            relations[i][n_torsion+j] = i_map[i][j]
        for i in range(n_q):
            relations[n_m+i][n_torsion+j] = -q_map[i][j]
    presentation = prediction['pushout_H1_presentation']
    require(presentation['relations']==relations and presentation['rows']==n_m+n_q and presentation['columns']==n_torsion+columns,'Pushout H1 presentation differs')
    old.verify_smith_certificate(relations,n_m+n_q,n_torsion+columns,presentation['smith_certificate'])
    factors = old.invariant_factors(relations,n_m+n_q,n_torsion+columns)
    group = {'free_rank':n_m+n_q-len(factors),'torsion':[x for x in factors if x>1]}
    group['label'] = old.group_label(group)
    require(prediction['predicted_H1']==group,'State-only H1 prediction differs')
    return group


def expected_counts(histories, transitions, comparisons):
    eligible = [h for h in histories if h['eligibility']['eligible']]
    groups = {}
    for label,key in (('base','base_key'),('enhanced','enhanced_key')):
        buckets = defaultdict(list)
        for h in eligible:
            buckets[h[key]].append(h['history_id'])
        groups[label] = sorted(buckets.values())
    statuses = defaultdict(int)
    for t in transitions:
        if t['state_predictor'] is not None:
            statuses[t['state_predictor']['status']] += 1
    return {'source_assignments':len(transitions),'first_histories':len(histories),
            'eligible_first_histories':len(eligible),'excluded_first_histories':len(histories)-len(eligible),
            'eligible_transitions':sum(t['eligible'] for t in transitions),
            'accepted_completions':sum(t['eligible'] and t['truth']['accepted'] for t in transitions),
            'excluded_transitions':sum(not t['eligible'] for t in transitions),
            'distinct_history_same_completion_candidates':len(comparisons),
            'eligible_distinct_history_same_completion_candidates':sum(c['eligible'] for c in comparisons),
            'equal_base_state_comparisons':sum(c['base_equal'] is True for c in comparisons),
            'equal_base_state_both_accepted':sum(c['base_equal'] is True and c['both_accepted'] is True for c in comparisons),
            'base_homology_counterexamples':sum(c['base_counterexample'] for c in comparisons),
            'equal_enhanced_state_comparisons':sum(c['enhanced_equal'] is True for c in comparisons),
            'equal_enhanced_state_both_accepted':sum(c['enhanced_equal'] is True and c['both_accepted'] is True for c in comparisons),
            'enhanced_homology_counterexamples':sum(c['enhanced_counterexample'] for c in comparisons),
            'state_groups':groups,'prediction_status_counts':dict(sorted(statuses.items())),
            'predictions_checked_against_truth':sum(t['prediction_H1_matches'] is not None for t in transitions),
            'prediction_mismatches':sum(t['prediction_H1_matches'] is False for t in transitions),
            'nontrivial_enhanced_collision_test':'NO_DISTINCT_HISTORY_PAIR_REMAINS; absence of counterexamples is not a general sufficiency proof.'}


def verify_csv_files(run, histories, transitions, comparisons):
    expected = []
    for h in histories:
        a = h['augmentation']
        expected.append({'history_id':h['history_id'],'eligible':str(h['eligibility']['eligible']),
            'exclusion_codes':';'.join(h['eligibility']['reasons']),'base_key':h['base_key'],
            'enhanced_key':h['enhanced_key'] or '',
            'boundary_H1':a['boundary_homology']['groups']['H1']['label'] if a else '',
            'interior_H1':a['interior_homology']['groups']['H1']['label'] if a else '',
            'canonical_map':json.dumps(a['canonical_map_key']['matrix']) if a else ''})
    with (run/'states.csv').open(encoding='utf-8-sig',newline='') as handle:
        require(list(csv.DictReader(handle))==expected,'States CSV differs')
    expected = []
    for t in transitions:
        p = t['state_predictor']
        expected.append({'case_id':t['case_id'],'eligible':str(t['eligible']),
                         'truth_accepted':str(t['truth']['accepted']),
                         'truth_H1':t['truth']['homology']['H1']['label'] if t['truth']['homology'] else '',
                         'prediction_status':p['status'] if p else 'EXCLUDED_INADMISSIBLE_FIRST_STAGE',
                         'predicted_H1':p['predicted_H1']['label'] if p and p['status']=='PREDICTED' else '',
                         'prediction_matches':str(t['prediction_H1_matches']) if t['prediction_H1_matches'] is not None else ''})
    with (run/'transitions.csv').open(encoding='utf-8-sig',newline='') as handle:
        require(list(csv.DictReader(handle))==expected,'Transitions CSV differs')
    fields = ['left_case','right_case','eligible','base_equal','enhanced_equal','both_accepted','homology_equal','base_counterexample','enhanced_counterexample','comparison_status']
    expected = [{key:str(c[key]) if c[key] is not None else '' for key in fields} for c in comparisons]
    with (run/'comparisons.csv').open(encoding='utf-8-sig',newline='') as handle:
        require(list(csv.DictReader(handle))==expected,'Comparisons CSV differs')


def verify_run(run_dir):
    run = Path(run_dir)
    path = run / 'results.json'
    report = json.loads(path.read_text(encoding='utf-8'))
    root = Path(__file__).resolve().parents[1]
    for relative, checksum in report['source_sha256'].items():
        require(hashlib.sha256((root / relative).read_bytes()).hexdigest() == checksum, f'Source checksum differs: {relative}')
    source = report['source_census']
    source_run = Path(source['run_directory'])
    source_path = source_run / 'results.json'
    require(hashlib.sha256(source_path.read_bytes()).hexdigest() == source['results_sha256'], 'Source census checksum differs')
    census = json.loads(source_path.read_text(encoding='utf-8'))
    expected_ids = [''.join(map(str, a)) + '-' + ''.join(map(str, b))
                    for a in permutations((0, 1, 3)) for b in permutations((1, 2, 3))]
    require([case['case_id'] for case in census['cases']] == expected_ids, 'Source census is not complete')
    for case in census['cases']:
        require(json.loads((source_run/'cases'/f"{case['case_id']}.json").read_text(encoding='utf-8'))==case,'Source case checkpoint differs')
        old.compare_case(case)
    source_by_id = {case['case_id']: case for case in census['cases']}
    histories = report['histories']
    require([h['history_id'] for h in histories] == [''.join(map(str,p)) for p in permutations((0,1,3))], 'History coverage differs')
    domain_bases = {}
    history_checks = []
    for history in histories:
        first = source_by_id[history['history_id'] + '-123']
        require(history['glues'] == first['glues'][:1], 'History gluing differs')
        require(history['stage'] == first['after_first'], 'History stage differs from independently checked census')
        independent = old.independent_topology(history['glues'])
        expected_eligibility = eligibility(independent)
        require(all(history['eligibility'][key] == value for key,value in expected_eligibility.items()), 'History eligibility differs')
        base = old.canonical_boundary(independent)
        require(history['base_state'] == base and history['base_key'] == state_hash(base), 'Base state/key differs')
        require(json.loads((run/'histories'/f"{history['history_id']}.json").read_text(encoding='utf-8')) == history, 'History checkpoint differs')
        if history['eligibility']['eligible']:
            check = verify_inclusion(history['augmentation'], history['glues'])
            basis = check['boundary_generator_cycles']
            if history['base_key'] in domain_bases:
                require(domain_bases[history['base_key']] == basis, 'Same marked boundary used different homology bases')
            domain_bases[history['base_key']] = basis
            state = {'version': 'CeCv+marked-H1-inclusion-v1', 'base': base,
                     'homology_map': check['canonical_map_key'], 'marked_boundary_generator_cycles': basis}
            require(history['enhanced_state'] == state and history['enhanced_key'] == state_hash(state), 'Enhanced state/key differs')
        else:
            require(history['augmentation'] is None and history['enhanced_state'] is None and history['enhanced_key'] is None, 'Ineligible history has an augmented manifold state')
        history_checks.append({'history_id':history['history_id'], 'status':'PASS', 'eligible':history['eligibility']['eligible']})
    history_by_id = {h['history_id']:h for h in histories}
    transitions = report['transitions']
    require([t['case_id'] for t in transitions] == expected_ids, 'Transition coverage differs')
    for transition in transitions:
        source_case = source_by_id[transition['case_id']]
        history_id = transition['case_id'].split('-')[0]
        require(transition['history_id'] == history_id, 'Transition history differs')
        require(transition['completion'] == source_case['glues'][1], 'Transition completion differs')
        require(transition['eligible'] == history_by_id[history_id]['eligibility']['eligible'], 'Transition eligibility differs')
        require(transition['base_key']==history_by_id[history_id]['base_key'] and transition['enhanced_key']==history_by_id[history_id]['enhanced_key'],'Transition state keys differ')
        truth = {'accepted':source_case['decision']['accepted'],
                 'rejection_codes':sorted({r['code'] for r in source_case['decision']['rejection_reasons']}),
                 'homology':source_case['homology']['groups'] if source_case['homology'] else None}
        require(transition['truth'] == truth, 'Transition truth differs')
        if transition['eligible']:
            predicted = verify_prediction(transition['state_predictor'],history_by_id[history_id],transition['completion'])
            expected_match = group_data(predicted)==group_data(truth['homology']['H1']) if predicted is not None and truth['homology'] is not None else None
            require(transition['prediction_H1_matches'] is expected_match,'Prediction truth comparison differs')
        else:
            require(transition['state_predictor'] is None and transition['prediction_H1_matches'] is None,'Excluded transition produced prediction')
        require(json.loads((run/'transitions'/f"{transition['case_id']}.json").read_text(encoding='utf-8')) == transition, 'Transition checkpoint differs')
    comparisons = expected_comparisons(histories, census['cases'])
    require(report['comparisons'] == comparisons, 'Comparison census differs')
    for comparison in comparisons:
        name = comparison['left_case'] + '__' + comparison['right_case'] + '.json'
        require(json.loads((run/'comparisons'/name).read_text(encoding='utf-8')) == comparison, 'Comparison checkpoint differs')
    base_counterexamples = [comparison for comparison in comparisons if comparison['base_counterexample']]
    enhanced_counterexamples = [comparison for comparison in comparisons if comparison['enhanced_counterexample']]
    require(report['base_counterexamples'] == base_counterexamples, 'Base counterexample set differs')
    require(report['enhanced_counterexamples'] == enhanced_counterexamples, 'Enhanced counterexample set differs')
    counterexample_file = json.loads((run/'counterexamples.json').read_text(encoding='utf-8'))
    require(counterexample_file['base']==base_counterexamples and counterexample_file['enhanced']==enhanced_counterexamples,'Counterexample checkpoint differs')
    require(counterexample_file['status']=='NO_INFORMATIVE_EQUAL_ENHANCED_STATE_PAIR','Counterexample scope status differs')
    require(report['counts']==expected_counts(histories,transitions,comparisons),'Aggregate counts differ')
    verify_csv_files(run,histories,transitions,comparisons)
    checks = {'histories_checked': len(histories), 'eligible_histories':sum(h['eligibility']['eligible'] for h in histories),
              'transitions_checked':len(transitions), 'comparisons_checked':len(comparisons),
              'eligible_comparisons':sum(c['eligible'] for c in comparisons),
              'base_equal_comparisons':sum(c['base_equal'] is True for c in comparisons),
              'enhanced_equal_comparisons':sum(c['enhanced_equal'] is True for c in comparisons),
              'base_counterexamples':len(base_counterexamples), 'enhanced_counterexamples':len(enhanced_counterexamples)}
    require(checks == {'histories_checked':6,'eligible_histories':3,'transitions_checked':36,'comparisons_checked':90,
                       'eligible_comparisons':18,'base_equal_comparisons':6,'enhanced_equal_comparisons':0,
                       'base_counterexamples':2,'enhanced_counterexamples':0}, 'Finite experiment counts differ')
    result = {'status':'PASS','checked_utc':datetime.now(timezone.utc).isoformat(),
              'results_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
              'verifier_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              **checks,'histories':history_checks,
              'prediction_status_counts':report['counts']['prediction_status_counts'],
              'predictions_checked_against_truth':report['counts']['predictions_checked_against_truth'],
              'prediction_mismatches':report['counts']['prediction_mismatches'],
              'checks':['source hashes and all 36 independent census reconstructions',
                        'all six history checkpoints and eligibility decisions',
                        'Ce/Cv-derived marked boundary cell complexes',
                        'chain inclusions J0/J1/J2 and chain-map identities',
                        'homology Smith/kernel certificates and exact minors',
                        'marked H1 inclusion matrices and target-sign canonicalization',
                        'fixed boundary generator cycles and enhanced-state hashes',
                        'all 36 transition checkpoints and held-out truth',
                        'boundary quotients and q* from boundary/completion alone',
                        'Mayer-Vietoris presentations and predicted H1 via exact minors',
                        'all 90 genuine-history comparison checkpoints',
                        'aggregate groups/counts, both counterexample lists and all CSV cells'],
              'scope':'Independent marked boundary chain inclusion and exact homology checks. Zero genuine same-enhanced-state pairs remain in this six-history family; absence of counterexamples is not general sufficiency.'}
    (run/'independent-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    args = parser.parse_args()
    result = verify_run(args.run)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
