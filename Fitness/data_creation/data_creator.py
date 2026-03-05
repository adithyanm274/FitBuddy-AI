import pandas as pd
import random

# Exercise database with difficulty levels (1-5 scale)
exercises_db = {
    "push": {
        "beginner": ["pushups", "bench press (machine)", "shoulder press (machine)"],
        "intermediate": ["bench press (barbell)", "dumbbell press", "dips"],
        "advanced": ["incline bench press", "overhead press", "weighted dips"]
    },
    "pull": {
        "beginner": ["lat pulldown", "seated row", "face pulls"],
        "intermediate": ["pullups (assisted)", "barbell rows", "chin-ups"],
        "advanced": ["weighted pullups", "deadlifts", "muscle-ups"]
    },
    "legs": {
        "beginner": ["bodyweight squats", "leg press", "step-ups"],
        "intermediate": ["barbell squats", "lunges", "leg curls"],
        "advanced": ["front squats", "deadlifts", "bulgarian split squats"]
    },
    "cardio": {
        "beginner": ["walking", "light cycling", "elliptical"],
        "intermediate": ["jogging", "cycling", "swimming"],
        "advanced": ["sprints", "HIIT", "stair climbing"]
    }
}

goals = ["Weight Loss", "Muscle Gain", "Maintain Fitness"]
genders = ["Male", "Female"]
bmi_categories = ["Underweight", "Normal", "Overweight", "Obese"]
difficulty_levels = ["beginner", "intermediate", "advanced"]

def determine_difficulty(profile):
    """Determine workout difficulty based on user profile"""
    age, gender, goal_idx, bmi_idx = profile
    goal = goals[goal_idx]
    bmi = bmi_categories[bmi_idx]
    
    if age < 25 and bmi_idx <= 1 and goal == "Muscle Gain":
        return "advanced"
    elif age > 50 or bmi_idx >= 2:
        return "beginner"
    else:
        return "intermediate"

def get_next_workout_type(current_type):
    """Get next workout type ensuring proper rotation"""
    types = ["push", "pull", "legs", "cardio"]
    if current_type is None:
        return random.choice(types)
    
    # Ensure we don't repeat the same type consecutively
    remaining_types = [t for t in types if t != current_type]
    return random.choice(remaining_types)

def select_exercises(workout_type, difficulty, goal):
    """Select exercises based on workout type and difficulty"""
    available_exercises = exercises_db[workout_type][difficulty]
    
    if workout_type == "cardio":
        exercises = [random.choice(available_exercises), "", ""]  # Only one cardio exercise
    else:
        # Select 3 different exercises for the workout type
        selected = random.sample(available_exercises, min(3, len(available_exercises)))
        exercises = selected + [""] * (3 - len(selected))  # Fill empty slots if needed
    
    # Format: (name, type, sets, reps, duration, difficulty)
    formatted = []
    for ex in exercises:
        if not ex:  # Empty slot
            formatted.append(("", "", 0, 0, 0, 0))
        elif workout_type == "cardio":
            duration = random.randint(15, 45) if difficulty == "beginner" else (
                random.randint(20, 60) if difficulty == "intermediate" else random.randint(30, 90))
            formatted.append((ex, "cardio", 0, 0, duration, difficulty_levels.index(difficulty)+1))
        else:
            sets = 3 if goal == "Weight Loss" else (4 if difficulty == "intermediate" else 5)
            reps = 12 if goal == "Weight Loss" else (8 if difficulty == "intermediate" else 6)
            formatted.append((ex, workout_type, sets, reps, 0, difficulty_levels.index(difficulty)+1))
    
    return formatted

def generate_workout_sequence(profile, length=7):
    """Generate workout sequence without rest days"""
    goal = goals[profile[2]]
    difficulty = determine_difficulty(profile)
    sequence = []
    current_type = None
    
    for _ in range(length):
        current_type = get_next_workout_type(current_type)
        sequence.append((current_type, select_exercises(current_type, difficulty, goal)))
    
    return sequence

def generate_fitness_data(num_samples=2000):
    """Generate sequential training data without rest days"""
    data = []
    
    for _ in range(num_samples):
        # Profile
        profile = [
            random.randint(18, 70),
            genders.index(random.choice(genders)),
            goals.index(random.choice(goals)),
            bmi_categories.index(random.choice(bmi_categories))
        ]
        
        # Generate workout sequence
        sequence = generate_workout_sequence(profile)
        
        # Create sequences (day1+day2 → day3)
        for i in range(len(sequence)-2):
            day1_type, day1_exercises = sequence[i]
            day2_type, day2_exercises = sequence[i+1]
            day3_type, day3_exercises = sequence[i+2]
            
            # Flatten exercises
            input_day1 = [day1_type] + [item for ex in day1_exercises for item in ex]
            input_day2 = [day2_type] + [item for ex in day2_exercises for item in ex]
            target_day = [day3_type] + [item for ex in day3_exercises for item in ex]
            
            data.append(profile + input_day1 + input_day2 + target_day)
    
    # Column names
    columns = ['age', 'gender', 'goal', 'bmi']
    
    # Input day columns
    for day in [1, 2]:
        columns.append(f'day{day}_workout_type')
        for ex in [1, 2, 3]:
            prefix = f'day{day}_exercise{ex}_'
            columns.extend([f'{prefix}name', f'{prefix}category', 
                          f'{prefix}sets', f'{prefix}reps', 
                          f'{prefix}duration', f'{prefix}difficulty'])
    
    # Target day columns
    columns.append('target_day_workout_type')
    for ex in [1, 2, 3]:
        prefix = f'target_exercise{ex}_'
        columns.extend([f'{prefix}name', f'{prefix}category',
                       f'{prefix}sets', f'{prefix}reps',
                       f'{prefix}duration', f'{prefix}difficulty'])
    
    return pd.DataFrame(data, columns=columns)

# Generate and save data
df = generate_fitness_data(2000)
df.to_csv('Fitness/data_creation/workout_data_no_rest.csv', index=False)
print("Generated workout_data_no_rest.csv")