import json
import logging

from google import genai
from google.genai import types

from agent.prompt import build_system_prompt
from agent.tools import ALL_TOOLS
from auth.users import User
from capabilities.browser.tasks import run_browser_task
from capabilities.call.outbound import trigger_outbound_call
from capabilities.search.scrappa import scrappa_search
from capabilities.search.web import web_search
from config import settings
from memory.history import append_message, get_recent_history
from memory.semantic import recall, store_preference

logger = logging.getLogger(__name__)

_client = genai.Client(api_key=settings.gemini_api_key)
_MODEL = "gemini-3.8-flash"

# Convert tool defs to Gemini FunctionDeclaration format
_TOOLS = [
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name=t["name"],
                description=t["description"],
                parameters=t["parameters"],
            )
            for t in ALL_TOOLS
        ]
    )
]


async def handle_message(user: User, text: str, channel: str = "telegram") -> str:
    """
    Core agent entry point. Receives a normalized message, runs the LLM,
    dispatches tool calls, and returns the reply text.
    """
    await append_message(user.id, channel, "user", text)

    history = await get_recent_history(user.id, channel)
    memory = await recall(user.id, text)
    system_prompt = build_system_prompt(user, memory)

    # Build Gemini content history (exclude the message we just stored)
    contents = []
    for msg in history[:-1]:
        role = msg["role"] if msg["role"] in ("user", "model") else "model"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))
    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=text)]))

    config = types.GenerateContentConfig(
        max_output_tokens=1024,
        thinking_config=types.ThinkingConfig(thinking_level="low"),
        tools=_TOOLS,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        system_instruction=system_prompt,
    )

    response = await _client.aio.models.generate_content(
        model=_MODEL,
        contents=contents,
        config=config,
    )

    reply = await _process_response(user, response, contents, config, channel)
    await append_message(user.id, channel, "model", reply)
    return reply


async def _process_response(user: User, response, contents: list, config, channel: str) -> str:
    """Agentic loop: process tool calls until we get a text response."""
    max_iterations = 3
    for _ in range(max_iterations):
        # Check for function calls
        function_calls = response.function_calls
        if not function_calls:
            # No tool calls — return text
            text = response.text
            if text:
                return text.strip()
            return "I ran into an issue processing that. Try again?"

        # Execute all function calls
        function_responses = []
        direct_return = None
        for fc in function_calls:
            args = dict(fc.args) if fc.args else {}
            result = await _dispatch_tool(user, fc.name, args, channel)
            if fc.name in ("place_call", "remember"):
                direct_return = result
            function_responses.append(
                types.Part.from_function_response(
                    name=fc.name,
                    response={"result": result[:10000]},
                )
            )

        if direct_return is not None:
            return direct_return

        # Append model response + function results back to contents
        contents.append(response.candidates[0].content)
        contents.append(types.Content(role="user", parts=function_responses))

        response = await _client.aio.models.generate_content(
            model=_MODEL,
            contents=contents,
            config=config,
        )

    # Exhausted iterations
    text = response.text
    if text:
        return text.strip()
    return "I ran into an issue processing that. Try again?"


async def _dispatch_tool(user: User, tool_name: str, args: dict, channel: str) -> str:
    if tool_name == "place_call":
        return await trigger_outbound_call(
            user, args["phone_number"], args["mission"], args.get("context", "")
        )

    if tool_name == "web_search":
        return await web_search(args["query"])

    if tool_name == "scrappa_search":
        result = await scrappa_search(args["endpoint"], args.get("params", {}))
        return json.dumps(result, indent=2)

    if tool_name == "browse_web":
        return await run_browser_task(user, args["task"], args.get("start_url"))

    if tool_name == "remember":
        await store_preference(user.id, args["content"])
        return "Got it, I'll remember that."

    return f"Unknown tool: {tool_name}"
