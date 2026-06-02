# SimulaRenda — Prompts para ChatGPT Codex
**Aplicação:** Simulador de Renda Passiva com Calculadora de Aposentadoria  
**Stack:** React 18 + TypeScript + Vite (frontend) · FastAPI + Python 3.12 (backend) · PostgreSQL 16 · Redis  
**Metodologia:** TDD — escreva os testes antes da implementação em cada prompt  
**Total:** 48 prompts organizados em 5 fases

---

## FASE 1 — Setup e Infraestrutura (Prompts 1–8)

---

### Prompt 01 — Inicialização do Monorepo

```
Crie a estrutura de um monorepo para o projeto SimulaRenda com as seguintes pastas:
- /frontend  (React 18 + TypeScript + Vite)
- /backend   (FastAPI + Python 3.12)
- /shared    (tipos TypeScript compartilhados)

Na raiz, crie:
- README.md com descrição do projeto e instruções de setup
- .gitignore cobrindo Node, Python, .env e artefatos de build
- docker-compose.yml com serviços: postgres (v16), redis (v7), backend e frontend
- .env.example com as variáveis: DATABASE_URL, REDIS_URL, SECRET_KEY, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, CORS_ORIGINS

No /frontend, inicialize com: npm create vite@latest -- --template react-ts
Instale as dependências: tailwindcss, @tailwindcss/vite, zustand, recharts, react-hook-form, zod, @hookform/resolvers, axios, react-router-dom, lucide-react

No /backend, crie pyproject.toml com dependências: fastapi, uvicorn[standard], sqlalchemy[asyncio], asyncpg, alembic, pydantic[email], pydantic-settings, python-jose[cryptography], passlib[bcrypt], redis, httpx, pytest, pytest-asyncio, httpx (para testes)

Crie Makefile na raiz com targets: install, dev, test, lint, build, migrate
```

---

### Prompt 02 — Configuração do Backend FastAPI

```
No /backend do projeto SimulaRenda, configure a aplicação FastAPI com:

1. Estrutura de pastas:
   /backend
     /app
       /api/v1/routes/       (auth.py, simulations.py, users.py)
       /core/                (config.py, security.py, dependencies.py)
       /db/                  (session.py, base.py)
       /models/              (user.py, simulation.py)
       /schemas/             (user.py, simulation.py, auth.py)
       /services/            (auth_service.py, simulation_service.py, calculator.py)
       /tests/               (conftest.py, test_auth.py, test_simulations.py, test_calculator.py)
       main.py
     alembic.ini
     /alembic/versions/

2. Em app/core/config.py: classe Settings usando pydantic-settings lendo do .env as variáveis: DATABASE_URL, REDIS_URL, SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES=15, REFRESH_TOKEN_EXPIRE_DAYS=7, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, CORS_ORIGINS

3. Em main.py: instância FastAPI com CORS configurado via settings.CORS_ORIGINS, inclusão dos routers com prefixo /api/v1, e lifespan gerenciando conexão com DB e Redis

4. Em app/db/session.py: async engine com asyncpg e AsyncSession factory

5. Em app/core/dependencies.py: funções get_db (AsyncSession), get_current_user (valida JWT e retorna User)

Escreva primeiro os testes em /tests/conftest.py com fixtures: async_client (AsyncClient do httpx), test_db (banco SQLite em memória para testes)
```

---

### Prompt 03 — Modelos de Banco de Dados e Migrações

```
No /backend/app/models do SimulaRenda, crie os modelos SQLAlchemy com mapeamento declarativo async:

1. user.py — modelo User:
   - id: UUID primary key (default uuid4)
   - email: String(255) unique not null
   - name: String(255) nullable
   - hashed_password: String nullable (nullable para OAuth)
   - birth_date: Date nullable
   - created_at: DateTime com default utcnow
   - deleted_at: DateTime nullable (soft delete)
   - Relacionamento: simulations (one-to-many)

2. simulation.py — modelo Simulation:
   - id: UUID primary key
   - user_id: UUID FK users.id nullable (simulations anônimas via token)
   - name: String(255) default 'Simulação sem título'
   - parameters: JSONB not null
   - results: JSONB not null
   - share_token: String(64) unique nullable
   - is_public: Boolean default False
   - created_at: DateTime
   - updated_at: DateTime com onupdate

A estrutura exata do JSONB parameters deve validar:
{
  current_age, current_patrimony, monthly_contribution,
  desired_monthly_income, retirement_age, life_expectancy,
  inflation_rate, annual_real_return, safe_withdrawal_rate,
  public_pension: { enabled, monthly_amount?, start_age?, amount_in_today_reais? },
  private_pension: { enabled, monthly_amount?, start_age?, modality?, term_years?, amount_in_today_reais? }
}

Crie a migração Alembic inicial: alembic revision --autogenerate -m "create_users_and_simulations"

Escreva testes em test_models.py verificando: criação de User, criação de Simulation vinculada a User, soft delete de User não apaga Simulations (SET NULL), constraint unique em share_token
```

---

### Prompt 04 — Schemas Pydantic (Request/Response)

```
No /backend/app/schemas do SimulaRenda, crie os schemas Pydantic v2:

1. auth.py:
   - RegisterRequest: email (EmailStr), password (str, min 8 chars), name (str opcional)
   - LoginRequest: email, password
   - TokenResponse: access_token, refresh_token, token_type="bearer"
   - GoogleAuthRequest: code (str), redirect_uri (str)

2. simulation.py:
   - PublicPensionInput: enabled (bool), monthly_amount (Decimal opcional), start_age (int opcional, 18–80), amount_in_today_reais (bool default True)
   - PrivatePensionInput: enabled (bool), monthly_amount (Decimal opcional), start_age (int opcional), modality (Enum: lifetime|fixed_term|lump_sum), term_years (int opcional), amount_in_today_reais (bool default True)
   - SimulationParameters: current_age (int 18–80), current_patrimony (Decimal ≥ 0), monthly_contribution (Decimal > 0), desired_monthly_income (Decimal > 0), retirement_age (int, deve ser > current_age), life_expectancy (int, deve ser > retirement_age), inflation_rate (Decimal 0–0.20 default 0.045), annual_real_return (Decimal 0–0.30 default 0.06), safe_withdrawal_rate (Decimal 0.01–0.10 default 0.04), public_pension (PublicPensionInput), private_pension (PrivatePensionInput)
   - Validadores customizados (@model_validator): retirement_age > current_age; life_expectancy > retirement_age; se pensão habilitada, start_age >= retirement_age
   - PhaseResult: from_age, to_age, monthly_withdrawal_from_patrimony, monthly_income_total, sources (list[str])
   - ProjectionPoint: age (int), patrimony (Decimal), monthly_income (Decimal)
   - SimulationResults: required_patrimony, projected_patrimony, required_monthly_contribution, feasibility_status (Enum: viable|warning|unviable), patrimony_gap, phases (list[PhaseResult]), projection_series (list[ProjectionPoint])
   - SimulationCreate: name (str), parameters (SimulationParameters)
   - SimulationResponse: id, name, parameters, results, created_at, share_token, is_public
   - SimulationListItem: id, name, feasibility_status, required_patrimony, projected_patrimony, created_at

Escreva testes unitários para todos os validadores customizados nos schemas
```

---

### Prompt 05 — Engine de Cálculo (TDD Completo)

