"""
Validate a runner-readable test recipe YAML file.

This script checks:
1. The recipe YAML has the required structure.
2. Each phase and measurement has required fields.
3. Each error_id / error_code used by the recipe exists in the centralized
   error catalog, if an error catalog is provided.

Examples:
    python scripts/validate_recipe.py configs/evt_debug_recipe.yaml

    python scripts/validate_recipe.py configs/evt_debug_recipe.yaml ^
        --error-catalog configs/error_catalog.yaml
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml


ALLOWED_MEASUREMENT_TYPES = {"string", "boolean", "numeric"}
ALLOWED_FAIL_BEHAVIORS = {"continue", "stop", "fail_and_collect_debug"}
ALLOWED_ERROR_STATUS = {"active", "deprecated", "reserved"}


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"YAML must be a dictionary at the top level: {path}")

    return data


def require_key(obj: dict[str, Any], key: str, context: str) -> Any:
    if key not in obj:
        raise ValueError(f"Missing required key '{key}' in {context}.")
    return obj[key]


def require_list(obj: dict[str, Any], key: str, context: str) -> list[Any]:
    value = require_key(obj, key, context)
    if not isinstance(value, list):
        raise ValueError(f"'{key}' in {context} must be a list.")
    return value


def validate_error_id(error_id: str, context: str) -> None:
    pattern = r"^E-[A-Z]+-\d{3}$"
    if not re.match(pattern, error_id):
        raise ValueError(
            f"Invalid error_id '{error_id}' in {context}. "
            "Expected format like E-THERM-001."
        )


def validate_error_code(error_code: str, context: str) -> None:
    pattern = r"^[A-Z0-9_]+$"
    if not re.match(pattern, error_code):
        raise ValueError(
            f"Invalid error_code '{error_code}' in {context}. "
            "Expected uppercase snake-case like THERM_FAN_RAMP_TIMEOUT."
        )


def validate_recipe_header(data: dict[str, Any]) -> None:
    require_key(data, "schema_version", "top level")

    recipe = require_key(data, "recipe", "top level")
    if not isinstance(recipe, dict):
        raise ValueError("'recipe' must be a dictionary.")

    for key in ["name", "version", "stage", "mode"]:
        require_key(recipe, key, "recipe")


def validate_metadata_schema(data: dict[str, Any]) -> None:
    metadata_schema = require_key(data, "metadata_schema", "top level")
    if not isinstance(metadata_schema, dict):
        raise ValueError("'metadata_schema' must be a dictionary.")

    required = require_list(metadata_schema, "required", "metadata_schema")
    if not required:
        raise ValueError("'metadata_schema.required' must not be empty.")

    if "optional" in metadata_schema and not isinstance(metadata_schema["optional"], list):
        raise ValueError("'metadata_schema.optional' must be a list if present.")


def validate_execution_policy(data: dict[str, Any]) -> None:
    execution_policy = require_key(data, "execution_policy", "top level")
    if not isinstance(execution_policy, dict):
        raise ValueError("'execution_policy' must be a dictionary.")

    required_keys = [
        "stop_on_first_failure",
        "collect_raw_trace",
        "save_debug_logs",
        "repeat_on_failure",
        "cycle_time_target_sec",
    ]

    for key in required_keys:
        require_key(execution_policy, key, "execution_policy")


def validate_measurement(measurement: dict[str, Any], context: str) -> None:
    for key in ["name", "type", "error_id", "error_code"]:
        require_key(measurement, key, context)

    measurement_type = measurement["type"]

    if measurement_type not in ALLOWED_MEASUREMENT_TYPES:
        raise ValueError(
            f"Invalid measurement type '{measurement_type}' in {context}. "
            f"Allowed types: {sorted(ALLOWED_MEASUREMENT_TYPES)}"
        )

    validate_error_id(str(measurement["error_id"]), context)
    validate_error_code(str(measurement["error_code"]), context)

    if measurement_type in {"string", "boolean"}:
        require_key(measurement, "expected", context)

    if measurement_type == "numeric":
        has_limit = any(
            key in measurement for key in ["lower_limit", "upper_limit", "expected"]
        )
        if not has_limit:
            raise ValueError(
                f"Numeric measurement in {context} must define at least one of "
                "lower_limit, upper_limit, or expected."
            )


def validate_phase(phase: dict[str, Any], index: int) -> str:
    context = f"phases[{index}]"

    for key in ["phase_name", "phase_type", "enabled", "fail_behavior"]:
        require_key(phase, key, context)

    phase_name = str(phase["phase_name"])

    if phase["fail_behavior"] not in ALLOWED_FAIL_BEHAVIORS:
        raise ValueError(
            f"Invalid fail_behavior '{phase['fail_behavior']}' in {context}. "
            f"Allowed values: {sorted(ALLOWED_FAIL_BEHAVIORS)}"
        )

    measurements = require_list(phase, "measurements", context)
    if not measurements:
        raise ValueError(f"'measurements' in {context} must not be empty.")

    measurement_names: set[str] = set()

    for measurement_index, measurement in enumerate(measurements):
        measurement_context = (
            f"{context}.measurements[{measurement_index}] "
            f"({phase_name})"
        )

        if not isinstance(measurement, dict):
            raise ValueError(f"{measurement_context} must be a dictionary.")

        validate_measurement(measurement, measurement_context)

        measurement_name = str(measurement["name"])
        if measurement_name in measurement_names:
            raise ValueError(
                f"Duplicate measurement name '{measurement_name}' in phase '{phase_name}'."
            )
        measurement_names.add(measurement_name)

    required_logs = require_list(phase, "required_logs", context)
    if not required_logs:
        raise ValueError(f"'required_logs' in {context} must not be empty.")

    if "stimulus" in phase and not isinstance(phase["stimulus"], dict):
        raise ValueError(f"'stimulus' in {context} must be a dictionary if present.")

    return phase_name


def validate_phases(data: dict[str, Any]) -> None:
    phases = require_list(data, "phases", "top level")

    if not phases:
        raise ValueError("'phases' must not be empty.")

    phase_names: set[str] = set()

    for index, phase in enumerate(phases):
        if not isinstance(phase, dict):
            raise ValueError(f"phases[{index}] must be a dictionary.")

        phase_name = validate_phase(phase, index)

        if phase_name in phase_names:
            raise ValueError(f"Duplicate phase_name found: {phase_name}")
        phase_names.add(phase_name)


def validate_recipe(data: dict[str, Any]) -> None:
    validate_recipe_header(data)
    validate_metadata_schema(data)
    validate_execution_policy(data)
    validate_phases(data)


def collect_recipe_errors(data: dict[str, Any]) -> list[dict[str, str]]:
    recipe_errors: list[dict[str, str]] = []

    for phase_index, phase in enumerate(data["phases"]):
        phase_name = str(phase["phase_name"])

        for measurement_index, measurement in enumerate(phase["measurements"]):
            context = (
                f"phases[{phase_index}].measurements[{measurement_index}] "
                f"({phase_name}.{measurement['name']})"
            )

            recipe_errors.append(
                {
                    "error_id": str(measurement["error_id"]),
                    "error_code": str(measurement["error_code"]),
                    "context": context,
                }
            )

    return recipe_errors


def validate_error_catalog(catalog_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    require_key(catalog_data, "schema_version", "error catalog top level")
    errors = require_list(catalog_data, "errors", "error catalog top level")

    if not errors:
        raise ValueError("'errors' in error catalog must not be empty.")

    catalog_by_id: dict[str, dict[str, Any]] = {}
    seen_codes: set[str] = set()

    required_keys = [
        "error_id",
        "error_code",
        "category",
        "severity",
        "introduced_stage",
        "status",
        "description",
        "debug_hint",
    ]

    for index, error in enumerate(errors):
        context = f"error_catalog.errors[{index}]"

        if not isinstance(error, dict):
            raise ValueError(f"{context} must be a dictionary.")

        for key in required_keys:
            require_key(error, key, context)

        error_id = str(error["error_id"])
        error_code = str(error["error_code"])
        status = str(error["status"])

        validate_error_id(error_id, context)
        validate_error_code(error_code, context)

        if status not in ALLOWED_ERROR_STATUS:
            raise ValueError(
                f"Invalid status '{status}' in {context}. "
                f"Allowed values: {sorted(ALLOWED_ERROR_STATUS)}"
            )

        if error_id in catalog_by_id:
            raise ValueError(f"Duplicate error_id in error catalog: {error_id}")

        if error_code in seen_codes:
            raise ValueError(f"Duplicate error_code in error catalog: {error_code}")

        catalog_by_id[error_id] = error
        seen_codes.add(error_code)

    return catalog_by_id


def validate_recipe_errors_against_catalog(
    recipe_data: dict[str, Any],
    catalog_data: dict[str, Any],
) -> None:
    catalog_by_id = validate_error_catalog(catalog_data)
    recipe_errors = collect_recipe_errors(recipe_data)

    for recipe_error in recipe_errors:
        error_id = recipe_error["error_id"]
        error_code = recipe_error["error_code"]
        context = recipe_error["context"]

        if error_id not in catalog_by_id:
            raise ValueError(
                f"Recipe uses error_id '{error_id}' in {context}, "
                "but it is missing from the error catalog."
            )

        catalog_error = catalog_by_id[error_id]
        catalog_error_code = str(catalog_error["error_code"])

        if error_code != catalog_error_code:
            raise ValueError(
                f"Recipe uses error_id '{error_id}' with error_code '{error_code}' "
                f"in {context}, but catalog defines it as '{catalog_error_code}'."
            )

        if str(catalog_error["status"]) != "active":
            raise ValueError(
                f"Recipe uses error_id '{error_id}' in {context}, "
                f"but its catalog status is '{catalog_error['status']}'."
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a test recipe YAML file.")
    parser.add_argument("recipe_path", help="Path to the recipe YAML file.")
    parser.add_argument(
        "--error-catalog",
        default=None,
        help="Optional path to the centralized error catalog YAML file.",
    )
    args = parser.parse_args()

    recipe_path = Path(args.recipe_path)

    try:
        recipe_data = load_yaml(recipe_path)
        validate_recipe(recipe_data)

        if args.error_catalog:
            catalog_path = Path(args.error_catalog)
            catalog_data = load_yaml(catalog_path)
            validate_recipe_errors_against_catalog(recipe_data, catalog_data)
            print(f"[PASS] Recipe validation passed with error catalog: {recipe_path}")
        else:
            print(f"[PASS] Recipe validation passed: {recipe_path}")

    except Exception as exc:
        print(f"[FAIL] Recipe validation failed: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())