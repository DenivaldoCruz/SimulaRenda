# CONTEXT.md — SimulaRenda
> Leia este arquivo inteiro antes de qualquer tarefa. Ele é a fonte de verdade sobre o projeto.

**Versão do contexto:** 1.1 · **Atualizado em:** 02/06/2026
**Stack principal:** FastAPI (Python 3.12) + NiceGUI (Python 3.12) + PostgreSQL 16 + Redis 7

---

## 1. O QUE É O SIMULARENDA

SimulaRenda é uma aplicação web de **planejamento de independência financeira** voltada ao mercado brasileiro. O usuário informa sua situação atual (patrimônio, aportes, idade) e suas metas (renda desejada, idade para parar de trabalhar) e a aplicação calcula quanto precisa acumular, quanto tempo levará e como a renda será composta ao longo da vida.

### Diferencial central — o gap previdenciário

A maioria das calculadoras trata "aposentar" como um único evento. No SimulaRenda, três datas são **independentes entre si**:

| Evento | Campo | Regra |
|--------|-------|-------|
| Parar de trabalhar | `retirement_age` | Fim da acumulação, início do usufruto |
| Início do INSS / Regime Próprio | `public_pension.start_age` | ≥ `retirement_age` |
| Início da Previdência Privada | `private_pension.start_age` | ≥ `retirement_age` |

O período entre `retirement_age` e o início do primeiro benefício previdenciário é chamado de **gap previdenciário** e é financiado exclusivamente pelo patrimônio acumulado. **Toda lógica de cálculo, UI e comunicação ao usuário deve reforçar esse conceito.**

---

## 2. ESTRUTURA DO REPOSITÓRIO

```
simularenda/                        ← raiz do monorepo
├── frontend/                       ← NiceGUI + Python 3.12
│   ├── app/                        ← aplicação NiceGUI, formatação e cliente HTTP
│   │   ├── main.py                 ← tela principal e chamada à API de cálculo
│   │   └── formatting.py           ← helpers de moeda e taxas pt-BR
│   ├── tests/                      ← testes pytest do frontend
│   ├── pyproject.toml              ← dependências Python do frontend
│   └── Dockerfile                  ← serviço NiceGUI em :5173
├── backend/
│   └── app/
│       ├── api/v1/routes/          ← auth.py, simulations.py, users.py
│       ├── core/                   ← config.py, security.py, dependencies.py
│       ├── db/                     ← session.py, base.py
│       ├── models/                 ← user.py, simulation.py (SQLAlchemy)
│       ├── schemas/                ← Pydantic v2 request/response
│       ├── services/
│       │   ├── calculator.py       ← ENGINE DE CÁLCULO (arquivo mais crítico)
│       │   └── auth_service.py
│       └── tests/
├── shared/                         ← documentação de contratos compartilhados
├── docker-compose.yml              ← dev
├── docker-compose.prod.yml         ← produção
└── Makefile
```

---

## 3. STACK E VERSÕES EXATAS

### Backend
| Dependência | Versão | Uso |
|-------------|--------|-----|
| Python | 3.12 | runtime |
| FastAPI | latest stable | framework web |
| SQLAlchemy | 2.x async | ORM |
| asyncpg | latest | driver PostgreSQL async |
| Alembic | latest | migrações |
| Pydantic | v2 | validação/schemas |
| pydantic-settings | v2 | configuração via .env |
| python-jose[cryptography] | latest | JWT |
| passlib[bcrypt] | latest | hash de senhas (cost=12) |
| redis | latest | cache + blocklist de tokens |
| slowapi | latest | rate limiting |
| structlog | latest | logging estruturado JSON |
| pytest + pytest-asyncio | latest | testes |
| pytest-cov | latest | cobertura (meta: ≥ 80%, calculator.py: 100%) |

### Frontend
| Dependência | Versão | Uso |
|-------------|--------|-----|
| Python | 3.12 | runtime do frontend |
| NiceGUI | latest stable | UI web declarativa em Python |
| httpx | latest | HTTP client assíncrono para chamar a API FastAPI |
| pytest | latest | testes unitários do frontend |

**Importante:** o projeto não usa mais Node.js, npm, React, Vite ou pacotes TypeScript no frontend.

### Infra
| Serviço | Versão | Uso |
|---------|--------|-----|
| PostgreSQL | 16 | banco principal |
| Redis | 7 | cache + token blocklist |
| Docker + Docker Compose | latest | containerização |
| GitHub Actions | — | CI/CD |
| Nginx | alpine | reverse proxy em produção |