```
No /backend/app/services/calculator.py do SimulaRenda, implemente a engine de cálculo financeiro.

ESCREVA OS TESTES PRIMEIRO em /tests/test_calculator.py cobrindo TODOS os cenários abaixo antes de implementar o código.

Funções a implementar:

1. calculate_future_value(pv, pmt, annual_rate, months) -> Decimal
   Fórmula: FV = PV*(1+r)^n + PMT*((1+r)^n - 1)/r
   Teste: pv=150000, pmt=3000, annual_rate=0.06, months=240 → validar contra planilha de referência

2. calculate_required_patrimony(desired_income, safe_withdrawal_rate, active_pensions_income) -> Decimal
   Fórmula: (desired_income - active_pensions_income) * 12 / safe_withdrawal_rate
   Teste: desired_income=10000, rate=0.04, pensions=2500 → 2.250.000

3. calculate_required_contribution(target_patrimony, current_patrimony, annual_rate, months) -> Decimal
   Fórmula reversa do FV resolvendo para PMT
   Teste: se já tem mais que o necessário → retorna 0

4. adjust_for_inflation(value, inflation_rate, years) -> Decimal
   Fórmula: value * (1 + inflation_rate)^years

5. simulate_phases(params: SimulationParameters) -> list[PhaseResult]
   Regras:
   - Fase 1: retirement_age até min(public_pension.start_age, private_pension.start_age) se habilitados
   - Fases intermediárias: cada vez que um benefício começa, nova fase
   - Fase final: todos os benefícios ativos até life_expectancy
   - Cada fase retorna from_age, to_age, monthly_withdrawal_from_patrimony, sources

6. simulate_projection(params: SimulationParameters) -> tuple[list[ProjectionPoint], bool]
   Simula mês a mês: acumulação até retirement_age, retiradas após
   Retorna série de pontos (age, patrimony) e flag patrimony_exhausted
   Teste: patrimônio não deve zerar se plano for viável

7. run_full_simulation(params: SimulationParameters) -> SimulationResults
   Orquestra todas as funções acima e determina feasibility_status:
   - viable: projected >= required
   - warning: projected >= required * 0.80
   - unviable: projected < required * 0.80

Todos os cálculos devem usar Decimal com precisão de 2 casas para valores monetários e 6 para taxas. Sem usar float para evitar erros de precisão.
```

---

### Prompt 06 — Autenticação JWT e Google OAuth

```
No /backend/app do SimulaRenda, implemente autenticação completa:

1. app/core/security.py:
   - hash_password(plain: str) -> str usando bcrypt cost=12
   - verify_password(plain: str, hashed: str) -> bool
   - create_access_token(user_id: UUID) -> str (JWT HS256, exp=15min)
   - create_refresh_token(user_id: UUID) -> str (JWT HS256, exp=7dias)
   - decode_token(token: str) -> dict (lança HTTPException 401 se inválido/expirado)

2. app/services/auth_service.py:
   - register(db, data: RegisterRequest) -> User (verifica email único, faz hash da senha)
   - login(db, data: LoginRequest) -> TokenResponse (verifica credenciais, gera par de tokens)
   - google_auth(db, code: str, redirect_uri: str) -> TokenResponse (troca code por token Google, obtém perfil, upsert User sem senha)
   - refresh_token(db, refresh_token: str) -> TokenResponse (valida refresh, gera novo par)
   - logout(redis, refresh_token: str) -> None (adiciona token a blocklist no Redis com TTL=7dias)

3. app/api/v1/routes/auth.py:
   - POST /register → RegisterRequest → TokenResponse
   - POST /login → LoginRequest → TokenResponse
   - POST /google → GoogleAuthRequest → TokenResponse
   - POST /refresh → body {refresh_token} → TokenResponse
   - POST /logout → header Authorization → 204

Escreva testes em test_auth.py:
- Registro com email duplicado retorna 409
- Login com senha errada retorna 401
- Token expirado retorna 401
- Logout invalida token (segundo uso retorna 401)
- Fluxo Google OAuth mockado com httpx_mock
```

---

### Prompt 07 — CRUD de Simulações (API)

```
No /backend/app/api/v1/routes/simulations.py do SimulaRenda, implemente os endpoints REST:

POST /simulations/calculate
- Não requer autenticação
- Body: SimulationParameters
- Retorna: SimulationResults (calculado na hora, não persiste)
- Rate limit: 30 req/min por IP (via Redis)

POST /simulations
- Requer autenticação (get_current_user)
- Body: SimulationCreate {name, parameters}
- Calcula results via calculator.run_full_simulation
- Persiste no banco
- Retorna: SimulationResponse 201

GET /simulations
- Requer autenticação
- Query params: page=1, size=10, order_by=created_at|name
- Retorna: PaginatedResponse[SimulationListItem]
- Filtra por user_id do token, exclui deleted

GET /simulations/{id}
- Requer autenticação
- Retorna: SimulationResponse completo
- 404 se não pertencer ao usuário

PUT /simulations/{id}
- Requer autenticação
- Body: {name?: str, parameters?: SimulationParameters}
- Se parameters mudou, recalcula results
- Retorna: SimulationResponse atualizado

DELETE /simulations/{id}
- Requer autenticação
- Hard delete
- Retorna 204

POST /simulations/{id}/share
- Requer autenticação
- Body: {enable: bool}
- Se enable=true: gera share_token (secrets.token_urlsafe(32)) e is_public=true
- Se enable=false: limpa share_token e is_public=false
- Retorna: {share_token: str | null, share_url: str | null}

GET /simulations/shared/{token}
- Sem autenticação
- Retorna: SimulationResponse (read-only)
- 404 se token inválido ou is_public=false

Escreva testes de integração em test_simulations.py para todos os endpoints incluindo casos de erro e autorização
```

---

### Prompt 08 — Setup do Frontend React

```
No /frontend do SimulaRenda, configure a aplicação React com:

1. Configuração Tailwind CSS v4 no vite.config.ts com @tailwindcss/vite

2. Paleta de cores no CSS global (index.css) usando variáveis CSS:
   --color-primary: #0F766E (teal-700)
   --color-primary-light: #14B8A6 (teal-500)
   --color-success: #16A34A
   --color-warning: #D97706
   --color-danger: #DC2626
   --color-bg: #F8FAFC
   --color-surface: #FFFFFF
   --color-text: #0F172A
   --color-muted: #64748B

3. React Router v6 com as rotas:
   / → HomePage (simulador principal)
   /minhas-simulacoes → SimulationsPage (requer auth)
   /simulacao/:id → SimulationDetailPage (requer auth)
   /compartilhado/:token → SharedSimulationPage (público)
   /entrar → LoginPage
   /cadastrar → RegisterPage

4. Zustand stores:
   - useAuthStore: { user, accessToken, setAuth, clearAuth, isAuthenticated }
   - useSimulationStore: { parameters, results, isDirty, setParameters, setResults, resetForm }

5. Configuração do axios em /src/lib/api.ts:
   - baseURL do .env
   - interceptor de request: adiciona Authorization header se token presente
   - interceptor de response: se 401, tenta refresh token; se falhar, chama clearAuth e redireciona para /entrar

6. Componente ProtectedRoute que redireciona para /entrar se não autenticado

Crie testes com Vitest + Testing Library para: useAuthStore (set/clear), axios interceptors (mock com msw), ProtectedRoute (redireciona sem auth, renderiza com auth)
```

---

## FASE 2 — Formulário de Simulação (Prompts 9–18)

---

### Prompt 09 — Componente: CurrencyInput

```
No /frontend/src/components/ui do SimulaRenda, crie o componente CurrencyInput:

Props:
- name: string
- label: string
- value: number
- onChange: (value: number) => void
- min?: number (default 0)
- max?: number
- placeholder?: string
- hint?: string (texto de ajuda abaixo do campo)
- error?: string
- disabled?: boolean

Comportamento:
- Exibe valor formatado como moeda brasileira: R$ 1.234,56
- Ao digitar, aceita apenas dígitos; formata em tempo real da direita para esquerda (como caixa registradora)
- Valor interno é sempre number (centavos / 100)
- Ao perder foco, garante formatação correta
- Se value=0, exibe placeholder ao invés de R$ 0,00

Estilo:
- Input com borda arredondada, foco com ring teal
- Label acima, hint e error abaixo em texto menor
- Ícone R$ à esquerda como prefix visual (não editável)

Escreva testes:
- Renderiza com label e hint
- Formata R$ 1.234,56 corretamente
- Chama onChange com valor numérico correto
- Exibe mensagem de erro
- Não permite valor negativo quando min=0
```

---

### Prompt 10 — Componente: SliderInput

