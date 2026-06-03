# SimulaRenda — Prompts para ChatGPT Codex
**Stack:** FastAPI + NiceGUI (Python 3.12) · PostgreSQL 16 · Redis 7  
**Não há JavaScript, TypeScript, Node.js ou npm neste projeto.**  
**Metodologia:** TDD — escreva os testes antes da implementação em cada prompt  
**Total:** 4 prompts de reversão + 48 prompts de implementação

---

# ⚠️ PROMPTS DE REVERSÃO — Execute primeiro, na ordem R01→R04

> Você executou os prompts 01–04 da versão anterior (stack React/TypeScript).
> Estes prompts desfazem tudo que era exclusivo do frontend React, preservam
> integralmente o backend FastAPI (prompts 02, 03 e 04 — que continuam válidos)
> e preparam o repositório para a nova stack NiceGUI.

---

### Prompt R01 — Remover Frontend React e Pasta Shared

```
No repositório do SimulaRenda, remova completamente qualquer vestígio da stack
React/TypeScript que foi criada no prompt 01 original:

1. Delete a pasta /frontend inteira (se existir):
   rm -rf frontend/

2. Delete a pasta /shared inteira (se existir):
   rm -rf shared/

3. No .gitignore da raiz, remova todas as linhas relacionadas a Node.js:
   - node_modules/
   - dist/
   - .vite/
   - *.tsbuildinfo
   - .npm
   Mantenha as linhas de Python (.venv, __pycache__, *.pyc, .env, etc.)

4. No docker-compose.yml, remova o serviço "frontend" inteiro (se existir).
   Mantenha os serviços: postgres, redis, backend.
   Atualize o serviço "backend" para expor a porta 8000 diretamente
   (NiceGUI e FastAPI rodam no mesmo processo na porta 8000).

5. No Makefile, remova os targets que referenciam npm, vite, node ou frontend:
   - Remova: qualquer linha com npm, npx, vite, tsc, eslint (js)
   - Mantenha e atualize: install, dev, test, lint, build, migrate
   Os novos targets devem usar apenas pip/python:
     install: pip install -e ".[dev]"
     dev: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
     test: pytest --cov=app --cov-report=term-missing
     lint: ruff check app/ && mypy app/
     migrate: alembic upgrade head

6. Atualize o README.md:
   - Remova qualquer menção a Node.js, npm, React, TypeScript, Vite
   - Atualize a seção de setup para: Python 3.12, pip, variáveis de ambiente, make dev
   - Adicione nota: "Frontend construído com NiceGUI — não há build step separado"

7. Verifique que não restam arquivos com extensão .ts, .tsx, .js (exceto
   eventuais arquivos de config de ferramentas como .eslintrc — apague esses também),
   package.json, package-lock.json, yarn.lock, pnpm-lock.yaml.

Após as remoções, rode:
  find . -name "package.json" -not -path "*/node_modules/*"
  find . -name "*.ts" -not -path "*/node_modules/*"
Ambos devem retornar vazio. Confirme no output.
```

---

### Prompt R02 — Atualizar pyproject.toml com Dependências NiceGUI

```
No /backend/pyproject.toml do SimulaRenda, atualize as dependências para
incluir NiceGUI e remover quaisquer pacotes que existiam apenas para servir
o frontend React (como flask-cors ou similares que podem ter sido adicionados).

Dependências de produção (substitua a seção [project.dependencies]):
  fastapi>=0.111
  uvicorn[standard]>=0.29
  nicegui>=1.4
  sqlalchemy[asyncio]>=2.0
  asyncpg>=0.29
  alembic>=1.13
  pydantic[email]>=2.7
  pydantic-settings>=2.3
  python-jose[cryptography]>=3.3
  passlib[bcrypt]>=1.7
  redis>=5.0
  slowapi>=0.1.9
  plotly>=5.20
  reportlab>=4.1
  structlog>=24.0
  httpx>=0.27
  sentry-sdk[fastapi]>=2.0

Dependências de desenvolvimento ([project.optional-dependencies] dev):
  pytest>=8.0
  pytest-asyncio>=0.23
  pytest-cov>=5.0
  anyio>=4.0
  playwright>=1.44
  ruff>=0.4
  mypy>=1.10

Configure o pyproject.toml com:
  [tool.pytest.ini_options]
  asyncio_mode = "auto"
  testpaths = ["tests"]

  [tool.coverage.run]
  source = ["app"]
  omit = ["app/ui/*"]   # UI NiceGUI testada via E2E, não unitariamente

  [tool.mypy]
  python_version = "3.12"
  strict = true
  ignore_missing_imports = true

  [tool.ruff]
  line-length = 100
  select = ["E", "F", "I", "UP"]

Rode pip install -e ".[dev]" e confirme que não há erros de instalação.
Rode pytest --collect-only e confirme que os testes dos prompts 02, 03 e 04
ainda são coletados e passam (backend não foi alterado).
```

---

### Prompt R03 — Criar Estrutura de Pastas da UI NiceGUI

```
No /backend/app do SimulaRenda, crie a estrutura de pastas para a camada
de UI NiceGUI. Não modifique nada nas pastas existentes: api/, core/, db/,
models/, schemas/, services/, tests/. Apenas adicione o seguinte:

Criar /backend/app/ui/ com a estrutura:

app/ui/
├── __init__.py          ← função register_pages() que registra todas as rotas NiceGUI
├── pages/
│   ├── __init__.py
│   ├── home.py          ← página principal: formulário + resultados (rota '/')
│   ├── simulations.py   ← histórico e comparação (rota '/minhas-simulacoes')
│   ├── simulation_detail.py  ← detalhe/edição (rota '/simulacao/{id}')
│   ├── shared.py        ← visualização pública read-only (rota '/compartilhado/{token}')
│   ├── login.py         ← (rota '/entrar')
│   └── register.py      ← (rota '/cadastrar')
├── components/
│   ├── __init__.py
│   ├── simulation_form.py     ← formulário completo (5 seções)
│   ├── results_panel.py       ← cards de resultado e banner de viabilidade
│   ├── pension_timeline.py    ← linha do tempo de eventos previdenciários
│   ├── patrimony_chart.py     ← gráfico Plotly evolução patrimonial
│   ├── income_chart.py        ← gráfico Plotly composição de renda por fase
│   └── simulation_card.py     ← card individual na lista de simulações
└── state/
    ├── __init__.py
    └── simulation_state.py    ← dataclass SimulationState com todos os campos

Em cada arquivo, crie apenas o esqueleto (imports + classe/função vazia com docstring).
Não implemente nada ainda — isso é feito nos prompts seguintes.

Em app/ui/__init__.py, implemente register_pages():
```python
from app.ui.pages import home, simulations, simulation_detail, shared, login, register

def register_pages() -> None:
    """Registra todas as rotas NiceGUI na aplicação."""
    home.create()
    simulations.create()
    simulation_detail.create()
    shared.create()
    login.create()
    register.create()
```

Atualize app/main.py para integrar NiceGUI com FastAPI:
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from nicegui import ui
from app.core.config import settings
from app.api.v1.routes import auth, simulations, users
from app.db.session import init_db
from app.ui import register_pages

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="SimulaRenda API", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS,
                   allow_methods=["*"], allow_headers=["*"])

app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(simulations.router, prefix="/api/v1", tags=["simulations"])
app.include_router(users.router, prefix="/api/v1", tags=["users"])

register_pages()

ui.run_with(app, mount_path='/', storage_secret=settings.SECRET_KEY,
            title='SimulaRenda', favicon='💰', dark=False,
            host=settings.NICEGUI_HOST, port=settings.NICEGUI_PORT)
```

Confirme rodando: python -c "from app.main import app; print('OK')"
Não deve haver ImportError.
```

---

### Prompt R04 — Atualizar docker-compose e Variáveis de Ambiente

```
Atualize os arquivos de infraestrutura do SimulaRenda para refletir a nova
arquitetura de processo único (NiceGUI + FastAPI na porta 8000):

1. docker-compose.yml (desenvolvimento):
   Deve conter exatamente 3 serviços:

   postgres:
     image: postgres:16-alpine
     environment:
       POSTGRES_DB: simularenda
       POSTGRES_USER: simularenda
       POSTGRES_PASSWORD: simularenda
     ports: ["5432:5432"]
     volumes: [postgres_data:/var/lib/postgresql/data]
     healthcheck: pg_isready -U simularenda

   redis:
     image: redis:7-alpine
     command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
     ports: ["6379:6379"]
     volumes: [redis_data:/data]
     healthcheck: redis-cli ping

   backend:
     build: ./backend
     ports: ["8000:8000"]      ← porta única: NiceGUI + FastAPI + WebSocket
     env_file: .env
     depends_on:
       postgres: {condition: service_healthy}
       redis: {condition: service_healthy}
     volumes: ["./backend:/app"]
     command: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

   volumes: [postgres_data, redis_data]

