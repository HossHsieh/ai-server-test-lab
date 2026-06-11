# 03. EVT Test Plan - AI Server Debug and Observability

## Purpose

This document defines the EVT test plan for a synthetic AI server node.

EVT stands for Engineering Validation Test. In this stage, the goal is not only to determine whether a unit passes or fails. The main goal is to understand whether the design, firmware, sensors, telemetry, and debug hooks are sufficient for engineering investigation.

The executable YAML recipe connected to this document is:

```text
configs/evt_debug_recipe.yaml
```

The markdown document explains the engineering reasoning.

The YAML recipe defines what a shared test runner can execute.

## Stage Context

EVT is an early engineering validation stage.

At this stage, the product may still have:

- Unstable board revisions
- Experimental firmware builds
- Incomplete telemetry
- Temporary engineering limits
- Incomplete failure classification
- Debug hooks that still need to be improved

Therefore, the EVT test plan focuses on learning and observability rather than production efficiency.

## EVT Test Objective

The main objective of this EVT test plan is to answer:

```text
If the DUT fails, do we have enough information to understand why?
```

The test plan should help identify:

- Design weakness
- Firmware debug gap
- Missing telemetry
- Sensor visibility issue
- Power or thermal behavior risk
- Failure modes that cannot be isolated with current logs
- Additional Design for Test requirements

## Scope

This EVT test plan covers a synthetic AI server node with the following simplified subsystems:

- DUT identification
- Board revision readback
- Firmware debug visibility
- Power rail telemetry
- Fan response behavior
- Thermal observability
- Firmware and BMC error logs

## Out of Scope

This EVT test plan does not cover:

- Full production screening
- Operator shift analysis
- High-volume yield monitoring
- Final production cycle-time optimization
- Formal GR&R study
- Full station-to-station correlation
- Lot-level production containment

Those topics are more relevant to NPI/PVT or HVM stages.

## Acronym Notes

| Acronym | Full Name | Meaning in This Project |
|---|---|---|
| DUT | Device Under Test | The hardware unit being tested |
| EVT | Engineering Validation Test | Early engineering stage focused on design, firmware, and testability debugging |
| DFT | Design for Test | Design choices that make the product easier to test and debug |
| BMC | Baseboard Management Controller | Server management controller used to monitor hardware status and logs |
| FW | Firmware | Low-level software running on hardware devices |
| PWM | Pulse Width Modulation | Digital ON/OFF control used to emulate analog control, such as fan speed |
| RPM | Revolutions Per Minute | Fan rotation speed |
| RCA | Root-Cause Analysis | Investigation process to identify the real cause of a failure |

## EVT Test Philosophy

In EVT, a test should collect more data than a production test.

A production test asks:

```text
Should this unit pass or fail quickly?
```

An EVT test asks:

```text
Can we understand the behavior deeply enough to improve the design, firmware, or testability?
```

Therefore, EVT tests may intentionally collect raw traces, debug logs, and intermediate signals even if they increase test time.

In EVT, a failure is not only a screening result. It is also an engineering learning signal.

## Key EVT Risks and Test Coverage

| Risk Area | Risk Description | Test Coverage |
|---|---|---|
| DUT identity | Wrong engineering unit or missing board revision | Identify engineering unit and board revision |
| Firmware debug | Firmware does not expose enough debug information | Check firmware build ID, debug log, and reset reason |
| Power telemetry | Power issue cannot be diagnosed from single-point measurement | Collect power rail traces under synthetic load |
| Fan response | Fan does not respond correctly to PWM command | Collect PWM, fan RPM, and thermal state traces |
| Thermal observability | Thermal failure cannot be localized | Collect package, inlet, outlet temperature traces |
| Error diagnosis | Failure only appears as generic error | Scan firmware and BMC logs |

## EVT Metadata Focus

EVT metadata is mainly for engineering debug.

Required metadata:

- Engineering unit ID
- Board revision
- Product revision
- Firmware build ID
- Test script version
- Bench ID
- Sensor configuration
- Raw telemetry path
- Debug log path

Optional metadata:

- Instrument ID
- Test engineer note

Unlike HVM, EVT does not primarily focus on operator ID, shift, or high-volume production segmentation.

## EVT Test Phases

### Phase 1: Identify Engineering Unit

#### Purpose

Confirm that the DUT can be identified and that board revision information is available.

#### Why This Matters

In EVT, multiple engineering units and board revisions may exist at the same time. If the unit or board revision is not tracked, debug conclusions may be misleading.

For example, a thermal issue may only exist on one board revision. Without board revision tracking, the team may incorrectly treat it as a general design issue.

#### Expected Outputs

- Engineering unit ID
- Board revision
- Product revision

#### Related Recipe Phase

```text
identify_engineering_unit
```

---

### Phase 2: Firmware Debug Visibility Check

#### Purpose

Confirm that firmware exposes enough debug information for EVT investigation.

#### Why This Matters

If firmware only reports a generic failure, engineering teams cannot separate firmware bugs, power events, thermal events, or hardware faults.

EVT is the right stage to discover whether additional firmware debug hooks are needed.

#### Expected Outputs

