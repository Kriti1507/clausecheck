"""Day 6. The ClauseCheck review screen.

Run:  streamlit run app.py
Pick a contract, run the ten checks, and see each answer with the clause it came from.
"""
import json
import streamlit as st
from config import QUESTIONS, RESULTS
from answer import CHUNK_SIZE, TOP_K, answer
from rag import contract_text, get_collection, load_gold

st.set_page_config(page_title="ClauseCheck", layout="wide")
CACHE = RESULTS / "app_cache.json"


def load_cache():
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_cache(cache):
    RESULTS.mkdir(exist_ok=True)
    CACHE.write_text(json.dumps(cache), encoding="utf-8")


gold = load_gold()
titles = {r["contract_id"]: r["title"] for r in gold}
dev_ids = sorted({r["contract_id"] for r in gold if r["split"] == "dev"})

st.title("ClauseCheck")
st.caption("Ten standard risk checks on a commercial contract, each linked to the clause it came from. "
           "It helps you decide whether this contract needs counsel. It is not legal advice.")

with st.sidebar:
    cid = st.selectbox("Contract", dev_ids, format_func=lambda c: f"{c}  {titles[c][:45]}")
    st.caption(f"{len(contract_text(cid).split()):,} words. Showing the dev set only; "
               "the test set stays unseen until Day 7.")
    run = st.button("Run the ten checks", type="primary")
    st.caption("Each check is one model call. On the free tier that takes 45-90 seconds in total.")

cache = load_cache()
results = cache.get(cid)

if run:
    col = get_collection(CHUNK_SIZE)
    results, bar = {}, st.progress(0.0, text="Starting...")
    for i, q in enumerate(QUESTIONS):
        bar.progress(i / len(QUESTIONS), text=f"Checking {q['name'].lower()} ({i + 1} of {len(QUESTIONS)})")
        try:
            r = answer(cid, q["id"], col=col)
            r["excerpts"] = [{k: e[k] for k in ("start", "end", "text")} for e in r["excerpts"]]
            results[q["id"]] = r
        except Exception as e:
            results[q["id"]] = {"error": f"{type(e).__name__}: {e}"}
    bar.empty()
    cache[cid] = results
    save_cache(cache)

if not results:
    st.info("Choose a contract and select **Run the ten checks**. Results are saved, "
            "so reopening a contract you've already checked costs nothing.")
    st.stop()


def status(r):
    if "error" in r:
        return "Couldn't check", "grey"
    if r.get("parse_error"):
        # The model's reply was unreadable. Never show that as "Not found".
        return "Check manually", "orange"
    if not r["present"]:
        return "Not found", "blue"
    if r["confidence"] == "low" or not r["quote_found"]:
        return "Check manually", "orange"
    return "Found", "green"


found = [q for q in QUESTIONS if status(results.get(q["id"], {"error": ""}))[0] == "Found"]
unsure = [q for q in QUESTIONS if status(results.get(q["id"], {"error": ""}))[0] in ("Check manually", "Couldn't check")]
risky = [q for q in found if q["severity"] == 3]
c1, c2, c3 = st.columns(3)
c1.metric("Clauses found", len(found))
c2.metric("Need a manual look", len(unsure))
c3.metric("Severity-3 clauses found", len(risky))

for q in QUESTIONS:
    r = results.get(q["id"], {"error": "not run"})
    label, colour = status(r)
    with st.container(border=True):
        st.markdown(f"**{q['name']}** &nbsp; :{colour}-badge[{label}]")
        if "error" in r:
            st.write(f"This check failed: {r['error']}. Run the checks again.")
            continue
        if r.get("parse_error"):
            st.write("The model's answer came back in an unreadable format, so this check has no result. "
                     "Read the excerpts below, or run the checks again.")
        elif not r["present"]:
            st.write("No clause on this was found in the excerpts searched. "
                     "That usually means the contract is silent, but retrieval can miss clauses.")
        else:
            st.write(r["summary"])
            if r["quote"]:
                st.markdown(f"> {r['quote']}")
            if not r["quote_found"]:
                st.warning("The quote doesn't match the contract word for word. Read the clause before relying on it.")
        with st.expander(f"Excerpts searched ({len(r['excerpts'])}) and model details"):
            cited = {n - 1 for n in r.get("citations", [])}
            for i, e in enumerate(r["excerpts"]):
                tag = " (cited)" if i in cited else ""
                st.markdown(f"**E{i + 1}{tag}**, characters {e['start']:,}-{e['end']:,}")
                st.text(e["text"])
            st.caption(f"{r['model']}, confidence {r['confidence']}, {r['latency_ms']} ms, "
                       f"{r['tokens_in']} tokens in, {r['tokens_out'] + r['tokens_thinking']} out")
