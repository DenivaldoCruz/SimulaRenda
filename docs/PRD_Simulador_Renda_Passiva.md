# PRD — Simulador de Renda Passiva com Calculadora de Aposentadoria

**Versão:** 1.0  
**Data:** 01 de junho de 2026  
**Status:** Draft  
**Autor:** Produto

---

## 1. Visão Geral do Produto

### 1.1 Sumário Executivo

O **Simulador de Renda Passiva** é uma aplicação web que permite ao usuário planejar sua independência financeira calculando quanto precisa acumular para viver de renda, considerando múltiplas fontes de receita passiva (rendimentos de investimentos, aposentadoria pública e previdência privada), inflação projetada e horizonte temporal personalizado. O diferencial central é a separação explícita entre **a idade de parar de trabalhar** e **a data de início de cada benefício previdenciário**, refletindo a realidade do planejamento financeiro brasileiro.

### 1.2 Problema a Resolver

Calculadoras de aposentadoria existentes assumem que renda passiva e benefício previdenciário começam simultaneamente. Na prática, a pessoa pode se aposentar financeiramente aos 50 anos, mas só receber o INSS aos 65 e a previdência privada aos 60. Sem modelar esse gap, o planejamento fica subestimado e o usuário corre risco de insuficiência de caixa nos anos de transição.

Além disso, simulações feitas manualmente se perdem. O sistema deve persistir cada simulação para que o usuário possa comparar cenários ao longo do tempo.

### 1.3 Objetivos de Negócio

- Ser referência como ferramenta gratuita de planejamento de independência financeira no Brasil.
- Gerar leads qualificados via CTA para consultor financeiro parceiro (futuro monetização).
- Aumentar tempo de sessão e retorno por meio do histórico de simulações salvas.

---

## 2. Personas e Contexto

### Persona A — "Planejador Antecipado"
- Homem ou mulher, 30–42 anos, renda mensal R$ 8.000–R$ 25.000.
- Já investe em renda variável (B3) e/ou previdência privada.
- Quer saber **quando** pode parar de trabalhar e **quanto** precisa ter acumulado.
- Preocupa-se com inflação e com o gap entre parar de trabalhar e receber INSS.

### Persona B — "Próximo da Aposentadoria"
- 50–60 anos, focado em validar se o patrimônio atual é suficiente.
- Quer inserir o patrimônio já acumulado e ver quantos anos de renda ele cobre.
- Tem datas precisas para INSS e previdência privada já estimadas.

### Persona C — "Curioso Iniciante"
- 22–29 anos, começando a poupar.
- Não tem previdência privada nem certeza sobre aposentadoria pública.
- Usa o simulador para descobrir o valor mensal a poupar para atingir a liberdade financeira.

---

## 3. Escopo Funcional

### 3.1 Módulos Principais

| # | Módulo | Descrição |
|---|--------|-----------|
| M1 | Formulário de Simulação | Inputs do usuário para calcular os resultados |
| M2 | Painel de Resultados | Exibição dos resultados calculados em tempo real |
| M3 | Gráfico de Projeção | Visualização da evolução patrimonial e de renda ao longo dos anos |
| M4 | Histórico de Simulações | Listagem e comparação de simulações salvas pelo usuário |
| M5 | Autenticação de Usuário | Cadastro/login para persistência das simulações |
| M6 | Compartilhamento | Geração de link ou PDF da simulação |

---

## 4. Requisitos Funcionais Detalhados

### 4.1 M1 — Formulário de Simulação

#### 4.1.1 Seção: Situação Atual

| Campo | Tipo | Obrigatório | Validação | Padrão |
|-------|------|-------------|-----------|--------|
| Patrimônio atual investido (R$) | Numérico monetário | Não | ≥ 0 | R$ 0 |
| Aporte mensal atual (R$) | Numérico monetário | Sim | > 0 | — |
| Idade atual (anos) | Inteiro | Sim | 18–80 | — |

#### 4.1.2 Seção: Metas de Independência

| Campo | Tipo | Obrigatório | Validação | Padrão |
|-------|------|-------------|-----------|--------|
| Renda mensal desejada na independência (R$) | Numérico monetário | Sim | > 0 | — |
| **Idade para parar de trabalhar** | Inteiro | Sim | > idade atual, ≤ 80 | — |
| Expectativa de vida (anos) | Inteiro | Sim | > idade parar, ≤ 110 | 90 |

