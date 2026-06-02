from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from ps1.raw_record import RawRecord
from ps1.registry import SourceRegistry
from ps1.web_adapter import WebScraperAdapter


class TestPS1(unittest.TestCase):
    def test_raw_record_is_immutable_and_uuid_unique(self):
        r1 = RawRecord(
            source_id="ds2",
            source_type="web",
            version="1.0",
            raw_content={"title": "A"},
        )
        r2 = RawRecord(
            source_id="ds2",
            source_type="web",
            version="1.0",
            raw_content={"title": "B"},
        )

        self.assertNotEqual(r1.record_id, r2.record_id)

        with self.assertRaises(AttributeError):
            r1.source_id = "changed"  # type: ignore[misc]

        with self.assertRaises(TypeError):
            r1.raw_content["title"] = "changed"  # type: ignore[index]

    @patch("ps1.web_adapter.requests.get")
    def test_web_adapter_extracts_json_ld(self, mock_get):
        html = """
        <html>
          <head>
            <title>Paneer Bhurji</title>
            <script type="application/ld+json">
            {
              "@context": "https://schema.org",
              "@type": "Recipe",
              "name": "Paneer Bhurji",
              "recipeIngredient": ["2 cups paneer", "1 onion"],
              "recipeInstructions": [
                {"@type": "HowToStep", "text": "Mix."},
                {"@type": "HowToStep", "text": "Cook."}
              ],
              "recipeCuisine": "Indian",
              "prepTime": "PT10M",
              "recipeYield": "4"
            }
            </script>
          </head>
          <body></body>
        </html>
        """

        response = Mock()
        response.status_code = 200
        response.text = html
        response.raise_for_status = Mock()
        mock_get.return_value = response

        adapter = WebScraperAdapter(
            source_id="ds2_hebbars_web",
            urls=["https://example.com/recipe"],
        )
        records = adapter.extract()

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].raw_content["title"], "Paneer Bhurji")
        self.assertEqual(len(records[0].raw_content["ingredients"]), 2)

    def test_registry_builds_adapter(self):
        yaml_text = """
        adapters:
          ds2:
            adapter: WebScraperAdapter
            source_id: ds2
            source_type: web
            version: "1.0"
            config:
              urls:
                - https://example.com/recipe
        """

        with tempfile.TemporaryDirectory() as tmpdir:
            registry_path = Path(tmpdir) / "source_registry.yaml"
            registry_path.write_text(yaml_text, encoding="utf-8")

            registry = SourceRegistry(registry_path)
            adapters = registry.load_adapters()

            self.assertEqual(len(adapters), 1)
            self.assertEqual(adapters[0].source_id, "ds2")
            self.assertEqual(adapters[0].source_type, "web")


if __name__ == "__main__":
    unittest.main()