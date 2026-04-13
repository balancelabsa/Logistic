from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.tracking import router as shifts_router
from app.api.visits import router as visits_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    default_response_class=ORJSONResponse,
    version="1.0.0",
    description="Production-ready logistics tracking platform backend",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(shifts_router)
app.include_router(visits_router)
app.include_router(admin_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": settings.app_name}
