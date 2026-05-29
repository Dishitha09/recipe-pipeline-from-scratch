import json
from urllib.parse import urlsplit, urlunsplit

INPUT_FILE = "tracking/url_registry.json"

def canonicalize(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, ""))

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

clean = {}
duplicates_removed = 0

for row in data:
    url = canonicalize(row["url"])
    if url in clean:
        duplicates_removed += 1
        continue
    row["url"] = url
    clean[url] = row

clean_data = list(clean.values())

with open(INPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(clean_data, f, indent=2, ensure_ascii=False)

print(f"Original URLs      : {len(data)}")
print(f"Clean URLs         : {len(clean_data)}")
print(f"Duplicates Removed : {duplicates_removed}")