2. docker-compose.prod.yml:
   Adicione um serviço nginx na frente do backend com este bloco CRÍTICO:
   (sem ele, a reatividade NiceGUI quebra em produção)

   nginx:
     image: nginx:alpine
     ports: ["80:80", "443:443"]
     volumes: ["./nginx.conf:/etc/nginx/conf.d/default.conf:ro"]
     depends_on: [backend]

   Crie nginx.conf com:
   ```nginx
   server {
       listen 80;
       location / {
           proxy_pass http://backend:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";   # OBRIGATÓRIO para WebSocket NiceGUI
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_read_timeout 86400;                # evita timeout no WebSocket
       }
   }
   ```

3. /backend/Dockerfile:
   FROM python:3.12-slim
   WORKDIR /app
   COPY pyproject.toml .
   RUN pip install -e ".[dev]"    # instala dependências incluindo NiceGUI
   COPY . .
   RUN useradd -m appuser && chown -R appuser /app
   USER appuser
   EXPOSE 8000
   HEALTHCHECK CMD curl -f http://localhost:8000/api/v1/health || exit 1
   CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

4. Atualize .env.example adicionando as variáveis NiceGUI:
   NICEGUI_HOST=0.0.0.0
   NICEGUI_PORT=8000
   NICEGUI_STORAGE_SECRET=   # pode ser o mesmo valor que SECRET_KEY

5. Atualize app/core/config.py adicionando ao Settings:
   nicegui_host: str = "0.0.0.0"
   nicegui_port: int = 8000
   nicegui_storage_secret: str = ""

   @model_validator(mode='after')
   def set_storage_secret(self) -> 'Settings':
       if not self.nicegui_storage_secret:
           self.nicegui_storage_secret = self.secret_key
       return self

Após as alterações, execute:
  docker-compose up -d postgres redis
  make dev
Acesse http://localhost:8000 e confirme que a página carrega (mesmo que vazia).
Acesse http://localhost:8000/api/v1/health e confirme {"status":"healthy"}.
```

---

# PROMPTS DE IMPLEMENTAÇÃO — Execute após R01–R04, na ordem

**Stack atual confirmada:** FastAPI + NiceGUI (Python 3.12). Zero JavaScript/npm.  
Os prompts 02, 03 e 04 originais (backend: modelos, migrações, schemas Pydantic)
**continuam válidos e não precisam ser refeitos.**

---

## FASE 1 — Setup e Engine de Cálculo (Prompts 01–06)

---

### Prompt 01 — SimulationState: Estado Reativo Central

```
Em /backend/app/ui/state/simulation_state.py do SimulaRenda, implemente a
dataclass SimulationState que centraliza todo o estado reativo da UI:

```python
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional
from enum import Enum

class FeasibilityStatus(str, Enum):
    VIABLE = "viable"
    WARNING = "warning"
    UNVIABLE = "unviable"

@dataclass
class SimulationState:
    # --- Inputs: Situação Atual ---
    current_age: int = 30
    current_patrimony: Decimal = Decimal('0')
    monthly_contribution: Decimal = Decimal('1000')

    # --- Inputs: Metas ---
    desired_monthly_income: Decimal = Decimal('10000')
    retirement_age: int = 55
    life_expectancy: int = 90

    # --- Inputs: Parâmetros Econômicos ---
    inflation_rate: Decimal = Decimal('0.045')
    annual_real_return: Decimal = Decimal('0.06')
    safe_withdrawal_rate: Decimal = Decimal('0.04')

    # --- Inputs: Aposentadoria Pública ---
    public_pension_enabled: bool = False
    public_pension_amount: Decimal = Decimal('0')
    public_pension_start_age: int = 65
    public_pension_in_today_reais: bool = True

    # --- Inputs: Previdência Privada ---
    private_pension_enabled: bool = False
    private_pension_amount: Decimal = Decimal('0')
    private_pension_start_age: int = 60
    private_pension_modality: str = 'lifetime'  # lifetime | fixed_term | lump_sum
    private_pension_term_years: Optional[int] = None
    private_pension_in_today_reais: bool = True

    # --- Outputs (preenchidos pelo calculator) ---
    results: Optional[dict] = None
    is_calculating: bool = False

    # --- Metadados de persistência ---
    is_dirty: bool = False
    saved_simulation_id: Optional[str] = None
    saved_simulation_name: Optional[str] = None

    def to_parameters_dict(self) -> dict:
        """Converte state para o schema SimulationParameters (usado no save)."""
        return {
            "current_age": self.current_age,
            "current_patrimony": float(self.current_patrimony),
            "monthly_contribution": float(self.monthly_contribution),
            "desired_monthly_income": float(self.desired_monthly_income),
            "retirement_age": self.retirement_age,
            "life_expectancy": self.life_expectancy,
            "inflation_rate": float(self.inflation_rate),
            "annual_real_return": float(self.annual_real_return),
            "safe_withdrawal_rate": float(self.safe_withdrawal_rate),
            "public_pension": {
                "enabled": self.public_pension_enabled,
                "monthly_amount": float(self.public_pension_amount),
                "start_age": self.public_pension_start_age,
                "amount_in_today_reais": self.public_pension_in_today_reais,
            },
            "private_pension": {
                "enabled": self.private_pension_enabled,
                "monthly_amount": float(self.private_pension_amount),
                "start_age": self.private_pension_start_age,
                "modality": self.private_pension_modality,
                "term_years": self.private_pension_term_years,
                "amount_in_today_reais": self.private_pension_in_today_reais,
            },
        }

    def is_valid(self) -> tuple[bool, list[str]]:
        """Retorna (valido, lista_de_erros)."""
        errors = []
        if self.monthly_contribution <= 0:
            errors.append("Aporte mensal deve ser maior que zero")
        if self.retirement_age <= self.current_age:
            errors.append("Idade de aposentadoria deve ser maior que a idade atual")
        if self.life_expectancy <= self.retirement_age:
            errors.append("Expectativa de vida deve ser maior que a idade de aposentadoria")
        if self.public_pension_enabled:
            if self.public_pension_start_age < self.retirement_age:
                errors.append("Início do INSS não pode ser antes de parar de trabalhar")
            if self.public_pension_amount <= 0:
                errors.append("Valor do benefício público deve ser maior que zero")
        if self.private_pension_enabled:
            if self.private_pension_start_age < self.retirement_age:
                errors.append("Início da previdência não pode ser antes de parar de trabalhar")
            if self.private_pension_amount <= 0:
                errors.append("Valor do benefício privado deve ser maior que zero")
        return len(errors) == 0, errors
```

Escreva testes em tests/test_simulation_state.py:
- to_parameters_dict() retorna dict com todas as chaves esperadas
- is_valid() retorna False quando retirement_age <= current_age
- is_valid() retorna False quando public_pension_start_age < retirement_age
- is_valid() retorna True com valores padrão válidos
- is_valid() retorna lista de erros descritivos para cada violação
```

---

### Prompt 02 — Engine de Cálculo (TDD Completo)

```
Em /backend/app/services/calculator.py do SimulaRenda, implemente a engine
de cálculo financeiro com TDD completo.

ESCREVA OS TESTES PRIMEIRO em tests/test_calculator.py antes de qualquer
linha de implementação. Meta: 100% de cobertura.

Funções a implementar (todas com type hints e Decimal):

1. calculate_future_value(pv: Decimal, pmt: Decimal,
                          annual_rate: Decimal, months: int) -> Decimal
   FV = PV*(1+r)^n + PMT*((1+r)^n - 1)/r  onde r = annual_rate/12
   Caso especial: se annual_rate == 0 → FV = PV + PMT * months

2. calculate_required_patrimony(desired_income: Decimal,
                                 safe_withdrawal_rate: Decimal,
                                 active_pensions_income: Decimal) -> Decimal
   P = (desired_income - active_pensions_income) * 12 / safe_withdrawal_rate

3. calculate_required_contribution(target: Decimal, pv: Decimal,
                                    annual_rate: Decimal, months: int) -> Decimal
   PMT reverso; retorna Decimal(0) se pv*(1+r)^n >= target

4. adjust_for_inflation(value: Decimal, inflation_rate: Decimal,
                         years: int) -> Decimal
   value * (1 + inflation_rate)^years

5. simulate_phases(params: SimulationParameters) -> list[PhaseResult]
   Constrói as fases a partir dos eventos previdenciários:
   - Ordena eventos habilitados por start_age
   - Fase inicial: retirement_age → primeiro start_age (ou life_expectancy)
   - Fase por evento: start_age_N → start_age_N+1
   - Fase final: último start_age → life_expectancy
   - Cada fase: from_age, to_age, sources, monthly_withdrawal_from_patrimony

6. simulate_projection(params: SimulationParameters
                       ) -> tuple[list[ProjectionPoint], bool, Optional[int]]
   Retorna (série de pontos, patrimony_exhausted, exhaustion_age)
   Fase acumulação: mês a mês até retirement_age
   Fase retirada: mês a mês até life_expectancy
   Patrimônio nunca negativo (clamp em 0)

7. run_full_simulation(params: SimulationParameters) -> SimulationResults
   Orquestra tudo; determina feasibility_status

