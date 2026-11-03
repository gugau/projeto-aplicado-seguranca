#!/usr/bin/env bash
# Consulta para a gravação: não altera serviços nem lê arquivos de credenciais.
set -Eeuo pipefail
[[ "$EUID" -eq 0 ]] || { echo 'Execute com sudo na VM.' >&2; exit 1; }
section="${1:-infra}"
case "$section" in
  infra)
    printf '\nSISTEMA E SERVIDOR WEB\n'
    hostname
    . /etc/os-release
    printf '%s\n' "$PRETTY_NAME"
    nginx -v 2>&1
    printf '\nSSH — CONFIGURAÇÃO EFETIVA\n'
    sshd -T | tr '[:upper:]' '[:lower:]' | awk '$1 ~ /^(pubkeyauthentication|passwordauthentication|kbdinteractiveauthentication|permitrootlogin)$/ { print }'
    printf '\nFAIL2BAN — JAIL SSHD\n'
    printf 'Falhas permitidas: '; fail2ban-client get sshd maxretry
    printf 'Banimento em segundos: '; fail2ban-client get sshd bantime
    printf '\nFIREWALL\n'
    ufw status numbered
    ;;
  tls)
    address="${2:-}"
    [[ "$address" =~ ^[A-Za-z0-9][A-Za-z0-9.-]*$ ]] || { echo 'Informe IP ou domínio, sem protocolo.' >&2; exit 1; }
    printf '\nCERTBOT E RENOVAÇÃO\n'
    certbot --version
    systemctl is-active certbot-renew.timer
    systemctl list-timers certbot-renew.timer --no-pager
    printf '\nREDIRECIONAMENTO HTTP REAL\n'
    curl --fail --silent --show-error --max-time 10 --head "http://$address/" | tr -d '\r' | awk 'NR == 1 || tolower($1) == "location:" { print }'
    verify_name=(-verify_hostname "$address")
    if [[ "$address" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]; then verify_name=(-verify_ip "$address"); fi
    printf '\nHANDSHAKE LOCAL — COMPLEMENTA OS TESTES EXTERNOS\n'
    timeout 15 openssl s_client -connect 127.0.0.1:443 -servername "$address" \
      -tls1_3 -groups X25519MLKEM768 -verify_return_error "${verify_name[@]}" -brief </dev/null
    ;;
  release)
    printf '\nVERSÃO REALMENTE ATIVA\n'
    readlink -f /opt/projeto-aplicado/current
    printf '\nSERVIÇO\n'
    systemctl is-active projeto-aplicado.service
    printf '\nSAÚDE LOCAL\n'
    curl --fail --silent --show-error --max-time 5 http://127.0.0.1:8000/healthz
    printf '\n'
    ;;
  *) echo 'Uso: sudo bash deploy/presentation.sh infra|tls IP|release' >&2; exit 1 ;;
esac
