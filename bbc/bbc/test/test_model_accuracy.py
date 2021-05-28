import torch
import logging
from torch.utils.data import DataLoader
from bbc.model.src.data import NewsDataset
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)
import unittest
import shutil
from determined.experimental import Determined
import os

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

class TestModelAccuracy(unittest.TestCase):

    # TODO: adjust the IP according to your Kubernetes Cluster
    DET_MASTER = "http://10.64.140.43:8080"
    MODEL_NAME = "news-classifier"

    # Define the minimum accuracy for the model to pass this test
    ACCURACY_THRESHOLD = 0.8

    def setUp(self):
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        logging.info("Testing model %s for accuracy", self.MODEL_NAME)
        logging.info("Testing accuracy threshold at %f", self.ACCURACY_THRESHOLD.__float__())

        # download model and metadata
        self.det = Determined(master=self.DET_MASTER)
        self.model_latest = self.det.get_model(self.MODEL_NAME).get_version()
        self.trial = self.det.get_trial(self.model_latest.trial_id)
        self.checkpoint = self.trial.select_checkpoint(uuid=self.model_latest.uuid)
        self.model = self.checkpoint.load(map_location=self.device)

        logging.info("Connected to Determined master at %s", self.DET_MASTER)
        logging.info("Loaded model %s version %s", self.model_latest.model_name,
                     self.model_latest.model_version)
        logging.info("Corresponding experiment %s", self.model_latest.experiment_id)
        logging.info("Loaded model from checkpoint")

        # load model dependencies from the corresponding checkpoint
        uuid = self.checkpoint.uuid
        self.checkpoint.download()

        # the test dataset requires the vocabulary and classes in the current working directory
        shutil.copy(f'checkpoints/{uuid}/code/bbc.vocab', os.path.join(os.getcwd(),'bbc.vocab'))
        shutil.copy(f'checkpoints/{uuid}/code/bbc.classes', os.path.join(os.getcwd(), 'bbc.classes'))

    def test_model_accuracy(self):
        # load testing data from the database and pachyderm
        test_ds = NewsDataset(mode='test', label_source_bucket='bbc-test-validate', branch='master')
        test_loader = DataLoader(test_ds)

        correct = 0
        total = 0
        # since we're not training, we don't need to calculate the gradients for our outputs
        with torch.no_grad():
            for data in test_loader:
                texts, labels = data
                # calculate outputs by running the texts through the network
                outputs = self.model.model(texts)
                # the class with the highest energy is what we choose as prediction
                _, predicted = torch.max(outputs.data, 1)
                correct += (predicted == labels).sum().item()
                total += 1

        test_acc = correct / total
        # write the test results to model metadata
        self.det.get_model(self.MODEL_NAME). \
            add_metadata({"metrics": {"test_accuracy": str(test_acc)}})

        # also write the test results to the model checkpoint
        self.checkpoint.add_metadata({"metrics": {"test_accuracy": str(test_acc)}})

        logging.info('Accuracy threshold set at %.2f', self.ACCURACY_THRESHOLD)
        logging.info('Accuracy of the mode: %.2f', test_acc)

        self.assertTrue(test_acc > self.ACCURACY_THRESHOLD, "Model accuracy lower than threshold")

if __name__ == '__main__':
    unittest.main()
