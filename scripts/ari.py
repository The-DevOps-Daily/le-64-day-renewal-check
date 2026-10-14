#!/usr/bin/env python3
"""Print the ARI suggested renewal window (RFC 9773) for each certificate given."""
import base64, json, subprocess, sys, urllib.request
from datetime import datetime, timezone

DIRECTORY = "https://acme-staging-v02.api.letsencrypt.org/directory"
renewal_info = json.load(urllib.request.urlopen(DIRECTORY))["renewalInfo"]

def b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")

def ts(s: str) -> datetime:
    return datetime.strptime(s, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)

for path in sys.argv[1:]:
    text = subprocess.run(["openssl", "x509", "-in", path, "-noout", "-text", "-serial", "-startdate", "-enddate"],
                          capture_output=True, text=True, check=True).stdout
    lines = text.splitlines()
    aki = next(lines[i + 1] for i, l in enumerate(lines) if "Authority Key Identifier" in l).strip()
    aki = aki.removeprefix("keyid:")
    serial = next(l.split("=", 1)[1] for l in lines if l.startswith("serial="))
    start = ts(next(l.split("=", 1)[1] for l in lines if l.startswith("notBefore=")))
    end = ts(next(l.split("=", 1)[1] for l in lines if l.startswith("notAfter=")))
    serial_bytes = bytes.fromhex(serial if len(serial) % 2 == 0 else "0" + serial)
    if serial_bytes[0] & 0x80:
        serial_bytes = b"\x00" + serial_bytes  # DER INTEGER stays positive
    cert_id = b64(bytes.fromhex(aki.replace(":", ""))) + "." + b64(serial_bytes)
    window = json.load(urllib.request.urlopen(f"{renewal_info}/{cert_id}"))["suggestedWindow"]
    w0 = datetime.fromisoformat(window["start"].replace("Z", "+00:00"))
    w1 = datetime.fromisoformat(window["end"].replace("Z", "+00:00"))
    life = (end - start).total_seconds() / 86400
    print(json.dumps({
        "cert": path.split("/")[-1] if "/live/" not in path else path.split("/live/")[1].split("/")[0],
        "notBefore": start.isoformat(), "notAfter": end.isoformat(), "lifetime_days": round(life, 2),
        "ari_start": w0.isoformat(), "ari_end": w1.isoformat(),
        "ari_start_day": round((w0 - start).total_seconds() / 86400, 2),
        "ari_end_day": round((w1 - start).total_seconds() / 86400, 2),
        "ari_start_share": round((w0 - start).total_seconds() / (end - start).total_seconds(), 3),
    }))