```
No /frontend/src/components/ui do SimulaRenda, crie o componente SliderInput:

Props:
- name: string
- label: string
- value: number
- onChange: (value: number) => void
- min: number
- max: number
- step?: number (default 1)
- unit?: string (ex: "anos", "%")
- hint?: string
- error?: string
- marks?: Array<{value: number, label: string}> (pontos de referência no slider)

Comportamento:
- Slider HTML nativo estilizado com Tailwind + CSS custom para thumb e track
- Input numérico ao lado direito, sincronizado bidirecionalmente com o slider
- Ao digitar no input, valida range e atualiza slider
- Marks renderizados abaixo do slider com linha pontilhada

Estilo:
- Track: bg-slate-200, parte preenchida bg-teal-500
- Thumb: círculo branco com sombra e borda teal
- Input numérico: pequeno, alinhado à direita, sufixo com unit

Escreva testes:
- Sincronização slider ↔ input
- Clamp de valores fora do range
- Renderização de marks
- Disparo correto do onChange
```

---

### Prompt 11 — Componente: PercentageInput

```
No /frontend/src/components/ui do SimulaRenda, crie o componente PercentageInput:

Props:
- name: string
- label: string
- value: number (0 a 1, ex: 0.045 para 4,5%)
- onChange: (value: number) => void
- min?: number (default 0)
- max?: number (default 1)
- step?: number (default 0.001)
- hint?: string
- error?: string
- benchmark?: string (ex: "Selic atual: 10,5% a.a." exibido como referência)

Comportamento:
- Exibe e recebe valor como percentual (ex: 4,50%)
- Internamente converte para decimal ao chamar onChange
- Aceita digitação com vírgula ou ponto como separador decimal
- Sufixo "% a.a." não editável

Estilo:
- Benchmark exibido em badge verde claro abaixo do campo
- Mesma identidade visual dos demais inputs

Escreva testes cobrindo conversão decimal ↔ percentual e exibição do benchmark
```

---

### Prompt 12 — Componente: TooltipInfo

```
No /frontend/src/components/ui do SimulaRenda, crie o componente TooltipInfo:

Props:
- content: string | React.ReactNode
- position?: 'top' | 'right' | 'bottom' | 'left' (default 'top')
- maxWidth?: number (default 280px)

Comportamento:
- Ícone de interrogação (lucide-react: HelpCircle) que ao hover/focus exibe tooltip
- Tooltip com animação fade-in (CSS transition opacity)
- Acessível: role="tooltip", aria-describedby no elemento-alvo
- Fecha ao pressionar Escape
- Em mobile: abre modal bottom-sheet ao invés de tooltip (breakpoint < 640px)

Uso pretendido: colocado ao lado de labels de campos complexos como "Taxa de Retirada Segura"

Escreva testes:
- Tooltip aparece no hover
- Tooltip fecha no Escape
- Conteúdo está acessível via aria
```

---

### Prompt 13 — Seção: Situação Atual do Formulário

```
No /frontend/src/features/simulation/components do SimulaRenda, crie o componente CurrentSituationSection:

Campos a renderizar (usando componentes CurrencyInput, SliderInput, TooltipInfo):
1. Patrimônio atual investido (R$) — CurrencyInput, min=0
2. Aporte mensal (R$) — CurrencyInput, min=0
3. Idade atual (anos) — SliderInput, min=18, max=70

Tooltips:
- Patrimônio: "Some todos os seus investimentos: CDB, fundos, ações, previdência privada, etc. Não inclua imóveis para moradia."
- Aporte mensal: "Quanto você consegue investir todo mês. Inclua aportes em previdência privada."

Estado: lê e escreve em useSimulationStore via react-hook-form + zod
Schema zod para esta seção:
- current_patrimony: z.number().min(0)
- monthly_contribution: z.number().min(1, "Informe um aporte maior que zero")
- current_age: z.number().int().min(18).max(70)

Escreva testes:
- Renderiza todos os campos
- Erro de validação aparece ao submeter vazio
- Valores são gravados no store ao mudar
```

---

### Prompt 14 — Seção: Metas de Independência

```
No /frontend/src/features/simulation/components do SimulaRenda, crie o componente IndependenceGoalsSection:

Campos:
1. Renda mensal desejada na independência (R$) — CurrencyInput, min=100
   Tooltip: "Valor em reais de hoje. O simulador corrige pela inflação automaticamente."
2. Idade para parar de trabalhar (anos) — SliderInput, min=current_age+1, max=80
   Tooltip: "Esta é a idade em que você planeja parar de trabalhar ativamente. Pode ser diferente da idade em que começará a receber INSS ou previdência privada."
   Marks: [{ value: 55, label: "55" }, { value: 60, label: "60" }, { value: 65, label: "65" }]
3. Expectativa de vida (anos) — SliderInput, min=retirement_age+1, max=110, default=90
   Tooltip: "Use 90 como referência conservadora. Para maior segurança, use 95 ou 100."

Comportamento especial:
- Quando "idade para parar de trabalhar" muda, garante que expectativa de vida > novo valor
- Exibe badge informativo: "Você terá X anos de aposentadoria" (life_expectancy - retirement_age)

Validação zod:
- desired_monthly_income: z.number().min(100)
- retirement_age: z.number().refine(val => val > current_age, "Deve ser maior que sua idade atual")
- life_expectancy: z.number().refine(val => val > retirement_age, "Deve ser maior que a idade de parar de trabalhar")

Escreva testes para a lógica do badge e do ajuste automático da expectativa de vida
```

---

### Prompt 15 — Seção: Aposentadoria Pública (INSS / RPPS)

```
No /frontend/src/features/simulation/components do SimulaRenda, crie o componente PublicPensionSection:

Estrutura:
- Toggle "Vou receber aposentadoria pública (INSS ou Regime Próprio)" (expandido/colapsado com animação)
- Quando habilitado, exibe os campos abaixo

Campos (quando habilitado):
1. Valor estimado do benefício (R$) — CurrencyInput
   Tooltip: "Consulte o extrato no Meu INSS (meu.inss.gov.br) para estimar sua aposentadoria. Use o valor em reais de hoje."
2. Idade de início do recebimento — SliderInput, min=retirement_age, max=80
   Tooltip: "Pode ser igual ou posterior à idade de parar de trabalhar. O período entre as duas idades será coberto exclusivamente pelo seu patrimônio acumulado."
   Destaque visual: se start_age > retirement_age, exibe alerta amarelo:
   "⚠️ Gap de X anos sem este benefício. Seu patrimônio precisará cobrir R$ Y/mês neste período."
3. Toggle "O valor informado já está em reais de hoje?" (default: Sim)

Validação zod:
- monthly_amount: z.number().min(1).optional()
- start_age: z.number().min(retirement_age, "Não pode ser antes de parar de trabalhar")

Escreva testes para: toggle expand/collapse, cálculo e exibição do alerta de gap, validação de start_age < retirement_age
```

---

### Prompt 16 — Seção: Previdência Privada

```
No /frontend/src/features/simulation/components do SimulaRenda, crie o componente PrivatePensionSection:

Estrutura análoga ao PublicPensionSection com toggle de habilitação.

Campos (quando habilitado):
1. Valor mensal esperado do benefício (R$) — CurrencyInput
   Tooltip: "Consulte sua seguradora ou banco. Use o valor em reais de hoje ou o projetado?"
2. Idade de início do recebimento — SliderInput, min=retirement_age, max=80
   Mesmo alerta de gap do PublicPensionSection
3. Modalidade — Select com opções:
   - "Renda Vitalícia" (value: lifetime) — Tooltip: "Você recebe até falecer. Sem herança."
   - "Prazo Certo" (value: fixed_term) — Tooltip: "Você define quantos anos receberá."
   - "Pagamento Único" (value: lump_sum) — Tooltip: "Recebe tudo de uma vez e gerencia você mesmo."
4. Prazo (anos) — NumberInput, visível apenas se modalidade = fixed_term, min=1, max=40
5. Toggle "O valor já está em reais de hoje?" (default: Sim)

Comportamento adicional:
- Se ambas as pensões estiverem habilitadas e tiverem start_age diferentes, exibir mini-timeline abaixo da seção mostrando as duas datas e o gap

Escreva testes para: visibilidade condicional do campo de prazo, mini-timeline com duas pensões, alerta de gap individual por pensão
```

---

### Prompt 17 — Seção: Parâmetros Econômicos (Colapsável)

