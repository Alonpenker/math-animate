from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.configs.app_settings import *
from app.dependencies.db import init_db, close_db
from app.routes.jobs import router as jobs_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown
    close_db()

app = FastAPI(title=APP_NAME,
              description=APP_DESCRIPTION,
              version=APP_VERSION,
              lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_credentials=True,
    allow_methods=["GET","POST"],
    allow_headers=["*"]
)


@app.get("/")
async def root():
    return {"message":"Welcome to my Manim Generator API"}

api_router = APIRouter(prefix=ROUTER_PREFIX)
api_router.include_router(jobs_router)

app.include_router(api_router)