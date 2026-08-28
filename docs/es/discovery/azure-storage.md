# Azure Storage Discovery

## Introducción

El plugin Azure Storage Discovery descubre automáticamente las cuentas de almacenamiento de una suscripción de Microsoft Azure, consulta mediante Azure Monitor las métricas de capacidad, operaciones, tráfico, latencia y disponibilidad de la cuenta y de los servicios Blob, File, Queue y Table, y genera los agentes y módulos correspondientes en Pandora FMS.

## Prerrequisitos

- El plugin se distribuye como un binario compilado y no requiere Python ni
  librerías adicionales en el servidor de Pandora FMS.
- Un servidor Pandora FMS con Discovery habilitado.
- Una suscripción de Microsoft Azure con cuentas de almacenamiento.
- Un grupo de agentes válido para la tarea. El grupo `All` no es válido porque
  su identificador es `0`.
- Para utilizar **Advanced container metrics**, la regla
  `ContainerLevelCapacityMetrics` debe estar habilitada previamente en Azure.

## Configuración de Azure

Cree un Service Principal de Microsoft Entra y asigne los roles **Reader** y
**Monitoring Reader** sobre la suscripción o el Resource Group que se quiera
descubrir. Guarde su **Client ID**, **Application secret**, **Tenant or domain
name** y **Subscription id** como una credencial de tipo Azure en el almacén de
credenciales de Pandora FMS.

Si necesita monitorización individual por contenedor, habilite previamente la
regla `ContainerLevelCapacityMetrics` para las Storage Accounts correspondientes.
El plugin comprueba el estado de esta regla, pero no la habilita en Azure.

## Parámetros

| Parámetro | Descripción |
| --- | --- |
| `--conf`, `-c` | Ruta obligatoria del fichero de configuración utilizado en la ejecución manual. |
| `--pretty` | Formatea el JSON de salida para facilitar su lectura. |
| `--version` | Muestra la versión del plugin, fijada en `1.0`. |
| `--help`, `-h` | Muestra la ayuda del comando. |

El fichero indicado mediante `--conf` admite las siguientes claves principales:

| Clave | Descripción | Valor predeterminado |
| --- | --- | --- |
| `credentials` | Credencial Azure codificada en Base64 y generada por Pandora FMS. | Vacío |
| `tenant_id`, `client_id`, `client_secret`, `subscription_id` | Valores de credenciales para ejecuciones manuales sin `credentials`. | Vacío |
| `group_id` | ID del grupo de Pandora FMS asignado a los agentes. Debe ser mayor que `0`. | Obligatorio |
| `custom_resource_group_enabled` | Limita el descubrimiento a un Resource Group exacto. | `0` |
| `resource_group` | Nombre exacto del Resource Group cuando la opción anterior está activada. | Vacío |
| `storage_account_names` | Nombres exactos de Storage Accounts separados por `;`. Vacío descubre todas. | Vacío |
| `create_agent_per_storage_account` | Crea un agente por Storage Account cuando está activado. | `1` |
| `target_agent` | Agente utilizado en modo consolidado. | `Azure Storage` |
| `agent_prefix` | Prefijo de los agentes creados por Storage Account. | `Azure Storage ` |
| `agent_autodisable` | Utiliza el modo de agente `2` al activarlo y el modo `1` al desactivarlo. | `0` |
| `interval` | Intervalo de monitorización heredado de la tarea de Discovery. | `300` en ejecución manual |
| `account_metrics_enabled` | Activa las métricas generales de la cuenta. | `1` |
| `blob_metrics_enabled` | Activa las métricas del servicio Blob. | `1` |
| `file_metrics_enabled` | Activa las métricas del servicio File. | `1` |
| `file_share_metrics_enabled` | Activa las métricas individuales de file shares. | `1` |
| `queue_metrics_enabled` | Activa las métricas del servicio Queue. | `1` |
| `table_metrics_enabled` | Activa las métricas del servicio Table. | `1` |
| `container_metrics_enabled` | Activa las métricas avanzadas por contenedor. | `0` |
| `container_regexp` | Expresión regular opcional aplicada a nombres de contenedores. | Vacío |
| `module_allow_list_file` | Fichero con una expresión regular de inclusión de módulos por línea. | Vacío |
| `module_deny_list_file` | Fichero con una expresión regular de exclusión de módulos por línea. | Vacío |
| `entities_list` | Ruta de la caché de entidades de Storage Accounts. | Vacío en ejecución manual |
| `enable_entities_interval` | Conserva las entidades hasta que vence el intervalo configurado. | `1` |
| `entities_interval` | Intervalo de reconstrucción de la caché en segundos. | `86400` |
| `timeout` | Timeout de las peticiones a Azure en segundos. | `30` |
| `management_endpoint` | Endpoint opcional de administración para nubes soberanas o personalizadas. | `https://management.azure.com` |
| `login_endpoint` | Endpoint opcional de Microsoft para nubes soberanas o personalizadas. | `https://login.microsoftonline.com` |