Casos de teste obrigatórios:
- Patrimônio já suficiente → required_contribution = 0 (não negativo)
- Taxa real = 0% → só soma aportes
- Inflação = 0% → valores sem correção
- Ambas pensões com start_age = retirement_age → sem gap
- Gap de 15 anos → fases corretas e alerta no exhaustion_age
- Patrimônio esgota antes da expectativa de vida → patrimony_exhausted=True
- Fase com fixed_term: benefício cessa após term_years, fase seguinte recalcula
- Divisão por zero impossível: safe_withdrawal_rate nunca é 0 (validado no schema)

Execute: pytest tests/test_calculator.py --cov=app/services/calculator --cov-fail-under=100
```

---

### Prompt 03 — Engine de Cálculo: Casos de Borda

```
Em tests/test_calculator.py do SimulaRenda, adicione os testes de borda que
garantem robustez da engine. Execute-os; se algum falhar, corrija calculator.py.

Casos a cobrir:

1. retirement_age = current_age + 1 (acumulação de apenas 1 ano)
   → FV deve ser calculado corretamente para 12 meses

2. life_expectancy = retirement_age + 1 (usufruto de apenas 1 ano)
   → phases deve ter exatamente 1 fase
   → projection_series deve ter pontos apenas até essa idade

3. Patrimônio atual = 0 e aporte = 0
   → FV = 0; required_contribution = target

4. Taxa de retirada = 10% (máxima permitida)
   → required_patrimony menor; status mais provavelmente viable

5. Previdência privada com modality=lump_sum, start_age=60
   → Deve ser modelada como pagamento único: sem renda mensal recorrente após o recebimento
   → Adiciona o valor ao patrimônio em start_age em vez de reduzir a retirada mensal

6. Previdência privada com modality=fixed_term, term_years=10, start_age=60
   → Benefício ativo dos 60 aos 70; após 70 some das sources
   → Phase de 60-70 inclui private_pension; phase de 70+ não inclui

7. Dois benefícios com mesmo start_age (raro mas possível)
   → Não duplicar fases; ambos entram na mesma fase

8. desired_monthly_income menor que a soma dos benefícios
   → monthly_withdrawal_from_patrimony = 0 (não negativo)
   → Patrimônio só cresce na fase de retirada

9. Todos os valores em Decimal com precisão máxima
   → Resultado de calculate_future_value não deve ter mais de 2 casas decimais monetárias
   → Diferença de resultado entre Decimal e float deve ser detectável (assert diferenças > 0.01 para inputs grandes)

Configure coverage:
pytest tests/test_calculator.py --cov=app/services/calculator --cov-report=html
Abra htmlcov/index.html e confirme 100%. Corrija qualquer branch não coberto.
```

---

### Prompt 04 — Autenticação JWT e Google OAuth

```
(Conteúdo idêntico ao Prompt 06 da versão anterior — backend não mudou)

No /backend/app do SimulaRenda, implemente autenticação completa:

1. app/core/security.py:
   - hash_password(plain: str) -> str usando bcrypt cost=12
   - verify_password(plain: str, hashed: str) -> bool
   - create_access_token(user_id: UUID) -> str (JWT HS256, exp=15min)
   - create_refresh_token(user_id: UUID) -> str (JWT HS256, exp=7dias)
   - decode_token(token: str) -> dict (lança HTTPException 401 se inválido/expirado)

2. app/services/auth_service.py:
   - register(db, data: RegisterRequest) -> User
   - login(db, data: LoginRequest) -> TokenResponse
   - google_auth(db, code: str, redirect_uri: str) -> TokenResponse
   - refresh_token(db, refresh_token: str) -> TokenResponse
   - logout(redis_client, refresh_token: str) -> None (blocklist no Redis, TTL=7dias)

3. app/api/v1/routes/auth.py:
   POST /register, POST /login, POST /google, POST /refresh, POST /logout

Testes em tests/test_auth.py:
- Email duplicado → 409
- Senha errada → 401
- Token expirado → 401
- Logout invalida token (segundo uso → 401)
- Google OAuth mockado com httpx_mock
```

---

### Prompt 05 — CRUD de Simulações (API REST)

```
(Conteúdo idêntico ao Prompt 07 da versão anterior — backend não mudou)

No /backend/app/api/v1/routes/simulations.py do SimulaRenda:

POST   /simulations/calculate  → calcula sem persistir (rate limit 30/min)
POST   /simulations            → cria e salva (requer auth)
GET    /simulations            → lista paginada do usuário
GET    /simulations/{id}       → detalhe
PUT    /simulations/{id}       → atualiza nome/parâmetros (recalcula se params mudou)
DELETE /simulations/{id}       → remove
POST   /simulations/{id}/share → {enable: bool} → gera/revoga share_token
GET    /simulations/shared/{token} → público, sem auth

Regra importante: results é SEMPRE recalculado no servidor no POST e PUT.
Nunca aceitar results enviados pelo cliente.

Testes de integração em tests/test_simulations.py cobrindo todos os endpoints,
autorização e casos de erro.
```

---

### Prompt 06 — Seed de Dados para Desenvolvimento

```
Em /backend/scripts/ do SimulaRenda, crie dois scripts:

seed_dev.py:
  Cria dados de desenvolvimento ao rodar: python scripts/seed_dev.py
  - 3 usuários de teste:
    dev@simularenda.com / Dev@12345
    usuario@teste.com  / Teste@123
    admin@simularenda.com / Admin@123
  - 5 simulações para cada usuário com parâmetros variados,
    cobrindo os três status: viable, warning e unviable
  - Pelo menos 2 simulações com share_token gerado (is_public=True)
  - Script é idempotente: rodar 2x não duplica dados

reset_dev.py:
  - Verifica que DATABASE_URL contém 'localhost' ou 'dev' (proteção)
  - DROP + recria todas as tabelas via Alembic
  - Chama seed_dev.py

Atualize o Makefile:
  seed:     cd backend && python scripts/seed_dev.py
  reset-db: cd backend && python scripts/reset_dev.py
  shell:    cd backend && python -c "import asyncio; from app.db.session import AsyncSessionLocal; ..."

Testes em tests/test_scripts.py:
- seed não falha em banco limpo
- seed é idempotente (rodar 2x não duplica usuários)
- reset_dev lança ValueError se DATABASE_URL não contiver 'localhost' ou 'dev'
```

---

## FASE 2 — UI NiceGUI: Formulário (Prompts 07–14)

---

### Prompt 07 — Layout Base e Navegação

```
Em /backend/app/ui/pages/ do SimulaRenda, implemente o layout base e a
navegação que envolve todas as páginas.

Crie app/ui/components/layout.py com a função page_layout(title: str):
  Context manager que envolve o conteúdo de cada página com:
  - Header fixo no topo:
    - Esquerda: logo "💰 SimulaRenda" (ui.link → '/')
    - Direita (se autenticado, lendo app.storage.user):
        Avatar com iniciais do nome em ui.avatar
        ui.button "Minhas Simulações" → '/minhas-simulacoes'
        ui.button "Sair" → chama logout e redireciona para '/'
    - Direita (se não autenticado):
        ui.button "Entrar" → '/entrar'
        ui.button "Cadastrar" (outline) → '/cadastrar'
  - Conteúdo central com max-width 1200px e padding lateral
  - Footer simples com copyright

Implemente app/ui/pages/home.py com a função create():
  @ui.page('/')
  async def home_page():
      with page_layout("SimulaRenda — Planeje sua Independência Financeira"):
          # Placeholder por enquanto — componentes adicionados nos próximos prompts
          ui.label("Formulário em construção").classes("text-2xl")

Implemente páginas placeholder (apenas rota + layout + label) para:
  /entrar, /cadastrar, /minhas-simulacoes, /simulacao/{id}, /compartilhado/{token}

Paleta de cores do projeto (adicione em CSS customizado via ui.add_head_html):
  --color-primary: #0F766E
  --color-primary-light: #14B8A6
  --color-success: #16A34A
  --color-warning: #D97706
  --color-danger: #DC2626

Teste E2E em e2e/test_navigation.py:
- GET / retorna 200
- GET /entrar retorna 200
- GET /minhas-simulacoes redireciona para /entrar (sem auth)
- Header contém "SimulaRenda"
```

---

### Prompt 08 — Seção: Situação Atual e Metas

```
Em /backend/app/ui/components/simulation_form.py do SimulaRenda, implemente
as duas primeiras seções do formulário usando NiceGUI.

A função build_simulation_form(state: SimulationState, on_change: Callable)
monta o formulário completo. Neste prompt, implemente as seções 1 e 2.

Seção 1 — "Situação Atual":
  ui.card com ui.card_section:
    - Patrimônio atual investido:
        ui.number(label='Patrimônio atual investido', prefix='R$', min=0, step=1000)
        .bind_value(state, 'current_patrimony')
        .on('update:model-value', on_change)
        + ui.tooltip("Some todos os seus investimentos: CDB, fundos, ações, previdência...")

    - Aporte mensal:
        ui.number(label='Aporte mensal', prefix='R$', min=0, step=100)
        .bind_value(state, 'monthly_contribution')
        .on('update:model-value', on_change)
        + ui.tooltip("Quanto você investe por mês. Inclua aportes em previdência privada.")

    - Idade atual:
        Row com ui.slider(min=18, max=70) e ui.number(min=18, max=70) sincronizados
        bind_value em ambos para state.current_age

