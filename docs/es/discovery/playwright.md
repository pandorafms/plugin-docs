# Playwright

## Introducción

**Ver**. 02-08-2026

Este documento describe la funcionalidad del plugin de Discovery de Playwright (`pandorafms.playwright.1`) y su integración con PandoraFMS. El plugin ejecuta un test `.ts` de Playwright proporcionado por el cliente dentro de un contenedor Docker preconfigurado, convirtiendo el resultado en módulos de monitorización transaccional que se integran con la vista transaccional WUX de la consola (estado/tiempo global, estado/tiempo por fase, captura de pantalla de error, métricas personalizadas y un módulo opcional de histórico de errores).

Es el equivalente en Playwright de `pandorafms.selenium.4`, pero construido en torno al modelo de ejecución nativo de Playwright: el cliente escribe código Playwright estándar — sin librería propia que importar, sin DSL que aprender — y el plugin obtiene todo directamente del reporter JSON nativo de Playwright.

**Tipo**: plugin de Discovery (`.disco`)

## Matriz de compatibilidad

| **Sistemas donde se ha probado** | Rocky Linux 9/10 (servidor Pandora), imagen Docker `pandorafms/pandora_playwright:noble` (Ubuntu Noble) |
| --- | --- |
| **Sistemas donde funciona** | Cualquier sistema que pueda ejecutar Docker como servidor local, o alcanzar por SSH un host remoto que pueda ejecutar Docker |

## Prerrequisitos

**1. Docker**La máquina que ejecuta el test debe tener Docker disponible: el propio servidor Discovery/Pandora para `worker_mode = local`, o el destino SSH para `worker_mode = remote`.

**2. La imagen Docker de Playwright**`pandorafms/pandora_playwright:noble` debe estar disponible en la máquina que ejecuta el test (con los navegadores preinstalados).

`docker pull pandorafms/pandora_playwright:noble` una vez publicada.

**3. Acceso SSH (solo worker remoto)**Para `worker_mode = remote`, un usuario SSH capaz de ejecutar Docker en el host de destino, además de una carpeta temporal con permisos de escritura para ese usuario (por defecto `/tmp`) donde depositar el fichero del test.

**4. Tentacle (opcional, uso CLI/independiente)**Si se invoca el plugin fuera del pipeline de tareas de Discovery con `--xml_mode`, se necesita un `tentacle_serverd` accesible para recibir el XML del agente generado.

## Parámetros

**Parámetros del asistente de tareas de Discovery**

| **Campo** | **Macro** | **Notas** | **Por defecto** |
| --- | --- | --- | --- |
| Worker mode | `_workerMode_` | `local` o `remote`. `remote` ejecuta Docker en un host SSH. | `local` |
| Browser | `_browser_` | `chromium`, `firefox`, `webkit` | `chromium` |
| SSH address | `_sshAddress_` | Host que ejecuta Docker (solo remoto) | — |
| SSH port | `_sshPort_` | — | `22` |
| SSH user | `_sshUser_` | Debe poder ejecutar Docker | `root` |
| SSH password | `_sshPassword_` | Se puede cifrar con `password_encrypter.py` | — |
| Encrypt password | `_sshPasswordEncrypt_` | Ofusca la contraseña en la configuración de la tarea | on |
| Temporal folder | `_sshTemp_` | Dónde se copia el fichero del test en el host remoto | `/tmp` |
| Docker image | `_dockerImage_` | — | `pandorafms/pandora_playwright:noble` |
| Browser width | `_browserWidth_` | — | `1920` |
| Browser height | `_browserHeight_` | — | `1080` |
| Test timeout | `_globalTimeout_` | Timeout por test, en **segundos** | `30` |
| Send full report | `_fullReport_` | Añade un módulo con el informe de texto detallado | off |
| Report agent name | `_reportAgent_` | Agente que contiene el informe completo; vacío = agente del primer test | — |
| Generate error history module | `_errorHistoryModule_` | Añade un módulo de cadena síncrono por estado/fase (`OK` o el texto del error), para que Pandora mantenga un histórico real de errores | off |
| Playwright test (.ts) | `_playwrightTest_` | El contenido completo del fichero de test | — |

