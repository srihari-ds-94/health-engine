import os
import hashlib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse
from typing import List

from app.database import get_db, init_db, hash_password
from app.schemas import (
    UserRegisterRequest, UserLoginRequest, UserProfileResponse, UserUpdateRequest,
    LogSetRequest, WorkoutSetResponse, StrengthCurveResponse, StrengthMilestonePoint,
    ParseMealRequest, MealNutritionEstimate, LogMealRequest, MealResponse,
    DayLogRequest, DayScoreSummary, AIQueryRequest, AIQueryResponse,
    UserStateSyncRequest, UserStateResponse
)
from app.engine import (
    calculate_1rm, calculate_protein_target, evaluate_progressive_overload,
    calculate_daily_health_score, calculate_tomorrow_readiness
)
from app.ai_coach import parse_meal_nutrition, get_ai_coaching_response

app = FastAPI(
    title="HealthEngine API",
    description="Backend engine for Personalized Health Progression & Progressive Overload Tracking",
    version="1.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", include_in_schema=False)
def root():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return RedirectResponse(url="/docs")


# ========================================================
# 1. USER AUTHENTICATION & VALIDATION ENDPOINTS
# ========================================================
@app.post("/api/auth/register", response_model=UserProfileResponse)
def register_user(req: UserRegisterRequest):
    email = req.email.strip().lower()
    if not email or "@" not in email or "." not in email:
        raise HTTPException(status_code=400, detail="Please provide a valid email address.")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")
    if not req.name.strip():
        raise HTTPException(status_code=400, detail="Full name is required.")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE LOWER(email) = ?", (email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="An account with this email already exists. Please sign in instead.")

        pw_hash = hash_password(req.password)
        cursor.execute("""
            INSERT INTO users (name, email, password_hash, gender, age, height, weight, goal, diet, protein_target, routine)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (req.name.strip(), email, pw_hash, req.gender, req.age, req.height, req.weight, req.goal, req.diet, req.protein_target, req.routine))
        user_id = cursor.lastrowid

        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row)

@app.post("/api/auth/login", response_model=UserProfileResponse)
def login_user(req: UserLoginRequest):
    email = req.email.strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required.")
    if not req.password:
        raise HTTPException(status_code=400, detail="Password is required.")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="No account found with this email. Please check your spelling or register.")

        entered_hash = hash_password(req.password)
        # Check against SHA-256 hash or legacy/demo password
        if row["password_hash"] != entered_hash and row["password_hash"] != req.password:
            raise HTTPException(status_code=401, detail="Incorrect password. Please verify and try again.")

        return dict(row)

@app.get("/api/user/{user_id}", response_model=UserProfileResponse)
def get_user_profile(user_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found.")
        return dict(row)

@app.put("/api/user/{user_id}", response_model=UserProfileResponse)
def update_user_profile(user_id: int, req: UserUpdateRequest):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        current = cursor.fetchone()
        if not current:
            raise HTTPException(status_code=404, detail="User not found.")

        name = req.name if req.name is not None else current["name"]
        gender = req.gender if req.gender is not None else current["gender"]
        age = req.age if req.age is not None else current["age"]
        height = req.height if req.height is not None else current["height"]
        weight = req.weight if req.weight is not None else current["weight"]
        goal = req.goal if req.goal is not None else current["goal"]
        diet = req.diet if req.diet is not None else current["diet"]
        protein_target = req.protein_target if req.protein_target is not None else current["protein_target"]
        routine = req.routine if req.routine is not None else current["routine"]

        cursor.execute("""
            UPDATE users SET name=?, gender=?, age=?, height=?, weight=?, goal=?, diet=?, protein_target=?, routine=?
            WHERE id=?
        """, (name, gender, age, height, weight, goal, diet, protein_target, routine, user_id))

        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return dict(cursor.fetchone())


# ========================================================
# 2. COMPLETE USER STATE FETCH & SYNC (PERSISTENCE)
# ========================================================
@app.get("/api/user/{user_id}/state/{date}", response_model=UserStateResponse)
def get_user_full_state(user_id: int, date: str):
    """Fetches user's actual isolated data from SQLite database. New users get strictly empty arrays."""
    with get_db() as conn:
        cursor = conn.cursor()
        # Ensure user exists
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found.")

        # Get day log if any
        cursor.execute("SELECT * FROM day_logs WHERE user_id = ? AND date = ?", (user_id, date))
        day_row = cursor.fetchone()

        # Get sets for date
        cursor.execute("SELECT * FROM workout_sets WHERE user_id = ? AND date = ? ORDER BY id ASC", (user_id, date))
        set_rows = cursor.fetchall()
        sets_list = [
            {
                "id": r["id"],
                "split": r["split"],
                "exercise_name": r["exercise_name"],
                "set_num": r["set_num"],
                "weight": r["weight"],
                "reps": r["reps"],
                "est_1rm": r["est_1rm"],
                "is_pr": bool(r["is_pr"]),
                "pr_type": r["pr_type"]
            }
            for r in set_rows
        ]

        # Get meals for date
        cursor.execute("SELECT * FROM meals WHERE user_id = ? AND date = ? ORDER BY id ASC", (user_id, date))
        meal_rows = cursor.fetchall()
        meals_list = [dict(r) for r in meal_rows]

        # Get strength milestones for this user
        cursor.execute("SELECT week_label, working_weight, reps, est_1rm FROM strength_milestones WHERE user_id = ? ORDER BY id ASC", (user_id,))
        mile_rows = cursor.fetchall()
        strength_points = [
            StrengthMilestonePoint(
                week_label=r["week_label"],
                working_weight=r["working_weight"],
                reps=r["reps"],
                est_1rm=r["est_1rm"]
            )
            for r in mile_rows
        ]

        if day_row:
            return UserStateResponse(
                user_id=user_id,
                date=date,
                workout_done=bool(day_row["workout_done"]),
                workout_split=day_row["workout_split"],
                sets=sets_list,
                meals=meals_list,
                strength_points=strength_points,
                sleep_hours=day_row["sleep_hours"],
                sleep_feeling=day_row["sleep_feeling"],
                stress_level=day_row["stress_level"],
                meditation_done=bool(day_row["meditation_done"]),
                soreness_level=day_row["soreness_level"],
                habit_acv=bool(day_row["habit_acv"]),
                habit_seeds=bool(day_row["habit_seeds"]),
                habit_fasting=bool(day_row["habit_fasting"]),
                score=day_row["score"],
                yesterday_score=day_row["yesterday_score"],
                readiness_pct=day_row["readiness_pct"]
            )
        else:
            # Clean Day 1 Initial State
            return UserStateResponse(
                user_id=user_id,
                date=date,
                workout_done=False,
                workout_split="Push",
                sets=sets_list,
                meals=meals_list,
                strength_points=strength_points,
                sleep_hours=7.5,
                sleep_feeling=2,
                stress_level="Low",
                meditation_done=False,
                soreness_level="None",
                habit_acv=False,
                habit_seeds=False,
                habit_fasting=False,
                score=0,
                yesterday_score=70,
                readiness_pct=85
            )

@app.post("/api/user/{user_id}/sync")
def sync_user_state(user_id: int, req: UserStateSyncRequest):
    """Persists entire active state from client directly into database."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Update or Insert day log
        cursor.execute("""
            INSERT INTO day_logs (
                user_id, date, workout_done, workout_split, sleep_hours, sleep_feeling,
                stress_level, meditation_done, soreness_level, habit_acv, habit_seeds,
                habit_fasting, score, yesterday_score, delta, readiness_pct
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, date) DO UPDATE SET
                workout_done=excluded.workout_done,
                workout_split=excluded.workout_split,
                sleep_hours=excluded.sleep_hours,
                sleep_feeling=excluded.sleep_feeling,
                stress_level=excluded.stress_level,
                meditation_done=excluded.meditation_done,
                soreness_level=excluded.soreness_level,
                habit_acv=excluded.habit_acv,
                habit_seeds=excluded.habit_seeds,
                habit_fasting=excluded.habit_fasting,
                score=excluded.score,
                yesterday_score=excluded.yesterday_score,
                delta=excluded.delta,
                readiness_pct=excluded.readiness_pct
        """, (
            user_id, req.date, int(req.workout_done), req.workout_split, req.sleep_hours, req.sleep_feeling,
            req.stress_level, int(req.meditation_done), req.soreness_level, int(req.habit_acv), int(req.habit_seeds),
            int(req.habit_fasting), req.score, req.yesterday_score, req.score - req.yesterday_score, 85
        ))
        return {"status": "synced", "user_id": user_id, "date": req.date}


# ========================================================
# 3. WORKOUT & PROGRESSIVE OVERLOAD ENDPOINTS
# ========================================================
@app.post("/api/workout/sets", response_model=WorkoutSetResponse)
def log_workout_set(req: LogSetRequest):
    with get_db() as conn:
        cursor = conn.cursor()
        est_1rm = calculate_1rm(req.weight, req.reps)

        cursor.execute("""
            SELECT weight, reps FROM workout_sets
            WHERE user_id = ? AND exercise_name = ?
            ORDER BY id DESC LIMIT 1
        """, (req.user_id, req.exercise_name))
        prev_row = cursor.fetchone()

        prev_weight = prev_row["weight"] if prev_row else 0.0
        prev_reps = prev_row["reps"] if prev_row else 0

        overload_eval = evaluate_progressive_overload(prev_weight, prev_reps, req.weight, req.reps)

        cursor.execute("""
            INSERT INTO workout_sets (user_id, date, split, exercise_name, set_num, weight, reps, est_1rm, is_pr, pr_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (req.user_id, req.date, req.split, req.exercise_name, req.set_num, req.weight, req.reps, est_1rm,
              1 if overload_eval["is_pr"] else 0, overload_eval["pr_type"]))

        set_id = cursor.lastrowid
        return {
            "id": set_id,
            "split": req.split,
            "exercise_name": req.exercise_name,
            "set_num": req.set_num,
            "weight": req.weight,
            "reps": req.reps,
            "est_1rm": est_1rm,
            "is_pr": overload_eval["is_pr"],
            "pr_type": overload_eval["pr_type"]
        }

@app.get("/api/workout/sets/{user_id}/{date}", response_model=List[WorkoutSetResponse])
def get_workout_sets(user_id: int, date: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM workout_sets WHERE user_id = ? AND date = ? ORDER BY id ASC", (user_id, date))
        rows = cursor.fetchall()
        return [
            {
                "id": r["id"],
                "split": r["split"],
                "exercise_name": r["exercise_name"],
                "set_num": r["set_num"],
                "weight": r["weight"],
                "reps": r["reps"],
                "est_1rm": r["est_1rm"],
                "is_pr": bool(r["is_pr"]),
                "pr_type": r["pr_type"]
            }
            for r in rows
        ]

@app.delete("/api/workout/sets/{set_id}")
def delete_workout_set(set_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM workout_sets WHERE id = ?", (set_id,))
        return {"status": "deleted", "set_id": set_id}

@app.get("/api/workout/strength-curve/{user_id}/{exercise_key}", response_model=StrengthCurveResponse)
def get_strength_curve(user_id: int, exercise_key: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT week_label, working_weight, reps, est_1rm FROM strength_milestones
            WHERE user_id = ? AND exercise_key = ? ORDER BY id ASC
        """, (user_id, exercise_key))
        rows = cursor.fetchall()

        if not rows:
            # Brand new users have no historical milestones yet
            points = []
            peak_1rm = 0.0
            story = "Log your working sets in the Workout tab to start building your actual strength curve!"
        else:
            points = [
                StrengthMilestonePoint(
                    week_label=r["week_label"],
                    working_weight=r["working_weight"],
                    reps=r["reps"],
                    est_1rm=r["est_1rm"]
                ) for r in rows
            ]
            peak_1rm = max(p.est_1rm for p in points)
            story = "Consistent progressive overload observed across your training cycle."

        return StrengthCurveResponse(
            exercise_key=exercise_key,
            title=exercise_key.capitalize(),
            peak_1rm=peak_1rm,
            gain_val=f"+{round(points[-1].est_1rm - points[0].est_1rm, 1)} kg" if len(points) >= 2 else "+0.0 kg",
            gain_pct=f"+{round(((points[-1].est_1rm - points[0].est_1rm) / points[0].est_1rm) * 100, 1)}%" if len(points) >= 2 and points[0].est_1rm > 0 else "+0.0%",
            rate_val="+1.8 kg/wk" if len(points) >= 2 else "+0.0 kg/wk",
            points=points,
            story=story
        )


# ========================================================
# 4. FOOD & NUTRITION ENDPOINTS
# ========================================================
@app.post("/api/food/parse", response_model=MealNutritionEstimate)
def parse_food_text(req: ParseMealRequest):
    return parse_meal_nutrition(req.text)

@app.post("/api/food/meals", response_model=MealResponse)
def log_meal(req: LogMealRequest):
    with get_db() as conn:
        cursor = conn.cursor()
        nutrition = parse_meal_nutrition(req.text)

        cursor.execute("""
            INSERT INTO meals (user_id, date, text, calories, protein, fiber)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (req.user_id, req.date, req.text, nutrition["calories"], nutrition["protein"], nutrition["fiber"]))
        meal_id = cursor.lastrowid

        return {
            "id": meal_id,
            "text": req.text,
            "calories": nutrition["calories"],
            "protein": nutrition["protein"],
            "fiber": nutrition["fiber"]
        }

@app.get("/api/food/meals/{user_id}/{date}", response_model=List[MealResponse])
def get_daily_meals(user_id: int, date: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM meals WHERE user_id = ? AND date = ? ORDER BY id ASC", (user_id, date))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

@app.delete("/api/food/meals/{meal_id}")
def delete_meal(meal_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM meals WHERE id = ?", (meal_id,))
        return {"status": "deleted", "meal_id": meal_id}


# ========================================================
# 5. AI COACH ENDPOINT
# ========================================================
@app.post("/api/ai/coach", response_model=AIQueryResponse)
def query_ai_coach(req: AIQueryRequest):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (req.user_id,))
        user_row = cursor.fetchone()
        profile = dict(user_row) if user_row else {}

    html_ans = get_ai_coaching_response(req.query, profile, req.api_key)
    return {"query": req.query, "response_html": html_ans}
