# KG Thesis Pipeline

## Description

This repository contains the implementation developed for the master's thesis:

"Исследование методов построения графов знаний из текстовых данных"

The project implements a reproducible preprocessing and orchestration pipeline for constructing unified text-to-knowledge-graph datasets from heterogeneous sources.

----------
## Implemented Components

- Dataset normalization and cleaning
- Unified JSONL conversion
- Incremental preprocessing pipeline
- Apache Airflow orchestration
- MinIO object storage integration
- Dataset merging and splitting
- Metadata and registry tracking
----------

## Repository Structure

- `airflow/` — Airflow DAGs and orchestration
- `scripts/` — pipeline execution scripts
- `preprocessors/` — dataset preprocessing modules
- `utils/` — utility functions
- `datasets/` — dataset references and download instructions
- `methods/` — references to evaluated methods
----------

## Datasets

The datasets used in this work are not included in the repository due to size limitations.

See:
- `datasets/README.md`

----------

## Methods

The evaluated methods and their references are listed in:
- `methods/README.md`

----------

## Installation

```bash
pip install -r requirements.txt

```

---

## Running the Pipeline

### Local execution

```bash
python3 scripts/run_pipeline.py

```

### Upload outputs to MinIO

```bash
python3 scripts/upload_outputs_to_minio.py

```

### Airflow DAG

The Airflow DAG is located at:

```text
airflow/dags/incremental_kg_pipeline_dag.py

```

---

## Reproducibility

The repository contains all scripts required to reproduce:
- dataset normalization,
- incremental preprocessing,
- orchestration,
- metadata generation,
- and MinIO synchronization."# KG-Thesis-Pipeline" 
