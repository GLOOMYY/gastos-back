# AGENTS.md

## 1. Purpose

This file defines the operating rules for any AI agent, developer, or automated coding assistant working on the **Gastos App** ecosystem.

The main repository is expected to contain multiple applications over time:

```text
gastos-app/
├── gastos-back/
├── gastos-front/
├── gastos-mobile/
├── docs/
└── AGENTS.md
```

The current priority is the backend:

```text
gastos-back
```

The backend is a modular monolith built with FastAPI and MongoDB. The system must be designed so that modules can later be extracted into microservices without rewriting the core business rules.

This file applies to the whole project unless a more specific `AGENTS.md` exists inside a subdirectory. When a nested `AGENTS.md` exists, the most specific file takes precedence for files inside its scope.

---

## 2. Project Context

- Product name: `Gastos App`
- Backend repository or module name: `gastos-back`
- Current architecture: modular monolith
- Future architecture: possible microservices only when justified

Possible future extraction candidates:

```text
identity
accounts
transactions
exchange-rates
budgets
investments
notifications
reports
```

Until a demonstrated need exists, keep the system as a well-structured modular monolith.

---

## 3. Primary Technology Stack

```text
Python 3.11.5
FastAPI
MongoDB Atlas
PyMongo Async
Pydantic
pytest
pytest-asyncio
Docker
Docker Compose
pip
```

Dependencies must be declared in:

```text
requirements.txt
requirements-dev.txt
```

Use the official asynchronous PyMongo API:

```python
from pymongo import AsyncMongoClient
```

Do not introduce Beanie, MongoEngine, ODMantic, or another ODM without explicit authorization.

---

## 4. General Agent Behavior

Before modifying code, the agent must first present a concise implementation plan including:

1. Requested scope.
2. Expected files to change.
3. Architectural impact.
4. Tests to add or update.
5. Assumptions.
6. Risks or open decisions.

The agent must not begin architectural changes without explicit authorization.

The agent must remain strictly within the requested scope and must not refactor unrelated code automatically.

When unrelated technical debt or an architecture violation is found, the agent must:

1. Describe the issue.
2. Explain its impact.
3. Add the correction proposal to the plan.
4. Request authorization before changing it.

The agent must not:

- Create commits unless explicitly authorized.
- Push branches unless explicitly authorized.
- Open pull requests unless explicitly authorized.
- Add dependencies without authorization.
- Modify Docker, CI, or configuration files without authorization.

---

## 5. Completion Report

At the end of every implementation task, provide:

1. Summary of changes.
2. Modified files.
3. Architectural decisions.
4. Tests created or updated.
5. Tests executed and results.
6. Risks, limitations, or pending work.
7. Required manual steps.

Never claim a command, test, migration, deployment, or validation was completed unless it was actually executed successfully.

---

## 6. Architecture

The backend must follow pragmatic Clean Architecture with these required layers:

```text
domain
application
infrastructure
presentation
```

Dependency direction:

```text
presentation
      ↓
application
      ↓
domain
```

Infrastructure implements abstractions required by inner layers:

```text
presentation ─────→ application ─────→ domain
                          ↑
                          │
                   infrastructure
```

Dependencies must point inward.

- Domain must not depend on application, infrastructure, presentation, FastAPI, PyMongo, BSON, or external providers.
- Application may depend on domain.
- Infrastructure may depend on application and domain.
- Presentation may depend on application.

---

## 7. Recommended Repository Structure

```text
gastos-app/
├── AGENTS.md
├── README.md
├── gastos-back/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   └── v1/
│   │   │       └── router.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── exceptions.py
│   │   │   ├── logging.py
│   │   │   └── security.py
│   │   ├── shared/
│   │   │   ├── domain/
│   │   │   ├── application/
│   │   │   └── infrastructure/
│   │   │       └── mongodb/
│   │   └── modules/
│   │       ├── users/
│   │       ├── account_types/
│   │       ├── accounts/
│   │       ├── categories/
│   │       └── transactions/
│   ├── scripts/
│   │   ├── create_indexes.py
│   │   ├── seed_account_types.py
│   │   ├── seed_categories.py
│   │   └── migrations/
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   ├── .env.example
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── Dockerfile
│   └── docker-compose.yml
├── gastos-front/
├── gastos-mobile/
└── docs/
```