```
No /frontend/src/features/simulation/components do SimulaRenda, crie o componente EconomicParametersSection:

Seção colapsada por padrão com cabeçalho "⚙️ Parâmetros econômicos avançados" e botão expand.
Ao expandir com animação suave (max-height transition).

Campos:
1. Inflação anual projetada — PercentageInput, default=4.5%, min=0%, max=20%
   Benchmark: "Meta do Banco Central: 3,0% para 2026"
   Tooltip: "Taxa de inflação esperada ao ano. Usada para corrigir o poder de compra da sua renda futura."

2. Rendimento anual real — PercentageInput, default=6.0%, min=0%, max=30%
   Benchmark: "Tesouro IPCA+ 2035: ~6,2% real a.a."
   Tooltip: "Retorno dos seus investimentos descontada a inflação. Para carteiras conservadoras use 4–5%. Moderadas: 6–7%. Arrojadas: 8–10%."

3. Taxa de retirada segura — PercentageInput, default=4.0%, min=1%, max=10%
   Benchmark: "Regra dos 4% (Estudo Trinity, EUA)"
   Tooltip: "Percentual do patrimônio que você pode retirar anualmente sem risco de esgotá-lo. 4% é o padrão internacional. Para maior segurança, use 3,5% ou 3%."

Botão "Restaurar padrões" que reseta os três campos para os valores padrão.

Escreva testes para: estado expandido/colapsado, restauração de padrões, cálculo correto com valores customizados
```

---

### Prompt 18 — Orquestrador do Formulário Completo

```
No /frontend/src/features/simulation do SimulaRenda, crie o componente SimulationForm:

Orquestra todas as seções em ordem:
1. <CurrentSituationSection />
2. <IndependenceGoalsSection />
3. <PublicPensionSection />
4. <PrivatePensionSection />
5. <EconomicParametersSection />

Comportamento:
- Usa react-hook-form no nível raiz com schema zod unificado
- onChange de qualquer campo dispara recálculo via useSimulationCalculator (hook customizado)
- useSimulationCalculator: debounce de 300ms, chama POST /api/v1/simulations/calculate, atualiza useSimulationStore.results
- Loading state durante o cálculo: cards de resultado mostram skeleton
- Erro de API: toast de erro não intrusivo

Botões no rodapé do formulário:
- "Salvar simulação" (primary): abre modal de nome se não tiver nome, então POST /simulations se autenticado, ou persiste em localStorage se não
- "Limpar" (ghost): reset do form com confirmação
- "Compartilhar" (outline): só visível se simulação salva

Barra de progresso no topo do formulário mostrando % de campos preenchidos

Escreva testes de integração mockando a API: fluxo completo de preenchimento → cálculo → exibição de resultados
```

---

## FASE 3 — Painel de Resultados e Gráficos (Prompts 19–28)

---

### Prompt 19 — Componente: ResultCard

```
No /frontend/src/features/simulation/components do SimulaRenda, crie o componente ResultCard:

Props:
- label: string
- value: string | number
- format?: 'currency' | 'percentage' | 'text' (default 'currency')
- variant?: 'default' | 'highlight' | 'success' | 'warning' | 'danger'
- hint?: string
- isLoading?: boolean
- trend?: { value: number, label: string } (ex: "+R$ 50.000 vs simulação anterior")

Comportamento:
- variant='highlight': card maior com valor em fonte grande (destaque para patrimônio necessário)
- isLoading: exibe skeleton animado no lugar do valor
- trend: exibe badge com seta ↑↓ e valor da diferença
- Valor monetário formatado em pt-BR com abreviação para milhões (ex: R$ 1,5M)

Escreva testes para: formatação de valores, variantes de cor, estado de loading, exibição de trend
```

---

### Prompt 20 — Grid de Cards de Resultados

```
No /frontend/src/features/simulation/components do SimulaRenda, crie o componente ResultsSummary:

Recebe SimulationResults do useSimulationStore.

Layout: grid responsivo (2 colunas mobile, 3 colunas desktop)

Cards a exibir:
1. "Patrimônio Necessário" — variant=highlight, valor=required_patrimony
2. "Patrimônio Projetado" — variant baseado em feasibility_status
3. "Aporte Mensal Necessário" — variant=default, valor=required_monthly_contribution
4. "Rendimento Anual Real" — format=percentage
5. "Inflação Projetada" — format=percentage
6. "Diferença (Gap)" — variant=danger se gap>0, variant=success se gap<=0, valor=patrimony_gap com sinal

Banner de status de viabilidade acima dos cards:
- viable: "✅ Seu plano é viável! Com os aportes atuais você atinge a independência financeira."
- warning: "⚠️ Plano com ajuste necessário. Você atingirá 80–100% do objetivo."
- unviable: "❌ Plano inviável com os parâmetros atuais. Veja sugestões abaixo."

Sugestões automáticas (quando warning ou unviable):
- "Aumentar o aporte mensal em R$ X chegaria ao objetivo"
- "Postergar a aposentadoria X anos resolveria o gap"
- "Reduzir a renda desejada em R$ Y tornaria o plano viável"

Escreva testes para: exibição correta por status, sugestões calculadas corretamente, responsividade
```

---

### Prompt 21 — Timeline de Eventos Previdenciários

```
No /frontend/src/features/simulation/components do SimulaRenda, crie o componente PensionTimeline:

Recebe: SimulationResults.phases e SimulationParameters

Renderiza uma linha do tempo horizontal com os eventos:
- [Hoje] → [Parar de trabalhar] → [Início Prev. Privada?] → [Início INSS?] → [Expectativa de vida]
  (a ordem dos dois benefícios depende dos start_ages)

Para cada segmento entre eventos, exibir:
- Rótulo da fase (ex: "Só patrimônio", "Patrimônio + Prev. Privada", "Patrimônio + INSS + Prev.")
- Duração em anos
- Renda mensal disponível no período
- Cor de fundo: vermelho claro para fases sem benefícios, amarelo para fases parciais, verde para fase com todos os benefícios

Cada evento é um marcador com ícone, rótulo e data/idade

Em mobile: timeline vertical

Alerta destacado se houver gap (período entre parar de trabalhar e início do primeiro benefício):
"Atenção: você terá X anos sem nenhum benefício previdenciário. Seu patrimônio precisa cobrir R$ Y/mês neste período."

Escreva testes para: renderização com 0, 1 e 2 benefícios, cálculo correto do alerta de gap, ordenação correta dos eventos por start_age
```

---

### Prompt 22 — Gráfico: Evolução Patrimonial

```
No /frontend/src/features/simulation/components/charts do SimulaRenda, crie o componente PatrimonyChart usando Recharts:

Dados: SimulationResults.projection_series (age, patrimony)

Tipo: ComposedChart com:
- Area para fase de acumulação (até retirement_age): fill teal com gradiente
- Line para fase de retirada (após retirement_age): linha sólida teal
- ReferenceLine vertical em retirement_age: "Parar de trabalhar" com label
- ReferenceLine vertical em public_pension.start_age (se habilitado): "Início INSS"
- ReferenceLine vertical em private_pension.start_age (se habilitado): "Início Prev. Privada"
- ReferenceLine horizontal em required_patrimony: "Patrimônio necessário" linha pontilhada vermelha
- Área sombreada em vermelho onde patrimony < required_patrimony

Eixos:
- X: idade (18 a life_expectancy)
- Y: valores em R$ com abreviação (K, M)

Tooltip customizado no hover:
- Idade: X anos
- Patrimônio: R$ X.XXX.XXX
- Fase atual: [nome da fase]
- Renda disponível: R$ X.XXX/mês

Controles:
- Botão "Exportar PNG" usando html2canvas
- Toggle "Mostrar em valores reais (ajustado pela inflação)"

Escreva testes: renderiza sem crashar com dados válidos, tooltip exibe dados corretos, toggle de inflação muda os valores do eixo Y
```

---

### Prompt 23 — Gráfico: Composição da Renda por Fase

