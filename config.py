"""ClauseCheck settings. Every script imports from here, so a change made here applies everywhere."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
CUAD_ZIP_URL = "https://raw.githubusercontent.com/TheAtticusProject/cuad/main/data.zip"
CUAD_JSON = DATA / "cuad" / "CUADv1.json"
CONTRACTS = DATA / "contracts"
GOLD = DATA / "gold.csv"
CHROMA = DATA / "chroma_db"
RESULTS = ROOT / "results"
ENV_FILE = ROOT.parent / ".env"          # the shared C:\dev\aipm\.env

# ---- Dataset slice --------------------------------------------------------
SEED = 7            # fixed, so your 50 contracts are the same every run
N_DEV = 30          # for tuning: look at these as often as you like
N_TEST = 20         # held out: score these on Day 7 and Day 8 only
MAX_WORDS = 15000   # skip the longest contracts to keep indexing fast on 12 GB

# ---- Models ---------------------------------------------------------------
MODEL_FAST = "gemini-3.5-flash-lite"
MODEL_STRONG = "gemini-3.5-flash"
EMBED_MODEL = "all-MiniLM-L6-v2"   # 384-dim, ~90 MB, reads only the first 256 word pieces

# Seconds between model calls. 4.5 s keeps you under 15 requests/minute.
# Check your real free-tier limit in AI Studio and lower this if you have headroom.
MIN_SECONDS_BETWEEN_CALLS = 4.5

# Paid-tier prices, USD per 1M tokens, from ai.google.dev/gemini-api/docs/pricing
# (checked 21 Sep 2026). Output price includes thinking tokens.
PRICES = {
    "gemini-3.5-flash-lite": {"in": 0.30, "out": 2.50},
    "gemini-3.5-flash": {"in": 1.50, "out": 9.00},
}
USD_TO_INR = 83.0   # update to today's rate when you present costs

# ---- The ten questions a deal desk analyst answers -------------------------
# cuad:     the CUAD label(s) that hold the ground truth for this question
# severity: 3 = a miss can cost real money, 2 = commercial impact, 1 = hygiene
#           You will challenge these defaults on Day 2.
# keywords: the Ctrl-F list used by the non-AI baseline (regular expressions)
QUESTIONS = [
    dict(id="Q1", name="Liability cap", cuad=["Cap On Liability"], severity=3,
         ask="Does this contract cap either party's liability? If so, what is the cap amount or formula?",
         keywords=[r"limitation of liability", r"limitation on liability", r"aggregate liability",
                   r"shall not exceed", r"\bin no event\b"]),
    dict(id="Q2", name="Uncapped liability", cuad=["Uncapped Liability"], severity=3,
         ask="Is any liability excluded from the cap or left unlimited, for example for indemnities, "
             "confidentiality breaches, gross negligence or wilful misconduct?",
         keywords=[r"unlimited liability", r"\buncapped\b", r"shall not apply to",
                   r"gross negligence", r"willful misconduct"]),
    dict(id="Q3", name="Auto-renewal", cuad=["Renewal Term"], severity=2,
         ask="Does the contract renew or extend automatically, and for what renewal term?",
         keywords=[r"automatically renew", r"renewal term", r"successive", r"\brenew"]),
    dict(id="Q4", name="Assignment / change of control", cuad=["Anti-Assignment", "Change Of Control"], severity=3,
         ask="Does a party need consent to assign the contract, or do rights change on a merger, "
             "acquisition or change of control?",
         keywords=[r"\bassign", r"change of control", r"change in control", r"\bmerger\b"]),
    dict(id="Q5", name="Governing law", cuad=["Governing Law"], severity=1,
         ask="Which jurisdiction's law governs this contract?",
         keywords=[r"governed by", r"governing law", r"laws of the state"]),
    dict(id="Q6", name="Termination for convenience", cuad=["Termination For Convenience"], severity=2,
         ask="Can either party terminate for convenience, without cause, and with what notice?",
         keywords=[r"for convenience", r"without cause", r"for any reason"]),
    dict(id="Q7", name="IP ownership", cuad=["Ip Ownership Assignment"], severity=3,
         ask="Who owns intellectual property created under this contract? Is any IP assigned to the other party?",
         keywords=[r"shall own", r"sole and exclusive property", r"work made for hire", r"hereby assigns"]),
    dict(id="Q8", name="Non-compete", cuad=["Non-Compete"], severity=2,
         ask="Is either party restricted from competing, or from working with competitors?",
         keywords=[r"non-compet", r"shall not compete", r"competing product", r"compete with"]),
    dict(id="Q9", name="Most-favoured nation", cuad=["Most Favored Nation"], severity=2,
         ask="Is there a most-favoured-nation clause guaranteeing terms or prices at least as good as "
             "those given to other customers?",
         keywords=[r"most favou?red", r"no less favou?rable", r"\bbest price", r"\blowest price"]),
    dict(id="Q10", name="Audit rights", cuad=["Audit Rights"], severity=1,
         ask="Does either party have the right to audit or inspect the other's books, records or compliance?",
         keywords=[r"\baudit", r"\binspect", r"books and records"]),
]