Each backend module should use:

```text
module_name/
├── domain/
│   ├── entities.py
│   ├── value_objects.py
│   ├── enums.py
│   ├── exceptions.py
│   └── repositories.py
├── application/
│   ├── dto.py
│   ├── ports.py
│   └── use_cases/
├── infrastructure/
│   ├── documents.py
│   ├── mappers.py
│   ├── repositories.py
│   └── services.py
└── presentation/
    ├── schemas.py
    ├── dependencies.py
    └── router.py
```

Do not create empty abstractions only to imitate the structure.

---

## 8. Module Communication

Modules must not import infrastructure implementations from other modules.

Forbidden:

```python
from app.modules.users.infrastructure.repositories import MongoUserRepository
```

Prefer:

1. Public application ports.
2. Public use cases.
3. Domain events.
4. Specific read interfaces.
5. Shared identifiers or value objects.

Cross-module access must be explicit and narrow. Do not expose one module's persistence model to another.

---

## 9. Domain Layer Rules

The domain contains:

- Entities.
- Value objects.
- Domain enums.
- Domain exceptions.
- Business invariants.
- Repository interfaces when they represent domain needs.

The domain must not import:

```text
fastapi
pymongo
bson
pydantic
jwt
httpx
requests
```

The domain must not:

- Know collection names.
- Use `ObjectId`.
- Build MongoDB queries.
- Return HTTP responses.
- Raise `HTTPException`.
- Access environment variables.
- Call external APIs.
- Create database clients.

Prefer behavior-rich entities:

```python
account.withdraw(amount)
```

instead of:

```python
account.balance -= amount
```

---

## 10. Application Layer Rules

The application layer contains:

- Use cases.
- Commands.
- Queries.
- DTOs.
- Application ports.
- Authorization rules.
- Transaction orchestration.

State-changing use cases must have explicit names, such as:

```text
CreateAccount
RegisterIncome
RegisterExpense
TransferMoney
ReverseTransaction
CloseAccount
```

Read operations should also be explicit:

```text
GetAccount
ListAccounts
ListTransactions
GetMonthlySummary
GetExpensesByCategory
```

Application code must not:

- Import FastAPI.
- Import PyMongo or BSON.
- Use `ObjectId`.
- Raise `HTTPException`.
- Return `JSONResponse`.
- Receive FastAPI `Request`.
- Read environment variables.
- Create database connections.

Authorization belongs here:

```python
if account.user_id != command.user_id:
    raise AccountAccessDeniedError()
```

Never trust a `user_id` provided by the client.

---

## 11. Infrastructure Layer Rules

Infrastructure contains:

- MongoDB client setup.
- Collection access.
- Repository implementations.
- Document definitions.
- BSON conversion.
- `ObjectId` conversion.
- `Decimal128` conversion.
- External API clients.
- Password hashing.
- JWT implementation.
- Index creation.
- Migration scripts.
- Logging adapters.

Infrastructure must implement interfaces defined by the domain or application layers.

MongoDB documents are persistence models, not domain entities.

Repositories must not:

- Return raw MongoDB documents.
- Expose cursors outside infrastructure.
- Contain business rules.

---

## 12. Presentation Layer Rules

Presentation contains:

- FastAPI routers.
- Request schemas.
- Response schemas.
- Dependencies.
- Authentication extraction.
- HTTP status codes.
- Exception handlers.
- API versioning.

Base prefix:

```text
/api/v1
```

Use English for:

- Endpoint names.
- Request fields.
- Response fields.
- Error codes.
- Error messages.
- Technical identifiers.

Routers may only:

1. Receive input.
2. Resolve dependencies.
3. Build a command or query.
4. Execute a use case.
5. Map results to responses.

Routers must not:

- Access MongoDB.
- Use collections.
- Calculate balances.
- Enforce domain invariants.
- Run transaction logic.
- Access another module's infrastructure.

All endpoints must use explicit request and response schemas and define `response_model` when applicable.

