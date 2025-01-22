import os
import json
import torch
import torch.nn as nn
import torch.optim as optim

# Use a relative import if this file and enemy_movement_model.py are in the same folder:
from .enemy_movement_model import EnemyMovementModel

# Build absolute paths to data and model, so it works regardless of where you run it from
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "training_data.json")
SAVE_PATH = os.path.join(PROJECT_ROOT, "models", "enemy_ai_model.pth")

# Load the training data
with open(DATA_PATH, "r") as f:
    training_data = json.load(f)

# Prepare inputs and targets
inputs = []
targets = []

for sample in training_data:
    # Example input structure: [player_x, player_y, enemy_x, enemy_y, dist]
    input_vec = [
        sample["player_x"],
        sample["player_y"],
        sample["enemy_x"],
        sample["enemy_y"],
        sample["dist"],
    ]

    # Example: 'missile_action' is your target field
    if "missile_action" in sample:
        target_val = [sample["missile_action"]]
        targets.append(target_val)
    else:
        # Skip samples that lack 'missile_action'
        continue

    inputs.append(input_vec)

# Convert lists to tensors
inputs = torch.tensor(inputs, dtype=torch.float32)
targets = torch.tensor(targets, dtype=torch.float32)

# Define and configure the model
model = EnemyMovementModel(input_size=5, hidden_size=64, output_size=2)
criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=1e-3)

# Training loop
epochs = 20
for epoch in range(epochs):
    model.train()
    optimizer.zero_grad()

    predictions = model(inputs)
    loss = criterion(predictions, targets)
    loss.backward()
    optimizer.step()

    print(f"Epoch {epoch+1}/{epochs}, Loss: {loss.item():.4f}")

# Save the trained model weights
torch.save(model.state_dict(), SAVE_PATH)
print(f"Model saved to {SAVE_PATH}")
