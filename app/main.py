import logging

from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect

from app.database import engine, Base
from app.auth import get_current_user
from app import auth

# routers
from app.routers import admin, users, tasks, analytics
from app import job_cards


# ==========================
# CREATE APP
# ==========================
app = FastAPI(
    title="DevWork Tracker API",
    version="1.0.0"
)

logger = logging.getLogger(__name__)


# ==========================
# STARTUP EVENT
# ==========================
@app.on_event("startup")
def startup():
    inspector = inspect(engine)
    if not inspector.get_table_names():
        logger.warning("No database tables found. Bootstrapping schema on startup.")
        Base.metadata.create_all(bind=engine)


# ==========================
# 🔥 CORRECT CORS CONFIG (FIXED)
# ==========================

origins = [
    "https://dev-tracker-sigma.vercel.app",
    "http://localhost:3000",
    "http://127.0.0.1:5500"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,   # 🔥 IMPORTANT CHANGE
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================
# ROUTERS
# ==========================
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(tasks.router)
app.include_router(job_cards.router)
app.include_router(analytics.router)


# ==========================
# HEALTH CHECK
# ==========================
@app.get("/health")
def health_check():
    return {"status": "ok"}


# ==========================
# ROOT
# ==========================
@app.get("/")
def root():
    return {
        "success": True,
        "message": "DevWork Tracker backend running 🚀"
    }


# ==========================
# PROTECTED ROUTE
# ==========================
@app.get("/protected")
def protected_route(current_user=Depends(get_current_user)):
    return {
        "success": True,
        "message": "You are authenticated",
        "user": {
            "email": current_user.email,
            "role": current_user.role
        }
    }


# ==========================
# HTTP EXCEPTION HANDLER
# ==========================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled application error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "message": "Internal server error"
        },
    )
