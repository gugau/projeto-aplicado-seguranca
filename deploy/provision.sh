#!/usr/bin/env bash
set -Eeuo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Execute com sudo: sudo bash deploy/provision.sh <IP-ou-dominio> <email>" >&2
  exit 1
fi

if [[ "$#" -ne 2 ]]; then
  echo "Uso: sudo bash deploy/provision.sh <IP-publico-ou-dominio> <email>" >&2
  exit 1
fi

public_address="$1"
email="$2"
deploy_user="${SUDO_USER:-}"
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "$script_dir/.." && pwd)"

if [[ ! "$public_address" =~ ^[A-Za-z0-9.-]+$ ]]; then
  echo "Informe um IPv4 ou domínio válido, sem protocolo ou caminho." >&2
  exit 1
fi

if [[ ! "$email" =~ ^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$ ]]; then
  echo "Informe um e-mail válido para a conta da Let's Encrypt." >&2
  exit 1
fi

if [[ -z "$deploy_user" || "$deploy_user" == "root" ]]; then
  echo "Execute o script com sudo a partir do usuário administrativo que fará o deploy." >&2
  exit 1
fi

if ! id "$deploy_user" >/dev/null 2>&1; then
  echo "Usuário de deploy inexistente: $deploy_user" >&2
  exit 1
fi

authorized_keys="/home/$deploy_user/.ssh/authorized_keys"
if [[ ! -s "$authorized_keys" ]]; then
  echo "Nenhuma chave SSH autorizada encontrada em $authorized_keys. O endurecimento foi interrompido para evitar bloqueio de acesso." >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends \
  nginx python3 python3-venv python3-pip rsync fail2ban ufw openssl ca-certificates curl

if ! openssl list -tls1_3 -tls-groups 2>/dev/null | grep -q 'X25519MLKEM768'; then
  echo "O OpenSSL disponível não oferece X25519MLKEM768. Use a versão estável mais recente do Ubuntu/Debian com OpenSSL 3.5+ antes de prosseguir." >&2
  exit 1
fi

if ! id webapp >/dev/null 2>&1; then
  useradd --system --no-create-home --shell /usr/sbin/nologin --gid www-data webapp
fi
usermod -a -G www-data "$deploy_user"

install -d -o "$deploy_user" -g www-data -m 0750 /opt/projeto-aplicado
install -d -o "$deploy_user" -g www-data -m 0750 /opt/projeto-aplicado/releases
install -d -o "$deploy_user" -g www-data -m 0750 /opt/projeto-aplicado/releases/bootstrap
rsync -a --delete \
  --exclude '.git' --exclude '.github' --exclude '.env*' \
  "$repo_root/" /opt/projeto-aplicado/releases/bootstrap/
chown -R "$deploy_user":www-data /opt/projeto-aplicado/releases/bootstrap
chmod -R o-rwx /opt/projeto-aplicado/releases/bootstrap

python3 -m venv /opt/projeto-aplicado/releases/bootstrap/.venv
/opt/projeto-aplicado/releases/bootstrap/.venv/bin/python -m pip install \
  --disable-pip-version-check --requirement /opt/projeto-aplicado/releases/bootstrap/requirements.txt
ln -sfn /opt/projeto-aplicado/releases/bootstrap /opt/projeto-aplicado/current

if [[ ! -f /etc/projeto-aplicado.env ]]; then
  read -r -p "Usuário inicial da aplicação [admin]: " app_username
  app_username="${app_username:-admin}"
  if [[ ! "$app_username" =~ ^[A-Za-z0-9_.-]{1,80}$ ]]; then
    echo "O usuário deve ter de 1 a 80 caracteres simples." >&2
    exit 1
  fi

  echo "Cadastre a senha inicial da aplicação (mínimo de 12 caracteres)."
  password_hash="$(/opt/projeto-aplicado/current/.venv/bin/python /opt/projeto-aplicado/current/tools/generate_password_hash.py)"
  secret_key="$(openssl rand -hex 32)"

  install -o root -g www-data -m 0640 /dev/null /etc/projeto-aplicado.env
  {
    printf 'APP_ENV=production\n'
    printf 'SECRET_KEY=%s\n' "$secret_key"
    printf 'APP_USERNAME=%s\n' "$app_username"
    printf 'APP_PASSWORD_HASH=%s\n' "$password_hash"
    printf 'SESSION_MINUTES=30\n'
  } > /etc/projeto-aplicado.env
