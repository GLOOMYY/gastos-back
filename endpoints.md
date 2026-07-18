# Endpoints de Gastos API

Este documento describe los endpoints disponibles actualmente en el backend.

## Información general

URL local predeterminada:

```text
http://127.0.0.1:8000
```

Prefijo de la API:

```text
/api/v1
```

Los cuerpos de petición y respuesta utilizan JSON, excepto las respuestas
`204 No Content`.

## Autenticación Bearer

Los endpoints protegidos requieren un access token en el encabezado:

```http
Authorization: Bearer ACCESS_TOKEN
```

El access token y el refresh token tienen responsabilidades diferentes:

- El access token autoriza endpoints protegidos.
- El refresh token permite obtener una nueva pareja de tokens.
- El refresh token no se utiliza como bearer token.
- Cada refresh exitoso invalida el refresh token anterior.

## Formato estándar de errores

```json
{
  "code": "invalid_credentials",
  "message": "The email or password is incorrect.",
  "details": null,
  "request_id": "c18a52c7-b6ee-4fbd-8226-ff0ff961afda"
}
```

- `code`: identificador estable para lógica del cliente.
- `message`: descripción en inglés para humanos.
- `details`: información adicional o errores de validación.
- `request_id`: identificador de correlación para soporte y logs.

El cliente debe tomar decisiones usando `code`, no comparando `message`.

## Resumen

| Método | Ruta | Autenticación | Descripción |
|---|---|---|---|
| `GET` | `/api/v1/health` | No | Comprueba disponibilidad HTTP |
| `POST` | `/api/v1/auth/register` | No | Registra un usuario |
| `POST` | `/api/v1/auth/login` | No | Inicia una sesión |
| `POST` | `/api/v1/auth/refresh` | Refresh token en body | Rota la sesión |
| `POST` | `/api/v1/auth/logout` | Refresh token en body | Revoca una sesión |
| `GET` | `/api/v1/auth/me` | Bearer | Consulta el usuario actual |
| `GET` | `/api/v1/users/me` | Bearer | Consulta el usuario actual |
| `PATCH` | `/api/v1/users/me` | Bearer | Actualiza email o contraseña |
| `DELETE` | `/api/v1/users/me` | Bearer | Desactiva el usuario actual |
| `POST` | `/api/v1/account-types` | Bearer | Crea un tipo de cuenta privado |
| `GET` | `/api/v1/account-types` | Bearer | Lista tipos globales y propios |
| `GET` | `/api/v1/account-types/{id}` | Bearer | Consulta un tipo disponible |
| `PUT` | `/api/v1/account-types/{id}` | Bearer | Actualiza un tipo propio |
| `DELETE` | `/api/v1/account-types/{id}` | Bearer | Desactiva un tipo propio |
| `POST` | `/api/v1/categories` | Bearer | Crea una categoría privada |
| `GET` | `/api/v1/categories` | Bearer | Lista categorías globales y propias |
| `GET` | `/api/v1/categories/{id}` | Bearer | Consulta una categoría disponible |
| `PUT` | `/api/v1/categories/{id}` | Bearer | Actualiza una categoría propia |
| `DELETE` | `/api/v1/categories/{id}` | Bearer | Desactiva una categoría propia |
| `POST` | `/api/v1/accounts` | Bearer | Crea una cuenta financiera |
| `GET` | `/api/v1/accounts` | Bearer | Lista las cuentas propias |
| `GET` | `/api/v1/accounts/{id}` | Bearer | Consulta una cuenta propia |
| `PUT` | `/api/v1/accounts/{id}` | Bearer | Actualiza nombre y descripción |
| `DELETE` | `/api/v1/accounts/{id}` | Bearer | Desactiva una cuenta |
| `POST` | `/api/v1/transactions/income` | Bearer | Registra un ingreso |
| `POST` | `/api/v1/transactions/expense` | Bearer | Registra un gasto |
| `GET` | `/api/v1/transactions` | Bearer | Lista el historial paginado |
| `GET` | `/api/v1/transactions/cash-flow` | Bearer | Entrega datos para gráfica de flujo de caja |
| `GET` | `/api/v1/transactions/{id}` | Bearer | Consulta un movimiento |
| `POST` | `/api/v1/transactions/{id}/reversal` | Bearer | Revierte un movimiento |

