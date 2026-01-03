# Fitness Tracker AI - Technical Architecture Document

## Project Overview

Fitness Tracker AI is a hackathon MVP that generates personalized, AI-powered workout routines using Google Gemini API. The application features a clean separation between backend (Python/FastAPI) and frontend (HTML/CSS/JavaScript), with intelligent regeneration based on user feedback.

## System Architecture

```
┌────────────────────────────────────────────────────────────┐
│                     Browser (Frontend)                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  HTML Templates (Single Page Application)            │  │
│  │  - User Input Form                                   │  │
│  │  - Workout Display with Progress Tracking            │  │
│  │  - Feedback Controls                                 │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  CSS Styling (Dark Fitness Theme)                    │  │
│  │  - Responsive Design (Mobile/Tablet/Desktop)         │  │
│  │  - Modern Gradients & Animations                     │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  JavaScript (Vanilla - No Frameworks)                │  │
│  │  - Form Handling & Validation                        │  │
│  │  - API Communication                                 │  │
│  │  - UI State Management                               │  │
│  │  - Progress Tracking & Updates                       │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────┬───────────────────────────────────────────┘
                 │ HTTP REST API (JSON)
                 ▼
┌───────────────────────────────────────────────────────────┐
│                   FastAPI Backend                         │
├───────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  API Layer (main.py)                                │  │
│  │  ├─ User Profile Endpoints                          │  │
│  │  ├─ Workout Generation Endpoints                    │  │
│  │  ├─ Progress Tracking Endpoints                     │  │
│  │  ├─ Utility Endpoints (quotes, stats)               │  │
│  │  └─ Error Handling & CORS                           │  │
│  └─────────────────────────────────────────────────────┘  │
│                      ▲                                    │
│                      │                                    │
│  ┌───────────────────┼───────────────────┐                │
│  │                   │                   │                │
│  ▼                   ▼                   ▼                │
│ ┌──────────┐  ┌────────────┐  ┌──────────────────────┐    │
│ │ Models   │  │  Storage   │  │  Gemini Integration  │    │
│ │          │  │            │  │                      │    │
│ │Pydantic  │  │In-memory   │  │ API Communication    │    │
│ │models    │  │JSON Persist│  │ JSON Parsing         │    │
│ │with      │  │users.json  │  │ Error Handling       │    │
│ │validation│  │workouts    │  │                      │    │
│ │          │  │progress    │  │                      │    │
│ └──────────┘  └────────────┘  └──────────────────────┘    │
│                                         │                 │
│                                         ▼                 │
│                                 ┌──────────────────┐      │
│                                 │ Prompts Module   │      │
│                                 │                  │      │
│                                 │ System Prompt    │      │
│                                 │ Generation Prompt│      │
│                                 │ Regeneration     │      │
│                                 │ Quotes           │      │
│                                 └──────────────────┘      │
│                                                           │
└───────────────────────────┬───────────────────────────────┘
                            │ HTTP REST (Google API Client)
                            ▼
                    ┌──────────────────┐
                    │ Google Gemini    │
                    │ API              │
                    │                  │
                    │ Generates        │
                    │ Workouts in JSON │
                    └──────────────────┘
```

## Module Responsibilities

### `models.py` - Data Models (Pydantic)

**Purpose**: Define all data structures with validation

**Classes**:
- `Enums`: `FitnessGoal`, `ExperienceLevel`, `EquipmentType`, `Gender`
- `Exercise`: Single exercise with sets, reps, rest time, notes
- `DayWorkout`: Workout for one day with multiple exercises
- `WorkoutPlan`: Complete weekly workout (7 days × 7 workouts = varies)
- `UserProfile`: User's fitness details and preferences
- `UserProgress`: Tracks completion and streak
- `Request Models`: `GenerateWorkoutRequest`, `UpdateExerciseRequest`, `RegenerateWorkoutRequest`
- `Response Models`: `WorkoutResponse`, `ProgressResponse`

**Key Features**:
- Type hints for all fields
- Field validation (age: 13-120, duration: 15-180 min, etc.)
- Optional fields for flexible user profiles
- Clear field descriptions for API documentation

### `storage.py` - Data Persistence

**Purpose**: Handle in-memory + JSON file storage

**Class**: `StorageManager`

