# 01. OpenHTF Learning Notes

## Learning Goal

The goal of studying OpenHTF is not to simply learn a Python package API.

The goal is to understand the architecture of large hardware test scripts:

* How to break a large test flow into maintainable steps
* How to define measurements and pass/fail criteria clearly
* How to isolate hardware or DUT interfaces from test logic
* How to avoid hard-coded limits and station settings
* How to generate structured test records for debugging and yield analysis

## Key Concept 1: Test Phases

A large manufacturing test script should not be written as one long monolithic script.

Instead, the test flow should be separated into phases. Each phase should have a clear responsibility.

Example phases for an AI server test station:

* Identify DUT
* Check firmware version
* Measure power rails
* Run fan response test
* Run thermal ramp test
* Run functional smoke test
* Scan error logs
* Generate final report

### Why This Matters

Separating test phases improves:

* Readability
* Debuggability
* Code ownership
* Reuse across EVT, NPI, and production flows
* Failure isolation

If a test fails, the station should clearly report which phase failed and why.

## Key Concept 2: Measurements

A test script should not only print pass or fail.

Each test item should define the measurement being collected, including:

* Measurement name
* Unit
* Lower limit
* Upper limit
* Expected value
* Validator
* Error code if failed

Example:

```text
Measurement: power_rail_12v
Unit: V
Lower limit: 11.7
Upper limit: 12.3
Fail code: POWER_12V_OUT_OF_RANGE
```

### Why This Matters

Structured measurements help with:

* Pass/fail consistency
* Limit review
* Yield analysis
* Station correlation
* Debugging false fail and false pass

## Key Concept 3: Plugs / Hardware Abstraction

In a real test station, the script may need to communicate with:

* Power supplies
* Thermal chambers
* Fan controllers
* BMC interfaces
* Firmware diagnostic tools
* DUT sensors
* Serial, SSH, USB, or vendor APIs

The test logic should not be tightly coupled with these interfaces.

A hardware abstraction layer helps separate:

```text
What the test wants to do
```

from:

```text
How the station communicates with the hardware
```

### Why This Matters

This separation improves:

* Maintainability
* Reuse across stations
* Easier mock testing
* Easier replacement of instruments
* Cleaner failure isolation

For example, if a power supply model changes, ideally only the instrument interface layer should change, not every test phase.

## Key Concept 4: Configuration

Large test scripts should avoid hard-coded settings.

Configuration files can manage:

* Test limits
* Product revision
* Firmware version
* Station ID
* Instrument address
* Timeout settings
* Retry policy
* Component-specific limits

Example:

```text
fan_response_check:
  pwm_command: 70
  min_rpm: 6800
  timeout_sec: 10
```

### Why This Matters

Config-driven test design helps with:

* Version control
* Reviewable changes
* Easier collaboration
* Faster update for product revisions
* Safer handling of BOM or firmware changes

## Key Concept 5: Test Records and Traceability

A manufacturing test script should generate structured test records.

A useful test record should include:

* DUT ID
* Station ID
* Operator ID
* Timestamp
* Firmware version
* Product revision
* Component lot
* Test phase
* Measurement value
* Pass/fail result
* Error code
* Raw telemetry path if available

### Why This Matters

Structured records are necessary for:

* Yield monitoring
* Root-cause analysis
* Station-to-station correlation
* Shift or operator comparison
* Firmware regression detection
* Component lot issue detection

Without structured logs, yield-drop investigation becomes much harder.

## My Takeaway

OpenHTF is useful as a public reference because it shows that professional hardware test scripts need more than test logic.

A scalable test system needs clear structure around:

* Test sequence
* Measurement definition
* Hardware abstraction
* Configuration management
* Execution control
* Result logging



