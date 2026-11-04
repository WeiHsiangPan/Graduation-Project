import unittest

import example7_rebuild as e


class Example7Tests(unittest.TestCase):
    def test_unpaired_tetrahedra_have_eight_disk_links(self):
        stage = e.analyse([])
        self.assertEqual(len(stage["vertex_classes"]), 8)
        self.assertTrue(all(link["type"] == "disk" for link in stage["links"]))
        self.assertEqual(len(stage["boundary_faces"]), 8)

    def test_first_glue_gives_five_vertex_classes(self):
        stage = e.analyse([e.FIRST])
        self.assertEqual(len(stage["vertex_classes"]), 5)
        self.assertEqual(len(stage["boundary_faces"]), 6)
        self.assertTrue(all(link["type"] == "disk" for link in stage["links"]))

    def test_inferred_matches_both_published_configurations(self):
        stage = e.analyse([e.FIRST, e.SECOND_INFERRED])
        self.assertEqual(stage["vertex_classes"], [list(map(tuple, group)) for group in e.EXPECTED_CV])
        self.assertEqual(e.canonical_ce(stage["Ce"]), e.canonical_ce(e.EXPECTED_CE))
        self.assertEqual([link["type"] for link in stage["links"]], ["disk", "disk", "annulus"])
        self.assertTrue(stage["partial_3_manifold_definition5"])
        self.assertFalse(stage["manifold_with_boundary_link_test"])

    def test_literal_input_must_not_be_silently_corrected(self):
        literal = e.analyse([e.FIRST, e.SECOND_LITERAL])
        apex = next(link for link in literal["links"] if (0, 2) in link["members"])
        self.assertEqual(apex["chi"], 0)
        self.assertEqual(apex["boundary_components"], 1)
        self.assertFalse(apex["orientable"])
        self.assertEqual(apex["type"], "mobius_band")
        self.assertFalse(literal["partial_3_manifold_definition5"])

    def test_duplicate_face_is_rejected(self):
        with self.assertRaises(ValueError):
            e.analyse([e.FIRST, e.FIRST])

    def test_nonbijective_face_map_is_rejected(self):
        with self.assertRaises(ValueError):
            e.analyse([{**e.FIRST, "target_face": [0, 0, 2]}])

    def test_gluing_direction_does_not_change_quotient(self):
        reverse = {"source_tet": 1, "source_face": [3, 2, 1],
                   "target_tet": 0, "target_face": [0, 2, 3]}
        direct = e.analyse([e.FIRST, e.SECOND_INFERRED])
        reversed_map = e.analyse([reverse, e.FIRST])
        self.assertEqual(direct["vertex_classes"], reversed_map["vertex_classes"])
        self.assertEqual(direct["Ce"], reversed_map["Ce"])
        for left, right in zip(direct["links"], reversed_map["links"]):
            self.assertEqual((left["V"], left["E"], left["F"], left["type"]),
                             (right["V"], right["E"], right["F"], right["type"]))

    def test_apex_strip_seam_matches_vertex_map(self):
        data = e.build()
        triangle0, triangle1 = (data["apex_strip"]["triangles"][key] for key in ("t0:2", "t1:2"))
        self.assertEqual(triangle0["0"], triangle1["0"])
        self.assertEqual(triangle0["1"], triangle1["1"])
        # Remaining seam: t0(0,3) -> t1(3,1), with equal y at each mapped end.
        self.assertEqual(triangle0["0"][1], triangle1["3"][1])
        self.assertEqual(triangle0["3"][1], triangle1["1"][1])


if __name__ == "__main__":
    unittest.main()
