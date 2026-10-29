from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from capabilities.call.pipeline import run_pipeline

router = APIRouter()


@router.websocket("/stream/{call_sid}")
async def media_stream(websocket: WebSocket, call_sid: str):
    """
    Twilio Media Streams WebSocket endpoint.
    Hands off to the Pipecat pipeline for STT → LLM → TTS.
    """
    await websocket.accept()
    try:
        await run_pipeline(websocket, call_sid)
    except WebSocketDisconnect:
        pass
