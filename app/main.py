"""FastAPI application entry point.

On startup it initializes the SQLite schema and seeds sample data if the database
is empty. Run it with::

    uvicorn app.main:app --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from . import db, seed
from .routes import router

STATIC_DIR = Path(__file__).resolve().parent / "static"


# Runs once when the server starts: sets up the database tables and adds sample data if it's a fresh start.
@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    seed.seed_if_empty()
    yield


app = FastAPI(title="AI Anki", version="0.1.0", lifespan=lifespan)
app.include_router(router)


# Serves the web UI when you open the app in a browser.
@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