fi

install -o root -g root -m 0644 "$repo_root/deploy/systemd/projeto-aplicado.service" /etc/systemd/system/projeto-aplicado.service

install -d -o root -g root -m 0755 /etc/nginx/snippets
install -o root -g root -m 0644 "$repo_root/deploy/nginx/projeto-proxy.conf" /etc/nginx/snippets/projeto-proxy.conf
install -o root -g root -m 0644 "$repo_root/deploy/nginx/projeto-pqc.conf" /etc/nginx/snippets/projeto-pqc.conf
install -o root -g root -m 0644 "$repo_root/deploy/nginx/projeto-rate-limit.conf" /etc/nginx/conf.d/projeto-rate-limit.conf
sed "s/__PUBLIC_ADDRESS__/$public_address/g" "$repo_root/deploy/nginx/bootstrap.conf" > /etc/nginx/sites-available/projeto-aplicado
ln -sfn /etc/nginx/sites-available/projeto-aplicado /etc/nginx/sites-enabled/projeto-aplicado
rm -f /etc/nginx/sites-enabled/default
install -d -o www-data -g www-data -m 0755 /var/www/certbot/.well-known/acme-challenge
nginx -t
systemctl enable --now nginx

python3 -m venv /opt/certbot
/opt/certbot/bin/python -m pip install --disable-pip-version-check 'certbot==5.8.0'
ln -sfn /opt/certbot/bin/certbot /usr/local/bin/certbot

if [[ "$public_address" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]; then
  certbot certonly \
    --non-interactive --agree-tos --no-eff-email --email "$email" \
    --preferred-profile shortlived \
    --webroot --webroot-path /var/www/certbot \
    --ip-address "$public_address" \
    --key-type ecdsa
else
  certbot certonly \
    --non-interactive --agree-tos --no-eff-email --email "$email" \
    --webroot --webroot-path /var/www/certbot \
    --domain "$public_address" \
    --key-type ecdsa
fi

sed "s/__PUBLIC_ADDRESS__/$public_address/g" "$repo_root/deploy/nginx/projeto-aplicado.conf" > /etc/nginx/sites-available/projeto-aplicado
install -d -o root -g root -m 0755 /etc/letsencrypt/renewal-hooks/deploy
install -o root -g root -m 0755 "$repo_root/deploy/certbot/reload-nginx.sh" /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
install -o root -g root -m 0644 "$repo_root/deploy/certbot/certbot-renew.service" /etc/systemd/system/certbot-renew.service
install -o root -g root -m 0644 "$repo_root/deploy/certbot/certbot-renew.timer" /etc/systemd/system/certbot-renew.timer

install -o root -g root -m 0644 "$repo_root/deploy/fail2ban/sshd.local" /etc/fail2ban/jail.d/sshd.local
install -o root -g root -m 0644 "$repo_root/deploy/ssh/99-projeto-aplicado.conf" /etc/ssh/sshd_config.d/99-projeto-aplicado.conf
sshd -t

sudoers_file="/etc/sudoers.d/projeto-aplicado-deploy"
{
  printf '%s ALL=(root) NOPASSWD: /usr/bin/systemctl restart projeto-aplicado.service\n' "$deploy_user"
  printf '%s ALL=(root) NOPASSWD: /usr/bin/systemctl is-active --quiet projeto-aplicado.service\n' "$deploy_user"
} > "$sudoers_file"
chmod 0440 "$sudoers_file"
visudo -cf "$sudoers_file"

ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'SSH protegido por Fail2Ban'
ufw allow 80/tcp comment 'HTTP para redirect e ACME'
ufw allow 443/tcp comment 'HTTPS da aplicacao'
ufw --force enable

nginx -t
systemctl daemon-reload
systemctl enable --now projeto-aplicado.service
systemctl enable --now fail2ban.service
systemctl restart fail2ban.service
systemctl enable --now certbot-renew.timer
systemctl reload nginx
systemctl restart ssh

certbot renew --dry-run
bash "$repo_root/deploy/verify-security.sh" "$public_address"

echo "Provisionamento concluído: https://$public_address"
echo "Abra uma NOVA sessão SSH para validar o acesso por chave antes de fechar esta sessão."
