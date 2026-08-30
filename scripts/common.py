import yaml
from minio import Minio
from pymongo import MongoClient


def load_config(path="config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)

def mongo_db(cfg):
    return MongoClient(cfg["mongo_uri"])[cfg["mongo_db"]]

def minio_client(cfg) -> Minio:
    c = Minio(cfg["minio_endpoint"], access_key=cfg["minio_access_key"],
              secret_key=cfg["minio_secret_key"], secure=False)
    if not c.bucket_exists(cfg["minio_bucket_audio"]):
        c.make_bucket(cfg["minio_bucket_audio"])
    return c
