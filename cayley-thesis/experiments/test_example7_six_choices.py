import copy
import json
from pathlib import Path
import tempfile
import unittest
from itertools import permutations

import example7_six_choices as experiment


class SixChoiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = {"".join(map(str, p)): experiment.make_case(p) for p in permutations([1, 2, 3])}

    def test_all_six_and_predicates_are_separate(self):
        self.assertEqual(len(self.cases), 6)
        self.assertEqual([key for key, c in self.cases.items() if not c["decision"]["partial_accepted"]], ["123"])
        self.assertEqual([key for key, c in self.cases.items() if c["decision"]["orientable_partial_accepted"]], ["132", "213", "321"])

    def test_123_rejection_has_explicit_orientation_conflict(self):
        case = self.cases["123"]
        self.assertEqual([r["code"] for r in case["decision"]["rejection_reasons"]], ["NONORIENTABLE_VERTEX_LINK"])
        trace = case["apex_orientation_trace"]
        self.assertEqual([eq["target_sign_over_source"] for eq in trace["equations"]], [-1, 1])
        self.assertEqual(trace["cycle_sign_product"], -1)

    def test_321_annulus_is_partial_but_not_manifold(self):
        case = self.cases["321"]
        self.assertTrue(case["decision"]["partial_accepted"])
        self.assertFalse(case["decision"]["manifold_with_boundary_link_test"])
        self.assertFalse(case["decision"]["closed"])
        self.assertEqual([eq["target_sign_over_source"] for eq in case["apex_orientation_trace"]["equations"]], [-1, -1])

    def test_same_euler_data_different_links(self):
        a, b = [next(l for l in self.cases[key]["after"]["links"] if (0, 2) in l["members"]) for key in ("321", "123")]
        self.assertEqual((a["V"], a["E"], a["F"], a["chi"]), (b["V"], b["E"], b["F"], b["chi"]))
        self.assertNotEqual(a["boundary_components"], b["boundary_components"])
        self.assertNotEqual(a["orientable"], b["orientable"])

    def test_tampered_ce_or_verdict_is_rejected(self):
        for field in ("Ce", "verdict"):
            broken = copy.deepcopy(self.cases["321"])
            if field == "Ce":
                broken["after"]["Ce"][0][2] = not broken["after"]["Ce"][0][2]
            else:
                broken["decision"]["partial_accepted"] = False
            with self.assertRaises(ValueError):
                experiment.verify_case(broken)

    def test_json_roundtrip_and_invalid_target(self):
        experiment.verify_case(experiment.json_value(self.cases["321"]))
        with self.assertRaises(ValueError):
            experiment.make_case((1, 1, 3))

    def test_saved_checkpoint_and_count_tampering(self):
        test_workspace = Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory(dir=test_workspace, prefix="six-choice-test-") as directory:
            root = Path(directory)
            self.assertTrue(root.resolve().is_relative_to(test_workspace))
            (root / "cases").mkdir()
            cases = [experiment.json_value(c) for c in self.cases.values()]
            report = {"before": experiment.json_value(experiment.core.analyse([experiment.core.FIRST])),
                      "cases": cases, "counts": {"choices": 6, "partial_accepted": 5,
                      "orientable_partial_accepted": 3, "distinct_accepted_labeled_states": 5}}
            for case in cases:
                (root / "cases" / f"{case['choice']}.json").write_text(json.dumps(case), encoding="utf-8")
            path = root / "results.json"
            path.write_text(json.dumps(report), encoding="utf-8")
            self.assertEqual(experiment.verify_saved(root)["status"], "PASS")
            report["counts"]["partial_accepted"] = 6
            path.write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaises(ValueError):
                experiment.verify_saved(root)


if __name__ == "__main__":
    unittest.main()
