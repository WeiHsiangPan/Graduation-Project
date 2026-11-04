"""Independent exact checks of representation bounds and sound rewrite search."""
from fractions import Fraction as F
from itertools import combinations
import json
from math import ceil
import unittest

import circuit_model as circuit
import partial_irrep_search as experiment
import relation_search as source
import small_irreps


def multiply(a, b):
    return [[sum(F(x)*F(y) for x, y in zip(row, column))
             for column in zip(*b)] for row in a]


def transpose(a):
    return list(map(list, zip(*a)))


class PartialIrrepTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        catalogue = json.loads((source.ROOT / 'data/surfaces/catalogue.json')
                               .read_text(encoding='utf-8'))
        cls.models = {}
        for key in ('d4', 's3', 's4'):
            group, generators, transitions, inverses, identity = source.model(catalogue['groups'][key])
            reps = small_irreps.representations(key, group)
            index = {g: i for i, g in enumerate(group['elements'])}
            parts = [experiment.contribution(rep, [index[g] for g in generators], len(index))
                     for rep in reps]
            cls.models[key] = (group, transitions, inverses, identity, reps, parts)

    def test_independent_multiplicativity_and_gram_isometry(self):
        for key, (group, _, _, identity, reps, _) in self.models.items():
            small_irreps.validate(reps, group)
            elements = group['elements']
            index = {g: i for i, g in enumerate(elements)}
            self.assertEqual(sum(rep['dimension']**2 for rep in reps), len(elements), key)
            characters = [[sum(matrix[i][i] for i in range(rep['dimension']))
                           for matrix in rep['matrices']] for rep in reps]
            for i, chi in enumerate(characters):
                for j, psi in enumerate(characters):
                    self.assertEqual(sum(F(a)*F(b) for a, b in zip(chi, psi)),
                                     len(elements)*int(i == j), (key, i, j))
            for rep in reps:
                matrices, gram = rep['matrices'], rep['gram']
                d = rep['dimension']
                self.assertEqual(matrices[identity], [[int(i == j) for j in range(d)]
                                                     for i in range(d)])
                for a, g in enumerate(elements):
                    # This is the exact nonorthonormal-basis condition, not M^T M=I.
                    self.assertEqual(multiply(multiply(transpose(matrices[a]), gram), matrices[a]), gram)
                    for b, h in enumerate(elements):
                        self.assertEqual(multiply(matrices[a], matrices[b]),
                                         matrices[index[group['mul'][g, h]]], (key, rep['name'], a, b))

    def test_full_irrep_sum_matches_independent_electrical_solve(self):
        for key, (_, transitions, _, identity, _, parts) in self.models.items():
            exact = circuit.resistance_table(transitions, identity)['resistances']
            actual = [sum((part[v] for part in parts), F(0)) for v in range(len(transitions))]
            self.assertEqual(actual, exact, key)
            self.assertTrue(all(isinstance(x, F) for part in parts for x in part))

    def test_every_subset_is_nonnegative_and_below_resistance_and_distance(self):
        for key, (_, transitions, _, identity, reps, parts) in self.models.items():
            exact = circuit.resistance_table(transitions, identity)['resistances']
            truth = circuit.distances(transitions, identity)
            for size in range(len(reps)+1):
                for subset in combinations(range(len(reps)), size):
                    for v in range(len(transitions)):
                        lower = sum((parts[i][v] for i in subset), F(0))
                        self.assertGreaterEqual(lower, 0, (key, subset, v))
                        self.assertLessEqual(lower, exact[v], (key, subset, v))
                        self.assertLessEqual(exact[v], truth[v], (key, subset, v))

    def test_ida_with_sound_rules_and_partial_irrep_bounds_is_optimal(self):
        # Small but genuinely noncommutative groups; S4 spectral correctness is
        # independently covered above without making this search test expensive.
        for key in ('d4', 's3'):
            group, transitions, inverses, identity, reps, parts = self.models[key]
            elements = group['elements']
            index = {g: i for i, g in enumerate(elements)}
            relations = source.closed_words(transitions, identity, inverses, 4)[:3]
            rules = source.rules_for(relations, inverses)
            source.verify_rules(rules, transitions)
            truth = circuit.distances(transitions, identity)
            for selected in [[], *[[i] for i in range(len(reps))], list(range(len(reps)))]:
                lower = [sum((parts[i][v] for i in selected), F(0))
                         for v in range(len(transitions))]
                for target in range(len(transitions)):
                    heuristic = lambda u: ceil(lower[index[group['mul'][group['inv'][elements[u]], elements[target]]]])
                    result = experiment.ida(transitions, identity, target, inverses, heuristic, rules)
                    endpoint = source.endpoint(result['word'], transitions, identity)
                    self.assertEqual(endpoint, target)
                    self.assertEqual(result['distance'], truth[target])
                    self.assertEqual(len(result['word']), truth[target])
                    for metric in ('generated', 'expanded', 'pruned', 'rules_checks'):
                        self.assertGreaterEqual(result[metric], 0)


if __name__ == '__main__':
    unittest.main()