Seção 2 — "Metas de Independência":
  ui.card com ui.card_section:
    - Renda mensal desejada:
        ui.number(label='Renda mensal desejada', prefix='R$', min=100, step=500)
        + ui.tooltip("Valor em reais de hoje. Corrigido pela inflação automaticamente.")

    - Idade para parar de trabalhar:
        Row: slider(min=current_age+1, max=80) + number sincronizados
        Marks no slider: 50, 55, 60, 65
        ui.tooltip("Pode ser diferente da data em que começará a receber INSS...")
        Badge reativo: "Você terá X anos de aposentadoria" (life_expectancy - retirement_age)

    - Expectativa de vida:
        Row: slider(min=retirement_age+1, max=110, value=90) + number sincronizados
        Quando retirement_age muda e life_expectancy <= novo retirement_age:
          ajustar automaticamente life_expectancy = retirement_age + 1

Testes unitários em tests/ui/test_form_sections.py:
- Ajuste automático de life_expectancy ao mudar retirement_age
- Badge mostra diferença correta
- on_change é chamado ao atualizar qualquer campo
```

---

### Prompt 09 — Seção: Aposentadoria Pública

```
Em build_simulation_form() do SimulaRenda, adicione a seção de aposentadoria pública.

Seção 3 — "Aposentadoria Pública (INSS / Regime Próprio)":

  ui.expansion("Aposentadoria Pública (INSS / Regime Próprio)", icon="account_balance"):
    Header com ui.switch vinculado a state.public_pension_enabled
    Conteúdo (visível apenas se switch ON via .bind_visibility_from):

      - Valor do benefício:
          ui.number(label='Valor mensal do benefício', prefix='R$', min=1)
          .bind_value(state, 'public_pension_amount')
          + ui.tooltip("Consulte o extrato no Meu INSS (meu.inss.gov.br).")

      - Idade de início do recebimento:
          Row: slider(min=state.retirement_age, max=80) + number sincronizados
          bind a state.public_pension_start_age
          ui.tooltip("Pode ser igual ou posterior à idade de parar de trabalhar...")

      - Alerta de gap (reativo, recalculado quando start_age ou retirement_age muda):
          Se public_pension_start_age > retirement_age:
            ui.banner(type='warning'):
              "⚠️ Gap de {start_age - retirement_age} anos sem este benefício.
               Seu patrimônio precisará cobrir R$ {desired_monthly_income}/mês neste período."
          Visível apenas quando o gap > 0

      - Toggle "O valor informado está em reais de hoje?":
          ui.switch.bind_value(state, 'public_pension_in_today_reais')

Testes:
- Campos ficam visíveis apenas quando switch ON
- Alerta de gap aparece quando start_age > retirement_age
- Alerta desaparece quando start_age == retirement_age
- Slider de start_age não permite valor < retirement_age
```

---

### Prompt 10 — Seção: Previdência Privada

```
Em build_simulation_form() do SimulaRenda, adicione a seção de previdência privada.

Seção 4 — "Previdência Privada (PGBL / VGBL)":

  Estrutura análoga ao Prompt 09 com:

  - Valor mensal do benefício (mesmo padrão)

  - Idade de início do recebimento (mesmo padrão, mesma lógica de gap)

  - Modalidade:
      ui.select(options={
          'lifetime': 'Renda Vitalícia — pago enquanto você viver',
          'fixed_term': 'Prazo Certo — você define quantos anos',
          'lump_sum': 'Pagamento Único — recebe tudo de uma vez'
      }).bind_value(state, 'private_pension_modality')
      + tooltips explicativos para cada opção

  - Prazo em anos (visível apenas se modality == 'fixed_term'):
      ui.number(label='Prazo (anos)', min=1, max=40)
      .bind_value(state, 'private_pension_term_years')
      .bind_visibility_from(state, 'private_pension_modality',
                            value='fixed_term')

  - Toggle "Valor em reais de hoje?"

  Mini-timeline (visível quando AMBAS as pensões estão habilitadas):
    Exibe os dois start_ages em sequência visual mostrando qual começa primeiro.
    Exemplo: "Prev. Privada (60 anos) → INSS (65 anos)"

Testes:
- Campo de prazo visível apenas com fixed_term
- Mini-timeline aparece apenas quando ambos habilitados
- Mini-timeline ordena corretamente qualquer combinação de start_ages
```

---

### Prompt 11 — Seção: Parâmetros Econômicos

```
Em build_simulation_form() do SimulaRenda, adicione a seção de parâmetros econômicos.

Seção 5 — "Parâmetros Econômicos Avançados" (colapsada por padrão):

  ui.expansion("⚙️ Parâmetros econômicos avançados", value=False):

    - Inflação anual projetada (%):
        ui.number(label='Inflação anual', suffix='% a.a.', min=0, max=20,
                  step=0.1, value=4.5)
        bind a state.inflation_rate com conversão /100 no getter e *100 no setter
        + ui.badge("Meta Banco Central 2026: 3,0%", color='green')
        + ui.tooltip("Taxa de inflação esperada ao ano...")

    - Rendimento anual real (%):
        ui.number(label='Rendimento real', suffix='% a.a.', min=0, max=30,
                  step=0.1, value=6.0)
        + ui.badge("Tesouro IPCA+ 2035: ~6,2% a.a.", color='teal')
        + ui.tooltip("Retorno dos investimentos descontada a inflação...")

    - Taxa de retirada segura (%):
        ui.number(label='Taxa de retirada', suffix='% a.a.', min=1, max=10,
                  step=0.5, value=4.0)
        + ui.badge("Regra dos 4% (Estudo Trinity, EUA)", color='blue')
        + ui.tooltip("% do patrimônio que pode ser retirado anualmente...")

    - Botão "Restaurar padrões":
        ui.button("Restaurar padrões", icon='restore', on_click=reset_economic_params)
        reset_economic_params: restaura inflation_rate=0.045, annual_real_return=0.06,
                                safe_withdrawal_rate=0.04 e chama on_change

Testes:
- Restaurar padrões redefine os três campos
- Conversão %↔decimal correta (4.5 exibido = 0.045 no state)
- on_change chamado após restaurar
```

---

### Prompt 12 — Integração do Formulário com a Engine

```
Em /backend/app/ui/pages/home.py do SimulaRenda, integre o formulário
completo com a engine de cálculo, criando o loop reativo principal.

Implemente a função recalculate(state: SimulationState):
  1. Verifica state.is_valid() → se inválido, state.results = None; retorna
  2. Converte state para SimulationParameters usando state.to_parameters_dict()
  3. Chama calculator.run_full_simulation(params) diretamente (sem HTTP)
  4. state.results = results (dict serializado do SimulationResults)
  5. state.is_dirty = True

Na página home_page():
  - Instancia SimulationState() por sessão (via app.storage.user ou variável local)
  - Chama recalculate(state) ao inicializar (com valores padrão)
  - Passa on_change=lambda: recalculate(state) para build_simulation_form()

Layout da página:
  Desktop (lg: duas colunas via ui.row):
    Coluna esquerda (45%): formulário com scroll
    Coluna direita (55%): painel de resultados (sticky — próximos prompts)

  Mobile (< 768px, via classes responsivas do Quasar/NiceGUI):
    Coluna única: formulário → resultados → gráficos

Estado inicial sem dados:
  Se state.results é None:
    Coluna de resultados exibe: ui.icon("insights") + label "Preencha os campos
    ao lado para ver sua projeção de independência financeira"

Testes E2E em e2e/test_home.py:
- Página carrega sem erro
- Preencher aporte mensal dispara recálculo (results não None após interação)
- Layout de duas colunas em viewport 1280px
- Layout de coluna única em viewport 390px
```

---

### Prompt 13 — Painel de Resultados: Cards e Banner de Viabilidade

```
Em /backend/app/ui/components/results_panel.py do SimulaRenda, implemente
o painel de resultados que exibe os cálculos em tempo real.

Função build_results_panel(state: SimulationState):
  Decorada com @ui.refreshable para re-renderizar quando state.results muda.

  Se state.results is None:
    Exibe estado vazio (ícone + mensagem)
    Retorna

  Banner de viabilidade (acima dos cards):
    viable:  ui.banner com icon='check_circle', color='positive'
             "✅ Plano viável! Com os aportes atuais você atinge a independência."
    warning: ui.banner com icon='warning', color='warning'
             "⚠️ Plano com ajuste necessário. Você atingirá 80–100% do objetivo."
    unviable: ui.banner com icon='error', color='negative'
             "❌ Plano inviável com os parâmetros atuais."

  Grid de 6 cards (ui.grid(columns=3) no desktop, columns=2 no mobile):
    1. "Patrimônio Necessário"   — valor grande, destaque
    2. "Patrimônio Projetado"    — cor conforme feasibility_status
    3. "Aporte Mensal Necessário"
    4. "Diferença (Gap)"         — verde se negativo (sobra), vermelho se positivo (falta)
    5. "Rendimento Anual Real"   — formato percentual
    6. "Inflação Projetada"      — formato percentual

  Cada card: ui.card > ui.card_section com:
    ui.label(label).classes('text-caption text-grey')
    ui.label(valor_formatado).classes('text-h5 text-weight-bold')

  Valores monetários formatados como "R$ 1,5M" (abreviação para ≥ 1.000.000)
  e "R$ 850.000" para menores.

  Sugestões automáticas (se warning ou unviable):
    ui.expansion("💡 Sugestões para viabilizar o plano"):
      - "Aumentar o aporte mensal em R$ X atingiria o objetivo"
      - "Postergar a aposentadoria X anos resolveria o gap"
      (calculados a partir dos results)

