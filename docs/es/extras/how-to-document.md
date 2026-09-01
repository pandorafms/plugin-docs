# Cómo documentar

Referencia para quien escriba o migre documentación a este sitio: dónde va
cada contenido nuevo, qué debe cubrir cada tipo de página, y la mecánica de
añadir páginas, secciones e imágenes.

## Cómo colaborar

Toda la documentación vive en el
[repositorio plugin-docs](https://github.com/pandorafms/plugin-docs). Para
colaborar:

1. Realiza tus cambios en una rama (o fork) y abre un pull request (PR)
   contra el repositorio. El formulario del PR se rellena automáticamente
   con la plantilla del repositorio (`.github/PULL_REQUEST_TEMPLATE.md`):
   tipo de cambio, sección afectada, cobertura de idiomas y verificación
   del build local.
2. Un administrador verifica el PR y, una vez que todo está correcto, lo
   aprueba y lo mergea.

La documentación oficial se publica en
<https://pandorafms.com/docs/integrations/> y se sincroniza periódicamente
con la rama `main` del repositorio, así que los cambios mergeados llegan al
sitio en vivo de forma automática.

## ¿Dónde va cada contenido nuevo?

| Sección | Qué va aquí | Ejemplo |
| --- | --- | --- |
| **Discovery** | Plugins que se integran con el asistente de tareas *Discovery* de Pandora: la consola crea una tarea, ejecuta el plugin, y genera automáticamente agentes/módulos a partir de su salida. | NGINX, Playwright |
| **Integrations** | Conectores a herramientas externas de comunicación/colaboración, usados principalmente para alertas (el patrón "enviar una alerta de Pandora a X": configurar el servicio externo, y luego crear un comando/acción de alerta en Pandora). | Telegram, Google Chat, Microsoft Teams |
| **Plugins** | Plugins independientes/manuales que *no* se ejecutan desde el asistente de Discovery — se corren a mano o se conectan como un plugin de servidor normal, sin tareas de Discovery autogeneradas. | Oculix, Logparser (Advanced Log Parser) |
| **Extras** | Contenido meta sobre el propio sitio: esta página, notas para quien documenta, todo lo que no sea documentación de producto. | Esta página |

Si un plugin encajaría en dos secciones (por ejemplo, tiene tanto una tarea
de Discovery como un modo CLI manual), clasifícalo por su vía de uso
*principal* y documentada — no dupliques el mismo contenido en dos
secciones.

## Secciones obligatorias por tipo de contenido

Toda página empieza con un único `# Título` (esto se convierte tanto en
la etiqueta del menú lateral como en el `<title>` de la página), seguido
de la línea de última actualización del artículo y de las secciones de
abajo.

### El orden de lectura es un contrato

Sea cual sea el tipo de contenido, una página guía a quien lee por el
mismo recorrido:

**Overview → Prepare → Configure → Verify → Understand → Troubleshoot → Reference**

La idea es la divulgación progresiva: quien lee tiene que poder
instalar, configurar y confirmar la integración *antes* de encontrarse
con el detalle exhaustivo. La referencia exhaustiva de parámetros va al
final: es aquello a lo que se vuelve, no lo primero que se lee.

De ahí se derivan tres reglas:

- **Nunca reordenes las etapas para encajar el contenido que ya
  tienes.** Al actualizar o migrar una página existente, realinéala a
  este orden; no heredes el orden de la página antigua.
- **Omite una etapa que no aplique** en lugar de dejar un encabezado
  vacío. Lo flexible es *qué* etapas aparecen y cómo las llames, nunca
  el orden de las que sí aparecen.
- **Inglés y español deben usar el mismo orden de secciones.** Si el par
  existente diverge, alinea ambos en el mismo cambio.

Si una sección no encaja en ninguna etapa, o no sabes dónde va,
pregunta antes de publicar. No inventes una posición, no elimines la
sección y no la dejes donde la tenía la página antigua.

### Plugins de Discovery

1. **Overview / What it monitors** — el destino, qué se recoge, qué
   produce el plugin y el modelo de tarea de Discovery.
2. **Prepare** — entorno validado y compatibilidad, prerrequisitos,
   permisos, configuración en el lado del destino e instalación.
3. **Configure the Discovery task** — los campos del asistente y el
   comportamiento de la tarea, con capturas donde eliminen ambigüedad
   real.
4. **Verify** — una ejecución correcta, el resumen de la tarea, los
   agentes esperados y módulos representativos.
5. **Understand the results** — identidad y cardinalidad de los agentes,
   más un resumen funcional de los grupos de módulos.
6. **Troubleshoot** — señales de fallo y diagnósticos con evidencia.
7. **Reference** — parámetros exhaustivos, agrupados por superficie de
   entrada (consola, fichero de configuración, CLI, entorno), y el
   inventario completo de módulos.

Añade una etapa **Operate** antes de Troubleshoot cuando el plugin tenga
una superficie real de operación diaria: ejecución manual, tiempos de
espera, modos de depuración, runtimes propios. La página de Playwright
es el ejemplo trabajado.

Pon un resumen funcional breve antes de cualquier inventario largo, y
agrupa una referencia extensa por recurso, agente generado o condición.

### Plugins (de agente, de servidor o autónomos)

El mismo recorrido, con la ruta de integración como variable:

1. **Overview / What it does** — propósito, modelo de ejecución, entrada
   y salida.
2. **Prepare** — prerrequisitos, instalación, dependencias, permisos y
   compatibilidad.
3. **Configure** — la configuración del agente, el registro del plugin
   de servidor y la creación del módulo, o la configuración autónoma,
   según lo que el plugin admita realmente.
4. **Verify** — salida esperada, ejecución correcta e ingesta en
   Pandora FMS cuando aplique.
5. **Understand the results** — primero el resumen funcional, después el
   detalle de la salida.
6. **Operate and troubleshoot** — ejecución manual, modo detallado,
   limitaciones y diagnósticos.
7. **Reference** — parámetros por superficie y salidas exhaustivas.

No escribas una plantilla distinta por subtipo de plugin, y no dejes que
una ejecución manual documentada dé a entender que hay soporte como
plugin de agente o de servidor.

### Integrations (notificaciones y servicios externos)

1. **Overview / What it does** — el destino, qué se envía y el resultado
   para quien opera.
2. **Prepare the external service** — los pasos realizados *en la
   herramienta externa* (crear un bot, un webhook, un canal...), con
   capturas de pantalla. Suele ser el grueso de la página. Omítela en
   los flujos integrados que no necesiten nada ahí.
3. **Configure Pandora FMS** — la integración incorporada, o el comando
   de alerta y la acción de alerta que lo usa, con capturas de la
   consola.
4. **Verify** — un procedimiento de prueba seguro y el resultado
   esperado en ambos extremos.
5. **Understand the integration** — flujo verificado, comportamiento del
   payload o restricciones de entrega, cuando ayuden.
6. **Troubleshoot** — errores, logs y comprobaciones de recuperación con
   evidencia.
7. **Reference** — parámetros por superficie y los límites relevantes.

## Añadir una página a una sección existente

1. Crea un fichero markdown en `docs/es/<sección>/<página>.md` (y su versión
   en `docs/en/<sección>/<página>.md`, si está lista).
2. Empieza el fichero con un `# Título` — eso es lo que aparece en el menú
   lateral, no el nombre del fichero.
3. Haz commit y push. El menú lo recoge solo, sin tocar `mkdocs.yml`.

## Añadir una sección o página nueva

Las secciones de primer nivel son **Plugins**, **Integrations**,
**Discovery** y **Extras** (`docs/es/plugins/`, `docs/es/integrations/`,
`docs/es/discovery/`, `docs/es/extras/` — con su espejo en `docs/en/`). El
menú se genera a partir de esta estructura de carpetas con
`mkdocs-awesome-pages-plugin` — no hay una lista `nav:` que mantener a mano
para páginas sueltas.

El *orden* de las secciones de primer nivel, sin embargo, necesita algo más
que un fichero `.pages`: `mkdocs-static-i18n` siempre ordena
alfabéticamente el menú de primer nivel al construir el árbol de cada
idioma, lo que deshace en silencio cualquier orden personalizado puesto en
`.pages`. `hooks.py` (registrado en la clave `hooks:` de `mkdocs.yml`) se
ejecuta después de ese ordenamiento y fija ciertos títulos de sección al
final — de momento solo `Extras`. Cualquier *otra* sección de primer nivel
se queda en el orden alfabético que le dio `mkdocs-static-i18n`; si
necesitas una posición fija distinta para una sección nueva, añade su
título a `PINNED_LAST` en `hooks.py` (el orden de esa lista es el orden en
que aparecerán, todas fijadas después de las alfabetizadas).

Para añadir una **sección de primer nivel nueva** (ej. "Dashboards"):

1. Crea `docs/es/dashboards/` (y `docs/en/dashboards/`).
2. Añade un fichero `.pages` dentro con el título de la sección:
   ```yaml
   title: Dashboards
   ```
3. Añade al menos un fichero `.md` dentro de la carpeta nueva.
4. Aparecerá en el menú automáticamente, alfabetizada junto a las demás
   secciones no fijadas. No hace falta tocar `.pages` ni `hooks.py` salvo
   que necesites fijarla a una posición concreta (ver arriba).

Para añadir una **subcategoría** dentro de una sección existente (ej.
agrupar plugins por "Monitoring" / "Network"), basta con anidar otra carpeta
con su propio `.pages`:

```
docs/es/plugins/
  example.md
  monitoring/
    .pages            # title: Monitoring
    cpu.md
    memory.md
```

Sin límite de profundidad — carpetas dentro de carpetas se convierten en
secciones anidadas del menú.

## Traducciones del menú

No hace falta traducir nada aparte del contenido: el título que se muestra en
el menú es el `# H1` de cada página, así que basta con que
`docs/es/<sección>/<página>.md` tenga su propio título en español. Los ficheros
`.pages` de sección (`title:`) se traducen igual, duplicando el fichero bajo
`docs/es/` con el texto correspondiente.

## Añadir una imagen

Las imágenes viven en `docs/<idioma>/assets/images/<sección>/<slug-del-plugin>/`,
una subcarpeta por cada plugin/integración — nunca sueltas directamente en
`assets/images/`. Esto evita que capturas de distintos plugins choquen por
nombre de fichero (BookStack exporta cosas como `image.png` o
`nU2image.png`, que no son únicas entre plugins) y deja claro a qué
pertenece cada carpeta.

Ejemplo, siguiendo el patrón que ya usa la integración de Telegram:

```
docs/en/assets/images/integrations/telegram/
  nU2image.png
  Qe2image.png
  ...
docs/es/assets/images/integrations/telegram/
  Milimage.png        # imagen exclusiva de ES (ver nota de fallback abajo)
```

1. Crea `docs/<idioma>/assets/images/<sección>/<slug-del-plugin>/`
   (coincidiendo con la sección de la página — `plugins`, `integrations` o
   `discovery`) y sube ahí el fichero (`git add` o arrastrándolo en el Web
   IDE de GitLab/GitHub).
2. Referéncialo desde el markdown con una ruta relativa a la página actual.
   Desde una página dentro de una carpeta de sección (el caso habitual, ej.
   `integrations/telegram.md`), es
   `../assets/images/<sección>/<slug-del-plugin>/mi-fichero.png`. Desde una
   página en la raíz como `index.md` (sin carpeta de sección), quita el
   `../` inicial.
3. Imágenes específicas por idioma: si una captura solo difiere de la del
   otro idioma (por ejemplo porque muestra texto de UI localizado),
   añádela en `docs/es/assets/images/<sección>/<slug-del-plugin>/` con el
   mismo nombre de fichero para sobrescribirla — `fallback_to_default: true`
   hace que cualquier fichero *no* sobrescrito ahí se sirva automáticamente
   desde la carpeta `en`, así que solo hace falta añadir las imágenes que
   realmente cambian.
4. Las imágenes se centran y se abren en un lightbox al hacer clic
   automáticamente (`mkdocs-glightbox` + la regla de centrado en
   `stylesheets/extra.css`) — no hace falta marcado extra, un simple
   `![alt](ruta)` es suficiente.

## Vista previa local

**Python:**

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/mkdocs serve
```

**Docker (sin instalar Python):**

```bash
UID=$(id -u) GID=$(id -g) docker compose up
```

Ambas abren `http://localhost:8000` con live reload — los cambios en
cualquier `.md` o imagen refrescan el navegador solos.

## Validación

Ejecuta las comprobaciones automatizadas antes de abrir un pull request:

```bash
python3 -m unittest discover -s tests -p 'test_validate_docs.py'
python3 scripts/validate_docs.py --fail-on blocking
.venv/bin/mkdocs build --strict
```

Los controles bloqueantes comprueban la paridad de rutas entre idiomas, que
cada página tenga un único H1 real, que existan las imágenes locales aplicando
el fallback de español a inglés y que no haya firmas de secretos de alta
confianza. El validador también informa de problemas en enlaces y anchors
locales, cruces entre idiomas, URLs legacy, marcadores pendientes, usos de
`PandoraFMS` en texto renderizado y firmas conocidas de contaminación de
contenido. Estas incidencias informativas permanecen visibles, pero no hacen
fallar el comando predeterminado. Usa `--fail-on all` para tratarlas como fallos
durante una comprobación local.

La vista previa en el navegador es útil para la revisión visual, pero no
sustituye estas comprobaciones.
