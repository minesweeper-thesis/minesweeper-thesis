import torch.nn as nn
import torchvision.models as models


class CNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.model = models.resnet18()

        self.model.conv1 = nn.Conv2d(
            in_channels=2,
            out_channels=64,
            kernel_size=7,
            stride=2,
            padding=3,
            bias=False,
        )
        self.model.fc = nn.Linear(self.model.fc.in_features, 1)

    def forward(self, x):
        return self.model(x)
