# Azure Microsoft Compute Discovery

*Última actualización del artículo: 2026-09-08.*

## Qué monitoriza

El plugin de Discovery de Azure Microsoft Compute lee las máquinas virtuales de una suscripción de Microsoft Azure mediante las API de Azure Resource Manager y Azure Monitor y las convierte en agentes y módulos de Pandora FMS: un agente global opcional por suscripción, un agente por zona monitorizada (región de Azure) y un agente por máquina virtual monitorizada.

Los agentes de zona y de instancia informan siempre del estado de la máquina. Cuando **Scan and general monitoring** está habilitado, añaden métricas de CPU, disco, IOPS y red leídas de Azure Monitor. Una tarea de Discovery selecciona las zonas, los tamaños de VM o las máquinas virtuales individuales que se van a monitorizar; seleccionar una zona monitoriza la zona y todas las instancias que contiene.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Versión del plugin `1.4` (`pandorafms.azure.mc`) | Objetivo documentado | La versión que describe esta página, identificada en la definición del paquete. Consulte [Identidad del plugin](#identidad-del-plugin). |
| Rocky Linux y Fedora 34 | `Probado` | La matriz de compatibilidad oficial indica estos sistemas como probados para este plugin. |
| Cualquier sistema Linux | `Compatible conocido` | La matriz de compatibilidad oficial indica que el plugin funciona en cualquier sistema Linux. |
| Una suscripción de Microsoft Azure con máquinas virtuales | `Requerido` | El plugin lee las máquinas virtuales y las métricas mediante las API de Azure Resource Manager y Azure Monitor. Prerrequisito, no una declaración de compatibilidad. |
| Una credencial de registro de aplicación de Azure | `Requerido` | El plugin se autentica contra Azure con una entidad de servicio. Prerrequisito, no una declaración de compatibilidad. Consulte [Preparar el acceso a Azure](#preparar-el-acceso-a-azure). |
| Una versión concreta de Pandora FMS | `Sin validar` | Ningún registro de pruebas publicado demuestra compatibilidad con una versión de consola o de servidor. |

### Requisitos

1. **Un servidor de Pandora FMS con Discovery habilitado** para ejecutar la tarea, y una consola para definirla.
2. **Una suscripción de Microsoft Azure** que contenga las máquinas virtuales que se van a monitorizar.
3. **Una credencial de Azure** guardada en el almacén de credenciales de Pandora FMS.
4. **Un grupo de agentes de destino y un intervalo de monitorización** para los agentes generados. Ambos provienen de la tarea de Discovery y los heredan todos los agentes generados.
5. **Acceso de red al destino de Tentacle**: el plugin entrega los datos de los agentes generados mediante Tentacle, usando la **Tentacle IP** y el **Tentacle port** de la tarea.

El plugin se distribuye como una aplicación de Discovery de Pandora FMS (paquete `.disco`). Incluye los binarios `bin/pandora_azure_mc` y `bin/azure_vm` con sus dependencias empaquetadas, por lo que no es necesario instalar ningún runtime adicional en el servidor de Discovery ni para una ejecución manual.

### Preparar el acceso a Azure

Cree un registro de aplicación de Microsoft Entra (Azure AD) y asígnele un secreto de cliente. El plugin se autentica con el **Client ID**, el **Client secret**, el **Tenant or domain** y el **Subscription id** de ese registro. Guarde estos cuatro valores como una credencial de Azure en el almacén de credenciales de Pandora FMS, de modo que la tarea haga referencia a la credencial en lugar de transportar el secreto.

Asigne el rol **Reader** a la aplicación sobre la suscripción, o sobre el ámbito más reducido que se vaya a monitorizar, tal y como indican los prerrequisitos oficiales. El plugin solo lee máquinas virtuales y métricas y nunca modifica la configuración de Azure.

### Instalar el plugin

Cargue el paquete `.disco` desde **Management → Discovery → Extension manager**. Una vez cargado, **Azure Microsoft Compute** aparece en la categoría **Cloud** del asistente de Discovery.

## Configurar la tarea de Discovery

Cree la tarea desde **Management → Discovery → Cloud → Azure Microsoft Compute**. El primer paso genérico del asistente define la tarea; el paquete añade **Azure basic**, **Instance explorer** y **Metrics**. Todos los campos están documentados en [Parámetros de la tarea](#parametros-de-la-tarea).

**Paso 1 — Task definition.** Nombre, grupo de agentes, servidor e intervalo. El grupo y el intervalo se pasan al plugin y los heredan todos los agentes generados.

**Paso 2 — Azure basic.** Conexión, concurrencia y entrega:

- **Azure credentials** selecciona la credencial de Azure guardada que se usa para consultar la suscripción.
- **Max threads** reparte las zonas y las instancias entre varios trabajadores en paralelo.
- **Use proxy**, **Proxy url** y **Verify proxy SSL** enrutan las peticiones a Azure a través de un proxy HTTPS cuando el servidor de Discovery no puede alcanzar Azure directamente.
- **Tentacle IP**, **Tentacle port** y **Tentacle extra options** definen el destino de Tentacle que recibe los datos de los agentes generados.
- **Add global stats agent** habilita el agente de estadísticas por suscripción, y **Stats agent name** cambia su nombre por defecto (`azure`).
- **Agent autodisable mode** crea los agentes generados en el modo `2` de Pandora FMS, que deshabilita un agente cuando todos sus módulos pasan a desconocidos.

![Microsoft Compute Discovery task step 2](../assets/images/discovery/azure-microsoft-compute/AzureMC_step2.png)

**Paso 3 — Instance explorer.** Un árbol de la suscripción que se rellena consultando Azure con la credencial seleccionada. Cada nivel se puede marcar para su monitorización:

- Seleccionar una **zona** (región de Azure) monitoriza la propia zona y todas las máquinas virtuales que contiene, incluidas las que se añadan más adelante.
- Seleccionar un **tamaño de VM** dentro de una región monitoriza las máquinas virtuales de ese subgrupo.
- Seleccionar una **instancia** individual la monitoriza con independencia de si su zona está seleccionada.

![Microsoft Compute Discovery task step 3](../assets/images/discovery/azure-microsoft-compute/AzureMC_step3.png)

**Paso 4 — Metrics.** Qué datos de rendimiento se recogen:

- **Scan and general monitoring** habilita las consultas de métricas a Azure Monitor.
- **Cpu performance summary**, **IOPs performance summary**, **Disk performance summary** y **Network performance summary** seleccionan las familias de métricas que se recogen y solo se muestran cuando **Scan and general monitoring** está habilitado.
- **Azure Monitor metric interval** define el rango temporal y la granularidad que se usan en las consultas de métricas.

![Microsoft Compute Discovery task step 4](../assets/images/discovery/azure-microsoft-compute/AzureMC_step4.png)

La tarea hace referencia a la credencial de Azure guardada; cuando se ejecuta, el servidor de Discovery la resuelve en la configuración temporal que lee el plugin. Restrinja el acceso a Pandora FMS y a sus archivos de configuración y temporales de Discovery conforme a la política de seguridad de su despliegue.

## Verificar la primera ejecución

Fuerce la tarea desde **Management → Discovery → Task list** y compruebe el resultado en este orden.

1. **El resumen de la tarea** informa de **Total agents**, **Zones agents** e **Instances agents**.

2. **Los agentes.** Con **Add global stats agent** habilitado aparece primero un agente global; aparece un agente de zona por cada zona seleccionada y un agente de instancia por cada máquina virtual monitorizada.

3. **Los módulos de estado.** Todo agente de zona lleva `summary.azure.compute.instances`, y todo agente de instancia lleva `State` e `Instance State (bool)`.

4. **Los módulos de rendimiento.** Con **Scan and general monitoring** habilitado, las instancias en ejecución llevan sus módulos de CPU, disco, IOPS y red, y sus zonas llevan los módulos de resumen correspondientes.

Si no aparece ningún agente, lo primero que hay que revisar son los valores de la credencial, el rol **Reader** y la accesibilidad de los endpoints de Azure.

## Interpretar los resultados

### Distribución de agentes

El plugin crea un agente global por suscripción cuando **Add global stats agent** está habilitado, un agente de zona por cada zona seleccionada y un agente de instancia por cada máquina virtual monitorizada. Los agentes de zona y de instancia pertenecen al grupo de agentes de la tarea y heredan su intervalo.

El agente global se llama `azure` por defecto, o con el nombre de **Stats agent name**. Los agentes de zona usan la región de Azure seleccionada para la zona, y los agentes de instancia usan `<resource group>/<VM name>` como alias. El nombre interno de Pandora FMS de cada agente es el hash MD5 del identificador de suscripción más el identificador propio de ese agente (`azure`, la región de la zona o `<resource group>/<VM name>`); la única excepción es el agente global cuando **Stats agent name** está definido, que usa directamente ese nombre literal. Las identidades son, por tanto, estables entre ejecuciones de la misma tarea y cambian si cambian la suscripción o el ámbito seleccionado.

Los agentes de instancia se enlazan bajo el agente de zona de su zona, y los agentes de zona bajo el agente global cuando está habilitado.

### Módulos por agente

| Agente | Se crea cuando | Módulos que lleva |
| --- | --- | --- |
| Agente global de estadísticas | **Add global stats agent** habilitado | `Azure MC Instances count` |
| Agente de zona | Se selecciona una zona | `summary.azure.compute.instances`, más los módulos de rendimiento `summary.azure.compute.*` de cada familia habilitada |
| Agente de instancia | La máquina virtual está monitorizada | `State` e `Instance State (bool)` siempre; los módulos de CPU, disco, IOPS y red cuando **Scan and general monitoring** está habilitado y la máquina está en ejecución |

`summary.azure.compute.instances` informa del número de entradas distintas de tamaño de máquina virtual recogidas en la zona (cada combinación `VM size|región` cuenta una vez), no del número de máquinas. Los resúmenes de rendimiento de la zona agregan los valores por instancia recogidos durante la ejecución: la CPU como promedio y el resto como totales.

El inventario exhaustivo de módulos, tipos y unidades está en [Módulos y agentes generados](#modulos-y-agentes-generados).

## Solución de problemas

| Síntoma | Comprobación |
| --- | --- |
| No se crea ningún agente y la tarea falla | Confirme la credencial de Azure guardada (Client ID, Client secret, Tenant or domain, Subscription id), que la aplicación tenga el rol **Reader** sobre el ámbito monitorizado y que el servidor de Discovery pueda alcanzar los endpoints de Azure, directamente o a través del proxy configurado. |
| Una tarea sin nada seleccionado en el Instance explorer solo genera el agente global, con `Azure MC Instances count` a `0` | Seleccione al menos una zona, un tamaño de VM o una instancia en el paso Instance explorer. |
| El Instance explorer no muestra ningún árbol | La credencial no es válida, falta el rol **Reader** o los endpoints de Azure no son accesibles. Los campos de proxy solo tienen efecto cuando **Use proxy** está habilitado. |
| Una instancia muestra `State` como `Unknown` e `Instance State (bool)` a `0` | El plugin no pudo leer la vista de instancia de esa máquina. Compruebe que el rol **Reader** cubra su grupo de recursos. |
| Faltan módulos de rendimiento en una instancia | Solo se crean cuando **Scan and general monitoring** está habilitado, la familia de rendimiento correspondiente está activada y la máquina está en ejecución en el momento de la recogida. |
| Los resúmenes de rendimiento de la zona quedan a `0` | Agregan los valores por instancia recogidos en la misma ejecución; una zona cuyas máquinas están detenidas, o cuyas familias de rendimiento están deshabilitadas, informa de ceros. |
| `summary.azure.compute.instances` no coincide con el número de máquinas | El módulo cuenta las entradas de tamaño de VM por zona, no las máquinas. |
| No se reciben los datos de los agentes generados | Confirme la **Tentacle IP** y el **Tentacle port** y que el servidor acepte conexiones de Tentacle en ellos. |

## Referencia

### Parámetros de la tarea

La consola presenta los campos en dos pasos después de la definición genérica de la tarea, más un paso de árbol. La columna de macro es el identificador que se usa en la configuración de la tarea generada.

#### Azure basic

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Azure credentials | `_credentials_` | select | — | Credencial de Azure del almacén de credenciales de Pandora FMS. Obligatorio |
| Max threads | `_threads_` | number | `1` | Trabajadores que reparten zonas e instancias |
| Use proxy | `_useProxy_` | checkbox | off | Enruta las peticiones a Azure a través de un proxy HTTPS |
| Proxy url | `_proxyUrl_` | string | — | URL del proxy. Solo se muestra cuando **Use proxy** está habilitado |
| Verify proxy SSL | `_sslCheck_` | checkbox | off | Verifica el certificado TLS del proxy. Solo se muestra cuando **Use proxy** está habilitado |
| Tentacle IP | `_tentacleIP_` | string | `127.0.0.1` | Destino de Tentacle para los datos de los agentes generados |
| Tentacle port | `_tentaclePort_` | number | `41121` | Puerto del destino de Tentacle |
| Tentacle extra options | `_tentacleExtraOpt_` | string | — | Opciones adicionales que se pasan al cliente de Tentacle |
| Add global stats agent | `_statsAgent_` | checkbox | on | Crea el agente de estadísticas por suscripción |
| Stats agent name | `_statsAgentName_` | string | — | Cambia el nombre por defecto (`azure`). Solo se muestra cuando **Add global stats agent** está habilitado |
| Agent autodisable mode | `_agentautodisable_` | checkbox | off | Crea los agentes en el modo `2` de Pandora FMS, que deshabilita un agente cuando todos sus módulos pasan a desconocidos |

#### Metrics

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Scan and general monitoring | `_azureMCInstanceSummary_` | checkbox | off | Habilita las consultas de métricas a Azure Monitor |
| Cpu performance summary | `_azureMCCpuPerfSummary_` | checkbox | off | Módulos de utilización de CPU. Solo se muestra cuando **Scan and general monitoring** está habilitado |
| IOPs performance summary | `_azureMCIopsPerfSummary_` | checkbox | off | Módulos de operaciones de disco. Solo se muestra cuando **Scan and general monitoring** está habilitado |
| Disk performance summary | `_azureMCDiskPerfSummary_` | checkbox | off | Módulos de bytes de lectura y escritura de disco. Solo se muestra cuando **Scan and general monitoring** está habilitado |
| Network performance summary | `_azureMCNetworkPerfSummary_` | checkbox | off | Módulos de tráfico de red. Solo se muestra cuando **Scan and general monitoring** está habilitado |
| Azure Monitor metric interval | `_azureMCMetricInterval_` | select | `PT5M` | Rango temporal y granularidad de las consultas de métricas a Azure Monitor |

### Claves del archivo de configuración

La tarea de Discovery construye un archivo temporal de clave/valor a partir de sus propios campos y lo pasa al plugin con `--conf`. Una ejecución manual suministra ese archivo directamente. El archivo no tiene cabecera de sección; el plugin lo lee como una sección `[CONF]`. Las selecciones de zonas, tamaños e instancias se escriben como arrays JSON.

| Clave | Por defecto | Descripción |
| --- | --- | --- |
| `agents_group_name` | `azure` | Grupo de agentes de los agentes generados, procedente de la tarea |
| `interval` | `300` | Intervalo de monitorización en segundos, heredado por los agentes generados |
| `metric_interval` | `PT5M` | Rango temporal y granularidad de Azure Monitor. Valores admitidos `PT1M`, `PT5M`, `PT15M`, `PT30M`, `PT1H`, `PT6H`, `PT12H`, `P1D`; cualquier otro valor usa `PT5M` |
| `threads` | `1` | Trabajadores que reparten zonas e instancias |
| `transfer_mode` | `local` | `tentacle` o `local`. La tarea escribe `tentacle` |
| `tentacle_ip` | `127.0.0.1` | Destino de Tentacle |
| `tentacle_port` | `41121` | Puerto del destino de Tentacle |
| `tentacle_opts` | Vacío | Opciones adicionales que se pasan al cliente de Tentacle |
| `tentacle_client` | `tentacle_client` | Nombre del ejecutable del cliente de Tentacle |
| `data_dir` | `/var/spool/pandora/data_in/` | Destino de los archivos XML de agente cuando `transfer_mode` es `local` |
| `temporal` | `/tmp` | Directorio temporal para los archivos XML de agente |
| `use_proxy` | `0` | Enruta las peticiones a Azure a través de un proxy HTTPS |
| `proxy_url` | Vacío | URL del proxy |
| `ssl_check` | `0` | Verifica el certificado TLS del proxy |
| `advance_monitoring` | `1` | Habilita las consultas de métricas a Azure Monitor |
| `cpu_summary` | `1` | Módulos de rendimiento de CPU |
| `iops_summary` | `1` | Módulos de operaciones de disco |
| `disk_summary` | `1` | Módulos de bytes de lectura y escritura de disco |
| `network_summary` | `1` | Módulos de tráfico de red |
| `stats_agent` | `1` | Crea el agente de estadísticas por suscripción |
| `stats_agent_name` | Vacío | Nombre del agente de estadísticas; `azure` cuando está vacío |
| `agent_autodisable` | `0` | Crea los agentes en el modo `2` de Pandora FMS cuando está habilitado |
| `azure_zones` | `[]` | Lista JSON de regiones de Azure que se van a monitorizar |
| `azure_sizes` | `[]` | Lista JSON de entradas `VM size|región` que se van a monitorizar |
| `azure_instances` | `[]` | Lista JSON de instancias `<resource group>/<VM name>` que se van a monitorizar |
| `creds_b64` | Vacío | Credencial de Azure en JSON codificado en base64 (`client_id`, `application_secret`, `tenant_domain`, `subscription_id`) |

El archivo contiene la credencial en texto plano (codificada en base64) cuando se ejecuta la tarea. Restrinja el acceso a él y al directorio temporal de Discovery a la cuenta que ejecuta el plugin, manténgalo fuera de directorios compartidos, registros y control de versiones, y siga la política de su despliegue para las credenciales de Azure.

### Ejecución en línea de comandos

Una ejecución manual replica lo que hace el servidor de Discovery en cada ejecución de tarea. El plugin acepta un único archivo de configuración:

```bash
./pandora_azure_mc --conf <PATH_TO_CONFIG>
```

| Opción | Descripción |
| --- | --- |
| `--conf` | Ruta obligatoria al archivo de configuración |
| `--help`, `-h` | Muestra la ayuda del comando |

Ejemplo de archivo de configuración:

```ini
agents_group_name=azure
interval=300
threads=1
metric_interval=PT5M
transfer_mode=tentacle
tentacle_ip=<PANDORA_FMS_SERVER_IPV4>
tentacle_port=41121
advance_monitoring=1
cpu_summary=1
iops_summary=1
disk_summary=1
network_summary=1
stats_agent=1
stats_agent_name=
azure_zones=["<AZURE_REGION>"]
azure_instances=[]
azure_sizes=[]
creds_b64=<BASE64_AZURE_CREDENTIAL>
```

Ese archivo contiene una credencial en texto plano. Restrinja su acceso a la cuenta que ejecuta el plugin y manténgalo fuera de directorios compartidos, registros y control de versiones.

Una ejecución correcta imprime un resumen JSON de los agentes generados, por ejemplo `{"summary": {"Total agents": 35, "Zones agents": 5, "Instances agents": 29}}`, y entrega un archivo XML de datos por cada agente generado al servidor de Pandora FMS mediante el modo de transferencia configurado.

El árbol de instancias que muestra el asistente lo genera el helper `azure_vm` incluido, invocado con `--creds`, `--use_proxy`, `--proxy_url` y `--ssl_check`. Imprime el árbol como JSON y lo ejecuta el asistente de Discovery, no está pensado para ejecución manual.

### Módulos y agentes generados

**Agente global de estadísticas**

- `Azure MC Instances count`: `generic_data`, número de máquinas virtuales que el plugin monitorizó en la ejecución.

**Agente de zona** (`<región de Azure>`)

- `summary.azure.compute.instances`: `generic_data`, número de entradas distintas de tamaño de VM recogidas en la zona (cada combinación `VM size|región` cuenta una vez).
- `summary.azure.compute.CPUUtilization`: `generic_data`, promedio de los valores de utilización de CPU recogidos para las instancias de la zona.
- `summary.azure.compute.DiskReadBytes`: `generic_data`, bytes leídos; unidad `Bytes`.
- `summary.azure.compute.diskWriteBytes`: `generic_data`, bytes escritos; unidad `Bytes`.
- `summary.azure.compute.DiskReadOps`: `generic_data`, operaciones de lectura de disco.
- `summary.azure.compute.DiskWriteOps`: `generic_data`, operaciones de escritura de disco.
- `summary.azure.compute.NetworkPacketsIn`: `generic_data`, tráfico de red de entrada; unidad `packets`.
- `summary.azure.compute.NetworkPacketsOut`: `generic_data`, tráfico de red de salida; unidad `packets`.

**Agente de instancia** (`<resource group>/<VM name>`)

- `State`: `generic_data_string`, texto del estado de energía de la máquina según Azure.
- `Instance State (bool)`: `generic_proc`, `1` cuando la máquina está en ejecución, `0` en caso contrario.
- `CPUUtilization`: `generic_data`, porcentaje de uso de CPU.
- `DiskReadBytes`: `generic_data`, bytes leídos; unidad `Bytes`.
- `DiskWriteBytes`: `generic_data`, bytes escritos; unidad `Bytes`.
- `DiskReadOps`: `generic_data`, operaciones de lectura de disco.
- `DiskWriteOps`: `generic_data`, operaciones de escritura de disco.
- `NetworkPacketsIn`: `generic_data`, tráfico de red de entrada; unidad `packets`.
- `NetworkPacketsOut`: `generic_data`, tráfico de red de salida; unidad `packets`.

Los módulos de rendimiento de instancia solo se crean cuando **Scan and general monitoring** está habilitado, la familia de rendimiento correspondiente está activada y la máquina está en ejecución en el momento de la recogida. Los módulos de resumen de rendimiento de la zona solo se crean cuando **Scan and general monitoring** está habilitado y su familia está activada.

### Identidad del plugin

| Campo | Valor |
| --- | --- |
| App short name | `pandorafms.azure.mc` |
| Versión del plugin | `1.4` |
| Tipo | Aplicación de Discovery (`.disco`) |
| Sección | Discovery → Cloud |