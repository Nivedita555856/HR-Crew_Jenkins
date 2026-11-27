"""
STEP 4 — RUN THE EVALS 🚀

For every test case:
    1. run the real CrewAI crew               (same crews as the website and MCP server)
    2. measure time ⏱ and tokens 🪙            (speed & cost)
    3. run the rule checks ✅                  (checks.py)
    4. ask the AI judge for scores 🧑‍⚖️          (judge.py)
    5. PASS only if all checks pass AND the judge passes
Then save an HTML report in evals/reports/.

Run everything:          uv run python -m evals.run_evals
Only one group:          uv run python -m evals.run_evals --only askhr      (askhr | resignation | safety)
Quick try (2 cases):     uv run python -m evals.run_evals --limit 2
Without the AI judge:    uv run python -m evals.run_evals --no-judge
"""
import argparse
import asyncio
import contextlib
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import database
from crew.hr_crew import HR_POLICY, helpdesk_crew, resignation_crew
from crewai import LLM

from crew.llm import api_key, llm
from evals.checks import run_checks
from evals.dataset import ASK_HR_CASES, RESIGNATION_CASES, SAFETY_CASES
from evals.judge import JUDGE_MODEL, judge_answer
from evals.report import build_html_report

REPORTS_DIR = Path(__file__).parent / "reports"

# Price per 1 million tokens in US$ (input, output). ESTIMATE — check openai.com/pricing and update.
PRICES = {"gpt-4o": (2.50, 10.00), "gpt-4o-mini": (0.15, 0.60), "gpt-4.1": (2.00, 8.00), "gpt-4.1-mini": (0.40, 1.60)}


# ---------------- helpers ----------------
def log(message: str):
    """Progress messages go to stderr, so they still show while crew output goes to the log file."""
    print(message, file=sys.stderr, flush=True)


def employee_by_name(name: str):
    for emp in database.get_employees():
        if name and emp["name"].lower() == name.lower():
            return emp
    return None


def employee_summary(emp) -> str:
    if emp is None:
        return "Not specified (anonymous question)"
    return (
        f"Name: {emp['name']}, Designation: {emp['designation']}, Department: {emp['department']}, "
        f"Date of joining: {emp['date_of_joining']}, Monthly gross salary: Rs. {emp['monthly_salary']}, "
        f"Leave balance: {emp['leave_balance']} days, Notice period: {emp['notice_period_days']} days"
    )


def give_each_agent_its_own_llm(crew):
    """All agents share ONE llm object in crew/llm.py, and CrewAI adds up token usage per agent.
    That would double-count tokens and mix runs together, so for evals each agent gets a fresh LLM."""
    for agent in [*crew.agents, crew.manager_agent]:
        agent.llm = LLM(model=llm.model, api_key=api_key, temperature=0)


def token_counts(result) -> dict:
    usage = getattr(result, "token_usage", None)
    return {
        "prompt": getattr(usage, "prompt_tokens", 0) or 0,
        "completion": getattr(usage, "completion_tokens", 0) or 0,
        "total": getattr(usage, "total_tokens", 0) or 0,
    }


def estimate_cost(tokens: dict) -> float:
    price_in, price_out = PRICES.get(llm.model, PRICES["gpt-4o"])
    return round(tokens["prompt"] / 1e6 * price_in + tokens["completion"] / 1e6 * price_out, 4)


# ---------------- run ONE case through the real crew ----------------
async def run_crew_for_case(category: str, case: dict, tracing: bool):
    """Returns (question_text, answer_text, crew_result)."""
    if category == "resignation":
        emp = employee_by_name(case["employee"])
        inputs = {
            "employee_name": emp["name"], "designation": emp["designation"], "department": emp["department"],
            "date_of_joining": emp["date_of_joining"], "monthly_salary": emp["monthly_salary"],
            "leave_balance": emp["leave_balance"], "notice_period_days": emp["notice_period_days"],
            "resignation_date": case["resignation_date"], "last_working_day": case["last_working_day"],
            "reason": case["reason"], "hr_policy": HR_POLICY,
        }
        crew = resignation_crew.copy()
        crew.tracing = tracing
        give_each_agent_its_own_llm(crew)
        result = await crew.kickoff_async(inputs=inputs)
        question = (f"Process resignation of {emp['name']}: resigned {case['resignation_date']}, "
                    f"last working day {case['last_working_day']}, reason: {case['reason']}")
        # numbers can be in the payroll section or the final report → check both
        answer = result.tasks_output[1].raw + "\n\n---\n\n" + result.raw
        return question, answer, result

    emp = employee_by_name(case.get("employee", ""))
    crew = helpdesk_crew.copy()
    crew.tracing = tracing
    give_each_agent_its_own_llm(crew)
    result = await crew.kickoff_async(inputs={
        "question": case["question"], "employee_context": employee_summary(emp), "hr_policy": HR_POLICY,
    })
    return case["question"], result.raw, result


