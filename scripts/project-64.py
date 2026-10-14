#!/usr/bin/env python3
"""Read the 45-day and 90-day results and project each client onto a 64-day certificate.

Two lifetimes were measured on Let's Encrypt staging on 2026-10-14: the 45-day
"tlsserver" profile and the 90-day "classic" profile. Staging had not yet switched
the classic profile to 64 days when this was written, so the 64-day column is a
projection: each client's rule, read from the two measurements (and the acme.sh
source), applied to a 64-day lifetime. scripts/compare-64.py checks it against
the 64-day run. It assumes Let's Encrypt keeps the same ARI window, which
was the same share of the lifetime at 45 and 90 days.

    python3 scripts/project-64.py   -> results/projection-64.txt
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
R45 = (ROOT / "results/tlsserver-45-2026-10-14.txt").read_text()
R90 = (ROOT / "results/classic-90-2026-10-14.txt").read_text()
LIFE = 64.0


def ari(text):
    rows = [json.loads(l) for l in text.splitlines() if l.startswith('{"cert"')]
    return min(r["ari_start_share"] for r in rows), max(r["ari_end_day"] / r["lifetime_days"] for r in rows), rows


def certbot(text, version):
    block = text.split(f"# certbot {version}")[1].split("==")[0]
    hours = re.findall(r"hour (\d+) \(day ([\d.]+).*?: (not due|RENEWED)", block)
    first = next(float(d) for _, d, v in hours if v == "RENEWED")
    last_not = max(float(d) for _, d, v in hours if v == "not due" and float(d) < first)
    return last_not, first


def openssl_time(s):
    return datetime.strptime(s, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)


def acme(text, prefix):
    out = {}
    for m in re.finditer(r"(?:acme\d+ )?(\S+) notBefore=(.+?) GMT notAfter=(.+?) GMT next='(\S+)' days='?(\d*)'?", text):
        name, nb, na, nxt, days = m.groups()
        if not name.startswith(prefix):
            continue
        nb, na = openssl_time(nb + " GMT"), openssl_time(na + " GMT")
        nxt = datetime.fromisoformat(nxt.replace("Z", "+00:00"))
        out[name] = {"next_day": (nxt - nb).total_seconds() / 86400, "life": (na - nb).total_seconds() / 86400, "days": days or "default"}
    return out


def lego(text):
    """Day after notBefore from which lego allows renewal, with ARI and with ARI disabled.

    Each "Skip renewal" line is logged at a timestamp and says how long until a
    renewal is allowed; adding the two and subtracting notBefore gives the day.
    """
    _, _, rows = ari(text)
    nb = next(datetime.fromisoformat(r["notBefore"]) for r in rows if "lego" in r["cert"])
    days = []
    for m in re.finditer(r"^(\S+Z) INFO\s+Skip renewal: .*?can be performed in (\d+)d(\d+)h(\d+)m([\d.]+)s", text, re.M):
        ts = datetime.fromisoformat(m.group(1)[:26].rstrip("Z") + "+00:00")
        wait = int(m.group(2)) * 86400 + int(m.group(3)) * 3600 + int(m.group(4)) * 60 + float(m.group(5)[:12].rstrip("."))
        days.append((ts.timestamp() + wait - nb.timestamp()) / 86400)
    return days


def main():
    lines = []
    p = lines.append
    s45, e45, _ = ari(R45)
    s90, e90, _ = ari(R90)
    p(f"ARI window as a share of the lifetime: 45-day {s45:.3f} to {e45:.3f}, 90-day {s90:.3f} to {e90:.3f}")
    s, e = min(s45, s90), max(e45, e90)
    p(f"  projected 64-day window: day {s * LIFE:.1f} to {e * LIFE:.1f}")
    p("")

    c29_45, c29_90 = certbot(R45, "2.9.0"), certbot(R90, "2.9.0")
    p(f"certbot 2.9.0 (Ubuntu 24.04 apt, no ARI): renewed between day {c29_45[0]:.2f} and {c29_45[1]:.2f} of 45, "
      f"between day {c29_90[0]:.2f} and {c29_90[1]:.2f} of 90 -> 30 days before expiry")
    p(f"  projected 64-day: day {LIFE - 30:.0f}, {30} days before expiry")
    c58_45, c58_90 = certbot(R45, "5.8.0"), certbot(R90, "5.8.0")
    p(f"certbot 5.8.0 (snap, ARI): first renewal seen at day {c58_45[1]:.2f} of 45 and {c58_90[1]:.2f} of 90, inside the ARI window")
    p(f"  projected 64-day: inside the ARI window, day {s * LIFE:.1f} to {e * LIFE:.1f}")
    p("")

    a307 = acme(R90, "a307")
    for name, v in sorted(a307.items()):
        p(f"acme.sh 3.0.7 --days {v['days']}: plans renewal on day {v['next_day']:.2f} of a {v['life']:.0f}-day certificate")
        nd = v["next_day"]
        margin = LIFE - nd
        p(f"  projected 64-day: day {nd:.1f}, " + (f"{margin:.1f} days before expiry" if margin > 0 else f"{-margin:.1f} days AFTER expiry"))
    a316 = {**acme(R45, "t316"), **acme(R90, "a316")}
    for name, v in sorted(a316.items()):
        p(f"acme.sh 3.1.6 --days {v['days']} ({v['life']:.0f}-day): plans renewal on day {v['next_day']:.2f} (ARI window)")
    p(f"  projected 64-day: inside the ARI window, day {s * LIFE:.1f} to {e * LIFE:.1f}")
    p("")

    l45, l90 = lego(R45), lego(R90)
    p(f"lego 5.5.2, checked at issuance (ARI on, then --ari-disable): renewal allowed from day "
      f"{', '.join(f'{d:.2f}' for d in l45)} of 45 and {', '.join(f'{d:.2f}' for d in l90)} of 90")
    share = sum(l45) / len(l45) / 45 + sum(l90) / len(l90) / 90
    p(f"  share of the lifetime: {share / 2:.3f}; projected 64-day: day {share / 2 * LIFE:.1f}")

    text = "\n".join(lines) + "\n"
    (ROOT / "results/projection-64.txt").write_text(text)
    print(text, end="")


if __name__ == "__main__":
    main()
