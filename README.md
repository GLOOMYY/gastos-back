# Gastos App Backend

Backend modular de Gastos App, diseñado con FastAPI, MongoDB Atlas y Clean
Architecture pragmática.

## Estado actual

El repositorio contiene el scaffolding inicial, el dominio básico de usuarios
y una aplicación FastAPI mínima con health check. Persistencia,
autenticación y operaciones de negocio todavía no están conectadas.

La estructura completa está documentada en `scaffolding.md`, mientras que
`AGENTS.MD` contiene las reglas obligatorias de arquitectura y desarrollo.

## Requisitos

- Python 3.11.5.
- `pip`.
- Acceso a MongoDB Atlas cuando se implemente la persistencia.

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

El hash de contraseñas se implementará con Passlib y Argon2. La autenticación
todavía no está implementada.

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

Las variables de MongoDB, JWT y tasas de cambio pueden permanecer vacías para
arrancar el servidor mínimo. Serán obligatorias cuando se activen sus
respectivas integraciones.

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

## Datos iniciales

`scripts/seed_account_types.py` y `scripts/seed_categories.py` podrán crear
recursos globales y recursos privados para un usuario explícitamente
identificado. Un recurso con `user_id` nulo será global; cualquier recurso con
usuario asignado pertenecerá exclusivamente a ese usuario.
