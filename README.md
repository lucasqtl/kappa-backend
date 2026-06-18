# Plataforma Kappa — Backend

API REST da **Plataforma Gamificada para o Ensino de Programação**. Construída com **Arquitetura Hexagonal** (Ports & Adapters), separando domínio, casos de uso, infraestrutura e apresentação de forma independente.

---

## Stack

| Tecnologia | Uso |
|------------|-----|
| Python 3.11+ | Linguagem |
| FastAPI | Framework web |
| Pydantic v2 | Schemas e configuração |
| SQLAlchemy 2.0 | ORM |
| Alembic | Migrações |
| PostgreSQL 16 | Banco de dados |
| Pytest | Testes |
| python-jose + passlib | JWT e hash de senha |
| structlog | Logging estruturado (JSON) |

---

## Banco de Dados

O projeto usa **PostgreSQL 16**. Há duas formas de rodar: via Docker (recomendado) ou instalação local.

### Credenciais padrão (desenvolvimento)

| Parâmetro | Valor |
|-----------|-------|
| Host | `localhost` |
| Porta | `5432` |
| Banco | `kappa_db` |
| Usuário | `kappa` |
| Senha | `kappa` |

Connection string completa:
```
postgresql+psycopg2://kappa:kappa@localhost:5432/kappa_db
```

### Opção 1 — Docker (recomendado)

Sobe apenas o banco (sem o app):
```bash
docker compose up db -d
```

Isso cria o container `postgres:16` já com o usuário, senha e banco configurados automaticamente via variáveis de ambiente no `docker-compose.yml`. O volume `postgres_data` persiste os dados entre restarts.

Para derrubar e destruir os dados:
```bash
docker compose down -v
```

### Opção 2 — PostgreSQL local

Se preferir instalar o PostgreSQL localmente (Ubuntu/Debian):
```bash
sudo apt install postgresql postgresql-contrib
sudo -u postgres psql
```

Dentro do psql:
```sql
CREATE USER kappa WITH PASSWORD 'kappa';
CREATE DATABASE kappa_db OWNER kappa;
GRANT ALL PRIVILEGES ON DATABASE kappa_db TO kappa;
\q
```

### Conectar via cliente gráfico

Qualquer cliente PostgreSQL funciona. Exemplos:

**psql (linha de comando):**
```bash
psql -h localhost -p 5432 -U kappa -d kappa_db
# senha: kappa
```

**DBeaver / TablePlus / pgAdmin / DataGrip:**
- Host: `localhost`
- Port: `5432`
- Database: `kappa_db`
- Username: `kappa`
- Password: `kappa`

**Connection string (para ferramentas que aceitam URI):**
```
postgresql://kappa:kappa@localhost:5432/kappa_db
```

### Aplicar as migrações

Após o banco estar rodando, aplique o schema com Alembic:
```bash
alembic upgrade head
```

Isso executa as duas migrations existentes:
- `001_initial_schema` — cria todas as tabelas e tipos ENUM
- `002_add_performance_indexes` — adiciona índices de performance

Para verificar se o schema está correto:
```bash
python scripts/verify_schema.py
```

Para aplicar migrations e verificar em um único comando:
```bash
python scripts/setup_database.py
```

### Popular com dados iniciais (seed)

Após aplicar as migrations, execute o seed para criar dados de desenvolvimento:
```bash
python scripts/seed.py
```

O seed cria:
- Usuário gestor: `admin@kappa.dev` (senha hash já embutida)
- 2 badges: `FIRST_BLOOD`, `CONTROL_FLOW_MASTER`
- 4 missões ATIVAS na trilha `STARTER_PACK_TRACK`

O seed é idempotente — roda de novo sem duplicar dados.

### Schema do banco

```
usuarios          → id, username, email, senha_hash, perfil, departamento
alunos            → usuario_id (FK), nivel, xp_total, xp_semana, dias_ofensiva
badges            → id, codigo, nome, descricao, icone_url
missoes           → id, titulo, descricao, dificuldade, xp_recompensa, badge_id_recompensa, data_inicio, deadline, status, trilha_id, ordem
submissoes        → id, aluno_id (FK), missao_id (FK), conteudo_codigo, status, criado_em, atualizado_em
correcoes         → id, submissao_id (FK), professor_id (FK), nota, feedback, criado_em
badges_conquistadas → id, aluno_id (FK), badge_id (FK), conquistado_em
```

Índices de performance criados: `ix_submissoes_aluno_id`, `ix_submissoes_missao_id`, `ix_alunos_xp_total`, `ix_badges_conquistadas_aluno_id`.

### Criar e gerenciar migrations

Ao alterar modelos SQLAlchemy em `app/infrastructure/database/models.py`, gere uma nova migration:

```bash
# Gerar migration automaticamente (Alembic detecta as mudanças)
alembic revision --autogenerate -m "descricao da mudanca"

# Revisar o arquivo gerado em alembic/versions/ antes de aplicar

# Aplicar
alembic upgrade head

# Reverter última migration
alembic downgrade -1

# Ver histórico
alembic history

# Ver versão atual do banco
alembic current
```

