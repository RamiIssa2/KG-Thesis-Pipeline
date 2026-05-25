import json
from pathlib import Path


def normalize_tekgen_file(input_path: Path, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    split = input_path.stem.replace("quadruples-", "")
    count = 0
    errors = 0

    print(f"Normalizing TekGen file: {input_path.name}")

    with input_path.open("r", encoding="utf-8") as in_f, output_path.open("w", encoding="utf-8") as out_f:
        for line in in_f:
            try:
                data = json.loads(line)
                normalized = {
                    "source": "tekgen",
                    "split": split,
                    "source_file": input_path.name,
                    "triples": data["triples"],
                    "text": data["sentence"].strip(),
                    "lang": "en",
                }
                out_f.write(json.dumps(normalized, ensure_ascii=False) + "\n")
                count += 1
            except Exception:
                errors += 1

    print(f"TekGen file normalized: {count:,} samples, errors: {errors:,}")
    return output_path


def normalize_tekgen(input_dir: Path, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as out_f:
        for path in sorted(input_dir.glob("*.tsv")):
            temp_path = output_path.parent / f"{path.stem}.tmp.jsonl"
            normalize_tekgen_file(path, temp_path)

            with temp_path.open("r", encoding="utf-8") as in_f:
                for line in in_f:
                    out_f.write(line)

            temp_path.unlink(missing_ok=True)

    return output_path