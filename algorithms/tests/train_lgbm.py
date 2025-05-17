from algorithms.data.data_loader import DataLoader
from algorithms.classifiers.lightgbm_classifier import LightGBMClassifier

data = DataLoader(16,30,99).load()
classifier = LightGBMClassifier(300)
print(classifier.fit(data))
classifier.save('algorithms/tests/16,30,99.model')