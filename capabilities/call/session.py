import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from memory.db import get_client


class CallStatus(StrEnum):
    BRIEFING = "briefing"
    ACTIVE = "active"
    AWAITING_INPUT = "awaiting_input"
    COMPLETE = "complete"


@dataclass
class CallSession:
    id: str  # Twilio CallSid
    user_id: str
    mission: str
    status: CallStatus
    pending_question: str | None = None
    transcript: list[dict] = field(default_factory=list)
    voicemail: bool = False
    _input_event: asyncio.Event = field(default_factory=asyncio.Event, repr=False)
    _injected_input: str | None = None


# In-memory registry of active sessions (single server process)
_sessions: dict[str, CallSession] = {}


def create_session(call_sid: str, user_id: str, mission: str) -> CallSession:
    session = CallSession(
        id=call_sid,
        user_id=user_id,
        mission=mission,
        status=CallStatus.BRIEFING,
    )
    _sessions[call_sid] = session
    return session


async def get_active_session(user_id: str) -> CallSession | None:
    """Return the active call session for a user, if any."""
    for session in _sessions.values():
        if session.user_id == user_id and session.status != CallStatus.COMPLETE:
            return session
    return None


async def get_session(call_sid: str) -> CallSession | None:
    return _sessions.get(call_sid)


async def inject_user_input(call_sid: str, text: str) -> None:
    """Called by the SMS webhook when user replies during an active call."""
    session = _sessions.get(call_sid)
    if session:
        session._injected_input = text
        session.status = CallStatus.ACTIVE
        session._input_event.set()


async def wait_for_input(session: CallSession, timeout: int) -> str | None:
    """
    Block until the user injects input via SMS or the timeout fires.
    Returns the input text, or None on timeout.
    """
    session.status = CallStatus.AWAITING_INPUT
    try:
        await asyncio.wait_for(session._input_event.wait(), timeout=timeout)
        result = session._injected_input
        session._injected_input = None
        session._input_event.clear()
        return result
    except TimeoutError:
        session.status = CallStatus.ACTIVE
        return None


def close_session(call_sid: str) -> None:
    session = _sessions.pop(call_sid, None)
    if session:
        session.status = CallStatus.COMPLETE
        # Persist transcript to Supabase
        get_client().table("call_sessions").insert(
            {
                "id": session.id,
                "user_id": session.user_id,
                "mission": session.mission,
                "status": CallStatus.COMPLETE,
                "transcript": session.transcript,
                "created_at": datetime.now(UTC).isoformat(),
            }
        ).execute()