---

## 13. Standard Error Format

All API errors must follow:

```json
{
  "code": "account_not_found",
  "message": "The account was not found.",
  "details": null,
  "request_id": "01JXYZ..."
}
```

Rules:

- `code` is stable and machine-readable.
- `message` is human-readable and in English.
- `details` may be null, an object, or a list.
- `request_id` supports log correlation.
- Clients must depend on `code`, not exact message wording.

Domain exceptions must be translated to HTTP errors in presentation.

---

## 14. MongoDB Atlas Rules

MongoDB Atlas is the primary database.

Connection data must come from environment variables:

```dotenv
MONGODB_URI=
MONGODB_DATABASE=
```

Never hardcode Atlas credentials, cluster hostnames, database names, secrets, or connection strings.

Never modify or create a real `.env` file. Only update `.env.example`.

---

## 15. MongoDB Transactions

Local development does not currently assume a replica set.

Therefore:

- Do not require local multidocument transactions for every test.
- Design transaction boundaries explicitly.
- Keep production compatible with Atlas transactions.
- Isolate transaction handling behind a Unit of Work or transaction manager.
- Do not simulate guarantees that do not exist.

Operations involving multiple financial documents must be transactional in Atlas, including:

- Transfers.
- Account balance plus transaction creation.
- Reversals.
- Cross-currency transfers.

When local integration tests cannot validate transactions, document that limitation.

---

## 16. Identifiers

Public identifiers use MongoDB `ObjectId` values serialized as strings.

Domain and application layers use:

```python
str
```

Infrastructure converts:

```text
str ↔ ObjectId
```

Do not use `ObjectId` in domain entities, commands, results, or application ports.

Validate identifiers before MongoDB queries.

---

## 17. Document Versioning and Migrations

All business documents must include:

```text
schema_version
```

Migration scripts belong in:

```text
scripts/migrations/
```

They must be:

- Versioned.
- Idempotent when possible.
- Restartable.
- Safe for partial execution.
- Observable through logs.
- Batch-oriented.
- Tested before production use.

Do not manually edit production documents instead of creating a migration.

---

## 18. MongoDB Schema Validation

Use MongoDB JSON Schema validation for important collections:

```text
users
account_types
accounts
categories
transactions
refresh_tokens
```

Responsibilities:

```text
Pydantic:
HTTP structure and input format.

Domain:
Business invariants.

MongoDB JSON Schema:
Persisted document structure.

Indexes:
Uniqueness and query performance.
```

Validator changes are schema migrations.

---

## 19. Indexes

Every new query must be reviewed for indexing.

Indexes must be managed in code.

Expected indexes include:

```text
users.normalized_email unique

accounts:
user_id + normalized_name
user_id + is_active + created_at

categories:
user_id + normalized_name + transaction_type

account_types:
user_id + normalized_name

transactions:
user_id + occurred_at
user_id + account_id + occurred_at
user_id + category_id + occurred_at
transfer_id
reversal_of_id
```

Consider read patterns, write cost, selectivity, compound order, uniqueness, partial filters, and overlap.

---

## 20. Financial Data Rules

Use `Decimal` in domain and application code.

Use `Decimal128` in MongoDB.

Never use `float` for money, balances, fees, exchange rates, or persisted financial calculations.

Each account has one currency. Different accounts may use different currencies.

Support all valid currency codes. Prefer uppercase ISO 4217-style codes.

Accounts may have negative balances. Do not impose a global `balance >= 0` rule.

Credit-card-specific behavior is outside the current scope.

---

## 21. Exchange Rates

Cross-currency transfers are allowed.

Supported rate modes:

```text
market
custom
```

Market rates must be obtained through an application port:

```python
class ExchangeRateProvider(Protocol):
    async def get_rate(
        self,
        source_currency: str,
        target_currency: str,
        occurred_at: datetime,
    ) -> Decimal:
        ...
```

The use case must not instantiate HTTP clients.

Store:

```text
source_currency
target_currency
source_amount
target_amount
exchange_rate
exchange_rate_mode
exchange_rate_provider
exchange_rate_timestamp
```

Use `Decimal` for all calculations.