Los reintentos de petición están fijados internamente a `3` y no son
configurables.

## Ejecución manual

Para ejecutar el plugin manualmente se puede utilizar un fichero de
configuración mínimo como el siguiente:

```ini
[CONF]
tenant_id=11111111-1111-1111-1111-111111111111
client_id=22222222-2222-2222-2222-222222222222
client_secret=my_client_secret
subscription_id=00000000-0000-0000-0000-000000000000
group_id=2
```

El comando de ejecución es:

```bash
./pandora_azure_storage --conf /etc/pandora/pandora_azure.conf
```

Para mostrar el JSON de salida con formato legible:

```bash
./pandora_azure_storage --conf /etc/pandora/pandora_azure.conf --pretty
```

## Configuración en PandoraFMS

Cargue el paquete `.disco` desde **Management > Discovery > Extension manager**
y cree una tarea desde **Management > Discovery > Applications > Azure
Storage**.

**Step 1. Task definition**

- Seleccione el grupo donde se crearán los agentes. Debe ser un grupo con
  identificador mayor que `0`; no se puede utilizar `All`.

**Step 2. Azure base**

- **Azure credentials:** selecciona una credencial de tipo Azure del almacén de
  credenciales de Pandora FMS.
- **Custom Resource Group:** activado limita el descubrimiento a un Resource
  Group concreto. Está desactivado por defecto.
- **Resource group:** nombre exacto del Resource Group. Se muestra al activar
  **Custom Resource Group** y no admite expresiones regulares.

**Step 3. Advanced options**

- **Storage account names:** permite indicar uno o varios nombres completos de
  Storage Accounts separados por `;`. La coincidencia es exacta y no distingue
  entre mayúsculas y minúsculas. Vacío descubre todas las cuentas.
- **Create one agent per Storage Account:** activado crea un agente por cuenta;
  desactivado envía todos los módulos a **Target agent**.
- **Target agent:** agente utilizado cuando la creación por cuenta está
  desactivada. Su valor predeterminado es `Azure Storage`.
- **Agent name prefix:** prefijo utilizado al crear un agente por cuenta. Su
  valor predeterminado es `Azure Storage `.
- **Agent autodisable mode:** activado crea los agentes con `agent_mode=2`;
  desactivado utiliza `agent_mode=1`.
- **Enable entities file re-scan interval:** activado conserva la caché de
  cuentas hasta que se alcanza el intervalo seleccionado.
- **Entities re-scan interval:** intervalo antes de reconstruir la caché. Solo
  se muestra al activar el token anterior y su valor predeterminado es 1 día.
- **Request timeout:** timeout de cada petición a Azure. El valor predeterminado
  es 30 segundos.
- **Azure management endpoint:** endpoint opcional para nubes soberanas o
  personalizadas. Vacío utiliza `https://management.azure.com`.
- **Microsoft login endpoint:** endpoint opcional para nubes soberanas o
  personalizadas. Vacío utiliza `https://login.microsoftonline.com`.

**Step 4. Metrics and module filters**

- **Storage account metrics:** activa las métricas generales de la cuenta.
- **Blob service metrics:** activa las métricas del servicio Blob.
- **File service metrics:** activa las métricas del servicio File.
- **File share metrics:** activa las métricas individuales de file shares. Solo
  se muestra cuando **File service metrics** está activado.
- **Queue service metrics:** activa las métricas del servicio Queue.
- **Table service metrics:** activa las métricas del servicio Table.
- **Advanced container metrics:** comprueba si
  `ContainerLevelCapacityMetrics` está habilitada en Azure y genera módulos de
  capacidad utilizada y número de blobs para cada contenedor. También genera el
  porcentaje de capacidad cuando **Blob service metrics** está activado. No crea
  agentes adicionales y está desactivado por defecto.
- **Container regexp:** expresión regular opcional aplicada únicamente a los
  nombres obtenidos mediante **Advanced container metrics**. Vacío monitoriza
  todos los contenedores. No afecta a las métricas generales de Blob ni al
  módulo `Container Count`.
- **Modules allow regexp:** una regexp por línea. Solo permite los módulos que
  coincidan con alguna expresión.
- **Modules deny regexp:** una regexp por línea. Excluye los módulos que
  coincidan con alguna expresión.

## Agentes y módulos generados por el plugin

Con **Create one agent per Storage Account** activado, el plugin crea un agente
por cuenta con el nombre `<Agent name prefix><storage account name>`. Si el
prefijo no termina en espacio, guion, punto o guion bajo, se añade un espacio
automáticamente. Con el token desactivado se utiliza un único **Target agent** y
el nombre de la cuenta se añade al principio de cada módulo.

