from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.configs.app_settings import *
from app.dependencies.db import init_db_pool, init_db_tables, close_db_pool
from app.dependencies.storage import init_storage
from app.routes.jobs import router as jobs_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db_pool()
    init_db_tables()
    init_storage()
    yield
    # Shutdown
    close_db_pool()

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

# TODO: should add an exception handler

@app.get("/")
async def root():
    return {"message":"Welcome to my Manim Generator API"}

api_router = APIRouter(prefix=ROUTER_PREFIX)
api_router.include_router(jobs_router)

app.include_router(api_router)