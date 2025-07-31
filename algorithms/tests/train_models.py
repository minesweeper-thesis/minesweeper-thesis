from algorithms.data.data_loader import DataLoader
from algorithms.classifiers.gaussiannb_classifier import GaussianNBClassifier
from algorithms.classifiers.catboost_classifier import CatBoostClassifier
from algorithms.classifiers.gaussiannb_classifier import (
    GaussianNBClassifier,
)
from algorithms.classifiers.mlp_classifier import MLPClassifier
from algorithms.classifiers.lightgbm_classifier import LightGBMClassifier
from algorithms.classifiers.xgboost_classifier import XGBoostClassifier


data = DataLoader(10, 10, 15).load()
classifier = GaussianNBClassifier()
print(f"10,10,15_gaussiannb\t{classifier.fit(data)}")
classifier.save(f"algorithms/models/10,10,15_gaussiannb.model")

data = DataLoader(16, 16, 40).load()
classifier = GaussianNBClassifier()
print(f"16,16,40_gaussiannb\t{classifier.fit(data)}")
classifier.save(f"algorithms/models/16,16,40_gaussiannb.model")

data = DataLoader(16, 30, 99).load()
classifier = GaussianNBClassifier()
print(f"16,30,99_gaussiannb\t{classifier.fit(data)}")
classifier.save(f"algorithms/models/16,30,99_gaussiannb.model")
