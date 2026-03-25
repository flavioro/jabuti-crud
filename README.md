# Jabuti Users API

Projeto completo para o desafio técnico da Jabuti AGI: uma API CRUD de usuários com **FastAPI**, **PostgreSQL**, **Redis como cache**, **Alembic para migrations**, **logs estruturados em JSON**, **Swagger/OpenAPI automático** e execução com **Docker Compose**.

## O que este projeto entrega

- API em Python com FastAPI
- CRUD completo de usuários
- campos `id`, `nome`, `email` único e `idade`
- paginação em `GET /usuarios`
- cache Redis em `GET /usuarios` e `GET /usuarios/{id}`
- invalidação de cache em `POST`, `PUT` e `DELETE`
- PostgreSQL como persistência principal
- migrations com Alembic
- logs estruturados em JSON
- graceful shutdown com fechamento de conexões do Redis e descarte do engine SQLAlchemy
- documentação automática em `/docs` e `/redoc`
- testes automatizados
- seed opcional para popular o banco
- execução local com Docker Compose (`app + db + cache`)
- `render.yaml` opcional para deploy por recursos separados no Render

## Validação rápida para o avaliador

Os pontos abaixo podem ser confirmados em poucos minutos:

- **Subida com um único comando**: `docker compose up --build`
- **Swagger/OpenAPI automático** em `/docs` e `/redoc`
- **Healthcheck** em `/api/v1/health`
- **Email com unicidade real no banco** via migration Alembic e `UniqueConstraint`
- **Redis resiliente**: se o cache falhar, o CRUD continua funcionando e a API entra em estado `degraded`, sem quebrar com erro 500
- **Invalidação de cache paginado**: as chaves `users:list:*` são invalidadas em `POST`, `PUT` e `DELETE`; em `PUT` e `DELETE`, `users:detail:{id}` também é invalidado
- **Migrations automáticas no container** antes da API subir
- **Docker Compose com healthcheck** para `app`, `db` e `cache`
- **Testes automatizados**, incluindo cenário com falha do Redis

## Arquitetura do projeto

```text
jabuti-crud/
├── alembic/                     # Ambiente e versões de migration
├── app/
│   ├── api/routes/              # Rotas da API
│   ├── core/                    # Configuração e logging
│   ├── db/                      # Sessão, models e helper de migrations
│   ├── repositories/            # Acesso a dados
│   ├── schemas/                 # Schemas Pydantic
│   ├── scripts/                 # Scripts utilitários, como seed
│   ├── services/                # Regras de negócio e cache
│   ├── dependencies.py          # Injeção de dependências
│   └── main.py                  # Aplicação FastAPI
├── tests/                       # Testes automatizados
├── .env.example                 # Exemplo de variáveis de ambiente
├── .gitignore                   # Exclusões importantes do Git
├── alembic.ini                  # Configuração do Alembic
├── Dockerfile                   # Imagem da API
├── docker-compose.yml           # App + Postgres + Redis
├── entrypoint.sh                # Migrações automáticas + start da API
├── Makefile                     # Comandos úteis
├── pyproject.toml               # Dependências e tooling
├── render.yaml                  # Deploy opcional no Render
└── README.md
```

## Stack usada

- **FastAPI** para a API e geração automática de OpenAPI/Swagger
- **SQLAlchemy 2** para persistência
- **Alembic** para migrations
- **PostgreSQL** como banco relacional
- **Redis** para cache
- **Pydantic 2 + pydantic-settings** para validação e configuração
- **python-json-logger** para logs em JSON
- **Pytest** para testes
- **Docker Compose** para rodar a aplicação multi-container

## Decisões técnicas importantes

### 1. Redis não é dependência obrigatória do CRUD
Se o Redis estiver indisponível, as operações de cache geram apenas logs de warning e a API continua atendendo pelo banco.

### 2. Unicidade de email garantida no banco
A unicidade do email não depende apenas de validação Pydantic. Ela está protegida no modelo e na migration, reduzindo risco de condição de corrida.

### 3. Invalidação de cache de listas paginadas
Ao criar, atualizar ou excluir usuários, o projeto invalida as chaves `users:list:*`. Em `PUT` e `DELETE`, também invalida `users:detail:{id}`.

