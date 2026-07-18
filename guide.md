# Guía de Clean Architecture con FastAPI y MongoDB

> Guía práctica para construir una API mantenible, escalable y testeable utilizando FastAPI, MongoDB, PyMongo Async y Pydantic.

---

## 1. Objetivo

Esta guía establece los lineamientos para construir una API con:

- FastAPI.
- MongoDB.
- PyMongo Async.
- Pydantic.
- Clean Architecture.
- Repository Pattern.
- Unit of Work.
- Dependency Injection.
- Pruebas unitarias y de integración.

El ejemplo principal será un sistema de finanzas personales multiusuario que permita administrar:

- Usuarios.
- Tipos de cuenta.
- Cuentas.
- Categorías.
- Ingresos.
- Gastos.
- Transferencias.
- Ahorros.
- Inversiones.

El propósito de Clean Architecture no es crear muchas carpetas o clases innecesarias. Su propósito es mantener las reglas del negocio independientes de:

- FastAPI.
- MongoDB.
- PyMongo.
- Proveedores externos.
- Sistemas de autenticación.
- Detalles de infraestructura.

---

# 2. Principio fundamental

La regla principal de Clean Architecture es:

> Las dependencias del código deben apuntar hacia el centro de la aplicación.

Las capas internas contienen las reglas más importantes y estables.

Las capas externas contienen detalles técnicos que pueden cambiar.

```text
┌─────────────────────────────────────────────┐
│ Infraestructura                             │
│ MongoDB, PyMongo, JWT, correo, servicios    │
│                                             │
│   ┌─────────────────────────────────────┐   │
│   │ Presentación                        │   │
│   │ FastAPI, routers, schemas HTTP      │   │
│   │                                     │   │
│   │   ┌─────────────────────────────┐   │   │
│   │   │ Aplicación                  │   │   │
│   │   │ Casos de uso, DTO, puertos  │   │   │
│   │   │                             │   │   │
│   │   │   ┌─────────────────────┐   │   │   │
│   │   │   │ Dominio             │   │   │   │
│   │   │   │ Entidades y reglas  │   │   │   │
│   │   │   └─────────────────────┘   │   │   │
│   │   └─────────────────────────────┘   │   │
│   └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

Dirección de dependencias:

```text
presentation
      ↓
application
      ↓
domain
```

La infraestructura implementa interfaces definidas por las capas internas:

```text
presentation ─────→ application ─────→ domain
                          ↑
                          │
                   infrastructure
```

---

# 3. Capas de la aplicación

## 3.1. Dominio

Es el núcleo del sistema.

Contiene:

- Entidades.
- Objetos de valor.
- Enumeraciones.
- Reglas del negocio.
- Excepciones de dominio.
- Interfaces de repositorios.
- Invariantes.

Ejemplos:

```text
User
Account
Transaction
Money
TransactionType
InsufficientBalanceError
AccountNotFoundError
```

El dominio no debe importar:

```text
fastapi
pymongo
bson
pydantic
jwt
```

El dominio tampoco debe:

- Conocer colecciones de MongoDB.
- Construir consultas MongoDB.
- Utilizar `ObjectId`.
- Lanzar `HTTPException`.
- Leer variables de entorno.
- Conectarse a bases de datos.

---

## 3.2. Aplicación

Contiene los casos de uso del sistema.

Ejemplos:

```text
CreateAccount
RegisterIncome
RegisterExpense
TransferMoney
CloseAccount
ListTransactions
GetMonthlySummary
```

La capa de aplicación:

- Coordina entidades.
- Usa repositorios mediante interfaces.
- Gestiona transacciones.
- Ejecuta autorización de negocio.
- Define comandos y resultados.
- Controla el flujo de una operación.

No debe:

- Importar FastAPI.
- Importar colecciones PyMongo.
- Construir consultas MongoDB.
- Lanzar `HTTPException`.
- Leer objetos `Request`.
- Devolver respuestas JSON.

---

## 3.3. Infraestructura

Contiene los detalles técnicos.

Ejemplos:

- Conexión a MongoDB.
- Implementaciones de repositorios.
- Conversión entre documentos y entidades.
- Manejo de `ObjectId`.
- Implementación de transacciones.
- JWT.
- Hash de contraseñas.
- Servicios de correo.
- Servicios externos.
- Creación de índices.

La infraestructura puede depender del dominio y de la aplicación.

---

## 3.4. Presentación

Expone la aplicación mediante HTTP.

Contiene:

- Routers FastAPI.
- Schemas Pydantic.
- Dependencias de FastAPI.
- Autenticación HTTP.
- Conversión de errores a respuestas HTTP.
- Versionamiento de endpoints.

La presentación no debe contener reglas del negocio.

---

# 4. Estructura de carpetas

Se recomienda organizar el proyecto por módulos funcionales, manteniendo las capas dentro de cada módulo.

```text
expense_control/
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   └── v1/
│   │       └── router.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   ├── logging.py
│   │   └── security.py
│   │
│   ├── shared/
│   │   ├── domain/
│   │   │   ├── entity.py
│   │   │   ├── exceptions.py
│   │   │   └── value_objects.py
│   │   │
│   │   ├── application/
│   │   │   ├── pagination.py
│   │   │   └── unit_of_work.py
│   │   │
│   │   └── infrastructure/
│   │       └── mongodb/
│   │           ├── client.py
│   │           ├── database.py
│   │           ├── indexes.py
│   │           └── unit_of_work.py
│   │
│   └── modules/
│       ├── users/
│       │   ├── domain/
│       │   │   ├── entities.py
│       │   │   ├── exceptions.py
│       │   │   ├── repositories.py
│       │   │   └── value_objects.py
│       │   │
│       │   ├── application/
│       │   │   ├── dto.py
│       │   │   ├── ports.py
│       │   │   └── use_cases/
│       │   │       ├── create_user.py
│       │   │       ├── authenticate_user.py
│       │   │       └── get_user.py
│       │   │
│       │   ├── infrastructure/
│       │   │   ├── documents.py
│       │   │   ├── mappers.py
│       │   │   ├── repositories.py
│       │   │   └── password_hasher.py
│       │   │
│       │   └── presentation/
│       │       ├── dependencies.py
│       │       ├── router.py
│       │       └── schemas.py
│       │
│       ├── accounts/
│       │   ├── domain/
│       │   │   ├── entities.py
│       │   │   ├── exceptions.py
│       │   │   └── repositories.py
│       │   ├── application/
│       │   │   ├── dto.py
│       │   │   └── use_cases/
│       │   │       ├── create_account.py
│       │   │       ├── get_account.py
│       │   │       ├── list_accounts.py
│       │   │       └── close_account.py
│       │   ├── infrastructure/
│       │   │   ├── documents.py
│       │   │   ├── mappers.py
│       │   │   └── repositories.py
│       │   └── presentation/
│       │       ├── dependencies.py
│       │       ├── router.py
│       │       └── schemas.py
│       │
│       └── transactions/
│           ├── domain/
│           │   ├── entities.py
│           │   ├── enums.py
│           │   ├── exceptions.py
│           │   └── repositories.py
│           ├── application/
│           │   ├── dto.py
│           │   └── use_cases/
│           │       ├── register_income.py
│           │       ├── register_expense.py
│           │       ├── reverse_transaction.py
│           │       └── transfer_money.py
│           ├── infrastructure/
│           │   ├── documents.py
│           │   ├── mappers.py
│           │   └── repositories.py
│           └── presentation/
│               ├── dependencies.py
│               ├── router.py
│               └── schemas.py
│
├── scripts/
│   ├── create_indexes.py
│   ├── seed_account_types.py
│   └── migrations/
│
├── tests/
│   ├── unit/
│   │   ├── domain/
│   │   └── application/
│   ├── integration/
│   │   └── repositories/
│   └── e2e/
│       └── api/
│
├── .env
├── .env.example
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

