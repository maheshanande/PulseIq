from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pulseiq_backend.core.logging import configure_logging
from pulseiq_backend.api.routes import auth, health, tenants, users, messages, queries
from pulseiq_backend.core.config import settings

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="PulseIQ", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials="*" not in settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(tenants.router)
app.include_router(users.router)
app.include_router(messages.router)
app.include_router(queries.router)
