"""
Dry-run a runner-readable test recipe.

This script does not control real hardware. It simulates measurement results
from a YAML recipe and produces a structured test record.

Example:
    python scripts/dry_run_recipe.py configs/evt_debug_recipe.yaml --error-catalog configs/error_catalog.yaml

Inject one failure:
    python scripts/dry_run_recipe.py configs/evt_debug_recipe.yaml --error-catalog configs/error_catalog.yaml --inject-failure fan_rpm_after_pwm_70
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"YAML must be a dictionary at the top level: {path}")

    return data


def load_error_catalog(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None:
        return {}

    catalog_data = load_yaml(path)
    catalog_by_id: dict[str, dict[str, Any]] = {}

    for error in catalog_data.get("errors", []):
        catalog_by_id[str(error["error_id"])] = error

    return catalog_by_id


def simulate_passing_value(measurement: dict[str, Any]) -> Any:
    measurement_type = measurement["type"]

    if measurement_type == "string":
        if measurement.get("expected") == "present":
            return "SIMULATED_VALUE"
        return measurement.get("expected")

    if measurement_type == "boolean":
        return measurement.get("expected", True)

    if measurement_type == "numeric":
        lower = measurement.get("lower_limit")
        upper = measurement.get("upper_limit")
        expected = measurement.get("expected")

        if expected is not None:
            return expected

        if lower is not None and upper is not None:
            return (float(lower) + float(upper)) / 2

        if lower is not None:
            return float(lower) + 1

        if upper is not None:
            return float(upper) - 1

    raise ValueError(f"Unsupported measurement type: {measurement_type}")


def simulate_failing_value(measurement: dict[str, Any]) -> Any:
    measurement_type = measurement["type"]

    if measurement_type == "string":
        return ""

    if measurement_type == "boolean":
        return not bool(measurement.get("expected", True))

    if measurement_type == "numeric":
        if "lower_limit" in measurement:
            return float(measurement["lower_limit"]) - 1

        if "upper_limit" in measurement:
            return float(measurement["upper_limit"]) + 1

        if "expected" in measurement:
            return float(measurement["expected"]) + 1

    raise ValueError(f"Unsupported measurement type: {measurement_type}")


def evaluate_measurement(measurement: dict[str, Any], value: Any) -> tuple[bool, str]:
    measurement_type = measurement["type"]

    if measurement_type == "string":
        expected = measurement.get("expected")

        if expected == "present":
            passed = value not in [None, ""]
            return passed, "value is present" if passed else "value is missing"

        passed = value == expected
        return passed, f"value == {expected}" if passed else f"value != {expected}"

    if measurement_type == "boolean":
        expected = measurement["expected"]
        passed = value is expected
        return passed, f"value == {expected}" if passed else f"value != {expected}"

    if measurement_type == "numeric":
        if "lower_limit" in measurement and value < measurement["lower_limit"]:
            return False, f"value {value} < lower_limit {measurement['lower_limit']}"

        if "upper_limit" in measurement and value > measurement["upper_limit"]:
            return False, f"value {value} > upper_limit {measurement['upper_limit']}"

        if "expected" in measurement and value != measurement["expected"]:
            return False, f"value {value} != expected {measurement['expected']}"

        return True, "numeric limits passed"

    raise ValueError(f"Unsupported measurement type: {measurement_type}")


def run_recipe(
    recipe_data: dict[str, Any],
    catalog_by_id: dict[str, dict[str, Any]],
    inject_failure: str | None,
) -> dict[str, Any]:
    recipe = recipe_data["recipe"]
    phases = recipe_data["phases"]

    record: dict[str, Any] = {
        "record_type": "dry_run_test_record",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "recipe_name": recipe["name"],
        "recipe_version": recipe["version"],
        "stage": recipe["stage"],
        "mode": recipe["mode"],
        "overall_status": "PASS",
        "phases": [],
    }

    for phase in phases:
        phase_record: dict[str, Any] = {
            "phase_name": phase["phase_name"],
            "phase_type": phase["phase_type"],
            "enabled": phase["enabled"],
            "status": "PASS",
            "measurements": [],
            "required_logs": phase.get("required_logs", []),
        }

        if not phase["enabled"]:
            phase_record["status"] = "SKIPPED"
            record["phases"].append(phase_record)
            continue

        for measurement in phase["measurements"]:
            measurement_name = measurement["name"]

            if inject_failure == measurement_name:
                value = simulate_failing_value(measurement)
            else:
                value = simulate_passing_value(measurement)

            passed, detail = evaluate_measurement(measurement, value)

            measurement_record: dict[str, Any] = {
                "name": measurement_name,
                "type": measurement["type"],
                "value": value,
                "status": "PASS" if passed else "FAIL",
                "detail": detail,
                "error_id": measurement["error_id"],
                "error_code": measurement["error_code"],
            }

            if "unit" in measurement:
                measurement_record["unit"] = measurement["unit"]

            if not passed:
                phase_record["status"] = "FAIL"
                record["overall_status"] = "FAIL"

                catalog_error = catalog_by_id.get(measurement["error_id"])
                if catalog_error:
                    measurement_record["error_description"] = catalog_error["description"]
                    measurement_record["debug_hint"] = catalog_error["debug_hint"]

            phase_record["measurements"].append(measurement_record)

        record["phases"].append(phase_record)

    return record


def main() -> int:
    parser = argparse.ArgumentParser(description="Dry-run a test recipe.")
    parser.add_argument("recipe_path", help="Path to the recipe YAML file.")
    parser.add_argument(
        "--error-catalog",
        default=None,
        help="Optional path to the centralized error catalog YAML file.",
    )
    parser.add_argument(
        "--inject-failure",
        default=None,
        help="Optional measurement name to force a simulated failure.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional path to write the dry-run test record as JSON.",
    )

    args = parser.parse_args()

    try:
        recipe_data = load_yaml(Path(args.recipe_path))

        catalog_path = Path(args.error_catalog) if args.error_catalog else None
        catalog_by_id = load_error_catalog(catalog_path)

        record = run_recipe(
            recipe_data=recipe_data,
            catalog_by_id=catalog_by_id,
            inject_failure=args.inject_failure,
        )

        output_text = json.dumps(record, indent=2, ensure_ascii=False)
        print(output_text)

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(output_text, encoding="utf-8")
            print(f"\n[INFO] Wrote dry-run record to: {output_path}")

    except Exception as exc:
        print(f"[FAIL] Dry-run failed: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())