---

## 4. VARIÁVEIS DE AMBIENTE

Todas as variáveis vivem no `.env` na raiz. Nunca hardcode valores sensíveis.

```env
# Banco de dados
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/simularenda

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=                        # mínimo 32 caracteres, gerado com secrets.token_hex(32)
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Google OAuth
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# CORS (lista separada por vírgula)
CORS_ORIGINS=http://localhost:5173,https://simularenda.com.br
BACKEND_API_URL=http://localhost:8000/api/v1      # usado pelo frontend NiceGUI

# Sentry (opcional em dev)
SENTRY_DSN=

# Ambiente
ENVIRONMENT=development            # development | staging | production
```

**Proteção:** `reset_dev.py` e scripts destrutivos verificam se `DATABASE_URL` contém `localhost` ou `dev` antes de executar.

---

## 5. BANCO DE DADOS — MODELOS E JSONB

### Tabela `users`
```sql
id            UUID PRIMARY KEY DEFAULT gen_random_uuid()
email         VARCHAR(255) UNIQUE NOT NULL
name          VARCHAR(255)
hashed_password VARCHAR(255)       -- NULL para usuários OAuth
birth_date    DATE
created_at    TIMESTAMPTZ DEFAULT now()
deleted_at    TIMESTAMPTZ          -- soft delete; filtre WHERE deleted_at IS NULL
```

### Tabela `simulations`
```sql
id            UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id       UUID REFERENCES users(id) ON DELETE SET NULL
name          VARCHAR(255) NOT NULL DEFAULT 'Simulação sem título'
parameters    JSONB NOT NULL
results       JSONB NOT NULL
share_token   VARCHAR(64) UNIQUE   -- gerado com secrets.token_urlsafe(32)
is_public     BOOLEAN DEFAULT false
created_at    TIMESTAMPTZ DEFAULT now()
updated_at    TIMESTAMPTZ
```

### Schema do JSONB `parameters` (fonte de verdade)
```json
{
  "current_age": 35,
  "current_patrimony": 150000.00,
  "monthly_contribution": 3000.00,
  "desired_monthly_income": 10000.00,
  "retirement_age": 55,
  "life_expectancy": 90,
  "inflation_rate": 0.045,
  "annual_real_return": 0.06,
  "safe_withdrawal_rate": 0.04,
  "public_pension": {
    "enabled": true,
    "monthly_amount": 2500.00,
    "start_age": 65,
    "amount_in_today_reais": true
  },
  "private_pension": {
    "enabled": true,
    "monthly_amount": 3000.00,
    "start_age": 60,
    "modality": "lifetime",
    "term_years": null,
    "amount_in_today_reais": true
  }
}
```

### Schema do JSONB `results` (fonte de verdade)
```json
{
  "required_patrimony": 1500000.00,
  "projected_patrimony": 1250000.00,
  "required_monthly_contribution": 3800.00,
  "feasibility_status": "warning",
  "patrimony_gap": 250000.00,
  "phases": [
    {
      "from_age": 55,
      "to_age": 60,
      "monthly_withdrawal_from_patrimony": 10000.00,
      "monthly_income_total": 10000.00,
      "sources": ["patrimony"]
    },
    {
      "from_age": 60,
      "to_age": 65,
      "monthly_withdrawal_from_patrimony": 7000.00,
      "monthly_income_total": 10000.00,
      "sources": ["patrimony", "private_pension"]
    },
    {
      "from_age": 65,
      "to_age": 90,
      "monthly_withdrawal_from_patrimony": 4500.00,
      "monthly_income_total": 10000.00,
      "sources": ["patrimony", "public_pension", "private_pension"]
    }
  ],
  "projection_series": [
    { "age": 35, "patrimony": 150000.00, "monthly_income": 0 },
    { "age": 36, "patrimony": 198500.00, "monthly_income": 0 }
  ],
  "patrimony_exhausted": false,
  "exhaustion_age": null
}
```

---

## 6. ENGINE DE CÁLCULO — REGRAS CRÍTICAS

> Arquivo: `backend/app/services/calculator.py`  
> **Este é o arquivo mais sensível do projeto. Toda alteração exige atualização dos testes.**

### Tipos numéricos
- **Sempre use `Decimal`**, nunca `float`, para valores monetários e taxas.
- Precisão monetária: 2 casas decimais.
- Precisão de taxas: 6 casas decimais.