> **Regra de negócio:** "Idade para parar de trabalhar" define quando a fase de acumulação termina e a fase de usufruto começa. É independente das datas de início dos benefícios previdenciários.

#### 4.1.3 Seção: Pensão / Aposentadoria Pública (INSS ou Regime Próprio)

| Campo | Tipo | Obrigatório | Validação |
|-------|------|-------------|-----------|
| Possui ou espera ter aposentadoria pública? | Toggle Sim/Não | Sim | — |
| Valor estimado do benefício (R$) | Numérico monetário | Se Sim | > 0 |
| **Data / Idade de início do recebimento** | Inteiro (idade) ou mês/ano | Se Sim | ≥ idade parar de trabalhar |
| O valor já está em reais de hoje? | Toggle Sim/Não | Se Sim | — |

> **Regra de negócio crítica:** A idade de início do benefício público pode ser igual ou **posterior** à idade de parar de trabalhar, criando um gap que o patrimônio acumulado precisa cobrir.

#### 4.1.4 Seção: Previdência Privada (PGBL/VGBL ou Fundo de Pensão)

| Campo | Tipo | Obrigatório | Validação |
|-------|------|-------------|-----------|
| Possui previdência privada? | Toggle Sim/Não | Sim | — |
| Valor mensal esperado do benefício (R$) | Numérico monetário | Se Sim | > 0 |
| **Data / Idade de início do recebimento** | Inteiro (idade) ou mês/ano | Se Sim | ≥ idade parar de trabalhar |
| Modalidade | Select: Renda vitalícia / Prazo certo / Pagamento único | Se Sim | — |
| Prazo (anos) | Inteiro | Se prazo certo | > 0 |

> A previdência privada e a pública podem ter idades de início diferentes entre si e diferentes da idade de parar de trabalhar.

#### 4.1.5 Seção: Parâmetros Econômicos

| Campo | Tipo | Padrão | Faixa |
|-------|------|--------|-------|
| Inflação anual projetada (%) | Decimal | 4,50% | 0%–20% |
| Rendimento anual real projetado (%) | Decimal | 6,00% | 0%–30% |
| Taxa de retirada segura (%) | Decimal | 4,00% | 1%–10% |

> **Nota UX:** Exibir tooltip explicativo para cada parâmetro econômico com benchmark de mercado.

#### 4.1.6 Comportamento do Formulário

- Todos os campos monetários usam máscara de real brasileiro (R$ 1.234,56).
- Sliders numéricos para campos inteiros (idade, expectativa de vida) com input numérico sincronizado.
- Recálculo automático (debounce 300ms) a cada alteração de campo.
- Botão "Salvar Simulação" habilitado somente quando campos obrigatórios estão preenchidos.
- Botão "Limpar" redefine o formulário para o estado inicial.

---

### 4.2 M2 — Painel de Resultados

#### 4.2.1 Cards de Resumo (sempre visíveis acima da dobra)

| Card | Cálculo |
|------|---------|
| **Patrimônio Necessário (R$)** | Renda mensal desejada líquida de pensões / Taxa de retirada segura × 12 |
| **Aporte Mensal Necessário (R$)** | Valor mensal adicional para atingir o patrimônio necessário até a idade alvo |
| **Rendimento Anual Esperado (%)** | Campo de entrada, exibido para referência |
| **Inflação Projetada (%)** | Campo de entrada, exibido para referência |
| **Valor Projetado do Patrimônio (R$)** | Patrimônio acumulado na data de parar de trabalhar |
| **Poupança Necessária (R$)** | Diferença entre patrimônio necessário e projetado (se positivo, falta; se negativo, sobra) |

#### 4.2.2 Linha do Tempo de Eventos

Exibição visual (timeline horizontal ou vertical) com os marcos:

```
[Hoje] ──── [Parar de trabalhar] ──── [Início INSS] ──── [Início Prev. Privada] ──── [Expectativa de vida]
  ↑ acumulação ↑                  ↑ gap: só patrimônio ↑    ↑ renda parcial ↑         ↑ renda plena ↑
```

- Cada fase exibe a renda mensal líquida disponível no período.
- O gap (período sem benefício) é destacado em cor de alerta se o patrimônio não cobrir as despesas.

#### 4.2.3 Indicadores de Viabilidade

| Status | Critério | Visual |
|--------|----------|--------|
| ✅ Plano Viável | Patrimônio projetado ≥ Patrimônio necessário | Verde |
| ⚠️ Plano com Ajuste | 80% ≤ Projetado < Necessário | Amarelo |
| ❌ Plano Inviável | Projetado < 80% do Necessário | Vermelho |

