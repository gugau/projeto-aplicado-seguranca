# Cola de gravação — meta: 8 minutos

Use junto do [roteiro completo, com falas e preparação](ROTEIRO-GRAVACAO.md). **Um vídeo de 5 a 10 minutos.** Não mostrar senha, chave, `.env`, cookies completos ou gerenciador de senhas.

| Tempo | Tela / atalho | O que demonstrar |
|---|---|---|
| 0:00–0:35 | Ctrl+1 — aplicação | Nome/curso; IP público; HTTPS; três eixos. |
| 0:35–1:40 | Ctrl+2 — OCI; Alt+Tab — SSH `infra` | Mesma VM/IP; Ubuntu; Nginx; chave, senha/root no; Fail2Ban **4/86.400s**; 22/80/443. |
| 1:40–2:35 | Ctrl+3 — SSL.org; Ctrl+4 — DigiCert; SSH `tls` | Testes já prontos no IP correto; confiança, assinatura/chave e **dois PASS**; Certbot e timer. |
| 2:35–3:45 | Ctrl+1 — aplicação | `/dashboard` sem login → login; uma senha errada; login válido; painel; logout; rota negada outra vez. |
| 3:45–4:25 | Ctrl+5 — GitHub; Ctrl+6 — gitignore | Público; README; exclusão de segredos; IA na escrita e auditoria + testes. |
| 4:25–5:40 | Ctrl+5 — README/OWASP | **A01:** rota protegida. **A02:** configuração/cookies/cabeçalhos. **A07:** hash, tentativas e sessão revogável. |
| 5:40–7:20 | Ctrl+7 — CI; Ctrl+8 — workflow; Ctrl+9 — deploy; SSH `release` | 21 testes; dev/hmg só testam; main publica; Secrets só por nome; run aprovado; SHA corresponde à VM. |
| 7:20–8:00 | Ctrl+1 — aplicação | Fechar o checklist; evidências no repositório; agradecer. |

Antes de gravar: testes externos concluídos; CI/deploy correspondentes abertos; SSH pronto; aplicação desconectada; áudio testado; texto legível. Não executar atualização, rollback, bloqueio por tentativas ou novo push durante a gravação.

**Lembretes de precisão:** 30 min = duração máxima desde o login, não tempo restante. PQC da troca de chaves não é assinatura PQC. Não afirmar “zero custo” nem “imune à OWASP”. SSL.org retornou **Good key**. Repositório com branch padrão dev pode fazer o registro do deploy mostrar dev; o artefato usa o SHA do CI pai da main.

Depois de gravar: 5–10 min; assistir inteiro; YouTube não listado; testar link sem login; conferir as cinco respostas do formulário, e-mail institucional e prazo oficial; enviar uma única vez. A senha vai somente no campo privado do formulário, no formato `usuario;senha`.
