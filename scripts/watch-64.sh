#!/bin/bash
# Every 10 minutes, ask staging for a classic certificate; when its lifetime is
# under 70 days, run the classic suite once. Gives up after 10 hours.
IPD=46-101-102-127
for i in $(seq 1 60); do
  rm -rf /srv/le/watch
  lego run --server letsencrypt-staging --accept-tos --http -d watch.$IPD.sslip.io --path /srv/le/watch >/dev/null 2>&1
  c=/srv/le/watch/certificates/watch.$IPD.sslip.io.crt
  if [ -f $c ]; then
    days=$(( ($(date -d "$(openssl x509 -in $c -noout -enddate | cut -d= -f2)" +%s) - $(date -d "$(openssl x509 -in $c -noout -startdate | cut -d= -f2)" +%s)) / 86400 ))
    echo "$(date -u +%FT%TZ) classic lifetime ${days}d" >> /srv/le/watch.log
    if [ $days -lt 70 ]; then /srv/le/classic-suite.sh; exit 0; fi
  else
    echo "$(date -u +%FT%TZ) issuance failed" >> /srv/le/watch.log
  fi
  sleep 600
done
