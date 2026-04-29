from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.database import init_db
from api.models_router import router as models_router
from api.profile_router import router as profile_router
from api.canvas_router import router as canvas_router
from api.chat_router import router as chat_router

app = FastAPI(title="True-Companion API", version="0.1.0")

# CORS — allow Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(models_router)
app.include_router(profile_router)
app.include_router(canvas_router)
app.include_router(chat_router)


@app.on_event("startup")
def on_startup():
    init_db()
    print("✅ True-Companion API ready")


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "true-companion"}
