# Configuración completa de Supabase

## A. Crear la base de datos

1. Entra a Supabase y crea un proyecto nuevo.
2. Espera a que termine la creación.
3. Abre **SQL Editor**.
4. Crea una consulta nueva.
5. Abre `supabase_schema.sql` de este proyecto.
6. Copia TODO el contenido.
7. Pégalo en SQL Editor.
8. Ejecuta la consulta.
9. Ve a **Table Editor** y verifica que existan:
   - `registros_diarios`
   - `actividades`

## B. Obtener las credenciales

En el proyecto de Supabase entra a **Settings → API**.

Necesitas:

- Project URL
- `service_role` key

La `service_role` key es privada y tiene privilegios elevados. No la subas a GitHub.

## C. Subir a GitHub

Crea un repositorio nuevo, por ejemplo:

`control-proyecto`

Sube el contenido de esta carpeta manteniendo `app.py` y `requirements.txt` en la raíz.

No subas `.streamlit/secrets.toml` con datos reales.

## D. Desplegar en Streamlit Community Cloud

1. Entra a Streamlit Community Cloud.
2. Conecta GitHub.
3. Pulsa **Create app**.
4. Selecciona el repositorio.
5. Branch: `main`.
6. Main file: `app.py`.
7. Abre **Advanced settings**.
8. En **Secrets** pega:

```toml
SUPABASE_URL = "https://TU-PROYECTO.supabase.co"
SUPABASE_SERVICE_KEY = "TU_SERVICE_ROLE_KEY"
APP_PASSWORD = "TU_CLAVE_PRIVADA"
```

9. Pulsa **Deploy**.

La app tendrá una URL `*.streamlit.app`.

## E. Verificación

1. Abre la URL.
2. Introduce `APP_PASSWORD`.
3. Ve a **⚡ Captura rápida**.
4. Registra una fecha.
5. Guarda.
6. Abre **📈 Dashboard**.
7. Abre **🧾 Datos**.
8. En Supabase > Table Editor verifica el registro.

## F. Qué pasa cuando apagas la laptop

Nada. La aplicación vive en Streamlit Community Cloud y los datos viven en Supabase. La laptop solamente se necesita si quieres desarrollar localmente.
