import json
import shutil
import os
import logging
import numpy as np

# give all files a unique ID within their filename, without changing file location
SOURCE_PATH = "/Users/janoschbaltensperger/Desktop/bbc"
DEST_PATH = "/Users/janoschbaltensperger/Desktop/bbc-enum"
i = 1
for dirpath, dirs, files in os.walk(SOURCE_PATH, topdown=True):
    for file in sorted(files):
        ext = os.path.splitext(file)[-1].lower()
        id = os.path.splitext(file)[0].lower()
        _, label = os.path.split(dirpath)
        if (ext == ".txt") & (id != "readme"):
            print(os.path.join(dirpath, file), os.path.join(DEST_PATH, f'{label}/{i}.txt'))
            os.makedirs(os.path.join(DEST_PATH, label), exist_ok=True)
            shutil.copyfile(os.path.join(dirpath, file), os.path.join(DEST_PATH, f'{label}/{i}.txt'))
            print(i)
            i += 1
        else:
            print("invalid file: " + file)




