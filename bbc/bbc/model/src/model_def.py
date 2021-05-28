import tempfile
from typing import Any, Dict, Sequence, Tuple, Union, cast
import torch
from torch import nn
from data import NewsDataset

from determined.pytorch import DataLoader, PyTorchTrial, PyTorchTrialContext

TorchData = Union[Dict[str, torch.Tensor], Sequence[torch.Tensor], torch.Tensor]


def accuracy_rate(predictions: torch.Tensor, labels: torch.Tensor) -> float:
    """Return the accuracy rate based on dense predictions and sparse labels."""
    assert len(predictions) == len(labels), "Predictions and labels must have the same length."
    assert len(labels.shape) == 1, "Labels must be a column vector."

    return (  # type: ignore
        float((predictions.argmax(1) == labels.to(torch.long)).sum()) / predictions.shape[0]
    )


class BBCTrial(PyTorchTrial):
    def __init__(self, context: PyTorchTrialContext) -> None:
        self.context = context

        # Create a unique download directory for each rank so they don't overwrite each
        # other when doing distributed training.
        self.download_directory = tempfile.mkdtemp()

        self.model = self.context.wrap_model(nn.Sequential(
            nn.Linear(9474, self.context.get_hparam("hidden1")),
            nn.LayerNorm(self.context.get_hparam("hidden1")),
            nn.Linear(self.context.get_hparam("hidden1"), 128),
            nn.Dropout(self.context.get_hparam("dropout")),
            nn.Linear(128, 64),
            nn.Linear(64, 5),
        ))

        self.optimizer = self.context.wrap_optimizer(torch.optim.Adam(  # type: ignore
            self.model.parameters(),
            lr=self.context.get_hparam("learning_rate"),
        ))

    def train_batch(
        self, batch: TorchData, epoch_idx: int, batch_idx: int
    ) -> Dict[str, torch.Tensor]:
        batch = cast(Tuple[torch.Tensor, torch.Tensor], batch)
        data, labels = batch

        output = self.model(data)
        loss = torch.nn.functional.cross_entropy(output, labels)
        accuracy = accuracy_rate(output, labels)

        self.context.backward(loss)
        self.context.step_optimizer(self.optimizer)
        return {"loss": loss, "train_error": 1.0 - accuracy, "train_accuracy": accuracy}

    def evaluate_batch(self, batch: TorchData) -> Dict[str, Any]:
        """
        Calculate validation metrics for a batch and return them as a dictionary.
        This method is not necessary if the user defines evaluate_full_dataset().
        """
        batch = cast(Tuple[torch.Tensor, torch.Tensor], batch)
        data, labels = batch

        output = self.model(data)
        accuracy = accuracy_rate(output, labels)
        return {"validation_accuracy": accuracy, "validation_error": 1.0 - accuracy}

    def build_training_data_loader(self) -> Any:
        data_config = self.context.get_data_config()
        train_set = NewsDataset(mode='train',
                                     label_source_bucket=data_config["source"],
                                     branch=data_config["branch"])
        train_loader = DataLoader(train_set, batch_size=self.context.get_per_slot_batch_size())
        return train_loader

    def build_validation_data_loader(self) -> Any:
         data_config = self.context.get_data_config()
         validation_set = NewsDataset(mode='validate',
                                      label_source_bucket=data_config["source"],
                                      branch=data_config["branch"])
         validation_loader = DataLoader(validation_set, batch_size=self.context.get_per_slot_batch_size())
         return validation_loader

