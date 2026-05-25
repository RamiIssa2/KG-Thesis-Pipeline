import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

import config
from minio import Minio
from minio.error import S3Error


MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "192.168.31.240:9000")
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin123"
SECURE = False


UPLOADS = [
    (config.TRAIN_JSONL, "kg-preprocessed-data", "final/train.jsonl"),
    (config.DEV_JSONL, "kg-preprocessed-data", "final/dev.jsonl"),
    (config.TEST_JSONL, "kg-preprocessed-data", "final/test.jsonl"),
    (config.CLEANED_DATASET, "kg-preprocessed-data", "merged/merged_cleaned_dataset.jsonl"),
    (config.DATASET_STATS_FILE, "kg-metadata", "dataset_stats.json"),
    (config.REGISTRY_FILE, "kg-metadata", "processed_files_registry.json"),
]


def get_client() -> Minio:
    return Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=SECURE,
    )


def ensure_bucket(client: Minio, bucket_name: str) -> None:
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
        print(f"Created bucket: {bucket_name}")


def upload_file(client: Minio, local_path: Path, bucket: str, object_name: str) -> None:
    if not local_path.exists():
        print(f"Skipped missing file: {local_path}")
        return

    ensure_bucket(client, bucket)

    client.fput_object(
        bucket_name=bucket,
        object_name=object_name,
        file_path=str(local_path),
    )

    print(f"Uploaded: {local_path} -> {bucket}/{object_name}")


def upload_directory(client: Minio, local_dir: Path, bucket: str, prefix: str) -> None:
    if not local_dir.exists():
        print(f"Skipped missing directory: {local_dir}")
        return

    ensure_bucket(client, bucket)

    uploaded = 0

    for path in sorted(local_dir.rglob("*")):
        if not path.is_file():
            continue

        relative_path = path.relative_to(local_dir)
        object_name = f"{prefix}/{relative_path}".replace("\\", "/")

        client.fput_object(
            bucket_name=bucket,
            object_name=object_name,
            file_path=str(path),
        )

        uploaded += 1
        print(f"Uploaded: {path} -> {bucket}/{object_name}")

    print(f"Uploaded directory files: {uploaded:,} from {local_dir}")


def main() -> None:
    client = get_client()

    try:
        for local_path, bucket, object_name in UPLOADS:
            upload_file(client, local_path, bucket, object_name)

        print("\nUpload to MinIO completed.")

    except S3Error as e:
        print(f"MinIO error: {e}")
        raise


if __name__ == "__main__":
    main()