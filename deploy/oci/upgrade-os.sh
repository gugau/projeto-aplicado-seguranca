#!/usr/bin/env bash
# Atualização suportada antes de instalar aplicação/dados na imagem OCI Ubuntu.
set -Eeuo pipefail
[[ "$EUID" -eq 0 ]] || { echo 'Execute com sudo.' >&2; exit 1; }
source /etc/os-release
[[ "$ID" == ubuntu ]] || { echo 'Este procedimento é específico do Ubuntu.' >&2; exit 1; }
if [[ "$VERSION_ID" == 26.10 ]]; then
  echo 'Ubuntu 26.10 já instalado. Confirme atualizações, reboot e serviços.'
  exit 0
fi
[[ "$VERSION_ID" == 26.04 ]] || { echo 'Versão inicial diferente da imagem planejada; revisar upgrade.' >&2; exit 1; }
export DEBIAN_FRONTEND=noninteractive
export LC_ALL=C
apt-get update
apt-get upgrade --yes
apt-get install --yes ubuntu-release-upgrader-core
sed -i 's/^Prompt=.*/Prompt=normal/' /etc/update-manager/release-upgrades
available="$(do-release-upgrade --check-dist-upgrade-only 2>&1)" || {
  printf '%s\n' "$available" >&2
  echo 'Upgrade estável indisponível: não forçar desenvolvimento nem declarar conformidade.' >&2
  exit 1
}
printf '%s\n' "$available"
grep -Eq "New release .*26\.10" <<< "$available" || {
  echo 'A oferta de atualização não é Ubuntu 26.10; revisar antes de continuar.' >&2; exit 1;
}
# Sem -d: nenhuma versão de desenvolvimento pode ser selecionada.
do-release-upgrade --frontend DistUpgradeViewNonInteractive
echo 'Atualização finalizada; reinicie e valide /etc/os-release, kernel e nova sessão SSH.'
