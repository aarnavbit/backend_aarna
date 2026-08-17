from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
import socketio
import os

from app.config import settings
from app.database import engine, Base
from app.routes.player import router as player_router
from app.routes.admin import router as admin_router
from app.socketio_app import sio

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Live Event Card Matching Game API")

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
app.include_router(player_router, prefix="/api/game", tags=["Player"])
app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])

# Mount Socket.IO app
app.mount("/socket.io", socketio.ASGIApp(sio))

# Mount Frontend Static Files with Cache-Control
# Assuming the frontend is located in a 'frontend' directory at the project root
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    class CustomStaticFiles(StaticFiles):
        def is_not_modified(self, response_headers, req_headers) -> bool:
            # Set Cache-Control header
            response_headers["Cache-Control"] = "max-age=3600"
            return super().is_not_modified(response_headers, req_headers)
            
    app.mount("/", CustomStaticFiles(directory=frontend_path, html=True), name="frontend")
