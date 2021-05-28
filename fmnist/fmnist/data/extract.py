# TensorFlow and tf.keras
import tensorflow as tf
import json
import numpy as np
import matplotlib.pyplot as plt
import os
from PIL import Image
import python_pachyderm
import gzip
import tempfile

print(tf.__version__)
repo = "fmnist-prep"
branch = "master"
pachyderm_host = "10.1.180.218"
pachyderm_port = "650"

client = python_pachyderm.Client(host="172.23.76.93", port=30650)
download_directory = tempfile.mkdtemp()

files = [
    "train-labels-idx1-ubyte.gz",
    "train-images-idx3-ubyte.gz",
]
sources = []
paths=[]
for file in files:
    sources.append(client.get_file(f'{repo}/{branch}', file))
    print(file)

print(sources)
# for dir in client.walk_file((repo, branch), "/"):
#     paths.append(dir.file.path)
#     fpath = os.path.join(download_directory, dir.file.path)
#     sources.append(client.get_file(f'{repo}/{branch}', fpath))


#with gzip.open("/Users/janoschbaltensperger/repos/fmnist-data/prep/train-labels-idx1-ubyte.gz", "rb") as lbpath:
with gzip.open(sources[0], "rb") as lbpath:
    train_labels = np.frombuffer(lbpath.read(), np.uint8, offset=8)
    print(train_labels.shape)

with gzip.open(sources[1], "rb") as imgpath:
    train_images = np.frombuffer(imgpath.read(), np.uint8, offset=16).reshape(len(train_labels), 28, 28)
    print(train_images.shape)

data_size = train_images.shape
split = int(data_size[0] * 0.8)
x_train = train_images[:split]
y_train = train_labels[:split]
x_val = train_images[split:]
y_val = train_labels[split:]

print(x_train.shape)
print(y_train.shape)
print(x_val.shape)
print(y_val.shape)

# (train_images, train_labels), (test_images, test_labels) = fashion_mnist.load_data()
# class_names = ['T-shirt/top', 'Trouser', 'Pullover', 'Dress', 'Coat',
#                'Sandal', 'Shirt', 'Sneaker', 'Bag', 'Ankle boot']

# train_images = x_train[100:]
# train_labels = y_train[100:]

#print(test_images[0])
# print(test_labels[0])
# print(class_names[test_labels[0]])
# print
# plt.figure()
# plt.imshow(test_images[0])
# plt.colorbar()
# plt.grid(False)
# plt.show()

# json_file = open('test-label.json', "r")
# ls_data = json.loads(json_file.read())
#
# print(ls_data["result"][0])
# label_choice = ls_data["result"][0]["value"]["choices"][0]
# label_id = class_names.index(label_choice)
# print(label_id)
#
# image_path = ls_data["task"]["data"]["image"]
# print(image_path)
#
# _, image_id = os.path.split(image_path)
# image = Image.open(os.path.join('/Users/janoschbaltensperger/repos/fmnist-data/images/', image_id))
# print(image.size)




# i = 0
# for test_image in test_images:
#     img = Image.fromarray(test_image)
#     img.save(f'{i}' + '.png')
#     i += 1

# i = 0
# for test_image in test_images:
#     img = Image.fromarray(test_image)
#     img.save(f'{i}' + '.png')
#     i += 1