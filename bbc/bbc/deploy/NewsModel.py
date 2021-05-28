from determined.experimental import Determined
import logging
import torch
import numpy as np

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)
import os
from nltk.stem import PorterStemmer
from sklearn.feature_extraction.text import CountVectorizer
import pandas as pd
from sklearn.preprocessing import LabelEncoder


class NewsModel(object):
    """
    Model template. You can load your model parameters in __init__ from a location accessible at runtime
    """

    def __init__(self, det_master="http://10.64.140.43:8080/", model_name="news-classifier"):
        """
        Add any initialization parameters. These will be passed at runtime from the graph definition parameters defined in your seldondeployment kubernetes resource manifest.
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.det = Determined(master=det_master)
        self.model_latest = self.det.get_model(model_name).get_version()
        self.trial = self.det.get_trial(self.model_latest.trial_id)
        self.checkpoint = self.trial.select_checkpoint(uuid=self.model_latest.uuid)
        self.model = self.checkpoint.load(map_location=self.device)

        logging.info("Connected to Determined master at %s", det_master)
        logging.info("Loaded model %s version %s", self.model_latest.model_name,
                     self.model_latest.model_version)
        logging.info("Checkpoint UUID %s", self.model_latest.uuid)
        logging.info("Corresponding experiment %s", self.model_latest.experiment_id)
        logging.info("Loaded model from checkpoint")

        uuid = self.checkpoint.uuid
        self.checkpoint.download()

        voc = pd.read_csv(f'checkpoints/{uuid}/code/bbc.vocab', header=None)
        bbc_classes = pd.read_csv(f'checkpoints/{uuid}/code/bbc.classes', header=None)

        le = LabelEncoder()
        logging.info(bbc_classes.iloc[:, 0].values.astype('U'))
        le.fit(bbc_classes.iloc[:, 0].values.astype('U'))
        self.le = le

        stemmer = PorterStemmer()

        def stemmed_words(doc):
            st = [stemmer.stem(w) for w in analyzer(doc)]
            return st

        analyzer = CountVectorizer().build_analyzer()
        stem_vectorizer = CountVectorizer(analyzer=stemmed_words)
        stem_vectorizer.fit(voc.iloc[:, 0].values.astype('U'))
        print(f'Fitted vectorizer with feature length {len(stem_vectorizer.get_feature_names())}')
        self.vectorizer = stem_vectorizer

    def predict(self, X, features_names=None):
        """
        Return a prediction.
        Parameters
        ----------
        X : array-like
        """

        logging.info(X.shape)
        X = X[0]
        logging.info("Predict called")
        logging.info(X)
        logging.info(type(X))
        logging.info(X.shape)

        # probability_model._make_predict_function()
        with torch.no_grad():
            X_tf = self.vectorizer.transform(X)
            logging.info(X_tf)
            X_tf = torch.tensor(X_tf.toarray()).float()
            X_tf = torch.Tensor(X_tf)
            pred = self.model.model(X_tf)

        label_id = np.argmax(pred[0])
        label = self.le.inverse_transform([label_id, ])
        logging.info("Predicted news class: %s", label[0])
        return label[0]
