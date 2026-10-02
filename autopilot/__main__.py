"""Weekly creator-campaign reporting, end to end.

python -m autopilot data/campaign.csv --name "Nordlys Skin · Autumn launch"
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date, timedelta
from pathlib import Path

from .metrics import compute, load, totals
from .report import html_report, markdown


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="autopilot", description="Build the weekly creator campaign report.")
    p.add_argument("csv", type=Path)
    p.add_argument("--name", default="Creator campaign")
    p.add_argument("--out", type=Path, default=Path("reports"))
    p.add_argument("--ai-summary", action="store_true", help="Let Claude write the client summary (needs ANTHROPIC_API_KEY)")
    a = p.parse_args(argv)

    ms = compute(load(a.csv))
    tot = totals(ms)
    week = date.today() - timedelta(days=date.today().weekday())

    summary = None
    if a.ai_summary:
        if os.environ.get("ANTHROPIC_API_KEY"):
            from .summary import write_summary

            summary = write_summary(a.name, ms, tot)
        else:
            print("No ANTHROPIC_API_KEY set; skipping the AI summary.", file=sys.stderr)

    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "latest.md").write_text(markdown(a.name, ms, tot, summary, week), encoding="utf-8")
    (a.out / "latest.html").write_text(html_report(a.name, ms, tot, summary, week), encoding="utf-8")
    print(f"{a.name}: {tot['creators']} creators, spend EUR {tot['cost_eur']:,.0f}, "
          f"{tot['conversions']} conversions, cost per conversion EUR {tot['cpa']}")
    for m in sorted(ms, key=lambda m: m.action):
        print(f"  {m.action:<5} {m.creator}")
    print(f"Wrote {a.out / 'latest.md'} and {a.out / 'latest.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
