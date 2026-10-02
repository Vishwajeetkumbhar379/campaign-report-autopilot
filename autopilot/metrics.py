"""Campaign maths: the numbers a client asks for every Monday."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Row:
    creator: str
    platform: str
    cost_eur: float
    reach: int
    impressions: int
    likes: int
    comments: int
    shares: int
    saves: int
    clicks: int
    conversions: int
    revenue_eur: float

    @property
    def engagements(self) -> int:
        return self.likes + self.comments + self.shares + self.saves


@dataclass
class Metrics:
    creator: str
    platform: str
    cost_eur: float
    reach: int
    engagements: int
    clicks: int
    conversions: int
    revenue_eur: float
    engagement_rate: float  # % of reach
    cpm_reach: float  # EUR per 1,000 reached
    cpe: float  # EUR per engagement
    cpc: float  # EUR per click
    cpa: float | None  # EUR per conversion
    ctr: float  # clicks / reach, %
    roas: float | None  # revenue / cost
    action: str = ""
    why: str = ""


def _f(v: str) -> float:
    return float(v.replace(",", "")) if v not in ("", None) else 0.0


def load(path: Path) -> list[Row]:
    with open(path, newline="", encoding="utf-8") as f:
        return [
            Row(
                creator=r["creator"],
                platform=r["platform"],
                cost_eur=_f(r["cost_eur"]),
                reach=int(_f(r["reach"])),
                impressions=int(_f(r["impressions"])),
                likes=int(_f(r["likes"])),
                comments=int(_f(r["comments"])),
                shares=int(_f(r["shares"])),
                saves=int(_f(r["saves"])),
                clicks=int(_f(r["clicks"])),
                conversions=int(_f(r["conversions"])),
                revenue_eur=_f(r.get("revenue_eur", "0")),
            )
            for r in csv.DictReader(f)
        ]


def _div(a: float, b: float) -> float:
    return a / b if b else 0.0


def compute(rows: list[Row]) -> list[Metrics]:
    out = []
    for r in rows:
        out.append(
            Metrics(
                creator=r.creator,
                platform=r.platform,
                cost_eur=r.cost_eur,
                reach=r.reach,
                engagements=r.engagements,
                clicks=r.clicks,
                conversions=r.conversions,
                revenue_eur=r.revenue_eur,
                engagement_rate=round(100 * _div(r.engagements, r.reach), 2),
                cpm_reach=round(1000 * _div(r.cost_eur, r.reach), 2),
                cpe=round(_div(r.cost_eur, r.engagements), 3),
                cpc=round(_div(r.cost_eur, r.clicks), 2),
                cpa=round(r.cost_eur / r.conversions, 2) if r.conversions else None,
                ctr=round(100 * _div(r.clicks, r.reach), 2),
                roas=round(r.revenue_eur / r.cost_eur, 2) if r.cost_eur and r.revenue_eur else None,
            )
        )
    recommend(out)
    return out


def totals(ms: list[Metrics]) -> dict:
    cost = sum(m.cost_eur for m in ms)
    reach = sum(m.reach for m in ms)
    eng = sum(m.engagements for m in ms)
    clicks = sum(m.clicks for m in ms)
    conv = sum(m.conversions for m in ms)
    rev = sum(m.revenue_eur for m in ms)
    return {
        "creators": len(ms),
        "cost_eur": cost,
        "reach": reach,
        "engagements": eng,
        "clicks": clicks,
        "conversions": conv,
        "revenue_eur": rev,
        "engagement_rate": round(100 * _div(eng, reach), 2),
        "cpm_reach": round(1000 * _div(cost, reach), 2),
        "cpa": round(_div(cost, conv), 2) if conv else None,
        "roas": round(_div(rev, cost), 2) if rev else None,
    }


def recommend(ms: list[Metrics]) -> None:
    """Scale / keep / cut, judged against the campaign median, not fixed thresholds."""
    if not ms:
        return
    cpas = sorted(m.cpa for m in ms if m.cpa is not None)
    cpms = sorted(m.cpm_reach for m in ms)
    med_cpa = cpas[len(cpas) // 2] if cpas else None
    med_cpm = cpms[len(cpms) // 2]
    for m in ms:
        if m.cpa is not None and med_cpa and m.cpa <= 0.75 * med_cpa:
            m.action, m.why = "scale", f"Conversions cost {m.cpa:.0f} EUR, well below the median of {med_cpa:.0f} EUR"
        elif m.conversions == 0 and m.cpm_reach > 1.25 * med_cpm:
            m.action, m.why = "cut", f"No conversions and reach costs {m.cpm_reach:.0f} EUR per 1,000, above the median"
        elif m.cpa is not None and med_cpa and m.cpa >= 1.5 * med_cpa:
            m.action, m.why = "cut", f"Conversions cost {m.cpa:,.0f} EUR, {m.cpa / med_cpa:.1f}x the median of {med_cpa:.0f} EUR"
        elif m.engagement_rate >= 5 and m.conversions == 0:
            m.action, m.why = "test", "Strong engagement but no sales yet; test a discount code or clearer call to action"
        else:
            m.action, m.why = "keep", "Performing in line with the rest of the campaign"
