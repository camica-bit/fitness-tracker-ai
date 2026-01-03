import os
import json
from datetime import datetime

import google.generativeai as genai
from models import WorkoutPlan
from prompts import build_gemini_prompt


class GeminiError(Exception):
    pass


class GeminiWorkoutGenerator:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise GeminiError("GEMINI_API_KEY is missing")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-flash-latest")

    def generate_workout(self, user_profile, user_id, previous_workout=None, feedback=None):
        prompt = build_gemini_prompt(
            user_profile=user_profile.model_dump(),
            previous_workout=previous_workout.model_dump() if previous_workout else None,
            feedback=feedback,
        )

        try:
            response = self.model.generate_content(prompt)
            raw_text = response.text.strip()

            # Parse JSON strictly
            data = json.loads(raw_text)

            # Inject required backend fields
            data["user_id"] = user_id
            data["generated_at"] = datetime.utcnow()

            # Validate with Pydantic
            return WorkoutPlan(**data)

        except json.JSONDecodeError as e:
            raise GeminiError(f"Invalid JSON from Gemini: {e}")

        except Exception as e:
            raise GeminiError(str(e))


def create_gemini_generator():
    return GeminiWorkoutGenerator()
