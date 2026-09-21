"""Day 5. Chunk the 50 contracts and store their embeddings in a local vector database.

Run:  python index.py --size 200 --overlap 40
Build one index per chunk size you want to compare, e.g. 100, 200 and 400 words.
"""
import argparse, time
from config import CONTRACTS
from rag import chunk_text, embed, embedder, get_collection, load_gold


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=200, help="chunk size in words")
    ap.add_argument("--overlap", type=int, default=40, help="words shared by neighbouring chunks")
    a = ap.parse_args()

    splits = {r["contract_id"]: r["split"] for r in load_gold()}
    col = get_collection(a.size, reset=True)
    model = embedder()
    limit = model.max_seq_length

    t0 = time.time()
    total = truncated = 0
    for path in sorted(CONTRACTS.glob("*.txt")):
        cid = path.stem
        chunks = chunk_text(path.read_text(encoding="utf-8"), a.size, a.overlap)
        texts = [c[2] for c in chunks]
        # How many chunks are longer than the embedding model can read?
        lengths = [len(ids) for ids in model.tokenizer(texts, add_special_tokens=True, verbose=False)["input_ids"]]
        truncated += sum(n > limit for n in lengths)
        total += len(chunks)
        col.add(ids=[f"{cid}:{i}" for i in range(len(chunks))],
                embeddings=embed(texts), documents=texts,
                metadatas=[{"contract_id": cid, "split": splits.get(cid, ""), "start": s, "end": e}
                           for s, e, _ in chunks])
        print(f"\r{cid}: {total} chunks so far", end="", flush=True)

    secs = time.time() - t0
    print(f"\n\nIndexed {total} chunks of {a.size} words (overlap {a.overlap}) in {secs:.0f} s")
    print(f"{truncated} chunks ({truncated / total:.0%}) exceed the model's {limit}-token limit; "
          f"the model never sees their endings.")


if __name__ == "__main__":
    main()
