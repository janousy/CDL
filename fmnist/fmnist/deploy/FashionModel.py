import logging

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)
import os

from determined.experimental import Determined
import logging
import tensorflow as tf
import numpy as np
import pandas as pd
import python_pachyderm


class FashionModel(object):
    """
    Model template. You can load your model parameters in __init__ from a location accessible at runtime
    """

    def __init__(self, det_master="http://10.64.140.43:8080/", model_name="fashion-classifier"):
        """
        Add any initialization parameters. These will be passed at runtime from the graph definition parameters defined in your seldondeployment kubernetes resource manifest.
        """

        # To overcome the graph issue: https://github.com/tensorflow/tensorflow/issues/33744

        config = tf.ConfigProto(
            intra_op_parallelism_threads=1,
            allow_soft_placement=True
        )
        # LP: create session by config
        self.tf_session = tf.Session(config=config)
        tf.compat.v1.keras.backend.set_session(self.tf_session)

        self.det = Determined(master=det_master)
        self.model_latest = self.det.get_model(model_name).get_version()
        self.trial = self.det.get_trial(self.model_latest.trial_id)
        self.checkpoint = self.trial.select_checkpoint(uuid=self.model_latest.uuid)
        self.model = self.checkpoint.load()

        logging.info("Connected to Determined master at %s", det_master)
        logging.info("Loaded model %s version %s", self.model_latest.model_name,
                     self.model_latest.model_version)
        logging.info("Checkpoint UUID %s", self.model_latest.uuid)
        logging.info("Corresponding experiment %s", self.model_latest.experiment_id)
        logging.info("Loaded model from checkpoint")

        uuid = self.checkpoint.uuid
        self.checkpoint.download()

        fmnist_classes = pd.read_csv(f'checkpoints/{uuid}/code/fmnist.classes', header=None)
        self.classes = fmnist_classes.iloc[:, 0].values.astype('U')
        logging.info(self.classes)

        logging.info("Loaded checkpoint")

        self.probability_model = tf.keras.Sequential([self.model, tf.keras.layers.Softmax()])

        self.model.summary()
        self.probability_model.summary()

        # https://github.com/keras-team/keras/issues/6462
        self.probability_model._make_predict_function()

    def predict(self, X, features_names=None):
        """
        Return a prediction.
        Parameters
        ----------
        X : array-like
        """
        logging.info("Predict called")
        logging.info(type(X))
        logging.info(X.shape)
        # X = np.expand_dims(X, axis=0)
        try:
            X.shape = (1, 28, 28)
        except Exception as error:
            logging.info(error)

        logging.info(f'input expanded: {X.shape}')

        pred = self.probability_model.predict(X)

        label_id = np.argmax(pred[0])
        logging.info("Computed label: %d", label_id)

        return self.classes[label_id]