**Configuración de la tarea (JSON que recibe el runner)**

```json
{
  "worker_mode": "local",
  "browser": "chromium",
  "ssh_address": "", "ssh_port": "22", "ssh_user": "root",
  "ssh_password": "", "ssh_password_encrypt": "0", "ssh_temp_folder": "/tmp",
  "docker_image": "pandorafms/pandora_playwright:noble",
  "browser_width": "1920", "browser_height": "1080",
  "global_timeout": "30",
  "full_report": "0",
  "report_agent": "",
  "error_history_module": "0"
}

```

**Parámetros CLI (ejecución manual / independiente)**

| **Corto** | **Largo** | **Obligatorio** | **Por defecto** | **Descripción** |
| --- | --- | --- | --- | --- |
| `-c` | `--conf` | sí | — | Ruta al JSON de configuración de la tarea |
| `-s` | `--test` | sí | — | Ruta al fichero de test `.ts` de Playwright |
| `-t` | `--task` | sí | — | Nombre de la tarea (se usa para derivar el nombre del contenedor) |
| `-i` | `--interval` | no | `300` | Intervalo del agente (segundos) |
| `-g` | `--group` | no | `0` | Id de grupo para los agentes creados |
| `-x` | `--xml_mode` | no | off | Genera el XML del agente y lo envía por Tentacle (modo independiente) |
| `-S` | `--server` | no | `127.0.0.1:41121` | `server:port` de Tentacle (con `-x`) |
| `-T` | `--temp` | no | `/tmp` | Carpeta temporal para el XML (con `-x`) |
| `-v` | `--verbose` | no | off | Traza paso a paso por STDERR |

`password_encrypter -e -p <password>` cifra una contraseña; `-d` la descifra (lo usa la consola para el campo de contraseña SSH).

## Ejecución manual

### Formato de ejecución

```
pandora_playwright -c <conf.json> -s <test.ts> -t <task_name> \
  [-i <interval>] [-g <group_id>] \
  [-x [-S <server:port>] [-T <temp_folder>]] \
  [-v]

```

- Sin `-x`, el plugin imprime el JSON de Discovery por STDOUT (modo nativo de tarea Discovery).
- Con `-x`, genera el XML del agente y lo envía directamente por Tentacle (modo independiente/manual).

#### Ejemplos

Modo nativo (JSON por STDOUT, como lo ejecutaría una tarea Discovery):

```bash
pandora_playwright -c conf.json -s task.spec.ts -t qa-test -g 0 -v

```

Modo independiente contra un servidor Pandora real (crea agentes/módulos reales vía Tentacle):

```bash
pandora_playwright -x -S 127.0.0.1:41121 \
    -c conf.json -s task.spec.ts -t qa-console -g 2 -T /tmp

```

Worker remoto (Docker se ejecuta por SSH; `worker_mode=remote` en `conf.json`):

```bash
pandora_playwright -c conf_remote.json -s task.spec.ts -t qa-remote -g 0 -v

```

#### Modo verbose

`-v` imprime una traza paso a paso con marca de tiempo por STDERR — útil para ejecuciones manuales. Registra literalmente cada comando Docker/SSH (`$` local, `ssh$` remoto), el resumen de configuración, el tamaño del informe, la captura de pantalla, la construcción de cada agente y el resumen de envío:

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

El plugin se distribuye como un paquete de Discovery `.disco`. Para configurarlo:

**1. Instala el paquete `.disco`**, si no está ya instalado: ve a **Discovery → Extension manager** y sube el paquete (o confirma que ya aparece en la lista).

**2. Crea una nueva tarea de Discovery**: ve a **Discovery → Applications → Playwright**.

