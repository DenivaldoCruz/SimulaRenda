# CONTEXT.md — SimulaRenda
> Leia este arquivo inteiro antes de qualquer tarefa. Ele é a fonte de verdade sobre o projeto.

**Versão:** 2.0 · **Atualizado em:** 01/06/2026  
**Stack:** FastAPI + NiceGUI (Python 3.12) · PostgreSQL 16 · Redis 7  
**Não há JavaScript, TypeScript, Node.js ou npm neste projeto.**

---

## 1. O QUE É O SIMULARENDA

SimulaRenda é uma aplicação web de **planejamento de independência financeira** voltada ao mercado brasileiro. O usuário informa sua situação atual (patrimônio, aportes, idade) e suas metas (renda desejada, idade para parar de trabalhar) e a aplicação calcula quanto precisa acumular, quanto tempo levará e como a renda será composta ao longo da vida.

A UI é construída em **Python puro com NiceGUI**. Não há build step, não há `node_modules`, não há TypeScript, não há npm.

### Diferencial central — o gap previdenciário

Três datas são **independentes entre si**:

| Evento | Campo | Regra |
|--------|-------|-------|
| Parar de trabalhar | `retirement_age` | Fim da acumulação, início do usufruto |
| Início do INSS / Regime Próprio | `public_pension.start_age` | ≥ `retirement_age` |
| Início da Previdência Privada | `private_pension.start_age` | ≥ `retirement_age` |

O período entre `retirement_age` e o início do primeiro benefício é o **gap previdenciário**, financiado exclusivamente pelo patrimônio acumulado. Toda lógica de cálculo, UI e comunicação ao usuário deve reforçar esse conceito.

---

## 2. ARQUITETURA — COMO NICEGUI E FASTAPI COEXISTEM

NiceGUI e FastAPI rodam no **mesmo processo Python**, na mesma porta (8000):

```
http://localhost:8000/
  ├── /*          → NiceGUI (páginas Python, reatividade via WebSocket)
  └── /api/v1/*   → FastAPI (REST API JSON)
```

Integração em `backend/app/main.py`:
```python
from nicegui import ui, app as nicegui_app
from app.ui import register_pages

# 1. Registra routers FastAPI normalmente
app.include_router(auth_router, prefix="/api/v1")
app.include_router(simulations_router, prefix="/api/v1")

# 2. Registra páginas NiceGUI
register_pages()

# 3. Monta NiceGUI sobre o app FastAPI (sem porta separada)
ui.run_with(app, mount_path='/', storage_secret=settings.SECRET_KEY,
            title='SimulaRenda', favicon='💰', dark=False)
```

**Consequência importante:** os services (`calculator.py`, `auth_service.py`, `simulation_service.py`) são chamados **diretamente** pelas páginas NiceGUI — sem HTTP interno. A REST API existe para: (a) compartilhamento público, (b) testes automatizados, (c) integrações futuras.

**WebSocket em produção:** o Nginx **obrigatoriamente** precisa de:
```nginx
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```
Sem isso, a reatividade da UI para de funcionar após o carregamento inicial.

---

## 3. ESTRUTURA DO REPOSITÓRIO

