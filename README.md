# Snowflake Iceberg Pipeline

Python foundations for loading local CSV extracts through Amazon S3 into **Snowflake-managed Apache Iceberg tables**, with structured logging and an optional Grafana Loki destination.

> **Current status: configuration and logging scaffold.**
> At reviewed commit `b2d330e`, `main.py` loads environment variables, validates that required values are present, and exits. CSV discovery, S3 upload, Snowflake connections, table creation and data loading are **not implemented**. A successful run currently means configuration validation passed.

This README describes the code that exists and a proposed architecture for completing the ingestion workflow. The architecture is a design, not a deployed system.

## Why this repository exists

The intended use case is a repeatable batch ingestion job for CSV extracts, such as customer and insurance-policy data. A completed implementation would preserve source files in S3, load them into Snowflake-managed Iceberg tables, track which file versions succeeded, and expose reconciled data to SQL consumers.

Snowflake would manage the Iceberg catalog and write the table's Parquet data and metadata to an external volume in S3. The Python application would coordinate ingestion and validation.

## Implementation status

| Capability | Status in the reviewed code |
|---|---|
| Load environment variables using python-dotenv | Implemented |
| Validate required configuration values are present | Implemented at import time |
| Structured JSON logging with level and timestamp | Implemented in `logger.py` |
| Optional Loki handler | Implemented with limitations; see the review |
| Call the logger from the main entry point | Not implemented |
| Discover, parse or validate CSV contents | Not implemented |
| Upload files to S3 | Not implemented |
| Connect to Snowflake or create/load Iceberg tables | Not implemented |
| Schema management, manifests, audit ledger and replay protection | Proposed |
| Row reconciliation and complete-release publication | Proposed |
| AWS/Snowflake setup SQL or infrastructure as code | Not present |
| Scheduler, container deployment, dashboards, alerts and CI | Not present |
| Application tests | Not present in the reviewed commit; an offline review reproduction script accompanies these docs |

The installed SDK packages are dependencies for future work. Their presence in the requirements file does not mean their integrations have been implemented.

## Architecture

![Proposed architecture and implementation status](docs/architecture.png)

[Open SVG](docs/architecture.svg) · [Editable Mermaid](docs/architecture.mmd) · [Architecture decisions](docs/ARCHITECTURE.md)

The proposed data flow has these stages:

1. **Discover and validate.** Read a complete CSV extract from a source-accessible host; validate headers, field counts, encoding and file sizes.
2. **Land immutable inputs.** Upload content-addressed file versions to an S3 landing location. Publish a ready manifest only after all uploads succeed.
3. **Read through a stage.** Give Snowflake read access to the landing location using a storage integration and external stage.
4. **Load managed Iceberg.** Execute `COPY INTO` with `LOAD_MODE=FULL_INGEST`. Snowflake converts CSV input to Parquet and manages the Iceberg metadata in the external-volume location.
5. **Reconcile and publish.** Record loaded versions and row counts, then publish a complete batch for consumers. Retry decisions use durable state rather than an unguarded second append.
6. **Observe.** Emit structured run/file events and expose failure, freshness and duration signals to an operations platform.

Stages 1–5 and the integration of stage 6 into a runnable job remain implementation work. Airflow is optional orchestration; the initial worker can be an ordinary Python batch process.

### The two S3 access paths

| Path | Identity and responsibility |
|---|---|
| Python → S3 landing | Application AWS identity uploads original CSVs and ready manifests |
| Snowflake stage → S3 landing | Storage-integration role reads CSV input |
| Snowflake external volume → S3 table storage | Separate writer role manages Iceberg data and metadata |

Keep source inputs and Iceberg table files in separate buckets or nonoverlapping prefixes. This separation is proposed; the current code only declares one `AWS_BUCKET_NAME` setting.

## Repository contents

