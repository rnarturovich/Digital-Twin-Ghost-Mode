#!/usr/bin/env python3
"""
validate_schema.py
==================

Validate a JSON document against one of this skill's schemas. Use it to:

  - sanity-check a profile or reply before passing it to the next stage
  - lint test fixtures
  - fail a CI build when a schema drifts

USAGE
-----

    python validate_schema.py --schema profile|reply|clone_test --input data.json
    cat data.json | python validate_schema.py --schema reply --stdin

Exits 0 on success, 1 on validation failure. Tries `jsonschema` first; if it's
not installed, falls back to a small built-in checker that covers the subset
of Draft-07 features actually used by the bundled schemas (type, enum,
required, minimum/maximum, minLength, items, additionalProperties, minItems,
maxItems). For full coverage in production, install jsonschema:

    pip install jsonschema
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, List

SCHEMA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "schemas")
SCHEMA_FILES = {
    "profile": "style_profile.schema.json",
    "reply": "reply_output.schema.json",
    "clone_test": "clone_test.schema.json",
}


def load_schema(name: str) -> dict:
    path = os.path.join(SCHEMA_DIR, SCHEMA_FILES[name])
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Minimal validator (used only when `jsonschema` isn't installed). It covers
# the features the bundled schemas actually use. If you add features to the
# schemas, extend this or require jsonschema.
# ---------------------------------------------------------------------------

def _type_ok(value: Any, expected: str) -> bool:
    return {
        "string": isinstance(value, str),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "array": isinstance(value, list),
        "object": isinstance(value, dict),
        "null": value is None,
    }.get(expected, False)


def _validate(value: Any, schema: dict, path: str, errors: List[str]) -> None:
    if "type" in schema:
        expected = schema["type"]
        types = expected if isinstance(expected, list) else [expected]
        if not any(_type_ok(value, t) for t in types):
            errors.append(f"{path}: expected {expected}, got {type(value).__name__}")
            return

    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} not in enum {schema['enum']}")

    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path}: string shorter than minLength {schema['minLength']}")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errors.append(f"{path}: string longer than maxLength {schema['maxLength']}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: {value} < minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: {value} > maximum {schema['maximum']}")

    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{path}: array has {len(value)} items, minItems is {schema['minItems']}")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{path}: array has {len(value)} items, maxItems is {schema['maxItems']}")
        if "items" in schema:
            for i, item in enumerate(value):
                _validate(item, schema["items"], f"{path}[{i}]", errors)

    if isinstance(value, dict):
        for req in schema.get("required", []):
            if req not in value:
                errors.append(f"{path}: missing required field '{req}'")
        properties = schema.get("properties", {})
        for k, v in value.items():
            if k in properties:
                _validate(v, properties[k], f"{path}.{k}", errors)
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}: unexpected property '{k}' (additionalProperties=false)")


def _builtin_validate(data: Any, schema: dict) -> List[str]:
    errors: List[str] = []
    _validate(data, schema, "$", errors)
    return errors


def validate(data: Any, schema: dict) -> List[str]:
    """Return list of error strings. Empty list = valid."""
    try:
        import jsonschema  # type: ignore
        validator = jsonschema.Draft7Validator(schema)
        return [f"{'.'.join(str(p) for p in e.absolute_path) or '$'}: {e.message}" for e in validator.iter_errors(data)]
    except ImportError:
        return _builtin_validate(data, schema)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--schema", choices=sorted(SCHEMA_FILES.keys()), required=True)
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--input", help="Path to JSON file.")
    src.add_argument("--stdin", action="store_true", help="Read JSON from stdin.")
    parser.add_argument("--quiet", action="store_true", help="No output; exit code only.")
    args = parser.parse_args()

    raw = sys.stdin.read() if args.stdin else open(args.input, "r", encoding="utf-8").read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        if not args.quiet:
            print(f"Invalid JSON: {e}", file=sys.stderr)
        return 1

    schema = load_schema(args.schema)
    errors = validate(data, schema)

    if errors:
        if not args.quiet:
            for err in errors:
                print(f"  - {err}", file=sys.stderr)
            print(f"\n{len(errors)} validation error(s).", file=sys.stderr)
        return 1

    if not args.quiet:
        print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
