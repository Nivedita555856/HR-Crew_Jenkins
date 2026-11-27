"""
STEP 5 — THE HTML REPORT 📊  (ProITBridge colours)

Turns the eval results into one HTML file: summary cards, scores per group,
and every test case with its answer, rule checks and the judge's reason.
"""
import base64
import html
import re
from pathlib import Path

import markdown

LOGO = Path(__file__).resolve().parent.parent / "static" / "logo.png"
GROUP_NAMES = {"askhr": "💬 Ask HR", "resignation": "📄 Resignation", "safety": "🛡️ Safety"}


def _avg(values):
    values = [v for v in values if v is not None]
    return round(sum(values) / len(values), 1) if values else None


def _md(text: str) -> str:
    """Markdown → HTML (adds the empty line Markdown needs before a list)."""
    is_item = lambda line: re.match(r"\s*([-*]|\d+\.)\s", line)
    lines = []
    for line in (text or "").splitlines():
        if is_item(line) and lines and lines[-1].strip() and not is_item(lines[-1]):
            lines.append("")
        lines.append(line)
    return markdown.markdown("\n".join(lines), extensions=["tables"])


def build_html_report(run: dict) -> str:
    results = run["results"]
    total = len(results)
    passed = sum(r["passed"] for r in results)
    judged = [r["judge"] for r in results if r.get("judge")]
    logo = base64.b64encode(LOGO.read_bytes()).decode() if LOGO.exists() else ""

    def score_avg(key):
        return _avg([j.get(key) for j in judged])

    # ---- summary cards ----
    cards = [
        ("Pass rate", f"{round(passed / total * 100) if total else 0}%", f"{passed} of {total} cases"),
        ("Correctness", f"{score_avg('correctness') or '-'}/5", "avg judge score"),
        ("Faithfulness", f"{score_avg('faithfulness') or '-'}/5", "no made-up rules"),
        ("Relevance", f"{score_avg('relevance') or '-'}/5", "answers the question"),
        ("Avg time", f"{_avg([r['seconds'] for r in results]) or 0}s", "per case"),
        ("Tokens", f"{sum(r['tokens']['total'] for r in results):,}",
         f"est. ${sum(r['cost'] for r in results):.3f}"),
    ]
    cards_html = "".join(f'<div class="card"><span>{t}</span><b>{v}</b><small>{s}</small></div>' for t, v, s in cards)

    # ---- per-group table ----
    group_rows = ""
    for key, name in GROUP_NAMES.items():
        rows = [r for r in results if r["category"] == key]
        if not rows:
            continue
        g_pass = sum(r["passed"] for r in rows)
        g_j = [r["judge"] for r in rows if r.get("judge")]
        group_rows += (
            f"<tr><td>{name}</td><td>{g_pass}/{len(rows)}</td>"
            f"<td>{_avg([j['correctness'] for j in g_j]) or '-'}</td>"
            f"<td>{_avg([j['faithfulness'] for j in g_j]) or '-'}</td>"
            f"<td>{_avg([j['relevance'] for j in g_j]) or '-'}</td>"
            f"<td>{_avg([r['seconds'] for r in rows])}s</td>"
            f"<td>{sum(r['tokens']['total'] for r in rows):,}</td></tr>"
        )

    # ---- every case ----
    case_html = ""
    for r in results:
        badge = '<span class="badge pass">PASS</span>' if r["passed"] else '<span class="badge fail">FAIL</span>'
        checks = "".join(
            f'<li class="{"ok" if c["passed"] else "bad"}">{"✓" if c["passed"] else "✗"} {html.escape(c["name"])}'
            f'{" — " + html.escape(c["detail"]) if c.get("detail") else ""}</li>'
            for c in r.get("checks", [])
        ) or "<li>—</li>"
        j = r.get("judge")
        judge_html = (
            f'<div class="scores"><span>Correctness <b>{j["correctness"]}</b></span>'
            f'<span>Faithfulness <b>{j["faithfulness"]}</b></span><span>Relevance <b>{j["relevance"]}</b></span></div>'
            f'<p class="reason">🧑‍⚖️ {html.escape(j.get("reason", ""))}</p>'
        ) if j else '<p class="muted">Judge not run.</p>'
        error = f'<p class="error">Error: {html.escape(r["error"])}</p>' if r.get("error") else ""
        case_html += f"""
        <details class="case">
          <summary>{badge}<span class="cid">{html.escape(r['id'])}</span>
            <span class="grp">{GROUP_NAMES.get(r['category'], r['category'])}</span>
            <span class="meta">{r['seconds']}s · {r['tokens']['total']:,} tokens</span></summary>
          <div class="body">
            <p><b>Question:</b> {html.escape(r.get('question', ''))}</p>
            <p><b>Expected:</b> {html.escape(r['expected'])}</p>
            {error}
            <div class="grid">
              <div><h4>Rule checks</h4><ul class="checks">{checks}</ul><h4>AI judge</h4>{judge_html}</div>
              <div><h4>Crew answer</h4><div class="answer">{_md(r.get('answer', ''))}</div></div>
            </div>
          </div>
        </details>"""

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>HR Crew Eval Report · {run['timestamp']}</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{{--navy:#002060;--cyan:#00b0f0;--deep:#01153a;--soft:#e6f7fe;--muted:#5b6b82;--line:#e3eaf3;--ok:#0f9d74;--bad:#d64545}}
*{{box-sizing:border-box}} body{{margin:0;font-family:Inter,sans-serif;background:#f3f7fb;color:#1a1a1a;line-height:1.5}}
h1,h2,h3,h4{{font-family:Poppins,sans-serif;color:var(--navy);margin:0}}
header{{background:linear-gradient(135deg,var(--deep),var(--navy));color:#cfe6f5;padding:24px}}
.wrap{{max-width:1150px;margin:0 auto;padding:0 16px}}
.logo{{background:#fff;border-radius:10px;padding:6px 10px;width:220px}} .logo img{{width:100%;display:block}}
header h1{{color:#fff;font-size:26px;margin-top:14px}} header p{{margin:4px 0 0;color:#9cc7e3;font-size:14px}}
main{{padding:24px 0 40px}} .cards{{margin-top:4px}} section{{background:#fff;border-radius:14px;padding:20px;margin-bottom:18px;box-shadow:0 6px 20px rgba(1,21,58,.06)}}
.cards{{display:grid;grid-template-columns:repeat(6,1fr);gap:12px}}
.card{{background:#fff;border-radius:12px;padding:14px;border-top:3px solid var(--cyan);box-shadow:0 6px 20px rgba(1,21,58,.06)}}
.card span{{display:block;font-size:12px;color:var(--muted)}} .card b{{display:block;font:700 26px Poppins,sans-serif;color:var(--navy)}} .card small{{color:var(--muted);font-size:12px}}
table{{width:100%;border-collapse:collapse;font-size:14px}} th{{background:var(--navy);color:#fff;text-align:left;padding:8px 10px}} td{{padding:8px 10px;border-bottom:1px solid var(--line)}}
.case{{border:1px solid var(--line);border-radius:12px;margin-bottom:10px;background:#fff}}
.case summary{{cursor:pointer;padding:12px 14px;display:flex;gap:12px;align-items:center;flex-wrap:wrap}}
.cid{{font-weight:600;color:var(--navy)}} .grp{{font-size:13px;color:var(--muted)}} .meta{{margin-left:auto;font-size:13px;color:var(--muted)}}
.badge{{font-size:12px;font-weight:700;padding:3px 10px;border-radius:99px}} .badge.pass{{background:#e3f7ef;color:var(--ok)}} .badge.fail{{background:#fde8e8;color:var(--bad)}}
.body{{padding:0 16px 16px;border-top:1px solid var(--line)}} .grid{{display:grid;grid-template-columns:1fr 1.4fr;gap:20px}}
h4{{font-size:14px;margin:14px 0 6px}} .checks{{list-style:none;padding:0;margin:0;font-size:14px}} .ok{{color:var(--ok)}} .bad{{color:var(--bad)}}
.scores{{display:flex;gap:10px;flex-wrap:wrap}} .scores span{{background:var(--soft);border-radius:8px;padding:4px 10px;font-size:13px}}
.reason{{font-size:14px;color:#333}} .muted{{color:var(--muted)}} .error{{color:var(--bad)}}
.answer{{background:#f8fbfe;border:1px solid var(--line);border-radius:10px;padding:10px 14px;font-size:14px;max-height:420px;overflow:auto}}
.answer table th{{background:#e6eef8;color:var(--navy)}}
@media(max-width:900px){{.cards{{grid-template-columns:repeat(2,1fr)}} .grid{{grid-template-columns:1fr}}}}
</style></head><body>
<header><div class="wrap">
  {f'<div class="logo"><img src="data:image/png;base64,{logo}" alt="ProITBridge"></div>' if logo else ''}
  <h1>HR Crew — AI Eval Report</h1>
  <p>{run['timestamp']} · crew model <b>{run['model']}</b> · judge <b>{run['judge_model'] or 'off'}</b> · total run time {run['wall_seconds']}s</p>
</div></header>
<main class="wrap">
  <div class="cards">{cards_html}</div><br>
  <section><h3 style="margin-bottom:10px">Results by group</h3>
    <table><tr><th>Group</th><th>Passed</th><th>Correctness</th><th>Faithfulness</th><th>Relevance</th><th>Avg time</th><th>Tokens</th></tr>{group_rows}</table>
  </section>
  <section><h3 style="margin-bottom:12px">All test cases <small class="muted">(click to open)</small></h3>{case_html}</section>
  <p class="muted" style="font-size:12px">A case PASSES when every rule check passes and all three judge scores are 4 or higher. Costs are estimates.</p>
</main></body></html>"""
