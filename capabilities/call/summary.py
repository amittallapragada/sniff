from google import genai
from google.genai import types

from config import settings

_client = genai.Client(api_key=settings.gemini_api_key)
_MODEL = "gemini-3.8-flash"


async def generate_call_summary(mission: str, transcript: list[dict]) -> str:
    """Use Gemini to produce a short post-call debrief from the transcript."""
    if not transcript:
        return "Call ended with no recorded transcript."

    transcript_text = "\n".join(f"{t['role'].capitalize()}: {t['content']}" for t in transcript)

    prompt = (
        f"Mission: {mission}\n\n"
        f"Call transcript:\n{transcript_text}\n\n"
        "Write a brief 2-3 sentence debrief of this call. "
        "Cover: what was accomplished, any key details (date, time, confirmation number, etc.), "
        "and anything that needs follow-up. Be direct and factual."
    )

    response = await _client.aio.models.generate_content(
        model=_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(),
    )
    return response.text.strip()
