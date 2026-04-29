from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from db.database import get_session
from models.tables import CanvasNode, Conversation, NodeArrow
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/canvas", tags=["canvas"])


class CreateNodeRequest(BaseModel):
    x: float
    y: float
    node_type: str = "chat"


class UpdateNodeRequest(BaseModel):
    x: float | None = None
    y: float | None = None
    title: str | None = None


@router.get("/nodes")
def get_all_nodes(session: Session = Depends(get_session)):
    nodes = session.exec(select(CanvasNode)).all()
    return {"nodes": [n.model_dump() for n in nodes]}


@router.post("/nodes")
def create_node(body: CreateNodeRequest, session: Session = Depends(get_session)):
    node = CanvasNode(x=body.x, y=body.y, node_type=body.node_type)
    session.add(node)
    session.commit()
    session.refresh(node)

    # Auto-create a conversation for chat nodes
    if body.node_type == "chat":
        conv = Conversation(node_id=node.id)
        session.add(conv)
        session.commit()
        session.refresh(conv)
        node.conversation_id = conv.id
        session.add(node)
        session.commit()
        session.refresh(node)

    return node.model_dump()


@router.patch("/nodes/{node_id}")
def update_node(node_id: int, body: UpdateNodeRequest, session: Session = Depends(get_session)):
    node = session.get(CanvasNode, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    if body.x is not None:
        node.x = body.x
    if body.y is not None:
        node.y = body.y
    if body.title is not None:
        node.title = body.title
    node.updated_at = datetime.utcnow()
    session.add(node)
    session.commit()
    session.refresh(node)
    return node.model_dump()


@router.delete("/nodes/{node_id}")
def delete_node(node_id: int, session: Session = Depends(get_session)):
    node = session.get(CanvasNode, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    session.delete(node)
    session.commit()
    return {"status": "deleted"}


@router.get("/arrows")
def get_all_arrows(session: Session = Depends(get_session)):
    arrows = session.exec(select(NodeArrow)).all()
    return {"arrows": [a.model_dump() for a in arrows]}
