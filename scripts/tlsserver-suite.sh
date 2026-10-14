#!/bin/bash
# The 45-day case, available today through the "tlsserver" profile: issue with
# every client that can request a profile, then record when each plans to renew.
# certbot 2.9 and acme.sh 3.0.7 cannot request a profile; certbot 2.9 is probed
# on a copy of the certbot 5.8 lineage. Output: /srv/le/tlsserver-45/results.txt
set -u
IPD=46-101-102-127
R=/srv/le/tlsserver-45; mkdir -p $R; OUT=$R/results.txt
exec > >(tee -a $OUT) 2>&1
echo "== tlsserver suite started $(date -u +%FT%TZ)"
echo "versions: $(certbot --version 2>&1), $(/snap/bin/certbot --version 2>&1), acme.sh $(bash /opt/acme316/acme.sh --version | tail -1), $(lego --version)"
/snap/bin/certbot certonly --standalone --staging --non-interactive --agree-tos --register-unsafely-without-email --preferred-profile tlsserver -d t58.$IPD.sslip.io --config-dir $R/cb58/etc --work-dir $R/cb58/work --logs-dir $R/cb58/logs | grep -E "expires"
iss() { bash /opt/acme316/acme.sh --home $R/acme316 --config-home $R/acme316 --server letsencrypt_test --issue --standalone --cert-profile tlsserver "$@" >/dev/null 2>&1; }
iss -d t316.$IPD.sslip.io
iss -d t316d60.$IPD.sslip.io --days 60
lego run --server letsencrypt-staging --accept-tos --http -d tlego.$IPD.sslip.io --path $R/lego --profile tlsserver >/dev/null 2>&1
echo "== acme.sh 3.1.6 planned renewals"
for d in $R/acme316/*_ecc; do n=$(basename $d _ecc); c=$d/$n.cer
  echo "${n%%.*} notBefore=$(openssl x509 -in $c -noout -startdate | cut -d= -f2) notAfter=$(openssl x509 -in $c -noout -enddate | cut -d= -f2) next=$(grep ^Le_NextRenewTimeStr= $d/$n.conf | cut -d= -f2-) days=$(grep ^Le_RenewalDays= $d/$n.conf | cut -d= -f2-)"; done
echo "== lego decision (ARI, then ARI disabled)"
lego run --server letsencrypt-staging --accept-tos --http -d tlego.$IPD.sslip.io --path $R/lego --profile tlsserver --log.level debug 2>&1 | grep -E "RenewalInfo|Skip renewal"
lego run --server letsencrypt-staging --accept-tos --http -d tlego.$IPD.sslip.io --path $R/lego --profile tlsserver --ari-disable 2>&1 | grep -E "Skip renewal"
echo "== ARI windows"
python3 /srv/le/ari.py $R/cb58/etc/live/*/cert.pem $R/lego/certificates/tlego*.sslip.io.crt $(ls $R/acme316/*_ecc/*.cer | grep -v -E "/ca.cer|fullchain")
echo "== certbot 5.8 probe (hours after notBefore)"
/srv/le/probe-certbot.sh /snap/bin/certbot $R/cb58 t58.$IPD.sslip.io 700 709 715 718 721 724 727 730 733 740
echo "== certbot 2.9 probe on a copy of the same 45-day lineage"
rm -rf $R/cb29 && cp -a $R/cb58 $R/cb29 && sed -i "s#$R/cb58#$R/cb29#g; /preferred_profile/d" $R/cb29/etc/renewal/*.conf
/srv/le/probe-certbot.sh certbot $R/cb29 t58.$IPD.sslip.io 340 355 359 362 365 380
echo "== tlsserver suite done $(date -u +%FT%TZ)"
