import json
from pathlib import Path
from typing import List


def replace_genwiki_entities(text: str, entities: List[str]) -> str:
    for idx, ent in enumerate(entities):
        text = text.replace(f"<ENT_{idx}>", ent)
    return text


def normalize_genwiki_file(input_path: Path, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    errors = 0

    print(f"Normalizing GenWiki file: {input_path.name}")

    with output_path.open("w", encoding="utf-8") as out_f:
        try:
            with input_path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            for entry in data:
                text = replace_genwiki_entities(entry["text"], entry["entities"])
                normalized = {
                    "source": "genwiki",
                    "source_file": input_path.name,
                    "triples": entry["graph"],
                    "text": text.strip(),
                    "lang": "en",
                }
                out_f.write(json.dumps(normalized, ensure_ascii=False) + "\n")
                count += 1

        except Exception:
            errors += 1

    print(f"GenWiki file normalized: {count:,} samples, errors: {errors:,}")
    return output_path


def normalize_genwiki(input_dir: Path, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    source_dir = input_dir / "train" / "full"

    with output_path.open("w", encoding="utf-8") as out_f:
        for path in sorted(source_dir.glob("*.json")):
            temp_path = output_path.parent / f"{path.stem}.tmp.jsonl"
            normalize_genwiki_file(path, temp_path)

            with temp_path.open("r", encoding="utf-8") as in_f:
                for line in in_f:
                    out_f.write(line)

            temp_path.unlink(missing_ok=True)

    return output_path