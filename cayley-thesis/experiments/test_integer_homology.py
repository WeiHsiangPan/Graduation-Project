"""Exact examples and certificate corruption checks for integral homology."""
import copy
from itertools import combinations
from math import gcd
import random
import unittest

from integer_homology import (determinant, integral_homology, smith_normal_form,
                              verify_homology, verify_smith)


class IntegralHomologyTests(unittest.TestCase):
    def test_lens_space_chain_and_top_class(self):
        maps = {1: [[0, 0]], 2: [[1, 0], [0, 5]], 3: [[0], [0]]}
        answer = integral_homology(maps, [1, 2, 2, 1])
        self.assertEqual([answer['groups'][f'H{k}']['label'] for k in range(4)],
                         ['Z', 'Z/5', '0', 'Z'])
        self.assertTrue(verify_homology(maps, [1, 2, 2, 1], answer))

    def test_integral_kernel_not_rational_rank_subtraction(self):
        maps = {1: [[2, 4]], 2: [[-4], [2]]}
        answer = integral_homology(maps, [1, 2, 1])
        self.assertEqual([answer['groups'][f'H{k}']['label'] for k in range(3)],
                         ['Z/2', 'Z/2', '0'])

    def test_h2_torsion(self):
        maps = {1: [[0]], 2: [[0]], 3: [[6]]}
        answer = integral_homology(maps, [1, 1, 1, 1])
        self.assertEqual([answer['groups'][f'H{k}']['label'] for k in range(4)],
                         ['Z', 'Z', 'Z/6', '0'])

    def test_nontrivial_graph_boundary(self):
        maps = {1: [[-1, -1, 0], [1, 0, -1], [0, 1, 1]],
                2: [[1], [-1], [1]], 3: [[]]}
        answer = integral_homology(maps, [3, 3, 1, 0])
        self.assertEqual([answer['groups'][f'H{k}']['label'] for k in range(4)],
                         ['Z', '0', '0', '0'])

    def test_empty_and_disconnected_chain(self):
        answer = integral_homology({1: [[], []], 2: [], 3: []}, [2, 0, 0, 0])
        self.assertEqual(answer['groups']['H0']['label'], 'Z^2')
        self.assertEqual(integral_homology({}, [0])['groups']['H0']['label'], '0')

    def test_invalid_chain_and_corrupt_certificate(self):
        with self.assertRaises(ValueError):
            integral_homology({1: [[2]], 2: [[3]]}, [1, 1, 1])
        maps = {1: [[0]], 2: [[7]]}
        answer = integral_homology(maps, [1, 1, 1])
        corrupted = copy.deepcopy(answer)
        corrupted['groups']['H1']['torsion'] = [8]
        with self.assertRaises(ValueError):
            verify_homology(maps, [1, 1, 1], corrupted)
        corrupted = copy.deepcopy(answer)
        corrupted['certificates']['H1']['kernel_basis'][0][0] *= 2
        with self.assertRaises(ValueError):
            verify_homology(maps, [1, 1, 1], corrupted)

    def test_smith_matches_determinantal_divisors(self):
        rng = random.Random(7301)
        for m in range(4):
            for n in range(4):
                for _ in range(12):
                    matrix = [[rng.randrange(-5, 6) for _ in range(n)] for _ in range(m)]
                    smith = smith_normal_form(matrix, n)
                    previous, expected = 1, []
                    for k in range(1, min(m, n) + 1):
                        divisor = 0
                        for rs in combinations(range(m), k):
                            for cs in combinations(range(n), k):
                                minor = [[matrix[i][j] for j in cs] for i in rs]
                                divisor = gcd(divisor, abs(determinant(minor)))
                        if divisor == 0:
                            break
                        expected.append(divisor // previous)
                        previous = divisor
                    self.assertEqual(smith['diagonal'], expected)
                    self.assertTrue(verify_smith(matrix, n, smith))


if __name__ == '__main__':
    unittest.main()
