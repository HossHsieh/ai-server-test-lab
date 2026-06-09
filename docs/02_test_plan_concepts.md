# 02. Test Plan Concepts

## Learning Goal

The goal of this note is to understand how a manufacturing test plan is designed.

A test plan should not be just a list of test items. It should connect product risks to observable signals, measurements, pass/fail limits, error codes, and debug actions.

For this learning project, the device under test is a synthetic AI server node. The test station and all telemetry are simulated.

## Test Plan Design Principle

A useful test plan should answer the following questions:

1. What product or station risk are we trying to detect?
2. What signal or behavior can reveal this risk?
3. What measurement should the test script collect?
4. What pass/fail limit should be applied?
5. What error code should be generated if the test fails?
6. What debug action should be taken after failure?
7. What metadata should be logged for later root-cause analysis(RCA)?

## Example: Fan Response Risk

### Product Risk

The fan may not respond correctly to a pulse width modulation (PWM) command during thermal loading.
PS: PWM simulates an analog signal (like changing voltage) by rapidly switching a digital signal ON and OFF.

### Observable Signal

The fan RPM does not reach the expected threshold after the PWM command is applied.

### Measurement

```text
fan_rpm_after_pwm_70
```

### Pass/Fail Criteria

```text
fan_rpm_after_pwm_70 >= 6800 RPM within 10 seconds
```

### Error Code

```text
THERM_FAN_RAMP_TIMEOUT
```

### Debug Direction

If this test fails, possible causes include:

* Fan hardware issue
* Fan vendor or part number change
* Firmware fan control regression
* Station airflow fixture issue
* High ambient temperature
* Test timeout too short

This example shows why a test plan must include not only the measurement, but also the expected debug direction.

## EVT Test Plan Focus

In EVT, the goal is not only to screen pass or fail units. The goal is also to find design, firmware, and testability gaps.

EVT tests should collect richer telemetry than production tests.

Important EVT questions:

* Can the DUT expose enough telemetry for debugging?
* Are firmware error codes specific enough?
* Can power, thermal, and fan behavior be monitored over time?
* Can the test script separate product failure from station failure?
* Are the current test limits meaningful or only temporary engineering limits?

## NPI / PVT Test Plan Focus

In NPI or PVT, the focus shifts toward station readiness and repeatability.

Important questions:

* Can the same unit produce consistent results on the same station?
* Can different stations produce correlated results?
* Can golden units consistently pass?
* Can known-bad units consistently fail?
* Are borderline units handled carefully?
* Are test limits stable enough for production use?

## High Volume Production Test Plan Focus

In high-volume production, the focus is yield monitoring, cycle time, false fail control, and traceability.

Important questions:

* Can the test catch real failures without creating too many false fails?
* Can logs support yield analysis by station, shift, operator, firmware version, and component lot?
* Can error codes support fast root-cause analysis?
* Can test limits be updated safely without changing source code?
* Can production issues be contained quickly?

## Required Test Record Metadata

A production-like test record should include:

* DUT ID
* Station ID
* Operator ID
* Shift
* Timestamp
* Product revision
* Firmware version
* Component lot
* Test plan version
* Test phase
* Measurement name
* Measurement value
* Unit
* Lower limit
* Upper limit
* Pass/fail result
* Error ID
* Error code
* Error message

## Error Code Design

For this project, I use a hybrid error-code design:

```text
error_id: stable machine-readable ID
error_code: readable engineering code
error_message: human-readable explanation
```

Example:

```text
error_id: E-THERM-001
error_code: THERM_FAN_RAMP_TIMEOUT
error_message: Fan RPM did not reach the required threshold within timeout.
```

This design keeps the log readable for engineers while still allowing stable long-term tracking in dashboards or databases.

## My Takeaway

A strong test plan connects product risk, measurement design, pass/fail logic, structured logging, and debug action.

For a large test script, the test plan should drive the script structure. The script should not hide test limits, assumptions, or failure definitions inside hard-coded logic.
