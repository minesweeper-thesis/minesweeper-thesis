from algorithms.data_loader import DataLoader as DL

data = [(board.model_input(), solvable) for board, solvable in DL(16,30,99).load()]

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader, random_split
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import balanced_accuracy_score

# === 1. Dataset ===

class BoardDataset(Dataset):
    def __init__(self, data):
        self.boards = [torch.tensor(b, dtype=torch.float32) for b, _ in data]
        self.labels = [torch.tensor(float(s), dtype=torch.float32) for _, s in data]

    def __len__(self):
        return len(self.boards)

    def __getitem__(self, idx):
        return self.boards[idx], self.labels[idx]

# === 2. Model ===

class SimpleCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(2, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1))
        )
        self.fc = nn.Linear(64, 1)

    def forward(self, x):
        x = self.conv(x)
        x = x.view(x.size(0), -1)
        return self.fc(x)


# === 3. Przygotowanie danych ===

# Zakładamy, że masz zmienną: data = List[Tuple[np.ndarray, bool]]
train_data, test_data = train_test_split(data, test_size=0.2, random_state=42)
train_dataset = BoardDataset(train_data)
test_dataset = BoardDataset(test_data)

# Podział train na train + val
train_size = int(0.8 * len(train_dataset))
val_size = len(train_dataset) - train_size
train_set, val_set = random_split(train_dataset, [train_size, val_size])

train_loader = DataLoader(train_set, batch_size=32, shuffle=True)
val_loader = DataLoader(val_set, batch_size=32)
test_loader = DataLoader(test_dataset, batch_size=32)

# Oblicz pos_weight do zbalansowanego lossu
labels = [int(s) for _, s in train_data]
neg, pos = labels.count(0), labels.count(1)
pos_weight = torch.tensor(neg / pos)

# === 4. Trening ===

model = SimpleCNN()
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)

best_val_loss = float('inf')  # Trzymamy najlepszy wynik
best_model_state = None

for epoch in range(50):
    model.train()
    total_loss = 0
    for x, y in train_loader:
        optimizer.zero_grad()
        logits = model(x)
        loss = criterion(logits.squeeze(), y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()

    # Walidacja
    model.eval()
    val_loss = 0
    with torch.no_grad():
        for x, y in val_loader:
            logits = model(x)
            loss = criterion(logits.squeeze(), y)
            val_loss += loss.item()

    print(f"Epoch {epoch+1} - Train loss: {total_loss:.4f}, Val loss: {val_loss:.4f}")

    # Jeśli wynik na zbiorze walidacyjnym jest najlepszy, zapisujemy model
    if val_loss < best_val_loss:
        best_val_loss = val_loss
        best_model_state = model.state_dict()

# Załaduj najlepszy model po zakończeniu treningu
model.load_state_dict(best_model_state)

# === 5. Testowanie ===

model.eval()
all_preds, all_labels = [], []

with torch.no_grad():
    for x, y in test_loader:
        logits = model(x)
        preds = (torch.sigmoid(logits).squeeze() > 0.5).int()
        all_preds.extend(preds.tolist())
        all_labels.extend(y.int().tolist())

acc = balanced_accuracy_score(all_labels, all_preds)
print(f"\n✅ Final balanced accuracy on test set: {acc:.4f}")

# Zapisz najlepszy model do pliku
 