# Implantação na Oracle Cloud Infrastructure

Este roteiro complementa o provisionamento existente. Não utiliza banco, containers, load balancer nem VMs para DEV/HMG. Requer acesso à conta pessoal OCI e GitHub; nenhuma credencial deve entrar no Git.

## 1. Conferir antes de criar

Execute `preflight.py` com o Python do ambiente da OCI CLI, passando `--config-file CAMINHO_LOCAL` e `--profile PERFIL`. O script usa sessão temporária e somente consulta. Não imprima o arquivo de configuração ou o token.

Resultado real em 03/11/2026: São Paulo é a home region, não há máquinas ativas e o catálogo Ubuntu para A1 retorna versões até 26.04. [Ubuntu 26.10](https://documentation.ubuntu.com/release-notes/26.10/) já é estável. A imagem 26.04 não deve ser apresentada como a última versão estável.

Plano de menor alteração: imagem oficial Ubuntu 26.04 ARM, seguida de atualização suportada para 26.10 antes do provisionamento da aplicação. Essa atualização ainda não foi executada/testada e pode exigir recuperação por console. Uma alternativa é Debian estável atual, mas imagem personalizada e elegibilidade/cobrança precisam ser verificadas antes da importação. Não criar imagem personalizada nem escolher shape pago por falta de capacidade.

Conferir no Console OCI:

- Shape A1 e imagem identificados como elegíveis, uso acumulado do mês, limites e recursos existentes.
- Plano inicial: 1 OCPU, 6 GB de RAM, disco de inicialização de 47 GB, desempenho padrão sem recursos premium.
- Nenhuma reserva paga, IP BYO, backup automático pago, LB, NAT gateway ou assinatura Marketplace.
- Se houver falta de capacidade ou elegibilidade incerta, interromper a criação e registrar a resposta; não trocar automaticamente para shape pago.

## 2. Rede e acesso

Criar uma VCN e uma sub-rede pública, um internet gateway e uma rota padrão para ele. A VM recebe IP público; registrar se efêmero ou reservado e confirmar a política de preço vigente. Não presumir estabilidade de um IP efêmero após reconstrução da VNIC. A emissão por IP depende do endereço final.

Regras de entrada stateful: TCP 80 e 443 para internet; TCP 22 conforme a decisão de origem abaixo. Não expor 5000/8000. Conferir Security Lists e NSG em conjunto, porque permissões se somam. Manter saída necessária para DNS, NTP, APT/PyPI, ACME e metadados OCI; não bloquear regras de plataforma sem validar o efeito.

**Origem SSH:** com o runner padrão `ubuntu-latest`, o IP de saída é dinâmico. Apenas o `/32` do aluno não permite deploy. Opções operacionais:

- Para o protótipo público com runner padrão: aceitar SSH público com autenticação exclusivamente por chave, conta deployer dedicada, root e senha desativados e Fail2Ban. Registrar explicitamente esse alcance em OCI e UFW. O escopo exige proteção da porta 22, não um `/32` exclusivo.
- Para SSH limitado por origem: definir conectividade de runner aprovada antes de habilitar a pipeline. Não contratar runner com IP fixo nem instalar runner auto-hospedado na VM automaticamente.

O quarto argumento de `provision.sh` é a origem real aprovada; `0.0.0.0/0` significa exposição pública de SSH. O script não muda a rede OCI e não sincroniza IPs de runners. [Referência GitHub](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-githubs-ip-addresses).

Antes de desabilitar senhas, manter acesso ao console serial/recuperação OCI e abrir uma segunda sessão com a chave administrativa. Conferir `/etc/os-release` e `openssl version` após qualquer atualização/reboot. No Ubuntu, verificar a política de atualização em `/etc/update-manager/release-upgrades`; executar upgrades de distribuição somente com plano de recuperação e concluir o reboot antes de instalar a aplicação.

## 3. Provisionar sem publicar segredos

Gerar chave Ed25519 dedicada ao deploy localmente. Manter a privada no armazenamento seguro local e depois no GitHub Secret; enviar somente a `.pub` para a VM por SSH cuja chave de host foi conferida pelo console OCI.

Clonar o repositório público e executar, a partir da raiz:

```bash
sudo bash deploy/provision.sh IP_PUBLICO EMAIL_DO_ALUNO /caminho/deploy.pub CIDR_SSH
```

Os argumentos são placeholders, não resultados reais. O aluno informa usuário e senha inicial da aplicação interativamente. A senha não deve aparecer em argumentos, logs ou na pipeline. O script cria `deployer` e `webapp`, separando o administrador da conta de implantação. `deployer` não deve ter sudo adicional por outros arquivos de sudoers.

Após instalar, abrir nova sessão administrativa antes de fechar a anterior e conferir:

```bash
sudo sshd -t
sudo sshd -T
sudo -l -U deployer
sudo ufw status numbered
sudo ss -ltnp
sudo fail2ban-client get sshd maxretry
sudo fail2ban-client get sshd bantime
sudo systemctl status projeto-aplicado nginx fail2ban --no-pager
sudo bash deploy/verify-security.sh IP_PUBLICO
sudo certbot renew --dry-run --run-deploy-hooks
sudo systemctl list-timers certbot-renew.timer
```

Comparar a versão OpenSSL de linha de comando com a biblioteca efetivamente ligada ao Nginx em `nginx -V`. O teste local de handshake exige TLS 1.3 e `X25519MLKEM768` com certificado verificado; sua aprovação ainda precisa ser obtida na VM.

## 4. Configurar GitHub e executar deploy

Usar apenas `gugau/projeto-aplicado-seguranca`, com identidade pessoal local e remote pelo alias pessoal. Não alterar identidade Git global nem credenciais do trabalho.

No environment `production`, cadastrar `SERVER_HOST`, `SERVER_USER=deployer`, `SERVER_SSH_KEY` e `SERVER_KNOWN_HOSTS`. Conferir a fingerprint da chave do host no console OCI antes de registrar `known_hosts`; `ssh-keyscan` sozinho não comprova identidade. `SERVER_PORT` é opcional e fica no environment; o padrão é 22.

Criar a variável **do repositório** `PRODUCTION_DEPLOY_ENABLED=true` somente após validar o servidor e a conectividade. O `if` do job não deve depender de variável exclusiva de environment. Enquanto o gate estiver ausente, o deploy fica skipped e a entrega de CI/CD não está comprovada.

Validar nesta ordem: testes Linux na branch de trabalho, promoção `dev` → `hmg` → `main`, CI do push main e execução do workflow de implantação. Nenhuma publicação deve acontecer em DEV/HMG. O artefato contém apenas caminhos selecionados de `git archive`, e não a pasta local de trabalho.

## 5. Recuperação e manutenção

`release.sh` mantém o alvo anterior e restaura automaticamente o link se a nova versão falhar após ativação. A implantação continua falhando no GitHub para não esconder o incidente. Falhas de download/instalação antes da ativação preservam a versão em uso.

Para recuperação manual, pausar a pipeline, conferir `readlink -f /opt/projeto-aplicado/current` e identificar a última pasta saudável em `releases`. Como deployer, com o caminho real escolhido:

```bash
cd /opt/projeto-aplicado
# Substituir DIRETORIO_SAUDAVEL pelo nome conferido, sem manter o placeholder.
ln -s /opt/projeto-aplicado/releases/DIRETORIO_SAUDAVEL current.recovery
mv -Tf current.recovery current
sudo -n /usr/bin/systemctl restart projeto-aplicado.service
sudo -n /usr/bin/systemctl is-active --quiet projeto-aplicado.service
curl --fail --retry 10 --retry-connrefused --retry-delay 1 http://127.0.0.1:8000/healthz
```

Se `current.recovery` já existir, inspecioná-lo antes de usá-lo; não apagar diretórios para contornar um erro. Reinício invalida sessões voláteis. Monitorar disco: versões e artefatos não são apagados automaticamente. Remover somente alvos específicos já conferidos, conservando a versão atual e uma anterior saudável.

Se acesso SSH se perder, usar o console OCI para corrigir a regra de rede/UFW ou configuração SSH. Conferir `sshd -t` antes de recarregar. Não usar senha, `StrictHostKeyChecking=no` ou liberação de portas adicionais como atalho.

## 6. Evidências para encerrar

Para endereço por IP: resultados reais de [SSL.org](https://www.ssl.org/) e [DigiCert](https://www.digicert.com/pqc-checker). Para domínio: [SSL Labs](https://www.ssllabs.com/ssltest/) com nota A e suporte PQC. Salvar data, endereço e resultado, sem expor credenciais.

Completar a matriz em `docs/REVISAO-TECNICA.md` com evidências de cada etapa. Nenhum desses resultados deve ser presumido a partir dos arquivos.
