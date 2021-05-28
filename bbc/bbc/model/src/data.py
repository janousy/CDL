from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
import logging
import python_pachyderm
import torch
from torch.utils.data import Dataset
import psycopg2
from psycopg2 import sql
from urllib.parse import urlparse
import pandas as pd
from nltk.stem import PorterStemmer

def connect_pachy():
    connection = None
    try:
        connection = python_pachyderm.Client(host="10.64.140.44", port=650)
    except Exception as error:
        logging.info(error)

    logging.info("Pachyderm connection successful")
    return connection


def connect_postgres():
    connection = None
    try:
        # TODO: add secrets for postgres credentials
        connection = psycopg2.connect(user="postgres",
                                      password="postgres",
                                      host="172.23.76.93",
                                      port="5432",
                                      database="bbc-news")
    except (Exception, psycopg2.DatabaseError) as error:
        logging.info(error)
    logging.info("Database connection successful")
    return connection


class NewsDataset(Dataset):
    vectorizer = None
    label_encoder = None

    train_query = sql.SQL("SELECT label_id, label, filepath FROM bbc_train WHERE branch = %s ORDER BY label_id")
    test_query = sql.SQL("SELECT label_id, label, filepath FROM bbc_test WHERE branch = %s ORDER BY label_id")

    # train branch repo, test branch repo
    def __init__(self, mode: str = 'train',
                 label_source_bucket: str = 'bbc-train-validate',
                 branch: str = "master"):

        self.bucket = f'{branch}.{label_source_bucket}'

        # define the labeling encoding
        le = LabelEncoder()
        bbc_classes = pd.read_csv("bbc.classes", header=None)
        logging.info(bbc_classes.iloc[:, 0].values.astype('U'))
        le.fit(bbc_classes.iloc[:, 0].values.astype('U'))
        self.le = le

        # define the text vectorizer
        voc = pd.read_csv("bbc.vocab", header=None)
        stemmer = PorterStemmer()

        def stemmed_words(doc):
            st = [stemmer.stem(w) for w in analyzer(doc)]
            return st

        analyzer = CountVectorizer().build_analyzer()
        stem_vectorizer = CountVectorizer(analyzer=stemmed_words)
        stem_vectorizer.fit(voc.iloc[:, 0].values.astype('U'))
        logging.info(f'Fitted vectorizer with feature length {len(stem_vectorizer.get_feature_names())}')
        self.vectorizer = stem_vectorizer

        if mode == 'train':
            train_x, val_x, train_y, val_y = self.load_train_dataset()
            self.data_frame = train_x
            self.labels = train_y
        elif mode == 'validate':
            train_x, val_x, train_y, val_y = self.load_train_dataset()
            self.data_frame = val_x
            self.labels = val_y

        elif mode == 'test':
            test_x, test_y = self.load_test_dataset()
            self.data_frame = test_x
            self.labels = test_y
        else:
            logging.info('invalid mode')

        logging.info("Dataset generated")
        logging.info(f'Dataset size in mode {mode}: {self.data_frame.shape}, labels {self.labels.shape}')

    def load_train_dataset(self):
        logging.info("Loading training data and labels..")
        train_df = self.get_data_set(self.train_query, self.bucket)
        logging.info("Data loaded")
        logging.info("Splitting data")
        train_x_df, val_x_df, train_y_df, val_y_df = train_test_split(train_df['text'], train_df['label'],
                                                                      test_size=0.2, random_state=42)

        train_y = self.le.transform(train_y_df)
        val_y = self.le.transform(val_y_df)

        train_x = self.vectorizer.transform(train_x_df)
        val_x = self.vectorizer.transform(val_x_df)

        train_x = torch.tensor(train_x.toarray()).float()
        train_y = torch.tensor(train_y)
        val_x = torch.tensor(val_x.toarray()).float()
        val_y = torch.tensor(val_y)

        return train_x, val_x, train_y, val_y

    def load_test_dataset(self):
        logging.info("Loading test data and labels..")
        test_df = self.get_data_set(self.test_query, self.bucket)
        logging.info("Data loaded")

        test_y = self.le.transform(test_df['label'])
        test_x = self.vectorizer.transform(test_df['text'])
        test_y = torch.tensor(test_y)
        test_x = torch.tensor(test_x.toarray()).float()

        return test_x, test_y

    def __len__(self):
        return len(self.data_frame)

    def __getitem__(self, idx):
        if torch.is_tensor(idx):
            idx = idx.tolist()
        data = self.data_frame[idx]
        label = self.labels[idx]
        sample = (data, label)
        return sample

    def get_data_set(self, query, bucket):
        pg = connect_postgres()
        cursor = pg.cursor()
        pc = connect_pachy()

        try:
            cursor.execute(query, (bucket,))

        except (Exception, psycopg2.DatabaseError) as error:
            logging.info("Error: %s" % error)
            cursor.close()
            logging.info(error)

        tupples = cursor.fetchall()
        cursor.close()
        pg.close()

        column_names = ["label_id", "label", "filepath"]
        df = pd.DataFrame(tupples, columns=column_names)
        df.insert(len(df.columns), 'text', '')

        try:
            for index, row in df.iterrows():
                url = df.at[index, 'filepath']
                branch, bucket = urlparse(url).netloc.split(".")
                _, file = urlparse(url).path.split("/")
                train_source = pc.get_file(f'{bucket}/{branch}', file)
                text = train_source.read().decode(errors='replace')
                df.at[index, 'text'] = text
                print('\r', f'{index}/{len(df.index)}', end='')

            logging.info(f'Loaded {len(df.index)} files')
            return df

        except Exception as error:
            logging.info(error)

    def get_text_vectorizer(self):
        return self.vectorizer

    def get_label_encoder(self):
        return self.le
