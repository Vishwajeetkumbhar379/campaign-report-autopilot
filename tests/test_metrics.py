from types import SimpleNamespace

from autopilot.metrics import Row, compute, totals
from autopilot.report import html_report, markdown
from autopilot.summary import write_summary
from datetime import date


def row(creator, cost, reach, eng, clicks, conv, rev=0.0):
    return Row(creator, "instagram", cost, reach, reach, eng, 0, 0, 0, clicks, conv, rev)


ROWS = [
    row("@cheap", 500, 10000, 600, 200, 25, 1500),
    row("@mid", 1000, 20000, 700, 300, 20, 1200),
    row("@pricey", 3000, 15000, 300, 100, 5, 300),
    row("@nosale", 2000, 8000, 900, 50, 0),
]


def test_core_metrics():
    m = compute([row("@a", 1000, 20000, 800, 400, 10, 2500)])[0]
    assert m.engagement_rate == 4.0
    assert m.cpm_reach == 50.0
    assert m.cpa == 100.0
    assert m.roas == 2.5
    assert m.ctr == 2.0


def test_actions_relative_to_median():
    ms = {m.creator: m for m in compute(ROWS)}
    assert ms["@cheap"].action == "scale"
    assert ms["@pricey"].action == "cut"
    assert ms["@nosale"].action in ("cut", "test")


def test_zero_division_is_safe():
    m = compute([row("@empty", 0, 0, 0, 0, 0)])[0]
    assert m.cpa is None and m.cpm_reach == 0


def test_reports_render():
    ms = compute(ROWS)
    tot = totals(ms)
    md = markdown("Test", ms, tot, "All good.", date(2026, 10, 5))
    assert "Headline numbers" in md and "@cheap" in md
    assert "<svg" in html_report("Test", ms, tot, None, date(2026, 10, 5))


def test_ai_summary_with_fake_client():
    fake = SimpleNamespace(messages=SimpleNamespace(create=lambda **kw: SimpleNamespace(
        content=[SimpleNamespace(type="text", text="  Strong week.  ")])))
    ms = compute(ROWS)
    assert write_summary("T", ms, totals(ms), client=fake) == "Strong week."
