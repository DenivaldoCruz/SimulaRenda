# SimulaRenda

SimulaRenda é uma aplicação web de planejamento de independência financeira para o mercado brasileiro. O projeto combina uma interface Python com NiceGUI e uma API FastAPI para calcular metas de patrimônio, aportes necessários e fases de renda, com atenção especial ao gap previdenciário entre a parada de trabalho e o início dos benefícios previdenciários.

## Estrutura do monorepo

```text
.
├── backend/   # FastAPI + Python 3.12
├── frontend/  # NiceGUI + Python 3.12
├── shared/    # Documentação de contratos compartilhados
└── docker-compose.yml
```

## Requisitos

- Docker e Docker Compose
- Python 3.12+

Não é necessário Node.js nem npm para desenvolver ou executar o projeto.

## Setup local

1. Copie o arquivo de ambiente de exemplo:

   ```bash
   cp .env.example .env
   ```

2. Ajuste `SECRET_KEY`, credenciais OAuth e origens de CORS no `.env`.

3. Instale as dependências locais:

   ```bash
   make install
   ```

4. Suba o ambiente de desenvolvimento:

   ```bash
   make dev
   ```

A interface NiceGUI ficará disponível em `http://localhost:5173` e a API em `http://localhost:8000`.

## Comandos úteis

```bash
make install  # instala dependências Python do frontend e backend
make dev      # sobe postgres, redis, backend e frontend com Docker Compose
make test     # executa testes Python do frontend e backend
make lint     # compila módulos Python para validação estática inicial
make build    # gera imagens Docker
make migrate  # executa migrações Alembic
```

## Serviços Docker

O `docker-compose.yml` define os serviços de desenvolvimento:

- `postgres`: PostgreSQL 16
- `redis`: Redis 7
- `backend`: API FastAPI em `:8000`
- `frontend`: interface NiceGUI em `:5173`
