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

## Matriz após as correções e validações de produção

Legenda: **VL** = validado localmente; **VP** = validado na VM/externamente; **AV** = arquivo implementado, validação no servidor pendente; **P** = parcial; **A** = ausente em produção. As categorias podem coexistir. Resultados reais em [EVIDENCIAS-ENTREGA.md](EVIDENCIAS-ENTREGA.md).

| Requisito | Situação atual | Evidência | Ajuste/etapa necessária | Como validar |
|---|---|---|---|---|
| OCI Free Tier | VP para configuração; contabilização final temporária pendente | Uma A1 1 OCPU/6 GB/50 GB na home region | Acompanhar fatura; importação temporária autorizada até US$ 0,10 já removida | API OCI e registro de custos/limites |
| Ubuntu/Debian estável mais recente | VP | Ubuntu 26.10 stable, kernel 7.3; SSH efetivo | Manter atualizações | `/etc/os-release` e fonte oficial |
| Nginx/Apache | VP | Nginx 1.30.4; configuração testada e aplicação pública | Manutenção | `nginx -v/-V/-t/-T`, HTTPS externo |
| Acesso por IP público | VP | `https://163.176.111.141` e teste funcional externo | Preservar IP ou atualizar configuração se reconstruir VNIC | Acesso HTTPS real |
| SSH por chave, sem senha | VP | Novas sessões admin/deployer; `sshd -T` confirma senha/interativo/root no | Preservar console e chaves seguras | Login por chave e configuração efetiva |
| Fail2Ban quatro erros/24 h | VP | Jail ativo; get maxretry=4 e bantime=86400 | Monitorar bans; teste destrutivo de ban não feito para evitar bloquear administrador | Consultas efetivas do Fail2Ban |
| Exposição mínima | VP | NSG/UFW 22/80/443; SSH público expressamente autorizado; 8000 loopback | Manter compatibilidade com runner e revisar alcance conforme arquitetura | UFW, OCI e escutas reais |
| Certbot ≥5.4, Let's Encrypt | VP | Certbot 5.8, certificado emitido com SAN IP | Manter renovação | Certificado externo confiável |
| Redirecionamento HTTP → HTTPS | VP | HTTP 301 observado externamente | Manutenção | Teste externo |
| Renovação automática/reload | VP para timer e ensaio de renovação | Timer ativo e renew --dry-run aprovado; hook instalado | Observar futura renovação real em operação | Timer, dry-run e logs futuros |
| TLS confiável por IP | VP | SSL.org Yes/Good signature/Good key; cliente externo verifica cadeia/IP | Guardar captura real; diferença de rótulo registrada | Evidências da entrega |
| PQC por IP | VP | Handshakes interno/externo negociam X25519MLKEM768; DigiCert PASS informado pelo aluno | Guardar captura real do teste do aluno | OpenSSL e DigiCert |
| TLS/PQC por domínio, se escolhido | Não se aplica ao plano por IP | Nginx suporta domínio, mas não foi escolhido domínio | Só aplicar se trocar o endereço de entrega | SSL Labs A com indicação de PQC; não substituir por teste de IP |
| GitHub público | Validado pela API e publicação | Repositório `gugau/projeto-aplicado-seguranca`: `private=false`, branch padrão `dev`; revisão publicada por PR | Manter público sem credenciais | Página pública e commits correspondentes |
| Proteção de branches (prática adicional solicitada) | Validada | Proteção aplicada em dev/hmg/main e PRs #6/#7/#8 promovidos com CI | Manter controles | API e histórico de PRs |
| Conta pessoal separada | Validada nos pushes e API | Alias SSH pessoal, identidade Git local e CLI isolada autenticada como gugau | Preservar separação da conta profissional | Configuração local, remote e autenticação pessoal |
| Prevenção de credenciais | VL e CI real; heurística | `.gitignore`, scanner de arquivos/histórico e Secrets fora do Git | Manter scanner e revisão de alterações | Verificação atual e de blobs históricos, sem imprimir valores |
| Login e página protegida | VL/VP | Testes locais e 11 verificações externas | Manter regressões | Sem cookie: 302; credenciais corretas: dashboard 200 |
| Logout e cookie reapresentado | VL/VP; falha inicial corrigida | Tickets revogáveis; cookie real capturado e rejeitado após logout | Manter regressão | Reutilização após logout recebe 302 |
| Expiração e rotação | VL; configuração VP | Expiração absoluta no ticket; `SESSION_REFRESH_EACH_REQUEST=False`; VM configurada com 30 min | Manter regressões; não foi necessário aguardar 30 min na VM | Testes de relógio/rotação e consulta restrita da duração configurada |
| Cookies, CSRF, entradas e erros | VL; cookies/cabeçalhos VP | Testes e cliente HTTPS real | Manter regressões | Cookies Secure/HttpOnly/Strict; CSRF inválido/Unicode rejeitado localmente |
| ≥3 categorias OWASP 2025 | VL/VP para controles examinados | A01, A02, A05 e A07, mapeadas no README; borda e acesso externos verificados | Não confundir mitigação com garantia total contra uma categoria | Regressões de acesso, configuração, escape e autenticação |
| IA no desenvolvimento/auditoria | Evidência nesta tarefa e arquivos | Histórico desta tarefa; README | Aluno demonstrar ferramentas e justificar decisões | Demonstração da revisão e das reproduções/correções |
| GitHub Actions após push main | VP | CI e deploy 41647928276/41648006741 aprovados; SHA 3832321 conferido no current da VM | Manter gate e Secrets protegidos | Run real verde, SHA exato, serviço e HTTPS saudáveis |
| DEV/HMG sem publicação | Validado no GitHub | CI das promoções #6/#7; condição do deploy exige push main | Preservar condição nas novas promoções | Runs em dev/hmg só build/testes; nenhum acesso aos Secrets de produção |
| Identidade SSH, usuário mínimo | VP | Fingerprint validada pelo console OCI; nova conexão deployer e sudo -l com duas operações | Proteger chave dedicada e Secrets | Teste real de acesso/privilégios |
| Recuperação do deploy | VL/VP | Falha real recuperada e ensaio controlado posterior: status 1, mesmo alvo anterior e saúde restabelecida | Manter versão anterior e monitorar disco; há interrupção durante restart/falha | Evidências, logs do workflow e teste controlado |
| README e evidências finais | Concluídos para os critérios técnicos | README, matriz, roteiro OCI e EVIDENCIAS-ENTREGA com resultados reais | Aluno pode anexar capturas à apresentação; acompanhar contabilização OCI | Checklist de demonstração abaixo |

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
- OCI: o levantamento inicial encontrou ausência de máquinas ativas; depois foi criada a VM mínima. Ubuntu 26.04 foi substituído por 26.10 quando o upgrade oficial não ofereceu a versão. Imagens/buckets temporários foram removidos após confirmar boot e acesso SSH.
- Produção: 11 verificações HTTPS externas passaram após deploy e ensaio de recuperação; verificador local aprovou serviços, SSH, Fail2Ban, UFW, renovação, cabeçalhos e handshake TLS híbrido.
- Primeiro deploy: falhou por modo 0700 da pasta criada por mktemp e recuperou bootstrap automaticamente. A correção de permissão recebeu regressão Linux e foi promovida por PR antes do deploy aprovado. Um segundo ensaio controlado confirmou restauração da versão saudável, com retorno não zero.

