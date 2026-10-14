# le-64-day-renewal-check

```bash
python3 scripts/project-64.py   # reads results/, writes results/projection-64.txt
```

When does each ACME client renew a Let's Encrypt certificate, and what happens when the default lifetime drops from 90 to 64 days on 10 February 2027?

We issued real Let's Encrypt **staging** certificates with certbot 2.9.0 (Ubuntu 24.04 apt), certbot 5.8.0 (snap), acme.sh 3.0.7 and 3.1.6, and lego 5.5.2, at two lifetimes: 45 days (the `tlsserver` profile) and 90 days (the `classic` profile). Then we recorded when each client plans to renew, moved certbot's clock forward with `faketime` to find the day it actually renews, and asked the ARI endpoint for its suggested window.

Let's Encrypt announced that staging would switch the classic profile to 64 days on 14 October 2026. A watcher asked for a fresh classic certificate every 10 minutes from 12:36 to 22:4x UTC that day and got a 90-day certificate every time (`results/watch-2026-10-14.log`; the script rounds the lifetime down, so it prints 89d). So the 64-day numbers here are a **projection** from the two measured lifetimes, not a run.

## Result

| Client | 45-day (measured) | 90-day (measured) | 64-day (projected) |
|---|---|---|---|
| ARI suggested window | day 29.6 to 30.5 | day 59.1 to 60.9 | day 42.0 to 43.3 |
| certbot 2.9.0, no ARI | day 15.0 | day 60.0 | day 34 |
| certbot 5.8.0, ARI | day 30.3 | day 59.9 | day 42 to 43 |
| acme.sh 3.1.6, ARI | day 29.7 to 30.3 | day 60.8 to 60.9 | day 42 to 43 |
| lego 5.5.2, ARI or 2/3 | day 30.0 | day 60.0 | day 42.7 |
| acme.sh 3.0.7, default `--days 60` | day 59 (from source: after expiry) | day 59.0 | day 59, 5 days before expiry |
| acme.sh 3.0.7, `--days 80` | day 79 (from source: after expiry) | day 79.0 | day 79, 15 days after expiry |

The ARI window was the same share of the lifetime at 45 and 90 days (65.7% to 67.7%), so the projection assumes Let's Encrypt keeps it. acme.sh 3.0.7 cannot request a profile, so its 45-day row comes from its source (`results/acme-sh-renewal-logic.txt`): next renewal = issue time + `--days` - 1 day, with no cap at expiry. acme.sh added ARI scheduling and a cap one day before expiry in 3.1.4 (July 2026), and changed the default from 60 to 30 days in 3.1.3.

## Scripts

| script | what it does |
|---|---|
| `scripts/setup.sh` | Installs the clients on a throwaway Ubuntu 24.04 droplet with port 80 open. |
| `scripts/tlsserver-suite.sh` | Issues 45-day certificates with every client that can request a profile and records the renewal plans. |
| `scripts/classic-90-suite.sh` | The same on the classic profile while it still issues 90-day certificates. |
| `scripts/classic-suite.sh` | The same for 64-day classic certificates; never ran, because staging did not switch. |
| `scripts/watch-64.sh` | Asks for a classic certificate every 10 minutes and runs the 64-day suite once the lifetime drops. |
| `scripts/probe-certbot.sh` | Runs `certbot renew` under `faketime` at chosen hours after issuance, on a copy of the state each time. |
| `scripts/ari.py` | Prints the ARI (RFC 9773) suggested window for each certificate. |
| `scripts/project-64.py` | Reads the two result files and projects each client onto a 64-day lifetime. |

The hostnames are `*.46-101-102-127.sslip.io`, which pointed at the throwaway droplet; it has been destroyed.

## Write-up

https://devops-daily.com/posts/lets-encrypt-64-day-certificates-renewal-check

## License

MIT
