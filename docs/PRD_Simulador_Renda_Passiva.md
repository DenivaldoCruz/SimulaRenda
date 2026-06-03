# PRD — SimulaRenda: Simulador de Renda Passiva com Calculadora de Aposentadoria

**Versão:** 2.0 · **Data:** 01/06/2026 · **Status:** Draft  
**Stack:** FastAPI + NiceGUI (Python 3.12) · PostgreSQL 16 · Redis 7  
**Não há JavaScript, TypeScript, Node.js ou npm neste projeto.**

---

## 1. Visão Geral do Produto

### 1.1 Sumário Executivo

O **SimulaRenda** é uma aplicação web que permite ao usuário planejar sua independência financeira, calculando quanto precisa acumular para viver de renda. Considera múltiplas fontes de receita passiva (rendimentos de investimentos, aposentadoria pública e previdência privada), inflação projetada e horizonte temporal personalizado.

O diferencial central é a separação explícita entre **a idade de parar de trabalhar** e **a data de início de cada benefício previdenciário**, refletindo a realidade do planejamento financeiro brasileiro.

A interface é construída em **Python puro com NiceGUI**, rodando no mesmo processo que o backend FastAPI. Não há build step, não há `node_modules`, não há TypeScript.

### 1.2 Problema a Resolver

Calculadoras de aposentadoria existentes assumem que renda passiva e benefício previdenciário começam simultaneamente. Na prática, a pessoa pode se aposentar financeiramente aos 50 anos, mas só receber o INSS aos 65 e a previdência privada aos 60. Sem modelar esse gap, o planejamento fica subestimado e o usuário corre risco de insuficiência de caixa nos anos de transição.

Além disso, simulações feitas manualmente se perdem. O sistema deve persistir cada simulação para que o usuário possa comparar cenários ao longo do tempo.

### 1.3 Objetivos de Negócio

- Ser referência como ferramenta gratuita de planejamento de independência financeira no Brasil.
- Gerar leads qualificados via CTA para consultor financeiro parceiro (futuro monetização).
- Aumentar tempo de sessão e retorno por meio do histórico de simulações salvas.

---

## 2. Personas

### Persona A — "Planejador Antecipado"
- 30–42 anos, renda mensal R$ 8.000–R$ 25.000, já investe em B3 e/ou previdência privada.
- Quer saber **quando** pode parar de trabalhar e **quanto** precisa ter acumulado.
- Preocupa-se com o gap entre parar de trabalhar e receber INSS.

### Persona B — "Próximo da Aposentadoria"
- 50–60 anos, focado em validar se o patrimônio atual é suficiente.
- Tem datas precisas para INSS e previdência privada já estimadas.

### Persona C — "Curioso Iniciante"
- 22–29 anos, começando a poupar. Usa o simulador para descobrir o valor mensal a investir.

---

## 3. Arquitetura — Como NiceGUI e FastAPI Coexistem

NiceGUI e FastAPI rodam no **mesmo processo Python**, na mesma porta (8000):

```
http://localhost:8000/
  ├── /*          → NiceGUI (páginas Python, reatividade via WebSocket)
  └── /api/v1/*   → FastAPI (REST API JSON — usada externamente e para compartilhamento)
```

Os services da camada de negócio (`calculator.py`, `auth_service.py`, `simulation_service.py`) são chamados **diretamente** pelas páginas NiceGUI, sem overhead de HTTP. A REST API existe para: (a) o endpoint público de simulação compartilhada, (b) integrações futuras, (c) testes automatizados.

**Atenção em produção:** o Nginx deve ter suporte a WebSocket (`Upgrade` / `Connection: upgrade`) para que a reatividade da UI funcione corretamente.

---

## 4. Módulos Principais

| # | Módulo | Implementação |
|---|--------|---------------|
| M1 | Formulário de Simulação | Página NiceGUI com componentes reativos |
| M2 | Painel de Resultados | Cards e métricas atualizados em tempo real via binding |
| M3 | Gráficos de Projeção | Plotly integrado ao NiceGUI (`ui.plotly`) |
| M4 | Histórico de Simulações | Página NiceGUI com lista e comparação |
| M5 | Autenticação | `app.storage.user` do NiceGUI + JWT para a REST API |
| M6 | Compartilhamento | Link público servido pela REST API FastAPI |

