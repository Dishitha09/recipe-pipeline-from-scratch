DENSITY_TABLE = {

    # Real densities

    "water": {"g_per_ml": 1.00},
    "milk": {"g_per_ml": 1.03},
    "oil": {"g_per_ml": 0.92},
    "butter": {"g_per_ml": 0.96},
    "yogurt": {"g_per_ml": 1.03},
    "sugar": {"g_per_ml": 0.85},
    "salt": {"g_per_ml": 1.20},
    "honey": {"g_per_ml": 1.42},
    "ghee": {"g_per_ml": 0.91},
    "lemon juice": {"g_per_ml": 1.03},

    # Common ingredients (temporary defaults)

    "ginger": {"g_per_ml": 1.0},
    "garam masala": {"g_per_ml": 1.0},
    "onion": {"g_per_ml": 1.0},
    "cumin seeds": {"g_per_ml": 1.0},
    "turmeric powder": {"g_per_ml": 1.0},
    "red chili powder": {"g_per_ml": 1.0},
    "coriander powder": {"g_per_ml": 1.0},
    "green chili": {"g_per_ml": 1.0},
    "turmeric": {"g_per_ml": 1.0},
    "red onion": {"g_per_ml": 1.0},
    "cilantro": {"g_per_ml": 1.0},
    "curry leaves": {"g_per_ml": 1.0},
    "cumin powder": {"g_per_ml": 1.0},
    "mustard seeds": {"g_per_ml": 1.0},
    "cardamom powder": {"g_per_ml": 1.0},
    "garlic": {"g_per_ml": 1.0},
    "kashmiri red chilli powder": {"g_per_ml": 1.0},
    "tomato": {"g_per_ml": 1.0},
    "cumin": {"g_per_ml": 1.0},
    "coriander": {"g_per_ml": 1.0},
    "urad dal": {"g_per_ml": 1.0},
}
def get_density(ingredient_name):

    ingredient_name = (
        str(ingredient_name)
        .lower()
        .strip()
    )

    if ingredient_name in DENSITY_TABLE:

        return DENSITY_TABLE[
            ingredient_name
        ]

    return {
        "g_per_ml": 1.0,
        "density_source": "default",
    }