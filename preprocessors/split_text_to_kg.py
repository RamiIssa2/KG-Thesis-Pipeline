import json
import random
from pathlib import Path
from typing import Dict, List


def triples_to_string(triples: List[List[str]]) -> str:
    valid = []

    for triple in triples:
        if isinstance(triple, list) and len(triple) == 3:
            valid.append(" | ".join(str(x).strip() for x in triple))

    return " ;|; ".join(valid)


def split_text_to_kg(
    input_path: Path,
    output_dir: Path,
    splits: Dict[str, float],
    random_seed: int,
):
    output_dir.mkdir(parents=True, exist_ok=True)

    random.seed(random_seed)

    output_files = {
        "train": (output_dir / "train.jsonl").open("w", encoding="utf-8"),
        "dev": (output_dir / "dev.jsonl").open("w", encoding="utf-8"),
        "test": (output_dir / "test.jsonl").open("w", encoding="utf-8"),
    }

    counts = {"train": 0, "dev": 0, "test": 0}

    try:
        with input_path.open("r", encoding="utf-8") as in_f:
            for line in in_f:
                sample = json.loads(line)

                r = random.random()

                if r < splits["train"]:
                    split_name = "train"
                elif r < splits["train"] + splits["dev"]:
                    split_name = "dev"
                else:
                    split_name = "test"

                out_obj = {
                    "input": sample["text"],
                    "output": triples_to_string(sample["triples"]),
                }

                output_files[split_name].write(
                    json.dumps(out_obj, ensure_ascii=False) + "\n"
                )

                counts[split_name] += 1

    finally:
        for f in output_files.values():
            f.close()

    for split_name, count in counts.items():
        print(f"{split_name}: {count:,} samples -> {output_dir / f'{split_name}.jsonl'}")