from algorithms.data.data_loader import DataLoader
from algorithms.classifiers.cnn_classifier import CNNClassifier

data = DataLoader(10,10,15).load()
classifier = CNNClassifier()
print(classifier.fit(data))
classifier.save('algorithms/tests/10,10,15.model')