> **Atenção:** sempre revise o arquivo gerado pelo `--autogenerate`. O Alembic pode não detectar renomeações de coluna corretamente — prefira criar a migration manualmente nesses casos.

---

## Setup completo para novos devs

### 1. Pré-requisitos

- Python 3.11+
- Docker + Docker Compose (ou PostgreSQL 16 instalado localmente)
- Git

### 2. Clonar e configurar ambiente

```bash
git clone <repo-url>
cd kappa_backend

python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

pip install -e ".[dev]"
```

### 3. Variáveis de ambiente

```bash
cp .env.example .env
```

Edite `.env` conforme necessário:

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `DATABASE_URL` | URL de conexão PostgreSQL | `postgresql+psycopg2://kappa:kappa@localhost:5432/kappa_db` |
| `SECRET_KEY` | Chave de assinatura JWT | `change-me-in-production` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Expiração do access token | `60` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Expiração do refresh token | `7` |
| `DEBUG` | Ativa logs detalhados e modo debug | `false` |

> Em produção, gere uma `SECRET_KEY` segura com: `openssl rand -hex 32`

### 4. Subir o banco

```bash
docker compose up db -d
```

### 5. Aplicar schema e seed

```bash
alembic upgrade head
python scripts/seed.py
```

### 6. Rodar o servidor

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Acesse:
- `http://127.0.0.1:8000/docs` — Swagger UI (todos os endpoints documentados)
- `http://127.0.0.1:8000/redoc` — ReDoc
- `http://127.0.0.1:8000/health` — Health check (também testa conexão com o banco)

---

## O que já existe

### Camada de domínio (`app/domain/`)

- **Entidades:** `Usuario`, `Aluno`, `Professor`, `Missao`, `Submissao`, `Correcao`, `Badge`, `BadgeConquistada`, `EntradaRanking`, `ProgressoMissao`
- **Enums:** perfil (`ALUNO`, `PROFESSOR`, `GESTOR`), dificuldade (`EASY`, `MEDIUM`, `BOSS`), status de missão e submissão
- **Máquinas de estado:** transições validadas em `state_machines.py`
- **Exceções de domínio:** `EntityNotFoundError`, `InvalidStateTransitionError`, `UnauthorizedActionError`

### Camada de aplicação (`app/application/`)

- **Ports (Protocol):** repositórios e `EngineIA`
- **Casos de uso implementados:**
  - `ObterDashboardAlunoUseCase` — XP, nível, ofensiva, trilha de missões, ranking
  - `SubmeterCodigoUseCase` — envia código, valida via Engine IA, dispara evolução
  - `ProcessarEvolucaoUseCase` — XP, level up, badges, ranking
  - `CriarMissaoUseCase` — missão em `EM_RASCUNHO` ou `AGENDADA`
  - `AvaliarSubmissaoUseCase` — correção manual com nota e feedback

### Infraestrutura (`app/infrastructure/`)

- **Modelos SQLAlchemy** separados das entidades de domínio (`database/models.py`)
- **Mappers** domínio ↔ ORM (`database/mappers.py`)
- **Repositórios SQLAlchemy** para cada port
- **`MockEngineIA`** — validação simulada para desenvolvimento

### Apresentação (`app/presentation/`)

- App FastAPI em `main.py`
- Routers v1, schemas Pydantic, injeção de dependências (`dependencies.py`)

### Core (`core/`)

- `config.py` — `BaseSettings` (`.env`)
- `database.py` — engine, sessão, `get_db`
- `security.py` — hash de senha e JWT
- `logging_config.py` — structlog JSON + decorator `@log_use_case`

---

## Estrutura do projeto

```
kappa_backend/
├── main.py                  # Entrada da aplicação
├── core/                    # Config, sessão de banco, segurança, logging
│   ├── config.py
│   ├── database.py
│   ├── security.py
│   └── logging_config.py
├── app/
│   ├── domain/              # Entidades, enums, exceções, state machines
│   ├── application/         # Ports (interfaces), DTOs, casos de uso
│   ├── infrastructure/      # SQLAlchemy models, repositórios, MockEngineIA
│   └── presentation/        # FastAPI routers, schemas Pydantic, dependencies
├── alembic/                 # Migrações de banco
│   └── versions/
│       ├── 001_initial_schema.py
│       └── 002_add_performance_indexes.py
├── scripts/
│   ├── seed.py              # Dados iniciais de desenvolvimento
│   ├── setup_database.py    # Aplica migrations + verifica schema
│   └── verify_schema.py     # Verifica integridade do schema
├── tests/                   # Testes unitários
├── pyproject.toml
├── alembic.ini
├── docker-compose.yml
└── .env.example
```

### Fluxo de dependências

```
Presentation (FastAPI)
    → Application (Use Cases / Ports)
        → Domain (Entities / Rules)
    ← Infrastructure (SQLAlchemy, MockEngineIA)
```

Os casos de uso não importam nada de FastAPI ou SQLAlchemy — dependem apenas dos Protocols em `application/ports/`.

---

## Domínio

**Máquinas de estado:**

