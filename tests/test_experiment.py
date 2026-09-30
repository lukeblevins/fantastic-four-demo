import random
import unittest
from experiment import cohort, sample_indices, run, review


class ExperimentTests(unittest.TestCase):
    def test_patient_splits_do_not_overlap(self):
        train, val, test, _, _ = cohort(42)
        groups = [{c["id"] for c in group} for group in (train, val, test)]
        self.assertEqual([len(g) for g in groups], [120, 40, 80])
        self.assertEqual(len(set.union(*groups)), 240)

    def test_equal_unique_patch_budgets(self):
        for budget in (16, 32, 64):
            for method in ("random", "spatial"):
                ids = sample_indices(budget, method, random.Random(7))
                self.assertEqual(len(set(ids)), budget)
                self.assertTrue(all(0 <= i < 384 for i in ids))

    def test_spatial_sampling_covers_each_region(self):
        for budget in (16, 32, 64):
            columns = 4 if budget == 16 else 8
            rows = budget // columns
            ids = sample_indices(budget, "spatial", random.Random(42))
            cells = {(i % 24 // (24 // columns), i // 24 // (16 // rows)) for i in ids}
            self.assertEqual(len(cells), budget)

    def test_matched_review_uses_correct_denominator(self):
        rows = [
            {
                "id": str(i),
                "mean": p,
                "variance": v,
                "confidence": max(p, 1 - p),
                "label": y,
            }
            for i, (p, v, y) in enumerate(
                [(0.9, 0.01, 1), (0.6, 0.2, 0), (0.2, 0.3, 0), (0.8, 0.1, 1)]
            )
        ]
        a = review(rows, 25, "confidence", 0.5)
        b = review(rows, 25, "disagreement", 0.5)
        self.assertEqual(a["flagged"], ["1"])
        self.assertEqual(b["flagged"], ["2"])
        self.assertEqual(a["error_rate"], 0)
        self.assertAlmostEqual(b["error_rate"], 1 / 3)

    def test_run_is_reproducible_and_flags_match(self):
        a = run(42, 16, 10)
        run.cache_clear()
        b = run(42, 16, 10)
        self.assertEqual(a, b)
        for m in a["methods"].values():
            for ca, cb in zip(m["curves"]["confidence"], m["curves"]["disagreement"]):
                self.assertEqual(ca["retained"], cb["retained"])
            for row in m["rows"]:
                self.assertEqual(len(row["probabilities"]), 10)
                self.assertTrue(all(0 <= p <= 1 for p in row["probabilities"]))

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            run(42, 1000000, 20)


if __name__ == "__main__":
    unittest.main()
