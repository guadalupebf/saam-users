# Documentación técnica del endpoint `api-token-auth-saam`

## 1. Objetivo

El endpoint `api-token-auth-saam` autentica a un usuario de SAAM con credenciales locales (usuario y contraseña) y devuelve un `token_jwt` que se utiliza como credencial de autorización para consumir la API externa de SAAM.

Además de autenticar al usuario, el endpoint:

- invalida cualquier token previo del mismo usuario;
- genera un nuevo token interno de Django REST Framework;
- empaqueta ese token en un JWT firmado por el backend;
- agrega metadatos funcionales de usuario, organización y vigencia;
- devuelve en la respuesta toda la información mínima necesaria para que un cliente externo pueda conectarse a servicios SAAM autenticados.

---

## 2. Ruta HTTP

- **Método:** `POST`
- **Ruta relativa:** `/api-token-auth-saam/`
- **Registro de ruta en el proyecto:** `cas2/urls.py`

### URL base
La URL completa depende del ambiente donde esté desplegado `saam-users`.

Ejemplos:

- `https://<host>/api-token-auth-saam/`
- `https://usuarios.<dominio>/api-token-auth-saam/`

---

## 3. Tipo de autenticación que entrega

Este endpoint **no devuelve directamente** el token plano de DRF para uso externo. Lo que devuelve es un JWT en el campo:

- `token_jwt`

Ese `token_jwt` contiene internamente el token DRF del usuario y metadatos adicionales. El backend lo firma con:

- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`

### Importante para integradores
Para conectarse con la **API externa de SAAM**, el valor que debe enviarse normalmente en los requests de integración es el JWT devuelto por este endpoint, usando el esquema:

```http
Authorization: Bearer <token_jwt>
```

Esto es consistente con el propio código del proyecto, que al consumir APIs externas SAAM o servicios relacionados construye cabeceras tipo `Bearer` con JWTs generados por backend.

---

## 4. Request esperado

### Content-Type recomendado
```http
Content-Type: application/json
```

También puede funcionar como formulario, porque la vista hereda de `ObtainAuthToken`, pero para integraciones externas se recomienda JSON.

### Campos obligatorios

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---:|---|
| `username` | string | Sí | Username del usuario SAAM. |
| `password` | string | Sí | Contraseña del usuario. |
| `org` | string | Sí, cuando el usuario tiene organización | `urlname` exacto de la organización a la que debe pertenecer el usuario. |

### Campos opcionales

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---:|---|
| `lite` | boolean / truthy | No | Indica autenticación para flujo SAAM Lite. Si se usa incorrectamente, el backend rechaza el acceso según el perfil del usuario. |

### Reglas funcionales del request

1. El usuario y contraseña deben ser válidos.
2. Debe existir `UserInfo` para el usuario.
3. Si el usuario tiene organización asociada, el valor de `org` enviado debe coincidir exactamente con `user_info.org.urlname`.
4. Si el acceso es `lite`, el backend valida compatibilidad entre:
   - el flag `lite` del request,
   - el atributo `is_user_lite` del usuario,
   - y en algunos casos que la organización sea `pruebas`.

---

## 5. Flujo interno del backend

Cuando se invoca `/api-token-auth-saam/`, el backend ejecuta este flujo:

1. Valida credenciales con el serializer de `ObtainAuthToken`.
2. Si el usuario existe, elimina cualquier token DRF previo asociado al usuario.
3. Crea un nuevo `Token` de Django REST Framework.
4. Construye un objeto `jwt_json` con:
   - `token`: token DRF recién creado;
   - `applications`: lista de aplicaciones activas del usuario;
   - `org`: identificador y `urlname` de la organización;
   - `expiration_date`: fecha/hora de expiración calculada con `TOKEN_DURATION`.
5. Firma `jwt_json` con `get_jwt_token(...)`.
6. Devuelve la respuesta con `token_jwt` y metadatos operativos del usuario.
7. Actualiza `ultimo_acceso_saam` del usuario.
8. Ejecuta `delete_token(user.id)` para cerrar sesión previa del mismo usuario en otro servicio SAAM si existe.

---

## 6. Ejemplo de request

### Ejemplo con cURL

```bash
curl --request POST 'https://<host>/api-token-auth-saam/' \
  --header 'Content-Type: application/json' \
  --data-raw '{
    "username": "usuario_demo",
    "password": "password_seguro",
    "org": "mi-organizacion"
  }'
