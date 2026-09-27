import pandas as pd
import numpy as np
from sklearn.preprocessing import OneHotEncoder, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.metrics import classification_report, accuracy_score
import joblib
from datetime import datetime
import matplotlib.pyplot as plt

# --------------------------
# LOAD & INSPECT DATA
# --------------------------
df = pd.read_csv("Fitness/data_creation/workout_data.csv")  # Adjust path as needed

# Only keep profile columns and the label
df = df[['age', 'gender', 'goal', 'bmi', 'day1_workout_type']].dropna()

# --------------------------
# FEATURE & LABEL SETUP
# --------------------------
X = df[['age', 'gender', 'goal', 'bmi']]
y = df['day1_workout_type']

# Encode labels (e.g., 'push', 'legs', 'cardio') to numbers
le = LabelEncoder()
y_encoded = le.fit_transform(y)

# --------------------------
# TRAIN-TEST SPLIT
# --------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)

# --------------------------
# PREPROCESSING PIPELINE
# --------------------------
categorical_features = ['gender', 'goal']
numeric_features = ['age', 'bmi']

preprocessor = ColumnTransformer(transformers=[
    ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features),
    ('num', 'passthrough', numeric_features)
])

# --------------------------
# FINAL PIPELINE
# --------------------------
model = Pipeline([
    ('preprocessor', preprocessor),
    ('classifier', GradientBoostingClassifier(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=6,
        random_state=42
    ))
])

# --------------------------
# TRAIN MODEL
# --------------------------
model.fit(X_train, y_train)

# --------------------------
# EVALUATION
# --------------------------
y_pred = model.predict(X_test)
print(f"\nAccuracy: {accuracy_score(y_test, y_pred):.2f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=le.classes_))

# --------------------------
# SAVE MODEL & LABEL ENCODER
# --------------------------
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
model_path = f"workout_type_classifier_{timestamp}.joblib"
encoder_path = f"label_encoder_{timestamp}.joblib"

joblib.dump(model, model_path)
joblib.dump(le, encoder_path)

print(f"✅ Model saved as: {model_path}")
print(f"✅ Label encoder saved as: {encoder_path}")
