"""Market Watch v3 — FastAPI Application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .database import engine, Base
from .config import UPLOAD_DIR
import os

app = FastAPI(title="Market Watch AJN", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Import and register routers
from .routers import auth_router, knmp_router, prices_router, stats_router, progress_router, users_router, export_router
app.include_router(auth_router.router, prefix="/api")
app.include_router(knmp_router.router, prefix="/api")
app.include_router(prices_router.router, prefix="/api")
app.include_router(stats_router.router, prefix="/api")
app.include_router(progress_router.router, prefix="/api")
app.include_router(users_router.router, prefix="/api")
app.include_router(export_router.router, prefix="/api")

@app.get("/api/health")
def health():
    return {"status": "ok"}

def init_db():
    Base.metadata.create_all(bind=engine)
