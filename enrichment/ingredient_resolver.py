import csv
from pathlib import Path

CATALOGUE_FILE = Path(
    "data/master_ingredients_final_v4.csv"
)


def load_catalogue():

    catalogue = []

    with open(
        CATALOGUE_FILE,
        "r",
        encoding="utf-8",
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            aliases = []

            alias_text = str(
                row.get(
                    "aliases",
                    "",
                )
            )

            if alias_text != "nan":

                aliases = [
                    x.strip().lower()
                    for x in alias_text.split("|")
                    if x.strip()
                ]

            catalogue.append(
                {
                    "ingredient_id": row[
                        "ingredient_id"
                    ],
                    "canonical_name": row[
                        "canonical_name"
                    ]
                    .strip()
                    .lower(),
                    "aliases": aliases,
                }
            )

    return catalogue


def resolve_ingredient(
    name: str,
):

    cleaned = (
        str(name)
        .strip()
        .lower()
    )

    for ingredient in load_catalogue():

        if (
            cleaned
            == ingredient[
                "canonical_name"
            ]
        ):

            return {
                "raw_name": name,
                "ingredient_id": ingredient[
                    "ingredient_id"
                ],
                "canonical_name": ingredient[
                    "canonical_name"
                ],
                "resolution_type": "exact",
            }

        if (
            cleaned
            in ingredient[
                "aliases"
            ]
        ):

            return {
                "raw_name": name,
                "ingredient_id": ingredient[
                    "ingredient_id"
                ],
                "canonical_name": ingredient[
                    "canonical_name"
                ],
                "resolution_type": "alias",
            }

    return None


if __name__ == "__main__":

    tests = [
        "haldi powder",
        "jeera powder",
        "gehun atta",
        "curd",
        "ghee",
    ]

    for test in tests:

        print(
            resolve_ingredient(
                test
            )
        )