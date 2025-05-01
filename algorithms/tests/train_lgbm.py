from algorithms.data.data_loader import DataLoader
from algorithms.classifiers.lightgbm_classifier import LightGBMClassifier

data = DataLoader(16,30,99).load()
classifier = LightGBMClassifier()
print(classifier.fit(data))