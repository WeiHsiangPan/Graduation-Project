"""State-only closure tests against fixed finite truth and deliberate thin inputs."""
import copy
import unittest
from itertools import permutations

import example7_rebuild as core
import one_tetrahedron_census as census
from boundary_homology import build_boundary_inclusion
from boundary_completion import predict_h1_completion


def thin(record):
    result={key:copy.deepcopy(record[key]) for key in
            ('boundary_chain_complex','boundary_homology')}
    result['induced_H1']={key:copy.deepcopy(record['induced_H1'][key]) for key in
                          ('domain','target','boundary_generator_cycles','canonical_matrix')}
    return result


class BoundaryCompletionTests(unittest.TestCase):
    def test_all_eighteen_prefix_completion_attempts(self):
        predicted,rejected=0,0
        for first in ((0,1,3),(1,3,0),(3,0,1)):
            glue=census.make_glues(first,(1,2,3))[0]
            stage=core.analyse([glue],tetrahedra=1)
            state=census.boundary_state(stage)
            inclusion=thin(build_boundary_inclusion([glue],stage))
            # No interior chain data, original history, or final truth exists in this input.
            self.assertNotIn('interior_chain_complex',inclusion)
            for last in permutations((1,2,3)):
                closing=census.make_glues(first,last)[1]
                outcome=predict_h1_completion(state,inclusion,closing)
                truth=census.make_case(first,last)
                if outcome['status']=='PREDICTED':
                    predicted+=1
                    self.assertTrue(truth['decision']['accepted'])
                    self.assertEqual(outcome['predicted_H1'],truth['homology']['groups']['H1'])
                else:
                    rejected+=1
                    self.assertEqual(outcome['status'],'REJECTED_EDGE_REVERSAL')
                    self.assertFalse(truth['decision']['accepted'])
        self.assertEqual((predicted,rejected),(9,9))

    def test_130_and_301_same_completion_give_four_and_five(self):
        groups=[]
        for first in ((1,3,0),(3,0,1)):
            glues=census.make_glues(first,(2,3,1))
            stage=core.analyse(glues[:1],tetrahedra=1)
            result=predict_h1_completion(census.boundary_state(stage),thin(build_boundary_inclusion(glues[:1],stage)),glues[1])
            groups.append(result['predicted_H1']['label'])
        self.assertEqual(groups,['Z/4','Z/5'])

    def test_domain_and_map_shape_corruption_rejected(self):
        glues=census.make_glues((1,3,0),(2,3,1))
        stage=core.analyse(glues[:1],tetrahedra=1)
        state=census.boundary_state(stage)
        inclusion=thin(build_boundary_inclusion(glues[:1],stage))
        bad=copy.deepcopy(inclusion)
        bad['induced_H1']['canonical_matrix']=[[1]]
        with self.assertRaises(ValueError):
            predict_h1_completion(state,bad,glues[1])
        bad=copy.deepcopy(inclusion)
        bad['boundary_chain_complex']['boundaries']['1'][0][0]=1
        with self.assertRaises(ValueError):
            predict_h1_completion(state,bad,glues[1])


if __name__=='__main__':
    unittest.main()