**Data Structures**:
```python
self.users: Dict[str, UserProfile]           # user_id -> UserProfile
self.workouts: Dict[str, List[WorkoutPlan]]  # user_id -> [WorkoutPlan]
self.progress: Dict[str, UserProgress]       # user_id -> UserProgress
```

**Methods**:
- **User Profile**: `save_user_profile()`, `get_user_profile()`, `user_exists()`
- **Workouts**: `save_workout()`, `get_current_workout()`, `get_all_workouts()`
- **Progress**: `initialize_progress()`, `get_progress()`, `update_progress()`, `update_exercise_completion()`
- **Persistence**: `_load_from_disk()`, `_save_to_disk()`
- **Analytics**: `calculate_completion_percentage()`, `update_streak()`

**Files** (in `data/` directory):
- `users.json`: User profiles indexed by user_id
- `workouts.json`: Workout plans indexed by user_id
- `progress.json`: Progress tracking indexed by user_id

### `prompts.py` - Prompt Engineering

**Purpose**: Generate optimized prompts for Gemini

**Functions**:
- `get_system_prompt()`: Returns system instruction for Gemini to act as personal trainer
- `build_initial_workout_prompt()`: Initial workout generation prompt
- `build_regeneration_prompt()`: Feedback-based regeneration prompt
- `build_motivational_quotes()`: List of motivational quotes for UI

**Key Features**:
- **System Prompt**: Defines Gemini's role and output format (JSON only, no explanations)
- **Dynamic Prompting**: Incorporates user profile details
- **Context Awareness**: Includes previous workout for regeneration
- **Safety Guidelines**: Emphasizes beginner-safe, form-correct exercises

**Prompt Strategy**:
1. Provides detailed user profile
2. States all constraints (equipment, time, experience)
3. Specifies JSON output format
4. Gives goal-specific guidance (fat loss, muscle gain, etc.)
5. Emphasizes safety and progression

### `gemini.py` - Gemini API Integration

**Purpose**: Communicate with Google Gemini API

**Class**: `GeminiWorkoutGenerator`

**Key Methods**:
- `__init__()`: Initialize Gemini client with API key
- `generate_workout()`: Main method to generate/regenerate workouts
- `_parse_gemini_response()`: Extract JSON from Gemini response
- `_build_day_workouts()`: Convert parsed JSON to DayWorkout objects
- `validate_api_key()`: Check API key validity

**Error Handling**:
- `GeminiError`: Custom exception for Gemini-specific errors
- Validates API key existence
- Handles JSON parsing errors
- Graceful error messages

**Model Configuration**:
- Uses `gemini-2.0-flash` by default (fast, low latency)
- Customizable model selection
- System prompt included for consistent behavior

### `main.py` - FastAPI Application

**Purpose**: REST API endpoints and request handling

**Route Groups**:

1. **Static Content** (`/`)
   - `GET /`: Serve index.html
   - `GET /health`: Health check

2. **Motivational** (`/api/quotes`)
   - `GET /api/quotes`: Random fitness quote

3. **User Profiles** (`/api/profile`)
   - `POST /api/profile/create`: Create new user
   - `GET /api/profile/{user_id}`: Get user profile

4. **Workout Generation** (`/api/workout`)
   - `POST /api/workout/generate`: Generate new workout
   - `POST /api/workout/regenerate`: Regenerate with feedback
   - `GET /api/workout/{user_id}`: Get current workout
   - `GET /api/workout/history/{user_id}`: Get all workouts

5. **Progress Tracking** (`/api/progress`)
   - `POST /api/progress/update-exercise`: Mark exercise complete
   - `GET /api/progress/{user_id}`: Get progress data
   - `POST /api/progress/update-streak`: Update streak

6. **Utilities** (`/api/user`, `/api/stats`)
   - `POST /api/user/generate-id`: Create UUID
   - `GET /api/stats/{user_id}`: Aggregated stats
   - `DELETE /api/user/{user_id}`: Delete user data

**Middleware**:
- CORS enabled for cross-origin requests
- Static file serving (CSS, JS)

**Error Handling**:
- Custom exception handlers
- Consistent error response format
- User-friendly error messages

### `templates/index.html` - Single Page Application

**Structure**:
```html
<header>      - Logo and tagline
<main>
  - #formSection      - User input form
  - #loadingSection   - Loading spinner + quote
  - #workoutSection   - Workout display + tracking
  - #errorSection     - Error messages
<footer>      - Credits
```

