PRESETS = [
    {
        "id": "afford",
        "label": "Can we fund the reqs?",
        "prompt": "Can we fund every open req through March without breaking the people opex cap? If not, what do we cut?",
    },
    {
        "id": "freeze",
        "label": "Freeze vs grow",
        "prompt": "Compare a full hire freeze against the base plan and a must-hire-only plan.",
    },
    {
        "id": "brief",
        "label": "CFO brief",
        "prompt": "Write a one-page CFO brief on Q4-Q1 headcount: current FTE, planned hires, cost, and recommendation.",
    },
]


def script_for(prompt: str) -> list[dict]:
    text = prompt.lower()
    if "freeze" in text or "compare" in text:
        return FREEZE
    if "brief" in text or "cfo" in text:
        return BRIEF
    return AFFORD


AFFORD = [
    {"type": "status", "text": "Pulling the live plan, not a vibe."},
    {"type": "thought", "text": "First the snapshot, then affordability, then the month-by-month so the cap argument is visible."},
    {"type": "tool", "name": "snapshot", "args": {}},
    {"type": "tool", "name": "can_we_afford", "args": {}},
    {"type": "tool", "name": "forecast", "args": {"scenario": "base"}},
    {"type": "tool", "name": "forecast", "args": {"scenario": "no_nice"}},
    {
        "type": "final",
        "text": (
            "**Snapshot**\n"
            "Northline is planning Oct 2026-Mar 2027 with a $1.07M people-opex cap and a 1.28 burden rate. "
            "Twelve people are already on the roster. Six reqs are open.\n\n"
            "**What breaks the cap**\n"
            "The base plan (fill every req on the posted start month) runs over the cap. "
            "The two nice-to-have roles - Data Analyst in Austin (Jan) and Recruiter (Feb) - are the cleanest cut. "
            "Must-hires stay: Senior FP&A Analyst and Analytics Engineer in November.\n\n"
            "**Recommendation**\n"
            "Run no_nice: keep must + should, slip the two nice reqs past March. "
            "That is the smallest cut that still funds the work Finance and Data already called critical.\n\n"
            "**CFO line**\n"
            "We are not freezing hiring. We are refusing to spend March money on February nice-to-haves."
        ),
    },
]


FREEZE = [
    {"type": "status", "text": "Stacking four scenarios against the same cap."},
    {"type": "thought", "text": "A freeze is a cost number, not a strategy. Show ending FTE and headroom next to each other."},
    {"type": "tool", "name": "compare_scenarios", "args": {}},
    {"type": "tool", "name": "forecast", "args": {"scenario": "must_only"}},
    {"type": "tool", "name": "forecast", "args": {"scenario": "freeze_all"}},
    {
        "type": "final",
        "text": (
            "**Read of the grid**\n"
            "Freeze-all prints the most savings and the worst org: no FP&A senior, no analytics engineer. "
            "Must-only protects the two bottleneck roles and still leaves cap headroom. "
            "Base looks complete and misses the cap.\n\n"
            "**Recommendation**\n"
            "Do not freeze. Do must-only if the cap is sacred this week; do no_nice if should-hires (AP, RevOps systems) can slip two weeks but not two quarters.\n\n"
            "**CFO line**\n"
            "A freeze saves cash and burns capacity. Must-only saves the year without pretending we have spare analysts."
        ),
    },
]


BRIEF = [
    {"type": "status", "text": "Drafting the brief from the model, then writing it down."},
    {"type": "tool", "name": "snapshot", "args": {}},
    {"type": "tool", "name": "compare_scenarios", "args": {}},
    {"type": "tool", "name": "can_we_afford", "args": {}},
    {
        "type": "tool",
        "name": "write_brief",
        "args": {
            "title": "CFO headcount brief",
            "body": (
                "Window: Oct 2026-Mar 2027. Cap $1.07M loaded people cost.\n"
                "Recommend no_nice: keep must and should reqs, slip recruiter and extra data analyst.\n"
                "Must hires stay on November starts."
            ),
        },
    },
    {
        "type": "final",
        "text": (
            "**CFO brief**\n"
            "Northline can staff the work that is already late - FP&A senior and analytics engineering - without a blanket freeze. "
            "The cap breaks only if we treat every req as equal.\n\n"
            "Cut order: nice first (R04, R06), should second (R02, R05), must last.\n"
            "A written copy is in workspace/CFO_headcount_brief.md.\n\n"
            "**CFO line**\n"
            "Headcount is a timing problem. November must-hires stay. February nice-to-haves wait."
        ),
    },
]


def iter_script(prompt: str):
    yield from script_for(prompt)
