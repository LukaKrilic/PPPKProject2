import argparse
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests
from common import load_config, minio_client, mongo_db

AUDIO_EXT = {".wav", ".mp3", ".flac", ".ogg"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio-dir", default=None)
    args = ap.parse_args()

    cfg = load_config()
    audio_dir = args.audio_dir or cfg["audio_dir"]
    db = mongo_db(cfg)
    mc = minio_client(cfg)
    audio_col, cls_col, species = db["audio_files"], db["classifications"], db["species"]
    loc = cfg["audio_location"]

    for path in sorted(Path(audio_dir).iterdir()):
        if path.suffix.lower() not in AUDIO_EXT:
            continue
        if audio_col.find_one({"filename": path.name}):
            print(f"skip (already processed): {path.name}")
            continue

        object_key = f"{uuid.uuid4()}-{path.name}"
        mc.fput_object(cfg["minio_bucket_audio"], object_key, str(path))

        audio_id = audio_col.insert_one({
            "filename": path.name,
            "minio_bucket": cfg["minio_bucket_audio"],
            "minio_key": object_key,
            "location": loc,
            "uploaded_at": datetime.now(timezone.utc),
        }).inserted_id

        with open(path, "rb") as f:
            resp = requests.post(f"{cfg['aves_base_url']}/api/classify",
                                 files={"file": (path.name, f)}, timeout=120)
        resp.raise_for_status()

        detections = resp.json().get("results", [])
        for det in detections:
            sp = species.find_one({"canonicalName": det.get("scientific_name")})
            cls_col.insert_one({
                "audio_file_id": audio_id,
                "minio_key": object_key,
                "species_key": sp["key"] if sp else None,
                "scientific_name": det.get("scientific_name"),
                "common_name": det.get("common_name"),
                "confidence": det.get("confidence"),
                "start_time": det.get("start_time"),
                "end_time": det.get("end_time"),
                "location": loc,
                "classified_at": datetime.now(timezone.utc),
            })
        print(f"processed {path.name} ({len(detections)} detections)")


if __name__ == "__main__":
    main()