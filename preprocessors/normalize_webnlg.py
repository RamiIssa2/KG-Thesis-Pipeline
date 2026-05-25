import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List


def parse_webnlg_triple(text: str) -> List[str]:
    return [part.strip().strip('"') for part in text.split("|")]


def infer_webnlg_split(path: Path) -> str:
    parts = [p.lower() for p in path.parts]
    if "train" in parts:
        return "train"
    if "dev" in parts:
        return "dev"
    if "test" in parts:
        return "test"
    return "unknown"


def normalize_webnlg_file(input_path: Path, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    errors = 0
    split = infer_webnlg_split(input_path)

    print(f"Normalizing WebNLG file: {input_path.name}")

    with output_path.open("w", encoding="utf-8") as out_f:
        try:
            tree = ET.parse(input_path)
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
                            "source_file": input_path.name,
                            "triples": triples,
                            "text": lex.text.strip(),
                            "lang": "en",
                        }
                        out_f.write(json.dumps(normalized, ensure_ascii=False) + "\n")
                        count += 1

        except Exception:
            errors += 1

    print(f"WebNLG file normalized: {count:,} samples, errors: {errors:,}")
    return output_path


def normalize_webnlg(input_dir: Path, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    root_dir = input_dir / "release_v3.0" / "en"

    with output_path.open("w", encoding="utf-8") as out_f:
        for path in sorted(root_dir.rglob("*.xml")):
            temp_path = output_path.parent / f"{path.stem}.tmp.jsonl"
            normalize_webnlg_file(path, temp_path)

            with temp_path.open("r", encoding="utf-8") as in_f:
                for line in in_f:
                    out_f.write(line)

            temp_path.unlink(missing_ok=True)

    return output_path