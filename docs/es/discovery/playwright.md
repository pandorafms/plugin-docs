# Playwright

## Introducción

**Ver**. 31-08-2026

Este documento describe el plugin de Discovery de Playwright (`pandorafms.playwright.1`) y su integración con PandoraFMS. El plugin proporciona monitorización web sintética con [Playwright](https://playwright.dev/): tú aportas un único test `.ts` de Playwright, el plugin lo ejecuta dentro de un contenedor Docker preconfigurado (en local o en un host remoto por SSH) y convierte el resultado en módulos de monitorización de PandoraFMS que se integran con la vista transaccional WUX de la consola (estado/tiempo global, estado/tiempo por fase, captura de pantalla de error, métricas personalizadas).

El modelo de ejecución está construido en torno al comportamiento nativo de Playwright:

1. La tarea de Discovery (o una ejecución manual por CLI) lanza un contenedor Docker a partir de la imagen de Playwright (`pandorafms/pandora_playwright:noble`).
2. El test `.ts` se copia dentro del contenedor y se ejecuta con `npx playwright test --reporter=json`.
3. El plugin lee el reporter JSON y construye **un agente por cada `test(...)` de Playwright**, con módulos para el estado/tiempo global, cada `test.step` como fase, una captura de pantalla de error en caso de fallo y cualquier métrica personalizada.
4. Los resultados se devuelven como datos de monitorización de Discovery o, con `-x`, se envían como XML de agente vía Tentacle.

Es el equivalente en Playwright de `pandorafms.selenium.4`, pero **sin librería propia que importar ni DSL que aprender**: escribes código Playwright estándar y el plugin obtiene todo directamente del reporter JSON de Playwright. La ejecución es siempre en Docker; con `worker_mode = remote` el contenedor se ejecuta en un host remoto al que se accede por SSH.

**Tipo**: plugin de Discovery (`.disco`). El nombre corto de la aplicación es `pandorafms.playwright.1` (`id_app = 10`) y `discovery_definition.ini` declara `version = "1.0"`.

## Matriz de compatibilidad

| **Sistemas donde se ha probado** | Runtime de Playwright **1.62.0** en Node 24; imagen Docker `pandorafms/pandora_playwright:noble` (basada en `mcr.microsoft.com/playwright:v1.62.0-noble`, Ubuntu 24.04, navegadores preinstalados); navegadores Chromium, Mozilla Firefox y WebKit (opción `_browser_` del plugin); modo de worker `local`; modo de worker `remote` (host SSH); vista transaccional WUX de la consola de PandoraFMS (ejecución de QA de extremo a extremo contra el Tentacle de un servidor Pandora real) |
| --- | --- |
| **Sistemas donde funciona** | Cualquier sistema que pueda ejecutar Docker como worker **local**, o alcanzar por SSH un host que pueda ejecutar Docker como worker **remoto**. **No establecido**: una matriz de compatibilidad por versión de servidor PandoraFMS (no existen registros por versión) y el sistema operativo del host Docker (la imagen está basada en Ubuntu 24.04 y el SO del host usado en las pruebas fue Linux) |

## Prerrequisitos

1. **Docker** en la máquina que ejecuta el test: el propio servidor de Discovery para `worker_mode = local`, o el destino SSH para `worker_mode = remote`.
2. **La imagen Docker de Playwright** `pandorafms/pandora_playwright:noble` disponible en esa máquina (con los navegadores preinstalados), descargada desde el registro:

   ```bash
   docker pull pandorafms/pandora_playwright:noble
   ```

   Esta es la forma recomendada de obtenerla. Qué contiene la imagen y cómo construirla o personalizarla tú mismo está en [La imagen Docker](#la-imagen-docker).
3. **PandoraFMS**: un servidor de Discovery habilitado (`discoveryserver 1` en `pandora_server.conf`) para ejecutar tareas, y la consola para definirlas.
4. **Solo worker remoto** (`worker_mode = remote`): una cuenta SSH que pueda ejecutar Docker en el host remoto (dirección, puerto, usuario y contraseña o contraseña cifrada).
5. **Solo ejecuciones manuales por CLI** (fuera de una instalación empaquetada): Python 3 con las dependencias del runner:

   ```bash
   python3 -m venv venv
   ./venv/bin/pip install "chardet<6" paramiko scp pycryptodome pandoraPlugintools-basic
   ```

## Parámetros

Estos se corresponden con el formulario de la tarea de Discovery (consola) y con la configuración JSON de la tarea que recibe el runner. La consola los presenta en **cuatro pasos de asistente** que coinciden con las secciones `[config_steps]` de `discovery_definition.ini`: Basic setup, Worker setup (solo para `remote`), Test setup y Advanced setup.

### Basic setup

| Campo | Macro | Valores | Por defecto | Notas |
|-------|-------|---------|-------------|-------|
| Worker mode | `_workerMode_` | `local`, `remote` | `local` | `remote` ejecuta Docker en un host SSH |
| Browser | `_browser_` | `chromium`, `firefox`, `webkit` | `chromium` | |

### Worker setup (solo se muestra para `remote`)

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|-------------|-------|
| SSH address | `_sshAddress_` | string | — | Host que ejecuta Docker |
| SSH port | `_sshPort_` | number | `22` | |
| SSH user | `_sshUser_` | string | `root` | Debe poder ejecutar Docker |
| SSH password | `_sshPassword_` | password | — | Cifrable |
| Encrypt password | `_sshPasswordEncrypt_` | checkbox | on | Ofusca la contraseña en la configuración de la tarea |
| Temporal folder | `_sshTemp_` | string | `/tmp` | Dónde se copia el fichero del test en el host |

### Test setup

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|-------------|-------|
| Docker image | `_dockerImage_` | string | `pandorafms/pandora_playwright:noble` | |
| Browser width | `_browserWidth_` | number | `1920` | Ancho del viewport en píxeles, aplicado a través de la configuración generada, ya que `viewport` no tiene flag de línea de comandos. Un valor no positivo vuelve al valor por defecto |
| Browser height | `_browserHeight_` | number | `1080` | Alto del viewport en píxeles, mismo mecanismo que el ancho |
| Test timeout | `_globalTimeout_` | number | `120` | Timeout global en **segundos** para cada test: es el presupuesto de un `test(...)` completo, no por paso ni por tarea. Para los de cada paso ver **Advanced timeouts** y [Tiempos de espera (timeouts)](#tiempos-de-espera-timeouts) |
| Send full report | `_fullReport_` | checkbox | off | Añade un módulo con el informe de texto detallado |
| Full report agent name | `_reportAgent_` | string | — | Agente que contiene el informe completo; vacío = agente del primer test. Solo se muestra cuando **Send full report** está marcado |
| Prefix for agents created | `_prefixAgents_` | string | — | Opcional. Se antepone al título del test al derivar el nombre y el alias del agente, de modo que dos tareas que ejecutan un test con el mismo título no compartan agente. Vacío conserva el nombrado original (y los agentes existentes) intactos |
| Playwright test (.ts) | `_playwrightTest_` | textarea | — | El contenido completo del fichero de test |
| Generate error history module | `_errorHistoryModule_` | checkbox | off | Añade un módulo de cadena síncrono por estado/fase (`OK` o el texto del error), para que Pandora mantenga una serie histórica real de errores |

### Advanced setup

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|-------------|-------|
| Debug mode | `_debug_` | checkbox | off | Ejecuta el test con la configuración de depuración de Playwright (trace, screenshot, video) y deja los artefactos en el directorio de depuración |
| Debug directory | `_debugDirectory_` | string | `/var/spool/pandora/data_in/discovery/tmp/playwright/_taskid_` | **Ruta absoluta** en la máquina que realmente ejecuta Docker — el servidor de Discovery local para `worker_mode = local`, o el host SSH remoto para `worker_mode = remote` — **no** en esta consola. Docker rechaza de plano una ruta relativa de bind-mount, así que el runner valida que la ruta sea absoluta y falla rápidamente si no lo es. Obligatorio cuando Debug mode está activado (el formulario de la consola no puede expresar un campo obligatorio condicional, así que también lo valida el runner). El placeholder `_taskid_` se sustituye en tiempo de ejecución por el plugin — **no** es una macro real de Discovery, solo se reconoce dentro de este campo — por el mismo valor `md5(id_rt)` que Discovery ya calcula internamente como `__taskMD5__`, de modo que cualquier otra herramienta puede recalcularlo a partir del `id_rt` de la tarea para localizar la salida de depuración correspondiente. Sustitúyelo por una ruta absoluta fija para reutilizar la misma carpeta entre ejecuciones de otra tarea |
| Advanced timeouts | `_advancedTimeouts_` | checkbox | off | Expone los tres timeouts por paso de Playwright, que no tienen flag de línea de comandos. Al activarlo, los tres valores siguientes se añaden a la configuración generada. **El fichero de test nunca se modifica.** Ver [Tiempos de espera (timeouts)](#tiempos-de-espera-timeouts) |
| Action timeout | `_actionTimeout_` | number | `0` | Segundos para cada acción (`click`, `fill`, `press`, `check`, `selectOption`...). `0` = sin límite, el valor por defecto de Playwright. Solo se muestra cuando **Advanced timeouts** está marcado |
| Navigation timeout | `_navigationTimeout_` | number | `0` | Segundos para cada navegación (`goto`, `waitForURL`, `waitForNavigation`, `reload`). `0` = sin límite, el valor por defecto de Playwright. Solo se muestra cuando **Advanced timeouts** está marcado |
| Expect timeout | `_expectTimeout_` | number | `5` | Segundos para cada aserción web-first (`expect(locator).toBeVisible()`, `toHaveText`...). El valor por defecto de Playwright es `5`; `0` = sin límite. Solo se muestra cuando **Advanced timeouts** está marcado |
| Remove existing container with the same task name | `_overrideContainer_` | checkbox | off | El runner siempre inicia el contenedor del test con `--rm`, así que un contenedor huérfano por una ejecución interrumpida se elimina solo cuando termina su `sleep` y libera el nombre de la tarea. Al activarlo, el runner además elimina (`docker rm -f`) cualquier contenedor que ya tenga el nombre derivado de esta tarea antes de empezar, de modo que un resto de una ejecución anterior interrumpida no pueda bloquear la siguiente con un error Docker de "name already in use". Actívalo solo si te encuentras ese error: si la misma tarea se lanza dos veces a la vez, esto también elimina la otra instancia en ejecución |

### Configuración JSON de la tarea (lo que lee el runner)

```json
{
  "worker_mode": "local",
  "browser": "chromium",
  "ssh_address": "", "ssh_port": "22", "ssh_user": "root",
  "ssh_password": "", "ssh_password_encrypt": "0", "ssh_temp_folder": "/tmp",
  "docker_image": "pandorafms/pandora_playwright:noble",
  "browser_width": "1920", "browser_height": "1080",
  "global_timeout": "120",
  "full_report": "0",
  "report_agent": "",
  "agent_prefix": "",
  "error_history_module": "0",
  "override_container": "0",
  "advanced_timeouts": "0",
  "action_timeout": "0", "navigation_timeout": "0", "expect_timeout": "5",
  "debug": "0",
  "debug_directory": ""
}
```

La plantilla vive en la sección `[tempfile_confs]` de `discovery_definition.ini`; cada macro con la forma `_xxx_` se sustituye con los valores almacenados de la tarea. La contraseña SSH se puede almacenar cifrada: la consola llama a `password_encrypter.py` (AES-256-CBC) cuando `_sshPasswordEncrypt_` está activado. Desde la CLI, `password_encrypter.py -e -p <password>` cifra una contraseña y `password_encrypter.py -d -p <password>` la descifra.

## Ejecución manual

El entrypoint del runner es `pandora_playwright.py`. Una ejecución manual reproduce lo que hace el servidor de Discovery en cada ejecución de tarea, pero sin `id_rt`: deriva el nombre del contenedor Docker a partir del nombre de tarea `-t` (haciéndole un hash cuando no es ya un md5) en lugar de usar `md5(id_rt)`.

### Formato de ejecución

```
pandora_playwright.py -c <conf.json> -s <test.ts> -t <task_name> [options]
```

| Opción | Larga | Obligatorio | Por defecto | Descripción |
|--------|-------|-------------|-------------|-------------|
| `-c` | `--conf` | sí | — | Ruta al JSON de configuración de la tarea |
| `-s` | `--test` | sí | — | Ruta al fichero de test `.ts` de Playwright |
| `-t` | `--task` | sí | — | Nombre de la tarea (se usa para derivar el nombre del contenedor) |
| `-i` | `--interval` | no | `300` | Intervalo del agente (segundos) |
| `-g` | `--group` | no | `0` | Id de grupo para los agentes creados |
| `-x` | `--xml_mode` | no | off | Genera el XML del agente y lo envía por Tentacle |
| `-S` | `--server` | no | `127.0.0.1:41121` | `server:port` de Tentacle (con `-x`) |
| `-T` | `--temp` | no | `/tmp` | Carpeta temporal para el XML (con `-x`) |
| `-v` | `--verbose` | no | off | Traza paso a paso por STDERR |

`password_encrypter.py` admite `-e/--encrypt`, `-d/--decrypt` y `-p/--password <password>` (`-e` y `-d` son mutuamente excluyentes).

#### Ejemplos

Ejecución local con un test y una configuración adecuada:

```bash
./venv/bin/python pandora_playwright.py -c conf.json -s sample.spec.ts -t qa-test -g 0
```

Ejecución remota por SSH (la configuración apunta `worker_mode` a `remote`):

```bash
./venv/bin/python pandora_playwright.py -c conf_remote.json -s sample.spec.ts -t qa-remote -g 0
```

De extremo a extremo contra el Tentacle de un servidor Pandora (crea agentes/módulos reales):

```bash
./venv/bin/python pandora_playwright.py -x -S 127.0.0.1:41121 \
    -c conf.json -s sample.spec.ts -t qa-console -g 13 -T /tmp
```

Cifrar una contraseña para la configuración del worker remoto:

```bash
./venv/bin/python password_encrypter.py -e -p <password>
```

#### Modo verbose

`-v` imprime una traza paso a paso con marca de tiempo por STDERR — útil para ejecuciones manuales. Registra literalmente cada comando Docker/SSH (`$` local, `ssh$` remoto), el resumen de configuración, el tamaño del informe, la captura de pantalla, la construcción de cada agente, el tamaño del informe completo y su envío. Ejemplo (remoto):

```
Task <id>: worker=remote browser=chromium image=...:noble timeout=15s ...
Connecting SSH to 10.0.0.5:22 as root
SSH authenticated
SCP test.ts -> /tmp/<id>.spec.ts
ssh$ docker run -d --name <id> ...:noble sleep 300
ssh$ docker cp "/tmp/<id>.spec.ts" <id>:/pandora/task.spec.ts
ssh$ docker exec <id> sh -c 'cd /pandora && ... npx playwright test ... --reporter=json'
ssh$ docker exec <id> cat /tmp/report.json
Report retrieved (10744 bytes)
Screenshot harvested: .../test-failed-1.png (7416 b64 chars)
ssh$ docker rm -f <id>
Agent a...  [passing checkout]: PASS, 2 phases, 9 modules
Emitting monitoring_data: 2 agents
```

## Configuración en PandoraFMS

El plugin se instala en el store de plugins de Discovery. Hay **dos copias** en disco:

- `<homedir>/attachment/discovery/pandorafms.playwright.1/` — la que usa la consola para el formulario de la tarea.
- `<remote_config>/discovery/pandorafms.playwright.1/`, normalmente `/var/spool/pandora/data_in/discovery/pandorafms.playwright.1/` — **la copia que ejecuta el servidor de Discovery**.

Actualizar solo la primera copia deja silenciosamente el binario antiguo en ejecución en el servidor de Discovery.

Una tarea se crea en la consola como tarea de Discovery de la aplicación **Playwright** (`pandorafms.playwright.1`, `id_app = 10`):

1. Ve a **Discovery → Tasks → New task**, elige la aplicación Playwright y configura el nombre de la tarea, grupo, servidor e intervalo.
2. Recorre los pasos del asistente: **Basic setup** (worker mode, browser), **Worker setup** (solo para `remote`), **Test setup** (imagen, viewport, timeout, informe completo, prefijo de agentes, el propio test de Playwright, módulo de histórico de errores) y **Advanced setup** (debug mode, debug directory, advanced timeouts, eliminar contenedor existente).
3. Pega el `.ts` completo en el campo **Playwright test (.ts)**, elige el navegador y el modo de worker, y guarda.

<!-- SCREENSHOT NEEDED: PandoraFMS Discovery task wizard for the Playwright app (pandorafms.playwright.1): the four steps of the task form — Basic setup (Worker mode, Browser), Worker setup (SSH fields), Test setup (Docker image, viewport, Test timeout, full report, agent prefix, Playwright test .ts, error history module) and Advanced setup (Debug mode, Debug directory, Advanced timeouts, Remove existing container). Image goes at ../assets/images/discovery/playwright/task-wizard.png -->

En el momento de la ejecución, el servidor de Discovery invoca el plugin con el comando definido en `exec[]` de `discovery_definition.ini`, sustituyendo las macros de la tarea:

```
'_exec1_' -c '_tempfileConf_' -s '_tempfileTest_' -t __taskMD5__ -i __taskInterval__ -g __taskGroupID__
```

`_tempfileConf_` se expande al JSON de configuración de la tarea mostrado en [Parámetros](#parametros) y `_tempfileTest_` al contenido del fichero de test. `__taskMD5__` es `md5(id_rt)`.

## Agentes y módulos generados por el plugin

**Un agente por cada `test(...)` de Playwright.** El nombre del agente es `a + md5(<prefijo de agente> + <título completo>)`, donde el título completo es la ruta `describe > test` y el prefijo es el campo opcional `_prefixAgents_` (vacío por defecto). **No** depende de la tarea, así que borrar y recrear la tarea informa al mismo agente y conserva el histórico.

Esa independencia de la tarea tiene otra cara: **dos tareas que ejecutan un test con el mismo título informan al mismo agente**, alternando sus datos en los mismos módulos. Cuando eso no es lo que quieres — normalmente la misma transacción apuntando a dos entornos — da a cada tarea su propio `_prefixAgents_` (por ejemplo `prod-`, `dev-`) para separarlas en agentes distintos. Dejarlo vacío reproduce exactamente el nombrado original, así que una actualización nunca deja agentes existentes huérfanos.

| Módulo | Tipo | Origen | `extra_data` |
|--------|------|--------|--------------|
| `Global status` | `generic_proc` | resultado del test (`passed` → 1) | `wux:global_status:<test>` |
| `Global time` | `generic_data` (s) | duración del test | `wux:global_time:<test>` |
| `Phase <name> status` | `generic_proc` | cada `test.step` | `wux:phase_status:<n>:<test>` |
| `Phase <name> time` | `generic_data` (s) | duración de cada `test.step` | `wux:phase_time:<n>:<test>` |
| `Last error screenshot` | `generic_data_string` (imagen) | captura de pantalla en caso de fallo | `wux:error_screenshot:<test>` |
| `Global error` | `generic_data_string` | `OK` o el texto del error del test (con `_errorHistoryModule_` activo) | `wux:global_error:<test>` |
| `Phase <name> error` | `generic_data_string` | `OK` o el texto del error de la fase (con `_errorHistoryModule_` activo) | `wux:phase_error:<n>:<test>` |
| `<metric name>` | `generic_data` / `generic_data_string` | anotación `pandora.metric` | `pw:metric:<name>` |
| `Full report` | `async_string` | informe detallado derivado del JSON | `pw:full_report` |

Los módulos `wux:*` se muestran en la vista transaccional WUX de la consola. Los módulos `pw:*` son módulos de agente normales (métricas e informe completo).

## Extensión de consola

El plugin incluye una extensión de consola compañera, **WUX Transactions** (`wux_transactions_ext`), que registra una opción **"WUX Transactions"** en el menú de operación (en la sección que aloja las vistas de monitorización/estado) y renderiza la vista identificada por la cabecera "Monitoring → Views → WUX Transactions". Para abrirla el usuario necesita al menos uno de los ACL **AR** o **RR**; la extensión también aplica el ACL de grupo (AR sobre el grupo del módulo) a todo lo que lista.

La vista proporciona la capa de monitorización transaccional para los datos WUX:

- **Las transacciones se descubren desde el `extra_data` de los módulos.** La extensión lista todos los módulos cuyo `extra_data` empieza por `wux:global_status:` (el `extra_data` del propio agente WUX está vacío, así que los marcadores de módulo son la fuente de las transacciones). Un filtro de selección múltiple ("Select transactions") permite elegir una o más transacciones para comparar sus últimos datos de ejecución.
- **Tarjetas de resumen** que agregan las transacciones seleccionadas: contadores Selected / Passing / Failing / Unknown y el Average global time. Cuando varias tareas de Discovery informan a la misma transacción, se muestra un aviso de "Shared transactions" (solo para tareas con debug mode activado, que es lo único que la extensión puede detectar); la corrección recomendada es un `_prefixAgents_` distinto por tarea.
- **Paneles por transacción** con el estado/tiempo global, la tabla de fases (Phase, Status, Time, Updated, más acciones de gráfica/detalle de módulo), las métricas de tiempos WUX, las métricas personalizadas (valores `pw:metric` emitidos por el test) y el bloque de evidencia: **Last error screenshot** (cuando el módulo contiene un valor `data:image/...` válido) y el **Full WUX report** cuando `_fullReport_` está activo.
- **Evidencia de depuración de Playwright**: para las tareas de la aplicación `pandorafms.playwright.1` con Debug mode activado, la extensión lee el campo **Debug directory** de la tarea desde `tdiscovery_apps_tasks_macros` (macro `_debugDirectory_`), sustituye el placeholder `_taskid_` por `md5(id_rt)` exactamente igual que el runner, lee el `manifest.json` dejado por la última ejecución y lo indexa por nombre de agente. Un botón "Playwright debug" en el panel de la transacción abre un modal con un bloque por ejecución de tarea: etiqueta Passed/Failed, marca de tiempo de captura, **vídeo del fallo** (webm), **captura de pantalla del fallo** (png), **contexto de error** (markdown con la foto de la página en el fallo), el informe completo de la ejecución y el log de transacciones de la API de Playwright (`pw:api`). Los artefactos se sirven a través de un endpoint que solo sirve los tipos permitidos (screenshot/video/error-context), aplica el ACL de grupo y nunca se cachea.
- **Informe de ausencia de evidencia**: las tareas cuya evidencia no se puede leer se listan al principio de la vista con la tarea, su debug directory y el motivo — ver la tabla de cuatro motivos en [Si la consola no muestra evidencia](#si-la-consola-no-muestra-evidencia).

<!-- SCREENSHOT NEEDED: Console view Monitoring → Views → WUX Transactions: the transaction selector filter, the overview cards (Selected, Passing, Failing, Unknown, Average global time) and a transaction panel with the phases table, custom metrics and the Playwright debug evidence modal open. Image goes at ../assets/images/discovery/playwright/wux-transactions-view.png -->

## La imagen Docker

Cada tarea se ejecuta dentro de `pandorafms/pandora_playwright:noble`, el valor por defecto del campo **Docker image** (`_dockerImage_`). La forma recomendada de obtenerla es descargarla:

```bash
docker pull pandorafms/pandora_playwright:noble
```

Es una capa fina sobre la imagen oficial de Playwright de Microsoft, que ya incluye Chromium, Firefox y WebKit con todas sus librerías de sistema — la parte lenta y frágil de montar a mano.

### El contrato de la imagen

El runner genera la configuración completa de Playwright en cada ejecución y la escribe dentro del contenedor en marcha (ver [Depurar un test](#depurar-un-test)), así que la imagen depende de **una sola** cosa:

> `@playwright/test` instalado en `/pandora/node_modules`, en la misma versión que los navegadores de la imagen.

Todo lo demás es comodidad. Cualquier imagen que cumpla esa línea sirve como valor de `docker_image`.

### El Dockerfile

No lo necesitas para usar el plugin — descarga la imagen y listo. Está aquí para que puedas reconstruir la imagen tú mismo, auditar su contenido o usarla como punto de partida para una personalizada. Este es el `docker/Dockerfile` que se distribuye con el plugin:

```dockerfile
# Base image ships the browsers preinstalled (Chromium, Firefox, WebKit).
# Pin the Playwright version to the same tag the runner was validated against.
FROM mcr.microsoft.com/playwright:v1.62.0-noble

# @playwright/test must match the base image Playwright version.
ARG PLAYWRIGHT_VERSION=1.62.0

WORKDIR /pandora

RUN apt update && apt install -y vim

# Minimal project so `npx playwright test` resolves the runner locally.
RUN npm init -y >/dev/null 2>&1 \
    && npm install -D @playwright/test@${PLAYWRIGHT_VERSION}
```

```bash
docker build --pull -t pandorafms/pandora_playwright:noble -f Dockerfile .
```

| Paso | Por qué está ahí |
|------|------------------|
| `FROM mcr.microsoft.com/playwright:v1.62.0-noble` | Ubuntu 24.04 con los tres navegadores ya instalados. Fijada, nunca `:latest`: unos navegadores que se mueven bajo tus pies convierten una actualización sin relación en un incidente de monitorización |
| `ARG PLAYWRIGHT_VERSION=1.62.0` | Versión del **runner de tests** instalado abajo. Debe coincidir con la etiqueta de la imagen base — ver [Dos versiones que deben coincidir](#dos-versiones-que-deben-coincidir) |
| `WORKDIR /pandora` | Todas las rutas que usa el runner están bajo `/pandora`: el test, la configuración generada, `node_modules` |
| `apt install vim` | Solo por comodidad, para la [depuración interactiva manual](#depuracion-interactiva-manual). Nada del plugin lo necesita |
| `npm init -y` + `npm install -D @playwright/test` | El único paso que importa. Crea `/pandora/node_modules` para que `npx playwright test` resuelva el runner **localmente**, desde dentro del proyecto |

Dos cosas que el Dockerfile deliberadamente **no** hace:

- **No hay `COPY` de ninguna configuración de Playwright.** El runner escribe la suya en cada ejecución, así que una configuración horneada en la imagen nunca se leería.
- **No hay `ENTRYPOINT` ni `CMD`.** El contenedor no tiene lógica propia: el runner lo inicia con `docker run -d <image> sleep <ttl>` y lo controla todo desde fuera con `docker cp` y `docker exec`. Un entrypoint personalizado se saltaría en el mejor caso y rompería la ejecución en el peor.

### Construir tu propia imagen

Si tus tests necesitan algo extra, añade una capa **encima** de la imagen publicada en lugar de reescribir el Dockerfile — mantienes la fijación de versión y heredas las correcciones futuras:

```dockerfile
FROM pandorafms/pandora_playwright:noble

# Extra system packages your tests need (a font pack, a VPN client, a CA bundle...).
USER root
RUN apt-get update && apt-get install -y fonts-noto-cjk && rm -rf /var/lib/apt/lists/*

# Extra npm libraries your tests import, installed into the same project so
# `npx playwright test` resolves them: /pandora/node_modules.
WORKDIR /pandora
RUN npm install -D otplib          # e.g. tests that need a TOTP second factor
```

Constrúyela, hazla disponible en la máquina que ejecuta los tests — el servidor de Discovery para `worker_mode = local`, el destino SSH para `remote` — y apunta el campo **Docker image** de la tarea a ella:

```json
"docker_image": "mycompany/pandora_playwright:noble-corp"
```

Dos reglas para una imagen personalizada:

- **No muevas `WORKDIR` fuera de `/pandora`.** El runner escribe `task.spec.ts` y `playwright.config.task.ts` ahí por ruta absoluta y ejecuta `cd /pandora` antes de `npx playwright test`.
- **Instala los paquetes npm dentro de `/pandora`**, no globalmente. Node resuelve los imports de un test desde su propio árbol de proyecto.

### Dos versiones que deben coincidir

La etiqueta de la imagen base y `PLAYWRIGHT_VERSION` son el mismo número dos veces, y tienen que seguir siéndolo: los navegadores están horneados en la imagen base, y `@playwright/test` solo maneja la compilación del navegador con la que fue publicado. Cámbialo en **ambos** sitios a la vez:

```dockerfile
FROM mcr.microsoft.com/playwright:v1.63.0-noble
ARG PLAYWRIGHT_VERSION=1.63.0
```

Un desajuste no falla en el momento de construir. Falla en tiempo de ejecución, normalmente como un navegador que se niega a arrancar o un ejecutable que Playwright dice no encontrar:

```
browserType.launch: Executable doesn't exist at /ms-playwright/chromium-1234/chrome-linux/chrome
```

Subir la versión mueve el runtime con el que se validó todo el plugin, así que repite el flujo de [Pruebas / QA — paso a paso](#pruebas-qa-paso-a-paso) y actualiza la [Matriz de compatibilidad](#matriz-de-compatibilidad) con la versión que hayas probado.

## Tiempos de espera (timeouts)

Playwright tiene varios timeouts independientes. **Test timeout** (`_globalTimeout_`) es el que siempre aparece en el asistente, y **no** es el timeout por paso que la mayoría entiende por tal. Los tres de cada paso están desactivados por defecto y aparecen en **Advanced setup** una vez que se marca **Advanced timeouts** (`_advancedTimeouts_`); también se pueden fijar en el fichero de test, que siempre gana.

| Timeout | Qué acota | Dónde se configura | Valor en este plugin |
|---------|-----------|--------------------|----------------------|
| Por test | un `test(...)` completo, incluidos todos sus `test.step`, acciones y aserciones | campo de tarea **Test timeout** (`_globalTimeout_`) → `npx playwright test --timeout=<s × 1000>` | `120` s por defecto |
| De acción | cada acción individual: `click`, `fill`, `press`, `check`, `selectOption`... | campo de tarea **Action timeout** (`_actionTimeout_`), o el fichero de test | sin fijar → valor por defecto de Playwright `0` (sin límite) |
| De navegación | cada navegación: `goto`, `waitForURL`, `waitForNavigation`, `reload` | campo de tarea **Navigation timeout** (`_navigationTimeout_`), o el fichero de test | sin fijar → valor por defecto de Playwright `0` (sin límite) |
| De expect | cada aserción web-first: `expect(locator).toBeVisible()`, `toHaveText`... | campo de tarea **Expect timeout** (`_expectTimeout_`), o el fichero de test | sin fijar → valor por defecto de Playwright `5000` ms |
| TTL del contenedor | toda la ejecución dentro de Docker | derivado, no configurable | `min(3600, max(120, <Test timeout> × 20))` → `2400` s por defecto |
| Conexión SSH | la apertura de la sesión SSH (solo worker `remote`) | derivado, no configurable | `<Test timeout>` → `120` s por defecto |

Con **Advanced timeouts** desactivado, la configuración generada no declara ninguno de los tres, así que se aplican los valores por defecto de Playwright y hay exactamente un sitio — la tarea o tu test — del que puede venir un valor.

### Test timeout: por test, no por paso y no por tarea

El campo se corresponde directamente con `--timeout` de Playwright, que es el **presupuesto de un bloque `test(...)` completo**. Todos sus pasos, acciones y aserciones gastan del mismo presupuesto.

Cuando un test lo supera, Playwright aborta **solo ese test** y lo marca como `timedOut`: su módulo `Global status` informa `0` y la fase que estaba en curso se informa como fallida. **Los bloques `test(...)` restantes del fichero siguen ejecutándose y la tarea de Discovery no se mata.** El plugin no pasa `--global-timeout` ni fija timeout alguno en el proceso o el comando SSH que ejecuta, así que nada en él aborta una ejecución por tardar demasiado en total — con la única excepción del TTL del contenedor descrito abajo.

### Advanced timeouts: timeouts por paso desde la tarea

Marca **Advanced timeouts** en **Advanced setup** y aparecen los tres campos por paso, precargados con los valores por defecto de Playwright (`0`, `0`, `5` segundos). Dejarlos en esos valores no cambia nada.

Ninguno de los tres tiene flag de línea de comandos, y solo acción y navegación son opciones de `use`: `expect.timeout` vive en el nivel superior de la configuración y no se puede alcanzar desde un fichero de test. Así que, en lugar de reescribir tu test, los tres valores se añaden a la configuración generada — el fichero que el runner escribe en el contenedor en cada ejecución y que ya lleva el viewport y los ajustes de captura. Tu test no se toca, y cualquier cosa que declare sigue ganando.

### Timeouts por paso, fijados en el fichero de test

Los mismos tres timeouts se pueden fijar en el `.ts` que pegas en **Playwright test**, a nivel de fichero o por test. Esto anula los campos de la tarea, y es la única opción si necesitas un valor distinto por test en lugar de uno para toda la tarea.

A nivel de fichero (también válido dentro de un `test.describe`, pero **no** dentro de `beforeEach` o `beforeAll`):

```ts
import { test, expect as baseExpect } from '@playwright/test';

// Each action gets 5 s, each navigation 10 s
test.use({ actionTimeout: 5000, navigationTimeout: 10000 });

// Each web-first assertion gets 5 s
const expect = baseExpect.configure({ timeout: 5000 });

test('login', async ({ page }) => {
  await page.goto('https://example.com');       // 10 s
  await page.getByRole('button').click();       // 5 s
  await expect(page.getByText('Welcome')).toBeVisible(); // 5 s
});
```

Por llamada, cuando solo un paso necesita un límite distinto:

```ts
await page.goto('https://slow.example.com', { timeout: 60000 });
await page.getByRole('button').click({ timeout: 2000 });
await expect(page.getByText('Report ready')).toBeVisible({ timeout: 30000 });
```

### Precedencia: el test siempre gana sobre el campo de la tarea

Cuando al mismo test se le da un timeout en ambos sitios, **gana el fichero de test**. Playwright resuelve el timeout por test en este orden, de menor a mayor prioridad:

```
playwright.config.task.ts  <  --timeout (task field)  <  test.describe.configure({ timeout })  <  test.setTimeout()
```

El campo de la tarea es un *valor por defecto* que el runner pone en la línea de comandos, no un techo. Anula la configuración generada, y cualquier cosa que declare el test lo anula a su vez — por test, de modo que el resto del fichero conserva el valor de la tarea.

```ts
// Task field says 120. This one test gets 5 min; every other test still gets 120 s.
test('long transaction', async ({ page }) => {
  test.setTimeout(300000);
  // ...
});
```

Los timeouts de acción, navegación y expect se resuelven igual: **Advanced timeouts** los pone en una configuración, que es el nivel más débil, así que cualquier cosa que declare el test lo anula. En cualquier caso, **Test timeout** sigue acotándolos en tiempo de reloj — ver abajo.

**Pero el campo de la tarea es lo único que fija el TTL del contenedor.** El TTL se calcula en el runner, antes de que Docker arranque, solo a partir del campo de la tarea; ningún `test.setTimeout()` puede subirlo. Un test que se conceda más tiempo del que permite el TTL muere igualmente con el contenedor (`Playwright produced no report`). Así que `test.setTimeout()` es seguro para **bajar** el presupuesto de un test, o para subirlo dentro del margen que ya da el TTL; para ir más allá, sube **Test timeout** en la tarea — es la única entrada que mueve el TTL con ella.

### Conseguir que los timeouts por paso realmente se disparen

El presupuesto por test siempre gana. Si **Test timeout** es `120` y a un paso se le da `actionTimeout: 180000`, ese paso nunca llega a su propio límite: el test muere antes a los 120 s, y el fallo se informa como timeout del test en lugar de como el paso que se colgó. Para que los timeouts por paso sean el límite decisivo, el presupuesto por test debe ser mayor que la suma de los pasos que esperas — sube **Test timeout** en la tarea, o anúlalo para un test desde el fichero. Ten en cuenta que subir **Test timeout** también sube el TTL del contenedor y el timeout de conexión SSH, ya que ambos se derivan de él; `test.setTimeout()` no.

### TTL del contenedor — el único límite que aborta una ejecución completa

El runner inicia el contenedor del test como `docker run -d --rm --name <task container> <image> sleep <ttl>` y después ejecuta el test vía `docker exec`. El TTL se deriva de **Test timeout**:

```
ttl = min(3600, max(120, <Test timeout> × 20))
```

El recorte importa: el TTL solo sigue a **Test timeout** entre `6` s y `180` s. Por debajo siempre es `120` s, por encima siempre `3600` s. Con el `120` s por defecto eso son `2400` s (40 min). Si la duración **total** de una ejecución supera el TTL, el `sleep` termina, el contenedor se detiene y se lleva consigo el `docker exec` en curso: no se produce `report.json` y la tarea falla con `Playwright produced no report`. Esto es lo más parecido a un timeout de toda la tarea que tiene el plugin — si ejecutas varios tests largos en un fichero, dimensiona **Test timeout** para que `× 20` cubra todo el fichero, no solo el test más lento.

## Varios tests en un fichero

Un mismo `.ts` puede llevar varios bloques `test(...)`. El plugin trata cada uno como una transacción independiente: **un agente por cada `test(...)`**, cada uno con su `Global status/time`, fases, captura de pantalla y métricas. Todos se ejecutan dentro del mismo contenedor Docker, en una sola invocación de `npx playwright test`.

### Comportamiento por defecto: secuencial

El valor por defecto de Playwright es que **los ficheros de test se ejecutan en paralelo entre sí, pero los tests dentro de un mismo fichero se ejecutan uno tras otro en el mismo proceso worker**. Este plugin siempre ejecuta un único fichero (`task.spec.ts`), así que el paralelismo entre ficheros nunca aplica: tus tests arrancan en el orden en que están escritos y cada uno termina antes de que empiece el siguiente.

Consecuencias:

- El tiempo total de ejecución es la **suma** de la duración de cada test.
- Cada `test(...)` recibe un contexto de navegador/página nuevo, así que un test no puede filtrar estado al siguiente.
- Un test que falla **no** aborta a los demás: Playwright informa de cada test de forma independiente y el plugin construye cada agente a partir de su propio resultado.
- Con un `expect` fuerte, una aserción fallida aborta *ese* test — sus fases posteriores no se ejecutan, y cualquier anotación `pandora.metric` publicada después del fallo nunca se alcanza (publica las métricas según las vayas calculando). Usa `expect.soft()` para seguir midiendo las fases restantes.

### Ejecutarlos en paralelo a nivel de test

Si los tests son independientes, envuélvelos en `test.describe.parallel(...)` y Playwright los repartirá entre varios procesos worker dentro del contenedor:

```typescript
import { test, expect } from '@playwright/test';

test.describe.parallel('independent checks', () => {
  test('checkout flow', async ({ page }) => { /* ... */ });
  test('login flow', async ({ page }) => { /* ... */ });
});

test('always sequential', async ({ page }) => { /* ... */ });
```

`test.describe.configure({ mode: 'parallel' })` a nivel de fichero es la forma equivalente que aplica a todo el fichero. El valor por defecto es `mode: 'serial'`, así que solo tienes que optar por ello.

Advertencias:

- El número de workers por defecto de Playwright es **la mitad de los núcleos lógicos de CPU del contenedor**, y el plugin no lo anula (no se pasa `--workers`). Con un contenedor de un solo núcleo, el bloque paralelo sigue ejecutando un test a la vez; con dos o más núcleos, los tests se ejecutan realmente de forma concurrente.
- Cada test en paralelo ejecuta su propia instancia de navegador dentro del contenedor, así que la concurrencia sube el uso de CPU y memoria — dimensiona el contenedor y la carga sobre el sitio objetivo en consecuencia.
- Los tests en paralelo no deben compartir estado ni depender del orden de ejecución. Si alguno necesita ejecutarse estrictamente después de otro, mantenlo fuera del bloque paralelo o usa `test.describe.configure({ mode: 'serial' })` para ese grupo.

## Grabar una transacción

Una "transacción" es simplemente un test de Playwright estándar. Escribes Playwright puro — sin importar nada de PandoraFMS — y el plugin hace corresponder tres construcciones nativas:

| Tú escribes | Se convierte en |
|-------------|-----------------|
| `test.step('name', ...)` | una **fase** monitorizada (estado + tiempo) |
| `test.info().annotations.push({ type: 'pandora.metric', description: 'name=value' })` | un módulo de **métrica** personalizado |
| una aserción fallida | el test falla; se captura automáticamente una **captura de pantalla** |

Para obtener el código inicial del flujo, grábalo con cualquiera de estas herramientas.

### 1. Grabar con Playwright codegen

En cualquier máquina con Playwright instalado, lanza el grabador contra tu sitio (ver el [generador de tests de Playwright](https://playwright.dev/docs/codegen-intro)):

```bash
npx playwright codegen https://your-app.example.com
```

Recorre tu flujo en el navegador; Playwright escribe el código equivalente. Copia ese código como punto de partida.

### 2. Grabar con la extensión de Playwright para VS Code

Instala la extensión **Playwright Test for VS Code** de Microsoft ([Visual Studio Marketplace](https://marketplace.visualstudio.com/items?itemName=ms-playwright.playwright); requiere Playwright v1.38+ en tu proyecto). Abre el panel **Test Explorer** y usa las herramientas del grabador:

- **Record new**: abre una ventana de navegador donde navegas e interactúas con el sitio; el test generado se escribe en un fichero `.spec.ts` nuevo en tiempo real.
- **Record at cursor**: inserta las acciones recién grabadas en la posición actual del cursor dentro de un test existente.
- **Pick locator**: pasa el ratón sobre un elemento del navegador y haz clic para copiar su mejor localizador al portapapeles.

La extensión trabaja sobre un proyecto de Playwright, así que graba en cualquier proyecto desechable y copia el `.ts` resultante como punto de partida.

### 3. Grabar con la extensión de navegador de Playwright

Instala **Playwright CRX** desde el [Chrome Web Store](https://chromewebstore.google.com/detail/playwright-crx/jambeljnbnfbkcpnoiaedcabbgmnnlcd) (extensión comunitaria de ruifigueira). Incluye el mismo grabador que `playwright codegen` como extensión de navegador, así que puedes grabar directamente en tu propio Chrome/Chromium/Edge:

- Fija la pestaña actual con el botón de la extensión (o el menú contextual), o usa el panel lateral; `Alt + Shift + R` empieza a grabar y `Alt + Shift + C` empieza a inspeccionar.
- Realiza el flujo en la página; el grabador genera el código de Playwright, en el lenguaje seleccionado.
- Copia o exporta el script generado y úsalo como punto de partida.

### Estructurarlo en fases y añadir métricas

Sea cual sea la forma en que hayas grabado el flujo, envuelve cada parte significativa en `test.step(...)` para que se convierta en fase, y añade aserciones para validar de verdad el resultado:

```typescript
import { test, expect } from '@playwright/test';

test('checkout flow', async ({ page }) => {
  await test.step('open home', async () => {
    await page.goto('https://your-app.example.com');
    await expect(page).toHaveTitle(/Shop/);
  });

  await test.step('login', async () => {
    await page.fill('#user', 'demo');
    await page.fill('#password', 'demo');
    await page.click('#submit');
    await expect(page.locator('.dashboard')).toBeVisible();
  });

  await test.step('add to cart', async () => {
    await page.click('text=Add to cart');
    const count = await page.locator('.cart-count').innerText();
    // publish a custom metric module:
    test.info().annotations.push({ type: 'pandora.metric', description: `cart_items=${count}` });
  });
});
```

Solo las llamadas `test.step` de **primer nivel** del test se convierten en fases — el plugin lee el array `steps` de primer nivel del reporter JSON de Playwright, así que un paso anidado dentro de otro paso no se informa como fase independiente. Mantén los pasos planos (un nivel) para todo lo que quieras ver como fase independiente en la consola.

Las métricas se parsean de la anotación con estas reglas exactas (tomadas del runner):

- `type` debe ser exactamente el string literal `pandora.metric`; cualquier otro valor se ignora.
- `description` debe ser `name=value`, dividido solo por el **primer** `=` — así un valor que contenga `=` (por ejemplo, una query string de una URL) no se trunca.
- `name` y `value` se recortan de espacios en blanco alrededor. Si `description` no tiene `=`, o `name` queda vacío tras recortar, esa anotación se descarta silenciosamente.
- El tipo de módulo se infiere a partir del valor: si se puede parsear como número → `generic_data`; en cualquier otro caso → `generic_data_string`. El módulo se nombra exactamente como `name` y se etiqueta con `extra_data = pw:metric:<name>`.

### Pégalo en la tarea

Pega el `.ts` completo en el campo **Playwright test (.ts)** de la tarea de Discovery, elige el navegador y el modo de worker, y guarda.

### Consejos

- **Nombrado**: los nombres de módulo salen de los títulos de `test.step`, así que mantenlos descriptivos (`'login'`, `'add to cart'`). Renombrar un test crea un agente nuevo.
- **Continuar tras un fallo**: con un `expect` normal, una fase fallida aborta el test y las fases posteriores no se ejecutan. Si quieres que se mida cada fase aunque una falle, usa aserciones suaves: `await expect.soft(locator).toHaveText('x')`.
- **Varias transacciones**: varios bloques `test(...)` en un mismo `.ts` generan varios agentes.
- **El código grabado es un punto de partida, no el entregable**: un grabador escribe acciones literales pero no tiene forma de saber qué agrupación de elementos es única, si un texto de badge/estado se repite en otro lugar de la página, o si el texto real del DOM coincide con lo que el CSS hace que *parezca* (p. ej. `text-transform: uppercase`). Revisa los localizadores grabados contra la página en vivo antes de conectarlo a una tarea de Discovery.

## Certificados autofirmados

Por defecto Playwright valida los certificados TLS como lo haría un navegador real, así que un destino con un certificado autofirmado o emitido internamente hace que cualquier `page.goto(...)` falle con `net::ERR_CERT_AUTHORITY_INVALID` antes incluso de que se ejecute la lógica del test.

No existe un interruptor a nivel de plugin para esto — se configura explícitamente en la transacción con el propio `test.use()` de Playwright:

```typescript
import { test, expect } from '@playwright/test';

test.use({ ignoreHTTPSErrors: true });

test('checkout flow', async ({ page }) => {
  await page.goto('https://internal.example.com');
  // ...
});
```

- `test.use({ ignoreHTTPSErrors: true })` colocado en el nivel superior del fichero se aplica a todos los `test(...)` que vengan después en esa transacción.
- Para limitarlo a solo algunos tests del mismo fichero, agrúpalos en su propio bloque `test.describe(...)` y llama a `test.use({ ignoreHTTPSErrors: true })` como primera línea dentro de ese bloque, en lugar de en el nivel superior.
- Esto solo desactiva la **validación del certificado**, no el TLS en sí — la conexión sigue cifrada, simplemente ya no exige una cadena de confianza CA válida.

## Generar una transacción con un agente de IA

En lugar de escribir a mano la transacción `.ts` (o grabarla una vez y confiar en que los selectores aguanten), puedes hacer que un agente de código local — Claude Code, opencode, `pi` o similar — conduzca un navegador real a través del flujo y escriba la transacción por ti, validando cada localizador contra el objetivo real antes de entregarla.

Esto funciona porque estos agentes pueden usar una **skill de CLI/automatización de navegador de Playwright** (una herramienta que abre un navegador real, hace clic, rellena y lee el DOM bajo control del agente) para ejecutar realmente el flujo paso a paso, no solo adivinar selectores a partir de una captura. Un grabador registra acciones literales pero no tiene forma de saber qué agrupación de elementos es única, si un texto de badge/estado se repite en otro lugar, o si el texto real del DOM coincide con lo que el CSS hace que *parezca*; un agente que pueda re-ejecutar cada localizador contra la página en vivo, ver una violación de modo estricto y corregir el alcance antes de entregar el fichero detecta exactamente la clase de fallo que vuelve inestable una transacción en producción.

### Plantilla de prompt

```
Validate [FLOW NAME] on [URL] and write it as a Playwright transaction for the
pandorafms.playwright.1 plugin.

What the transaction should check:
- [step 1, e.g. "open the page and confirm the title"]
- [step 2, e.g. "log in and confirm the dashboard loads"]
- [step 3, e.g. "read a value and publish it as a pandora.metric"]

Deliverable:
- Plain Playwright: wrap each meaningful step in `test.step('name', ...)` so it
  becomes a WUX phase, and use
  `test.info().annotations.push({ type: 'pandora.metric', description: 'name=value' })`
  for anything that should become a custom metric module.
- No PandoraFMS import, no DSL — this plugin harvests everything from
  Playwright's own JSON reporter.
- Validate every locator against the real target yourself (drive the browser,
  don't just infer from a snapshot) before handing me the file — fix anything
  ambiguous or strict-mode-violating first.
- If a later step depends on a hard assertion in an earlier step, tell me
  whether to keep it that way or switch to `expect.soft()` so every phase gets
  measured even when one fails.
```

### Después de recibir el fichero

Ejecútalo con el flujo local del propio plugin antes de conectarlo a una tarea de Discovery — ver [Pruebas / QA — paso a paso](#pruebas-qa-paso-a-paso) más abajo — para ver la salida real de agente/módulo, no solo "el test ha pasado".

## Pruebas / QA — paso a paso

Este es el flujo utilizado para validar el plugin de extremo a extremo. Incluye los ejemplos listos para usar referenciados en [Ejecución manual](#ejecucion-manual).

### 1. Un test y una configuración de ejemplo

`sample.spec.ts`:

```typescript
import { test, expect } from '@playwright/test';

test('passing check', async ({ page }) => {
  await test.step('open', async () => { await page.setContent('<h1 id=t>Hello</h1>'); });
  await test.step('assert', async () => { await expect(page.locator('#t')).toHaveText('Hello'); });
  test.info().annotations.push({ type: 'pandora.metric', description: 'items=3' });
});

test('failing check', async ({ page }) => {
  await test.step('render', async () => { await page.setContent('<h1 id=t>Hello</h1>'); });
  await test.step('bad assert', async () => { await expect(page.locator('#t')).toHaveText('Goodbye', { timeout: 1500 }); });
});
```

`conf.json`:

```json
{ "worker_mode": "local", "browser": "chromium",
  "docker_image": "pandorafms/pandora_playwright:noble",
  "global_timeout": "15", "full_report": "1", "report_agent": "" }
```

### 2. Ejecución local (inspecciona los datos de monitorización)

```bash
./venv/bin/python pandora_playwright.py -c conf.json -s sample.spec.ts -t qa-test -g 0 -v
```

El STDERR muestra la traza paso a paso; el STDOUT es el JSON de Discovery. Espera dos agentes (`Playwright - passing check`, `Playwright - failing check`), cada uno con `Global status/time`, módulos por fase, una captura de pantalla de error (un valor `data:image/png;base64,...` en el que falla, `None` en el que pasa), la métrica `items` y un módulo `Full report`. Checklist: test que pasa → `Global status = 1`; test que falla → `Global status = 0`; cada `test.step` produce `Phase <name> status/time`; el `Last error screenshot` del test que falla empieza por `data:image/png;base64,`; sin contenedores sobrantes (`docker ps -a` limpio).

### 3. Ejecución remota (SSH)

Apunta la configuración a un host SSH que tenga Docker y la imagen:

```json
{ "worker_mode": "remote", "browser": "chromium",
  "ssh_address": "10.0.0.5", "ssh_port": "22", "ssh_user": "root",
  "ssh_password": "secret", "ssh_password_encrypt": "0", "ssh_temp_folder": "/tmp",
  "docker_image": "pandorafms/pandora_playwright:noble",
  "global_timeout": "15", "full_report": "1" }
```

```bash
./venv/bin/python pandora_playwright.py -c conf_remote.json -s sample.spec.ts -t qa-remote -g 0 -v
```

La salida verbose es idéntica a la local pero con el prefijo `ssh$` y las líneas extra `Connecting SSH` / `SSH authenticated` / `SCP` / limpieza del temporal remoto.

### 4. De extremo a extremo contra un Pandora real (renderizado en consola)

Ejecuta contra el Tentacle de un servidor Pandora para crear agentes/módulos reales:

```bash
./venv/bin/python pandora_playwright.py -x -S 127.0.0.1:41121 \
    -c conf.json -s sample.spec.ts -t qa-console -g 13 -T /tmp
```

Después verifícalo en la base de datos (la vista WUX de la consola se basa en `extra_data`):

```sql
-- transactions found by the console:
SELECT id_agente_modulo, nombre, extra_data FROM tagente_modulo
WHERE extra_data LIKE 'wux:global_status:%' AND parent_module_id = 0;

-- phases of a transaction share the agent:
SELECT nombre, extra_data FROM tagente_modulo
WHERE extra_data LIKE 'wux:phase_status:%';
```

Por último, abre el agente en la consola y confirma que la **vista transaccional WUX** muestra las fases y que `Last error screenshot` se renderiza como imagen.

## Depurar un test

Cuando una transacción falla y la captura de pantalla / el `Full report` del plugin no bastan para ver qué ha pasado, hay dos formas de obtener evidencia más rica: dejar que la propia tarea la capture automáticamente (**Debug mode**), o entrar en la imagen de forma interactiva y navegar por el informe HTML propio de Playwright. Ambas usan los mismos ajustes de captura — `trace: 'on-first-retry'`, `screenshot: 'only-on-failure'`, `video: 'retain-on-failure'` — pero los obtienen de sitios distintos: una ejecución de tarea desde la configuración generada, una ejecución manual desde una configuración que escribes tú dentro del contenedor (la imagen no incluye ninguna).

### Debug mode (automatizado, por ejecución de tarea)

Activa **Debug mode** en el **Advanced setup** de la tarea y configura un **Debug directory** (por defecto `/var/spool/pandora/data_in/discovery/tmp/playwright/_taskid_`, con `_taskid_` sustituido automáticamente por `md5(id_rt)`; una ruta absoluta personalizada también funciona). La salida de depuración siempre acaba **centralizada en el servidor de Discovery**, en esa misma ruta, independientemente del `worker_mode`:

1. El runner vacía y recrea el directorio de depuración en el host Docker (el propio servidor de Discovery para `worker_mode = local`, o el worker SSH para `remote`), hace `chmod 777` para que el contenedor pueda escribir en él independientemente de su usuario interno, y lo monta en el contenedor en `/pandora/debug`.
2. El test se ejecuta con la configuración generada, que lleva los ajustes de captura de depuración, y con `--output` redirigido a ese montaje, de modo que las capturas, el trace y el vídeo caen directamente en `<debug_directory>/test-results/<test>/` de ese host.
3. El runner escribe un `report.md` de resumen (estado, fases, errores) en el mismo directorio.
4. Solo para `worker_mode = remote`: el runner descarga el directorio de depuración completo desde el worker remoto de vuelta al servidor de Discovery (por la misma sesión SSH, en la misma ruta absoluta) y después elimina la copia remota — pero solo una vez confirmada la copia local en disco. Si la descarga falla, la copia remota se deja en su sitio en lugar de borrarse.
5. Por último, el runner escribe `manifest.json` en el directorio, mapeando cada agente informado por esta ejecución a sus propios artefactos.

El directorio contiene los artefactos de **una sola ejecución** — se vacía, no se acumula, en cada ejecución, así que solo se conserva la última. Está pensado para que lo lea más tarde otra herramienta (por ejemplo, la extensión de consola), no para navegarlo en vivo — para la depuración interactiva con un informe HTML servido, usa el flujo manual de abajo.

### manifest.json: cómo relacionar los agentes con su evidencia

Un agente producido por este plugin se nombra `a + md5(<título del test>)` — la tarea no participa en ese nombre (recrear la tarea conserva el agente y su histórico). La relación entre tareas y agentes es genuinamente N:M: una tarea produce muchos agentes, y un agente puede venir de muchas tareas. `manifest.json` resuelve ese vínculo desde el lado que puede poseerlo: el directorio de depuración de cada tarea declara qué agentes produjo *esa* ejecución, de modo que un consumidor puede indexar todos los manifiestos por nombre de agente y obtener un mapeo exacto, sin tener que adivinar a partir de los slugs de los directorios de salida de Playwright.

```json
{
  "task_id": "<md5(id_rt)>",
  "generated": "2026-08-11T15:53:39.264478",
  "worker_mode": "local",
  "browser": "chromium",
  "report": "report.md",
  "tests": [
    {
      "title": "failing check",
      "agent_name": "a9e960014d5185274a2d527b6f457ee96",
      "status": "failed",
      "passed": false,
      "duration_ms": 1654,
      "error": "Error: expect(locator).toHaveText(expected) failed…",
      "artifacts": {
        "screenshot": "test-results/task-failing-check-chromium/test-failed-1.png",
        "video": "test-results/task-failing-check-chromium/video.webm",
        "error-context": "test-results/task-failing-check-chromium/error-context.md"
      }
    }
  ]
}
```

Notas para consumidores:

- Las rutas de `artifacts` son **relativas al directorio de depuración** y solo cubren los ficheros que Playwright escribió dentro de él; un test que pasa normalmente no tiene ninguno, ya que Playwright solo captura captura/vídeo en caso de fallo.
- Las rutas de artefactos vienen del propio reporter JSON de Playwright, no de escanear directorios, así que siguen siendo correctas sin importar cómo convierta Playwright los títulos de test en nombres de carpeta.
- El manifiesto se escribe **después** de la descarga remota, así que para tareas `remote` describe ficheros que ya están en local. Un manifiesto ausente significa que la ejecución no capturó nada (falló la orquestación, o una descarga remota que no cuajó).
- La extensión WUX Transactions de la consola consume exactamente este fichero para ofrecer evidencia de depuración por transacción.

### Si la consola no muestra evidencia

La extensión lee el campo **Debug directory** de cada tarea — no hay ninguna ruta que configurar en su lado — y lista, al principio de la vista, toda tarea con debug activado cuya evidencia no haya podido leer, con el motivo:

| Motivo | Causa |
|--------|-------|
| No absolute debug directory is set | Debug activado con una ruta vacía o relativa. La ejecución también aborta, ya que el runner la valida |
| Directory does not exist on this console | O la tarea aún no se ha ejecutado, o consola y servidor de Discovery están en **hosts distintos** — la ruta solo es válida en el servidor. Comparte `data_in` por NFS o sincronízalo |
| Directory exists but holds no `manifest.json` | Se está ejecutando un **build antiguo del plugin** (ver la nota de las dos copias en [Configuración en PandoraFMS](#configuracion-en-pandorafms)), la ejecución falló antes de capturar nada, o falló una descarga `remote` — en cuyo caso la evidencia sigue en el worker |
| Manifest unreadable or malformed | Permisos, o una ejecución interrumpida a mitad de escritura |

### El placeholder `_taskid_`

Es una convención específica del plugin, no una característica de Discovery. Las macros propias de Discovery (`__taskMD5__`, `__taskGroupID__`, ...) solo se sustituyen en el lado del servidor, en Perl, en el momento de la ejecución, así que el valor por defecto de un campo llega al plugin literalmente; es el propio plugin, en Python, el que sustituye `_taskid_` por `md5(id_rt)` — el mismo valor que Discovery calcula como `__taskMD5__` — después de que el valor ya haya llegado dentro del JSON de configuración de la tarea. Cualquier otra cosa con acceso al `id_rt` de la tarea puede recalcular el mismo valor y aterrizar en el mismo nombre de directorio. La única excepción es una ejecución manual por CLI (`-t <task_name>` con un nombre legible): el plugin hace hash de ese nombre, ya que `-t` se convierte en el nombre del contenedor Docker.

### Depuración interactiva manual

**1. Inicia el contenedor**, montando tu test `.ts` directamente si ya lo tienes:

```bash
docker run -it --rm \
  -v "$(pwd)/test.spec.ts:/pandora/test.spec.ts" \
  -p 9323:9323 \
  pandorafms/pandora_playwright:noble bash
```

O inícialo sin montar nada y escribe el test dentro del contenedor (por ejemplo con `vim`, ya instalado en la imagen).

**2. Escribe una configuración de depuración.** La imagen no incluye ninguna configuración de Playwright — una ejecución de tarea genera la suya y la desecha con el contenedor. Para una ejecución manual, escribe una tú mismo dentro de `/pandora`. `video` y `reporter` no tienen flag de línea de comandos, así que una configuración es la única forma de obtenerlos:

```bash
cat > playwright.config.debug.ts <<'EOF'
import { defineConfig } from '@playwright/test';

export default defineConfig({
  reporter: [
    ['html', { host: '0.0.0.0', port: 9323, open: 'never' }],
    ['list'],
  ],
  use: {
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
});
EOF
```

Estos son los mismos ajustes de captura que **Debug mode** pone en la configuración generada, más el reporter HTML, que una ejecución de tarea nunca usa porque el runner siempre pasa `--reporter=json`.

**3. Ejecuta el test con ella:**

```bash
npx playwright test test.spec.ts --config=playwright.config.debug.ts --browser=chromium --timeout=30000
```

**4. Sirve y visualiza el informe:**

```bash
npx playwright show-report --host 0.0.0.0 --port 9323
```

Con `-p 9323:9323` publicado en `docker run`, abre `http://localhost:9323` en el host para revisar el informe: resultados por step, el visor de trazas y el **vídeo del fallo**.

## Solución de problemas

- **`docker: ... name is already in use`** — una ejecución anterior se interrumpió antes de su limpieza (p. ej. el runner recibió un SIGKILL) y dejó el contenedor que posee el nombre derivado de esta tarea; su `sleep` puede retener el nombre hasta 30 minutos. El contenedor siempre se inicia con `--rm`, así que un huérfano libera el nombre por sí solo cuando termina el `sleep`. Para recuperarlo de inmediato, elimínalo (`docker rm -f <md5(task name)>`) o activa **Remove existing container with the same task name** en el Advanced setup de la tarea para que el runner lo haga antes de cada ejecución.
- **"Playwright produced no report"** — el test no llegó a ejecutarse (error de sintaxis, import incorrecto, navegador ausente) o la ejecución superó el TTL del contenedor. Ejecuta con `-v` y revisa el stderr de `docker exec`; ver [TTL del contenedor](#ttl-del-contenedor-el-unico-limite-que-aborta-una-ejecucion-completa).
- **La captura de pantalla se muestra como texto, no como imagen** — el valor debe ser `generic_data_string` con el prefijo `data:image/png;base64,` (lo gestiona el plugin); comprueba que el build del plugin lo incluye.
- **`Cannot find module '@playwright/test'`** — el test debe ejecutarse desde `/pandora` dentro de la imagen para que Node resuelva `node_modules`; por eso el plugin lo copia a `/pandora/task.spec.ts`.
- **Los agentes caen en el grupo equivocado (xml_mode)** — el XML de agente de Pandora espera el **nombre** del grupo, no el id numérico. La ruta `monitoring_data` de Discovery sí usa correctamente el `id_group` numérico.
- **Una fase posterior sigue mostrando "ok" tras un fallo anterior** — con aserciones fuertes, una fase fallida aborta la ejecución, así que las fases posteriores conservan su valor anterior. Usa `expect.soft()` si quieres que se mida cada fase en cada ejecución.
- **El formulario de tarea de la consola sigue ejecutando un build antiguo** — recuerda la nota de las dos copias en [Configuración en PandoraFMS](#configuracion-en-pandorafms): actualiza la copia de `<remote_config>/discovery/`, no solo el attachment de la consola.
- **`net::ERR_CERT_AUTHORITY_INVALID`** — ver [Certificados autofirmados](#certificados-autofirmados).