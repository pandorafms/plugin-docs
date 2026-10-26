# Hyper-V Discovery

*Última actualización del artículo: 2026-10-26.*

## Qué monitoriza

El addon de Discovery de Hyper-V monitoriza un host Microsoft Hyper-V y las máquinas virtuales (VM) que ejecuta. Se conecta de forma remota al host mediante WinRM, ejecuta consultas de solo lectura y convierte el resultado en agentes y módulos de Pandora FMS: memoria del host, unidades y estado del servicio Virtual Machine Management y, para cada VM, su estado, CPU, memoria, uptime, replicación, adaptadores de red y discos virtuales.

Una tarea de Discovery genera dos tipos de agentes, según las opciones que actives:

- **Un agente para el host Hyper-V** (opcional), con módulos a nivel de host.
- **Un agente por cada VM**, con los módulos de las opciones de escaneo activadas. Las VM no tienen agente propio en su sistema operativo: el addon las ve solo a través del host.

No se instala nada en el host Hyper-V ni dentro de las VM.

## Preparar

### Compatibilidad

| Ámbito | Estado | Evidencia |
|--------|--------|-----------|
| Addon `pandorafms.hyperv`, versión `1.1` | Objetivo documentado | La versión que describe esta página. Consulta [Identidad del addon](#identidad-del-addon) |
| Listener WinRM en el puerto TCP `5985` del host Hyper-V, accesible desde el servidor de Discovery | `Required` | El addon se conecta a `http://<host>:5985/wsman` |
| Cuenta aceptada por el host mediante autenticación HTTP Basic que pueda ejecutar los cmdlets de PowerShell de Hyper-V | `Required` | Prerrequisito, no una declaración de compatibilidad. Consulta [Permisos](#permisos) |
| Comando `curl` disponible en el servidor de Discovery | `Required` | El addon ejecuta `curl` para comunicarse con el host |
| Versiones de Windows Server y de Hyper-V del host monitorizado | `Not validated` | No se ha registrado ninguna versión para este addon |
| Sistema operativo del servidor de Discovery | `Not validated` | No se ha registrado ningún sistema operativo para esta versión |
| Versiones concretas de Pandora FMS | `Not validated` | No se ha registrado una matriz de versiones para este addon |

### Prerrequisitos

1. **Conectividad** desde el servidor de Discovery al puerto TCP `5985` del host Hyper-V. El puerto `5985` es el puerto HTTP de WinRM; el addon no usa HTTPS (`5986`).
2. **WinRM habilitado en el host Hyper-V**, que acepte autenticación HTTP Basic sobre el listener HTTP sin cifrar.
3. **Un usuario y una contraseña** del host, registrados en el almacén de credenciales de Pandora FMS como credencial **custom** que proporcione las claves `user` y `password`.
4. **Pandora FMS**: un servidor de Discovery para ejecutar la tarea y la consola para definirla.

El addon incluye su propio ejecutable (`bin/pandora_hyperV`), por lo que en el servidor de Discovery no hay que instalar nada más que el comando `curl`.

### Permisos

El addon ejecuta, a través de la sesión WinRM, las consultas de PowerShell de Hyper-V `Get-VM`, `Get-VMHost`, `Get-VMNetworkAdapter`, `Get-VMHardDiskDrive` y `Get-VHD`, además de consultas de solo lectura del sistema operativo del host, las unidades y el servicio `vmms`. La cuenta necesita por tanto permiso para abrir una sesión WinRM en el host y ejecutar esos cmdlets. Ninguna fuente oficial identifica un conjunto de roles más reducido, así que no se documenta una política de mínimo privilegio; usa una cuenta dedicada para Pandora FMS y concédele solo lo que esas consultas necesitan.

La tarea es de solo lectura: no arranca, detiene, modifica ni crea nada en el host.

### Consideraciones de seguridad

El addon se autentica con HTTP Basic sobre `http://` en el puerto `5985`. El usuario y la contraseña viajan codificados en Base64, lo que no es cifrado, por lo que cualquiera que pueda observar el tráfico entre el servidor de Discovery y el host puede leerlos. Ejecuta la tarea solo en una red de confianza o aísla ese trayecto. Usa una cuenta dedicada con una contraseña que no uses en ningún otro sitio.

El addon no verifica certificados TLS, porque no usa TLS.

### Instalar el addon

Descarga el paquete `.disco` desde la entrada del Marketplace de Pandora FMS, cuya descarga está limitada a usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.hyperv](https://marketplace.pandorafms.com/entries/pandorafms.hyperv)

Cárgalo en Pandora FMS. Una vez cargado, **Hyper-V** estará disponible al crear tareas de Discovery.

## Configurar la tarea de Discovery

Crea la tarea desde las aplicaciones de Discovery y elige **Hyper-V**. La consola presenta los campos en dos pasos; cada campo está documentado en [Parámetros de la tarea](#parametros-de-la-tarea).

1. **Hyper-V Connection** — dónde y cómo conectar, y cómo se nombran los agentes:

    - **Hyper-V IP**: dirección o nombre del host Hyper-V. Obligatorio.
    - **HyperV Credentials**: la credencial custom con las claves `user` y `password`. Obligatorio.
    - **Agent prefix (optional)**: texto que se antepone al nombre de cada agente generado. Por defecto `HyperV`.
    - **Agent autodisable mode**: deshabilita el agente cuando todos sus módulos pasan a desconocido hasta que vuelvan datos.

    <!-- SCREENSHOT NEEDED: Paso Hyper-V Connection del asistente con Hyper-V IP, HyperV Credentials, Agent prefix y Agent autodisable mode, sin direcciones ni credenciales reales. -->

2. **Monitoring Tokens and Filters** — qué se monitoriza:

    - **Scan Hypervisor**: crea el agente del host Hyper-V. Desactivado por defecto.
    - **Scan VM**: crea un agente por VM. Activado por defecto.
    - **Scan Networking**: añade los módulos de adaptadores de red de cada VM. Desactivado por defecto.
    - **Scan Storage**: añade los módulos de discos virtuales de cada VM. Desactivado por defecto.
    - **Regexp to filter agents** y **Allow regexp**: solo se crean las VM cuyo nombre coincide con el patrón. **Allow regexp** se muestra cuando la casilla está activada.
    - **Regexp to discard agents** y **Deny regexp**: no se crean las VM cuyo nombre coincide con el patrón. **Deny regexp** se muestra cuando la casilla está activada.

    <!-- SCREENSHOT NEEDED: Paso Monitoring Tokens and Filters del asistente con las cuatro casillas de escaneo y los campos de expresión regular de permitir y denegar, usando solo valores de laboratorio. -->

El grupo y el intervalo de la tarea proceden del paso genérico de definición de la tarea y se aplican a todos los agentes que crea.

## Verificar la primera ejecución

Fuerza la tarea desde la lista de tareas de Discovery y comprueba el resultado en este orden.

1. **El resumen de la tarea.** Una tarea que conecta correctamente informa de:

    - **hyperv_host**: el host consultado.
    - **VMs**: VM encontradas en el host, antes de aplicar los filtros de permitir y denegar.
    - **Agents**: agentes generados.

    <!-- SCREENSHOT NEEDED: Resumen de ejecución de una tarea de Discovery de Hyper-V con hyperv_host, VMs y Agents. -->

    Cuando el addon no puede conectar, el resumen muestra `status` con valor `ERROR`, el host y un `message` que identifica la causa; consulta [Solucionar problemas](#solucionar-problemas).

2. **Los agentes.** Uno por cada VM que supere los filtros y, con **Scan Hypervisor** activado, uno para el host.
3. **Los módulos.** Con **Scan VM** activado, cada agente de VM tiene `State`, `CPU Usage` y el resto de módulos de [Módulos por agente](#modulos-por-agente). Una VM en estado `Off` tiene `State` a `3`, que es crítico.

## Entender los resultados

### Agentes generados

| Agente | Nombre | Dirección | Notas |
|--------|--------|-----------|-------|
| Agente del host | `<prefijo> <ComputerName>` | El valor de **Hyper-V IP** | Se crea solo con **Scan Hypervisor** activado. `ComputerName` es el nombre que informa el host; si no devuelve ninguno se usa el valor de **Hyper-V IP**. Sistema operativo `Windows`, versión `Windows Server` |
| Agente de VM | `<prefijo> <nombre de la VM>` | Primera dirección IPv4 utilizable de la VM; el valor de **Hyper-V IP** si no tiene | Uno por VM que supere los filtros. Sistema operativo `Windows`, versión `Windows` |

Detalles comunes:

- El prefijo se separa del nombre con un espacio. En el prefijo, los caracteres distintos de letras, dígitos, `.`, `_` y `-` se sustituyen por `_`, y se eliminan los `_` y espacios finales. En el nombre de la VM, los caracteres distintos de letras, dígitos, `.`, `_`, `-` y espacios se sustituyen por `_`. Con un prefijo vacío, el nombre es solo el del host o la VM.
- Una dirección IPv4 utilizable excluye las de loopback (`127.x`) y link-local (`169.254.x`). La dirección se toma primero de la VM y, en segundo lugar, de sus adaptadores de red.
- La identidad del agente depende de su nombre: cambiar **Agent prefix** o renombrar una VM crea un agente nuevo en lugar de actualizar el existente.
- Los agentes de VM no son hijos del agente del host.
- Con **Scan VM** desactivado, los agentes de VM se siguen creando si **Scan Networking** o **Scan Storage** están activados, y contienen solo esos módulos. Si no se aplica ninguna de las tres opciones, no se crea ningún agente de VM.

### Módulos por agente

**Agente del host**

| Módulo | Tipo | Descripción |
|--------|------|-------------|
| `HyperV Connection Status` | `generic_proc` | `1` cuando la conexión WinRM funciona. Siempre presente |
| `Memory Used Percent` | `generic_data` | Porcentaje de memoria del host en uso, en `%` |
| `DiskUsed_<unidad>` | `generic_data` | Espacio usado de cada unidad del sistema de archivos con espacio usado, en `GB`. El espacio libre figura en la descripción |
| `VMMS Service Status` | `generic_data` | Estado del servicio Hyper-V Virtual Machine Management: `1` Stopped, `2` StartPending, `3` StopPending, `4` Running, `5` ContinuePending, `6` PausePending, `7` Paused; `0` si no se encuentra el servicio. Crítico en `1` y `2` |

Si las consultas al host fallan, el agente se crea igualmente solo con `HyperV Connection Status`.

**Agente de VM, Scan VM**

| Módulo | Tipo | Descripción |
|--------|------|-------------|
| `State` | `generic_data` | `2` Running, `3` Off, `32768` Paused, `32769` Saved, `32770` Starting, `32771` Stopping, `32772` Pausing, `32773` Resuming, `32774` Saving, `32775` FastSaved, `0` Unknown. Crítico en `3` |
| `CPU Usage` | `generic_data` | Uso de CPU, en `%` |
| `Memory Assigned MB` | `generic_data` | Memoria asignada a la VM, en `MB` |
| `Memory Demand MB` | `generic_data` | Memoria demandada por la VM, en `MB` |
| `Uptime` | `generic_data` | Uptime de la VM, en timeticks |
| `Status` | `generic_data_string` | Texto de estado operativo que informa Hyper-V |
| `Generation` | `generic_data` | Generación de la VM |
| `Replication State` | `generic_data` | `0` Disabled, `1` ReadyForReplication, `2` InitialReplicationInProgress, `3` Replicating, `4` Synced, `5` Recovered, `6` Committed, `7` Suspended, `8` Resynchronizing, `9` ResynchronizeSuspended, `10` Error |

**Agente de VM, Scan Networking**: cuatro módulos por cada adaptador de red de la VM. `<nic>` es el nombre del adaptador con los caracteres distintos de letras, dígitos, `.`, `_` y `-` sustituidos por `_`; si una VM tiene varios adaptadores con el mismo nombre se añaden `_1`, `_2`, etc.

| Módulo | Tipo | Descripción |
|--------|------|-------------|
| `<nic>-connected` | `generic_proc` | `1` si el adaptador está conectado, `0` en caso contrario |
| `<nic>-status` | `generic_data` | `1` si está conectado, `4` si no. Advertencia de `2` a `3`, crítico en `4` |
| `<nic>-switchname` | `generic_data_string` | Nombre del switch virtual; `0` si no hay |
| `<nic>-ipaddresses` | `generic_data_string` | Direcciones IP separadas por comas; `0` si no hay |

**Agente de VM, Scan Storage**: cinco módulos por cada disco virtual que el host puede leer, numerados `disk1`, `disk2`, etc. en el orden devuelto.

| Módulo | Tipo | Descripción |
|--------|------|-------------|
| `disk<n>-path` | `generic_data_string` | Ruta del archivo del disco virtual |
| `disk<n>-SizeGB` | `generic_data` | Tamaño máximo configurado, en `GB` |
| `disk<n>-FileSizeGB` | `generic_data` | Tamaño del archivo en el host, en `GB` |
| `disk<n>-DiskType` | `generic_data` | `1` Fixed, `2` Dynamic, `3` Differencing |
| `disk<n>-DiskFormat` | `generic_data_string` | Formato del disco, por ejemplo `VHD` o `VHDX` |

## Operar

### Ejecución manual

El addon puede ejecutarse fuera de una tarea de Discovery. El ejecutable recibe la ruta a un archivo de configuración descrito en [Archivo de configuración](#archivo-de-configuracion):

```bash
./pandora_hyperV --conf <PATH_TO_CONFIG>
```

Imprime un documento JSON con el `summary`, el `monitoring_data` de cada agente y, si hay errores, una clave `info` con los mensajes. El código de salida es `1` cuando se registró algún error.

Un archivo de configuración contiene la credencial codificada en `credentials`. Protégelo con permisos restrictivos.

### Modo local

Con `--execute_local` el ejecutable lanza las consultas de PowerShell en la máquina donde se inicia, en lugar de conectar por WinRM. No hacen falta `hyperv_host` ni credenciales, y cualquier credencial del archivo se ignora. La máquina debe ser el host Hyper-V y tener PowerShell disponible (`pwsh`, `powershell.exe` o `powershell`).

```bash
./pandora_hyperV --conf <PATH_TO_CONFIG> --execute_local
```

En este modo imprime solo el `monitoring_data` como JSON con sangría, y el agente del host contiene `HyperV Local Status` en lugar de `HyperV Connection Status`. Añade `--save_file` para escribir ese JSON en `hyperv_local_<hostname>_<timestamp>.txt` en el directorio actual en lugar de imprimirlo; `--save_file` se rechaza sin `--execute_local`. La tarea de Discovery no usa el modo local.

## Solucionar problemas

El addon no tiene opción verbose ni de depuración. Su canal de diagnóstico es el campo `info` del resultado JSON de la ejecución, que se muestra en la información de ejecución de la tarea.

Cuando falla la comprobación de conexión, la tarea termina con código de salida `1`, `status` `ERROR` y uno de estos mensajes:

- **`Unable to authenticate to host '<host>' authentication failed.`**: HTTP `401`. Revisa el usuario y la contraseña de la credencial y que el host acepte autenticación Basic.
- **`Access denied when connecting to host '<host>'.`**: HTTP `403`. La cuenta no tiene permitido abrir una sesión WinRM.
- **`Unable to reach host '<host>' connection timed out.`**: sin respuesta en 15 segundos para conectar o 30 en total. Revisa el enrutamiento y los cortafuegos.
- **`Unable to connect to host '<host>' verify WinRM is enabled and the firewall allows TCP 5985.`**: conexión rechazada. WinRM no escucha en el `5985`.
- **`Unable to connect to the specified host '<host>'. Error: ...`**: cualquier otro fallo, como un nombre que no se resuelve (`Unable to resolve host`), un host inalcanzable o la ausencia de `curl`. El mensaje incluye el error.

Otras señales aparecen en `info` con código de salida `1`:

- **`Missing required parameter: hyperv_host`**: el host está vacío.
- **`Missing credentials (user or password empty)`** o **`Error while parsing configuration credentials: ...`**: la credencial no tiene `user` o `password`, o no es JSON válido codificado en Base64.
- **`Configuration file not found: ...`** o **`Error reading config: ...`**: el archivo de configuración indicado con `--conf` no existe o no se puede leer.

Situaciones que no hacen fallar la tarea:

- **La tarea termina bien pero no crea agentes**: la conexión funciona pero las consultas de Hyper-V no devolvieron nada o fallaron. Los mensajes (`[vms] Get-VM error: ...`) solo están en `info`, y el resumen informa `VMs` como `0`. Comprueba que la cuenta puede ejecutar los cmdlets de [Permisos](#permisos) y que el rol Hyper-V está instalado en el host.
- **Menos agentes de VM que `VMs`**: la expresión regular de permitir o denegar los ha filtrado. `VMs` cuenta las VM encontradas antes de filtrar.
- **Un agente de VM no tiene módulos de red o de disco**: **Scan Networking** o **Scan Storage** están desactivados, o el host no pudo leer los adaptadores o discos de esa VM. Los discos cuyo archivo `Get-VHD` no puede leer se omiten.
- **Una VM no tiene dirección propia**: la VM no informa de ninguna IPv4 utilizable, por ejemplo porque los servicios de integración no se están ejecutando, así que el agente usa el valor de **Hyper-V IP**.
- **Un agente de VM muestra `State` crítico**: la VM está apagada (`State` `3`). El agente sigue informando; el resto de módulos conservan los valores que devuelve Hyper-V.

## Referencia

### Parámetros de la tarea

#### Hyper-V Connection

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|-------------|-------|
| Hyper-V IP | `_hypervhost_` | cadena | vacío | Obligatorio. Dirección o nombre del host Hyper-V |
| HyperV Credentials | `_credentials_` | selector de credencial (custom) | — | Obligatorio. Debe proporcionar las claves `user` y `password` |
| Agent prefix (optional) | `_agentprefix_` | cadena | `HyperV` | Opcional. Texto antes del nombre del agente; consulta [Agentes generados](#agentes-generados) |
| Agent autodisable mode | `_agentautodisable_` | casilla | desactivada | Deshabilita el agente cuando todos sus módulos pasan a desconocido hasta que vuelvan datos |

#### Monitoring Tokens and Filters

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|-------------|-------|
| Scan Hypervisor | `_monitorHypervisor_` | casilla | desactivada | Crea el agente del host |
| Scan VM | `_tokenVM_` | casilla | activada | Crea un agente por VM con los módulos de VM |
| Scan Networking | `_tokenNetworking_` | casilla | desactivada | Añade módulos de adaptadores de red a cada agente de VM |
| Scan Storage | `_tokenStorage_` | casilla | desactivada | Añade módulos de discos virtuales a cada agente de VM |
| Regexp to filter agents | `_regexpFilter_` | casilla | desactivada | Muestra **Allow regexp** |
| Allow regexp | `_allowRegexp_` | cadena | vacío | Opcional. Solo se crean las VM cuyo nombre coincide |
| Regexp to discard agents | `_regexpDiscard_` | casilla | desactivada | Muestra **Deny regexp** |
| Deny regexp | `_denyRegexp_` | cadena | vacío | Opcional. No se crean las VM cuyo nombre coincide |

Ambas expresiones regulares se buscan en cualquier posición del nombre de la VM, sin distinguir mayúsculas de minúsculas, y se comprueban contra el nombre de la VM sin el prefijo. Se aplican solo a los agentes de VM; el agente del host no se filtra. Una VM debe cumplir la expresión de permitir y no coincidir con la de denegar.

### Archivo de configuración

Se usa en la ejecución manual y lo escribe la tarea de Discovery a partir de los campos anteriores. Un `clave = valor` por línea. Los indicadores aceptan `1`, `true`, `yes` u `on` para activar.

| Clave | Por defecto | Descripción |
|-------|-------------|-------------|
| `hyperv_host` | vacío | Obligatorio salvo en modo local. Dirección o nombre del host Hyper-V |
| `credentials` | vacío | Obligatorio salvo en modo local. Base64 del JSON `{"user": "<USERNAME>", "password": "<PASSWORD>"}` |
| `agent_prefix` | `HyperV` | Prefijo del nombre de los agentes |
| `agents_group_id` | `0` | Identificador del grupo de los agentes generados |
| `interval` | `300` | Intervalo del agente, en segundos |
| `agent_autodisable` | `0` | Modo autodisable |
| `scan_hypervisor` | `0` | Agente del host |
| `scan_vm` | `1` | Agentes de VM |
| `scan_networking` | `0` | Módulos de adaptadores de red |
| `scan_storage` | `0` | Módulos de discos virtuales |
| `allow_list` | vacío | Expresión regular de permitir |
| `reject_list` | vacío | Expresión regular de denegar |

Ejemplo:

```ini
hyperv_host       = <HYPERV_HOST>
credentials       = <BASE64_CREDENTIALS>
agent_prefix      = HyperV
agents_group_id   = 0
interval          = 300
agent_autodisable = 0
scan_hypervisor   = 1
scan_vm           = 1
scan_networking   = 1
scan_storage      = 1
allow_list        =
reject_list       = ^template-
```

### Línea de comandos

| Opción | Obligatoria | Descripción |
|--------|-------------|-------------|
| `--conf <conf_file>` | Sí | Ruta al archivo de configuración |
| `--execute_local` | No | Ejecuta las consultas de PowerShell en local en lugar de por WinRM |
| `--save_file` | No | Solo con `--execute_local`. Guarda el JSON en un archivo en lugar de imprimirlo |

### Identidad del addon

| Elemento | Valor |
|----------|-------|
| Nombre | Hyper-V |
| Identificador | `pandorafms.hyperv` |
| Versión | `1.1` |
| Tipo y sección | Discovery, `app` |
| Entrada del Marketplace | [pandorafms.hyperv](https://marketplace.pandorafms.com/entries/pandorafms.hyperv), actualizada el 2026-08-24 |
| Disponibilidad | La entrada del Marketplace indica que la descarga está limitada a usuarios con licencia |