---

## Health check

### `GET /api/v1/health`

Comprueba que la aplicación HTTP está disponible. No comprueba el estado de
MongoDB.

Respuesta `200 OK`:

```json
{
  "status": "ok"
}
```

Ejemplo:

```bash
curl http://127.0.0.1:8000/api/v1/health
```

---

## Registro

### `POST /api/v1/auth/register`

Crea un usuario activo con rol `user`.

Autenticación: no requerida.

Body:

```json
{
  "email": "user@example.com",
  "password": "strong-password"
}
```

Validaciones:

- `email`: entre 3 y 254 caracteres y formato válido.
- `password`: entre 8 y 128 caracteres.
- El email se normaliza para comprobar unicidad sin distinguir mayúsculas.

Respuesta `201 Created`:

```json
{
  "id": "507f1f77bcf86cd799439011",
  "email": "user@example.com",
  "role": "user",
  "is_active": true,
  "created_at": "2026-07-17T12:00:00Z",
  "updated_at": "2026-07-17T12:00:00Z"
}
```

Errores frecuentes:

| Estado | `code` | Motivo |
|---|---|---|
| `409` | `user_already_exists` | El email normalizado ya existe |
| `422` | `invalid_email` | El formato del email es inválido |
| `422` | `invalid_password` | La contraseña incumple la política |
| `422` | `request_validation_error` | El body no cumple el schema |
| `503` | `service_unavailable` | MongoDB no está configurado o disponible |

Ejemplo:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"user@example.com","password":"strong-password"}'
```

---

## Login

### `POST /api/v1/auth/login`

Valida email y contraseña, crea una familia de sesión y entrega una pareja de
tokens.

Autenticación: no requerida.

Body:

```json
{
  "email": "user@example.com",
  "password": "strong-password"
}
```

Respuesta `200 OK`:

```json
{
  "access_token": "ACCESS_TOKEN",
  "refresh_token": "REFRESH_TOKEN",
  "token_type": "bearer",
  "access_token_expires_at": "2026-07-17T12:30:00Z",
  "refresh_token_expires_at": "2026-08-16T12:00:00Z"
}
```

Errores frecuentes:

| Estado | `code` | Motivo |
|---|---|---|
| `401` | `invalid_credentials` | Email inexistente o contraseña incorrecta |
| `403` | `inactive_user` | El usuario está desactivado |
| `422` | `request_validation_error` | El body no cumple el schema |
| `503` | `service_unavailable` | MongoDB o JWT no están configurados |

El error de credenciales no indica si falló el email o la contraseña.

Ejemplo:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"user@example.com","password":"strong-password"}'
```

---

## Renovar sesión

### `POST /api/v1/auth/refresh`

Consume un refresh token y devuelve una pareja nueva. El refresh token usado
queda revocado inmediatamente.

Autenticación: refresh token en el body; no utiliza encabezado bearer.

Body:

```json
{
  "refresh_token": "REFRESH_TOKEN"
}
```

Respuesta `200 OK`:

```json
{
  "access_token": "NEW_ACCESS_TOKEN",
  "refresh_token": "NEW_REFRESH_TOKEN",
  "token_type": "bearer",
  "access_token_expires_at": "2026-07-17T13:00:00Z",
  "refresh_token_expires_at": "2026-08-16T12:30:00Z"
}
```

Errores frecuentes:

| Estado | `code` | Motivo |
|---|---|---|
| `401` | `invalid_authentication_token` | Token inválido, expirado, revocado o reutilizado |
| `403` | `inactive_user` | El usuario fue desactivado |
| `422` | `request_validation_error` | Falta el token o el body es inválido |
| `503` | `service_unavailable` | MongoDB o JWT no están configurados |

Si se reutiliza un refresh token que ya fue rotado, se revoca toda su familia
de sesión. El cliente debe reemplazar siempre ambos tokens por los nuevos.

---

## Logout

### `POST /api/v1/auth/logout`

Revoca el refresh token indicado. La operación es idempotente: repetirla no
revela si el token existía.

Autenticación: refresh token en el body; no utiliza encabezado bearer.

Body:

```json
{
  "refresh_token": "REFRESH_TOKEN"
}
```

Respuesta `204 No Content`: no contiene body.

Errores frecuentes:

