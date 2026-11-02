from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

# --- User & Auth Schemas ---
class UserRegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    gender: str = "male"  # male, female, other
    age: int = 30
    height: float = 175.0
    weight: float = 67.0
    goal: str = "muscle_gain"
    diet: str = "Balanced Omnivore"
    protein_target: int = 97
    routine: str = "Standard Day"

class UserLoginRequest(BaseModel):
    email: str
    password: str

class UserProfileResponse(BaseModel):
    id: int
    name: str
    email: str
    gender: str
    age: int
    height: float
    weight: float
    goal: str
    diet: str
    protein_target: int
    routine: str

class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    goal: Optional[str] = None
    diet: Optional[str] = None
    protein_target: Optional[int] = None
    routine: Optional[str] = None

# --- Workout & Strength Schemas ---
class LogSetRequest(BaseModel):
    user_id: int
    date: str
    split: str
    exercise_name: str
    set_num: int
    weight: float
    reps: int

class WorkoutSetResponse(BaseModel):
    id: int
    split: str
    exercise_name: str
    set_num: int
    weight: float
    reps: int
    est_1rm: float
    is_pr: bool
    pr_type: str

class StrengthMilestonePoint(BaseModel):
    week_label: str
    working_weight: float
    reps: int
    est_1rm: float

class StrengthCurveResponse(BaseModel):
    exercise_key: str
    title: str
    peak_1rm: float
    gain_val: str
    gain_pct: str
    rate_val: str
    points: List[StrengthMilestonePoint]
    story: str

# --- Food & Nutrition Schemas ---
class ParseMealRequest(BaseModel):
    text: str

class MealNutritionEstimate(BaseModel):
    calories: int
    protein: int
    fiber: int

class LogMealRequest(BaseModel):
    user_id: int
    date: str
    text: str

class MealResponse(BaseModel):
    id: int
    text: str
    calories: int
    protein: int
    fiber: int

# --- Daily Health Score & Recovery Schemas ---
class DayLogRequest(BaseModel):
    user_id: int
    date: str
    workout_done: bool = False
    workout_split: str = "Push"
    sleep_hours: float = 7.5
    sleep_feeling: int = 2
    stress_level: str = "Low"
    meditation_done: bool = False
    soreness_level: str = "None"
    habit_acv: bool = False
    habit_seeds: bool = False
    habit_fasting: bool = False

class DayScoreSummary(BaseModel):
    score: int
    yesterday_score: int
    delta: int
    status: str
    headline: str
    narrative: str
    readiness_pct: int
    recovery_title: str
    recovery_text: str

# --- Full User Data Sync Schemas ---
class UserStateSyncRequest(BaseModel):
    user_id: int
    date: str
    workout_done: bool = False
    workout_split: str = "Push"
    sets: List[Dict[str, Any]] = []
    meals: List[Dict[str, Any]] = []
    sleep_hours: float = 7.5
    sleep_feeling: int = 2
    stress_level: str = "Low"
    meditation_done: bool = False
    soreness_level: str = "None"
    habit_acv: bool = False
    habit_seeds: bool = False
    habit_fasting: bool = False
    score: int = 0
    yesterday_score: int = 70

class UserStateResponse(BaseModel):
    user_id: int
    date: str
    workout_done: bool
    workout_split: str
    sets: List[WorkoutSetResponse]
    meals: List[MealResponse]
    strength_points: List[StrengthMilestonePoint]
    sleep_hours: float
    sleep_feeling: int
    stress_level: str
    meditation_done: bool
    soreness_level: str
    habit_acv: bool
    habit_seeds: bool
    habit_fasting: bool
    score: int
    yesterday_score: int
    readiness_pct: int

# --- AI Coach Schemas ---
class AIQueryRequest(BaseModel):
    user_id: int
    query: str
    api_key: Optional[str] = None

class AIQueryResponse(BaseModel):
    query: str
    response_html: str