---

## 5. Requisitos Funcionais

### 5.1 Formulário de Simulação

#### Seção: Situação Atual

| Campo | Componente NiceGUI | Validação |
|-------|-------------------|-----------|
| Patrimônio atual investido (R$) | `ui.number` com prefix "R$" | ≥ 0 |
| Aporte mensal (R$) | `ui.number` com prefix "R$" | > 0 |
| Idade atual (anos) | `ui.slider` + `ui.number` sincronizados | 18–80 |

#### Seção: Metas de Independência

| Campo | Componente NiceGUI | Validação |
|-------|-------------------|-----------|
| Renda mensal desejada (R$) | `ui.number` com prefix "R$" | > 0 |
| **Idade para parar de trabalhar** | `ui.slider` + `ui.number` | > idade atual, ≤ 80 |
| Expectativa de vida | `ui.slider` + `ui.number` | > retirement_age, ≤ 110, default 90 |

> **Regra de negócio:** `retirement_age` é independente de qualquer `start_age` de benefício previdenciário.

#### Seção: Aposentadoria Pública (INSS / RPPS)

| Campo | Componente NiceGUI | Validação |
|-------|-------------------|-----------|
| Possui aposentadoria pública? | `ui.switch` | — |
| Valor do benefício (R$) | `ui.number` (visível se switch ON) | > 0 |
| **Idade de início do recebimento** | `ui.slider` (visível se switch ON) | ≥ retirement_age |
| Valor em reais de hoje? | `ui.switch` (default ON) | — |

> **Regra crítica:** `start_age` pode ser posterior a `retirement_age`, criando o gap previdenciário que o patrimônio precisa cobrir.

#### Seção: Previdência Privada (PGBL / VGBL)

| Campo | Componente NiceGUI | Validação |
|-------|-------------------|-----------|
| Possui previdência privada? | `ui.switch` | — |
| Valor mensal do benefício (R$) | `ui.number` (visível se ON) | > 0 |
| **Idade de início do recebimento** | `ui.slider` (visível se ON) | ≥ retirement_age |
| Modalidade | `ui.select` (visível se ON) | lifetime \| fixed_term \| lump_sum |
| Prazo (anos) | `ui.number` (visível se fixed_term) | > 0 |
| Valor em reais de hoje? | `ui.switch` (default ON) | — |

#### Seção: Parâmetros Econômicos (colapsável)

| Campo | Padrão | Faixa |
|-------|--------|-------|
| Inflação anual projetada | 4,50% | 0%–20% |
| Rendimento anual real | 6,00% | 0%–30% |
| Taxa de retirada segura | 4,00% | 1%–10% |

#### Comportamento do Formulário
- Recálculo automático em cada mudança de campo via `ui.refreshable` ou bindings reativos do NiceGUI.
- Alertas inline de gap previdenciário quando `start_age > retirement_age`.
- Tooltips explicativos com `ui.tooltip` em cada campo complexo.
- Parâmetros econômicos em `ui.expansion` (colapsado por padrão).

### 5.2 Painel de Resultados

Cards sempre visíveis com:

| Card | Cálculo |
|------|---------|
| **Patrimônio Necessário** | Renda líquida mensal / taxa_retirada × 12 |
| **Patrimônio Projetado** | FV acumulado até retirement_age |
| **Aporte Mensal Necessário** | Cálculo reverso do FV |
| **Gap (diferença)** | Projetado − Necessário (positivo = sobra, negativo = falta) |
| Rendimento Anual Real | Parâmetro de entrada |
| Inflação Projetada | Parâmetro de entrada |

Banner de viabilidade:

| Status | Critério | Cor NiceGUI |
|--------|----------|-------------|
| `viable` | Projetado ≥ Necessário | `positive` (verde) |
| `warning` | Projetado ≥ 80% do Necessário | `warning` (amarelo) |
| `unviable` | Projetado < 80% do Necessário | `negative` (vermelho) |

### 5.3 Gráficos (Plotly via `ui.plotly`)

