"""Day 7. Ask all ten questions of every contract in a split and save the answers.

Run:  python run_eval.py --split test --tag v1
It saves after every answer, so you can stop with Ctrl+C and rerun the same command
to carry on where it stopped. 20 contracts x 10 questions = 200 calls, about 15-20 minutes.
"""
import argparse, json
from config import MODEL_FAST, MODEL_STRONG, QUESTIONS, RESULTS
from answer import CHUNK_SIZE, TOP_K, answer
from rag import get_collection, load_gold


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="test")
    ap.add_argument("--tag", default="v1", help="a name for this version of the system")
    ap.add_argument("--size", type=int, default=CHUNK_SIZE)
    ap.add_argument("--k", type=int, default=TOP_K)
    ap.add_argument("--strong", action="store_true", help=f"use {MODEL_STRONG} instead")
    ap.add_argument("--limit", type=int, default=0, help="only the first N contracts (for a dry run)")
    a = ap.parse_args()

    model = MODEL_STRONG if a.strong else MODEL_FAST
    RESULTS.mkdir(exist_ok=True)
    path = RESULTS / f"answers_{a.tag}_{a.split}.jsonl"
    done = set()
    if path.exists():
        done = {(r["contract_id"], r["qid"]) for r in map(json.loads, path.open(encoding="utf-8"))}

    gold = load_gold(a.split)
    contracts = sorted({r["contract_id"] for r in gold})
    if a.limit:
        contracts = contracts[:a.limit]
    todo = [(c, q["id"]) for c in contracts for q in QUESTIONS if (c, q["id"]) not in done]
    print(f"{model}, {a.size}-word chunks, k={a.k}: {len(done)} done, {len(todo)} to go -> {path.name}")

    col = get_collection(a.size)
    by_key = {(r["contract_id"], r["qid"]): r for r in gold}
    with path.open("a", encoding="utf-8") as f:
        for n, (cid, qid) in enumerate(todo, 1):
            res = answer(cid, qid, model=model, size=a.size, k=a.k, col=col)
            g = by_key[(cid, qid)]
            res["gold_present"] = g["present"]
            res["gold_spans"] = g["spans"]
            res["retrieval_hit"] = any(e["start"] < s_end and s_start < e["end"]
                                       for e in res["excerpts"] for s_start, s_end in g["spans"])
            res["excerpts"] = [[e["start"], e["end"]] for e in res["excerpts"]]
            f.write(json.dumps(res) + "\n")
            f.flush()
            mark = "ok " if res["present"] == g["present"] else "MISS"
            print(f"[{n}/{len(todo)}] {cid} {qid:4} {mark} predicted={res['present']!s:5} "
                  f"gold={g['present']!s:5} {res['latency_ms']} ms")
    print(f"\nDone. Now run: python score.py --tag {a.tag} --split {a.split}")


if __name__ == "__main__":
    main()
