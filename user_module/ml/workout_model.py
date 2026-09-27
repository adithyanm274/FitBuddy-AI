import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler, OneHotEncoder
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer


class EnhancedWorkoutClassifier:
    def __init__(self):
        # Initialize encoders and model components
        self.exercise_encoder = LabelEncoder()
        self.workout_type_encoder = LabelEncoder()
        self.model = self._create_model()

        # Define mappings for encoded values
        self.goals = ["Weight Loss", "Muscle Gain", "Maintain Fitness"]
        self.genders = ["Male", "Female"]
        self.bmi_categories = ["Underweight", "Normal", "Overweight", "Obese"]

        # Define exercise database with difficulty levels
        self.exercise_db = {
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

        # Goal-specific parameters
        self.goal_params = {
            "Weight Loss": {"rep_range": (12, 15), "set_range": (3, 4), "duration_multiplier": 1.2},
            "Muscle Gain": {"rep_range": (6, 12), "set_range": (4, 5), "duration_multiplier": 0.8},
            "Maintain Fitness": {"rep_range": (8, 12), "set_range": (3, 4), "duration_multiplier": 1.0}
        }

    def _create_model(self):
        """Create the enhanced model pipeline"""
        # Treat bmi as categorical because it has string categories
        numeric_features = ['age', 'day1_exercise_difficulty']
        categorical_features = ['gender', 'workout_type', 'goal', 'bmi']

        numeric_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())
        ])

        categorical_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='most_frequent')),
            ('onehot', OneHotEncoder(handle_unknown='ignore'))
        ])

        preprocessor = ColumnTransformer(
            transformers=[
                ('num', numeric_transformer, numeric_features),
                ('cat', categorical_transformer, categorical_features)
            ])

        return Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('regressor', MultiOutputRegressor(
                GradientBoostingRegressor(
                    n_estimators=300,
                    learning_rate=0.05,
                    max_depth=7,
                    min_samples_split=5,
                    random_state=42
                )
            ))
        ])

    def _get_difficulty_level(self, difficulty_score):
        """Convert numeric difficulty to category"""
        if difficulty_score < 2:
            return 'beginner'
        elif difficulty_score < 4:
            return 'intermediate'
        return 'advanced'

    def _decode_encoded_values(self, data):
        """Convert encoded values back to their string representations"""
        data = data.copy()

        if 'gender' in data.columns:
            data['gender'] = data['gender'].apply(
                lambda x: self.genders[int(x)] if pd.notna(x) and str(x).isdigit() else str(x)
            )

        if 'goal' in data.columns:
            data['goal'] = data['goal'].apply(
                lambda x: self.goals[int(x)] if pd.notna(x) and str(x).isdigit() else str(x)
            )

        if 'bmi' in data.columns:
            data['bmi'] = data['bmi'].apply(
                lambda x: self.bmi_categories[int(x)] if pd.notna(x) and str(x).isdigit() else str(x)
            )

        return data

    def clean_data(self, data):
        """Enhanced data cleaning with exercise categorization"""
        data = self._decode_encoded_values(data)

        # Standardize workout types and goals
        data['workout_type'] = data['workout_type'].astype(str).str.lower().str.strip()
        data['goal'] = data['goal'].astype(str).str.strip()
        data['bmi'] = data['bmi'].astype(str).str.strip()

        # Clean exercise names
        for i in range(1, 4):
            col = f'day1_exercise{i}_name'
            if col in data.columns:
                data[col] = data[col].astype(str).str.lower().str.strip()

        # Ensure exercises match their workout type and difficulty
        for idx, row in data.iterrows():
            workout_type = row['workout_type']
            difficulty = self._get_difficulty_level(row['day1_exercise_difficulty'])
            goal = row['goal']

            for i in range(1, 4):
                col = f'day1_exercise{i}_name'
                if col in data.columns and workout_type in self.exercise_db:
                    exercise = row[col]
                    available = self.exercise_db[workout_type].get(difficulty, [])
                    if exercise not in available and available:
                        data.at[idx, col] = np.random.choice(available)

        return data

    def prepare_data(self, data):
        """Prepare features and targets with validation"""
        # Input features
        X = data[['age', 'gender', 'goal', 'bmi', 'workout_type', 'day1_exercise_difficulty']].copy()

        # Output targets
        output_cols = []
        for i in range(1, 4):
            output_cols.extend([
                f'day1_exercise{i}_name',
                f'day1_exercise{i}_sets',
                f'day1_exercise{i}_reps',
                f'day1_exercise{i}_duration'
            ])

        y = data[output_cols].copy()

        # Encode exercise names
        all_exercises = []
        for i in range(1, 4):
            all_exercises.extend(y[f'day1_exercise{i}_name'].unique())
        self.exercise_encoder.fit(all_exercises)

        for i in range(1, 4):
            y[f'day1_exercise{i}_name'] = self.exercise_encoder.transform(
                y[f'day1_exercise{i}_name']
            )

        # Convert numeric columns
        for col in y.columns:
            if 'name' not in col:
                y[col] = pd.to_numeric(y[col], errors='coerce').fillna(0)

        # Encode categorical features
        self.workout_type_encoder.fit(X['workout_type'])

        return X, y

    def fit(self, data):
        """Train the enhanced model"""
        data = self.clean_data(data)
        X, y = self.prepare_data(data)
        self.model.fit(X, y)
        return self

    def _adjust_for_goal(self, params, goal, workout_type):
        """Adjust workout parameters based on fitness goal"""
        goal = str(goal).strip()
        if goal in self.goal_params:
            config = self.goal_params[goal]

            if workout_type == "cardio":
                params['duration'] = int(params['duration'] * config['duration_multiplier'])
            else:
                params['sets'] = np.random.randint(*config['set_range'])
                params['reps'] = np.random.randint(*config['rep_range'])

        return params

    def predict(self, input_data):
        """Make accurate predictions considering difficulty and goals"""
        if not isinstance(input_data, pd.DataFrame):
            input_data = pd.DataFrame([input_data])

        # Convert encoded values if needed
        input_data = self._decode_encoded_values(input_data)

        # Ensure all columns are strings
        for col in ['workout_type', 'goal', 'bmi']:
            if col in input_data.columns:
                input_data[col] = input_data[col].astype(str)

        input_data = self.clean_data(input_data)
        workout_type = input_data['workout_type'].iloc[0]
        difficulty = self._get_difficulty_level(input_data['day1_exercise_difficulty'].iloc[0])
        goal = input_data['goal'].iloc[0]

        # Encode input features
        input_data['workout_type'] = self.workout_type_encoder.transform(
            input_data['workout_type']
        )

        # One-hot encode gender and goal (binary encoding for gender)
        gender_dummy = 1 if input_data['gender'].iloc[0].lower() == 'male' else 0
        input_data['gender'] = gender_dummy

        goal_idx = self.goals.index(goal) if goal in self.goals else 0
        input_data['goal'] = goal_idx

        # Encode bmi as index of bmi_categories or 0 if unknown
        try:
            bmi_idx = self.bmi_categories.index(input_data['bmi'].iloc[0])
        except ValueError:
            bmi_idx = 0
        input_data['bmi'] = bmi_idx

        # Make predictions
        predictions = self.model.predict(input_data)

        # Format results
        is_cardio = (workout_type == "cardio")
        result = {}

        for i in range(3):
            ex_num = i + 1
            start_idx = i * 4

            # Get predicted exercise
            try:
                name_idx = int(round(predictions[0][start_idx]))
                name = self.exercise_encoder.inverse_transform([name_idx])[0]
            except:
                name = 'none'

            if name.lower() == 'none':
                continue

            # Ensure exercise matches workout type and difficulty
            if workout_type in self.exercise_db:
                available = self.exercise_db[workout_type].get(difficulty, [])
                if name.lower() not in available and available:
                    name = np.random.choice(available)

            # Get base parameters
            if is_cardio:
                params = {
                    'duration': max(10, min(90, int(round(predictions[0][start_idx + 3]))))
                }
            else:
                params = {
                    'sets': max(2, min(6, int(round(predictions[0][start_idx + 1])))),
                    'reps': max(5, min(20, int(round(predictions[0][start_idx + 2]))))
                }

            # Adjust for goal
            params = self._adjust_for_goal(params, goal, workout_type)

            # Format output
            if is_cardio:
                if i == 0:  # Only first exercise for cardio
                    result[f'exercise{ex_num}'] = f"{name.title()} - {params['duration']} mins"
            else:
                result[f'exercise{ex_num}'] = f"{name.title()} - {params['sets']}x{params['reps']}"

        return result