**Sections**:
1. **Form Section**: Input form with fieldsets
   - Basic info (age, gender, height, weight)
   - Goals & experience (fitness goal, experience level)
   - Equipment & schedule (equipment checkboxes, duration, days/week)

2. **Loading Section**:
   - Animated spinner
   - Motivational quote from API

3. **Workout Section**:
   - Progress bar and stats
   - Day cards with exercises
   - Exercise checkboxes
   - Feedback buttons
   - Export & regeneration actions

4. **Error Section**:
   - Error message display
   - Back button

**Templates** (for dynamic content):
- `#dayWorkoutTemplate`: Day workout card template
- `#exerciseTemplate`: Exercise item template

### `static/style.css` - Dark Fitness Theme

**Design System**:
```
Colors:
- Primary: #ff6b35 (Orange - energy)
- Primary Dark: #e55a24
- Secondary: #00d4ff (Cyan - modern)
- Accent: #ffd43b (Yellow - highlights)
- BG Dark: #0a0e27 (Main background)
- BG Darker: #050812 (Darker background)
- BG Card: #1a1f3a (Card background)

Spacing:
- xs: 4px, sm: 8px, md: 16px, lg: 24px, xl: 32px, xxl: 48px

Typography:
- Font Family: System fonts (-apple-system, Segoe UI, etc.)
- Sizes: sm, base, lg, xl, 2xl

Transitions:
- Fast: 150ms, Standard: 300ms, Slow: 500ms
```

**Components**:
- **Form**: Fieldsets, inputs, checkboxes, buttons
- **Buttons**: Primary, secondary, outline variations
- **Progress Bar**: Gradient fill animation
- **Workout Cards**: Hover effects, day headers, exercise lists
- **Loading Spinner**: CSS animation
- **Responsive Grid**: CSS Grid for layout

**Responsive Breakpoints**:
- Desktop: Full layout
- Tablet (768px): 2-column grid
- Mobile (480px): 1-column, optimized touch targets

### `static/script.js` - Frontend Logic

**State Management**:
```javascript
currentState = {
    userId: string,
    userProfile: UserProfile,
    currentWorkout: WorkoutPlan,
    currentProgress: UserProgress,
    isLoading: boolean
}
```

**Major Functions**:

1. **Initialization**
   - `initializeApp()`: Set up event listeners
   - `generateUserId()`: Create or restore user ID
   - `loadUserWorkout()`: Restore previous session

2. **Form Handling**
   - `handleFormSubmit()`: Process form submission
   - `validateForm()`: Validate required fields
   - `collectFormData()`: Extract form values

3. **API Communication**
   - `fetch()` calls to `/api/` endpoints
   - Error handling with try-catch
   - Response parsing and validation

4. **Workout Display**
   - `renderWorkout()`: Display workout plan
   - `createDayWorkoutElement()`: Build day cards
   - `createExerciseElement()`: Build exercise items
   - `attachExerciseListeners()`: Add event handlers

5. **Progress Tracking**
   - `handleExerciseToggle()`: Mark exercise complete
   - `updateProgress()`: Update UI progress bars
   - `loadUserProgress()`: Fetch progress data

6. **Feedback & Regeneration**
   - `handleFeedback()`: Send feedback to API
   - `handleExport()`: Download workout as CSV

7. **Navigation**
   - `showSection()`: Switch between sections
   - `resetToForm()`: Return to form
   - `showError()`: Display errors

## Data Flow

### Workflow: User Creates Workout

```
1. User fills form
           ↓
2. Frontend validates form data
           ↓
3. API POST /api/workout/generate
           ↓
4. Backend creates UserProfile
           ↓
5. Backend calls Gemini with prompt
           ↓
6. Gemini returns JSON workout
           ↓
7. Backend parses JSON → WorkoutPlan object
           ↓
8. Backend saves to storage (JSON files)
           ↓
9. Backend returns WorkoutPlan response
           ↓
10. Frontend renders workout display
           ↓
11. User can track and provide feedback
```

### Workflow: User Provides Feedback

