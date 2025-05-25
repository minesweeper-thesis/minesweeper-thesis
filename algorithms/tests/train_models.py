from algorithms.data.data_loader import DataLoader
from algorithms.classifiers.gaussiannb_classifier import GaussianNBClassifier
from algorithms.classifiers.gradientboosting_classifier import GradientBoostingClassifier
from algorithms.classifiers.mlp_classifier import MLPClassifier


'''classifier = MLPClassifier()
print(classifier.fit(data))
classifier.save('algorithms/models/16,30,99_mlp.model')

classifier = GaussianNBClassifier()
print(classifier.fit(data))
classifier.save('algorithms/models/16,30,99_gaussiannb.model')'''


data = DataLoader(10,10,15).load()

classifier = GradientBoostingClassifier(10000)
print(classifier.fit(data))
classifier.save('algorithms/models/10,10,15_gradientboosting2.model')

data = DataLoader(16,16,40).load()

classifier = GradientBoostingClassifier(10000)
print(classifier.fit(data))
classifier.save('algorithms/models/16,16,40_gradientboosting2.model')