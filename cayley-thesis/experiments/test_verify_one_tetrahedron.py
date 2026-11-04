"""Reject corrupted topology, orientation, algebra, and compression certificates."""
from copy import deepcopy
from itertools import permutations, product
import json
import unittest

import one_tetrahedron_census as census
import verify_one_tetrahedron as verifier


class IndependentVerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = [census.make_case(a, b) for a, b in product(permutations((0, 1, 3)), permutations((1, 2, 3)))]
        cls.by_id = {c["case_id"]: c for c in cls.cases}

    def test_all_36_independent_reconstructions(self):
        checked = [verifier.compare_case(case) for case in self.cases]
        self.assertEqual(sum(c["accepted"] for c in checked), 9)
        self.assertEqual(verifier.expected_counts(self.cases)["accepted_H1_counts"], {"0": 5, "Z/4": 2, "Z/5": 2})

    def test_corrupt_link_count_rejected(self):
        case = deepcopy(self.by_id["130-231"])
        case["after"]["links"][0]["V"] += 1
        with self.assertRaisesRegex(ValueError, "link mismatch"):
            verifier.compare_case(case)

    def test_corrupt_partial_state_rejected(self):
        case = deepcopy(self.by_id["130-231"])
        case["after_first"]["Ce"][0][2] = not case["after_first"]["Ce"][0][2]
        with self.assertRaisesRegex(ValueError, "first-stage mismatch"):
            verifier.compare_case(case)

    def test_corrupt_smith_certificate_rejected(self):
        case = deepcopy(self.by_id["130-231"])
        case["homology"]["certificates"]["H1"]["quotient_smith"]["U"][0][0] += 2
        with self.assertRaises(ValueError):
            verifier.compare_case(case)

    def test_corrupt_reversal_walk_rejected(self):
        case = deepcopy(next(c for c in self.cases if c["edge_reversal_witness"]))
        case["edge_reversal_witness"]["sign_product"] = 1
        with self.assertRaisesRegex(ValueError, "Witness does not reverse"):
            verifier.compare_case(case)

    def test_corrupt_classification_key_rejected(self):
        case = deepcopy(self.by_id["130-231"])
        case["relabeling_key"][0][2] = 9
        with self.assertRaisesRegex(ValueError, "relabeling key"):
            verifier.compare_case(case)

    def test_nonzero_boundary_product_rejected(self):
        chain = {"dimensions": [1, 1, 1, 0], "boundaries": {"1": [[1]], "2": [[2]], "3": [[]]}}
        with self.assertRaisesRegex(ValueError, "Chain condition"):
            verifier.independent_homology(chain)

    def test_boundary_inclusion_witness_and_tamper(self):
        witness = json.loads(json.dumps(census.boundary_inclusion_witness(self.cases)))
        verifier.verify_boundary_inclusion(witness, self.cases)
        corrupted = deepcopy(witness)
        corrupted["records"][0]["boundary_inclusion_to_Z"]["x_03"] = 3
        with self.assertRaisesRegex(ValueError, "inclusion values"):
            verifier.verify_boundary_inclusion(corrupted, self.cases)


if __name__ == "__main__":
    unittest.main()