---

### 4.3 M3 — Gráfico de Projeção

#### 4.3.1 Gráfico Principal: Evolução Patrimonial

- Tipo: Área (fase acumulação) + Linha (fase retirada)
- Eixo X: Idade do usuário (da atual até a expectativa de vida)
- Eixo Y: Patrimônio acumulado (R$, escala linear)
- Linhas adicionais sobrepostas:
  - Linha pontilhada: patrimônio necessário (constante ajustado por inflação)
  - Marcadores verticais: início INSS, início previdência privada, idade para parar de trabalhar

#### 4.3.2 Gráfico Secundário: Composição da Renda Mensal por Fase

- Tipo: Barras empilhadas por faixa etária
- Segmentos: Retirada do patrimônio | INSS/Regime Próprio | Previdência Privada
- Linha de meta: renda desejada

#### 4.3.3 Interatividade

- Hover/tooltip em cada ponto mostrando: idade, patrimônio, renda disponível no período.
- Zoom e pan habilitados.
- Exportação do gráfico como PNG.

---

### 4.4 M4 — Histórico de Simulações

#### 4.4.1 Lista de Simulações

- Exibida em cards ou tabela com:
  - Nome da simulação (editável pelo usuário)
  - Data de criação
  - Patrimônio necessário calculado
  - Status de viabilidade (ícone colorido)
  - Ações: Ver detalhes | Duplicar | Excluir

#### 4.4.2 Comparação de Simulações

- Seleção de até 3 simulações para comparação lado a lado.
- Tabela comparativa com todos os campos principais e resultados.
- Gráfico sobreposto das projeções das simulações selecionadas.

#### 4.4.3 Persistência

- **Usuário autenticado:** dados armazenados no banco de dados do servidor.
- **Usuário não autenticado:** dados armazenados em `localStorage` com até 5 simulações; CTA para criar conta para não perder.
- Cada simulação salva snapshot completo dos parâmetros de entrada e resultados calculados.

---

### 4.5 M5 — Autenticação de Usuário

| Funcionalidade | Detalhe |
|----------------|---------|
| Cadastro | Email + senha ou Google OAuth |
| Login | Email + senha, Google OAuth, "Lembrar de mim" |
| Recuperação de senha | Via email (token com 24h de validade) |
| Perfil | Nome, email, data de nascimento (pré-preenche campo de idade) |
| Exclusão de conta | Soft delete com 30 dias de carência |

---

### 4.6 M6 — Compartilhamento

- **Link Público:** gera URL com parâmetros codificados (sem login necessário para visualizar).
- **Exportação PDF:** relatório gerado server-side com: resumo dos inputs, cards de resultados, gráficos e linha do tempo.
- **Compartilhamento Social:** botões para WhatsApp e Twitter/X com texto pré-formatado.

---

## 5. Regras de Negócio e Cálculos

### 5.1 Fase de Acumulação

```
FV = PV × (1 + r)^n + PMT × ((1 + r)^n − 1) / r
```

Onde:
- `PV` = patrimônio atual
- `PMT` = aporte mensal (convertido para períodos mensais com `r` mensal)
- `r` = rendimento anual real / 12
- `n` = número de meses até parar de trabalhar

### 5.2 Patrimônio Necessário

```
P_necessário = Renda_líquida_mensal × 12 / taxa_retirada_segura
```

Onde:
- `Renda_líquida_mensal` = Renda desejada − benefícios previdenciários ativos no período de referência (idade de parar de trabalhar + 1)
- Benefícios só entram no cálculo a partir da sua respectiva data de início

### 5.3 Modelo de Retirada com Eventos Previdenciários

O sistema simula mês a mês:

1. **Fase 1** — Da idade de parar de trabalhar até o início do 1º benefício:
   - Retirada mensal = Renda desejada (totalmente do patrimônio)

2. **Fase 2** — Do início do 1º benefício até o início do 2º (se houver):
   - Retirada mensal = Renda desejada − Benefício 1

3. **Fase 3** — Do início do 2º benefício até a expectativa de vida:
   - Retirada mensal = Renda desejada − Benefício 1 − Benefício 2

4. O patrimônio em cada mês = Patrimônio anterior × (1 + r_mensal) − Retirada

5. Alerta de **risco de esgotamento** se patrimônio < 0 em qualquer mês projetado.

### 5.4 Correção pela Inflação

