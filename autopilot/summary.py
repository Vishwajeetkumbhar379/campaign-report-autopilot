"""Optional: Claude writes the client summary from the computed numbers only."""
from __future__ import annotations

import json
import os

from .metrics import Metrics

MODEL = os.environ.get("AUTOPILOT_MODEL", "claude-sonnet-4-5")

PROMPT = """You are the account lead on an influencer campaign. Write the weekly client summary.

Rules:
- 4 to 6 sentences, plain English, no bullet points, no emojis.
- Lead with the single most important result.
- Name the best and worst performing creators and say what to do next with budget.
- Use only the numbers provided. Never invent figures.

Campaign data (JSON):
{data}
"""


def write_summary(name: str, ms: list[Metrics], tot: dict, client=None) -> str:
    if client is None:
        import anthropic

        client = anthropic.Anthropic()
    data = {
        "campaign": name,
        "totals": tot,
        "creators": [
            {k: getattr(m, k) for k in ("creator", "platform", "cost_eur", "reach", "engagement_rate", "cpm_reach", "cpa", "roas", "action", "why")}
            for m in ms
        ],
    }
    msg = client.messages.create(
        model=MODEL,
        max_tokens=400,
        messages=[{"role": "user", "content": PROMPT.format(data=json.dumps(data, indent=1))}],
    )
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()
