from fmnist.model.src.data import transform
from determined.experimental import Determined
import unittest
import python_pachyderm
import gzip
import numpy as np
import logging

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)


class TestModelAccuracy(unittest.TestCase):
    # TODO: adjust the IP according to your Kubernetes Cluster
    DET_MASTER = "http://10.64.140.43:8080"
    MODEL_NAME = "fashion-classifier"

    # Define the minimum accuracy for the model to pass this test
    ACCURACY_THRESHOLD = 0.7

    PACH_TEST_REPO = "fmnist-test-raw"
    PACH_TEST_BRANCH = "master"

    def setUp(self):

        # get latest version from registered model
        logging.info("Testing model %s for accuracy", self.MODEL_NAME)
        logging.info("Testing accuracy threshold at %f", self.ACCURACY_THRESHOLD.__float__())

        # download model and metadata
        self.det = Determined(master=self.DET_MASTER)
        self.model_latest = self.det.get_model(self.MODEL_NAME).get_version()
        self.trial = self.det.get_trial(self.model_latest.trial_id)
        self.checkpoint = self.trial.select_checkpoint(uuid=self.model_latest.uuid)
        self.model = self.checkpoint.load()

        logging.info("Connected to Determined master at %s", self.DET_MASTER)
        logging.info("Loaded model %s version %s", self.model_latest.model_name,
                     self.model_latest.model_version)
        logging.info("Corresponding experiment %s", self.model_latest.experiment_id)
        logging.info("Loaded model from checkpoint")

        self.model.summary()

    def test_model_accuracy(self):

        # Load testing data from Pachyderm
        pc = self.connect_pachy()
        test_img_source = pc.get_file(f'{self.PACH_TEST_REPO}/{self.PACH_TEST_BRANCH}', 't10k-images-idx3-ubyte.gz')
        test_label_source = pc.get_file(f'{self.PACH_TEST_REPO}/{self.PACH_TEST_BRANCH}', 't10k-labels-idx1-ubyte.gz')
        with gzip.open(test_label_source, "rb") as lbpath:
            test_labels = np.frombuffer(lbpath.read(), np.uint8, offset=8)
        with gzip.open(test_img_source, "rb") as imgpath:
            test_images = np.frombuffer(imgpath.read(), np.uint8, offset=16).reshape(len(test_labels), 28, 28)

        # transform the images the same way as during training
        test_images = transform(test_images)
        #test_images = test_images / 255

        test_loss, test_acc = self.model.evaluate(test_images, test_labels, verbose=1)

        # write the test results to model metadata
        self.det.get_model(self.MODEL_NAME). \
           add_metadata({"metrics": {"test_accuracy": str(test_acc),
                                      "test_loss": str(test_loss)}})

        # also write the test descriptions to the model checkpoint
        self.checkpoint.add_metadata({"metrics": {"test_accuracy": str(test_acc),
                                                  "test_loss": str(test_loss)}})

        logging.info('Accuracy of the network on the 10000 test images: %.2f', test_acc)
        logging.info('Accuracy threshold set at %.2f', self.ACCURACY_THRESHOLD)

        self.assertTrue(test_acc > self.ACCURACY_THRESHOLD, "Model accuracy lower than threshold")

    def connect_pachy(self):
        connection = None
        try:
            connection = python_pachyderm.Client(host="10.64.140.44", port=650)
        except Exception as error:
            print(error)

        logging.info("Pachyderm connection successful")
        return connection


if __name__ == '__main__':
    unittest.main()
