from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# ===================== WORKOUT MODELS =====================

class Exercise(BaseModel):
    name: str
    sets: int
    reps: str
    rest_seconds: int
    notes: Optional[str] = ""
    completed: bool = False


class DayWorkout(BaseModel):
    day: str
    focus: str
    exercises: List[Exercise]


class WorkoutPlan(BaseModel):
    user_id: str
    week: int
    days: List[DayWorkout]
    total_days_in_week: int
    generated_at: datetime


# ===================== USER PROFILE =====================

class UserProfile(BaseModel):
    user_id: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[int] = None
    weight_kg: Optional[float] = None
    fitness_goal: Optional[str] = None
    experience_level: Optional[str] = None
    available_days_per_week: int
    equipment: Optional[List[str]] = []


# ===================== REQUEST MODELS =====================

class GenerateWorkoutRequest(BaseModel):
    user_profile: UserProfile
    previous_workout: Optional[WorkoutPlan] = None
    feedback: Optional[str] = None


class RegenerateWorkoutRequest(BaseModel):
    user_id: str
    current_workout: WorkoutPlan
    feedback_type: str


class UpdateExerciseRequest(BaseModel):
    user_id: str
    day: str
    exercise_index: int
    completed: bool


# ===================== PROGRESS TRACKING =====================

class UserProgressDay(BaseModel):
    day: str
    total_exercises: int
    exercises_completed: int


class UserProgress(BaseModel):
    user_id: str
    days: List[UserProgressDay]
    current_streak: int = 0


class ProgressResponse(BaseModel):
    success: bool
    progress: UserProgress
    overall_completion: float
    current_streak: int


# ===================== RESPONSES =====================

class WorkoutResponse(BaseModel):
    success: bool
    workout: WorkoutPlan
    message: str
