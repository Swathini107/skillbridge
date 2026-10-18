from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routers import health, applications, analyzer, questions, practice, dashboard, resumes

# (lifespan and middleware)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database and tables automatically on startup
    init_db()
    yield


app = FastAPI(
    title="SkillBridge API",
    description="Backend API for SkillBridge — Student Career Preparation & Job Tracking Platform",
    version="1.0.0",
    lifespan=lifespan
)

import os

# Configure CORS for frontend access (configurable via ALLOWED_ORIGINS env var)
env_origins = os.getenv("ALLOWED_ORIGINS")
if env_origins:
    origins = [o.strip() for o in env_origins.split(",") if o.strip()]
else:
    origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(health.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(applications.router, prefix="/api")
app.include_router(analyzer.router, prefix="/api")
app.include_router(questions.router, prefix="/api")
app.include_router(practice.router, prefix="/api")
app.include_router(resumes.router, prefix="/api")

# Also provide root health check for direct accessibility
@app.get("/")
def root():
    return {
        "message": "Welcome to the SkillBridge API",
        "docs": "/docs",
        "health": "/api/health"
    }