| Estado | `code` | Motivo |
|---|---|---|
| `422` | `request_validation_error` | Falta el token o el body es inválido |
| `503` | `service_unavailable` | MongoDB o JWT no están configurados |

El access token ya emitido conserva su expiración normal.

---

## Consultar el usuario actual

### `GET /api/v1/users/me`

Devuelve el usuario identificado por el access token.

Autenticación: bearer access token.

Respuesta `200 OK`:

```json
{
  "id": "507f1f77bcf86cd799439011",
  "email": "user@example.com",
  "role": "user",
  "is_active": true,
  "created_at": "2026-07-17T12:00:00Z",
  "updated_at": "2026-07-17T12:00:00Z"
}
```

Errores frecuentes:

| Estado | `code` | Motivo |
|---|---|---|
| `401` | `authentication_required` | No se envió un bearer token |
| `401` | `invalid_authentication_token` | El access token no es válido |
| `403` | `inactive_user` | El usuario está desactivado |
| `503` | `service_unavailable` | MongoDB o JWT no están configurados |

Ejemplo:

```bash
curl http://127.0.0.1:8000/api/v1/users/me \
  -H 'Authorization: Bearer ACCESS_TOKEN'
```

### `GET /api/v1/auth/me`

Alias compatible de `GET /api/v1/users/me`. Utiliza la misma autenticación y
devuelve el mismo schema. Se conserva para no romper clientes existentes.

---

## Actualizar el usuario actual

### `PATCH /api/v1/users/me`

Actualiza el email, la contraseña o ambos. No acepta un `user_id`; el recurso
se obtiene siempre del access token.

Autenticación: bearer access token.

Body con ambos campos:

```json
{
  "email": "new@example.com",
  "password": "new-strong-password"
}
```

También son válidos:

```json
{
  "email": "new@example.com"
}
```

```json
{
  "password": "new-strong-password"
}
```

Debe enviarse al menos uno de los campos.

Respuesta `200 OK`: utiliza el mismo schema de usuario mostrado anteriormente.

Efectos de seguridad:

- Cambiar la contraseña genera un hash Argon2 nuevo.
- Cambiar la contraseña revoca todos los refresh tokens del usuario.
- Los access tokens ya emitidos conservan su expiración normal.

Errores frecuentes:

| Estado | `code` | Motivo |
|---|---|---|
| `401` | `authentication_required` | No se envió un bearer token |
| `401` | `invalid_authentication_token` | El access token no es válido |
| `403` | `inactive_user` | El usuario está desactivado |
| `409` | `user_already_exists` | El email pertenece a otro usuario |
| `422` | `invalid_email` | El nuevo email es inválido |
| `422` | `invalid_password` | La contraseña incumple la política |
| `422` | `request_validation_error` | Body vacío o formato inválido |
| `503` | `service_unavailable` | MongoDB o JWT no están configurados |

Ejemplo:

```bash
curl -X PATCH http://127.0.0.1:8000/api/v1/users/me \
  -H 'Authorization: Bearer ACCESS_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{"email":"new@example.com"}'
```

---

## Desactivar el usuario actual

### `DELETE /api/v1/users/me`

Realiza una eliminación lógica:

- El documento del usuario no se borra.
- El historial financiero se conserva.
- `is_active` cambia a `false`.
- Todos los refresh tokens del usuario quedan revocados.
- Los endpoints protegidos rechazan al usuario inactivo.

Autenticación: bearer access token.

Respuesta `204 No Content`: no contiene body.

Errores frecuentes:

| Estado | `code` | Motivo |
|---|---|---|
| `401` | `authentication_required` | No se envió un bearer token |
| `401` | `invalid_authentication_token` | El access token no es válido |
| `403` | `inactive_user` | El usuario ya está desactivado |
| `503` | `service_unavailable` | MongoDB o JWT no están configurados |

Ejemplo:

```bash
curl -X DELETE http://127.0.0.1:8000/api/v1/users/me \
  -H 'Authorization: Bearer ACCESS_TOKEN'
```

---

## Catálogos: tipos de cuenta y categorías

Los listados combinan recursos globales (`user_id: null`) y recursos privados
del usuario autenticado. Los globales son de sólo lectura desde la API. Las
operaciones `PUT` y `DELETE` únicamente aceptan recursos propios; `DELETE`
realiza desactivación lógica.

