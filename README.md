# AI Server Test Development Learning Lab

## Purpose

This repository is a simulation-based learning project for understanding manufacturing test development concepts for AI server hardware.

The goal is not to replicate any real system, product, test station, or internal manufacturing process. Instead, the purpose is to practice transferable engineering concepts, including:

* Large test script architecture
* Config-driven test plans
* Measurement definition and pass/fail criteria
* DUT and instrument abstraction
* Structured logging and traceability
* Golden-unit and known-bad-unit validation
* Station qualification and correlation
* Yield-drop investigation and root-cause analysis

## Why This Project

My background is in semiconductor manufacturing. Since manufacturing test development is an adjacent but different domain, I created this project to build a hands-on learning bridge.

Instead of only reading about test development concepts, I use synthetic AI-server test scenarios to practice how a test engineer may think about:

* How to structure a scalable test script
* How to define test coverage and limits
* How to separate product failures from station failures
* How to detect false fail and false pass risks
* How to investigate production yield drops using structured data

## OpenHTF as a Learning Reference

I use OpenHTF as a public reference architecture for hardware test automation. The goal is not to treat the framework as a black box, but to understand why large hardware test scripts are often organized around concepts such as:

* Test phases
* Measurements
* Plugs or hardware interfaces
* Configuration
* Test records
* Execution control

These concepts help avoid monolithic scripts and make test logic more maintainable, reusable, and traceable.

## Project Scope

This project focuses on a simplified AI server test station simulation. The synthetic device under test may include:

* Firmware version check
* Power rail measurement
* Fan response test
* Thermal ramp test
* Cooling sensor check
* Functional smoke test
* Error log scan

All test data, failure modes, telemetry, and station behavior are synthetic.

## Planned Modules

### 1\. OpenHTF Learning Notes

Summarize the large-test-script concepts learned from OpenHTF and map them to general manufacturing test development principles.

### 2\. Test Plan Design

Create a simplified EVT / NPI test plan for an AI server test station, including test objectives, measurements, limits, and expected logs.

### 3\. OpenHTF-Inspired Demo

Build a small Python-based demo that executes synthetic test phases, records measurements, checks pass/fail criteria, and generates structured logs.

### 4\. Station Qualification

Practice golden-unit, known-bad-unit, and borderline-unit validation to separate station issues from product issues.

### 5\. Root-Cause Analysis Cases

Create synthetic RCA cases for different product stages:

* EVT / DFT observability gap
* NPI station correlation issue
* High-volume production firmware regression
* Component lot change and hard-coded test limit issue

## Current Progress

* Initialized project structure.
* Added OpenHTF learning notes.
* Added stage-based test plan concepts.
* Added EVT test plan for debug and observability.
* Added runner-readable EVT recipe.
* Added recipe schema validator.

## Quick Validation

* Install dependencies:
pip install -r requirements.txt
* Validate EVT recipe:
python scripts/validate\_recipe.py configs/evt\_debug\_recipe.yaml

## Disclaimer

This project is for learning  only.

It does not represent any real system, product, station design, manufacturing process, or internal test methodology.

All assumptions, telemetry, failure modes, and data are synthetic. In a real manufacturing environment, these assumptions would need to be validated with product specifications, hardware owners, firmware owners, factory engineers, historical production data, calibration results, and safety requirements.

