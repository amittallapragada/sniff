import logging

from browser_use import Agent as BrowserAgent
from browser_use import Browser

from auth.users import User
from config import settings

logger = logging.getLogger(__name__)

MAX_STEPS = 10

_EXTEND_SYSTEM = (
    "Complete the task in as few steps as possible. "
    "Do NOT open multiple tabs. Do NOT search multiple variations. "
    "If a button or element cannot be clicked, use send_keys with Tab/Enter to navigate. "
    "If a page fails to load or shows anti-bot protection, use go_back and try an alternative approach. "
    "When done, use the done action with a clear summary of results."
)


def _get_llm():
    """Get the best available LLM for browser tasks."""
    # ChatBrowserUse is optimized for browser automation (fastest + most accurate)
    if settings.browser_use_api_key:
        from browser_use import ChatBrowserUse

        return ChatBrowserUse()

    # Fallback to Gemini Flash (free tier / cheap paid)
    from browser_use import ChatGoogle

    return ChatGoogle(model="gemini-3.8-flash", api_key=settings.gemini_api_key)


async def run_browser_task(user: User, task: str, start_url: str | None = None) -> str:
    """
    Run a browser-use agent to complete a web task on behalf of the user.
    Returns a plain-text summary of the result.
    """
    full_task = task
    if start_url:
        full_task = f"1. Navigate to {start_url}\n2. {task}"

    llm = _get_llm()
    browser = Browser(headless=True)

    agent = BrowserAgent(
        task=full_task,
        llm=llm,
        browser=browser,
        max_steps=MAX_STEPS,
        use_thinking=False,
        extend_system_message=_EXTEND_SYSTEM,
    )

    try:
        result = await agent.run()
        final = result.final_result()
        if final:
            return str(final)
        extracted = result.extracted_content()
        if extracted:
            return "\n".join(str(e) for e in extracted if e)
        return "Task completed. No specific result to report."
    except Exception as e:
        logger.error("Browser task failed: %s", e)
        return f"Browser task failed: {e}"