Los agentes utilizan `Azure` como sistema operativo, heredan el grupo y el
intervalo de la tarea y se crean con modo `2` cuando
**Agent autodisable mode** está activado o con modo `1` cuando está desactivado.

El módulo `Azure Storage Connection` se genera siempre como `generic_proc`, con
valor `1` para las cuentas descubiertas. Cuando una cuenta almacenada en la
caché deja de aparecer, se mantiene su agente y el módulo toma el valor `0`
hasta que la entidad se elimina al reconstruir la caché.

**Storage account metrics**

- `Account Used Capacity`: `generic_data`, GiB.
- `Account Capacity Quota`: `generic_data`, GiB; solo para cuentas Standard.
- `Account Used Capacity Percentage`: `generic_data`, porcentaje; solo para
  cuentas Standard.
- `Account Transactions_Current`: `generic_data`, requests.
- `Account Ingress_Current`: `generic_data`, bytes.
- `Account Egress_Current`: `generic_data`, bytes.
- `Account SuccessServerLatency_Current`: `generic_data`, ms.
- `Account SuccessE2ELatency_Current`: `generic_data`, ms.
- `Account Availability_Current`: `generic_data`, porcentaje.

Cuando la cuenta tiene habilitado el namespace jerárquico también se genera
`Data Lake Storage Gen2 Enabled` como `generic_proc`.

**Blob service metrics**

- `Blob Used Capacity`: `generic_data`, GiB.
- `Blob Object Count`: `generic_data`.
- `Blob Container Count`: `generic_data`.
- `Blob Index Capacity`: `generic_data`, GiB.
- `Blob Transactions_Current`: `generic_data`, requests.
- `Blob Ingress_Current`: `generic_data`, bytes.
- `Blob Egress_Current`: `generic_data`, bytes.
- `Blob SuccessServerLatency_Current`: `generic_data`, ms.
- `Blob SuccessE2ELatency_Current`: `generic_data`, ms.
- `Blob Availability_Current`: `generic_data`, porcentaje.

**File service metrics**

- `File Used Capacity`: `generic_data`, GiB.
- `File Object Count`: `generic_data`.
- `File Share Count`: `generic_data`.
- `File Snapshot Count`: `generic_data`.
- `File Snapshot Size`: `generic_data`, GiB.
- `File Capacity Quota`: `generic_data`, GiB.
- `File Transactions_Current`: `generic_data`, requests.
- `File Ingress_Current`: `generic_data`, bytes.
- `File Egress_Current`: `generic_data`, bytes.
- `File SuccessServerLatency_Current`: `generic_data`, ms.
- `File SuccessE2ELatency_Current`: `generic_data`, ms.
- `File Availability_Current`: `generic_data`, porcentaje.

**File share metrics**

- `File Share <name> Used Capacity`: `generic_data`, GiB.
- `File Share <name> Capacity Quota`: `generic_data`, GiB.
- `File Share <name> Used Capacity Percentage`: `generic_data`, porcentaje.

**Queue service metrics**

- `Queue Used Capacity`: `generic_data`, GiB.
- `Queue Count`: `generic_data`.
- `Queue Message Count`: `generic_data`.
- `Queue Transactions_Current`: `generic_data`, requests.
- `Queue Ingress_Current`: `generic_data`, bytes.
- `Queue Egress_Current`: `generic_data`, bytes.
- `Queue SuccessServerLatency_Current`: `generic_data`, ms.
- `Queue SuccessE2ELatency_Current`: `generic_data`, ms.
- `Queue Availability_Current`: `generic_data`, porcentaje.

**Table service metrics**

- `Table Used Capacity`: `generic_data`, GiB.
- `Table Count`: `generic_data`.
- `Table Entity Count`: `generic_data`.
- `Table Transactions_Current`: `generic_data`, requests.
- `Table Ingress_Current`: `generic_data`, bytes.
- `Table Egress_Current`: `generic_data`, bytes.
- `Table SuccessServerLatency_Current`: `generic_data`, ms.
- `Table SuccessE2ELatency_Current`: `generic_data`, ms.
- `Table Availability_Current`: `generic_data`, porcentaje.

**Advanced container metrics**

- `Blob Container Metrics Enabled`: `generic_proc`, con valor `1` cuando Azure
  tiene habilitada la regla avanzada y `0` cuando está deshabilitada.
- `Container <name> Used Capacity`: `generic_data`, GiB.
- `Container <name> Blob Count`: `generic_data`.
- `Container <name> Blob Capacity Percentage`: `generic_data`, porcentaje; se
  genera cuando **Blob service metrics** también está activado y Azure devuelve
  `BlobCapacity`.

Los filtros **Modules allow regexp** y **Modules deny regexp** se aplican al
nombre final de todos los módulos. En modo consolidado, el nombre final incluye
el prefijo de la cuenta de almacenamiento.
