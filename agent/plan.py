from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = ROOT / "workspace"


def _month_start(stamp: str) -> date:
    y, m = stamp.split("-")[:2]
    return date(int(y), int(m), 1)


def _add_months(start: date, n: int) -> date:
    month = start.month - 1 + n
    year = start.year + month // 12
    month = month % 12 + 1
    return date(year, month, 1)


def _months_between(a: date, b: date) -> int:
    return (b.year - a.year) * 12 + (b.month - a.month)


@dataclass
class Seat:
    key: str
    team: str
    role: str
    level: str
    location: str
    fte: float
    base: float
    start: date
    kind: str
    priority: str = "filled"


def load_state() -> dict:
    assumptions = json.loads((WORKSPACE / "assumptions.json").read_text())
    roster: list[Seat] = []
    with (WORKSPACE / "roster.csv").open() as f:
        for row in csv.DictReader(f):
            roster.append(
                Seat(
                    key=row["employee_id"],
                    team=row["team"],
                    role=row["role"],
                    level=row["level"],
                    location=row["location"],
                    fte=float(row["fte"]),
                    base=float(row["base_salary"]),
                    start=_month_start(row["start_month"]),
                    kind="roster",
                    priority="filled",
                )
            )
    reqs: list[Seat] = []
    with (WORKSPACE / "open_reqs.csv").open() as f:
        for row in csv.DictReader(f):
            reqs.append(
                Seat(
                    key=row["req_id"],
                    team=row["team"],
                    role=row["role"],
                    level=row["level"],
                    location=row["location"],
                    fte=float(row["fte"]),
                    base=float(row["midpoint"]),
                    start=_month_start(row["planned_start"]),
                    kind="req",
                    priority=row["priority"],
                )
            )
    return {"assumptions": assumptions, "roster": roster, "reqs": reqs}


def horizon(assumptions: dict) -> list[date]:
    start = _month_start(assumptions["planning_month"])
    return [_add_months(start, i) for i in range(int(assumptions["horizon_months"]))]


def monthly_loaded(seat: Seat, month: date, burden: float, attrition_monthly: float, scenario: str) -> tuple[float, float]:
    if month < seat.start:
        return 0.0, 0.0
    if seat.kind == "req":
        if scenario == "freeze_all":
            return 0.0, 0.0
        if scenario == "must_only" and seat.priority != "must":
            return 0.0, 0.0
        if scenario == "no_nice" and seat.priority == "nice":
            return 0.0, 0.0
    fte = seat.fte
    if seat.kind == "roster" and month > seat.start:
        elapsed = _months_between(seat.start, month)
        fte *= max(0.0, (1 - attrition_monthly) ** max(elapsed, 0))
    cost = (seat.base / 12.0) * fte * burden
    return fte, cost


def rollup(scenario: str = "base") -> dict:
    state = load_state()
    a = state["assumptions"]
    months = horizon(a)
    attrition_m = 1 - (1 - float(a["annual_attrition"])) ** (1 / 12)
    burden = float(a["burden_rate"])
    seats = state["roster"] + state["reqs"]
    by_month = []
    team_cost: dict[str, float] = {}
    hired = []
    skipped = []
    for month in months:
        fte_total = 0.0
        cost_total = 0.0
        for seat in seats:
            fte, cost = monthly_loaded(seat, month, burden, attrition_m, scenario)
            if seat.kind == "req" and month == seat.start:
                if fte > 0:
                    hired.append({"id": seat.key, "role": seat.role, "team": seat.team, "month": month.isoformat()[:7], "priority": seat.priority})
                else:
                    skipped.append({"id": seat.key, "role": seat.role, "team": seat.team, "priority": seat.priority})
            fte_total += fte
            cost_total += cost
            team_cost[seat.team] = team_cost.get(seat.team, 0.0) + cost
        by_month.append({"month": month.isoformat()[:7], "fte": round(fte_total, 2), "loaded_cost": round(cost_total, 0)})
    window_cost = sum(m["loaded_cost"] for m in by_month)
    cap = float(a["fy_hc_opex_cap"])
    current_fte = round(sum(s.fte for s in state["roster"]), 2)
    open_fte = round(sum(s.fte for s in state["reqs"]), 2)
    return {
        "company": a["company"],
        "scenario": scenario,
        "planning_month": a["planning_month"],
        "burden_rate": burden,
        "current_fte": current_fte,
        "open_req_fte": open_fte,
        "window_loaded_cost": round(window_cost, 0),
        "cap": cap,
        "vs_cap": round(window_cost - cap, 0),
        "headroom": round(cap - window_cost, 0),
        "by_month": by_month,
        "cost_by_team": {k: round(v, 0) for k, v in sorted(team_cost.items())},
        "hires_kept": hired,
        "hires_skipped": skipped,
        "roster_count": len(state["roster"]),
        "req_count": len(state["reqs"]),
    }


