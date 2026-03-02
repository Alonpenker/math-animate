from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.configs.app_settings import *
from app.dependencies.db import init_db_pool, init_db_tables, close_db_pool
from app.dependencies.redis_client import init_redis_pool, close_redis_pool
from app.dependencies.storage import init_storage
from app.exceptions.exception_handler import handle_exceptions
from app.routes.jobs import router as jobs_router
from app.routes.artifacts import router as artifacts_router
from app.routes.knowledge import router as knowledge_router
from app.routes.usage import router as usage_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db_pool()
    init_db_tables()
    init_redis_pool()
    init_storage()
    yield
    # Shutdown
    close_db_pool()
    close_redis_pool()

app = FastAPI(title=APP_NAME,
              description=APP_DESCRIPTION,
              version=APP_VERSION,
              lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_credentials=True,
    allow_methods=["GET","POST","PATCH","DELETE"],
    allow_headers=["*"]
)

app.add_exception_handler(Exception, handle_exceptions)

@app.get("/")
async def root():
    return {"message":"Welcome to my Manim Generator API"}

api_router = APIRouter(prefix=ROUTER_PREFIX)
api_router.include_router(jobs_router)
api_router.include_router(artifacts_router)
api_router.include_router(knowledge_router)
api_router.include_router(usage_router)

app.include_router(api_router)