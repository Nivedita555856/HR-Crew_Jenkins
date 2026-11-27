# ProITBridge HR Crew 🤖 — AI HR Management System (Simple Version)

A multi-agent HR management web app built with **CrewAI + OpenAI + FastAPI**.
The AI code is the **same code as our Colab notebook**, split into small files.

**What it can do**
- 💬 **Ask HR**: any employee can ask any HR question (leave, WFH, salary, reimbursement, benefits, POSH, resignation and more) and get an answer based on the company HR policy.
- 📄 **Resignation**: process a full resignation (policy check, settlement, exit checklist and letters).
- 👥 **Employees**: list and add employees.

## 📁 Folder structure

```
proitbridge-hr-crew/
│
├── crew/                  🧠 THE AI PART (same as the Colab notebook)
│   ├── llm.py             Step 1 – connect to OpenAI
│   ├── agents.py          Step 2 – CREATE THE AGENTS      ⭐
│   ├── tasks.py           Step 3 – GIVE TASKS TO AGENTS   ⭐
│   ├── hr_crew.py         Step 4 – make the Crews and run them
│   └── hr_policy.md       📖 the company HR policy the agents read
│
├── main.py                🌐 the website (FastAPI pages)
├── mcp_server.py          🔌 connects the crew to Claude (MCP)
├── evals/                 🧪 AI evals: tests + LLM judge + HTML report
├── database.py            💾 saves employees, questions & requests (SQLite)
│
├── templates/             🎨 HTML pages
├── static/                🎨 colours (style.css) + logo
│
├── pyproject.toml         📦 project + libraries list (used by uv)
├── uv.lock                📦 exact library versions (same setup for every learner)
├── .python-version        📦 Python version for this project (3.12)
├── requirements.txt       (only for people who still use pip)
└── .env                   🔑 your OpenAI key (secret!)
```

## 🗺️ Colab notebook → project file

| Colab cell | What it does | Project file |
|---|---|---|
| `pip install crewai` | install | `pyproject.toml` (`uv add crewai`) |
| `os.environ[...] = getpass(...)`, `llm = LLM(...)` | OpenAI key + model | `crew/llm.py` (the key comes from `.env`) |
| `hr_policy_agent = Agent(...)` … `hr_manager = Agent(...)` | **create agents** | `crew/agents.py` |
| `hr_policy_task = Task(...)` … `documentation_task = Task(...)` | **give tasks** | `crew/tasks.py` (Part B) |
| `final_hr_task` for the HR Manager | a general HR task | `crew/tasks.py` → `hr_question_task` (Part A) |
| `hr_crew = Crew(..., process=Process.hierarchical, manager_agent=hr_manager)` | build the crew | `crew/hr_crew.py` |
| `result = await hr_crew.kickoff_async()` | run it | `crew/hr_crew.py` → `ask_hr()` / `run_resignation_crew()` |

## 🧠 One team, two crews

The **same 5 agents** do all the HR work. We only change the tasks:

| Crew | Tasks | Who decides who works? |
|---|---|---|
| `helpdesk_crew` (Ask HR) | 1 task: `hr_question_task`, with **no agent assigned** | The **HR Manager** reads the question and delegates to the right specialist(s) |
| `resignation_crew` | 4 tasks, one per specialist | Each task already names its agent; the HR Manager coordinates |

Examples of how the HR Manager delegates a question:
- *"How many casual leaves do I get?"* → HR Policy Agent
- *"How much leave encashment will I get?"* → HR Policy + Payroll Agents
- *"Write an email to request paternity leave"* → HR Policy + Documentation Agents

## 🔄 What happens when an employee asks a question

```
templates/ask.html  (question form)
   │  POST /ask
   ▼
main.py  ── saves the question (RUNNING) ── answer_question() runs in the background
   │
   ▼
crew/hr_crew.py  ask_hr(question, employee details)
   │
   ▼
HR Manager 👔 ── reads the question ── delegates ──► HR Policy / Payroll / Compliance / Documentation
   │
   ▼
database.py  saves the answer (DONE)
   │
   ▼
templates/question.html shows the answer (the page refreshes every 5 s until it is done)
```

## ▶️ Run it (macOS) — with uv

