from fastapi import FastAPI, APIRouter, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
from app.configs.app_settings import *
from app.dependencies.limiter import limiter, handle_rate_limit_exceeded
from app.dependencies.api_key import verify_api_key
from app.dependencies.db import init_db_pool, init_db_tables, close_db_pool, get_cursor
from app.dependencies.redis_client import init_redis_pool, close_redis_pool, get_redis_client
from app.dependencies.storage import init_storage, get_storage_client
from app.exceptions.exception_handler import handle_exceptions
from app.routes.jobs import router as jobs_router
from app.routes.artifacts import router as artifacts_router
from app.routes.artifacts import internal_router as artifacts_internal_router
from app.routes.knowledge import router as knowledge_router
from app.routes.knowledge import internal_router as knowledge_internal_router
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
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["GET","POST","PATCH","DELETE","OPTIONS"],
    allow_headers=["*"]
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, handle_rate_limit_exceeded)

app.add_exception_handler(Exception, handle_exceptions)

@app.get("/")
async def root():
    return {"message":"Welcome to MathAnimate API"}

@app.get("/health")
async def health_check(cursor = Depends(get_cursor), 
                       redis = Depends(get_redis_client), 
                       storage = Depends(get_storage_client)):
    try:
        cursor.execute("SELECT true")
    except Exception as e:
        raise HTTPException(status_code=503,detail=f"Database is down: {e}")
    try:
        redis.ping()
    except Exception as e:
        raise HTTPException(status_code=503,detail=f"Redis is down: {e}")
    try:
        storage.bucket_exists(settings.storage_bucket)
    except Exception as e:
        raise HTTPException(status_code=503,detail=f"Storage is down: {e}")
    return {"message":"application healthy"}

api_router = APIRouter(prefix=ROUTER_PREFIX, dependencies=[Depends(verify_api_key)])
api_router.include_router(jobs_router)
api_router.include_router(artifacts_router)
api_router.include_router(knowledge_router)
api_router.include_router(usage_router)
app.include_router(api_router)

internal_api_router = APIRouter(prefix=INTERNAL_ROUTER_PREFIX, dependencies=[Depends(verify_api_key)])
internal_api_router.include_router(artifacts_internal_router)
internal_api_router.include_router(knowledge_internal_router)
app.include_router(internal_api_router)