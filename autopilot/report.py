"""Turns metrics into a client-ready weekly report (Markdown for GitHub, HTML for email)."""
from __future__ import annotations

import html
from datetime import date

from .metrics import Metrics

ACTION_COLOR = {"scale": "#1f7a4f", "keep": "#5b6770", "test": "#b7791f", "cut": "#b42318"}


def eur(v: float | None, d: int = 0) -> str:
    return "n/a" if v is None else f"EUR {v:,.{d}f}"


def num(v: float) -> str:
    return f"{v:,.0f}"


def markdown(name: str, ms: list[Metrics], tot: dict, summary: str | None, week: date) -> str:
    ranked = sorted(ms, key=lambda m: (m.cpa is None, m.cpa or 0))
    lines = [
        f"# {name} · weekly creator report",
        f"_Week of {week:%d %B %Y} · generated automatically_",
        "",
        "## Headline numbers",
        "",
        "| Spend | Reach | Engagement rate | Cost per 1,000 reached | Conversions | Cost per conversion | ROAS |",
        "|---:|---:|---:|---:|---:|---:|---:|",
        f"| {eur(tot['cost_eur'])} | {num(tot['reach'])} | {tot['engagement_rate']}% | {eur(tot['cpm_reach'], 2)} "
        f"| {num(tot['conversions'])} | {eur(tot['cpa'], 2)} | {tot['roas'] or 'n/a'}x |",
        "",
    ]
    if summary:
        lines += ["## Summary", "", summary.strip(), ""]
    lines += [
        "## By creator",
        "",
        "| Creator | Platform | Spend | Reach | ER | Per 1,000 reached | Per conversion | ROAS | Action |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for m in ranked:
        lines.append(
            f"| {m.creator} | {m.platform} | {eur(m.cost_eur)} | {num(m.reach)} | {m.engagement_rate}% "
            f"| {eur(m.cpm_reach, 2)} | {eur(m.cpa, 2)} | {m.roas or 'n/a'} | **{m.action}** |"
        )
    lines += ["", "## Next moves", ""]
    for action in ("scale", "test", "cut"):
        for m in [m for m in ranked if m.action == action]:
            lines.append(f"- **{action.title()} {m.creator}.** {m.why}.")
    lines += ["", "<sub>ER = engagements / reach. ROAS = revenue / spend. Actions compare each creator with the campaign median.</sub>", ""]
    return "\n".join(lines)


def _bar_chart(ms: list[Metrics]) -> str:
    """Inline SVG: cost per conversion by creator, coloured by action."""
    data = sorted([m for m in ms if m.cpa is not None], key=lambda m: m.cpa)
    if not data:
        return ""
    w, row, left, right = 640, 30, 170, 80
    h = row * len(data) + 20
    mx = max(m.cpa for m in data)
    parts = [f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="Cost per conversion by creator">']
    for i, m in enumerate(data):
        y = 10 + i * row
        bw = (w - left - right) * m.cpa / mx
        c = ACTION_COLOR.get(m.action, "#5b6770")
        parts.append(f'<text x="{left - 10}" y="{y + 17}" text-anchor="end" font-size="13" fill="#1d2939">{html.escape(m.creator)}</text>')
        parts.append(f'<rect x="{left}" y="{y + 4}" width="{bw:.1f}" height="18" rx="3" fill="{c}"/>')
        parts.append(f'<text x="{left + bw + 6:.1f}" y="{y + 17}" font-size="12" fill="#475467">EUR {m.cpa:,.2f}</text>')
    parts.append("</svg>")
    return "".join(parts)


def html_report(name: str, ms: list[Metrics], tot: dict, summary: str | None, week: date) -> str:
    ranked = sorted(ms, key=lambda m: (m.cpa is None, m.cpa or 0))
    rows = "".join(
        f"<tr><td>{html.escape(m.creator)}</td><td>{m.platform}</td><td>{eur(m.cost_eur)}</td><td>{num(m.reach)}</td>"
        f"<td>{m.engagement_rate}%</td><td>{eur(m.cpm_reach, 2)}</td><td>{eur(m.cpa, 2)}</td>"
        f'<td><span class="pill" style="background:{ACTION_COLOR[m.action]}">{m.action}</span></td></tr>'
        for m in ranked
    )
    kpis = [
        ("Spend", eur(tot["cost_eur"])),
        ("Reach", num(tot["reach"])),
        ("Engagement rate", f"{tot['engagement_rate']}%"),
        ("Conversions", num(tot["conversions"])),
        ("Cost per conversion", eur(tot["cpa"], 2)),
        ("ROAS", f"{tot['roas']}x" if tot["roas"] else "n/a"),
    ]
    kpi_html = "".join(f"<div><span>{k}</span><strong>{v}</strong></div>" for k, v in kpis)
    summary_html = f"<h2>Summary</h2><p>{html.escape(summary)}</p>" if summary else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(name)} weekly report</title>
<style>
body{{font:15px/1.55 -apple-system,Segoe UI,Roboto,sans-serif;color:#1d2939;max-width:860px;margin:32px auto;padding:0 16px}}
h1{{font-size:24px;margin:0}} h2{{font-size:17px;margin:28px 0 10px}} .sub{{color:#667085;margin:4px 0 20px}}
.kpis{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}} .kpis div{{border:1px solid #e4e7ec;border-radius:8px;padding:12px}}
.kpis span{{display:block;font-size:12px;color:#667085}} .kpis strong{{font-size:20px}}
table{{width:100%;border-collapse:collapse;font-size:14px}} th,td{{text-align:left;padding:8px 6px;border-bottom:1px solid #e4e7ec}}
th{{font-size:12px;color:#667085;text-transform:uppercase;letter-spacing:.04em}} .pill{{color:#fff;border-radius:99px;padding:2px 9px;font-size:12px}}
.wrap{{overflow-x:auto}} @media(max-width:600px){{.kpis{{grid-template-columns:1fr 1fr}}}}
</style></head><body>
<h1>{html.escape(name)}</h1><p class="sub">Weekly creator report · week of {week:%d %B %Y}</p>
<div class="kpis">{kpi_html}</div>{summary_html}
<h2>Cost per conversion</h2>{_bar_chart(ms)}
<h2>By creator</h2><div class="wrap"><table><thead><tr><th>Creator</th><th>Platform</th><th>Spend</th><th>Reach</th><th>ER</th><th>Per 1,000</th><th>Per conv.</th><th>Action</th></tr></thead><tbody>{rows}</tbody></table></div>
</body></html>"""
