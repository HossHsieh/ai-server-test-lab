# 02. Test Plan Concepts

## Learning Goal

The goal of this note is to understand how a manufacturing test plan is designed.

A test plan should not be just a list of test items. It should connect product risks to observable signals, measurements, pass/fail limits, error codes, debug actions, and required logs.

For this learning project, the device under test is a synthetic AI server node. The test station and all telemetry are simulated.

The key learning is that a test plan should change by product stage. EVT, NPI/PVT, and HVM do not have the same focus.

## Acronym Notes

| Acronym | Full Name                       | Meaning in This Project                                                                       |
| ------- | ------------------------------- | --------------------------------------------------------------------------------------------- |
| DUT     | Device Under Test               | The hardware unit being tested                                                                |
| EVT     | Engineering Validation Test     | Early engineering stage focused on design, firmware, and testability debugging                |
| DFT     | Design for Test                 | Design choices that make the product easier to test and debug                                 |
| NPI     | New Product Introduction        | Stage where the product and test process are prepared for manufacturing                       |
| PVT     | Production Validation Test      | Stage focused on validating production process and station readiness                          |
| HVM     | High Volume Manufacturing       | Mass production stage focused on yield, cycle time, traceability, and containment             |
| RCA     | Root-Cause Analysis             | Investigation process to identify the real cause of a failure                                 |
| PWM     | Pulse Width Modulation          | A digital signal rapidly switched ON/OFF to emulate analog control, such as fan speed control |
| RPM     | Revolutions Per Minute          | Fan rotation speed                                                                            |
| BMC     | Baseboard Management Controller | Management controller used in servers to monitor hardware status and logs                     |
| FW      | Firmware                        | Low-level software running on hardware devices                                                |

## Test Plan Design Principle

A useful test plan should answer the following questions:

1. What product, firmware, station, or process risk are we trying to detect?
2. What signal or behavior can reveal this risk?
3. What measurement should the test script collect?
4. What pass/fail limit should be applied?
5. What error code should be generated if the test fails?
6. What debug action should be taken after failure?
7. What metadata should be logged for later root-cause analysis?
8. Does the test plan fit the current product stage?

## Stage-Based Test Plan Mindset

The same product risk may require different test strategies at different stages.

For example, a fan response issue can appear in EVT, NPI/PVT, or HVM, but the test plan should emphasize different things.

| Stage     | Main Goal                                     | Test Plan Focus                                                                              |
| --------- | --------------------------------------------- | -------------------------------------------------------------------------------------------- |
| EVT       | Find design, firmware, and observability gaps | Collect rich telemetry and raw traces                                                        |
| NPI / PVT | Validate station readiness and repeatability  | Use golden units, known-bad units, borderline units, repeatability, and station correlation  |
| HVM       | Screen production units and support yield RCA | Optimize cycle time, structured logging, stable error codes, and metadata for yield analysis |

## Example: Fan Response Risk

### Product Risk

The fan may not respond correctly to a pulse width modulation (PWM) command during thermal loading.

PS: PWM simulates an analog signal, such as changing voltage, by rapidly switching a digital signal ON and OFF.

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

## Same Risk, Different Stage

### EVT Version

In EVT, the fan response test should collect rich telemetry because the goal is to understand the behavior and find testability gaps.

For example, the test should log:

* PWM command trace
* Fan RPM trace
* Package temperature trace
* Inlet temperature trace
* Firmware thermal state
* Firmware event log
* Sensor readback timing
* Raw telemetry file path

In EVT, the question is not only:

```text
Did the fan pass or fail?
```

The more important questions are:

```text
Do we have enough telemetry to understand why it failed?
Can firmware expose the right debug information?
Can the test separate fan hardware, firmware, thermal, and station effects?
```

### NPI / PVT Version

In NPI or PVT, the fan response test should focus on station readiness and repeatability.

For example, the test plan should include:

* Golden unit repeated test
* Known-bad unit detection
* Borderline unit sensitivity check
* Station-to-station comparison
* Fixture ID tracking
* Calibration status
* Repeat count
* Measurement variation

In NPI/PVT, the key questions are:

```text
Can the same unit produce consistent results on the same station?
Can different stations produce correlated results?
Does the issue follow the unit or follow the station?
Can the station reliably detect known-bad units without failing golden units?
```

### HVM Version

In HVM, the fan response test should be production-friendly.

The test may collect less raw trace than EVT, but it must keep enough structured metadata for yield analysis.

For example, the test should log:

* DUT serial number
* Station ID
* Operator ID
* Shift
* Firmware version
* Fan part number
* Fan component lot
* Test plan version
* Error ID
* Error code
* Cycle time
* Retest count