### Fórmulas

**Valor Futuro (acumulação)**
```
FV = PV × (1 + r_mensal)^n + PMT × ((1 + r_mensal)^n − 1) / r_mensal
```
- `r_mensal = annual_real_return / 12`
- `n = (retirement_age − current_age) × 12`

**Patrimônio Necessário**
```
P_necessário = renda_líquida_mensal × 12 / safe_withdrawal_rate
renda_líquida_mensal = desired_monthly_income − Σ(benefícios ativos no retirement_age + 1)
```
Benefício só é "ativo" se `start_age <= retirement_age + 1`. Geralmente nenhum está ativo logo no início.

**Aporte Necessário (cálculo reverso)**
```
PMT = (P_necessário − PV × (1 + r)^n) × r / ((1 + r)^n − 1)
```
Se `PV × (1 + r)^n >= P_necessário`, retornar `Decimal(0)` — nunca negativo.

**Simulação mês a mês (fase de retirada)**
```
Para cada mês m após retirement_age:
  benefícios_ativos = soma dos benefícios com start_age <= idade_atual(m)
  retirada = max(0, desired_monthly_income − benefícios_ativos)
  patrimônio[m] = patrimônio[m−1] × (1 + r_mensal) − retirada
  se patrimônio[m] < 0: marcar patrimony_exhausted=True, registrar exhaustion_age, zerar
```

### Correção por inflação
- Todos os valores inseridos são assumidos como **reais de hoje** (se `amount_in_today_reais=true`).
- A `projection_series` reporta valores nominais (corrigidos).
- `annual_real_return` já é a taxa real — não subtrair inflação novamente.

### Status de viabilidade
| Status | Condição |
|--------|----------|
| `viable` | `projected_patrimony >= required_patrimony` |
| `warning` | `projected_patrimony >= required_patrimony × 0.80` |
| `unviable` | `projected_patrimony < required_patrimony × 0.80` |

### Invariantes (nunca violar)
- `retirement_age > current_age`
- `life_expectancy > retirement_age`
- `public_pension.start_age >= retirement_age` (se habilitada)
- `private_pension.start_age >= retirement_age` (se habilitada)
- Patrimônio nunca negativo na `projection_series` (clamp em 0)
- `phases` sem lacunas e sem sobreposições de `from_age`/`to_age`
- `required_monthly_contribution` nunca negativo

---

## 7. API — CONTRATOS E AUTENTICAÇÃO

### Base URL
- Dev: `http://localhost:8000`
- Produção: `https://api.simularenda.com.br`
- Prefixo: `/api/v1`

### Autenticação
- **Access token:** JWT HS256, expiração 15 min, enviado no header `Authorization: Bearer <token>`
- **Refresh token:** JWT HS256, expiração 7 dias, enviado no body de `POST /auth/refresh`
- **Blocklist:** refresh tokens invalidados ficam no Redis com TTL = 7 dias
- **Google OAuth:** troca `code` por token Google no backend; nunca expor client_secret no frontend

### Endpoints principais

```
# Autenticação
POST   /api/v1/auth/register          # { email, password, name? } → TokenResponse
POST   /api/v1/auth/login             # { email, password } → TokenResponse
POST   /api/v1/auth/google            # { code, redirect_uri } → TokenResponse
POST   /api/v1/auth/refresh           # { refresh_token } → TokenResponse
POST   /api/v1/auth/logout            # Authorization header → 204
POST   /api/v1/auth/forgot-password   # { email } → 204
POST   /api/v1/auth/reset-password    # { token, new_password } → 204

# Simulações
POST   /api/v1/simulations/calculate  # SimulationParameters → SimulationResults (sem persistir)
POST   /api/v1/simulations            # SimulationCreate → SimulationResponse 201
GET    /api/v1/simulations            # ?page=1&size=10 → PaginatedResponse[SimulationListItem]
GET    /api/v1/simulations/{id}       # → SimulationResponse
PUT    /api/v1/simulations/{id}       # { name?, parameters? } → SimulationResponse
DELETE /api/v1/simulations/{id}       # → 204
POST   /api/v1/simulations/{id}/share # { enable: bool } → { share_token, share_url }
GET    /api/v1/simulations/shared/{token} # público → SimulationResponse

# Saúde
GET    /api/v1/health                 # → { status, database, redis, version }
GET    /metrics                       # Prometheus (requer X-Metrics-Token)
```

