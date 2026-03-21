"""Update file_path in MongoDB to use new dataset/ folder structure."""
import sys, os, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from audio_service.db.mongo_client import get_collection

ROOT = Path(__file__).resolve().parent.parent

INSTRUMENT_FOLDER = {
    "clarinet": "clarinet",
    "flute": "flute",
    "saxophone": "saxophone",
    "trumpet": "trumpet",
}

col = get_collection()
docs = list(col.find({}, {"_id": 1, "file_name": 1, "instrument": 1}))
print(f"Updating {len(docs)} documents...")

updated = 0
for doc in docs:
    instrument = doc.get("instrument", "")
    file_name = doc.get("file_name", "")
    folder = INSTRUMENT_FOLDER.get(instrument, instrument)
    new_path = str(ROOT / "dataset" / folder / file_name)
    col.update_one({"_id": doc["_id"]}, {"$set": {"file_path": new_path}})
    updated += 1

print(f"Updated {updated} documents with new file_path.")