Adding an exchange-rate SDK or dependency requires authorization.

---

## 22. Accounts and Balances

Store the current balance in the account for efficient reads.

Store transactions as an immutable ledger.

Balance changes must happen only through authorized use cases.

Use atomic MongoDB operations such as `find_one_and_update` and `$inc` when appropriate.

The design must support future reconciliation between stored balances and ledger totals.

---

## 23. Initial Balance

A non-zero initial balance must also create an immutable transaction.

Recommended type:

```text
initial_balance
```

Account creation and initial-balance transaction must remain consistent and be transactional in supported environments.

---

## 24. Transactions and Reversals

Confirmed financial transactions are immutable.

Do not edit or delete confirmed transactions.

Corrections use reversal transactions with:

```text
reversal_of_id
reason
created_at
created_by
```

The original transaction remains unchanged.

---

## 25. Transfers

A transfer creates:

1. Outgoing transaction.
2. Incoming transaction.

Both share:

```text
transfer_id
```

For cross-currency transfers, store both amounts and exchange-rate metadata.

A transfer is complete only when both balances and both transactions are persisted atomically.

---

## 26. Account Types and Categories

Account types and categories may be global or user-owned.

Ownership rules:

```text
user_id is null:
Global resource available to every user.

user_id contains an identifier:
Private resource available only to its owner.
```

The initial data scripts may create global resources and starter resources
for an explicitly identified initial user. User-owned seeded resources must
include that user's identifier and remain private to that user.

Suggested fields:

```text
_id
user_id
name
normalized_name
transaction_type
is_active
created_at
updated_at
schema_version
```

A user-owned category or account type must not be shared across users.

---

## 27. Authentication

Authentication uses:

```text
email and password
JWT access tokens
JWT refresh tokens
```

Registration is public.

Current role:

```text
user
```

Do not add admin roles unless requested.

Email verification and password recovery belong to version 2.

Use `passlib` with Argon2 for password hashing.

Never log passwords or return password hashes.

---

## 28. Refresh Tokens

Recommended rules:

- Store only token hashes.
- Support expiration.
- Support revocation.
- Support rotation.
- Track token families or sessions.
- Detect reuse when rotation is implemented.
- Associate tokens with users.
- Allow logout.
- Allow future logout from all devices.

Suggested fields:

```text
user_id
token_hash
family_id
expires_at
revoked_at
replaced_by_id
created_at
user_agent
ip_address
schema_version
```

Minimize sensitive metadata.

---

## 29. Cursor Pagination

Use cursor-based pagination.

Response shape:

```json
{
  "items": [],
  "next_cursor": null,
  "has_more": false
}
```

Cursors should be opaque when possible and must be validated.

Transaction ordering should be deterministic:

```text
occurred_at descending
_id descending
```

Indexes must support cursor order.

---

## 30. Pydantic Schemas

All HTTP input and output uses explicit Pydantic schemas.

Request schemas validate:

- Shape.
- Length.
- Enums.
- Currency format.
- Decimal precision.
- Identifiers where appropriate.

Response schemas must never expose:

- Password hashes.
- Raw refresh tokens.
- Provider secrets.
- Raw MongoDB documents.

Do not reuse persistence documents as API schemas.

---

## 31. Naming and Language

Use English for code, endpoints, fields, collections, error codes, and error messages.

Project documentation may be written in Spanish.

Git commit messages and pull request descriptions must be in Spanish, while Conventional Commit prefixes remain in English.

Examples:

```text
feat(accounts): agregar creación de cuentas multimoneda
fix(transactions): corregir reversión de movimientos
test(auth): añadir pruebas de rotación de refresh token
docs(api): actualizar variables de entorno
```

---

## 32. Python Style

Target:

```text
Python 3.11.5
```

Follow PEP 8.

Preferred maximum line length:

```text
79 characters
```

Use type hints throughout.

Treat strict typing as a project standard even before a static type checker is added.

Avoid `Any` whenever possible.

Avoid generic `except Exception` unless used intentionally at a boundary and logged or re-raised.

Never silently swallow exceptions.

Prefer absolute imports.

---

