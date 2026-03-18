from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.auth import get_current_user
from app import auth
from app.routers import admin, users, tasks, analytics
from app import job_cards

# Create FastAPI app
app = FastAPI()
app.include_router(job_cards.router)
# Create database tables
Base.metadata.create_all(bind=engine)

# CORS configuration (allow frontend at port 5500)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TEMP: allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(users.router)
app.include_router(tasks.router)
app.include_router(analytics.router)


# Health check
@app.get("/health")
def health_check():
    return {"status": "ok"}


# Root endpoint
@app.get("/")
def root():
    return {"status": "DevWork Tracker backend running 🚀"}


# Protected route example
@app.get("/protected")
def protected_route(current_user: dict = Depends(get_current_user)):
    return {
        "message": "You are authenticated",
        "user": current_user
    }


# Global error handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "message": exc.detail
        },
    )