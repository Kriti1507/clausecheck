"""Shared retrieval helpers: chunking, embedding, the vector store, and gold-span matching."""
import csv, json, re
from functools import lru_cache
from config import CHROMA, CONTRACTS, EMBED_MODEL, GOLD

WORD = re.compile(r"\S+")


def chunk_text(text, size_words, overlap_words):
    """Fixed-size windows of words. Returns (start_char, end_char, chunk_text) tuples,
    keeping character offsets so every chunk can be matched back to the lawyers' labels."""
    words = [(m.start(), m.end()) for m in WORD.finditer(text)]
    step = max(1, size_words - overlap_words)
    chunks = []
    for i in range(0, len(words), step):
        window = words[i:i + size_words]
        start, end = window[0][0], window[-1][1]
        chunks.append((start, end, text[start:end]))
        if i + size_words >= len(words):
            break
    return chunks


@lru_cache(maxsize=1)
def embedder():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBED_MODEL)   # downloads ~90 MB on first use


def embed(texts):
    return embedder().encode(list(texts), batch_size=64, normalize_embeddings=True,
                             show_progress_bar=False).tolist()


def collection_name(size_words):
    return f"cuad_w{size_words}"


def get_collection(size_words, reset=False):
    import chromadb
    client = chromadb.PersistentClient(path=str(CHROMA))
    name = collection_name(size_words)
    if reset:
        try:
            client.delete_collection(name)
        except Exception:
            pass
    return client.get_or_create_collection(name, metadata={"hnsw:space": "cosine"})


def retrieve(col, contract_id, query, k):
    """Top-k chunks for one question, searching only inside the contract being reviewed."""
    res = col.query(query_embeddings=embed([query]), n_results=k,
                    where={"contract_id": contract_id},
                    include=["documents", "metadatas", "distances"])
    return [{"text": d, "start": m["start"], "end": m["end"], "distance": dist}
            for d, m, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0])]


def overlaps(chunk, spans):
    """True if a retrieved chunk shares any characters with a lawyer-labelled span."""
    return any(chunk["start"] < end and start < chunk["end"] for start, end in spans)


def load_gold(split=None):
    rows = list(csv.DictReader(open(GOLD, encoding="utf-8")))
    for r in rows:
        r["present"] = r["present"] == "1"
        r["spans"] = json.loads(r["spans"])
    return [r for r in rows if split in (None, r["split"])]


def contract_text(cid):
    return (CONTRACTS / f"{cid}.txt").read_text(encoding="utf-8")
