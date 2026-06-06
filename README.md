# SimulaRenda

SimulaRenda é uma aplicação web de planejamento de independência financeira para o mercado brasileiro. O projeto combina uma interface Python com NiceGUI e uma API FastAPI para calcular metas de patrimônio, aportes necessários e fases de renda, com atenção especial ao gap previdenciário entre a parada de trabalho e o início dos benefícios previdenciários.

## Estrutura do projeto

```text
.
├── backend/            # FastAPI + NiceGUI + Python 3.12
├── docker-compose.yml  # PostgreSQL, Redis e aplicação Python
└── README.md
```

## Requisitos

- Python 3.12+
- pip
- Docker e Docker Compose para executar PostgreSQL e Redis em desenvolvimento

## Setup local

1. Copie o arquivo de ambiente de exemplo:

   ```bash
   cp .env.example .env
   ```

2. Ajuste `SECRET_KEY`, credenciais OAuth e origens de CORS no `.env`.

3. Instale as dependências Python:

   ```bash
   make install
   ```

4. Suba os serviços de apoio em outro terminal, se necessário:
https://docker-for-mac.en.uptodown.com/mac/download/3734812

   ```bash
   docker compose up -d postgres redis
   ```

5. Inicie a aplicação:

   ```bash
   make dev
   ```

A interface NiceGUI e a API FastAPI ficam disponíveis no mesmo processo em `http://localhost:8000`.

> Frontend construído com NiceGUI — não há build step separado.

## Comandos úteis

```bash
make install  # instala dependências Python de desenvolvimento
make dev      # inicia FastAPI e NiceGUI em :8000
make test     # executa testes com cobertura
make lint     # executa ruff e mypy
make build    # valida a compilação dos módulos Python
make migrate  # executa migrações Alembic
```

## Serviços Docker

O `docker-compose.yml` define os serviços de desenvolvimento:

- `postgres`: PostgreSQL 16 em `:5432`
- `redis`: Redis 7 em `:6379`
- `backend`: FastAPI + NiceGUI em `:8000`