Testes:
- Banner correto para cada feasibility_status
- Card de gap verde quando negativo, vermelho quando positivo
- Formatação "R$ 1,5M" para 1.500.000
- Sugestões aparecem para warning e unviable, não para viable
```

---

### Prompt 14 — Timeline de Eventos e Gráficos Plotly

```
Em /backend/app/ui/components/ do SimulaRenda, implemente a timeline e
os dois gráficos Plotly.

1. pension_timeline.py — build_pension_timeline(state: SimulationState):
   @ui.refreshable, renderiza com base em state.results.

   Timeline horizontal usando ui.stepper ou HTML customizado via ui.html:
   [Hoje] → [Parar de trabalhar] → [Benefício 1] → [Benefício 2] → [Expectativa de vida]
   (ordem dos benefícios determinada pelos start_ages)

   Para cada segmento: rótulo da fase, duração, renda disponível, cor de fundo:
   - Sem benefício: fundo laranja claro
   - Um benefício: fundo amarelo claro
   - Todos os benefícios: fundo verde claro

   Alerta de gap se phases[0].sources == ["patrimony"] e duração > 0:
     ui.card(color='warning'): "⚠️ Gap de X anos sem benefício previdenciário..."

2. patrimony_chart.py — build_patrimony_chart(state: SimulationState):
   @ui.refreshable, usa ui.plotly.

   Constrói figura Plotly com:
   - Trace Area: pontos de acumulação (até retirement_age), fill='tozeroy', cor teal
   - Trace Line: pontos de retirada (após retirement_age), cor teal mais escuro
   - Linha vertical pontilhada em retirement_age ("Parar de trabalhar")
   - Linha vertical pontilhada em public_pension.start_age (se habilitado)
   - Linha vertical pontilhada em private_pension.start_age (se habilitado)
   - Linha horizontal pontilhada em required_patrimony ("Patrimônio necessário")
   - Layout: bg branco, eixo X = "Idade", eixo Y = "Patrimônio (R$)"
   - Tooltip: age, patrimony formatado, fase atual

3. income_chart.py — build_income_chart(state: SimulationState):
   @ui.refreshable, usa ui.plotly.

   Bar chart empilhado com uma barra por fase:
   - Stack 1: "Retirada do Patrimônio" (teal)
   - Stack 2: "INSS / Aposent. Pública" (azul, se habilitado)
   - Stack 3: "Previdência Privada" (violeta, se habilitado)
   - Linha horizontal: desired_monthly_income ("Renda desejada")
   - Eixo X: rótulo da fase ("55–60 anos")
   - Eixo Y: R$/mês

Integre os três componentes na home_page() abaixo do painel de resultados.

Testes E2E:
- Gráfico SVG presente no DOM após preenchimento do formulário
- Timeline exibe número correto de segmentos conforme benefícios habilitados
- Alerta de gap aparece e desaparece corretamente
```

---

## FASE 3 — Autenticação e Persistência (Prompts 15–21)

---

### Prompt 15 — Páginas de Login e Cadastro

```
Em /backend/app/ui/pages/ do SimulaRenda, implemente login.py e register.py.

login.py — @ui.page('/entrar'):
  Card centralizado com:
  - ui.input label='Email', type='email' com validação
  - ui.input label='Senha', type='password' com validação
  - ui.checkbox "Lembrar de mim" (controla duração da sessão)
  - ui.button "Entrar" → chama auth_service.login() →
      sucesso: app.storage.user['user_id'] = id; app.storage.user['user_name'] = name
               migrar simulações locais → redirect para '/' ou rota de origem
      erro: ui.notify(mensagem_erro, type='negative')
  - ui.button "Entrar com Google" (OAuth — abre ui.open para URL do Google)
  - ui.link "Esqueci minha senha" → '/esqueci-senha'
  - ui.link "Criar conta" → '/cadastrar'

register.py — @ui.page('/cadastrar'):
  Card centralizado com:
  - ui.input "Nome completo"
  - ui.input "Email"
  - ui.input "Senha" (mínimo 8 caracteres)
  - ui.input "Confirmar senha" + validação de igualdade
  - ui.button "Cadastrar" → auth_service.register() →
      sucesso: mesmo fluxo do login (set storage + migrar + redirect)
      erro: ui.notify
  - ui.button "Cadastrar com Google"
  - ui.link "Já tenho conta" → '/entrar'

Função migrate_local_simulations(user_id: str):
  - Lê app.storage.user.get('local_simulations', [])
  - Para cada uma: POST /api/v1/simulations via httpx (com token do usuário)
  - Limpa app.storage.user['local_simulations'] = []
  - ui.notify(f"{n} simulações migradas para sua conta")

Testes E2E:
- Login com credenciais corretas → redireciona para /
- Login com senha errada → notificação de erro visível
- Cadastro com emails diferentes → notificação de erro
- Após login, header mostra avatar e "Minhas Simulações"
```

---

### Prompt 16 — Salvar Simulação com Dialog de Nome

```
Em /backend/app/ui/pages/home.py do SimulaRenda, implemente o fluxo de
salvar simulação.

Botão "Salvar Simulação" no rodapé do formulário (habilitado quando form é válido):

Fluxo (usuário autenticado — app.storage.user.get('user_id') is not None):
  1. Se state.saved_simulation_name is None:
     Abre ui.dialog com:
       ui.input label='Nome da simulação',
                value=f"Simulação — {datetime.now().strftime('%b %Y')}",
                on_keydown Enter → confirmar
       ui.button "Salvar" + ui.button "Cancelar"
  2. POST /api/v1/simulations via httpx com token do usuário
     Body: {name, parameters: state.to_parameters_dict()}
  3. Sucesso: state.saved_simulation_id = id; state.is_dirty = False
              ui.notify("Simulação salva!", type='positive')
  4. Erro: ui.notify("Erro ao salvar. Tente novamente.", type='negative')

Fluxo (usuário não autenticado):
  1. Verifica len(app.storage.user.get('local_simulations', [])):
     < 4: salva diretamente com ui.notify de aviso
     == 4: salva + ui.notify "Você tem espaço para mais 1 simulação local..."
     == 5: ui.dialog bloqueante "Limite de simulações locais atingido.
           Crie uma conta gratuita ou exclua uma simulação existente."
           Botões: "Criar conta" → '/cadastrar' | "Ver minhas simulações" → '/minhas-simulacoes'

Botão "Limpar" com ui.dialog de confirmação antes de resetar state.

Indicador is_dirty:
  Quando state.is_dirty=True e saved_simulation_id is not None:
    Exibe ui.badge("Não salvo", color='orange') próximo ao botão salvar

Testes E2E:
- Dialog de nome abre ao clicar salvar sem nome
- Simulação aparece em /minhas-simulacoes após salvar
- Limite de 5 locais exibe dialog bloqueante
```

---

### Prompt 17 — Página: Minhas Simulações

```
Em /backend/app/ui/pages/simulations.py do SimulaRenda, implemente a
página de histórico de simulações.

@ui.page('/minhas-simulacoes'):
  Redirecionar para '/entrar' se não autenticado.

  Header da página:
    - Título "Minhas Simulações" + badge com contagem total
    - ui.button "Nova Simulação" → '/'
    - ui.input de busca (filtra localmente por nome)

  Lista de simulações (GET /api/v1/simulations via httpx):
    ui.grid de SimulationCards (2 colunas desktop, 1 mobile)
    Paginação: botão "Carregar mais" (página seguinte da API)

  Estado vazio:
    ui.icon("savings") + "Você ainda não salvou nenhuma simulação."
    ui.button "Fazer minha primeira simulação" → '/'

  SimulationCard (build_simulation_card em components/simulation_card.py):
    ui.card clicável → '/simulacao/{id}':
      - Nome da simulação (ui.label com edição inline ao duplo clique)
      - Data formatada (ex: "2 jun. 2026")
      - Badge de status (viable=verde, warning=amarelo, unviable=vermelho)
      - Dois valores: "Necessário: R$ X" e "Projetado: R$ Y"
      - ui.linear_progress value=projected/required (clamp 0–1)
      - Menu kebab (ui.button icon='more_vert' + ui.menu):
          Renomear: PUT /simulations/{id} {name: novo_nome}
          Duplicar: POST /simulations com mesmo parameters + "Cópia de " no nome
          Compartilhar: abre dialog com toggle e URL copiável
          Excluir: ui.dialog de confirmação → DELETE /simulations/{id}

  Modo comparação:
    ui.button "Comparar" → ativa checkbox em cada card
    Ao selecionar 2–3 cards: ui.button "Ver comparação (N)" aparece → abre ComparisonDialog