Crear tipo de cuenta privado:

```json
{
  "code": "DIGITAL_WALLET",
  "name": "Digital wallet",
  "description": "Personal wallet"
}
```

Crear o reemplazar una categoría:

```json
{
  "name": "Transport",
  "transaction_type": "expense",
  "description": "Daily transport"
}
```

`GET /api/v1/categories` acepta el filtro opcional
`transaction_type=income|expense`.

## Cuentas

`POST /api/v1/accounts` recibe:

```json
{
  "account_type_id": "507f1f77bcf86cd799439011",
  "name": "Main account",
  "initial_balance": "1000000.00",
  "currency": "COP",
  "description": "Daily account"
}
```

Si `initial_balance` es diferente de cero, la cuenta y el movimiento
inmutable `initial_balance` se persisten dentro de la misma transacción de
MongoDB. `PUT` sólo cambia `name` y `description`; el saldo nunca se modifica
mediante el CRUD. `DELETE` desactiva la cuenta y conserva su historial.

## Movimientos financieros

Ingresos y gastos comparten este body:

```json
{
  "account_id": "507f1f77bcf86cd799439011",
  "category_id": "507f1f77bcf86cd799439012",
  "amount": "25000.00",
  "occurred_at": "2026-07-18T15:00:00Z",
  "description": "Example movement",
  "note": null
}
```

La categoría debe ser global o propia, estar activa y coincidir con el tipo
del movimiento. La actualización del saldo y la creación del movimiento son
atómicas. Las cuentas pueden quedar con saldo negativo.

El listado usa `limit` (1 a 100, predeterminado 20) y un `cursor` opaco:

```json
{
  "items": [],
  "next_cursor": null,
  "has_more": false
}
```

Los movimientos confirmados no tienen `PUT` ni `DELETE`. Para corregir uno se
usa `POST /api/v1/transactions/{id}/reversal`:

```json
{
  "reason": "Duplicated entry"
}
```

La reversión crea un asiento compensatorio y deja intacto el original.

## Gráfica de ingresos y gastos

### `GET /api/v1/transactions/cash-flow`

Entrega una serie continua lista para utilizarse directamente en una gráfica
del frontend. Sólo incluye movimientos del usuario autenticado y de la moneda
solicitada.

Parámetros opcionales:

| Parámetro | Valor predeterminado | Descripción |
|---|---|---|
| `date_from` | 89 días antes de `date_to` | Primera fecha incluida |
| `date_to` | Fecha actual | Última fecha incluida |
| `currency` | `COP` | Código de moneda de tres letras |
| `interval` | `day` | Agrupación `day` o `month` |

El rango debe contener entre 1 y 366 días. Ejemplo:

```http
GET /api/v1/transactions/cash-flow?date_from=2026-05-01&date_to=2026-07-31&currency=COP&interval=month
Authorization: Bearer ACCESS_TOKEN
```

Respuesta `200 OK`:

```json
{
  "currency": "COP",
  "interval": "month",
  "date_from": "2026-05-01",
  "date_to": "2026-07-31",
  "points": [
    {
      "period": "2026-05",
      "income": "3650000",
      "expense": "815000",
      "net": "2835000"
    }
  ],
  "total_income": "3650000",
  "total_expense": "815000",
  "net": "2835000"
}
```

Los períodos sin movimientos también aparecen con valores en cero. Las
reversiones compensan el ingreso o gasto original sin alterar el asiento
confirmado.

## Documentación automática

FastAPI expone además:

| Ruta | Descripción |
|---|---|
| `/docs` | Swagger UI interactivo |
| `/redoc` | Documentación ReDoc |
| `/openapi.json` | Documento OpenAPI en JSON |

Estas rutas no utilizan el prefijo `/api/v1`.

## Flujo recomendado del cliente

1. Registrar el usuario con `/auth/register`, si aún no existe.
2. Iniciar sesión con `/auth/login`.
3. Guardar access y refresh token de forma segura.
4. Usar el access token como bearer en endpoints protegidos.
5. Antes de expirar, llamar `/auth/refresh` y reemplazar ambos tokens.
6. Al cerrar sesión, llamar `/auth/logout` con el refresh token vigente.

Nunca deben almacenarse tokens en logs ni incluirse en URLs.