```
No /frontend/src/features/simulation/components/charts do SimulaRenda, crie o componente IncomeCompositionChart usando Recharts:

Dados: SimulationResults.phases

Tipo: BarChart empilhado (stacked) com uma barra por fase

Barras empilhadas:
- "Retirada do Patrimônio" — cor teal
- "INSS / Aposentadoria Pública" — cor azul (se habilitado)
- "Previdência Privada" — cor violeta (se habilitado)

Eixo X: rótulo da fase (ex: "55–60 anos")
Eixo Y: R$/mês com abreviação

ReferenceLine horizontal em desired_monthly_income: "Renda desejada" com linha pontilhada

Tooltip: detalha cada fonte de renda e o total

Legenda clicável para mostrar/ocultar cada série

Escreva testes: empilhamento correto das barras, referência na renda desejada, legenda interativa
```

---

### Prompt 24 — Layout do Painel Principal (Desktop e Mobile)

```
No /frontend/src/pages do SimulaRenda, crie a HomePage:

Layout Desktop (lg: breakpoint):
- Grid 2 colunas: 45% formulário | 55% resultados
- Formulário: coluna esquerda com scroll independente
- Resultados: coluna direita sticky (acompanha o scroll do formulário)
- Ordem: ResultsSummary → PensionTimeline → PatrimonyChart → IncomeCompositionChart

Layout Mobile:
- Coluna única
- Formulário completo
- Após formulário: ResultsSummary → PensionTimeline
- Gráficos em seção colapsável "📊 Ver projeção detalhada"

Header da página:
- Logo "SimulaRenda" à esquerda
- Botão "Minhas Simulações" e avatar/login à direita
- Em mobile: menu hambúrguer

Estado inicial (sem dados):
- Painel de resultados exibe ilustração e texto: "Preencha os campos ao lado para ver sua projeção de independência financeira"

Escreva testes para: layout desktop com dados, layout mobile com dados, estado inicial sem dados
```

---

### Prompt 25 — Componente: SimulationNameModal

```
No /frontend/src/features/simulation/components do SimulaRenda, crie o componente SimulationNameModal:

Props:
- isOpen: boolean
- defaultName?: string
- onSave: (name: string) => void
- onCancel: () => void
- isSaving?: boolean

Comportamento:
- Modal com backdrop blur
- Input de nome com foco automático ao abrir
- Enter no input dispara onSave
- Nome padrão sugerido: "Simulação — [data atual]" ex: "Simulação — Jun 2026"
- Validação: nome não vazio, max 100 caracteres
- Botão "Salvar" com spinner quando isSaving=true
- Fecha no Escape ou clique fora (se não isSaving)

Escreva testes: foco automático, submit com Enter, validação de nome vazio, estado de loading
```

---

### Prompt 26 — Hook: useSimulationCalculator

```
No /frontend/src/features/simulation/hooks do SimulaRenda, crie o hook useSimulationCalculator:

Interface:
const { results, isCalculating, error, calculate } = useSimulationCalculator()

Comportamento:
- calculate(params: SimulationParameters): void
- Debounce de 300ms: múltiplas chamadas rápidas disparam apenas uma requisição
- Durante cálculo: isCalculating=true
- Sucesso: atualiza useSimulationStore.results, isCalculating=false
- Erro de validação (422): error com mensagem amigável, isCalculating=false
- Erro de rede: error="Não foi possível calcular. Verifique sua conexão."
- Cancela requisição pendente se nova chamada chegar antes do debounce (AbortController)

Também exporta: calculateSync(params) → SimulationResults
(versão síncrona para uso nos testes de cálculo, sem chamada de API)

Escreva testes:
- Debounce: 3 chamadas em 100ms disparam só 1 requisição
- Cancelamento de requisição anterior
- Atualização correta do store após sucesso
- Mensagem de erro correta para 422 vs erro de rede
```

---

### Prompt 27 — Exportação PDF do Relatório

```
No /frontend/src/features/simulation/services do SimulaRenda, crie o serviço generateSimulationPDF:

Tecnologia: @react-pdf/renderer (instale a dependência)

Conteúdo do PDF gerado:
- Cabeçalho: logo SimulaRenda, data de geração, nome da simulação
- Seção 1 — Resumo dos Parâmetros: tabela 2 colunas com todos os inputs
- Seção 2 — Resultados: cards principais (patrimônio necessário, projetado, gap, status)
- Seção 3 — Linha do Tempo: versão textual da PensionTimeline com fases e rendas
- Seção 4 — Tabela de Projeção: tabela com colunas Idade | Patrimônio | Fase | Renda/mês (a cada 5 anos)
- Rodapé: disclaimer "Este simulador tem fins educacionais e não constitui aconselhamento financeiro."

Botão "📥 Baixar PDF" no componente ResultsSummary que:
- Exibe loading durante geração
- Dispara download automático com nome: "SimulaRenda_[nome-simulação]_[data].pdf"

Escreva testes: conteúdo do documento gerado contém os campos esperados, nome do arquivo correto
```

---

### Prompt 28 — Página de Simulação Compartilhada

```
No /frontend/src/pages do SimulaRenda, crie a SharedSimulationPage:

Rota: /compartilhado/:token

Comportamento:
- Ao montar: GET /api/v1/simulations/shared/:token
- Loading: skeleton do painel de resultados
- Erro 404: "Esta simulação não existe ou o compartilhamento foi desativado"
- Sucesso: renderiza ResultsSummary + PensionTimeline + PatrimonyChart em modo read-only

Banner no topo:
"Você está visualizando a simulação '[nome]' compartilhada por [nome do usuário ou 'alguém'].
Crie sua própria simulação gratuitamente!"
CTA: "Simular agora" → /

Meta tags OG para preview ao compartilhar no WhatsApp:
- og:title: "Meu plano de independência financeira — SimulaRenda"
- og:description: "Patrimônio necessário: R$ X · Idade alvo: X anos · Status: Viável ✅"
- og:image: imagem estática de preview

Escreva testes: loading state, exibição de erro 404, dados renderizados corretamente, banner de CTA presente
```

---

## FASE 4 — Histórico e Comparação (Prompts 29–36)

---

### Prompt 29 — Página: Minhas Simulações

```
No /frontend/src/pages do SimulaRenda, crie a SimulationsPage (rota /minhas-simulacoes, requer auth):

Layout:
- Header com título "Minhas Simulações" e botão "Nova Simulação" → /
- Grid de SimulationCards (2 colunas desktop, 1 mobile)
- Paginação com infinite scroll ou botão "Carregar mais"
- Barra de busca por nome de simulação (filtra localmente se < 20 itens, senão query na API)

SimulationCard exibe:
- Nome da simulação (clicável → detalhe)
- Data de criação formatada
- Badge de status (viable/warning/unviable) com cor
- Patrimônio necessário e projetado
- Mini-barra de progresso: projetado/necessário
- Menu kebab (três pontos) com: Renomear | Duplicar | Compartilhar | Excluir

Estado vazio (sem simulações): ilustração + "Você ainda não salvou nenhuma simulação. Faça sua primeira simulação!"

Ação Renomear: inline edit no card com save on blur/Enter
Ação Duplicar: POST /simulations com mesmo parameters e nome "Cópia de [nome]"
Ação Excluir: confirmação com Dialog antes de DELETE

Escreva testes: renderização de cards, inline rename, confirmação de exclusão, estado vazio
```

---

### Prompt 30 — Comparação de Simulações

```
No /frontend/src/features/simulations/components do SimulaRenda, crie o componente SimulationComparison:

Ativação: botão "Comparar" na SimulationsPage entra em modo seleção; usuário seleciona 2 ou 3 cards; botão "Ver comparação" abre a tela de comparação.

Layout da tela de comparação:
- Tabela com simulações nas colunas e métricas nas linhas
- Linhas: Nome | Data | Patrimônio Necessário | Patrimônio Projetado | Gap | Aporte Mensal | Idade de Aposentadoria | Status
- Células com status destacadas pela cor de feasibility
- Linha de melhor valor em cada métrica destacada em verde

Gráfico sobreposto:
- PatrimonyChart com uma linha por simulação (cores distintas)
- Legenda interativa (clica na legenda para mostrar/ocultar linha)

Botão "Fechar comparação" volta ao modo normal de lista

Escreva testes: tabela exibe dados corretos, destaque de melhor valor por linha, gráfico sobreposto com N linhas
```

