"""Day 3. Measure tokens, latency and cost on your own contracts, then compare two architectures.

Run:  python cost_model.py
Makes 3 free token-count calls and 15 model calls (about 2 minutes), then writes results/cost_model.md.

Architecture A: send the whole contract once and ask all ten questions in one call.
Architecture B: retrieval (RAG), one call per question with only the top-k excerpts.
"""
import statistics
from pydantic import BaseModel
from config import MODEL_FAST, MODEL_STRONG, PRICES, QUESTIONS, RESULTS, USD_TO_INR
from llm import client, generate
from rag import chunk_text, contract_text, load_gold

SIZE, K = 200, 5                       # change to your Day 5 choice later
VOLUMES = [100, 400, 2000]              # contracts reviewed per month
SYSTEM_TOKENS = 250                     # rough size of the instructions in answer.py


class Finding(BaseModel):
    present: bool
    summary: str
    quote: str
    citations: list[int]
    confidence: str


def pctl(values, p):
    v = sorted(values)
    return v[min(len(v) - 1, int(p * len(v)))]


def main():
    gold = load_gold("dev")
    cids = sorted({r["contract_id"] for r in gold})
    words = {r["contract_id"]: int(r["words"]) for r in gold}

    # 1. How many tokens is a word of contract text? Ask the model's own tokenizer.
    ratios = []
    for cid in cids[:3]:
        text = contract_text(cid)
        n = client().models.count_tokens(model=MODEL_FAST, contents=text).total_tokens
        ratios.append(n / len(text.split()))
        print(f"{cid}: {len(text.split())} words -> {n} tokens")
    tpw = statistics.mean(ratios)
    print(f"Tokens per word: {tpw:.2f}\n")

    # 2. Latency and real token use for a RAG-sized request, on both models.
    probe = {}
    text = contract_text(cids[0])
    excerpts = [c[2] for c in chunk_text(text, SIZE, SIZE // 5)[:K]]
    prompt = f"Question: {QUESTIONS[0]['ask']}\n\nExcerpts:\n\n" + "\n\n".join(
        f"[E{i + 1}]\n{e}" for i, e in enumerate(excerpts))
    for model, n in ((MODEL_FAST, 10), (MODEL_STRONG, 5)):
        runs = []
        for i in range(n):
            _, s = generate(model, prompt, system="Answer only from the excerpts.", schema=Finding)
            runs.append(s)
            print(f"{model} call {i + 1}/{n}: {s['latency_ms']} ms, {s['tokens_in']} in, "
                  f"{s['tokens_out']} out, {s['tokens_thinking']} thinking")
        probe[model] = runs

    # 3. Cost per contract for each architecture, using measured output and thinking tokens.
    avg_words = statistics.mean(words.values())
    rows = []
    for model, runs in probe.items():
        price = PRICES[model]
        out_per_answer = statistics.mean(r["tokens_out"] + r["tokens_thinking"] for r in runs)
        rag_in = statistics.mean(r["tokens_in"] for r in runs)
        a_in = avg_words * tpw + SYSTEM_TOKENS + 60 * len(QUESTIONS)
        a_out = out_per_answer * len(QUESTIONS)
        b_in = rag_in * len(QUESTIONS)
        b_out = out_per_answer * len(QUESTIONS)
        for arch, tin, tout in (("A whole contract", a_in, a_out), ("B retrieval", b_in, b_out)):
            usd = (tin * price["in"] + tout * price["out"]) / 1e6
            rows.append((model, arch, tin, tout, usd))

    lat = {m: [r["latency_ms"] for r in runs] for m, runs in probe.items()}
    md = ["# Cost and latency model", "",
          f"Dev contracts average {avg_words:,.0f} words, about {avg_words * tpw:,.0f} tokens "
          f"({tpw:.2f} tokens per word, measured).", "",
          "## Latency for one retrieval-sized question", "",
          "| Model | Calls | p50 | p95 | slowest |", "|---|---|---|---|---|"]
    for m, v in lat.items():
        md.append(f"| {m} | {len(v)} | {statistics.median(v) / 1000:.1f} s | "
                  f"{pctl(v, 0.95) / 1000:.1f} s | {max(v) / 1000:.1f} s |")
    md += ["", "With 5-10 calls, p95 is close to the slowest call. Treat it as a first reading, not a fact.", "",
           "## Cost per contract (10 questions), paid-tier prices", "",
           "| Model | Architecture | Input tokens | Output + thinking tokens | USD | INR |",
           "|---|---|---|---|---|---|"]
    for model, arch, tin, tout, usd in rows:
        md.append(f"| {model} | {arch} | {tin:,.0f} | {tout:,.0f} | ${usd:.4f} | Rs {usd * USD_TO_INR:.2f} |")
    md += ["", "## Monthly cost at volume", "", "| Model | Architecture | " +
           " | ".join(f"{v:,} contracts" for v in VOLUMES) + " |", "|---|---|" + "---|" * len(VOLUMES)]
    for model, arch, _, _, usd in rows:
        md.append(f"| {model} | {arch} | " + " | ".join(f"${usd * v:,.2f}" for v in VOLUMES) + " |")
    md += ["", "Free tier: $0, but rate-limited and your prompts may be used to improve Google's products.",
           "Output prices include thinking tokens, so a model that thinks more costs more for the same answer."]

    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "cost_model.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n" + "\n".join(md))
    print("\nSaved results/cost_model.md")


if __name__ == "__main__":
    main()
