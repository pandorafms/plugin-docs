# SAP R3 Discovery

*Última actualización del artículo: 2026-10-26.*

## Qué monitoriza

El addon de Discovery de SAP R3 monitoriza sistemas SAP de forma remota, sin instalar software en los equipos SAP. Se conecta al sistema SAP con un usuario SAP y convierte el resultado en un agente de Pandora FMS cuyos módulos informan de la disponibilidad, los procesos de trabajo, los IDocs, los dumps ABAP, los trabajos en segundo plano, las colas RFC, datos de la base de datos y, opcionalmente, indicadores de seguridad y auditoría.

Una tarea de Discovery monitoriza un sistema SAP (un nombre de host, un cliente y un número de sistema SAP) y genera **un único agente** con:

- Un módulo `SAP connection` que indica si el sistema SAP respondió.
- Los módulos que se seleccionen en la tarea, más módulos personalizados opcionales que ejecutan comprobaciones SAP definidas por el usuario.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
|--------|--------|-----------|
| Addon `pandorafms.sap`, versión `1.8` | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del addon](#identidad-del-addon) |
| Acceso de red desde el servidor de Discovery al sistema SAP | `Requerido` | El addon abre una conexión remota con el sistema SAP. El paquete no registra el puerto; use el que exponga su sistema SAP para conexiones remotas |
| Un usuario SAP con contraseña y el acceso que necesiten los módulos seleccionados | `Requerido` | Consulte [Usuario SAP](#usuario-sap) |
| Versiones y productos SAP | `No validado` | No se ha registrado ninguna matriz de versiones SAP para esta versión |
| Sistema operativo del servidor de Discovery | `No validado` | No se ha registrado ningún sistema operativo para esta versión |
| Versiones concretas de Pandora FMS | `No validado` | No se ha registrado ninguna matriz de versiones para este addon |

### Prerrequisitos

1. **Conectividad** desde el servidor de Discovery hasta el sistema SAP.
2. **Un usuario SAP** y su contraseña, registrados en el almacén de credenciales de Pandora FMS como credencial SAP.
3. **El cliente y el número de sistema SAP** del sistema que se va a monitorizar.
4. **Pandora FMS**: un servidor de Discovery que ejecute la tarea y la consola que la defina.

El addon incluye su propio ejecutable, `bin/pandora_sap`, junto con todo lo necesario para consultar SAP, de modo que no hay que instalar nada más en el servidor de Discovery ni en los equipos SAP.

### Usuario SAP

El addon se autentica con el usuario y la contraseña almacenados en la credencial. Las autorizaciones SAP que necesita este usuario para cada módulo no se han registrado para esta versión, por lo que esta página no indica un conjunto mínimo. Cree un usuario dedicado para Pandora FMS y conceda solo lo que sus administradores SAP confirmen que requieren los módulos que active; un módulo que el usuario no esté autorizado a ejecutar puede informar en su descripción del error devuelto por SAP.

La credencial almacenada en Pandora FMS debe proporcionar las claves `user` y `password`.

!!! warning
    El usuario y la contraseña de SAP se pasan como argumentos al proceso que consulta SAP, por lo que pueden ser visibles en la lista de procesos del servidor de Discovery. Restrinja el acceso a ese servidor.

### Instalar el addon

Descargue el paquete `.disco` desde la entrada del Marketplace de Pandora FMS, cuya descarga está limitada a usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.sap](https://marketplace.pandorafms.com/entries/pandorafms.sap)

Cárguelo en Pandora FMS. Una vez cargado, **SAP R3** está disponible entre las tareas de Discovery de aplicaciones.

## Configurar la tarea de Discovery

Cree la tarea desde las aplicaciones de Discovery y elija **SAP R3**. La consola presenta los campos en dos pasos; cada campo se documenta en [Parámetros de la tarea](#parametros-de-la-tarea).

1. **SAP R3 Base** — el sistema SAP y la credencial:

    - **SAP Hostname**: dirección o nombre del sistema SAP.
    - **SAP Client**: cliente SAP.
    - **SAP System Number**: número de sistema SAP.
    - **SAP Credentials**: la credencial SAP registrada en el almacén de credenciales.
    - **SAP SNC Mode**: activa la protección SNC en la comunicación. Al activarlo, la consola muestra **SAP SNC Partner name**, **SAP SNC QOP** y **Client SNC name**.

    <!-- SCREENSHOT NEEDED: Paso SAP R3 Base del asistente con SAP Hostname, SAP Client, SAP System Number y SAP Credentials, sin direcciones ni credenciales reales. -->

    <!-- SCREENSHOT NEEDED: Paso SAP R3 Base del asistente con SAP SNC Mode activado, mostrando los campos de nombre del partner SNC, SNC QOP y nombre SNC del cliente. -->

2. **SAP R3 Detailed** — opciones de ejecución y monitorización:

    - **Max threads**: número de trabajadores en paralelo que ejecutan los módulos.
    - **Target agent**: nombre del agente que recibe los módulos. Si está vacío, se usa el **SAP Hostname**.
    - **Security and Audit Modules**: añade los módulos de seguridad y auditoría. Puede aumentar el tiempo de ejecución de la tarea.
    - **SAP modules**: módulos predefinidos que se van a monitorizar.
    - **Custom modules definitions**: módulos propios, uno por línea. Consulte [Módulos personalizados](#modulos-personalizados).

    <!-- SCREENSHOT NEEDED: Paso SAP R3 Detailed del asistente con Max threads, Target agent, Security and Audit Modules, SAP modules y Custom modules definitions. -->

El grupo y el intervalo de la tarea proceden del paso genérico de definición de la tarea y se aplican al agente que crea.

## Verificar la primera ejecución

Fuerza la tarea desde la lista de tareas de Discovery y compruebe el resultado en este orden.

1. **El resumen de la tarea.** Una tarea que finaliza correctamente informa de:

    - **SAP Target**, **SAP Client** y **SAP System**: los valores de la tarea.
    - **Total modules**: módulos generados, incluido `SAP connection`.

    Una tarea que no finaliza correctamente registra los errores en su información de ejecución.

    <!-- SCREENSHOT NEEDED: Resumen de ejecución de una tarea de Discovery de SAP R3 con SAP Target, SAP Client, SAP System y Total modules. -->

2. **El agente.** Un único agente, con el nombre de **Target agent** o, si está vacío, el **SAP Hostname**.

3. **El módulo `SAP connection`.** Vale `1` cuando SAP respondió. Si vale `0`, no se genera ningún otro módulo; consulte su descripción y la información de ejecución de la tarea.

## Interpretar los resultados

### Agente generado

| Elemento | Valor |
|----------|-------|
| Nombre y alias del agente | **Target agent**, o el **SAP Hostname** si está vacío |
| Sistema operativo | `SAP` |
| Versión del sistema operativo | El sistema operativo y la versión que informa el sistema SAP |
| Dirección | La dirección que informa el sistema SAP |
| Grupo e intervalo | El grupo y el intervalo de la tarea de Discovery |

El nombre del agente es la única identidad que establece el addon, por lo que conviene usar **Target agent** para dar a cada sistema SAP monitorizado un nombre de agente distinto y estable.

### Cómo se comprueba la conexión

Antes de ejecutar ningún módulo, el addon ejecuta la comprobación `SAP System info` (`120`). Una respuesta válida proporciona la dirección del agente, la versión del sistema operativo y el identificador del sistema. Si la comprobación falla, el addon informa del error, crea únicamente el módulo `SAP connection` con valor `0` y no ejecuta el resto de módulos. Si la comprobación tiene éxito, la descripción del módulo indica `SAP is reachable. Running on <DATABASE_TYPE> <INSTANCE>`.

### Módulos

Cada módulo incluye el identificador del sistema SAP como dato extra. Los módulos se agrupan a continuación; la lista completa con identificadores está en [Módulos predefinidos](#modulos-predefinidos).

| Grupo | Qué informa |
|-------|-------------|
| Sistema y disponibilidad | Información del sistema, estado de login, tiempo de respuesta de SAPGUI y usuarios de diálogo |
| Procesos de trabajo | Procesos de trabajo fallidos, sin reinicio, detenidos y disponibles, como recuentos y porcentajes |
| IDocs | IDocs fallidos y procesados desde ayer |
| Dumps | Dumps ABAP de ayer, de hoy y de la última hora, como recuentos, listas y recuentos agrupados |
| Trabajos y batch input | Trabajos cancelados de ayer y de hoy y batch input fallido |
| Operaciones de envío externas | Operaciones de envío procesadas y no procesadas desde ayer |
| Base de datos | Uso de tablespaces de Oracle, datos del log de Microsoft SQL Server y memoria de SAP HANA |
| Datos de negocio y de sistema | Entradas de bloqueo del sistema, datos de cuentas de clientes, valores de parámetros de perfil y cambios en perfiles de autorización |
| Colas RFC | Entradas e intentos fallidos en las colas RFC de entrada y de salida |
| Seguridad y auditoría | Usuarios con autorizaciones sensibles y órdenes importadas del mes. Se activan con **Security and Audit Modules** |

Por defecto la tarea selecciona diez módulos: `102`, `103`, `104`, `105`, `109`, `111`, `113`, `116`, `150` y `151`.

## Operación

### Módulos personalizados

Además de los módulos predefinidos, **Custom modules definitions** admite módulos propios. Escriba un módulo por línea:

```text
<NOMBRE_MODULO>;<TIPO_MODULO>;<COMPROBACION_SAP>;<DESCRIPCION>
```

- `<NOMBRE_MODULO>`: nombre del módulo.
- `<TIPO_MODULO>`: tipo de módulo de Pandora FMS, por ejemplo `generic_data` o `generic_data_string`.
- `<COMPROBACION_SAP>`: los argumentos de la comprobación SAP que se ejecuta, con la misma forma que usan los módulos predefinidos, por ejemplo `-m 120`.
- `<DESCRIPCION>`: opcional.

Las líneas vacías y las que empiezan por `#` se ignoran. Una línea con menos de tres campos se ignora sin error. El paquete no enumera las comprobaciones disponibles más allá de los módulos predefinidos, así que use únicamente valores de `<COMPROBACION_SAP>` facilitados por Pandora FMS.

Ejemplo con una comprobación predefinida:

```text
SAP info;generic_data_string;-m 120
```

### Ejecución manual

El addon se puede ejecutar fuera de una tarea de Discovery. El ejecutable recibe la ruta a un fichero de configuración descrito en [Fichero de configuración](#fichero-de-configuracion) y, opcionalmente, la ruta a un fichero de módulos personalizados con el formato anterior:

```bash
./pandora_sap --conf <PATH_TO_CONFIG> --custom_modules <PATH_TO_CUSTOM_MODULES>
```

Imprime en la salida estándar un documento JSON con un `summary`, una clave `info` cuando hay mensajes y `monitoring_data` con el agente y sus módulos. No envía datos a Pandora FMS por sí mismo. El código de salida es `1` si se produjo algún error.

El fichero de configuración contiene el usuario y la contraseña de SAP codificados en `credentials`. Protéjalo con permisos restrictivos.

## Solución de problemas

El addon no tiene opción verbose ni de depuración. Su canal de diagnóstico es el campo `info` del resultado JSON de ejecución, que se muestra en la información de ejecución de la tarea.

- **`Parameter [server] not defined`, `Parameter [client] not defined` o `Parameter [system] not defined`**: un campo obligatorio de la tarea está vacío.
- **`Can't get user from [credentials] parameter` o `Can't get password from [credentials] parameter`**: la credencial no proporciona `user` y `password`, o `credentials` no es un JSON válido codificado en base64.
- **`Parameter [snc_partner] not defined`, `Parameter [snc_qop] not defined` o `Parameter [snc_myname] not defined`**: **SAP SNC Mode** está activado y el campo está vacío. Los tres campos SNC son obligatorios cuando SNC está activado.
- **`Failed to connect SAP server: ...`**: falló la comprobación de conexión. El mensaje contiene el error devuelto por SAP, por ejemplo un código `RFC_ERROR_...`. Revise el nombre de host, el cliente, el número de sistema, la credencial, el acceso de red y la configuración SNC. Solo se crea el módulo `SAP connection`, con valor `0`.
- **`Error while running module <NAME>: ...`**: un módulo falló. El resto de módulos se siguen ejecutando.
- **La descripción de un módulo contiene un mensaje `RFC_ERROR_...`**: SAP devolvió un error para esa comprobación, por ejemplo porque el usuario no está autorizado a ejecutarla.
- **`Error while reading configuration modules: ...`**: la lista de módulos no es una lista válida de identificadores.
- **`Error while reading custom modules file: ...`**: no se pudo leer el fichero de módulos personalizados.
- **Faltan módulos**: los identificadores que el addon no conoce se ignoran sin error.
- **La tarea tarda demasiado**: aumente **Max threads**, o desactive **Security and Audit Modules** y los módulos que no necesite. Más hilos aumentan el uso de CPU del servidor de Discovery.

## Referencia

### Parámetros de la tarea

#### SAP R3 Base

| Campo | Macro | Tipo | Valor por defecto | Notas |
|-------|-------|------|-------------------|-------|
| SAP Hostname | `_server_` | cadena | — | Obligatorio |
| SAP Client | `_sapClient_` | cadena | — | Obligatorio |
| SAP System Number | `_sapSystem_` | cadena | — | Obligatorio |
| SAP Credentials | `_credentials_` | selección de credencial (SAP) | — | Obligatorio. Debe proporcionar `user` y `password` |
| SAP SNC Mode | `_sapSNCMode_` | casilla | desactivada | Activa la protección SNC. Los tres campos siguientes se muestran al activarla |
| SAP SNC Partner name | `_sapSNCPartnerName_` | cadena | — | Un nombre SNC válido del servidor SAP, igual al Distinguished Name (DN) del PSE del servidor SAP. El addon lo exige con el modo SNC activado |
| SAP SNC QOP | `_sapSNCQOP_` | selección | `8` | Calidad de protección: `1` solo autenticación, `2` autenticación y protección de integridad, `3` autenticación, integridad y privacidad, `8` protección global por defecto, `9` protección máxima |
| Client SNC name | `_sapSNCMyName_` | cadena | — | Un nombre SNC válido del cliente, igual al Distinguished Name (DN) del PSE del cliente. El addon lo exige con el modo SNC activado |

#### SAP R3 Detailed

| Campo | Macro | Tipo | Valor por defecto | Notas |
|-------|-------|------|-------------------|-------|
| Max threads | `_threads_` | número | `1` | Opcional. Nunca más hilos que módulos |
| Target agent | `_targetAgent_` | cadena | — | Opcional. Si está vacío, se usa el nombre de host SAP |
| Security and Audit Modules | `_secAudit_` | casilla | activada | Añade los módulos `220` a `228` a la selección |
| SAP modules | `_customModules_` | selección múltiple | `102`, `103`, `104`, `105`, `109`, `111`, `113`, `116`, `150`, `151` | Opcional. Consulte [Módulos predefinidos](#modulos-predefinidos) |
| Custom modules definitions | `_customModulesDefinition_` | área de texto | — | Opcional. Un módulo por línea: `module name;module type;SAP check definition;module description` |

### Fichero de configuración

Se usa en la ejecución manual. Una pareja `clave = valor` por línea. Las opciones numéricas aceptan `1` para activar y `0` para desactivar; un valor que no sea un número se lee como `0`.

| Clave | Valor por defecto | Descripción |
|-------|-------------------|-------------|
| `agents_group_id` | `10` | ID del grupo del agente generado |
| `interval` | `300` | Intervalo del agente, en segundos |
| `threads` | `1` | Número de trabajadores en paralelo |
| `server` | vacío | Obligatorio. Nombre de host SAP |
| `client` | vacío | Obligatorio. Cliente SAP |
| `system` | vacío | Obligatorio. Número de sistema SAP |
| `credentials` | vacío | Obligatorio. Base64 del JSON `{"user": "<SAP_USER>", "password": "<SAP_PASSWORD>"}` |
| `snc_mode` | `0` | `1` activa SNC |
| `snc_partner` | vacío | Nombre SNC del partner. Obligatorio si `snc_mode` es `1` |
| `snc_qop` | vacío | Calidad de protección SNC (`1`, `2`, `3`, `8` o `9`). Obligatorio si `snc_mode` es `1` |
| `snc_myname` | vacío | Nombre SNC del cliente. Obligatorio si `snc_mode` es `1` |
| `sec_audit` | `1` | `1` añade los módulos `220` a `228` a `modules` |
| `agent` | vacío | Nombre del agente. Si está vacío, se usa `server` |
| `modules` | `[]` | Lista JSON de identificadores de módulos predefinidos, por ejemplo `[120, 104]` |

Ejemplo:

```ini
agents_group_id = 10
threads         = 4
interval        = 300
server          = <SAP_HOSTNAME>
client          = <SAP_CLIENT>
system          = <SAP_SYSTEM_NUMBER>
credentials     = <BASE64_CREDENTIALS>
sec_audit       = 0
agent           = <AGENT_NAME>
modules         = [120, 104, 105, 109]
```

### Módulos predefinidos

La columna **Lista del asistente** indica si el módulo se puede elegir en **SAP modules**. Los módulos marcados con `No` solo se generan mediante la selección por defecto, **Security and Audit Modules** o la clave `modules` del fichero de configuración. Los módulos de tipo `async_string` son asíncronos.

#### Sistema y disponibilidad

| ID | Módulo | Tipo | Lista del asistente |
|----|--------|------|---------------------|
| `120` | SAP System info | `generic_data_string` | Sí |
| `160` | SAP Login status - Text | `generic_data_string` | Sí |
| `102` | Average time of SAPGUI response- Count | `generic_data` | No |
| `103` | Dialog Logged users - Count | `generic_data` | No |

#### Procesos de trabajo

| ID | Módulo | Tipo | Lista del asistente |
|----|--------|------|---------------------|
| `114` | WP DIA failed - Count | `generic_data` | Sí |
| `115` | WP BGD failed - Count | `generic_data` | Sí |
| `116` | WP UPD failed - Count | `generic_data` | Sí |
| `117` | WP UP2 failed - Count | `generic_data` | Sí |
| `118` | WP SPO failed - Count | `generic_data` | Sí |
| `119` | WP ENQ failed - Count | `generic_data` | Sí |
| `150` | WP with restart not active - Count | `generic_data` | Sí |
| `151` | WP stopped - Count | `generic_data` | Sí |
| `202` | WP DIA available - Count | `generic_data` | Sí |
| `203` | WP BGD available - Count | `generic_data` | Sí |
| `204` | WP UPD available - Count | `generic_data` | Sí |
| `302` | WP DIA available - Percent | `generic_data` | Sí |
| `303` | WP BGD available - Percent | `generic_data` | Sí |
| `304` | WP UPD available - Percent | `generic_data` | Sí |

#### IDocs

| ID | Módulo | Tipo | Lista del asistente |
|----|--------|------|---------------------|
| `104` | IDOCs failed from yesterday - Count | `generic_data` | Sí |
| `105` | IDOCs ok from yesterday - Count | `generic_data` | Sí |

#### Dumps

| ID | Módulo | Tipo | Lista del asistente |
|----|--------|------|---------------------|
| `108` | Dumps from yesterday - List | `async_string` | Sí |
| `109` | Dumps from yesterday - Count | `generic_data` | Sí |
| `123` | Dumps data from yesterday - Count | `generic_data` | Sí |
| `124` | Dumps data from yesterday - List | `async_string` | Sí |
| `125` | Dumps data today - Count | `generic_data` | Sí |
| `126` | Dumps data today - List | `async_string` | Sí |
| `128` | Dumps data from the last hour - Count | `generic_data` | Sí |
| `129` | Dumps data from the last hour - List | `async_string` | Sí |
| `148` | Dumps today - Grouped count list | `async_string` | Sí |
| `149` | Dumps today - Count | `generic_data` | Sí |

#### Trabajos y batch input

| ID | Módulo | Tipo | Lista del asistente |
|----|--------|------|---------------------|
| `112` | Jobs canceled from yesterday - List | `async_string` | Sí |
| `113` | Jobs canceled from yesterday - Count | `generic_data` | Sí |
| `122` | Jobs canceled from yesterday - Grouped count list | `async_string` | Sí |
| `121` | Batch input failed from yesterday - Count | `generic_data` | Sí |
| `142` | Jobs canceled today - List | `async_string` | Sí |
| `143` | Jobs canceled today - Count | `generic_data` | Sí |
| `144` | Jobs canceled today - Grouped count list | `async_string` | Sí |

#### Operaciones de envío externas

| ID | Módulo | Tipo | Lista del asistente |
|----|--------|------|---------------------|
| `206` | External send operations not processed from yesterday - Count | `generic_data` | Sí |
| `207` | External send operations processed from yesterday - Count | `generic_data` | Sí |

#### Base de datos

| ID | Módulo | Tipo | Lista del asistente |
|----|--------|------|---------------------|
| `106` | Oracle tablespaces usage - List | `generic_data_string` | No |
| `107` | Oracle tablespaces usage greater equal 95% - Count | `generic_data` | No |
| `127` | Oracle tablespaces usage greater equal 99% - Count | `generic_data` | No |
| `130` | MS SQL log size | `generic_data` | No |
| `131` | MS SQL log free | `generic_data` | No |
| `132` | MS SQL log free % | `generic_data` | No |
| `210` | Hana free memory bytes | `generic_data` | No |
| `211` | Hana used memory bytes | `generic_data` | No |

#### Datos de negocio y de sistema

| ID | Módulo | Tipo | Lista del asistente |
|----|--------|------|---------------------|
| `110` | System block entries - List | `async_string` | Sí |
| `111` | System block entries - Count | `generic_data` | Sí |
| `1221` | Customers accounts open items - Count | `generic_data` | Sí |
| `1101` | Closing balance of customers accounts - List | `async_string` | Sí |
| `1110` | Customers accounts clearing transactions - Count | `generic_data` | Sí |
| `1201` | PFL parameters values - List | `async_string` | Sí |
| `1202` | Changes on auth profiles from yesterday - Count | `generic_data` | Sí |
| `1203` | Changes on auth profiles from yesterday - List | `async_string` | Sí |

#### Colas RFC

| ID | Módulo | Tipo | Lista del asistente |
|----|--------|------|---------------------|
| `190` | RFC Queue OUT - Count | `generic_data` | Sí |
| `191` | RFC Queue IN - Count | `generic_data` | Sí |
| `192` | RFC send tries failed - Count | `generic_data` | Sí |
| `193` | RFC send tries failed return O - Count | `generic_data` | Sí |
| `194` | RFC send tries failed return I - Count | `generic_data` | Sí |
| `195` | RFC Error queue OUT failed - Count | `generic_data` | Sí |
| `196` | RFC Error queue IN failed - Count | `generic_data` | Sí |
| `197` | RFC Queue OUT - Older entry seconds not processing | `generic_data` | Sí |
| `198` | RFC Queue IN - Older entry seconds not processing | `generic_data` | Sí |

#### Seguridad y auditoría

| ID | Módulo | Tipo | Lista del asistente |
|----|--------|------|---------------------|
| `220` | Users - Change passwords and block users (count) | `generic_data` | No |
| `221` | Users - Change passwords and block users (table) | `generic_data_string` | No |
| `222` | Users - Manage profiles (count) | `generic_data` | No |
| `223` | Users - Manage profiles (table) | `generic_data_string` | No |
| `224` | Users - Restart server application (count) | `generic_data` | No |
| `225` | Users - Restart server application (table) | `generic_data_string` | No |
| `226` | Users - Run and stop work processes (count) | `generic_data` | No |
| `227` | Users - Run and stop work processes (table) | `generic_data_string` | No |
| `228` | Month imported orders | `generic_data_inc_abs` | No |

### Identidad del addon

| Elemento | Valor |
|----------|-------|
| Nombre | SAP R3 |
| Identificador | `pandorafms.sap` |
| Versión | `1.8` |
| Tipo y sección | Discovery, `app` |
| Entrada del Marketplace | [pandorafms.sap](https://marketplace.pandorafms.com/entries/pandorafms.sap), actualizada el 2026-05-07 |
| Disponibilidad | La entrada del Marketplace indica que la descarga está limitada a usuarios con licencia |
