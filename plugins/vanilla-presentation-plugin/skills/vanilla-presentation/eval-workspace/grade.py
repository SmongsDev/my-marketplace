#!/usr/bin/env python3
"""Grade eval outputs against assertions using grep-based checks."""
import json, re, os
from pathlib import Path

BASE = Path(__file__).parent / "iteration-1"

EVALS = [
    {
        "id": 1, "name": "eval-1-web-dev-intro",
        "assertions": [
            {"id": "single-file",        "desc": "No external JS/CSS src refs",         "pattern": r'<script src=[\'"](?!https://fonts)', "expect_absent": True},
            {"id": "slide-count",        "desc": "6-8 slides",                           "count_pattern": r'<section class="slide', "min": 6, "max": 8},
            {"id": "has-fragments",      "desc": "data-step fragments present",          "pattern": r'data-step=', "expect_present": True},
            {"id": "has-navigation-js",  "desc": "keydown handler present",              "pattern": r'keydown', "expect_present": True},
            {"id": "has-progress-bar",   "desc": "progressFill element present",         "pattern": r'progressFill', "expect_present": True},
            {"id": "has-speaker-notes",  "desc": "speakerNotes JSON present",            "pattern": r'speakerNotes', "expect_present": True},
            {"id": "has-themes",         "desc": "data-theme attributes on slides",      "pattern": r'data-theme=', "expect_present": True},
            {"id": "animation-lock",     "desc": "isAnimating flag present",             "pattern": r'isAnimating', "expect_present": True},
            {"id": "touch-swipe",        "desc": "touchstart handler present",           "pattern": r'touchstart', "expect_present": True},
            {"id": "hash-sync",          "desc": "history.pushState present",            "pattern": r'pushState', "expect_present": True},
        ]
    },
    {
        "id": 2, "name": "eval-2-react-vs-vue",
        "assertions": [
            {"id": "single-file",        "desc": "No external JS/CSS src refs",         "pattern": r'<script src=[\'"](?!https://fonts)', "expect_absent": True},
            {"id": "slide-count",        "desc": "6-9 slides",                           "count_pattern": r'<section class="slide', "min": 6, "max": 9},
            {"id": "has-code-blocks",    "desc": "<pre> code blocks present",            "pattern": r'<pre>', "expect_present": True},
            {"id": "has-fragments",      "desc": "data-step fragments present",          "pattern": r'data-step=', "expect_present": True},
            {"id": "has-navigation-js",  "desc": "keydown handler present",              "pattern": r'keydown', "expect_present": True},
            {"id": "has-speaker-notes",  "desc": "speakerNotes JSON present",            "pattern": r'speakerNotes', "expect_present": True},
            {"id": "animation-lock",     "desc": "isAnimating flag present",             "pattern": r'isAnimating', "expect_present": True},
            {"id": "touch-swipe",        "desc": "touchstart handler present",           "pattern": r'touchstart', "expect_present": True},
            {"id": "hash-sync",          "desc": "history.pushState present",            "pattern": r'pushState', "expect_present": True},
        ]
    },
    {
        "id": 3, "name": "eval-3-startup-pitch",
        "assertions": [
            {"id": "single-file",        "desc": "No external JS/CSS src refs",         "pattern": r'<script src=[\'"](?!https://fonts)', "expect_absent": True},
            {"id": "slide-count",        "desc": "7-9 slides",                           "count_pattern": r'<section class="slide', "min": 7, "max": 9},
            {"id": "has-result-cards",   "desc": "result-card layout present",           "pattern": r'result-card', "expect_present": True},
            {"id": "has-tech-badges",    "desc": "tech-badge layout present",            "pattern": r'tech-badge', "expect_present": True},
            {"id": "has-fragments",      "desc": "data-step fragments present",          "pattern": r'data-step=', "expect_present": True},
            {"id": "has-speaker-notes",  "desc": "speakerNotes JSON present",            "pattern": r'speakerNotes', "expect_present": True},
            {"id": "has-themes",         "desc": "data-theme attributes on slides",      "pattern": r'data-theme=', "expect_present": True},
            {"id": "animation-lock",     "desc": "isAnimating flag present",             "pattern": r'isAnimating', "expect_present": True},
            {"id": "touch-swipe",        "desc": "touchstart handler present",           "pattern": r'touchstart', "expect_present": True},
            {"id": "hash-sync",          "desc": "history.pushState present",            "pattern": r'pushState', "expect_present": True},
            {"id": "dataflow-ai-content","desc": "DataFlow AI company name present",     "pattern": r'DataFlow', "expect_present": True},
        ]
    },
]


