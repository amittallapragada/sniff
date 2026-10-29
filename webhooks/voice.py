import logging

from fastapi import APIRouter, Form, Request
from fastapi.responses import Response
from twilio.twiml.voice_response import Connect, VoiceResponse

from capabilities.call.session import get_session
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


def _stream_twiml(call_sid: str) -> Response:
    """Return TwiML that opens a bidirectional media stream."""
    ws_url = settings.app_base_url.replace("https://", "wss://").replace("http://", "ws://")
    ws_url = f"{ws_url}/ws/stream/{call_sid}"

    response = VoiceResponse()
    connect = Connect()
    connect.stream(url=ws_url)
    response.append(connect)
    return Response(content=str(response), media_type="application/xml")


@router.post("/voice/outbound")
async def outbound_voice(
    request: Request,
    CallSid: str = Form(...),
):
    """Twilio calls this when an outbound call is answered."""
    logger.info("Outbound voice webhook hit for CallSid: %s", CallSid)
    return _stream_twiml(CallSid)


@router.post("/voice/amd")
async def amd_callback(
    request: Request,
    CallSid: str = Form(...),
    AnsweredBy: str = Form("unknown"),
):
    """Twilio async AMD callback — tells us if a machine or human answered."""
    logger.info("AMD result for %s: %s", CallSid, AnsweredBy)

    if AnsweredBy in ("machine_end_beep", "machine_end_silence", "machine_end_other"):
        session = await get_session(CallSid)
        if session:
            session.voicemail = True
            logger.info("Marked session %s as voicemail", CallSid)

    return Response(status_code=204)
