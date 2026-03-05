import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler, OneHotEncoder
from sklearn.multioutput import MultiOutputRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer

# Load data
df = pd.read_csv(r'Fitness\data_creation\workout_data_rnn_day2.csv')  # Replace with your actual path

# Input features
input_cols = [
    'age', 'gender', 'goal', 'bmi',
    'day1_exercise_difficulty', 'day1_workout_type'
]

# Target columns
target_categorical_cols = [
    'target_day_workout_type',
    'target_exercise1_name',
    'target_exercise2_name',
    'target_exercise3_name'
]

target_numeric_cols = [
    'target_exercise_difficulty',
    'target_exercise1_sets', 'target_exercise1_reps', 'target_exercise1_duration',
    'target_exercise2_sets', 'target_exercise2_reps', 'target_exercise2_duration',
    'target_exercise3_sets', 'target_exercise3_reps', 'target_exercise3_duration'
]

# Prepare label encoders for categorical targets
target_encoders = {}
for col in target_categorical_cols:
    le = LabelEncoder()
    df[col] = df[col].fillna('none').astype(str)
    df[col] = le.fit_transform(df[col])
    target_encoders[col] = le

# Prepare label encoders for input categorical features
# Assume gender, goal, bmi, day1_workout_type are categorical
for col in ['gender', 'goal', 'bmi', 'day1_workout_type']:
    df[col] = df[col].astype(str)

# Features and target
X = df[input_cols]
y_cat = df[target_categorical_cols]
y_num = df[target_numeric_cols]

# Combine categorical and numeric targets for multioutput regressor
y = pd.concat([y_cat, y_num], axis=1)

# Preprocessing for inputs
numeric_features = ['age', 'day1_exercise_difficulty']
categorical_features = ['gender', 'goal', 'bmi', 'day1_workout_type']

numeric_transformer = Pipeline(steps=[
    ('scaler', StandardScaler())
])

categorical_transformer = Pipeline(steps=[
    ('onehot', OneHotEncoder(handle_unknown='ignore'))
])

preprocessor = ColumnTransformer(
    transformers=[
        ('num', numeric_transformer, numeric_features),
        ('cat', categorical_transformer, categorical_features)
    ])

# Define model pipeline
model = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('regressor', MultiOutputRegressor(GradientBoostingRegressor(n_estimators=200, random_state=42)))
])

# Train model
model.fit(X, y)

# Function to inverse transform categorical predictions back to strings
def decode_predictions(pred_array):
    decoded = {}
    # First 4 columns are categorical targets
    for i, col in enumerate(target_categorical_cols):
        le = target_encoders[col]
        val = int(round(pred_array[i]))
        # Clamp value to valid range
        val = max(0, min(val, len(le.classes_) - 1))
        decoded[col] = le.inverse_transform([val])[0]
    # Remaining are numeric
    idx = len(target_categorical_cols)
    for j, col in enumerate(target_numeric_cols):
        decoded[col] = max(0, round(pred_array[idx + j]))
    return decoded

# Example input for prediction (change values to test)
sample_input = pd.DataFrame([{
    'age': 28,
    'gender': 'male',
    'goal': 'Weight Loss',
    'bmi': 'Normal',
    'day1_exercise_difficulty': 2,
    'day1_workout_type': 'cardio'
}])

# Predict
predicted = model.predict(sample_input)[0]

# Decode and print results
decoded_pred = decode_predictions(predicted)
print("Predicted target values:")
for k, v in decoded_pred.items():
    print(f"{k}: {v}")
