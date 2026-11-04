import copy
import json
from pathlib import Path
import unittest

import relation_automata as automata
import verify_relation_automata as verifier


class RelationAutomataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources, cls.results = {}, {}
        for budget, folder in automata.SOURCE_RUNS.items():
            source = json.loads((automata.ROOT / "experiments/results" / folder / "d4-g0-squares-seed0.json").read_text(encoding="utf-8"))
            cls.sources[budget] = source
            for method in ("cancellation_only", "ordinary", "faces"):
                item = automata.analyse_method(source, method, 5)
                item["budget"] = budget
                cls.results[budget, method] = item

    def test_single_relation_pumping_words(self):
        ordinary = self.results["single_relation", "ordinary"]
        faces = self.results["single_relation", "faces"]
        self.assertFalse(ordinary["language"]["finite"])
        self.assertFalse(faces["language"]["finite"])
        self.assertEqual(ordinary["language"]["certificate"]["prefix"], (0,))
        self.assertEqual(ordinary["language"]["certificate"]["cycle"], (0,))
        self.assertEqual(faces["language"]["certificate"]["prefix"], (0,))
        self.assertEqual(faces["language"]["certificate"]["cycle"], (2, 0))

    def test_full_language_and_bfs_diameter(self):
        item = self.results["full_budget", "faces"]
        cert = item["language"]["certificate"]
        self.assertTrue(item["language"]["finite"])
        self.assertEqual(cert["max_length"], 3)
        self.assertEqual(cert["longest_word"], (0, 0, 2))
        self.assertEqual(cert["accepted_word_count"], 8)
        self.assertTrue(all(item["finite_comparison"].values()))
        self.assertEqual(item["rules"], self.results["full_budget", "ordinary"]["rules"])

    def test_rejecting_sink_cycle_does_not_make_language_infinite(self):
        dfa = automata.compile_dfa([((0,), ())], 1)
        self.assertEqual(dfa["transitions"][dfa["dead"]], [dfa["dead"]])
        result = automata.classify_language(dfa)
        self.assertTrue(result["finite"])
        self.assertEqual(result["certificate"]["max_length"], 0)
        self.assertEqual(result["certificate"]["accepted_word_count"], 1)

    def test_no_patterns_and_empty_left_side(self):
        dfa = automata.compile_dfa([], 2)
        result = automata.classify_language(dfa)
        self.assertFalse(result["finite"])
        self.assertTrue(automata.accepts(dfa, (0, 1) * 20))
        with self.assertRaises(ValueError):
            automata.compile_dfa([((), ())], 2)

    def test_subword_rejection_is_absorbing(self):
        dfa = self.results["single_relation", "faces"]["dfa"]
        self.assertTrue(automata.accepts(dfa, (0, 0)))
        self.assertFalse(automata.accepts(dfa, (0, 0, 0)))
        self.assertFalse(automata.accepts(dfa, (0, 0, 0, 2)))

    def test_all_certificates_check_after_json_roundtrip(self):
        for (budget, method), item in self.results.items():
            decoded = json.loads(json.dumps(item))
            verifier.verify_method(decoded, self.sources[budget], 5)

    def test_transition_and_finite_certificate_corruption_rejected(self):
        item = json.loads(json.dumps(self.results["full_budget", "faces"]))
        for field in ("transition", "dp"):
            broken = copy.deepcopy(item)
            if field == "transition":
                broken["dfa"]["transitions"][0][0] = broken["dfa"]["dead"]
            else:
                broken["language"]["certificate"]["suffix_max_lengths"]["0"] += 1
            with self.assertRaises(ValueError):
                verifier.verify_method(broken, self.sources["full_budget"], 5)

    def test_fake_empty_cycle_rejected(self):
        item = json.loads(json.dumps(self.results["single_relation", "ordinary"]))
        item["language"]["certificate"]["cycle"] = []
        with self.assertRaises(ValueError):
            verifier.verify_method(item, self.sources["single_relation"], 5)


if __name__ == "__main__":
    unittest.main()
