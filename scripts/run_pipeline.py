import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

import config

from utils.hashing import file_sha256
from utils.registry import load_registry, save_registry

from preprocessors.normalize_tekgen import normalize_tekgen_file
from preprocessors.normalize_webnlg import normalize_webnlg_file
from preprocessors.normalize_genwiki import normalize_genwiki_file
from preprocessors.merge_datasets import merge_datasets
from preprocessors.clean_dataset import clean_dataset
from preprocessors.split_text_to_kg import split_text_to_kg


def ensure_dirs() -> None:
    for path in [
        config.NORMALIZED_DIR,
        config.NORMALIZED_BY_FILE_DIR,
        config.MERGED_DIR,
        config.FINAL_DIR,
        config.REGISTRY_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def scan_input_files() -> Dict[str, List[Path]]:
    return {
        "tekgen": sorted(config.TEKGEN_DIR.glob("*.tsv")),
        "webnlg": sorted((config.WEBNLG_DIR / "release_v3.0" / "en").rglob("*.xml")),
        "genwiki": sorted((config.GENWIKI_DIR / "train" / "full").glob("*.json")),
    }


def cached_output_path(dataset_name: str, raw_path: Path) -> Path:
    rel = raw_path.relative_to(config.BASE_DIR)
    safe_name = "__".join(rel.parts).replace(".", "_") + ".jsonl"
    return config.NORMALIZED_BY_FILE_DIR / dataset_name / safe_name


def detect_changes(files_by_dataset, registry) -> Tuple[bool, List[Tuple[str, Path, Path]]]:
    changed_files = []
    current_paths = set()

    active_prefixes = [
        str(config.TEKGEN_DIR.relative_to(config.BASE_DIR)),
        str((config.WEBNLG_DIR / "release_v3.0" / "en").relative_to(config.BASE_DIR)),
        str((config.GENWIKI_DIR / "train" / "full").relative_to(config.BASE_DIR)),
    ]

    for dataset_name, files in files_by_dataset.items():
        print(f"\nChecking {dataset_name}: {len(files)} files")

        for path in files:
            rel_path = str(path.relative_to(config.BASE_DIR))
            current_paths.add(rel_path)

            stat = path.stat()

            current_size = stat.st_size
            current_mtime = stat.st_mtime

            old_record = registry["files"].get(rel_path, {})

            same_size = old_record.get("size_bytes") == current_size
            same_mtime = old_record.get("mtime") == current_mtime

            cache_path = cached_output_path(dataset_name, path)

            if same_size and same_mtime and cache_path.exists():
                continue

            current_hash = file_sha256(path)
            old_hash = old_record.get("sha256")

            if old_hash != current_hash or not cache_path.exists():
                print(f"Changed/new file: {rel_path}")
                changed_files.append((dataset_name, path, cache_path))

            registry["files"][rel_path] = {
                "dataset": dataset_name,
                "sha256": current_hash,
                "size_bytes": current_size,
                "mtime": current_mtime,
                "cached_normalized_path": str(cache_path.relative_to(config.BASE_DIR)),
            }

    deleted_files = []

    for rel_path in list(registry["files"].keys()):
        in_active_scope = any(
            rel_path.startswith(prefix)
            for prefix in active_prefixes
        )

        if not in_active_scope:
            continue

        if rel_path not in current_paths:
            print(f"Deleted file detected: {rel_path}")

            old_cache = registry["files"][rel_path].get(
                "cached_normalized_path"
            )

            if old_cache:
                cache_path = config.BASE_DIR / old_cache
                cache_path.unlink(missing_ok=True)

            deleted_files.append(rel_path)

    for rel_path in deleted_files:
        del registry["files"][rel_path]

    changed = bool(changed_files or deleted_files)

    return changed, changed_files


def normalize_changed_files(changed_files: List[Tuple[str, Path, Path]]) -> None:
    for dataset_name, raw_path, cache_path in changed_files:
        if dataset_name == "tekgen":
            normalize_tekgen_file(raw_path, cache_path)
        elif dataset_name == "webnlg":
            normalize_webnlg_file(raw_path, cache_path)
        elif dataset_name == "genwiki":
            normalize_genwiki_file(raw_path, cache_path)
        else:
            raise ValueError(f"Unknown dataset type: {dataset_name}")


def get_all_cached_normalized_files() -> List[Path]:
    return sorted(config.NORMALIZED_BY_FILE_DIR.rglob("*.jsonl"))


def outputs_exist() -> bool:
    return (
        config.CLEANED_DATASET.exists()
        and config.TRAIN_JSONL.exists()
        and config.DEV_JSONL.exists()
        and config.TEST_JSONL.exists()
    )


def write_stats() -> None:
    stats = {}

    for path in [
        config.MERGED_DATASET,
        config.CLEANED_DATASET,
        config.TRAIN_JSONL,
        config.DEV_JSONL,
        config.TEST_JSONL,
    ]:
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                stats[path.name] = sum(1 for _ in f)

    with config.DATASET_STATS_FILE.open("w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    print(f"Stats saved: {config.DATASET_STATS_FILE}")
    print(stats)


def rebuild_from_cached_normalized() -> None:
    cached_paths = get_all_cached_normalized_files()

    if not cached_paths:
        raise RuntimeError("No cached normalized files found.")

    print(f"\nMerging cached normalized files: {len(cached_paths)} files")

    merge_datasets(cached_paths, config.MERGED_DATASET)

    clean_dataset(
        input_path=config.MERGED_DATASET,
        output_path=config.CLEANED_DATASET,
        min_tokens=config.MIN_TOKENS,
        max_tokens=config.MAX_TOKENS,
        min_triples=config.MIN_TRIPLES,
    )

    split_text_to_kg(
        input_path=config.CLEANED_DATASET,
        output_dir=config.FINAL_DIR,
        splits=config.SPLITS,
        random_seed=config.RANDOM_SEED,
    )

    write_stats()


def main() -> None:
    ensure_dirs()

    registry = load_registry(config.REGISTRY_FILE)
    files_by_dataset = scan_input_files()

    changed, changed_files = detect_changes(files_by_dataset, registry)

    if not changed and outputs_exist():
        print("\nNo input changes detected. Pipeline skipped.")
        return

    print("\nChanges detected. Running cached incremental preprocessing...")
    normalize_changed_files(changed_files)
    rebuild_from_cached_normalized()

    save_registry(config.REGISTRY_FILE, registry)

    print("\nIncremental cached pipeline completed.")


if __name__ == "__main__":
    main()