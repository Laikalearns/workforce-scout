from __future__ import annotations

import json
import os
from typing import Iterator

import httpx

from . import demo, tools
from .prompts import SYSTEM_PROMPT


def live_enabled() -> bool:
    return bool(os.getenv("LLM_API_KEY", "").strip())


def run(prompt: str, max_steps: int = 6) -> Iterator[dict]:
    if not live_enabled():
        yield {"type": "status", "text": "No API key · demo mode with live plan math"}
        for event in demo.iter_script(prompt):
            if event["type"] == "tool":
                result = tools.run_tool(event["name"], event.get("args") or {})
                yield {**event, "result": result}
            else:
                yield event
        return

    yield {"type": "status", "text": f"Live model · {os.getenv('LLM_MODEL', 'gpt-4o-mini')}"}
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    base = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    headers = {
        "Authorization": f"Bearer {os.getenv('LLM_API_KEY', '')}",
        "Content-Type": "application/json",
    }

    for step in range(1, max_steps + 1):
        yield {"type": "thought", "text": f"Step {step}: asking what number we need next."}
        try:
            with httpx.Client(timeout=60) as client:
                res = client.post(
                    f"{base}/chat/completions",
                    headers=headers,
                    json={
                        "model": os.getenv("LLM_MODEL", "gpt-4o-mini"),
                        "messages": messages,
                        "tools": tools.TOOL_SCHEMAS,
                        "tool_choice": "auto",
                        "temperature": 0.2,
                    },
                )
                res.raise_for_status()
                message = res.json()["choices"][0]["message"]
        except Exception as exc:  # noqa: BLE001
            yield {"type": "error", "text": str(exc)}
            yield {"type": "final", "text": "Live model failed. Rerun without a key to use demo mode."}
            return

        messages.append(message)
        calls = message.get("tool_calls") or []
        if not calls:
            yield {"type": "final", "text": message.get("content") or "(empty)"}
            return
        for call in calls:
            fn = call["function"]
            name = fn["name"]
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            yield {"type": "tool", "name": name, "args": args}
            result = tools.run_tool(name, args)
            yield {"type": "tool", "name": name, "args": args, "result": result}
            messages.append(
                {"role": "tool", "tool_call_id": call["id"], "name": name, "content": result}
            )

    yield {"type": "final", "text": "Hit the step cap. Narrow the question to one scenario."}
