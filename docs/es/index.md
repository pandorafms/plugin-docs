# Guías de Pandora FMS — Piloto

Esta es una migración piloto de BookStack a **MkDocs + Material**, con:

- Soporte multilenguaje (`mkdocs-static-i18n`, basado en carpetas: `docs/en/`, `docs/es/`)
- Gestión de imágenes vía commits de Git + zoom con lightbox (`mkdocs-glightbox`)
- Despliegues de staging por rama a través de GitLab CI/Pages

## Imagen de ejemplo

Esta captura no existe en `docs/es/assets/images/`, así que el plugin la sirve
automáticamente desde el idioma por defecto (`en/`) gracias a
`fallback_to_default: true`.

![Captura del piloto](assets/images/screenshot.png)

Siguiente: [Cómo documentar](extras/how-to-document.md)
