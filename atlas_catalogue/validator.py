"""Validate the public LoLz Mesh Atlas catalogue."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError
from yaml.constructor import ConstructorError

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "schemas" / "catalogue.schema.json"
DEFAULT_CATALOGUE = ROOT / "catalogue" / "projects.yaml"


class UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


def _construct_unique_mapping(loader: UniqueKeyLoader, node: yaml.nodes.MappingNode, deep: bool = False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in mapping
        except TypeError as exc:
            raise ConstructorError("while constructing a mapping", node.start_mark,
                                   "unhashable mapping key", key_node.start_mark) from exc
        if duplicate:
            raise ConstructorError("while constructing a mapping", node.start_mark,
                                   f"duplicate key {key!r}", key_node.start_mark)
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def load_catalogue(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.load(handle, Loader=UniqueKeyLoader)


def load_schema(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_format_checker() -> FormatChecker:
    """Require absolute HTTPS URLs without credentials or malformed ports."""
    checker = FormatChecker()

    @checker.checks("uri")
    def is_absolute_https_uri(value: Any) -> bool:
        if not isinstance(value, str) or not value or any(ch.isspace() or ch == "\\" for ch in value):
            return False
        try:
            parsed = urlsplit(value)
            port = parsed.port
            if parsed.scheme != "https" or not parsed.hostname:
                return False
            if parsed.username is not None or parsed.password is not None:
                return False
            if parsed.netloc.endswith(":"):
                return False
            return port is None or 1 <= port <= 65535
        except ValueError:
            return False

    return checker


def validate_catalogue(document: Any, schema: dict[str, Any] | None = None) -> list[str]:
    """Return deterministic schema and cross-record validation errors."""
    selected_schema = schema if schema is not None else load_schema(DEFAULT_SCHEMA)
    Draft202012Validator.check_schema(selected_schema)
    validator = Draft202012Validator(selected_schema, format_checker=build_format_checker())
    errors = []
    for error in validator.iter_errors(document):
        location = ".".join(str(part) for part in error.absolute_path) or "$"
        errors.append(f"{location}: {error.message}")

    if isinstance(document, dict) and isinstance(document.get("projects"), list):
        seen_ids: set[str] = set()
        seen_repositories: set[str] = set()
        for index, project in enumerate(document["projects"]):
            if not isinstance(project, dict):
                continue
            project_id = project.get("id")
            repository = project.get("repository")
            if isinstance(project_id, str):
                if project_id in seen_ids:
                    errors.append(f"projects.{index}.id: duplicate project id {project_id!r}")
                seen_ids.add(project_id)
            if isinstance(repository, str):
                if repository in seen_repositories:
                    errors.append(f"projects.{index}.repository: duplicate repository {repository!r}")
                seen_repositories.add(repository)

    return sorted(errors)


def export_catalogue_json(document: dict[str, Any], destination: Path) -> None:
    """Write deterministic JSON through a same-directory atomic replacement."""
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, destination)
        temporary_path = None
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the LoLz Mesh Atlas catalogue.")
    parser.add_argument("catalogue", nargs="?", type=Path, default=DEFAULT_CATALOGUE)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--export-json", type=Path, help="Write a deterministic JSON export after validation")
    args = parser.parse_args(argv)

    try:
        if args.export_json is not None:
            output = args.export_json.resolve()
            if output in {args.catalogue.resolve(), args.schema.resolve()}:
                raise ValueError("JSON export destination must differ from the catalogue and schema inputs")
        schema = load_schema(args.schema)
        catalogue = load_catalogue(args.catalogue)
        errors = validate_catalogue(catalogue, schema)
        if errors:
            for error in errors:
                print(f"FAIL: {error}")
            return 1
        if args.export_json is not None:
            export_catalogue_json(catalogue, args.export_json)
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError, SchemaError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"PASS: {len(catalogue['projects'])} public project records validated")
    if args.export_json is not None:
        print(f"EXPORTED: {args.export_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
