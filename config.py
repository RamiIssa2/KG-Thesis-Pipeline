from pathlib import Path

BASE_DIR = Path("/media/sf_KG_Thesis_Pipeline")

DATASETS_DIR = BASE_DIR / "datasets"
PIPELINE_DIR = BASE_DIR / "pipeline"

NORMALIZED_DIR = PIPELINE_DIR / "normalized"
NORMALIZED_BY_FILE_DIR = PIPELINE_DIR / "normalized_by_file"
MERGED_DIR = PIPELINE_DIR / "merged"
FINAL_DIR = PIPELINE_DIR / "final"
REGISTRY_DIR = PIPELINE_DIR / "registry"

TEKGEN_DIR = DATASETS_DIR / "TekGen"
WEBNLG_DIR = DATASETS_DIR / "WebNLG" / "webnlg-dataset-master"
GENWIKI_DIR = DATASETS_DIR / "GenWiki" / "genwiki"

TEKGEN_NORMALIZED = NORMALIZED_DIR / "tekgen_normalized.jsonl"
WEBNLG_NORMALIZED = NORMALIZED_DIR / "webnlg_normalized.jsonl"
GENWIKI_NORMALIZED = NORMALIZED_DIR / "genwiki_normalized.jsonl"

MERGED_DATASET = MERGED_DIR / "merged_kg_text_dataset.jsonl"
CLEANED_DATASET = MERGED_DIR / "merged_cleaned_dataset.jsonl"

TRAIN_JSONL = FINAL_DIR / "train.jsonl"
DEV_JSONL = FINAL_DIR / "dev.jsonl"
TEST_JSONL = FINAL_DIR / "test.jsonl"

REGISTRY_FILE = REGISTRY_DIR / "processed_files_registry.json"

MIN_TOKENS = 5
MAX_TOKENS = 150
MIN_TRIPLES = 2

RANDOM_SEED = 42
SPLITS = {
    "train": 0.8,
    "dev": 0.1,
    "test": 0.1,
}

DATASET_STATS_FILE = PIPELINE_DIR / "dataset_stats.json"