**Gráfico 1 — Evolução Patrimonial:**
- Área preenchida na fase de acumulação (até `retirement_age`)
- Linha na fase de retirada (após `retirement_age`)
- Linhas verticais pontilhadas nos eventos: parar de trabalhar, início INSS, início Prev. Privada
- Linha horizontal pontilhada no patrimônio necessário
- Tooltip com: idade, patrimônio, fase atual, renda disponível no período

**Gráfico 2 — Composição da Renda por Fase:**
- Barras empilhadas por fase (Retirada do Patrimônio | INSS | Prev. Privada)
- Linha de referência na renda desejada

### 5.4 Timeline de Eventos (ui.timeline ou HTML customizado)

```
[Hoje] ──── [Parar de trabalhar] ──── [Início Prev. Privada] ──── [Início INSS] ──── [Expectativa de vida]
  acumulação       gap: só patrimônio        renda parcial              renda plena
```

Alerta destacado quando há gap: "⚠️ X anos sem benefício previdenciário. Patrimônio cobre R$ Y/mês neste período."

### 5.5 Histórico de Simulações

- Lista de simulações salvas em cards (`ui.card`) com: nome, data, status, patrimônio necessário/projetado, mini progress bar.
- Menu de ações por simulação: Renomear | Duplicar | Compartilhar | Excluir.
- Comparação de até 3 simulações em tabela side-by-side + gráfico Plotly sobreposto.
- Estado vazio com CTA para criar primeira simulação.

### 5.6 Autenticação

- Sessão gerenciada via `app.storage.user` do NiceGUI (cookie seguro, server-side).
- Login com email/senha e Google OAuth.
- JWT gerado para uso na REST API (compartilhamento externo).
- Persistência offline: até 5 simulações em `app.storage.user` para usuários não autenticados; migração automática ao fazer login.

### 5.7 Compartilhamento

- Link público `/compartilhado/{token}` servido pela REST API FastAPI como página NiceGUI read-only.
- `share_token` gerado com `secrets.token_urlsafe(32)`.
- Exportação PDF via `reportlab` gerada server-side e entregue como download.

---

## 6. Regras de Negócio e Fórmulas de Cálculo

### Fase de Acumulação
```
FV = PV × (1 + r_mensal)^n + PMT × ((1 + r_mensal)^n − 1) / r_mensal
r_mensal = annual_real_return / 12
n = (retirement_age − current_age) × 12
```

### Patrimônio Necessário
```
P_necessário = renda_líquida_mensal × 12 / safe_withdrawal_rate
renda_líquida_mensal = desired_monthly_income − Σ(benefícios com start_age ≤ retirement_age + 1)
```

### Aporte Necessário (reverso)
```
PMT = (P_necessário − PV × (1 + r)^n) × r / ((1 + r)^n − 1)
Se PV × (1 + r)^n ≥ P_necessário → retornar Decimal(0)
```

### Simulação Mês a Mês (fase de retirada)
```
Para cada mês m após retirement_age:
  benefícios_ativos = Σ benefícios com start_age ≤ idade_no_mês_m
  retirada = max(0, desired_monthly_income − benefícios_ativos)
  patrimônio[m] = max(0, patrimônio[m−1] × (1 + r_mensal) − retirada)
  se patrimônio[m] == 0: registrar patrimony_exhausted=True, exhaustion_age
```

### Invariantes (nunca violar)
- `retirement_age > current_age`
- `life_expectancy > retirement_age`
- `public_pension.start_age >= retirement_age` (se habilitada)
- `private_pension.start_age >= retirement_age` (se habilitada)
- `required_monthly_contribution >= 0` (nunca negativo)
- Patrimônio na `projection_series` nunca negativo (clamp em 0)

---

## 7. Banco de Dados

### Tabela `users`
```sql
id               UUID PRIMARY KEY DEFAULT gen_random_uuid()
email            VARCHAR(255) UNIQUE NOT NULL
name             VARCHAR(255)
hashed_password  VARCHAR(255)   -- NULL para usuários OAuth
birth_date       DATE
created_at       TIMESTAMPTZ DEFAULT now()
deleted_at       TIMESTAMPTZ    -- soft delete, carência 30 dias
```

