# Roteiro de gravação — Projeto Aplicado

Preparado em 03/11/2026 com base na transcrição fornecida pelo aluno e no [escopo oficial, versão 1.0](https://github.com/ziraldocardoso/Projeto_aplicado-praticas_de_mercado/blob/main/Escopo_e_elementos_obrigatorios.md). A transcrição orienta a apresentação; os requisitos técnicos continuam sendo os do escopo. As falas abaixo são uma adaptação em português, não uma citação literal do professor.

## O que entregar e quanto mostrar

- **Um vídeo de 5 a 10 minutos.** Meta deste roteiro: aproximadamente 8 minutos, incluindo cliques e pequenas pausas. Ensaie com cronômetro; termine antes de 9min30s.
- Apresentação objetiva do checklist, com aplicação, evidências e explicação do aluno. Não é necessário gravar a construção do projeto, editar uma produção elaborada ou criar vários vídeos.
- O professor aceita uma página interna simples com logout. Mantivemos **um painel**, com melhor legibilidade e dados reais do acesso. Gráficos, cadastros, banco, novos dashboards e indicadores fictícios não acrescentam uma exigência da atividade.
- Escolhemos três categorias para explicar em voz alta: **A01, A02 e A07 da OWASP 2025**. O README documenta também A05; não é necessário apresentar as dez categorias. [Lista oficial](https://top10.owasp.org/2025/).
- Repositório público; vídeo no YouTube pode ser **não listado**. Vídeo privado pode impedir a avaliação. Segundo a transcrição, há **uma única submissão**.
- A aula menciona **5 de novembro** como prazo. Confira a data/horário atuais no Moodle e no formulário: a transcrição contém repetições e referências de calendário inconsistentes, e não substitui o aviso oficial vigente.

## Preparação antes de apertar gravar

1. Use o perfil pessoal do navegador. Feche abas profissionais, mensagens, gerenciador de senhas e notificações que possam aparecer na captura.
2. Grave preferencialmente em 1920 × 1080. Se o monitor tiver resolução muito maior, evite capturar a tela inteira com letras minúsculas. Comece com zoom de navegador 110–125% e ajuste olhando uma gravação curta. Terminal com fonte entre 20 e 24 e saída sem rolagem horizontal.
3. Faça um teste de 15 segundos: voz compreensível, texto legível e endereço do navegador visível. Webcam é opcional; não é necessário criar slides.
4. Abra as nove abas na ordem da próxima tabela. Deixe o roteiro em outro monitor ou impresso. Não leia o arquivo de credenciais na tela gravada.
5. Execute **antes** os testes SSL.org e DigiCert para o IP `163.176.111.141`. Deixe os resultados reais abertos com o IP visível. Não reutilize o teste de outro endereço nem troque o teste por um selo escrito na aplicação.
6. Confira o último CI da `main` e o deploy correspondente: ambos precisam estar verdes. Deixe os detalhes dos jobs abertos nas abas 7 e 9. O histórico inclui uma tentativa que falhou e recuperou a versão anterior; selecione a execução aprovada para demonstrar a entrega atual.
7. Entre na VM por SSH antes da gravação e execute a consulta `infra` descrita adiante. Abra uma segunda aba de terminal para `tls` e uma terceira para `release`, se isso facilitar. Mantenha a conexão identificada como remota.
8. Deixe a aplicação **desconectada**. Tenha a senha disponível fora da área gravada. No formulário de login, mantenha o campo de senha mascarado; desative visualização da senha e feche sugestões do gerenciador.
9. Não abra Network/Form Data, cookies completos, `.env`, GitHub Secrets ou chaves privadas durante o vídeo. Para demonstrar os Secrets, basta explicar seu uso e mostrar os nomes referenciados no workflow.
10. Faça apenas **uma tentativa inválida** no login. Não teste bloqueio por força bruta nem banimento do seu próprio SSH durante a apresentação.

## Abas abertas na ordem

| Atalho | Aba | Preparação |
|---|---|---|
| Ctrl+1 | [Aplicação](https://163.176.111.141/login) | Desconectada; barra de endereços visível. |
| Ctrl+2 | [Console OCI](https://cloud.oracle.com/) | Região São Paulo; detalhes da VM `projeto-aplicado-prod`, IP e recursos visíveis. Evite páginas de faturamento/dados pessoais. |
| Ctrl+3 | [SSL.org](https://www.ssl.org/) | Resultado concluído para o IP, com confiança, assinatura e chave visíveis. |
| Ctrl+4 | [DigiCert](https://www.digicert.com/pqc-checker) | Resultado concluído para o IP, mostrando os dois PASS. |
| Ctrl+5 | [Repositório e README na main](https://github.com/gugau/projeto-aplicado-seguranca/tree/main) | Comece no topo para mostrar acesso público; depois role até OWASP ou use Ctrl+F. |
| Ctrl+6 | [.gitignore](https://github.com/gugau/projeto-aplicado-seguranca/blob/main/.gitignore) | Mostrar `.env`, chaves, credenciais OCI e `.cache` ignorados. |
| Ctrl+7 | [CI](https://github.com/gugau/projeto-aplicado-seguranca/actions/workflows/ci.yml) | Abra o último run aprovado por push em `main`, com os 21 testes e auditoria. |
| Ctrl+8 | [Workflow de deploy](https://github.com/gugau/projeto-aplicado-seguranca/blob/main/.github/workflows/deploy.yml) | Condições de main/CI, environment e referências a Secrets visíveis. |
| Ctrl+9 | [Deploy](https://github.com/gugau/projeto-aplicado-seguranca/actions/workflows/deploy.yml) | Abra o run aprovado correspondente ao CI da aba 7; mostrar envio/ativação concluídos. |

Com exatamente nove abas, Ctrl+9 seleciona a última. **Alt+Tab** alterna para o terminal SSH; confira a janela de destino antes de gravar. O roteiro volta à aba 1 para o login; não é necessário seguir a ordem numérica sem retornar.

### Terminal preparado, sem expor segredos

Se já estiver conectado por SSH, use essa sessão. Para conectar a partir do PowerShell, na pasta local do projeto:

```powershell
& 'C:\Program Files\Git\usr\bin\ssh.exe' -i '.cache/oci-keys/projeto_admin_ed25519' -o 'UserKnownHostsFile=.cache/oci-auth/production-known-hosts' -o StrictHostKeyChecking=yes -o IdentitiesOnly=yes ubuntu@163.176.111.141
```

O caminho é da chave local; não mostre seu conteúdo. Não aceite uma chave de host diferente sem conferi-la pelo console OCI. Estabeleça a conexão **antes** de gravar; limpe a tela depois.

Já dentro da VM, deixe as consultas abaixo preparadas. Elas apenas consultam estado e não leem senhas/chaves:

```bash
# Tela 1: SO, Nginx, SSH, Fail2Ban e firewall
sudo bash /opt/projeto-aplicado/current/deploy/presentation.sh infra

# Tela 2: Certbot, timer e handshake local complementar
sudo bash /opt/projeto-aplicado/current/deploy/presentation.sh tls 163.176.111.141

# Tela 3: versão em uso, serviço e saúde
sudo bash /opt/projeto-aplicado/current/deploy/presentation.sh release
```

O script só estará na VM após a publicação desta revisão. A duração real de uma renovação não deve consumir o vídeo. Se quiser atualizar a evidência, execute **antes**, não no trecho cronometrado:

```bash
sudo certbot renew --dry-run --run-deploy-hooks
```

Só diga que o novo ensaio passou se ele realmente concluir com sucesso. Se não o repetir, descreva o ensaio já documentado e mostre o timer atual; não afirme ter executado um novo teste.

## Roteiro falado e ações — aproximadamente 8 minutos

As falas podem ser lidas ou adaptadas ao seu jeito. Substitua `[seu nome completo]` antes de ensaiar. Use as frases de transição para evitar narrar cada clique.

### 0:00–0:35 — apresentação e aplicação online

**Tela:** aba 1. Comece pela página de login. Para mostrar o redirecionamento sem interferência do HSTS salvo, use a evidência HTTP de uma consulta prévia; o navegador pode trocar para HTTPS por conta própria. Se quiser mostrar na barra, digite `http://163.176.111.141` e aponte o endereço final, sem chamar isso de prova isolada do 301.

**Fala:**

> Olá, meu nome é [seu nome completo], sou aluno da pós-graduação em Segurança da Informação e Análise Forense. Vou apresentar meu Projeto Aplicado: Práticas de Mercado, seguindo o checklist da atividade. A solução reúne uma aplicação web, um repositório público no GitHub e uma máquina virtual na Oracle Cloud, integrados por uma pipeline automática. A aplicação está acessível neste IP público, por HTTPS. Vou mostrar o funcionamento e as evidências de cada parte.

**Transição:** “Começando pela infraestrutura que atende esse endereço.”

### 0:35–1:40 — OCI, SSH, Fail2Ban e firewall

**Tela:** aba 2, depois Alt+Tab para a consulta `infra`. Aponte o IP na OCI e compare com o do navegador. No terminal, mostre os valores efetivos, sem abrir arquivos privados.

**Fala:**

> Esta é a VM do projeto na Oracle Cloud, na região de São Paulo. O IP público é o mesmo usado na aplicação. O ambiente utiliza Ubuntu 26.10, Nginx e uma VM A1 com um OCPU, seis gigabytes de memória e cinquenta gigabytes de disco. Mantive uma única VM de produção, sem banco de dados ou load balancer.
>
> Agora estou na sessão SSH dessa máquina. O acesso usa chave: senha, autenticação interativa e login de root estão desabilitados. O Fail2Ban protege a porta SSH com quatro falhas e banimento por 86.400 segundos, que equivalem a 24 horas. O firewall permite 22, 80 e 443; a aplicação interna fica em loopback. A porta 22 atende também ao deploy dos runners do GitHub, com chave dedicada e usuário de implantação restrito.

**Se precisar reduzir:** não leia todas as linhas do firewall; aponte os números. Não faça o teste de quatro falhas na gravação.

### 1:40–2:35 — HTTPS, renovação e PQC

**Tela:** abas 3 e 4, com resultados prontos. Mostre rapidamente a consulta `tls` no terminal para Certbot/timer. O handshake local é um complemento, não um substituto dos testes externos.

**Fala:**

> Como escolhi acesso por IP, utilizei os dois verificadores previstos no escopo. No SSL.org, este resultado corresponde ao IP do projeto: o certificado é confiável e os resultados de assinatura e chave são positivos. A interface retornou “Good key”; registrei o rótulo real, que difere da expressão “Acceptable key” usada no documento.
>
> No DigiCert, os dois itens estão como PASS: TLS 1.3 e troca de chaves resistente a ameaças quânticas. O handshake independente negociou o grupo híbrido X25519MLKEM768. Isso é troca de chaves, não uma afirmação de que a assinatura do certificado seja pós-quântica.
>
> O certificado é da Let's Encrypt, emitido com Certbot 5.8. O timer de renovação está ativo, e o ensaio de renovação foi validado conforme o relatório. O servidor também redireciona HTTP para HTTPS.

**Transição:** “Com a conexão demonstrada, vou testar o acesso à aplicação.”

### 2:35–3:45 — login, página interna e logout

**Tela/ações, na aba 1:**

1. Digite `/dashboard` na barra, sem estar conectado: retorna ao login.
2. Faça uma tentativa com senha errada: mostre a mensagem genérica.
3. Entre com a credencial correta, sem exibir a senha.
4. Mostre o painel: usuário atual, duração máxima da sessão e conexão HTTPS. Não chame o valor de “tempo restante”.
5. Clique **Sair da conta**. Digite `/dashboard` novamente e confirme o retorno ao login.

**Fala:**

> Primeiro tento acessar diretamente a página interna sem login. O servidor me redireciona para a autenticação. Com uma senha incorreta, a mensagem é genérica, sem confirmar se o usuário existe. Agora faço o login com a credencial válida.
>
> Esta é a página interna exigida na atividade. Ela mostra a conta conectada, a duração máxima da sessão configurada e a conexão atual. Os trinta minutos são o limite a partir do login, não um contador de tempo restante. Mantive o protótipo simples, com o botão de logout sempre visível.
>
> Ao sair, o acesso é encerrado. Tento a mesma rota novamente e volto ao login. Os testes também verificam que reapresentar um cookie capturado antes do logout não recupera a sessão.

**Se aparecer uma sessão antiga:** saia antes e repita apenas este bloco. Evite usar o botão Voltar como única comprovação: faça nova requisição digitando a rota.

### 3:45–4:25 — GitHub público, gitignore e IA

**Tela:** aba 5 no topo, aba 6, depois retorne à 5. Antes de gravar, confira o repositório numa janela anônima para comprovar acesso público. Não é necessário exibir a janela anônima durante todo o vídeo.

**Fala:**

> O código está neste repositório público da minha conta pessoal. O README é o relatório técnico e descreve arquitetura, execução, segurança e evidências. O gitignore exclui arquivos de ambiente, chaves privadas e credenciais da nuvem; a pipeline também faz uma varredura do código e do histórico por padrões de credenciais.
>
> Utilizei o Codex como ambiente assistido por inteligência artificial para desenvolver e auditar o código. As sugestões foram conferidas com testes e execução real; por exemplo, a revisão identificou a reutilização de sessão após logout, que foi corrigida e recebeu teste de regressão.

**Não mostrar:** histórico completo do chat, porque contém aprovações e dados de acesso. O relato e os arquivos/testes são suficientes; se quiser mostrar a IDE, abra somente o código ou um trecho sem informações privadas.

### 4:25–5:40 — três mitigações OWASP 2025

**Tela:** aba 5, seção OWASP do README. Deixe os títulos e referências aos arquivos visíveis. Não abra três arquivos durante a gravação se isso prejudicar o ritmo; as referências já estão no relatório.

**Fala:**

> Vou destacar três categorias da OWASP Top 10 de 2025. A primeira é A01, falhas de controle de acesso. A rota interna exige uma sessão válida no servidor, implementada no decorador de proteção e aplicada às rotas. O acesso direto que demonstrei e os testes comprovam esse comportamento.
>
> A segunda é A02, configuração incorreta de segurança. A aplicação exige configuração segura para iniciar, usa cookies protegidos, cabeçalhos de segurança e mensagens de erro genéricas. Na infraestrutura, o processo da aplicação escuta somente na interface local, atrás do Nginx.
>
> A terceira é A07, falhas de autenticação. A senha é armazenada como hash scrypt, há limitação de tentativas e a sessão possui expiração e revogação no logout. O README aponta os arquivos e os testes de cada controle. Essas são mitigações verificadas; não estou afirmando que o sistema elimina todos os riscos dessas categorias.

**Apoio para perguntas:** A01 → `app/security.py` e `app/auth.py`; A02 → `app/__init__.py`, `app/security.py` e `deploy/`; A07 → `app/auth.py`, `app/sessions.py` e `tests/test_auth.py`. A05 permanece documentada como controle adicional, sem precisar alongar o vídeo.

### 5:40–7:20 — CI/CD real, Secrets e versão na VM

**Tela:** aba 7, aba 8, aba 9; termine no terminal com a consulta `release`. Selecione o CI do push main e o deploy correspondente, não apenas um check de PR.

**Fala:**

> Aqui está uma execução aprovada do CI: o build, os 21 testes, a verificação de credenciais e a auditoria de dependências passaram. O fluxo de trabalho utiliza dev, hmg e main, com promoções por Pull Request e checks obrigatórios. Dev e hmg executam build e testes, sem publicar.
>
> Neste arquivo está o deploy. Ele só continua depois de um CI aprovado originado por push na main do próprio repositório. Usa o environment production e os Secrets para conectar com a chave dedicada; a identidade SSH do servidor é verificada. A pipeline envia o artefato do commit testado, instala uma nova versão, ativa o serviço e verifica sua saúde.
>
> Esta é a execução real de implantação aprovada. O commit usado no checkout é o mesmo que aparece no caminho da versão ativa na VM, e o serviço responde à consulta local de saúde. A pipeline foi testada também em falha: restaurou a versão anterior e manteve o retorno de erro. O deploy envolve reinício do serviço; não estou apresentando uma solução sem interrupção.

**Atenção:** o workflow é disparado por `workflow_run` e pode aparecer associado a `dev`, que é a branch padrão. Para demonstrar a origem correta, mostre a condição `head_branch == 'main'`, o CI pai e o SHA usado no checkout/artefato; não confunda o SHA da configuração padrão com o SHA efetivamente implantado.

**Não faça ao vivo:** criar um commit apenas para preencher tempo, abrir Secrets, executar rollback ou interromper o serviço. Mostrar a execução real já concluída e sua versão na VM evita espera e não simula uma publicação.

### 7:20–8:00 — conclusão

**Tela:** volte à aplicação e, se houver tempo, à seção de evidências do README. Pode encerrar no login após logout.

**Fala:**

> Com isso, demonstrei os três eixos do projeto: infraestrutura Linux na Oracle, código público e versionado no GitHub e aplicação com login, área interna e logout. Mostrei HTTPS, os testes externos com PQC, proteção do SSH, três mitigações OWASP e a implantação automática da versão aprovada.
>
> As evidências e os limites estão documentados no repositório. Mantive o escopo simples e validei o funcionamento, em vez de acrescentar funcionalidades que não fazem parte da atividade. Obrigado.

Se estiver próximo de dez minutos, reduza a conclusão a duas frases. Não acelere a ponto de perder clareza. Se ficar abaixo de cinco minutos, aprofunde a explicação das três mitigações e da correspondência entre CI, SHA e VM — não preencha com espera de testes.

## Respostas do formulário — conferir fora da gravação

Segundo a transcrição, são cinco perguntas técnicas, além da identificação do aluno:

| Campo | Resposta / cuidado |
|---|---|
| Identificação | Seu nome completo e **e-mail institucional**, mesmo que acesse o formulário com outra conta. |
| 1. Endereço da aplicação | `https://163.176.111.141/login` — informe um endereço, não uma lista de IP e domínio. |
| 2. Credencial | `admin;SUA_SENHA_ATUAL` — usuário seguido de ponto e vírgula e da senha real da aplicação. Substitua o marcador **somente no formulário privado**; a senha está no campo `password` do arquivo local `.cache/oci-auth/application-credentials.json`. Não coloque essa resposta no Git, no vídeo ou na descrição do YouTube. Não são credenciais da OCI/GitHub. |
| 3. Repositório | `https://github.com/gugau/projeto-aplicado-seguranca` — não colocar o endereço da aplicação neste campo. |
| 4. IP e provedor | `163.176.111.141 [Oracle Cloud Infrastructure (OCI)]` — IP da VM que realmente hospeda a aplicação. |
| 5. Vídeo | Link compartilhável do **vídeo completo**, com 5–10 minutos, após enviar ao YouTube como não listado. O link ainda depende da sua gravação e publicação. |

Antes de **enviar uma única vez**: assista ao vídeo inteiro; abra o link do vídeo em janela anônima; teste o login usando exatamente a resposta do campo 2; abra o repositório sem autenticar; confira o IP na OCI e o prazo no Moodle. Mantenha a VM, o repositório e o vídeo disponíveis durante a avaliação. Se trocar a senha após preencher o formulário, a credencial entregue deixará de funcionar.

## O que não precisa acrescentar

Outros dashboards, gráficos sem dados reais, novo banco, novo domínio, containers, uma tela pública de administração, gravação longa da instalação, prova de força bruta ao vivo e edição elaborada não são necessários. O professor valoriza o checklist demonstrado e a explicação do aluno. Os controles técnicos e os resultados detalhados continuam na [matriz](REVISAO-TECNICA.md) e nas [evidências](EVIDENCIAS-ENTREGA.md).
