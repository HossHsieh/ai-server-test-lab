"""
Validate a runner-readable test recipe YAML file.

This script checks whether a recipe file has the minimum structure needed
by a future shared test runner.

Example:
    python scripts/validate_recipe.py configs/evt_debug_recipe.yaml
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


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Recipe file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError("Recipe YAML must be a dictionary at the top level.")

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


def validate_recipe(path: Path) -> None:
    data = load_yaml(path)
    validate_recipe_header(data)
    validate_metadata_schema(data)
    validate_execution_policy(data)
    validate_phases(data)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a test recipe YAML file.")
    parser.add_argument("recipe_path", help="Path to the recipe YAML file.")
    args = parser.parse_args()

    recipe_path = Path(args.recipe_path)

    try:
        validate_recipe(recipe_path)
    except Exception as exc:
        print(f"[FAIL] Recipe validation failed: {exc}")
        return 1

    print(f"[PASS] Recipe validation passed: {recipe_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())