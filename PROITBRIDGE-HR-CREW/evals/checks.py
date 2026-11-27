"""
STEP 2 — RULE-BASED CHECKS ✅  (fast, free, no AI)

Simple Python checks on the answer text:
    must_include      → each item must appear  ("4,000|4000" means either is OK)
    must_not_include  → none of these may appear
    format            → Ask HR answers must have the 4 sections we asked for in tasks.py
"""

ASK_HR_SECTIONS = ["answer", "details", "policy reference", "next steps"]


def _found(option: str, text: str) -> bool:
    """Case-insensitive search. Also matches numbers written with or without commas."""
    option = option.strip().lower()
    text = text.lower()
    return option in text or option.replace(",", "") in text.replace(",", "")


def run_checks(case: dict, answer: str, check_format: bool = False) -> list[dict]:
    results = []

    for item in case.get("must_include", []):
        options = item.split("|")
        ok = any(_found(opt, answer) for opt in options)
        results.append({"name": f"includes '{item}'", "passed": ok})

    for item in case.get("must_not_include", []):
        ok = not _found(item, answer)
        results.append({"name": f"does NOT include '{item}'", "passed": ok})

    if check_format:
        missing = [s for s in ASK_HR_SECTIONS if s not in answer.lower()]
        results.append({
            "name": "has 4 sections (Answer, Details, Policy reference, Next steps)",
            "passed": not missing,
            "detail": f"missing: {', '.join(missing)}" if missing else "",
        })

    return results
