"""Market Watch v3 — Price-focused FastAPI"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base

app = FastAPI(title="Market Watch AJN", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .routers import auth_router, knmp_router, prices_router, stats_router, users_router
app.include_router(auth_router.router, prefix="/api")
app.include_router(knmp_router.router, prefix="/api")
app.include_router(prices_router.router, prefix="/api")
app.include_router(stats_router.router, prefix="/api")
app.include_router(users_router.router, prefix="/api")

@app.get("/api/health")
def health():
    return {"status": "ok"}

def init_db():
    Base.metadata.create_all(bind=engine)
