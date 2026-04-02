"""Yado FastAPI application."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response

from yado.database import init_db
from yado.routers import polls, ws


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    await init_db()
    yield


app = FastAPI(title="Yado", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(polls.router)
app.include_router(ws.router)

# Serve SvelteKit static build (production)
_static = Path(__file__).resolve().parent.parent / "static"
_index = _static / "index.html"


@app.get("/{path:path}", include_in_schema=False)
async def spa(path: str) -> Response:
    if ".." not in path:
        file = _static / path
        if file.is_file():
            return FileResponse(file)
    if _index.is_file():
        return FileResponse(_index)
    raise HTTPException(404, "Frontend not built. Run: cd frontend && npm run build")
