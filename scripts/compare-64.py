#!/usr/bin/env python3
"""Compare the 64-day staging run with the projection made before it.

Staging switched the classic profile to 64 days at 21:35 UTC on 2026-10-14, after
results/projection-64.txt had been committed and pushed (21:32 UTC). This reads
the 64-day run and the acme.sh upgrade check and prints each client's measured
day next to the projected one.

    python3 scripts/compare-64.py   -> results/measured-64.txt
"""
import importlib.util
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("project64", ROOT / "scripts/project-64.py")
p64 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p64)

R64 = (ROOT / "results/classic-64-2026-10-14.txt").read_text()
UPG = (ROOT / "results/acme-sh-upgrade-64-day.txt").read_text()


def main():
    lines = []
    p = lines.append
    _, _, rows = p64.ari(R64)
    life = rows[0]["lifetime_days"]
    s = min(r["ari_start_day"] for r in rows)
    e = max(r["ari_end_day"] for r in rows)
    p(f"Certificate lifetime: {life:.1f} days (all {len(rows)} certificates)")
    p(f"ARI window: measured day {s:.2f} to {e:.2f} (share {s / life:.3f} to {e / life:.3f}); projected day 42.0 to 43.3")
    p("")

    not_due, renewed = p64.certbot(R64, "2.9.0")
    p(f"certbot 2.9.0: measured not due at day {not_due:.2f}, renewed at day {renewed:.2f}; projected day 34")

    c58 = next(r for r in rows if r["cert"].startswith("c58n"))
    w0, w1 = datetime.fromisoformat(c58["ari_start"]), datetime.fromisoformat(c58["ari_end"])
    nb = datetime.fromisoformat(c58["notBefore"])
    block = R64.split("# certbot 5.8.0")[1].split("==")[0]
    p("certbot 5.8.0: each run draws a random time inside the window, so a run renews with")
    p("  probability (now - start) / (end - start); measured probes:")
    for hour, day, verdict in re.findall(r"hour (\d+) \(day ([\d.]+).*?: (not due|RENEWED)", block):
        t = nb.timestamp() + int(hour) * 3600
        frac = (t - w0.timestamp()) / (w1.timestamp() - w0.timestamp())
        chance = "before the window" if frac < 0 else f"{min(frac, 1):.0%} chance"
        p(f"    day {day}: {verdict} ({chance})")
    p("  projected: inside the ARI window, day 42.0 to 43.3")
    p("")

    for name, v in sorted(p64.acme(R64, "a307").items()):
        margin = v["life"] - v["next_day"]
        when = f"{margin:.2f} days before expiry" if margin > 0 else f"{-margin:.2f} days AFTER expiry"
        proj = "59.0" if v["days"] == "default" else "79.0"
        p(f"acme.sh 3.0.7 --days {v['days']}: measured day {v['next_day']:.2f}, {when}; projected day {proj}")
    for name, v in sorted(p64.acme(R64, "a316").items()):
        p(f"acme.sh 3.1.6 --days {v['days']}: measured day {v['next_day']:.2f} (window {s:.2f} to {e:.2f}); projected inside the window")
    nxt = re.findall(r"Le_NextRenewTimeStr='(\S+)'", UPG)
    nb80 = datetime.fromisoformat(next(r["notBefore"] for r in rows if r["cert"].startswith("a307n80")))
    before, after = (datetime.fromisoformat(x.replace("Z", "+00:00")) for x in nxt)
    p(f"  upgrade to 3.1.6 on the --days 80 lineage: day {(before - nb80).total_seconds() / 86400:.2f} -> "
      f"day {(after - nb80).total_seconds() / 86400:.2f}, Le_RenewalDays kept")
    p("")

    days = p64.lego(R64)
    p(f"lego 5.5.2 (ARI on, then --ari-disable): measured renewal allowed from day {', '.join(f'{d:.2f}' for d in days)}; projected day 42.7")

    text = "\n".join(lines) + "\n"
    (ROOT / "results/measured-64.txt").write_text(text)
    print(text, end="")


if __name__ == "__main__":
    main()