---

### Prompt 31 — Página de Detalhe da Simulação

```
No /frontend/src/pages do SimulaRenda, crie a SimulationDetailPage (rota /simulacao/:id):

Comportamento:
- GET /api/v1/simulations/:id ao montar
- Exibe formulário pre-preenchido com simulation.parameters (modo edição)
- Painel de resultados com simulation.results
- Header com: nome da simulação (editável inline), data de criação, botões Salvar | Duplicar | Excluir | Compartilhar

Modo edição:
- Qualquer alteração no formulário marca isDirty=true
- Botão "Salvar alterações" (visível quando isDirty) dispara PUT /simulations/:id
- Aviso "Alterações não salvas" ao tentar navegar para outra rota com isDirty=true (React Router blocker)

Toggle de compartilhamento:
- "Compartilhar simulação" → POST /simulations/:id/share {enable: true}
- Exibe URL copiável com botão "Copiar link"
- "Desativar compartilhamento" → POST /simulations/:id/share {enable: false}

Escreva testes: carregamento de dados, detecção de dirty state, blocker de navegação, toggle de compartilhamento
```

---

### Prompt 32 — Persistência Offline (localStorage)

```
No /frontend/src/services do SimulaRenda, crie o serviço offlineSimulationsService:

Funções:
- save(simulation: LocalSimulation): void — máximo 5 simulações (FIFO: remove a mais antiga se cheio)
- list(): LocalSimulation[]
- get(id: string): LocalSimulation | null
- remove(id: string): void
- clear(): void
- count(): number

Tipo LocalSimulation:
- id: string (nanoid)
- name: string
- parameters: SimulationParameters
- results: SimulationResults
- created_at: string (ISO)
- is_local: true

Integração no SimulationForm:
- Se !isAuthenticated e clica "Salvar": salva via offlineSimulationsService
- Toast informativo: "Simulação salva localmente. Crie uma conta gratuita para não perder suas simulações!"
- Se count() === 4: "Você tem espaço para mais 1 simulação local. Crie uma conta para salvar ilimitadas."
- Se count() === 5: modal bloqueante "Limite atingido. Crie uma conta ou exclua uma simulação."

Migração ao fazer login:
- useAuthStore.setAuth chama migrateLocalSimulations()
- migrateLocalSimulations: POST /simulations para cada local simulation; clear() local após sucesso

Escreva testes: limite de 5, remoção FIFO, migração ao login (mock da API), toast correto por quantidade
```

---

### Prompt 33 — Autenticação: Páginas de Login e Cadastro

```
No /frontend/src/pages do SimulaRenda, crie LoginPage e RegisterPage:

LoginPage (/entrar):
- Formulário: email + senha + "Lembrar de mim" (checkbox)
- Botão "Entrar com Google" (OAuth, abre popup)
- Link "Esqueci minha senha"
- Link "Criar conta"
- Após login bem-sucedido: redireciona para a rota de origem (via state do location) ou para /

RegisterPage (/cadastrar):
- Formulário: nome + email + senha + confirmação de senha
- Botão "Cadastrar com Google"
- Link "Já tenho conta"
- Após cadastro: migra simulações locais (se houver) → redireciona para /

ForgotPasswordPage (/esqueci-senha):
- Campo email → POST /auth/forgot-password
- Exibe: "Email enviado! Verifique sua caixa de entrada."

ResetPasswordPage (/redefinir-senha?token=X):
- Campos: nova senha + confirmação
- POST /auth/reset-password

Todos com validação zod + react-hook-form.
Escreva testes: validação de formulários, fluxo de login com redirect, migração de simulações ao cadastrar
```

---

### Prompt 34 — Notificações e Toasts

```
No /frontend/src/components/ui do SimulaRenda, crie o sistema de notificações:

1. Componente Toast:
   Props: message, type ('success'|'error'|'warning'|'info'), duration=5000, onDismiss
   - Posição: canto inferior direito
   - Animação: slide-in da direita, fade-out ao fechar
   - Ícone por tipo (lucide-react: CheckCircle, XCircle, AlertTriangle, Info)
   - Barra de progresso indicando tempo restante
   - Botão X para fechar manualmente

2. Hook useToast:
   const { toast } = useToast()
   - toast.success("Simulação salva!")
   - toast.error("Erro ao salvar")
   - toast.warning("Você está prestes a atingir o limite")
   - toast.info("Dica: ...")
   - Fila de até 3 toasts simultâneos (FIFO)

3. Componente ToastContainer: renderizado no root da app via portal

Escreva testes: exibição e auto-dismiss, limite de 3, fechamento manual, ícones corretos por tipo
```

---

### Prompt 35 — Perfil do Usuário

```
No /frontend/src/pages do SimulaRenda, crie a UserProfilePage (/perfil, requer auth):

Seções:
1. Dados pessoais: nome (editável), email (somente leitura), data de nascimento (editável — usada para pré-preencher "idade atual" no formulário)
2. Segurança: "Alterar senha" (formulário inline: senha atual + nova + confirmação)
3. Simulações: contador de simulações salvas + link para /minhas-simulacoes
4. Zona de perigo: "Excluir minha conta" com confirmação via modal solicitando digitação do email

Comportamento da exclusão:
- Modal: "Digite seu email para confirmar a exclusão permanente da sua conta e todas as suas simulações"
- Input de email deve corresponder ao email da conta
- DELETE /api/v1/users/me → clearAuth → redireciona para / com toast "Sua conta foi excluída."

Avatar: iniciais do nome em círculo colorido (sem upload de foto no MVP)

Escreva testes: edição de nome, validação de exclusão de conta, pré-preenchimento de idade no formulário com base na data de nascimento
```

---

### Prompt 36 — SEO e Meta Tags Dinâmicas

```
No /frontend do SimulaRenda, configure SEO e meta tags:

1. Instale react-helmet-async

2. Crie componente SEO com props: title, description, ogImage?, noIndex?
   - title: "[título] | SimulaRenda"
   - Canonical URL automática baseada em window.location
   - Open Graph: og:title, og:description, og:url, og:image, og:type
   - Twitter Card: summary_large_image

3. Configure em cada página:
   - /: "Simule sua independência financeira | SimulaRenda" — description sobre a calculadora
   - /minhas-simulacoes: noIndex=true (página privada)
   - /compartilhado/:token: title e description dinâmicos com dados da simulação

4. Crie sitemap.xml estático para as rotas públicas

5. Em vite.config.ts: configure prerender das páginas / e /entrar usando vite-plugin-ssr ou similar para SSG

6. robots.txt:
   - Allow: /
   - Disallow: /minhas-simulacoes, /simulacao/, /perfil
   - Sitemap: https://simularenda.com.br/sitemap.xml

Escreva testes: meta tags corretas por rota, noIndex em rotas privadas
```

---

## FASE 5 — Qualidade, Performance e Deploy (Prompts 37–48)

---

### Prompt 37 — Testes E2E com Playwright

```
No /e2e do SimulaRenda, configure Playwright e crie os testes end-to-end:

Configuração:
- playwright.config.ts com: baseURL=http://localhost:5173, browsers=[chromium, firefox], screenshots on failure, vídeo on retry

Cenário 1 — Fluxo principal sem login:
- Abre a página inicial
- Preenche todos os campos do formulário
- Verifica que os cards de resultado aparecem e têm valores > 0
- Verifica que a timeline exibe as fases corretas
- Verifica que o gráfico renderizou (canvas/svg presente)
- Clica "Salvar" → verifica modal de nome → salva → verifica toast de sucesso

Cenário 2 — Cadastro e persistência:
- Simula sem login
- Cria conta
- Verifica migração da simulação local para a conta
- Acessa /minhas-simulacoes e verifica a simulação

Cenário 3 — Compartilhamento:
- Abre simulação salva
- Ativa compartilhamento → copia link
- Abre o link em aba anônima → verifica que exibe os resultados em modo read-only

Cenário 4 — Comparação de simulações:
- Cria 3 simulações com parâmetros diferentes
- Seleciona todas na lista
- Abre comparação → verifica tabela e gráfico

Cenário 5 — Fluxo mobile (viewport 390x844):
- Repete Cenário 1 em viewport mobile
- Verifica layout em coluna única
- Verifica que gráficos são acessíveis
```

