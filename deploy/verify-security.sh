#!/usr/bin/env bash
set -Eeuo pipefail

public_address="${1:-}"
if [[ -z "$public_address" ]]; then
  echo "Uso: bash deploy/verify-security.sh <IP-ou-dominio>" >&2
  exit 1
fi
[[ "$public_address" =~ ^[A-Za-z0-9.-]+$ ]] || { echo 'Endereço inválido.' >&2; exit 1; }

failures=0

check() {
  local description="$1"
  shift
  if "$@"; then
    printf '[OK] %s\n' "$description"
  else
    printf '[FALHA] %s\n' "$description" >&2
    failures=$((failures + 1))
  fi
}

check "aplicação ativa" systemctl is-active --quiet projeto-aplicado.service
check "Nginx ativo" systemctl is-active --quiet nginx.service
check "Fail2Ban ativo" systemctl is-active --quiet fail2ban.service
check "renovação automática ativa" systemctl is-active --quiet certbot-renew.timer
check "configuração do Nginx válida" nginx -t
check "configuração do SSH válida" sshd -t
effective_ssh="$(sshd -T | tr '[:upper:]' '[:lower:]')"
check "autenticação SSH efetiva por senha desativada" grep -qx 'passwordauthentication no' <<< "$effective_ssh"
check "autenticação interativa efetiva desativada" grep -qx 'kbdinteractiveauthentication no' <<< "$effective_ssh"
check "login root efetivo desativado" grep -qx 'permitrootlogin no' <<< "$effective_ssh"
check "Fail2Ban efetivo para quatro erros" test "$(fail2ban-client get sshd maxretry)" = 4
check "Fail2Ban efetivo para 24 horas" test "$(fail2ban-client get sshd bantime)" = 86400
check "UFW ativo" bash -c 'ufw status | grep -q "Status: active"'
check "Gunicorn escuta em loopback" bash -c 'ss -ltnH | awk "{print \$4}" | grep -qx "127.0.0.1:8000"'
check "Gunicorn não expõe 8000 externamente" bash -c '! ss -ltnH | awk "{print \$4}" | grep -Eq "^(0.0.0.0|\*|\[::\]|::):8000$"'
check "grupo híbrido PQC habilitado" grep -q 'X25519MLKEM768' /etc/nginx/snippets/projeto-pqc.conf
check "HTTP redireciona para HTTPS" bash -c "curl --silent --output /dev/null --write-out '%{http_code}' 'http://$public_address/' | grep -q '^301$'"
check "HTTPS responde" curl --fail --silent --show-error --output /dev/null "https://$public_address/"
check "HSTS presente" bash -c "curl --silent --head 'https://$public_address/' | tr -d '\r' | grep -qi '^Strict-Transport-Security:'"
check "área interna exige autenticação" bash -c "curl --silent --output /dev/null --write-out '%{http_code}' 'https://$public_address/dashboard' | grep -q '^302$'"
check "healthz não é público" bash -c "curl --silent --output /dev/null --write-out '%{http_code}' 'https://$public_address/healthz' | grep -q '^403$'"
check "Certbot mínimo 5.4" bash -c 'installed=$(certbot --version | awk "{print \$2}"); dpkg --compare-versions "$installed" ge 5.4.0'
verify_name=(-verify_hostname "$public_address")
if [[ "$public_address" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]; then
  verify_name=(-verify_ip "$public_address")
fi
check "handshake TLS 1.3 híbrido PQC com certificado confiável" \
  timeout 15 openssl s_client -connect 127.0.0.1:443 -servername "$public_address" \
  -tls1_3 -groups X25519MLKEM768 -verify_return_error "${verify_name[@]}" -brief </dev/null

if (( failures > 0 )); then
  echo "$failures verificação(ões) falharam." >&2
  exit 1
fi

echo "Todas as verificações locais de segurança foram aprovadas."