### Rate limits
| Rota | Limite |
|------|--------|
| POST /auth/login | 10 req/min por IP |
| POST /auth/register | 5 req/min por IP |
| POST /simulations/calculate | 30 req/min por IP |
| POST /simulations | 20 req/hora por user_id |

### Respostas de erro padrão
```json
{ "detail": "mensagem de erro" }
```
Códigos: 400 (bad request), 401 (não autenticado), 403 (sem permissão), 404 (não encontrado), 409 (conflito), 422 (validação Pydantic), 429 (rate limit), 500 (erro interno)

---

## 8. FRONTEND — NICEGUI E FLUXO DE DADOS

### Serviço NiceGUI

- Arquivo principal: `frontend/app/main.py`
- Porta dev: `http://localhost:5173`
- O frontend chama a API FastAPI usando `BACKEND_API_URL` (padrão local: `http://localhost:8000/api/v1`; Docker: `http://backend:8000/api/v1`).
- Não há build npm: desenvolvimento, testes e Docker usam apenas Python.

### Fluxo de cálculo (NiceGUI → API)

```
1. Usuário preenche o formulário NiceGUI na página `/`
2. O handler do botão monta `SimulationParameters` com strings decimais para valores financeiros e taxas
3. Frontend faz POST `${BACKEND_API_URL}/simulations/calculate` com `httpx.AsyncClient`
4. API valida com Pydantic → chama calculator.run_full_simulation()
5. NiceGUI renderiza cards, tabela de fases e gráfico de patrimônio
6. Erros HTTP/validação aparecem em banner acessível na própria tela
```

### Persistência e autenticação

O MVP NiceGUI atual prioriza a simulação sem login. Fluxos autenticados, armazenamento offline e migração de simulações devem ser reimplementados em Python/NiceGUI antes de serem considerados disponíveis.

## 9. COMPONENTES UI — GUIA RÁPIDO

A UI é construída com componentes NiceGUI (`ui.number`, `ui.checkbox`, `ui.select`, `ui.table`, `ui.echart`, `ui.banner`, `ui.card`).

**Regras de estilo:**
- Preferir classes utilitárias suportadas pelo NiceGUI/Quasar para layout e espaçamento.
- Textos visíveis no MVP ficam em pt-BR diretamente no frontend Python até a futura camada i18n server-side.
- Campos obrigatórios devem usar labels explícitos e `aria-required=true`.
- Tabelas e gráficos devem conter labels/captions suficientes para explicar o gap previdenciário.

## 10. TESTES — ESTRATÉGIA E COBERTURA

### Backend (pytest)
| Módulo | Cobertura mínima | Observação |
|--------|-----------------|------------|
| `services/calculator.py` | **100%** | Crítico — nenhum merge sem 100% |
| `api/v1/routes/*` | 80% | Cobrir happy path + erros comuns |
| `services/auth_service.py` | 80% | Cobrir todos os fluxos de auth |
| Geral | 80% | Falha o CI se abaixo |

**Fixtures disponíveis em `conftest.py`:**
- `async_client` — `AsyncClient` do httpx com app montada
- `test_db` — banco SQLite em memória
- `user_factory(email, name)` — cria e persiste User
- `simulation_factory(user, **overrides)` — cria Simulation com parâmetros padrão sobrescrevíveis
- `authenticated_client(user)` — `async_client` com Authorization header

### Frontend (pytest)
| Módulo | Cobertura mínima |
|--------|-----------------|
| `app/formatting.py` | 80% |
| `app/main.py` helpers não-UI | 70% |

**Padrão de testes:**
- Testar helpers Python com `pytest`.
- Para chamadas à API, preferir testes com `httpx.MockTransport` ou fixtures assíncronas; não há axios/msw.
- Validar que taxas exibidas em percentual são enviadas à API como decimal (`4.5` → `0.045`).

### E2E / smoke browser
Cenários obrigatórios antes de deploy em produção quando houver suíte browser configurada para NiceGUI:
1. Fluxo completo sem login (preencher formulário → calcular → visualizar fases)
2. Tratamento de erro de validação da API
3. Gráfico e tabela de fases renderizados após cálculo
4. Fluxo completo em viewport mobile (390×844)

---

## 11. SEGURANÇA — REGRAS INVIOLÁVEIS