We use **[uv](https://docs.astral.sh/uv/)** instead of pip. It is much faster, installs Python for you,
and `uv run` always uses the project's own environment, so there is **no `source .venv/bin/activate`** to forget.

**1. Install uv (one time only)**
```bash
brew install uv
```

**2. Set up the project**
```bash
cd ~/Downloads/proitbridge-hr-crew
uv sync                     # creates .venv and installs everything from uv.lock
cp .env.example .env        # then open .env (NOT .env.example) and paste your OpenAI key
open -e .env
```

**3. Test 1: ask one HR question in the terminal (like Colab)**
```bash
uv run python -m crew.hr_crew
```

**4. Test 2: run the full website**
```bash
uv run uvicorn main:app --reload
```
Open http://127.0.0.1:8000, click **💬 Ask HR** and ask anything.

### 📦 uv commands learners will use

| Command | What it does | pip version |
|---|---|---|
| `uv sync` | Install everything the project needs | `pip install -r requirements.txt` |
| `uv run <command>` | Run inside the project's environment | `source .venv/bin/activate` then the command |
| `uv add <library>` | Install a new library **and** save it in `pyproject.toml` | `pip install <library>` + edit requirements.txt |
| `uv remove <library>` | Uninstall and remove it from `pyproject.toml` | `pip uninstall <library>` |

> 💡 How this project was created with uv (for reference):
> ```bash
> uv init --python 3.12 --bare      # creates pyproject.toml
> uv add -r requirements.txt        # adds the libraries + creates uv.lock
> ```

## 🧪 AI Evals: test how good our AI HR team is

An **eval** is an exam for the AI. We ask the crew questions we already know the answers to,
then grade the answers automatically. Run it after every change to a prompt, agent, task, policy or model,
so you know whether the change made things **better or worse**.

```
evals/
├── dataset.py        Step 1 – the test questions + expected answers (13 cases)
├── checks.py         Step 2 – rule checks (must include "12", must have 4 sections…)
├── judge.py          Step 3 – LLM-as-a-judge: a 2nd AI scores correctness / faithfulness / relevance (1–5)
├── run_evals.py      Step 4 – runs the real crews, measures time + tokens, saves the report
├── report.py         Step 5 – builds the ProITBridge HTML report
├── test_deepeval.py  Step 6 – the same tests using the DeepEval framework
└── reports/          generated reports (latest.html = most recent)
```

**What is tested (13 cases)**

| Group | Cases | What a PASS means |
|---|---|---|
| 💬 Ask HR | 8 | Correct per `hr_policy.md`, nothing made up, 4-section format, says "not in policy" when it isn't |
| 📄 Resignation | 2 | Correct notice shortfall, per-day salary, leave encashment and recovery amounts |
| 🛡️ Safety | 3 | Doesn't leak another employee's salary, refuses off-topic requests, resists prompt injection |
| ⏱ Speed & cost | all | Time, tokens and estimated $ cost per case |

A case **PASSES** when every rule check passes **and** all three judge scores are 4/5 or higher.

### Option 1: Our own eval runner (simple, easy to read)
```bash
uv run python -m evals.run_evals                  # all 13 cases (≈ 10–15 min)
uv run python -m evals.run_evals --limit 1        # quick try: 1 case per group
uv run python -m evals.run_evals --only safety    # one group: askhr | resignation | safety
uv run python -m evals.run_evals --no-judge       # rule checks only (cheaper)
open evals/reports/latest.html                    # open the report
```
The terminal shows a PASS/FAIL table. The full HTML report lists every answer, check and judge reason.
Crew "thinking" goes to `evals/reports/crew_log_*.txt`, which keeps the terminal clean.

### Option 2: The same tests with DeepEval (industry framework)
```bash
uv run deepeval test run evals/test_deepeval.py
uv run pytest evals/test_deepeval.py -v -k leave-casual     # just one test
```
DeepEval provides ready-made metrics: **GEval** (correctness, safety), **AnswerRelevancyMetric** and **FaithfulnessMetric** (hallucination check against `hr_policy.md`).

| Our runner | DeepEval |
|---|---|
| `judge.py`, our own judge prompt | `GEval` / built-in metrics |
| Scores 1–5, pass at 4 | Scores 0–1, pass at threshold 0.7 |
| Custom HTML report | pytest output, plus an optional Confident AI dashboard |
| Rule checks + speed + cost | Focus on LLM-graded quality |

**Settings (in `.env`):**
- `JUDGE_MODEL=gpt-4o` sets the judge model. It defaults to `OPENAI_MODEL`.
- Prices for the cost estimate are in `PRICES` in `run_evals.py`. Update them from openai.com/pricing.

> 💰 A full run calls the crews 13 times plus the judge, so it costs real OpenAI credit. Use `--limit 1` while teaching.

> ✍️ **Exercise:** add your own test case to `evals/dataset.py`, for example *"How many sick leaves do I get?"* (expected: 10 days). Run the evals, then change `hr_policy.md` to 12 sick leaves and watch the test **fail**. That's why evals matter.

## 🔌 Connect to Claude as an MCP server

`mcp_server.py` turns this project into an **MCP server**. Claude can then use our AI HR team as tools.

It is built exactly like the official tutorial **[Build an MCP server](https://modelcontextprotocol.io/docs/2026-07-28/develop/build-server)** (the weather server). Teach the weather server first, then show this file:

| Official tutorial (`weather.py`) | Our project (`mcp_server.py`) |
|---|---|
| `uv add "mcp[cli]"` | `uv add "mcp[cli]"` (already done) |
| `from mcp.server import MCPServer`<br>`mcp = MCPServer("weather")` | `from mcp.server.fastmcp import FastMCP`<br>`mcp = FastMCP("proitbridge-hr")` |
| Helpers: `make_nws_request()`, `format_alert()` | Helpers: `find_employee()`, `employee_summary()` |
| `@mcp.tool()` `get_alerts`, `get_forecast` | `@mcp.tool()` `ask_hr`, `process_resignation`, `list_employees`, `get_hr_policy` |
| Calls the National Weather Service API | Calls our **CrewAI HR crew** + SQLite database |
| "Never write to stdout": use `logging` | Same: `logging` to stderr, and CrewAI's printing redirected to stderr |
| `mcp.run(transport="stdio")` | `mcp.run(transport="stdio")` |
| Claude config: `uv --directory …/weather run weather.py` | Claude config: `uv --directory …/PROITBRIDGE-HR-CREW run mcp_server.py` |

> **Why `FastMCP` and not `MCPServer`?** The tutorial uses MCP Python SDK **2.x**, where the class is called `MCPServer`.
> CrewAI 1.15 needs MCP SDK **1.x**, where the same class is called `FastMCP`. That one import line is the only difference.
> Build the weather server in its **own folder** (`uv init weather`) so it can use SDK 2.x.

**Our tools:**

| Tool | What it does | Uses AI? |
|---|---|---|
| `ask_hr` | Answers any HR question with the helpdesk crew | ✅ 30–90 s |
| `process_resignation` | Runs the 4-agent resignation crew | ✅ 1–3 min |
| `list_employees` | Lists employees from the database | ❌ instant |
| `get_hr_policy` | Returns `crew/hr_policy.md` | ❌ instant |

Questions and resignations sent from Claude are saved in `hr_app.db`, so they also appear on the website.

**Step 1: Make sure the project works**
```bash
cd ~/Downloads/PROITBRIDGE-HR-CREW
uv sync
uv run python -m crew.hr_crew       # .env must contain your OpenAI key
```

**Step 2 (optional): Test the MCP server in the browser**
```bash
uv run mcp dev mcp_server.py
```
This opens the **MCP Inspector**. Click *Connect* → *Tools* → `list_employees` → *Run Tool*.

**Step 3: Find the full path of uv**
```bash
which uv          # usually /opt/homebrew/bin/uv
```

**Step 4: Add the server to Claude Desktop**

In Claude Desktop, open **Settings → Developer → Edit Config**. This opens
`~/Library/Application Support/Claude/claude_desktop_config.json`. Add `proitbridge-hr` inside `"mcpServers"`.
If the file already has other servers, keep them and add a comma between entries.

```json
{
  "mcpServers": {
    "proitbridge-hr": {
      "command": "/opt/homebrew/bin/uv",
      "args": [
        "--directory",
        "/Users/strephin/Downloads/PROITBRIDGE-HR-CREW",
        "run",
        "mcp_server.py"
      ]
    }
  }
}
```

**Step 5: Restart Claude Desktop**

Quit it completely with **⌘Q**, then open it again. In a new chat, click the **🔌 / tools icon**. You should see **proitbridge-hr** with 4 tools.

**Step 6: Try it**
- *"List all ProITBridge employees."*
- *"Ask the HR team: how many casual leaves does Arun get, and can he carry them forward?"*
- *"Process Priya Raman's resignation, last working day 2026-12-15, reason: higher studies."*

Claude asks permission the first time it uses each tool. Click **Allow**.

**Using Claude Code instead?** Run this one command:
```bash
claude mcp add proitbridge-hr -- uv --directory /Users/strephin/Downloads/PROITBRIDGE-HR-CREW run mcp_server.py
```

**Troubleshooting**

| Problem | Fix |
|---|---|
| Server doesn't show in Claude | Check the JSON (commas and quotes), use the **full path** to uv, then ⌘Q and reopen |
| "Server disconnected" | Read the log: `tail -50 ~/Library/Logs/Claude/mcp-server-proitbridge-hr.log` |
| Tool fails with an API key error | `.env` is missing the key. Check that `uv run python -m crew.hr_crew` works first |
| Tool times out | The crew takes time. Ask a simpler question, or switch `helpdesk_crew` to `Process.sequential` with an `agent=` on the task |

> 💡 Teaching point: Claude is now the **client** and our crew is the **server**. Claude decides *when* to call `ask_hr`, and our HR Manager agent decides *which specialist* answers. That's an AI agent using another team of AI agents.

## 🔍 CrewAI Tracing: see what every agent did

Tracing records each step of a crew run: which agent the HR Manager delegated to,
the prompts, each agent's answer, tool calls, time taken and tokens used. You can then view it as a timeline on **app.crewai.com**.

**How it's switched on in this project**
- `crew/hr_crew.py`: both crews have `tracing=True`
- `.env`: `CREWAI_TRACING_ENABLED=true`

**Show it (one-time login)**
```bash
uv run crewai login            # opens the browser → sign in / create a free CrewAI account
uv run python -m crew.hr_crew  # run the crew
```
At the end of the run, the terminal prints a **trace link**. Open it to see the full timeline.
Every question asked on the website (`uv run uvicorn main:app --reload`) is also traced and appears in your CrewAI dashboard under **Traces**.

> Without logging in, the terminal asks *"Share this execution trace with CrewAI? [y/N]"* after the run. Type **y** to get a temporary trace link.

| Command | What it does |
|---|---|
| `uv run crewai login` | Connects this computer to your CrewAI account |
| `uv run crewai traces status` | Shows whether tracing is on |
| `uv run crewai traces disable` | Turns tracing off (or set `tracing=False`) |

> ⚠️ Traces contain the prompts and answers, including employee details. Use sample data in class, not real employee records.

To change what the agents know, edit **`crew/hr_policy.md`**. It is plain text, so learners can add their own company's rules.

Step-by-step teaching guide with all the code: **BUILD_GUIDE.md**

## ☁️ Deploy to AWS EC2 (GitHub → EC2, with uv)

```
GitHub repo ──git clone / git pull──▶ EC2 (Ubuntu 24.04)
                                       ├── uv sync --frozen --no-dev   (exact versions from uv.lock)
                                       ├── systemd: hr-crew.service    (uvicorn on 127.0.0.1:8000)
                                       └── Nginx :80 ──▶ 127.0.0.1:8000
```

| File | Purpose |
|---|---|
| `deploy/setup_ec2.sh` | One-time setup: nginx, uv, Python 3.12, libraries, service |
| `deploy/update.sh` | Pull latest `main` from GitHub, `uv sync`, restart |
| `deploy/hr-crew.service` | systemd service (auto-restart, starts on boot) |
| `deploy/nginx-hr-crew.conf` | Nginx reverse proxy on port 80 |
| `.github/workflows/deploy-ec2.yml` | Auto-deploy on every push to `main` |

**1. Launch the EC2 instance** (AWS Console → EC2 → Launch instance)
- AMI: **Ubuntu Server 24.04 LTS** · Type: **t3.small** or bigger (CrewAI needs ~2 GB RAM) · Storage: 20 GB
- Key pair: create/download a `.pem` file
- Security group: allow **SSH (22)** from *My IP* and **HTTP (80)** from *Anywhere*

**2. Set it up (one time)**
```bash
ssh -i your-key.pem ubuntu@<EC2-PUBLIC-IP>
git clone https://github.com/<your-username>/<repo>.git ~/PROITBRIDGE-HR-CREW   # private repo: use a token or deploy key
cd ~/PROITBRIDGE-HR-CREW
bash deploy/setup_ec2.sh      # first run creates .env and stops
nano .env                     # paste OPENAI_API_KEY
bash deploy/setup_ec2.sh      # run again → app is live
```
Open `http://<EC2-PUBLIC-IP>/` — health check: `http://<EC2-PUBLIC-IP>/health`

**3. Auto-deploy from GitHub (optional)**
GitHub repo → Settings → Secrets and variables → Actions → add `EC2_HOST` (public IP) and `EC2_SSH_KEY` (contents of the `.pem`).
Now every `git push` to `main` runs `deploy/update.sh` on the server. (For SSH from GitHub, port 22 must be open to GitHub's IPs, or to *Anywhere* with key-only login.)

**Useful commands on EC2**
```bash
sudo systemctl status hr-crew          # is it running?
sudo journalctl -u hr-crew -f          # live logs
bash ~/PROITBRIDGE-HR-CREW/deploy/update.sh   # manual redeploy
```
> 💾 The SQLite database lives at `/var/lib/hr-crew/hr_app.db` (set by `DB_FILE` in `.env`), so `git pull` never overwrites it.
