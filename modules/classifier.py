from modules.text_vectorizer import TextVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.base import ClassifierMixin, BaseEstimator
from sklearn.utils.validation import check_is_fitted


class ClaimsClassifier(ClassifierMixin, BaseEstimator):
    def __init__(self):
        self.__encoder = None
        self.__clf = None
        
    def fit(self, X, y):
        self.__encoder = LabelEncoder()
        y = self.__encoder.fit_transform(y)
        pipe = Pipeline([
            ('vectorizer', TextVectorizer()),
            ('scaler', StandardScaler()),
            ('classifier', RandomForestClassifier(max_depth=20, max_features='log2', n_estimators=10))
        ])
        self.__clf = pipe.fit(X, y)
        if self.__clf:
            self.is_fitted_ = True
        return self
    
    def __predict(self, X):
        check_is_fitted(self)
        return self.__encoder.inverse_transform(self.__clf.predict(X))
    
    def classify(self, X):
        """Clasifica una lista de reclamos
        Args:
            X (List): Lista de reclamos a clasificar, el formato de cada reclamo debe ser un string
        Returns:
            clasificación: Lista con las clasificaciones de los reclamos, el formato de cada clasificación es un string
            los valores posibles dependen de las etiquetas en y usadas en el entrenamiento
        """
        return self.__predict(X)
    
