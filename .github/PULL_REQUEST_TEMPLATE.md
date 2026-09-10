## Objetivo

Descreva de forma curta o que mudou e por quê.

## Fluxo de promoção

- [ ] `feature/*` ou `bugfix/*` → `dev` (DEV)
- [ ] `release/*` ou `dev` → `hmg` (HMG)
- [ ] `hmg` ou `hotfix/*` → `main` (produção)

## Validação

- [ ] Executei os testes localmente.
- [ ] O build e os testes do GitHub Actions foram aprovados.
- [ ] Não incluí `.env`, credenciais, tokens, chaves ou senhas.
- [ ] Revisei possíveis impactos nas categorias OWASP documentadas.
- [ ] Atualizei a documentação quando necessário.

## Produção

- [ ] Este item não se aplica porque o destino não é `main`.
- [ ] Se o destino é `main`, confirmei que o commit está pronto para publicação automática após o CI.