def grade_file(html_path, assertions):
    if not html_path.exists():
        return [{"text": a["id"], "passed": False, "evidence": "File not found"} for a in assertions]

    content = html_path.read_text(encoding="utf-8", errors="replace")
    results = []

    for a in assertions:
        if "count_pattern" in a:
            count = len(re.findall(a["count_pattern"], content))
            passed = a["min"] <= count <= a["max"]
            evidence = f"Found {count} matches (expected {a['min']}-{a['max']})"
        elif a.get("expect_absent"):
            matches = re.findall(a["pattern"], content)
            passed = len(matches) == 0
            evidence = f"Found {len(matches)} matches (should be 0)" if not passed else "No forbidden patterns found"
        else:  # expect_present
            matches = re.findall(a["pattern"], content)
            passed = len(matches) > 0
            evidence = f"Found {len(matches)} matches" if passed else f"Pattern '{a['pattern']}' not found"

        results.append({"text": a["id"], "passed": passed, "evidence": evidence})

    return results


all_results = {}
for ev in EVALS:
    ev_dir = BASE / ev["name"]
    for variant in ["with_skill", "without_skill"]:
        html_path = ev_dir / variant / "outputs"
        # find the html file
        html_files = list(html_path.glob("*.html")) if html_path.exists() else []
        html_file = html_files[0] if html_files else html_path / "output.html"

        grades = grade_file(html_file, ev["assertions"])
        passed = sum(1 for g in grades if g["passed"])
        total = len(grades)

        run_id = f"eval-{ev['id']}-{variant}"
        all_results[run_id] = {
            "eval_id": ev["id"],
            "eval_name": ev["name"],
            "variant": variant,
            "pass_rate": passed / total,
            "passed": passed,
            "total": total,
            "assertions": grades
        }

        # Save grading.json
        grading_dir = BASE / ev["name"] / variant
        grading_dir.mkdir(parents=True, exist_ok=True)
        grading_file = grading_dir / "grading.json"
        grading_file.write_text(json.dumps({
            "run_id": run_id,
            "pass_rate": passed / total,
            "expectations": grades
        }, indent=2, ensure_ascii=False))

        print(f"{run_id}: {passed}/{total} ({passed/total*100:.0f}%)")
        for g in grades:
            status = "PASS" if g["passed"] else "FAIL"
            print(f"  {status} {g['text']}: {g['evidence']}")
        print()

# Print summary comparison
print("=" * 60)
print("SUMMARY: with_skill vs without_skill")
print("=" * 60)
for ev in EVALS:
    with_id = f"eval-{ev['id']}-with_skill"
    without_id = f"eval-{ev['id']}-without_skill"
    w = all_results.get(with_id, {})
    wo = all_results.get(without_id, {})
    w_rate = w.get('pass_rate', 0) * 100
    wo_rate = wo.get('pass_rate', 0) * 100
    delta = w_rate - wo_rate
    print(f"Eval {ev['id']} ({ev['name']}):")
    print(f"  with_skill:    {w_rate:.0f}%")
    print(f"  without_skill: {wo_rate:.0f}%")
    print(f"  delta:         {delta:+.0f}%")
    print()
