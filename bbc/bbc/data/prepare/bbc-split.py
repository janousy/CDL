import os
import numpy as np
import shutil
news = []

ROOT = "/Users/janoschbaltensperger/Desktop/"

SOURCE_PATH = os.path.join(ROOT, "bbc-enum")
SOURCE_LABEL_PATH = os.path.join(ROOT, "bbc-labels")

DEST_TRAIN_PATH = os.path.join(ROOT, "bbc-train-raw")
DEST_TEST_PATH = os.path.join(ROOT, "bbc-test-raw")
TEST_LABEL_PATH = os.path.join(ROOT, "bbc-test-label")
TRAIN_LABEL_PATH = os.path.join(ROOT, "bbc-train-label")

os.makedirs(DEST_TEST_PATH, exist_ok=True)
os.makedirs(DEST_TRAIN_PATH, exist_ok=True)
os.makedirs(TEST_LABEL_PATH, exist_ok=True)
os.makedirs(TRAIN_LABEL_PATH, exist_ok=True)

# collect all news articles
for dirpath, dirs, files in os.walk(SOURCE_PATH, topdown=True):
    for file in sorted(files):
        ext = os.path.splitext(file)[-1].lower()
        if (ext == ".txt"):
            news.append(os.path.join(dirpath, file))

# split the articles into train and test sets
np_news = np.array(news)
split = round(np_news.size * 0.8)
print(np_news.size)
np.random.shuffle(np_news)
trainset, testset = np_news[:split], np_news[split:]


# for each dataset, create source directories and labels
print(f'generate test set of size: {testset.size}')
for test in testset:
    print(test)
    _, filename = os.path.split(test)
    print(filename)
    file_id = os.path.splitext(filename)[0].lower()
    print(file_id)
    shutil.copy(test, os.path.join(DEST_TEST_PATH, filename))
    shutil.copy(os.path.join(SOURCE_LABEL_PATH, f'{file_id}.json'), os.path.join(TEST_LABEL_PATH, f'{file_id}.json'))

print(f'generate train set of size: {trainset.size}')
for train in trainset:
    _, filename = os.path.split(train)
    print(filename)
    file_id = os.path.splitext(filename)[0].lower()
    print(file_id)
    shutil.copy(train, os.path.join(DEST_TRAIN_PATH, filename))
    shutil.copy(os.path.join(SOURCE_LABEL_PATH, f'{file_id}.json'), os.path.join(TRAIN_LABEL_PATH, f'{file_id}.json'))