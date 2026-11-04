"""Mathematical examples and corruption checks for marked boundary H1 maps."""
import copy
import unittest

import example7_rebuild as core
import one_tetrahedron_census as census
from boundary_homology import (build_boundary_inclusion,canonical_cyclic_map,
                               verify_boundary_inclusion,boundary_complex)


class BoundaryHomologyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maps = {}
        for target in ((0,1,3),(1,3,0),(3,0,1)):
            glues = census.make_glues(target,(1,2,3))[:1]
            cls.maps[''.join(map(str,target))] = build_boundary_inclusion(glues,core.analyse(glues,tetrahedra=1))

    def test_sphere_boundary_and_nontrivial_B1(self):
        data = self.maps['013']
        self.assertEqual(data['boundary_homology']['groups']['H1']['label'],'0')
        self.assertEqual(data['interior_homology']['groups']['H1']['label'],'0')
        self.assertEqual(data['induced_H1']['matrix'],[])
        self.assertTrue(any(x for row in data['boundary_chain_complex']['boundaries']['1'] for x in row))
        self.assertTrue(verify_boundary_inclusion(data))

    def test_common_boundary_basis_distinguishes_130_and_301(self):
        a,b = self.maps['130'],self.maps['301']
        self.assertEqual(a['boundary_chain_complex'],b['boundary_chain_complex'])
        self.assertEqual(a['induced_H1']['boundary_generator_cycles'],b['induced_H1']['boundary_generator_cycles'])
        self.assertEqual(a['boundary_homology']['groups']['H1']['label'],'Z^2')
        self.assertEqual(a['interior_homology']['groups']['H1']['label'],'Z')
        self.assertNotEqual(a['canonical_map_key'],b['canonical_map_key'])
        for data in (a,b):
            self.assertTrue(verify_boundary_inclusion(data))

    def test_target_generator_sign_is_not_a_false_distinction(self):
        data = self.maps['130']['induced_H1']
        matrix = data['matrix']
        a,_ = canonical_cyclic_map(data['domain'],data['target'],matrix)
        b,_ = canonical_cyclic_map(data['domain'],data['target'],[[-x for x in row] for row in matrix])
        self.assertEqual(a,b)

    def test_corrupted_inclusion_and_induced_map_rejected(self):
        data = copy.deepcopy(self.maps['130'])
        data['chain_inclusion']['1'][0][0] += 1
        with self.assertRaises(ValueError):
            verify_boundary_inclusion(data)
        data = copy.deepcopy(self.maps['130'])
        data['induced_H1']['matrix'][0][0] += 1
        with self.assertRaises(ValueError):
            verify_boundary_inclusion(data)

    def test_invalid_reversed_edge_does_not_get_cell_map(self):
        glues = census.make_glues((1,0,3),(1,2,3))[:1]
        with self.assertRaises(ValueError):
            build_boundary_inclusion(glues,core.analyse(glues,tetrahedra=1))

    def test_Ce_Cv_coverage_and_direction_are_checked(self):
        glues = census.make_glues((1,3,0),(1,2,3))[:1]
        state = census.boundary_state(core.analyse(glues,tetrahedra=1))
        state['Ce'].pop()
        with self.assertRaises(ValueError):
            boundary_complex(state)


if __name__=='__main__':
    unittest.main()