- Senhas sempre com `bcrypt` cost=12 — nunca MD5, SHA1 ou sem hash
- Tokens JWT com `HS256` usando `SECRET_KEY` de pelo menos 32 caracteres
- `share_token` sempre gerado com `secrets.token_urlsafe(32)` — nunca sequencial ou previsível
- HTTPS obrigatório em produção — redirecionar HTTP → HTTPS no Nginx
- Headers de segurança em todas as respostas: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`
- Dados financeiros do usuário **nunca** em logs (nem em desenvolvimento)
- `user_id` pode aparecer em logs, mas nunca `email`, `name` ou qualquer dado financeiro
- CORS: apenas origens explicitamente listadas em `CORS_ORIGINS`
- Inputs string sempre com `.strip()` antes de persistir; `name` da simulação sem HTML tags (sanitizar)
- Soft delete em `users`: nunca apagar fisicamente registros de usuário antes dos 30 dias de carência

---

## 12. PERFORMANCE — METAS E ESTRATÉGIAS

| Métrica | Meta |
|---------|------|
| API `POST /simulations/calculate` | < 300ms P95 |
| Renderização pós-cálculo no NiceGUI | < 500ms após resposta da API |
| Lighthouse Performance | ≥ 90 |
| Lighthouse Acessibilidade | ≥ 90 |

**Estratégias obrigatórias:**
- Manter cálculo financeiro centralizado no backend; frontend NiceGUI não deve duplicar a engine.
- Reutilizar helpers de formatação e evitar recriar estruturas grandes desnecessariamente em handlers.
- Gráficos devem renderizar apenas a série anual retornada pela API, não iterações mês a mês extras.
- Chamadas HTTP do frontend devem usar timeout explícito.

## 13. ACESSIBILIDADE — REGRAS OBRIGATÓRIAS

- WCAG 2.1 nível AA em todos os componentes
- Todos os campos de entrada NiceGUI devem ter label visível
- `aria-required="true"` em campos obrigatórios
- Erros de validação devem aparecer em banner perceptível e com semântica de alerta quando possível
- Gráficos devem ter `aria-label` descrevendo a série exibida
- Tabelas de fases devem expor colunas claras para período, retirada, renda e fontes
- Outline de foco nunca removido sem substituto visual equivalente
- Fluxos mobile devem ser validados em viewport estreita antes de deploy

## 14. INTERNACIONALIZAÇÃO

- Idioma único no MVP: **pt-BR**
- Textos visíveis do frontend NiceGUI ficam em pt-BR; se um segundo idioma for adicionado, criar camada i18n Python antes de novas strings
- Formatação monetária: helpers Python devem exibir `R$`, separador de milhar `.` e centavos com `,`
- Taxas exibidas ao usuário são percentuais, mas enviadas à API como decimal

## 15. CONVENÇÕES DE CÓDIGO

### Nomenclatura
| Tipo | Convenção | Exemplo |
|------|-----------|---------|
| Funções Python | snake_case | `format_brl`, `to_decimal_string` |
| Constantes | SCREAMING_SNAKE_CASE | `BACKEND_API_URL` |
| Arquivos Python | snake_case | `auth_service.py` |
| Modelos SQLAlchemy | PascalCase | `User`, `Simulation` |
| Schemas Pydantic | PascalCase com sufixo | `SimulationCreate`, `TokenResponse` |

### Git
- Branches: `feature/`, `fix/`, `chore/`, `docs/`
- Commits em inglês, formato Conventional Commits: `feat:`, `fix:`, `test:`, `chore:`, `docs:`
- PR para `main` requer: CI verde + aprovação manual (deploy de produção)
- PR para `develop` requer: CI verde

### Python
- Type hints em todas as funções públicas
- Docstrings em Google style para funções da `calculator.py`
- `Decimal` para todo valor financeiro — proibido `float` na calculator
- Imports absolutos (nunca relativos implícitos)

### Frontend Python / NiceGUI
- Type hints em helpers públicos do frontend
- Não adicionar dependências npm; o frontend deve permanecer 100% Python
- Manter conversões monetárias e taxas em strings decimais antes de enviar para a API
- Componentes NiceGUI devem reforçar visualmente o gap previdenciário

---

## 16. FLUXOS CRÍTICOS — PASSO A PASSO

### Fluxo de Cálculo (frontend NiceGUI → API)
```
1. Usuário altera campos no formulário NiceGUI
2. Usuário clica "Calcular independência financeira"
3. Handler monta payload no contrato `SimulationParameters`
4. POST /api/v1/simulations/calculate com strings decimais para dinheiro/taxas
5. API valida com Pydantic → chama calculator.run_full_simulation()
6. Retorna SimulationResults
7. NiceGUI renderiza cards, tabela de fases e gráfico
```

### Fluxos de persistência e autenticação no NiceGUI

Os endpoints de autenticação e persistência seguem disponíveis na API, mas a implementação NiceGUI atual entrega apenas o cálculo sem login. Antes de reativar salvar/listar/compartilhar no frontend, implementar esses fluxos em Python/NiceGUI respeitando os contratos da seção 7.

---

## 17. O QUE NÃO FAZER (ANTI-PATTERNS)

- ❌ Usar `float` em cálculos financeiros (use `Decimal`)
- ❌ Assumir que `retirement_age` == `public_pension.start_age` (eles são independentes)
- ❌ Recalcular na rota GET — resultados são sempre salvos como snapshot no `results` JSONB
- ❌ Retornar `required_monthly_contribution` negativo (clamp em 0)
- ❌ Logar dados financeiros do usuário
- ❌ Adicionar JSX/React/Vite ou dependências npm ao frontend
- ❌ Chamar a engine de cálculo diretamente no frontend; a UI NiceGUI deve usar a API FastAPI
- ❌ Reintroduzir axios/msw; testes do frontend devem usar ferramentas Python
- ❌ Fazer deploy em produção sem os smoke tests passando
- ❌ Adicionar dependência npm; o projeto não deve depender de Node.js/npm

---

## 18. DECISÕES DE ARQUITETURA E JUSTIFICATIVAS

| Decisão | Justificativa |
|---------|--------------|
| `results` persiste como snapshot JSONB | Se a engine de cálculo mudar, simulações históricas preservam os resultados originais. Não recalcular on-the-fly. |
| Cálculo centralizado na API | A engine crítica permanece no backend FastAPI e o frontend NiceGUI envia payloads validados para `/simulations/calculate`. |
| NiceGUI no frontend | Remove a dependência de Node.js/npm e mantém a aplicação full Python no MVP. |
| Soft delete em `users` | LGPD exige carência de 30 dias antes da exclusão definitiva. |
| `share_token` no modelo `Simulation` | Compartilhamento granular por simulação, não por usuário. Revogável individualmente. |
| `Decimal` com precisão 6 em taxas | Taxas como 4.5% a.a. precisam de precisão para composição ao longo de décadas sem erro acumulado. |

---

## 19. GLOSSÁRIO DO DOMÍNIO

| Termo | Definição no contexto do SimulaRenda |
|-------|--------------------------------------|
| **Independência Financeira** | Condição em que o patrimônio gera renda suficiente sem trabalho ativo |
| **Gap Previdenciário** | Período entre `retirement_age` e o início do primeiro benefício previdenciário |
| **Taxa de Retirada Segura** | `safe_withdrawal_rate`: % do patrimônio retirado anualmente. Padrão: 4% (Regra dos 4%) |
| **Taxa Real de Retorno** | `annual_real_return`: rendimento já descontado a inflação |
| **Fase** | Período entre dois eventos previdenciários com composição de renda fixa |
| **Snapshot** | Cópia imutável dos `parameters` e `results` no momento do salvamento |
| **INSS** | Instituto Nacional do Seguro Social — aposentadoria pública do trabalhador CLT/MEI |
| **RPPS** | Regime Próprio de Previdência Social — aposentadoria de servidores públicos |
| **PGBL** | Previdência privada com dedução no IR (indicado para declaração completa) |
| **VGBL** | Previdência privada sem dedução no IR (indicado para declaração simplificada) |
| **Renda vitalícia** | Modalidade em que a seguradora paga enquanto o beneficiário viver |
| **Prazo certo** | Modalidade em que a seguradora paga por `term_years` anos fixos |
| **Patrimônio Projetado** | `projected_patrimony`: FV calculado ao atingir `retirement_age` |
| **Patrimônio Necessário** | `required_patrimony`: valor mínimo para sustentar `desired_monthly_income` até `life_expectancy` |

---

*Este arquivo deve ser atualizado sempre que: (1) um novo campo for adicionado ao schema, (2) uma regra de negócio mudar, (3) uma decisão arquitetural for revertida. Nunca deixe este arquivo desatualizado em relação ao código.*
