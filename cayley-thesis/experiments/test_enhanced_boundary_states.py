"""Coverage, leakage controls and negative controls for the state experiment."""
import copy
from itertools import product
import unittest

import enhanced_boundary_states as study
import one_tetrahedron_census as census


class EnhancedStateStudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=[census.make_case(a,b) for a,b in product(census.FIRST_TARGETS,census.SECOND_TARGETS)]
        cls.histories=[study.make_history(first,next(c for c in cls.cases if c['case_id'].startswith(first+'-')))
                       for first in sorted({c['case_id'].split('-')[0] for c in cls.cases})]
        cls.by_id={h['history_id']:h for h in cls.histories}
        cls.transitions=[study.make_transition(c,cls.by_id[c['case_id'].split('-')[0]]) for c in cls.cases]
        cls.comparisons=study.compare_transitions(cls.transitions,cls.histories)

    def test_augmentation_distinguishes_the_real_old_collision(self):
        a,b=self.by_id['130'],self.by_id['301']
        self.assertEqual(a['base_state'],b['base_state'])
        self.assertEqual(a['enhanced_state']['marked_boundary_generator_cycles'],b['enhanced_state']['marked_boundary_generator_cycles'])
        self.assertNotEqual(a['enhanced_key'],b['enhanced_key'])
        self.assertEqual(a['augmentation']['canonical_map_key']['matrix'],[[2,3]])
        self.assertEqual(b['augmentation']['canonical_map_key']['matrix'],[[1,3]])

    def test_all_assignments_and_genuine_comparisons_are_preserved(self):
        counts=study.aggregate(self.histories,self.transitions,self.comparisons)
        self.assertEqual((counts['source_assignments'],counts['first_histories']),(36,6))
        self.assertEqual((counts['eligible_transitions'],counts['excluded_transitions']),(18,18))
        self.assertEqual((len(self.comparisons),counts['eligible_distinct_history_same_completion_candidates']),(90,18))
        self.assertEqual((counts['equal_base_state_comparisons'],counts['base_homology_counterexamples']),(6,2))
        self.assertEqual(counts['equal_enhanced_state_comparisons'],0)
        self.assertIn('NO_DISTINCT_HISTORY_PAIR_REMAINS',counts['nontrivial_enhanced_collision_test'])

    def test_failed_prefixes_are_excluded_before_seeing_completion(self):
        for first in ('031','103','310'):
            h=self.by_id[first]
            self.assertFalse(h['eligibility']['eligible'])
            self.assertIsNone(h['augmentation'])
            self.assertTrue(all(t['state_predictor'] is None for t in self.transitions if t['history_id']==first))

    def test_state_extraction_does_not_use_future_homology(self):
        source=next(c for c in self.cases if c['case_id']=='130-231')
        corrupted=copy.deepcopy(source)
        corrupted['homology']={'this_is_future_truth':'must not be read'}
        corrupted['glues'][1]=copy.deepcopy(next(c for c in self.cases if c['case_id']=='130-312')['glues'][1])
        self.assertEqual(study.make_history('130',corrupted)['enhanced_state'],self.by_id['130']['enhanced_state'])

    def test_predictor_uses_thin_state_and_checks_nine_actual_results(self):
        thin=study.thin_prediction_input(self.by_id['130'])
        self.assertEqual(set(thin),{'boundary_chain_complex','boundary_homology','induced_H1'})
        self.assertNotIn('interior_chain_complex',thin)
        checked=[t for t in self.transitions if t['prediction_H1_matches'] is not None]
        self.assertEqual(len(checked),9)
        self.assertTrue(all(t['prediction_H1_matches'] for t in checked))

    def test_deliberately_removing_map_recovers_both_counterexamples(self):
        histories=copy.deepcopy(self.histories)
        for history in histories:
            if history['eligibility']['eligible']:
                history['enhanced_key']=history['base_key']
        comparisons=study.compare_transitions(self.transitions,histories)
        failures=[(c['left_case'],c['right_case']) for c in comparisons if c['enhanced_counterexample']]
        self.assertEqual(failures,[('130-231','301-231'),('130-312','301-312')])


if __name__=='__main__':
    unittest.main()
