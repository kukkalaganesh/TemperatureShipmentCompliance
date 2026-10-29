# Temperature Shipment Compliance System

## Overview

The Temperature Shipment Compliance System is a Python and MySQL data engineering project designed to monitor temperature-controlled shipments and evaluate compliance with product-specific cold-chain requirements.

The system combines shipment records, temperature logger readings, chain-of-custody events, route stops, threshold policies, and exception records to identify temperature excursions and produce auditable compliance decisions.

The current dataset contains 5,000 shipments and more than 1.16 million synthetic temperature readings.

## Project Objectives

- Store shipment, product, packaging, logger, and policy information in a relational database.
- Generate time-series temperature readings for shipments.
- Maintain shipment custody, route, and status history.
- Detect out-of-range temperature readings.
- Compare excursion durations with product-specific policy limits.
- Generate compliance results, excursion reports, and exception records.
- Validate detection against known test cases and automated tests.

## Technology Stack

- Python
- MySQL
- SQL
- mysql-connector-python
- python-dotenv
- Python unittest
- CSV-based ground-truth validation

## Architecture

```text
Reference Data
      |
      v
Shipment and Logger Assignments
      |
      v
Temperature Reading Generation
      |
      v
Shipment Events and Route History
      |
      v
Controlled Temperature Anomalies
      |
      v
Compliance Evaluation
      |
      +----> Excursion Reports
      |
      +----> Compliance Results
      |
      +----> Exception Events
      |
      v
Data Quality and Ground-Truth Validation
      |
      v
Automated Tests
```

## Database

The MySQL database is named `cold_chain_compliance`.

The schema includes tables for:

- Products and packaging
- Threshold policies and lots
- Temperature loggers
- Shipments and logger assignments
- Temperature readings
- Chain-of-custody events
- Route stops and shipment status history
- Excursion reports
- Compliance results
- Exception events

## Product Temperature Policies

| Product | Minimum | Maximum | Maximum excursion duration |
|---|---:|---:|---:|
| Vaccine A | 2°C | 8°C | 30 minutes |
| Biologic B | 2°C | 8°C | 20 minutes |
| Frozen Sample C | -25°C | -15°C | 15 minutes |

The system evaluates readings against the policy associated with each shipment.

## Current Dataset

The current generated dataset includes:

- 3 products
- 3 packaging configurations
- 3 threshold policies
- 3 lots
- 1,000 loggers
- 5,000 shipments
- 5,000 logger assignments
- 1,169,474 temperature readings
- 15,000 custody events
- 15,000 route stops
- 15,000 shipment status events
- 15 excursion reports
- 5,000 compliance results
- 15 exception events

These figures describe the current generated dataset and may change if the pipeline is regenerated.

## Compliance Results

The initial validated run produced:

| Compliance status | Shipments |
|---|---:|
| Compliant | 4,985 |
| Non-compliant | 15 |
| Review required | 0 |
| Total | 5,000 |

Fifteen controlled anomaly cases were injected across the three products. The ground-truth validation detected all 15 expected non-compliant shipments, with zero false positives and zero false negatives in this controlled test.

## Project Structure

```text
TemperatureShipmentCompliance/
├── data/
│   └── ground_truth/
│       └── anomaly_ground_truth.csv
├── src/
│   ├── generate_temperature_readings.py
│   ├── generate_shipment_events.py
│   ├── generate_anomalies.py
│   ├── compliance_engine.py
│   ├── generate_exception_events.py
│   ├── validate_ground_truth.py
│   └── validate_data_quality.py
├── tests/
│   └── test_pipeline_validation.py
├── db_connection.py
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

The structure above represents the main files created during the workflow. Include other existing scripts or SQL schema files in the final repository as appropriate.

## Setup

### 1. Install Python

Install a compatible Python 3 version and create a virtual environment.

### 2. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```text
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_local_password
DB_NAME=cold_chain_compliance
```

Replace the example password with your local MySQL password. Never commit `.env` or credentials to GitHub.

### 4. Create the database

Create the `cold_chain_compliance` database and execute the project's SQL schema before running the data-generation scripts.

### 5. Run the pipeline

Run each script from the project root in the following order, after confirming that its prerequisites and database tables are available:

```powershell
python src/generate_temperature_readings.py
python src/generate_shipment_events.py
python src/generate_anomalies.py
python src/compliance_engine.py
python src/generate_exception_events.py
python src/validate_ground_truth.py
python src/validate_data_quality.py
```

Reference-data, logger, shipment, and logger-assignment generation must be completed before temperature reading generation.

**Important:** Some scripts deliberately stop if their destination tables already contain records. Do not blindly rerun the full pipeline against a populated database. Use a clean development database or implement an explicit reset and rerun procedure first.

## Testing

Run the automated integration tests from the project root:

```powershell
python -m unittest discover -s tests -v
```

The current test suite checks reading coverage, compliance-result coverage, duplicate reading IDs, expected compliance counts, ground-truth detection, and exception linkage.

## Data Quality

The current validation checks cover:

- Missing temperature readings
- Missing logger assignments
- Invalid logger references
- Expected out-of-range readings
- Missing compliance results
- Missing custody events
- Missing route stops
- Missing exceptions for non-compliant shipments
- Duplicate reading IDs

The current data-quality validation passed all implemented checks.

## Important Limitations

- The dataset is synthetic and is not evidence of real-world shipment performance.
- Controlled anomaly detection validates the implemented scenarios, not every possible excursion pattern.
- Temperature readings are sampled at ten-minute intervals; the exact physical start and end of an excursion cannot be known from those samples alone.
- The current compliance engine should be extended with explicit handling for suspect and invalid readings, missing data intervals, logger calibration uncertainty, policy effective dates, and more complex excursion patterns.
- Operational deployment would require stronger monitoring, access control, audit logging, and performance testing.

## Future Enhancements

- Dashboard for shipment compliance and excursion trends
- More comprehensive anomaly scenarios and edge-case tests
- Policy version and effective-date validation
- Detection of missing readings and logger calibration issues
- Performance optimization for large-scale datasets
- Automated pipeline orchestration and reporting

## Disclaimer

This project is intended for software engineering, data engineering, and cold-chain compliance analytics demonstration. It is not a validated medical, pharmaceutical, or regulatory decision system.
