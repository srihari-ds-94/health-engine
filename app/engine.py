def calculate_1rm(weight: float, reps: int) -> float:
    """Calculate theoretical One-Rep Max using the Epley formula."""
    if reps <= 1:
        return float(weight)
    return round(float(weight) * (1.0 + reps / 30.0), 1)

def calculate_protein_target(weight: float, goal: str, gender: str = "male", age: int = 30, height: float = 175.0) -> dict:
    """
    Biological gender-aware calculation for protein target and BMR/TDEE.
    Accounts for lean body mass baseline, metabolic rate, and muscle protein synthesis differences.
    """
    g_lower = (gender or "male").lower()

    if g_lower == "male":
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
        if goal == "recomp":
            multiplier = 1.7
            desc = "1.7g/kg for male body recomposition to preserve lean mass during fat loss"
        elif goal == "maintenance":
            multiplier = 1.1
            desc = "1.1g/kg for male metabolic vitality and joint health"
        else: # muscle_gain
            multiplier = 1.45
            desc = "1.45g/kg calibrated for male athletic hypertrophy and muscle protein synthesis"
    elif g_lower == "female":
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
        if goal == "recomp":
            multiplier = 1.55
            desc = "1.55g/kg for female body recomposition, preserving nitrogen balance while in deficit"
        elif goal == "maintenance":
            multiplier = 1.0
            desc = "1.0g/kg for female daily vitality, hormone balance, and lean muscle retention"
        else: # muscle_gain
            multiplier = 1.35
            desc = "1.35g/kg calibrated for female athletic lean muscle synthesis"
    else:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 78
        if goal == "recomp":
            multiplier = 1.6
            desc = "1.6g/kg for active body recomposition"
        elif goal == "maintenance":
            multiplier = 1.05
            desc = "1.05g/kg for maintenance and vitality"
        else:
            multiplier = 1.4
            desc = "1.4g/kg for athletic hypertrophy"

    target = int(round(weight * multiplier))
    tdee = int(round(bmr * 1.375)) # Moderate training multiplier

    return {
        "target": target,
        "multiplier": multiplier,
        "desc": desc,
        "bmr": int(round(bmr)),
        "tdee": tdee
    }

def evaluate_progressive_overload(prev_weight: float, prev_reps: int, new_weight: float, new_reps: int) -> dict:
    """Check if a new set represents progressive overload or a personal record."""
    if new_weight > prev_weight and new_reps >= max(1, prev_reps - 2):
        return {
            "is_pr": True,
            "pr_type": "weight",
            "message": f"Weight PR! +{round(new_weight - prev_weight, 1)} kg heavier than baseline."
        }
    elif new_weight == prev_weight and new_reps > prev_reps:
        return {
            "is_pr": True,
            "pr_type": "rep",
            "message": f"Rep PR! +{new_reps - prev_reps} reps added at {new_weight} kg."
        }
    elif new_weight == prev_weight and new_reps == prev_reps:
        return {
            "is_pr": False,
            "pr_type": "matched",
            "message": "Matched baseline volume."
        }
    else:
        return {
            "is_pr": False,
            "pr_type": "submaximal",
            "message": "Sub-maximal working load."
        }

def calculate_daily_health_score(
    workout_done: bool,
    has_pr: bool,
    sets_count: int,
    sleep_hours: float,
    sleep_feeling: int,
    stress_level: str,
    meditation_done: bool,
    habit_acv: bool,
    habit_seeds: bool,
    habit_fasting: bool,
    total_protein: int,
    protein_target: int,
    yesterday_score: int = 74
) -> dict:
    """Calculates the overall daily progression score (0-100) answering 'Am I healthier today than yesterday?'"""
    score = 0

    # 1. Workout & Movement (max 35 pts)
    if workout_done:
        score += 20
        if has_pr:
            score += 10
        if sets_count >= 3:
            score += 5
    else:
        score += 12  # Active rest baseline

    # 2. Sleep & Wellness (max 25 pts)
    if 7.0 <= sleep_hours <= 9.0:
        score += 14
    elif sleep_hours >= 6.0:
        score += 9
    else:
        score += 4

    if sleep_feeling == 3:  # Energized
        score += 4
    elif sleep_feeling == 2:  # Okay
        score += 2

    if stress_level == "Low":
        score += 4
    elif stress_level == "Moderate":
        score += 2

    if meditation_done:
        score += 3

    # 3. Micro-Habits (max 15 pts)
    if habit_acv:
        score += 5
    if habit_seeds:
        score += 5
    if habit_fasting:
        score += 5

    # 4. Nutrition & Protein (max 25 pts)
    if total_protein >= protein_target:
        score += 25
    elif total_protein >= int(protein_target * 0.75):
        score += 18
    elif total_protein >= int(protein_target * 0.5):
        score += 12
    else:
        score += 6

    # Clamp score
    score = max(0, min(100, score))
    delta = score - yesterday_score

    if delta > 0:
        status = "Progressing"
        headline = "Healthier Today! 🎉"
        narrative = f"You are trending ahead of yesterday by +{delta} pts. High training output, solid recovery, and hitting nutrition targets kept you moving forward."
    elif delta == 0:
        status = "Maintaining"
        headline = "Holding Steady"
        narrative = "You matched yesterday's baseline. A quick evening stretch or an extra protein snack will tip today into progress."
    else:
        status = "Needs Recovery"
        headline = "Room to Recover"
        narrative = f"Today is {abs(delta)} pts under yesterday. Prioritize hitting your fasting window, taking healthy fats, and getting 8+ hours of sleep tonight."

    # Readiness for tomorrow
    readiness_data = calculate_tomorrow_readiness(sleep_hours, stress_level, "None", workout_done)

    return {
        "score": score,
        "yesterday_score": yesterday_score,
        "delta": delta,
        "status": status,
        "headline": headline,
        "narrative": narrative,
        "readiness_pct": readiness_data["readiness_pct"],
        "recovery_title": readiness_data["title"],
        "recovery_text": readiness_data["text"]
    }

def calculate_tomorrow_readiness(
    sleep_hours: float,
    stress_level: str,
    soreness_level: str,
    workout_done_today: bool
) -> dict:
    """Calculates tomorrow's physical readiness score and recovery prescription."""
    readiness = 88

    if sleep_hours < 6.0:
        readiness -= 25
    elif sleep_hours < 7.0:
        readiness -= 10

    if stress_level == "High":
        readiness -= 15
    elif stress_level == "Moderate":
        readiness -= 5

    if soreness_level == "Joint":
        readiness -= 35
    elif soreness_level == "Mild":
        readiness -= 10

    if workout_done_today:
        readiness -= 5

    readiness = max(25, min(98, readiness))

    if readiness >= 75:
        title = "Tomorrow: Prime for High Intensity Training"
        text = "Your sleep and recovery indicators are optimal. Your central nervous system is fully recharged to tackle your next scheduled progressive overload session."
    elif readiness >= 55:
        title = "Tomorrow: Active Recovery or Light Deload Advised"
        text = "Mild fatigue accumulation suggests an active recovery day tomorrow. Take a brisk walk, do mobility drills, or perform light core work to stimulate blood flow."
    else:
        title = "Tomorrow: Full Rest Day Strongly Recommended"
        text = "Elevated fatigue markers require rest. Take a complete off-day, keep protein intake high, and prioritize restorative 8+ hour sleep."

    return {
        "readiness_pct": readiness,
        "title": title,
        "text": text
    }
