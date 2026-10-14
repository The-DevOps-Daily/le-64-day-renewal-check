#!/bin/bash
# Does upgrading acme.sh fix a lineage that 3.0.7 scheduled with --days 80?
# Copies the 3.0.7 state from a suite run and runs 3.1.6 --renew on it,
# without --force, so nothing is issued unless a renewal is due.
#   upgrade-check.sh classic-90 > results/acme-sh-upgrade-90-day.txt
#   upgrade-check.sh classic-64 > results/acme-sh-upgrade-64-day.txt
set -u
SUITE=${1:?usage: upgrade-check.sh classic-90|classic-64}
R=/srv/le/migrate-$SUITE; rm -rf $R; cp -a /srv/le/$SUITE/acme307 $R
n=a307n80.46-101-102-127.sslip.io; d=$R/${n}_ecc
echo "== before: acme.sh 3.0.7 state"
grep -E "^Le_RenewalDays=|^Le_NextRenewTimeStr=" $d/$n.conf
openssl x509 -in $d/$n.cer -noout -enddate
echo "== acme.sh 3.1.6 --renew on the same state (no --force), $(date -u +%FT%TZ)"
bash /opt/acme316/acme.sh --home $R --config-home $R --renew -d $n --ecc --server letsencrypt_test 2>&1 \
  | grep -E "ARI|renewal time|Skipping|Next renewal|WARNING|Renew" | sed "s/\x1b\[[0-9;]*m//g"
echo "== after"
grep -E "^Le_RenewalDays=|^Le_NextRenewTimeStr=" $d/$n.conf
