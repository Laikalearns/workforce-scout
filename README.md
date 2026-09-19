# Workforce Scout

A small finance agent for **headcount planning**.

It reads a roster and open reqs, rolls a 6-month fully loaded cost, and tells you whether the hire plan fits the people-opex cap.

Demo mode uses the same math as live mode. No API key required.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:8000

## What it plans

- Company: fictional **Northline**
- Window: Oct 2026 – Mar 2027
- Burden: 1.28x base salary
- Cap: $1.07M loaded people cost in the window
- Scenarios: `base`, `no_nice`, `must_only`, `freeze_all`

## Showcase prompts

1. **Can we fund the reqs?** — base plan vs cap, what to cut first
2. **Freeze vs grow** — four scenarios, ending FTE, savings
3. **CFO brief** — writes a note into `workspace/`

## How to talk about it

- “I don’t guess headcount cost. Fully loaded = base / 12 × FTE × 1.28, timed from the start month.”
- “Nice-to-have reqs are the first cut. Must-hires in November stay.”
- “A freeze saves cash and shrinks capacity. The model shows both.”

Spoken script: [demos/interview_script.md](demos/interview_script.md)

## Files

```
app.py                 API + UI server
agent/plan.py          the actual FP&A math
agent/tools.py         snapshot, forecast, compare, afford, write_brief
workspace/roster.csv   current people
workspace/open_reqs.csv planned hires
workspace/assumptions.json cap, burden, attrition
```

Swap the CSVs for a real team and the same agent still runs.

## License

MIT
