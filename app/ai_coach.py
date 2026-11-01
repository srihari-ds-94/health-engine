import os
import re
import json
import urllib.request
import urllib.error

FOOD_DATABASE = [
    {"keywords": ["rice", "brown rice", "quinoa", "grain", "oats", "oatmeal"], "cal": 210, "prot": 5, "fib": 2},
    {"keywords": ["lentil", "lentils", "dal", "beans", "chickpea", "chickpeas", "hummus", "edamame"], "cal": 170, "prot": 11, "fib": 7},
    {"keywords": ["yogurt", "curd", "greek yogurt", "dahi", "cottage cheese"], "cal": 120, "prot": 10, "fib": 0},
    {"keywords": ["tofu", "paneer", "tempeh", "soy"], "cal": 220, "prot": 18, "fib": 1},
    {"keywords": ["broccoli", "salad", "greens", "spinach", "vegetables", "veggies", "beans"], "cal": 70, "prot": 3, "fib": 4},
    {"keywords": ["toast", "bread", "roti", "tortilla", "pita", "bagel"], "cal": 120, "prot": 4, "fib": 2},
    {"keywords": ["peanut", "peanuts", "almond", "almonds", "walnut", "nuts"], "cal": 170, "prot": 8, "fib": 2},
    {"keywords": ["seed", "seeds", "chia", "flax", "pumpkin seeds"], "cal": 90, "prot": 4, "fib": 4},
    {"keywords": ["smoothie", "protein shake", "shake", "whey"], "cal": 250, "prot": 24, "fib": 3},
    {"keywords": ["avocado", "olive"], "cal": 140, "prot": 2, "fib": 5},
    {"keywords": ["chicken", "turkey", "breast"], "cal": 220, "prot": 31, "fib": 0},
    {"keywords": ["egg", "eggs"], "cal": 140, "prot": 12, "fib": 0},
    {"keywords": ["fish", "salmon", "tuna"], "cal": 200, "prot": 25, "fib": 0},
    {"keywords": ["coffee", "tea"], "cal": 25, "prot": 1, "fib": 0}
]

def parse_meal_nutrition(text: str) -> dict:
    """Natural Language keyword parser estimating Calories, Protein, and Fiber."""
    lower = text.lower()
    cal = 150
    prot = 4
    fib = 2

    for item in FOOD_DATABASE:
        for kw in item["keywords"]:
            if re.search(r'\b' + re.escape(kw) + r'\b', lower):
                cal += item["cal"]
                prot += int(item.get("prot", 4))
                fib += item["fib"]
                break

    return {"calories": cal, "protein": prot, "fiber": fib}

