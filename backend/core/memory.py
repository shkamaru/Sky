"""
Two-layer memory:
  Layer 1 — Structured profile (SQLite via UserProfile table)
  Layer 2 — Episodic memory (ChromaDB semantic search over conversations)
"""
from sqlmodel import Session, select
from models.tables import UserProfile
from db.database import get_conversations_collection
from core.llm import llm


# ── Layer 1: Structured profile ────────────────────────────────────────────

PROFILE_KEYS = ["name", "goals", "current_projects", "interests", "philosophy", "financial_context"]

def get_full_profile(session: Session) -> dict[str, str]:
    results = session.exec(select(UserProfile)).all()
    return {r.key: r.value for r in results}


def upsert_profile(session: Session, key: str, value: str):
    existing = session.exec(select(UserProfile).where(UserProfile.key == key)).first()
    if existing:
        existing.value = value
        session.add(existing)
    else:
        session.add(UserProfile(key=key, value=value))
    session.commit()


def build_profile_block(profile: dict[str, str]) -> str:
    if not profile:
        return ""
    lines = ["## User Profile"]
    for k, v in profile.items():
        if v:
            lines.append(f"- **{k.replace('_', ' ').title()}**: {v}")
    return "\n".join(lines)


# ── Layer 2: Episodic memory (ChromaDB) ────────────────────────────────────

async def embed_and_store_message(
    node_id: int,
    conversation_id: int,
    text: str,
):
    """Embed a message and store in ChromaDB for future retrieval."""
    collection = get_conversations_collection()
    vector = await llm.embed(text)
    doc_id = f"node_{node_id}_conv_{conversation_id}_{hash(text) & 0xFFFFFF}"
    collection.upsert(
        ids=[doc_id],
        embeddings=[vector],
        documents=[text],
        metadatas=[{"node_id": node_id, "conversation_id": conversation_id}],
    )


async def retrieve_relevant_memory(query: str, top_k: int = 5, exclude_node_id: int | None = None) -> list[str]:
    """Semantic search over past conversations."""
    collection = get_conversations_collection()
    if collection.count() == 0:
        return []

    vector = await llm.embed(query)
    results = collection.query(
        query_embeddings=[vector],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas"],
    )
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]

    # Optionally exclude current node's own memories
    if exclude_node_id is not None:
        filtered = [
            doc for doc, meta in zip(docs, metas)
            if meta.get("node_id") != exclude_node_id
        ]
        return filtered

    return docs


def build_memory_block(memories: list[str]) -> str:
    if not memories:
        return ""
    lines = ["## Relevant Past Context"]
    for i, mem in enumerate(memories, 1):
        lines.append(f"{i}. {mem[:300]}")  # cap each chunk to 300 chars
    return "\n".join(lines)
