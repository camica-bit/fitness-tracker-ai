# 💪 Fitness Tracker AI - Personalized Workout Generator

An AI-powered fitness application that generates personalized weekly workout routines using Google Gemini API. This hackathon MVP features a clean, modern dark-theme UI with real-time workout tracking and intelligent regeneration based on user feedback.

## ✨ Features

- **AI-Powered Workout Generation**: Uses Google Gemini to create personalized, safety-focused routines
- **Smart Personalization**: Considers age, fitness goal, experience level, equipment, and available time
- **Real-time Tracking**: Mark exercises as complete and track weekly progress
- **Intelligent Regeneration**: 
  - "Too Easy" - Increases intensity with more sets/reps
  - "Too Hard" - Reduces difficulty and provides easier variations
  - "Missed a Day" - Adjusts the plan to accommodate missed workouts
- **Progress Analytics**: 
  - Weekly completion percentage
  - Consecutive workout streak counter
  - Exercise-level tracking
- **Mobile-Friendly**: Fully responsive design works on desktop, tablet, and mobile
- **Export Functionality**: Download your workout plan as CSV
- **Dark Fitness Theme**: Modern, eye-friendly dark UI optimized for gym usage

## 🏗️ Architecture

The application follows a clean, modular architecture:

```
FitnessTracker/
├── main.py              # FastAPI application with all endpoints
├── models.py            # Pydantic models for validation
├── gemini.py            # Google Gemini API integration
├── prompts.py           # Prompt templates and generation logic
├── storage.py           # In-memory storage with JSON persistence
├── templates/
│   └── index.html       # Single-page application
├── static/
│   ├── style.css        # Dark theme stylesheet (mobile-responsive)
│   └── script.js        # Frontend logic and API communication
├── .env.example         # Environment variables template
└── data/                # Generated JSON storage files
    ├── users.json
    ├── workouts.json
    └── progress.json
```

### Design Principles

