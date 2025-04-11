from data_loader import DataLoader

data = [(board.model_input(), solvable) for board, solvable in DataLoader(16,30,99).load()]

import numpy as np
from lightgbm import LGBMClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import balanced_accuracy_score

# Zakładamy: data = List[Tuple[np.ndarray (2,10,10), bool]]

def prepare_data(data):
    X = np.array([board.flatten() for board, _ in data])  # (N, 200)
    y = np.array([int(solvable) for _, solvable in data]) # (N,)
    return X, y

# Przygotuj dane
X, y = prepare_data(data)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Pipeline: Standaryzacja + LightGBM z class_weight
model = make_pipeline(
    StandardScaler(),
    LGBMClassifier(
        class_weight='balanced',   # uwzględnia niezbalansowanie klas
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5,
        random_state=42,
        verbose=-1
    )
)

# Trening
model.fit(X_train, y_train)

# Ewaluacja
y_pred = model.predict(X_test)
acc = balanced_accuracy_score(y_test, y_pred)
print(f"\nLightGBM balanced accuracy: {acc:.4f}")
