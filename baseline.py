"""Day 1. The non-AI baseline: a keyword search, scored against the lawyers' answers.

Run:  python baseline.py                 (dev split, Day 1)
      python baseline.py --split test    (Day 7, to compare with ClauseCheck on the same contracts)
It flags a clause as present if any keyword from config.QUESTIONS appears in the contract,
then compares that with CUAD's expert labels.
"""
import argparse, csv, re
from config import CONTRACTS, GOLD, QUESTIONS, RESULTS


def prf(tp, fp, fn):
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return precision, recall


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev")
    split = ap.parse_args().split
    gold = [r for r in csv.DictReader(open(GOLD, encoding="utf-8")) if r["split"] == split]
    print(f"Keyword baseline on the {split} split ({len(gold) // len(QUESTIONS)} contracts)\n")
    texts = {}
    RESULTS.mkdir(exist_ok=True)
    out = []
    print(f"{'Question':35} {'precision':>9} {'recall':>7} {'accuracy':>9} {'always-no':>10}")
    for q in QUESTIONS:
        tp = fp = fn = tn = 0
        pattern = re.compile("|".join(q["keywords"]), re.IGNORECASE)
        for r in (r for r in gold if r["qid"] == q["id"]):
            cid = r["contract_id"]
            if cid not in texts:
                texts[cid] = (CONTRACTS / f"{cid}.txt").read_text(encoding="utf-8")
            predicted = bool(pattern.search(texts[cid]))
            actual = r["present"] == "1"
            tp += predicted and actual
            fp += predicted and not actual
            fn += actual and not predicted
            tn += not predicted and not actual
        n = tp + fp + fn + tn
        p, rc = prf(tp, fp, fn)
        acc = (tp + tn) / n
        always_no = (fp + tn) / n          # accuracy of a system that always answers "not present"
        out.append({"qid": q["id"], "name": q["name"], "tp": tp, "fp": fp, "fn": fn, "tn": tn,
                    "precision": round(p, 2), "recall": round(rc, 2),
                    "accuracy": round(acc, 2), "always_no_accuracy": round(always_no, 2)})
        print(f"{q['id'] + ' ' + q['name']:35} {p:>9.0%} {rc:>7.0%} {acc:>9.0%} {always_no:>10.0%}")

    tp, fp, fn = (sum(r[k] for r in out) for k in ("tp", "fp", "fn"))
    p, rc = prf(tp, fp, fn)
    print(f"\n{'All questions':35} {p:>9.0%} {rc:>7.0%}")
    name = f"baseline_keywords_{split}.csv"
    with open(RESULTS / name, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    print(f"\nSaved results/{name}")
    print("Read the last column before you celebrate any accuracy number this week.")


if __name__ == "__main__":
    main()