---

### Prompt 38 — Testes de Unidade da Engine de Cálculo (Cobertura 100%)

```
No /backend/tests/test_calculator.py do SimulaRenda, adicione os casos de teste de borda para garantir 100% de cobertura da engine:

Casos de borda a cobrir:
1. Patrimônio atual já suficiente (required_contribution deve ser 0, não negativo)
2. Idade de parar de trabalhar = idade atual + 1 (acumulação mínima)
3. Ambas as pensões com start_age = retirement_age (sem gap em nenhuma)
4. Expectativa de vida = retirement_age + 1 (usufruto mínimo)
5. Taxa de retirada = 10% (caso conservador de prazo certo)
6. Inflação = 0% (sem correção)
7. Rendimento real = 0% (sem crescimento patrimonial)
8. Previdência privada com modalidade fixed_term: patrimônio deve sobreviver após encerramento do benefício
9. Pensão pública com start_age muito posterior (gap de 15+ anos)
10. Simulação com patrimônio se esgotando antes da expectativa de vida (sinalizar corretamente)

Para cada caso, verificar:
- Sem exceção de divisão por zero ou overflow
- feasibility_status correto
- projection_series sem valores negativos (mínimo 0 após esgotamento)
- phases com from_age/to_age sem sobreposição

Configure coverage com pytest-cov:
pytest --cov=app/services/calculator --cov-report=html --cov-fail-under=100
```

---

### Prompt 39 — Rate Limiting e Segurança da API

```
No /backend do SimulaRenda, implemente segurança e rate limiting:

1. Rate limiting com slowapi (wrapper do Flask-Limiter para FastAPI):
   - POST /auth/login: 10 req/min por IP
   - POST /auth/register: 5 req/min por IP
   - POST /simulations/calculate: 30 req/min por IP
   - POST /simulations: 20 req/hour por user_id
   - Resposta 429 com header Retry-After

2. Middleware de segurança:
   - CORS: apenas origens da lista CORS_ORIGINS no settings
   - Helmet-like headers: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy
   - Content-Security-Policy para rotas que retornam HTML

3. Validação de entrada:
   - Todos os campos string com strip() antes de persistir
   - Sanitização de name da simulação (remover HTML tags)
   - share_token gerado com secrets.token_urlsafe(32), não previsível

4. Proteção CSRF: token em cookie httpOnly para rotas mutativas

5. Logs de segurança:
   - Logar IP + tentativas de login falhas
   - Alertar (log WARNING) após 5 falhas consecutivas do mesmo IP

Escreva testes: rate limit retorna 429 na 11ª requisição, CORS bloqueia origem não listada, sanitização de XSS no nome da simulação
```

---

### Prompt 40 — Otimização de Performance do Frontend

```
No /frontend do SimulaRenda, implemente otimizações de performance:

1. Code splitting com React.lazy e Suspense:
   - SimulationsPage, SimulationDetailPage, SharedSimulationPage carregados sob demanda
   - Recharts importado dinamicamente (é pesado)
   - Suspense fallback com skeleton da página

2. Memoização:
   - ResultsSummary: React.memo, recalcula apenas quando results mudar
   - PatrimonyChart: React.memo + useMemo para dados do gráfico
   - Funções de formatação de moeda: useMemo com Intl.NumberFormat

3. Web Worker para cálculos sincronos pesados:
   - Mova calculateSync para /src/workers/calculator.worker.ts
   - Use comlink para comunicação tipada
   - Isso libera a thread principal durante projeções de 70+ anos

4. Otimização de imagens:
   - Ícones: apenas lucide-react (tree-shaking automático)
   - Qualquer imagem estática: use WebP com fallback PNG

5. Prefetch de rotas:
   - Ao hover em "Minhas Simulações", prefetch do chunk da SimulationsPage

6. Bundle analysis:
   - Configure rollup-plugin-visualizer
   - Meta: bundle principal < 150KB gzipped (excluindo chunks lazy)

Execute Lighthouse CI e garanta score ≥ 90 em Performance, Acessibilidade e SEO.
Escreva teste verificando que o bundle principal não excede 150KB.
```

---

### Prompt 41 — Containerização Docker

```
Na raiz do SimulaRenda, crie os Dockerfiles e docker-compose de produção:

/backend/Dockerfile:
- FROM python:3.12-slim
- Multi-stage: builder (instala deps) + runtime (copia apenas o necessário)
- Usuário não-root
- HEALTHCHECK via GET /health

/frontend/Dockerfile:
- Multi-stage: builder (npm run build) + nginx (serve os estáticos)
- nginx.conf: gzip, cache-control headers, try_files para SPA routing
- HEALTHCHECK via curl

docker-compose.prod.yml:
- backend: image build, env_file, depends_on postgres e redis, restart=unless-stopped
- frontend: image build, porta 80/443
- postgres: volume persistente, healthcheck
- redis: volume persistente, password via env, maxmemory 256mb com allkeys-lru
- nginx-proxy: imagem nginx:alpine como reverse proxy (/ → frontend, /api → backend)

Variáveis de ambiente de produção necessárias documentadas em .env.prod.example

Makefile targets adicionais: docker-build, docker-push, docker-prod-up, docker-prod-down

Escreva smoke test: docker-compose -f docker-compose.prod.yml up -d → GET / retorna 200 → GET /api/v1/health retorna 200
```

---

### Prompt 42 — CI/CD com GitHub Actions

```
No /.github/workflows do SimulaRenda, crie os pipelines:

ci.yml (trigger: push e PR para main e develop):
  Jobs em paralelo:
  - backend-test:
    - Python 3.12, instala deps, roda pytest com coverage
    - Falha se coverage < 80%
    - Upload do relatório de coverage como artefato
  - frontend-test:
    - Node 20, instala deps, roda vitest --coverage
    - Falha se coverage < 70%
  - frontend-lint:
    - ESLint + TypeScript check (tsc --noEmit)
  - e2e (apenas em PRs para main):
    - Sobe stack com docker-compose
    - Roda playwright test
    - Upload screenshots/vídeos de falhas

deploy-staging.yml (trigger: push para develop):
  - Depende de ci.yml passar
  - Build das imagens Docker e push para registry
  - Deploy em ambiente de staging via SSH

deploy-prod.yml (trigger: push de tag v*.*.* para main):
  - Aprovação manual obrigatória (environment: production com reviewers)
  - Mesmos steps do staging
  - Após deploy: smoke test automático nos endpoints principais
  - Em caso de falha: rollback automático para a imagem anterior

Secrets necessários documentados em DEPLOYMENT.md
```

---

### Prompt 43 — Monitoramento e Observabilidade

```
No /backend do SimulaRenda, configure observabilidade:

1. Structured logging com structlog:
   - Formato JSON em produção, colorido no desenvolvimento
   - Cada requisição loga: method, path, status_code, duration_ms, user_id (se autenticado), request_id (UUID gerado por middleware)
   - Não logar senhas, tokens, dados financeiros sensíveis

2. Métricas com prometheus-fastapi-instrumentator:
   - GET /metrics (protegido por header X-Metrics-Token)
   - Métricas customizadas: simulations_calculated_total, simulations_saved_total, calculation_duration_seconds

3. Health check endpoint GET /health:
   Retorna JSON:
   {
     "status": "healthy" | "degraded",
     "database": "up" | "down",
     "redis": "up" | "down",
     "version": "1.0.0"
   }
   Status HTTP 200 se healthy, 503 se degraded

4. Sentry para error tracking:
   - Instale sentry-sdk[fastapi]
   - Configure SENTRY_DSN no settings
   - Captura exceções não tratadas com contexto do usuário (apenas user_id, sem dados financeiros)

5. No frontend:
   - Web Vitals reporting via web-vitals package → POST /api/v1/metrics/vitals
   - Sentry para erros de JavaScript

Escreva testes: /health retorna 200 com DB up, retorna 503 com DB down mockado
```

---

### Prompt 44 — Acessibilidade (WCAG 2.1 AA)