```
simularenda/
├── backend/
│   ├── app/
│   │   ├── api/v1/routes/        ← auth.py, simulations.py, users.py (FastAPI REST)
│   │   ├── core/                 ← config.py, security.py, dependencies.py
│   │   ├── db/                   ← session.py, base.py
│   │   ├── models/               ← user.py, simulation.py (SQLAlchemy)
│   │   ├── schemas/              ← Pydantic v2 request/response
│   │   ├── services/
│   │   │   ├── calculator.py     ← ENGINE DE CÁLCULO (arquivo mais crítico do projeto)
│   │   │   ├── auth_service.py
│   │   │   └── simulation_service.py
│   │   ├── ui/                   ← CAMADA NICEGUI (tudo que o usuário vê)
│   │   │   ├── pages/
│   │   │   │   ├── home.py           ← formulário + resultados (página principal)
│   │   │   │   ├── simulations.py    ← histórico e comparação
│   │   │   │   ├── simulation_detail.py
│   │   │   │   ├── shared.py         ← visualização pública read-only
│   │   │   │   ├── login.py
│   │   │   │   └── register.py
│   │   │   ├── components/
│   │   │   │   ├── simulation_form.py     ← formulário completo
│   │   │   │   ├── results_panel.py       ← cards de resultado
│   │   │   │   ├── pension_timeline.py    ← linha do tempo de eventos
│   │   │   │   ├── patrimony_chart.py     ← gráfico Plotly evolução patrimonial
│   │   │   │   ├── income_chart.py        ← gráfico Plotly composição de renda
│   │   │   │   └── simulation_card.py     ← card da lista de simulações
│   │   │   ├── state/
│   │   │   │   └── simulation_state.py    ← estado reativo compartilhado entre componentes
│   │   │   └── __init__.py               ← register_pages()
│   │   └── main.py
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_calculator.py    ← cobertura 100% obrigatória
│   │   ├── test_auth.py
│   │   ├── test_simulations.py
│   │   └── test_models.py
│   ├── alembic/
│   │   └── versions/
│   ├── alembic.ini
│   └── pyproject.toml
├── docker-compose.yml            ← dev (postgres, redis, backend)
├── docker-compose.prod.yml       ← produção (+ nginx)
├── Makefile
├── .env.example
├── CONTEXT.md                    ← este arquivo
└── README.md
```

**Não existe pasta `/frontend`, `/shared` ou qualquer arquivo `.ts`, `.tsx`, `.js`, `package.json` ou `node_modules` neste projeto.**

---

## 4. STACK E VERSÕES

| Dependência | Versão | Uso |
|-------------|--------|-----|
| Python | 3.12 | runtime único |
| FastAPI | latest stable | framework REST API |
| NiceGUI | latest stable | framework UI (Python → browser via WebSocket) |
| SQLAlchemy | 2.x async | ORM |
| asyncpg | latest | driver PostgreSQL async |
| Alembic | latest | migrações de banco |
| Pydantic | v2 | validação e schemas |
| pydantic-settings | v2 | configuração via .env |
| python-jose[cryptography] | latest | JWT |
| passlib[bcrypt] | latest | hash de senhas (cost=12) |
| redis | latest | cache + blocklist de tokens |
| slowapi | latest | rate limiting |
| plotly | latest | gráficos (integrado via `ui.plotly`) |
| reportlab | latest | geração de PDF server-side |
| structlog | latest | logging estruturado JSON |
| httpx | latest | cliente HTTP (Google OAuth + testes) |
| pytest | latest | testes |
| pytest-asyncio | latest | testes async |
| pytest-cov | latest | cobertura (meta: ≥ 80%; `calculator.py`: 100%) |
| Playwright | latest | testes E2E |

**Não há dependências npm, yarn, pnpm ou bun. Não há Vite, Webpack, React, Vue ou similar.**

---

## 5. VARIÁVEIS DE AMBIENTE

Todas no `.env` na raiz do projeto. Nunca hardcodar valores sensíveis.

```env
# Banco de dados
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/simularenda

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT e sessão NiceGUI
SECRET_KEY=          # mínimo 32 chars — gerado com: python -c "import secrets; print(secrets.token_hex(32))"
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Google OAuth
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# NiceGUI
NICEGUI_STORAGE_SECRET=   # pode ser igual ao SECRET_KEY
NICEGUI_HOST=0.0.0.0
NICEGUI_PORT=8000

# Sentry (opcional em dev)
SENTRY_DSN=

# Ambiente
ENVIRONMENT=development   # development | staging | production
```

**Proteção:** scripts destrutivos (`reset_dev.py`) verificam se `DATABASE_URL` contém `localhost` ou `dev` antes de executar.

---

## 6. BANCO DE DADOS — MODELOS E JSONB

### Tabela `users`
```sql
id               UUID PRIMARY KEY DEFAULT gen_random_uuid()
email            VARCHAR(255) UNIQUE NOT NULL
name             VARCHAR(255)
hashed_password  VARCHAR(255)    -- NULL para usuários OAuth
birth_date       DATE
created_at       TIMESTAMPTZ DEFAULT now()
deleted_at       TIMESTAMPTZ     -- soft delete; sempre filtrar WHERE deleted_at IS NULL
```

