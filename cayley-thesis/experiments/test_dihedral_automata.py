import json
import unittest

import dihedral_automata as experiment
import verify_dihedral_automata as verifier
from verify_relation_automata import verify_method


class DihedralAutomataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = {n: experiment.build_source(n) for n in (8,16)}

    def test_models_faces_and_bfs(self):
        for n, source in self.sources.items():
            self.assertEqual(source["diameter"], n//2+1)
            self.assertEqual(source["surface_validation"]["genus"], 0)
            self.assertEqual(source["surface_validation"]["face_count"], n+2)
            verifier.verify_source(json.loads(experiment.pack(source)))

    def test_critical_budget_transitions(self):
        for n, source in self.sources.items():
            finite_k = 3 if n == 8 else 71
            for k, expected in ((finite_k-1,False),(finite_k,True)):
                stage = experiment.evaluate(source, list(range(k)), "test", "ordinary_shortlex_prefix", 0)
                self.assertEqual(stage["language"]["finite"], expected)
                if expected:
                    self.assertEqual(stage["upper_bound"], source["diameter"])
                    self.assertEqual(stage["gap"], 0)
                else:
                    self.assertIsNone(stage["gap"])
                    self.assertTrue(stage["language"]["certificate"]["cycle"])

    def test_short_cutoff_does_not_implicitly_get_long_face(self):
        for n, source in self.sources.items():
            stage = experiment.evaluate(source, source["short_relator_ids"], "test", "short", 0)
            self.assertEqual(stage["budget"],2)
            self.assertFalse(stage["language"]["finite"])
            self.assertTrue(all(len(source["relator_pool"][i])<=6 for i in stage["selected_relator_ids"]))

    def test_face_upper_bound_and_independent_certificate(self):
        for n, source in self.sources.items():
            stage = experiment.evaluate(source, source["face_relator_ids"], "test", "faces", 2)
            self.assertTrue(stage["language"]["finite"])
            self.assertEqual(stage["language"]["certificate"]["accepted_word_count"],2*n)
            self.assertEqual(stage["costs"]["expanded_rules"],22 if n==8 else 30)
            self.assertEqual(stage["costs"]["live_dfa_states"],11 if n==8 else 19)
            _, rules = experiment.select_rules(source, stage["selected_relator_ids"])
            view = experiment.source_view(source, stage["selected_relator_ids"], "faces", rules)
            view = json.loads(experiment.pack(view))
            item = json.loads(experiment.pack({**stage,"rules":rules,"relators":[source["relator_pool"][i] for i in stage["selected_relator_ids"]]}))
            verify_method(item, view, 2)
            item["language"]["certificate"]["max_length"] += 1
            with self.assertRaises(ValueError):
                verify_method(item, view, 2)

    def test_group_model_tampering_is_rejected(self):
        source = json.loads(experiment.pack(self.sources[8]))
        source["transitions"][0][0] = 0
        with self.assertRaises(ValueError):
            verifier.verify_source(source)


if __name__ == "__main__":
    unittest.main()
