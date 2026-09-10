#!/usr/bin/env bash
set -Eeuo pipefail

public_address="${1:-}"
if [[ -z "$public_address" ]]; then
  echo "Uso: bash deploy/verify-security.sh <IP-ou-dominio>" >&2
  exit 1
fi

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
check "autenticação SSH por senha desativada" grep -Eq '^PasswordAuthentication[[:space:]]+no$' /etc/ssh/sshd_config.d/99-projeto-aplicado.conf
check "Fail2Ban configurado para quatro erros" grep -Eq '^maxretry[[:space:]]*=[[:space:]]*4$' /etc/fail2ban/jail.d/sshd.local
check "Fail2Ban configurado para 24 horas" grep -Eq '^bantime[[:space:]]*=[[:space:]]*24h$' /etc/fail2ban/jail.d/sshd.local
check "grupo híbrido PQC habilitado" grep -q 'X25519MLKEM768' /etc/nginx/snippets/projeto-pqc.conf
check "HTTP redireciona para HTTPS" bash -c "curl --silent --output /dev/null --write-out '%{http_code}' 'http://$public_address/' | grep -q '^301$'"
check "HTTPS responde" curl --fail --silent --show-error --output /dev/null "https://$public_address/"
check "HSTS presente" bash -c "curl --silent --head 'https://$public_address/' | tr -d '\r' | grep -qi '^Strict-Transport-Security:'"

if (( failures > 0 )); then
  echo "$failures verificação(ões) falharam." >&2
  exit 1
fi

echo "Todas as verificações locais de segurança foram aprovadas."
