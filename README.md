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

Para crear el usuario inicial, completa también:

```dotenv
INITIAL_USER_EMAIL=user@example.com
INITIAL_USER_PASSWORD=una-contraseña-segura
```

Para consultar tasas y convertir monedas configura ExchangeRate-API:

```dotenv
EXCHANGE_RATE_PROVIDER=exchangerate_api
EXCHANGE_RATE_API_KEY=tu-clave-regenerada
```

La clave se envía al proveedor como token bearer y nunca forma parte de la
URL. Las respuestas de tasas se conservan temporalmente en memoria para
reducir el consumo de cuota.

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
GET  /api/v1/users/me
PATCH /api/v1/users/me
DELETE /api/v1/users/me
GET|POST /api/v1/account-types
GET|PUT|DELETE /api/v1/account-types/{id}
GET|POST /api/v1/categories
GET|PUT|DELETE /api/v1/categories/{id}
GET|POST /api/v1/accounts
GET|PUT|DELETE /api/v1/accounts/{id}
GET /api/v1/transactions
GET /api/v1/transactions/cash-flow
POST /api/v1/transactions/income
POST /api/v1/transactions/expense
GET /api/v1/transactions/{id}
POST /api/v1/transactions/{id}/reversal
GET /api/v1/exchange-rates/{source_currency}/{target_currency}
POST /api/v1/exchange-rates/convert
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

## CRUD del usuario autenticado

La creación se realiza mediante `/auth/register`. La lectura del usuario
actual está disponible en `/users/me` y se mantiene `/auth/me` por
compatibilidad.

El email y la contraseña pueden actualizarse juntos o por separado:

```bash
curl -X PATCH http://127.0.0.1:8000/api/v1/users/me \
  -H 'Authorization: Bearer ACCESS_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{"email":"new@example.com","password":"new-strong-password"}'
```

Cambiar la contraseña revoca todos los refresh tokens del usuario. Los access
tokens ya emitidos conservan su expiración normal.

La eliminación es lógica:

```bash
curl -X DELETE http://127.0.0.1:8000/api/v1/users/me \
  -H 'Authorization: Bearer ACCESS_TOKEN'
```

El documento y su historial se conservan, el usuario queda inactivo y todas
sus sesiones de refresh son revocadas. No existe listado global ni endpoints
para modificar otros usuarios porque el sistema solo tiene el rol `user`.

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

## Seed del usuario inicial

Con Atlas y las variables `INITIAL_USER_*` configuradas, ejecuta:

```bash
python -m scripts.seed_user
```

El seed utiliza el caso de uso real de registro, normaliza el email y genera
el hash Argon2. Es idempotente: si el email ya existe, termina correctamente
sin duplicarlo y sin modificar su contraseña. El script nunca muestra ni
registra la contraseña.

Después puedes iniciar sesión usando los valores configurados en
`INITIAL_USER_EMAIL` e `INITIAL_USER_PASSWORD`.

Para crear el conjunto completo de prueba —usuario, tipo de cuenta global,
categorías globales y privadas, cuenta, saldo inicial y 18 ingresos/gastos en
COP distribuidos durante 90 días— llena también las variables
`INITIAL_ACCOUNT_*` y ejecuta:

```bash
python -m scripts.seed_data
```

Este seed también es idempotente. Requiere MongoDB Atlas con soporte para
transacciones cuando el saldo inicial es distinto de cero. No registra
contraseñas, tokens ni URI de conexión en los logs.

El historial se identifica mediante notas internas `seed:history:v1:*`, por
lo que repetir el comando no duplica los movimientos ni vuelve a alterar el
saldo. La cuenta inicial debe estar configurada en `COP` para este seed.

El frontend puede obtener datos diarios o mensuales para una gráfica mediante
`GET /api/v1/transactions/cash-flow`. El rango predeterminado cubre 90 días y
el máximo permitido es de 366 días.

## Conversión de divisas

Los endpoints de divisas requieren access token. Para consultar una tasa:

```bash
curl http://127.0.0.1:8000/api/v1/exchange-rates/USD/COP \
  -H 'Authorization: Bearer ACCESS_TOKEN'
```

Para convertir un monto sin utilizar números de punto flotante:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/exchange-rates/convert \
  -H 'Authorization: Bearer ACCESS_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{"source_currency":"USD","target_currency":"COP","amount":"25.50"}'
```

La respuesta incluye la tasa, fecha de actualización y proveedor usados. El
resultado no se redondea automáticamente porque cada moneda tiene reglas
distintas de unidades menores; el frontend debe aplicar su formato de moneda.

## Datos iniciales

`scripts/seed_data.py` crea los recursos globales y privados iniciales. Un
recurso con `user_id` nulo es global; cualquier recurso con usuario asignado
pertenece exclusivamente a ese usuario.

## Despliegue en Render

El repositorio incluye [`render.yaml`](render.yaml) para crear un Web Service
con el runtime nativo de Python de Render. La configuración fija Python
3.11.5, instala `requirements.txt`, inicia Uvicorn usando el puerto asignado
por Render y comprueba `/api/v1/health` antes de publicar una versión.

### Crear el servicio

1. Publica este repositorio en GitHub, GitLab o Bitbucket.
2. En Render selecciona **New > Blueprint** y conecta el repositorio.
3. Render detectará `render.yaml` en la raíz.
4. Proporciona los valores solicitados para `MONGODB_URI`,
   `MONGODB_DATABASE`, `CORS_ALLOWED_ORIGINS` y
   `EXCHANGE_RATE_API_KEY`.
5. Confirma la creación del servicio `gastos-back`.

`JWT_SECRET_KEY` es generado por Render y no debe copiarse al repositorio.
Las variables obligatorias quedan así:

| Variable | Valor o propósito |
|---|---|
| `MONGODB_URI` | URI secreta de MongoDB Atlas |
| `MONGODB_DATABASE` | Base de datos de producción |
| `JWT_SECRET_KEY` | Generada automáticamente por Render |
| `CORS_ALLOWED_ORIGINS` | URL exacta del frontend, sin `/` final |
| `EXCHANGE_RATE_API_KEY` | Secreto regenerado de ExchangeRate-API |
| `ENVIRONMENT` | `production` |
| `DEBUG` | `false` |

Para varios frontends, separa los orígenes con comas:

```text
https://gastos.example.com,https://gastos-front.onrender.com
```

No uses `*`: la aplicación lo rechaza en producción porque la autenticación
utiliza encabezados y credenciales de navegador.

### MongoDB Atlas

Después de crear el servicio, abre **Connect > Outbound** en Render, copia sus
rangos de salida y añádelos a **Network Access** en Atlas. Utiliza un usuario
de base de datos de mínimos privilegios y una región de Atlas cercana a la
región elegida en Render.

La aplicación valida la configuración al arrancar. Un secreto JWT corto,
MongoDB o ExchangeRate-API sin configurar, `DEBUG=true` o CORS con comodín
hacen fallar el despliegue deliberadamente.

### Verificación posterior

Cuando Render marque el despliegue como disponible, comprueba:

```bash
curl https://TU-SERVICIO.onrender.com/api/v1/health
```

La respuesta esperada es:

```json
{"status":"ok"}
```

Después prueba `/docs`, registra o inicia sesión y verifica una petición desde
el dominio real del frontend. El seed no se ejecuta automáticamente durante
los despliegues para evitar duplicaciones o cambios involuntarios en
producción. Si necesitas datos iniciales, ejecuta `python -m scripts.seed_data`
una sola vez desde un entorno seguro con las variables de producción.
