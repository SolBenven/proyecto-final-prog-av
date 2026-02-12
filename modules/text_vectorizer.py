import numpy as np
import spacy
from sklearn.base import BaseEstimator, TransformerMixin


class TextVectorizer(BaseEstimator, TransformerMixin):
    def __init__(self, p_language_model='es_core_news_sm'):
        """
        Vectorizador de texto basado en spaCy (para español).
        - Tokeniza, lematiza y elimina stopwords y signos de puntuación.
        """
        self.__nlp = spacy.load(p_language_model)
        self.__word2idx = {}
        self.__vocabulary = None

    def __get_tokens(self, texto):
        """
        Procesa el texto: minúsculas, lematización, eliminación de stopwords y puntuación.
        """
        doc = self.__nlp(texto.lower())
        word_tokens = [
            token.lemma_ for token in doc
                if not token.is_stop and not token.is_punct and not token.is_space and not token.like_num
        ]
        return ' '.join(word_tokens)

    def __text_to_vector(self, texto):
        """
        Convierte un texto en un vector de frecuencia de palabras basado en el vocabulario aprendido.
        """
        word_vector = np.zeros(len(self.__vocabulary), dtype=np.int_)
        texto = self.__get_tokens(texto)
        for word in texto.split(" "):
            idx = self.__word2idx.get(word)
            if idx is not None:
                word_vector[idx] += 1
        return word_vector

    def fit(self, X, y=None):
        """
        Construye el vocabulario a partir del conjunto de textos de entrenamiento.
        """
        X_processed = [self.__get_tokens(text) for text in X]

        words = set()
        for text in X_processed:
            for word in text.split(" "):
                words.add(word)
        
        self.__vocabulary = list(words)
        for i, word in enumerate(self.__vocabulary):
            self.__word2idx[word] = i

        return self

    def transform(self, X, y=None):
        """
        Transforma una lista de textos en una matriz de vectores.
        """
        word_vectors = np.zeros((len(X), len(self.__vocabulary)), dtype=np.int_)
        for i, text in enumerate(X):
            word_vectors[i] = self.__text_to_vector(text)
        return word_vectors