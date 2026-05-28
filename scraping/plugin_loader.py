from __future__ import annotations

from scraping.plugins.archana_plugin import (
    ArchanaKitchenPlugin,
)
from scraping.plugins.hebbars_plugin import (
    HebbarsKitchenPlugin,
)


PLUGIN_REGISTRY = {
    "hebbars": HebbarsKitchenPlugin,
    "archana": ArchanaKitchenPlugin,
}


def get_plugin(plugin_name: str):

    if plugin_name not in PLUGIN_REGISTRY:

        raise ValueError(
            f"Unknown plugin: {plugin_name}"
        )

    return PLUGIN_REGISTRY[
        plugin_name
    ]()