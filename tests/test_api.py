import unittest
import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

TEST_DB = "test_healthengine.db"
os.environ["DATABASE_PATH"] = TEST_DB

from fastapi.testclient import TestClient
from app.database import init_db, get_db, hash_password
from app.main import app
from app.engine import calculate_1rm, calculate_protein_target, evaluate_progressive_overload, calculate_daily_health_score
from app.ai_coach import parse_meal_nutrition, get_ai_coaching_response

class TestHealthEngineSuite(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        init_db()
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_01_user_registration_and_hashing(self):
        """Test user registration is properly validated and hashed in the database."""
        # 1. Invalid email
        res_bad_email = self.client.post("/api/auth/register", json={
            "name": "Invalid User", "email": "notanemail", "password": "password123",
            "gender": "male", "age": 28, "height": 180, "weight": 75,
            "goal": "muscle_gain", "diet": "Keto / Ketogenic (High-Fat, Low-Carb)", "protein_target": 120, "routine": "Day"
        })
        self.assertEqual(res_bad_email.status_code, 400)

        # 2. Short password
        res_short_pw = self.client.post("/api/auth/register", json={
            "name": "Short PW", "email": "valid@example.com", "password": "123",
            "gender": "male", "age": 28, "height": 180, "weight": 75,
            "goal": "muscle_gain", "diet": "Balanced Omnivore", "protein_target": 120, "routine": "Day"
        })
        self.assertEqual(res_short_pw.status_code, 400)

        # 3. Valid registration with Keto diet
        res_valid = self.client.post("/api/auth/register", json={
            "name": "Sarah Connor", "email": "sarah@example.com", "password": "secretpassword",
            "gender": "female", "age": 30, "height": 168, "weight": 62,
            "goal": "recomp", "diet": "Keto / Ketogenic (High-Fat, Low-Carb)", "protein_target": 96, "routine": "Day"
        })
        self.assertEqual(res_valid.status_code, 200)
        data = res_valid.json()
        self.assertEqual(data["email"], "sarah@example.com")
        self.assertEqual(data["gender"], "female")
        self.assertIn("keto", data["diet"].lower())

        # 4. Verify password is saved as SHA-256 hash in DB, NOT plaintext
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password_hash FROM users WHERE email = 'sarah@example.com'")
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["password_hash"], hash_password("secretpassword"))
            self.assertNotEqual(row["password_hash"], "secretpassword")

        # 5. Duplicate email rejection
        res_dup = self.client.post("/api/auth/register", json={
            "name": "Sarah Dup", "email": "sarah@example.com", "password": "anotherpassword",
            "gender": "female", "age": 30, "height": 168, "weight": 62,
            "goal": "recomp", "diet": "Keto", "protein_target": 96, "routine": "Day"
        })
        self.assertEqual(res_dup.status_code, 400)

    def test_02_user_login_validation(self):
        """Test sign-in functionality with correct and incorrect credentials."""
        # Correct login
        res_ok = self.client.post("/api/auth/login", json={
            "email": "sarah@example.com", "password": "secretpassword"
        })
        self.assertEqual(res_ok.status_code, 200)
        self.assertEqual(res_ok.json()["name"], "Sarah Connor")

        # Wrong password
        res_wrong_pw = self.client.post("/api/auth/login", json={
            "email": "sarah@example.com", "password": "wrongpassword"
        })
        self.assertEqual(res_wrong_pw.status_code, 401)
        self.assertIn("Incorrect password", res_wrong_pw.json()["detail"])

        # Non-existent user
        res_no_user = self.client.post("/api/auth/login", json={
            "email": "ghost@example.com", "password": "anypassword"
        })
        self.assertEqual(res_no_user.status_code, 401)
        self.assertIn("No account found", res_no_user.json()["detail"])

    def test_03_new_user_clean_state_isolation(self):
        """Verify new registered user starts with 0 sets, 0 meals, 0 volume."""
        res_user = self.client.post("/api/auth/register", json={
            "name": "Fresh User", "email": "fresh@example.com", "password": "password123",
            "gender": "male", "age": 25, "height": 182, "weight": 78,
            "goal": "muscle_gain", "diet": "Balanced", "protein_target": 113, "routine": "Day"
        })
        user_id = res_user.json()["id"]

        # Fetch state from DB
        res_state = self.client.get(f"/api/user/{user_id}/state/2026-11-02")
        self.assertEqual(res_state.status_code, 200)
        state = res_state.json()

        # Strict clean-slate assertions
        self.assertEqual(len(state["sets"]), 0)
        self.assertEqual(len(state["meals"]), 0)
        self.assertEqual(len(state["strength_points"]), 0)
        self.assertEqual(state["score"], 0)

        # Strength curve should have empty points for brand new user
        res_curve = self.client.get(f"/api/workout/strength-curve/{user_id}/bench")
        self.assertEqual(res_curve.status_code, 200)
        self.assertEqual(len(res_curve.json()["points"]), 0)

    def test_04_keto_protein_calculation(self):
        """Test gender-aware and keto-specific protein calculations."""
        # Male Keto: 70kg * 1.6 = 112g
        res_male_keto = calculate_protein_target(70.0, "muscle_gain", gender="male", diet="Keto / Ketogenic (High-Fat, Low-Carb)")
        self.assertEqual(res_male_keto["target"], 112)
        self.assertIn("Ketogenic", res_male_keto["desc"])

        # Female Keto: 60kg * 1.5 = 90g
        res_female_keto = calculate_protein_target(60.0, "muscle_gain", gender="female", diet="Keto / Ketogenic (High-Fat, Low-Carb)")
        self.assertEqual(res_female_keto["target"], 90)
        self.assertIn("Ketogenic", res_female_keto["desc"])

    def test_05_ai_coach_workout_query_relevance(self):
        """Ensure workout questions receive relevant progressive overload responses, not meal text."""
        profile = {"name": "Alex", "gender": "male", "weight": 67, "protein_target": 97}
        
        # Ask about Bench Press
        bench_ans = get_ai_coaching_response("How do I progressively overload bench press?", profile)
        self.assertIn("Bench Press", bench_ans)
        self.assertIn("Progressive Overload", bench_ans)
        self.assertNotIn("fasting window with a 30g+ protein", bench_ans)

        # Ask about shoulder pinch
        injury_ans = get_ai_coaching_response("I have a slight shoulder pinch on overhead press", profile)
        self.assertIn("Shoulder", injury_ans)
        self.assertIn("Joint Protection", injury_ans)
        self.assertNotIn("fasting window with a 30g+ protein", injury_ans)

if __name__ == "__main__":
    unittest.main()
