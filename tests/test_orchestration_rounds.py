import unittest

from scripts.run_multi_seed_compare import DEFAULT_SEEDS
from scripts.run_multi_seed_compare import determine_round_plan
from scripts.run_multi_seed_compare import should_stop_after_round


class OrchestrationRoundsTests(unittest.TestCase):
    def test_default_seeds_are_fixed_three_seed_set(self) -> None:
        self.assertEqual(DEFAULT_SEEDS, [41, 42, 43])

    def test_should_stop_after_round_when_aggregate_win_criteria_met(self) -> None:
        aggregate = {
            "seed_count": 3,
            "win_count": 2,
            "win_rate": 2 / 3,
            "mean_delta": 15.0,
        }
        self.assertTrue(should_stop_after_round(aggregate))

    def test_should_not_stop_after_round_when_win_criteria_not_met(self) -> None:
        aggregate = {
            "seed_count": 3,
            "win_count": 1,
            "win_rate": 1 / 3,
            "mean_delta": -3.0,
        }
        self.assertFalse(should_stop_after_round(aggregate))

    def test_round3_is_only_scheduled_when_round2_not_winning(self) -> None:
        self.assertEqual(determine_round_plan(round2_passed=True), ["round1", "round2"])
        self.assertEqual(determine_round_plan(round2_passed=False), ["round1", "round2", "round3"])


if __name__ == "__main__":
    unittest.main()
