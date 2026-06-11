"""One-time ingestion script — converts HR knowledge base into Pinecone vectors.

Run once (or after any policy/benefits/holidays/contacts update):
    python3 ingest.py

Requires:
    PINECONE_API_KEY  — from https://app.pinecone.io
"""
from __future__ import annotations

import os
import time

from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

from hr_data import BENEFITS, HOLIDAYS, HR_CONTACTS, LEAVE_POLICY

INDEX_NAME   = "hrbot-knowledge"
EMBED_MODEL  = "multilingual-e5-large"
EMBED_DIM    = 1024
BATCH_SIZE   = 50


# ── Document generation ───────────────────────────────────────────────────────

def _dict_to_text(title: str, data: dict) -> str:
    lines = [title, ""]
    for key, val in data.items():
        if isinstance(val, list):
            lines.append(f"{key.replace('_', ' ').title()}:")
            for item in val:
                lines.append(f"  - {item}")
        else:
            lines.append(f"{key.replace('_', ' ').title()}: {val}")
    return "\n".join(lines)


def build_documents() -> list[dict]:
    docs: list[dict] = []

    # Leave policies
    for country, policies in LEAVE_POLICY.items():
        for leave_type, details in policies.items():
            slug = f"{country.lower()}-leave-{leave_type.lower().replace(' ', '-').replace('/', '-')}"
            docs.append({
                "id": slug,
                "text": _dict_to_text(f"{leave_type} Policy — {country}", details),
                "metadata": {"type": "leave_policy", "country": country, "topic": leave_type},
            })

    # Benefits
    for country, benefits in BENEFITS.items():
        for name, details in benefits.items():
            slug = (
                f"{country.lower()}-benefit-"
                + name.lower().replace(" ", "-").replace("(", "").replace(")", "").replace("&", "and")
            )
            docs.append({
                "id": slug,
                "text": _dict_to_text(f"{name} — {country}", details),
                "metadata": {"type": "benefit", "country": country, "topic": name},
            })

    # Holidays
    for country, groups in HOLIDAYS.items():
        for htype, holidays in groups.items():
            lines = [f"{htype.title()} Holidays 2025 — {country}", ""]
            for h in holidays:
                line = f"{h['date']}  {h['name']}"
                if "type" in h:
                    line += f"  [{h['type']}]"
                lines.append(line)
            docs.append({
                "id": f"{country.lower()}-holidays-{htype}",
                "text": "\n".join(lines),
                "metadata": {"type": "holiday", "country": country, "topic": f"{htype} holidays 2025"},
            })

    # HR contacts
    for country, contacts in HR_CONTACTS.items():
        for team, info in contacts.items():
            slug = f"{country.lower()}-contact-{team.lower().replace(' ', '-')}"
            if team == "Escalation Path":
                text = f"HR Escalation Path — {country}\n\n" + "\n".join(info)
            else:
                text = _dict_to_text(f"{team} — {country}", info)
            docs.append({
                "id": slug,
                "text": text,
                "metadata": {"type": "hr_contact", "country": country, "topic": team},
            })

    return docs


# ── Pinecone setup ────────────────────────────────────────────────────────────

def get_or_create_index(pc: Pinecone) -> None:
    existing = [idx.name for idx in pc.list_indexes()]
    if INDEX_NAME not in existing:
        print(f"Creating index '{INDEX_NAME}'...")
        pc.create_index(
            name=INDEX_NAME,
            dimension=EMBED_DIM,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        while not pc.describe_index(INDEX_NAME).status["ready"]:
            time.sleep(1)
        print("Index ready.")
    else:
        print(f"Index '{INDEX_NAME}' already exists.")


# ── Embed + upsert ────────────────────────────────────────────────────────────

def upsert_documents(pc: Pinecone, docs: list[dict]) -> None:
    index = pc.Index(INDEX_NAME)
    for i in range(0, len(docs), BATCH_SIZE):
        batch = docs[i : i + BATCH_SIZE]
        texts = [d["text"] for d in batch]

        embeddings = pc.inference.embed(
            model=EMBED_MODEL,
            inputs=texts,
            parameters={"input_type": "passage", "truncate": "END"},
        )

        vectors = [
            {
                "id": d["id"],
                "values": emb["values"],
                "metadata": {**d["metadata"], "text": d["text"]},
            }
            for d, emb in zip(batch, embeddings)
        ]
        index.upsert(vectors=vectors)
        print(f"Upserted {i + len(batch)}/{len(docs)} documents.")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    pinecone_key = os.environ.get("PINECONE_API_KEY")
    if not pinecone_key:
        raise SystemExit("Set PINECONE_API_KEY environment variable.")

    pc = Pinecone(api_key=pinecone_key)
    docs = build_documents()
    print(f"Built {len(docs)} documents.")

    get_or_create_index(pc)
    upsert_documents(pc, docs)
    print("Ingestion complete.")


if __name__ == "__main__":
    main()
