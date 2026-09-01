# Playwright

*Última actualización del artículo: 2026-09-01.*

## Qué monitoriza

El plugin de Discovery Playwright proporciona monitorización web sintética con [Playwright](https://playwright.dev/): usted aporta un único test `.ts` de Playwright, el plugin lo ejecuta dentro de un contenedor Docker preconfigurado (en local o en un host remoto por SSH) y convierte el resultado en módulos de monitorización de Pandora FMS que se integran en la vista transaccional WUX de la consola: estado y tiempo globales, estado y tiempo por fase, captura de pantalla del error y métricas personalizadas.

El modelo de ejecución se apoya en el comportamiento nativo de Playwright:

1. La tarea de Discovery (o una ejecución manual por CLI) lanza un contenedor Docker a partir de la imagen de Playwright (`pandorafms/pandora_playwright:noble`).
2. El test `.ts` se copia dentro del contenedor y se ejecuta con `npx playwright test --reporter=json`.
3. El plugin lee el reporter JSON y construye **un agente por cada `test(...)` de Playwright**, con módulos para el estado y el tiempo globales, cada `test.step` como fase, una captura de pantalla del error en caso de fallo y las métricas personalizadas.
4. Los resultados se devuelven como datos de monitorización de Discovery o (con `-x`) se envían como XML de agente mediante Tentacle.

Es el equivalente en Playwright de `pandorafms.selenium.4`, pero **no hay librería propia que importar ni DSL que aprender**: usted escribe código Playwright estándar y el plugin recoge todo del reporter JSON de Playwright. La ejecución siempre es en Docker; con `worker_mode = remote` el contenedor se ejecuta en un host remoto alcanzado por SSH.

## Preparación

### Compatibilidad

| Alcance | Estado | Evidencia |
|---------|--------|-----------|
| Versión del plugin `1.0` (`pandorafms.playwright.1`) | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del plugin](#identidad-del-plugin) |
| Runtime de Playwright **1.62.0** sobre Node 24 | `Probado` | Runtime contra el que se validó el plugin |
| Imagen Docker `pandorafms/pandora_playwright:noble` (base Ubuntu 24.04, navegadores preinstalados) | `Probado` | Valor por defecto del campo **Docker image** |
| Navegadores Chromium, Mozilla Firefox y WebKit | `Probado` | Los tres valores del campo **Browser** |
| Modos de worker `local` y `remote` (SSH) | `Probado` | Ambas rutas de ejecución verificadas de extremo a extremo |
| Servidor y consola de Pandora FMS **800.5 LTS** y **804 FR** | `Probado` | Ejecución de extremo a extremo contra un Tentacle real, con la vista transaccional WUX renderizada en la consola |
| Docker en el host que ejecuta el test | `Requerido` | Prerrequisito, no una declaración de compatibilidad. Consulte [Prerrequisitos](#prerrequisitos) |
| Cualquier otra versión del servidor de Pandora FMS | `Sin validar` | No hay evidencia de una matriz por versión más allá de las anteriores |
| Sistema operativo del host Docker distinto de Linux | `Sin validar` | La imagen está basada en Ubuntu 24.04; el sistema operativo del host usado en las pruebas fue Linux |

### Prerrequisitos

1. **Docker** en la máquina que ejecuta el test: el propio servidor de Discovery para `worker_mode = local`, o el destino SSH para `worker_mode = remote`.
2. **La imagen Docker de Playwright** `pandorafms/pandora_playwright:noble` disponible en esa máquina (con los navegadores preinstalados), descargada del registro:

    ```bash
    docker pull pandorafms/pandora_playwright:noble
    ```

    Esta es la forma recomendada de obtenerla. Para añadir sus propias dependencias encima, consulte [Usar una imagen Docker propia](#usar-una-imagen-docker-propia).

3. **Pandora FMS**: un servidor de Discovery habilitado (`discoveryserver 1` en `pandora_server.conf`) para ejecutar tareas, y la consola para definirlas.
4. **Solo para worker remoto** (`worker_mode = remote`): una cuenta SSH en el host remoto capaz de ejecutar Docker (dirección, puerto, usuario y contraseña o contraseña cifrada).

    El campo **SSH user** tiene `root` como valor por defecto. El plugin no requiere root: sirve cualquier cuenta que pueda ejecutar `docker` en ese host, así que es preferible una cuenta dedicada sin privilegios añadida al grupo que concede acceso a Docker. Tenga en cuenta que ese acceso equivale a acceso administrativo sobre ese host.

El plugin se distribuye como un ejecutable autocontenido: la aplicación de Discovery empaquetada incluye `bin/pandora_playwright`, por lo que no hay que instalar ningún runtime adicional, ni en el servidor de Discovery ni para una ejecución manual por CLI.

### Instalar el plugin

El plugin se instala desde la tienda de plugins de Discovery. Existen **dos copias** en disco:

- `<homedir>/attachment/discovery/pandorafms.playwright.1/` — la que usa la consola para el formulario de la tarea.
- `<remote_config>/discovery/pandorafms.playwright.1/`, habitualmente `/var/spool/pandora/data_in/discovery/pandorafms.playwright.1/` — **la copia que ejecuta el servidor de Discovery**.

Actualizar solo la primera copia mantiene silenciosamente la versión antigua en ejecución en el servidor de Discovery.

## Configuración

Configurar una transacción monitorizada son dos cosas: crear la tarea de Discovery y escribir el test de Playwright que esta ejecuta. Empiece por la tarea, para ver dónde vive cada campo; [Escribir la transacción de Playwright](#escribir-la-transaccion-de-playwright) cubre el test que se pega en ella.

### Crear la tarea de Discovery

La tarea se crea en la consola como una tarea de Discovery de la aplicación **Playwright**:

1. Vaya a **Discovery → Tasks → New task**, elija la aplicación Playwright y establezca el nombre de la tarea, el grupo, el servidor y el intervalo: el paso genérico **Task definition** del propio asistente.

    ![Paso de definición de la tarea del asistente de la tarea de Discovery de Playwright](../assets/images/discovery/playwright/task-wizard-1.png)

2. Recorra los pasos del asistente: **Basic setup** (modo de worker, navegador), **Worker setup** (solo para `remote`), **Test setup** (imagen, viewport, timeout, informe completo, prefijo de agentes, el propio test de Playwright, módulo de histórico de errores) y **Advanced setup** (modo debug, directorio de debug, timeouts avanzados, eliminar contenedor existente). Todos los campos están documentados en [Parámetros de la tarea](#parametros-de-la-tarea).

    ![Paso Basic setup: modo de worker y navegador](../assets/images/discovery/playwright/task-wizard-2.png)

    ![Paso Worker setup: campos de conexión SSH, mostrados solo cuando el modo de worker es remote](../assets/images/discovery/playwright/task-wizard-3.png)

    ![Paso Test setup: imagen Docker, viewport, timeout del test, informe completo, prefijo de agentes y el campo del test de Playwright](../assets/images/discovery/playwright/task-wizard-4.png)

    ![Paso Advanced setup: modo debug, directorio de debug, eliminar contenedor existente y timeouts avanzados](../assets/images/discovery/playwright/task-wizard-5.png)

3. Pegue el `.ts` completo en el campo **Playwright test (.ts)**, elija el navegador y el modo de worker, y guarde. Si aún no tiene el test, escríbalo primero: consulte [Escribir la transacción de Playwright](#escribir-la-transaccion-de-playwright).

La contraseña SSH puede almacenarse cifrada: la consola llama al binario `password_encrypter` (AES-256-CBC) cuando **Encrypt password** está activo, que es el valor por defecto.

### Escribir la transacción de Playwright

Una «transacción» no es más que un test estándar de Playwright. Usted escribe Playwright puro —sin necesidad de importar nada de Pandora FMS— y el plugin traduce tres construcciones nativas:

| Usted escribe | Se convierte en |
|---------------|-----------------|
| `test.step('nombre', ...)` | una **fase** monitorizada (estado + tiempo) |
| `test.info().annotations.push({ type: 'pandora.metric', description: 'nombre=valor' })` | un módulo de **métrica** personalizada |
| una aserción que falla | el test falla; se captura automáticamente una **captura de pantalla** |

Para obtener el código inicial del flujo, grábelo con cualquiera de las herramientas siguientes, o encargue a un agente de codificación que lo escriba contra el destino real.

#### Grabar con Playwright codegen

En cualquier máquina con Playwright instalado, lance el grabador contra su sitio (consulte el [generador de tests de Playwright](https://playwright.dev/docs/codegen-intro)):

```bash
npx playwright codegen https://su-aplicacion.example.com
```

Recorra su flujo en el navegador; Playwright escribe el código equivalente. Copie ese código como punto de partida.

#### Grabar con la extensión de Playwright para VS Code

Instale la extensión **Playwright Test for VS Code** de Microsoft ([Visual Studio Marketplace](https://marketplace.visualstudio.com/items?itemName=ms-playwright.playwright); requiere Playwright v1.38+ en el proyecto). Abra la barra lateral **Test Explorer** y use las herramientas de grabación:

- **Record new**: abre una ventana del navegador donde usted navega e interactúa con el sitio; el test generado se escribe en tiempo real en un fichero `.spec.ts` nuevo.
- **Record at cursor**: inserta las acciones recién grabadas en la posición actual del cursor dentro de un test existente.
- **Pick locator**: al pasar el ratón sobre un elemento del navegador y hacer clic, copia su mejor localizador al portapapeles.

La extensión trabaja sobre un proyecto de Playwright, así que grabe en cualquier proyecto desechable y copie el `.ts` resultante como punto de partida.

#### Grabar con la extensión de navegador de Playwright

Instale **Playwright CRX** desde la [Chrome Web Store](https://chromewebstore.google.com/detail/playwright-crx/jambeljnbnfbkcpnoiaedcabbgmnnlcd) (extensión comunitaria de ruifigueira). Incorpora el mismo grabador que usa `playwright codegen` en forma de extensión de navegador, de modo que puede grabar directamente en su propio Chrome/Chromium/Edge:

- Asocie la pestaña actual con el botón de la extensión (o el menú contextual), o use el panel lateral; `Alt + Shift + R` inicia la grabación y `Alt + Shift + C` inicia la inspección.
- Realice el flujo en la página; el grabador genera el código de Playwright en el lenguaje seleccionado.
- Copie o exporte el script generado y úselo como punto de partida.

#### Generar la transacción con un agente de IA

En lugar de escribir a mano la transacción `.ts` (o grabarla una vez y confiar en que los selectores aguanten), puede encargar a un agente de codificación local —Claude Code, opencode, `pi` o similar— que conduzca un navegador real por el flujo y escriba la transacción por usted, validando cada localizador contra el destino real antes de entregarla.

Esto funciona porque estos agentes pueden usar una **skill de CLI de Playwright o de automatización de navegador** (una herramienta que abre un navegador real, hace clic, rellena y lee el DOM bajo control del agente) para ejecutar realmente el flujo paso a paso, no solo adivinar selectores a partir de una captura. Un grabador registra acciones literales, pero no tiene forma de saber qué agrupación de elementos es única, si un texto de estado o etiqueta se repite en otro punto, o si el texto real del DOM coincide con lo que el CSS hace *parecer*; un agente que puede reejecutar cada localizador contra la página real, ver una violación de modo estricto y corregir el alcance antes de entregar el fichero detecta exactamente la clase de fallo que vuelve inestable una transacción en producción.

Plantilla de prompt:

```
Valida [NOMBRE DEL FLUJO] en [URL] y escríbelo como una transacción de Playwright
para el plugin pandorafms.playwright.1.

Qué debe comprobar la transacción:
- [paso 1, p. ej. "abrir la página y confirmar el título"]
- [paso 2, p. ej. "iniciar sesión y confirmar que carga el dashboard"]
- [paso 3, p. ej. "leer un valor y publicarlo como pandora.metric"]

Entregable:
- Playwright puro: envuelve cada paso relevante en `test.step('nombre', ...)` para
  que se convierta en una fase WUX, y usa
  `test.info().annotations.push({ type: 'pandora.metric', description: 'nombre=valor' })`
  para todo lo que deba convertirse en un módulo de métrica personalizada.
- Sin importar nada de Pandora FMS, sin DSL: este plugin recoge todo del propio
  reporter JSON de Playwright.
- Valida tú mismo cada localizador contra el destino real (conduce el navegador,
  no lo infieras de una captura) antes de entregarme el fichero, y corrige antes
  cualquier cosa ambigua o que viole el modo estricto.
- Si un paso posterior depende de una aserción dura de un paso anterior, dime si
  conviene mantenerlo así o cambiar a `expect.soft()` para que todas las fases se
  midan aunque una falle.
```

Nunca incluya credenciales reales en el prompt ni en el fichero entregado: use una cuenta de pruebas y trate lo que pegue en la tarea como configuración almacenada de la tarea.

#### Estructurarlo en fases y añadir métricas

Sea cual sea la forma en que haya producido el flujo, envuelva cada parte relevante en `test.step(...)` para que se convierta en una fase, y añada aserciones que validen realmente el resultado:

```typescript
import { test, expect } from '@playwright/test';

test('checkout flow', async ({ page }) => {
  await test.step('open home', async () => {
    await page.goto('https://su-aplicacion.example.com');
    await expect(page).toHaveTitle(/Shop/);
  });

  await test.step('login', async () => {
    await page.fill('#user', '<USERNAME>');
    await page.fill('#password', '<PASSWORD>');
    await page.click('#submit');
    await expect(page.locator('.dashboard')).toBeVisible();
  });

  await test.step('add to cart', async () => {
    await page.click('text=Add to cart');
    const count = await page.locator('.cart-count').innerText();
    // publica un módulo de métrica personalizada:
    test.info().annotations.push({ type: 'pandora.metric', description: `cart_items=${count}` });
  });
});
```

Solo las llamadas `test.step` de **primer nivel** se convierten en fases: el plugin lee el array `steps` de primer nivel del reporter JSON de Playwright, así que un paso anidado dentro de otro no se reporta como fase independiente. Mantenga los pasos planos (un solo nivel) para todo lo que quiera ver como fase independiente en la consola.

Las métricas se interpretan a partir de la anotación con estas reglas exactas:

- `type` debe ser literalmente la cadena `pandora.metric`; cualquier otro valor se ignora.
- `description` debe ser `nombre=valor`, dividido **solo por el primer** `=`, de modo que un valor que contenga `=` (por ejemplo una cadena de consulta de una URL) no se trunca.
- `nombre` y `valor` se recortan de espacios. Si `description` no tiene `=`, o `nombre` queda vacío tras el recorte, esa anotación se descarta silenciosamente.
- El tipo de módulo se deduce del valor: si se interpreta como número → `generic_data`; en caso contrario → `generic_data_string`. El módulo se llama exactamente `nombre` y se etiqueta con `extra_data = pw:metric:<nombre>`.

Consejos de redacción:

- **Nombres**: los nombres de módulo salen de los títulos de sus `test.step`, así que manténgalos descriptivos (`'login'`, `'add to cart'`). Renombrar un test inicia un agente nuevo.
- **Continuar tras un fallo**: con un `expect` normal, una fase fallida aborta el test y las fases posteriores no se ejecutan. Si quiere medir todas las fases aunque una falle, use aserciones blandas: `await expect.soft(locator).toHaveText('x')`.
- **Varias transacciones**: varios bloques `test(...)` en un mismo `.ts` producen varios agentes. Consulte [Varios tests en un fichero](#varios-tests-en-un-fichero).
- **El código grabado es un punto de partida, no el entregable**: revise los localizadores grabados contra la página real antes de conectarlo a una tarea de Discovery.
- **Credenciales**: el contenido del test se almacena junto con la tarea. Use cuentas de monitorización dedicadas con el menor privilegio que necesite el flujo.

## Verificar la primera ejecución

Fuerce la tarea desde **Discovery → Task list → Application tasks** y compruebe el resultado en este orden.

1. **El resumen de la tarea.** La consola muestra un resumen de ejecución con el progreso global y el recuento de aciertos y fallos:

    ![Resumen de ejecución de la tarea con el progreso global y el recuento de aciertos y fallos](../assets/images/discovery/playwright/task_summary.png)

2. **Los agentes.** Un agente por cada `test(...)` de su fichero, con el alias `Playwright - <título del test>` (con prefijo cuando **Prefix for agents created** está establecido).

3. **Los módulos de cada agente.** Una ejecución correcta produce al menos:

    | Módulo | Valor esperado en un test que pasa |
    |--------|------------------------------------|
    | `Global status` | `1` (un test que falla reporta `0`) |
    | `Global time` | La duración del test en segundos |
    | `Phase <nombre> status` / `Phase <nombre> time` | Un par por cada `test.step` de primer nivel |
    | `Last error screenshot` | `None` si tiene éxito; un valor `data:image/png;base64,...` si falla |
    | `<nombre de la métrica>` | El valor publicado por cada anotación `pandora.metric` |

4. **La vista transaccional WUX.** Abra el agente en la consola y confirme que la vista transaccional lista las fases y que `Last error screenshot` se renderiza como imagen y no como texto. La vista dedicada se describe en [Extensión de consola WUX Transactions](#extension-de-consola-wux-transactions).

Si no se produce nada, ejecute la misma configuración manualmente con `-v` para ver la traza paso a paso —consulte [Ejecución por línea de comandos](#ejecucion-por-linea-de-comandos)— y después [Solución de problemas](#solucion-de-problemas).

## Interpretar los resultados

### Agentes y módulos generados

**Un agente por cada `test(...)` de Playwright.** El nombre del agente es `a + md5(<prefijo de agentes> + <título completo>)`, donde el título completo es la ruta `describe > test` y el prefijo es el campo opcional **Prefix for agents created** (vacío por defecto). El alias es `Playwright - <prefijo de agentes><título completo>`. El nombre **no** depende de la tarea, así que borrar y recrear la tarea reporta al mismo agente y conserva el histórico.

Esa independencia respecto a la tarea tiene su contrapartida: **dos tareas que ejecuten un test con el mismo título reportan al mismo agente**, alternando sus datos en los mismos módulos. Cuando eso no es lo deseado —típicamente la misma transacción apuntada a dos entornos— dé a cada tarea su propio prefijo (por ejemplo `prod-`, `dev-`) para separarlas en agentes distintos. Dejarlo vacío reproduce exactamente la nomenclatura original, de modo que una actualización nunca deja huérfanos a los agentes existentes.

| Módulo | Tipo | Origen | `extra_data` |
|--------|------|--------|--------------|
| `Global status` | `generic_proc` | resultado del test (`passed` → 1) | `wux:global_status:<test>` |
| `Global time` | `generic_data` (s) | duración del test | `wux:global_time:<test>` |
| `Phase <nombre> status` | `generic_proc` | cada `test.step` | `wux:phase_status:<n>:<test>` |
| `Phase <nombre> time` | `generic_data` (s) | duración de cada `test.step` | `wux:phase_time:<n>:<test>` |
| `Last error screenshot` | `generic_data_string` (imagen) | captura de pantalla al fallar | `wux:error_screenshot:<test>` |
| `Global error` | `generic_data_string` | `OK` o el texto del error del test (con **Generate error history module** activo) | `wux:global_error:<test>` |
| `Phase <nombre> error` | `generic_data_string` | `OK` o el texto del error de la fase (con **Generate error history module** activo) | `wux:phase_error:<n>:<test>` |
| `<nombre de la métrica>` | `generic_data` / `generic_data_string` | anotación `pandora.metric` | `pw:metric:<nombre>` |
| `Full report` | `async_string` | informe detallado derivado del reporter JSON | `pw:full_report` |

Los módulos `wux:*` se renderizan en la vista transaccional WUX de la consola. Los módulos `pw:*` son módulos de agente normales (métricas e informe completo).

### Extensión de consola WUX Transactions

El plugin incluye una extensión de consola complementaria, **WUX Transactions** (`wux_transactions_ext`), que registra una opción **«WUX Transactions»** en el menú de operación (bajo la sección que aloja las vistas de monitorización y estado) y renderiza la vista identificada por la ruta «Monitoring → Views → WUX Transactions». Abrirla requiere que el usuario tenga al menos uno de los ACL **AR** o **RR**; la extensión aplica además ACL de grupo (AR sobre el grupo del módulo) a todo lo que lista.

La vista aporta la capa de monitorización transaccional para los datos WUX:

- **Las transacciones se descubren a partir del `extra_data` de los módulos.** La extensión lista todos los módulos cuyo `extra_data` empieza por `wux:global_status:` (el `extra_data` del propio agente WUX está vacío, así que los marcadores de módulo son el origen de las transacciones). Un filtro de selección múltiple («Select transactions») elige una o varias transacciones para comparar los datos de su última ejecución.

    ![Panel de filtro de WUX Transactions con la lista de selección múltiple «Select transactions»](../assets/images/discovery/playwright/wux-transactions-view-filter.png)

- **Las tarjetas de resumen** agregan las transacciones seleccionadas: recuentos de Selected / Passing / Failing / Unknown y el tiempo global medio. Cuando varias tareas de Discovery reportan a la misma transacción se muestra un aviso de «Shared transactions» (para las tareas con modo debug activado, que es lo único que la extensión puede detectar); la corrección recomendada es un prefijo de agentes distinto por tarea.

    ![Tarjetas de resumen y gráfica comparativa de tiempo de respuesta global para varias transacciones seleccionadas](../assets/images/discovery/playwright/wux-transactions-view-compare.png)

- **Los paneles por transacción** muestran el estado y el tiempo globales, la tabla de fases (Phase, Status, Time, Updated, más las acciones de gráfica y detalle del módulo), las métricas de tiempo WUX, las métricas personalizadas (valores `pw:metric` emitidos por el test) y el bloque de evidencia: **Last error screenshot** (cuando el módulo contiene un valor `data:image/...` válido) y el **Full WUX report** cuando **Send full report** está activo.

    ![Panel por transacción con las métricas de tiempo WUX, la gráfica de tiempo de respuesta por fase y la tabla de fases](../assets/images/discovery/playwright/wux-transactions-view-single.png)

- **Evidencia de depuración de Playwright**: para las tareas de la aplicación `pandorafms.playwright.1` con el modo debug activado, la extensión lee el campo **Debug directory** de la tarea desde `tdiscovery_apps_tasks_macros`, sustituye el marcador de identificador de tarea por `md5(id_rt)` exactamente igual que hace el runner, lee el `manifest.json` que dejó la última ejecución y lo indexa por nombre de agente. Un botón «Playwright debug» en el panel de la transacción abre una ventana modal con un bloque por ejecución de la tarea: etiqueta Passed/Failed, marca de tiempo de la captura, **vídeo del fallo** (webm), **captura de pantalla del fallo** (png), **contexto del error** (instantánea de la página en markdown en el momento del fallo), el informe completo de la ejecución y el registro de transacciones de la API de Playwright (`pw:api`). Los artefactos se sirven mediante un endpoint que solo entrega los tipos permitidos (captura, vídeo y contexto del error), aplica el ACL de grupo y nunca se cachea.

    ![Ventana modal de evidencia de depuración de Playwright con el vídeo del fallo, la captura de pantalla del fallo y el contexto del error](../assets/images/discovery/playwright/wux-transactions-view-debug.png)

- **Notificación de ausencia de evidencia**: las tareas cuya evidencia no se puede leer se listan en la parte superior de la vista con la tarea, su directorio de debug y el motivo; consulte la tabla de cuatro motivos en [Si la consola no muestra evidencia](#si-la-consola-no-muestra-evidencia).

## Operación y solución de problemas

### Tiempos de espera

Playwright tiene varios tiempos de espera independientes. **Test timeout** es el que siempre aparece en el asistente, y **no** es el tiempo de espera por paso que la mayoría de la gente tiene en mente. Los tres tiempos por paso están desactivados por defecto y aparecen en **Advanced setup** al marcar **Advanced timeouts**; también pueden fijarse en el fichero de test, que siempre gana.

| Tiempo de espera | Qué acota | Dónde se fija | Valor en este plugin |
|------------------|-----------|---------------|----------------------|
| Por test | un `test(...)` completo, incluidos todos sus `test.step`, acciones y aserciones | campo de tarea **Test timeout** → `npx playwright test --timeout=<s × 1000>` | `120` s por defecto |
| Acción | cada acción individual: `click`, `fill`, `press`, `check`, `selectOption`... | campo de tarea **Action timeout**, o el fichero de test | sin fijar → valor por defecto de Playwright `0` (sin límite) |
| Navegación | cada navegación: `goto`, `waitForURL`, `waitForNavigation`, `reload` | campo de tarea **Navigation timeout**, o el fichero de test | sin fijar → valor por defecto de Playwright `0` (sin límite) |
| Aserción | cada aserción web-first: `expect(locator).toBeVisible()`, `toHaveText`... | campo de tarea **Expect timeout**, o el fichero de test | sin fijar → valor por defecto de Playwright `5000` ms |
| TTL del contenedor | la ejecución completa dentro de Docker | derivado, no configurable | `min(3600, max(120, <Test timeout> × 20))` → `2400` s por defecto |
| Conexión SSH | apertura de la sesión SSH (solo worker `remote`) | derivado, no configurable | `<Test timeout>` → `120` s por defecto |

Con **Advanced timeouts** desactivado, la configuración generada no declara ninguno de los tres, así que se aplican los valores por defecto de Playwright y hay exactamente un lugar —la tarea, o su test— del que puede venir un valor.

#### Test timeout: por test, no por paso y no por tarea

El campo se corresponde directamente con el `--timeout` de Playwright, que es el **presupuesto de un bloque `test(...)` completo**. Todos sus pasos, acciones y aserciones consumen del mismo presupuesto.

Cuando un test lo supera, Playwright aborta **solo ese test** y lo marca como `timedOut`: su módulo `Global status` reporta `0` y la fase en curso se reporta como fallida. **El resto de bloques `test(...)` del fichero se siguen ejecutando, y la tarea de Discovery no se interrumpe.** El plugin no pasa `--global-timeout` ni fija tiempo de espera alguno sobre el proceso o el comando SSH que ejecuta, así que nada en él aborta una ejecución por durar demasiado en conjunto, con la única excepción del TTL del contenedor descrito más abajo.

#### Advanced timeouts: tiempos por paso desde la tarea

Marque **Advanced timeouts** en **Advanced setup** y aparecerán los tres campos por paso, precargados con los valores por defecto del propio Playwright (`0`, `0`, `5` segundos). Dejarlos en esos valores no cambia nada.

Ninguno de los tres tiene opción de línea de comandos, y solo acción y navegación son opciones de `use`: `expect.timeout` vive en el nivel superior de la configuración y no es accesible desde un fichero de test. Por eso, en lugar de reescribir su test, los tres valores se añaden a la configuración generada: el fichero que el runner escribe dentro del contenedor en cada ejecución y que ya lleva el viewport y los ajustes de captura. Su test no se toca, y lo que él declare sigue prevaleciendo.

#### Tiempos por paso fijados en el fichero de test

Los mismos tres tiempos de espera pueden fijarse en el `.ts` que pega en **Playwright test**, a nivel de fichero o por test. Esto prevalece sobre los campos de la tarea, y es la única opción si necesita un valor distinto por test en lugar de uno para toda la tarea.

A nivel de fichero (también válido dentro de un `test.describe`, pero **no** dentro de `beforeEach` ni `beforeAll`):

```ts
import { test, expect as baseExpect } from '@playwright/test';

// Cada acción dispone de 5 s, cada navegación de 10 s
test.use({ actionTimeout: 5000, navigationTimeout: 10000 });

// Cada aserción web-first dispone de 5 s
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

#### Precedencia: el test siempre gana sobre el campo de la tarea

Cuando al mismo test se le fija un tiempo de espera en ambos sitios, **gana el fichero de test**. Playwright resuelve el tiempo por test en este orden, de menor a mayor prioridad:

```
configuración generada de la tarea  <  --timeout (campo de la tarea)  <  test.describe.configure({ timeout })  <  test.setTimeout()
```

El campo de la tarea es un *valor por defecto* que el runner pone en la línea de comandos, no un techo. Prevalece sobre la configuración generada, y lo que declare el test prevalece a su vez sobre él, por test, de modo que el resto del fichero conserva el valor de la tarea.

```ts
// El campo de la tarea dice 120. Este test recibe 5 min; los demás siguen con 120 s.
test('long transaction', async ({ page }) => {
  test.setTimeout(300000);
  // ...
});
```

Los tiempos de acción, navegación y aserción se resuelven igual: **Advanced timeouts** los coloca en una configuración, que es el nivel más débil, así que lo que declare el test prevalece. En cualquier caso, **Test timeout** sigue acotándolos en tiempo real de reloj.

**Pero el campo de la tarea es lo único que fija el TTL del contenedor.** El TTL se calcula antes de arrancar Docker, únicamente a partir del campo de la tarea; ningún `test.setTimeout()` puede elevarlo. Un test que se conceda más tiempo del que permite el TTL igualmente muere con el contenedor (`Playwright produced no report`). Por eso `test.setTimeout()` es seguro para **bajar** el presupuesto de un test, o para subirlo dentro del margen que ya da el TTL; para ir más allá, suba **Test timeout** en la tarea, que es la única entrada que mueve el TTL con él.

#### Conseguir que los tiempos por paso se disparen realmente

El presupuesto por test siempre gana. Si **Test timeout** es `120` y a un paso se le da `actionTimeout: 180000`, ese paso nunca alcanza su propio límite: el test muere antes, a los 120 s, y el fallo se reporta como tiempo de espera del test y no como el paso que se quedó colgado. Para que los tiempos por paso sean el límite decisivo, el presupuesto por test debe ser mayor que la suma de los pasos que espera: suba **Test timeout** en la tarea, o sobrescríbalo para un test desde el fichero. Tenga en cuenta que subir **Test timeout** sube también el TTL del contenedor y el tiempo de conexión SSH, ya que ambos se derivan de él; `test.setTimeout()` no.

#### TTL del contenedor: el único límite que aborta una ejecución completa

El runner arranca el contenedor de test como `docker run -d --rm --name <contenedor de la tarea> <imagen> sleep <ttl>` y después ejecuta el test mediante `docker exec`. El TTL se deriva de **Test timeout**:

```
ttl = min(3600, max(120, <Test timeout> × 20))
```

El recorte importa: el TTL solo sigue a **Test timeout** entre `6` s y `180` s. Por debajo es siempre `120` s, por encima siempre `3600` s. Con el valor por defecto de `120` s son `2400` s (40 min). Si la duración **total** de una ejecución supera el TTL, el `sleep` termina, el contenedor se detiene y se lleva por delante el `docker exec` en curso: no se produce informe y la tarea falla con `Playwright produced no report`. Esto es lo más parecido a un tiempo de espera de tarea completa que hay en el plugin: si ejecuta varios tests largos en un mismo fichero, dimensione **Test timeout** de forma que su `× 20` cubra el fichero entero, no solo el test más lento.

### Varios tests en un fichero

Un solo `.ts` puede contener varios bloques `test(...)`. El plugin trata cada uno como una transacción independiente: **un agente por cada `test(...)`**, cada uno con su propio `Global status` y `Global time`, sus fases, su captura de pantalla y sus métricas. Todos se ejecutan dentro del mismo contenedor Docker, en una única invocación de `npx playwright test`.

#### Comportamiento por defecto: secuencial

El comportamiento por defecto de Playwright es que **los ficheros de test se ejecutan en paralelo entre sí, pero los tests dentro de un mismo fichero se ejecutan uno tras otro en el mismo proceso worker**. Este plugin ejecuta siempre un único fichero, así que el paralelismo a nivel de fichero nunca se aplica: sus tests arrancan en el orden en que están escritos y cada uno termina antes de que empiece el siguiente.

Consecuencias:

- El tiempo total de ejecución es la **suma** de la duración de cada test.
- Cada `test(...)` recibe un contexto y una página de navegador nuevos, así que un test no puede filtrar estado al siguiente.
- Un test que falla **no** aborta los demás: Playwright reporta cada test de forma independiente y el plugin construye cada agente a partir de su propio resultado.
- Con un `expect` duro, una aserción fallida aborta *ese* test: sus fases posteriores no se ejecutan y ninguna anotación `pandora.metric` posterior al fallo llega a evaluarse (publique las métricas según se calculan). Use `expect.soft()` para seguir midiendo las fases restantes.

#### Ejecutarlos en paralelo a nivel de test

Si los tests son independientes, envuélvalos en `test.describe.parallel(...)` y Playwright los repartirá entre varios procesos worker dentro del contenedor:

```typescript
import { test, expect } from '@playwright/test';

test.describe.parallel('independent checks', () => {
  test('checkout flow', async ({ page }) => { /* ... */ });
  test('login flow', async ({ page }) => { /* ... */ });
});

test('always sequential', async ({ page }) => { /* ... */ });
```

`test.describe.configure({ mode: 'parallel' })` en el ámbito del fichero es la forma equivalente aplicada a todo el fichero. El valor por defecto es `mode: 'serial'`, así que solo hay que activarlo explícitamente.

Advertencias:

- El número de workers por defecto de Playwright es **la mitad de los núcleos lógicos del contenedor**, y el plugin no lo sobrescribe (no pasa `--workers`). Con un contenedor de un solo núcleo el bloque paralelo sigue ejecutando un test cada vez; con dos o más núcleos los tests se ejecutan realmente de forma concurrente.
- Cada test paralelo ejecuta su propia instancia de navegador dentro del contenedor, así que la concurrencia eleva el uso de CPU y memoria: dimensione el contenedor y la carga sobre el sitio de destino en consecuencia.
- Los tests paralelos no deben compartir estado ni depender del orden de ejecución. Si alguno debe ejecutarse estrictamente después de otro, manténgalo fuera del bloque paralelo o use `test.describe.configure({ mode: 'serial' })` para ese grupo.

### Certificados autofirmados

Por defecto Playwright valida los certificados TLS como un navegador real, así que un destino con un certificado autofirmado o emitido internamente hace que cada `page.goto(...)` falle con `net::ERR_CERT_AUTHORITY_INVALID` incluso antes de que se ejecute la lógica de su test.

No hay opción a nivel de plugin para esto: fíjelo explícitamente en la transacción con el propio `test.use()` de Playwright:

```typescript
import { test, expect } from '@playwright/test';

test.use({ ignoreHTTPSErrors: true });

test('checkout flow', async ({ page }) => {
  await page.goto('https://internal.example.com');
  // ...
});
```

- `test.use({ ignoreHTTPSErrors: true })` colocado en el nivel superior del fichero se aplica a todos los `test(...)` que haya por debajo en esa transacción.
- Para limitarlo solo a algunos tests del mismo fichero, envuélvalos en su propio bloque `test.describe(...)` y llame a `test.use({ ignoreHTTPSErrors: true })` como primera línea dentro de ese bloque, en lugar de en el nivel superior.
- Esto solo desactiva la **validación del certificado**, no TLS: la conexión sigue cifrada, simplemente deja de exigir una cadena de CA de confianza. Es preferible instalar la CA interna en una imagen propia antes que desactivar la validación contra un destino público.

### Usar una imagen Docker propia

Cada tarea se ejecuta dentro de la imagen indicada en el campo **Docker image**, `pandorafms/pandora_playwright:noble` por defecto. El runner genera la configuración completa de Playwright en cada ejecución y la escribe dentro del contenedor en marcha, así que la imagen solo tiene que cumplir **un** requisito:

> `@playwright/test` instalado en `/pandora/node_modules`, en la misma versión que los navegadores de la imagen.

Cualquier imagen que cumpla esa línea sirve como valor de **Docker image**.

Si sus tests necesitan algo adicional —un paquete de fuentes, un certificado de CA interna, un cliente VPN, una librería npm que el test importa— construya **encima** de la imagen publicada en lugar de ensamblar una desde cero. Así conserva el emparejamiento de versiones entre navegadores y runner y hereda las correcciones futuras:

```dockerfile
FROM pandorafms/pandora_playwright:noble

# Paquetes de sistema adicionales que necesiten sus tests.
USER root
RUN apt-get update && apt-get install -y fonts-noto-cjk && rm -rf /var/lib/apt/lists/*

# Librerías npm adicionales que importen sus tests, instaladas en el mismo
# proyecto para que `npx playwright test` las resuelva: /pandora/node_modules.
WORKDIR /pandora
RUN npm install -D otplib          # p. ej. tests que necesitan un segundo factor TOTP
```

Constrúyala, póngala a disposición de la máquina que ejecuta los tests —el servidor de Discovery para `worker_mode = local`, el destino SSH para `remote`— y apunte a ella el campo **Docker image** de la tarea, por ejemplo `miempresa/pandora_playwright:noble-corp`.

Tres reglas para una imagen propia:

- **No mueva `WORKDIR` fuera de `/pandora`.** El runner escribe allí el test y la configuración generada por ruta absoluta, y ejecuta `cd /pandora` antes de `npx playwright test`.
- **Instale los paquetes npm en `/pandora`**, no globalmente. Node resuelve las importaciones de un test desde el árbol de su propio proyecto.
- **Mantenga `@playwright/test` y los navegadores en la misma versión.** Los navegadores están integrados en la imagen y `@playwright/test` solo controla la compilación de navegador con la que se publicó. Un desajuste no falla al construir la imagen; falla en tiempo de ejecución, normalmente como un navegador que no arranca:

    ```
    browserType.launch: Executable doesn't exist at /ms-playwright/chromium-1234/chrome-linux/chrome
    ```

Cambiar la versión de Playwright mueve el runtime contra el que se validó todo el plugin, así que vuelva a verificar el flujo de [Verificar la primera ejecución](#verificar-la-primera-ejecucion) y contraste la versión con la tabla de [Compatibilidad](#compatibilidad).

### Depurar un test

Cuando una transacción falla y la captura de pantalla y el `Full report` del plugin no bastan para ver qué ocurrió, hay dos formas de obtener evidencia más rica: dejar que la propia tarea la capture automáticamente (**Debug mode**), o entrar de forma interactiva en la imagen y consultar el informe HTML del propio Playwright. Ambas usan los mismos ajustes de captura —`trace: 'on-first-retry'`, `screenshot: 'only-on-failure'`, `video: 'retain-on-failure'`— pero los obtienen de sitios distintos: una ejecución de tarea, de la configuración generada; una ejecución manual, de una configuración que usted escribe dentro del contenedor (la imagen no incluye ninguna).

#### Debug mode (automatizado, por ejecución de tarea)

Active **Debug mode** en el paso **Advanced setup** de la tarea y establezca un **Debug directory** (consulte el valor por defecto y el marcador en [Marcador de identificador de tarea](#marcador-de-identificador-de-tarea)). La salida de depuración acaba siempre **centralizada en el servidor de Discovery**, en esa misma ruta, con independencia de `worker_mode`:

1. El runner borra y recrea el directorio de debug en el host Docker (el propio servidor de Discovery para `worker_mode = local`, o el worker SSH para `remote`), lo hace escribible para que el contenedor pueda escribir en él sea cual sea su usuario interno, y lo monta en el contenedor en `/pandora/debug`.
2. El test se ejecuta con la configuración generada, que lleva los ajustes de captura de depuración, y con `--output` redirigido a ese montaje, de modo que capturas, traza y vídeo aterrizan directamente bajo `<directorio_de_debug>/test-results/<test>/` en ese host.
3. El runner escribe un resumen `report.md` (estado, fases, errores) en el mismo directorio.
4. Solo para `worker_mode = remote`: el runner descarga el directorio de debug completo desde el worker remoto al servidor de Discovery (por la misma sesión SSH, en la misma ruta absoluta) y después elimina la copia remota, pero solo una vez confirmada la copia local en disco. Si la descarga falla, la copia remota se conserva en lugar de borrarse.
5. Por último, el runner escribe `manifest.json` en el directorio, relacionando cada agente reportado por esa ejecución con sus propios artefactos.

El directorio contiene los artefactos de **una sola ejecución**: se borra, no se acumula, en cada ejecución, así que solo se conserva la última. Es escribible por todos mientras una ejecución está en curso, así que ubíquelo en una ruta que solo puedan leer los operadores: las capturas, los vídeos y las instantáneas de página de una transacción monitorizada pueden contener contenido de sesión.

#### manifest.json: cómo relacionar los agentes con su evidencia

Un agente producido por este plugin toma su nombre únicamente del título del test; la tarea no interviene en ese nombre. La relación entre tareas y agentes es genuinamente N:M: una tarea produce muchos agentes y un agente puede provenir de muchas tareas. `manifest.json` resuelve ese vínculo desde el lado que puede poseerlo: el directorio de debug de cada tarea declara qué agentes produjo *esa* ejecución, de modo que un consumidor puede indexar todos los manifiestos por nombre de agente y obtener una correspondencia exacta.

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

Notas para los consumidores:

- Las rutas de `artifacts` son **relativas al directorio de debug** y solo cubren ficheros que Playwright escribió dentro de él; un test que pasa normalmente no tiene ninguno, ya que Playwright solo captura pantalla y vídeo al fallar.
- Las rutas de los artefactos proceden del propio reporter JSON de Playwright, no de recorrer directorios, así que siguen siendo correctas con independencia de cómo Playwright convierta los títulos de test en nombres de carpeta.
- El manifiesto se escribe **después** de la descarga remota, así que para las tareas `remote` describe ficheros que ya están en local. Un manifiesto ausente significa que la ejecución no capturó nada (falló la orquestación, o una descarga remota que no llegó a completarse).
- La extensión WUX Transactions de la consola consume exactamente este fichero para ofrecer evidencia de depuración por transacción.

#### Si la consola no muestra evidencia

La extensión lee el campo **Debug directory** de cada tarea —no hay ruta que configurar por su lado— y lista, en la parte superior de la vista, cada tarea con depuración activada cuya evidencia no ha podido leer, con el motivo:

| Motivo | Causa |
|--------|-------|
| No hay un directorio de debug absoluto establecido | Depuración activada con una ruta vacía o relativa. La ejecución también aborta, ya que el runner lo valida |
| El directorio no existe en esta consola | O la tarea aún no se ha ejecutado, o consola y servidor de Discovery son **hosts distintos**: la ruta solo es válida en el servidor. Comparta `data_in` por NFS o sincronícelo |
| El directorio existe pero no contiene `manifest.json` | Se está ejecutando una **versión antigua del plugin** (consulte [Instalar el plugin](#instalar-el-plugin)), la ejecución falló antes de capturar nada, o falló una descarga `remote`, en cuyo caso la evidencia sigue en el worker |
| Manifiesto ilegible o mal formado | Permisos, o una ejecución interrumpida a mitad de escritura |

#### Depuración interactiva manual

**1. Arranque el contenedor**, montando directamente su test `.ts` si ya lo tiene:

```bash
docker run -it --rm \
  -v "$(pwd)/test.spec.ts:/pandora/test.spec.ts" \
  -p 9323:9323 \
  pandorafms/pandora_playwright:noble bash
```

O arránquelo sin montar nada y escriba el test dentro del contenedor.

**2. Escriba una configuración de depuración.** La imagen no incluye configuración de Playwright: una ejecución de tarea genera la suya y la descarta con el contenedor. Para una ejecución manual, escriba una usted mismo dentro de `/pandora`. `video` y `reporter` no tienen opción de línea de comandos, así que una configuración es la única forma de obtenerlos:

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

**3. Ejecute el test con ella:**

```bash
npx playwright test test.spec.ts --config=playwright.config.debug.ts --browser=chromium --timeout=30000
```

**4. Sirva y consulte el informe:**

```bash
npx playwright show-report --host 0.0.0.0 --port 9323
```

Con `-p 9323:9323` publicado en el `docker run`, abra `http://localhost:9323` en el host para navegar el informe: resultados por paso, el visor de trazas y el **vídeo del fallo**. El servidor del informe escucha en todas las interfaces dentro del contenedor, así que publique el puerto solo en una red de confianza y detenga el contenedor al terminar.

### Solución de problemas

- **`docker: ... name is already in use`** — una ejecución anterior se interrumpió antes de su limpieza y dejó el contenedor que posee el nombre derivado de esta tarea; su `sleep` puede retener el nombre hasta que termine el TTL. El contenedor siempre se arranca con `--rm`, así que un contenedor huérfano libera el nombre por sí solo cuando termina el `sleep`. Para recuperarlo de inmediato, elimínelo (`docker rm -f <nombre del contenedor>`) o active **Remove existing container with the same task name** en el paso Advanced setup de la tarea para que el runner lo haga antes de cada ejecución.
- **`Playwright produced no report`** — el test no llegó a ejecutarse (error de sintaxis, importación incorrecta, navegador ausente), o la ejecución superó el TTL del contenedor. Ejecute con `-v` y lea el stderr del `docker exec`; consulte [TTL del contenedor](#ttl-del-contenedor-el-unico-limite-que-aborta-una-ejecucion-completa).
- **La captura de pantalla se muestra como texto y no como imagen** — el valor debe ser `generic_data_string` con el prefijo `data:image/png;base64,`, de lo que se encarga el plugin; compruebe que el servidor de Discovery ejecuta una versión que lo incluya, consulte [Instalar el plugin](#instalar-el-plugin).
- **`Cannot find module '@playwright/test'`** — el test debe ejecutarse desde `/pandora` dentro de la imagen para que Node resuelva `node_modules`; el plugin lo copia allí por ese motivo. Una imagen propia que mueva `WORKDIR` rompe esto, consulte [Usar una imagen Docker propia](#usar-una-imagen-docker-propia).
- **Los agentes acaban en el grupo equivocado (modo `-x`)** — el XML de agente de Pandora FMS espera el **nombre** del grupo, no el identificador numérico, así que `-g 0` es el único valor que garantiza el resultado esperado salvo que exista un grupo llamado exactamente como el número que pase. La ruta `monitoring_data` de Discovery sí usa correctamente el identificador numérico de grupo.
- **Una fase posterior muestra «ok» tras un fallo anterior** — con aserciones duras una fase fallida aborta la ejecución, así que las fases posteriores conservan su valor anterior. Use `expect.soft()` si quiere medir todas las fases en cada ejecución.
- **El formulario de la tarea en la consola sigue ejecutando una versión antigua** — actualice la copia bajo `<remote_config>/discovery/`, no solo el adjunto de la consola. Consulte [Instalar el plugin](#instalar-el-plugin).

## Referencia

### Parámetros de la tarea

La consola presenta los campos de la tarea en **cuatro pasos del asistente**: Basic setup, Worker setup (solo para `remote`), Test setup y Advanced setup. La columna de macro es el identificador usado en la configuración almacenada de la tarea.

#### Basic setup

| Campo | Macro | Valores | Por defecto | Notas |
|-------|-------|---------|-------------|-------|
| Worker mode | `_workerMode_` | `local`, `remote` | `local` | `remote` ejecuta Docker en un host SSH |
| Browser | `_browser_` | `chromium`, `firefox`, `webkit` | `chromium` | |

#### Worker setup (solo se muestra para `remote`)

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|-------------|-------|
| SSH address | `_sshAddress_` | cadena | — | Host que ejecuta Docker |
| SSH port | `_sshPort_` | número | `22` | |
| SSH user | `_sshUser_` | cadena | `root` | Debe poder ejecutar Docker; root no es obligatorio |
| SSH password | `_sshPassword_` | contraseña | — | Cifrable |
| Encrypt password | `_sshPasswordEncrypt_` | casilla | activada | Almacena la contraseña cifrada en la configuración de la tarea |
| Temporal folder | `_sshTemp_` | cadena | `/tmp` | Dónde se copia el fichero de test en el host |

#### Test setup

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|-------------|-------|
| Docker image | `_dockerImage_` | cadena | `pandorafms/pandora_playwright:noble` | Consulte [Usar una imagen Docker propia](#usar-una-imagen-docker-propia) |
| Browser width | `_browserWidth_` | número | `1920` | Ancho del viewport en píxeles, aplicado a través de la configuración generada, ya que `viewport` no tiene opción de línea de comandos. Un valor no positivo revierte al valor por defecto |
| Browser height | `_browserHeight_` | número | `1080` | Alto del viewport en píxeles, con el mismo mecanismo que el ancho |
| Test timeout | `_globalTimeout_` | número | `120` | Tiempo de espera global en **segundos** para cada test: el presupuesto de un `test(...)` completo, no por paso y no por tarea. También deriva el TTL del contenedor. Consulte [Tiempos de espera](#tiempos-de-espera) |
| Generate error history module | `_errorHistoryModule_` | casilla | desactivada | Añade un módulo de cadena síncrono por estado y por fase (`OK` o el texto del error), de modo que Pandora FMS conserva una serie histórica de valores de error |
| Send full report | `_fullReport_` | casilla | desactivada | Añade un módulo de informe de texto detallado |
| Full report agent name | `_reportAgent_` | cadena | — | Agente que aloja el informe completo; vacío usa el agente del primer test. Solo se muestra cuando **Send full report** está marcado |
| Prefix for agents created | `_prefixAgents_` | cadena | — | Opcional. Se antepone al título del test al derivar el nombre y el alias del agente, de forma que dos tareas que ejecuten un test con el mismo título no compartan agente. Vacío mantiene intactos la nomenclatura original y los agentes existentes |
| Playwright test (.ts) | `_playwrightTest_` | área de texto | — | El contenido completo del fichero de test |

#### Advanced setup

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|-------------|-------|
| Debug mode | `_debug_` | casilla | desactivada | Ejecuta el test con la configuración de depuración de Playwright (traza, captura de pantalla, vídeo) y deja los artefactos en el directorio de debug. Consulte [Depurar un test](#depurar-un-test) |
| Debug directory | `_debugDirectory_` | cadena | `/var/spool/pandora/data_in/discovery/tmp/playwright/_taskid_` | **Ruta absoluta** en la máquina que ejecuta realmente Docker —el servidor de Discovery local para `worker_mode = local`, o el host SSH remoto para `remote`—, **no** en esta consola. Docker rechaza directamente una ruta relativa de montaje, así que el runner valida que la ruta sea absoluta y falla de inmediato si no lo es. Obligatorio cuando el modo debug está activado: el formulario de la consola no puede expresar un campo obligatorio condicional, así que el runner también lo valida. Consulte [Marcador de identificador de tarea](#marcador-de-identificador-de-tarea) |
| Remove existing container with the same task name | `_overrideContainer_` | casilla | desactivada | El runner arranca siempre el contenedor de test con `--rm`, así que un contenedor huérfano de una ejecución interrumpida se elimina solo cuando termina su `sleep` y libera el nombre de la tarea. Al activarlo, el runner elimina además (`docker rm -f`) cualquier contenedor que ya posea el nombre derivado de esta tarea antes de arrancar, para que un resto no pueda bloquear la siguiente ejecución con un error «name already in use» de Docker. Actívelo solo si se encuentra con ese error: si la misma tarea llega a lanzarse dos veces a la vez, esto elimina también la otra instancia en ejecución |
| Advanced timeouts | `_advancedTimeouts_` | casilla | desactivada | Expone los tres tiempos de espera por paso de Playwright, que no tienen opción de línea de comandos. Al activarlo, los tres valores siguientes se añaden a la configuración generada. **El fichero de test nunca se modifica.** Consulte [Tiempos de espera](#tiempos-de-espera) |
| Action timeout | `_actionTimeout_` | número | `0` | Segundos para cada acción (`click`, `fill`, `press`, `check`, `selectOption`...). `0` = sin límite, el valor por defecto de Playwright. Solo se muestra cuando **Advanced timeouts** está marcado |
| Navigation timeout | `_navigationTimeout_` | número | `0` | Segundos para cada navegación (`goto`, `waitForURL`, `waitForNavigation`, `reload`). `0` = sin límite, el valor por defecto de Playwright. Solo se muestra cuando **Advanced timeouts** está marcado |
| Expect timeout | `_expectTimeout_` | número | `5` | Segundos para cada aserción web-first (`expect(locator).toBeVisible()`, `toHaveText`...). El valor por defecto de Playwright es `5`; `0` = sin límite. Solo se muestra cuando **Advanced timeouts** está marcado |

### Configuración JSON de la tarea

En el momento de la ejecución, el servidor de Discovery invoca el plugin con el comando declarado por la definición de la aplicación, sustituyendo las macros de la tarea:

```
'_exec1_' -c '_tempfileConf_' -s '_tempfileTest_' -t __taskMD5__ -i __taskInterval__ -g __taskGroupID__
```

`_tempfileConf_` se expande a la configuración JSON de la tarea, `_tempfileTest_` al contenido del fichero de test, y `__taskMD5__` es `md5(id_rt)`. Ese mismo JSON es el que pasa una ejecución manual por CLI con `-c`:

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

### Ejecución por línea de comandos

El punto de entrada del runner es el ejecutable `pandora_playwright`. Una ejecución manual reproduce lo que hace el servidor de Discovery en cada ejecución de tarea, pero sin `id_rt`: deriva el nombre del contenedor Docker del nombre de tarea de `-t` (aplicándole un hash cuando no es ya un md5) en lugar de usar `md5(id_rt)`.

```
pandora_playwright -c <conf.json> -s <test.ts> -t <nombre_tarea> [opciones]
```

| Opción | Larga | Obligatoria | Por defecto | Descripción |
|--------|-------|-------------|-------------|-------------|
| `-c` | `--conf` | sí | — | Ruta a la configuración JSON de la tarea |
| `-s` | `--test` | sí | — | Ruta al fichero `.ts` de test de Playwright |
| `-t` | `--task` | sí | — | Nombre de la tarea (usado para derivar el nombre del contenedor) |
| `-i` | `--interval` | no | `300` | Intervalo del agente (segundos) |
| `-g` | `--group` | no | `0` | Identificador de grupo para los agentes creados |
| `-x` | `--xml_mode` | no | desactivada | Construye el XML de agente y lo envía mediante Tentacle |
| `-S` | `--server` | no | `127.0.0.1:41121` | `servidor:puerto` de Tentacle (con `-x`) |
| `-T` | `--temp` | no | `/tmp` | Carpeta temporal para el XML (con `-x`) |
| `-v` | `--verbose` | no | desactivada | Traza paso a paso por STDERR |

Ejemplos:

```bash
# Ejecución local: STDOUT son los datos de monitorización de Discovery
./pandora_playwright -c conf.json -s transaction.spec.ts -t <NOMBRE_TAREA> -g 0

# Ejecución remota por SSH (conf.json fija worker_mode = remote)
./pandora_playwright -c conf_remote.json -s transaction.spec.ts -t <NOMBRE_TAREA> -g 0

# De extremo a extremo contra un Tentacle de Pandora FMS: crea agentes y módulos reales
./pandora_playwright -x -S 127.0.0.1:41121 \
    -c conf.json -s transaction.spec.ts -t <NOMBRE_TAREA> -g 0 -T /tmp
```

`password_encrypter` cifra un valor para el campo `ssh_password` y admite `-e/--encrypt`, `-d/--decrypt` y `-p/--password <contraseña>` (`-e` y `-d` son mutuamente excluyentes):

```bash
./password_encrypter -e -p <SSH_PASSWORD>
```

Pasar un secreto como argumento de línea de comandos lo expone en el historial del shell y en la lista de procesos del sistema operativo de esa máquina. Borre después la entrada del historial, o ejecútelo en un host donde eso sea aceptable.

#### Modo detallado

`-v` imprime por STDERR una traza paso a paso con marca de tiempo. Registra literalmente cada comando de Docker y SSH (`$` local, `ssh$` remoto), además del resumen de configuración, el tamaño del informe, la recogida de la captura de pantalla, la construcción por agente, el tamaño del informe completo y la emisión. Ejemplo (remoto):

```
Task <id>: worker=remote browser=chromium image=...:noble timeout=15s ...
Connecting SSH to <SSH_HOST>:22 as <SSH_USER>
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

### Marcador de identificador de tarea

El campo **Debug directory** admite un marcador `_taskid_`, sustituido en tiempo de ejecución por `md5(id_rt)`, el mismo valor que Discovery calcula internamente como `__taskMD5__`. Es una convención propia del plugin, no una funcionalidad de Discovery: las macros propias de Discovery se sustituyen en el servidor en el momento de la ejecución, de modo que el valor por defecto de un campo llega al plugin de forma literal, y es el propio plugin el que realiza esta sustitución una vez que el valor ha llegado dentro de la configuración JSON de la tarea. Cualquier otra herramienta con acceso al `id_rt` de la tarea puede recalcular el mismo valor y llegar exactamente al mismo nombre de directorio, que es como la extensión de consola localiza la evidencia de una tarea.

Sustitúyalo por una ruta absoluta fija para reutilizar la misma carpeta entre ejecuciones de una tarea distinta. En una ejecución manual por CLI (`-t <nombre_tarea>` con un nombre legible) el plugin aplica un hash a ese nombre, ya que `-t` se convierte además en el nombre del contenedor Docker.

### Identidad del plugin

| Campo | Valor |
|-------|-------|
| Nombre corto de la aplicación | `pandorafms.playwright.1` |
| Identificador de la aplicación | `10` |
| Versión del plugin | `1.0` |
| Tipo | Aplicación de Discovery (`.disco`) |
| Sección | Discovery → Applications |
