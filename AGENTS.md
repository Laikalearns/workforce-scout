# Workforce Scout — Grok Build notes

This is a small FastAPI headcount planner. The UI is a browser page, not the CLI.

## Run (do this unless the user asks to change code)

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then tell the user to open http://127.0.0.1:8000

Demo mode works with no API key. Do not require LLM_API_KEY.

## Do not break

- Keep `agent/plan.py` math intact unless asked.
- Keep workspace CSVs as the source of truth.
- Cap, burden, and scenarios live in `workspace/assumptions.json` and `agent/plan.py`.

## Useful tasks

- Explain the plan like FP&A.
- Run the server.
- Swap `workspace/roster.csv` / `open_reqs.csv` for a real team.
- Do not rewrite this into a chatbot.
