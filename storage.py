"""
Storage layer for Fitness Tracker.
Handles in-memory storage and JSON persistence.
"""

import json
import os
from typing import Dict, Optional, List
from models import UserProfile, WorkoutPlan, UserProgress, DayWorkout, UserProgressDay
from datetime import datetime


class StorageManager:
    """Manages application data storage (in-memory + JSON)."""

    def __init__(self, data_dir: str = "data"):
        """
        Initialize storage manager.
        
        Args:
            data_dir: Directory for JSON persistence files
        """
        self.data_dir = data_dir
        self.users_file = os.path.join(data_dir, "users.json")
        self.workouts_file = os.path.join(data_dir, "workouts.json")
        self.progress_file = os.path.join(data_dir, "progress.json")
        
        # In-memory storage
        self.users: Dict[str, UserProfile] = {}
        self.workouts: Dict[str, List[WorkoutPlan]] = {}  # user_id -> list of workouts
        self.progress: Dict[str, UserProgress] = {}
        
        # Create data directory if needed
        os.makedirs(data_dir, exist_ok=True)
        
        # Load from files
        self._load_from_disk()

    def _load_from_disk(self) -> None:
        """Load data from JSON files."""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    users_data = json.load(f)
                    self.users = {
                        uid: UserProfile(**data) 
                        for uid, data in users_data.items()
                    }
            except Exception as e:
                print(f"Error loading users: {e}")

        if os.path.exists(self.workouts_file):
            try:
                with open(self.workouts_file, 'r') as f:
                    workouts_data = json.load(f)
                    self.workouts = {
                        uid: [WorkoutPlan(**w) for w in workouts]
                        for uid, workouts in workouts_data.items()
                    }
            except Exception as e:
                print(f"Error loading workouts: {e}")

        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r') as f:
                    progress_data = json.load(f)
                    self.progress = {
                        uid: UserProgress(**data)
                        for uid, data in progress_data.items()
                    }
            except Exception as e:
                print(f"Error loading progress: {e}")

    def _save_to_disk(self) -> None:
        """Save data to JSON files."""
        try:
            # Save users
            users_data = {
                uid: user.model_dump()
                for uid, user in self.users.items()
            }
            with open(self.users_file, 'w') as f:
                json.dump(users_data, f, indent=2)

            # Save workouts
            workouts_data = {
                uid: [w.model_dump() for w in workouts]
                for uid, workouts in self.workouts.items()
            }
            with open(self.workouts_file, 'w') as f:
                json.dump(workouts_data, f, indent=2)

            # Save progress
            progress_data = {
                uid: progress.model_dump()
                for uid, progress in self.progress.items()
            }
            with open(self.progress_file, 'w') as f:
                json.dump(progress_data, f, indent=2)
        except Exception as e:
            print(f"Error saving to disk: {e}")

    # User Profile Methods

    def save_user_profile(self, profile: UserProfile) -> None:
        """Save user profile."""
        self.users[profile.user_id] = profile
        self._save_to_disk()

    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by ID."""
        return self.users.get(user_id)

    def user_exists(self, user_id: str) -> bool:
        """Check if user exists."""
        return user_id in self.users

    # Workout Methods

    def save_workout(self, workout: WorkoutPlan) -> None:
        """Save/update workout plan for user."""
        if workout.user_id not in self.workouts:
            self.workouts[workout.user_id] = []
        self.workouts[workout.user_id].append(workout)
        self._save_to_disk()

    def get_current_workout(self, user_id: str) -> Optional[WorkoutPlan]:
        """Get the most recent workout for user."""
        if user_id not in self.workouts or not self.workouts[user_id]:
            return None
        return self.workouts[user_id][-1]

    def get_all_workouts(self, user_id: str) -> List[WorkoutPlan]:
        """Get all workouts for user."""
        return self.workouts.get(user_id, [])

    def update_exercise_completion(
        self,
        user_id: str,
        day: str,
        exercise_index: int,
        completed: bool
    ) -> bool:
        """
        Update exercise completion status.
        
        Args:
            user_id: User ID
            day: Day name
            exercise_index: Index of exercise in day
            completed: Completion status
            
        Returns:
            True if successful, False otherwise
        """
        workout = self.get_current_workout(user_id)
        if not workout:
            return False

        for day_workout in workout.days:
            if day_workout.day.lower() == day.lower():
                if 0 <= exercise_index < len(day_workout.exercises):
                    day_workout.exercises[exercise_index].completed = completed
                    self._save_to_disk()
                    return True
        
        return False

    # Progress Methods

    def initialize_progress(self, user_id: str, total_days: int) -> UserProgress:
        """Initialize progress tracking for user."""
        progress = UserProgress(
            user_id=user_id,
            week=1,
            days=[
                UserProgressDay(day=f"Day {i+1}", exercises_completed=0, total_exercises=0)
                for i in range(total_days)
            ],
            current_streak=0
        )
        self.progress[user_id] = progress
        self._save_to_disk()
        return progress

    def get_progress(self, user_id: str) -> Optional[UserProgress]:
        """Get user progress."""
        return self.progress.get(user_id)

    def update_progress(self, user_id: str, progress: UserProgress) -> None:
        """Update user progress."""
        self.progress[user_id] = progress
        self._save_to_disk()

    def calculate_completion_percentage(self, user_id: str) -> float:
        """
        Calculate overall completion percentage for the week.
        
        Args:
            user_id: User ID
            
        Returns:
            Completion percentage (0-100)
        """
        progress = self.get_progress(user_id)
        if not progress or not progress.days:
            return 0.0

        total_exercises = sum(d.total_exercises for d in progress.days)
        if total_exercises == 0:
            return 0.0

        completed_exercises = sum(d.exercises_completed for d in progress.days)
        return (completed_exercises / total_exercises) * 100

    def update_streak(self, user_id: str, new_streak: int) -> None:
        """Update user's workout streak."""
        progress = self.get_progress(user_id)
        if progress:
            progress.current_streak = new_streak
            self.update_progress(user_id, progress)

    def clear_all_data(self) -> None:
        """Clear all stored data (for testing/reset)."""
        self.users.clear()
        self.workouts.clear()
        self.progress.clear()
        self._save_to_disk()


# Global storage instance
_storage: Optional[StorageManager] = None


def get_storage() -> StorageManager:
    """Get or create the global storage instance."""
    global _storage
    if _storage is None:
        _storage = StorageManager()
    return _storage


def reset_storage() -> None:
    """Reset the storage instance (useful for testing)."""
    global _storage
    _storage = None
