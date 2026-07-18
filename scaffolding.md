# Scaffolding del proyecto

Este documento describe la estructura inicial del backend de control de gastos. El scaffolding define los límites de Clean Architecture, pero todavía no implementa lógica de negocio, conexiones, endpoints ni configuración ejecutable.

## Vista general

```text
gastos-back/
├── app/
│   ├── api/v1/
│   ├── core/
│   ├── shared/
│   │   ├── domain/
│   │   ├── application/
│   │   └── infrastructure/mongodb/
│   └── modules/
│       ├── users/
│       ├── account_types/
│       ├── accounts/
│       ├── categories/
│       └── transactions/
├── scripts/
│   └── migrations/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── .env.example
├── .gitignore
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── README.md
├── guide.md
└── scaffolding.md
```

Los archivos `__init__.py` identifican paquetes de Python. Permanecen vacíos hasta que exista una razón concreta para exponer símbolos desde un paquete.

## `app/`

Contiene todo el código fuente de la aplicación.

- `main.py`: punto de entrada futuro de FastAPI. Aquí se creará la aplicación, se configurará el ciclo de vida y se registrarán routers y manejadores de errores.
- `api/`: composición de la interfaz HTTP. No contiene reglas de negocio.
- `core/`: configuración transversal propia de la aplicación.
- `shared/`: abstracciones y adaptadores reutilizables por varios módulos.
- `modules/`: módulos funcionales del negocio, separados internamente por capas.

## `app/api/v1/`

Agrupa la versión 1 de la API.

- `router.py`: router principal que incorporará los routers HTTP de cada módulo.

Mantener esta carpeta separada permite introducir versiones futuras sin mezclar contratos HTTP incompatibles.

## `app/core/`

Contiene aspectos globales que no pertenecen a un módulo de negocio específico.

- `config.py`: carga y validación futura de variables de entorno.
- `exceptions.py`: registro futuro de la traducción de excepciones de dominio o aplicación a respuestas HTTP.
- `logging.py`: configuración centralizada de logs.
- `security.py`: utilidades y configuración técnica de seguridad compartida, sin reglas propias del módulo de usuarios.

## `app/shared/`

Reúne conceptos que realmente son compartidos. No debe convertirse en un lugar genérico para código sin dueño.

### `shared/domain/`

- `entity.py`: bases mínimas para entidades, únicamente si varios módulos llegan a necesitarlas.
- `exceptions.py`: excepciones genuinamente transversales.
- `value_objects.py`: objetos de valor compartidos, por ejemplo dinero, si su reutilización lo justifica.

Esta capa no puede depender de FastAPI, Pydantic, PyMongo, BSON ni otros detalles externos.

### `shared/application/`

- `pagination.py`: contratos de paginación reutilizables por consultas.
- `unit_of_work.py`: puerto abstracto para delimitar operaciones transaccionales.

### `shared/infrastructure/mongodb/`

- `client.py`: creación y cierre del cliente asíncrono reutilizable.
- `database.py`: acceso a la base de datos y futura integración con inyección de dependencias.
- `indexes.py`: creación coordinada de índices.
- `object_id.py`: conversión segura entre identificadores `str` y `ObjectId`.
- `unit_of_work.py`: implementación de sesiones y transacciones de MongoDB.

Todo conocimiento de PyMongo, BSON, `ObjectId` y `Decimal128` debe permanecer en infraestructura.

## Organización interna de los módulos

Cada carpeta de `app/modules/` representa una capacidad funcional y repite cuatro capas:

```text
module/
├── domain/
├── application/
│   └── use_cases/
├── infrastructure/
└── presentation/
```

### `domain/`

Contiene las reglas estables del negocio:

- `entities.py`: entidades y sus invariantes.
- `value_objects.py`: objetos de valor propios del módulo, cuando sean necesarios.
- `enums.py`: enumeraciones de negocio, cuando apliquen.
- `exceptions.py`: errores específicos del dominio.
- `repositories.py`: interfaces o protocolos de persistencia requeridos por los casos de uso.

No conoce HTTP, MongoDB ni Pydantic.

### `application/`

Coordina las operaciones del sistema:

- `dto.py`: comandos, consultas y resultados independientes de HTTP.
- `ports.py`: contratos con servicios externos que necesita el módulo.
- `use_cases/`: un archivo por operación o caso de uso.

Esta capa depende del dominio, pero no de FastAPI ni de implementaciones PyMongo.

### `infrastructure/`

Implementa los detalles técnicos:

- `documents.py`: forma tipada de los documentos persistidos.
- `mappers.py`: conversión entre documentos BSON y entidades/DTO.
- `repositories.py`: implementación MongoDB de los repositorios abstractos.
- Adaptadores específicos adicionales, como hash de contraseñas o emisión de tokens, viven aquí cuando pertenecen al módulo.

