from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class UserProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(index=True, unique=True)   # e.g. "name", "goals", "interests"
    value: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CanvasNode(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    x: float
    y: float
    width: float = 280
    height: float = 60
    node_type: str = "chat"          # "chat" | "file"
    title: str = "New conversation"
    conversation_id: Optional[int] = None
    file_id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Conversation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    node_id: int = Field(foreign_key="canvasnode.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversation.id")
    role: str                       # "user" | "assistant" | "agent"
    content: str
    model_used: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class UploadedFile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    file_type: str
    stored_path: str
    node_id: Optional[int] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class NodeArrow(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    from_node_id: int = Field(foreign_key="canvasnode.id")
    to_node_id: int = Field(foreign_key="canvasnode.id")
    similarity_score: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