### Tabela `simulations`
```sql
id           UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id      UUID REFERENCES users(id) ON DELETE SET NULL
name         VARCHAR(255) NOT NULL DEFAULT 'Simulação sem título'
parameters   JSONB NOT NULL
results      JSONB NOT NULL   -- snapshot imutável dos resultados
share_token  VARCHAR(64) UNIQUE
is_public    BOOLEAN DEFAULT false
created_at   TIMESTAMPTZ DEFAULT now()
updated_at   TIMESTAMPTZ
```

`results` é sempre calculado no servidor no momento do save — nunca confiar em resultados enviados pelo cliente.

---

## 8. REST API (FastAPI)

Prefixo: `/api/v1`

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| POST | `/auth/register` | — | Cadastro email/senha |
| POST | `/auth/login` | — | Login → JWT |
| POST | `/auth/google` | — | Google OAuth |
| POST | `/auth/refresh` | — | Renova token |
| POST | `/auth/logout` | JWT | Invalida refresh |
| POST | `/simulations/calculate` | Opcional | Calcula sem persistir |
| POST | `/simulations` | JWT | Cria e salva simulação |
| GET | `/simulations` | JWT | Lista do usuário |
| GET | `/simulations/{id}` | JWT | Detalhe |
| PUT | `/simulations/{id}` | JWT | Atualiza nome/parâmetros |
| DELETE | `/simulations/{id}` | JWT | Remove |
| POST | `/simulations/{id}/share` | JWT | Liga/desliga compartilhamento |
| GET | `/simulations/shared/{token}` | — | Visualização pública |
| GET | `/health` | — | Status dos serviços |

Rate limits: login 10 req/min por IP; register 5 req/min; calculate 30 req/min; POST simulations 20 req/hora por user.

---

## 9. Requisitos Não Funcionais

| Categoria | Requisito |
|-----------|-----------|
| Performance | Cálculo síncrono < 100ms; API P95 < 300ms |
| Disponibilidade | 99,5% uptime mensal |
| Segurança | HTTPS obrigatório; bcrypt cost=12; rate limiting |
| Privacidade | LGPD; dados financeiros não logados; não compartilhados com terceiros |
| WebSocket | Nginx com suporte a Upgrade obrigatório em produção |
| Idioma | pt-BR exclusivo no MVP |

---

## 10. Roadmap

### Fase 1 — MVP Core (Semanas 1–4)
- Setup do projeto (monorepo Python puro, Docker, CI)
- Engine de cálculo com 100% de cobertura de testes
- UI NiceGUI: formulário completo com reatividade
- Painel de resultados e timeline

### Fase 2 — Persistência e Autenticação (Semanas 5–7)
- Banco de dados, modelos e migrações Alembic
- Autenticação (email/senha + Google OAuth)
- CRUD de simulações (NiceGUI + REST API)
- Persistência offline em `app.storage.user`

### Fase 3 — Funcionalidades Avançadas (Semanas 8–10)
- Gráficos Plotly integrados
- Comparação de simulações
- Exportação PDF com reportlab
- Compartilhamento público via link

### Fase 4 — Qualidade e Go-Live (Semanas 11–12)
- Testes E2E com Playwright
- Otimização de performance
- Deploy em produção (Docker + Nginx)
- Monitoramento com Prometheus + Sentry

---

## 11. Fora do Escopo (MVP)

- Open Finance / APIs de corretoras
- Cálculo de IR sobre rendimentos
- Monte Carlo (múltiplos cenários de mercado)
- Aplicativo mobile nativo
- Modo casal (dois planejamentos combinados)

---

## 12. Glossário

| Termo | Definição |
|-------|-----------|
| **Gap Previdenciário** | Período entre `retirement_age` e o início do primeiro benefício previdenciário |
| **Taxa de Retirada Segura** | % do patrimônio retirado anualmente sem esgotá-lo (padrão: 4% — Regra dos 4%) |
| **Taxa Real de Retorno** | Rendimento já descontado a inflação |
| **Snapshot** | Cópia imutável de `parameters` e `results` no momento do save |
| **INSS** | Aposentadoria pública do trabalhador CLT/MEI |
| **RPPS** | Regime Próprio — aposentadoria de servidores públicos |
| **PGBL / VGBL** | Modalidades de previdência privada complementar |

---

*Versão 2.0 — Migrado de React/TypeScript para NiceGUI/Python em 01/06/2026.*