**3. Completa los pasos del asistente** (ver [Parámetros](#parametros) más arriba):

- *Basic setup*: modo de worker y navegador.
- *Worker setup*: solo se muestra cuando el modo de worker es `remote` — datos de conexión SSH.
- *Test setup*: imagen Docker, tamaño de navegador, timeout, `Send full report`, `Generate error history module`, y el propio contenido del test `.ts` de Playwright.

**4. Guarda la tarea.** En cada ejecución, el plugin corre el test en Docker e informa de un agente por cada `test(...)` de Playwright encontrado en el fichero.

**5. Abre el/los agente(s) resultante(s)** en la consola. La **vista transaccional WUX** muestra las fases derivadas de `test.step(...)`; las vistas de módulo estándar muestran estado, tiempo, captura de pantalla del error, métricas y (si está activado) los módulos de histórico de errores.

## Agente y módulos generados por el plugin

**Un agente por cada `test(...)` de Playwright.**

| **Nombre del módulo** | **Tipo** | **Descripción** | **`extra_data`** |
| --- | --- | --- | --- |
| `Global status` | `generic_proc` | Resultado global del test: 1 si `passed`, 0 en caso contrario | `wux:global_status:<test>` |
| `Global time` | `generic_data` | Duración total del test, en segundos | `wux:global_time:<test>` |
| `Phase <name> status` | `generic_proc` | Resultado de cada `test.step`: 1 si no tuvo error, 0 en caso contrario | `wux:phase_status:<n>:<test>` |
| `Phase <name> time` | `generic_data` | Duración de cada `test.step`, en segundos | `wux:phase_time:<n>:<test>` |
| `Last error screenshot` | `generic_data_string` | Captura de pantalla en caso de fallo, como valor `data:image/png;base64,...` (se renderiza como imagen en la consola) | `wux:error_screenshot:<test>` |
| `Global error` | `generic_data_string` | Solo cuando `_errorHistoryModule_` está activo. `OK` cuando el test pasa, o el texto del error cuando falla — un módulo síncrono, para que Pandora mantenga una serie histórica real de valores (no solo la descripción del módulo de estado, que se sobrescribe en cada ejecución) | `wux:global_error:<test>` |
| `Phase <name> error` | `generic_data_string` | Solo cuando `_errorHistoryModule_` está activo. `OK` o el texto del error de la fase, misma lógica de histórico que `Global error` | `wux:phase_error:<n>:<test>` |
| `metric name` | `generic_data` / `generic_data_string` | A partir de una anotación `pandora.metric` (`name=value`, dividido por el primer `=`); los valores numéricos se convierten en `generic_data`, el resto en `generic_data_string` | `pw:metric:<name>` |
| `Full report` | `async_string` | Solo cuando `_fullReport_` está activo. Informe de texto detallado derivado del reporter JSON (estado, pasos, stdout/stderr, anotaciones, adjuntos) | `pw:full_report` |

Los módulos `wux:*` se muestran en la vista transaccional WUX de la consola. Los módulos `pw:*` son módulos de agente normales (métricas e informe completo).

## Grabar una transacción

Una "transacción" es un test de Playwright estándar — no requiere importar nada de PandoraFMS. Tres construcciones nativas se corresponden con el comportamiento del plugin:

| Tú escribes | Se convierte en |
| --- | --- |
| `test.step('name', ...)` | una **fase** monitorizada (estado + tiempo) |
| `test.info().annotations.push({ type: 'pandora.metric', description: 'name=value' })` | un módulo de **métrica** personalizado |
| una aserción fallida | el test falla; se captura automáticamente una **captura de pantalla** |

### 1. Graba el flujo con el grabador de Playwright (`codegen`)

Playwright incluye su propio grabador, `codegen`: abre un navegador real, y cada clic, relleno de campo y navegación que realices se convierte en código Playwright en tiempo real, además de un modo Pick Locator / Explore para probar selectores contra la página en vivo. Documentación oficial: **[playwright.dev/docs/codegen-intro](https://playwright.dev/docs/codegen-intro)**. Referencia general de escritura de tests: **[playwright.dev/docs/writing-tests](https://playwright.dev/docs/writing-tests)**.

En cualquier máquina con Node y Playwright instalados (no tiene por qué ser la imagen Docker del plugin):

```bash
npm init playwright@latest    # solo la primera vez, si el proyecto aún no está configurado
npx playwright codegen https://your-app.example.com

```

Se abren dos ventanas: el navegador con el que interactúas, y el **Playwright Inspector**, que muestra el código generado en vivo y te permite elegir/copiar un localizador para cualquier elemento de la página. Flags útiles:

- `--browser=firefox` / `--browser=webkit` — graba contra un motor concreto (coincide con el ajuste `_browser_` del plugin).
- `--viewport-size=1920,1080` — graba a la misma resolución con la que correrá el plugin (coincide con `_browserWidth_`/`_browserHeight_`).
- `--save-storage=state.json` — captura cookies/localStorage tras un login interactivo, para usarlas como base en grabaciones autenticadas posteriores con `--load-storage=state.json` (ver [Authentication](https://playwright.dev/docs/auth) en la documentación oficial si el flujo necesita una sesión persistida).

La salida de `codegen` es **código plano, sin agrupar** — clics y aserciones uno detrás de otro, sin `test.step(...)` ni anotaciones de métricas. Es un punto de partida, no la transacción final: cópialo en tu fichero `.ts` y pasa al paso 2.

### 2. Conviértelo en fases

Envuelve cada parte significativa del flujo grabado en `test.step('name', async () => { ... })`. Cada llamada a `test.step` de **primer nivel** — escrita directamente dentro del callback de `test(...)` — se convierte en una fase, con su propio módulo `Phase <name> status` y `Phase <name> time` (ver [Agente y módulos generados por el plugin](#agente-y-modulos-generados-por-el-plugin)). Referencia oficial: **[test.step() API](https://playwright.dev/docs/api/class-test#test-step)**.

```typescript
await test.step('open home', async () => {
  await page.goto('https://your-app.example.com');
  await expect(page).toHaveTitle(/Shop/);
});

```

Cosas a tener en cuenta:

- **Solo los steps de primer nivel se convierten en fases.** Un `test.step(...)` anidado *dentro* de otro `test.step(...)` no se reporta como una fase independiente — el plugin solo lee el array `steps` de primer nivel del propio test, tal como lo entrega el reporter JSON de Playwright. Mantén los steps planos (un solo nivel) para todo lo que quieras ver como fase independiente en la consola.
- **Las aserciones van dentro del step**, no después — `expect(...)` debe ejecutarse mientras el step sigue abierto, para que un fallo se atribuya a esa fase (y quede reflejado en su estado/descripción), no a una fase posterior ni al test en conjunto.
- **Una fase sin aserción es solo una caja de tiempo.** `test.step('open home', async () => { await page.goto(...); })` sin ningún `expect` prácticamente siempre reportará `status = 1`, ya que Playwright solo marca un step como fallido cuando algo dentro de él lanza una excepción. Añade al menos una aserción por cada fase que realmente quieras monitorizar, no solo cronometrar.
- **Orden y duración**: el orden de las fases en la consola coincide con el orden en que se ejecutan los steps; `Phase <name> time` es la duración de reloj propia de ese step, no acumulada.

### 3. Añade métricas personalizadas

Publica una anotación `pandora.metric` con `test.info()` — desde cualquier punto del cuerpo del test, incluso dentro de un `test.step`:

```typescript
const count = await page.locator('.cart-count').innerText();
test.info().annotations.push({ type: 'pandora.metric', description: `cart_items=${count}` });

```

Referencia oficial de anotaciones: **[test.info().annotations](https://playwright.dev/docs/api/class-testinfo#test-info-annotations)**.

Reglas de parseo (exactas, tomadas del runner):

- `type` debe ser exactamente el string literal `pandora.metric`; cualquier otro valor se ignora.
- `description` debe ser `name=value`, dividido solo por el **primer** `=` — así un valor que contenga `=` (por ejemplo, una query string de una URL) no se trunca.
- `name` y `value` se recortan de espacios en blanco alrededor. Si `description` no tiene `=`, o `name` queda vacío tras recortar, esa anotación se descarta silenciosamente — sin módulo, sin error.
- El tipo de módulo se infiere a partir de `value`: si se puede parsear como número → `generic_data`; en cualquier otro caso → `generic_data_string`.
- El módulo se nombra exactamente como `name` y se etiqueta con `extra_data = pw:metric:<name>`.
- Publica **una anotación por nombre de métrica y ejecución de test.** La lista de anotaciones no se deduplica — publicar el mismo nombre dos veces en una misma ejecución encola dos módulos con el mismo nombre/`extra_data`, lo cual es redundante en el mejor caso y ambiguo de reconciliar para Pandora en el peor.

### Ejemplo completo

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
    test.info().annotations.push({ type: 'pandora.metric', description: `cart_items=${count}` });
  });
});

```

### Notas

- **Nombrado**: los nombres de módulo salen de los títulos de `test.step` — mantenlos descriptivos. Renombrar un test crea un agente nuevo.
- **Continuar tras un fallo**: un `expect` normal aborta el test al fallar, así que las fases posteriores no llegan a ejecutarse (simplemente no aparecen en esa ejecución). Usa `expect.soft(locator)` si necesitas que se mida cada fase aunque una falle.
- **Varias transacciones**: varios bloques `test(...)` en un mismo fichero `.ts` generan varios agentes.
- En lugar de escribir o grabar la transacción a mano, también puede generarse de principio a fin por un agente de IA que conduzca un navegador real (vía una herramienta de automatización de navegador/Playwright) para validar cada localizador contra el objetivo real antes de entregar el fichero — detectando selectores ambiguos o que violan el modo estricto que un `codegen` normal no detecta.

## Generar tests con un agente de IA

En lugar de escribir a mano la transacción `.ts`, o grabarla una vez con `codegen` y confiar en que los selectores aguanten, un agente de código local — Claude Code, Codex o similar — puede conducir un navegador real a través del flujo y escribir la transacción por ti, validando cada localizador contra el objetivo real antes de entregarla. Esto detecta justo el tipo de fallo que hace que una transacción sea inestable en producción (badges de estado duplicados, filtros `hasText` ambiguos, una coincidencia visual solo por CSS que en realidad no es única en el DOM) — cosas que un `codegen` normal no puede detectar, porque solo graba acciones literales sin comprobar si el localizador resultante es realmente único.

### 1. Instala una capacidad de automatización de navegador de Playwright

El agente necesita una herramienta que pueda abrir un navegador real y manejarlo (clicar, rellenar, leer el DOM), no solo intuir a partir de una captura de pantalla. La forma estándar es el servidor MCP oficial de Playwright, `@playwright/mcp` (de Microsoft) — expone el control del navegador como herramientas MCP para cualquier agente compatible con MCP.

**Claude Code**:

```bash
claude mcp add playwright -- npx @playwright/mcp@latest

```

(El marketplace oficial de plugins de Anthropic también incluye un plugin "playwright" ya preparado que conecta este mismo servidor MCP — cualquiera de las dos vías funciona.)

**Codex CLI**:

```bash
codex mcp add playwright -- npx @playwright/mcp@latest

```

Ambos comandos registran el servidor para uso por stdio; `npx` descarga `@playwright/mcp` la primera vez que se ejecuta. Esto requiere tener Node disponible en la máquina que ejecuta el agente — no en la imagen Docker del plugin, ya que este paso ocurre en local, antes de que exista siquiera el fichero del test.

### 2. Plantilla de prompt

```
Validate [FLOW NAME] on [URL] and write it as a Playwright transaction for the
pandorafms.playwright.1 plugin.

What the transaction should check:
- [step 1, e.g. "open the page and confirm the title"]
- [step 2, e.g. "log in and confirm the dashboard loads"]
- [step 3, e.g. "read a value and publish it as a pandora.metric"]

Deliverable:
- Plain Playwright: wrap each meaningful step in a top-level `test.step('name', ...)`
  so it becomes a monitored phase, and use
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

### 3. Después de recibir el fichero

Ejecútalo con el plugin en local antes de conectarlo a una tarea de Discovery — ver [Ejecución manual](#ejecucion-manual) más arriba — para ver la salida real de agente/módulo, no solo "el test ha pasado".

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

- `test.use({ ignoreHTTPSErrors: true })` en el nivel superior del fichero se aplica a todos los `test(...)` que vengan después.
- Para limitarlo a solo algunos tests del mismo fichero, agrúpalos en su propio bloque `test.describe(...)` y llama a `test.use({ ignoreHTTPSErrors: true })` como primera línea dentro de ese bloque, en lugar de en el nivel superior.
- Esto solo desactiva la **validación del certificado**, no el TLS en sí — la conexión sigue cifrada, simplemente ya no exige una cadena de confianza CA válida.

## Depuración y solución de problemas

### Depurar un test

Cuando una transacción falla y la captura de pantalla / el `Full report` no son suficientes, ejecuta el test de forma interactiva dentro de la misma imagen que usa el plugin, con el informe HTML de Playwright (traza + vídeo del fallo) servido desde el contenedor. La imagen incluye `playwright.config.debug.ts` (en `/pandora`) preconfigurado con `trace: 'on-first-retry'`, `screenshot: 'only-on-failure'`, `video: 'retain-on-failure'`, y un reporter HTML expuesto en `0.0.0.0:9323`.

```bash
docker run -it --rm \
  -v "$(pwd)/test.spec.ts:/pandora/test.spec.ts" \
  -p 9323:9323 \
  pandorafms/pandora_playwright:noble bash

# dentro del contenedor:
npx playwright test test.spec.ts --config=playwright.config.debug.ts --browser=chromium --timeout=30000
npx playwright show-report --host 0.0.0.0 --port 9323

```

Con `-p 9323:9323` publicado, abre `http://localhost:9323` en el host para revisar el informe: resultados por step, el visor de trazas y el vídeo del fallo.

### Solución de problemas

- **"Playwright produced no report"** — el test no llegó a ejecutarse (error de sintaxis, import incorrecto, navegador ausente). Ejecuta con `-v` y revisa el stderr de `docker exec`.
- **La captura de pantalla se muestra como texto, no como imagen** — el valor debe ser `generic_data_string` con el prefijo `data:image/png;base64,`; comprueba que el build del plugin lo incluye.
- **`Cannot find module '@playwright/test'`** — el test debe ejecutarse desde `/pandora` dentro de la imagen para que Node resuelva `node_modules`; por eso el plugin lo copia a `/pandora/task.spec.ts`.
- **Los agentes caen en el grupo equivocado (modo independiente `-x`)** — el XML de agente de Pandora espera el **nombre** del grupo, no el id numérico. La ruta `monitoring_data` de Discovery sí usa correctamente el `id_group` numérico.
- **Una fase posterior sigue mostrando "ok" tras un fallo anterior** — una aserción fuerte fallida aborta la ejecución, así que las fases posteriores conservan su valor anterior. Usa `expect.soft()` si necesitas que se mida cada fase en cada ejecución.
- **`net::ERR_CERT_AUTHORITY_INVALID`** — ver [Certificados autofirmados](#certificados-autofirmados).
