from algorithms.data.data_loader import DataLoader
from algorithms.classifiers.lightgbm_classifier import LightGBMClassifier
from algorithms.classifiers.catboost_classifier import CatBoostClassifier
from algorithms.classifiers.xgboost_classifier import XGBoostClassifier

data = DataLoader(16,16,40).load()

classifier = LightGBMClassifier(300)
print(classifier.fit(data))
classifier.save('algorithms/tests/16,16,40_lightgbm.model')

classifier = CatBoostClassifier(300)
print(classifier.fit(data))
classifier.save('algorithms/tests/16,16,40_catboost.model')

classifier = XGBoostClassifier(300)
print(classifier.fit(data))
classifier.save('algorithms/tests/16,16,40_xgboost.model')