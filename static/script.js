/**
 * Fitness Tracker AI - Frontend JavaScript
 * Handles form submission, API calls, and UI interactions
 */

// ============================================================================
// STATE MANAGEMENT
// ============================================================================

let currentState = {
    userId: null,
    userProfile: null,
    currentWorkout: null,
    currentProgress: null,
    isLoading: false
};

// DOM Elements
const sections = {
    form: document.getElementById('formSection'),
    loading: document.getElementById('loadingSection'),
    workout: document.getElementById('workoutSection'),
    error: document.getElementById('errorSection')
};

const forms = {
    user: document.getElementById('userForm')
};

const buttons = {
    generateWorkout: forms.user.querySelector('button[type="submit"]'),
    tooEasy: document.getElementById('tooEasyBtn'),
    tooHard: document.getElementById('tooHardBtn'),
    missedDay: document.getElementById('missedDayBtn'),
    newPlan: document.getElementById('newPlanBtn'),
    export: document.getElementById('exportBtn'),
    back: document.getElementById('backBtn')
};

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

function initializeApp() {
    // Attach event listeners
    forms.user.addEventListener('submit', handleFormSubmit);
    buttons.tooEasy.addEventListener('click', () => handleFeedback('too_easy'));
    buttons.tooHard.addEventListener('click', () => handleFeedback('too_hard'));
    buttons.missedDay.addEventListener('click', () => handleFeedback('missed_day'));
    buttons.newPlan.addEventListener('click', () => resetToForm());
    buttons.export.addEventListener('click', handleExport);
    buttons.back.addEventListener('click', resetToForm);

    // Load user ID from localStorage if exists
    const savedUserId = localStorage.getItem('fitnessTrackerUserId');
    if (savedUserId) {
        currentState.userId = savedUserId;
        loadUserWorkout();
    } else {
        generateUserId();
    }

    showSection('form');
}

// ============================================================================
// USER ID MANAGEMENT
// ============================================================================

async function generateUserId() {
    try {
        const response = await fetch('/api/user/generate-id', { method: 'POST' });
        const data = await response.json();
        currentState.userId = data.user_id;
        localStorage.setItem('fitnessTrackerUserId', currentState.userId);
    } catch (error) {
        console.error('Error generating user ID:', error);
        showError('Failed to initialize user ID');
    }
}

// ============================================================================
// FORM HANDLING
// ============================================================================

async function handleFormSubmit(e) {
    e.preventDefault();

    // Validate form
    if (!validateForm()) {
        return;
    }

    // Collect form data
    const userProfile = collectFormData();

    // Show loading state
    showLoading();

    try {
        // Generate workout
        const response = await fetch('/api/workout/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_profile: userProfile,
                feedback: null,
                previous_workout: null
            })
        });

        if (!response.ok) {
            let errorText = `HTTP ${response.status}`;
            const bodyText = await response.text();
            let errorData = null;
            try {
                errorData = JSON.parse(bodyText);
            } catch (e) {
                throw new Error(`${errorText}: ${bodyText}`);
            }

            if (errorData) {
                if (errorData.detail) {
                    if (Array.isArray(errorData.detail) && errorData.detail.length > 0) {
                        const first = errorData.detail[0];
                        errorText += `: ${first.msg || JSON.stringify(first)}`;
                    } else if (typeof errorData.detail === 'string') {
                        errorText += `: ${errorData.detail}`;
                    } else {
                        errorText += `: ${JSON.stringify(errorData.detail)}`;
                    }
                } else if (errorData.message) {
                    errorText += `: ${errorData.message}`;
                } else {
                    errorText += `: ${JSON.stringify(errorData)}`;
                }
            }

            throw new Error(errorText);
        }

        const result = await response.json();

        if (result.success && result.workout) {
            currentState.userProfile = userProfile;
            currentState.currentWorkout = result.workout;
            await loadUserProgress();
            showWorkout();
        } else {
            throw new Error('Invalid response from server');
        }
    } catch (error) {
        console.error('Error generating workout:', error);
        showError(`Error: ${error.message}`);
    }
}

function validateForm() {
    const age = document.getElementById('age').value;
    const goal = document.getElementById('goal').value;
    const experience = document.getElementById('experience').value;
    const duration = document.getElementById('duration').value;
    const daysPerWeek = document.getElementById('daysPerWeek').value;
    const equipment = Array.from(document.querySelectorAll('input[name="equipment"]:checked'));

    if (!age || !goal || !experience || !duration || !daysPerWeek) {
        alert('Please fill in all required fields');
        return false;
    }

    if (equipment.length === 0) {
        alert('Please select at least one equipment type');
        return false;
    }

    return true;
}

