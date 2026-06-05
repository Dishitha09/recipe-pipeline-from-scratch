import json
from urllib.parse import urlparse
from collections import Counter

with open("data/final_recipes.json", encoding="utf-8") as f:
    data = json.load(f)

counter = Counter()

for record in data:
    url = record.get("raw_content", {}).get("source_url", "")
    if url:
        counter[urlparse(url).netloc] += 1

print("\nRECIPE COUNT BY DOMAIN")
print("=" * 50)

for domain, count in counter.most_common():
    print(f"{domain:<40} {count}")

print("=" * 50)
print("Total recipes:", sum(counter.values()))