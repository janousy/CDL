"""
This files mimics keras.dataset download's function.

For parallel and distributed training, we need to account
for multiple processes (one per GPU) per agent.

For more information on data in Determined, read our data-access tutorial.
"""

import gzip
import python_pachyderm
import numpy as np
import logging

def connect_to_pachyderm(data_config):
    pachyderm_host = data_config['pachyderm']['host']
    pachyderm_port = data_config['pachyderm']['port']

    logging.info("Connecting to Pachyderm at: %s:%s", pachyderm_host, pachyderm_port)
    pc = python_pachyderm.Client(host=pachyderm_host, port=pachyderm_port)
    return pc


def load_training_data(self):
    data_config = self.context.get_data_config()
    pc = connect_to_pachyderm(data_config)

    repo = data_config['pachyderm']['repo']
    branch = data_config['pachyderm']['branch']

    sources = []
    files = []

    logging.info("loading train labels: " + data_config['pachyderm']['sources']['train-labels'])
    logging.info("loading train images: " + data_config['pachyderm']['sources']['train-images'])
    files.append(data_config['pachyderm']['sources']['train-labels'])
    files.append(data_config['pachyderm']['sources']['train-images'])

    for file in files:
        sources.append(pc.get_file(f'{repo}/{branch}', file))

    with gzip.open(sources[0], "rb") as lbpath:
        train_labels = np.frombuffer(lbpath.read(), np.uint8, offset=8)

    with gzip.open(sources[1], "rb") as imgpath:
        train_images = np.frombuffer(imgpath.read(), np.uint8, offset=16).reshape(len(train_labels), 28, 28)

    data_size = train_images.shape
    split = int(data_size[0] * 0.8)
    train_img = train_images[:split]
    train_lb = train_labels[:split]
    val_img = train_images[split:]
    val_lb = train_labels[split:]

    return train_img, train_lb, val_img, val_lb

def transform(data):
    tf_data = data / 255.00
    return tf_data

