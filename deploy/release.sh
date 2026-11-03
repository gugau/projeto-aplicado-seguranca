#!/usr/bin/env bash
# Executado como usuário dedicado, sem sudo geral, após upload por SSH verificado.
set -Eeuo pipefail
umask 0027

release_sha="${1:-}"
[[ "$release_sha" =~ ^[a-f0-9]{40}$ ]] || { echo 'Commit inválido.' >&2; exit 1; }
app_root="${APP_ROOT:-/opt/projeto-aplicado}"
archive="$app_root/incoming/$release_sha.tar.gz"
[[ -f "$archive" ]] || { echo 'Artefato ausente.' >&2; exit 1; }
exec 9>"$app_root/deploy.lock"
flock -n 9 || { echo 'Outra implantação em execução.' >&2; exit 1; }

previous="$(readlink -f "$app_root/current" || true)"
release_dir="$(mktemp -d "$app_root/releases/$release_sha.XXXXXX")"
activated=false

activate() {
  local temporary="$app_root/.current.$$.${RANDOM}"
  ln -s "$1" "$temporary"
  mv -Tf "$temporary" "$app_root/current"
}

healthy() {
  for _ in {1..20}; do
    if sudo -n /usr/bin/systemctl is-active --quiet projeto-aplicado.service && \
      curl --fail --silent --show-error --max-time 3 http://127.0.0.1:8000/healthz >/dev/null; then
      return 0
    fi
    sleep 1
  done
  return 1
}

recover() {
  local exit_code="$?"
  trap - EXIT
  if (( exit_code != 0 )) && [[ "$activated" == true ]]; then
    if [[ "$previous" == "$app_root/releases/"* && -d "$previous" ]]; then
      activate "$previous"
      sudo -n /usr/bin/systemctl restart projeto-aplicado.service
      if healthy; then
        echo 'Nova versão falhou; versão anterior restaurada.' >&2
      else
        echo 'FALHA: versão anterior restaurada, mas requer diagnóstico do serviço.' >&2
      fi
    else
      echo 'FALHA: primeira publicação sem versão anterior para restauração.' >&2
    fi
  fi
  exit "$exit_code"
}
trap recover EXIT

tar -xzf "$archive" -C "$release_dir" --no-same-owner
python3 -m venv "$release_dir/.venv"
"$release_dir/.venv/bin/python" -m pip install --disable-pip-version-check --requirement "$release_dir/requirements.txt"
chgrp -R "${APP_GROUP:-www-data}" "$release_dir"
# mktemp cria o diretório com 0700; o serviço webapp precisa atravessá-lo.
# Dar leitura/execução ao grupo sem permitir escrita ou acesso a terceiros.
chmod -R g+rX,g-w,o-rwx "$release_dir"
# Marcado antes da troca: qualquer falha na ativação também aciona recuperação.
activated=true
activate "$release_dir"
sudo -n /usr/bin/systemctl restart projeto-aplicado.service
healthy
printf 'Versão %s ativada e saudável.\n' "$release_sha"
# Não remover versões automaticamente: conservamos o caminho de recuperação.