- Missão: `EM_RASCUNHO` → `AGENDADA` → `ATIVA` → `EXPIRADA | SUSPENSA`
- Submissão: `EM_RASCUNHO` → `VALIDANDO` → `FALHA | PROCESSANDO_EVOLUCAO` → `LEVEL_UP` → `FINALIZADA`

**Gamificação:**
- 5000 XP por nível (configurável via `XP_POR_NIVEL` no `Settings`)
- Level up detectado ao cruzar o limiar
- Badges concedidos automaticamente ao completar missão com `badge_id_recompensa`
- Ranking derivado de `xp_total` em tempo real

---

## Casos de uso

| Use Case | Responsabilidade |
|----------|-----------------|
| `ObterDashboardAlunoUseCase` | XP, nível, ofensiva, trilha de missões, ranking |
| `SubmeterCodigoUseCase` | Valida submissão via Engine IA e dispara evolução |
| `ProcessarEvolucaoUseCase` | XP, level up, badges, atualização de ranking |
| `CriarMissaoUseCase` | Cria missão em `EM_RASCUNHO` ou `AGENDADA` |
| `AvaliarSubmissaoUseCase` | Correção manual pelo professor (nota + feedback) |

---

## API

Prefixo base: `/api/v1`

### Auth

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/auth/registro/aluno` | Cadastrar aluno |
| `POST` | `/auth/registro/professor` | Cadastrar professor |
| `POST` | `/auth/login` | Login (retorna access + refresh token) |
| `POST` | `/auth/refresh` | Renovar access token |

### Alunos

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/alunos` | Listar alunos (paginado) |
| `GET` | `/alunos/{id}` | Detalhe do aluno |
| `GET` | `/alunos/{id}/dashboard` | Dashboard gamificado (`?trilha_id=`) |
| `GET` | `/alunos/{id}/badges` | Badges conquistadas |
| `GET` | `/alunos/{id}/submissoes` | Histórico de submissões (paginado) |
| `GET` | `/alunos/ranking` | Ranking global (`?limite=`) |

### Missões

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/missoes` | Criar missão |
| `GET` | `/missoes` | Listar missões (`?status=&trilha_id=`) |
| `GET` | `/missoes/{id}` | Detalhe da missão |
| `PUT` | `/missoes/{id}` | Atualizar missão |
| `PATCH` | `/missoes/{id}/status` | Alterar status (valida state machine) |
| `DELETE` | `/missoes/{id}` | Remover missão |
| `POST` | `/missoes/{id}/submeter` | Submeter código (`?aluno_id=`) |
| `POST` | `/missoes/submissoes/{id}/avaliar` | Correção manual pelo professor |

### Submissões

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/submissoes/{id}` | Detalhe de uma submissão |

### Sistema

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/health` | Health check (inclui status do banco) |

Documentação interativa: `/docs` (Swagger UI) e `/redoc`.

---

## Mock da Engine IA

Em desenvolvimento, a Engine IA é simulada por `MockEngineIA` (`app/infrastructure/integrations/mock_engine_ia.py`):

| Código enviado | Resultado |
|----------------|-----------|
| Vazio | `FALHA_COMPILACAO` |
| Contém `SyntaxError` | `FALHA_COMPILACAO` |
| Contém `FAIL_TEST` | `FALHA_TESTE` |
| Qualquer outro conteúdo | Aprovado → XP + evolução |

---

## Testes

```bash
pytest tests/ -q
```

Os testes unitários em `tests/unit/` não dependem de banco de dados — utilizam repositórios fake em memória.

Cobertura atual:
- `test_state_machines.py` — transições válidas e inválidas de missão e submissão
- `test_submeter_codigo_use_case.py` — fluxo completo de submissão (aprovação, falha de teste, missão inativa, aluno inexistente)

---

## Docker — app completo

Para subir a aplicação inteira (banco + API) via Docker:

```bash
docker compose up --build
```

A API ficará disponível em `http://localhost:8000`. O container `app` aguarda o `db` passar no healthcheck antes de iniciar.

> **Atenção:** o `docker-compose.yml` não roda as migrations automaticamente. Após subir, execute:
> ```bash
> docker compose exec app alembic upgrade head
> docker compose exec app python scripts/seed.py
> ```

---

## Variáveis de ambiente — referência completa

| Variável | Tipo | Padrão | Descrição |
|----------|------|--------|-----------|
| `DATABASE_URL` | string | `postgresql+psycopg2://kappa:kappa@localhost:5432/kappa_db` | URL de conexão SQLAlchemy |
| `SECRET_KEY` | string | `change-me-in-production` | Chave HMAC para assinar JWTs — **troque em produção** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | int | `60` | Validade do access token JWT |
| `REFRESH_TOKEN_EXPIRE_DAYS` | int | `7` | Validade do refresh token JWT |
| `DEBUG` | bool | `false` | Ativa logging em nível DEBUG |
| `SQLALCHEMY_ECHO` | bool | `false` | Loga todas as queries SQL no console |

Todas as variáveis são lidas via `core/config.py` usando `pydantic-settings` — o arquivo `.env` é carregado automaticamente.