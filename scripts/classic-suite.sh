#!/bin/bash
# Run once staging issues 64-day "classic" certificates: issue with every client,
# then record when each one plans to renew. Output: /srv/le/classic-64/results.txt
set -u
IPD=46-101-102-127
R=/srv/le/classic-64; mkdir -p $R; OUT=$R/results.txt
STG=https://acme-staging-v02.api.letsencrypt.org/directory
exec > >(tee -a $OUT) 2>&1
echo "== classic suite started $(date -u +%FT%TZ)"
certbot certonly --standalone --staging --non-interactive --agree-tos --register-unsafely-without-email -d c29n.$IPD.sslip.io --config-dir $R/cb29/etc --work-dir $R/cb29/work --logs-dir $R/cb29/logs | grep -E "expires"
/snap/bin/certbot certonly --standalone --staging --non-interactive --agree-tos --register-unsafely-without-email -d c58n.$IPD.sslip.io --config-dir $R/cb58/etc --work-dir $R/cb58/work --logs-dir $R/cb58/logs | grep -E "expires"
iss() { home=$1; bin=$2; shift 2; bash $bin --home $R/$home --config-home $R/$home --server letsencrypt_test --issue --standalone "$@" >/dev/null 2>&1; }
iss acme307 /opt/acme307/acme.sh -d a307n.$IPD.sslip.io
iss acme307 /opt/acme307/acme.sh -d a307n80.$IPD.sslip.io --days 80
iss acme316 /opt/acme316/acme.sh -d a316n.$IPD.sslip.io
iss acme316 /opt/acme316/acme.sh -d a316n80.$IPD.sslip.io --days 80
lego run --server letsencrypt-staging --accept-tos --http -d legon.$IPD.sslip.io --path $R/lego >/dev/null 2>&1
echo "== acme.sh planned renewals"
for h in acme307 acme316; do for d in $R/$h/*_ecc; do n=$(basename $d _ecc); c=$d/$n.cer
  echo "$h ${n%%.*} notBefore=$(openssl x509 -in $c -noout -startdate | cut -d= -f2) notAfter=$(openssl x509 -in $c -noout -enddate | cut -d= -f2) next=$(grep ^Le_NextRenewTimeStr= $d/$n.conf | cut -d= -f2-) days=$(grep ^Le_RenewalDays= $d/$n.conf | cut -d= -f2-)"; done; done
echo "== lego decision"
lego run --server letsencrypt-staging --accept-tos --http -d legon.$IPD.sslip.io --path $R/lego --log.level debug 2>&1 | grep -E "RenewalInfo|Skip renewal"
lego run --server letsencrypt-staging --accept-tos --http -d legon.$IPD.sslip.io --path $R/lego --ari-disable 2>&1 | grep -E "Skip renewal"
echo "== ARI windows"
python3 /srv/le/ari.py $R/cb29/etc/live/*/cert.pem $R/cb58/etc/live/*/cert.pem $R/lego/certificates/legon*.sslip.io.crt $(ls $R/acme3*/*_ecc/*.cer | grep -v -E "/ca.cer|fullchain")
echo "== certbot 2.9 probe (hours after notBefore)"
/srv/le/probe-certbot.sh certbot $R/cb29 c29n.$IPD.sslip.io 800 812 815 818 830
echo "== certbot 5.8 probe"
/srv/le/probe-certbot.sh /snap/bin/certbot $R/cb58 c58n.$IPD.sslip.io 990 1000 1006 1010 1014 1020 1030
echo "== classic suite done $(date -u +%FT%TZ)"
