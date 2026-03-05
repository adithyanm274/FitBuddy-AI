import torch
import torch.nn.functional as F
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification
import json
import os

# Load model and tokenizer
model_name = "intent_classifier_model"
tokenizer = DistilBertTokenizerFast.from_pretrained(model_name)
model = DistilBertForSequenceClassification.from_pretrained(model_name)
model.eval()

# Load intent label mapping (if available)
label_path = os.path.join(model_name, "intent_labels.json")
if os.path.exists(label_path):
    with open(label_path, "r") as f:
        label_mapping = json.load(f)
        idx_to_label = {v: k for k, v in label_mapping.items()}
else:
    idx_to_label = {}

# Function to predict the intent with confidence
def predict_intent(user_message):
    inputs = tokenizer(user_message, return_tensors="pt", truncation=True, padding=True, max_length=128)
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probs = F.softmax(logits, dim=-1)
        confidence, predicted_class = torch.max(probs, dim=-1)
        predicted_class = predicted_class.item()
        confidence = confidence.item()
        if confidence < 0.6:
            intent = "unknown"
            response = "I'm not sure I understood that. Can you please clarify?"
    intent_label = idx_to_label.get(predicted_class, str(predicted_class))
    return intent_label, confidence

# Test it
y=input("Type:")
x = predict_intent(y)
print("Predicted intent:", x)

