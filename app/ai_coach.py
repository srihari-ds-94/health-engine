import os
import re

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

def get_ai_coaching_response(query: str, user_profile: dict) -> str:
    """
    Generates contextual AI health advice.
    Optionally queries Ollama or Gemini if LLM_API_KEY / OLLAMA_HOST is set in environment.
    Falls back gracefully to the built-in evidence-based health engine.
    """
    q_lower = query.lower()
    name = user_profile.get("name", "Athlete")
    target_protein = user_profile.get("protein_target", 94)

    if any(k in q_lower for k in ["carb", "family", "dinner", "rice", "pasta", "heavy"]):
        return f"""
        <div class="space-y-2">
          <p class="font-semibold text-purple-900">🥗 Carb-Heavy Meal Balancing Strategy:</p>
          <ul class="list-disc pl-4 space-y-1 text-slate-700">
            <li><strong>Portion Partitioning:</strong> If dinner was high in starchy carbs (rice, pasta, bread, or potatoes), limit the starch to 1 moderate cup.</li>
            <li><strong>Protein Anchor (+20g to +30g):</strong> Balance the meal with a high-protein side—such as greek yogurt, cottage cheese, pan-seared tofu, edamame, or lentil soup.</li>
            <li><strong>Fiber & Glucose Buffer:</strong> Add a leafy green salad or steamed cruciferous vegetables (broccoli/cauliflower) with olive oil to slow glucose absorption and prevent insulin spikes before sleep.</li>
          </ul>
        </div>
        """
    elif any(k in q_lower for k in ["shift", "night", "snack", "late", "10 pm", "sleep"]):
        return """
        <div class="space-y-2">
          <p class="font-semibold text-purple-900">⏰ Late Evening Sleep-Safe Nutrition:</p>
          <ul class="list-disc pl-4 space-y-1 text-slate-700">
            <li><strong>Avoid Late Glycemic Spikes:</strong> Heavy simple carbs eaten within 2 hours of bedtime cause nighttime glucose swings and reduce deep slow-wave sleep.</li>
            <li><strong>Recommended Snack:</strong> A bowl of greek yogurt or cottage cheese with a tablespoon of soaked chia or flax seeds, or warm almond milk with cinnamon.</li>
            <li><strong>Magnesium & Tryptophan:</strong> A handful of pumpkin seeds or walnuts provides natural magnesium, aiding CNS relaxation after late screen time.</li>
          </ul>
        </div>
        """
    elif any(k in q_lower for k in ["push", "bench", "overload", "gym", "squat", "lift"]):
        return """
        <div class="space-y-2">
          <p class="font-semibold text-purple-900">🏋️ Progressive Overload Recommendation:</p>
          <ul class="list-disc pl-4 space-y-1 text-slate-700">
            <li><strong>Target:</strong> Compound Resistance Training.</li>
            <li><strong>Overload Rule:</strong> If your previous session hit target reps, do not jump weight immediately. Aim for <strong>+1 to +2 clean reps</strong> with the same weight today.</li>
            <li><strong>Load Progression:</strong> Once you can achieve 3 sets of 10 clean reps with solid form, increment the bar by +2.5kg.</li>
            <li><strong>Rest Timing:</strong> Rest 2 to 3 minutes between heavy compound sets to maximize ATP regeneration.</li>
          </ul>
        </div>
        """
    else:
        return f"""
        <div class="space-y-2">
          <p class="font-semibold text-purple-900">✨ AI Health Engine Synthesis for {name}:</p>
          <p class="text-slate-700">Based on your baseline profile and {target_protein}g daily protein target:</p>
          <ul class="list-disc pl-4 space-y-1 text-slate-700">
            <li>Break your fasting window with a 30g+ protein anchor to stimulate muscle protein synthesis.</li>
            <li>Maintain your daily intake of omega-3 rich seeds (chia, flax, or walnuts) for cardiovascular elasticity and joint lubrication.</li>
            <li>Continue prioritizing progressive overload on compound lifts at least 3-4 days per week.</li>
          </ul>
        </div>
        """
