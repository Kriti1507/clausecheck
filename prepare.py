"""Day 1. Download CUAD, pick a fixed slice of 50 contracts, and write the ground truth.

Run:  python prepare.py
Makes: data/contracts/*.txt   one plain-text file per contract
       data/gold.csv          one row per contract x question: is the clause present, and where
"""
import csv, io, json, random, re, urllib.request, zipfile
from config import (CUAD_ZIP_URL, CUAD_JSON, CONTRACTS, GOLD, DATA, SEED,
                    N_DEV, N_TEST, MAX_WORDS, QUESTIONS)


def download():
    if CUAD_JSON.exists():
        return
    print("Downloading CUAD (18 MB)...")
    raw = urllib.request.urlopen(CUAD_ZIP_URL, timeout=120).read()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        z.extract("CUADv1.json", CUAD_JSON.parent)
    print("Saved", CUAD_JSON)


def label_of(question_text):
    return re.search(r'related to "(.+?)"', question_text).group(1)


def main():
    DATA.mkdir(exist_ok=True)
    download()
    data = json.loads(CUAD_JSON.read_text(encoding="utf-8"))["data"]

    usable = [c for c in data if len(c["paragraphs"][0]["context"].split()) <= MAX_WORDS]
    random.Random(SEED).shuffle(usable)
    chosen = usable[: N_DEV + N_TEST]
    print(f"{len(data)} contracts in CUAD, {len(usable)} under {MAX_WORDS} words, using {len(chosen)}")

    CONTRACTS.mkdir(exist_ok=True)
    rows = []
    for i, c in enumerate(chosen):
        cid = f"c{i + 1:03d}"
        split = "dev" if i < N_DEV else "test"
        text = c["paragraphs"][0]["context"]
        (CONTRACTS / f"{cid}.txt").write_text(text, encoding="utf-8")

        spans_by_label = {}
        for qa in c["paragraphs"][0]["qas"]:
            spans = []
            for a in qa["answers"]:
                start = a["answer_start"]
                end = start + len(a["text"])
                assert text[start:end] == a["text"], f"offset mismatch in {cid}"
                spans.append([start, end])
            spans_by_label[label_of(qa["question"])] = spans

        for q in QUESTIONS:
            spans = [s for label in q["cuad"] for s in spans_by_label.get(label, [])]
            rows.append({"contract_id": cid, "split": split, "title": c["title"],
                         "words": len(text.split()), "qid": q["id"],
                         "present": int(bool(spans)), "spans": json.dumps(spans)})

    with open(GOLD, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {len(chosen)} contracts to {CONTRACTS} and {len(rows)} gold rows to {GOLD}\n")
    print(f"{'Question':35} {'present in dev':>15} {'present in test':>16}")
    for q in QUESTIONS:
        dev = sum(r["present"] for r in rows if r["qid"] == q["id"] and r["split"] == "dev")
        test = sum(r["present"] for r in rows if r["qid"] == q["id"] and r["split"] == "test")
        print(f"{q['id'] + ' ' + q['name']:35} {dev:>9} / {N_DEV:<4} {test:>10} / {N_TEST}")


if __name__ == "__main__":
    main()