def call_gemini_api(api_key: str, query: str, user_profile: dict) -> str:
    """Optional direct call to Google Gemini 1.5 Flash API using standard library."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    system_prompt = (
        f"You are the HealthEngine AI Coach. The user is: {user_profile.get('name', 'User')}, "
        f"Gender: {user_profile.get('gender', 'not specified')}, Weight: {user_profile.get('weight', 67)}kg, "
        f"Goal: {user_profile.get('goal', 'muscle_gain')}, Diet: {user_profile.get('diet', 'Vegetarian')}, "
        f"Daily Protein Target: {user_profile.get('protein_target', 94)}g. "
        "Provide direct, concise, actionable advice (2 to 4 bullet points). Always reply directly to their specific question."
    )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"{system_prompt}\n\nUser Question: {query}"}]
            }
        ]
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=8) as response:
        data = json.loads(response.read().decode("utf-8"))
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        # Basic markdown to HTML bullet conversion
        lines = raw_text.split("\n")
        html_lines = []
        for line in lines:
            if line.strip().startswith("* ") or line.strip().startswith("- "):
                clean = line.strip()[2:].strip()
                html_lines.append(f"<li>{clean}</li>")
            elif line.strip():
                html_lines.append(f"<p class='mb-1 font-semibold text-purple-900'>{line.strip()}</p>")
        return f"<ul class='list-disc pl-4 space-y-1 text-slate-700'>{''.join(html_lines)}</ul>"

def get_ai_coaching_response(query: str, user_profile: dict, custom_key: str = None) -> str:
    """
    Intelligent multi-intent query router.
    Routes correctly to WORKOUT, INJURY, SLEEP, NUTRITION, or SUPPLEMENTS.
    Never returns irrelevant food templates to workout questions!
    """
    api_key = custom_key or os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            return call_gemini_api(api_key, query, user_profile)
        except Exception:
            pass  # Fall back to high-fidelity local intent engine

    q_lower = query.lower()
    gender = (user_profile.get("gender") or "male").lower()
    weight = user_profile.get("weight", 67)
    target = user_profile.get("protein_target", 94)

    # 1. WORKOUT & PROGRESSIVE OVERLOAD INTENTS
    workout_keywords = [
        "workout", "exercise", "lift", "lifting", "bench", "squat", "deadlift", "rdl",
        "overload", "progressive overload", "push", "pull", "legs", "rep", "reps", "set",
        "sets", "1rm", "chest", "bicep", "tricep", "shoulder", "back", "lat", "hypertrophy",
        "strength", "weights", "dumbbells", "barbell", "failure", "rpe", "rest"
    ]
    if any(k in q_lower for k in workout_keywords):
        if "bench" in q_lower or "chest" in q_lower:
            return f"""
            <div class="space-y-2">
              <p class="font-bold text-orange-950">🏋️ Chest & Bench Press Strategy ({gender.capitalize()}, {weight}kg):</p>
              <ul class="list-disc pl-4 space-y-1.5 text-slate-700">
                <li><strong>Progressive Overload Rule:</strong> Do not jump weight every session. If your previous benchmark was 50kg for 8 reps, today's objective is <strong>50kg for 9 to 10 clean reps</strong>.</li>
                <li><strong>Increment Threshold:</strong> Once you can hit 3 sets of 10 clean repetitions with no form breakdown, increase the load by the smallest increment (+2.5 kg total).</li>
                <li><strong>Scapular Retraction & Bar Path:</strong> Keep your shoulder blades retracted and depressed against the bench; lower the bar to your lower sternum with elbows tucked at a 45-degree angle.</li>
                <li><strong>Rest Periods:</strong> Allow 2.5 to 3 minutes between heavy working sets to fully replenish phosphocreatine (ATP).</li>
              </ul>
            </div>
            """
        elif "squat" in q_lower or "leg" in q_lower or "quad" in q_lower:
            return f"""
            <div class="space-y-2">
              <p class="font-bold text-orange-950">🏋️ Lower Body & Squat Progression:</p>
              <ul class="list-disc pl-4 space-y-1.5 text-slate-700">
                <li><strong>Depth & Footing:</strong> Stance slightly wider than shoulder-width, toes angled out 15–30 degrees. Descend until hip crease is below the knee (parallel or below).</li>
                <li><strong>Bracing Mechanism:</strong> Take a deep diaphragmatic breath into your core and brace (Valsalva maneuver) before initiating each repetition.</li>
                <li><strong>Overload Recommendation:</strong> Back squats respond best to 2.5kg wave loading. Target 3 working sets of 6–8 reps before adding load.</li>
              </ul>
            </div>
            """
        elif "rep" in q_lower or "set" in q_lower or "how many" in q_lower or "volume" in q_lower:
            return f"""
            <div class="space-y-2">
              <p class="font-bold text-orange-950">🏋️ Optimal Training Volume & Rep Ranges:</p>
              <ul class="list-disc pl-4 space-y-1.5 text-slate-700">
                <li><strong>Hypertrophy Sweet Spot:</strong> 10 to 16 total hard working sets per muscle group per week (e.g., 6-8 sets per Push session).</li>
                <li><strong>Rep Range:</strong> 6 to 10 reps for heavy compound movements (Bench, Squat, OHP); 10 to 15 reps for isolation (Tricep Pushdowns, Lateral Raises).</li>
                <li><strong>Intensity:</strong> Train within 1 to 2 reps in reserve (RIR 1-2) on compound lifts; push isolation sets to 0 RIR or failure.</li>
              </ul>
            </div>
            """
        else:
            return f"""
            <div class="space-y-2">
              <p class="font-bold text-orange-950">🏋️ Resistance Training & Progressive Overload Engine:</p>
              <ul class="list-disc pl-4 space-y-1.5 text-slate-700">
                <li><strong>The 3 Overload Pathways:</strong> (1) Add 1-2 reps at current weight, (2) Add weight once target reps are mastered, or (3) Improve movement tempo (3-second eccentric).</li>
                <li><strong>Fatigue Management:</strong> Rotate through your Push/Pull/Legs/Core split to ensure 48 hours recovery between the same primary muscle groups.</li>
                <li><strong>Warm-up Protocol:</strong> 2 progressive ramp-up sets (40% and 70% of working weight) before your first heavy working set.</li>
              </ul>
            </div>
            """

    # 2. INJURY & SORENESS INTENTS
    if any(k in q_lower for k in ["injury", "pain", "hurt", "sore", "soreness", "tweak", "pinch", "joint", "shoulder", "knee", "back"]):
        return """
        <div class="space-y-2">
          <p class="font-bold text-red-950">🩺 Injury Prevention & Joint Readiness:</p>
          <ul class="list-disc pl-4 space-y-1.5 text-slate-700">
            <li><strong>DOMS vs. Joint Pain:</strong> Muscle belly soreness 24-48 hours post-workout is normal. Sharp joint pain or localized tendon twinges require immediate load reduction.</li>
            <li><strong>Active Deload:</strong> If you feel a joint tweak, replace the exercise with a joint-friendly variation (e.g., replace barbell bench with neutral-grip dumbbell press).</li>
            <li><strong>Rotator Cuff & Hip Primers:</strong> Add 2 sets of external band rotations (face pulls) and glute bridges before loading heavy.</li>
          </ul>
        </div>
        """

    # 3. SLEEP & CHRONO-BIOLOGY INTENTS
    if any(k in q_lower for k in ["sleep", "shift", "night", "insomnia", "tired", "bed", "rest", "wake"]):
        return f"""
        <div class="space-y-2">
          <p class="font-bold text-indigo-950">🌙 Sleep Architecture & Chrono-Recovery:</p>
          <ul class="list-disc pl-4 space-y-1.5 text-slate-700">
            <li><strong>Caffeine Cutoff:</strong> Adenosine clearance takes 6-8 hours. Stop coffee or pre-workout by 4:00 PM if winding down by 11:00 PM.</li>
            <li><strong>Late Shift Wind-down:</strong> Avoid bright screen exposure during your final work hour; blue-light blocks pineal melatonin secretion.</li>
            <li><strong>Temperature & Darkness:</strong> Keep the bedroom at ~18-20°C (65-68°F). A dropping core body temperature signals the brain to enter Stage 3 deep slow-wave sleep.</li>
          </ul>
        </div>
        """

    # 4. NUTRITION & PROTEIN INTENTS
    if any(k in q_lower for k in ["food", "diet", "protein", "eat", "meal", "calorie", "carb", "macro", "shake", "snack"]):
        gender_note = "male lean mass targets" if gender == "male" else "female nitrogen balance & hormonal preservation"
        return f"""
        <div class="space-y-2">
          <p class="font-bold text-emerald-950">🥗 Targeted Nutrition & Protein Synthesis ({gender.capitalize()}, {target}g Target):</p>
          <ul class="list-disc pl-4 space-y-1.5 text-slate-700">
            <li><strong>Target Distribution:</strong> Spread your {target}g protein across 3 to 4 eating opportunities (~25g–35g per feeding) to sustain muscle protein synthesis.</li>
            <li><strong>Leucine Threshold:</strong> Ensure each main meal contains at least 2.5g of the essential amino acid leucine (found in greek yogurt, tofu/paneer, lentils + grains, or protein powder).</li>
            <li><strong>Carb Timing:</strong> Consume complex carbohydrates (brown rice, oats, sweet potatoes) around your training window to replenish muscle glycogen.</li>
            <li><strong>Hydration:</strong> Aim for 35ml to 40ml of water per kg of body weight (~2.5 to 3 liters daily) for intracellular volumization.</li>
          </ul>
        </div>
        """

    # 5. GENERAL COMPREHENSIVE HEALTH ENGINE SUMMARY
    return f"""
    <div class="space-y-2">
      <p class="font-bold text-purple-950">✨ HealthEngine Daily Readiness Synthesis ({user_profile.get('name', 'Athlete')}):</p>
      <ul class="list-disc pl-4 space-y-1.5 text-slate-700">
        <li><strong>Gender-Calibrated Target:</strong> Based on your {gender.capitalize()} physiology and {weight}kg body weight, your daily target is <strong>{target}g protein</strong>.</li>
        <li><strong>Training Objective:</strong> Complete your scheduled split with deliberate progressive overload; log all sets with exact weights and reps.</li>
        <li><strong>Recovery Baseline:</strong> Target 7.5 to 8.5 hours of sleep tonight to maximize testosterone/GH release and CNS recovery.</li>
      </ul>
    </div>
    """
