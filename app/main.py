from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
import socketio
import os

from app.config import settings
from app.database import engine, Base, SessionLocal
import app.models  # Ensure all models are registered
from app.routes.player import router as player_router
from app.routes.admin import router as admin_router
from app.routes.recruitment import router as recruitment_router
from app.routes.ishanya import router as ishanya_router
from app.services.auth import seed_super_admin
from app.socketio_app import sio

# Create database tables
Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------------------------
# Safe startup migrations — PostgreSQL
# All three migrations are idempotent: safe to run on every restart.
# New columns are nullable so existing rows are completely unaffected.
# ---------------------------------------------------------------------------
def _run_migrations():
    with engine.connect() as conn:
        # 1. Make registration.year nullable (existing rows already have values)
        try:
            conn.execute(text(
                "ALTER TABLE registration ALTER COLUMN year DROP NOT NULL"
            ))
            conn.commit()
        except Exception:
            conn.rollback()  # Already nullable — no action needed

        # 2. Add leader_year to ishanya_team (nullable, existing rows get NULL)
        try:
            conn.execute(text(
                "ALTER TABLE ishanya_team ADD COLUMN IF NOT EXISTS leader_year VARCHAR(10)"
            ))
            conn.commit()
        except Exception:
            conn.rollback()  # Column already exists

        # 3. Add year to ishanya_member (nullable, existing rows get NULL)
        try:
            conn.execute(text(
                "ALTER TABLE ishanya_member ADD COLUMN IF NOT EXISTS year VARCHAR(10)"
            ))
            conn.commit()
        except Exception:
            conn.rollback()  # Column already exists

        # 4. Ensure unique index on ishanya_team(team_name)
        try:
            conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_ishanya_team_name ON ishanya_team (LOWER(team_name))"
            ))
            conn.commit()
        except Exception:
            conn.rollback()

        # 5. Ensure unique index on ishanya_team(utr_number) where utr_number is not null
        try:
            conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_ishanya_team_utr ON ishanya_team (utr_number) WHERE utr_number IS NOT NULL AND utr_number != ''"
            ))
            conn.commit()
        except Exception:
            conn.rollback()

_run_migrations()

# Auto-seed Super Admin if not present
with SessionLocal() as db_session:
    seed_super_admin(db_session)

app = FastAPI(title="AARNA Recruitment & Live Event Game API")

# GZip Middleware
app.add_middleware(GZipMiddleware, minimum_size=256)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(player_router, prefix="/api/games", tags=["Flipcard Player"])
app.include_router(player_router, prefix="/api/game", tags=["Flipcard Player (Legacy)"])
app.include_router(player_router, prefix="/api", tags=["Flipcard Player (Root Alias)"])
app.include_router(admin_router, prefix="/api/admin", tags=["Flipcard Admin"])
app.include_router(recruitment_router, tags=["Recruitment & Portal Admin"])
app.include_router(ishanya_router, prefix="/api/ishanya", tags=["Ishanya Event"])

# Mount Socket.IO app
app.mount("/socket.io", socketio.ASGIApp(sio))

# Mount Frontend Static Files with Cache-Control (if present)
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    class CustomStaticFiles(StaticFiles):
        def is_not_modified(self, response_headers, req_headers) -> bool:
            response_headers["Cache-Control"] = "max-age=3600"
            return super().is_not_modified(response_headers, req_headers)
            
    app.mount("/games", CustomStaticFiles(directory=frontend_path, html=True), name="games_frontend")
    app.mount("/flipcard", CustomStaticFiles(directory=frontend_path, html=True), name="flipcard_frontend")
    app.mount("/", CustomStaticFiles(directory=frontend_path, html=True), name="frontend")