## Diferenças e referências atuais

- O escopo aceita qualquer provedor gratuito; neste projeto a escolha foi OCI, por decisão do aluno.
- O escopo exige última versão estável, não apenas a última LTS disponível no catálogo. Em 03/11/2026, as fontes oficiais indicam [Ubuntu 26.10](https://documentation.ubuntu.com/release-notes/26.10/) e [Debian 13.7](https://www.debian.org/releases/). O catálogo OCI consultado não retornou Ubuntu 26.10 para A1.
- Para **IP**, o escopo exige SSL.org e DigiCert. Para **domínio**, exige SSL Labs A com PQC; não exige duplicar o teste de IP. O checklist antigo que sugeria DigiCert em todos os casos foi corrigido no roteiro.
- Assinatura do certificado e troca de chaves TLS são mecanismos diferentes. Certificado ECDSA pode coexistir com troca híbrida ML-KEM; só o teste real confirma negociação.
- A configuração aplicada é 1 OCPU, 6 GB e 50 GB de disco, na home region. A imagem importada foi armazenamento temporário cobrável, autorizado até US$ 0,10 e removido. Não há promessa de custo total zero. [Always Free](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm).

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

Não anexar cookies, chaves, tokens, senhas, arquivos de sessão ou conteúdo de `/etc/projeto-aplicado.env`. Os critérios técnicos obrigatórios têm evidências registradas. Permanecem como atividades do aluno a apresentação e eventuais capturas solicitadas pelo professor; a contabilização final do armazenamento temporário depende da Oracle. Esses limites não são apresentados como testes já executados ou custo total zero.
