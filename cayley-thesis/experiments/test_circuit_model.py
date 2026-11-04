"""Independent exact examples for electrical bounds and shortest-path search.

Edges are undirected, have unit resistance, and are counted once.  The
four-cycle deliberately separates electrical L2 energy from shortest paths.
"""
from fractions import Fraction
from math import ceil
import json
import unittest

import circuit_model as circuit


C4 = [[1, 3], [2, 0], [3, 1], [0, 2]]
PATH2 = [[1], [0, 2], [1]]


class CircuitModelTests(unittest.TestCase):
    def test_exact_solver_residual_and_fraction(self):
        # Known nonintegral solution; check against the original equations.
        matrix, rhs = [[2, -1], [-1, 2]], [1, 0]
        answer = circuit.solve(matrix, rhs)
        self.assertEqual(answer, [Fraction(2, 3), Fraction(1, 3)])
        self.assertTrue(all(isinstance(x, Fraction) for x in answer))
        self.assertEqual([sum(a*x for a, x in zip(row, answer))
                          for row in matrix], rhs)

    def test_graph_edges_deduplicate_both_orientations(self):
        self.assertEqual(circuit.graph_edges(C4),
                         [(0, 1), (0, 3), (1, 2), (2, 3)])

    def test_parallel_paths_are_not_graph_distance(self):
        cycle = circuit.resistance_table(C4, 0)
        path = circuit.resistance_table(PATH2, 0)
        self.assertEqual(cycle['resistances'],
                         [Fraction(0), Fraction(3, 4), Fraction(1), Fraction(3, 4)])
        self.assertEqual(path['resistances'][2], Fraction(2))
        self.assertEqual(circuit.distances(C4, 0), [0, 1, 2, 1])
        self.assertEqual(circuit.distances(PATH2, 0), [0, 1, 2])
        self.assertNotEqual(cycle['resistances'][2], 2)

    def test_kirchhoff_and_unit_current_energy_certificates(self):
        for adjacency in (C4, PATH2):
            table = circuit.resistance_table(adjacency, 0)
            edges = circuit.graph_edges(adjacency)
            for target in range(1, len(adjacency)):
                voltage = table['potentials'][target]
                divergence = [sum(voltage[u] - voltage[v]
                                  for v in adjacency[u])
                              for u in range(len(adjacency))]
                expected = [int(u == 0) - int(u == target)
                            for u in range(len(adjacency))]
                self.assertEqual(divergence, expected)
                energy = sum((voltage[u] - voltage[v])**2 for u, v in edges)
                self.assertEqual(energy, table['resistances'][target])
                self.assertEqual(voltage[0] - voltage[target], energy)

    def test_ceil_resistance_admissible_and_consistent(self):
        # Re-root each target: h(v)=ceil(R(v,target)), not R(v,identity).
        for target in range(4):
            table = circuit.resistance_table(C4, target)
            heuristic = [ceil(r) for r in table['resistances']]
            # Exact distances here are supplied independently, not by BFS.
            truth = [min((v-target) % 4, (target-v) % 4) for v in range(4)]
            self.assertEqual(heuristic[target], 0)
            for u in range(4):
                self.assertLessEqual(heuristic[u], truth[u])
                for v in C4[u]:
                    self.assertLessEqual(heuristic[u], 1 + heuristic[v])

    def test_ida_keeps_exact_distance_with_electrical_heuristic(self):
        for source in range(4):
            for target in range(4):
                resistance = circuit.resistance_table(C4, target)['resistances']
                heuristic = lambda v: ceil(resistance[v])
                result = circuit.search_ida(C4, source, target, [1, 0], heuristic)
                expected = min((source-target) % 4, (target-source) % 4)
                self.assertEqual(result['distance'], expected)
                self.assertGreaterEqual(result['generated'], 0)
                self.assertGreaterEqual(result['expanded'], 0)

    def test_nonabelian_translation_lookup_matches_rerooted_solves(self):
        # A commutative cycle cannot catch using the wrong multiplication side.
        catalogue = json.loads((circuit.source.ROOT / 'data/surfaces/catalogue.json')
                               .read_text(encoding='utf-8'))
        group, _, transitions, _, identity = circuit.source.model(catalogue['groups']['s3'])
        elements = group['elements']
        index = {g: i for i, g in enumerate(elements)}
        rooted = circuit.resistance_table(transitions, identity)['resistances']
        for u, g in enumerate(elements):
            actual = circuit.resistance_table(transitions, u)['resistances']
            for t, target in enumerate(elements):
                relative = index[group['mul'][group['inv'][g], target]]
                self.assertEqual(rooted[relative], actual[t])
            # Left translation must preserve every labeled right-generator edge.
            translate = [index[group['mul'][group['inv'][g], x]] for x in elements]
            for v, row in enumerate(transitions):
                for move, next_vertex in enumerate(row):
                    self.assertEqual(translate[next_vertex],
                                     transitions[translate[v]][move])

    def test_l1_flow_and_lipschitz_dual_certify_distance_two(self):
        # Orient cycle edges 0->1->2->3->0. Every unit 0->2 flow has
        # coordinates (a,a,a-1,a-1). L1 >= 2 by triangle inequality;
        # a=0 or 1 attains 2, while L2 at a=1/2 is only 1.
        for a in (Fraction(-1), Fraction(0), Fraction(1, 2), Fraction(1), Fraction(2)):
            flow = [a, a, a-1, a-1]
            self.assertEqual([flow[u]-flow[(u-1) % 4] for u in range(4)],
                             [1, 0, -1, 0])
            self.assertGreaterEqual(sum(abs(f) for f in flow), 2)
        self.assertEqual(sum(abs(f) for f in [1, 1, 0, 0]), 2)
        self.assertEqual(sum(f*f for f in [Fraction(1, 2)]*2 + [Fraction(-1, 2)]*2), 1)
        # An explicit dual witness gives lower bound 2 for every unit flow.
        potential = [2, 1, 0, 1]
        self.assertTrue(all(abs(potential[u]-potential[v]) <= 1
                            for u, v in circuit.graph_edges(C4)))
        self.assertEqual(potential[0]-potential[2], 2)


if __name__ == '__main__':
    unittest.main()