def snapshot_text() -> str:
    b = rollup("base")
    teams = ", ".join(f"{k} ${v:,.0f}" for k, v in b["cost_by_team"].items())
    return (
        f"{b['company']} workforce snapshot as of {b['planning_month']}\n"
        f"Current FTE: {b['current_fte']}  |  Open reqs: {b['open_req_fte']} FTE across {b['req_count']} roles\n"
        f"Burden rate: {b['burden_rate']}  |  6-month people opex cap: ${b['cap']:,.0f}\n"
        f"Base plan 6-month loaded cost: ${b['window_loaded_cost']:,.0f}  |  vs cap: ${b['vs_cap']:,.0f}\n"
        f"Team cost in window: {teams}"
    )


def forecast_text(scenario: str = "base") -> str:
    b = rollup(scenario)
    lines = [
        f"Scenario={b['scenario']}  window cost=${b['window_loaded_cost']:,.0f}  cap=${b['cap']:,.0f}  headroom=${b['headroom']:,.0f}",
        "Month          FTE     Loaded $",
    ]
    for row in b["by_month"]:
        lines.append(f"{row['month']:12} {row['fte']:6.2f}   ${row['loaded_cost']:,.0f}")
    if b["hires_kept"]:
        lines.append("Hires kept: " + ", ".join(f"{h['id']} {h['role']} ({h['month']})" for h in b["hires_kept"]))
    if b["hires_skipped"]:
        lines.append("Hires skipped: " + ", ".join(f"{h['id']} {h['role']}" for h in b["hires_skipped"]))
    return "\n".join(lines)


def compare_text() -> str:
    rows = []
    for name in ("base", "no_nice", "must_only", "freeze_all"):
        r = rollup(name)
        rows.append((name, r["window_loaded_cost"], r["headroom"], r["by_month"][-1]["fte"]))
    lines = ["Scenario comparison, Oct 2026 - Mar 2027", f"{'scenario':12} {'cost':>12} {'headroom':>12} {'ending FTE':>12}"]
    for name, cost, head, fte in rows:
        lines.append(f"{name:12} ${cost:>10,.0f} ${head:>10,.0f} {fte:>12.2f}")
    base, freeze = rows[0][1], rows[3][1]
    lines.append(f"Freeze-all savings vs base: ${base - freeze:,.0f}")
    lines.append(f"Dropping nice-to-have reqs saves: ${rows[0][1] - rows[1][1]:,.0f}")
    return "\n".join(lines)


def affordability_text() -> str:
    base = rollup("base")
    must = rollup("must_only")
    no_nice = rollup("no_nice")
    if base["headroom"] >= 0:
        verdict = f"BASE PLAN FITS the ${base['cap']:,.0f} window cap."
    elif no_nice["headroom"] >= 0:
        verdict = "Base plan OVER cap. Cutting nice-to-have reqs brings it inside the cap."
    elif must["headroom"] >= 0:
        verdict = "Need a must-only hire freeze on should/nice roles to stay inside the cap."
    else:
        verdict = "Even must-only hires miss the cap. Slip a must-hire or raise the cap."
    return (
        f"{verdict}\n"
        f"Base headroom: ${base['headroom']:,.0f}\n"
        f"No-nice headroom: ${no_nice['headroom']:,.0f}\n"
        f"Must-only headroom: ${must['headroom']:,.0f}\n"
        "Must hires: R01 Senior FP&A Analyst (Nov), R03 Analytics Engineer (Nov)."
    )


def write_brief(title: str, body: str) -> str:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    safe = "".join(ch if ch.isalnum() or ch in "-_ " else "" for ch in title).strip().replace(" ", "_")[:48]
    path = WORKSPACE / f"{safe or 'brief'}.md"
    path.write_text(f"# {title}\n\n{body.strip()}\n", encoding="utf-8")
    return f"Wrote {path.name}"
