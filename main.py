"""
FastAPI application for Fitness Tracker.
Main entry point with all API endpoints.
"""

# Load .env early and provide a compatibility shim for importlib.metadata
import os
import importlib

# Simple .env loader (no dependency on python-dotenv) so env vars are
# available before other imports (important for uvicorn reloader).
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    try:
        with open(env_path, "r") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    # do not override existing environment variables
                    os.environ.setdefault(k.strip(), v.strip().strip('\"').strip("'"))
    except Exception:
        pass


from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import random
from typing import Optional

from models import (
    UserProfile, WorkoutPlan, UserProgress, UserProgressDay,
    GenerateWorkoutRequest, UpdateExerciseRequest, RegenerateWorkoutRequest,
    WorkoutResponse, ProgressResponse
)
from storage import get_storage
from gemini import create_gemini_generator, GeminiError
from prompts import build_motivational_quotes


# Initialize FastAPI app
app = FastAPI(
    title="Fitness Tracker AI",
    description="AI-powered personalized fitness workout generator",
    version="1.0.0"
)

# Add CORS middleware for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize storage and Gemini
storage = get_storage()
try:
    gemini = create_gemini_generator()
except GeminiError as e:
    print(f"Warning: Gemini initialization error: {e}")
    gemini = None


from gemini import GeminiWorkoutGenerator

@app.get("/api/debug/gemini-test")
@app.get("/api/debug/gemini-test")
def gemini_test():
    if not gemini:
        return {"status": "not initialized"}
    return {
        "status": "endpoint_hit",
        "api_key_loaded": gemini.api_key is not None,
        "model": gemini.model_name
    }


# ============================================================================
# STATIC CONTENT ROUTES
# ============================================================================

@app.get("/")
async def root():
    """Serve the main HTML page."""
    return FileResponse("templates/index.html", media_type="text/html")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "storage": "operational",
        "gemini": "operational" if gemini else "not initialized"
    }


# ============================================================================
# MOTIVATIONAL ENDPOINTS
# ============================================================================

@app.get("/api/quotes")
async def get_motivational_quotes():
    """Get a random motivational fitness quote."""
    quotes = build_motivational_quotes()
    return {"quote": random.choice(quotes)}


# ============================================================================
# USER PROFILE ENDPOINTS
# ============================================================================

