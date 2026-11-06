import os
import re
import json
import urllib.request
import urllib.error

# ==============================================================================
# 🔑 PASTE YOUR GOOGLE GEMINI API KEY HERE TO HARDCODE IT DIRECTLY IN VS CODE:
# ==============================================================================
HARDCODED_GEMINI_KEY = ""  # e.g., "AIzaSyYourActualKeyHere"

def _auto_load_env():
    """Auto-load .env file if present without needing external packages."""
    for base in [os.getcwd(), os.path.dirname(__file__), os.path.dirname(os.path.dirname(__file__))]:
        env_file = os.path.join(base, ".env")
        if os.path.exists(env_file):
            try:
                with open(env_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
            except Exception:
                pass
            break

_auto_load_env()

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
    """Direct call to Google Gemini API using standard library urllib."""
    api_key = api_key.strip()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    system_prompt = (
        f"You are the HealthEngine AI Coach. The athlete is: {user_profile.get('name', 'Athlete')}, "
        f"Biological Gender: {user_profile.get('gender', 'male')}, Weight: {user_profile.get('weight', 67)}kg, "
        f"Height: {user_profile.get('height', 175)}cm, Fitness Goal: {user_profile.get('goal', 'muscle_gain')}, "
        f"Diet: {user_profile.get('diet', 'Balanced')}, Daily Protein Target: {user_profile.get('protein_target', 97)}g. "
        "Provide direct, concise, scientifically accurate advice (2 to 4 bullet points). Always reply directly to their specific question."
    )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"{system_prompt}\n\nQuestion: {query}"}]
            }
        ]
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            data = json.loads(response.read().decode("utf-8"))
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            lines = raw_text.split("\n")
            html_lines = []
            for line in lines:
                clean = line.strip()
                if clean.startswith("* ") or clean.startswith("- "):
                    html_lines.append(f"<li>{clean[2:].strip()}</li>")
                elif clean:
                    html_lines.append(f"<p class='mb-1 font-semibold text-purple-900'>{clean}</p>")
            return f"<div class='space-y-1.5'><p class='text-[10px] text-emerald-700 font-bold mb-1'>✨ Live Gemini 1.5 Flash Response</p><ul class='list-disc pl-4 space-y-1 text-slate-700'>{''.join(html_lines)}</ul></div>"
    except urllib.error.HTTPError as http_err:
        err_body = http_err.read().decode("utf-8", errors="ignore")
        print(f"[Gemini API HTTP Error {http_err.code}]: {err_body}")
        try:
            err_json = json.loads(err_body)
            err_msg = err_json.get("error", {}).get("message", http_err.reason)
        except Exception:
            err_msg = str(http_err)
        return f"""
        <div class="p-3 bg-red-50 text-red-900 rounded-xl border border-red-200 text-xs">
          <p class="font-bold">⚠️ Google Gemini API Error ({http_err.code}):</p>
          <p class="mt-0.5 text-red-700">{err_msg}</p>
          <p class="mt-1 text-[11px] text-slate-500">Please check that your Gemini API key is active at <a href="https://aistudio.google.com/" target="_blank" class="underline font-bold text-red-800">aistudio.google.com</a>.</p>
        </div>
        """
    except Exception as e:
        print(f"[Gemini API Connection Error]: {e}")
        return f"""
        <div class="p-3 bg-red-50 text-red-900 rounded-xl border border-red-200 text-xs">
          <p class="font-bold">⚠️ Gemini Connection Error:</p>
          <p class="mt-0.5 text-red-700">{str(e)}</p>
        </div>
        """

