from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from config import settings
from interfaces.telegram import register_webhook
from webhooks.stream import router as stream_router
from webhooks.telegram import router as telegram_router
from webhooks.voice import router as voice_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await register_webhook()
    yield


app = FastAPI(title="Sniff", lifespan=lifespan)

app.include_router(telegram_router, prefix="/webhook")
app.include_router(voice_router, prefix="/webhook")
app.include_router(stream_router, prefix="/ws")


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=False)