### Tabela `simulations`
```sql
id           UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id      UUID REFERENCES users(id) ON DELETE SET NULL
name         VARCHAR(255) NOT NULL DEFAULT 'Simulação sem título'
parameters   JSONB NOT NULL
results      JSONB NOT NULL   -- snapshot calculado no momento do save, nunca recalcular no GET
share_token  VARCHAR(64) UNIQUE
is_public    BOOLEAN DEFAULT false
created_at   TIMESTAMPTZ DEFAULT now()
updated_at   TIMESTAMPTZ
```

### Schema exato do JSONB `parameters`
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

### Schema exato do JSONB `results`
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
    {"age": 35, "patrimony": 150000.00, "monthly_income": 0},
    {"age": 36, "patrimony": 198500.00, "monthly_income": 0}
  ],
  "patrimony_exhausted": false,
  "exhaustion_age": null
}
```

---

## 7. ENGINE DE CÁLCULO — REGRAS CRÍTICAS

> **Arquivo:** `backend/app/services/calculator.py`  
> **Cobertura obrigatória: 100%.** Nenhum merge sem testes cobrindo todas as funções e casos de borda.

### Tipos numéricos
- **Sempre `Decimal`** para valores monetários e taxas. Nunca `float`.
- Precisão monetária: 2 casas. Precisão de taxas: 6 casas.

### Fórmulas

```python
# Acumulação
r_mensal = annual_real_return / 12
n = (retirement_age - current_age) * 12
FV = PV * (1 + r_mensal)**n + PMT * ((1 + r_mensal)**n - 1) / r_mensal

# Patrimônio necessário
renda_liquida = desired_monthly_income - sum(b.monthly_amount for b in beneficios_ativos_no_retirement)
P_necessario = renda_liquida * 12 / safe_withdrawal_rate

# Aporte necessário (reverso)
PMT = (P_necessario - PV * (1 + r)**n) * r / ((1 + r)**n - 1)
# Se PV * (1+r)^n >= P_necessario: retornar Decimal(0) — nunca negativo

# Retirada mês a mês
for cada mês m após retirement_age:
    beneficios = sum(b.monthly_amount for b in beneficios com start_age <= idade_em_m)
    retirada = max(Decimal(0), desired_monthly_income - beneficios)
    patrimonio[m] = max(Decimal(0), patrimonio[m-1] * (1 + r_mensal) - retirada)
    if patrimonio[m] == 0: patrimony_exhausted = True; exhaustion_age = idade_em_m; break
```

### Status de viabilidade
| Status | Condição |
|--------|----------|
| `viable` | `projected >= required` |
| `warning` | `projected >= required * Decimal('0.80')` |
| `unviable` | `projected < required * Decimal('0.80')` |

### Invariantes (nunca violar)
- `retirement_age > current_age`
- `life_expectancy > retirement_age`
- `public_pension.start_age >= retirement_age` (se enabled)
- `private_pension.start_age >= retirement_age` (se enabled)
- `required_monthly_contribution >= Decimal(0)`
- Patrimônio na `projection_series` nunca negativo
- `phases` sem lacunas e sem sobreposição de `from_age`/`to_age`

---

## 8. ESTADO REATIVO NO NICEGUI

O estado compartilhado entre componentes vive em `backend/app/ui/state/simulation_state.py`:

```python
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional
from nicegui import ui

@dataclass
class SimulationState:
    # Inputs
    current_age: int = 30
    current_patrimony: Decimal = Decimal('0')
    monthly_contribution: Decimal = Decimal('0')
    desired_monthly_income: Decimal = Decimal('0')
    retirement_age: int = 55
    life_expectancy: int = 90
    inflation_rate: Decimal = Decimal('0.045')
    annual_real_return: Decimal = Decimal('0.06')
    safe_withdrawal_rate: Decimal = Decimal('0.04')
    public_pension_enabled: bool = False
    public_pension_amount: Decimal = Decimal('0')
    public_pension_start_age: int = 65
    private_pension_enabled: bool = False
    private_pension_amount: Decimal = Decimal('0')
    private_pension_start_age: int = 60
    private_pension_modality: str = 'lifetime'
    private_pension_term_years: Optional[int] = None

    # Outputs (preenchidos pelo calculator)
    results: Optional[dict] = None
    is_calculating: bool = False
    is_dirty: bool = False          # True se parâmetros mudaram desde o último save
    saved_simulation_id: Optional[str] = None
    saved_simulation_name: Optional[str] = None
