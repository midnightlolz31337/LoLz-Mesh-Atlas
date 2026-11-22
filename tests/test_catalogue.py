import tempfile
import unittest
from pathlib import Path

from atlas_catalogue.validator import load_catalogue, validate_catalogue

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / "catalogue" / "projects.yaml"


class CatalogueValidationTests(unittest.TestCase):
    def setUp(self):
        self.document = load_catalogue(CATALOGUE)

    def test_current_catalogue_passes(self):
        self.assertEqual(validate_catalogue(self.document), [])

    def test_duplicate_project_id_fails(self):
        self.document["projects"].append(dict(self.document["projects"][0]))
        errors = validate_catalogue(self.document)
        self.assertTrue(any("duplicate project id" in error for error in errors))

    def test_duplicate_repository_fails(self):
        duplicate = dict(self.document["projects"][0])
        duplicate["id"] = "different-project-id"
        self.document["projects"].append(duplicate)
        errors = validate_catalogue(self.document)
        self.assertTrue(any("duplicate repository" in error for error in errors))

    def test_private_visibility_fails_closed(self):
        self.document["projects"][0]["visibility"] = "private"
        self.assertTrue(validate_catalogue(self.document))

    def test_http_repository_url_fails(self):
        self.document["projects"][0]["repository"] = "http://example.org/project"
        self.assertTrue(validate_catalogue(self.document))

    def test_unknown_fields_fail_closed(self):
        self.document["unexpected"] = "not allowed"
        self.assertTrue(validate_catalogue(self.document))

    def test_duplicate_yaml_mapping_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "duplicate.yaml"
            path.write_text("schema_version: '1.0'\nschema_version: '1.0'\n", encoding="utf-8")
            with self.assertRaises(Exception):
                load_catalogue(path)


if __name__ == "__main__":
    unittest.main()
