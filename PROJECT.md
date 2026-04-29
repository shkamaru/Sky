# True-Companion — Project Document

**Vision:** A true companion who knows you to make you grow. You can make the best out of you.

**Status:** V1 Planning → Build
**Last updated:** 2026-04-29

---

## 1. What Is This

True-Companion is a personal productivity app running entirely on your local machine. It pairs a freeform spatial canvas (like a living second brain) with a local LLM running via Ollama. Every conversation you have lives as a node on the canvas — positioned by you, connected automatically by the system when topics are related, and stored with vector memory so the companion grows smarter about you over time.

It is not a chat app. It is a thinking environment.

---

## 2. Architecture Overview

Three layers, each building on the one below:

```
┌──────────────────────────────────────────────────────┐
│  HIGH LAYER — Focus Areas (Agents)                   │
│  #1 Read/Write/Research  #2 Build  #3 Grow/Finance   │
├──────────────────────────────────────────────────────┤
│  MID LAYER — Agent Orchestration                     │
│  Spawn, route, coordinate agents via connectors      │
├──────────────────────────────────────────────────────┤
│  BASE LAYER — Core Platform                          │
│  Canvas GUI · LLM (Ollama) · Memory · Security       │
└──────────────────────────────────────────────────────┘
```

V1 builds the entire Base Layer and one agent (Web Search) from the Mid Layer.

---

## 3. V1 Scope

### What we are building

| Area | V1 Feature |
|---|---|
| Canvas | Freeform whiteboard, click anywhere to start a chat node |
| Canvas | Drag and reposition nodes |
| Canvas | Zoom / pan navigation (Figma-style) |
| Canvas | Automatic arrows drawn between semantically related nodes |
| LLM | Ollama integration, switchable model via UI |
| LLM | Companion persona via engineered system prompt |
| Memory | Vector store (semantic search) over all past conversations |
| Memory | Structured user profile (name, goals, interests, projects, philosophy) |
| Memory | Both injected into context at inference time |
| Files | Upload PDF, DOCX, CSV, XLSX, TXT — parsed, embedded, used as context |
| Agents | One agent: Web Search (DuckDuckGo, no API key required) |
| Persistence | All data local — SQLite + ChromaDB (no cloud, no accounts) |

### What is explicitly out of V1

- Widgets that float on the canvas (V2)
- Auto-refresh schedules for agents (V2)
- Finance, Build focus area agents (V2+)
- Email / news connectors (V2+)
- Custom user-defined agents (V2+)
- Audio / video file support (future)
- Fine-tuning model weights (future)
- Multi-model routing (designed for, built later — see Section 6)
- Production deployment / multi-user (future)

---

## 4. Tech Stack

### Why a backend server is needed

The app needs a backend for: streaming LLM responses from Ollama, file parsing (PDF/DOCX/XLSX), maintaining the vector store across sessions, running the web search agent, and managing the semantic similarity engine that auto-draws arrows. Browser-only cannot do this cleanly.

### Recommended Stack

| Layer | Technology | Reason |
|---|---|---|
| Frontend | React + TypeScript | Mature, fast, great canvas library ecosystem |
| Frontend build | Vite | Fast HMR, lightweight |
| Canvas rendering | React-Konva (Konva.js) | 2D canvas with zoom/pan, drag-drop, performant |
| State management | Zustand | Lightweight, no boilerplate |
| Styling | Tailwind CSS | Utility-first, fast to iterate |
| Backend | FastAPI (Python) | Async, fast, best LLM/ML library support |
| LLM interface | Ollama Python SDK | Native Ollama support, streaming |
| Vector store | ChromaDB | Embedded (no separate server), local, semantic search |
| Embeddings | nomic-embed-text via Ollama | Keeps everything in Ollama, no extra dep |
| Structured DB | SQLite via SQLModel | Simple, local, no setup |
| File parsing | PyMuPDF, python-docx, pandas | PDF, DOCX, CSV/XLSX respectively |
| Web search agent | DuckDuckGo Search (ddgs) | Free, no API key, privacy-respecting |
| RAG pipeline | LlamaIndex | File chunking, embedding, retrieval — clean abstraction |

### Project Structure