- Todos os valores inseridos pelo usuário são assumidos como **reais de hoje**.
- A projeção corrige a renda desejada pela inflação acumulada a cada ano.
- Os rendimentos do patrimônio usam **taxa real** (nominal − inflação).
- Benefícios previdenciários: usuário informa se o valor já está em reais de hoje ou valor nominal futuro.

### 5.5 Aporte Necessário (cálculo reverso)

Se o usuário não saber quanto poupar, o sistema calcula o `PMT` necessário:

```
PMT = (P_necessário − PV × (1 + r)^n) × r / ((1 + r)^n − 1)
```

---

## 6. Arquitetura Técnica

### 6.1 Stack Recomendada

| Camada | Tecnologia |
|--------|------------|
| Frontend | React 18 + TypeScript + Vite |
| Estilização | Tailwind CSS + shadcn/ui |
| Gráficos | Recharts ou Chart.js |
| Estado Global | Zustand |
| Backend | FastAPI (Python 3.12) |
| Banco de Dados | PostgreSQL 16 |
| ORM | SQLAlchemy 2 + Alembic |
| Autenticação | JWT (access 15min + refresh 7 dias) + Google OAuth 2.0 |
| Cache | Redis (simulações e sessões) |
| Testes | pytest (backend) + Vitest + Testing Library (frontend) |
| CI/CD | GitHub Actions |
| Deploy | Docker Compose / Kubernetes |

### 6.2 Modelo de Dados

#### Tabela `users`
```sql
id            UUID PRIMARY KEY
email         VARCHAR(255) UNIQUE NOT NULL
name          VARCHAR(255)
birth_date    DATE
created_at    TIMESTAMPTZ DEFAULT now()
deleted_at    TIMESTAMPTZ  -- soft delete
```

#### Tabela `simulations`
```sql
id              UUID PRIMARY KEY
user_id         UUID REFERENCES users(id)
name            VARCHAR(255) NOT NULL DEFAULT 'Simulação sem título'
created_at      TIMESTAMPTZ DEFAULT now()
updated_at      TIMESTAMPTZ
parameters      JSONB NOT NULL  -- snapshot de todos os inputs
results         JSONB NOT NULL  -- snapshot de todos os outputs calculados
share_token     VARCHAR(64) UNIQUE  -- token para link público
is_public       BOOLEAN DEFAULT false
```

#### Estrutura do JSONB `parameters`
```json
{
  "current_age": 35,
  "current_patrimony": 150000,
  "monthly_contribution": 3000,
  "desired_monthly_income": 10000,
  "retirement_age": 55,
  "life_expectancy": 90,
  "inflation_rate": 0.045,
  "annual_real_return": 0.06,
  "safe_withdrawal_rate": 0.04,
  "public_pension": {
    "enabled": true,
    "monthly_amount": 2500,
    "start_age": 65,
    "amount_in_today_reais": true
  },
  "private_pension": {
    "enabled": true,
    "monthly_amount": 3000,
    "start_age": 60,
    "modality": "lifetime",
    "amount_in_today_reais": true
  }
}
```

#### Estrutura do JSONB `results`
```json
{
  "required_patrimony": 1500000,
  "projected_patrimony": 1250000,
  "required_monthly_contribution": 3800,
  "feasibility_status": "warning",
  "annual_expected_return": 0.06,
  "projected_inflation": 0.045,
  "patrimony_gap": 250000,
  "phases": [
    { "from_age": 55, "to_age": 60, "monthly_withdrawal": 10000, "sources": ["patrimony"] },
    { "from_age": 60, "to_age": 65, "monthly_withdrawal": 7000, "sources": ["patrimony", "private_pension"] },
    { "from_age": 65, "to_age": 90, "monthly_withdrawal": 4500, "sources": ["patrimony", "private_pension", "public_pension"] }
  ],
  "projection_series": [
    { "age": 35, "patrimony": 150000 },
    { "age": 36, "patrimony": 198500 }
  ]
}
```

### 6.3 API REST

#### Endpoints de Simulação

