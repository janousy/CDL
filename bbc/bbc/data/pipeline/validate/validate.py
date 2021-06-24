import os
import logging
import shutil
import sys
import argparse
import pathlib
logging.basicConfig(level=logging.INFO)

"""
This script cleans and validates news articles from the bbc data set.
The data is not tested per se.
- cleaning: ensure UTF-8 encoding
- validation: minimum character length and TXT file format
"""

MIN_NEWS_LENGTH = 20
def validate(file):
    tail = os.path.split(file)[1]
    try:
        input = open(file, "rb").read()
        text = input.decode("utf-8", "replace")
        if len(text) > MIN_NEWS_LENGTH:
            shutil.copy(file, os.path.join("/pfs/out", tail))
        else:
            logging.info(file + " discarded as not meeting requirements")
    except OSError as error:
        logging.info(error, file)
        sys.exit(error)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--inputpath', type=pathlib.Path, required=True)

    args = parser.parse_args()
    logging.info(args.inputpath)

    nr_processed = 0
    total = 0
    for dirpath, dirs, files in os.walk(args.inputpath):
        total = len(files)
        for file in sorted(files):
            logging.info(file)
            ext = os.path.splitext(file)[-1].lower()
            if ext == ".txt":
                validate(os.path.join(dirpath, file))
                nr_processed += 1
            else:
                logging.info(file + ": invalid file type")
        logging.info(f'processed {nr_processed} of {total} files')