```
1. User clicks "Too Easy"
           ↓
2. Frontend POST /api/workout/regenerate
   - current_workout (previous plan)
   - feedback_type ("too_easy")
           ↓
3. Backend retrieves UserProfile
           ↓
4. Backend calls Gemini with:
   - Previous workout context
   - Feedback instruction (increase difficulty)
           ↓
5. Gemini returns modified JSON
           ↓
6. Backend parses and saves
           ↓
7. Frontend displays new workout
           ↓
8. Exercise progress resets (new plan)
```

## API Request/Response Examples

### Generate Workout Request
```json
{
  "user_profile": {
    "user_id": "abc-123",
    "age": 28,
    "gender": "male",
    "height_cm": 180,
    "weight_kg": 85,
    "fitness_goal": "muscle_gain",
    "experience_level": "intermediate",
    "equipment": ["dumbbells", "gym"],
    "workout_duration_minutes": 60,
    "days_per_week": 4
  },
  "feedback": null,
  "previous_workout": null
}
```

### Generate Workout Response
```json
{
  "success": true,
  "workout": {
    "user_id": "abc-123",
    "week": 1,
    "days": [
      {
        "day": "Monday",
        "focus": "Chest & Triceps",
        "exercises": [
          {
            "name": "Barbell Bench Press",
            "sets": 4,
            "reps": "6-8",
            "rest_seconds": 120,
            "notes": "Keep chest up, lower to mid-chest",
            "completed": false
          }
        ]
      }
    ],
    "total_days_in_week": 4,
    "generated_at": "2024-01-03T10:30:00",
    "context": null
  },
  "message": "Workout generated successfully"
}
```

## Security Considerations

1. **API Keys**: 
   - Stored in `.env` (never committed)
   - Loaded via environment variables
   - Not exposed in responses

2. **User Data**:
   - No authentication in MVP (add for production)
   - User IDs are UUIDs for anonymity
   - Local JSON storage (not cloud)

3. **Input Validation**:
   - All inputs validated by Pydantic
   - Type checking and constraints
   - Range validation (age, duration, etc.)

4. **CORS**:
   - Enabled for development
   - Restrict to specific origins in production

5. **Error Handling**:
   - Never expose stack traces to users
   - Generic error messages
   - Log errors server-side

## Performance Considerations

1. **Gemini API Latency**:
   - Using `gemini-2.0-flash` for speed
   - Typical response: 2-5 seconds
   - Longer for complex requests

2. **Storage**:
   - In-memory hash maps (O(1) lookup)
   - JSON persistence (async save)
   - No database overhead

3. **Frontend**:
   - Vanilla JavaScript (no framework overhead)
   - Minimal CSS animations
   - Local storage for user ID

## Extensibility

### Adding New Features

1. **New User Profile Field**
   - Add to `UserProfile` model
   - Update form in HTML
   - Update Gemini prompt

2. **New Feedback Type**
   - Add to feedback buttons in HTML
   - Create prompt in `prompts.py`
   - Handle in `handleFeedback()` in JS

3. **New API Endpoint**
   - Define route in `main.py`
   - Use existing models or create new ones
   - Update frontend to call new endpoint

4. **New Report/Analytics**
   - Query `storage` for data
   - Calculate metrics
   - Return in new API endpoint

## Testing Strategy

1. **Manual Testing**:
   - Test form validation
   - Test all feedback types
   - Test on different devices
   - Test error scenarios

2. **API Testing**:
   - Use curl or Postman
   - Test all endpoints
   - Verify response formats

3. **Gemini Testing**:
   - Verify JSON output parsing
   - Test with different profiles
   - Check safety guidelines

## Deployment Considerations

1. **Environment Variables**:
   - `GEMINI_API_KEY` required
   - Optional: `FLASK_ENV`, `LOG_LEVEL`

2. **Dependencies**:
   - Python 3.9+ required
   - All packages in `requirements.txt`

3. **Data Storage**:
   - Ensure `data/` directory writable
   - Consider cloud storage for production

4. **Scaling**:
   - Move to database (PostgreSQL, MongoDB)
   - Add user authentication
   - Implement caching layer
   - Use message queue for async jobs

## Conclusion

The Fitness Tracker AI demonstrates a clean, well-architected web application with:
- Clear separation of concerns
- Effective AI integration
- Professional UI/UX
- Production-ready error handling
- Extensible design

Perfect for a hackathon MVP and ready to scale!
