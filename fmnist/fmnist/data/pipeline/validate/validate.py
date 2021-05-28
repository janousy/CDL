import os
import gzip
import numpy as np
import shutil
import argparse
import pathlib
import logging
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir', type=pathlib.Path, required=True)
    parser.add_argument('--label', type=str, required=True)
    parser.add_argument('--data', type=str, required=True)
    args = parser.parse_args()

    label_path = os.path.join(args.dir, args.label)
    data_path = os.path.join(args.dir, args.data)
    try:
        with gzip.open(label_path, "rb") as lbpath:
            train_labels = np.frombuffer(lbpath.read(), np.uint8, offset=8)
            print(train_labels)

        with gzip.open(data_path, "rb") as imgpath:
            train_images = np.frombuffer(imgpath.read(), np.uint8, offset=16).reshape(len(train_labels), 28, 28)
            print(train_images)

        shutil.copy(label_path, os.path.join("/pfs/out", args.label))
        shutil.copy(data_path, os.path.join("/pfs/out", args.data))

    except Exception as error:
        logging.info(error)

# python validate.py
# --dir /Users/janoschbaltensperger/Desktop/fmnist-train-raw
# --label train-labels-idx1-ubyte.gz
# --data train-images-idx3-ubyte.gz