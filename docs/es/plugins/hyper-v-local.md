# Hyper-V local

*Última actualización del artículo: 2026-10-26.*

## Qué hace

El addon Hyper-V local lee el inventario de un host de Microsoft Hyper-V y
devuelve la definición de los agentes y módulos de Pandora FMS que le
corresponden, como un documento JSON. Es una herramienta de ejecución local: se
ejecuta en el servidor Windows que tiene el rol Hyper-V, consulta Hyper-V a
través de PowerShell del propio host y no necesita conexión remota, ni un
listener de WinRM, ni credenciales.

Cada ejecución produce:

- **Un agente para el host Hyper-V**, con módulos de memoria, discos locales y
  servicio de administración de máquinas virtuales. Es opcional y está
  desactivado por defecto.
- **Un agente por máquina virtual (VM)**, con módulos de estado, CPU, memoria,
  tiempo de actividad, replicación y, cuando se habilitan, de adaptadores de red
  y discos virtuales. Está activado por defecto.

El addon imprime el documento JSON en la salida estándar o lo escribe en un
archivo del directorio actual cuando se usa `--save_file`. No envía el documento
a Pandora FMS y no crea los agentes: el documento JSON es el resultado de la
ejecución.

El plugin de Hyper-V también se distribuye como addon de Discovery, con conexión
remota y una tarea de Discovery. Ese addon y su propio modo local se documentan
en [Hyper-V Discovery](../discovery/hyper-v.md#modo-local).

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
|--------|--------|-----------|
| Addon `pandorafms.hyperv.local`, versión `1.0` | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del addon](#identidad-del-addon) |
| Windows Server 2022 con el rol Hyper-V, ejecución local | `Known compatible` | La guía oficial del addon, enlazada desde su entrada de Marketplace, indica que la ejecución local se probó en Windows Server 2022; no hay un registro de prueba independiente |
| Otras versiones de Windows Server con el rol Hyper-V | `Not validated` | Ningún registro de prueba ni declaración de soporte las cubre |
| PowerShell disponible en el `PATH` (`pwsh`, `powershell.exe` o `powershell`) | `Required` | El ejecutable realiza todas las consultas de Hyper-V mediante PowerShell |
| El rol Hyper-V y sus cmdlets de PowerShell en el host | `Required` | Las consultas usan `Get-VM`, `Get-VMHost`, `Get-VMNetworkAdapter`, `Get-VMHardDiskDrive`, `Get-VHD`, `Get-CimInstance`, `Get-PSDrive` y `Get-Service` |
| Una cuenta autorizada a ejecutar esos cmdlets | `Required` | Requisito previo, no una declaración de compatibilidad. Consulte [Permisos](#permisos) |
| Servicios de integración de Hyper-V en las VM Linux | `Required` para informar la dirección de las VM | Una VM Linux no informa ninguna dirección IP a Hyper-V sin ellos; entonces la dirección del agente pasa a ser el nombre del host |
| Pandora FMS NG 784 y posteriores | `Supported` | El Marketplace indica que sus integraciones son compatibles con estas versiones; es una declaración de todo el catálogo que cubre este addon, no un registro de prueba |

### Requisitos

1. **Un servidor Windows con el rol Hyper-V** donde se ejecutan las VM. El addon
   consulta la instancia local de Hyper-V; no puede consultar otro host.
2. **PowerShell que pueda cargar los cmdlets de Hyper-V**, disponible en el
   `PATH` de la cuenta que ejecuta el ejecutable.
3. **Una cuenta autorizada a ejecutar esos cmdlets** en el host.
4. **Un archivo de configuración**, pasado con `--conf` en cada ejecución.

Las VM Linux necesitan los servicios de integración de Hyper-V (el demonio KVP,
`hv-kvp-daemon`) para informar sus direcciones IP. Sin ellos el agente de la VM existe igualmente, pero
su dirección es el nombre del host.

### Permisos

El addon solo lee. Consulta el inventario de Hyper-V, la memoria del host, los
discos locales y el estado del servicio `vmms`; no inicia, detiene, modifica ni
crea VM, discos ni servicios.

Ninguna fuente oficial identifica un conjunto de permisos más restrictivo que la
ejecución de esos cmdlets. Use una cuenta dedicada con el acceso que necesitan
las consultas y no le conceda nada más. En ejecución local, el ejecutable se
ejecuta con los privilegios de la cuenta que lo inicia.

### Consideraciones de seguridad

- La ejecución local no abre ninguna conexión de red ni envía nada fuera del
  host. No necesita credenciales y las claves del modo remoto se ignoran.
- El documento JSON contiene el nombre del host, los nombres de las VM, las rutas
  de los discos virtuales y las direcciones IP de las VM. Trate un documento
  guardado como un inventario del host: guárdelo donde solo puedan leerlo los
  operadores que lo necesiten.
- El documento no contiene credenciales ni tokens.

### Instalar el addon

Descargue el addon desde su entrada de Marketplace. La descarga es gratuita y
consiste en un único ejecutable de Windows, listado como
`pandorafms.hyperv.local.1.0.exe`. Cópielo al host Hyper-V, por ejemplo a la
carpeta donde guarda las herramientas de Pandora FMS.

Los ejemplos de esta página usan el nombre de archivo `pandora_hyperV.exe`; use
el nombre que haya dado al archivo descargado.

No hay que instalar nada más en el host aparte del rol Hyper-V y PowerShell.

## Configuración

El ejecutable lee todos sus ajustes del archivo que se pasa con `--conf`. El
archivo es obligatorio en cada ejecución, también en ejecución local, pero puede
estar vacío: un archivo vacío aplica los valores por defecto.

### Formato del archivo de configuración

El archivo usa una línea `clave = valor` por cada ajuste:

- La cabecera `[sección]` es opcional. Un archivo sin ella se lee como una única
  sección.
- Los nombres de las claves no distinguen mayúsculas de minúsculas.
- Las líneas que empiezan por `#` o `;` son comentarios.
- No se admiten comentarios al final de la línea: un `#` después de un valor
  forma parte del valor.
- Las claves booleanas aceptan `1`, `true`, `yes` u `on` para activarse, en
  cualquier combinación de mayúsculas y minúsculas; cualquier otro valor las
  desactiva.

La ejecución local ignora las claves del modo remoto `hyperv_host` y
`credentials`, aunque estén presentes en el archivo.

Esta es una configuración completa para ejecución local:

```ini
# Ejecución local en el host Hyper-V
agent_prefix = HyperV
agents_group_id = 0
interval = 300
scan_hypervisor = 1
scan_vm = 1
scan_networking = 1
scan_storage = 1
```

### Seleccionar qué recopilar

| Clave | Valor por defecto | Efecto |
|-------|-------------------|--------|
| `scan_hypervisor` | Desactivado | Crea el agente del host Hyper-V |
| `scan_vm` | Activado | Crea un agente por VM con los módulos de VM |
| `scan_networking` | Desactivado | Añade los módulos de adaptador de red a cada agente de VM |
| `scan_storage` | Desactivado | Añade los módulos de disco virtual a cada agente de VM |

Los grupos de módulos son independientes: activar solo `scan_networking` crea
agentes de VM que contienen únicamente los módulos de adaptador. Una VM que no
produce ningún módulo de los grupos habilitados no obtiene agente. La
[Referencia](#referencia) enumera todos los módulos.

### Nombrar los agentes y fijar el intervalo

- `agent_prefix` se coloca delante del nombre del host o de la VM, separado por un
  espacio. El valor por defecto es `HyperV`, de modo que una VM llamada `vm01`
  produce el agente `HyperV vm01`. Con un prefijo vacío, el nombre del agente es
  solo el nombre del host o de la VM.
- En el prefijo, los caracteres distintos de letras, dígitos, `.`, `_` y `-` se
  sustituyen por `_`, y se eliminan los `_` y espacios finales. En el nombre de la
  VM, los caracteres distintos de letras, dígitos, `.`, `_`, `-` y espacios se
  sustituyen por `_`.
- El nombre del agente es la identidad del agente: cambiar el prefijo o renombrar
  una VM produce un nombre de agente distinto.
- `agents_group_id` es el identificador del grupo asignado a los agentes
  generados. El valor por defecto es `0`.
- `interval` es el intervalo del agente, en segundos. El valor por defecto es
  `300`.

### Filtrar las VM

`allow_list` y `reject_list` son expresiones regulares que se buscan en cualquier
posición del nombre de la VM, sin distinguir mayúsculas de minúsculas, y se
comparan con el nombre de la VM sin el prefijo:

- Una VM debe coincidir con `allow_list`, cuando está definida, para producir un
  agente.
- Una VM que coincide con `reject_list` no produce agente.
- El agente del host no se filtra.
- Una expresión regular no válida se ignora, por lo que no filtra nada.

## Verificación

Ejecute el ejecutable en el host Hyper-V, pasando el archivo de configuración con
`--conf` y seleccionando la ejecución local con `--execute_local`:

```powershell
.\pandora_hyperV.exe --conf <PATH_TO_CONFIG> --execute_local
```

Una ejecución correcta imprime el documento JSON y termina con estado `0`. El
documento es un array con un elemento por cada agente generado. Este es un
fragmento con un agente de VM y tres de sus módulos:

```json
[
  {
    "agent_data": {
      "agent_name": "HyperV vm01",
      "agent_alias": "HyperV vm01",
      "os": "Windows",
      "os_version": "Windows",
      "interval": 300,
      "id_group": 0,
      "address": "<HYPERV_HOST>",
      "description": "VM vm01 on Hyper-V host <HYPERV_HOST>"
    },
    "module_data": [
      {
        "name": "State",
        "type": "generic_data",
        "data": 2,
        "description": "VM state: 2=Running 3=Off 32768=Paused 32769=Saved 32770=Starting 32771=Stopping 32772=Pausing 32773=Resuming 32774=Saving 32775=FastSaved 0=Unknown. Current: Running",
        "min_critical": 3,
        "max_critical": 3.1
      },
      {
        "name": "CPU Usage",
        "type": "generic_data",
        "data": 7.0,
        "description": "CPU usage percentage",
        "unit": "%"
      },
      {
        "name": "Uptime",
        "type": "generic_data",
        "data": 88423900,
        "description": "VM uptime",
        "unit": "_timeticks_"
      }
    ]
  }
]
```

En este ejemplo la VM no informa ninguna dirección IPv4 utilizable, por lo que la
dirección del agente es el nombre del host. Cuando la VM informa una, la
dirección es esa dirección IPv4.

## Entender los resultados

### Agentes generados

| Agente | Se crea cuando | Nombre | Dirección | Campos de sistema operativo |
|--------|----------------|--------|-----------|-----------------------------|
| Agente del host | `scan_hypervisor` está activado | `<prefijo> <ComputerName>` | El nombre del equipo local | `Windows`, `Windows Server` |
| Agente de VM | Se aplica al menos un grupo de sondeo y la VM pasa los filtros | `<prefijo> <nombre de la VM>` | Primera dirección IPv4 utilizable de la VM; el nombre del equipo local cuando no tiene ninguna | `Windows`, `Windows` |

Detalles que se aplican a ambos:

- Una dirección IPv4 utilizable excluye las direcciones de loopback (`127.x`) y
  de enlace local (`169.254.x`).
- Todos los agentes de VM se informan con sistema operativo `Windows` y versión
  `Windows`, incluidas las VM Linux: el addon lee la VM desde Hyper-V, no desde
  el sistema invitado.
- Los agentes de VM no son hijos del agente del host.
- El número de agentes es el agente del host, cuando está habilitado, más un
  agente por cada VM que pasa los filtros y produce al menos un módulo.

### Grupos de módulos

- **Host.** `HyperV Local Status`, `Memory Used Percent`, un módulo
  `DiskUsed_<unidad>` por cada unidad del sistema de archivos con espacio usado y
  `VMMS Service Status`.
- **VM.** `State`, `CPU Usage`, `Memory Assigned MB`, `Memory Demand MB`,
  `Uptime`, `Status`, `Generation` y `Replication State`.
- **Adaptadores de red.** Cuatro módulos por adaptador: `<nic>-connected`,
  `<nic>-status`, `<nic>-switchname` y `<nic>-ipaddresses`.
- **Discos virtuales.** Cinco módulos por disco: `disk<n>-path`,
  `disk<n>-SizeGB`, `disk<n>-FileSizeGB`, `disk<n>-DiskType` y
  `disk<n>-DiskFormat`.

### Resultados parciales

El addon registra una consulta fallida como un grupo ausente y conserva el resto
del documento:

- Si falla la consulta del host, el agente del host se emite igualmente con solo
  `HyperV Local Status`.
- Si falla la consulta del inventario de VM, no se emite ningún agente de VM.
- Si falla la consulta de adaptadores o de discos, esos módulos faltan y se
  conservan los demás módulos de la VM.

`HyperV Local Status` vale `1` en todas las ejecuciones del ejecutable. No cambia
a `0` cuando una consulta falla, así que use la presencia de los demás módulos
para detectar una consulta fallida.

El estado de salida es `0` en estos resultados parciales. Solo una línea de
comandos no válida o un archivo de configuración ilegible producen un estado de
salida distinto de cero.

## Operar y resolver problemas

### Guardar la salida en un archivo

Añada `--save_file` para escribir el documento en un archivo en lugar de
imprimirlo:

```powershell
.\pandora_hyperV.exe --conf <PATH_TO_CONFIG> --execute_local --save_file
```

- El archivo se llama `hyperv_local_<hostname>_<timestamp>.txt` y se escribe en
  el directorio actual, en UTF-8.
- El ejecutable no imprime nada en la salida estándar e informa la ruta absoluta
  del archivo en la salida de error estándar, con el prefijo
  `[save_file] JSON saved to:`.
- `--save_file` solo es válido junto con `--execute_local`.

### Características de la ejecución

- El addon no guarda estado entre ejecuciones y solo lee. Puede ejecutarse
  manualmente en cualquier momento, tantas veces como sea necesario.
- No entrega datos a Pandora FMS: cada ejecución devuelve el documento JSON y
  termina.
- El ejecutable intenta primero `pwsh`, después `powershell.exe` y después
  `powershell`. El primero que exista debe poder cargar los cmdlets de Hyper-V;
  un PowerShell que arranca y falla no se reintenta con el siguiente.
- El tamaño del documento crece con el número de VM, adaptadores y discos.

### Solución de problemas

- **El ejecutable termina con estado `2` e imprime un mensaje de uso en la salida
  de error estándar** — la línea de comandos no es válida: falta `--conf`, hay una
  opción desconocida o se usó `--save_file` sin `--execute_local`.
- **El ejecutable termina con estado `1` e imprime `[]`** — la ruta pasada con
  `--conf` no existe o no se puede leer. Con `--save_file`, el archivo guardado
  contiene el array vacío. El mensaje de diagnóstico no se imprime en modo local.
- **El documento es `[]` con estado de salida `0`** — no hay ningún grupo de
  sondeo habilitado, o ninguna VM pasó los filtros. Revise las claves `scan_*` y
  las expresiones regulares.
- **El agente del host contiene solo `HyperV Local Status`** — fallaron las
  consultas del host. Compruebe que el PowerShell encontrado en el `PATH` puede
  ejecutar `Get-VMHost`, `Get-CimInstance`, `Get-PSDrive` y `Get-Service`, y que
  la cuenta puede usarlos.
- **No hay agentes de VM pero el agente del host existe** — falló la consulta del
  inventario de VM, o todas las VM quedaron filtradas por `allow_list` o
  `reject_list`.
- **Un agente de VM no tiene módulos de red o de disco** — `scan_networking` o
  `scan_storage` está desactivado, o falló la consulta correspondiente para esa
  VM.
- **Una VM no tiene dirección propia** — el sistema invitado no informa ninguna
  dirección IPv4 utilizable, por ejemplo porque sus servicios de integración no
  están en ejecución, así que el agente usa el nombre del host.
- **Una VM muestra `State` en estado crítico** — la VM está apagada (`State`
  `3`). Los demás módulos conservan los valores que devuelve Hyper-V.
- **`--save_file` no produce salida en pantalla** — es lo esperado: el documento
  va al archivo y solo se informa la ruta, en la salida de error estándar.

## Referencia

### Línea de comandos

```powershell
.\pandora_hyperV.exe --conf <PATH_TO_CONFIG> --execute_local [--save_file]
```

| Opción | Obligatoria | Descripción |
|--------|-------------|-------------|
| `--conf <PATH_TO_CONFIG>` | Sí | Ruta del [archivo de configuración](#archivo-de-configuracion). Debe existir, también en ejecución local; un archivo vacío aplica los valores por defecto. |
| `--execute_local` | Para la ejecución local | Ejecuta las consultas de PowerShell en la máquina donde se ejecuta el ejecutable. No necesita host ni credenciales. |
| `--save_file` | No | Solo con `--execute_local`. Escribe el documento JSON en `hyperv_local_<hostname>_<timestamp>.txt`, en el directorio actual, en lugar de imprimirlo. |
| `-h`, `--help` | No | Imprime el resumen de uso y termina. |

Sin `--execute_local`, el ejecutable usa el modo remoto por WinRM del plugin de
Hyper-V, que necesita `hyperv_host` y credenciales. Ese modo pertenece al flujo de
Discovery y se documenta en [Hyper-V Discovery](../discovery/hyper-v.md).

### Archivo de configuración

Un `clave = valor` por línea. La ejecución local ignora `hyperv_host` y
`credentials`.

| Clave | Valor por defecto | Descripción |
|-------|-------------------|-------------|
| `agent_prefix` | `HyperV` | Texto colocado delante del nombre del host o de la VM, separado por un espacio. Vacío usa solo el nombre |
| `agents_group_id` | `0` | Identificador del grupo de los agentes generados |
| `interval` | `300` | Intervalo del agente, en segundos |
| `scan_hypervisor` | Desactivado | Crea el agente del host |
| `scan_vm` | Activado | Crea un agente por VM con los módulos de VM |
| `scan_networking` | Desactivado | Añade los módulos de adaptador de red |
| `scan_storage` | Desactivado | Añade los módulos de disco virtual |
| `allow_list` | Vacío | Expresión regular; solo las VM que coinciden producen agente |
| `reject_list` | Vacío | Expresión regular; las VM que coinciden no producen agente |
| `monitor_hypervisor` | Desactivado | Nombre heredado de `scan_hypervisor`, se usa cuando esa clave falta o está vacía |
| `token_vm` | Activado | Nombre heredado de `scan_vm`, se usa cuando esa clave falta o está vacía |
| `token_networking` | Desactivado | Nombre heredado de `scan_networking`, se usa cuando esa clave falta o está vacía |
| `token_storage` | Desactivado | Nombre heredado de `scan_storage`, se usa cuando esa clave falta o está vacía |
| `hyperv_host` | Vacío | Solo modo remoto. Se ignora en ejecución local |
| `credentials` | Vacío | Solo modo remoto. Se ignora en ejecución local |

### Campos del agente

| Campo | Contenido |
|-------|-----------|
| `agent_name`, `agent_alias` | El nombre del agente; ambos campos contienen el mismo valor |
| `os` | `Windows` |
| `os_version` | `Windows Server` para el agente del host; `Windows` para todos los agentes de VM |
| `interval` | Intervalo del agente, en segundos |
| `id_group` | Identificador del grupo |
| `address` | Agente del host: el nombre del equipo local. Agente de VM: la primera dirección IPv4 utilizable, o el nombre del host cuando la VM no tiene ninguna |
| `description` | Agente del host: `Hyper-V host <ComputerName> (<host>)`. Agente de VM: `VM <nombre> on Hyper-V host <host>` |

### Módulos del agente del host

| Módulo | Tipo | Descripción |
|--------|------|-------------|
| `HyperV Local Status` | `generic_proc` | `1` en todas las ejecuciones; no cambia cuando una consulta falla |
| `Memory Used Percent` | `generic_data` | Memoria del host en uso, en `%` |
| `DiskUsed_<unidad>` | `generic_data` | Espacio usado de cada unidad del sistema de archivos con espacio usado, en `GB`; el espacio libre está en la descripción |
| `VMMS Service Status` | `generic_data` | Estado del servicio `vmms`: `1` Stopped, `2` StartPending, `3` StopPending, `4` Running, `5` ContinuePending, `6` PausePending, `7` Paused; `0` cuando no se encuentra el servicio. Crítico en `1` y `2` |

### Módulos del agente de la VM

| Módulo | Tipo | Descripción |
|--------|------|-------------|
| `State` | `generic_data` | `2` Running, `3` Off, `32768` Paused, `32769` Saved, `32770` Starting, `32771` Stopping, `32772` Pausing, `32773` Resuming, `32774` Saving, `32775` FastSaved, `0` Unknown. Crítico en `3` |
| `CPU Usage` | `generic_data` | Uso de CPU, en `%` |
| `Memory Assigned MB` | `generic_data` | Memoria asignada a la VM, en `MB` |
| `Memory Demand MB` | `generic_data` | Memoria que demanda la VM, en `MB` |
| `Uptime` | `generic_data` | Tiempo de actividad en timeticks (1/100 s), calculado a partir del tiempo de actividad que informa Hyper-V |
| `Status` | `generic_data_string` | Texto del estado operativo que informa Hyper-V |
| `Generation` | `generic_data` | Generación de la VM |
| `Replication State` | `generic_data` | `0` Disabled, `1` ReadyForReplication, `2` InitialReplicationInProgress, `3` Replicating, `4` Synced, `5` Recovered, `6` Committed, `7` Suspended, `8` Resynchronizing, `9` ResynchronizeSuspended, `10` Error |

### Módulos de los adaptadores de red

`<nic>` es el nombre del adaptador con los caracteres distintos de letras,
dígitos, `.`, `_` y `-` sustituidos por `_`. Cuando una VM tiene varios
adaptadores con el mismo nombre, se añaden `_1`, `_2`, etc.

| Módulo | Tipo | Descripción |
|--------|------|-------------|
| `<nic>-connected` | `generic_proc` | `1` cuando el adaptador está conectado, `0` en caso contrario |
| `<nic>-status` | `generic_data` | `1` Ok, `2` Degraded, `3` Unknown, `4` Error, deducido del estado de conexión: `1` conectado, `4` no conectado. Aviso de `2` a `3`, crítico en `4` |
| `<nic>-switchname` | `generic_data_string` | Nombre del conmutador virtual; `0` cuando no hay ninguno |
| `<nic>-ipaddresses` | `generic_data_string` | Direcciones IP separadas por comas; `0` cuando no hay ninguna |

### Módulos de los discos virtuales

`<n>` numera los discos de cada VM en el orden en que los devuelve Hyper-V,
empezando por `1`.

| Módulo | Tipo | Descripción |
|--------|------|-------------|
| `disk<n>-path` | `generic_data_string` | Ruta del archivo del disco virtual |
| `disk<n>-SizeGB` | `generic_data` | Tamaño máximo configurado, en `GB` |
| `disk<n>-FileSizeGB` | `generic_data` | Tamaño del archivo en el host, en `GB` |
| `disk<n>-DiskType` | `generic_data` | `1` Fixed, `2` Dynamic, `3` Differencing; `0` cuando se desconoce |
| `disk<n>-DiskFormat` | `generic_data_string` | Formato del disco, por ejemplo `VHD` o `VHDX` |

### Documento de salida

El documento es un array JSON. Cada elemento tiene un objeto `agent_data` y un
array `module_data`:

| Campo | Contenido |
|-------|-----------|
| `agent_data` | Identidad y metadatos del agente; consulte [Campos del agente](#campos-del-agente) |
| `module_data` | Un objeto por módulo: `name`, `type`, `data`, `description` y, cuando el módulo los define, `unit` y los umbrales `min_warning`, `max_warning`, `min_critical` y `max_critical` |

La ejecución local imprime solo este array. Los objetos `summary` e `info` del
modo remoto no forman parte de la salida local.

### Estado de salida

| Estado | Significado |
|--------|-------------|
| `0` | La ejecución terminó. El array puede estar vacío o contener resultados parciales |
| `1` | El archivo de configuración no existe o no se puede leer. La salida es un array vacío |
| `2` | Línea de comandos no válida: falta `--conf`, opción desconocida, o `--save_file` sin `--execute_local` |

### Identidad del addon

| Propiedad | Valor |
|-----------|-------|
| Identificador de Marketplace | `pandorafms.hyperv.local` |
| Nombre | Hyper-V local |
| Versión | `1.0` |
| Última actualización en Marketplace | 2026-05-28 |
| Licencia | Descarga gratuita |
| Autor | Pandora FMS |
| Archivo de descarga | `pandorafms.hyperv.local.1.0.exe` |
| Entrada de Marketplace | [pandorafms.hyperv.local](https://marketplace.pandorafms.com/entries/pandorafms.hyperv.local) |
| Documentación oficial | [Inglés](https://pandorafms.com/guides/public/books/hyper-v-windows-Hcs) · [Español](https://pandorafms.com/guides/public/books/hyper-v-windows) |
