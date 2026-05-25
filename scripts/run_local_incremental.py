import json
import hashlib
import random
from pathlib import Path
from typing import Dict, List, Any

BASE_DIR = Path("/media/sf_KG_Thesis_Pipeline")

DATASETS_DIR = BASE_DIR / "datasets"
PIPELINE_DIR = BASE_DIR / "pipeline"

NORMALIZED_DIR = PIPELINE_DIR / "normalized"
MERGED_DIR = PIPELINE_DIR / "merged"
FINAL_DIR = PIPELINE_DIR / "final"
REGISTRY_DIR = PIPELINE_DIR / "registry"

REGISTRY_PATH = REGISTRY_DIR / "processed_files_registry.json"

MERGED_PATH = MERGED_DIR / "merged_kg_text_dataset.jsonl"
CLEANED_PATH = MERGED_DIR / "merged_cleaned_dataset.jsonl"

MIN_TOKENS = 5
MAX_TOKENS = 150
MIN_TRIPLES = 2

RANDOM_SEED = 42
SPLITS = {"train": 0.8, "dev": 0.1, "test": 0.1}


def ensure_dirs():
    for path in [NORMALIZED_DIR, MERGED_DIR, FINAL_DIR, REGISTRY_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_registry() -> Dict[str, Any]:
    if REGISTRY_PATH.exists():
        with REGISTRY_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {"files": {}}


def save_registry(registry: Dict[str, Any]):
    with REGISTRY_PATH.open("w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)


def scan_input_files() -> Dict[str, List[Path]]:
    return {
        "tekgen": sorted((DATASETS_DIR / "TekGen").glob("*.tsv")),
        "webnlg": sorted((DATASETS_DIR / "WebNLG" / "webnlg-dataset-master").rglob("*.xml")),
        "genwiki": sorted((DATASETS_DIR / "GenWiki" / "genwiki").rglob("*.json")),
    }


def detect_changes(files_by_dataset: Dict[str, List[Path]], registry: Dict[str, Any]) -> bool:
    changed = False

    for dataset_name, files in files_by_dataset.items():
        print(f"\nChecking {dataset_name}: {len(files)} files")

        for path in files:
            rel_path = str(path.relative_to(BASE_DIR))
            current_hash = file_sha256(path)
            old_hash = registry["files"].get(rel_path, {}).get("sha256")

            if old_hash != current_hash:
                print(f"Changed/new file: {rel_path}")
                changed = True

            registry["files"][rel_path] = {
                "dataset": dataset_name,
                "sha256": current_hash,
                "size_bytes": path.stat().st_size,
            }

    return changed


def normalize_tekgen() -> Path:
    output_path = NORMALIZED_DIR / "tekgen_normalized.jsonl"
    input_files = sorted((DATASETS_DIR / "TekGen").glob("*.tsv"))

    count = 0
    errors = 0

    with output_path.open("w", encoding="utf-8") as out_f:
        for path in input_files:
            split = path.stem.replace("quadruples-", "")
            print(f"Normalizing TekGen: {path.name}")

            with path.open("r", encoding="utf-8") as in_f:
                for line in in_f:
                    try:
                        data = json.loads(line)
                        normalized = {
                            "source": "tekgen",
                            "split": split,
                            "triples": data["triples"],
                            "text": data["sentence"].strip(),
                            "lang": "en",
                        }
                        out_f.write(json.dumps(normalized, ensure_ascii=False) + "\n")
                        count += 1
                    except Exception:
                        errors += 1

    print(f"TekGen normalized: {count:,} samples, errors: {errors:,}")
    return output_path


def parse_webnlg_triple(text: str) -> List[str]:
    return [part.strip().strip('"') for part in text.split("|")]


def normalize_webnlg() -> Path:
    import xml.etree.ElementTree as ET

    root_dir = DATASETS_DIR / "WebNLG" / "webnlg-dataset-master" / "release_v3.0" / "en"
    output_path = NORMALIZED_DIR / "webnlg_normalized.jsonl"

    count = 0
    errors = 0

    with output_path.open("w", encoding="utf-8") as out_f:
        for split in ["train", "dev", "test"]:
            split_dir = root_dir / split
            for xml_path in sorted(split_dir.rglob("*.xml")):
                try:
                    tree = ET.parse(xml_path)
                    root = tree.getroot()

                    for entry in root.findall(".//entry"):
                        triples = [
                            parse_webnlg_triple(mt.text)
                            for mt in entry.findall(".//modifiedtripleset/mtriple")
                            if mt.text
                        ]

                        for lex in entry.findall("lex"):
                            if lex.text:
                                normalized = {
                                    "source": "webnlg",
                                    "split": split,
                                    "triples": triples,
                                    "text": lex.text.strip(),
                                    "lang": "en",
                                }
                                out_f.write(json.dumps(normalized, ensure_ascii=False) + "\n")
                                count += 1
                except Exception:
                    errors += 1

    print(f"WebNLG normalized: {count:,} samples, errors: {errors:,}")
    return output_path


def replace_genwiki_entities(text: str, entities: List[str]) -> str:
    for idx, ent in enumerate(entities):
        text = text.replace(f"<ENT_{idx}>", ent)
    return text


def normalize_genwiki() -> Path:
    input_dir = DATASETS_DIR / "GenWiki" / "genwiki" / "train" / "full"
    output_path = NORMALIZED_DIR / "genwiki_normalized.jsonl"

    count = 0
    errors = 0

    with output_path.open("w", encoding="utf-8") as out_f:
        for json_path in sorted(input_dir.glob("*.json")):
            print(f"Normalizing GenWiki: {json_path.name}")
            try:
                with json_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)

                for entry in data:
                    text = replace_genwiki_entities(entry["text"], entry["entities"])
                    normalized = {
                        "source": "genwiki",
                        "triples": entry["graph"],
                        "text": text.strip(),
                        "lang": "en",
                    }
                    out_f.write(json.dumps(normalized, ensure_ascii=False) + "\n")
                    count += 1
            except Exception:
                errors += 1

    print(f"GenWiki normalized: {count:,} samples, errors: {errors:,}")
    return output_path


def merge_normalized(paths: List[Path]) -> Path:
    total = 0

    with MERGED_PATH.open("w", encoding="utf-8") as out_f:
        for path in paths:
            print(f"Merging: {path.name}")
            if not path.exists():
                print(f"Missing file, skipped: {path}")
                continue

            with path.open("r", encoding="utf-8") as in_f:
                for line in in_f:
                    out_f.write(line)
                    total += 1

    print(f"Merged samples: {total:,}")
    return MERGED_PATH


def clean_dataset() -> Path:
    seen_texts = set()
    total = 0
    kept = 0

    skipped = {
        "duplicate_text": 0,
        "too_short": 0,
        "too_long": 0,
        "too_few_triples": 0,
        "bad_json": 0,
    }

    with MERGED_PATH.open("r", encoding="utf-8") as in_f, CLEANED_PATH.open("w", encoding="utf-8") as out_f:
        for line in in_f:
            total += 1

            try:
                sample = json.loads(line)
                text = sample["text"].strip()
                triples = sample["triples"]
            except Exception:
                skipped["bad_json"] += 1
                continue

            token_count = len(text.split())
            triple_count = len(triples)

            if text in seen_texts:
                skipped["duplicate_text"] += 1
                continue
            seen_texts.add(text)

            if token_count < MIN_TOKENS:
                skipped["too_short"] += 1
                continue

            if token_count > MAX_TOKENS:
                skipped["too_long"] += 1
                continue

            if triple_count < MIN_TRIPLES:
                skipped["too_few_triples"] += 1
                continue

            out_f.write(json.dumps(sample, ensure_ascii=False) + "\n")
            kept += 1

    print(f"Cleaned samples: {kept:,} / {total:,}")
    print(f"Skipped: {skipped}")
    return CLEANED_PATH


def triples_to_string(triples: List[List[str]]) -> str:
    valid = []
    for triple in triples:
        if isinstance(triple, list) and len(triple) == 3:
            valid.append(" | ".join(str(x).strip() for x in triple))
    return " ;|; ".join(valid)


def split_text_to_kg():
    with CLEANED_PATH.open("r", encoding="utf-8") as f:
        dataset = [json.loads(line) for line in f]

    random.seed(RANDOM_SEED)
    random.shuffle(dataset)

    total = len(dataset)
    train_end = int(total * SPLITS["train"])
    dev_end = train_end + int(total * SPLITS["dev"])

    split_data = {
        "train": dataset[:train_end],
        "dev": dataset[train_end:dev_end],
        "test": dataset[dev_end:],
    }

    for split_name, rows in split_data.items():
        out_path = FINAL_DIR / f"{split_name}.jsonl"
        with out_path.open("w", encoding="utf-8") as out_f:
            for sample in rows:
                out_obj = {
                    "input": sample["text"],
                    "output": triples_to_string(sample["triples"]),
                }
                out_f.write(json.dumps(out_obj, ensure_ascii=False) + "\n")

        print(f"{split_name}: {len(rows):,} samples → {out_path}")


def write_stats():
    stats = {}

    for path in [MERGED_PATH, CLEANED_PATH, FINAL_DIR / "train.jsonl", FINAL_DIR / "dev.jsonl", FINAL_DIR / "test.jsonl"]:
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                stats[path.name] = sum(1 for _ in f)

    stats_path = PIPELINE_DIR / "dataset_stats.json"
    with stats_path.open("w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    print(f"Stats saved: {stats_path}")
    print(stats)


def main():
    ensure_dirs()

    registry = load_registry()
    files_by_dataset = scan_input_files()

    changed = detect_changes(files_by_dataset, registry)

    if not changed and CLEANED_PATH.exists() and (FINAL_DIR / "train.jsonl").exists():
        print("\nNo input changes detected. Pipeline skipped.")
        return

    print("\nChanges detected. Rebuilding dataset outputs...")

    normalized_paths = [
        normalize_tekgen(),
        normalize_webnlg(),
        normalize_genwiki(),
    ]

    merge_normalized(normalized_paths)
    clean_dataset()
    split_text_to_kg()
    write_stats()

    save_registry(registry)
    print("\nIncremental local pipeline completed.")


if __name__ == "__main__":
    main()