function collectFormData() {
    const age = parseInt(document.getElementById('age').value);
    const gender = document.getElementById('gender').value || null;
    const height = document.getElementById('height').value ? parseInt(document.getElementById('height').value) : null;
    const weight = document.getElementById('weight').value ? parseFloat(document.getElementById('weight').value) : null;
    const fitnessGoal = document.getElementById('goal').value;
    const experienceLevel = document.getElementById('experience').value;
    const equipment = Array.from(document.querySelectorAll('input[name="equipment"]:checked')).map(e => e.value);
    const workoutDuration = parseInt(document.getElementById('duration').value);
    const daysPerWeek = parseInt(document.getElementById('daysPerWeek').value);

    return {
        user_id: currentState.userId,
        age,
        gender: gender || undefined,
        height_cm: height,
        weight_kg: weight,
        fitness_goal: fitnessGoal,
        experience_level: experienceLevel,
        equipment,
        workout_duration_minutes: workoutDuration,
        available_days_per_week: daysPerWeek
    };
}

// ============================================================================
// LOADING STATE
// ============================================================================

async function showLoading() {
    showSection('loading');
    currentState.isLoading = true;

    try {
        const response = await fetch('/api/quotes');
        const data = await response.json();
        document.getElementById('motivationalQuote').textContent = `"${data.quote}"`;
    } catch (error) {
        console.error('Error fetching quote:', error);
        document.getElementById('motivationalQuote').textContent = '"Keep pushing, you got this!"';
    }
}

// ============================================================================
// WORKOUT DISPLAY
// ============================================================================

function showWorkout() {
    showSection('workout');
    renderWorkout();
    attachExerciseListeners();
}

function renderWorkout() {
    const workoutPlanEl = document.getElementById('workoutPlan');
    workoutPlanEl.innerHTML = '';

    if (!currentState.currentWorkout || !currentState.currentWorkout.days) {
        workoutPlanEl.innerHTML = '<p>No workout data available</p>';
        return;
    }

    currentState.currentWorkout.days.forEach((day, dayIndex) => {
        const dayEl = createDayWorkoutElement(day, dayIndex);
        workoutPlanEl.appendChild(dayEl);
    });

    updateProgress();
}

function createDayWorkoutElement(day, dayIndex) {
    const template = document.getElementById('dayWorkoutTemplate');
    const clone = template.content.cloneNode(true);

    clone.querySelector('.day-name').textContent = day.day;
    clone.querySelector('.day-focus').textContent = day.focus;

    const exercisesContainer = clone.querySelector('.exercises-list');
    const exercisesCount = day.exercises.length;
    const completedCount = day.exercises.filter(e => e.completed).length;
    clone.querySelector('.day-progress-text').textContent = `${completedCount}/${exercisesCount} exercises`;

    day.exercises.forEach((exercise, exerciseIndex) => {
        const exerciseEl = createExerciseElement(exercise, dayIndex, exerciseIndex);
        exercisesContainer.appendChild(exerciseEl);
    });

    return clone;
}

function createExerciseElement(exercise, dayIndex, exerciseIndex) {
    const template = document.getElementById('exerciseTemplate');
    const clone = template.content.cloneNode(true);

    const exerciseItem = clone.querySelector('.exercise-item');
    const checkbox = clone.querySelector('.exercise-check');
    const nameEl = clone.querySelector('.exercise-name');
    const specsEl = clone.querySelector('.specs');
    const restEl = clone.querySelector('.rest');
    const notesEl = clone.querySelector('.exercise-notes');

    nameEl.textContent = exercise.name;
    specsEl.textContent = `${exercise.sets}x${exercise.reps}`;
    restEl.textContent = `${exercise.rest_seconds}s rest`;
    checkbox.checked = exercise.completed;

    if (exercise.completed) {
        exerciseItem.classList.add('completed');
    }

    if (exercise.notes) {
        notesEl.textContent = exercise.notes;
    } else {
        notesEl.remove();
    }

    checkbox.dataset.dayIndex = dayIndex;
    checkbox.dataset.exerciseIndex = exerciseIndex;

    return clone;
}

function attachExerciseListeners() {
    document.querySelectorAll('.exercise-check').forEach(checkbox => {
        checkbox.addEventListener('change', handleExerciseToggle);
    });
}

async function handleExerciseToggle(e) {
    const dayIndex = parseInt(e.target.dataset.dayIndex);
    const exerciseIndex = parseInt(e.target.dataset.exerciseIndex);
    const completed = e.target.checked;

    const day = currentState.currentWorkout.days[dayIndex];

    try {
        const response = await fetch('/api/progress/update-exercise', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: currentState.userId,
                day: day.day,
                exercise_index: exerciseIndex,
                completed: completed
            })
        });

        if (response.ok) {
            day.exercises[exerciseIndex].completed = completed;
            updateProgress();
        }
    } catch (error) {
        console.error('Error updating exercise:', error);
        e.target.checked = !completed; // Revert on error
    }
}

// ============================================================================
// PROGRESS TRACKING
// ============================================================================

async function loadUserProgress() {
    try {
        const response = await fetch(`/api/progress/${currentState.userId}`);
        if (response.ok) {
            const data = await response.json();
            currentState.currentProgress = data.progress;
        }
    } catch (error) {
        console.error('Error loading progress:', error);
    }
}