In HVM, the key questions are:

```text
Can the test catch real failures quickly?
Can we avoid excessive false fails?
If yield drops, can we segment the data by station, shift, firmware version, and component lot?
Can we contain the issue quickly?
```

## EVT Test Plan Focus

In EVT, the goal is not only to screen pass or fail units. The goal is also to find design, firmware, and testability gaps.

EVT tests should collect richer telemetry than production tests.

Important EVT questions:

* Can the DUT expose enough telemetry for debugging?
* Are firmware error codes specific enough?
* Can power, thermal, and fan behavior be monitored over time?
* Can the test script separate product failure from station failure?
* Are the current test limits meaningful, or are they temporary engineering limits?
* Are additional DFT hooks needed?

### EVT Metadata Focus

EVT traceability is still important, but the metadata is mainly for engineering debug, not production yield monitoring.

Useful EVT metadata may include:

* Engineering unit ID
* Board revision
* Product revision
* Firmware build ID
* Test script version
* Bench ID
* Instrument ID
* Sensor configuration
* Raw telemetry path
* Debug log path
* Test engineer note

Operator ID and shift are usually not the main analysis dimensions in EVT.

## NPI / PVT Test Plan Focus

In NPI or PVT, the focus shifts toward station readiness, repeatability, and production preparation.

Important questions:

* Can the same unit produce consistent results on the same station?
* Can different stations produce correlated results?
* Can golden units consistently pass?
* Can known-bad units consistently fail?
* Are borderline units handled carefully?
* Are test limits stable enough for production use?
* Is the station calibration status controlled?
* Is the fixture repeatable?
* Is the test cycle time close to production requirements?

### NPI / PVT Metadata Focus

Useful NPI / PVT metadata may include:

* DUT ID
* Golden unit ID
* Known-bad unit ID
* Borderline unit ID
* Station ID
* Fixture ID
* Calibration date
* Test software version
* Test plan version
* Repeat count
* Measurement value
* Pass/fail result
* Error ID
* Error code
* Operator ID, if operator variation is being studied

In NPI/PVT, station ID and fixture ID become much more important because the test process itself is being qualified.

## HVM Test Plan Focus

In high-volume manufacturing, the focus is production screening, yield monitoring, cycle time, false fail control, and traceability.

Important HVM questions:

* Can the test catch real failures without creating too many false fails?
* Can logs support yield analysis by station, shift, operator, firmware version, and component lot?
* Can error codes support fast root-cause analysis?
* Can test limits be updated safely without changing source code?
* Can production issues be contained quickly?
* Can the test run within the required cycle time?
* Is the retest policy clearly defined?

### HVM Metadata Focus

A production-like HVM test record should include:

* DUT serial number
* Station ID
* Operator ID
* Shift
* Timestamp
* Product revision
* Firmware version
* Component part number
* Component lot
* Test plan version
* Test software version
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
* Retest count
* Cycle time

In HVM, metadata is critical because root-cause analysis often depends on segmentation.

Example segmentation dimensions:

* By station
* By shift
* By operator
* By firmware version
* By component lot
* By product revision
* By test software version
* By time window

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

### Why Not Only Use Human-Readable Messages?

A message like this is easy to read:

```text
Fan RPM did not reach the required threshold within timeout.
```

However, it is not ideal for long-term data analysis because the wording may change.

A stable error ID such as:

```text
E-THERM-001
```

is better for dashboards, databases, and yield trend monitoring.

### Why Not Only Use Numeric Error IDs?

A numeric or encoded ID is stable, but it is not easy for engineers to understand during debug.

Therefore, this project keeps both:

```text
E-THERM-001
THERM_FAN_RAMP_TIMEOUT
```

The first is stable for systems. The second is readable for engineers.

## What Should Not Be Hidden in Code

For a large test script, the following items should not be hidden inside hard-coded Python logic:

* Test limits
* Expected firmware version
* Component-specific limits
* Timeout settings
* Retry policy
* Error code definition
* Required logs
* Stage-specific test behavior

These should be managed through configuration files, test plan documents, or reviewed data tables.

## My Takeaway

A strong test plan connects product risk, measurement design, pass/fail logic, structured logging, and debug action.

A stronger test plan also changes by product stage.

In EVT, the test plan should focus on observability and engineering debug.

In NPI/PVT, the test plan should focus on station qualification, repeatability, and correlation.

In HVM, the test plan should focus on production screening, cycle time, traceability, and yield root-cause analysis.

For a large test script, the test plan should drive the script structure. The script should not hide test limits, assumptions, or failure definitions inside hard-coded logic.