```
sky/
├── frontend/               # React + Vite app
│   ├── src/
│   │   ├── canvas/         # Canvas engine, node rendering, arrows
│   │   ├── chat/           # Chat UI within a node
│   │   ├── memory/         # User profile display/edit
│   │   ├── agents/         # Agent trigger UI
│   │   └── store/          # Zustand global state
│   └── ...
├── backend/                # FastAPI app
│   ├── api/                # Route handlers
│   ├── core/
│   │   ├── llm.py          # Ollama wrapper, model switching
│   │   ├── memory.py       # Vector store + user profile
│   │   ├── persona.py      # System prompt builder
│   │   └── similarity.py   # Auto-arrow detection
│   ├── agents/
│   │   └── web_search.py   # Web search agent (V1)
│   ├── parsers/            # File type parsers
│   ├── models/             # SQLModel DB schemas
│   └── db/                 # SQLite + ChromaDB setup
├── PROJECT.md
└── First notes.pdf
```

---

## 5. Core Systems — How They Work

### 5.1 Canvas

- The canvas is an infinite 2D plane rendered with Konva.js
- Click anywhere on empty canvas → creates a new **Conversation Node** at that (x, y) position
- Each node opens a chat panel attached to it
- Nodes can be dragged to new positions (x, y saved to SQLite)
- Zoom (scroll wheel) and pan (middle-click drag or space+drag) like Figma
- Node stores: position, title (auto-generated from first message), conversation history ID, embedding vector, created timestamp

### 5.2 Automatic Arrows (Semantic Similarity)

- When a node's first message is sent, its embedding is computed via `nomic-embed-text`
- Cosine similarity is calculated against all existing node embeddings in ChromaDB
- If similarity > threshold (e.g., 0.75), an arrow is drawn between the nodes
- Arrow thickness or opacity can represent strength of relationship
- Arrows are recomputed when new nodes are added (not on every message — only on node creation)

### 5.3 Memory

**Two-layer memory system:**

```
Layer 1 — Structured Profile (SQLite)
  User name, goals, current projects, philosophy, 
  interests, financial situation (broad), reading list
  → Injected as the top of every system prompt

Layer 2 — Episodic Memory (ChromaDB)
  Every conversation chunked and embedded
  → At inference time, semantic search retrieves the 
     top-k most relevant past conversation chunks 
     and injects them into context
```

The companion always "knows" the user profile + recalls the most relevant past conversations before answering.

### 5.4 Companion Persona (Prompt Engineering)

The system prompt is assembled dynamically per request:

```
[COMPANION PERSONA]          ← fixed personality instructions
[USER PROFILE]               ← from SQLite (injected every time)
[RETRIEVED MEMORY]           ← top-k from ChromaDB semantic search
[FILE CONTEXT if uploaded]   ← parsed + chunked file content
[CONVERSATION HISTORY]       ← current node's chat history
[USER MESSAGE]               ← current input
```

The persona block defines the companion's tone: direct, curious, growth-oriented, honest, not sycophantic. We will iterate on this prompt heavily during V1 testing.

### 5.5 Model Switching

- Ollama manages all models locally
- Backend exposes a `/models` endpoint that calls `ollama list`
- Frontend shows a model selector in the top bar
- The selected model is stored in app state and sent with every inference request
- One model is active at a time in V1
- **Architecture note:** The `llm.py` wrapper is designed with a `BaseLLMProvider` interface so a true multi-model router can be dropped in later without touching the rest of the codebase

### 5.6 File Upload

- User can upload files directly on the canvas (drop on empty space, or via a button)
- File is sent to the backend, parsed into text chunks, embedded, stored in ChromaDB tagged with a file ID
- A special **File Node** is created on the canvas at the drop point
- User can start a conversation from that File Node — the file's chunks are retrieved via semantic search and injected as context
- Supported: PDF, DOCX, CSV, XLSX, TXT

### 5.7 Web Search Agent (V1's only agent)

- Triggered from any conversation node via a `/search` command or a "Search Web" button
- Takes the current conversation context, extracts a search query, runs DuckDuckGo search, retrieves top results, summarizes them, and returns the summary as a message in the node
- Results are stored in the node's conversation history
- The agent is a simple tool-call loop: query → fetch → summarize → respond

---

## 6. Multi-Model Question — Decision

**Recommendation for V1: single model active at a time (switchable), not multi-model routing.**

Reasons:
- Multi-model routing (e.g., "use model A for code, model B for reasoning") adds an orchestration layer that is premature before you've found which models work best for your tasks
- The companion persona needs to be tuned to one model at a time — consistency matters for the "companion feel"
- Ollama handles model switching cleanly; you can hot-swap between sessions

**The architecture accommodates multi-model later:** the `BaseLLMProvider` abstraction in `llm.py` means you can later route by task type without rewriting inference logic.

---

## 7. Data Model (SQLite)

