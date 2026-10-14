#!/bin/bash
# Throwaway Ubuntu 24.04 droplet with port 80 open. Installs the clients this
# test compares: certbot from apt (2.9.0 on 24.04) and from snap (5.8.0),
# acme.sh 3.0.7 and 3.1.6 from the upstream repo, and the latest lego.
set -e
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq certbot faketime socat jq git
snap install certbot --classic
git clone -q https://github.com/acmesh-official/acme.sh.git /opt/acme-src
mkdir -p /opt/acme307 /opt/acme316 /srv/le
git -C /opt/acme-src show 3.0.7:acme.sh > /opt/acme307/acme.sh
git -C /opt/acme-src show 3.1.6:acme.sh > /opt/acme316/acme.sh
chmod +x /opt/acme307/acme.sh /opt/acme316/acme.sh
LV=$(curl -s https://api.github.com/repos/go-acme/lego/releases/latest | jq -r .tag_name)
curl -sL -o /tmp/lego.tgz "https://github.com/go-acme/lego/releases/download/$LV/lego_${LV}_linux_amd64.tar.gz"
tar -xzf /tmp/lego.tgz -C /usr/local/bin lego
certbot --version; /snap/bin/certbot --version; lego --version
