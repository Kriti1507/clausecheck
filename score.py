"""Day 7. Turn saved answers into a scorecard and a list of errors to review.

Run:  python score.py --tag v1 --split test
Makes: results/scorecard_v1_test.md   the numbers
       results/errors_v1_test.csv     every mistake, with columns for you to label the failure type
"""
import argparse, csv, json, statistics
from config import QUESTIONS, RESULTS, USD_TO_INR


def pct(x):
    return "n/a" if x is None else f"{x:.0%}"


def ratio(a, b):
    return a / b if b else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="v1")
    ap.add_argument("--split", default="test")
    a = ap.parse_args()
    rows = [json.loads(l) for l in open(RESULTS / f"answers_{a.tag}_{a.split}.jsonl", encoding="utf-8")]

    lines = [f"# Scorecard: {a.tag} on the {a.split} split",
             "", f"{len(rows)} answers across {len({r['contract_id'] for r in rows})} contracts. "
             f"Model: {rows[0]['model']}, {rows[0]['size']}-word chunks, k={rows[0]['k']}.", "",
             "| Question | Present | Precision | Recall | Accuracy | Always-no accuracy | Citation correct | Retrieval hit |",
             "|---|---|---|---|---|---|---|---|"]
    errors = []
    tot = dict(tp=0, fp=0, fn=0, tn=0, cite_ok=0, hits=0)
    for q in QUESTIONS:
        rs = [r for r in rows if r["qid"] == q["id"]]
        if not rs:
            continue
        tp = sum(r["present"] and r["gold_present"] for r in rs)
        fp = sum(r["present"] and not r["gold_present"] for r in rs)
        fn = sum(not r["present"] and r["gold_present"] for r in rs)
        tn = sum(not r["present"] and not r["gold_present"] for r in rs)
        # A true positive is only useful if it points at the right clause.
        cite_ok = sum(any(cs < ge and gs < ce for cs, ce in r["cited_ranges"] for gs, ge in r["gold_spans"])
                      for r in rs if r["present"] and r["gold_present"])
        hits = sum(r["retrieval_hit"] for r in rs if r["gold_present"])
        for k, v in dict(tp=tp, fp=fp, fn=fn, tn=tn, cite_ok=cite_ok, hits=hits).items():
            tot[k] += v
        lines.append(f"| {q['id']} {q['name']} | {tp + fn}/{len(rs)} | {pct(ratio(tp, tp + fp))} | "
                     f"{pct(ratio(tp, tp + fn))} | {pct(ratio(tp + tn, len(rs)))} | "
                     f"{pct(ratio(fp + tn, len(rs)))} | {pct(ratio(cite_ok, tp))} | {pct(ratio(hits, tp + fn))} |")
        for r in rs:
            kind = None
            if r.get("parse_error"):
                kind = "format failure"
            elif r["present"] and not r["gold_present"]:
                kind = "false alarm"
            elif r["gold_present"] and not r["present"]:
                kind = "missed clause"
            elif r["present"] and r["gold_present"] and not any(
                    cs < ge and gs < ce for cs, ce in r["cited_ranges"] for gs, ge in r["gold_spans"]):
                kind = "wrong citation"
            if kind:
                errors.append({"contract_id": r["contract_id"], "qid": r["qid"], "severity": q["severity"],
                               "error": kind, "retrieval_hit": r["retrieval_hit"],
                               "confidence": r["confidence"], "summary": r["summary"], "quote": r["quote"],
                               "failure_type": "", "notes": ""})

    t = tot
    n = len(rows)
    lat = sorted(r["latency_ms"] for r in rows)
    p95 = lat[min(len(lat) - 1, int(0.95 * len(lat)))]
    per_contract = sum(r["cost_usd_if_paid"] for r in rows) / len({r["contract_id"] for r in rows})
    lines += ["", f"| **All** | {t['tp'] + t['fn']}/{n} | {pct(ratio(t['tp'], t['tp'] + t['fp']))} | "
              f"{pct(ratio(t['tp'], t['tp'] + t['fn']))} | {pct(ratio(t['tp'] + t['tn'], n))} | "
              f"{pct(ratio(t['fp'] + t['tn'], n))} | {pct(ratio(t['cite_ok'], t['tp']))} | "
              f"{pct(ratio(t['hits'], t['tp'] + t['fn']))} |",
              "", "## Operations", "",
              f"- Latency per question: p50 {statistics.median(lat) / 1000:.1f} s, p95 {p95 / 1000:.1f} s",
              f"- Tokens per question: {statistics.mean(r['tokens_in'] for r in rows):.0f} in, "
              f"{statistics.mean(r['tokens_out'] for r in rows):.0f} out, "
              f"{statistics.mean(r['tokens_thinking'] for r in rows):.0f} thinking",
              f"- Cost per contract at paid-tier prices: ${per_contract:.4f} "
              f"(about Rs {per_contract * USD_TO_INR:.2f})",
              f"- Answers where the model broke the output format: {sum(r.get('parse_error', False) for r in rows)}",
              f"- Quotes not found word for word in the excerpts: "
              f"{sum(bool(r['quote']) and not r['quote_found'] for r in rows)}",
              "", "## Errors by type", ""]
    for kind in ("missed clause", "false alarm", "wrong citation", "format failure"):
        es = [e for e in errors if e["error"] == kind]
        detail = f"{sum(e['severity'] == 3 for e in es)} on severity-3 questions"
        if kind in ("missed clause", "wrong citation"):   # only these have a gold clause to find
            detail += f", {sum(not e['retrieval_hit'] for e in es)} where retrieval never found the clause"
        lines.append(f"- {kind}: {len(es)} ({detail})")

    out = RESULTS / f"scorecard_{a.tag}_{a.split}.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    err_path = RESULTS / f"errors_{a.tag}_{a.split}.csv"
    with open(err_path, "w", newline="", encoding="utf-8-sig") as f:   # -sig so Excel shows quotes correctly
        w = csv.DictWriter(f, fieldnames=["contract_id", "qid", "severity", "error", "retrieval_hit",
                                          "confidence", "summary", "quote", "failure_type", "notes"])
        w.writeheader()
        w.writerows(errors)
    print("\n".join(lines))
    print(f"\nSaved {out.name} and {err_path.name} ({len(errors)} errors to label)")


if __name__ == "__main__":
    main()
