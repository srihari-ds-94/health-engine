import unittest
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.engine import calculate_1rm, calculate_protein_target, evaluate_progressive_overload, calculate_daily_health_score
from app.ai_coach import parse_meal_nutrition, get_ai_coaching_response
from app.database import init_db, get_db

class TestHealthEngine(unittest.TestCase):

    def setUp(self):
        os.environ["DATABASE_PATH"] = ":memory:"
        init_db()

    def test_calculate_1rm(self):
        # 50kg for 10 reps: 50 * (1 + 10/30) = 50 * 1.333 = 66.7 kg
        one_rm = calculate_1rm(50.0, 10)
        self.assertAlmostEqual(one_rm, 66.7, places=1)

        # 100kg for 1 rep: exactly 100kg
        self.assertEqual(calculate_1rm(100.0, 1), 100.0)

    def test_calculate_protein_target(self):
        # 67kg * 1.4 = 93.8 ~ 94g
        res = calculate_protein_target(67.0, "muscle_gain")
        self.assertEqual(res["target"], 94)

        # 67kg * 1.6 = 107.2 ~ 107g
        res_recomp = calculate_protein_target(67.0, "recomp")
        self.assertEqual(res_recomp["target"], 107)

    def test_progressive_overload_eval(self):
        # Beat previous reps with same weight
        eval_rep_pr = evaluate_progressive_overload(prev_weight=50.0, prev_reps=8, new_weight=50.0, new_reps=10)
        self.assertTrue(eval_rep_pr["is_pr"])
        self.assertEqual(eval_rep_pr["pr_type"], "rep")

        # Beat previous weight
        eval_wt_pr = evaluate_progressive_overload(prev_weight=50.0, prev_reps=8, new_weight=52.5, new_reps=6)
        self.assertTrue(eval_wt_pr["is_pr"])
        self.assertEqual(eval_wt_pr["pr_type"], "weight")

    def test_food_parser(self):
        text = "Brown rice with lentil soup, broccoli, and a cup of greek yogurt"
        nutrition = parse_meal_nutrition(text)
        self.assertGreater(nutrition["calories"], 400)
        self.assertGreater(nutrition["protein"], 20)
        self.assertGreater(nutrition["fiber"], 5)

    def test_daily_health_score(self):
        res = calculate_daily_health_score(
            workout_done=True,
            has_pr=True,
            sets_count=4,
            sleep_hours=7.5,
            sleep_feeling=3,
            stress_level="Low",
            meditation_done=True,
            habit_acv=True,
            habit_seeds=True,
            habit_fasting=True,
            total_protein=95,
            protein_target=94,
            yesterday_score=74
        )
        self.assertGreaterEqual(res["score"], 80)
        self.assertEqual(res["status"], "Progressing")
        self.assertGreater(res["delta"], 0)

if __name__ == "__main__":
    unittest.main()