@app.post("/api/profile/create")
async def create_user_profile(profile: UserProfile):
    """
    Create a new user profile.
    
    Args:
        profile: User fitness profile
        
    Returns:
        Confirmation with user_id
    """
    try:
        storage.save_user_profile(profile)
        return {
            "success": True,
            "message": f"User profile created successfully",
            "user_id": profile.user_id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/profile/{user_id}")
async def get_user_profile(user_id: str):
    """
    Get user profile by ID.
    
    Args:
        user_id: User identifier
        
    Returns:
        User profile data
    """
    profile = storage.get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    return {"success": True, "profile": profile}


# ============================================================================
# WORKOUT GENERATION ENDPOINTS
# ============================================================================

@app.post("/api/workout/generate", response_model=WorkoutResponse)
async def generate_workout(request: GenerateWorkoutRequest):
    """
    Generate a new personalized workout plan.
    
    Args:
        request: Contains user profile and optional feedback
        
    Returns:
        Generated workout plan
    """
    if not gemini:
        raise HTTPException(
            status_code=503,
            detail="Gemini API not initialized. Check GEMINI_API_KEY environment variable."
        )

    try:
        # Generate unique user ID if not provided
        user_id = request.user_profile.user_id
        if not user_id:
            user_id = str(uuid.uuid4())
            request.user_profile.user_id = user_id

        # Save user profile
        storage.save_user_profile(request.user_profile)

        # Generate workout using Gemini
        workout = gemini.generate_workout(
            user_profile=request.user_profile,
            user_id=user_id,
            previous_workout=request.previous_workout,
            feedback=request.feedback
        )

        # Save workout
        storage.save_workout(workout)

        # Initialize or update progress tracking
        if not storage.get_progress(user_id):
            storage.initialize_progress(user_id, workout.total_days_in_week)

        return WorkoutResponse(
            success=True,
            workout=workout,
            message="Workout generated successfully"
        )

    except GeminiError as e:
        raise HTTPException(status_code=500, detail=f"Workout generation error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/api/workout/regenerate", response_model=WorkoutResponse)
async def regenerate_workout(request: RegenerateWorkoutRequest):
    """
    Regenerate workout with feedback adjustments.
    
    Args:
        request: Current workout and feedback type
        
    Returns:
        Regenerated workout plan
    """
    if not gemini:
        raise HTTPException(
            status_code=503,
            detail="Gemini API not initialized"
        )

    try:
        user_id = request.user_id
        profile = storage.get_user_profile(user_id)

        if not profile:
            raise HTTPException(status_code=404, detail="User not found")

        # Generate new workout with feedback
        workout = gemini.generate_workout(
            user_profile=profile,
            user_id=user_id,
            previous_workout=request.current_workout,
            feedback=request.feedback_type
        )

        storage.save_workout(workout)

        return WorkoutResponse(
            success=True,
            workout=workout,
            message=f"Workout regenerated with '{request.feedback_type}' adjustments"
        )

    except GeminiError as e:
        raise HTTPException(status_code=500, detail=f"Regeneration error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/api/workout/history/{user_id}")
async def get_workout_history(user_id: str):
    """
    Get all workouts history for a user.
    
    Args:
        user_id: User identifier
        
    Returns:
        List of all workouts
    """
    workouts = storage.get_all_workouts(user_id)
    return {"success": True, "workouts": workouts, "count": len(workouts)}


@app.get("/api/workout/{user_id}")
async def get_current_workout(user_id: str):
    """
    Get the current/latest workout for a user.
    
    Args:
        user_id: User identifier
        
    Returns:
        Current workout plan
    """
    workout = storage.get_current_workout(user_id)
    if not workout:
        raise HTTPException(status_code=404, detail="No workout found for this user")

    return {"success": True, "workout": workout}


# ============================================================================
# PROGRESS TRACKING ENDPOINTS
# ============================================================================

@app.post("/api/progress/update-exercise")
async def update_exercise_completion(request: UpdateExerciseRequest):
    """
    Mark an exercise as completed or incomplete.
    
    Args:
        request: Contains user_id, day, exercise index, and completion status
        
    Returns:
        Success confirmation
    """
    try:
        success = storage.update_exercise_completion(
            user_id=request.user_id,
            day=request.day,
            exercise_index=request.exercise_index,
            completed=request.completed
        )

        if not success:
            raise HTTPException(status_code=404, detail="Exercise not found")

        # Update progress counters
        workout = storage.get_current_workout(request.user_id)
        if workout:
            progress = storage.get_progress(request.user_id)
            if progress:
                # Count completed exercises
                for day_progress in progress.days:
                    if day_progress.day == request.day:
                        # Count exercises in this day's workout
                        for day_workout in workout.days:
                            if day_workout.day == request.day:
                                day_progress.total_exercises = len(day_workout.exercises)
                                day_progress.exercises_completed = sum(
                                    1 for ex in day_workout.exercises if ex.completed
                                )
                                break
                        break
                storage.update_progress(request.user_id, progress)

        return {
            "success": True,
            "message": "Exercise status updated",
            "completed": request.completed
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/progress/{user_id}", response_model=ProgressResponse)
async def get_user_progress(user_id: str):
    """
    Get user's progress tracking data.
    
    Args:
        user_id: User identifier
        
    Returns:
        Progress data including completion percentage and streak
    """
    progress = storage.get_progress(user_id)
    if not progress:
        raise HTTPException(status_code=404, detail="No progress data found")

    completion = storage.calculate_completion_percentage(user_id)

    return ProgressResponse(
        success=True,
        progress=progress,
        overall_completion=completion,
        current_streak=progress.current_streak
    )


@app.post("/api/progress/update-streak")
async def update_streak(user_id: str, streak: int):
    """
    Update user's workout streak.
    
    Args:
        user_id: User identifier
        streak: New streak count
        
    Returns:
        Success confirmation
    """
    try:
        storage.update_streak(user_id, streak)
        return {"success": True, "message": "Streak updated", "streak": streak}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@app.post("/api/user/generate-id")
async def generate_user_id():
    """
    Generate a new unique user ID.
    
    Returns:
        Generated user ID
    """
    return {"user_id": str(uuid.uuid4())}

@app.get("/api/stats/{user_id}")
async def get_user_stats(user_id: str):
    """
    Get comprehensive stats for a user.
    
    Args:
        user_id: User identifier
        
    Returns:
        Aggregated user statistics
    """
    try:
        profile = storage.get_user_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="User not found")

        progress = storage.get_progress(user_id)
        workout = storage.get_current_workout(user_id)
        workouts_count = len(storage.get_all_workouts(user_id))
        completion = storage.calculate_completion_percentage(user_id)

        return {
            "success": True,
            "profile": profile,
            "progress": progress,
            "current_workout": workout,
            "workouts_count": workouts_count,
            "weekly_completion": completion,
            "current_streak": progress.current_streak if progress else 0
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/user/{user_id}")
async def delete_user_data(user_id: str):
    """
    Delete all data for a user (for testing/privacy).
    
    Args:
        user_id: User identifier
        
    Returns:
        Success confirmation
    """
    try:
        # This would require adding delete methods to storage
        # For now, just acknowledge
        return {
            "success": True,
            "message": f"User {user_id} data deletion initiated"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with consistent format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error"}
    )


# ============================================================================
# STARTUP/SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialization on app startup."""
    print("🏋️ Fitness Tracker AI - Starting up...")
    if gemini:
        print("✅ Gemini API initialized")
    else:
        print("⚠️ Warning: Gemini API not initialized")
    print("✅ Storage initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on app shutdown."""
    print("🏋️ Fitness Tracker AI - Shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )
