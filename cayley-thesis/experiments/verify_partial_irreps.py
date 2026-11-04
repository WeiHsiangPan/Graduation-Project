"""Read-only verifier: python verify_partial_irreps.py RUN_DIRECTORY.

Does not import partial_irrep_search, small_irreps, or circuit_model. Shared
trusted core: relation_search.model/surface_systems reconstruct the catalogue
group and transitions. Rational elimination, Gram-adjoint contributions, BFS,
word/rule replay and saved-result arithmetic are implemented here separately.
Timing arithmetic is checked, not the accuracy of the original clock readings.
"""
from collections import deque
from fractions import Fraction as F
from itertools import combinations
import argparse
import json
from math import ceil, isclose
from pathlib import Path
from statistics import median

import relation_search as source


def require(condition, message):
    if not condition:
        raise ValueError(message)


def mm(a, b):
    return [[sum((F(x)*F(y) for x, y in zip(row, col)), F(0))
             for col in zip(*b)] for row in a]


def transpose(a):
    return list(map(list, zip(*a)))


def eye(n):
    return [[F(i == j) for j in range(n)] for i in range(n)]


def inverse(matrix):
    n = len(matrix)
    a = [[F(x) for x in row] + ident for row, ident in zip(matrix, eye(n))]
    for j in range(n):
        pivot = next((i for i in range(j, n) if a[i][j]), None)
        require(pivot is not None, 'Singular certificate matrix')
        a[j], a[pivot] = a[pivot], a[j]
        scale = a[j][j]
        a[j] = [x/scale for x in a[j]]
        for i in range(n):
            if i != j:
                scale = a[i][j]
                a[i] = [x-scale*y for x, y in zip(a[i], a[j])]
    return [row[n:] for row in a]


def bfs(transitions, start):
    d = [-1]*len(transitions)
    d[start] = 0
    queue = deque([start])
    while queue:
        u = queue.popleft()
        for v in transitions[u]:
            if d[v] < 0:
                d[v] = d[u]+1
                queue.append(v)
    require(min(d) >= 0, 'Disconnected transition table')
    return d


def endpoint(transitions, start, word):
    u = start
    for move in word:
        require(isinstance(move, int) and 0 <= move < len(transitions[u]), 'Invalid move')
        u = transitions[u][move]
    return u


def representation_values(library, group, generator_indices):
    elements = group['elements']
    n = len(elements)
    index = {g: i for i, g in enumerate(elements)}
    require(sum(r['dimension']**2 for r in library) == n, 'Incomplete irrep dimensions')
    require(len({r['name'] for r in library}) == len(library), 'Duplicate irrep name')
    values, characters = {}, []
    for rep in library:
        d = rep['dimension']
        matrices = [[[F(x) for x in row] for row in a] for a in rep['matrices']]
        h = [[F(x) for x in row] for row in rep['gram']]
        require(len(matrices) == n and all(len(a) == d and all(len(row) == d for row in a)
                                          for a in [h]+matrices), 'Representation shape')
        require(h == transpose(h), 'Gram not symmetric')
        # Sylvester via exact Schur complements: all pivots positive.
        schur = [row[:] for row in h]
        for j in range(d):
            require(schur[j][j] > 0, 'Gram not positive definite')
            for i in range(j+1, d):
                for k in range(j+1, d):
                    schur[i][k] -= schur[i][j]*schur[j][k]/schur[j][j]
        require(matrices[index[group['identity']]] == eye(d), 'Representation identity')
        for i, g in enumerate(elements):
            require(mm(mm(transpose(matrices[i]), h), matrices[i]) == h, 'Gram isometry')
            for j, t in enumerate(elements):
                require(mm(matrices[i], matrices[j]) == matrices[index[group['mul'][g, t]]],
                        'Representation multiplication')
        characters.append([sum(a[i][i] for i in range(d)) for a in matrices])
        lap = [[len(generator_indices)*int(i == j)-sum(matrices[s][i][j] for s in generator_indices)
                for j in range(d)] for i in range(d)]
        if all(x == 0 for row in lap for x in row):
            require(all(a == eye(d) for a in matrices), 'Unexpected zero Laplacian block')
            values[rep['name']] = [F(0)]*n
            continue
        kinv, hinv = inverse(lap), inverse(h)
        result = []
        for a in matrices:
            delta = [[int(i == j)-a[i][j] for j in range(d)] for i in range(d)]
            adjoint = mm(mm(hinv, transpose(delta)), h)
            product = mm(mm(delta, kinv), adjoint)
            result.append(F(d, n)*sum(product[i][i] for i in range(d)))
        require(all(x >= 0 for x in result), 'Negative irrep contribution')
        values[rep['name']] = result
    for i, chi in enumerate(characters):
        for j, psi in enumerate(characters):
            require(sum(x*y for x, y in zip(chi, psi)) == n*int(i == j), 'Character orthogonality')
    return values