## 33. Docstrings

All modules, public classes, public methods, and public functions require docstrings.

Follow:

```text
PEP 257
Google Python Style Guide
```

Example:

```python
async def get_by_id(self, account_id: str) -> Account | None:
    """Retrieve an account by its public identifier.

    Args:
        account_id: MongoDB ObjectId serialized as a string.

    Returns:
        The account when it exists; otherwise, None.

    Raises:
        ValueError: If the identifier is malformed.
    """
```

Avoid meaningless docstrings that only repeat the name.

---

## 34. Tooling

The project adopts:

```text
Ruff
mypy
```

Ruff is the formatter and linter. Mypy is the static type checker. New code
must be compatible with both tools and keep type annotations precise.

The project does not currently require:

```text
Pyright
pre-commit
GitHub Actions
dependency security scanning
```

Do not add the tools above without authorization.

---

## 35. Testing

Use:

```text
pytest
pytest-asyncio
```

Structure:

```text
tests/
├── unit/
├── integration/
└── e2e/
```

Every functional change must add or update tests.

Required categories:

1. Success cases.
2. Domain failures.
3. Authorization failures.
4. Invalid identifiers.
5. Duplicate constraints.
6. Rollback where applicable.
7. Concurrency-sensitive behavior.
8. Unique index behavior.
9. Cursor pagination.
10. Cross-currency calculations.

Coverage target:

```text
80%
```

Unit tests must not require FastAPI, MongoDB, network access, Atlas credentials, or Docker.

Use fake repositories and providers.

Integration tests must clearly document when real MongoDB behavior is not being validated.

Never run destructive tests against production or development collections.

---

## 36. Test Commands

Current mandatory completion gate:

```bash
ruff check .
mypy app
pytest
```

When Python files are modified, also verify formatting with:

```bash
ruff format --check .
```

When coverage support is configured:

```bash
pytest --cov=app --cov-report=term-missing
```

Do not add other mandatory formatter, linter, type-checker, or CI gates
without authorization.

---

## 37. Docker

The project uses Docker and Docker Compose.

Docker changes require authorization.

Docker configuration must:

- Avoid embedded secrets.
- Use environment variables.
- Support local backend execution.
- Avoid requiring a local MongoDB instance.
- Keep Atlas as the primary database.
- Use reproducible dependencies.
- Prefer a non-root production user.
- Include health checks when practical.

Do not add a local MongoDB service as a hard requirement without authorization.

---

## 38. Configuration

Use environment variables and `pydantic-settings`.

Recommended variables:

```dotenv
APP_NAME=Gastos API
ENVIRONMENT=development
DEBUG=false

MONGODB_URI=
MONGODB_DATABASE=

JWT_SECRET_KEY=
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30

EXCHANGE_RATE_PROVIDER=
EXCHANGE_RATE_API_KEY=
```

Never commit `.env`, credentials, private keys, Atlas secrets, JWT secrets, or API keys.

Only update `.env.example`.

---

## 39. External Services

Access external services through application ports:

```text
ExchangeRateProvider
EmailSender
Clock
IdGenerator
TokenService
PasswordHasher
```

Infrastructure implementations must include:

- Timeouts.
- Controlled retries when appropriate.
- Error mapping.
- Secret-safe logging.
- Test doubles.
- Clear failure behavior.

New third-party dependencies require authorization.

---

## 40. Logging

Use structured logging. Do not use `print()` for application logs.

Useful fields:

```text
request_id
user_id
use_case
resource_id
duration
error_code
```

Never log passwords, hashes, JWTs, refresh tokens, Atlas URIs, API keys, or unnecessary full financial payloads.

---

## 41. Security

Minimum requirements:

- Argon2 password hashing.
- JWT expiration.
- Refresh-token rotation design.
- Environment-based secrets.
- Resource ownership validation.
- Restricted CORS.
- No stack traces in production responses.
- Input size validation.
- No raw exception leakage.
- Rate-limit-ready authentication.
- Least-privilege Atlas users.
- No credentials in local files.
- No secrets in logs.

Security behavior must be tested.

---

## 42. Git Workflow

Use:

```text
main
feature branches
```