| Método | Rota | Autenticação | Descrição |
|--------|------|--------------|-----------|
| `POST` | `/api/v1/simulations/calculate` | Opcional | Calcula simulação (não persiste) |
| `POST` | `/api/v1/simulations` | Obrigatório | Cria e salva simulação |
| `GET` | `/api/v1/simulations` | Obrigatório | Lista simulações do usuário |
| `GET` | `/api/v1/simulations/{id}` | Obrigatório | Detalhe de simulação |
| `PUT` | `/api/v1/simulations/{id}` | Obrigatório | Atualiza nome ou parâmetros |
| `DELETE` | `/api/v1/simulations/{id}` | Obrigatório | Remove simulação |
| `POST` | `/api/v1/simulations/{id}/share` | Obrigatório | Gera/revoga token público |
| `GET` | `/api/v1/simulations/shared/{token}` | Nenhuma | Visualiza simulação pública |

#### Endpoints de Autenticação

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/api/v1/auth/register` | Cadastro com email/senha |
| `POST` | `/api/v1/auth/login` | Login com email/senha |
| `POST` | `/api/v1/auth/google` | Login com Google OAuth |
| `POST` | `/api/v1/auth/refresh` | Renova access token |
| `POST` | `/api/v1/auth/logout` | Invalida refresh token |
| `POST` | `/api/v1/auth/forgot-password` | Envia email de redefinição |
| `POST` | `/api/v1/auth/reset-password` | Redefine senha com token |

---

## 7. Design e Experiência do Usuário

### 7.1 Princípios de Design

- **Clareza sobre complexidade:** campos avançados (parâmetros econômicos) colapsados por padrão com valores pré-configurados sensatos.
- **Feedback em tempo real:** resultados recalculam visualmente enquanto o usuário digita.
- **Confiança:** tooltips explicativos em cada parâmetro; referências a benchmarks de mercado (ex: "Taxa Selic atual: X%").
- **Progressive disclosure:** novos campos (pensão pública, previdência privada) só aparecem quando habilitados por toggle.

### 7.2 Fluxo Principal de Usuário (Happy Path)

```
1. Usuário acessa a página
2. Preenche patrimônio atual, aporte mensal e idade atual
3. Define renda mensal desejada e idade para parar de trabalhar
4. Resultados aparecem automaticamente (painel lateral / seção abaixo)
5. Expande "Aposentadoria Pública" → informa valor e IDADE de início (ex: 65)
6. Expande "Previdência Privada" → informa valor e IDADE de início (ex: 60)
7. Gráfico atualiza mostrando fases distintas e timeline de eventos
8. Usuário clica "Salvar Simulação" → modal de login/cadastro se não autenticado
9. Simulação salva com nome padrão → usuário renomeia se quiser
10. Usuário pode acessar "Minhas Simulações" para comparar cenários
```

### 7.3 Responsividade

- Layout de 2 colunas em desktop (formulário esquerda | resultados direita).
- Layout de 1 coluna em mobile (formulário → resultados → gráficos).
- Gráficos com scroll horizontal em viewport < 480px.

### 7.4 Acessibilidade

- WCAG 2.1 AA: contraste mínimo 4.5:1 em todos os textos.
- Todos os inputs com `<label>` explícita.
- Gráficos com texto alternativo e tabela de dados colapsável.
- Navegação completa por teclado.

---

## 8. Requisitos Não Funcionais

| Categoria | Requisito |
|-----------|-----------|
| Performance | Cálculo de simulação < 100ms no frontend; API response < 300ms no P95 |
| Disponibilidade | 99,5% uptime mensal |
| Segurança | HTTPS obrigatório; senhas com bcrypt (cost 12); rate limiting nas rotas de auth |
| Privacidade | Dados financeiros não compartilhados com terceiros; conformidade LGPD |
| Escalabilidade | Suportar 10.000 simulações/dia sem degradação |
| SEO | Server-side rendering ou Static Generation para página principal |
| Internacionalização | Português Brasil (pt-BR) como única língua no MVP |

---

## 9. Roadmap de Desenvolvimento

### Fase 1 — MVP Core (Semanas 1–4)

| # | Entrega | Critério de Aceite |
|---|---------|-------------------|
| 1.1 | Setup do projeto (repo, CI, ambientes) | Pipeline verde com lint + testes |
| 1.2 | Engine de cálculo (puro TypeScript/Python) | 100% cobertura de testes unitários nos cálculos |
| 1.3 | Formulário de simulação (sem login) | Todos os campos funcionando com validação |
| 1.4 | Painel de resultados com cards | Recálculo em tempo real < 300ms |
| 1.5 | Timeline de eventos previdenciários | Exibe fases corretamente com gaps |
| 1.6 | Gráfico de projeção patrimonial | Interativo com tooltips |

### Fase 2 — Persistência e Autenticação (Semanas 5–7)

| # | Entrega | Critério de Aceite |
|---|---------|-------------------|
| 2.1 | Backend FastAPI + PostgreSQL | Endpoints de cálculo funcionando |
| 2.2 | Autenticação JWT + Google OAuth | Login/logout/refresh funcionando |
| 2.3 | CRUD de simulações | Usuário salva, lista, edita e deleta |
| 2.4 | Persistência offline (localStorage) | Até 5 simulações sem login |
| 2.5 | Migração localStorage → conta | Simula antes, faz login, dados preservados |

### Fase 3 — Funcionalidades Avançadas (Semanas 8–10)

| # | Entrega | Critério de Aceite |
|---|---------|-------------------|
| 3.1 | Comparação de simulações | Side-by-side de até 3 simulações |
| 3.2 | Gráfico de composição de renda por fase | Barras empilhadas por período |
| 3.3 | Exportação PDF do relatório | PDF com dados e gráficos |
| 3.4 | Link público de compartilhamento | Visualização read-only sem login |
| 3.5 | Cálculo de aporte necessário (reverso) | Campo mostra quanto precisa poupar |

### Fase 4 — Qualidade e Go-Live (Semanas 11–12)

| # | Entrega | Critério de Aceite |
|---|---------|-------------------|
| 4.1 | Testes E2E (Playwright) | Fluxo principal automatizado |
| 4.2 | Otimização de performance | Lighthouse score ≥ 90 |
| 4.3 | SEO e meta tags | Google Search Console indexado |
| 4.4 | Deploy em produção | Monitoramento + alertas configurados |
| 4.5 | Documentação de usuário | FAQ e tooltips revisados |

---

## 10. Métricas de Sucesso (KPIs)

| Métrica | Meta 3 meses | Meta 6 meses |
|---------|-------------|-------------|
| Simulações realizadas/mês | 1.000 | 5.000 |
| Taxa de cadastro após simulação | 15% | 25% |
| Simulações salvas por usuário | ≥ 2 | ≥ 3 |
| Bounce rate | < 50% | < 40% |
| NPS da ferramenta | ≥ 40 | ≥ 50 |
| Taxa de retorno (usuários com ≥ 2 sessões) | 20% | 35% |

---

## 11. Fora do Escopo (MVP)

- Conexão com APIs de corretoras ou Open Finance para importar patrimônio automaticamente.
- Cálculo de IR sobre rendimentos e benefícios.
- Simulação de múltiplos cenários de mercado (Monte Carlo).
- Aplicativo mobile nativo (iOS/Android).
- Modo multi-usuário (casais com rendas e planos distintos combinados).
- Integração com plataformas de previdência privada para cotações reais.

---

## 12. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Cálculos financeiros com erros | Média | Alto | Engine isolada com 100% de cobertura de testes; validação por especialista financeiro |
| Usuário não entender a diferença entre "parar de trabalhar" e "receber pensão" | Alta | Médio | Tooltips detalhados, exemplos no formulário, timeline visual explicita |
| LGPD — coleta de dados financeiros sensíveis | Baixa | Alto | Política de privacidade clara; dados criptografados em repouso; não usar dados para publicidade |
| Performance com projeções de 50+ anos mês a mês | Baixa | Médio | Calcular no frontend (sem I/O de rede); Web Worker para não bloquear UI |

---

## 13. Glossário

| Termo | Definição |
|-------|-----------|
| **Independência Financeira** | Condição em que o patrimônio investido gera renda suficiente para cobrir todas as despesas sem necessidade de trabalho ativo |
| **Taxa de Retirada Segura** | Percentual do patrimônio que pode ser retirado anualmente sem esgotá-lo ao longo da vida. Referência histórica: 4% (Regra dos 4%) |
| **Taxa Real de Retorno** | Rendimento do investimento descontada a inflação |
| **Gap Previdenciário** | Período entre a idade de parar de trabalhar e o início dos benefícios previdenciários, financiado exclusivamente pelo patrimônio acumulado |
| **PGBL** | Plano Gerador de Benefício Livre — previdência privada com dedução no IR |
| **VGBL** | Vida Gerador de Benefício Livre — previdência privada sem dedução no IR |
| **INSS** | Instituto Nacional do Seguro Social — aposentadoria pública brasileira |
| **Regime Próprio** | Aposentadoria de servidores públicos estaduais ou federais (RPPS) |

---

*Documento revisado em 01/06/2026. Próxima revisão prevista após conclusão da Fase 1.*