async def evaluate_case(category: str, case: dict, use_judge: bool, tracing: bool, semaphore) -> dict:
    async with semaphore:
        log(f"  ▶ [{category}] {case['id']} ...")
        row = {"id": case["id"], "category": category, "expected": case["expected"]}
        start = time.perf_counter()
        try:
            question, answer, result = await run_crew_for_case(category, case, tracing)
        except Exception as error:
            row.update(question=case.get("question", ""), answer="", error=str(error), passed=False,
                       seconds=round(time.perf_counter() - start, 1), checks=[], judge=None,
                       tokens={"prompt": 0, "completion": 0, "total": 0}, cost=0)
            log(f"  ✖ {case['id']} crashed: {error}")
            return row

        row["seconds"] = round(time.perf_counter() - start, 1)
        row["question"], row["answer"] = question, answer
        row["tokens"] = token_counts(result)
        row["cost"] = estimate_cost(row["tokens"])
        row["checks"] = run_checks(case, answer, check_format=(category == "askhr"))
        row["judge"] = await asyncio.to_thread(judge_answer, question, case["expected"], answer) if use_judge else None

        checks_ok = all(c["passed"] for c in row["checks"])
        judge_ok = row["judge"]["passed"] if row["judge"] else True
        row["passed"] = checks_ok and judge_ok
        log(f"  {'✅' if row['passed'] else '❌'} {case['id']}  ({row['seconds']}s, {row['tokens']['total']} tokens)")
        return row


# ---------------- main ----------------
async def main():
    parser = argparse.ArgumentParser(description="Run AI evals for the ProITBridge HR Crew")
    parser.add_argument("--only", choices=["askhr", "resignation", "safety"], help="run only one group")
    parser.add_argument("--limit", type=int, help="max cases per group (quick test)")
    parser.add_argument("--no-judge", action="store_true", help="skip the LLM judge (rule checks only)")
    parser.add_argument("--concurrency", type=int, default=2, help="how many crews run at the same time")
    parser.add_argument("--trace", action="store_true", help="send CrewAI traces for eval runs")
    args = parser.parse_args()

    groups = {"askhr": ASK_HR_CASES, "resignation": RESIGNATION_CASES, "safety": SAFETY_CASES}
    if args.only:
        groups = {args.only: groups[args.only]}

    database.init_db()
    REPORTS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    crew_log = REPORTS_DIR / f"crew_log_{stamp}.txt"

    jobs = [(cat, case) for cat, cases in groups.items() for case in cases[: args.limit or None]]
    log(f"\n🧪 Running {len(jobs)} eval cases  (model: {llm.model}, judge: {'off' if args.no_judge else JUDGE_MODEL})")
    log(f"   Crew thinking is written to {crew_log}\n")

    semaphore = asyncio.Semaphore(args.concurrency)
    started = time.perf_counter()
    # CrewAI prints a lot (verbose=True) — send it to a log file to keep the terminal clean
    with open(crew_log, "w", encoding="utf-8") as f, contextlib.redirect_stdout(f):
        results = await asyncio.gather(*[evaluate_case(c, case, not args.no_judge, args.trace, semaphore)
                                         for c, case in jobs])

    run = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "model": llm.model,
        "judge_model": None if args.no_judge else JUDGE_MODEL,
        "wall_seconds": round(time.perf_counter() - started, 1),
        "results": results,
    }

    json_path = REPORTS_DIR / f"eval_{stamp}.json"
    html_path = REPORTS_DIR / f"eval_{stamp}.html"
    json_path.write_text(json.dumps(run, indent=2, ensure_ascii=False), encoding="utf-8")
    html_path.write_text(build_html_report(run), encoding="utf-8")
    (REPORTS_DIR / "latest.html").write_text(build_html_report(run), encoding="utf-8")

    # ---- terminal summary ----
    passed = sum(r["passed"] for r in results)
    log("\n" + "=" * 72)
    log(f"{'CASE':<24}{'GROUP':<13}{'RESULT':<8}{'TIME':>7}{'TOKENS':>9}{'JUDGE (C/F/R)':>15}")
    log("-" * 72)
    for r in results:
        j = r.get("judge") or {}
        scores = f"{j.get('correctness','-')}/{j.get('faithfulness','-')}/{j.get('relevance','-')}" if j else "-"
        log(f"{r['id']:<24}{r['category']:<13}{'PASS' if r['passed'] else 'FAIL':<8}"
            f"{r['seconds']:>6}s{r['tokens']['total']:>9}{scores:>15}")
    log("-" * 72)
    log(f"PASSED {passed}/{len(results)}   total tokens {sum(r['tokens']['total'] for r in results):,}"
        f"   est. cost ${sum(r['cost'] for r in results):.3f}")
    log(f"📄 Report: {html_path}\n")


if __name__ == "__main__":
    asyncio.run(main())
