from sqlmodel import SQLModel, create_engine, Session
import chromadb
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# ── SQLite ─────────────────────────────────────────────────────────────────
SQLITE_URL = f"sqlite:///{DATA_DIR}/true_companion.db"
engine = create_engine(SQLITE_URL, echo=False)


def get_session():
    with Session(engine) as session:
        yield session


def init_db():
    SQLModel.metadata.create_all(engine)


# ── ChromaDB (embedded, local) ─────────────────────────────────────────────
CHROMA_DIR = DATA_DIR / "chroma"
CHROMA_DIR.mkdir(exist_ok=True)

chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))

# Collections
def get_conversations_collection():
    return chroma_client.get_or_create_collection(
        name="conversations",
        metadata={"hnsw:space": "cosine"},
    )


def get_files_collection():
    return chroma_client.get_or_create_collection(
        name="files",
        metadata={"hnsw:space": "cosine"},
    )
