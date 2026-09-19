from __future__ import annotations

from . import plan

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "snapshot",
            "description": "Current headcount, open reqs, burden rate, and 6-month people-cost cap.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "forecast",
            "description": "Month-by-month FTE and fully loaded cost. scenario: base, no_nice, must_only, freeze_all.",
            "parameters": {
                "type": "object",
                "properties": {
                    "scenario": {
                        "type": "string",
                        "enum": ["base", "no_nice", "must_only", "freeze_all"],
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_scenarios",
            "description": "Compare base vs cut-nice vs must-only vs full freeze against the opex cap.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "can_we_afford",
            "description": "Say whether the hire plan fits the remaining people opex cap and what to cut.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_brief",
            "description": "Save a short FP&A brief into the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "body": {"type": "string"},
                },
                "required": ["title", "body"],
            },
        },
    },
]


def run_tool(name: str, arguments: dict | None = None) -> str:
    arguments = arguments or {}
    if name == "snapshot":
        return plan.snapshot_text()
    if name == "forecast":
        return plan.forecast_text(arguments.get("scenario") or "base")
    if name == "compare_scenarios":
        return plan.compare_text()
    if name == "can_we_afford":
        return plan.affordability_text()
    if name == "write_brief":
        return plan.write_brief(arguments.get("title", "brief"), arguments.get("body", ""))
    return f"Unknown tool: {name}"