# Example usage
if __name__ == "__main__":
    # Load your data
    data = pd.read_csv(r'Fitness/data_creation/workout_data_day1.csv')

    # Initialize and train classifier
    classifier = EnhancedWorkoutClassifier()
    classifier.fit(data)

    # Test predictions with encoded values
    print("Weight Loss Cardio Recommendation (Encoded Input):")
    print(classifier.predict({
        'age': 30,
        'gender':0,  # 0 = Male
        'goal': 0,    # 0 = Weight Loss
        'bmi': 2,     # 2 = Overweight
        'workout_type': 'cardio',
        'day1_exercise_difficulty': 3
    }))

    print("\nMuscle Gain Legs Recommendation (Encoded Input):")
    print(classifier.predict({
        'age': 30,
        'gender': 0,  # 1 = Female
        'goal': 0,    # 1 = Muscle Gain
        'bmi':2,     # 1 = Normal
        'workout_type': 'legs',
        'day1_exercise_difficulty': 3
    }))

    print("\nMaintain Fitness Push Recommendation (Encoded Input):")
    print(classifier.predict({
        'age': 30,
        'gender': 0,  # 0 = Male
        'goal': 0,    # 2 = Maintain Fitness
        'bmi': 2,     # 1 = Normal
        'workout_type': 'push',
        'day1_exercise_difficulty': 3
    }))
