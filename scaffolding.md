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
│       ├── transactions/
│       ├── exchange_rates/
│       └── reference_data/
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

- Casos de uso implementados: registro, login, consulta y actualización del
  usuario actual, desactivación lógica, rotación de refresh token y logout.
- El perfil admite nombre personalizable, país y divisa favorita sin mezclar
  esos datos con las credenciales de autenticación.
- `password_hasher.py`: adaptación Passlib con Argon2 para generar y verificar
  hashes de contraseña.
- `token_service.py`: emisión y validación de JWT, además del hash SHA-256 de
  refresh tokens.
- `repositories.py`: persistencia PyMongo de usuarios y sesiones de refresh.
- Los refresh tokens usan rotación, revocación por familia e índice TTL.

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

- Casos de uso implementados: registrar ingreso, registrar gasto, listar y
  consultar movimientos, transferir dinero, generar flujo de caja y revertir
  un movimiento.
- Las transferencias crean asientos `transfer_out` y `transfer_in` con un
  `transfer_id` compartido y actualizan ambos saldos atómicamente.
- Las transferencias multimoneda aceptan tasa `market` mediante el puerto de
  `exchange_rates` o una tasa `custom` proporcionada por el usuario.
- Los metadatos financieros se persisten como `Decimal128`; la migración
  `v2_add_transfer_metadata.py` actualiza el validador y crea el índice por
  `transfer_id`.

### `exchange_rates/`

Integra proveedores externos de tasas sin acoplar los casos de uso a HTTP.

- `domain/exceptions.py`: fallos estables de moneda no soportada, monto
  inválido y proveedor no disponible.
- `application/dto.py`: consultas, comandos, cotizaciones y resultados de
  conversión con `Decimal`.
- `application/ports.py`: contrato `ExchangeRateProvider` implementado por
  infraestructura.
- `application/use_cases/`: consulta la tasa más reciente y convierte montos.
- `infrastructure/exchangerate_api.py`: cliente de ExchangeRate-API con token
  bearer, validación de respuestas, reintentos acotados y caché en memoria.
- `presentation/`: dependencias, esquemas y endpoints autenticados bajo
  `/api/v1/exchange-rates`.

Este módulo no persiste documentos ni requiere índices o migraciones. Las
tasas son informativas y se consultan al proveedor configurado.

### `reference_data/`

Gestiona catálogos globales de países, territorios, divisas fiat y
criptomonedas principales.

- `domain/entities.py`: entidades `Country` y `CurrencyCatalogEntry` sin
  dependencias de MongoDB o FastAPI.
- `domain/enums.py`: distingue activos monetarios `fiat` y `crypto`.
- `application/use_cases/list_reference_data.py`: consultas mediante un
  puerto de repositorio.
- `infrastructure/`: documentos, mapeos BSON y repositorio PyMongo para las
  colecciones `countries` y `currencies`.
- `presentation/`: endpoints autenticados de sólo lectura
  `/api/v1/countries` y `/api/v1/currencies`.

## `scripts/`

Contiene procesos administrativos ejecutados fuera del servidor web.

- `create_indexes.py`: ejecución explícita de la creación de índices.
- `seed_user.py`: crea idempotentemente el usuario inicial definido mediante
  variables de entorno, usando el flujo real de registro y Argon2.
- `seed_data.py`: crea idempotentemente un conjunto completo de prueba con
  usuario configurado en CO/COP, catálogos globales y privados, cuenta
  favorita, saldo inicial y un historial de ingresos y gastos en COP.
- `data/reference_catalog.py`: dataset estático versionado con 250 países y
  territorios, sus divisas y diez criptomonedas principales.
- `seed_countries.py`: carga países, territorios y sus asociaciones
  monetarias.
- `seed_currencies.py`: carga divisas fiat y criptomonedas.
- `seed_reference_data.py`: ejecuta ambos seeds de referencia.
- `seed_account_types.py`: carga idempotente del catálogo inicial de tipos de cuenta.
- `seed_categories.py`: carga idempotente de categorías globales y, cuando se
  indique un usuario inicial explícito, de categorías privadas para ese
  usuario.
- `migrations/`: migraciones versionadas para evolucionar documentos MongoDB. El archivo `.gitkeep` conserva la carpeta mientras aún no hay migraciones.
- `migrations/v2_add_transfer_metadata.py`: aplica idempotentemente el
  validador de metadatos de transferencias y asegura sus índices.
- `migrations/v3_add_profile_reference_data.py`: incorpora preferencias de
  perfil, cuenta favorita, esquemas de catálogos e índices relacionados.
- `migrations/v4_add_user_name.py`: añade el nombre opcional a usuarios
  existentes y actualiza el validador MongoDB.

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
- `.python-version`: fija Python 3.11.5 para desarrollo y Render.
- `render.yaml`: Blueprint del Web Service, health check y variables de Render.
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

El módulo de usuarios, la configuración, la conexión MongoDB y el health check
ya tienen implementación. Los archivos aún vacíos de los demás módulos siguen
siendo marcadores de posición intencionales y deben incorporarse por fases.
