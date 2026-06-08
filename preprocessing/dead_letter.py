import json
from pathlib import Path
from datetime import datetime

DEAD_LETTER_FILE = Path("quarantine/dead_letter/dead_letter.json")

def send_to_dead_letter(raw_record, error_message):
DEAD_LETTER_FILE.parent.mkdir(parents=True, exist_ok=True)


payload = {
    "timestamp": datetime.utcnow().isoformat(),
    "error": str(error_message),
    "record": raw_record,
}

existing = []

if DEAD_LETTER_FILE.exists():
    try:
        with open(DEAD_LETTER_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)
    except Exception:
        existing = []

existing.append(payload)

with open(DEAD_LETTER_FILE, "w", encoding="utf-8") as f:
    json.dump(existing, f, indent=2, ensure_ascii=False)

