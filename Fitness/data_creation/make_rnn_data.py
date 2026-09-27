import random
from pathlib import Path
import pandas as pd

workout_types = ['legs', 'push', 'cardio', 'pull']

def next_type(prev):
    if prev is None:
        return random.choice(workout_types)
    return random.choice([t for t in workout_types if t != prev])

def make_row():
    age = random.randint(18, 70)
    gender = random.choice([0, 1])
    goal = random.choice([0, 1, 2])
    bmi = round(random.uniform(15.0, 40.0), 1)
    if age < 25 and bmi < 25 and goal == 1:
        diff = "advanced"
    elif age > 50 or bmi >= 30:
        diff = "beginner"
    else:
        diff = "intermediate"
    prev, seq = None, []
    for _ in range(3):
        prev = next_type(prev)
        seq.append(prev)
    return {
        'age': age, 'gender': gender, 'goal': goal, 'bmi': bmi,
        'day1_workout': seq[0], 'day1_diff': diff,
        'day2_workout': seq[1], 'day2_diff': diff,
        'target_workout': seq[2], 'target_diff': diff,
    }

rows = [make_row() for _ in range(4000)]
out = Path(__file__).resolve().parent / "workout_data_no_rest.csv"
pd.DataFrame(rows).to_csv(out, index=False)
print("Wrote", out, "rows:", len(rows))