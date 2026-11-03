# Evidências de entrega — 03/11/2026

Aplicação: **https://163.176.111.141**. Repositório: [gugau/projeto-aplicado-seguranca](https://github.com/gugau/projeto-aplicado-seguranca).

Este documento distingue consultas executadas pelo agente, testes feitos pelo aluno no navegador e etapas ainda em validação. Não contém cookies, senhas, chaves privadas ou valores dos GitHub Secrets.

## Infraestrutura observada

| Item | Resultado real |
|---|---|
| Provedor/região | OCI, São Paulo (`sa-saopaulo-1`, home region) |
| VM | Uma A1 Flex, 1 OCPU e 6 GB de RAM |
| Disco | Inicialização de 50 GB; sem disco de dados ou load balancer |
| Sistema | Ubuntu 26.10, `RELEASE_TYPE=stable` |
| Kernel | `7.3.0-9-generic` |
| Python | `3.14.8` |
| OpenSSL | `4.0.3` |
| Nginx | `1.30.4` |
| Certbot | `5.8.0` |
| SSH efetivo | Chave pública habilitada; senha, autenticação interativa e root desabilitados |
| Fail2Ban efetivo | `maxretry=4`, `bantime=86400` segundos |
| UFW | Ativo; entradas 22, 80 e 443; SSH público expressamente autorizado para os runners hospedados |
| Aplicação interna | Gunicorn em `127.0.0.1:8000`, dois workers |
| Deploy | Usuário `deployer`, sem grupo administrativo; sudo restrito a reiniciar/consultar o serviço |

A fingerprint Ed25519 do servidor foi comparada ao console obtido pela API OCI autenticada antes do primeiro SSH. O `known_hosts` resultante foi configurado no GitHub Secret; não foi usado `StrictHostKeyChecking=no`.

## Autenticação e aplicação pela internet

O teste HTTPS externo retornou sucesso para os 11 controles abaixo, sem imprimir senha ou cookie:

- HTTP redireciona para HTTPS.
- Dashboard sem autenticação redireciona para login.
- Página de login disponível.
- Cookie com Secure, HttpOnly e SameSite=Strict.
- Cabeçalhos de segurança presentes.
- Credenciais corretas aceitas.
- Dashboard autenticado acessível.
- Logout funcional.
- Cookie capturado antes do logout rejeitado após a saída.
- Navegador que saiu não acessa a área interna.
- `/healthz` negado externamente com HTTP 403.

Resultado coletado em 03/11/2026, 13:28 UTC. O login usa uma senha aleatória gerada localmente; o Git contém apenas dados sintéticos dos testes. O valor inicial foi entregue em arquivo local protegido, não neste documento.

## HTTPS, renovação e PQC

Certificado Let's Encrypt emitido para SAN IP `163.176.111.141`, emissor `YE1`; cadeia validada por cliente externo. Validade observada: **03/11/2026 12:26:31 UTC a 10/11/2026 04:26:30 UTC**. Essas datas descrevem a emissão observada, não um prazo universal de certificados.

- `certbot renew --dry-run`: todas as renovações simuladas aprovadas.
- Timer `certbot-renew.timer`: ativo, agenda 00/12 UTC com atraso aleatório e execução persistente após indisponibilidade.
- Hook instalado: valida configuração e recarrega Nginx após renovação.
- `deploy/verify-security.sh`: verificações efetivas do servidor aprovadas.
- OpenSSL da VM e cliente externo Debian: TLS 1.3, `TLS_AES_256_GCM_SHA384`, verificação OK e grupo negociado **`X25519MLKEM768`**.

### Verificadores exigidos

| Verificador | Resultado | Origem da evidência |
|---|---|---|
| [SSL.org](https://www.ssl.org/) | Certificate Trusted: Yes; Good signature; Good key; chave EC 256 bits | Consulta real submetida pelo agente; resposta HTML/texto preservada localmente |
| [DigiCert](https://www.digicert.com/pqc-checker) | PASS para TLS 1.3 e quantum-safe key exchange | Executado pelo aluno no navegador; resultado textual fornecido nesta tarefa |

O SSL.org usou o rótulo atual **Good key**, em vez da expressão **Acceptable key** citada no escopo. O resultado positivo é registrado com seu texto real, sem fabricar uma captura ou um rótulo diferente. A consulta automatizada direta ao DigiCert encontrou proteção anti-automação; a evidência do navegador é atribuída ao aluno. O handshake externo independente confirma a negociação híbrida, mas não foi apresentado como captura do DigiCert.

## Testes e GitHub

- Baseline anterior: 10 testes passaram.
- Windows/Python 3.12 após correções: 19 passaram, dois testes Linux ignorados.
- Debian local/Python 3.13: 21 passaram, incluindo ativação e recuperação do script de deploy com serviços simulados.
- CI real do GitHub/Python 3.12: build, 21 testes, varredura heurística de credenciais e auditoria de dependências aprovados.
- Werkzeug 3.1.8 e pytest 8.4.2 tinham alertas de segurança; foram substituídos por 3.1.9 e 9.0.3. A reauditoria e o CI não encontraram vulnerabilidades conhecidas nos respectivos conjuntos examinados.
- `pip check`, compilação Python, parsing YAML e sintaxe Bash aprovados.

Promoções executadas por Pull Request com checks aprovados:

1. [Revisão → dev, PR #6](https://github.com/gugau/projeto-aplicado-seguranca/pull/6).
2. [dev → hmg, PR #7](https://github.com/gugau/projeto-aplicado-seguranca/pull/7).
3. [hmg → main, PR #8](https://github.com/gugau/projeto-aplicado-seguranca/pull/8).

[CI da main aprovado](https://github.com/gugau/projeto-aplicado-seguranca/actions/runs/41636354206).

As três branches estão protegidas: PR obrigatório, check `Build e testes`, conversas resolvidas, proteção aplicada também ao administrador, force push e exclusão proibidos. Como o projeto tem um mantenedor, não foi imposta aprovação de um segundo revisor inexistente. A conta usada é `gugau`, com identidade Git local e configuração CLI isolada da conta profissional.

**Deploy automático:** configuração e Secrets preparados; a execução final do workflow e a comparação do commit servido ainda serão registradas após a promoção desta revisão de infraestrutura.

## Decisões, custos e limites

O catálogo OCI não ofereceu Ubuntu 26.10 para A1; o upgrade oficial da 26.04 retornou “No new release found”. Foi necessário importar a imagem oficial atual, com SHA-256 conferido. A OCI contabilizou cerca de 50 GB para o armazenamento da imagem, acima do tamanho do arquivo/volume virtual. A estimativa inicial foi corrigida; uma primeira importação foi abortada e excluída. A repetição ocorreu após autorização explícita do aluno para até US$ 0,10 temporários. Ambas as imagens e os respectivos buckets foram removidos; a VM 26.04 inicial e seu disco também foram encerrados.

A configuração permanente permanece uma VM A1 pequena e rede mínima, sem LB, NAT gateway, bancos ou containers. A elegibilidade e os limites foram conferidos nas fontes oficiais; o valor efetivo final do consumo temporário ainda depende da contabilização da Oracle. Não se declara custo total zero nem se mistura esse custo com o consumo do ambiente anterior removido.

O servidor e a pipeline ainda exigem manutenção: acompanhar renovação, atualizações, disco, logs e disponibilidade do IP. A apresentação deve incluir as capturas reais que o aluno desejar anexar; nenhum screenshot foi inventado nesta revisão.
