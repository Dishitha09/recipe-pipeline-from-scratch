from enrichment.ingredient_catalogue import MASTER_INGREDIENTS


def resolve_ingredient(name: str):
    cleaned = name.strip().lower()

    for canonical_name, aliases in MASTER_INGREDIENTS.items():
        if cleaned == canonical_name or cleaned in aliases:
            return {
                "raw_name": name,
                "canonical_name": canonical_name,
                "resolution_type": "exact"
            }

    return {
        "raw_name": name,
        "canonical_name": None,
        "resolution_type": "unresolved"
    }