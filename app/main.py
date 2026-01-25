from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.configs.settings import Settings

settings = Settings()
app = FastAPI(title=settings.app_name)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, __: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "type": "internal_error",
                "message": "Unexpected error",
            }
        },
    )
