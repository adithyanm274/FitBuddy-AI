import joblib
import pandas as pd

# Load saved model and encoder
model = joblib.load("Fitness/data_creation/workout_type_classifier_20250609_013449.joblib")
le = joblib.load("Fitness/data_creation/label_encoder_20250609_013449.joblib")

# Input user profile
user_input = pd.DataFrame([{
    'age': 27,
    'gender': 1,  # 0 = Female, 1 = Male
    'goal': 0,    # 0 = Weight Loss, 1 = Maintain, 2 = Muscle Gain
    'bmi': 24.5
}])

# Predict workout type
pred = model.predict(user_input)
pred_label = le.inverse_transform(pred)[0]

print(f"Recommended Workout Type: {pred_label}")
