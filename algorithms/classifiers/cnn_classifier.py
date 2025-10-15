import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.metrics import balanced_accuracy_score
from algorithms.boards.board import Board
from algorithms.classifiers.classifier import Classifier
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
import random


class BoardDataset(Dataset):
    """
    PyTorch Dataset for board game samples.

    Each sample is a tuple of (board, label), where `board` has a `model_input()`
    method returning a tensor-like array suitable for CNN input, and `label` is a float.
    """

    def __init__(self, data: list[tuple[object, float]]) -> None:
        """
        Initialize the dataset.

        Args:
            data (List[Tuple[object, float]]): List of tuples containing board objects and labels.
        """
        self.samples: list[tuple[object, float]] = data

    def __len__(self) -> int:
        """
        Return the number of samples in the dataset.
        """
        return len(self.samples)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Retrieve a sample and convert it to tensors.

        Args:
            idx (int): Index of the sample.

        Returns:
            Tuple[torch.Tensor, torch.Tensor]: Input tensor `x` and label tensor `y`.
        """
        board, label = self.samples[idx]
        x: torch.Tensor = torch.tensor(board.model_input(), dtype=torch.float32)
        y: torch.Tensor = torch.tensor(float(label), dtype=torch.float32)
        return x, y


class CNN(nn.Module):
    """
    Convolutional Neural Network for board state evaluation.

    The network takes an input of shape (batch_size, 2, H, W) and outputs a single
    scalar per sample, after passing through convolutional layers and fully connected layers.
    """

    def __init__(self) -> None:
        """
        Initialize the CNN model with convolutional and fully connected layers.
        """
        super().__init__()
        self.features: nn.Sequential = nn.Sequential(
            nn.Conv2d(2, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1)),
        )
        self.classifier: nn.Sequential = nn.Sequential(
            nn.Flatten(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(64, 1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass of the network.

        Args:
            x (torch.Tensor): Input tensor of shape (batch_size, 2, H, W).

        Returns:
            torch.Tensor: Output tensor of shape (batch_size, 1) with values in [0, 1].
        """
        x = self.features(x)
        return self.classifier(x)


class CNNClassifier(Classifier):
    """Classifier based on a CNN network."""

    def __init__(self) -> None:
        """Initializes classifier model."""
        if torch.cuda.is_available():
            self.device = "cuda"
        elif torch.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"
        self.model = CNN().to(self.device)

    def fit(self, data: list[tuple["Board", bool]]) -> float:
        """Trains the classifier on provided data.

        Args:
            data (list[tuple[Board, bool]]): list of pairs (board, deterministic or not?).

        Returns:
            float: balanced accuracy on testing subset.
        """
        random.shuffle(data)

        total = len(data)
        train_size = int(0.8 * total)
        val_size = int(0.1 * total)

        train_set = BoardDataset(data[:train_size])
        val_set = BoardDataset(data[train_size : train_size + val_size])
        test_set = BoardDataset(data[train_size + val_size :])

        train_loader = DataLoader(train_set, batch_size=32, shuffle=True)
        val_loader = DataLoader(val_set, batch_size=32)
        test_loader = DataLoader(test_set, batch_size=32)

        best_model = None
        best_val_acc = 0.0

        optimizer = optim.Adam(self.model.parameters(), lr=1e-3)
        loss_fn = nn.BCELoss()

        for epoch in range(50):
            self.model.train()
            for x_batch, y_batch in train_loader:
                x_batch = x_batch.to(self.device)
                y_batch = y_batch.to(self.device).unsqueeze(1)

                optimizer.zero_grad()
                preds = self.model(x_batch)
                loss = loss_fn(preds, y_batch)
                loss.backward()
                optimizer.step()

            # validation
            self.model.eval()
            all_preds, all_labels = [], []
            with torch.no_grad():
                for x_val, y_val in val_loader:
                    x_val = x_val.to(self.device)
                    preds = self.model(x_val).cpu().numpy()
                    all_preds.extend(preds.flatten())
                    all_labels.extend(y_val.numpy())

            pred_labels = [p > 0.5 for p in all_preds]
            val_acc = balanced_accuracy_score(all_labels, pred_labels)
            print(val_acc)

            if val_acc > best_val_acc:
                best_val_acc = val_acc
                best_model = self.model.state_dict()

        if best_model:
            self.model.load_state_dict(best_model)

        # test
        self.model.eval()
        all_preds, all_labels = [], []
        with torch.no_grad():
            for x_test, y_test in test_loader:
                x_test = x_test.to(self.device)
                preds = self.model(x_test).cpu().numpy()
                all_preds.extend(preds.flatten())
                all_labels.extend(y_test.numpy())

        pred_labels = [p > 0.5 for p in all_preds]
        return balanced_accuracy_score(all_labels, pred_labels)

    def classify(self, board: "Board") -> float:
        """Classifies the board.

        Args:
            board (Board): board to classify.

        Returns:
            float: probability that the board is deterministically solvable.
        """
        self.model.eval()
        x = (
            torch.tensor(board.model_input(), dtype=torch.float32)
            .unsqueeze(0)
            .to(self.device)
        )
        with torch.no_grad():
            output = self.model(x)
        return float(output.item())

    def save(self, filename: str) -> None:
        """Saves the classifier model.

        Args:
            filename (str): path to the model.
        """
        torch.save(self.model.state_dict(), filename)

    def load(self, filename: str) -> None:
        """Loads the classifier model.

        Args:
            filename (str): path to the model.
        """
        self.model.load_state_dict(torch.load(filename, map_location=self.device))
        self.model.to(self.device)
