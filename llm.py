"""One place that talks to Gemini: throttling, retries, token and latency logging."""
import os, time
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types
from config import ENV_FILE, MIN_SECONDS_BETWEEN_CALLS, PRICES

load_dotenv(ENV_FILE)
_client = None
_last_call = 0.0


def client():
    global _client
    if _client is None:
        key = os.getenv("GOOGLE_API_KEY")
        if not key:
            raise SystemExit(f"GOOGLE_API_KEY not found. Check {ENV_FILE}")
        _client = genai.Client(api_key=key)
    return _client


def generate(model, prompt, system=None, schema=None, attempts=5):
    """Call the model. Returns (response, stats). Waits between calls to respect rate limits,
    and retries only errors worth retrying: 429 (rate limit) and 5xx (provider busy)."""
    global _last_call
    config = types.GenerateContentConfig(
        temperature=0,
        system_instruction=system,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        **({"response_mime_type": "application/json", "response_schema": schema} if schema else {}),
    )
    for attempt in range(attempts):
        wait = MIN_SECONDS_BETWEEN_CALLS - (time.time() - _last_call)
        if wait > 0:
            time.sleep(wait)
        _last_call = time.time()
        t0 = time.time()
        try:
            resp = client().models.generate_content(model=model, contents=prompt, config=config)
        except errors.APIError as e:
            code = getattr(e, "code", None)
            if (code == 429 or (code and code >= 500)) and attempt < attempts - 1:
                backoff = min(60, 5 * 2 ** attempt)
                print(f"  [{code}] provider says wait; retrying in {backoff}s")
                time.sleep(backoff)
                continue
            raise
        return resp, stats(model, resp, time.time() - t0)


def stats(model, resp, seconds):
    u = resp.usage_metadata
    tin = getattr(u, "prompt_token_count", 0) or 0
    tout = getattr(u, "candidates_token_count", 0) or 0
    tthink = getattr(u, "thoughts_token_count", 0) or 0
    price = PRICES.get(model, {"in": 0, "out": 0})
    cost = (tin * price["in"] + (tout + tthink) * price["out"]) / 1e6
    return {"model": model, "latency_ms": int(seconds * 1000), "tokens_in": tin,
            "tokens_out": tout, "tokens_thinking": tthink, "cost_usd_if_paid": round(cost, 6)}
