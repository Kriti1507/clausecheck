"""Day 5. Does retrieval find the clause? Scored against the lawyers' labels, no model calls, free.

Run:  python retrieval_eval.py --size 200 --k 5
      python retrieval_eval.py --size 200 --k 5 --random    (what luck alone scores)
Hit = at least one of the top-k chunks overlaps the text the lawyers highlighted.
Only contracts where the clause is actually present are scored.

Compare chunk sizes at the same words-retrieved budget (size x k), or bigger chunks
win simply by covering more of the contract.
"""
import argparse, csv, random
from config import QUESTIONS, RESULTS, SEED
from rag import get_collection, load_gold, overlaps, retrieve

RNG = random.Random(SEED)
_chunks_cache = {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=200)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--split", default="dev")
    ap.add_argument("--random", action="store_true", help="pick k chunks at random instead")
    a = ap.parse_args()

    col = get_collection(a.size)
    if col.count() == 0:
        raise SystemExit(f"No index for {a.size}-word chunks yet. Run: python index.py --size {a.size}")
    gold = [r for r in load_gold(a.split) if r["present"]]
    RESULTS.mkdir(exist_ok=True)
    out_path = RESULTS / "retrieval.csv"
    new_file = not out_path.exists()
    method = "random" if a.random else "embedding"

    print(f"Recall@{a.k}, {a.size}-word chunks ({a.size * a.k} words retrieved), "
          f"{method}, {a.split} split\n")
    rows, all_hits = [], []
    for q in QUESTIONS:
        hits = [hit(col, r, q, a.k, a.random) for r in gold if r["qid"] == q["id"]]
        all_hits += hits
        recall = sum(hits) / len(hits) if hits else float("nan")
        rows.append({"size": a.size, "k": a.k, "words_retrieved": a.size * a.k, "method": method,
                     "split": a.split, "qid": q["id"], "name": q["name"], "n": len(hits),
                     "recall": round(recall, 3)})
        print(f"{q['id'] + ' ' + q['name']:35} {sum(hits):>3} / {len(hits):<3} {recall:>6.0%}")
    overall = sum(all_hits) / len(all_hits)
    rows.append({"size": a.size, "k": a.k, "words_retrieved": a.size * a.k, "method": method,
                 "split": a.split, "qid": "ALL", "name": "All questions",
                 "n": len(all_hits), "recall": round(overall, 3)})
    print(f"\n{'All questions':35} {sum(all_hits):>3} / {len(all_hits):<3} {overall:>6.0%}")

    with open(out_path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        if new_file:
            w.writeheader()
        w.writerows(rows)
    print(f"Appended to {out_path}")


def hit(col, gold_row, q, k, use_random):
    cid = gold_row["contract_id"]
    if use_random:
        if cid not in _chunks_cache:
            got = col.get(where={"contract_id": cid}, include=["metadatas"])
            _chunks_cache[cid] = [{"start": m["start"], "end": m["end"]} for m in got["metadatas"]]
        pool = _chunks_cache[cid]
        chosen = RNG.sample(pool, min(k, len(pool)))
    else:
        chosen = retrieve(col, cid, q["ask"], k)
    return any(overlaps(c, gold_row["spans"]) for c in chosen)


if __name__ == "__main__":
    main()