```
No /frontend do SimulaRenda, realize auditoria e correções de acessibilidade:

1. Formulário:
   - Todos os inputs com id e label htmlFor correspondente
   - Campos obrigatórios com aria-required="true"
   - Erros de validação com role="alert" e aria-live="polite"
   - SliderInput com aria-valuemin, aria-valuemax, aria-valuenow, aria-label

2. Gráficos:
   - PatrimonyChart: aria-label descrevendo o gráfico, role="img"
   - Tabela de dados colapsável abaixo de cada gráfico como alternativa acessível (visível apenas para leitores de tela via sr-only + focusable)

3. Modal/Dialog:
   - Focus trap dentro do modal (Tab não sai do modal)
   - Foco retorna ao elemento disparador ao fechar
   - aria-modal="true", aria-labelledby apontando para o título

4. Toast:
   - role="status" para success/info, role="alert" para error/warning
   - aria-live="polite" para status, aria-live="assertive" para alert

5. Timeline:
   - Implementada como lista ordenada (<ol>) semanticamente
   - Cada fase com aria-label descritivo

6. Contraste:
   - Verificar todos os pares texto/fundo com plugin eslint-plugin-jsx-a11y
   - Mínimo 4.5:1 para texto normal, 3:1 para texto grande

7. Navegação por teclado:
   - Todos os elementos interativos alcançáveis por Tab
   - Nenhum outline removido sem substituto visual

Execute axe-core via jest-axe em todos os componentes e corrija todos os violations.
```

---

### Prompt 45 — Internacionalização Futura (i18n Ready)

```
No /frontend do SimulaRenda, prepare a base para internacionalização sem implementar múltiplos idiomas no MVP:

1. Instale i18next + react-i18next

2. Crie /src/locales/pt-BR/translation.json com TODAS as strings da aplicação organizadas por namespace:
   {
     "common": { "save": "Salvar", "cancel": "Cancelar", ... },
     "simulation": { "form": {...}, "results": {...} },
     "auth": { "login": {...}, "register": {...} },
     "errors": { "required": "Campo obrigatório", ... }
   }

3. Substitua TODOS os textos hardcoded nos componentes por chamadas t('namespace.key')

4. Formatação de moeda via Intl.NumberFormat configurada em hook useCurrency que respeita o locale atual

5. Formatação de datas via date-fns com locale pt-BR

6. Crie script /scripts/check-i18n.ts que:
   - Varre todos os componentes TSX
   - Detecta strings hardcoded que NÃO sejam variáveis, props ou valores técnicos
   - Reporta como warning no CI

Escreva testes: todas as keys do translation.json são usadas em pelo menos um componente (sem keys órfãs); todos os textos visíveis nos snapshots passam pelo t()
```

---

### Prompt 46 — Documentação da API (OpenAPI/Swagger)

```
No /backend do SimulaRenda, configure documentação interativa da API:

1. FastAPI já gera OpenAPI automaticamente. Enriqueça com:
   - Descrição de cada endpoint (docstring + summary + description)
   - Exemplos de request/response em cada schema Pydantic usando model_config com json_schema_extra
   - Tags organizando endpoints: Authentication, Simulations, Users, Health
   - Respostas de erro documentadas (400, 401, 403, 404, 422, 429, 500)

2. Customize o Swagger UI em /docs:
   - Título: "SimulaRenda API"
   - Logo: /static/logo.png
   - Autenticação via Bearer Token configurada no Swagger (botão Authorize)

3. Crie /docs/api-examples.md com:
   - Exemplos de curl para os fluxos principais
   - Exemplo de integração Python com httpx
   - Exemplo de integração JavaScript com fetch

4. Endpoint GET /api/v1/openapi.json retorna o schema completo

5. No README.md do /backend, adicione seção "Desenvolvimento" com:
   - Como rodar localmente
   - Como rodar os testes
   - Link para a documentação interativa

Escreva testes: GET /docs retorna 200; GET /openapi.json retorna schema válido com todos os endpoints documentados
```

---

### Prompt 47 — Seed de Dados e Ambiente de Desenvolvimento

```
No /backend do SimulaRenda, crie scripts de seed e fixtures para desenvolvimento:

1. /backend/scripts/seed_dev.py:
   Cria dados de desenvolvimento ao rodar python scripts/seed_dev.py:
   - 3 usuários de teste com senhas conhecidas:
     dev@simularenda.com / senha: Dev@12345
     usuario@teste.com / senha: Teste@123
     admin@simularenda.com / senha: Admin@123
   - 5 simulações variadas para cada usuário (cobrindo viable, warning e unviable)
   - Pelo menos 2 simulações com share_token gerado (is_public=True)

2. /backend/scripts/reset_dev.py:
   DROP + recria todas as tabelas + roda seed_dev.py
   Só executa se DATABASE_URL contiver 'localhost' ou 'dev' (proteção contra execução em produção)

3. Fixtures Pytest em conftest.py:
   - user_factory: cria usuário com parâmetros customizáveis
   - simulation_factory: cria simulação com parameters padrão sobrescrevíveis
   - authenticated_client: AsyncClient com Authorization header do usuário de teste

4. Makefile targets:
   - make seed: roda seed_dev.py
   - make reset-db: roda reset_dev.py
   - make shell: abre Python shell com contexto da app e sessão DB

Escreva testes: seed não falha em banco limpo; seed é idempotente (rodar 2x não duplica dados); reset_dev falha se DATABASE_URL apontar para produção
```

---

### Prompt 48 — Checklist de Go-Live e Smoke Tests

```
No /backend e /frontend do SimulaRenda, crie o checklist automatizado de go-live:

1. Script /scripts/pre_deploy_check.sh:
   Executa e falha se qualquer item não passar:
   □ Testes backend: pytest --tb=short (todos passando)
   □ Cobertura backend: ≥ 80% (pytest-cov)
   □ Testes frontend: vitest run (todos passando)
   □ TypeScript: tsc --noEmit (sem erros de tipo)
   □ ESLint: eslint src --max-warnings 0
   □ Build frontend: vite build (sem erros, bundle < 200KB gzipped)
   □ Variáveis de ambiente: verifica que todas as vars do .env.prod.example estão definidas
   □ Migrações pendentes: alembic check (sem migrações não aplicadas)

2. Script /scripts/smoke_test.sh BASE_URL:
   Após deploy, executa:
   □ GET $BASE_URL/ → 200
   □ GET $BASE_URL/api/v1/health → 200 com status:healthy
   □ POST $BASE_URL/api/v1/simulations/calculate com payload válido → 200 com required_patrimony > 0
   □ POST $BASE_URL/api/v1/auth/login com credenciais inválidas → 401
   □ GET $BASE_URL/api/v1/simulations sem token → 401
   □ GET $BASE_URL/api/v1/simulations/shared/token-invalido → 404

3. Crie RUNBOOK.md com:
   - Procedimento de rollback (passos manuais + comando)
   - Como verificar logs em produção
   - Contatos de emergência
   - SLOs: uptime 99.5%, cálculo p95 < 300ms, error rate < 0.1%

4. GitHub Actions job post-deploy que roda smoke_test.sh após cada deploy e abre issue automática se falhar.
```

---

## Resumo das Fases

| Fase | Prompts | Entregável Principal |
|------|---------|---------------------|
| **1 — Setup e Infraestrutura** | 01–08 | Monorepo configurado, backend FastAPI, modelos DB, schemas, engine de cálculo, autenticação, CRUD de API, frontend base |
| **2 — Formulário de Simulação** | 09–18 | Todos os componentes de input, 5 seções do formulário, hook de cálculo em tempo real |
| **3 — Resultados e Gráficos** | 19–28 | Cards de resultado, timeline de eventos, 2 gráficos interativos, export PDF, página de compartilhamento |
| **4 — Histórico e Comparação** | 29–36 | Lista de simulações, comparação side-by-side, offline localStorage, autenticação completa, SEO |
| **5 — Qualidade e Deploy** | 37–48 | E2E Playwright, segurança, performance, Docker, CI/CD, monitoramento, acessibilidade, go-live |

---

*SimulaRenda — Prompts para ChatGPT Codex · v1.0 · 01/06/2026*
