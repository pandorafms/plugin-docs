# Veeam Backup Discovery

*Última actualización del artículo: 2026-09-08.*

## Qué monitoriza

El plugin de Discovery de Veeam Backup lee un servidor de Veeam Backup & Replication mediante su API REST y convierte el estado de siete categorías de recursos en agentes y módulos de Pandora FMS: trabajos de copia de seguridad, copias de seguridad, montajes de recuperación instantánea de VMs y de FCDs, repositorios de copia de seguridad, sesiones de copia de seguridad y proxies de copia de seguridad.

Una tarea de Discovery crea un agente de Pandora FMS por cada categoría de recursos que está habilitada y cuya consulta a la API devuelve datos. Las siete categorías están habilitadas por defecto, por lo que un servidor plenamente accesible genera hasta siete agentes. Cada agente lleva los módulos de una sola categoría: un módulo de total más un módulo por cada recurso que la API informa para esa categoría.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Versión del plugin `1.0` (`pandorafms.veeam.backup`) | Objetivo documentado | La versión que describe esta página, identificada en la definición del paquete. Consulte [Identidad del plugin](#identidad-del-plugin). |
| API REST de Veeam Backup accesible por HTTPS | `Requerido` | El plugin se autentica y lee los recursos mediante `https://<veeam_ip>/api/...`. Prerrequisito, no una declaración de compatibilidad. Consulte [Requisitos](#requisitos). |
| Una versión concreta de Veeam Backup & Replication | `Sin validar` | Ningún registro de pruebas publicado demuestra compatibilidad con una versión concreta de Veeam. |
| Sistema operativo del host que ejecuta el plugin | `Sin validar` | Ningún registro de pruebas publicado demuestra compatibilidad con sistemas operativos. |
| Una cuenta de API de Veeam capaz de autenticarse y leer los recursos monitorizados | `Requerido` | El plugin se autentica con un nombre de usuario y una contraseña y lee los recursos monitorizados. Prerrequisito, no una declaración de compatibilidad. |

### Requisitos

- Un servidor de Pandora FMS con Discovery habilitado para ejecutar la tarea, y una consola para definirla.
- Un servidor de Veeam Backup & Replication que exponga la API REST por HTTPS y sea accesible desde el sistema que ejecuta el plugin.
- Una cuenta de usuario de Veeam que pueda autenticarse contra la API REST y leer los recursos que se vayan a monitorizar. Concédale únicamente el acceso que exija su política de copias de seguridad; el plugin solo lee el estado y nunca modifica la configuración de las copias.
- Un grupo de agentes de destino y un intervalo de monitorización para los agentes generados. Ambos provienen de la tarea de Discovery y los heredan todos los agentes generados.
- Acceso de red al destino de Tentacle cuando la tarea transfiera los datos en modo **Tentacle**.

El plugin se distribuye como una aplicación de Discovery de Pandora FMS (paquete `.disco`) que la consola ejecuta en el servidor de Discovery.

### Instalar el plugin

Cargue el paquete `.disco` desde **Management → Discovery → Extension manager**. Una vez cargado, **Veeam Backup** aparece en la categoría **Cloud** del asistente de Discovery.

## Configurar la tarea de Discovery

Cree la tarea desde **Management → Discovery → Cloud → Veeam Backup**. El primer paso genérico del asistente define la tarea; el paquete añade **Veeam Backup Base** y **Veeam Backup Detailed**. Todos los campos están documentados en [Parámetros de la tarea](#parametros-de-la-tarea).

**Paso 1 — Task definition.** Nombre, grupo de agentes, servidor e intervalo. El nombre y el identificador del grupo y el intervalo se pasan al plugin y los heredan todos los agentes generados.

**Paso 2 — Veeam Backup Base.** Conexión, categorías monitorizadas y entrega de datos:

- **Veeam Backup IP**, **API username** y **API password** son la dirección del endpoint de la API REST y sus credenciales. Los tres son obligatorios.
- **API version** es la cadena de versión de la API REST de Veeam que se envía con cada petición. Deje el valor por defecto salvo que su servidor de Veeam requiera otro.
- Los siete conmutadores **Monitor Jobs**, **Monitor Backups**, **Monitor VMs Mount**, **Monitor FCDs Mount**, **Monitor Repositories**, **Monitor Sessions** y **Monitor Proxies** habilitan o deshabilitan cada categoría de recursos. Todos están habilitados por defecto.
- **Transfer mode** selecciona cómo se entregan los agentes generados, y **Tentacle IP** y **Tentacle port** definen el destino de Tentacle. Consulte la nota en [Parámetros de la tarea](#parametros-de-la-tarea) sobre el comportamiento de la versión `1.0`.
- **Allow list** y **Deny list** son expresiones regulares aplicadas a los nombres de los módulos generados. Allow conserva solo los módulos que coinciden; Deny elimina los que coinciden. Ambas se aplican además de los conmutadores de categoría.

![Veeam Backup Discovery task step 2](../assets/images/discovery/veeam-backup/veeambk_step2_1.png)

**Paso 3 — Veeam Backup Detailed.** Nombrado de la salida y diagnóstico:

- **Prefix for agents and modules** se antepone literalmente a cada alias de agente y nombre de módulo generado, sin insertar separador. Por eso un valor típico termina en espacio, guion u otro separador, por ejemplo `LAB-`.
- **Debug mode** añade mensajes de diagnóstico a la información de ejecución cuando no se puede convertir una marca de tiempo. Deshabilitado por defecto.

![Veeam Backup Discovery task step 2](../assets/images/discovery/veeam-backup/veeambk_step3_1.png)

La contraseña de la API facilitada en la tarea se escribe en la configuración temporal que el servidor de Discovery construye para el plugin. Restrinja el acceso a Pandora FMS y a sus ficheros de configuración y temporales conforme a la política de seguridad de su despliegue.

## Verificar la primera ejecución

Fuerce la tarea desde **Management → Discovery → Task list** y compruebe el resultado en este orden.

1. **El resumen de la tarea** informa de los agentes y módulos generados. Espere un agente por cada categoría habilitada cuya consulta a la API tenga éxito, hasta siete.

2. **Los agentes.** Cada uno aparece como `<Prefix>Veeam Backup <Categoría>`, por ejemplo `Veeam Backup Jobs` o `LAB-Veeam Backup Repositories`. Una categoría habilitada cuya consulta a la API falla no genera ningún agente y registra el fallo en la información de ejecución.

3. **Los totales por categoría.** Todo agente generado lleva un módulo de total de su categoría (por ejemplo `Total jobs`), y los módulos por recurso aparecen cuando la API informa de recursos.

4. **Los valores de los módulos.** Una primera ejecución correcta muestra los trabajos, las copias de seguridad, los repositorios, las sesiones y los proxies accesibles contados, y los montajes de recuperación instantánea en su estado actual.

Si no aparece ningún agente, lo primero que hay que revisar son las credenciales o la accesibilidad de la API REST.

## Interpretar los resultados

### Agentes e identidad

El plugin crea un agente por categoría de recursos habilitada, nunca un agente por servidor de Veeam ni por recurso individual. Los módulos de los recursos de una categoría se acumulan en el agente de esa categoría.

El alias de cada agente es `<Prefix>Veeam Backup <Categoría>`, y su nombre interno de Pandora FMS es el hash MD5 de ese alias. Las etiquetas de categoría que usa el plugin son **Veeam Backup Jobs**, **Veeam Backup Backups**, **Veeam Backup VMs Mounted**, **Veeam Backup FCDs Mounted**, **Veeam Backup Repositories**, **Veeam Backup Sessions** y **Veeam Backup Proxies**. Un prefijo configurado se antepone literalmente y, por tanto, también forma parte de la identidad con hash; si cambia el prefijo más adelante, los agentes cambian de nombre.

Los agentes pertenecen al grupo de agentes de la tarea y heredan su intervalo. Un agente se crea siempre que la consulta a la API de su categoría tiene éxito y devuelve datos — incluso una lista vacía genera el agente con su módulo de total a `0`. Una consulta que falla no genera agente para esa categoría. Los filtros Allow y Deny se aplican antes de crear el agente: si todos los módulos quedan filtrados, el agente se omite y el evento se registra en la información de ejecución.

### Módulos por agente

| Agente | Se crea cuando | Módulos que lleva |
| --- | --- | --- |
| `Veeam Backup Jobs` | **Monitor Jobs** habilitado y `/jobs/states` responde | `Total jobs`, más `<job>.lastResult` y `<job>.lastRun` por cada trabajo |
| `Veeam Backup Backups` | **Monitor Backups** habilitado y `/backups` responde | `Total backups`, más un módulo por copia de seguridad que informa de su antigüedad |
| `Veeam Backup VMs Mounted` | **Monitor VMs Mount** habilitado y la consulta de recuperación instantánea responde | `Total VMs mount`, `VMs mount active`, `VMs mount not active`, más `<vm>.status` y `<vm>.powerState` por cada VM montada |
| `Veeam Backup FCDs Mounted` | **Monitor FCDs Mount** habilitado y la consulta de recuperación instantánea responde | `Total FCDs mount`, `FCDs mount active`, `FCDs mount not active`, más `<fcd>.status` por cada FCD montado |
| `Veeam Backup Repositories` | **Monitor Repositories** habilitado y `/repositories/states` responde | `Total repositories`, más `freeGB`, `capacityGB` y `usedSpaceGB` por cada repositorio |
| `Veeam Backup Sessions` | **Monitor Sessions** habilitado y `/sessions` responde | `Veeam.Total_Sessions`, `Veeam.Running_Sessions`, `Veeam.Failed_Sessions_24h`, `Veeam.Warning_Sessions_24h` y `Veeam.All_Sessions` |
| `Veeam Backup Proxies` | **Monitor Proxies** habilitado y `/proxies` responde | `Total proxies` |

Los nombres de recursos dentro de los nombres de módulo provienen de la API de Veeam y conservan los caracteres que esta informa. Los nombres de módulo varían, por tanto, con su entorno de copias; los patrones de nombre exhaustivos y la semántica de los valores están en [Módulos y agentes generados](#modulos-y-agentes-generados).

## Solución de problemas

| Síntoma | Comprobación |
| --- | --- |
| La tarea falla y la información de ejecución informa de un error de autenticación | Confirme **Veeam Backup IP**, **API username** y **API password**, que la API REST sea accesible por HTTPS y que **API version** sea aceptada por el servidor de Veeam. |
| Una categoría completa no genera ningún agente y su total en el resumen es `0` | La consulta a la API de esa categoría falló. Revise la información de ejecución para ver el error de conexión, de estado HTTP, de JSON o de API registrado para ese endpoint. |
| Faltan agentes o módulos esperados | Revise **Allow list** y **Deny list**: se aplican al nombre final del módulo, incluido cualquier prefijo, y una categoría cuyos módulos quedan todos filtrados no genera ningún agente. |
| La transferencia por Tentacle falla | Confirme que **Transfer mode** es **Tentacle** y que el servidor puede alcanzar **Tentacle IP** en **Tentacle port**. |
| Los contadores de sesiones de 24 horas no coinciden con una ventana de 24 horas | `Veeam.Failed_Sessions_24h` y `Veeam.Warning_Sessions_24h` cuentan los resultados de error y de advertencia entre las sesiones devueltas por la consulta actual a `/sessions`. Los nombres y las descripciones de los módulos conservan la redacción `24h`, pero el plugin no aplica ningún filtro explícito de 24 horas. |

## Referencia

### Parámetros de la tarea

La consola presenta los campos en dos pasos después de la definición genérica de la tarea. La columna de macro es el identificador que se usa en la configuración de la tarea generada.

#### Veeam Backup Base

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Veeam Backup IP | `_veeamIp_` | string | — | Dirección IP o nombre de host del servidor de Veeam Backup. Obligatorio |
| API username | `_veeamUser_` | string | — | Nombre de usuario de la API REST de Veeam Backup. Obligatorio |
| API password | `_veeamPass_` | password | — | Contraseña de la API REST de Veeam Backup. Obligatorio |
| API version | `_veeamApiVersion_` | string | `1.3-rev1` | Cadena de versión de la API REST de Veeam enviada con cada petición |
| Monitor Jobs | `_monitorJobs_` | checkbox | on | Monitoriza los trabajos de copia de seguridad |
| Monitor Backups | `_monitorBackups_` | checkbox | on | Monitoriza las copias de seguridad |
| Monitor VMs Mount | `_monitorVmsMount_` | checkbox | on | Monitoriza los montajes de recuperación instantánea de VMs |
| Monitor FCDs Mount | `_monitorFcdMount_` | checkbox | on | Monitoriza los montajes de recuperación instantánea de FCDs |
| Monitor Repositories | `_monitorRepositories_` | checkbox | on | Monitoriza los repositorios de copia de seguridad |
| Monitor Sessions | `_monitorSessions_` | checkbox | on | Monitoriza las sesiones de copia de seguridad |
| Monitor Proxies | `_monitorProxies_` | checkbox | on | Monitoriza los proxies de copia de seguridad |
| Transfer mode | `_transferMode_` | select | `native` | Opciones `native` y `tentacle` |
| Tentacle IP | `_tentacleIp_` | string | `127.0.0.1` | Destino de la transferencia por Tentacle |
| Tentacle port | `_tentaclePort_` | number | `41121` | Puerto de destino de la transferencia por Tentacle |
| Allow list | `_allowList_` | string | — | Expresión regular de inclusión de módulos. Solo conserva los módulos que coinciden |
| Deny list | `_denyList_` | string | — | Expresión regular de exclusión de módulos. Elimina los módulos que coinciden |

**Transfer mode en la versión `1.0`.** La ayuda del campo describe *native* como el servidor de Discovery leyendo directamente los datos de los agentes y *tentacle* como el envío mediante el cliente de Tentacle. En la versión distribuida `1.0`, ambos valores seleccionables hacen que el plugin escriba ficheros XML de datos de agente y delegue la transferencia en el asistente de transferencia del plugin con el modo seleccionado y la **Tentacle IP** y el **Tentacle port** configurados; el asistente decide si se trata de una ingesta local o de un envío por Tentacle. La acumulación nativa de salida JSON de Discovery del plugin solo se alcanza cuando el fichero de configuración define `transfer_mode=local`, un valor que el asistente no ofrece.

#### Veeam Backup Detailed

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Prefix for agents and modules | `_prefix_` | string | — | Texto antepuesto literalmente a cada alias de agente y nombre de módulo. No se añade ningún separador |
| Debug mode | `_debugMode_` | checkbox | off | Añade mensajes de diagnóstico a la información de ejecución cuando no se puede convertir una marca de tiempo |

### Claves del fichero de configuración

La tarea de Discovery construye un fichero temporal de clave/valor a partir de sus propios campos y se lo pasa al plugin con `--conf`. Una ejecución manual facilita ese fichero directamente. El fichero no tiene cabecera de sección; el plugin lo lee como una sección `[CONF]`.

| Clave | Por defecto | Descripción |
| --- | --- | --- |
| `veeam_ip` | Vacío | Dirección del servidor de Veeam Backup. Obligatorio |
| `veeam_user` | Vacío | Nombre de usuario de la API REST de Veeam. Obligatorio |
| `veeam_pass` | Vacío | Contraseña de la API REST de Veeam. Obligatorio |
| `veeam_api_version` | `1.0-rev2` | Versión de la API REST de Veeam. La tarea siempre escribe el valor configurado en el asistente (por defecto `1.3-rev1`); el plugin usa `1.0-rev2` solo si la clave está ausente |
| `agents_group` | Vacío | Nombre del grupo de agentes, procedente de la tarea. Se usa como grupo de los agentes generados |
| `agents_group_id` | Vacío | Identificador del grupo de agentes, procedente de la tarea |
| `interval` | `300` | Intervalo de monitorización en segundos, heredado por los agentes generados |
| `transfer_mode` | `local` | `native`, `tentacle` o `local`. `native` y `tentacle` escriben y transfieren ficheros XML de datos de agente; `local` acumula los agentes en la salida nativa JSON de Discovery |
| `tentacle_ip` | `127.0.0.1` | Destino de la transferencia por Tentacle |
| `tentacle_port` | `41121` | Puerto de destino de la transferencia por Tentacle |
| `allow_list` | Vacío | Expresión regular de inclusión aplicada a los nombres de módulo |
| `deny_list` | Vacío | Expresión regular de exclusión aplicada a los nombres de módulo |
| `prefix` | Vacío | Texto antepuesto literalmente a los alias de agente y nombres de módulo |
| `monitor_jobs` | `true` | Habilita la categoría Jobs |
| `monitor_backups` | `true` | Habilita la categoría Backups |
| `monitor_vms_mount` | `true` | Habilita la categoría VMs Mount |
| `monitor_fcd_mount` | `true` | Habilita la categoría FCDs Mount |
| `monitor_repositories` | `true` | Habilita la categoría Repositories |
| `monitor_sessions` | `true` | Habilita la categoría Sessions |
| `monitor_proxies` | `true` | Habilita la categoría Proxies |
| `debug_mode` | `false` | Añade mensajes de diagnóstico cuando no se puede convertir una marca de tiempo |

El fichero contiene la contraseña de la API en texto plano cuando la tarea se ejecuta. Restríjalo a la cuenta que ejecuta el plugin junto con el directorio temporal de Discovery, manténgalo fuera de directorios compartidos, registros y control de versiones, y siga la política de su despliegue para las credenciales de Veeam.

### Ejecución por línea de comandos

Una ejecución manual reproduce lo que el servidor de Discovery hace por cada ejecución de tarea. El plugin acepta un único fichero de configuración:

```bash
./pandora_veeam_backup --conf <RUTA_AL_FICHERO>
```

| Opción | Descripción |
| --- | --- |
| `--conf` | Ruta obligatoria al fichero de configuración |
| `--help`, `-h` | Muestra la ayuda del comando |

Ejemplo de fichero de configuración:

```ini
veeam_ip=<IP_DEL_SERVIDOR_VEEAM>
veeam_user=<USUARIO_API_VEEAM>
veeam_pass=<CONTRASEÑA_API_VEEAM>
veeam_api_version=1.0-rev2
interval=300
transfer_mode=tentacle
tentacle_ip=<IPV4_DEL_SERVIDOR_PANDORA_FMS>
tentacle_port=41121
agents_group=<NOMBRE_DEL_GRUPO_DE_AGENTES>
prefix=<PREFIJO>
monitor_jobs=true
monitor_backups=true
monitor_vms_mount=true
monitor_fcd_mount=true
monitor_repositories=true
monitor_sessions=true
monitor_proxies=true
debug_mode=false
```

Ese fichero contiene una credencial en texto plano. Restríjalo a la cuenta que ejecuta el plugin y manténgalo fuera de directorios compartidos, registros y control de versiones. Evite volcarlo en una línea de comandos de shell, donde el historial del shell y la lista de procesos del sistema operativo podrían revelarlo.

### Módulos y agentes generados

Los módulos se nombran `<Prefijo><nombre del módulo>`; los patrones siguientes omiten el prefijo. Los nombres de módulo por recurso incrustan el nombre o identificador que la API de Veeam informa para el recurso.

**Veeam Backup Jobs**

- `Total jobs`: `generic_data`, número de trabajos devueltos.
- `<job>.lastResult`: `generic_data`, `1` para un último resultado correcto, `2` para una advertencia y `0` en el resto de casos. La definición del módulo lleva umbrales que marcan `0` como crítico y `2` como de advertencia.
- `<job>.lastRun`: `generic_data`, tiempo transcurrido desde la última ejecución del trabajo, expresado en timeticks de Pandora; unidad `_timeticks_`.

**Veeam Backup Backups**

- `Total backups`: `generic_data`, número de copias de seguridad devueltas.
- `<backup>`: `generic_data`, tiempo transcurrido desde la creación de la copia, expresado en timeticks de Pandora; unidad `_timeticks_`.

**Veeam Backup VMs Mounted**

- `Total VMs mount`: `generic_data`, número de montajes de recuperación instantánea de VMs devueltos.
- `VMs mount active`: `generic_data`, montajes cuyo estado se considera activo.
- `VMs mount not active`: `generic_data`, montajes cuyo estado se considera inactivo.
- `<vm>.status`: `generic_data_string`, texto del estado de la VM montada.
- `<vm>.powerState`: `generic_data_string`, texto del estado de energía de la VM montada.

**Veeam Backup FCDs Mounted**

- `Total FCDs mount`: `generic_data`, número de montajes de recuperación instantánea de FCDs devueltos.
- `FCDs mount active`: `generic_data`, montajes cuyo estado se considera activo.
- `FCDs mount not active`: `generic_data`, montajes cuyo estado se considera inactivo.
- `<fcd>.status`: `generic_data_string`, texto del estado del FCD montado.

**Veeam Backup Repositories**

- `Total repositories`: `generic_data`, número de repositorios devueltos.
- `<repository>.freeGB`: `generic_data`, espacio libre en GiB; unidad `GB`.
- `<repository>.capacityGB`: `generic_data`, capacidad en GiB; unidad `GB`.
- `<repository>.usedSpaceGB`: `generic_data`, espacio usado en GiB; unidad `GB`.

**Veeam Backup Sessions**

- `Veeam.Total_Sessions`: `generic_data`, número de sesiones devueltas.
- `Veeam.Running_Sessions`: `generic_data`, sesiones cuyo estado no es terminal (`success`, `completed`, `failed`, `error`, `warning`, `stopped` o `stopping`).
- `Veeam.Failed_Sessions_24h`: `generic_data`, sesiones con resultado de error. El recuento cubre las sesiones devueltas por la consulta actual; el plugin no aplica ningún filtro explícito de 24 horas.
- `Veeam.Warning_Sessions_24h`: `generic_data`, sesiones con resultado de advertencia. Mismo alcance que el contador de errores.
- `Veeam.All_Sessions`: `generic_data_string`, una línea por sesión devuelta que describe su estado, progreso, resultado y mensaje. Se crea solo cuando se devuelve al menos una sesión.

**Veeam Backup Proxies**

- `Total proxies`: `generic_data`, número de proxies devueltos.

### Identidad del plugin

| Campo | Valor |
| --- | --- |
| Nombre corto de la aplicación | `pandorafms.veeam.backup` |
| Versión del plugin | `1.0` |
| Tipo | Aplicación de Discovery (`.disco`) |
| Sección | Discovery → Cloud |
