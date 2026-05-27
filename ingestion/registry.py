import yaml

from ingestion.csv_adapter import CSVRecipeAdapter


ADAPTER_MAPPING = {
    "CSVRecipeAdapter": CSVRecipeAdapter
}


def load_registry():

    with open("config/sources.yaml", "r") as file:

        config = yaml.safe_load(file)

    registry = {}

    for source_id, source_config in config["sources"].items():

        adapter_name = source_config["adapter"]

        registry[source_id] = ADAPTER_MAPPING[adapter_name]

    return registry


SOURCE_REGISTRY = load_registry()