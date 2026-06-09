
import csv
import sys
from pathlib import Path

CATALOGUE_FILE = Path("data/master_ingredients.csv")


def add_alias(canonical_name: str, alias: str):

    rows = []

    with open(CATALOGUE_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:

            if row["canonical_name"].strip().lower() == canonical_name.lower():

                existing_aliases = set()

                if row["aliases"]:
                    existing_aliases.update(
                        x.strip()
                        for x in row["aliases"].split("|")
                        if x.strip()
                    )

                existing_aliases.add(alias)

                row["aliases"] = "|".join(
                    sorted(existing_aliases)
                )

            rows.append(row)

    with open(CATALOGUE_FILE, "w", newline="", encoding="utf-8") as f:

        writer = csv.DictWriter(
            f,
            fieldnames=[
                "ingredient_id",
                "canonical_name",
                "aliases",
            ],
        )

        writer.writeheader()
        writer.writerows(rows)

    print(
        f"Added alias '{alias}' -> '{canonical_name}'"
    )


if __name__ == "__main__":

    if len(sys.argv) != 3:
        print(
            "Usage: python scripts/add_alias.py <canonical_name> <alias>"
        )
        sys.exit(1)

    add_alias(
        sys.argv[1],
        sys.argv[2],
    )

