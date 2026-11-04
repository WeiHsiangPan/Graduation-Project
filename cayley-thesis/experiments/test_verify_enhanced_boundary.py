"""Independent marked-map checks, including basis changes and corrupt evidence."""
import copy
import unittest

import example7_rebuild as core
import one_tetrahedron_census as census
from boundary_homology import build_boundary_inclusion
from verify_enhanced_boundary import (verify_inclusion, eligibility, expected_comparisons,
                                      state_hash, verify_prediction)
import verify_one_tetrahedron as old
from boundary_completion import predict_h1_completion


class EnhancedBoundaryVerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.glues, cls.records = {}, {}
        for choice in ('013','130','301'):
            glues = census.make_glues(tuple(map(int,choice)),(1,2,3))[:1]
            cls.glues[choice] = glues
            cls.records[choice] = build_boundary_inclusion(glues,core.analyse(glues,tetrahedra=1))

    def test_all_eligible_inclusions_independently_checked(self):
        for name, record in self.records.items():
            self.assertEqual(verify_inclusion(record,self.glues[name])['status'],'PASS')

    def test_130_and_301_marked_maps_differ(self):
        self.assertNotEqual(self.records['130']['canonical_map_key'],self.records['301']['canonical_map_key'])
        self.assertEqual(self.records['130']['boundary_chain_complex'],self.records['301']['boundary_chain_complex'])

    def test_interior_generator_sign_is_not_new_state(self):
        original = self.records['130']
        changed = copy.deepcopy(original)
        cert = changed['interior_homology']['certificates']['H1']['quotient_smith']
        free_index = cert['rank']
        cert['U'][free_index] = [-x for x in cert['U'][free_index]]
        changed['induced_H1']['matrix'] = [[-x for x in row] for row in changed['induced_H1']['matrix']]
        changed['induced_H1']['interior_generator_cycles'] = [[-x for x in row] for row in changed['induced_H1']['interior_generator_cycles']]
        self.assertEqual(verify_inclusion(changed,self.glues['130'])['canonical_map_key'],original['canonical_map_key'])

    def test_corrupt_chain_inclusion_rejected(self):
        bad = copy.deepcopy(self.records['130'])
        bad['chain_inclusion']['1'][0][0] += 1
        with self.assertRaises(ValueError):
            verify_inclusion(bad,self.glues['130'])

    def test_corrupt_induced_matrix_rejected(self):
        bad = copy.deepcopy(self.records['130'])
        bad['induced_H1']['matrix'][0][0] += 1
        with self.assertRaises(ValueError):
            verify_inclusion(bad,self.glues['130'])

    def test_corrupt_boundary_marking_rejected(self):
        bad = copy.deepcopy(self.records['301'])
        bad['induced_H1']['boundary_generator_cycles'][0][0] += 1
        with self.assertRaises(ValueError):
            verify_inclusion(bad,self.glues['301'])

    def test_corrupt_boundary_complex_rejected(self):
        bad = copy.deepcopy(self.records['013'])
        bad['boundary_chain_complex']['boundaries']['2'][0][0] += 1
        with self.assertRaises(ValueError):
            verify_inclusion(bad,self.glues['013'])

    def test_corrupt_canonical_key_rejected(self):
        bad = copy.deepcopy(self.records['130'])
        bad['canonical_map_key']['matrix'][0][0] += 1
        with self.assertRaises(ValueError):
            verify_inclusion(bad,self.glues['130'])

    def test_all_genuine_pairs_include_two_old_counterexamples(self):
        from itertools import permutations, product
        cases = [census.make_case(a,b) for a,b in product(census.FIRST_TARGETS,census.SECOND_TARGETS)]
        histories = []
        for first in permutations((0,1,3)):
            name = ''.join(map(str,first))
            partial = old.independent_topology(census.make_glues(first,(1,2,3))[:1])
            eligible = eligibility(partial)
            histories.append({'history_id':name,'eligibility':eligible,
                              'base_key':state_hash(old.canonical_boundary(partial)),
                              'enhanced_key':state_hash(self.records[name]['canonical_map_key']) if eligible['eligible'] else None})
        rows = expected_comparisons(histories,cases)
        self.assertEqual(len(rows),90)
        self.assertEqual(sum(row['eligible'] for row in rows),18)
        self.assertEqual([(row['left_case'],row['right_case']) for row in rows if row['base_counterexample']],
                         [('130-231','301-231'),('130-312','301-312')])
        self.assertEqual(sum(row['enhanced_equal'] is True for row in rows),0)

    def prediction_fixture(self, first='130', last='231'):
        full = census.make_glues(tuple(map(int,first)),tuple(map(int,last)))
        stage = core.analyse(full[:1],tetrahedra=1)
        augmentation = self.records[first]
        thin = {'boundary_chain_complex':augmentation['boundary_chain_complex'],
                'boundary_homology':augmentation['boundary_homology'],
                'induced_H1':{key:augmentation['induced_H1'][key] for key in
                              ('domain','target','boundary_generator_cycles','canonical_matrix')}}
        prediction = predict_h1_completion(census.boundary_state(stage),thin,full[1])
        return prediction,{'augmentation':augmentation},full[1]

    def test_all_state_only_predictions_and_reversals_independently_checked(self):
        from itertools import permutations
        totals = {'PREDICTED':0,'REJECTED_EDGE_REVERSAL':0}
        for first in self.records:
            for last in permutations((1,2,3)):
                prediction,history,completion = self.prediction_fixture(first,''.join(map(str,last)))
                result = verify_prediction(prediction,history,completion)
                totals[prediction['status']] += 1
                truth = census.make_case(tuple(map(int,first)),last)
                if result is not None:
                    self.assertEqual(result,truth['homology']['groups']['H1'])
                else:
                    self.assertFalse(truth['decision']['accepted'])
        self.assertEqual(totals,{'PREDICTED':9,'REJECTED_EDGE_REVERSAL':9})

    def test_corrupt_quotient_chain_rejected(self):
        prediction,history,completion = self.prediction_fixture()
        prediction['quotient_chain_complex']['boundaries']['2'][0][0] += 1
        with self.assertRaises(ValueError):
            verify_prediction(prediction,history,completion)

    def test_corrupt_quotient_map_rejected(self):
        prediction,history,completion = self.prediction_fixture()
        prediction['induced_q_H1'][0][0] += 1
        with self.assertRaises(ValueError):
            verify_prediction(prediction,history,completion)

    def test_corrupt_pushout_relation_rejected(self):
        prediction,history,completion = self.prediction_fixture()
        prediction['pushout_H1_presentation']['relations'][0][0] += 1
        with self.assertRaises(ValueError):
            verify_prediction(prediction,history,completion)

    def test_corrupt_predicted_torsion_rejected(self):
        prediction,history,completion = self.prediction_fixture()
        prediction['predicted_H1']['torsion'] = [5]
        with self.assertRaises(ValueError):
            verify_prediction(prediction,history,completion)


if __name__ == '__main__':
    unittest.main()
