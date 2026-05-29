import json
import re
from pathlib import Path
from collections import Counter

INPUT_FILE = Path("processed_data/normalized_recipes.json")
OUTPUT_FILE = Path("processed_data/cuisine_catalog.json")


CUISINE_RULES = {
    "South Indian": [
        "dosa", "idli", "vada", "uttapam", "sambar",
        "rasam", "upma", "pongal", "coconut chutney",
        "puliogare", "bisi bele bath"
    ],

    "Punjabi": [
        "paneer", "chole", "rajma", "dal makhani",
        "bhatura", "sarson", "makki", "lassi"
    ],

    "Gujarati": [
        "thepla", "dhokla", "khandvi",
        "handvo", "undhiyu", "khaman"
    ],

    "Rajasthani": [
        "dal baati", "baati", "gatte",
        "ker sangri", "laal maas"
    ],

    "Bengali": [
        "posto", "shorshe", "macher",
        "ilish", "cholar dal", "sandesh"
    ],

    "Maharashtrian": [
        "poha", "misal", "vada pav",
        "sabudana", "puran poli",
        "kolhapuri", "thalipeeth"
    ],

    "Kerala": [
        "appam", "puttu", "avial",
        "thoran", "coconut milk"
    ],

    "Andhra": [
        "gongura", "pulusu",
        "pachadi", "avakaya",
        "ulavacharu"
    ],

    "Karnataka": [
        "mysore", "neer dosa",
        "ragi", "akki roti",
        "bisi bele bath"
    ]
}


def normalize_text(text):
    if text is None:
        return ""

    text = str(text).lower()
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def build_search_text(recipe):

    chunks = []

    chunks.append(normalize_text(recipe.get("title")))

    ingredients = recipe.get("ingredients", [])
    if isinstance(ingredients, list):
        chunks.extend(normalize_text(x) for x in ingredients)

    cuisine_tags = recipe.get("cuisine_tags", [])
    if isinstance(cuisine_tags, list):
        chunks.extend(normalize_text(x) for x in cuisine_tags)

    return " ".join(chunks)


def classify_recipe(recipe):

    text = build_search_text(recipe)

    scores = {}
    matched = {}

    for cuisine, keywords in CUISINE_RULES.items():

        score = 0
        hits = []

        for keyword in keywords:

            if keyword in text:
                score += 1
                hits.append(keyword)

        scores[cuisine] = score
        matched[cuisine] = hits

    best_cuisine = max(scores, key=scores.get)

    best_score = scores[best_cuisine]

    if best_score == 0:
        return {
            "primary_cuisine": "Indian",
            "confidence": 0.10,
            "matched_keywords": []
        }

    confidence = min(1.0, best_score / 5)

    return {
        "primary_cuisine": best_cuisine,
        "confidence": round(confidence, 2),
        "matched_keywords": matched[best_cuisine]
    }


def main():

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        recipes = json.load(f)

    cuisine_counter = Counter()

    classified_recipes = []

    for recipe in recipes:

        result = classify_recipe(recipe)

        cuisine_counter[result["primary_cuisine"]] += 1

        classified_recipes.append({
            "recipe_id": recipe.get("recipe_id"),
            "title": recipe.get("title"),
            "source_url": recipe.get("source_url"),
            "primary_cuisine": result["primary_cuisine"],
            "confidence": result["confidence"],
            "matched_keywords": result["matched_keywords"]
        })

    output = {
        "total_recipes": len(recipes),
        "cuisine_counts": dict(cuisine_counter),
        "classified_recipes": classified_recipes
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print()
    print("=" * 50)
    print("CUISINE CLASSIFICATION SUMMARY")
    print("=" * 50)

    for cuisine, count in cuisine_counter.most_common():
        print(f"{cuisine:<20} {count}")

    print()
    print(f"Saved -> {OUTPUT_FILE}")


if __name__ == "__main__":
    main()