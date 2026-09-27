import random
from pathlib import Path
import pandas as pd

exercise_db = {
    "push": {
        "beginner":     ["pushups", "bench press (machine)", "shoulder press (machine)"],
        "intermediate": ["bench press (barbell)", "dumbbell press", "dips"],
        "advanced":     ["incline bench press", "overhead press", "weighted dips"],
    },
    "pull": {
        "beginner":     ["lat pulldown", "seated row", "face pulls"],
        "intermediate": ["pullups (assisted)", "barbell rows", "chin-ups"],
        "advanced":     ["weighted pullups", "deadlifts", "muscle-ups"],
    },
    "legs": {
        "beginner":     ["bodyweight squats", "leg press", "step-ups"],
        "intermediate": ["barbell squats", "lunges", "leg curls"],
        "advanced":     ["front squats", "deadlifts", "bulgarian split squats"],
    },
    "cardio": {
        "beginner":     ["walking", "light cycling", "elliptical"],
        "intermediate": ["jogging", "cycling", "swimming"],
        "advanced":     ["sprints", "HIIT", "stair climbing"],
    },
}

goals          = ["Weight Loss", "Muscle Gain", "Maintain Fitness"]
genders        = ["Male", "Female"]
bmi_categories = ["Underweight", "Normal", "Overweight", "Obese"]
workout_types  = ["push", "pull", "legs", "cardio"]

goal_params = {
    "Weight Loss":      {"rep_range": (12, 15), "set_range": (3, 4), "duration_mult": 1.2},
    "Muscle Gain":      {"rep_range": (6, 12),  "set_range": (4, 5), "duration_mult": 0.8},
    "Maintain Fitness": {"rep_range": (8, 12),  "set_range": (3, 4), "duration_mult": 1.0},
}

def difficulty_to_score(level):
    return {"beginner": 1, "intermediate": 3, "advanced": 5}[level]

def pick_difficulty(age, bmi_cat, goal):
    if age < 25 and bmi_cat in ("Underweight", "Normal") and goal == "Muscle Gain":
        return "advanced"
    if age > 50 or bmi_cat in ("Overweight", "Obese"):
        return "beginner"
    return random.choice(["beginner", "intermediate", "advanced"])

def make_row():
    age       = random.randint(18, 70)
    gender    = random.choice(genders)
    goal      = random.choice(goals)
    bmi_cat   = random.choice(bmi_categories)
    workout_type = random.choice(workout_types)
    difficulty   = pick_difficulty(age, bmi_cat, goal)
    params       = goal_params[goal]

    row = {
        'age': age,
        'gender': gender,
        'goal': goal,
        'bmi': bmi_cat,
        'workout_type': workout_type,
        'day1_exercise_difficulty': difficulty_to_score(difficulty),
    }

    if workout_type == "cardio":
        name     = random.choice(exercise_db["cardio"][difficulty])
        base_dur = random.randint(15, 45)
        names     = [name, 'none', 'none']
        sets_list = [0, 0, 0]
        reps_list = [0, 0, 0]
        durations = [base_dur, 0, 0]
    else:
        pool   = exercise_db[workout_type][difficulty]
        chosen = random.sample(pool, min(3, len(pool)))
        while len(chosen) < 3:
            chosen.append('none')
        names     = chosen
        sets_list = [random.randint(*params['set_range']) if n != 'none' else 0 for n in names]
        reps_list = [random.randint(*params['rep_range']) if n != 'none' else 0 for n in names]
        durations = [0, 0, 0]

    for i in range(3):
        row[f'day1_exercise{i+1}_name']     = names[i]
        row[f'day1_exercise{i+1}_sets']     = sets_list[i]
        row[f'day1_exercise{i+1}_reps']     = reps_list[i]
        row[f'day1_exercise{i+1}_duration'] = durations[i]

    return row

rows = [make_row() for _ in range(3000)]
out  = Path(__file__).resolve().parent / "workout_data_day1.csv"
pd.DataFrame(rows).to_csv(out, index=False)
print("Wrote", out, "rows:", len(rows))