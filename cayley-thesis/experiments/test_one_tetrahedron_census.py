"""Concrete mathematical regression examples for the complete one-tet census."""
import unittest
from itertools import product, permutations

import one_tetrahedron_census as census
from verify_one_tetrahedron import compare_case


class OneTetrahedronTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = [census.make_case(a,b) for a,b in product(census.FIRST_TARGETS,census.SECOND_TARGETS)]
        cls.by_id = {case['case_id']:case for case in cls.cases}

    def test_complete_labeled_scope_and_independent_checks(self):
        self.assertEqual(len(self.by_id),36)
        for case in self.cases:
            self.assertEqual(compare_case(case)['status'],'PASS')
        counts = census.aggregate(self.cases)
        self.assertEqual((counts['accepted'],counts['rejected']),(9,27))
        self.assertEqual(counts['accepted_H1_counts'],{'0':5,'Z/4':2,'Z/5':2})

    def test_two_vertex_example_really_uses_nonzero_B1(self):
        case = self.by_id['013-123']
        self.assertTrue(case['decision']['accepted'])
        self.assertEqual(len(case['after']['links']),2)
        self.assertTrue(any(x for row in case['chain_complex']['boundaries']['1'] for x in row))
        self.assertEqual([case['homology']['groups'][f'H{k}']['label'] for k in range(4)],['Z','0','0','Z'])

    def test_spherical_links_do_not_excuse_reversed_edges(self):
        case = self.by_id['103-132']
        self.assertTrue(case['decision']['all_links_spheres'])
        self.assertFalse(case['decision']['accepted'])
        witness = case['edge_reversal_witness']
        self.assertEqual(witness['sign_product'],-1)
        self.assertEqual(len(witness['closed_walk']),1)

    def test_consistent_edges_do_not_excuse_klein_bottle_link(self):
        case = self.by_id['031-213']
        self.assertTrue(case['decision']['edge_orientation_consistent'])
        link = case['after']['links'][0]
        self.assertTrue(link['is_surface'])
        self.assertEqual((link['chi'],link['boundary_components'],link['orientable']),(0,0,False))
        self.assertIsNone(case['homology'])

    def test_equal_state_and_completion_forget_integral_homology(self):
        witness = census.boundary_inclusion_witness(self.cases)
        values = [record['boundary_inclusion_to_Z'] for record in witness['records']]
        self.assertEqual([(v['x_03'],v['y_13']) for v in values],[(2,1),(1,2)])
        self.assertEqual([r['closing_relation_value'] for r in witness['records']],[4,5])
        self.assertEqual(len(census.compression_witnesses(self.cases)),2)

    def test_all_relabelings_and_pair_reversals_preserve_canonical_key(self):
        glues = self.by_id['130-231']['glues']
        expected = census.canonical_relabeling_key(glues)
        for r in permutations(range(4)):
            transformed = [{**g,'source_face':[r[v] for v in g['source_face']],
                            'target_face':[r[v] for v in g['target_face']]} for g in glues]
            self.assertEqual(census.canonical_relabeling_key(transformed),expected)
            reversed_glues = [{**g,'source_face':g['target_face'],'target_face':g['source_face']} for g in transformed]
            self.assertEqual(census.canonical_relabeling_key(reversed_glues),expected)


if __name__ == '__main__':
    unittest.main()
