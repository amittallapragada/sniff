import logging

from twilio.rest import Client

from auth.users import User
from capabilities.call.session import create_session
from config import settings

logger = logging.getLogger(__name__)

_client = Client(settings.twilio_account_sid, settings.twilio_auth_token)


async def trigger_outbound_call(
    user: User, phone_number: str, mission: str, context: str = ""
) -> str:
    """
    Initiate an outbound call from Twilio. The call connects back to our
    Media Streams WebSocket where the Pipecat pipeline handles the conversation.
    """
    full_mission = mission
    if context:
        full_mission += f"\n\nAdditional context: {context}"

    # Twilio calls our /webhook/voice endpoint on answer, which opens the WS stream.
    twiml_url = f"{settings.app_base_url}/webhook/voice/outbound"
    logger.info("Outbound TwiML URL: %s", twiml_url)

    amd_callback_url = f"{settings.app_base_url}/webhook/voice/amd"

    call = _client.calls.create(
        to=phone_number,
        from_=settings.twilio_phone_number,
        url=twiml_url,
        method="POST",
        machine_detection="DetectMessageEnd",
        async_amd=True,
        async_amd_status_callback=amd_callback_url,
        async_amd_status_callback_method="POST",
    )

    # Register the session immediately so the pipeline knows the mission when it connects
    create_session(call.sid, user.id, full_mission)

    return f"Call placed to {phone_number}. I'll send you a summary when it's done."
