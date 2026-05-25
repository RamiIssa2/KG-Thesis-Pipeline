from pathlib import Path
from typing import List


def merge_datasets(input_paths: List[Path], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    total = 0

    with output_path.open("w", encoding="utf-8") as out_f:
        for path in input_paths:
            print(f"Merging: {path.name}")

            if not path.exists():
                print(f"Missing file skipped: {path}")
                continue

            with path.open("r", encoding="utf-8") as in_f:
                for line in in_f:
                    out_f.write(line)
                    total += 1

    print(f"Merged samples: {total:,}")
    return output_path