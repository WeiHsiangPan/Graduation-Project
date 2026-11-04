"""Correctness checks for pruning, certificate verification and a negative control."""
import copy
import json
import unittest

import relation_search as experiment
import verify_run


class RelationSearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogue = json.loads((experiment.ROOT / "data/surfaces/catalogue.json").read_text(encoding="utf-8"))
        cls.group, cls.generators, cls.transitions, cls.inverses, cls.identity = experiment.model(cls.catalogue["groups"]["d4"])

    def test_pruning_preserves_all_d4_distances(self):
        truth = experiment.bfs(self.transitions, self.identity)
        # Test each short relator separately, not just the final chosen pool.
        for relator in experiment.closed_words(self.transitions, self.identity, self.inverses, 6):
            rules = experiment.rules_for([relator], self.inverses)
            experiment.verify_rules(rules, self.transitions)
            for target in truth:
                result = experiment.iddfs(target, self.transitions, self.identity, rules, 3)
                self.assertEqual(result["distance"], len(truth[target]))

    def test_unsound_rule_rejected(self):
        with self.assertRaises(ValueError):
            experiment.verify_rules([((0,), ())], self.transitions)

    def test_local_irreducibility_is_not_shortest(self):
        rules = experiment.rules_for([], self.inverses)
        example = experiment.counterexample(self.transitions, self.identity, rules,
                                           experiment.bfs(self.transitions, self.identity), 6)
        self.assertEqual(example["status"], "found")
        self.assertGreater(example["excess_length"], 0)

    def test_independent_checker_rejects_corrupt_certificate(self):
        from argparse import Namespace
        report = experiment.run(Namespace(groups=["d4"], rounds=1, seed=0,
            max_relator_length=6, relators=8, counterexample_length=6, output="unused"))
        # Roundtrip mimics persisted JSON and catches tuple/list assumptions.
        case = json.loads(json.dumps(report["cases"][0]))
        verify_run.verify_case(case, self.catalogue)
        corrupt = copy.deepcopy(case)
        corrupt["truth_paths"][str(self.identity)] = [0]
        with self.assertRaises(ValueError):
            verify_run.verify_case(corrupt, self.catalogue)


if __name__ == "__main__":
    unittest.main()