```

### Ejemplo para flujo lite

```bash
curl --request POST 'https://<host>/api-token-auth-saam/' \
  --header 'Content-Type: application/json' \
  --data-raw '{
    "username": "usuario_lite",
    "password": "password_seguro",
    "org": "pruebas",
    "lite": true
  }'
```

---

## 7. Respuesta exitosa

### HTTP Status
- `200 OK`

### Estructura general

```json
{
  "email": "usuario@dominio.com",
  "first_name": "Nombre",
  "last_name": "Apellido",
  "username": "usuario_demo",
  "superuser": false,
  "staff": false,
  "user_id": 123,
  "org": {
    "id": 10,
    "name": "mi-organizacion",
    "urlname": "mi-organizacion",
    "logo_mini": "https://...",
    "whatsappweb": true,
    "phone_mensajeria": "5555555555",
    "phone_sms": "5555555555",
    "active_app1": true,
    "active_app2": false
  },
  "token_jwt": "eyJ0eXAiOiJKV1QiLCJhbGciOi...",
  "permissions": {
    "saam": {
      "clientes": [
        {
          "name": "ver",
          "checked": true,
          "is_active": true
        }
      ]
    }
  },
  "crud_permissions": {
    "crear": true,
    "editar": true,
    "eliminar": true
  },
  "role": 4,
  "cobranza_pendiente": false,
  "crear_usuarios_app": true,
  "another_tasks": false,
  "applications": [
    "saam",
    "multicotizador"
  ]
}
```

### Campos clave para integración

| Campo | Descripción |
|---|---|
| `token_jwt` | Token de autorización que debe usar el integrador frente a la API externa SAAM. |
| `org.urlname` | Organización validada para construir contexto de negocio. |
| `applications` | Aplicaciones activas incluidas en el JWT. |
| `permissions` | Permisos funcionales útiles para control del cliente consumidor. |
| `role` | Rol del usuario. |

---

## 8. Cómo usar el token obtenido contra la API externa SAAM

Una vez obtenido `token_jwt`, el cliente debe enviarlo en los requests posteriores como encabezado `Authorization` con esquema `Bearer`.

### Formato

```http
Authorization: Bearer <token_jwt>
```

### Ejemplo con cURL

```bash
curl --request GET 'https://<api-saam-externa>/recurso/protegido/' \
  --header 'Authorization: Bearer <token_jwt>' \
  --header 'Content-Type: application/json'
```

### Ejemplo con JavaScript

```javascript
const loginResponse = await fetch('https://<host>/api-token-auth-saam/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    username: 'usuario_demo',
    password: 'password_seguro',
    org: 'mi-organizacion'
  })
});

const loginData = await loginResponse.json();
const token = loginData.token_jwt;

const apiResponse = await fetch('https://<api-saam-externa>/recurso/protegido/', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});
```

### Ejemplo con Python

```python
import requests

login = requests.post(
    'https://<host>/api-token-auth-saam/',
    json={
        'username': 'usuario_demo',
        'password': 'password_seguro',
        'org': 'mi-organizacion'
    }
)
login.raise_for_status()

data = login.json()
token = data['token_jwt']

