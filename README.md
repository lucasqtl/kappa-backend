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
| PostgreSQL | Banco de dados |
| Pytest | Testes |
| python-jose + passlib | Base para JWT e hash de senha (ainda não exposta em endpoints) |

---

## O que já existe

### Camada de domínio (`app/domain/`)

- **Entidades:** `Usuario`, `Aluno`, `Professor`, `Missao`, `Submissao`, `Correcao`, `Badge`, `BadgeConquistada`, `EntradaRanking`, `ProgressoMissao`
- **Enums:** perfil (`ALUNO`, `PROFESSOR`, `GESTOR`), dificuldade (`EASY`, `MEDIUM`, `BOSS`), status de missão e submissão
- **Máquinas de estado:** transições validadas em `state_machines.py` (ex.: `EM_RASCUNHO` → `VALIDANDO` → `PROCESSANDO_EVOLUCAO` → `FINALIZADA`)
- **Exceções de domínio:** `EntityNotFoundError`, `InvalidStateTransitionError`, `UnauthorizedActionError`

### Camada de aplicação (`app/application/`)

- **Ports (Protocol):** repositórios (`Aluno`, `Missao`, `Submissao`, `Progresso`, `Ranking`, `Badge`, `Correcao`) e `EngineIA`
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
- **`MockEngineIA`** — validação simulada para desenvolvimento (sem serviço externo real)

### Apresentação (`app/presentation/`)

- App FastAPI em `main.py`
- Routers v1, schemas Pydantic, injeção de dependências (`dependencies.py`)

### Core (`core/`)

- `config.py` — `BaseSettings` (`.env`)
- `database.py` — engine, sessão, `get_db`
- `security.py` — hash de senha e JWT (preparado para auth futura)

### Testes (`tests/`)

- `test_state_machines.py` — transições de estado
- `test_submeter_codigo_use_case.py` — fluxo de submissão com repositórios fake (8 testes)

### Alembic (`alembic/`)

- Configuração pronta (`env.py` aponta para os modelos SQLAlchemy)
- **Ainda não há revision inicial gerada** — ver secção [Banco de dados](#banco-de-dados)

---

## Estrutura do projeto

```
kappa_backend/
├── main.py                  # Entrada da aplicação
├── core/                    # Config, sessão de banco, segurança
│   ├── config.py
│   ├── database.py
│   └── security.py
├── app/
│   ├── domain/              # Entidades, enums, exceções, state machines
│   ├── application/         # Ports (interfaces), DTOs, casos de uso
│   ├── infrastructure/      # SQLAlchemy models, repositórios, MockEngineIA
│   └── presentation/        # FastAPI routers, schemas Pydantic, dependencies
├── alembic/                 # Migrações de banco
│   └── versions/
│       └── 001_initial_schema.py
├── tests/                   # Testes unitários
├── pyproject.toml
├── alembic.ini
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

**Entidades:** `Aluno`, `Professor`, `Missao`, `Submissao`, `Correcao`, `Badge`, `BadgeConquistada`, `EntradaRanking`, `ProgressoMissao`

**Máquinas de estado:**

- Missão: `EM_RASCUNHO` → `AGENDADA` → `ATIVA` → `EXPIRADA | SUSPENSA`
- Submissão: `EM_RASCUNHO` → `VALIDANDO` → `FALHA | PROCESSANDO_EVOLUCAO` → `LEVEL_UP` → `FINALIZADA`

**Gamificação:**
- 5000 XP por nível (configurável via `XP_POR_NIVEL`)
- Level up detectado ao cruzar o limiar, não apenas em múltiplos exatos
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
| `GET` | `/health` | Health check |

Documentação interativa disponível em `/docs` (Swagger UI) e `/redoc`.

---

## Mock da Engine IA

Em desenvolvimento, a Engine IA é simulada por `MockEngineIA`:

| Código enviado | Resultado |
|----------------|-----------|
| Vazio | `FALHA_COMPILACAO` |
| Contém `SyntaxError` | `FALHA_COMPILACAO` |
| Contém `FAIL_TEST` | `FALHA_TESTE` |
| Qualquer outro conteúdo | Aprovado → XP + evolução |

---

## Configuração e execução

### 1. Requisitos

- Python 3.11+
- PostgreSQL

### 2. Ambiente virtual e dependências

```bash
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

Edite `.env` conforme seu ambiente:

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `DATABASE_URL` | URL do PostgreSQL | `postgresql+psycopg2://kappa:kappa@localhost:5432/kappa_db` |
| `SECRET_KEY` | Chave de assinatura JWT | `change-me-in-production` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Expiração do access token | `60` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Expiração do refresh token | `7` |
| `DEBUG` | Modo debug | `false` |

### 4. Banco de dados

Crie o banco e aplique as migrações:

```bash
# Criar banco (exemplo)
createdb kappa_db

# Aplicar migração inicial
alembic upgrade head
```

### 5. Iniciar o servidor

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Acesse:
- `http://127.0.0.1:8000/docs` — Swagger UI
- `http://127.0.0.1:8000/health` — Health check

---

## Testes

```bash
pytest tests/ -q
```

Os testes unitários em `tests/unit/` não dependem de banco de dados — utilizam repositórios fake.