### `presentation/`

Expone los casos de uso mediante FastAPI:

- `schemas.py`: contratos de entrada y salida con Pydantic.
- `dependencies.py`: composición e inyección de repositorios, adaptadores y casos de uso.
- `router.py`: definición de rutas HTTP. Debe limitarse a recibir, convertir, ejecutar y responder.

## Módulos iniciales

### `users/`

Responsable del ciclo de vida de usuarios y autenticación.

- Casos de uso iniciales: `create_user.py`, `authenticate_user.py` y `get_user.py`.
- `password_hasher.py`: adaptación técnica para generar y verificar hashes.
- `token_service.py`: adaptación técnica para crear y validar tokens.

### `account_types/`

Administra tipos de cuenta globales y personalizados por usuario, como
efectivo, cuenta bancaria, billetera digital o tipos definidos por el usuario.

- Casos de uso iniciales: `get_account_type.py` y `list_account_types.py`.
- Normalmente sus datos iniciales serán creados mediante un script de seed.

### `accounts/`

Administra las cuentas financieras y su saldo almacenado.

- Casos de uso iniciales: crear, consultar, listar, renombrar y cerrar cuentas.
- Las actualizaciones críticas de saldo deberán diseñarse como operaciones atómicas.

### `categories/`

Administra categorías globales y categorías personalizadas por usuario para
ingresos y gastos. Un `user_id` nulo identifica una categoría global.

- Casos de uso iniciales: crear, consultar, listar, actualizar y desactivar categorías.

### `transactions/`

Administra ingresos, gastos, transferencias y reversiones.

- Casos de uso iniciales: registrar ingreso, registrar gasto, listar movimientos, transferir dinero y revertir un movimiento.
- Las operaciones que modifican saldos y crean movimientos deberán usar una transacción MongoDB.

## `scripts/`

Contiene procesos administrativos ejecutados fuera del servidor web.

- `create_indexes.py`: ejecución explícita de la creación de índices.
- `seed_account_types.py`: carga idempotente del catálogo inicial de tipos de cuenta.
- `seed_categories.py`: carga idempotente de categorías globales y, cuando se
  indique un usuario inicial explícito, de categorías privadas para ese
  usuario.
- `migrations/`: migraciones versionadas para evolucionar documentos MongoDB. El archivo `.gitkeep` conserva la carpeta mientras aún no hay migraciones.

Los scripts deben reutilizar configuración e infraestructura de la aplicación, y ser idempotentes cuando corresponda.

## `tests/`

Separa pruebas por alcance.

### `tests/unit/`

- `domain/`: pruebas rápidas de entidades, objetos de valor e invariantes sin MongoDB ni FastAPI.
- `application/`: pruebas de casos de uso con repositorios y puertos falsos.

### `tests/integration/`

- `repositories/`: verifica implementaciones PyMongo contra una instancia real de MongoDB, incluyendo mapeos, índices y concurrencia.
- `transactions/`: verifica commit y rollback de operaciones multidocumento.

### `tests/e2e/api/`

Prueba los contratos HTTP y el flujo completo de la API mediante un cliente ASGI y dependencias de prueba.

- `conftest.py`: fixtures compartidas. Solo deben colocarse aquí las que tengan alcance global para las pruebas.

## Archivos de la raíz

- `.env.example`: catálogo sin secretos de las variables requeridas.
- `.gitignore`: exclusiones de Python, entornos locales, cachés, cobertura y secretos.
- `docker-compose.yml`: definición futura de los servicios necesarios para
  ejecutar el backend localmente. Atlas es la base de datos principal y el
  desarrollo local no presupone un replica set de MongoDB.
- `pyproject.toml`: metadatos, dependencias y configuración de herramientas de calidad.
- `requirements.txt`: dependencias necesarias para ejecutar la aplicación.
- `requirements-dev.txt`: dependencias de ejecución más pytest, cobertura,
  cliente de pruebas, Ruff y mypy para desarrollo y control de calidad.
- `README.md`: entrada breve para instalar, configurar y ejecutar el proyecto.
- `guide.md`: guía arquitectónica de referencia entregada para el proyecto.
- `scaffolding.md`: este mapa de la estructura inicial.

## Reglas de dependencia

```text
presentation -> application -> domain
infrastructure -------------> domain/application
```

- Dominio no importa capas externas.
- Aplicación trabaja con puertos e interfaces.
- Infraestructura implementa esos contratos.
- Presentación compone dependencias y traduce HTTP.
- Un módulo no debe acceder directamente a las colecciones internas de otro módulo.

## Estado del scaffolding

Los archivos creados son marcadores de posición intencionales. La implementación debe incorporarse por fases, comenzando por configuración, conexión MongoDB, ciclo de vida, health check e índices. Crear el esqueleto completo desde el inicio no implica que todos los módulos deban implementarse simultáneamente.
