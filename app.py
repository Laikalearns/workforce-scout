from __future__ import annotations

import json
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent import demo, loop, plan

load_dotenv()
ROOT = Path(__file__).resolve().parent
app = FastAPI(title="Workforce Scout")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


class Mission(BaseModel):
    prompt: str


@app.get("/")
def index():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/api/presets")
def presets():
    return {"presets": demo.PRESETS, "live": loop.live_enabled(), "snapshot": plan.rollup("base")}


@app.post("/api/run")
def run_mission(mission: Mission):
    prompt = (mission.prompt or "").strip() or demo.PRESETS[0]["prompt"]

    def events():
        for event in loop.run(prompt):
            yield f"data: {json.dumps(event)}\n\n"
        yield 'data: {"type": "done"}\n\n'

    return StreamingResponse(events(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn

    print("\n  Workforce Scout → http://127.0.0.1:8000\n")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