| File | Responsibility |
|---|---|
| `main.py` | Defines its own Config class, validates environment values, then exits |
| `config.py` | Defines another Config class; currently hardcodes a Windows source path |
| `logger.py` | Imports config, configures root logging/structlog, optionally adds Loki |
| `requirements.txt.txt` | Six pinned direct dependencies; the double extension is the actual filename |
| `.env.example` | Documentation template with placeholder values; no real credentials |
| `docs/ARCHITECTURE.md` | Proposed component boundaries, data contracts and implementation sequence |
| `docs/CODE_REVIEW.md` | Findings, evidence, priorities and validation limits |
| `review/verify_current_behavior.py` | Reproduces the reviewed behavior offline with dummy configuration |

## Run the existing scaffold

These steps exercise the code currently in the repository. They do not upload or load data.

### 1. Open the project and install dependencies

Clone/download the repository and open its root folder in VS Code or PyCharm. Select a Python **3.12** virtual environment; that is the interpreter used for this review.

Install from the actual dependency file:

```text
python -m pip install -r requirements.txt.txt
```

You can also select that file in your IDE's package-management UI. A conventional `requirements.txt` file does not exist yet.

### 2. Create local configuration

Copy `.env.example` to `.env` in the project root. The example uses non-secret placeholders so you can demonstrate presence validation without real AWS/Snowflake credentials. Replace the directory with the folder you intend to ingest later.

```dotenv
LOCAL_FILES_DIR=C:/data/massmutual/local_csv_files
SNOWFLAKE_USER=replace_me
SNOWFLAKE_PASSWORD=replace_me
SNOWFLAKE_ACCOUNT=replace_me
SNOWFLAKE_DATABASE=replace_me
SNOWFLAKE_STORAGE_INTEGRATION=replace_me
SNOWFLAKE_EXTERNAL_VOLUME=replace_me
AWS_BUCKET_NAME=replace-me
```

Keep credentials out of committed files. The existing `.gitignore` excludes `.env`.

### 3. Run main.py

Open `main.py` and select your IDE's Run action. The equivalent command is:

```text
python main.py
```

**Expected behavior today:**

- Missing required values produce a `ValueError` naming the missing settings.
- With all required values present, the process exits successfully with no normal console output.
- No directory inspection, network authentication, file upload or Snowflake operation occurs.

The current validation checks presence only. It does not verify that the source path exists, credentials work, or configured cloud resources exist.

### 4. Try console logging separately

Leave all `GRAFANA_LOKI_*` values empty for this local check. In a separate Python script/run configuration rooted at this project, execute:

```python
from logger import logger

logger.info("configuration_smoke_test", run_id="local-demo", rows=0)
```

In a fresh process, expect a JSON log record with the event, level and timestamp. Importing the logger also imports `config.py`, which requires the Snowflake/AWS configuration values even for console-only logging.

### 5. Run the offline review checks

```text
python review/verify_current_behavior.py
```

The script uses dummy configuration, disables dotenv file loading inside its isolated probes and intercepts the Loki HTTP call. It reports **nine observed behaviors** with no cloud calls.

These are characterization checks for the reviewed revision, not proof that ingestion works. After fixing an issue, the matching check is expected to require an update.

## Configuration reference

| Variable | Required by main.py | Default / current meaning |
|---|---|---|
| `LOCAL_FILES_DIR` | Yes | Read from environment by main.py; ignored by the Config in config.py |
| `SNOWFLAKE_USER` | Yes | Stored only; no connection is created |
| `SNOWFLAKE_PASSWORD` | Yes | Stored only; no other authentication mode is implemented |
| `SNOWFLAKE_ACCOUNT` | Yes | Account identifier placeholder |
| `SNOWFLAKE_WAREHOUSE` | No | `COMPUTE_WH` |
| `SNOWFLAKE_DATABASE` | Yes | Target database placeholder |
| `SNOWFLAKE_SCHEMA` | No | `PUBLIC` |
| `SNOWFLAKE_STORAGE_INTEGRATION` | Yes | Name placeholder; the object is not created or inspected |
| `SNOWFLAKE_EXTERNAL_VOLUME` | Yes | Name placeholder; the object is not created or inspected |
| `AWS_BUCKET_NAME` | Yes | Bucket name placeholder |
| `AWS_REGION` | No | `us-east-1` |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | No | Read but unused; no boto3 session is created |
| `GRAFANA_LOKI_URL` | No | Full Loki ingestion endpoint |
| `GRAFANA_LOKI_USER` | No | Loki Basic Auth username / Cloud Logs instance ID |
| `GRAFANA_LOKI_PASSWORD` | No | Loki credential / Grafana Cloud access-policy token |

