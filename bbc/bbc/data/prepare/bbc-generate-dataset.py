import os
import numpy as np
import shutil
import json

# The source of the raw dataset: http://mlg.ucd.ie/files/datasets/bbc-fulltext.zip
# More information about the dataset here: http://mlg.ucd.ie/datasets/bbc.html

# TODO: set these paths accordingly
# ROOT: the directory where the test and train set incl. labels will be stored
# SOURCE_PATH: directory of the downloaded and extracted data set
# LABELSTUDIO_TEMPLATE: The template file for labels, supported by label studio

ROOT = "/Users/janoschbaltensperger/Desktop/"
SOURCE_PATH = "/Users/janoschbaltensperger/Desktop/bbc"
LABELSTUDIO_TEMPLATE = "/Users/janoschbaltensperger/repos/gitlab/cdl-pipe/bbc/data/ls-template.json"

SOURCE_ENUM_PATH = os.path.join(ROOT, "bbc-enum")
SOURCE_LABEL_PATH = os.path.join(ROOT, "bbc-labels")
DEST_TRAIN_PATH = os.path.join(ROOT, "bbc-train-raw")
DEST_TEST_PATH = os.path.join(ROOT, "bbc-test-raw")
TEST_LABEL_PATH = os.path.join(ROOT, "bbc-test-label")
TRAIN_LABEL_PATH = os.path.join(ROOT, "bbc-train-label")
LABELSTUDIO_TEST_SOURCE_BUCKET = "s3://master.bbc-test-validate"
LABELSTUDIO_TRAIN_SOURCE_BUCKET = "s3://master.bbc-train-validate"

os.makedirs(SOURCE_ENUM_PATH, exist_ok=True)
os.makedirs(DEST_TEST_PATH, exist_ok=True)
os.makedirs(DEST_TRAIN_PATH, exist_ok=True)
os.makedirs(TEST_LABEL_PATH, exist_ok=True)
os.makedirs(TRAIN_LABEL_PATH, exist_ok=True)

# generate unique file IDs for each news source as source IDs are only unique per category
# with unique Ids, we can generate labels with recoverable file paths
i = 1
for dirpath, dirs, files in os.walk(SOURCE_PATH, topdown=True):
    for file in sorted(files):
        ext = os.path.splitext(file)[-1].lower()
        id = os.path.splitext(file)[0].lower()
        _, label = os.path.split(dirpath)
        if (ext == ".txt") & (id != "readme"):
            # copy the renamed file with unique ID to the merge directory
            print(os.path.join(dirpath, file), os.path.join(SOURCE_ENUM_PATH, f'{label}/{i}.txt'))
            os.makedirs(os.path.join(SOURCE_ENUM_PATH, label), exist_ok=True)
            shutil.copyfile(os.path.join(dirpath, file), os.path.join(SOURCE_ENUM_PATH, f'{label}/{i}.txt'))
            print(i)
            i += 1
        else:
            print("invalid file: " + file)


# create an array from the enumerated files
news = []
for dirpath, dirs, files in os.walk(SOURCE_ENUM_PATH, topdown=True):
    for file in sorted(files):
        ext = os.path.splitext(file)[-1].lower()
        if (ext == ".txt"):
            news.append(os.path.join(dirpath, file))

# split the articles into train and test sets, using a standard ratio
np_news = np.array(news)
split = round(np_news.size * 0.8)
print(np_news.size)
np.random.shuffle(np_news)
trainset, testset = np_news[:split], np_news[split:]


# for each dataset, create source directories and labels
# labels are generated using a template JSON file retrieved from LabelStudio
print(f'generate test set of size: {testset.size}')
for test in testset:
    # retrieve metadata from path
    dirpath, filename = os.path.split(test)
    ext = os.path.splitext(filename)[-1].lower()
    _, label = os.path.split(dirpath)
    file_id = os.path.splitext(filename)[0].lower()
    print(filename, label, ext, file_id)
    shutil.copy(LABELSTUDIO_TEMPLATE, f'{TEST_LABEL_PATH}/{file_id}.json')

    # create the corresponding label
    new_label = open(f'{TEST_LABEL_PATH}/{file_id}.json', "r")
    json_object = json.load(new_label)
    new_label.close()

    json_object["id"] = file_id
    json_object["annotations"][0]["result"][0]["value"]["choices"] = label
    json_object["data"]["text"] = f'{LABELSTUDIO_TEST_SOURCE_BUCKET}/{file_id}{ext}'

    a_file = open(os.path.join(TEST_LABEL_PATH, f'{file_id}.json'), "w")
    json.dump(json_object, a_file)

    a_file.close()
    shutil.copy(test, os.path.join(DEST_TEST_PATH, filename))

print(f'generate train set of size: {trainset.size}')
for train in trainset:
    # retrieve metadata from path
    dirpath, filename = os.path.split(train)
    ext = os.path.splitext(filename)[-1].lower()
    _, label = os.path.split(dirpath)
    file_id = os.path.splitext(filename)[0].lower()
    print(filename, label, ext, file_id)
    shutil.copy(LABELSTUDIO_TEMPLATE, f'{TRAIN_LABEL_PATH}/{file_id}.json')

    # create the corresponding label
    new_label = open(f'{TRAIN_LABEL_PATH}/{file_id}.json', "r")
    json_object = json.load(new_label)
    new_label.close()

    json_object["id"] = file_id
    json_object["annotations"][0]["result"][0]["value"]["choices"] = label
    json_object["data"]["text"] = f'{LABELSTUDIO_TRAIN_SOURCE_BUCKET}/{file_id}{ext}'

    a_file = open(os.path.join(TRAIN_LABEL_PATH, f'{file_id}.json'), "w")
    json.dump(json_object, a_file)

    a_file.close()
    shutil.copy(train, os.path.join(DEST_TRAIN_PATH, filename))