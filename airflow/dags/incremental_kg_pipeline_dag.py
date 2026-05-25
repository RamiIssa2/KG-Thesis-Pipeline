from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator


PROJECT_DIR = "/media/sf_KG_Thesis_Pipeline"


with DAG(
    dag_id="incremental_kg_pipeline",
    description="Incremental preprocessing pipeline for text-to-knowledge-graph datasets",
    start_date=datetime(2025, 12, 20),
    schedule=None,
    catchup=False,
    tags=["kg", "preprocessing", "incremental"],
) as dag:

    run_incremental_pipeline = BashOperator(
        task_id="run_incremental_pipeline",
        bash_command=f"cd {PROJECT_DIR} && python3 scripts/run_pipeline.py",
    )

    upload_outputs_to_minio = BashOperator(
        task_id="upload_outputs_to_minio",
        bash_command=f"cd {PROJECT_DIR} && MINIO_ENDPOINT=minio:9000 python3 scripts/upload_outputs_to_minio.py",
    )

    run_incremental_pipeline >> upload_outputs_to_minio