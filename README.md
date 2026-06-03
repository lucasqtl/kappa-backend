# Equipe Kappa — Backend

API back-end da **Plataforma Gamificada para o Ensino de Programação**. O código segue **Arquitetura Hexagonal** (Ports & Adapters) com **Clean Architecture**, separando domínio, casos de uso, infraestrutura e apresentação.

**Versão atual:** `0.1.0` (fundação — base pronta para evoluir com auth, migrações e seed de dados).

---

## Stack

| Tecnologia | Uso |
|------------|-----|
| Python 3.11+ | Linguagem |
| FastAPI | API REST |
| Pydantic v2 | Schemas e configuração |
| SQLAlchemy 2.0 | ORM |
| Alembic | Migrações PostgreSQL |
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

## O que ainda não está implementado

- Endpoints de **login / registo** (`Access Portal` no frontend)
- Migração Alembic aplicada e **dados de seed** (aluno demo, trilha `STARTER_PACK_TRACK`)
- Engine IA real (substituir `MockEngineIA`)
- Middleware de autenticação JWT nos endpoints
- Testes de integração com PostgreSQL

---

## Estrutura de diretórios

```text
kappa_backend/
├── app/
│   ├── domain/              # Entidades, enums, exceções, state machines
│   ├── application/         # Ports, DTOs, casos de uso
│   ├── infrastructure/      # SQLAlchemy, repositórios, MockEngineIA
│   └── presentation/        # FastAPI, routers, schemas
├── core/                    # Config, DB session, security
├── tests/                   # Unitários (domain + use cases)
├── alembic/                 # Migrações
├── .venv/                   # Ambiente virtual (não versionar)
├── requirements.txt
├── pyproject.toml
├── alembic.ini
└── .env.example
```

### Fluxo de dependências (hexagonal)

```text
Presentation (FastAPI)
    → Application (Use Cases)
        → Domain (Entities / Rules)
        ← Ports (interfaces)
    ← Infrastructure (SQLAlchemy, MockEngineIA)
```

Os casos de uso **não importam** FastAPI nem SQLAlchemy; apenas os **Protocols** em `application/ports/`.

---

## API disponível

Prefixo: `/api/v1` (configurável em `API_V1_PREFIX`).

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/health` | Health check |
| `GET` | `/api/v1/alunos/{aluno_id}/dashboard` | Dashboard gamificado (`?trilha_id=`) |
| `POST` | `/api/v1/missoes` | Criar missão (professor) |
| `POST` | `/api/v1/missoes/{missao_id}/submeter?aluno_id=` | Submeter código |
| `POST` | `/api/v1/missoes/submissoes/{submissao_id}/avaliar?professor_id=&nota=&feedback=` | Avaliação manual |

Documentação interativa (com o servidor a correr):

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

---

## Requisitos

- **Python 3.11+** (o projeto foi testado com 3.13)
- **PostgreSQL** (para endpoints que usam repositórios SQLAlchemy)
- Opcional: [pyenv](https://github.com/pyenv/pyenv) ou instalador oficial do Python no Windows

---

## Dependências

Lista em `requirements.txt`:

- **Runtime:** `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`, `sqlalchemy`, `alembic`, `psycopg2-binary`, `python-jose`, `passlib`
- **Desenvolvimento / testes:** `pytest`, `pytest-asyncio`, `httpx`

Instalação recomendada **dentro de um ambiente virtual** (ver abaixo).

---

## Configuração e instalação

### 1. Clonar / entrar no projeto

```powershell
cd c:\dev\clp\kappa_backend
```

### 2. Criar e ativar o venv

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependências

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Variáveis de ambiente

Copie o exemplo e ajuste conforme o seu PostgreSQL:

```powershell
copy .env.example .env
```

| Variável | Descrição | Default (código) |
|----------|-----------|------------------|
| `DATABASE_URL` | URL SQLAlchemy | `postgresql+psycopg2://kappa:kappa@localhost:5432/kappa_db` |
| `SECRET_KEY` | Chave JWT | `change-me-in-production` |
| `DEBUG` | Modo debug | `false` |

Outras opções em `core/config.py`: `API_V1_PREFIX`, `SQLALCHEMY_ECHO`, `XP_POR_NIVEL`, etc.

---

## Como executar

Todos os comandos abaixo assumem que está na pasta `kappa_backend` e que o **venv está ativo** (ou use o caminho completo para `.venv\Scripts\python.exe`).

### Testes unitários

```powershell
python -m pytest tests/ -q
```

Com mais detalhe:

```powershell
python -m pytest tests/ -v
```

### Servidor de desenvolvimento

```powershell
uvicorn app.presentation.main:app --reload --host 127.0.0.1 --port 8000
```

Sem ativar o venv:

```powershell
.\.venv\Scripts\uvicorn.exe app.presentation.main:app --reload
```

Abrir no browser:

- `http://127.0.0.1:8000/` — informação da API (JSON)
- `http://127.0.0.1:8000/docs` — Swagger UI (recomendado para testar endpoints)
- `http://127.0.0.1:8000/health` — health check

```powershell
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/health
```

---

## Banco de dados

1. Crie a base PostgreSQL (ex.: `kappa_db`) e utilizador com permissões.
2. Confirme `DATABASE_URL` no `.env`.
3. Gere a primeira migração (quando ainda não existir `alembic/versions/`):

```powershell
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

Os modelos estão em `app/infrastructure/database/models.py` e são carregados em `alembic/env.py`.

> **Nota:** Endpoints que consultam o banco falham até o PostgreSQL estar acessível e as tabelas criadas. Os testes em `tests/unit/` **não** precisam de base de dados (usam fakes).

---

## Mock da Engine IA

Implementação: `app/infrastructure/integrations/mock_engine_ia.py`.

| Código enviado | Resultado simulado |
|----------------|-------------------|
| Vazio | `FALHA_COMPILACAO` |
| Contém `SyntaxError` ou `raise SyntaxError` | `FALHA_COMPILACAO` |
| Contém `FAIL_TEST` | `FALHA_TESTE` |
| Qualquer outro conteúdo não vazio | Aprovado → XP e evolução |

---

## Gamificação (regras atuais)

- **XP por nível:** 5000 (`XP_POR_NIVEL` / `ObterDashboardAlunoUseCase.XP_POR_NIVEL`)
- Barra de progresso: `xp_total % 5000` (ex.: 4200/5000 → faltam 800 XP)
- **Level up:** quando `xp_total` é múltiplo de 5000 após ganhar recompensa da missão
- **Trilha padrão no dashboard:** `STARTER_PACK_TRACK`
- Missões bloqueadas se a anterior não estiver `FINALIZADA` (lógica em `SqlAlchemyProgressoMissaoRepository`)

---

## Próximos passos sugeridos

1. Gerar e aplicar migração Alembic + script de seed
2. Endpoints `/auth/login` e `/auth/register`
3. Proteger rotas com JWT
4. Substituir `MockEngineIA` por executor de testes (sandbox) ou serviço externo
5. Testes de integração com PostgreSQL (pytest + container ou DB local)

---

## Licença

A definir pelo proprietário do projeto.
