from algorithms.data.data_loader import DataLoader
from algorithms.classifiers.lightgbm_classifier import LightGBMClassifier

data = DataLoader(16,16,40).load()
classifier = LightGBMClassifier()
print(classifier.fit(data))
classifier.save('algorithms/tests/16,16,40.model')