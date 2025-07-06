from algorithms.data.data_loader import DataLoader
from algorithms.classifiers.gaussiannb_classifier import GaussianNBClassifier
from algorithms.classifiers.gradientboosting_classifier import (
    GradientBoostingClassifier,
)
from algorithms.classifiers.mlp_classifier import MLPClassifier
from algorithms.classifiers.lightgbm_classifier import LightGBMClassifier


data = DataLoader(16, 30, 99).load()
for tries in (100, 200, 300, 400, 500):
    classifier = LightGBMClassifier(tries)
    print(classifier.fit(data))
    classifier.save("algorithms/models/16,30,99_lightgbm.model")
