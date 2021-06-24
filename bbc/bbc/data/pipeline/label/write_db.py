import argparse
import pathlib
import psycopg2
from psycopg2 import sql
import json
import os
import logging
from urllib.parse import urlparse
logging.basicConfig(level=logging.INFO)

"""
This script writes the labels exported from LabelStudio into a Pachyderm repository in to a Postgres table
Assuming the labels are in LabelStudio JSON export format
Secrets are currently not handled as this prototype is for demonstration purposes
"""
def write_label_to_db(cursor, args, file):
    # load label in json format and extract values
    file_label = open(file)
    json_label = json.load(file_label)
    label_id = json_label["id"]
    label = json_label["annotations"][0]["result"][0]["value"]["choices"]
    file_path = json_label["data"]["text"]
    label_date = json_label["created_at"]
    creator = json_label["annotations"][0]["completed_by"]["email"]

    # current workaround, as this info cannot be extracted from pachyderm
    branch = urlparse(file_path).netloc

    try:
        # the following query either inserts a new label with metadata, or updates if the label by id already exists
        # TODO: instead of checking the --test argument, try to fix placeholder: https://www.psycopg.org/docs/sql.html
        if args.test:
            query = sql.SQL("""INSERT INTO bbc_test("label_id", "label", "filepath", "creator_mail", "label_create_date", "branch")
                                            VALUES (%s, %s, %s, %s, %s, %s)
                                            ON CONFLICT ("label_id") DO UPDATE SET
                                            ("label", "filepath", "creator_mail", "label_create_date", "branch")
                                             = (EXCLUDED."label",
                                                 EXCLUDED."filepath",
                                                  EXCLUDED."creator_mail",
                                                   EXCLUDED."label_create_date",
                                                    EXCLUDED."branch");
                                        """)
        else:
            query = sql.SQL("""INSERT INTO bbc_train("label_id", "label", "filepath", "creator_mail", "label_create_date", "branch")
                                            VALUES (%s, %s, %s, %s, %s, %s)
                                            ON CONFLICT ("label_id") DO UPDATE SET
                                            ("label", "filepath", "creator_mail", "label_create_date", "branch")
                                             = (EXCLUDED."label",
                                                 EXCLUDED."filepath",
                                                  EXCLUDED."creator_mail",
                                                   EXCLUDED."label_create_date",
                                                    EXCLUDED."branch");
                                        """)

        cursor.execute(query, (label_id, label, file_path, creator, label_date, branch))

    except (Exception, psycopg2.Error) as error:
        print("Failed: ", error)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--inputpath', type=pathlib.Path, required=True)
    parser.add_argument('--test', action="store_true")
    args = parser.parse_args()

    print(args.test)
    logging.info(f'input-path: {args.inputpath}')

    try:
        # TODO: add secrets for postgres credentials
        connection = psycopg2.connect(user="postgres",
                                      password="postgres",
                                      host="172.23.76.93",
                                      port="5432",
                                      database="bbc-news")

        cursor = connection.cursor()
        print("successfully connected to db")

        # for each json file from the input repo, write to the db
        for dirpath, dirs, files in os.walk(args.inputpath):
            for file in files:
                logging.info(file)
                ext = os.path.splitext(file)[-1].lower()
                # to prevent errors, we only allow json
                # however we do not check if the json has the correct format from labelstudio
                if ext == ".json":
                    logging.info(f'writing file: {os.path.join(dirpath, file)}')
                    write_label_to_db(cursor, args, os.path.join(dirpath, file))
                else:
                    logging.info("invalid label: ", file)

    except (Exception, psycopg2.Error) as error:
        print("Failed: ", error)

    finally:
        # closing database connection.
        if connection:
            connection.commit()
            connection.close()
            print("PostgreSQL connection is closed")
