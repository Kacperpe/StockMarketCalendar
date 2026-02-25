from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import accounts, auth, data, ingest
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.models import account_credential, broker_account, daily_metric, trade, user  # noqa: F401


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
    docs_url=f"{settings.api_prefix}/docs",
    openapi_url=f"{settings.api_prefix}/openapi.json",
)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(accounts.router, prefix=settings.api_prefix)
app.include_router(data.router, prefix=settings.api_prefix)
app.include_router(ingest.router, prefix=settings.api_prefix)