```

**Padrão de atualização:** cada campo de input chama `on_change` que atualiza o estado e dispara `recalculate()`. O recálculo chama `calculator.run_full_simulation()` diretamente (sem HTTP). Componentes de resultado usam `ui.refreshable` decorado para re-renderizar quando `state.results` muda.

**Sessão do usuário:** autenticação e preferências ficam em `app.storage.user` (dicionário por sessão, persistido em cookie seguro pelo NiceGUI). Simulações offline ficam em `app.storage.user['local_simulations']` (lista de dicts, máximo 5).

---

## 9. API REST — CONTRATOS

### Base URL
- Dev: `http://localhost:8000`
- Produção: `https://api.simularenda.com.br`

### Autenticação
- **Access token:** JWT HS256, 15 min, header `Authorization: Bearer <token>`
- **Refresh token:** JWT HS256, 7 dias, enviado no body de `POST /auth/refresh`
- **Blocklist:** Redis com TTL = 7 dias para tokens invalidados

### Endpoints

```
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/google
POST   /api/v1/auth/refresh
POST   /api/v1/auth/logout             (requer JWT)
POST   /api/v1/auth/forgot-password
POST   /api/v1/auth/reset-password

POST   /api/v1/simulations/calculate   (sem persistir; rate limit 30/min por IP)
POST   /api/v1/simulations             (requer JWT; rate limit 20/hora por user)
GET    /api/v1/simulations             (requer JWT; ?page=1&size=10)
GET    /api/v1/simulations/{id}        (requer JWT)
PUT    /api/v1/simulations/{id}        (requer JWT; recalcula se parameters mudou)
DELETE /api/v1/simulations/{id}        (requer JWT)
POST   /api/v1/simulations/{id}/share  (requer JWT; body: {enable: bool})
GET    /api/v1/simulations/shared/{token}  (público)

GET    /api/v1/health
GET    /metrics                        (requer header X-Metrics-Token)
```

### Rate limits
| Rota | Limite |
|------|--------|
| POST /auth/login | 10 req/min por IP |
| POST /auth/register | 5 req/min por IP |
| POST /simulations/calculate | 30 req/min por IP |
| POST /simulations | 20 req/hora por user_id |

---

## 10. COMPONENTES NICEGUI — GUIA RÁPIDO

| Componente NiceGUI | Uso no SimulaRenda |
|--------------------|-------------------|
| `ui.number(prefix='R$')` | Campos monetários |
| `ui.slider` + `ui.number` (bind bidirecional) | Campos de idade |
| `ui.switch` | Toggles de pensão habilitada / "valor em reais de hoje" |
| `ui.select` | Modalidade de previdência privada |
| `ui.expansion` | Seção de parâmetros econômicos colapsável |
| `ui.tooltip` | Explicações de cada campo |
| `ui.plotly` | Gráfico de evolução patrimonial e composição de renda |
| `ui.card` + `ui.card_section` | Cards de resultado e cards de simulação |
| `ui.notify` | Toasts de sucesso/erro |
| `ui.dialog` | Modais de nome de simulação e confirmação de exclusão |
| `ui.refreshable` | Decorator para re-renderizar seções quando o estado muda |
| `ui.linear_progress` | Mini progress bar nas cards de simulação |
| `app.storage.user` | Estado de sessão por usuário (autenticação + offline storage) |

**Padrão de binding reativo:**
```python
# Slider e input sincronizados
slider = ui.slider(min=18, max=80, value=state.current_age)
number = ui.number(value=state.current_age)
slider.bind_value(number, 'value')
number.on('change', lambda e: update_state('current_age', int(e.value)))
```

---

## 11. TESTES — ESTRATÉGIA E COBERTURA

### Backend (pytest + pytest-asyncio)

| Módulo | Cobertura mínima |
|--------|-----------------|
| `services/calculator.py` | **100%** obrigatório |
| `api/v1/routes/*` | 80% |
| `services/auth_service.py` | 80% |
| Geral | 80% |

