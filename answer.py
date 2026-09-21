"""Day 6. Answer one risk question about one contract, grounded in retrieved excerpts.

Try it:  python answer.py c001 Q1
"""
import json, sys
from pydantic import BaseModel
from config import MODEL_FAST, QUESTIONS
from llm import generate
from rag import get_collection, retrieve

CHUNK_SIZE = 200   # set this to the winner of your Day 5 experiment
TOP_K = 5

SYSTEM = """You help a deal desk analyst review commercial contracts before deciding whether to
involve outside counsel. You are given numbered excerpts from ONE contract and one question.

Rules:
- Use only the excerpts. Never rely on general knowledge of what contracts usually say.
- If the excerpts do not address the question, set present to false. Do not guess.
- quote must be copied word for word from a single excerpt. Keep it under 60 words.
- citations lists the excerpt numbers that support your answer. Empty if present is false.
- confidence is "high" only when an excerpt answers the question directly and unambiguously,
  "medium" when it needs interpretation, "low" when the excerpts are partial or conflicting.
- summary is one plain-English sentence a non-lawyer can act on."""


class Finding(BaseModel):
    present: bool
    summary: str
    quote: str
    citations: list[int]
    confidence: str


def build_prompt(question, excerpts):
    blocks = "\n\n".join(f"[E{i + 1}]\n{e['text']}" for i, e in enumerate(excerpts))
    return f"Question: {question}\n\nExcerpts:\n\n{blocks}"


def answer(contract_id, qid, model=MODEL_FAST, size=CHUNK_SIZE, k=TOP_K, col=None):
    q = next(q for q in QUESTIONS if q["id"] == qid)
    col = col or get_collection(size)
    excerpts = retrieve(col, contract_id, q["ask"], k)
    resp, stats = generate(model, build_prompt(q["ask"], excerpts), system=SYSTEM, schema=Finding)
    try:
        finding = Finding.model_validate_json(resp.text).model_dump()
        finding["parse_error"] = False
    except Exception:
        # The model broke the format. Treat it as "not answered" and keep the raw text for review.
        finding = {"present": False, "summary": "", "quote": "", "citations": [],
                   "confidence": "low", "parse_error": True, "raw": (resp.text or "")[:500]}
    # Map citation numbers back to character ranges in the contract.
    finding["cited_ranges"] = [[excerpts[n - 1]["start"], excerpts[n - 1]["end"]]
                               for n in finding["citations"] if 1 <= n <= len(excerpts)]
    # Is the quote really in the contract? Compare with whitespace collapsed.
    squash = lambda s: " ".join(s.split())
    finding["quote_found"] = bool(finding["quote"].strip()) and any(
        squash(finding["quote"]) in squash(e["text"]) for e in excerpts)
    finding["excerpts"] = excerpts
    return {**finding, **stats, "contract_id": contract_id, "qid": qid, "size": size, "k": k}


if __name__ == "__main__":
    sys.stdout.reconfigure(errors="replace")
    cid = sys.argv[1] if len(sys.argv) > 1 else "c001"
    qid = sys.argv[2] if len(sys.argv) > 2 else "Q1"
    result = answer(cid, qid)
    result.pop("excerpts")
    print(json.dumps(result, indent=2))
