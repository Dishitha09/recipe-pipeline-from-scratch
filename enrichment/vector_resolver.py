import csv
import os
import pickle

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from enrichment.logger import logger
from enrichment.config import CONFIG


CATALOGUE_FILE = CONFIG[
    "catalogue_file"
]

CACHE_FILE = CONFIG[
    "cache_file"
]

MODEL_NAME = CONFIG[
    "embedding_model"
]

VECTOR_THRESHOLD = CONFIG[
    "vector_threshold"
]


model = SentenceTransformer(
    MODEL_NAME
)

_catalogue = []

_embeddings = None


def build_cache():

    global _catalogue
    global _embeddings

    names = []

    with open(
        CATALOGUE_FILE,
        "r",
        encoding="utf-8",
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            _catalogue.append(
                {
                    "ingredient_id":
                        row["ingredient_id"],

                    "canonical_name":
                        row["canonical_name"],
                }
            )

            names.append(
                row["canonical_name"]
            )

    logger.info(
        f"Loaded {len(_catalogue)} catalogue entries"
    )

    logger.info(
        "Building embeddings"
    )

    _embeddings = model.encode(
        names,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    os.makedirs(
        "cache",
        exist_ok=True,
    )

    with open(
        CACHE_FILE,
        "wb",
    ) as f:

        pickle.dump(
            {
                "catalogue":
                    _catalogue,

                "embeddings":
                    _embeddings,
            },
            f,
        )

    logger.info(
        f"Cache saved: {CACHE_FILE}"
    )


def load_catalogue():

    global _catalogue
    global _embeddings

    if _catalogue:
        return

    if os.path.exists(
        CACHE_FILE
    ):

        logger.info(
            "Loading embedding cache"
        )

        with open(
            CACHE_FILE,
            "rb",
        ) as f:

            cache = pickle.load(f)

        _catalogue = cache[
            "catalogue"
        ]

        _embeddings = cache[
            "embeddings"
        ]

        logger.info(
            f"Loaded {_embeddings.shape[0]} cached embeddings"
        )

        return

    build_cache()


def resolve_by_vector(
    name: str,
):

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

    best_score = float(
        scores[best_idx]
    )

    best_match = (
        _catalogue[best_idx][
            "canonical_name"
        ]
    )

    logger.info(
        f"QUERY={name}"
    )

    logger.info(
        f"BEST_MATCH={best_match} SCORE={round(best_score,4)}"
    )

    if best_score < VECTOR_THRESHOLD:

        logger.warning(
            f"Rejected vector match for {name}"
        )

        return None

    logger.info(
        f"Accepted vector match for {name}"
    )

    return {

        "ingredient_id":
            _catalogue[
                best_idx
            ][
                "ingredient_id"
            ],

        "canonical_name":
            best_match,

        "resolution_type":
            "vector",

        "score":
            round(
                best_score,
                4,
            ),
    }


if __name__ == "__main__":

    tests = [

        "haldi powder",

        "gehun atta",

        "cilantro leaves",

        "jeera powder",
    ]

    for test in tests:

        print(
            "-" * 50
        )

        print(
            resolve_by_vector(
                test
            )
        )