function updateProgress() {
    if (!currentState.currentWorkout) return;

    // Calculate completion percentage
    let totalExercises = 0;
    let completedExercises = 0;

    currentState.currentWorkout.days.forEach(day => {
        totalExercises += day.exercises.length;
        completedExercises += day.exercises.filter(e => e.completed).length;
    });

    const completion = totalExercises > 0 ? (completedExercises / totalExercises) * 100 : 0;
    document.getElementById('completionPercentage').textContent = Math.round(completion) + '%';

    const progressFill = document.getElementById('progressFill');
    progressFill.style.width = completion + '%';

    // Update day progress text in UI
    document.querySelectorAll('.day-progress-text').forEach((el, index) => {
        const day = currentState.currentWorkout.days[index];
        const completed = day.exercises.filter(e => e.completed).length;
        el.textContent = `${completed}/${day.exercises.length} exercises`;
    });

    // Update streak (simple logic: increment if any exercise done today)
    if (completedExercises > 0) {
        const streak = (currentState.currentProgress?.current_streak || 0) + 1;
        document.getElementById('streakCount').textContent = streak;
    }
}

async function loadUserWorkout() {
    try {
        const response = await fetch(`/api/workout/${currentState.userId}`);
        if (response.ok) {
            const data = await response.json();
            currentState.currentWorkout = data.workout;
            await loadUserProgress();
            showWorkout();
        }
    } catch (error) {
        console.error('Error loading workout:', error);
        showSection('form');
    }
}

// ============================================================================
// FEEDBACK & REGENERATION
// ============================================================================

async function handleFeedback(feedbackType) {
    if (!currentState.currentWorkout) {
        showError('No active workout to regenerate');
        return;
    }

    showLoading();

    try {
        const response = await fetch('/api/workout/regenerate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: currentState.userId,
                feedback_type: feedbackType,
                current_workout: currentState.currentWorkout
            })
        });

        if (!response.ok) {
            let errorText = `HTTP ${response.status}`;
            const bodyText = await response.text();
            let errorData = null;
            try {
                errorData = JSON.parse(bodyText);
            } catch (e) {
                throw new Error(`${errorText}: ${bodyText}`);
            }

            if (errorData) {
                if (errorData.detail) {
                    if (Array.isArray(errorData.detail) && errorData.detail.length > 0) {
                        const first = errorData.detail[0];
                        errorText += `: ${first.msg || JSON.stringify(first)}`;
                    } else if (typeof errorData.detail === 'string') {
                        errorText += `: ${errorData.detail}`;
                    } else {
                        errorText += `: ${JSON.stringify(errorData.detail)}`;
                    }
                } else if (errorData.message) {
                    errorText += `: ${errorData.message}`;
                } else {
                    errorText += `: ${JSON.stringify(errorData)}`;
                }
            }

            throw new Error(errorText);
        }

        const result = await response.json();

        if (result.success && result.workout) {
            currentState.currentWorkout = result.workout;
            await loadUserProgress();
            showWorkout();
        } else {
            throw new Error('Invalid response');
        }
    } catch (error) {
        console.error('Error regenerating workout:', error);
        showError(`Error: ${error.message}`);
    }
}

// ============================================================================
// EXPORT FUNCTIONALITY
// ============================================================================

function handleExport() {
    if (!currentState.currentWorkout) {
        alert('No workout to export');
        return;
    }

    const workout = currentState.currentWorkout;
    let csvContent = 'Day,Focus,Exercise,Sets,Reps,Rest (sec),Notes,Completed\n';

    workout.days.forEach(day => {
        day.exercises.forEach((exercise, index) => {
            const row = [
                day.day,
                day.focus,
                exercise.name,
                exercise.sets,
                exercise.reps,
                exercise.rest_seconds,
                exercise.notes || '',
                exercise.completed ? 'Yes' : 'No'
            ].map(field => `"${field}"`).join(',');

            csvContent += row + '\n';
        });
    });

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `workout-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

// ============================================================================
// SECTION NAVIGATION
// ============================================================================

function showSection(sectionName) {
    Object.values(sections).forEach(section => {
        section.classList.remove('active');
    });

    if (sections[sectionName]) {
        sections[sectionName].classList.add('active');
    }

    window.scrollTo(0, 0);
}

function resetToForm() {
    forms.user.reset();
    currentState.currentWorkout = null;
    currentState.userProfile = null;
    showSection('form');
}

function showError(message) {
    document.getElementById('errorMessage').textContent = message;
    showSection('error');
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function formatDate(isoString) {
    const date = new Date(isoString);
    return date.toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// ============================================================================
// KEYBOARD SHORTCUTS
// ============================================================================

document.addEventListener('keydown', (e) => {
    // Alt+N: Generate new plan
    if (e.altKey && e.key === 'n') {
        if (currentState.currentWorkout) {
            buttons.newPlan.click();
        }
    }

    // Escape: Go back
    if (e.key === 'Escape' && currentState.currentWorkout) {
        resetToForm();
    }
});

// ============================================================================
// PERSISTENCE
// ============================================================================

window.addEventListener('beforeunload', () => {
    if (currentState.currentWorkout) {
        localStorage.setItem('lastWorkout', JSON.stringify(currentState.currentWorkout));
    }
});