1. **Separation of Concerns**: Each module has a single, well-defined responsibility
2. **Pydantic Validation**: All inputs validated with type hints and constraints
3. **Error Handling**: Comprehensive error handling with user-friendly messages
4. **API-Driven**: Backend and frontend completely decoupled via REST API
5. **Extensibility**: Easy to add diet plans, recovery protocols, injury handling

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- pip or uv
- Google Gemini API key (free at https://ai.google.dev/)

### Installation

1. **Clone/Navigate to the project**
   ```bash
   cd FitnessTracker
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install fastapi uvicorn google-generativeai pydantic python-dotenv
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

   The app will start at `http://localhost:8000`

## 📖 Usage Guide

### User Flow

1. **Enter Fitness Profile**
   - Age (required)
   - Gender (optional)
   - Height & Weight (optional)
   - Fitness Goal: Fat Loss, Muscle Gain, or General Fitness
   - Experience Level: Beginner, Intermediate, Advanced
   - Available Equipment: Bodyweight, Dumbbells, Full Gym
   - Workout Duration: 15-180 minutes
   - Days Per Week: 3-6 days

2. **AI Generates Workout**
   - Gemini creates a personalized weekly split
   - Shows motivational quote while generating
   - Workout tailored to your exact specifications

3. **Track Your Workout**
   - Click checkboxes to mark exercises complete
   - See real-time progress percentage
   - View consecutive workout streak

4. **Adjust Based on Feedback**
   - Too Easy → Increase intensity
   - Too Hard → Reduce difficulty
   - Missed a Day → Recalibrate the schedule

5. **Export or Start New Plan**
   - Download workout as CSV
   - Generate a fresh plan anytime

## 🧠 Gemini Integration

### How Prompts Work

The application uses two main prompting strategies:

#### Initial Generation
When generating the first workout, Gemini receives:
- User's complete fitness profile
- Fitness goal (fat loss, muscle gain, general fitness)
- Experience level with appropriate safety guidelines
- Equipment constraints
- Time constraints

**Example Prompt** (simplified):
```
Create a personalized 4-day per week workout plan for a beginner user.

USER PROFILE:
- Age: 28
- Fitness Goal: Fat Loss
- Experience Level: Beginner
- Available Equipment: Bodyweight, Dumbbells
- Target Workout Duration: 45 minutes per session
- Days Per Week: 4

REQUIREMENTS:
- Generate 4 complete workout days
- Each workout should take approximately 45 minutes
- Vary muscle groups (upper body, lower body, full body, cardio)
- For Fat Loss: Focus on compound movements with moderate-high reps for calorie burn
- All exercises must use ONLY: Bodyweight, Dumbbells
- Use basic, safe movements with proper form cues

Output the complete JSON workout plan immediately with no other text.
```

#### Regeneration with Feedback
When user provides feedback, Gemini includes:
- The previous workout context
- The specific feedback type
- Instruction to adjust intensity accordingly

**Example Regeneration**:
```
Regenerate a 4-day per week workout plan with the following adjustment:

PREVIOUS WORKOUT CONTEXT:
  Monday (Upper Body):
    - Push-ups: 3x10 (rest 60s)
    - Dumbbell Rows: 3x10 (rest 60s)
  [... more exercises ...]

ADJUSTMENT NEEDED:
TOO DIFFICULT: Reduce sets, use easier exercise variations, increase rest time between sets...

Create a NEW workout plan that addresses the feedback while maintaining appropriate progression and safety.
```

### Gemini Output Format

Gemini is instructed to return **valid JSON only**, no explanations:

```json
{
  "days": [
    {
      "day": "Monday",
      "focus": "Upper Body",
      "exercises": [
        {
          "name": "Dumbbell Bench Press",
          "sets": 3,
          "reps": "8-10",
          "rest_seconds": 90,
          "notes": "Keep elbows at 45 degrees, control the descent"
        }
      ]
    }
  ]
}
```

### Prompt Rules for Gemini

1. **No explanations** - Output JSON only
2. **No emojis** - Clean, professional format
3. **No unnecessary text** - Straight to the plan
4. **Beginner-safe** - Prioritizes form and injury prevention
5. **Equipment-aware** - Only uses available equipment
6. **Time-conscious** - Respects duration and frequency constraints

## 📡 API Endpoints

### User Profile
- `POST /api/profile/create` - Create user profile
- `GET /api/profile/{user_id}` - Get user profile

### Workout Generation
- `POST /api/workout/generate` - Generate new workout plan
- `POST /api/workout/regenerate` - Regenerate with feedback
- `GET /api/workout/{user_id}` - Get current workout
- `GET /api/workout/history/{user_id}` - Get workout history

### Progress Tracking
- `POST /api/progress/update-exercise` - Mark exercise complete/incomplete
- `GET /api/progress/{user_id}` - Get user progress
- `POST /api/progress/update-streak` - Update streak counter

### Utilities
- `POST /api/user/generate-id` - Generate unique user ID
- `GET /api/quotes` - Get random motivational quote
- `GET /api/stats/{user_id}` - Get comprehensive user statistics
- `GET /health` - Health check

## 🗄️ Data Storage

### In-Memory + JSON Persistence

All data is stored in JSON files in the `data/` directory:

**users.json** - User profiles
```json
{
  "user-id-1": {
    "user_id": "user-id-1",
    "age": 28,
    "fitness_goal": "fat_loss",
    "experience_level": "beginner",
    "equipment": ["bodyweight", "dumbbells"],
    "workout_duration_minutes": 45,
    "days_per_week": 4
  }
}
```

**workouts.json** - Generated workout plans
```json
{
  "user-id-1": [
    {
      "user_id": "user-id-1",
      "week": 1,
      "days": [...],
      "total_days_in_week": 4,
      "generated_at": "2024-01-03T10:30:00",
      "context": null
    }
  ]
}
```

**progress.json** - User progress tracking
```json
{
  "user-id-1": {
    "user_id": "user-id-1",
    "week": 1,
    "days": [
      {
        "day": "Day 1",
        "exercises_completed": 3,
        "total_exercises": 5
      }
    ],
    "current_streak": 2
  }
}
```

## 🎨 Frontend Features

### Dark Fitness Theme
- Modern gradient backgrounds
- High-contrast text for readability
- Orange primary color (#ff6b35) for energy
- Blue secondary color (#00d4ff) for accents

### Responsive Design
- Desktop: Full-width layout with multi-column workout cards
- Tablet: 2-column workout layout
- Mobile: Single-column, optimized touch targets

### Interactive Elements
- Real-time progress bar with percentage
- Exercise checkboxes with visual feedback
- Motivational loading spinner
- Smooth section transitions
- Keyboard shortcuts (Alt+N for new plan, ESC to go back)

## 🧪 Testing

### Manual Testing Steps

1. **Test with different profiles**
   ```
   - Beginner, bodyweight only, 20 mins
   - Intermediate, dumbbells, 45 mins
   - Advanced, full gym, 60 mins
   ```

2. **Test feedback buttons**
   - Generate workout → Click "Too Easy" → Verify increased intensity
   - Generate workout → Click "Too Hard" → Verify reduced difficulty
   - Check exercises remain same focus area but adjusted

3. **Test progress tracking**
   - Check exercises, verify completion percentage updates
   - Reload page, verify progress persists (localStorage)

4. **Test mobile responsiveness**
   - Use browser DevTools to simulate different screen sizes
   - Verify all buttons clickable and readable

## 🔐 Security Considerations

- API key stored in environment variables (never in code)
- User IDs are UUIDs for anonymity
- No authentication required (MVP - add for production)
- Input validation with Pydantic
- CORS enabled for frontend-backend communication

## 🛠️ Configuration

### Gemini API Model Selection

Current: `gemini-2.0-flash` (recommended for speed and cost)

To switch models, edit `gemini.py`:
```python
self.model = genai.GenerativeModel(
    model_name="gemini-1.5-pro"  # Change here
)
```

**Model Options:**
- `gemini-2.0-flash` - Fast, low latency, great for MVP
- `gemini-1.5-pro` - More capable, better for complex plans
- `gemini-1.5-flash` - Balance of speed and capability

### Customizing Prompts

Edit `prompts.py` to modify:
- System instructions (trainer persona)
- Prompt templates
- Motivational quotes
- Safety guidelines

## 📈 Future Enhancements

1. **User Authentication**
   - Email/password registration
   - Social login (Google, Apple)
   - Session management

2. **Advanced Features**
   - Meal planning integration with Gemini
   - Workout video demonstrations
   - Rest day recovery protocols
   - Injury prevention guides
   - Real-time form checking (with camera)

3. **Data Analytics**
   - Long-term progress charts
   - Muscle gain/fat loss tracking
   - Workout consistency metrics
   - Personalized recommendations based on history

4. **Social Features**
   - Share workouts with friends
   - Leaderboards
   - Community challenges
   - Social media integration

5. **Mobile App**
   - Native iOS/Android apps
   - Offline mode
   - Push notifications for workout reminders
   - Wearable integration (Apple Watch, Fitbit)

6. **Advanced AI**
   - Computer vision for form correction
   - Voice commands
   - Predictive difficulty scaling
   - Natural language workout adjustments

## 🐛 Troubleshooting

### "GEMINI_API_KEY not found"
- Ensure `.env` file exists with valid API key
- Check API key is not expired at https://ai.google.dev/

### "Failed to parse Gemini response as JSON"
- Gemini may occasionally return extra text
- Check `_parse_gemini_response()` in `gemini.py` - it attempts to extract JSON

### Progress not persisting
- Check that `data/` directory exists and is writable
- Clear localStorage in browser: `localStorage.clear()`

### Slow workout generation
- Using `gemini-2.0-flash` for fastest responses
- Network latency may affect speed
- Gemini API rate limits (free tier: 15 requests/minute)

## 📄 License

This hackathon MVP is provided as-is for educational and demonstration purposes.

## 🙋 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review FastAPI docs: https://fastapi.tiangolo.com/
3. Check Gemini API docs: https://ai.google.dev/

## 🎯 Hackathon Key Points

This MVP demonstrates:

✅ **Clean Architecture** - Modular, well-organized code
✅ **API Design** - RESTful endpoints with proper validation
✅ **AI Integration** - Effective use of Gemini API with smart prompting
✅ **UI/UX** - Professional dark theme, responsive design
✅ **Feature Completeness** - Full workflow from profile to tracking
✅ **Error Handling** - Comprehensive error management
✅ **Documentation** - Clear setup and usage instructions
✅ **MVP-Ready** - Demo-ready with smooth user flow

Perfect for a hackathon presentation demonstrating AI integration with practical fitness applications!

---

Built with ❤️ using FastAPI, Google Gemini, and Vanilla JavaScript
