# Revisão técnica e matriz de conformidade

Data: 03/11/2026. Esta revisão preserva Flask, Gunicorn, Nginx, systemd, a ausência de banco e o fluxo `dev` → `hmg` → `main`. Não cria ambientes de nuvem para DEV/HMG.

Fonte principal: [escopo oficial da disciplina](https://github.com/ziraldocardoso/Projeto_aplicado-praticas_de_mercado/blob/main/Escopo_e_elementos_obrigatorios.md). Categorias conferidas na [OWASP Top 10:2025](https://top10.owasp.org/2025/).

## Diagnóstico inicial, antes das alterações

| Classificação | Evidência observada |
|---|---|
| Implementado e validado localmente | Login, dashboard protegido, logout normal, CSRF básico, cabeçalhos, limite de corpo e rate limit: 10 testes passaram. |
| Implementado, sem validação em servidor | Configurações Nginx, SSH, Fail2Ban, UFW, Certbot e systemd existiam em `deploy/`. Não havia VM para executá-las. |
| Parcialmente implementado | Deploy tinha validação de host e seleção do commit testado, mas trocava symlink sem rollback. O administrador da nuvem era também o usuário de deploy. |
| Ausente | VM atual, IP de aplicação, certificado emitido, renovação comprovada, testes externos TLS/PQC e deploy atual em produção. |
| Em desacordo com o comportamento seguro declarado | Copiar o cookie antes do logout e reapresentá-lo depois retornou HTTP 200 no dashboard. CSRF não ASCII lançou `TypeError`. A restrição de SSH ao IP do aluno bloqueava o runner hospedado. |

O teste de reprodução usou somente credenciais sintéticas dos testes. Nenhuma credencial real foi reproduzida no relatório. A presença de diretivas nos arquivos e os resultados históricos de CI não foram classificados como validação atual de produção.

## Prioridades e correções desta revisão

1. Segurança: revogar sessões no servidor; expiração absoluta; rejeitar CSRF malformado; validar hash `scrypt`; precedência e configuração efetiva de SSH.
2. Implantação: usuário dedicado, artefato restrito do Git, ativação atômica, espera de saúde e recuperação automática.
3. Testes: regressões de autenticação, cookies, entradas, duas instâncias de aplicação e cenários Linux do script de deploy.
4. Documentação: situação real, roteiro OCI, diferenças do escopo, matriz e evidências a coletar.

## Matriz após as correções locais

Legenda: **VL** = validado localmente; **AV** = arquivo implementado, validação no servidor pendente; **P** = parcial; **A** = ausente em produção. As categorias podem coexistir porque código local e infraestrutura têm evidências distintas.

| Requisito | Situação atual | Evidência | Ajuste/etapa necessária | Como validar |
|---|---|---|---|---|
| OCI Free Tier | P; conta acessível, sem VM ativa | Consulta autenticada à OCI após limpeza; `deploy/oci/preflight.py` | Confirmar limites, uso acumulado e capacidade antes de provisionar | Console Always Free + API, configuração e análise de custos |
| Ubuntu/Debian estável mais recente | A | Catálogo OCI ARM retornou Ubuntu até 26.04 | Usar versão atual, não apenas LTS antiga; ver roteiro | `/etc/os-release`, `uname -r`, fonte oficial da distribuição |
| Nginx/Apache | AV | `deploy/nginx/`, `deploy/provision.sh` | Instalar e testar configuração efetiva | `nginx -v`, `nginx -V`, `nginx -t`, `nginx -T` |
| Acesso por IP público | A | Nenhum IP de produção foi criado | Criar VM/rede mínima e publicar | Acesso externo HTTPS por IP e captura |
| SSH por chave, sem senha | AV | `deploy/ssh/00-projeto-aplicado.conf`; `sshd -T` no script | Validar chave em segunda sessão antes de endurecer; manter console de recuperação | `sshd -t`, `sshd -T`, login por chave e rejeição de senha |
| Fail2Ban quatro erros/24 h | AV | `deploy/fail2ban/sshd.local`; backend systemd e `python3-systemd` | Conferir jail ativo | `fail2ban-client get sshd maxretry`, `get sshd bantime`, teste controlado por origem recuperável |
| Exposição mínima | AV/P | UFW parametrizado, proxy loopback; origem SSH depende da pipeline | Alinhar NSG/UFW com origem de administração/Actions | `ufw status numbered`, regras OCI, `ss -ltnp` e sondagem externa |
| Certbot ≥5.4, Let's Encrypt | AV | `deploy/provision.sh` fixa 5.8 e usa perfil obrigatório para IP | Emitir certificado real | `certbot --version`, `certbot certificates`, validar cadeia/SAN IP |
| Redirecionamento HTTP → HTTPS | AV | `deploy/nginx/projeto-aplicado.conf` | Aplicar na VM | HTTP 301 para HTTPS; exceção ACME continua acessível |
| Renovação automática/reload | AV | `deploy/certbot/` timer/hook | Testar emissão e renovação | Timer ativo; `certbot renew --dry-run --run-deploy-hooks`; datas do certificado |
| TLS confiável por IP | A | Verificador local preparado, nenhum certificado emitido | Publicar e submeter endereço real | SSL.org: confiança YES e assinatura/chave aceitáveis |
| PQC por IP | AV/A | Grupo híbrido configurado e handshake local adicionado a `verify-security.sh` | Comprovar biblioteca usada pelo Nginx e handshake real | `nginx -V`, OpenSSL 3.5+; s_client híbrido e DigiCert |
| TLS/PQC por domínio, se escolhido | Não se aplica ao plano por IP | Nginx suporta domínio, mas não foi escolhido domínio | Só aplicar se trocar o endereço de entrega | SSL Labs A com indicação de PQC; não substituir por teste de IP |
| GitHub público | Validado pela API pública em 03/11/2026 | Repositório `gugau/projeto-aplicado-seguranca`: `private=false`, branch padrão `dev` | Publicar esta revisão após validação | Página pública e commit correspondente |
| Proteção de branches (prática adicional solicitada) | P; dev/hmg/main estão sem proteção na API atual | API `/branches`: `protected=false` para as três branches | Configurar PR/check obrigatório após autenticar a conta pessoal | API e ensaio de promoção sem push direto |
| Conta pessoal separada | Implementado; configuração histórica | Alias SSH pessoal e identidade local definidos nesta tarefa | Conferir identidade antes de push; sem alterar Git global | `git config --local user.name`, remote e autenticação pessoal |
| Prevenção de credenciais | VL, heurística | `.gitignore`, `tools/check_secrets.py --history` | Repetir no CI; revisar também alterações novas | Verificação atual e de blobs históricos, sem imprimir valores |
| Login e página protegida | VL | `app/auth.py`, `app/security.py`, testes de autenticação | Repetir externamente na VM | Acesso direto sem cookie recebe 302; credenciais corretas abrem dashboard |
| Logout e cookie reapresentado | VL; falha inicial corrigida | `app/sessions.py`; regressão entre duas aplicações | Confirmar diretório compartilhado com dois workers reais | Capturar cookie sintético, sair e reutilizar: 302 |
| Expiração e rotação | VL | Expiração absoluta no ticket; `SESSION_REFRESH_EACH_REQUEST=False` | Confirmar tempo configurado em produção | Testes de relógio e uso contínuo; ausência de renovação automática |
| Cookies, CSRF, entradas e erros | VL | `tests/test_auth.py`, `tests/test_security.py` | Conferir proxy/HTTPS real | Cookies Secure/HttpOnly/Strict; CSRF ausente, inválido e Unicode rejeitados |
| ≥3 categorias OWASP 2025 | VL para aplicação; AV para borda | A01, A02, A05 e A07, mapeadas no README | Não confundir mitigação com garantia total contra uma categoria | Regressões de acesso, configuração, escape e autenticação |
| IA no desenvolvimento/auditoria | Evidência nesta tarefa e arquivos | Histórico desta tarefa; README | Aluno demonstrar ferramentas e justificar decisões | Demonstração da revisão e das reproduções/correções |
| GitHub Actions após push main | P | Workflow preserva CI aprovado, SHA exato e Secrets; gate desabilitado | Cadastrar Secrets, habilitar variável do repositório e executar push main | Run real verde com SHA correspondente e aplicação atualizada |
| DEV/HMG sem publicação | AV | `ci.yml` e condição de branch em `deploy.yml` | Validar novos workflows no GitHub | Runs em dev/hmg só build/testes; nenhum acesso aos Secrets de produção |
| Identidade SSH, usuário mínimo | AV | StrictHostKeyChecking e deployer dedicado; duas permissões sudo | Confirmar chave de host por console confiável e sudo efetivo | Fingerprint validada e `sudo -l -U deployer` |
| Recuperação do deploy | VL com serviços simulados; AV para OCI | `deploy/release.sh`, `tests/test_release.py` | Executar novo CI e ensaio real com falha controlada | Link anterior restaurado e pipeline continua vermelha |
| README e evidências finais | P | README revisto; este relatório e roteiro OCI | Acrescentar resultados de nuvem realmente coletados | Checklist de demonstração abaixo |

## Verificações executadas nesta revisão

- Baseline: **10 testes passaram** antes de alterar código.
- Após as correções da aplicação: **19 passaram** no Windows.
- Windows/Python 3.12: **19 passaram e 2 foram ignorados**, pois exigem Linux.
- Debian local/Python 3.13: **21 passaram**, incluindo ativação e rollback com o script real e serviços simulados. Houve aviso de permissão na gravação do cache pytest compartilhado com Windows; não foi falha de teste. Isso não constitui validação de deploy na OCI.
- Compilação Python: aprovada.
- Parsing dos dois workflows YAML: aprovado; isso não valida semanticamente todas as expressões de Actions.
- Sintaxe dos scripts Bash: aprovada; Nginx, systemd e firewall não foram executados no Windows.
- Varredura heurística de credenciais em arquivos do projeto e blobs do histórico local: nenhum padrão detectado. Isso não prova ausência de todo tipo de segredo.
- Auditoria atual: o conjunto instalado apresentou alertas para Werkzeug 3.1.8 (PYSEC-2026-4312) e pytest 8.4.2 (PYSEC-2026-1845; repetido na resposta da ferramenta). Foram fixados Werkzeug 3.1.9 e pytest 9.0.3. A reauditoria dos pacotes diretos e transitivos enumerados do ambiente Windows retornou **nenhuma vulnerabilidade conhecida**; a resolução automática inicial foi interrompida por execução prolongada e substituída por enumeração explícita, sem omitir as dependências instaladas de aplicação/testes. O novo CI também audita `requirements-dev.txt` com resolução de dependências. Referências dos mantenedores: [Werkzeug](https://werkzeug.palletsprojects.com/en/stable/changes/), [pytest](https://docs.pytest.org/en/9.0.x/changelog.html).
- `pip check`: sem conflitos nos ambientes Windows e Linux após as atualizações.
- OCI: consulta autenticada confirmou ausência de máquinas ativas e catálogo Ubuntu ARM até 26.04. Não foram criados recursos durante esta revisão.

## Diferenças e referências atuais

- O escopo aceita qualquer provedor gratuito; neste projeto a escolha foi OCI, por decisão do aluno.
- O escopo exige última versão estável, não apenas a última LTS disponível no catálogo. Em 03/11/2026, as fontes oficiais indicam [Ubuntu 26.10](https://documentation.ubuntu.com/release-notes/26.10/) e [Debian 13.7](https://www.debian.org/releases/). O catálogo OCI consultado não retornou Ubuntu 26.10 para A1.
- Para **IP**, o escopo exige SSL.org e DigiCert. Para **domínio**, exige SSL Labs A com PQC; não exige duplicar o teste de IP. O checklist antigo que sugeria DigiCert em todos os casos foi corrigido no roteiro.
- Assinatura do certificado e troca de chaves TLS são mecanismos diferentes. Certificado ECDSA pode coexistir com troca híbrida ML-KEM; só o teste real confirma negociação.
- A documentação Oracle apresenta diferenças entre limites A1 por tipo de conta e páginas; o plano conservador é 1 OCPU, 6 GB de memória e 47 GB de disco. Isso é planejamento, não garantia de capacidade ou custo zero. [Always Free](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm).

## Limitações conhecidas

O limitador de login é por processo; a borda Nginx mantém limite por IP compartilhado na VM. Não é um limitador distribuído. Os tickets são locais e voláteis; não suportam múltiplas VMs sem redesenho. Não há necessidade de Redis, banco ou containers para o protótipo atual. A conta de deploy pode publicar código da aplicação, portanto suas chaves continuam sensíveis mesmo com sudo limitado.

## Roteiro de demonstração e coleta

1. Mostrar o sistema operacional e os recursos/custos na OCI, sem credenciais.
2. Acessar o IP externamente; demonstrar 301 e certificado confiável.
3. Tentar dashboard sem sessão; errar login; entrar; sair; reapresentar somente cookie de teste.
4. Mostrar cookie protegido, cabeçalhos e rejeição de CSRF.
5. Mostrar configuração SSH efetiva, jail Fail2Ban, firewall e escuta loopback.
6. Mostrar timer, renovação de ensaio e reload do Nginx.
7. Salvar resultados externos exigidos para o tipo de endereço escolhido, com data/IP real.
8. Mostrar PR/promoção, CI, push main, deploy automático e versão servida.
9. Ensaiar recuperação usando uma alteração controlada e depois restaurar a versão saudável.

Não anexar cookies, chaves, tokens, senhas, arquivos de sessão ou conteúdo de `/etc/projeto-aplicado.env`. A conclusão acadêmica permanece pendente enquanto os itens de produção não tiverem evidência.
