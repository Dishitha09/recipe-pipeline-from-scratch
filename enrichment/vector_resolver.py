import csv
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

CATALOGUE_FILE = "data/master_ingredients_seed.csv"

model = SentenceTransformer("all-MiniLM-L6-v2")

_catalogue = []
_embeddings = None


def load_catalogue():
    global _catalogue
    global _embeddings

    if _catalogue:
        return

    names = []

    with open(CATALOGUE_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            _catalogue.append(
                {
                    "ingredient_id": row["ingredient_id"],
                    "canonical_name": row["canonical_name"],
                }
            )

            names.append(row["canonical_name"])

    print(f"Loaded {len(_catalogue)} catalogue entries")

    _embeddings = model.encode(
        names,
        normalize_embeddings=True,
        show_progress_bar=True,
    )


def resolve_by_vector(name: str):
    load_catalogue()

    query_embedding = model.encode(
        [name],
        normalize_embeddings=True,
    )

    scores = cosine_similarity(
        query_embedding,
        _embeddings,
    )[0]

    best_idx = scores.argmax()
    best_score = float(scores[best_idx])

    print(f"QUERY: {name}")
    print(
        f"BEST MATCH: {_catalogue[best_idx]['canonical_name']} SCORE: {round(best_score, 4)}"
    )

    if best_score < 0.50:
        return None

    return {
        "ingredient_id": _catalogue[best_idx]["ingredient_id"],
        "canonical_name": _catalogue[best_idx]["canonical_name"],
        "resolution_type": "vector",
        "score": round(best_score, 4),
    }


if __name__ == "__main__":
    tests = [
        "haldi powder",
        "gehun atta",
        "cilantro leaves",
        "ghee",
        "jeera powder",
    ]

    for item in tests:
        print(resolve_by_vector(item))
        print("-" * 50)