Examples:

```text
feature/create-account
feature/register-expense
fix/refresh-token-rotation
docs/update-agents
```

Use Conventional Commits.

Allowed prefixes:

```text
feat
fix
refactor
test
docs
chore
build
ci
perf
```

Messages must be in Spanish.

The agent must not commit, push, or open pull requests without explicit authorization.

---

## 43. README Maintenance

Update README when changes affect:

- Setup.
- Environment variables.
- Architecture.
- Commands.
- Dependencies.
- Docker.
- API conventions.
- Testing.
- Deployment.
- Folder structure.

Include required README changes in the implementation plan.

---

## 44. Dependency Policy

Before adding, removing, or replacing a dependency, request authorization and explain:

1. Name.
2. Purpose.
3. Why existing tools are insufficient.
4. Maintenance status.
5. Security considerations.
6. Deployment impact.
7. Alternatives.

Prefer official and well-maintained libraries.

---

## 45. Scope Control

The agent must not:

- Rename unrelated modules.
- Reformat the entire repository.
- Change architecture opportunistically.
- Upgrade dependencies without authorization.
- Replace MongoDB.
- Introduce an ODM.
- Introduce microservices.
- Add CI or static-analysis tools.
- Add unrelated abstractions.
- Modify frontend or mobile code in a backend-only task.

Report related issues without changing them unless approved.

---

## 46. Architectural Violations

When existing code violates these rules, report:

1. File.
2. Violated rule.
3. Practical risk.
4. Smallest correction.
5. Whether the requested task can proceed safely.

Any correction that expands scope requires authorization.

---

## 47. Definition of Done

A task is complete only when:

- Requested behavior is implemented.
- Architecture rules are respected.
- Tests are added or updated.
- Required tests pass.
- Ruff checks pass.
- Mypy checks pass.
- Public schemas are explicit.
- Errors use the standard format.
- Money uses `Decimal`.
- MongoDB uses `Decimal128`.
- Authorization is enforced.
- Index impact is reviewed.
- Schema-version impact is reviewed.
- `.env.example` is updated when needed.
- README is updated when needed.
- No secrets are introduced.
- Completion report is provided.

---

## 48. Current and Future Modules

Initial modules:

```text
users
account_types
accounts
categories
transactions
```

Possible future modules:

```text
exchange_rates
budgets
savings
investments
debts
goals
reports
notifications
```

New modules must follow the same layered architecture.

---

## 49. Suggested Financial Documents

### User

```text
_id
email
normalized_email
password_hash
role
is_active
created_at
updated_at
schema_version
```

### Account type

```text
_id
user_id
code
name
description
is_active
created_at
updated_at
schema_version
```

### Account

```text
_id
user_id
account_type_id
name
normalized_name
currency
balance
is_active
created_at
updated_at
schema_version
```

### Category

```text
_id
user_id
name
normalized_name
transaction_type
is_active
created_at
updated_at
schema_version
```

For account types and categories, `user_id` is null only for global resources.

### Transaction

```text
_id
user_id
account_id
category_id
transaction_type
amount
currency
description
occurred_at
created_at
transfer_id
reversal_of_id
status
exchange_rate
exchange_rate_mode
exchange_rate_provider
exchange_rate_timestamp
source_amount
target_amount
source_currency
target_currency
schema_version
```

Only include exchange-rate fields when applicable. Avoid unnecessary null fields.

---

## 50. Final Decision Checklist

Before implementation, verify:

1. Can the use case run without FastAPI?
2. Can the business rule be tested without MongoDB?
3. Does the domain avoid `ObjectId`?
4. Does the application avoid PyMongo?
5. Is the router free of business logic?
6. Is authorization enforced?
7. Does money use `Decimal`?
8. Does persistence use `Decimal128`?
9. Is transaction history immutable?
10. Is an Atlas transaction required?
11. Is a new index required?
12. Must `schema_version` change?
13. Must `.env.example` change?
14. Must README change?
15. Are tests included?
16. Is scope still respected?
17. Is authorization required for a dependency or infrastructure change?

If any answer is unclear, state the uncertainty in the plan before changing code.
