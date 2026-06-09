
import csv
from pathlib import Path


CATALOGUE_FILE = Path("data/master_ingredients.csv")


def load_catalogue():
    catalogue = []

    with open(CATALOGUE_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            aliases = [
                x.strip().lower()
                for x in row["aliases"].split("|")
                if x.strip()
            ]

            catalogue.append(
                {
                    "ingredient_id": row["ingredient_id"],
                    "canonical_name": row["canonical_name"].strip().lower(),
                    "aliases": aliases,
                }
            )

    return catalogue


def resolve_ingredient(name: str):
    cleaned = str(name).strip().lower()

    for ingredient in load_catalogue():

        if cleaned == ingredient["canonical_name"]:
            return {
                "raw_name": name,
                "ingredient_id": ingredient["ingredient_id"],
                "canonical_name": ingredient["canonical_name"],
                "resolution_type": "exact",
            }

        if cleaned in ingredient["aliases"]:
            return {
                "raw_name": name,
                "ingredient_id": ingredient["ingredient_id"],
                "canonical_name": ingredient["canonical_name"],
                "resolution_type": "exact",
            }

    return {
        "raw_name": name,
        "ingredient_id": None,
        "canonical_name": None,
        "resolution_type": "unresolved",
    }

