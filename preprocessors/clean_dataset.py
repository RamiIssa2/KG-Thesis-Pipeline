import json
from pathlib import Path


def clean_dataset(
    input_path: Path,
    output_path: Path,
    min_tokens: int,
    max_tokens: int,
    min_triples: int,
) -> Path:

    output_path.parent.mkdir(parents=True, exist_ok=True)

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

    with input_path.open("r", encoding="utf-8") as in_f, \
         output_path.open("w", encoding="utf-8") as out_f:

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

            if token_count < min_tokens:
                skipped["too_short"] += 1
                continue

            if token_count > max_tokens:
                skipped["too_long"] += 1
                continue

            if triple_count < min_triples:
                skipped["too_few_triples"] += 1
                continue

            out_f.write(json.dumps(sample, ensure_ascii=False) + "\n")
            kept += 1

    print(f"Cleaned samples: {kept:,} / {total:,}")
    print(f"Skipped: {skipped}")

    return output_path