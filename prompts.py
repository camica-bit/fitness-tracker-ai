
def build_gemini_prompt(user_profile, previous_workout=None, feedback=None):
    days = user_profile.get("available_days_per_week")

    if not days:
        raise ValueError("available_days_per_week is required")
    return f"""

You are an expert fitness coach AI.

You MUST return ONLY valid JSON.
NO explanations.
NO markdown.
NO text outside JSON.

The JSON MUST strictly follow this schema:

{{
  "week": number,
  "days": [
    {{
      "day": string,
      "focus": string,
      "exercises": [
        {{
          "name": string,
          "sets": number,
          "reps": string,
          "rest_seconds": number,
          "notes": string,
          "completed": false
        }}
      ]
    }}
  ],
  "total_days_in_week": number
}}

User profile:
{user_profile}

Previous workout:
{previous_workout}

User feedback:
{feedback}

Rules:
CRITICAL RULES:
1. You MUST generate EXACTLY {days} workout days.
2. Do NOT generate more or fewer days under any circumstance.
3. Each day MUST be explicitly numbered from Day 1 to Day {days}.
4. If you cannot comply, regenerate internally until you can.
- Use realistic exercises
- Match user's fitness level and goal
- Respect available days per week
- Make workouts varied and progressive
"""
def build_motivational_quotes():
    return [
        "Push yourself, because no one else is going to do it for you.",
        "Your body can stand almost anything. It’s your mind you have to convince.",
        "Success starts with self-discipline.",
        "No pain, no gain. Shut up and train.",
        "Small progress is still progress.",
        "Don’t limit your challenges. Challenge your limits.",
        "Sweat is just fat crying.",
        "Train insane or remain the same.",
        "Discipline is choosing between what you want now and what you want most.",
        "The hard part isn’t getting your body in shape. The hard part is getting your mind in shape."
    ]
