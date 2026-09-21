# ClauseCheck

Ten standard risk checks on a commercial contract, each answer linked to the clause it came from. Built for a deal desk analyst deciding whether a contract needs outside counsel. Built on the [CUAD](https://www.atticusprojectai.org/cuad) corpus (CC BY 4.0), whose expert labels double as the evaluation set.

> Status: Week 1 of a 30-day AI product management program. The case study and results go here on Day 8.

## Run it

From `C:\dev\aipm` with the virtual environment active:

```powershell
cd clausecheck
python prepare.py                      # download CUAD, pick 50 contracts, write the answer key
python baseline.py                     # the non-AI baseline, scored
python index.py --size 200             # chunk and embed the contracts
python retrieval_eval.py --size 200 --k 5
streamlit run app.py                   # the review screen
python run_eval.py --split test --tag v1 && python score.py --tag v1 --split test
```

Needs `GOOGLE_API_KEY` in `C:\dev\aipm\.env`.

## Files

| File | Day | What it does |
|---|---|---|
| `config.py` | all | Settings: models, prices, the ten questions, their CUAD labels and keywords |
| `prepare.py` | 1 | Downloads CUAD, picks 30 dev + 20 test contracts, writes `data/gold.csv` |
| `baseline.py` | 1, 7 | Keyword search scored against the lawyers' labels |
| `show_gold.py` | 1-8 | Shows the answer key for one contract |
| `cost_model.py` | 3 | Measures tokens, latency and cost; compares whole-contract vs retrieval |
| `rag.py` | 5-8 | Chunking, embeddings, vector store, span matching |
| `index.py` | 5 | Builds one vector index per chunk size |
| `retrieval_eval.py` | 5, 8 | Recall@k against the lawyers' spans, plus a random baseline |
| `llm.py` | 3, 6-8 | The only file that calls Gemini: throttling, retries, token and cost logging |
| `answer.py` | 6 | One grounded answer with quote, citations and confidence |
| `app.py` | 6 | The Streamlit review screen |
| `run_eval.py` | 7, 8 | Answers every question for a split; resumable |
| `score.py` | 7, 8 | Scorecard plus an error list to label |
| `docs/` | 1-8 | Problem, PRD, architecture log, eval plan, case study, demo script |