FastAPI permite dividir aplicaciones grandes usando `APIRouter` y dependencias, por lo que esta organización encaja naturalmente con su sistema de composición. citeturn739995search0turn739995search2

---

# 5. Driver recomendado

Para proyectos nuevos se recomienda:

```text
PyMongo Async
```

No se recomienda comenzar un proyecto nuevo con Motor.

Instalación:

```bash
pip install pymongo
```

Importación:

```python
from pymongo import AsyncMongoClient
```

Ejemplo:

```python
client = AsyncMongoClient(
    "mongodb://localhost:27017",
)
```

PyMongo es el driver oficial de MongoDB para Python. La API asíncrona de PyMongo reemplaza el uso tradicional de Motor para nuevos proyectos asíncronos. citeturn782399search0turn782399search3turn782399search8

---

# 6. Configuración

```python
# app/core/config.py

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Expense Control API"
    environment: str = "development"
    debug: bool = False

    mongodb_uri: str
    mongodb_database: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
```

Archivo `.env.example`:

```dotenv
APP_NAME=Expense Control API
ENVIRONMENT=development
DEBUG=false

MONGODB_URI=mongodb://localhost:27017/?replicaSet=rs0
MONGODB_DATABASE=expense_control

JWT_SECRET_KEY=change-me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

No se deben almacenar secretos reales en el repositorio.

---

# 7. Cliente MongoDB

El cliente debe crearse una vez durante el ciclo de vida de la aplicación.

```python
# app/shared/infrastructure/mongodb/client.py

from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from app.core.config import settings


class MongoDatabase:

    def __init__(self) -> None:
        self.client: AsyncMongoClient | None = None
        self.database: AsyncDatabase | None = None

    async def connect(self) -> None:
        self.client = AsyncMongoClient(settings.mongodb_uri)
        self.database = self.client[settings.mongodb_database]

        await self.client.admin.command("ping")

    async def disconnect(self) -> None:
        if self.client is not None:
            await self.client.close()

        self.client = None
        self.database = None

    def get_database(self) -> AsyncDatabase:
        if self.database is None:
            raise RuntimeError(
                "La conexión con MongoDB no está inicializada."
            )

        return self.database


mongo_database = MongoDatabase()
```

---

# 8. Ciclo de vida de FastAPI

```python
# app/main.py

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.shared.infrastructure.mongodb.client import mongo_database
from app.shared.infrastructure.mongodb.indexes import create_indexes


@asynccontextmanager
async def lifespan(app: FastAPI):
    await mongo_database.connect()
    await create_indexes(mongo_database.get_database())

    yield

    await mongo_database.disconnect()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.include_router(api_v1_router)
    register_exception_handlers(app)

    return app


app = create_app()
```

---

# 9. Dependencia de base de datos

```python
# app/shared/infrastructure/mongodb/database.py

from typing import Annotated

from fastapi import Depends
from pymongo.asynchronous.database import AsyncDatabase

from app.shared.infrastructure.mongodb.client import mongo_database


def get_database() -> AsyncDatabase:
    return mongo_database.get_database()


MongoDatabaseDep = Annotated[
    AsyncDatabase,
    Depends(get_database),
]
```

No se debe abrir un cliente nuevo en cada petición.

Incorrecto:

```python
@router.get("/accounts")
async def list_accounts():
    client = AsyncMongoClient(...)
```

Correcto:

```python
@router.get("/accounts")
async def list_accounts(database: MongoDatabaseDep):
    ...
```

---

# 10. Identificadores del dominio

El dominio no debería depender directamente de `ObjectId`.

Se recomienda utilizar identificadores como cadenas:

```python
AccountId = str
UserId = str
TransactionId = str
```

La infraestructura convierte:

```text
str ↔ ObjectId
```

Esto mantiene el dominio independiente de MongoDB.

---

# 11. Conversión segura de ObjectId

```python
# app/shared/infrastructure/mongodb/object_id.py

from bson import ObjectId
from bson.errors import InvalidId


