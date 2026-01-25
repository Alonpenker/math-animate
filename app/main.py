from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from app.configs.app_settings import *
from app.routes.jobs import router as jobs_router

app = FastAPI(title=APP_NAME,
              description=APP_DESCRIPTION,
              version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_credentials=True,
    allow_methods=["GET","POST"],
    allow_headers=["*"]
)


@app.get("/")
async def root():
    return {"message":"Welcome to my Task Manager API"}

api_router = APIRouter(prefix=ROUTER_PREFIX)
api_router.include_router(jobs_router)

app.include_router(api_router)