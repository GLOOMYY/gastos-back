# Gastos App Backend

Backend modular de Gastos App, diseñado con FastAPI, MongoDB Atlas y Clean
Architecture pragmática.

## Estado actual

El repositorio contiene el scaffolding inicial, las entidades financieras y
el flujo completo de autenticación. Están implementados registro, login,
tokens JWT de acceso y refresh, rotación, detección de reutilización, logout y
consulta del usuario actual.

La estructura completa está documentada en `scaffolding.md`, mientras que
`AGENTS.MD` contiene las reglas obligatorias de arquitectura y desarrollo.

## Requisitos

- Python 3.11.5.
- `pip`.
- Acceso a MongoDB Atlas para utilizar autenticación y persistencia.

Atlas es la base de datos principal. El desarrollo local no presupone una
instancia de MongoDB ni un replica set local.

## Dependencias

Para instalar únicamente las dependencias de ejecución:

```bash
python -m pip install -r requirements.txt
```

Para preparar un entorno de desarrollo:

```bash
python -m pip install -r requirements-dev.txt
```

Las dependencias de desarrollo incluyen pytest, pytest-asyncio, cobertura,
HTTPX, Ruff y mypy.

Las contraseñas se protegen con Passlib y Argon2. Los tokens de sesión se
firman como JWT y los refresh tokens se almacenan únicamente mediante su hash
SHA-256.

## Controles de calidad adoptados

```bash
ruff check .
ruff format --check .
mypy app
pytest
```

Estos comandos serán la puerta de validación cuando exista código funcional.

## Configuración

Los secretos y credenciales se proporcionarán mediante variables de entorno.
Nunca se debe crear ni versionar un archivo `.env` real; el contrato de
configuración se documentará exclusivamente en `.env.example`.

Crea tu archivo local a partir del ejemplo y completa sus valores:

```bash
cp .env.example .env
```

El health check puede ejecutarse sin credenciales. Para utilizar los endpoints
de autenticación deben completarse:

```dotenv
MONGODB_URI=mongodb+srv://...
MONGODB_DATABASE=gastos
JWT_SECRET_KEY=un-secreto-largo-aleatorio
```

`JWT_SECRET_KEY` debe tener al menos 32 caracteres, ser aleatorio y diferente
por entorno. No debe incluirse en logs, commits ni documentación compartida.

## Ejecución local

Después de instalar las dependencias y preparar `.env`, inicia el servidor:

```bash
uvicorn app.main:app --reload
```

El health check estará disponible en:

```text
GET http://127.0.0.1:8000/api/v1/health
```

Respuesta esperada:

```json
{
  "status": "ok"
}
```

Al iniciar con MongoDB configurado, la aplicación verifica la conexión, crea
con validación JSON Schema las colecciones de autenticación que aún no existan
y asegura sus índices. Los cambios posteriores de validadores deben realizarse
mediante migraciones versionadas.

## Autenticación

Endpoints disponibles:

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
GET  /api/v1/auth/me
```

Registro:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"user@example.com","password":"strong-password"}'
```

Login:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"user@example.com","password":"strong-password"}'
```

La respuesta contiene `access_token`, `refresh_token`, sus fechas de
expiración y `token_type`. El token de acceso se envía como bearer:

```bash
curl http://127.0.0.1:8000/api/v1/auth/me \
  -H 'Authorization: Bearer ACCESS_TOKEN'
```

Cada llamada a `/refresh` consume el refresh token recibido y entrega uno
nuevo. Reutilizar un token ya rotado revoca toda su familia. `/logout` revoca
el refresh token indicado y es idempotente.

Todas las respuestas de error siguen este contrato:

```json
{
  "code": "invalid_credentials",
  "message": "The email or password is incorrect.",
  "details": null,
  "request_id": "correlation-id"
}
```

## Persistencia de autenticación

- `users.normalized_email` tiene un índice único.
- Los documentos incluyen `schema_version`.
- Los refresh tokens crudos nunca se persisten.
- Los refresh tokens expiran mediante un índice TTL.
- La rotación consume el token anterior con una actualización atómica.
- Los tokens se agrupan en familias para detectar reutilización.

Las pruebas automatizadas utilizan repositorios falsos y no escriben en Atlas.
La integración contra una instancia real de MongoDB queda pendiente de un
entorno de pruebas aislado.

## Datos iniciales

`scripts/seed_account_types.py` y `scripts/seed_categories.py` podrán crear
recursos globales y recursos privados para un usuario explícitamente
identificado. Un recurso con `user_id` nulo será global; cualquier recurso con
usuario asignado pertenecerá exclusivamente a ese usuario.
