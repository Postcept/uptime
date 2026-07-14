"""Render the status page from the probe history.

Runs inside the probe workflow after each probe, so the page is regenerated on
GitHub's infrastructure and served by GitHub Pages, both outside the accounts
that serve production. A production outage cannot take the page that reports it
down with it.
"""

import html
import json
import statistics
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WINDOW_DAYS = 30
ENDPOINT_LABELS = {
    "readyz": "API",
    "v1/signing-key": "Signing keys",
    "v1/transparency/sth": "Transparency log",
}


def load_probes() -> list[dict]:
    probes = []
    for path in sorted(ROOT.glob("history/*.jsonl")):
        for line in path.read_text().splitlines():
            if line.strip():
                probes.append(json.loads(line))
    cutoff = datetime.now(UTC) - timedelta(days=WINDOW_DAYS)
    return [p for p in probes if datetime.fromisoformat(p["ts"].replace("Z", "+00:00")) >= cutoff]


def render(probes: list[dict]) -> str:
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    by_endpoint: dict[str, list[dict]] = {}
    for p in probes:
        by_endpoint.setdefault(p["endpoint"], []).append(p)

    total = len(probes)
    ok = sum(1 for p in probes if 200 <= p["status"] < 400)
    overall = (ok / total * 100) if total else 0.0
    all_up = total > 0 and ok == total

    rows = []
    for endpoint, items in by_endpoint.items():
        good = [p for p in items if 200 <= p["status"] < 400]
        pct = len(good) / len(items) * 100 if items else 0.0
        latency = int(statistics.median(p["ms"] for p in good)) if good else 0
        label = ENDPOINT_LABELS.get(endpoint, endpoint)
        recent = items[-64:]
        ticks = "".join(
            f'<span class="tick {"up" if 200 <= p["status"] < 400 else "down"}" '
            f'title="{html.escape(p["ts"])} · HTTP {p["status"]} · {p["ms"]}ms"></span>'
            for p in recent
        )
        rows.append(
            f"""<div class="row">
  <div class="row-head">
    <span class="name">{html.escape(label)}</span>
    <span class="mono meta">{pct:.2f}% · median {latency}ms</span>
  </div>
  <div class="ticks">{ticks}</div>
</div>"""
        )

    banner_class = "ok" if all_up else "warn"
    banner_text = "All systems operational" if all_up else "Degraded performance"

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Postcept status</title>
<meta name="description" content="Independent uptime for the Postcept API, probed from outside the infrastructure that serves it.">
<style>
  :root {{ color-scheme: dark; }}
  * {{ box-sizing: border-box; margin: 0; }}
  body {{
    background: #0B0F14; color: #E6EDF3;
    font: 16px/1.6 -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
    padding: 48px 20px;
  }}
  .wrap {{ max-width: 720px; margin: 0 auto; }}
  .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
  h1 {{ font-size: 1.35rem; letter-spacing: -0.02em; }}
  .sub {{ color: #8B98A5; font-size: 0.9rem; margin-top: 4px; }}
  .banner {{
    margin-top: 28px; padding: 16px 20px; border-radius: 10px;
    border: 1px solid; font-weight: 600;
  }}
  .banner.ok {{ border-color: rgba(34,197,94,.35); background: rgba(34,197,94,.08); color: #22C55E; }}
  .banner.warn {{ border-color: rgba(245,158,11,.35); background: rgba(245,158,11,.08); color: #F59E0B; }}
  .overall {{ color: #8B98A5; font-size: 0.85rem; font-weight: 400; float: right; }}
  .row {{ margin-top: 26px; }}
  .row-head {{ display: flex; justify-content: space-between; align-items: baseline; }}
  .name {{ font-weight: 600; }}
  .meta {{ color: #8B98A5; font-size: 0.8rem; }}
  .ticks {{ display: flex; gap: 2px; margin-top: 8px; }}
  .tick {{ flex: 1; height: 26px; border-radius: 2px; min-width: 3px; }}
  .tick.up {{ background: #1E9E58; }}
  .tick.down {{ background: #E5484D; }}
  .foot {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid rgba(139,152,165,.15);
          color: #8B98A5; font-size: 0.85rem; }}
  a {{ color: #E6EDF3; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>Postcept status</h1>
  <p class="sub">Probed every 15 minutes from GitHub's infrastructure, outside the accounts
  that serve production. Every probe is committed to an append-only public history.</p>

  <div class="banner {banner_class}">{banner_text}
    <span class="overall mono">{overall:.2f}% over {WINDOW_DAYS} days · {total} checks</span>
  </div>

  {"".join(rows)}

  <p class="foot">
    Last check {now} ·
    <a href="https://github.com/Postcept/uptime/tree/main/history">raw history (JSONL)</a> ·
    <a href="https://github.com/Postcept/uptime">how this works</a> ·
    <a href="https://postcept.com">postcept.com</a>
  </p>
</div>
</body>
</html>
"""


def main() -> None:
    probes = load_probes()
    out = ROOT / "docs"
    out.mkdir(exist_ok=True)
    (out / "index.html").write_text(render(probes))
    print(f"rendered docs/index.html from {len(probes)} probes")


if __name__ == "__main__":
    main()