- Firmware build ID
- Firmware debug log
- Reset reason code
- Firmware event log

#### Related Recipe Phase

```text
firmware_debug_visibility_check
```

---

### Phase 3: Power Telemetry Trace Check

#### Purpose

Collect power rail telemetry over time during synthetic load.

#### Why This Matters

A single voltage reading may miss transient behavior.

EVT should collect traces to understand whether voltage droop, unstable fixture contact, or load-related power behavior exists.

This is especially important because a power issue may trigger downstream symptoms, such as system reset, thermal control instability, or functional test failure.

#### Expected Outputs

- 12V rail trace
- 5V rail trace
- 3.3V rail trace
- Load profile
- Raw telemetry path

#### Related Recipe Phase

```text
power_telemetry_trace_check
```

---

### Phase 4: Fan Response Debug Check

#### Purpose

Study fan response behavior after a PWM command.

#### Why This Matters

Fan response failure can come from several different causes:

- Fan hardware issue
- Firmware fan-control issue
- Fan RPM sensor issue
- Thermal control state issue
- Station airflow condition
- Test timeout that is not yet mature

EVT should collect enough telemetry to separate these possibilities.

#### Example Risk-to-Measurement Mapping

| Item | Example |
|---|---|
| Risk | Fan does not respond correctly to PWM command |
| Observable signal | Fan RPM does not reach expected threshold |
| Measurement | `fan_rpm_after_pwm_70` |
| Temporary EVT limit | `fan_rpm_after_pwm_70 >= 6500 RPM` |
| Error code | `THERM_FAN_RAMP_TIMEOUT` |
| Debug data | PWM trace, fan RPM trace, package temperature trace, firmware thermal state |

#### Expected Outputs

- PWM command trace
- Fan RPM trace
- Package temperature trace
- Firmware thermal state
- Fan part number
- Ambient temperature

#### Related Recipe Phase

```text
fan_response_debug_check
```

---

### Phase 5: Thermal Observability Check

#### Purpose

Verify that thermal telemetry is available during synthetic load.

#### Why This Matters

If the package temperature rises too quickly, the team needs enough data to determine whether the issue is caused by:

- Cooling system behavior
- Fan response
- Firmware thermal control
- Sensor reporting
- Board-level thermal design
- Station setup

If only a final pass/fail result is available, the failure is difficult to debug.

#### Expected Outputs

- Package temperature trace
- Inlet temperature trace
- Outlet temperature trace
- Fan RPM trace
- Firmware thermal state
- Raw telemetry path

#### Related Recipe Phase

```text
thermal_observability_check
```

---

### Phase 6: Error Log Scan

#### Purpose

Collect firmware and BMC logs to identify hidden errors.

#### Why This Matters

A hardware or firmware issue may be visible in BMC or firmware logs before it appears as a test failure.

For EVT, these logs are important because they may reveal missing error classifications, generic reset reasons, or hidden warning patterns.

#### Expected Outputs

- BMC event log
- Firmware error log
- Reset reason code
- Debug log path

#### Related Recipe Phase

```text
error_log_scan_debug
```

## EVT Pass/Fail Interpretation

In EVT, a failure does not always mean the product should be rejected.

A failure may mean:

- The design has a real issue
- The firmware has a bug
- The test limit is still immature
- The station setup is not stable
- The DUT does not expose enough telemetry
- The test plan needs additional debug hooks

Therefore, EVT failures should be treated as engineering learning signals.

## EVT Error Code Strategy

EVT should still use structured error codes, but the purpose is slightly different from HVM.

In HVM, error codes support yield monitoring and containment.

In EVT, error codes support engineering classification and debug direction.

Example:

```text
error_id: E-THERM-001
error_code: THERM_FAN_RAMP_TIMEOUT
```

This error does not immediately prove that the fan hardware is bad.

It only indicates that the fan RPM did not reach the expected threshold within the test condition.

Possible next checks include:

- Check PWM command trace
- Check fan RPM trace
- Check firmware thermal state
- Check package temperature trace
- Check ambient temperature
- Check fan part number
- Check whether the EVT limit is still temporary

## EVT Exit Criteria

This EVT test plan can be considered useful if it helps answer:

- Can we identify the DUT and board revision clearly?
- Can firmware provide enough debug information?
- Can power, fan, and thermal behavior be observed over time?
- Can failures be mapped to meaningful error codes?
- Can raw telemetry be saved for engineering review?
- Are additional DFT hooks needed before moving to NPI/PVT?

## Relationship to YAML Recipe

This document explains the EVT test strategy.

The YAML recipe defines the executable structure:

```text
configs/evt_debug_recipe.yaml
```

The recipe contains:

- Metadata schema
- Execution policy
- Phase list
- Measurement definitions
- Limits
- Error IDs
- Error codes
- Required logs

A shared test runner should read the recipe and execute each enabled phase.

## My Takeaway

For EVT, I would not design the test only as a pass/fail screen.

I would design it as a debug and observability tool.

The key question is whether the test can help the team understand why a failure happened and what additional design, firmware, telemetry, or DFT improvement is needed before moving toward NPI or production.
