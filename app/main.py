from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.config import settings
from app.db.session import init_db
from app.api.router import api_router
import os
from fastapi.middleware.cors import CORSMiddleware

def on_startup():
    print("Initializing database...")
    init_db()
    print("Database initialized.")
    upload_dir = "uploaded_documents"
    os.makedirs(upload_dir, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    on_startup()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan= lifespan
)

origins = [
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], 
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Welcome to QuizGeniusAI!"}