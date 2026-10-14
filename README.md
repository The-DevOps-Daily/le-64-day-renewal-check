# le-64-day-renewal-check

```bash
python3 scripts/compare-64.py   # reads results/, writes results/measured-64.txt
```

When does each ACME client renew a Let's Encrypt certificate, now that the default lifetime drops from 90 to 64 days on 10 February 2027?

We issued real Let's Encrypt **staging** certificates with certbot 2.9.0 (Ubuntu 24.04 apt), certbot 5.8.0 (snap), acme.sh 3.0.7 and 3.1.6, and lego 5.5.2, at three lifetimes: 64 days (the `classic` profile after staging switched), 90 days (`classic` before the switch) and 45 days (the `tlsserver` profile). Then we recorded when each client plans to renew, moved certbot's clock forward with `faketime` to find the day it actually renews, and asked the ARI endpoint for its suggested window.

A watcher asked for a fresh classic certificate every 10 minutes from 12:36 UTC on 14 October 2026 (`results/watch-2026-10-14.log`). The request at 21:25 UTC returned a 90-day certificate and the one at 21:35 UTC a 64-day certificate, so the watcher ran the 64-day suite (`results/classic-64-2026-10-14.txt`). One request, at 16:30 UTC, failed to issue. The script rounds the lifetime down, so it prints 89d and 63d.

## Result

| Client | 64-day | 45-day | 90-day |
|---|---|---|---|
| ARI suggested window | day 42.04 to 43.32 | day 29.56 to 30.46 | day 59.11 to 60.91 |
| certbot 5.8.0, ARI | first renewal seen at day 42.50 | first renewal seen at day 30.29 | first renewal seen at day 59.92 |
| acme.sh 3.1.6, ARI | scheduled day 42.16 | scheduled day 29.6 to 30.3 | scheduled day 60.7 to 60.9 |
| lego 5.5.2 (checked at issuance) | allowed from day 42.67 | allowed from day 30.0 | allowed from day 60.0 |
| certbot 2.9.0, no ARI | due between day 33.96 and 34.08 | due between day 14.96 and 15.08 | due between day 59.79 and 60.21 |
| acme.sh 3.0.7, default `--days 60` | day 59.04, 5 days before expiry | day 59 (from source: after expiry) | day 59.0 |
| acme.sh 3.0.7, `--days 80` | day 79.04, 15 days after expiry | day 79 (from source: after expiry) | day 79.0 |

The ARI window was the same share of the lifetime at all three lengths (65.7% to 67.7%). certbot 5.8 picks a random time inside the window on every run (`results/certbot-5.8-ari-source.txt`), so a probe inside the window can go either way. acme.sh 3.0.7 cannot request a profile, so its 45-day row comes from its source (`results/acme-sh-renewal-logic.txt`): next renewal = issue time + `--days` - 1 day, with no cap at expiry. `results/acme-sh-tags.txt` scans every tag from 3.0.7 to 3.1.6: the default is 60 up to 3.1.2 and 30 from 3.1.3, the cap one day before expiry arrives in 3.1.4, and the per-run ARI check in 3.1.5. Only 3.0.7 and 3.1.6 were run.

`results/acme-sh-upgrade-64-day.txt` and `results/acme-sh-upgrade-90-day.txt`: acme.sh 3.1.6 run (`--renew`, no `--force`) on a certificate that 3.0.7 had scheduled for day 79 with `--days 80`. It kept `Le_RenewalDays='80'` but moved the next renewal into the ARI window on its first check (day 42.23 of 64).

`results/projection-64.txt` is the 64-day projection from the 45-day and 90-day runs. It was pushed in commit f909cfc at 21:32 UTC, before the first 64-day certificate; the later commit changes only how the lego line is computed, not its result. `scripts/compare-64.py` prints each measured 64-day value next to it.

## Scripts

| script | what it does |
|---|---|
| `scripts/setup.sh` | Installs the clients on a throwaway Ubuntu 24.04 droplet with port 80 open. |
| `scripts/tlsserver-suite.sh` | Issues 45-day certificates with every client that can request a profile and records the renewal plans. |
| `scripts/classic-90-suite.sh` | The same on the classic profile while it still issues 90-day certificates. |
| `scripts/classic-suite.sh` | The same for 64-day classic certificates; the watcher ran it at 21:35 UTC. |
| `scripts/watch-64.sh` | Asks for a classic certificate every 10 minutes and runs the 64-day suite once the lifetime drops. |
| `scripts/probe-certbot.sh` | Runs `certbot renew` under `faketime` at chosen hours after issuance, on a copy of the state each time. |
| `scripts/ari.py` | Prints the ARI (RFC 9773) suggested window for each certificate. |
| `scripts/upgrade-check.sh` | Runs acme.sh 3.1.6 on a copy of a 3.0.7 lineage to see what an upgrade does to its stored schedule. |
| `scripts/project-64.py` | Reads the 45-day and 90-day results and projects each client onto a 64-day lifetime. |
| `scripts/compare-64.py` | Prints the measured 64-day results next to the projection. |

The hostnames are `*.46-101-102-127.sslip.io`, which pointed at the throwaway droplet; it has been destroyed.

## Write-up

https://devops-daily.com/posts/lets-encrypt-64-day-certificates-renewal-check

## License

MIT
