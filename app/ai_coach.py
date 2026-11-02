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
        f"Daily Protein Target: {user_profile.get('protein_target', 97)}g. "
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
    Prioritizes INJURY/SAFETY first, then WORKOUT, SLEEP, NUTRITION.
    """
    api_key = custom_key or os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            return call_gemini_api(api_key, query, user_profile)
        except Exception:
            pass

    q_lower = query.lower()
    gender = (user_profile.get("gender") or "male").lower()
    weight = user_profile.get("weight", 67)
    target = user_profile.get("protein_target", 97)
    diet = user_profile.get("diet", "Balanced")

    # 1. INJURY & SAFETY INTENTS (HIGHEST PRIORITY)
    injury_keywords = ["pinch", "shoulder", "knee", "pain", "injury", "hurt", "tweak", "impingement", "joint", "rotator cuff"]
    if any(k in q_lower for k in injury_keywords):
        return """
        <div class="space-y-2">
          <p class="font-bold text-red-950">🩺 Joint Protection & Injury Mitigation:</p>
          <ul class="list-disc pl-4 space-y-1.5 text-slate-700">
            <li><strong>Shoulder Pinch Mechanics:</strong> A tweak on overhead pressing usually stems from flared elbows or lack of thoracic spine extension. Tuck elbows 30° inward in the scapular plane.</li>
            <li><strong>Pain-Free Substitutions:</strong> Switch from straight barbells to neutral-grip dumbbells, landmine presses, or high incline presses to avoid subacromial impingement.</li>
            <li><strong>Rotator Cuff Priming:</strong> Perform 2 sets of 15 face pulls and band pull-aparts to activate external rotators and stabilizers before pressing.</li>
          </ul>
        </div>
        """

    # 2. WORKOUT & PROGRESSIVE OVERLOAD INTENTS
    workout_keywords = [
        "workout", "exercise", "lift", "lifting", "bench", "squat", "deadlift", "rdl",
        "overload", "progressive overload", "push", "pull", "legs", "rep", "reps", "set",
        "sets", "1rm", "chest", "bicep", "tricep", "back", "lat", "hypertrophy",
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
                <li><strong>Depth & Footing:</strong> Stance slightly wider than shoulder-width, toes angled out 15–30 degrees. Descend until hip crease is parallel with knees.</li>
                <li><strong>Bracing Mechanism:</strong> Take a deep diaphragmatic breath into your core and brace (Valsalva maneuver) before initiating each repetition.</li>
                <li><strong>Overload Recommendation:</strong> Back squats respond best to 2.5kg wave loading. Target 3 working sets of 6–8 reps before adding load.</li>
              </ul>
            </div>
            """
        else:
            return f"""
            <div class="space-y-2">
              <p class="font-bold text-orange-950">🏋️ Progressive Overload & Training Volume:</p>
              <ul class="list-disc pl-4 space-y-1.5 text-slate-700">
                <li><strong>The 3 Overload Pathways:</strong> (1) Add 1-2 reps at current weight, (2) Add weight once target reps are mastered, or (3) Improve movement tempo (3-second eccentric).</li>
                <li><strong>Volume Target:</strong> Aim for 10-14 hard working sets per muscle group per week within 1-2 Reps In Reserve (RIR).</li>
                <li><strong>Compound Priming:</strong> Perform 2 light warmup ramp-up sets before your first heavy working set.</li>
              </ul>
            </div>
            """

    # 3. SLEEP & CHRONO-BIOLOGY INTENTS
    if any(k in q_lower for k in ["sleep", "shift", "night", "insomnia", "tired", "bed", "rest", "wake"]):
        return f"""
        <div class="space-y-2">
          <p class="font-bold text-indigo-950">🌙 Sleep Architecture & Chrono-Recovery:</p>
          <ul class="list-disc pl-4 space-y-1.5 text-slate-700">
            <li><strong>Caffeine Cutoff:</strong> Adenosine clearance takes 6-8 hours. Stop caffeine 7 hours prior to bedtime.</li>
            <li><strong>Late Shift Wind-down:</strong> Avoid bright screen exposure during your final work hour; blue-light blocks pineal melatonin secretion.</li>
            <li><strong>Temperature:</strong> Keep the bedroom cool (~18-20°C / 65-68°F) to facilitate the natural core body temperature drop needed for Stage 3 deep sleep.</li>
          </ul>
        </div>
        """

    # 4. NUTRITION & KETO INTENTS
    if any(k in q_lower for k in ["keto", "ketogenic", "carbs", "carb", "protein", "food", "eat", "meal", "fat"]):
        if "keto" in q_lower or "keto" in diet.lower():
            return f"""
            <div class="space-y-2">
              <p class="font-bold text-emerald-950">🥑 Ketogenic Protocol & Macro Management ({gender.capitalize()}):</p>
              <ul class="list-disc pl-4 space-y-1.5 text-slate-700">
                <li><strong>Carb Limit:</strong> Keep net carbohydrates strictly under 30g to 50g daily to maintain liver ketone production (acetoacetate/beta-hydroxybutyrate).</li>
                <li><strong>Protein Moderation:</strong> Your target of <strong>{target}g protein</strong> is calibrated to preserve muscle without excessive gluconeogenesis.</li>
                <li><strong>Electrolyte Balance:</strong> In ketosis, kidneys excrete sodium rapidly. Add 2g-3g of sodium (sea salt) and ensure adequate magnesium & potassium to prevent keto fatigue.</li>
                <li><strong>Healthy Fats:</strong> Anchor calories with avocado, extra virgin olive oil, nuts, and MCTs.</li>
              </ul>
            </div>
            """
        else:
            return f"""
            <div class="space-y-2">
              <p class="font-bold text-emerald-950">🥗 Targeted Nutrition & Protein Synthesis ({target}g Target):</p>
              <ul class="list-disc pl-4 space-y-1.5 text-slate-700">
                <li><strong>Distribution:</strong> Spread your {target}g protein across 3 to 4 meals (~25g–35g per feeding) to optimize muscle protein synthesis.</li>
                <li><strong>Leucine Threshold:</strong> Ensure each main meal contains at least 2.5g of leucine for mTOR pathway activation.</li>
                <li><strong>Post-Workout Window:</strong> Consume a balanced protein and carbohydrate meal within 1-2 hours after your session to replenish glycogen.</li>
              </ul>
            </div>
            """

    # 5. GENERAL SUMMARY
    return f"""
    <div class="space-y-2">
      <p class="font-bold text-purple-950">✨ HealthEngine Daily Synthesis ({user_profile.get('name', 'Athlete')}):</p>
      <ul class="list-disc pl-4 space-y-1.5 text-slate-700">
        <li><strong>Biological Baseline:</strong> Calibrated for {gender.capitalize()}, {weight}kg, targeting {target}g protein daily.</li>
        <li><strong>Training Focus:</strong> Progressive overload on compound lifts with 2-3 minutes rest between working sets.</li>
        <li><strong>Recovery:</strong> Target 7.5 to 8.5 hours of sleep to support natural endocrine recovery and tissue synthesis.</li>
      </ul>
    </div>
    """
