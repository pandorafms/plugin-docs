# Selenium 4 Discovery

*Última actualización del artículo: 2026-09-08.*

## Qué monitoriza

El plugin de Discovery de Selenium 4 (WUX, monitorización de experiencia de usuario web) ejecuta transacciones web grabadas con la extensión de navegador Selenium IDE contra un navegador real de Google Chrome o Mozilla Firefox y convierte cada prueba grabada en un agente de Pandora FMS con los resultados de la transacción. Lee la transacción de un archivo `.side` de Selenium IDE (formato Selenium JSON) y maneja el navegador mediante la API WebDriver de Selenium 4.

Una tarea de Discovery puede ejecutar las pruebas grabadas en cuatro modos: un driver de Selenium local en el servidor de Pandora FMS, un servidor remoto de Selenium 4, un contenedor de Docker en el servidor de Discovery, o un contenedor de Docker en un worker remoto alcanzado por SSH. Se crea un agente por cada prueba del proyecto, más un agente por proyecto con estadísticas de conexión cuando **Monitor time statistics** está habilitado.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Versión del plugin `1.8` (`pandorafms.selenium.4`) | Objetivo documentado | La versión que describe esta página, identificada en la definición del paquete. Consulte [Identidad del plugin](#identidad-del-plugin). |
| Discovery de Pandora FMS, versión `780` o posterior | `Compatible conocido` | El manual oficial de WUX indica que el WUX centralizado en Discovery se basa en Selenium 4, está disponible desde Pandora FMS 780 y es el método recomendado desde la versión 782. |
| Google Chrome y Mozilla Firefox | `Soportado` | El manual oficial de WUX describe el plugin ejecutando transacciones con estos navegadores y recomienda usar el mismo navegador donde se grabó la transacción. |
| Un sistema operativo concreto del host del worker | `Sin validar` | Ningún registro de pruebas publicado demuestra compatibilidad con sistemas operativos para la máquina que ejecuta las pruebas. |
| Un servidor de Selenium 4 accesible por HTTP | `Requerido` | El modo Remote Driver se conecta al endpoint de WebDriver de la URL configurada. Prerrequisito, no una declaración de compatibilidad. |
| Un motor de Docker | `Requerido` | Los modos Docker ejecutan el contenedor del navegador en el servidor de Discovery (Local Docker) o en el worker por SSH (Remote Docker). Prerrequisito, no una declaración de compatibilidad. |
| `curl` para las estadísticas de conexión | `Requerido` | Las estadísticas de URL se miden con `curl`. Prerrequisito, no una declaración de compatibilidad. |
| Una cuenta SSH capaz de iniciar contenedores de Docker y escribir en el directorio temporal | `Requerido` | El modo Remote Docker copia el plugin y la transacción al worker y ejecuta Docker allí. Prerrequisito, no una declaración de compatibilidad. |

### Requisitos

1. **Un servidor de Pandora FMS con Discovery habilitado** para ejecutar la tarea, y una consola para definirla.
2. **Una transacción grabada con Selenium IDE** (extensión de Google Chrome o Mozilla Firefox). El proyecto se exporta como un archivo `.side`, cuyo contenido JSON se pega en el campo **Selenium IDE JSON** de la tarea.
3. **Un grupo de agentes de destino y un intervalo de monitorización** para los agentes generados, tomados de la tarea de Discovery. Los agentes se crean en ese grupo por su ID y heredan el intervalo.
4. **El modo de ejecución elegido, preparado en la máquina que lo ejecuta.** Consulte [Preparar el modo de ejecución](#preparar-el-modo-de-ejecucion).

El plugin se distribuye como una aplicación de Discovery de Pandora FMS (paquete `.disco`) con sus dependencias de ejecución empaquetadas, por lo que no es necesario instalar paquetes de Python en el servidor de Discovery. El paquete incluye también los helpers `worker_setup` y `password_encrypter` que usa el asistente de Discovery.

### Preparar el modo de ejecución

**Local Driver.** El plugin usa Google Chrome o Mozilla Firefox instalados en la máquina donde se ejecuta la tarea. Los binarios se buscan por defecto en `/usr/share/pandora_server/util/selenium_headless_drivers/` (`chrome/google-chrome`, `chromedriver`, `firefox/firefox`, `geckodriver`); un paquete de drivers para estas rutas está disponible en la librería de Pandora FMS, o puede configurar rutas distintas en la tarea. También deben instalarse las dependencias del sistema del navegador: para Firefox `gtk3`, `alsa-lib` y `libX11-xcb`; para Google Chrome `nss`, `libdrm` y `mesa-libgbm`. La tarea ejecuta el navegador en modo headless o en un display virtual (Xvfb); en caso contrario, la máquina necesita un escritorio físico conectado.

**Remote Driver.** El plugin se conecta a un servidor de Selenium 4 mediante su endpoint de WebDriver, por ejemplo `http://<SELENIUM_SERVER>:4444/wd/hub`. El servidor de Discovery debe poder alcanzar ese endpoint; el puerto de escucha por defecto de un Selenium Grid es `4444`.

**Local Docker.** El plugin inicia un contenedor de Docker en el servidor de Discovery con una imagen que incluye los navegadores y los drivers en `/tmp/lib`. La imagen por defecto es `pandorafms/pandora_selenium_headless:el9`; asegúrese de que esté disponible en el servidor (por ejemplo con `docker pull`). La imagen incluye `curl` para las estadísticas de conexión.

**Remote Docker.** El plugin se conecta por SSH a un worker remoto que tiene Docker, se copia a sí mismo y el archivo de transacción, y ejecuta el contenedor de Docker de forma remota. El usuario de SSH debe poder iniciar contenedores y escribir en el directorio temporal (por defecto `/tmp`). El asistente cifra la contraseña de SSH antes de guardarla en la configuración de la tarea.

Los perfiles de navegador son opcionales en todos los modos. La ruta de un **Firefox profile**, el **User data dir** de Chrome y un **profile** de Chrome deben existir en la máquina que inicia el navegador; en los modos Docker esas carpetas se montan como volúmenes dentro del contenedor, por lo que las rutas se leen del host que ejecuta Docker.

### Instalar el plugin

Cargue el paquete `.disco` desde **Management → Discovery → Extension manager** (la vista *Manage disco packages*). El paquete está disponible en la librería de Pandora FMS en la [entrada de Marketplace de Selenium 4](https://marketplace.pandorafms.com/entries/pandorafms.selenium.4). Una vez cargado, **Selenium 4** aparece en la categoría **Applications** del asistente de Discovery.

## Configurar la tarea de Discovery

Cree la tarea desde **Management → Discovery → Applications → Selenium 4**. El primer paso genérico define la tarea; el paquete añade **Basic setup**, **Worker setup** y **Test setup**. Todos los campos están documentados en [Parámetros de la tarea](#parametros-de-la-tarea).

**Paso 1 — Task definition.** Nombre, grupo de agentes, servidor e intervalo. El ID del grupo y el intervalo se pasan al plugin y se aplican a todos los agentes generados.

**Paso 2 — Basic setup.** Modo de ejecución y navegador:

- **Worker mode** selecciona dónde se ejecutan las pruebas: **Local server** o **Remote server**.
- **Run mode** selecciona cómo se maneja el navegador: **Selenium driver** o **Docker image**.
- **Browser** selecciona **Mozilla Firefox** o **Google Chrome**. Pandora recomienda usar el mismo navegador donde se grabó la transacción.

![Paso Basic setup de la tarea de Discovery de Selenium 4: selectores de Worker mode, Run mode y Browser.](../assets/images/discovery/selenium-4/basic-setup.png)
**Paso 3 — Worker setup.** Los campos que se muestran dependen de la combinación elegida en el Paso 2:

- **Remote server + Selenium driver**: **Driver URL**, el endpoint de WebDriver de Selenium 4, por ejemplo `http://192.168.1.10:4444/wd/hub`.
- **Remote server + Docker image**: **SSH address**, **SSH port** (por defecto `22`), **SSH user**, **SSH password** (cifrada por defecto mediante **Encrypt password**) y **Temporal folder** (por defecto `/tmp`).
- **Docker image** (en cualquiera de los modos Docker): nombre de la imagen. Déjelo vacío para usar la imagen por defecto `pandorafms/pandora_selenium_headless:el9`. La imagen debe contener los drivers del navegador en `/tmp/lib`.
- **Firefox**: **Geckodriver path** y **Firefox binary path** (solo Local server + Selenium driver), y **Firefox profile** (cualquier modo).
- **Chrome**: **Chromedriver path** y **Chrome binary path** (solo Local server + Selenium driver), **User data dir** y **Chrome profile** (cualquier modo).
- **Local server + Selenium driver**: **Virtual display** y **Headless browser**. Pandora recomienda dejar ambos habilitados.

![Paso Worker setup de Selenium 4 para Local server + Selenium driver (Chrome).](../assets/images/discovery/selenium-4/worker-local-driver.png)

![Paso Worker setup de Selenium 4 para Local server + Docker image (Chrome).](../assets/images/discovery/selenium-4/worker-local-docker.png)

![Paso Worker setup de Selenium 4 para Remote server + Docker image (Chrome).](../assets/images/discovery/selenium-4/worker-remote-docker.png)

![Paso Worker setup de Selenium 4 para Remote server + Selenium driver (Chrome).](../assets/images/discovery/selenium-4/worker-remote-driver.png)

**Paso 4 — Test setup.** Comportamiento de la transacción:

- **Accept insecure certs** acepta certificados TLS autofirmados o no válidos durante la transacción.
- **Monitor time statistics** crea el agente de estadísticas del proyecto con las temporizaciones de conexión a la URL principal de la transacción.
- **Browser width** y **Browser height** fijan el tamaño de la ventana del navegador (por defecto `1920`×`1080`).
- **Global timeout** es el tiempo de espera por defecto, en segundos, para los comandos de Selenium y para operaciones como la apertura de la sesión (por defecto `10`).
- **Wait between commands** añade una pausa, en segundos, entre los comandos de la transacción (por defecto `0.15`).
- **Monitor errors** crea módulos de cadena dedicados — `Global error` y `Phase <N> error` — que informan de `OK` o del último texto de error de cada transacción y fase, conservando el historial de fallos.
- **Selenium IDE JSON** contiene el contenido JSON completo del archivo `.side` grabado.

![Paso Test setup de la tarea de Discovery de Selenium 4.](../assets/images/discovery/selenium-4/test-setup.png)

Cuando **Encrypt password** está habilitada, la contraseña de SSH se cifra con el helper `password_encrypter` incluido antes de guardarla en la configuración de la tarea, y el plugin la descifra cuando la tarea se ejecuta.

## Verificar la primera ejecución

Fuerce la tarea desde **Management → Discovery → Task list** y compruebe el resultado en este orden.

1. **El resumen de la tarea** informa de las pruebas parseadas y de los agentes generados. Espere que **Tests parsed** coincida con las pruebas del proyecto y que **Agents count** coincida con el número de agentes de prueba, más el agente de estadísticas cuando **Monitor time statistics** está habilitado.

2. **Los agentes.** Aparece un agente `WUX Discovery - <nombre de la prueba>` por cada prueba del proyecto, y un agente `WUX Discovery - <nombre del proyecto>` cuando **Monitor time statistics** está habilitado.

3. **Los módulos de transacción.** Todo agente de prueba lleva **Global status** (`1` en éxito), **Global time** (segundos) y **Last error screenshot** (una captura cuando la prueba falla, `None` cuando tiene éxito).

4. **Los módulos de estadísticas.** Cuando **Monitor time statistics** está habilitado, el agente del proyecto lleva **URL status** y los módulos de temporización **URL stat**.

Si no aparece ningún agente, lo primero que hay que revisar son los requisitos del modo de ejecución: drivers, Docker, acceso SSH o la URL del servidor de Selenium.

![Resumen de ejecución de una tarea de Discovery de Selenium 4.](../assets/images/discovery/selenium-4/task-summary.png)

## Interpretar los resultados

### Agentes e identidad

El plugin crea un agente por cada prueba del proyecto de Selenium IDE, llamado `WUX Discovery - <nombre de la prueba>`, y un agente por proyecto, llamado `WUX Discovery - <nombre del proyecto>`, solo cuando **Monitor time statistics** está habilitado. Los agentes se crean en el grupo de la tarea (por ID) y heredan su intervalo.

El nombre interno de Pandora FMS de cada agente es `a` + el hash MD5 del nombre de la prueba o del proyecto, de modo que las ejecuciones repetidas de la misma tarea actualizan los mismos agentes, y renombrar una prueba o un proyecto en Selenium IDE cambia el agente.

### Módulos por agente

| Agente | Se crea cuando | Módulos que lleva |
| --- | --- | --- |
| `WUX Discovery - <nombre de la prueba>` | El proyecto contiene una prueba | `Global status`, `Global time`, `Last error screenshot`; `Phase <nombre> status`, `Phase <nombre> time` y, con **Monitor errors**, `Phase <nombre> error` por cada fase; módulos personalizados |
| `WUX Discovery - <nombre del proyecto>` | **Monitor time statistics** habilitado | `URL status`, `URL stat TT`, `URL stat DNS`, `URL stat TTCP`, `URL stat TST`, `URL stat TTC` y, para URLs HTTPS, `URL stat TSSL` |

**Global time** mide la ejecución completa de la prueba, incluido el tiempo que el navegador tarda en abrirse y cerrarse, por lo que no es necesariamente la suma de los tiempos de las fases. **Last error screenshot** se declara crítico cuando contiene una captura, es decir, cuando la prueba falló. El texto del error se conserva en la descripción de **Global status** y, con **Monitor errors**, en los módulos **Global error** y de error de fase.

El inventario exhaustivo de módulos y los comandos de transacción están en [Módulos y agentes generados](#modulos-y-agentes-generados) y en [Comandos para archivos SIDE](#comandos-para-archivos-side).

## Operación

### Ejecución manual

El plugin puede ejecutarse fuera de Discovery, desde un agente de Pandora FMS (como plugin de agente) o directamente desde la línea de comandos. La ejecución necesita un archivo de configuración y un archivo `.side`, ambos creados manualmente:

```bash
./pandora_selenium -c <PATH_TO_CONFIG> -s <PATH_TO_SIDE> -t <TASK_NAME> -i <AGENT_INTERVAL> -g <GROUP_ID> -x
```

El parámetro `-x` hace que el plugin genere archivos XML de agentes y los envíe por Tentacle en lugar de imprimir la salida JSON de Discovery. Use `-S <SERVER>:<PORT>` para apuntar a un servidor de Tentacle cuando no sea el por defecto (`127.0.0.1:41121`). Cada XML corresponde a un agente generado distinto, nunca al agente que ejecuta el plugin.

El plugin también acepta `-v` para mensajes de progreso detallados en la salida estándar de error.

### Depuración

Ejecute el plugin con `-v` (o `--verbose`) para imprimir el progreso de la ejecución, incluida la prueba, el comando, el target y el valor actuales, en la salida estándar de error. En los modos Docker el mismo parámetro se reenvía a la ejecución dentro del contenedor.

## Solución de problemas

| Síntoma | Comprobación |
| --- | --- |
| No se crea ningún agente y la tarea falla | Revise el modo de ejecución: binarios y drivers del navegador presentes en **Local Driver**, servidor de Selenium accesible en **Remote Driver**, imagen de Docker disponible y motor en marcha en los modos **Docker**, conectividad y permisos SSH en **Remote Docker**. |
| La creación de la sesión falla o agota el tiempo | **Global timeout** acota también la apertura de la sesión; un valor demasiado bajo o un driver/navegador inalcanzable la abortan. Compruebe las rutas del navegador y del driver. |
| Una tarea de Local Driver no puede iniciar el navegador | Confirme las dependencias del sistema del navegador (`gtk3`, `alsa-lib`, `libX11-xcb` para Firefox; `nss`, `libdrm`, `mesa-libgbm` para Chrome) y que **Virtual display** o **Headless browser** esté habilitado, o que haya un escritorio físico conectado. |
| Una tarea de Remote Driver no puede conectarse | Compruebe la **Driver URL** y que el servidor de Discovery pueda alcanzar el servidor de Selenium por su puerto (por defecto `4444`). |
| Una tarea Docker informa de una imagen ausente o de errores de Docker | Descargue la **Docker image** configurada en la máquina que ejecuta Docker y verifique el motor y los permisos del usuario. |
| Una tarea de Remote Docker falla al autenticarse | Confirme **SSH address**, **SSH port**, **SSH user** y **SSH password**, y que la contraseña cifrada se generó para este plugin. El usuario de SSH debe poder iniciar contenedores y escribir en el **Temporal folder**. |
| Faltan módulos de estadísticas o están a `0` | **Monitor time statistics** requiere `curl` en la máquina que ejecuta el plugin (incluido en la imagen Docker por defecto). En el modo Remote Driver las estadísticas se miden desde el servidor de Discovery, no desde el servidor de Selenium. |
| La tarea informa de un error de parseo de SIDE | El campo **Selenium IDE JSON** debe contener el contenido JSON del archivo `.side` exportado. |
| Una prueba falla con `Global status` a `0` | Abra el módulo **Last error screenshot** y la descripción de **Global status** para ver el texto del fallo. Las fases y los módulos de error apuntan al comando que falló. |
| Un comando de Selenium IDE parece ignorarse | Los comandos que no están en la [lista de soportados](#comandos-para-archivos-side) se omiten silenciosamente. Los comandos que generan módulos deben empezar por `//`. |

## Referencia

### Parámetros de la tarea

La consola presenta los campos de la tarea en tres pasos después de la definición genérica. La columna de macro es el identificador que se usa en la configuración de la tarea generada.

#### Basic setup

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Worker mode | `_workerMode_` | select | `local` | `local` (Local server) o `remote` (Remote server) |
| Run mode | `_runMode_` | select | `docker` | `driver` (Selenium driver) o `docker` (Docker image) |
| Browser | `_browser_` | select | `chrome` | `chrome` (Google Chrome) o `firefox` (Mozilla Firefox) |

#### Worker setup

Los campos que se muestran dependen de **Worker mode**, **Run mode** y **Browser**.

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Driver URL | `_driverURL_` | string | — | Endpoint de WebDriver de Selenium 4. Solo **Remote server + Selenium driver** |
| SSH address | `_sshAddress_` | string | — | Worker remoto que ejecuta Docker. Solo **Remote server + Docker image** |
| SSH port | `_sshPort_` | number | `22` | Puerto SSH. Solo **Remote server + Docker image** |
| SSH user | `_sshUser_` | string | `root` | Usuario SSH con permisos de Docker. Solo **Remote server + Docker image** |
| SSH password | `_sshPassword_` | password | — | Contraseña SSH, cifrada cuando **Encrypt password** está habilitado. Solo **Remote server + Docker image** |
| Encrypt password | `_sshPasswordEncrypt_` | checkbox | on | Cifra la contraseña SSH en la configuración de la tarea. Solo **Remote server + Docker image** |
| Temporal folder | `_sshTemp_` | string | `/tmp` | Carpeta donde se copian el plugin y la transacción en el worker. Solo **Remote server + Docker image** |
| Docker image | `_dockerImage_` | string | `pandorafms/pandora_selenium_headless:el9` | Imagen con los navegadores y los drivers en `/tmp/lib`. Solo modos Docker |
| Geckodriver path | `_geckodriver_` | string | `/usr/share/pandora_server/util/selenium_headless_drivers/geckodriver` | Solo Local server + Selenium driver + Firefox |
| Firefox binary path | `_firefoxBinary_` | string | `/usr/share/pandora_server/util/selenium_headless_drivers/firefox/firefox` | Solo Local server + Selenium driver + Firefox |
| Firefox profile | `_firefoxProfile_` | string | — | Carpeta del perfil de Firefox; debe existir en la máquina que inicia el navegador |
| Chromedriver path | `_chromedriver_` | string | `/usr/share/pandora_server/util/selenium_headless_drivers/chromedriver` | Solo Local server + Selenium driver + Chrome |
| Chrome binary path | `_chromeBinary_` | string | `/usr/share/pandora_server/util/selenium_headless_drivers/chrome/google-chrome` | Solo Local server + Selenium driver + Chrome |
| User data dir | `_chromeUserDataDir_` | string | — | Directorio de datos de Chrome; debe existir en la máquina que inicia el navegador |
| Chrome profile | `_chromeProfile_` | string | — | Carpeta del perfil de Chrome dentro del directorio de datos |
| Virtual display | `_virtualDisplay_` | checkbox | on | Ejecuta el navegador en un display virtual (Xvfb). Solo Local server + Selenium driver |
| Headless browser | `_headless_` | checkbox | on | Ejecuta el navegador en modo headless. Solo Local server + Selenium driver |

#### Test setup

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Accept insecure certs | `_acceptInsecureCerts_` | checkbox | off | Acepta certificados TLS no válidos durante la transacción |
| Monitor time statistics | `_monitorStats_` | checkbox | on | Crea el agente de estadísticas del proyecto con las temporizaciones de conexión |
| Browser width | `_browserWidth_` | number | `1920` | Anchura de la ventana del navegador en píxeles |
| Browser height | `_browserHeight_` | number | `1080` | Altura de la ventana del navegador en píxeles |
| Global timeout | `_globalTimeout_` | number | `10` | Tiempo de espera por defecto en segundos para los comandos de Selenium y la apertura de la sesión. El plugin usa `5` cuando la clave no está presente |
| Wait between commands | `_waitBetweenCommands_` | number | `0.15` | Segundos de espera entre cada comando de la transacción |
| Monitor errors | `_monitorErrors_` | checkbox | off | Crea los módulos de cadena `Global error` y `Phase <N> error` |
| Selenium IDE JSON | `_side_` | textarea | — | Contenido JSON completo del archivo `.side` de Selenium IDE |

### Archivo de configuración

La tarea de Discovery construye un archivo JSON temporal a partir de sus propios campos y lo pasa al plugin con `-c`. Una ejecución manual suministra ese archivo directamente. Las claves marcadas como *solo tarea* las escribe el asistente; las demás se leen cuando están presentes.

| Clave | Por defecto | Descripción |
| --- | --- | --- |
| `worker_mode` | — | `local` o `remote` |
| `run_mode` | — | `driver` o `docker` |
| `browser` | — | `chrome` o `firefox` |
| `driver_url` | — | Endpoint de WebDriver de Selenium 4. Solo modo remote driver |
| `ssh_address` | — | Dirección del worker remoto. Solo modo remote docker |
| `ssh_port` | `22` | Puerto SSH. Solo modo remote docker |
| `ssh_user` | `root` | Usuario SSH. Solo modo remote docker |
| `ssh_password` | — | Contraseña SSH, en claro o cifrada. Solo modo remote docker |
| `ssh_password_encrypt` | `0` | `1` descifra la contraseña SSH con la clave embebida |
| `ssh_temp_folder` | `/tmp` | Carpeta temporal para los archivos copiados al worker. Solo modo remote docker |
| `docker_image` | `pandorafms/pandora_selenium_headless` | Imagen de Docker; el asistente escribe `pandorafms/pandora_selenium_headless:el9` |
| `chromedriver_path` | `/usr/share/pandora_server/util/selenium_headless_drivers/chromedriver` | Modo local driver, Chrome |
| `chrome_binary_path` | `/usr/share/pandora_server/util/selenium_headless_drivers/chrome/google-chrome` | Modo local driver, Chrome |
| `chrome_user_data_dir` | Vacío | Directorio de datos de Chrome; se monta en el contenedor en los modos Docker |
| `chrome_profile` | Vacío | Carpeta del perfil de Chrome dentro del directorio de datos |
| `geckodriver_path` | `/usr/share/pandora_server/util/selenium_headless_drivers/geckodriver` | Modo local driver, Firefox |
| `firefox_binary_path` | `/usr/share/pandora_server/util/selenium_headless_drivers/firefox/firefox` | Modo local driver, Firefox |
| `firefox_profile` | Vacío | Carpeta del perfil de Firefox; se monta en el contenedor en los modos Docker |
| `accept_insecure_certs` | `0` | `1` acepta certificados TLS no válidos |
| `monitor_stats` | `0` | `1` crea el agente de estadísticas del proyecto |
| `browser_width` | `1920` | Anchura del navegador en píxeles |
| `browser_height` | `1080` | Altura del navegador en píxeles |
| `global_timeout` | `5` | Tiempo de espera en segundos para comandos y operaciones de sesión |
| `wait_between_commands` | `0` | Segundos de espera entre comandos |
| `monitor_errors` | `0` | `1` crea los módulos `Global error` y de error de fase |
| `headless` | `1` | `1` ejecuta el navegador en modo headless. Modo local driver |
| `virtual_display` | `1` | `1` ejecuta el navegador en un display virtual. Modo local driver |
| `phase_summarize` | `0` | Solo tarea — `1` hace que `Global time` sea la suma de los tiempos de fase |
| `legacy_data_structure` | `0` | Solo tarea — `1` usa el nombrado de módulos compatible con Selenium 3 y envía un único agente heredado |
| `legacy_data_agent_name` | `a` + MD5 del nombre del archivo SIDE | Solo tarea — nombre del agente heredado |
| `legacy_data_agent_group` | Vacío | Solo tarea — grupo del agente heredado |

La contraseña SSH, cifrada o no, y cualquier credencial incluida en el JSON de Selenium IDE se guardan en la configuración de la tarea. El cifrado usado para la contraseña SSH es un cifrado con clave embebida en el plugin; oculta la contraseña en la configuración guardada pero no sustituye a proteger el acceso a Pandora FMS y a los archivos de configuración y temporales de Discovery. Siga la política de seguridad de su despliegue para ambos.

### Ejecución en línea de comandos

El plugin principal lee un archivo de configuración JSON y un archivo SIDE:

```bash
./pandora_selenium -c <PATH_TO_CONFIG> -s <PATH_TO_SIDE> -t <TASK_NAME> -i <AGENT_INTERVAL> -g <GROUP_ID>
```

| Opción | Descripción |
| --- | --- |
| `-c`, `--conf` | Ruta obligatoria al archivo de configuración de la tarea |
| `-s`, `--side` | Ruta obligatoria al archivo SIDE |
| `-t`, `--task` | Nombre obligatorio de la tarea, usado para derivar los nombres de los agentes y los elementos temporales |
| `-i`, `--interval` | Intervalo del agente en segundos. Por defecto `300` |
| `-g`, `--group` | ID del grupo de los agentes generados. Por defecto `0` |
| `-v`, `--verbose` | Imprime mensajes de progreso en STDERR |
| `-x`, `--xml_mode` | Genera archivos XML de agentes y los envía por Tentacle en lugar de la salida JSON de Discovery |
| `-S`, `--server` | Servidor de Tentacle `server:port`. Por defecto `127.0.0.1:41121`. Se usa con `-x` |
| `-T`, `--temp` | Carpeta temporal para los archivos XML. Por defecto `/tmp`. Se usa con `-x` |

Ejemplo de archivo de configuración:

```json
{
    "worker_mode": "local",
    "run_mode": "docker",
    "browser": "chrome",
    "driver_url": "",
    "ssh_address": "",
    "ssh_port": "",
    "ssh_user": "",
    "ssh_password": "",
    "ssh_password_encrypt": "",
    "ssh_temp_folder": "",
    "docker_image": "",
    "chromedriver_path": "",
    "chrome_binary_path": "",
    "chrome_user_data_dir": "",
    "chrome_profile": "",
    "geckodriver_path": "",
    "firefox_binary_path": "",
    "firefox_profile": "",
    "accept_insecure_certs": "0",
    "monitor_stats": "1",
    "browser_width": "1920",
    "browser_height": "1080",
    "global_timeout": "10",
    "wait_between_commands": "0.15",
    "monitor_errors": "0"
}
```

El plugin imprime una salida JSON de Discovery con los agentes generados cuando se ejecuta sin `-x`, y un archivo XML de datos por agente generado cuando se ejecuta con `-x`. En los modos Docker la configuración y el contenido SIDE se copian dentro del contenedor, que ejecuta el plugin internamente y devuelve su salida.

El asistente también usa dos helpers incluidos:

- `./worker_setup -w <local|remote> -r <driver|docker> -b <chrome|firefox>` imprime los campos JSON del paso **Worker setup** para la combinación seleccionada.
- `./password_encrypter -e -p <PASSWORD>` cifra y `-d -p <PASSWORD>` descifra una contraseña con la clave del plugin. El asistente lo invoca cuando **Encrypt password** está habilitado.

### Comandos para archivos SIDE

El plugin ejecuta comandos de Selenium IDE. Además del conjunto de comandos de Selenium IDE que se indica abajo, los comandos personalizados que generan módulos deben empezar por `//`:

| Comando personalizado | Propósito |
| --- | --- |
| `//phase_start:<nombre>` | Inicia una fase; dura hasta el siguiente `//phase_start` o el final de la prueba, y genera los módulos `Phase <nombre> status` y `Phase <nombre> time` (y `Phase <nombre> error` con **Monitor errors**). Ejemplo: `//phase_start:Login` |
| `//getValue;<módulo>;<tipo>;<regexp>` | Crea un módulo con el primer grupo de captura de la expresión regular del código fuente de la página. Ejemplo: `//getValue;Temperature;generic_data;<span class="temperature">(\d+\.*\,*\d*).*</span>` |
| `//getVariable;<módulo>;<tipo>;<variable>` | Crea un módulo con el valor de una variable guardada con un comando `store`. Ejemplo: `//getVariable;List count;generic_data;listCount` |
| `//getScreenshot;<módulo>` | Crea un módulo con una captura del navegador actual, como `generic_data_string`. Ejemplo: `//getScreenshot;URL home` |

Los comandos de Selenium IDE soportados son:

- **Navegación y navegador**: `open`, `close`, `selectWindow`, `selectFrame`, `setWindowSize`, `run`, `runScript`, `executeScript`, `executeAsyncScript`, `pause`, `setSpeed`.
- **Acciones sobre elementos**: `click`, `clickAt`, `doubleClick`, `doubleClickAt`, `mouseDown`, `mouseDownAt`, `mouseMoveAt`, `mouseOut`, `mouseOver`, `mouseUp`, `mouseUpAt`, `dragAndDropToObject`, `type`, `sendKeys`, `check`, `uncheck`, `select`, `addSelection`, `removeSelection`, `submit`, `editContent`, `answerOnNextPrompt`, `chooseCancelOnNextConfirmation`, `chooseCancelOnNextPrompt`, `chooseOkOnNextConfirmation`, `webdriverAnswerOnVisiblePrompt`, `webdriverChooseCancelOnVisibleConfirmation`, `webdriverChooseCancelOnVisiblePrompt`, `webdriverChooseOkOnVisibleConfirmation`.
- **Store**: `store`, `storeAttribute`, `storeJson`, `storeText`, `storeTitle`, `storeValue`, `storeWindowHandle`, `storeXpathCount`.
- **Asserts**: `assert`, `assertAlert`, `assertChecked`, `assertConfirmation`, `assertEditable`, `assertElementNotPresent`, `assertElementPresent`, `assertNotChecked`, `assertNotEditable`, `assertNotSelectedValue`, `assertNotText`, `assertPrompt`, `assertSelectedLabel`, `assertSelectedValue`, `assertText`, `assertTitle`, `assertValue`.
- **Verifies**: `verify`, `verifyChecked`, `verifyEditable`, `verifyElementNotPresent`, `verifyElementPresent`, `verifyNotChecked`, `verifyNotEditable`, `verifyNotSelectedValue`, `verifyNotText`, `verifySelectedLabel`, `verifySelectedValue`, `verifyText`, `verifyTitle`, `verifyValue`.
- **Esperas**: `waitForElementEditable`, `waitForElementNotEditable`, `waitForElementNotPresent`, `waitForElementNotVisible`, `waitForElementPresent`, `waitForElementVisible`, `waitForText`.
- **Control de flujo**: `if`, `elseIf`, `else`, `do`, `while`, `times`, `forEach`, cerrados con `end` (y `repeatIf` para `do`).

Los comandos que no están en esta lista se omiten silenciosamente. Los targets de los localizadores se resuelven con las estrategias `id=`, `name=`, `css=`, `linkText=`, `xpath=`, `className=`, `partialLinkText=`, `tagName=`, `index=` y `relative=`; un target sin prefijo reconocido se trata como XPath. Las variables guardadas se referencian como `${variable}` y están disponibles para los comandos personalizados.

**Web scraping.** Los comandos personalizados convierten el navegador en un web scraper: capture un valor con un comando `storeText` de Selenium IDE y publíquelo con `//getVariable`, o extráigalo directamente del código fuente de la página con `//getValue` y una expresión regular. El tipo de módulo resultante es el indicado en el comando personalizado (por ejemplo `generic_data` para un número).

### Módulos y agentes generados

Todos los módulos siguientes se crean en el agente de su transacción. Los prefijos `wux:` son identificadores internos de módulo que mantienen los nombres estables entre ejecuciones.

**Agente de prueba** (`WUX Discovery - <nombre de la prueba>`)

- `Global status`: `generic_proc`, `1` cuando la prueba se completa sin fallos, `0` en caso contrario. La descripción lleva el texto del fallo o `Test succeeded`.
- `Global error`: `generic_data_string`, `OK` o el último texto de error de la transacción. Solo se crea cuando **Monitor errors** está habilitado.
- `Global time`: `generic_data`, segundos que tarda toda la ejecución de la prueba, incluidos la apertura y el cierre del navegador; unidad `seconds`.
- `Last error screenshot`: `generic_data_string`, captura PNG en base64 del navegador en el momento del fallo, o `None` cuando la prueba tiene éxito. Se declara crítico cuando contiene una captura.
- `Phase <nombre> status`: `generic_proc`, `1` o `0` para la fase.
- `Phase <nombre> error`: `generic_data_string`, `OK` o el último texto de error de la fase. Solo se crea cuando **Monitor errors** está habilitado.
- `Phase <nombre> time`: `generic_data`, segundos invertidos en la fase; unidad `seconds`.
- Módulos personalizados creados por los comandos `//getValue`, `//getVariable` y `//getScreenshot`, con el tipo solicitado en el comando.

**Agente de estadísticas** (`WUX Discovery - <nombre del proyecto>`, creado cuando **Monitor time statistics** está habilitado)

- `URL status`: `generic_proc`, `1` cuando la URL principal del proyecto responde, `0` en caso contrario.
- `URL stat TT`: `generic_data`, tiempo total de acceso a la URL.
- `URL stat DNS`: `generic_data`, tiempo de resolución DNS.
- `URL stat TTCP`: `generic_data`, tiempo para establecer la conexión TCP.
- `URL stat TST`: `generic_data`, tiempo para recibir el primer byte.
- `URL stat TTC`: `generic_data`, tiempo desde el primer byte hasta el final de la transferencia.
- `URL stat TSSL`: `generic_data`, tiempo para establecer la conexión TLS; solo se crea cuando la URL es HTTPS.

Los módulos de estadísticas se miden con `curl` en la máquina que ejecuta el plugin e informan de la unidad `miliseconds` tal y como la define el plugin; los valores están en milisegundos. En el modo Remote Driver la medición la hace el servidor de Discovery, no el servidor de Selenium.

### Identidad del plugin

| Campo | Valor |
| --- | --- |
| App short name | `pandorafms.selenium.4` |
| Versión del plugin | `1.8` |
| Tipo | Aplicación de Discovery (`.disco`) |
| Sección | Discovery → Applications |