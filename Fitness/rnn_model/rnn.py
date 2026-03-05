import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import pandas as pd

# Updated vocabularies (core removed)
workout_types = ['legs', 'push', 'cardio', 'pull']
difficulty_levels = ['beginner', 'intermediate', 'advanced']

workout_to_idx = {w: i for i, w in enumerate(workout_types)}
diff_to_idx = {d: i for i, d in enumerate(difficulty_levels)}

class WorkoutDataset(Dataset):
    def __init__(self, csv_path):
        df = pd.read_csv(csv_path)

        self.sequences = []
        self.extra_features = []
        self.targets = []

        for _, row in df.iterrows():
            seq = [
                (workout_to_idx[row['day1_workout']], diff_to_idx[row['day1_diff']]),
                (workout_to_idx[row['day2_workout']], diff_to_idx[row['day2_diff']])
            ]
            # normalize age & bmi
            age = row['age'] / 100
            bmi = row['bmi'] / 50

            self.sequences.append(seq)
            self.extra_features.append([age, row['gender'], row['goal'], bmi])
            self.targets.append((
                workout_to_idx[row['target_workout']],
                diff_to_idx[row['target_diff']]
            ))

    def __len__(self):
        return len(self.sequences)

    def __getitem__(self, idx):
        input_seq = torch.tensor(self.sequences[idx], dtype=torch.long)
        extra_feat = torch.tensor(self.extra_features[idx], dtype=torch.float)
        target = torch.tensor(self.targets[idx], dtype=torch.long)
        return (input_seq, extra_feat), target

class WorkoutRNN(nn.Module):
    def __init__(self, workout_vocab_size, diff_vocab_size, embed_dim, hidden_dim, extra_feat_dim):
        super().__init__()
        self.workout_embedding = nn.Embedding(workout_vocab_size, embed_dim)
        self.diff_embedding = nn.Embedding(diff_vocab_size, embed_dim)
        self.lstm = nn.LSTM(embed_dim * 2, hidden_dim, batch_first=True)

        self.extra_fc = nn.Sequential(
            nn.Linear(extra_feat_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 8)
        )

        self.fc_workout = nn.Linear(hidden_dim + 8, workout_vocab_size)
        self.fc_diff = nn.Linear(hidden_dim + 8, diff_vocab_size)

    def forward(self, x):
        seq, extra = x
        workout_idx = seq[:, :, 0]
        diff_idx = seq[:, :, 1]

        workout_emb = self.workout_embedding(workout_idx)
        diff_emb = self.diff_embedding(diff_idx)

        x_emb = torch.cat((workout_emb, diff_emb), dim=2)
        out, _ = self.lstm(x_emb)
        last_out = out[:, -1, :]

        extra_out = self.extra_fc(extra)
        combined = torch.cat((last_out, extra_out), dim=1)

        workout_out = self.fc_workout(combined)
        diff_out = self.fc_diff(combined)

        return workout_out, diff_out

def train_model(model, dataloader, epochs=10, lr=0.001):
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    model.train()
    for epoch in range(epochs):
        total_loss = 0
        for (inputs, extra_feats), targets in dataloader:
            optimizer.zero_grad()
            workout_pred, diff_pred = model((inputs, extra_feats))
            loss1 = criterion(workout_pred, targets[:, 0])
            loss2 = criterion(diff_pred, targets[:, 1])
            loss = loss1 + loss2
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        print(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss/len(dataloader):.4f}")

def predict_next_day(model, input_seq, extra_feat):
    model.eval()
    with torch.no_grad():
        input_tensor = torch.tensor([input_seq], dtype=torch.long)
        extra_tensor = torch.tensor([extra_feat], dtype=torch.float)
        workout_out, diff_out = model((input_tensor, extra_tensor))
        workout_idx = torch.argmax(workout_out, dim=1).item()
        diff_idx = torch.argmax(diff_out, dim=1).item()
        return workout_types[workout_idx], difficulty_levels[diff_idx]

# === Load Data and Train Model ===

csv_path = "Fitness/data_creation/rnn_data.csv"  # your updated CSV file
dataset = WorkoutDataset(csv_path)
dataloader = DataLoader(dataset, batch_size=32, shuffle=True)

model = WorkoutRNN(
    workout_vocab_size=len(workout_types),
    diff_vocab_size=len(difficulty_levels),
    embed_dim=8,
    hidden_dim=16,
    extra_feat_dim=4
)

train_model(model, dataloader, epochs=10)

# Save model
torch.save(model.state_dict(), "Fitness/data_creation/workout_rnn_model.pth")

# === Example Prediction ===

example_seq = [(workout_to_idx['legs'], diff_to_idx['intermediate']),
               (workout_to_idx['cardio'], diff_to_idx['beginner'])]
example_extra = [0.54, 1, 1, 22.2/50]  # normalized age, gender, goal, bmi

predicted_workout, predicted_diff = predict_next_day(model, example_seq, example_extra)
print(f"Predicted workout: {predicted_workout}, difficulty: {predicted_diff}")