response = requests.get(
    'https://<api-saam-externa>/recurso/protegido/',
    headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
)
response.raise_for_status()
print(response.json())
```

---

## 9. Vigencia y expiración del token

La vigencia del token se calcula con la constante de configuración:

- `TOKEN_DURATION`

En la configuración principal del proyecto está en:

- `480` minutos

El valor también se inserta explícitamente en el JWT como `expiration_date` con formato:

```text
YYYY-MM-DD HH:MM:SS
```

### Consideraciones importantes

- El token DRF interno tiene control de vigencia por middleware.
- Si el token está vencido, el backend lo elimina.
- En endpoints protegidos por autenticación DRF + middleware, el encabezado esperado es `Authorization: Token <token_interno>`.
- Para la integración externa descrita en este documento, el artefacto emitido por `api-token-auth-saam` es el `token_jwt`.

### Recomendación operativa
Renovar el token antes de su expiración o al recibir una respuesta de no autorizado del servicio consumidor.

---

## 10. Posibles errores y respuestas esperadas

### 10.1 Credenciales inválidas
- **HTTP:** `404`
- **Respuesta:** `0018-Usuario y/o contraseña incorrectos`

### 10.2 Usuario sin información complementaria (`UserInfo`)
- **HTTP:** `404`
- **Respuesta:** `0003-Informacion del usuario incompleta (birthdate, genero, phone, rfc)`

### 10.3 Usuario no pertenece a la organización enviada
- **HTTP:** `400`
- **Respuesta:** `0019-Usuario no pertence a la organizacion`

### 10.4 Perfil de login no permitido (`lite` vs normal)
- **HTTP:** `404`
- **Respuesta:** `0022-El usuario no corresponde a su perfil de ingreso`

### 10.5 Token inválido en endpoints protegidos posteriores
- **HTTP:** `401`
- **Respuesta:** `0009-Token Invalido`

---

## 11. Matriz de validaciones de negocio

| Validación | Resultado si falla |
|---|---|
| Usuario/contraseña incorrectos | `404` con error `0018` |
| No existe `UserInfo` del usuario | `404` con error `0003` |
| `org` no coincide con `user_info.org.urlname` | `400` con error `0019` |
| Usuario `lite` intentando login normal | `404` con error `0022` |
| Usuario normal intentando login `lite` indebido | `404` con error `0022` |

---

## 12. Contrato técnico recomendado para integradores

### Request mínimo recomendado

```json
{
  "username": "<usuario>",
  "password": "<password>",
  "org": "<urlname_org>"
}
```

### Response mínima a persistir en cliente

Guardar al menos:

- `token_jwt`
- `user_id`
- `username`
- `org.urlname`
- `applications`
- `expiration_date` (si el consumidor decide decodificar el JWT en cliente o mantener una expiración derivada)

### Buenas prácticas de integración

1. No hardcodear el token.
2. No reutilizar indefinidamente un token antiguo.
3. Renovar sesión cuando el servicio responda `401/403` o al alcanzar vigencia máxima local.
4. Enmascarar credenciales en logs.
5. No exponer `token_jwt` en URL query params.
6. Enviar el token únicamente por header `Authorization`.

---

## 13. Consideraciones de seguridad

- El JWT está firmado por el backend; no debe ser alterado por el cliente.
- El token devuelto contiene contexto de organización y aplicaciones, por lo que debe tratarse como credencial sensible.
- Si el usuario inicia sesión otra vez, el backend elimina tokens previos antes de emitir uno nuevo.
- Existe una limpieza adicional de sesión en SAAM mediante `delete_token(user.id)`.

---

## 14. Procedimiento de conexión extremo a extremo

### Paso 1. Obtener credenciales válidas
Solicitar al administrador del sistema:

- `username`
- `password`
- `org` (`urlname` exacto)
- confirmación de si el usuario es `lite` o no

### Paso 2. Invocar `POST /api-token-auth-saam/`
Enviar las credenciales con `Content-Type: application/json`.

### Paso 3. Validar respuesta `200`
Confirmar que exista el campo:

- `token_jwt`

### Paso 4. Guardar el token de forma segura
Persistirlo en memoria segura o almacén temporal protegido.

### Paso 5. Consumir la API externa SAAM
Enviar en cada request:

```http
Authorization: Bearer <token_jwt>
```

### Paso 6. Renovar cuando expire o falle
Si la API devuelve no autorizado, repetir autenticación para obtener un nuevo `token_jwt`.

---

## 15. Ejemplo de especificación breve para terceros

> Para conectarse a la API externa de SAAM se debe consumir el endpoint `POST /api-token-auth-saam/` enviando `username`, `password` y `org`. La respuesta exitosa devuelve `token_jwt`; ese valor debe enviarse en requests subsecuentes como `Authorization: Bearer <token_jwt>`.

---

## 16. Referencias de implementación en el código fuente

Para auditoría técnica o trazabilidad, la implementación relevante está en:

- Ruta del endpoint: `cas2/urls.py`
- Implementación del login SAAM: `core/views.py`
- Generación del JWT: `core/utils.py`
- Validación de token DRF en middleware: `middlewares/utils.py`
- Middleware de rechazo por token inválido: `middlewares/authentication.py`
- Catálogo de errores funcionales: `core/errors.py`

