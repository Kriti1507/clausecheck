"""Show what the lawyers marked in one contract: the answer key for all ten questions.

Run:  python show_gold.py c001          all ten questions
      python show_gold.py c001 Q2       one question, full clause text
Use it on dev contracts (c001-c030). Leave c031-c050 unseen until Day 7.
"""
import sys
from config import QUESTIONS
from rag import contract_text, load_gold

cid = sys.argv[1] if len(sys.argv) > 1 else "c001"
only = sys.argv[2] if len(sys.argv) > 2 else None
sys.stdout.reconfigure(errors="replace")   # contracts contain characters some consoles can't print
rows = {r["qid"]: r for r in load_gold() if r["contract_id"] == cid}
if not rows:
    raise SystemExit(f"No contract called {cid}. Try c001 to c050.")
text = contract_text(cid)
first = next(iter(rows.values()))
print(f"{cid} ({first['split']}): {first['title']}, {int(first['words']):,} words\n")
for q in QUESTIONS:
    if only and q["id"] != only:
        continue
    r = rows[q["id"]]
    print(f"{q['id']:4} {q['name']:32} {'PRESENT' if r['present'] else 'absent'}")
    for start, end in r["spans"]:
        clause = " ".join(text[start:end].split())
        print(f"       chars {start:,}-{end:,}: {clause if only else clause[:160] + ('...' if len(clause) > 160 else '')}")
