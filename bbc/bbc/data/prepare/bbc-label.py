import json
import shutil
import os
import logging

# create labels for each news text, such that file IDs correspond
# TODO: change these paths accordingly
LABELSTUDIO_TEMPLATE = "/Users/janoschbaltensperger/repos/gitlab/cdl-pipe/bbc/data/ls-template.json"
SOURCE_PATH = "/Users/janoschbaltensperger/Desktop/bbc-enum"
DEST_PATH = "/Users/janoschbaltensperger/Desktop/bbc-labels"
LABELSTUDIO_SOURCE_BUCKET = "s3://master.bbc-news-validate"

os.makedirs(DEST_PATH, exist_ok=True)

for dirpath, dirs, files in os.walk(SOURCE_PATH, topdown=True):
    for file in sorted(files):
        ext = os.path.splitext(file)[-1].lower()
        id = os.path.splitext(file)[0].lower()
        if ext == ".txt":
            print(dirpath)
            _, label = os.path.split(dirpath)

            shutil.copy(LABELSTUDIO_TEMPLATE, f'{DEST_PATH}/{id}.json')

            new_label = open(f'{DEST_PATH}/{id}.json', "r")
            json_object = json.load(new_label)
            new_label.close()

            json_object["id"] = id
            json_object["annotations"][0]["result"][0]["value"]["choices"] = label
            json_object["data"]["text"] = f'{LABELSTUDIO_SOURCE_BUCKET}/{id}{ext}'

            a_file = open(os.path.join(DEST_PATH, f'{id}.json'), "w")
            json.dump(json_object, a_file)

            a_file.close()
            print(json_object)