Testes E2E:
- Lista carrega com simulações do usuário logado
- Excluir remove o card da lista
- Renomear atualiza o nome no card
- Estado vazio exibido quando lista vazia
```

---

### Prompt 18 — Comparação de Simulações

```
Em /backend/app/ui/components/ do SimulaRenda, implemente o dialog de
comparação de simulações.

comparison_dialog.py — build_comparison_dialog(simulations: list[dict]):
  ui.dialog fullscreen=True:

    Título: "Comparação de Simulações ({n} selecionadas)"
    ui.button "Fechar" (canto superior direito)

    Tabela comparativa (ui.table):
      Colunas: Métrica | Simulação 1 | Simulação 2 | Simulação 3
      Linhas:
        Nome, Data, Status (badge colorido),
        Patrimônio Necessário, Patrimônio Projetado, Gap,
        Aporte Mensal Necessário, Idade de Aposentadoria,
        Renda Desejada, Rendimento Real, Inflação
      Para cada linha de valor numérico:
        Célula com menor valor em vermelho claro, maior em verde claro
        (exceto para Gap: menor é melhor)

    Gráfico Plotly sobreposto (build_comparison_chart):
      Uma linha por simulação na projection_series
      Cores distintas: teal, laranja, roxo
      Legenda clicável (visibleonly ao clicar)
      Linha horizontal pontilhada para required_patrimony de cada simulação
      (mesma cor da simulação, tracejado diferente)

Integração em simulations.py:
  Ao clicar "Ver comparação": carrega detalhes das simulações selecionadas via
  GET /api/v1/simulations/{id} para cada uma, abre build_comparison_dialog

Testes E2E:
- Dialog abre com dados de 2 e de 3 simulações
- Célula com melhor valor destacada em verde
- Gráfico renderizado com N linhas
```

---

### Prompt 19 — Página de Detalhe e Edição

```
Em /backend/app/ui/pages/simulation_detail.py do SimulaRenda, implemente
a página de detalhe de uma simulação.

@ui.page('/simulacao/{id}'):
  Redirecionar para '/entrar' se não autenticado.
  GET /api/v1/simulations/{id} → carrega parâmetros e resultados.
  404: ui.notify + redirect para '/minhas-simulacoes'.

  Header da página:
    - Nome editável inline (ui.input com save no blur e no Enter)
      PUT /api/v1/simulations/{id} {name: novo_nome} ao salvar
    - Data de criação
    - Botões: "Salvar alterações" (visível quando is_dirty) | "Duplicar" | "Excluir" | "Compartilhar"

  Conteúdo: formulário completo pré-preenchido + painel de resultados
    (reutiliza build_simulation_form e build_results_panel com um SimulationState
    populado a partir dos parameters salvos)

  Alterações:
    Qualquer mudança no formulário → state.is_dirty = True
    "Salvar alterações" → PUT /api/v1/simulations/{id} {parameters: state.to_parameters_dict()}
    Backend recalcula results

  Proteção de navegação:
    Se state.is_dirty e usuário tentar navegar (ui.navigate):
    ui.dialog de confirmação "Há alterações não salvas. Deseja sair?"
    Botões: "Sair sem salvar" | "Salvar e sair" | "Continuar editando"

  Toggle de compartilhamento:
    ui.switch "Compartilhar simulação publicamente"
    Ao ligar: POST /api/v1/simulations/{id}/share {enable: true}
              Exibe URL com ui.input readonly + ui.button "Copiar" (ui.clipboard)
    Ao desligar: POST {enable: false}; esconde URL

Testes E2E:
- Campos pré-preenchidos com os parâmetros salvos
- Alteração ativa o botão "Salvar alterações"
- Toggle de compartilhamento gera URL copiável
- Dialog de proteção aparece ao tentar navegar com is_dirty=True
```

---

### Prompt 20 — Página de Simulação Compartilhada

```
Em /backend/app/ui/pages/shared.py do SimulaRenda, implemente a página
de visualização pública.

@ui.page('/compartilhado/{token}'):
  Nenhuma autenticação necessária.
  GET /api/v1/simulations/shared/{token}

  Se 404: exibe ui.card centralizado:
    ui.icon('link_off', size='xl')
    "Esta simulação não existe ou o compartilhamento foi desativado."
    ui.button "Criar minha simulação" → '/'

  Se sucesso:
    Banner no topo (ui.banner color='info'):
      "Você está visualizando a simulação '[nome]' compartilhada.
       Crie a sua gratuitamente!"
      ui.button "Simular agora" → '/'

    Exibe em modo read-only (sem formulário editável):
      - Tabela de parâmetros (2 colunas: campo | valor)
      - build_results_panel (read-only, sem botão salvar)
      - build_pension_timeline
      - build_patrimony_chart
      - build_income_chart

  Meta tags OG para preview no WhatsApp (via ui.add_head_html):
    og:title: "Meu plano de independência financeira — SimulaRenda"
    og:description: "Patrimônio necessário: R$ X · Idade alvo: X anos · Status: ✅ Viável"

Testes E2E:
- Token inválido exibe mensagem de erro e CTA
- Token válido exibe dados da simulação em modo read-only
- Formulário NÃO está presente na página (apenas visualização)
- Banner de CTA presente
```

---

### Prompt 21 — Exportação PDF

```
Em /backend/app/services/ do SimulaRenda, implemente o serviço de
geração de PDF usando reportlab.

pdf_service.py — generate_simulation_pdf(simulation: dict) -> bytes:
  Retorna bytes do PDF gerado (para envio como download).

  Estrutura do PDF:
  - Cabeçalho: "SimulaRenda" em destaque + data de geração + nome da simulação
  - Seção 1 — Parâmetros: tabela 2 colunas (campo | valor), todos os inputs
  - Seção 2 — Resultados: 6 métricas principais com status de viabilidade em cor
  - Seção 3 — Fases: tabela com from_age, to_age, fontes de renda, retirada mensal
  - Seção 4 — Projeção simplificada: tabela a cada 5 anos (idade, patrimônio)
  - Rodapé: "Este simulador tem fins educacionais e não constitui
             aconselhamento financeiro."

Botão "📥 Baixar PDF" em build_results_panel:
  ui.button("Baixar PDF", icon='download', on_click=download_pdf)
  download_pdf():
    pdf_bytes = generate_simulation_pdf(state.results)
    ui.download(src=pdf_bytes, filename=f"SimulaRenda_{nome}_{data}.pdf")

Testes unitários em tests/test_pdf_service.py:
- generate_simulation_pdf retorna bytes (len > 0)
- PDF contém o nome da simulação no conteúdo
- PDF contém o valor de required_patrimony formatado
- PDF contém o disclaimer no rodapé
- Não lança exceção para qualquer combinação válida de parâmetros
```

---

## FASE 4 — Qualidade e Deploy (Prompts 22–30)

---

### Prompt 22 — Testes E2E Completos com Playwright

```
Em /backend/e2e/ do SimulaRenda, configure Playwright e implemente os
cinco cenários obrigatórios.

conftest.py:
  - fixture page: Page do Playwright com baseURL=http://localhost:8000
  - fixture authenticated_page: page com login via API (set cookie de sessão)
  - BROWSER_ARGS: --no-sandbox para CI

Cenário 1 — Fluxo principal sem login:
  test_simulation_flow_unauthenticated:
  - Acessa /
  - Preenche: patrimônio=150000, aporte=3000, idade=35
  - Preenche: renda desejada=10000, aposentadoria=55
  - Verifica que cards de resultado aparecem com valores > 0
  - Verifica banner de viabilidade visível
  - Ativa switch INSS, preenche valor=2500, start_age=65
  - Verifica que alerta de gap aparece
  - Clica "Salvar Simulação" → dialog de nome aparece → confirma
  - Verifica ui.notify de sucesso

Cenário 2 — Cadastro e migração:
  test_register_and_migrate:
  - Simula sem login (salva 1 simulação local)
  - Acessa /cadastrar, preenche formulário com email aleatório
  - Verifica ui.notify "1 simulação migrada"
  - Acessa /minhas-simulacoes → card da simulação presente

Cenário 3 — Compartilhamento:
  test_sharing:
  - Login com credenciais de seed (dev@simularenda.com)
  - Abre simulação existente
  - Ativa toggle de compartilhamento → URL aparece
  - Copia URL, abre em novo contexto sem auth
  - Verifica banner "Você está visualizando" presente
  - Verifica formulário NÃO presente

Cenário 4 — Comparação:
  test_comparison:
  - Login, vai para /minhas-simulacoes (seed tem ≥ 3 simulações)
  - Clica "Comparar", seleciona 3 simulações
  - Clica "Ver comparação"
  - Verifica tabela presente com 3 colunas de simulação
  - Verifica gráfico SVG presente

