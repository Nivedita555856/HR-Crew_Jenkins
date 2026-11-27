"""
STEP 3 — LLM-AS-A-JUDGE 🧑‍⚖️  (a second AI grades our AI's answer)

Rule checks can't tell if an answer is *correct* or *made up*.
So we ask another LLM to compare the answer with the expected answer and the HR policy,
and give scores from 1 (bad) to 5 (perfect):

    correctness   → does it match the expected answer?
    faithfulness  → is everything it says supported by the HR policy? (no hallucination)
    relevance     → does it actually answer the question asked?
"""
import json
import os

from openai import OpenAI

from crew.hr_crew import HR_POLICY
from crew.llm import api_key  # same cleaned key from .env

JUDGE_MODEL = os.getenv("JUDGE_MODEL", os.getenv("OPENAI_MODEL", "gpt-4o")).strip()
PASS_SCORE = 4  # every score must be at least 4 out of 5

client = OpenAI(api_key=api_key)

JUDGE_PROMPT = """You are a strict evaluator of an AI HR assistant for the company ProITBridge.

COMPANY HR POLICY (the only source of truth):
<policy>
{policy}
</policy>

QUESTION / REQUEST:
{question}

EXPECTED ANSWER (what a correct response must contain or do):
{expected}

AI ASSISTANT'S ANSWER:
<answer>
{answer}
</answer>

Score the AI's answer from 1 to 5 on each criterion:
- correctness: matches the expected answer (5 = fully correct, 1 = wrong)
- faithfulness: every claim is supported by the policy or the given employee data; nothing invented (5 = nothing invented)
- relevance: directly answers the question or request (5 = fully on point)

Reply ONLY with JSON:
{{"correctness": <1-5>, "faithfulness": <1-5>, "relevance": <1-5>, "reason": "<one or two sentences>"}}"""


def judge_answer(question: str, expected: str, answer: str) -> dict:
    """Ask the judge LLM to grade one answer. Returns scores, pass/fail and the reason."""
    response = client.chat.completions.create(
        model=JUDGE_MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": JUDGE_PROMPT.format(
            policy=HR_POLICY, question=question, expected=expected, answer=answer)}],
    )
    scores = json.loads(response.choices[0].message.content)
    scores["passed"] = all(scores.get(k, 0) >= PASS_SCORE for k in ("correctness", "faithfulness", "relevance"))
    scores["tokens"] = response.usage.total_tokens if response.usage else 0
    return scores