The two Config definitions have different required fields and source-directory behavior. Consolidating them is a review finding, not a feature supplied by this documentation update.

## Optional Grafana Loki integration

For Grafana Cloud Logs, obtain the stack's Loki ingestion endpoint, instance ID and a **Cloud Access Policy token with logs:write permission**. This credential is different from a Grafana service-account token used for dashboard APIs.

Set all three `GRAFANA_LOKI_*` values only when you intend to send logs. The endpoint must include the ingestion path `/loki/api/v1/push`. The code constructs a Basic Auth tuple from the user/password settings.

Current limitations:

- `main.py` does not import or use the logger.
- Loki initialization is skipped if the root logger already has any handler.
- The pinned Loki client posts synchronously without an explicit HTTP timeout.
- The Loki environment label is always `production`.
- There are no dashboards, alerts, metrics, traces, queue buffering or delivery guarantees.

For unattended workloads, prefer application JSON logs shipped by a managed collector, or implement a bounded queue and explicit transport timeouts before wiring network logging into the ingestion path.

## Review summary and next implementation steps

Read [CODE_REVIEW.md](docs/CODE_REVIEW.md) before treating this repository as a functioning pipeline. The main blocker is that the ingestion entry point is missing.

Recommended order:

1. Consolidate configuration and make validation an explicit startup step.
2. Implement a real worker entry point with clear exit statuses and logged run IDs.
3. Add CSV contracts, stable naming, checksums and safe S3 publication.
4. Add reviewed IAM/setup SQL and a Snowflake connector with an approved authentication method.
5. Implement managed-Iceberg DDL/COPY, reconciliation and durable retry state.
6. Add release publication, failure/replay tests, schema-change policy and live cloud acceptance.
7. Repair logging initialization/transport and add deployment, monitoring and CI.

The proposed architecture assumes complete folder snapshots. Business-key upserts, CDC, typed Silver/Gold models and merging multiple chunks into one table require additional explicit contracts.

## Validation scope

Review baseline: [b2d330e0bc4b5bdb46201e818515384bac2b6f74](https://github.com/chidha2019/snowflake-iceberg-pipeline/tree/b2d330e0bc4b5bdb46201e818515384bac2b6f74), reviewed **October 26, 2026**.

The pinned dependencies installed successfully on Python 3.12.14 and `pip check` reported no broken requirements. Nine offline probes reproduced the documented behavior. No live AWS, Snowflake or Loki endpoint was contacted. Dependency installation compatibility is not a vulnerability assessment.

## References

- [Snowflake: load data into managed Iceberg tables](https://docs.snowflake.com/en/user-guide/tables-iceberg-load)
- [Snowflake: S3 storage integrations](https://docs.snowflake.com/en/user-guide/data-load-s3-config-storage-integration)
- [Snowflake: S3 external volumes](https://docs.snowflake.com/en/user-guide/tables-iceberg-configure-external-volume-s3)
- [Grafana Cloud access policies](https://grafana.com/docs/grafana-cloud/platform/security-and-account-management/security-and-access/authentication-and-permissions/access-policies/)
- [Grafana: Loki ingestion HTTP API](https://grafana.com/docs/learning-hub/intro-to-send-data/02-send-logs/11-http-api-logs/)