Cenário 5 — Mobile:
  test_mobile_flow:
  - Mesmo que Cenário 1, viewport={"width": 390, "height": 844}
  - Verifica layout de coluna única (formulário acima, resultados abaixo)

Execute: pytest e2e/ -v --screenshot=only-on-failure
```

---

### Prompt 23 — Segurança da API

```
No /backend do SimulaRenda, implemente as medidas de segurança:

1. Rate limiting com slowapi:
   Em app/main.py: adicionar SlowAPIMiddleware
   Em cada rota: @limiter.limit("10/minute") para login, etc.

2. Headers de segurança (middleware customizado em app/core/security_headers.py):
   Para toda resposta, adicionar:
     X-Content-Type-Options: nosniff
     X-Frame-Options: SAMEORIGIN
     Referrer-Policy: strict-origin-when-cross-origin
     X-XSS-Protection: 1; mode=block
   Excluir rotas NiceGUI internas (prefixo /_nicegui/)

3. Sanitização de inputs:
   Em simulation_service.py antes de persistir:
     name = name.strip()[:255]
     name = bleach.clean(name, tags=[], strip=True)  # instale bleach
   Em auth_service.py:
     email = email.strip().lower()

4. Logs de segurança (estrutlog):
   Em auth_service.login(): logar IP + email_hash (não o email) + success/failure
   Após 5 falhas consecutivas do mesmo IP: logar WARNING "possible brute force"
   NUNCA logar senhas, tokens ou valores financeiros

5. Endpoint GET /api/v1/health:
   Retorna:
     { "status": "healthy"|"degraded",
       "database": "up"|"down",
       "redis": "up"|"down",
       "version": "1.0.0" }
   HTTP 200 se healthy, 503 se degraded

Testes:
- Rate limit retorna 429 na 11ª requisição de login no mesmo minuto
- Headers de segurança presentes em todas as respostas da API
- XSS no nome da simulação é sanitizado (ex: '<script>' vira '')
- /health retorna 503 quando banco está down (mock da sessão)
```

---

### Prompt 24 — Monitoramento com Prometheus e Sentry

```
No /backend do SimulaRenda, configure observabilidade:

1. Logging estruturado com structlog:
   Em app/core/logging.py: configure structlog com:
   - Produção: renderer JSON
   - Desenvolvimento: renderer colorido
   - Campos automáticos em toda requisição:
       request_id (UUID gerado por middleware), method, path,
       status_code, duration_ms, user_id (se autenticado)
   - NUNCA incluir: email, name, valores monetários, tokens

2. Métricas Prometheus (prometheus-fastapi-instrumentator):
   Instale: prometheus-fastapi-instrumentator
   Em main.py: Instrumentator().instrument(app).expose(app, endpoint='/metrics',
                                                        include_in_schema=False)
   Header de proteção: X-Metrics-Token validado em middleware

   Métricas customizadas (adicionar em app/core/metrics.py):
   - simulations_calculated_total (Counter)
   - simulations_saved_total (Counter)
   - calculation_duration_seconds (Histogram, buckets=[.01, .05, .1, .25, .5, 1])

3. Sentry:
   Em app/core/config.py: sentry_dsn: str = ""
   Em main.py lifespan:
     if settings.sentry_dsn:
         import sentry_sdk
         sentry_sdk.init(dsn=settings.sentry_dsn,
                         traces_sample_rate=0.1)

4. Incrementar métricas nos services:
   calculator.run_full_simulation: incrementa simulations_calculated_total
                                   e registra duration no Histogram
   simulation_service.create: incrementa simulations_saved_total

Testes:
- GET /metrics retorna 403 sem X-Metrics-Token
- GET /metrics retorna 200 com X-Metrics-Token correto e contém 'simulations_calculated_total'
- GET /api/v1/health retorna 200 healthy com serviços up
- GET /api/v1/health retorna 503 com DB mockado como down
```

---

### Prompt 25 — CI/CD com GitHub Actions

```
Em /.github/workflows/ do SimulaRenda, crie os pipelines:

ci.yml (trigger: push e PR para main e develop):
  Jobs:
  - test-backend:
      runs-on: ubuntu-latest
      services:
        postgres: {image: postgres:16-alpine, env: POSTGRES_*, ports: 5432}
        redis: {image: redis:7-alpine, ports: 6379}
      steps:
        - checkout
        - setup-python 3.12
        - pip install -e ".[dev]"
        - alembic upgrade head
        - pytest --cov=app --cov-fail-under=80
             --cov-report=xml --cov-report=term-missing
        - upload-artifact: coverage.xml
      env: (todas as vars do .env.example com valores de teste)

  - lint:
      steps: ruff check app/ && mypy app/

  - e2e (apenas em PRs para main):
      services: postgres + redis
      steps:
        - pip install -e ".[dev]"
        - playwright install chromium
        - uvicorn app.main:app &  (start em background)
        - sleep 3  (aguarda inicialização)
        - pytest e2e/ --screenshot=only-on-failure
        - upload-artifact: screenshots de falha

deploy-staging.yml (trigger: push para develop):
  Depende de ci.yml verde
  Build imagem Docker + push para registry
  SSH deploy no servidor de staging
  Smoke test: curl -f https://staging.simularenda.com.br/api/v1/health

deploy-prod.yml (trigger: tag v*.*.*):
  environment: production (requer aprovação manual de reviewer)
  Mesmos steps de staging
  Após deploy: smoke test completo
  Falha: rollback automático para imagem anterior

Makefile targets:
  ci-local: docker-compose up -d postgres redis && pytest && ruff check . && mypy app/
```

---

### Prompt 26 — Dockerfile de Produção e Nginx Final

```
No SimulaRenda, finalize os arquivos de produção:

backend/Dockerfile (multi-stage):
  FROM python:3.12-slim AS builder
  WORKDIR /build
  COPY pyproject.toml .
  RUN pip install --user -e ".[dev]"

  FROM python:3.12-slim AS runtime
  WORKDIR /app
  COPY --from=builder /root/.local /root/.local
  COPY . .
  RUN useradd -m -u 1000 appuser && chown -R appuser /app
  USER appuser
  ENV PATH=/root/.local/bin:$PATH
  EXPOSE 8000
  HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1
  CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000",
       "--workers", "1"]
  # workers=1 obrigatório para NiceGUI (estado de sessão não é compartilhado entre workers)

nginx.conf (produção completa):
  - HTTPS com certificado Let's Encrypt (certbot)
  - Redirect HTTP → HTTPS
  - Headers de segurança: HSTS, X-Frame-Options, etc.
  - Bloco WebSocket OBRIGATÓRIO (proxy_set_header Upgrade, Connection "upgrade")
  - proxy_read_timeout 86400 (evita timeout de sessões longas)
  - Gzip para respostas text/html, application/json
  - Cache de assets estáticos do NiceGUI: /_nicegui/static/ com Cache-Control 1 ano

docker-compose.prod.yml final com 4 serviços:
  postgres (volume persistente + healthcheck)
  redis (senha via env + maxmemory + healthcheck)
  backend (imagem buildada, env_file, restart=unless-stopped)
  nginx (imagem alpine, volumes de cert e conf, depends_on backend)

scripts/smoke_test.sh BASE_URL:
  Verificações após deploy:
  ✓ GET $BASE_URL/ → 200 (NiceGUI carrega)
  ✓ GET $BASE_URL/api/v1/health → 200 e status=healthy
  ✓ POST $BASE_URL/api/v1/simulations/calculate → 200 com required_patrimony > 0
  ✓ POST $BASE_URL/api/v1/auth/login (credenciais erradas) → 401
  ✓ GET $BASE_URL/api/v1/simulations (sem token) → 401
  ✓ GET $BASE_URL/api/v1/simulations/shared/token-invalido → 404

Adicione ao CI: rodar smoke_test.sh após cada deploy de staging e produção.
```

---

### Prompt 27 — Acessibilidade WCAG 2.1 AA

```
No SimulaRenda, audite e corrija a acessibilidade da UI NiceGUI.

NiceGUI usa Quasar Framework internamente. As correções são aplicadas via
props de acessibilidade nos componentes Quasar/HTML customizado.

1. Inputs:
   Todo ui.number, ui.input, ui.select, ui.slider deve ter aria-label explícito
   se o label visual não for suficiente para leitores de tela.
   ui.slider: adicionar props :aria-valuemin, :aria-valuemax, :aria-valuenow,
              :aria-label via .props()

2. Notificações e alertas:
   ui.notify: adicionar role='alert' para type='negative', role='status' para outros
   (via app.add_body_html com CSS override ou JavaScript mínimo via ui.run_javascript)

3. Modais:
   ui.dialog: adicionar aria-modal='true' e aria-labelledby apontando para
              o título do dialog (via .props('aria-modal="true"'))
   Garantir que foco vai para o dialog ao abrir e retorna ao elemento disparador ao fechar

