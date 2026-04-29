"""
Auto-arrow engine — detects semantically related canvas nodes.
Runs after a new node's first message is embedded.
"""
import math
from db.database import get_conversations_collection
from models.tables import NodeArrow, CanvasNode
from sqlmodel import Session, select

SIMILARITY_THRESHOLD = 0.75  # tunable


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x ** 2 for x in a))
    mag_b = math.sqrt(sum(x ** 2 for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


async def detect_and_store_arrows(
    new_node_id: int,
    new_embedding: list[float],
    session: Session,
) -> list[NodeArrow]:
    """
    Compare the new node's embedding against all existing nodes.
    Creates NodeArrow records for any pair above the threshold.
    Returns the list of new arrows created.
    """
    collection = get_conversations_collection()
    if collection.count() == 0:
        return []

    # Fetch all existing node embeddings from ChromaDB
    all_data = collection.get(include=["embeddings", "metadatas"])
    embeddings = all_data.get("embeddings") or []
    metadatas = all_data.get("metadatas") or []

    seen_node_ids: set[int] = set()
    new_arrows: list[NodeArrow] = []

    for embedding, meta in zip(embeddings, metadatas):
        other_node_id = meta.get("node_id")
        if other_node_id is None or other_node_id == new_node_id:
            continue
        if other_node_id in seen_node_ids:
            continue
        seen_node_ids.add(other_node_id)

        score = cosine_similarity(new_embedding, embedding)
        if score >= SIMILARITY_THRESHOLD:
            # Avoid duplicate arrows
            existing = session.exec(
                select(NodeArrow).where(
                    NodeArrow.from_node_id == min(new_node_id, other_node_id),
                    NodeArrow.to_node_id == max(new_node_id, other_node_id),
                )
            ).first()
            if not existing:
                arrow = NodeArrow(
                    from_node_id=min(new_node_id, other_node_id),
                    to_node_id=max(new_node_id, other_node_id),
                    similarity_score=score,
                )
                session.add(arrow)
                new_arrows.append(arrow)

    if new_arrows:
        session.commit()
        for a in new_arrows:
            session.refresh(a)

    return new_arrows
