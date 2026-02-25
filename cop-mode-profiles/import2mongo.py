import argparse
import gzip
import json
import os
import sys
from pathlib import Path
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path
import getpass
from urllib.parse import quote_plus


def read_gz_json(path):
    with gzip.open(path, 'r') as f:
        try:
            data = json.load(f)
        except EOFError as e:
            print(f"Failed to read file {path}, treating as empty data. Error: {e}")
            return []
    return data


def get_mongo_client():
    dotenv_path = Path(__file__).parent.joinpath('.env')
    load_dotenv(dotenv_path)
    mongo_user = os.environ.get("MONGO_USER")
    mongo_password = os.environ.get("MONGO_PWD")
    mongo_host = os.environ.get("MONGO_HOST")

    if not mongo_user or not mongo_password:
        print("Mongo user not found in MONGO_USER and MONGO_PWD environment variables...")
        mongo_user = input('Insert mongo user: ')
        mongo_password = getpass.getpass('Insert mongo user password: ')

    if not mongo_host:
        mongo_host = input("Insert mongo host: [localhost:27017] ") or "localhost:27017"

    mongo_uri = "mongodb://%s:%s@%s" % (quote_plus(mongo_user), quote_plus(mongo_password), mongo_host)
    return MongoClient(mongo_uri)


def fill_data(db, datapath_root):
    print(f"Looking for files in: {datapath_root.resolve()}")
    count_total = 0
    for file_path in datapath_root.rglob('*.json.gz'):
        print(f"Reading file: {file_path.name}")
        data = read_gz_json(file_path)
        if data:
            result = db.data.insert_many(data)
            print(f"✔ Inserted {len(result.inserted_ids)} documents from {file_path.name}")
            count_total += len(result.inserted_ids)
        else:
            print(f"⚠ No data found in {file_path.name}")
    print(f"Total documents inserted: {count_total}")



if __name__ == '__main__':
    datapath_root = Path(__file__).parent.joinpath('data')

    confirmed = input("Continuing with this script will delete and repopulate the DB cop_mode. "
                      "Are you sure you want to continue? (y to continue) ")
    if confirmed != 'y':
        print("Aborted...")
        sys.exit()

    client = get_mongo_client()
    db = client.cop_mode # DB used is cop_mode

    db.data.drop()
    print('Loading files to mongoDB. This can take a few minutes...')
    fill_data(db, datapath_root)
    print('Done.')