4. Gráficos Plotly:
   Envolver ui.plotly em div com role='img' e aria-label descritivo:
     f"Gráfico de evolução patrimonial. Patrimônio cresce de R$ {pv} aos {current_age} anos
       até R$ {projected} aos {retirement_age} anos."
   Adicionar tabela de dados colapsável abaixo de cada gráfico:
     ui.expansion("📋 Dados do gráfico (acessível)"):
       ui.table com os mesmos dados do gráfico

5. Contraste:
   Verificar que todos os textos sobre fundo colorido têm contraste ≥ 4.5:1.
   Em especial: badges de status (viable/warning/unviable) e texto sobre cards coloridos.
   Ajustar cores se necessário.

6. Navegação por teclado:
   Verificar que todos os elementos interativos são alcançáveis via Tab.
   Testar o formulário completo apenas com teclado (sem mouse).

Execute axe-core via Playwright em cada página:
  from playwright.sync_api import Page
  def check_accessibility(page: Page, path: str):
      page.goto(path)
      violations = page.evaluate("""
          () => new Promise(resolve => {
              const s = document.createElement('script')
              s.src = 'https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js'
              s.onload = () => axe.run().then(r => resolve(r.violations))
              document.head.appendChild(s)
          })
      """)
      return violations

Nenhuma violation de nível 'critical' ou 'serious' pode estar presente em /.
```

---

### Prompt 28 — Internacionalização (i18n Ready)

```
No SimulaRenda, prepare a base de internacionalização sem implementar
múltiplos idiomas no MVP (pt-BR exclusivo).

1. Crie /backend/app/i18n/pt_BR.py com TODAS as strings visíveis ao usuário:

```python
STRINGS = {
    # Navegação
    "nav.logo": "SimulaRenda",
    "nav.my_simulations": "Minhas Simulações",
    "nav.login": "Entrar",
    "nav.register": "Cadastrar",
    "nav.logout": "Sair",
    # Formulário
    "form.current_situation": "Situação Atual",
    "form.current_patrimony": "Patrimônio atual investido",
    "form.monthly_contribution": "Aporte mensal",
    "form.current_age": "Idade atual",
    "form.independence_goals": "Metas de Independência",
    "form.desired_income": "Renda mensal desejada",
    "form.retirement_age": "Idade para parar de trabalhar",
    "form.life_expectancy": "Expectativa de vida",
    # ... (todas as strings do projeto)
    # Resultados
    "results.required_patrimony": "Patrimônio Necessário",
    "results.projected_patrimony": "Patrimônio Projetado",
    "results.required_contribution": "Aporte Mensal Necessário",
    "results.gap": "Diferença (Gap)",
    "results.viable": "✅ Plano viável!...",
    "results.warning": "⚠️ Plano com ajuste necessário...",
    "results.unviable": "❌ Plano inviável...",
    # Erros
    "error.required_field": "Campo obrigatório",
    "error.invalid_age": "Idade inválida",
    # ...
}

def t(key: str, **kwargs) -> str:
    text = STRINGS.get(key, key)
    return text.format(**kwargs) if kwargs else text
```

2. Substitua TODAS as strings hardcoded nos componentes por t('chave').
   Exemplos:
     ui.label("Patrimônio Necessário") → ui.label(t("results.required_patrimony"))
     ui.notify("Simulação salva!") → ui.notify(t("notify.simulation_saved"))

3. Formatação de moeda e datas via locale:
   Em app/i18n/formatters.py:
     format_currency(value: Decimal) -> str  (R$ 1.234,56 ou R$ 1,5M)
     format_age(age: int) -> str  (f"{age} anos")
     format_date(dt: datetime) -> str  (ex: "2 jun. 2026")

4. Script check_i18n.py:
   Varre app/ui/ em busca de strings hardcoded em português dentro de ui.*()
   Reporta como warning; falha no CI se count > 0

Testes:
- t('key_inexistente') retorna a própria chave (não lança exceção)
- format_currency(Decimal('1500000')) retorna 'R$ 1,5M'
- Todas as keys em STRINGS são usadas em pelo menos um componente (sem órfãs)
- check_i18n.py retorna 0 warnings após a substituição
```

---

### Prompt 29 — Perfil do Usuário

```
Em /backend/app/ui/pages/ do SimulaRenda, crie a página de perfil.

@ui.page('/perfil'):
  Redirecionar para '/entrar' se não autenticado.

  Seção 1 — Dados Pessoais:
    ui.input "Nome completo" pré-preenchido
    ui.input "Email" readonly
    ui.input "Data de nascimento" (type=date)
    ui.button "Salvar" → PUT /api/v1/users/me
    Ao salvar data de nascimento: atualizar idade atual no formulário principal
    (calcular current_age = anos completos desde a data de nascimento)

  Seção 2 — Segurança (apenas para usuários com senha — não OAuth):
    ui.expansion("Alterar senha"):
      ui.input "Senha atual" (type=password)
      ui.input "Nova senha" (type=password, mínimo 8 chars)
      ui.input "Confirmar nova senha"
      ui.button "Alterar" → POST /api/v1/auth/change-password

  Seção 3 — Suas Simulações:
    Badge com contagem total
    ui.link "Ver todas" → '/minhas-simulacoes'

  Seção 4 — Zona de Perigo:
    ui.expansion("⚠️ Excluir minha conta", color='negative'):
      ui.label com aviso sobre exclusão permanente (30 dias de carência)
      ui.input "Digite seu email para confirmar"
      ui.button "Excluir conta permanentemente" (só habilitado quando email correto digitado)
      → DELETE /api/v1/users/me → clearAuth → redirect para / com notify

Adicione endpoint no backend:
  PUT /api/v1/users/me → atualiza name e birth_date
  DELETE /api/v1/users/me → soft delete (sets deleted_at = now())

Testes E2E:
- Edição de nome é salva (página recarregada mostra novo nome)
- Exclusão com email incorreto mantém botão desabilitado
- Exclusão com email correto realiza logout e redireciona
```

---

### Prompt 30 — Checklist de Go-Live e Documentação Final

```
No SimulaRenda, crie os artefatos finais para o go-live.

1. scripts/pre_deploy_check.sh:
   Executa e falha se qualquer item não passar:
   □ pytest --cov=app --cov-fail-under=80
   □ pytest tests/test_calculator.py --cov=app/services/calculator --cov-fail-under=100
   □ ruff check app/ (sem erros)
   □ mypy app/ (sem erros de tipo)
   □ python scripts/check_i18n.py (sem strings hardcoded)
   □ python -c "from app.main import app" (sem ImportError)
   □ Verificar que todas as vars do .env.prod.example estão definidas no ambiente
   □ alembic check (sem migrações pendentes)

2. RUNBOOK.md na raiz:
   ## Rollback
   - docker-compose -f docker-compose.prod.yml pull backend
   - docker tag simularenda_backend:previous simularenda_backend:latest
   - docker-compose -f docker-compose.prod.yml up -d backend

   ## Verificar Logs em Produção
   - docker-compose -f docker-compose.prod.yml logs -f backend --tail=100

   ## SLOs
   - Uptime: 99.5% mensal
   - API P95: < 300ms
   - Error rate: < 0.1%

   ## Contatos de Emergência
   [preencher]

3. Atualize README.md com:
   - Descrição do produto (2 parágrafos)
   - Stack: Python 3.12 + FastAPI + NiceGUI + PostgreSQL + Redis
   - Setup em 5 passos:
       git clone ...
       cp .env.example .env  # edite as variáveis
       docker-compose up -d postgres redis
       make install && make migrate && make seed
       make dev  # acesse http://localhost:8000
   - Link para CONTEXT.md ("Para agentes de IA e novos desenvolvedores")
   - Link para o PRD

4. GitHub Actions: job post-deploy que executa smoke_test.sh e abre issue
   automaticamente se alguma verificação falhar.

Confirmação final:
  make ci-local  (deve passar 100%)
  docker-compose up --build
  scripts/smoke_test.sh http://localhost:8000
  Todos os checks devem passar antes de marcar o projeto como pronto para produção.
```

---

## Resumo das Fases

| Fase | Prompts | Entregável Principal |
|------|---------|---------------------|
| **Reversão** | R01–R04 | Remove React/npm, adiciona NiceGUI, atualiza infra |
| **1 — Engine** | 01–06 | SimulationState, calculator.py (100% cobertura), auth, CRUD API, seed |
| **2 — Formulário** | 07–14 | Layout base, 5 seções do formulário, integração reativa, resultados, gráficos |
| **3 — Autenticação** | 15–21 | Login/cadastro, salvar simulação, histórico, comparação, detalhe, compartilhado, PDF |
| **4 — Qualidade** | 22–30 | E2E Playwright, segurança, monitoramento, CI/CD, Docker prod, acessibilidade, i18n, go-live |

**Nota:** Os prompts 02, 03 e 04 originais (modelos SQLAlchemy, migrações Alembic e schemas Pydantic)  
**continuam válidos e já foram executados.** Não é necessário refazê-los.

---

*SimulaRenda — Prompts para ChatGPT Codex · v2.0 (NiceGUI) · 01/06/2026*