```
users (only 1 row — you)
  id, name, created_at

user_profile
  key (e.g., "goals", "interests", "philosophy"), value, updated_at

canvas_nodes
  id, x, y, width, height, type (chat|file), title, 
  conversation_id, file_id, created_at, updated_at

conversations
  id, node_id, created_at

messages
  id, conversation_id, role (user|assistant|agent), 
  content, timestamp, model_used

node_embeddings
  node_id, embedding_id (ChromaDB ref)

files
  id, name, type, path, node_id, uploaded_at

arrows
  id, from_node_id, to_node_id, similarity_score, created_at
```

---

## 8. V1 Build Phases

### Phase 0 — Setup (Day 1–2)
- Initialize monorepo structure (frontend + backend)
- Ollama running locally with at least one model pulled
- FastAPI skeleton with health check
- React + Vite + Konva.js hello world
- SQLite + ChromaDB initialized

### Phase 1 — Canvas Core (Week 1)
- Infinite canvas with zoom/pan
- Click to create a node
- Node drag and reposition
- Node title display
- Basic node persistence to SQLite

### Phase 2 — LLM Chat in Node (Week 1–2)
- Chat panel opens when node is clicked
- FastAPI route → Ollama → streaming response
- Conversation history persisted to SQLite
- Model switcher in UI

### Phase 3 — Companion Memory (Week 2–3)
- User profile form (goals, interests, philosophy, projects)
- Profile injected into system prompt
- ChromaDB setup
- Conversation embedding on node close
- Semantic search retrieval at inference time
- Companion persona system prompt (first iteration)

### Phase 4 — Auto Arrows (Week 3)
- Embedding on node first message
- Cosine similarity check against all nodes
- Arrow drawn on canvas between related nodes
- Similarity threshold tunable in settings

### Phase 5 — File Upload (Week 4)
- File drop on canvas → File Node created
- Backend parsers (PDF, DOCX, CSV, XLSX)
- Chunks embedded into ChromaDB
- File context retrieved in conversation

### Phase 6 — Web Search Agent (Week 4–5)
- `/search` trigger in chat
- DuckDuckGo query + summarization
- Result returned as message in node
- Agent response distinguishable from LLM response in UI

### Phase 7 — Polish & Persona Tuning (Week 5–6)
- Test with different Ollama models (Llama 3.1, Mistral, Phi-3, Qwen2.5)
- Iterate companion system prompt
- UI polish: node styling, arrow rendering, canvas UX
- Performance check: large canvas with many nodes

---

## 9. Open Questions for V1

| Question | Decision needed |
|---|---|
| Which Ollama model to start with? | **`qwen2.5:14b`** (~9GB, Metal GPU on Apple Silicon, best reasoning/speed balance). Also pull `qwen2.5:32b` (~19GB) for heavier tasks. Embeddings: `nomic-embed-text` (274MB). Hardware: Mac Mini Apple Silicon, 24GB unified RAM, 10-core GPU — Ollama uses Metal automatically. |
| Similarity threshold for arrows? | Start at 0.75, make it tunable in settings panel |
| How many memory chunks to retrieve per inference? | Start with top-5 chunks, tune based on context window of model |
| Where does the user profile form live? | Dedicated onboarding form on first launch. Simple fields: name, goals, current projects, interests, philosophy. Can be edited later from a settings panel. |
| Should nodes have a visual type distinction (chat vs file)? | Yes — color or icon difference on the node |

---

## 10. Future Phases (Not V1)

| Phase | What |
|---|---|
| V2 — Agents | Finance agent, Research agent, Build/code agent |
| V2 — Widgets | Focus area outputs as floating canvas widgets, auto-refresh |
| V2 — Connectors | Email (newsletter summaries), News API |
| V2 — Custom Agents | User defines agent name + instructions in UI |
| V3 — Multi-model routing | Route tasks to different models based on type |
| V3 — Fine-tuning | Fine-tune selected model on your personal data/style |
| Future — Audio/Video | Support audio transcription (Whisper), video input |
| Future — Mobile | Companion on phone |

---

## 11. Guiding Principles for This Build

1. **Local first, always.** No data leaves your machine in V1. No cloud, no accounts.
2. **Canvas is truth.** Everything the companion knows is visible as a node. No hidden state.
3. **Companion grows with you.** Memory is not a log — it is a model of who you are.
4. **Build thin, not wide.** Get one thing working deeply before adding the next.
5. **Architect for tomorrow, build for today.** Abstractions at the LLM and agent layer now prevent rewrites later.