def get_ai_coaching_response(query: str, user_profile: dict, custom_key: str = None) -> str:
    """
    Intelligent multi-intent query router.
    Checks for Gemini API Key first. If none is active, routes through an extensive,
    highly specific domain knowledge base.
    """
    api_key = (
        (custom_key.strip() if custom_key else None) or
        os.getenv("GEMINI_API_KEY") or
        (HARDCODED_GEMINI_KEY.strip() if HARDCODED_GEMINI_KEY else None)
    )

    if api_key:
        return call_gemini_api(api_key, query, user_profile)

    q_lower = query.lower()
    gender = (user_profile.get("gender") or "male").lower()
    weight = user_profile.get("weight", 67)
    target = user_profile.get("protein_target", 97)
    diet = user_profile.get("diet", "Balanced")

    # 1. INJURY & SAFETY (HIGHEST PRIORITY)
    if any(k in q_lower for k in ["pinch", "shoulder", "knee", "pain", "injury", "hurt", "tweak", "impingement", "joint", "rotator cuff"]):
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

    # 2. SPECIFIC EXERCISES
    if "pullup" in q_lower or "pull up" in q_lower or "chin up" in q_lower or "chinup" in q_lower:
        return """
        <div class="space-y-2">
          <p class="font-bold text-orange-950">🏋️ Pull-Up Mastery & Progressive Overload:</p>
          <ul class="list-disc pl-4 space-y-1.5 text-slate-700">
            <li><strong>Scapular Initiation:</strong> Don't yank with your arms first. Depress and retract your scapulae (pull shoulder blades down and back) before bending your elbows.</li>
            <li><strong>Progression Pathway:</strong> If you cannot do 5 clean bodyweight reps yet, use eccentric negatives (jump up, take 4 full seconds to lower) or heavy resistance bands.</li>
            <li><strong>Overload Trigger:</strong> Once you can achieve 3 sets of 8 clean bodyweight pull-ups, introduce a dip belt with a 2.5kg or 5kg plate to build upper back thickness.</li>
          </ul>
        </div>
        """

    if "bench" in q_lower or "chest press" in q_lower:
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

    if "squat" in q_lower or "quad" in q_lower:
        return """
        <div class="space-y-2">
          <p class="font-bold text-orange-950">🏋️ Lower Body & Squat Progression:</p>
          <ul class="list-disc pl-4 space-y-1.5 text-slate-700">
            <li><strong>Depth & Footing:</strong> Stance slightly wider than shoulder-width, toes angled out 15–30 degrees. Descend until hip crease is parallel with knees.</li>
            <li><strong>Bracing Mechanism:</strong> Take a deep diaphragmatic breath into your core and brace (Valsalva maneuver) before initiating each repetition.</li>
            <li><strong>Overload Recommendation:</strong> Back squats respond best to 2.5kg wave loading. Target 3 working sets of 6–8 reps before adding load.</li>
          </ul>
        </div>
        """

    if "deadlift" in q_lower or "rdl" in q_lower or "hamstring" in q_lower:
        return """
        <div class="space-y-2">
          <p class="font-bold text-orange-950">🏋️ Hinge Mechanics & Deadlift / RDL Form:</p>
          <ul class="list-disc pl-4 space-y-1.5 text-slate-700">
            <li><strong>The Hip Hinge:</strong> Push your hips backward towards the wall behind you rather than squatting down. Keep the bar gliding directly against your shins and thighs.</li>
            <li><strong>Lat Engagement:</strong> Engage your lats by squeezing imaginary oranges in your armpits. This prevents thoracic rounding and protects spinal erectors.</li>
            <li><strong>Hamstring Stretch:</strong> Stop descending the moment your hips stop traveling backward (usually just below the kneecap on RDLs).</li>
          </ul>
        </div>
        """

    if "bicep" in q_lower or "arm" in q_lower or "tricep" in q_lower:
        return """
        <div class="space-y-2">
          <p class="font-bold text-orange-950">💪 Arm Hypertrophy & Isolation Loading:</p>
          <ul class="list-disc pl-4 space-y-1.5 text-slate-700">
            <li><strong>Elbow Stability:</strong> Keep your elbows pinned at your sides during curls. If your elbows drift forward, your front deltoids take over the tension from your biceps.</li>
            <li><strong>Tricep Long Head:</strong> Overhead cable extensions recruit the long head of the tricep (which makes up 60% of upper arm size).</li>
            <li><strong>Volume Prescription:</strong> 6 to 8 weekly sets of direct bicep and tricep isolation is optimal when already performing compound Push/Pull movements.</li>
          </ul>
        </div>
        """

    if "ab" in q_lower or "core" in q_lower or "plank" in q_lower:
        return """
        <div class="space-y-2">
          <p class="font-bold text-orange-950">🧱 Core Strength & Abdominal Development:</p>
          <ul class="list-disc pl-4 space-y-1.5 text-slate-700">
            <li><strong>Progressive Ab Training:</strong> Abs are a muscle like any other. Endless high-rep crunches produce diminishing returns. Train them with resistance (cable crunches, hanging leg raises).</li>
            <li><strong>Posterior Pelvic Tilt:</strong> During hanging leg raises and planks, tuck your pelvis under to fully engage the rectus abdominis rather than overworking the hip flexors.</li>
            <li><strong>Visibility:</strong> Visible definition is driven primarily by body fat percentage (caloric balance), while core stability prevents lower back pain on heavy squats and deadlifts.</li>
          </ul>
        </div>
        """

    # 3. SUPPLEMENTS
    if "creatine" in q_lower:
        return """
        <div class="space-y-2">
          <p class="font-bold text-purple-950">⚡ Creatine Monohydrate Protocol:</p>
          <ul class="list-disc pl-4 space-y-1.5 text-slate-700">
            <li><strong>Dosing:</strong> Take 3g to 5g of pure Creatine Monohydrate daily. No expensive loading phase or cycling off is necessary.</li>
            <li><strong>Mechanism:</strong> Saturates intramuscular phosphocreatine stores, increasing power output on heavy 1-5 rep sets and pulling intracellular water into muscle cells.</li>
            <li><strong>Hydration Note:</strong> Drink an extra 500ml of water daily to support intracellular hydration.</li>
          </ul>
        </div>
        """

    if "whey" in q_lower or "protein powder" in q_lower or "supplement" in q_lower:
        return f"""
        <div class="space-y-2">
          <p class="font-bold text-purple-950">🥛 Protein Supplementation Strategy:</p>
          <ul class="list-disc pl-4 space-y-1.5 text-slate-700">
            <li><strong>Whole Food First:</strong> Protein powder is a convenience tool. Use it to comfortably hit your {target}g target when traveling or on a busy shift.</li>
            <li><strong>Source Comparison:</strong> Whey Isolate offers rapid digestion with ~2.7g leucine per scoop. Pea + Rice protein blends provide an identical amino acid profile for plant-based athletes.</li>
          </ul>
        </div>
        """

    # 4. KETO & NUTRITION
    if any(k in q_lower for k in ["keto", "ketogenic", "carb", "carbs", "fat loss", "cut", "bulk"]):
        if "keto" in q_lower or "keto" in diet.lower():
            return f"""
            <div class="space-y-2">
              <p class="font-bold text-emerald-950">🥑 Ketogenic Macro Management ({gender.capitalize()}):</p>
              <ul class="list-disc pl-4 space-y-1.5 text-slate-700">
                <li><strong>Carb Limit:</strong> Keep net carbohydrates strictly under 30g to 50g daily to maintain liver ketone production.</li>
                <li><strong>Protein Moderation:</strong> Your target of <strong>{target}g protein</strong> is calibrated to preserve muscle without excessive gluconeogenesis.</li>
                <li><strong>Electrolytes:</strong> Add 2g-3g of sodium (sea salt) and ensure adequate magnesium & potassium to prevent keto fatigue.</li>
                <li><strong>Healthy Fats:</strong> Anchor calories with avocado, extra virgin olive oil, nuts, and MCTs.</li>
              </ul>
            </div>
            """
        else:
            return f"""
            <div class="space-y-2">
              <p class="font-bold text-emerald-950">🥗 Nutrition & Macronutrient Distribution ({target}g Target):</p>
              <ul class="list-disc pl-4 space-y-1.5 text-slate-700">
                <li><strong>Distribution:</strong> Spread your {target}g protein across 3 to 4 meals (~25g–35g per feeding) to optimize muscle protein synthesis.</li>
                <li><strong>Energy Balance:</strong> For hypertrophy, eat in a modest 250-300 kcal surplus. For fat loss, maintain a 300-500 kcal deficit while keeping protein high.</li>
                <li><strong>Post-Workout Window:</strong> Consume a balanced protein and carbohydrate meal within 1-2 hours after your session to replenish glycogen.</li>
              </ul>
            </div>
            """

    # 5. GENERAL WORKOUT OVERLOAD
    workout_keywords = ["workout", "exercise", "lift", "lifting", "overload", "progressive overload", "push", "pull", "legs", "rep", "reps", "set", "sets", "1rm", "hypertrophy", "strength", "weights", "dumbbells", "barbell", "failure", "rpe", "rest"]
    if any(k in q_lower for k in workout_keywords):
        return f"""
        <div class="space-y-2">
          <p class="font-bold text-orange-950">🏋️ Progressive Overload & Training Volume:</p>
          <ul class="list-disc pl-4 space-y-1.5 text-slate-700">
            <li><strong>The 3 Overload Pathways:</strong> (1) Add 1-2 reps at current weight, (2) Add weight once target reps are mastered, or (3) Improve movement tempo (3-second eccentric).</li>
            <li><strong>Volume Target:</strong> Aim for 10-14 hard working sets per muscle group per week within 1-2 Reps In Reserve (RIR).</li>
            <li><strong>Rest Timing:</strong> Rest 2 to 3 minutes between heavy compound sets to maximize ATP replenishment.</li>
          </ul>
        </div>
        """

    # 6. SLEEP & CHRONO-BIOLOGY
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

    # 7. DEFAULT PERSONALIZED SUMMARY
    return f"""
    <div class="space-y-2">
      <p class="font-bold text-purple-950">✨ HealthEngine Daily Synthesis ({user_profile.get('name', 'Athlete')}):</p>
      <ul class="list-disc pl-4 space-y-1.5 text-slate-700">
        <li><strong>Biological Baseline:</strong> Calibrated for {gender.capitalize()}, {weight}kg, targeting {target}g protein daily on a {diet} protocol.</li>
        <li><strong>Training Focus:</strong> Progressive overload on compound lifts with 2-3 minutes rest between working sets.</li>
        <li><strong>Recovery:</strong> Target 7.5 to 8.5 hours of sleep to support natural endocrine recovery and tissue synthesis.</li>
      </ul>
    </div>
    """
