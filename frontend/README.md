# Frontend — Dashboard SOC

[← Volver al README principal](../README.md)

Dashboard web de monitorización del Centro de Operaciones de Seguridad, desplegado como sitio estático en Azure Blob Storage.

## URL pública

[https://stsocsmlstorage.z28.web.core.windows.net/](https://stsocsmlstorage.z28.web.core.windows.net/)

## Funcionalidades

- **Métricas en tiempo real** — conexiones analizadas, anomalías detectadas, score medio del modelo, ejecuciones de la Logic App
- **Terminal de pruebas** — envía tráfico normal o simula anomalías contra el endpoint ML y la Logic App directamente desde el navegador
- **Diagrama de flujo animado** — visualiza qué paso del pipeline está activo en cada momento
- **Registro de eventos** — historial de todas las peticiones procesadas en la sesión
- **Panel de incidentes** — muestra los incidentes generados en Sentinel durante la sesión

## Tecnologías

- HTML5 / CSS3 / JavaScript vanilla (sin frameworks)
- Azure Blob Storage — Static Website hosting
- Fuentes: Share Tech Mono, Barlow Condensed (Google Fonts)

## Despliegue

```bash
az storage blob upload \
  --account-name stsocsmlstorage \
  --container-name '$web' \
  --name index.html \
  --file frontend/index.html \
  --content-type "text/html" \
  --auth-mode login
```

## Estructura

```
frontend/
└── index.html    # Aplicación completa (HTML + CSS + JS en un solo fichero)
```

## Notas

- El endpoint ML tiene CORS bloqueado para peticiones desde el navegador. El dashboard usa resultados simulados para la visualización y llama a la Logic App con `mode: no-cors` para disparar el pipeline real.
- La URL del trigger de la Logic App está embebida en el HTML. La clave ML ha sido reemplazada por un placeholder para evitar exposición en GitHub.