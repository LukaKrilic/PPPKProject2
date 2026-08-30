import requests
from common import load_config, mongo_db
from pymongo import ASCENDING
from pymongo.errors import BulkWriteError


def main():
    cfg = load_config()
    db = mongo_db(cfg)
    col = db["species"]

    if col.estimated_document_count() > 0:
        print("Species collection already populated. Skipping fetch.")
        return

    col.create_index([("key", ASCENDING)], unique=True)

    r = requests.get(cfg["taxonomy_url"], timeout=60)
    r.raise_for_status()
    items = r.json()

    try:
        col.insert_many(items, ordered=False)
    except BulkWriteError:
        pass

    stored = col.count_documents({})
    print(f"Stored {stored} species")

if __name__ == "__main__":
    main()