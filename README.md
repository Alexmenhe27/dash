# Control de Proyecto — Cloud + Supabase

Sistema de control diario inspirado en la pizarra proporcionada. La app está pensada para trabajar desde navegador y guardar los datos en Supabase, de modo que la laptop no sea el servidor.

## Arquitectura

GitHub = código → Streamlit Community Cloud = aplicación → Supabase = base de datos.

## Incluye

- Inicio con indicadores.
- Captura rápida de un día.
- Cálculo automático del costo total de cada actividad.
- Costo acumulado.
- Retrasos, depreciación, sueldo, altas, bajas y cambios.
- Matriz de riesgos.
- Cronograma tipo Gantt.
- Dashboard ejecutivo.
- Evolución diaria.
- Histórico y CSV.
- Vista de la pizarra original.
- Contraseña de aplicación mediante Secrets.
- PostgreSQL en Supabase.

## Despliegue final

1. Crear un proyecto en Supabase.
2. Abrir SQL Editor.
3. Ejecutar el archivo `supabase_schema.sql` completo.
4. Obtener Project URL y la `service_role` key desde Settings > API.
5. Subir esta carpeta a un repositorio de GitHub.
6. En Streamlit Community Cloud elegir ese repositorio y `app.py`.
7. En Advanced settings > Secrets pegar:

```toml
SUPABASE_URL = "https://TU-PROYECTO.supabase.co"
SUPABASE_SERVICE_KEY = "TU_SERVICE_ROLE_KEY"
APP_PASSWORD = "TU_CLAVE_PRIVADA"
```

8. Deploy.

## Seguridad

La `service_role` key es una credencial privilegiada. Nunca debe estar en el código, README, GitHub ni capturas de pantalla. Debe existir únicamente como Secret de Streamlit.

## Uso

Una vez desplegada, la app queda disponible desde cualquier dispositivo con internet. La laptop puede estar apagada.
