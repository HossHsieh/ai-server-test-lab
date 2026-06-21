"""
Dry-run a runner-readable test recipe.

This script does not control real hardware. It simulates measurement results
from a YAML recipe and produces a structured test record.

It supports two simulation modes:
1. Default mode:
   Generate passing values from the recipe limits / expected values.

2. DUT profile mode:
   Load synthetic DUT telemetry from configs/dut_profiles.yaml and use those
   values when measurement names match telemetry keys.

The optional --inject-failure argument still has highest priority and can force
a selected measurement to fail for quick debugging.
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


def load_dut_profile(
    dut_profiles_path: Path | None,
    profile_name: str | None,
) -> dict[str, Any] | None:
    if dut_profiles_path is None and profile_name is None:
        return None

    if dut_profiles_path is None:
        raise ValueError("--profile-name requires --dut-profiles")

    if profile_name is None:
        raise ValueError("--dut-profiles requires --profile-name")

    profiles_data = load_yaml(dut_profiles_path)
    profiles = profiles_data.get("profiles", {})

    if not isinstance(profiles, dict):
        raise ValueError("DUT profiles YAML must contain a 'profiles' dictionary.")

    if profile_name not in profiles:
        available = ", ".join(sorted(profiles.keys()))
        raise ValueError(
            f"DUT profile not found: {profile_name}. Available profiles: {available}"
        )

    selected_profile = profiles[profile_name]

    if not isinstance(selected_profile, dict):
        raise ValueError(f"DUT profile must be a dictionary: {profile_name}")

    selected_profile = dict(selected_profile)
    selected_profile["profile_name"] = profile_name
    return selected_profile


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


def get_measurement_value(
    measurement: dict[str, Any],
    dut_profile: dict[str, Any] | None,
    inject_failure: str | None,
) -> tuple[Any, str]:
    measurement_name = measurement["name"]

    if inject_failure == measurement_name:
        return simulate_failing_value(measurement), "injected_failure"

    if dut_profile is not None:
        telemetry = dut_profile.get("telemetry", {})
        if measurement_name in telemetry:
            return telemetry[measurement_name], "dut_profile_telemetry"

    return simulate_passing_value(measurement), "simulated_passing_value"


def evaluate_measurement(measurement: dict[str, Any], value: Any) -> tuple[bool, str]:
    measurement_type = measurement["type"]

    if value is None:
        return False, "value is missing"

    if measurement_type == "string":
        expected = measurement.get("expected")

        if expected == "present":
            passed = value not in [None, ""]
            return passed, "value is present" if passed else "value is missing"

        passed = value == expected
        return passed, f"value == {expected}" if passed else f"value != {expected}"

    if measurement_type == "boolean":
        expected = measurement["expected"]
        passed = value == expected
        return passed, f"value == {expected}" if passed else f"value != {expected}"

    if measurement_type == "numeric":
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            return False, f"value {value} is not numeric"

        if "lower_limit" in measurement and numeric_value < measurement["lower_limit"]:
            return False, (
                f"value {numeric_value} < lower_limit {measurement['lower_limit']}"
            )

        if "upper_limit" in measurement and numeric_value > measurement["upper_limit"]:
            return False, (
                f"value {numeric_value} > upper_limit {measurement['upper_limit']}"
            )

        if "expected" in measurement and numeric_value != measurement["expected"]:
            return False, (
                f"value {numeric_value} != expected {measurement['expected']}"
            )

        return True, "numeric limits passed"

    raise ValueError(f"Unsupported measurement type: {measurement_type}")


def get_measurement_limits(measurement: dict[str, Any]) -> dict[str, Any]:
    limits: dict[str, Any] = {}

    for key in ["expected", "lower_limit", "upper_limit"]:
        if key in measurement:
            limits[key] = measurement[key]

    return limits


def run_recipe(
    recipe_data: dict[str, Any],
    catalog_by_id: dict[str, dict[str, Any]],
    inject_failure: str | None,
    dut_profile: dict[str, Any] | None,
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

    if dut_profile is not None:
        record["dut_profile"] = dut_profile.get("profile_name")
        record["dut_metadata"] = dut_profile.get("dut_metadata", {})
        record["firmware"] = dut_profile.get("firmware", {})
        record["fault_model"] = dut_profile.get("fault_model", {})

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
            value, value_source = get_measurement_value(
                measurement=measurement,
                dut_profile=dut_profile,
                inject_failure=inject_failure,
            )
            passed, detail = evaluate_measurement(measurement, value)

            measurement_record: dict[str, Any] = {
                "name": measurement_name,
                "type": measurement["type"],
                "value": value,
                "value_source": value_source,
                "status": "PASS" if passed else "FAIL",
                "detail": detail,
                "error_id": measurement["error_id"],
                "error_code": measurement["error_code"],
            }

            limits = get_measurement_limits(measurement)
            if limits:
                measurement_record["limits"] = limits

            if "unit" in measurement:
                measurement_record["unit"] = measurement["unit"]

            if not passed:
                phase_record["status"] = "FAIL"
                record["overall_status"] = "FAIL"

                catalog_error = catalog_by_id.get(measurement["error_id"])
                if catalog_error:
                    measurement_record["error_description"] = catalog_error[
                        "description"
                    ]
                    measurement_record["debug_hint"] = catalog_error["debug_hint"]
                    measurement_record["category"] = catalog_error.get("category")
                    measurement_record["severity"] = catalog_error.get("severity")

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
        "--dut-profiles",
        default=None,
        help="Optional path to the synthetic DUT profiles YAML file.",
    )
    parser.add_argument(
        "--profile-name",
        default=None,
        help="Name of the synthetic DUT profile to use.",
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

        dut_profiles_path = Path(args.dut_profiles) if args.dut_profiles else None
        dut_profile = load_dut_profile(
            dut_profiles_path=dut_profiles_path,
            profile_name=args.profile_name,
        )

        record = run_recipe(
            recipe_data=recipe_data,
            catalog_by_id=catalog_by_id,
            inject_failure=args.inject_failure,
            dut_profile=dut_profile,
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