#!/bin/bash
# Probe on which day after issuance a certbot install decides to renew.
# Usage: probe-certbot.sh <certbot-bin> <state-dir> <cert-name> <hours> [<hours> ...]  (hours after notBefore)
# The state is copied before each probe, so one renewal does not affect the next.
bin=$1; state=$2; name=$3; shift 3
nb=$(openssl x509 -in "$state/etc/live/$name/cert.pem" -noout -startdate | cut -d= -f2)
na=$(openssl x509 -in "$state/etc/live/$name/cert.pem" -noout -enddate | cut -d= -f2)
echo "# $($bin --version 2>&1) $name notBefore=$nb notAfter=$na"
for d in "$@"; do
  tmp=$(mktemp -d)
  cp -a "$state/." "$tmp/"
  # The renewal config stores absolute paths; point them at the copy so the
  # original lineage is never touched.
  sed -i "s#$state#$tmp#g" "$tmp"/etc/renewal/*.conf
  at=$(date -u -d "$nb + $d hours" '+%Y-%m-%d %H:%M:%S')
  out=$(faketime -f "@$at" "$bin" renew --cert-name "$name" --config-dir "$tmp/etc" --work-dir "$tmp/work" \
        --logs-dir "$tmp/logs" --no-verify-ssl --non-interactive --no-random-sleep-on-renew 2>&1)
  if echo "$out" | grep -q "not yet due for renewal"; then verdict="not due"
  elif echo "$out" | grep -q -i "renewals succeeded\|Congratulations"; then verdict="RENEWED"
  else verdict="other: $(echo "$out" | grep -v '^\s*$' | tail -1)"; fi
  echo "hour $d (day $(awk "BEGIN{printf \"%.2f\", $d/24}"), $at UTC): $verdict"
  rm -rf "$tmp"
done