**Fixtures em `conftest.py`:**
- `async_client` — `AsyncClient` do httpx apontando para a app FastAPI
- `test_db` — banco SQLite em memória para testes isolados
- `user_factory(email, name)` — cria e persiste User no banco de teste
- `simulation_factory(user, **overrides)` — cria Simulation com parâmetros padrão sobrescrevíveis
- `authenticated_client(user)` — `async_client` com JWT válido no header

**Importante:** testes unitários da `calculator.py` são **síncronos** (funções puras com `Decimal`) — não precisam de `pytest-asyncio` nem de banco.

### E2E (Playwright)

Cenários obrigatórios antes de qualquer deploy em produção:
1. Formulário completo → resultados aparecem → salvar em storage local (sem login)
2. Cadastro → migração de simulação local para conta → histórico mostra a simulação
3. Compartilhamento → link abre em aba anônima em modo read-only
4. Comparação de 3 simulações
5. Fluxo completo em viewport mobile (390×844)

---

## 12. SEGURANÇA — REGRAS INVIOLÁVEIS

- Senhas sempre com `bcrypt` cost=12
- `share_token` sempre com `secrets.token_urlsafe(32)` — nunca sequencial
- `SECRET_KEY` mínimo 32 caracteres
- HTTPS obrigatório em produção
- Headers: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` em todas as respostas
- **Dados financeiros nunca em logs** — nem em desenvolvimento
- `user_id` pode aparecer em logs, mas nunca `email`, `name` ou valores monetários
- CORS: apenas origens listadas em `CORS_ORIGINS` no `.env`
- Inputs string: `.strip()` antes de persistir; campo `name` sem HTML tags
- Soft delete: não apagar fisicamente registros de `users` antes dos 30 dias de carência

---

## 13. PERFORMANCE — METAS

| Métrica | Meta |
|---------|------|
| Cálculo síncrono (calculator.py) | < 100ms para 70 anos × 12 meses |
| API `POST /simulations/calculate` | < 300ms P95 |
| Carregamento inicial da UI | < 2s em conexão 4G |
| Lighthouse Performance | ≥ 85 (NiceGUI tem overhead de WebSocket) |

**NiceGUI e performance:** o recálculo acontece no servidor Python e o resultado é enviado via WebSocket para o browser. Para simulações longas (70+ anos), o cálculo é síncrono e rápido o suficiente (< 100ms) para não precisar de threading.

---

## 14. CONVENÇÕES DE CÓDIGO

### Nomenclatura Python
| Tipo | Convenção | Exemplo |
|------|-----------|---------|
| Módulos | snake_case | `simulation_state.py` |
| Classes | PascalCase | `SimulationState`, `User` |
| Funções | snake_case | `run_full_simulation` |
| Constantes | SCREAMING_SNAKE_CASE | `MAX_LOCAL_SIMULATIONS = 5` |
| Schemas Pydantic | PascalCase + sufixo | `SimulationCreate`, `TokenResponse` |

### Git
- Branches: `feature/`, `fix/`, `chore/`, `docs/`
- Commits em inglês, Conventional Commits: `feat:`, `fix:`, `test:`, `chore:`
- PR para `main`: CI verde + aprovação manual
- PR para `develop`: CI verde

### Python
- Type hints em todas as funções públicas
- Docstrings Google style em `calculator.py`
- `Decimal` para todo valor financeiro — **`float` proibido em calculator.py**
- Imports absolutos

---

## 15. FLUXOS CRÍTICOS

### Recálculo em tempo real (NiceGUI)
```
1. Usuário altera campo no formulário
2. Handler on_change atualiza SimulationState
3. recalculate() chamado diretamente (sem HTTP)
4. calculator.run_full_simulation(params) → SimulationResults
5. state.results = results
6. @ui.refreshable nos componentes de resultado re-renderiza automaticamente
```

### Salvar simulação (usuário autenticado)
```
1. Usuário clica "Salvar Simulação"
2. Se state.saved_simulation_name é None → ui.dialog para nomear
3. POST /api/v1/simulations com {name, parameters}
4. Backend recalcula results (nunca confiar nos results do state)
5. Retorna SimulationResponse com id
6. state.is_dirty = False; state.saved_simulation_id = id
7. ui.notify("Simulação salva!", type='positive')
```

### Salvar simulação (usuário não autenticado)
```
1. Usuário clica "Salvar Simulação"
2. len(app.storage.user.get('local_simulations', [])) < 5 → salva localmente
3. ui.notify("Salvo localmente. Crie uma conta para não perder!", type='warning')
4. Se count >= 5 → ui.dialog bloqueante pedindo cadastro ou exclusão
```

### Migração de simulações locais ao login
```
1. login_service.login() bem-sucedido
2. local = app.storage.user.get('local_simulations', [])
3. Para cada simulação local: POST /api/v1/simulations (sequencial, não paralelo)
4. app.storage.user['local_simulations'] = []
5. ui.notify(f"{len(local)} simulações migradas para sua conta")
```

---

## 16. O QUE NÃO FAZER (ANTI-PATTERNS)

- ❌ Criar qualquer arquivo `.js`, `.ts`, `.jsx`, `.tsx`, `package.json`
- ❌ Instalar npm, pnpm, yarn ou qualquer gerenciador JavaScript
- ❌ Usar `float` em cálculos financeiros (usar `Decimal`)
- ❌ Assumir que `retirement_age == public_pension.start_age`
- ❌ Recalcular `results` no GET de simulações (é snapshot imutável)
- ❌ Retornar `required_monthly_contribution` negativo (clamp em 0)
- ❌ Logar dados financeiros ou email do usuário
- ❌ Fazer chamadas HTTP internas entre NiceGUI e FastAPI (chamar os services diretamente)
- ❌ Usar `app.storage.general` para dados de usuário (usar `app.storage.user`)
- ❌ Deploy sem os smoke tests passando
- ❌ Remover suporte a WebSocket no Nginx em produção

---

## 17. DECISÕES DE ARQUITETURA E JUSTIFICATIVAS

| Decisão | Justificativa |
|---------|--------------|
| NiceGUI + FastAPI no mesmo processo | Elimina Node.js/npm; calls diretas ao service layer sem HTTP interno |
| `results` como snapshot JSONB | Mudanças futuras na engine não invalidam simulações históricas |
| Services chamados diretamente pela UI | Sem latência de rede interna; mais simples de testar |
| REST API mantida mesmo com NiceGUI | Necessária para compartilhamento público e testes E2E via httpx |
| `app.storage.user` para offline | Nativo do NiceGUI, sem localStorage JS; migra automaticamente ao login |
| Plotly via `ui.plotly` | Único framework de gráficos integrado nativamente ao NiceGUI |
| reportlab para PDF | Geração 100% server-side em Python puro; sem puppeteer ou headless browser |
| `Decimal` em vez de `float` | Composição de taxas ao longo de décadas acumula erros com float |
| Soft delete em `users` | LGPD exige carência de 30 dias antes da exclusão definitiva |

---

## 18. GLOSSÁRIO DO DOMÍNIO

| Termo | Definição |
|-------|-----------|
| **Gap Previdenciário** | Período entre `retirement_age` e o início do primeiro benefício; coberto só pelo patrimônio |
| **Taxa de Retirada Segura** | `safe_withdrawal_rate`: % retirado anualmente do patrimônio. Padrão: 4% (Regra dos 4%) |
| **Taxa Real de Retorno** | `annual_real_return`: rendimento já descontado a inflação |
| **Snapshot** | Cópia imutável de `parameters` e `results` no momento do save |
| **Fase** | Período entre dois eventos previdenciários com composição de renda fixa |
| **INSS** | Aposentadoria pública de trabalhadores CLT/MEI |
| **RPPS** | Regime Próprio — aposentadoria de servidores públicos |
| **PGBL** | Previdência privada com dedução no IR (declaração completa) |
| **VGBL** | Previdência privada sem dedução no IR (declaração simplificada) |
| **Renda vitalícia** | Benefício pago enquanto o beneficiário viver |
| **Prazo certo** | Benefício pago por `term_years` anos fixos |

---

*Versão 2.0 — Migrado de React/TypeScript/npm para NiceGUI/Python puro em 01/06/2026.*  
*Atualizar este arquivo sempre que: (1) novo campo for adicionado ao schema, (2) regra de negócio mudar, (3) decisão arquitetural for revertida.*