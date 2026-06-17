# 04. Dry-Run Runner Design



## Purpose



This document explains why this project includes a framework-independent dry-run runner before building an OpenHTF-based execution demo.



The dry-run runner is implemented in:



```text

scripts/dry_run_recipe.py

```



It reads the EVT debug recipe:



```text

configs/evt_debug_recipe.yaml

```



and optionally links failures to the centralized error catalog:



```text

configs/error_catalog.yaml

```



The goal is not to control real hardware. The goal is to validate the test flow, pass/fail logic, error mapping, and structured test record format before connecting the recipe to a real hardware test framework.



---



## Why a Dry-Run Runner Is Useful



A config-driven test system depends heavily on external recipe files. This is useful because limits, phases, logs, and execution policies can be changed without rewriting the runner.



However, config-driven design also introduces risk:



* A recipe may be valid YAML but still missing required test fields.

* A measurement may not define a usable pass/fail criterion.

* A recipe may reference an error code that does not exist in the error catalog.

* A test record format may not contain enough information for debugging.

* A test flow may look reasonable in a document but fail once executed by a runner.



The dry-run runner helps catch these problems early without requiring hardware, instruments, a test station, or OpenHTF integration.



In this project, the dry-run runner is used as an intermediate layer between static validation and real test execution.



---



## Relationship Between Validator and Dry-Run Runner



The validator checks whether the recipe is structurally valid.



```text

scripts/validate_recipe.py

```



It answers questions such as:



* Does the recipe contain the required top-level fields?

* Does every phase define a phase name, phase type, enabled flag, and fail behavior?

* Does every measurement define a name, type, error ID, and error code?

* Does every numeric measurement define at least one pass/fail criterion?

* Does every recipe error exist in the centralized error catalog?



The dry-run runner goes one step further.



```text

scripts/dry_run_recipe.py

```



It answers questions such as:



* Can the recipe be executed phase by phase?

* Can simulated measurements be evaluated against expected values and limits?

* Can the runner generate PASS and FAIL outcomes?

* Can a failed measurement be linked back to the error catalog?

* Can the runner produce a structured test record?



In short:



```text

validator = checks whether the recipe is well-defined

dry-run runner = checks whether the recipe can drive an execution flow

```



---



## Why This Step Does Not Use OpenHTF Yet



The dry-run runner intentionally does not use OpenHTF.



At this stage, the project is validating the internal recipe design, measurement evaluation logic, error catalog linkage, and structured output format. These are framework-independent concerns.



The dry-run runner focuses on this path:



```text

recipe

 -> phases

 -> measurements

 -> simulated values

 -> pass/fail evaluation

 -> error catalog lookup

 -> structured test record

```



This does not require real hardware control, instrument plugs, DUT communication, or OpenHTF phase execution.



OpenHTF becomes more relevant at the next layer, when the project starts modeling how a real test framework would manage:



* test phases

* measurements

* plugs or instrument interfaces

* test state

* attachments and logs

* test records

* phase outcomes



The dry-run runner is therefore not a replacement for OpenHTF. It is a preparation step before OpenHTF integration.



---



## Development Layering



This project uses a staged development model:



```text

Layer 1: Test plan documentation

Layer 2: Runner-readable YAML recipe

Layer 3: Recipe schema validation

Layer 4: Error catalog consistency check

Layer 5: Framework-independent dry-run runner

Layer 6: OpenHTF-based execution demo

Layer 7: Hardware or station integration concept

```



The current dry-run runner belongs to Layer 5.



This layering is intentional. It allows the project to validate as much logic as possible before depending on a hardware test framework or real equipment.



---



## What the Dry-Run Runner Simulates



The dry-run runner simulates measurement values based on the recipe.



For example, if a measurement is defined as:



```yaml

- name: "fan_rpm_after_pwm_70"

  type: "numeric"

  unit: "RPM"

  lower_limit: 6500

  error_id: "E-THERM-001"

  error_code: "THERM_FAN_RAMP_TIMEOUT"

```



then the dry-run runner can generate a passing value above the lower limit.



It can also inject a failure using:



```bash

python scripts/dry_run_recipe.py configs/evt_debug_recipe.yaml --error-catalog configs/error_catalog.yaml --inject-failure fan_rpm_after_pwm_70

```



When this failure is injected, the runner produces:



* a failed measurement result

* a failed phase result

* an overall failed test record

* the corresponding error description from the catalog

* the corresponding debug hint from the catalog



This confirms that the recipe, pass/fail logic, and error catalog are connected correctly.



---



## Example Commands



Run a normal dry run:



```bash

python scripts/dry_run_recipe.py configs/evt_debug_recipe.yaml --error-catalog configs/error_catalog.yaml

```



Run a dry run with an injected fan ramp failure:



```bash

python scripts/dry_run_recipe.py configs/evt_debug_recipe.yaml --error-catalog configs/error_catalog.yaml --inject-failure fan_rpm_after_pwm_70

```



Write the dry-run output to a JSON file:



```bash

python scripts/dry_run_recipe.py configs/evt_debug_recipe.yaml --error-catalog configs/error_catalog.yaml --inject-failure fan_rpm_after_pwm_70 --output outputs/evt_dry_run_failure_record.json

```



The `outputs/` folder is ignored by Git because it contains generated runtime artifacts rather than source files.



---



## Structured Test Record



The dry-run runner outputs a structured JSON test record.



The record includes:



* recipe name

* recipe version

* stage

* mode

* generated timestamp

* overall status

* phase-level results

* measurement-level results

* error ID

* error code

* error description

* debug hint

* required logs



This is important because a real test system should not only print human-readable messages. It should also generate structured records that can support debugging, reporting, yield analysis, and RCA.



---



## Design Principle



The dry-run runner follows this design principle:



```text

Do not wait for real hardware execution to discover that the test recipe, error mapping, or output structure is broken.

```



By validating the execution flow offline, the project becomes easier to debug, easier to test, and easier to extend.



This is especially important for large hardware test scripts, where failures may come from many sources:



* DUT behavior

* firmware behavior

* station setup

* sensor mapping

* test limits

* recipe configuration

* missing logs

* missing metadata

* error code inconsistency



The dry-run layer helps separate recipe and framework issues from real hardware issues.



---



## Relationship to Future OpenHTF Demo



The next step is to build an OpenHTF-based demo under:



```text

openhtf_demo/

```



That demo should reuse the same design concepts:



* phase-based execution

* measurement definitions

* error mapping

* structured records

* simulated or mocked DUT interfaces



The dry-run runner proves that the recipe can already drive a test flow. The OpenHTF demo will show how the same flow can be mapped into a hardware test framework style.



The intended progression is:



```text

evt_debug_recipe.yaml

 -> validate_recipe.py

 -> dry_run_recipe.py

 -> OpenHTF demo runner

```



This keeps the project modular. If the framework changes later, the recipe, catalog, and validation logic can still remain useful.