def to_object_id(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except (InvalidId, TypeError) as error:
        raise ValueError(
            f"El identificador '{value}' no es válido."
        ) from error


def object_id_to_str(value: ObjectId) -> str:
    return str(value)
```

`ObjectId` tiene una representación hexadecimal útil para URLs, pero debe validarse antes de utilizarse en una consulta. citeturn782399search7

---

# 12. Entidad de dominio

```python
# app/modules/accounts/domain/entities.py

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from app.modules.accounts.domain.exceptions import (
    AccountAlreadyClosedError,
    InsufficientBalanceError,
    InvalidInitialBalanceError,
)


@dataclass
class Account:
    id: str | None
    user_id: str
    account_type_id: str
    name: str
    currency: str
    balance: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        user_id: str,
        account_type_id: str,
        name: str,
        currency: str,
        initial_balance: Decimal,
    ) -> "Account":
        clean_name = name.strip()
        clean_currency = currency.strip().upper()

        if not clean_name:
            raise ValueError(
                "El nombre de la cuenta es obligatorio."
            )

        if len(clean_currency) != 3:
            raise ValueError(
                "La moneda debe tener tres caracteres."
            )

        if initial_balance < Decimal("0"):
            raise InvalidInitialBalanceError()

        now = datetime.now(UTC)

        return cls(
            id=None,
            user_id=user_id,
            account_type_id=account_type_id,
            name=clean_name,
            currency=clean_currency,
            balance=initial_balance,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

    def deposit(self, amount: Decimal) -> None:
        if amount <= Decimal("0"):
            raise ValueError(
                "El valor debe ser mayor que cero."
            )

        self.balance += amount
        self.updated_at = datetime.now(UTC)

    def withdraw(self, amount: Decimal) -> None:
        if amount <= Decimal("0"):
            raise ValueError(
                "El valor debe ser mayor que cero."
            )

        if amount > self.balance:
            raise InsufficientBalanceError()

        self.balance -= amount
        self.updated_at = datetime.now(UTC)

    def close(self) -> None:
        if not self.is_active:
            raise AccountAlreadyClosedError()

        self.is_active = False
        self.updated_at = datetime.now(UTC)
```

La entidad:

- No utiliza Pydantic.
- No utiliza PyMongo.
- No utiliza `ObjectId`.
- No conoce el nombre de la colección.
- No lanza errores HTTP.
- No guarda datos directamente.

---

# 13. Dinero en MongoDB

No se debe utilizar `float` para cantidades financieras.

Opciones recomendadas:

## Opción A: Decimal128

MongoDB ofrece el tipo BSON `Decimal128`.

```python
from bson.decimal128 import Decimal128
```

Conversión:

```python
from decimal import Decimal

from bson.decimal128 import Decimal128


def decimal_to_bson(value: Decimal) -> Decimal128:
    return Decimal128(value)


def bson_to_decimal(value: Decimal128) -> Decimal:
    return value.to_decimal()
```

Documento:

```json
{
  "balance": {
    "$numberDecimal": "150000.00"
  }
}
```

## Opción B: almacenar centavos como entero

```json
{
  "balance_in_cents": 15000000
}
```

Para este proyecto se recomienda:

> Usar `Decimal` en el dominio y `Decimal128` en MongoDB.

---

# 14. Documento de persistencia

El documento de MongoDB no debe convertirse en la entidad principal del dominio.

Ejemplo conceptual:

```python
# app/modules/accounts/infrastructure/documents.py

from datetime import datetime
from typing import TypedDict

from bson import ObjectId
from bson.decimal128 import Decimal128


class AccountDocument(TypedDict):
    _id: ObjectId
    user_id: ObjectId
    account_type_id: ObjectId
    name: str
    currency: str
    balance: Decimal128
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

`TypedDict` ayuda con el tipado, pero no valida datos en tiempo de ejecución.

---

# 15. Mapeo documento-entidad

```python
# app/modules/accounts/infrastructure/mappers.py

from bson import ObjectId
from bson.decimal128 import Decimal128

from app.modules.accounts.domain.entities import Account


def document_to_account(document: dict) -> Account:
    return Account(
        id=str(document["_id"]),
        user_id=str(document["user_id"]),
        account_type_id=str(document["account_type_id"]),
        name=document["name"],
        currency=document["currency"],
        balance=document["balance"].to_decimal(),
        is_active=document["is_active"],
        created_at=document["created_at"],
        updated_at=document["updated_at"],
    )


def account_to_document(account: Account) -> dict:
    document = {
        "user_id": ObjectId(account.user_id),
        "account_type_id": ObjectId(account.account_type_id),
        "name": account.name,
        "currency": account.currency,
        "balance": Decimal128(account.balance),
        "is_active": account.is_active,
        "created_at": account.created_at,
        "updated_at": account.updated_at,
    }

    if account.id is not None:
        document["_id"] = ObjectId(account.id)

    return document
```

---

# 16. Interfaz del repositorio

```python
# app/modules/accounts/domain/repositories.py

from typing import Protocol

from app.modules.accounts.domain.entities import Account


class AccountRepository(Protocol):

    async def add(self, account: Account) -> Account:
        ...

    async def get_by_id(
        self,
        account_id: str,
    ) -> Account | None:
        ...

    async def list_by_user(
        self,
        user_id: str,
    ) -> list[Account]:
        ...

    async def update(self, account: Account) -> None:
        ...

    async def exists_name_for_user(
        self,
        user_id: str,
        name: str,
    ) -> bool:
        ...
```

La interfaz:

- No importa PyMongo.
- No recibe colecciones.
- No devuelve documentos crudos.
- No utiliza `ObjectId`.

---

# 17. Repositorio MongoDB

```python
# app/modules/accounts/infrastructure/repositories.py

from bson import ObjectId
from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.database import AsyncDatabase

from app.modules.accounts.domain.entities import Account
from app.modules.accounts.infrastructure.mappers import (
    account_to_document,
    document_to_account,
)
from app.shared.infrastructure.mongodb.object_id import to_object_id


class MongoAccountRepository:

    def __init__(
        self,
        database: AsyncDatabase,
        session: AsyncClientSession | None = None,
    ) -> None:
        self.collection: AsyncCollection = database["accounts"]
        self.session = session

    async def add(self, account: Account) -> Account:
        document = account_to_document(account)
        document.pop("_id", None)

        result = await self.collection.insert_one(
            document,
            session=self.session,
        )

        created_document = await self.collection.find_one(
            {"_id": result.inserted_id},
            session=self.session,
        )

        if created_document is None:
            raise RuntimeError(
                "No fue posible recuperar la cuenta creada."
            )

        return document_to_account(created_document)

    async def get_by_id(
        self,
        account_id: str,
    ) -> Account | None:
        document = await self.collection.find_one(
            {"_id": to_object_id(account_id)},
            session=self.session,
        )

        if document is None:
            return None

        return document_to_account(document)

    async def list_by_user(
        self,
        user_id: str,
    ) -> list[Account]:
        cursor = self.collection.find(
            {
                "user_id": to_object_id(user_id),
                "is_active": True,
            },
            session=self.session,
        ).sort("created_at", -1)

        accounts: list[Account] = []

        async for document in cursor:
            accounts.append(document_to_account(document))

        return accounts

    async def update(self, account: Account) -> None:
        if account.id is None:
            raise ValueError(
                "No se puede actualizar una cuenta sin ID."
            )

        result = await self.collection.update_one(
            {"_id": to_object_id(account.id)},
            {
                "$set": {
                    "name": account.name,
                    "currency": account.currency,
                    "balance": account_to_document(account)["balance"],
                    "is_active": account.is_active,
                    "updated_at": account.updated_at,
                }
            },
            session=self.session,
        )

        if result.matched_count == 0:
            raise ValueError(
                "La cuenta no existe en MongoDB."
            )

    async def exists_name_for_user(
        self,
        user_id: str,
        name: str,
    ) -> bool:
        document = await self.collection.find_one(
            {
                "user_id": to_object_id(user_id),
                "normalized_name": name.strip().lower(),
                "is_active": True,
            },
            projection={"_id": 1},
            session=self.session,
        )

        return document is not None
```

---

# 18. DTO de aplicación

```python
# app/modules/accounts/application/dto.py

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class CreateAccountCommand:
    user_id: str
    account_type_id: str
    name: str
    currency: str
    initial_balance: Decimal


@dataclass(frozen=True)
class AccountResult:
    id: str
    user_id: str
    account_type_id: str
    name: str
    currency: str
    balance: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

Los DTO:

- No representan documentos MongoDB.
- No utilizan `ObjectId`.
- No conocen FastAPI.
- No conocen Pydantic HTTP.

---

# 19. Caso de uso

```python
# app/modules/accounts/application/use_cases/create_account.py

from app.modules.accounts.application.dto import (
    AccountResult,
    CreateAccountCommand,
)
from app.modules.accounts.domain.entities import Account
from app.modules.accounts.domain.exceptions import (
    AccountNameAlreadyExistsError,
)
from app.modules.accounts.domain.repositories import AccountRepository


class CreateAccount:

    def __init__(
        self,
        account_repository: AccountRepository,
    ) -> None:
        self.account_repository = account_repository

    async def execute(
        self,
        command: CreateAccountCommand,
    ) -> AccountResult:
        exists = await self.account_repository.exists_name_for_user(
            user_id=command.user_id,
            name=command.name,
        )

        if exists:
            raise AccountNameAlreadyExistsError(command.name)

        account = Account.create(
            user_id=command.user_id,
            account_type_id=command.account_type_id,
            name=command.name,
            currency=command.currency,
            initial_balance=command.initial_balance,
        )

        created_account = await self.account_repository.add(account)

        if created_account.id is None:
            raise RuntimeError(
                "La cuenta fue creada sin identificador."
            )

        return AccountResult(
            id=created_account.id,
            user_id=created_account.user_id,
            account_type_id=created_account.account_type_id,
            name=created_account.name,
            currency=created_account.currency,
            balance=created_account.balance,
            is_active=created_account.is_active,
            created_at=created_account.created_at,
            updated_at=created_account.updated_at,
        )
```

Crear una sola cuenta requiere una única inserción de documento, por lo que no necesita una transacción multidocumento.

MongoDB garantiza atomicidad para una operación sobre un solo documento.

---

# 20. Unit of Work con MongoDB

MongoDB utiliza sesiones para agrupar operaciones relacionadas.

```python
# app/shared/application/unit_of_work.py

from types import TracebackType
from typing import Protocol, Self


class UnitOfWork(Protocol):

    async def __aenter__(self) -> Self:
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        ...

    async def commit(self) -> None:
        ...

    async def rollback(self) -> None:
        ...
```

Implementación:

```python
# app/shared/infrastructure/mongodb/unit_of_work.py

from types import TracebackType
from typing import Self

from pymongo import AsyncMongoClient
from pymongo.asynchronous.client_session import AsyncClientSession


class MongoUnitOfWork:

    def __init__(
        self,
        client: AsyncMongoClient,
    ) -> None:
        self.client = client
        self.session: AsyncClientSession | None = None

    async def __aenter__(self) -> Self:
        self.session = self.client.start_session()
        await self.session.start_transaction()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self.session is None:
            return

        try:
            if exc_type is not None:
                await self.rollback()
        finally:
            await self.session.end_session()

    async def commit(self) -> None:
        if self.session is None:
            raise RuntimeError(
                "No existe una sesión activa."
            )

        await self.session.commit_transaction()

    async def rollback(self) -> None:
        if self.session is None:
            return

        await self.session.abort_transaction()
```

Las transacciones permiten ejecutar varias operaciones que solamente se hacen visibles cuando se confirma la transacción; si ocurre un error, los cambios pueden abortarse. citeturn782399search5

---

# 21. Requisito para transacciones

Para usar transacciones multidocumento, MongoDB debe ejecutarse como:

- Replica set.
- Clúster fragmentado compatible.

Un servidor standalone local no permite trabajar de la misma manera con transacciones multidocumento.

Para desarrollo local conviene ejecutar MongoDB como un replica set de un solo nodo.

---

# 22. Docker Compose con replica set

```yaml
services:
  mongodb:
    image: mongo:8
    container_name: expense-control-mongodb
    command: ["mongod", "--replSet", "rs0", "--bind_ip_all"]
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db

  mongo-init:
    image: mongo:8
    depends_on:
      - mongodb
    restart: "no"
    entrypoint:
      - bash
      - -c
      - |
        sleep 5
        mongosh --host mongodb:27017 --eval '
          try {
            rs.status()
          } catch (error) {
            rs.initiate({
              _id: "rs0",
              members: [
                {
                  _id: 0,
                  host: "mongodb:27017"
                }
              ]
            })
          }
        '

volumes:
  mongodb_data:
```

Conexión desde otro contenedor:

```dotenv
MONGODB_URI=mongodb://mongodb:27017/?replicaSet=rs0
```

---

# 23. Ejemplo: registrar un gasto

Esta operación debe:

1. Consultar la cuenta.
2. Verificar que pertenece al usuario.
3. Verificar saldo.
4. Reducir el saldo.
5. Crear el movimiento.
6. Confirmar ambas operaciones juntas.

## Comando

```python
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class RegisterExpenseCommand:
    user_id: str
    account_id: str
    category_id: str | None
    amount: Decimal
    description: str | None
    occurred_at: datetime
```

## Caso de uso

```python
class RegisterExpense:

    def __init__(
        self,
        database,
        mongo_client,
    ) -> None:
        self.database = database
        self.mongo_client = mongo_client

    async def execute(
        self,
        command: RegisterExpenseCommand,
    ) -> TransactionResult:
        async with MongoUnitOfWork(self.mongo_client) as unit_of_work:
            if unit_of_work.session is None:
                raise RuntimeError(
                    "No fue posible iniciar la transacción."
                )

            accounts = MongoAccountRepository(
                database=self.database,
                session=unit_of_work.session,
            )

            transactions = MongoTransactionRepository(
                database=self.database,
                session=unit_of_work.session,
            )

            account = await accounts.get_by_id(
                command.account_id
            )

            if account is None:
                raise AccountNotFoundError(
                    command.account_id
                )

            if account.user_id != command.user_id:
                raise AccountAccessDeniedError()

            account.withdraw(command.amount)

            transaction = Transaction.create_expense(
                user_id=command.user_id,
                account_id=command.account_id,
                category_id=command.category_id,
                amount=command.amount,
                currency=account.currency,
                description=command.description,
                occurred_at=command.occurred_at,
            )

            await accounts.update(account)
            created_transaction = await transactions.add(
                transaction
            )

            await unit_of_work.commit()

            return transaction_to_result(
                created_transaction
            )
```

---

# 24. Mejor opción para modificar saldos

Leer una cuenta, modificarla en memoria y guardarla puede generar problemas de concurrencia.

Ejemplo:

```text
Saldo: 100.000

Petición A lee 100.000
Petición B lee 100.000

A descuenta 80.000
B descuenta 50.000
```

Ambas peticiones podrían aprobarse basándose en el mismo saldo inicial.

Para evitarlo, se recomienda realizar una actualización atómica condicional.

```python
from bson.decimal128 import Decimal128
from pymongo import ReturnDocument


async def withdraw_atomic(
    self,
    account_id: str,
    user_id: str,
    amount: Decimal,
) -> Account | None:
    document = await self.collection.find_one_and_update(
        {
            "_id": to_object_id(account_id),
            "user_id": to_object_id(user_id),
            "is_active": True,
            "balance": {
                "$gte": Decimal128(amount),
            },
        },
        {
            "$inc": {
                "balance": Decimal128(-amount),
            },
            "$set": {
                "updated_at": datetime.now(UTC),
            },
        },
        return_document=ReturnDocument.AFTER,
        session=self.session,
    )

    if document is None:
        return None

    return document_to_account(document)
```

La condición:

```python
"balance": {"$gte": amount}
```

y la modificación:

```python
"$inc": {"balance": -amount}
```

se ejecutan como una operación atómica sobre el documento.

---

# 25. Transferencias

Una transferencia entre cuentas involucra varios documentos:

- Cuenta de origen.
- Cuenta de destino.
- Movimiento de salida.
- Movimiento de entrada.

Debe ejecutarse dentro de una transacción.

```text
1. Iniciar sesión.
2. Iniciar transacción.
3. Validar cuenta de origen.
4. Validar cuenta de destino.
5. Descontar saldo de origen.
6. Incrementar saldo de destino.
7. Crear movimiento de salida.
8. Crear movimiento de entrada.
9. Confirmar transacción.
```

Los dos movimientos deben compartir un identificador:

```json
{
  "transfer_id": "01JQTRANSFER123"
}
```

Ejemplo:

```python
class TransferMoney:

    async def execute(
        self,
        command: TransferMoneyCommand,
    ) -> TransferResult:
        async with MongoUnitOfWork(self.mongo_client) as uow:
            accounts = MongoAccountRepository(
                self.database,
                session=uow.session,
            )

            transactions = MongoTransactionRepository(
                self.database,
                session=uow.session,
            )

            source = await accounts.get_by_id(
                command.source_account_id
            )

            target = await accounts.get_by_id(
                command.target_account_id
            )

            if source is None:
                raise AccountNotFoundError(
                    command.source_account_id
                )

            if target is None:
                raise AccountNotFoundError(
                    command.target_account_id
                )

            if source.user_id != command.user_id:
                raise AccountAccessDeniedError()

            if target.user_id != command.user_id:
                raise AccountAccessDeniedError()

            if source.currency != target.currency:
                raise DifferentCurrencyTransferError()

            source.withdraw(command.amount)
            target.deposit(command.amount)

            transfer_id = self.id_generator.generate()

            outgoing = Transaction.create_transfer_out(
                transfer_id=transfer_id,
                account_id=source.id,
                amount=command.amount,
                currency=source.currency,
            )

            incoming = Transaction.create_transfer_in(
                transfer_id=transfer_id,
                account_id=target.id,
                amount=command.amount,
                currency=target.currency,
            )

            await accounts.update(source)
            await accounts.update(target)
            await transactions.add(outgoing)
            await transactions.add(incoming)

            await uow.commit()

            return TransferResult(
                transfer_id=transfer_id,
            )
```

---

# 26. Modelado documental

MongoDB permite:

- Embeber documentos.
- Referenciar documentos.

La decisión debe basarse en cómo se consultan y modifican los datos.

## Embeber cuando

- Los datos pertenecen al mismo agregado.
- Se leen casi siempre juntos.
- No crecen ilimitadamente.
- Se modifican como una sola unidad.

Ejemplo:

```json
{
  "_id": "...",
  "name": "Bancolombia",
  "settings": {
    "color": "#FFCC00",
    "icon": "bank",
    "include_in_total": true
  }
}
```

## Referenciar cuando

- Los datos tienen ciclo de vida independiente.
- Pueden crecer sin límite.
- Se consultan por separado.
- Son compartidos por múltiples documentos.

Ejemplo:

```json
{
  "_id": "...",
  "account_id": "...",
  "category_id": "...",
  "amount": "50000.00"
}
```

No se deben embeber todos los movimientos dentro de la cuenta:

```json
{
  "name": "Bancolombia",
  "transactions": ["... millones de movimientos ..."]
}
```

La colección crecería sin control y dificultaría consultas, paginación e índices.

---

# 27. Colecciones recomendadas

```text
users
account_types
accounts
categories
transactions
savings_goals
investments
```

---

# 28. Documento de usuario

```json
{
  "_id": "ObjectId",
  "email": "sebastian@example.com",
  "normalized_email": "sebastian@example.com",
  "password_hash": "...",
  "full_name": "Sebastián Mesa",
  "is_active": true,
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

# 29. Documento de tipo de cuenta

```json
{
  "_id": "ObjectId",
  "code": "BANK_ACCOUNT",
  "name": "Cuenta bancaria",
  "description": "Cuenta de ahorros o corriente",
  "allows_negative_balance": false,
  "is_system": true,
  "is_active": true,
  "created_at": "datetime"
}
```

---

# 30. Documento de cuenta

```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "account_type_id": "ObjectId",
  "name": "Bancolombia",
  "normalized_name": "bancolombia",
  "currency": "COP",
  "balance": "Decimal128",
  "credit_limit": null,
  "settings": {
    "include_in_total": true,
    "color": null,
    "icon": null
  },
  "is_active": true,
  "created_at": "datetime",
  "updated_at": "datetime",
  "schema_version": 1
}
```

---

# 31. Documento de categoría

```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId | null",
  "name": "Alimentación",
  "normalized_name": "alimentacion",
  "transaction_type": "expense",
  "is_system": false,
  "is_active": true,
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

Cuando `user_id` sea `null`, puede representar una categoría global del sistema.

---

# 32. Documento de movimiento

```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "account_id": "ObjectId",
  "category_id": "ObjectId | null",
  "transaction_type": "expense",
  "amount": "Decimal128",
  "currency": "COP",
  "description": "Almuerzo",
  "occurred_at": "datetime",
  "created_at": "datetime",
  "transfer_id": null,
  "reversal_of_id": null,
  "status": "confirmed",
  "schema_version": 1
}
```

---

# 33. Índices

MongoDB no crea automáticamente todos los índices necesarios para las consultas de la aplicación.

Sin índices apropiados, MongoDB puede tener que revisar todos los documentos de una colección. citeturn782399search6

```python
# app/shared/infrastructure/mongodb/indexes.py

from pymongo import ASCENDING, DESCENDING
from pymongo.asynchronous.database import AsyncDatabase


async def create_indexes(
    database: AsyncDatabase,
) -> None:
    await database.users.create_index(
        [("normalized_email", ASCENDING)],
        unique=True,
        name="uq_users_normalized_email",
    )

    await database.accounts.create_index(
        [
            ("user_id", ASCENDING),
            ("normalized_name", ASCENDING),
        ],
        unique=True,
        partialFilterExpression={
            "is_active": True,
        },
        name="uq_active_account_name_per_user",
    )

    await database.accounts.create_index(
        [
            ("user_id", ASCENDING),
            ("is_active", ASCENDING),
            ("created_at", DESCENDING),
        ],
        name="ix_accounts_user_active_created",
    )

    await database.transactions.create_index(
        [
            ("user_id", ASCENDING),
            ("occurred_at", DESCENDING),
        ],
        name="ix_transactions_user_occurred",
    )

    await database.transactions.create_index(
        [
            ("user_id", ASCENDING),
            ("account_id", ASCENDING),
            ("occurred_at", DESCENDING),
        ],
        name="ix_transactions_user_account_occurred",
    )

    await database.transactions.create_index(
        [
            ("user_id", ASCENDING),
            ("category_id", ASCENDING),
            ("occurred_at", DESCENDING),
        ],
        name="ix_transactions_user_category_occurred",
    )

    await database.transactions.create_index(
        [("transfer_id", ASCENDING)],
        sparse=True,
        name="ix_transactions_transfer_id",
    )
```

En índices compuestos, el orden de los campos es importante y determina qué prefijos del índice pueden aprovechar las consultas. citeturn782399search2

---

# 34. Diseñar índices desde consultas reales

No crear índices al azar.

Primero identificar consultas:

```text
Listar cuentas activas de un usuario.
Listar movimientos de un usuario por fecha.
Filtrar movimientos por cuenta.
Filtrar movimientos por categoría.
Consultar una transferencia.
Buscar usuario por email.
```

Después diseñar índices que coincidan con:

1. Filtros de igualdad.
2. Campos de ordenamiento.
3. Campos de rango.

Ejemplo:

```python
{
    "user_id": user_id,
    "account_id": account_id,
    "occurred_at": {
        "$gte": date_from,
        "$lte": date_to,
    },
}
```

Índice:

```python
[
    ("user_id", 1),
    ("account_id", 1),
    ("occurred_at", -1),
]
```

---

# 35. Schemas Pydantic

Los schemas de presentación representan contratos HTTP.

```python
# app/modules/accounts/presentation/schemas.py

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CreateAccountRequest(BaseModel):
    account_type_id: str
    name: str = Field(
        min_length=1,
        max_length=100,
    )
    currency: str = Field(
        default="COP",
        min_length=3,
        max_length=3,
    )
    initial_balance: Decimal = Field(
        default=Decimal("0.00"),
        ge=Decimal("0.00"),
        max_digits=18,
        decimal_places=2,
    )


class AccountResponse(BaseModel):
    id: str
    user_id: str
    account_type_id: str
    name: str
    currency: str
    balance: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

Pydantic valida el formato HTTP.

El dominio valida las reglas del negocio.

---

# 36. Dependencias de casos de uso

```python
# app/modules/accounts/presentation/dependencies.py

from typing import Annotated

from fastapi import Depends

from app.modules.accounts.application.use_cases.create_account import (
    CreateAccount,
)
from app.modules.accounts.infrastructure.repositories import (
    MongoAccountRepository,
)
from app.shared.infrastructure.mongodb.database import (
    MongoDatabaseDep,
)


def get_create_account_use_case(
    database: MongoDatabaseDep,
) -> CreateAccount:
    repository = MongoAccountRepository(database)

    return CreateAccount(
        account_repository=repository,
    )


CreateAccountDep = Annotated[
    CreateAccount,
    Depends(get_create_account_use_case),
]
```

---

# 37. Router

```python
# app/modules/accounts/presentation/router.py

from fastapi import APIRouter, status

from app.modules.accounts.application.dto import (
    CreateAccountCommand,
)
from app.modules.accounts.presentation.dependencies import (
    CreateAccountDep,
)
from app.modules.accounts.presentation.schemas import (
    AccountResponse,
    CreateAccountRequest,
)
from app.modules.users.presentation.dependencies import (
    CurrentUserDep,
)


router = APIRouter(
    prefix="/accounts",
    tags=["Accounts"],
)


@router.post(
    "",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_account(
    request: CreateAccountRequest,
    current_user: CurrentUserDep,
    use_case: CreateAccountDep,
) -> AccountResponse:
    command = CreateAccountCommand(
        user_id=current_user.id,
        account_type_id=request.account_type_id,
        name=request.name,
        currency=request.currency,
        initial_balance=request.initial_balance,
    )

    result = await use_case.execute(command)

    return AccountResponse.model_validate(result)
```

El router solamente debe:

1. Recibir la petición.
2. Obtener dependencias.
3. Construir el comando.
4. Ejecutar el caso de uso.
5. Construir la respuesta.

---

# 38. Excepciones de dominio

```python
# app/modules/accounts/domain/exceptions.py


class AccountDomainError(Exception):
    pass


class AccountNotFoundError(AccountDomainError):

    def __init__(self, account_id: str) -> None:
        self.account_id = account_id
        super().__init__(
            f"No se encontró la cuenta {account_id}."
        )


class AccountAccessDeniedError(AccountDomainError):

    def __init__(self) -> None:
        super().__init__(
            "El usuario no tiene acceso a esta cuenta."
        )


class InsufficientBalanceError(AccountDomainError):

    def __init__(self) -> None:
        super().__init__(
            "La cuenta no tiene saldo suficiente."
        )


class InvalidInitialBalanceError(AccountDomainError):

    def __init__(self) -> None:
        super().__init__(
            "El saldo inicial no puede ser negativo."
        )


class AccountNameAlreadyExistsError(AccountDomainError):

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(
            f"Ya existe una cuenta activa con el nombre '{name}'."
        )
```

---

# 39. Conversión de errores a HTTP

```python
# app/core/exceptions.py

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.modules.accounts.domain.exceptions import (
    AccountAccessDeniedError,
    AccountNameAlreadyExistsError,
    AccountNotFoundError,
    InsufficientBalanceError,
)


def register_exception_handlers(
    app: FastAPI,
) -> None:

    @app.exception_handler(AccountNotFoundError)
    async def account_not_found_handler(
        request: Request,
        exc: AccountNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "code": "account_not_found",
                "message": str(exc),
            },
        )

    @app.exception_handler(AccountAccessDeniedError)
    async def account_access_denied_handler(
        request: Request,
        exc: AccountAccessDeniedError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "code": "account_access_denied",
                "message": str(exc),
            },
        )

    @app.exception_handler(AccountNameAlreadyExistsError)
    async def account_name_exists_handler(
        request: Request,
        exc: AccountNameAlreadyExistsError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "code": "account_name_already_exists",
                "message": str(exc),
            },
        )

    @app.exception_handler(InsufficientBalanceError)
    async def insufficient_balance_handler(
        request: Request,
        exc: InsufficientBalanceError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "code": "insufficient_balance",
                "message": str(exc),
            },
        )
```

El dominio no conoce códigos HTTP.

---

# 40. Autenticación y autorización

La autenticación determina:

```text
¿Quién es el usuario?
```

La autorización determina:

```text
¿Puede este usuario realizar esta acción?
```

Nunca confiar en un `user_id` enviado en el cuerpo.

Incorrecto:

```json
{
  "user_id": "otro-usuario",
  "account_id": "...",
  "amount": "50000.00"
}
```

Correcto:

```python
command = RegisterExpenseCommand(
    user_id=current_user.id,
    account_id=request.account_id,
    amount=request.amount,
)
```

Y dentro del caso de uso:

```python
if account.user_id != command.user_id:
    raise AccountAccessDeniedError()
```

---

# 41. Paginación

No utilizar solamente `skip` para volúmenes muy grandes.

Una paginación inicial puede usar:

```python
cursor = (
    collection.find(filters)
    .sort("occurred_at", -1)
    .skip(offset)
    .limit(page_size)
)
```

Para colecciones grandes se recomienda paginación por cursor:

```python
filters = {
    "user_id": user_id,
    "_id": {
        "$lt": last_id,
    },
}
```

Respuesta:

```python
class TransactionPageResponse(BaseModel):
    items: list[TransactionResponse]
    next_cursor: str | None
    has_more: bool
```

---

# 42. Migraciones en MongoDB

MongoDB no utiliza Alembic.

Aunque MongoDB tenga un esquema flexible, los documentos deben evolucionar de forma controlada.

Agregar a cada documento:

```json
{
  "schema_version": 1
}
```

Ejemplo de migración:

```python
# scripts/migrations/v002_add_currency.py

from pymongo import AsyncMongoClient


async def migrate(database) -> None:
    await database.accounts.update_many(
        {
            "schema_version": 1,
            "currency": {
                "$exists": False,
            },
        },
        {
            "$set": {
                "currency": "COP",
                "schema_version": 2,
            },
        },
    )
```

Buenas prácticas:

- Las migraciones deben ser idempotentes.
- Deben poder reanudarse.
- Deben trabajar por lotes.
- Deben registrar progreso.
- Deben probarse con una copia de datos.
- No deben asumir que todos los documentos tienen la misma estructura.
- Deben conservar respaldo antes de cambios destructivos.

---

# 43. Validación de esquema en MongoDB

MongoDB puede aplicar validación JSON Schema en las colecciones.

Ejemplo conceptual:

```javascript
db.createCollection("accounts", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: [
        "user_id",
        "account_type_id",
        "name",
        "currency",
        "balance",
        "is_active",
        "created_at",
      ],
      properties: {
        user_id: {
          bsonType: "objectId",
        },
        account_type_id: {
          bsonType: "objectId",
        },
        name: {
          bsonType: "string",
          minLength: 1,
          maxLength: 100,
        },
        currency: {
          bsonType: "string",
          minLength: 3,
          maxLength: 3,
        },
        balance: {
          bsonType: "decimal",
        },
        is_active: {
          bsonType: "bool",
        },
      },
    },
  },
});
```

La validación debe existir en varios niveles:

```text
Pydantic → formato HTTP
Dominio → reglas del negocio
MongoDB → integridad estructural
Índices → unicidad y rendimiento
```

---

# 44. Pruebas unitarias

## Entidad

```python
from decimal import Decimal

import pytest

from app.modules.accounts.domain.entities import Account
from app.modules.accounts.domain.exceptions import (
    InsufficientBalanceError,
)


def test_withdraw_reduces_balance() -> None:
    account = Account.create(
        user_id="user-1",
        account_type_id="type-1",
        name="Efectivo",
        currency="COP",
        initial_balance=Decimal("100000.00"),
    )

    account.withdraw(Decimal("25000.00"))

    assert account.balance == Decimal("75000.00")


def test_withdraw_rejects_insufficient_balance() -> None:
    account = Account.create(
        user_id="user-1",
        account_type_id="type-1",
        name="Efectivo",
        currency="COP",
        initial_balance=Decimal("10000.00"),
    )

    with pytest.raises(InsufficientBalanceError):
        account.withdraw(Decimal("15000.00"))
```

Estas pruebas no necesitan:

- FastAPI.
- MongoDB.
- PyMongo.
- Docker.
- HTTP.

---

# 45. Repositorio falso

```python
class FakeAccountRepository:

    def __init__(self) -> None:
        self.accounts: dict[str, Account] = {}
        self.next_id = 1

    async def add(
        self,
        account: Account,
    ) -> Account:
        account.id = str(self.next_id)
        self.next_id += 1

        self.accounts[account.id] = account
        return account

    async def get_by_id(
        self,
        account_id: str,
    ) -> Account | None:
        return self.accounts.get(account_id)

    async def list_by_user(
        self,
        user_id: str,
    ) -> list[Account]:
        return [
            account
            for account in self.accounts.values()
            if account.user_id == user_id
        ]

    async def update(
        self,
        account: Account,
    ) -> None:
        if account.id is None:
            raise ValueError(
                "La cuenta no tiene identificador."
            )

        self.accounts[account.id] = account

    async def exists_name_for_user(
        self,
        user_id: str,
        name: str,
    ) -> bool:
        normalized_name = name.strip().lower()

        return any(
            account.user_id == user_id
            and account.name.strip().lower() == normalized_name
            and account.is_active
            for account in self.accounts.values()
        )
```

---

# 46. Prueba del caso de uso

```python
from decimal import Decimal

import pytest


@pytest.mark.asyncio
async def test_create_account() -> None:
    repository = FakeAccountRepository()

    use_case = CreateAccount(repository)

    result = await use_case.execute(
        CreateAccountCommand(
            user_id="user-1",
            account_type_id="type-1",
            name="Efectivo",
            currency="COP",
            initial_balance=Decimal("50000.00"),
        )
    )

    assert result.id == "1"
    assert result.name == "Efectivo"
    assert result.balance == Decimal("50000.00")
```

---

# 47. Pruebas de integración

Las pruebas de repositorios deben usar MongoDB real.

Deben verificar:

- Inserciones.
- Actualizaciones.
- `Decimal128`.
- Conversión de `ObjectId`.
- Índices únicos.
- Filtros.
- Ordenamiento.
- Transacciones.
- Rollback.
- Concurrencia.

Evitar depender exclusivamente de mocks de MongoDB, porque pueden comportarse diferente al servidor real.

---

# 48. Pruebas de API

```python
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.mark.asyncio
async def test_create_account_endpoint() -> None:
    app = create_app()

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/accounts",
            headers={
                "Authorization": "Bearer test-token",
            },
            json={
                "account_type_id": "507f1f77bcf86cd799439011",
                "name": "Efectivo",
                "currency": "COP",
                "initial_balance": "50000.00",
            },
        )

    assert response.status_code == 201
    assert response.json()["name"] == "Efectivo"
```

---

# 49. Movimientos financieros inmutables

No se recomienda editar o eliminar movimientos financieros confirmados.

En lugar de modificar un gasto:

- Crear un movimiento de reversión.
- Referenciar el movimiento original.
- Registrar motivo.
- Registrar fecha.
- Registrar usuario responsable.

Ejemplo:

```json
{
  "transaction_type": "reversal",
  "reversal_of_id": "ObjectId",
  "amount": "Decimal128",
  "reason": "Movimiento duplicado"
}
```

Esto mantiene trazabilidad.

---

# 50. Saldo almacenado y libro mayor

Existen dos estrategias.

## Saldo almacenado

La cuenta contiene:

```json
{
  "balance": "Decimal128"
}
```

Ventajas:

- Consulta rápida.
- Fácil mostrar totales.

Riesgos:

- Puede desincronizarse de los movimientos.
- Requiere transacciones y controles de concurrencia.

## Saldo calculado

El saldo se obtiene sumando movimientos.

Ventajas:

- Los movimientos son la fuente de verdad.
- Mayor trazabilidad.

Riesgos:

- Consultas más costosas.
- Requiere agregaciones o proyecciones.

Para la primera versión:

> Mantener saldo en la cuenta y movimientos como historial, actualizando ambos dentro de la misma transacción.

También se recomienda crear un proceso de reconciliación:

```text
Saldo almacenado
vs.
Suma de movimientos
```

---

# 51. Agregaciones

MongoDB permite realizar reportes con aggregation pipelines.

Ejemplo de gastos por categoría:

```python
pipeline = [
    {
        "$match": {
            "user_id": to_object_id(user_id),
            "transaction_type": "expense",
            "occurred_at": {
                "$gte": date_from,
                "$lt": date_to,
            },
        }
    },
    {
        "$group": {
            "_id": "$category_id",
            "total": {
                "$sum": "$amount",
            },
            "count": {
                "$sum": 1,
            },
        }
    },
    {
        "$sort": {
            "total": -1,
        }
    },
]
```

Estas consultas pueden residir en repositorios de lectura o query services.

No siempre es necesario reconstruir entidades completas para reportes.

---

# 52. Separación ligera de comandos y consultas

Comandos:

```text
CreateAccount
RegisterIncome
RegisterExpense
TransferMoney
CloseAccount
ReverseTransaction
```

Consultas:

```text
GetAccount
ListAccounts
ListTransactions
GetMonthlySummary
GetExpensesByCategory
GetNetWorth
```

Los comandos modifican el estado.

Las consultas leen datos y pueden utilizar pipelines optimizados.

No es necesario implementar CQRS completo al comenzar.

---

# 53. Errores comunes

## Usar documentos MongoDB como entidades

Incorrecto:

```python
account = await collection.find_one(...)
account["balance"] -= amount
```

Esto mezcla persistencia y dominio.

## Usar ObjectId en todo el proyecto

Incorrecto:

```python
class Account:
    id: ObjectId
```

Acopla el dominio a MongoDB.

## Lógica en routers

Incorrecto:

```python
@router.post("/expenses")
async def expense(request):
    await accounts.update_one(...)
    await transactions.insert_one(...)
```

## No usar transacciones para transferencias

Puede dejar una cuenta modificada y la otra sin modificar.

## Usar float para dinero

```python
amount = 0.1 + 0.2
```

## No crear índices

Las consultas terminan revisando la colección completa.

## Embeber listas sin límite

No guardar todos los movimientos dentro del documento de cuenta.

## Crear un cliente por petición

El cliente debe reutilizarse.

## Confiar en user_id del cliente

El usuario debe obtenerse del token.

## Usar Motor en un proyecto nuevo

Para proyectos nuevos, utilizar PyMongo Async.

---

# 54. Convenciones

Clases:

```text
CreateAccount
RegisterExpense
AccountRepository
MongoAccountRepository
CreateAccountCommand
AccountResult
AccountResponse
```

Archivos:

```text
create_account.py
register_expense.py
entities.py
repositories.py
documents.py
mappers.py
schemas.py
dependencies.py
```

Colecciones:

```text
users
account_types
accounts
categories
transactions
```

Campos:

```text
snake_case
```

No usar nombres ambiguos como:

```text
Manager
Helper
Common
Utils
Processor
```

salvo que tengan una responsabilidad verdaderamente clara.

---

# 55. Dependencias sugeridas

```toml
[project]
dependencies = [
    "fastapi",
    "uvicorn[standard]",
    "pymongo",
    "pydantic-settings",
    "python-jose[cryptography]",
    "passlib[bcrypt]",
]

[project.optional-dependencies]
dev = [
    "pytest",
    "pytest-asyncio",
    "pytest-cov",
    "httpx",
    "ruff",
    "mypy",
]
```

---

# 56. Herramientas de calidad

```bash
ruff check .
ruff format .
mypy app
pytest
pytest --cov=app --cov-report=term-missing
```

Lineamientos:

- Usar tipado.
- Evitar `Any` innecesario.
- Evitar funciones demasiado grandes.
- Usar excepciones específicas.
- No usar `except Exception: pass`.
- No usar `print()` como logging.
- Mantener imports absolutos.
- Evitar dependencias circulares.

---

# 57. Plan de implementación

## Fase 1: infraestructura

- Configurar proyecto.
- Configurar variables de entorno.
- Crear cliente MongoDB.
- Configurar replica set local.
- Configurar lifespan.
- Crear endpoint `/health`.
- Crear sistema de índices.

## Fase 2: usuarios

- Entidad `User`.
- Repositorio.
- Registro.
- Hash de contraseña.
- Login.
- JWT.
- Usuario actual.

## Fase 3: tipos de cuenta

- Crear colección `account_types`.
- Crear datos iniciales.
- Crear índices.

Tipos iniciales:

```text
CASH
BANK_ACCOUNT
DIGITAL_WALLET
CREDIT_CARD
SAVINGS
INVESTMENT
```

## Fase 4: cuentas

- Crear.
- Listar.
- Consultar.
- Renombrar.
- Cerrar.
- Saldo inicial.

## Fase 5: categorías

- Categorías de ingresos.
- Categorías de gastos.
- Categorías del sistema.
- Categorías personalizadas.

## Fase 6: movimientos

- Registrar ingreso.
- Registrar gasto.
- Consultar movimientos.
- Filtrar.
- Paginar.
- Revertir.

## Fase 7: transferencias

- Transacción multidocumento.
- Dos movimientos relacionados.
- Modificación atómica de saldos.
- Pruebas de rollback.

## Fase 8: reportes

- Resumen mensual.
- Ingresos frente a gastos.
- Gastos por categoría.
- Evolución del saldo.
- Patrimonio total.

---

# 58. Flujo de una petición

```text
Cliente HTTP
    ↓
FastAPI Router
    ↓
Pydantic Request
    ↓
Command / Query
    ↓
Caso de uso
    ↓
Entidad de dominio
    ↓
Interfaz de repositorio
    ↓
Repositorio MongoDB
    ↓
Mapper
    ↓
Documento BSON
    ↓
MongoDB
```

Respuesta:

```text
MongoDB
    ↓
Documento BSON
    ↓
Mapper
    ↓
Entidad o DTO
    ↓
Caso de uso
    ↓
Response Schema
    ↓
JSON
```

---

# 59. Checklist de arquitectura

## Dominio

- [ ] No importa FastAPI.
- [ ] No importa PyMongo.
- [ ] No utiliza `ObjectId`.
- [ ] No conoce colecciones.
- [ ] Usa `Decimal` para dinero.
- [ ] Protege invariantes.
- [ ] Define excepciones del negocio.
- [ ] No ejecuta consultas.

## Aplicación

- [ ] Cada operación tiene un caso de uso.
- [ ] Los casos de uso dependen de interfaces.
- [ ] No usa `HTTPException`.
- [ ] No crea clientes MongoDB.
- [ ] No construye consultas BSON.
- [ ] Controla transacciones cuando corresponde.
- [ ] Verifica autorización.
- [ ] Devuelve entidades o DTO.

## Infraestructura

- [ ] Convierte `str` y `ObjectId`.
- [ ] Convierte `Decimal` y `Decimal128`.
- [ ] Implementa repositorios.
- [ ] No contiene reglas del negocio.
- [ ] Utiliza sesiones correctamente.
- [ ] Tiene índices para consultas frecuentes.
- [ ] No abre clientes por petición.
- [ ] Tiene estrategia de migración.

## Presentación

- [ ] El router es pequeño.
- [ ] Usa schemas Pydantic.
- [ ] Obtiene el usuario desde autenticación.
- [ ] No confía en `user_id` del cliente.
- [ ] Traduce excepciones a HTTP.
- [ ] Define `response_model`.
- [ ] No contiene consultas MongoDB.

## Finanzas

- [ ] No se utiliza `float`.
- [ ] Los movimientos son trazables.
- [ ] Las transferencias son atómicas.
- [ ] Existe control de concurrencia.
- [ ] Los movimientos confirmados no se editan libremente.
- [ ] Las reversas referencian el movimiento original.
- [ ] Existe reconciliación de saldos.

## Pruebas

- [ ] Las entidades tienen pruebas unitarias.
- [ ] Los casos de uso usan repositorios falsos.
- [ ] Los repositorios tienen pruebas con MongoDB real.
- [ ] Las transacciones prueban rollback.
- [ ] Los índices únicos tienen pruebas.
- [ ] Los endpoints tienen pruebas.
- [ ] Se prueban operaciones concurrentes críticas.

---

# 60. Regla final

Antes de aprobar una funcionalidad, responder:

1. ¿El caso de uso puede ejecutarse sin FastAPI?
2. ¿La regla puede probarse sin MongoDB?
3. ¿El dominio conoce `ObjectId`?
4. ¿El caso de uso conoce PyMongo?
5. ¿El router contiene reglas del negocio?
6. ¿Las operaciones financieras son atómicas?
7. ¿El usuario autenticado es validado contra el recurso?
8. ¿Los campos consultados tienen índices?
9. ¿El dinero se almacena sin utilizar `float`?
10. ¿Los movimientos conservan trazabilidad?
11. ¿Existe una estrategia para evolucionar documentos?
12. ¿Cada clase tiene una responsabilidad clara?

La arquitectura está bien separada cuando:

```text
Los casos de uso pueden probarse sin FastAPI.
Las reglas pueden probarse sin MongoDB.
El dominio no conoce detalles de infraestructura.
```

---

# 61. Recomendación específica para este proyecto

La arquitectura inicial debería seguir este flujo:

```text
Router FastAPI
      ↓
Caso de uso
      ↓
Repositorio abstracto
      ↓
Repositorio PyMongo
      ↓
MongoDB
```

Para operaciones simples sobre un único documento:

```text
Operación atómica MongoDB
```

Para gastos, ingresos o transferencias que modifican saldos y crean movimientos:

```text
Sesión MongoDB
      ↓
Transacción
      ↓
Actualizar cuenta
      ↓
Crear movimiento
      ↓
Commit
```

Para reportes:

```text
Query Service
      ↓
Aggregation Pipeline
      ↓
DTO de lectura
```

Esta combinación mantiene Clean Architecture sin introducir complejidad innecesaria y permite que el sistema crezca hacia ahorros, inversiones, presupuestos y reportes financieros.