def electrical(transitions, identity):
    n = len(transitions)
    neighbors = [set(row)-{i} for i, row in enumerate(transitions)]
    require(all(u in neighbors[v] for u in range(n) for v in neighbors[u]), 'Nonundirected graph')
    free = [i for i in range(n) if i != identity]
    grounded = [[len(neighbors[u])*int(u == v)-int(v in neighbors[u]) for v in free] for u in free]
    inv = inverse(grounded)
    result = [F(0)]*n
    for j, u in enumerate(free):
        result[u] = inv[j][j]
    return result


def close(a, b, message):
    require(isclose(a, b, rel_tol=1e-10, abs_tol=1e-12), message)


def verify(run_directory):
    data = json.loads((Path(run_directory)/'results.json').read_text(encoding='utf-8'))
    catalogue = json.loads((source.ROOT/'data/surfaces/catalogue.json').read_text(encoding='utf-8'))
    require([g['group'] for g in data['groups']] == data['parameters']['groups'], 'Group list')
    repeats = data['parameters']['repeats']
    require(repeats >= 1, 'Repetition count')
    for saved in data['groups']:
        key = saved['group']
        group, generators, tr, inverses, identity = source.model(catalogue['groups'][key])
        n = len(tr)
        require(saved['transitions'] == tr and saved['inverses'] == list(inverses)
                and saved['identity'] == identity and saved['vertices'] == n, 'Model mismatch')
        require(saved['elements'] == json.loads(json.dumps(group['elements'])), 'Element order mismatch')
        index = {g: i for i, g in enumerate(group['elements'])}
        parts = representation_values(saved['library'], group, [index[s] for s in generators])
        dimensions = {r['name']: r['dimension'] for r in saved['library']}
        named = {r['name']: r for r in saved['representations']}
        nonzero = {name: value for name, value in parts.items() if any(value)}
        require(set(named) == set(nonzero), 'Missing or extra nontrivial contribution')
        for name, values in nonzero.items():
            require(list(map(F, named[name]['values'])) == values, 'Contribution value mismatch')
            require(named[name]['dimension'] == dimensions[name], 'Contribution dimension')
        full, truth = electrical(tr, identity), bfs(tr, identity)
        require([sum(value[v] for value in parts.values()) for v in range(n)] == full,
                'Full representation sum differs from electrical solve')
        require(saved['diameter'] == max(truth), 'Diameter')
        require(set(saved['truth_paths']) == {str(v) for v in range(n)}, 'Truth target set')
        for v in range(n):
            word = saved['truth_paths'][str(v)]
            require(endpoint(tr, identity, word) == v and len(word) == truth[v], 'Truth path')
        rules = saved['rule_data']['rules']
        for left, right in rules:
            require((len(left), left) > (len(right), right), 'Rule not decreasing shortlex')
            require(all(endpoint(tr, u, left) == endpoint(tr, u, right) for u in range(n)), 'Unsound rule')
        expected = {('free_h1', p) for p in (False, True)} | {('full_electrical', p) for p in (False, True)}
        names = list(nonzero)
        for count in range(1, len(names)+1):
            for subset in combinations(names, count):
                expected.update(('+'.join(subset), p) for p in (False, True))
        require(len(saved['arms']) == len(expected) and
                {(a['heuristic'], a['pruning']) for a in saved['arms']} == expected, 'Arm coverage')
        for arm in saved['arms']:
            name, members = arm['heuristic'], arm['members']
            require(len(set(members)) == len(members), 'Duplicate subset member')
            if name == 'free_h1':
                raw = [F(0)]*n
                require(not members and arm['dimension_squared'] == 0, 'Free baseline members')
            elif name == 'full_electrical':
                raw = full
                require(not members and arm['dimension_squared'] is None, 'Electrical baseline members')
            else:
                require(name == '+'.join(members) and all(m in nonzero for m in members), 'Subset name')
                raw = [sum(nonzero[m][v] for m in members) for v in range(n)]
                require(arm['dimension_squared'] == sum(dimensions[m]**2 for m in members), 'Subset budget')
            require(list(map(F, arm['raw_values'])) == raw, 'Arm raw values')
            require(all(0 <= raw[v] <= full[v] <= truth[v] for v in range(n)), 'Admissibility bound')
            violations = 0
            for t, target in enumerate(group['elements']):
                h = [max(int(u != t), ceil(raw[index[group['mul'][group['inv'][g], target]]]))
                     for u, g in enumerate(group['elements'])]
                td = bfs(tr, t)
                require(all(h[u] <= td[u] for u in range(n)), 'Target-specific admissibility')
                violations += sum(h[u] > 1+h[v] for u in range(n) for v in tr[u])
            require(violations == arm['consistency_violations'], 'Consistency count')
            require([c['target'] for c in arm['cases']] == list(range(n)), 'Case coverage')
            for case in arm['cases']:
                word, t = case['word'], case['target']
                require(endpoint(tr, identity, word) == t and len(word) == case['distance'] == truth[t], 'Search path')
                require(len(case['timings']) == repeats and min(case['timings']) >= 0, 'Case timings')
                close(case['seconds'], median(case['timings']), 'Case median')
                if arm['pruning']:
                    require(not any(word[i:i+len(left)] == left for left, _ in rules
                                    for i in range(len(word)-len(left)+1)), 'Forbidden search word')
            for metric in ('generated', 'expanded', 'pruned', 'rules_checks'):
                require(all(isinstance(c[metric], int) and c[metric] >= 0 for c in arm['cases']), 'Negative count')
                require(arm['totals'][metric] == sum(c[metric] for c in arm['cases']), 'Count total')
            for label, parity in (('train_generated', 0), ('heldout_generated', 1)):
                require(arm[label] == sum(c['generated'] for c in arm['cases'] if c['target'] % 2 == parity), 'Split total')
            require(len(arm['sweep_seconds']) == repeats, 'Sweep count')
            for repeat in range(repeats):
                close(arm['sweep_seconds'][repeat], sum(c['timings'][repeat] for c in arm['cases']), 'Sweep sum')
            close(arm['search_seconds'], median(arm['sweep_seconds']), 'Search median')
            close(arm['end_to_end_seconds'], arm['preprocessing_seconds']+arm['search_seconds'], 'End-to-end sum')
            require(arm['table_entries'] == (0 if name == 'free_h1' else n*n), 'Lookup size')
            timing = saved['timing']
            preprocessing = timing['model']
            combination_seconds = arm.get('combination_seconds', 0)
            require(combination_seconds >= 0, 'Negative combination time')
            if not members:
                require(combination_seconds == 0, 'Baseline combination charge')
            preprocessing += combination_seconds
            if members:
                preprocessing += timing['library_all_reps']+sum(named[m]['cost']['seconds'] for m in members)
            elif name == 'full_electrical':
                preprocessing += timing['full_electrical']
            if name != 'free_h1':
                preprocessing += timing['difference_table']+arm['heuristic_table_seconds']
            else:
                require(arm['heuristic_table_seconds'] == 0, 'Free lookup charge')
            if arm['pruning']:
                preprocessing += saved['rule_data']['build_seconds']+saved['rule_data']['validation_seconds']
            close(arm['preprocessing_seconds'], preprocessing, 'Preprocessing charge sum')
        for selection in saved['train_selected']:
            candidates = [a for a in saved['arms'] if a['members'] and a['pruning'] == selection['pruning']
                          and a['dimension_squared'] <= selection['budget']]
            winner = min(candidates, key=lambda a: (a['train_generated'], a['dimension_squared'], a['heuristic']))
            require(selection['winner'] == winner['heuristic'] and
                    selection['train_generated'] == winner['train_generated'] and
                    selection['heldout_generated'] == winner['heldout_generated'], 'Training selection')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_directory', type=Path)
    verify(parser.parse_args().run_directory)
    print('PASS')