### 4. Swagger como ponto de validação
O FastAPI gera automaticamente a documentação interativa, facilitando a inspeção dos contratos de request/response sem depender de ferramenta externa.

### 5. Logs em JSON
Os logs foram formatados em JSON para facilitar ingestão por ferramentas de observabilidade e leitura em pipelines de execução.

### 6. Migrations automáticas no container
O `entrypoint.sh` executa `alembic upgrade head` antes do `uvicorn`, reduzindo atrito para o avaliador no fluxo com Docker.

## Variáveis de ambiente

Copie o arquivo de exemplo:

```bash
cp .env.example .env
```

## Como rodar localmente com Docker

```bash
docker compose up --build
```

Serviços:

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/api/v1/openapi.json`
- Healthcheck: `http://localhost:8000/api/v1/health`

## Como validar rapidamente a aplicação

```bash
curl http://localhost:8000/api/v1/health
```

```bash
curl -X POST http://localhost:8000/api/v1/usuarios \
  -H "Content-Type: application/json" \
  -d '{"nome":"Flavio Rodrigues","email":"flavio@example.com","idade":30}'
```

```bash
curl "http://localhost:8000/api/v1/usuarios?limit=10&offset=0"
```

## Como rodar os testes

Localmente:

```bash
pytest -q
```

Dentro do container da aplicação:

```bash
docker compose exec app pytest -q
```

## Como rodar sem Docker

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

No Windows:

```powershell
.venv\Scripts\activate
```

## Migrations

O projeto já usa Alembic. Comandos úteis:

```bash
alembic upgrade head
alembic revision --autogenerate -m "nova migration"
```

## Seed opcional

Para popular o banco com 50 usuários de teste:

```bash
python -m app.scripts.seed --count 50
```

ou

```bash
seed-users --count 50
```

Se já houver usuários cadastrados, o seed não duplica a base.

## Endpoints

### Health
- `GET /api/v1/health`

### Usuários
- `GET /api/v1/usuarios?limit=10&offset=0`
- `GET /api/v1/usuarios/{user_id}`
- `POST /api/v1/usuarios`
- `PUT /api/v1/usuarios/{user_id}`
- `DELETE /api/v1/usuarios/{user_id}`

## Swagger / OpenAPI

O FastAPI gera automaticamente a documentação interativa da API.

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Observabilidade

Exemplo de log no formato JSON:

```json
{"timestamp": "2026-03-25 12:00:00,000", "level": "INFO", "logger": "app.main", "message": "request_completed", "method": "GET", "path": "/api/v1/health", "status_code": 200, "duration_ms": 4.31, "service": "jabuti-users-api"}
```

## Como esta API pode ser consumida por agentes

Mesmo sendo um CRUD simples, esta API foi organizada de forma útil para cenários com agentes e automações:

- **contratos claros** via OpenAPI, facilitando integração automática
- **erros previsíveis** como `404` e `409`, úteis para retry e branching
- **healthcheck** para orquestradores e agentes verificarem disponibilidade
- **cache resiliente**, evitando indisponibilidade total quando o Redis falha
- **logs estruturados**, úteis para auditoria e diagnóstico de fluxos automatizados

## Testes

Cobertura validada nesta versão:

- CRUD básico
- paginação
- conflito de email duplicado
- invalidação de cache após update
- healthcheck saudável
- healthcheck degradado quando o Redis falha
- CRUD funcionando mesmo com falha de Redis

## Git ignore

Itens críticos para nunca subir no repositório:

- `.env`
- ambientes virtuais como `.venv/`
- caches (`__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`)
- artefatos de build (`build/`, `dist/`, `*.egg-info/`)
- logs e bancos locais (`*.log`, `*.db`, `*.sqlite3`)

## Melhorias adicionadas nesta v5

- UUID gerado no banco no ambiente PostgreSQL, com fallback apenas para ambientes não-PostgreSQL de teste
- logs de duplicidade de email mais completos e estruturados
- `.env.example` reforçado com `DATABASE_URL` e `REDIS_URL`
- limpeza de artefatos locais que não devem ir para o repositório
- versão atualizada para `0.5.0`

## Próximos passos possíveis

- GitHub Actions para CI
- coverage report
- endpoint `/ready` separado de `/health`
- deploy opcional no Render usando `render.yaml`
