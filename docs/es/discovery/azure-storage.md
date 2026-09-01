# Azure Storage Discovery

*Última actualización del artículo: 2026-09-01.*

## Qué monitoriza

El plugin de Discovery de Azure Storage descubre las cuentas de almacenamiento de una suscripción de Microsoft Azure y convierte sus métricas de Azure Monitor en agentes y módulos de Pandora FMS: capacidad, operaciones, tráfico, latencia y disponibilidad, tanto de la propia cuenta como de sus servicios Blob, File, Queue y Table.

Por defecto crea **un agente por cada Storage Account**, con un módulo de disponibilidad y un módulo por cada métrica habilitada. También puede consolidar todas las cuentas en un único agente. Las métricas por recurso compartido de archivos y por contenedor son extras opcionales.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
|--------|--------|-----------|
| Versión del plugin `1.0` (`pandorafms.azure_storage`) | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del plugin](#identidad-del-plugin) |
| Azure Resource Manager y Azure Monitor de Microsoft | `Requerido` | El plugin lee las cuentas y las métricas mediante estas API |
| Un service principal de Microsoft Entra con **Reader** y **Monitoring Reader** | `Requerido` | Prerrequisito, no una declaración de compatibilidad. Consulte [Preparar el acceso a Azure](#preparar-el-acceso-a-azure) |
| Un grupo de agentes de Pandora FMS con identificador mayor que `0` | `Requerido` | El grupo `All` tiene el identificador `0` y no puede usarse |
| Nubes soberanas o personalizadas de Azure | `Sin validar` | Los endpoints son configurables, pero ningún registro de pruebas demuestra el funcionamiento contra una nube que no sea la pública |
| Sistema operativo del host que ejecuta el plugin | `Sin validar` | Ningún registro de pruebas demuestra compatibilidad con sistemas operativos |

### Prerrequisitos

1. **Un servidor de Pandora FMS con Discovery habilitado** para ejecutar la tarea, y la consola para definirla.
2. **Una suscripción de Microsoft Azure** que contenga cuentas de almacenamiento.
3. **Una credencial de Azure** almacenada en el almacén de credenciales de Pandora FMS, o sus valores facilitados directamente para una ejecución manual.
4. **Un grupo de agentes válido** para la tarea. El grupo `All` no es válido, porque su identificador es `0`.
5. **Solo para las métricas avanzadas de contenedor**: la regla `ContainerLevelCapacityMetrics` ya habilitada en Azure. El plugin comprueba el estado de esa regla; nunca la habilita.

El plugin se distribuye como un ejecutable autocontenido: la aplicación de Discovery empaquetada incluye `bin/pandora_azure_storage`, por lo que no hay que instalar ningún runtime adicional, ni en el servidor de Pandora FMS ni para una ejecución manual.

### Preparar el acceso a Azure

Cree un service principal de Microsoft Entra y asígnele los roles **Reader** y **Monitoring Reader** sobre la suscripción o el Resource Group que se vaya a descubrir. Esos dos roles son lo que el plugin necesita: Reader para enumerar las cuentas de almacenamiento y Monitoring Reader para leer sus métricas. No conceda un rol más amplio.

Almacene su **Client ID**, **Application secret**, **Tenant o nombre de dominio** e **Subscription id** como credencial de Azure en el almacén de credenciales de Pandora FMS, de forma que la tarea referencie la credencial en lugar de contener el secreto.

Si necesita monitorización por contenedor, habilite la regla `ContainerLevelCapacityMetrics` en las Storage Accounts correspondientes antes de ejecutar la tarea.

### Instalar el plugin

Cargue el paquete `.disco` desde **Management → Discovery → Extension manager**.

## Configurar la tarea de Discovery

Cree la tarea desde **Management → Discovery → Cloud → Azure Storage**. El primer paso genérico del asistente define la tarea; el paquete añade otros tres. Todos los campos están documentados en [Parámetros de la tarea](#parametros-de-la-tarea).

**Paso 1 — Task definition.** Nombre, grupo, servidor e intervalo. El grupo debe tener un identificador mayor que `0`; `All` no puede usarse. El grupo y el intervalo se pasan al plugin y los heredan todos los agentes generados.

**Paso 2 — Azure base.** Qué suscripción leer y qué parte de ella:

- **Azure credentials** selecciona la credencial de Azure almacenada.
- **Custom Resource Group** limita el descubrimiento a un único Resource Group, y **Resource group** lo nombra de forma exacta. Aquí no se admiten expresiones regulares.

<!-- SCREENSHOT NEEDED: paso Azure base del asistente mostrando el selector de credencial, el conmutador Custom Resource Group y el campo Resource group, sin identificadores de tenant ni de suscripción visibles. -->

**Paso 3 — Advanced options.** Qué cuentas, cómo se nombran los agentes y cómo se alcanza Azure:

- **Storage account names** filtra por nombre exacto de cuenta, sin distinguir mayúsculas, y admite varios separados por `;`. Vacío descubre todas las cuentas.
- **Create one agent per Storage Account**, **Target agent** y **Agent name prefix** deciden la disposición de los agentes. Consulte [Interpretar los resultados](#interpretar-los-resultados).
- **Enable entities file re-scan interval** y **Entities re-scan interval** controlan cuánto tiempo se reutiliza la caché de cuentas descubiertas antes de reconstruirla.
- **Request timeout**, **Azure management endpoint** y **Microsoft login endpoint** cubren entornos lentos y nubes soberanas o personalizadas.
- **Debug** revela las opciones de mock local, que existen solo para pruebas. Consulte [Solución de problemas](#solucion-de-problemas).

<!-- SCREENSHOT NEEDED: paso Advanced options del asistente mostrando el filtro de nombres de cuenta, los conmutadores de disposición de agentes y los campos de endpoint, con el conmutador Debug desactivado. -->

**Paso 4 — Metrics and module filters.** Qué familias de métricas se recogen y qué módulos sobreviven:

- Un conmutador por servicio: métricas de **Storage account**, **Blob service**, **File service**, **Queue service** y **Table service**. **File share metrics** solo aparece cuando las métricas de File service están habilitadas.
- **Advanced container metrics** y **Container regexp** añaden módulos por contenedor.
- **Modules allow regexp** y **Modules deny regexp** admiten una expresión regular por línea y filtran los nombres finales de los módulos.

<!-- SCREENSHOT NEEDED: paso Metrics and module filters del asistente mostrando los conmutadores por servicio y los campos de expresiones regulares de inclusión y exclusión. -->

## Verificar la primera ejecución

Fuerce la tarea desde **Management → Discovery → Task list** y compruebe el resultado en este orden.

1. **El resumen de la tarea** informa de los agentes y módulos generados. Espere un agente por cada Storage Account descubierta, o un único **Target agent** cuando la creación por cuenta esté desactivada.

    <!-- SCREENSHOT NEEDED: resumen de ejecución de una tarea de Discovery de Azure Storage mostrando los totales de agentes y módulos generados. -->

2. **Los agentes.** Se llaman `<Agent name prefix><nombre de la storage account>` por defecto, es decir `Azure Storage micuenta`. Cada uno reporta `Azure` como sistema operativo y hereda el grupo y el intervalo de la tarea.

3. **`Azure Storage Connection`** vale `1` en todas las cuentas descubiertas. Un `0` significa que la cuenta estaba en la caché pero ya no es descubrible; consulte [Solución de problemas](#solucion-de-problemas).

4. **Los módulos de métricas** de cada servicio habilitado. El conjunto exacto depende de la cuenta: los módulos de cuota y porcentaje existen solo en cuentas Standard, y los módulos por recurso compartido o por contenedor solo cuando esas opciones están habilitadas.

Si no aparece ningún agente, lo primero que hay que revisar es la credencial y sus roles.

## Interpretar los resultados

### Disposición de los agentes

**Con Create one agent per Storage Account habilitado**, que es el valor por defecto, el plugin crea un agente por cuenta, con el nombre `<Agent name prefix><nombre de la storage account>`. Cuando el prefijo no termina en espacio, guion, punto o guion bajo, se inserta un separador, de modo que un prefijo `Azure Storage` se comporta como `Azure Storage `.

**Con la opción desactivada**, todos los módulos van al único **Target agent** y el nombre de la cuenta se antepone al nombre de cada módulo. Esto importa para el filtrado: las expresiones regulares de inclusión y exclusión se evalúan contra el nombre *final* del módulo, que en modo consolidado incluye ese prefijo de cuenta.

Los agentes generados reportan `Azure` como sistema operativo, heredan el grupo y el intervalo de la tarea, y se crean en el modo de agente `2` de Pandora FMS cuando **Agent autodisable mode** está habilitado, o en el modo `1` cuando está desactivado.

### Qué se crea

`Azure Storage Connection` se crea siempre, como `generic_proc`, con valor `1` para una cuenta descubierta. Cuando una cuenta en caché deja de ser descubrible, su agente se conserva y este módulo reporta `0` hasta que la entidad se elimina durante una reconstrucción de la caché.

Todo lo demás es `generic_data`, agrupado por la opción que lo habilita:

| Habilitado por | Qué obtiene |
| --- | --- |
| Storage account metrics | Capacidad, cuota y ocupación de la cuenta, más transacciones, entrada, salida, latencia y disponibilidad. Añade `Data Lake Storage Gen2 Enabled` cuando la cuenta tiene espacio de nombres jerárquico |
| Blob service metrics | Capacidad de Blob, recuentos de objetos y contenedores, capacidad de índice, y el mismo conjunto de tráfico, latencia y disponibilidad |
| File service metrics | Capacidad de File, recuentos de objetos, recursos compartidos e instantáneas, cuota, y el mismo conjunto de tráfico, latencia y disponibilidad |
| File share metrics | Capacidad usada, cuota y ocupación por recurso compartido |
| Queue service metrics | Capacidad de Queue, recuentos de colas y mensajes, y el mismo conjunto de tráfico, latencia y disponibilidad |
| Table service metrics | Capacidad de Table, recuentos de tablas y entidades, y el mismo conjunto de tráfico, latencia y disponibilidad |
| Advanced container metrics | `Blob Container Metrics Enabled`, más capacidad usada y recuento de blobs por contenedor |

Los módulos de cuota y ocupación se crean solo en cuentas Standard. Los nombres y unidades exhaustivos están en [Módulos generados](#modulos-generados).

## Solución de problemas

- **La tarea falla por el grupo** — el grupo de agentes debe tener un identificador mayor que `0`. `All` es el grupo `0` y no puede usarse.
- **No se descubre ninguna cuenta de almacenamiento** — revise el service principal en este orden: los valores de la credencial, después que **Reader** y **Monitoring Reader** estén asignados sobre el ámbito correcto, después si **Custom Resource Group** está acotando la búsqueda, y por último si **Storage account names** contiene un nombre que no coincide exactamente. Ese campo compara nombres completos, sin distinguir mayúsculas; no es una expresión regular.
- **Un agente sobrevive con `Azure Storage Connection` a `0`** — la cuenta está en la caché de entidades pero ya no es descubrible, porque se eliminó, se renombró o salió del ámbito configurado. El agente se conserva hasta que se reconstruye la caché, lo que ocurre tras el **Entities re-scan interval**.
- **`Blob Container Metrics Enabled` reporta `0`** — la regla `ContainerLevelCapacityMetrics` no está habilitada en Azure para esa Storage Account. El plugin informa del estado; habilite la regla en Azure.
- **Faltan módulos por contenedor aunque la regla esté habilitada** — **Container regexp** filtra los nombres de contenedor. Se aplica únicamente a los contenedores obtenidos mediante **Advanced container metrics**; nunca afecta a las métricas generales de Blob ni a `Blob Container Count`.
- **Faltan módulos esperados** — las expresiones regulares de inclusión y exclusión se evalúan contra el nombre final del módulo. En modo consolidado ese nombre lleva el prefijo de la storage account, así que una expresión escrita para el modo por cuenta no coincidirá.
- **Las peticiones agotan el tiempo de espera** — suba **Request timeout**. Cada petición se reintenta hasta tres veces; ese número de reintentos está fijado en el plugin y no es configurable.
- **Una nube soberana o personalizada es inalcanzable** — configure **Azure management endpoint** y **Microsoft login endpoint**. Los valores vacíos usan `https://management.azure.com` y `https://login.microsoftonline.com`.
- **Debug, Mock Azure API URL y Verify mock TLS certificate** existen para apuntar el plugin a un mock local durante las pruebas. Deje **Debug** desactivado en entornos reales, y no desactive nunca **Verify mock TLS certificate** salvo contra un mock local de confianza.

## Referencia

### Parámetros de la tarea

La consola presenta los campos de la tarea en tres pasos tras la definición genérica de la tarea. La columna de macro es el identificador usado en la configuración generada de la tarea.

#### Azure base

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|-------------|-------|
| Azure credentials | `_credentials_` | selector | — | Credencial de Azure del almacén de credenciales de Pandora FMS |
| Custom Resource Group | `_customresourcegroup_` | casilla | desactivada | Limita el descubrimiento a un Resource Group |
| Resource group | `_resourcegroup_` | cadena | — | Nombre exacto del Resource Group. Solo se muestra cuando la opción anterior está habilitada; no es una expresión regular |

#### Advanced options

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|-------------|-------|
| Storage account names | `_storageaccountregexp_` | cadena | — | Nombres completos de cuenta separados por `;`. La coincidencia es exacta y no distingue mayúsculas. Vacío descubre todas las cuentas |
| Create one agent per Storage Account | `_agentperstorageaccount_` | casilla | activada | Desactivada envía todos los módulos a **Target agent** |
| Target agent | `_targetagent_` | cadena | `Azure Storage` | Agente usado en modo consolidado |
| Agent name prefix | `_agentprefix_` | cadena | `Azure Storage ` | Prefijo de los agentes por cuenta. Se inserta un separador cuando el prefijo no termina en espacio, guion, punto o guion bajo |
| Agent autodisable mode | `_agentautodisable_` | casilla | desactivada | Habilitada crea agentes en modo `2`; desactivada usa el modo `1` |
| Enable entities file re-scan interval | `_enableentitiesinterval_` | casilla | activada | Reutiliza la caché de cuentas descubiertas hasta que expira el intervalo |
| Entities re-scan interval | `_entitiesinterval_` | selector | `86400` | Segundos antes de reconstruir la caché. Solo se muestra cuando la opción anterior está habilitada |
| Request timeout | `_timeout_` | número | `30` | Segundos por petición a Azure |
| Azure management endpoint | `_managementendpoint_` | cadena | — | Vacío usa `https://management.azure.com` |
| Microsoft login endpoint | `_loginendpoint_` | cadena | — | Vacío usa `https://login.microsoftonline.com` |
| Debug | `_debug_` | casilla | desactivada | Revela las opciones de mock local siguientes, que existen solo para pruebas |
| Mock Azure API URL | `_mockapiurl_` | cadena | — | URL base del mock local. Solo se muestra cuando **Debug** está habilitado; déjelo vacío en entornos reales |
| Verify mock TLS certificate | `_verifyssl_` | casilla | activada | Solo se muestra cuando **Debug** está habilitado. Desactívelo únicamente para un mock local de confianza |

#### Metrics and module filters

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|-------------|-------|
| Storage account metrics | `_accountmetrics_` | casilla | activada | Capacidad, tráfico, latencia y disponibilidad de la cuenta |
| Blob service metrics | `_blobmetrics_` | casilla | activada | Capacidad, recuentos, tráfico y disponibilidad de Blob |
| File service metrics | `_filemetrics_` | casilla | activada | Capacidad, recuentos, cuota, tráfico y disponibilidad de File |
| File share metrics | `_filesharemetrics_` | casilla | activada | Capacidad usada, cuota y ocupación por recurso compartido. Solo se muestra cuando **File service metrics** está habilitado |
| Queue service metrics | `_queuemetrics_` | casilla | activada | Capacidad, recuentos, tráfico y disponibilidad de Queue |
| Table service metrics | `_tablemetrics_` | casilla | activada | Capacidad, recuentos, tráfico y disponibilidad de Table |
| Advanced container metrics | `_containermetrics_` | casilla | desactivada | Requiere la regla `ContainerLevelCapacityMetrics` en Azure. No crea agentes adicionales |
| Container regexp | `_containerregexp_` | cadena | — | Se aplica únicamente a los nombres de contenedor obtenidos mediante la opción anterior |
| Modules allow regexp | `_moduleallowlist_` | área de texto | — | Una expresión por línea. Solo se conservan los módulos que coincidan con al menos una |
| Modules deny regexp | `_moduledenylist_` | área de texto | — | Una expresión por línea. Los módulos que coincidan se excluyen |

### Claves del fichero de configuración

La tarea de Discovery construye este fichero a partir de sus propios campos; una ejecución manual lo aporta con `--conf`. Las listas de inclusión y exclusión se pasan como rutas de fichero, con una expresión por línea.

| Clave | Descripción | Por defecto |
| --- | --- | --- |
| `credentials` | Credencial de Azure codificada en base64 generada por Pandora FMS | Vacío |
| `tenant_id`, `client_id`, `client_secret`, `subscription_id` | Valores de credencial manuales, usados cuando no se facilita `credentials` | Vacío |
| `group_id` | Identificador de grupo de Pandora FMS asignado a los agentes generados. Debe ser mayor que `0` | Obligatorio |
| `custom_resource_group_enabled` | Habilita el descubrimiento dentro de un Resource Group exacto | `0` |
| `resource_group` | Nombre exacto del Resource Group usado cuando la opción anterior está habilitada | Vacío |
| `storage_account_names` | Nombres exactos de Storage Account separados por `;`. Vacío descubre todas las cuentas | Vacío |
| `create_agent_per_storage_account` | Crea un agente por Storage Account cuando está habilitado | `1` |
| `target_agent` | Agente usado en modo consolidado | `Azure Storage` |
| `agent_prefix` | Prefijo de los agentes creados por Storage Account | `Azure Storage ` |
| `agent_autodisable` | Usa el modo de agente `2` de Pandora FMS cuando está habilitado, y el modo `1` en caso contrario | `0` |
| `interval` | Intervalo de monitorización heredado de la tarea de Discovery | `300` en ejecuciones manuales |
| `standard_account_quota_gib` | Cuota asumida para las cuentas Standard, usada para derivar el porcentaje de ocupación | `5242880` |
| `account_metrics_enabled` | Habilita las métricas de Storage Account | `1` |
| `blob_metrics_enabled` | Habilita las métricas del servicio Blob | `1` |
| `file_metrics_enabled` | Habilita las métricas del servicio File | `1` |
| `file_share_metrics_enabled` | Habilita las métricas por recurso compartido de archivos | `1` |
| `queue_metrics_enabled` | Habilita las métricas del servicio Queue | `1` |
| `table_metrics_enabled` | Habilita las métricas del servicio Table | `1` |
| `container_metrics_enabled` | Habilita las métricas avanzadas por contenedor | `0` |
| `container_regexp` | Expresión regular opcional aplicada a los nombres de contenedor | Vacío |
| `module_allow_list_file` | Fichero con una expresión regular de inclusión de módulos por línea | Vacío |
| `module_deny_list_file` | Fichero con una expresión regular de exclusión de módulos por línea | Vacío |
| `entities_list` | Ruta a la caché de entidades de Storage Account | Vacío en ejecuciones manuales |
| `enable_entities_interval` | Conserva las entidades en caché hasta que expira el intervalo configurado | `1` |
| `entities_interval` | Intervalo de reconstrucción de la caché de entidades en segundos | `86400` |
| `timeout` | Tiempo de espera de las peticiones a Azure en segundos | `30` |
| `management_endpoint` | Endpoint de gestión de Azure para nubes soberanas o personalizadas | `https://management.azure.com` |
| `login_endpoint` | Endpoint de login de Microsoft para nubes soberanas o personalizadas | `https://login.microsoftonline.com` |
| `debug` | Habilita las opciones de mock local siguientes. Solo para pruebas | `0` |
| `mock_api_url` | URL base del mock local. Solo para pruebas | Vacío |
| `verify_ssl` | Verifica el certificado TLS del mock. Desactívelo únicamente para un mock local de confianza | `1` |

Los reintentos de petición están fijados internamente en `3` y no son configurables.

### Ejecución por línea de comandos

El plugin lee un único fichero de configuración. Una ejecución manual reproduce lo que hace el servidor de Discovery en cada ejecución de la tarea.

```bash
./pandora_azure_storage --conf <PATH_TO_CONFIG>
```

| Opción | Descripción |
| --- | --- |
| `--conf`, `-c` | Ruta obligatoria al fichero de configuración |
| `--pretty` | Formatea la salida JSON de forma legible |
| `--version` | Imprime la versión del plugin |
| `--help`, `-h` | Muestra la ayuda del comando |

Fichero de configuración mínimo para una ejecución manual:

```ini
[CONF]
tenant_id=<TENANT_ID>
client_id=<CLIENT_ID>
client_secret=<CLIENT_SECRET>
subscription_id=<SUBSCRIPTION_ID>
group_id=<GROUP_ID>
```

Ese fichero contiene una credencial en texto plano. Restrínjalo a la cuenta que ejecuta el plugin, manténgalo fuera de directorios compartidos y del control de versiones, y prefiera el almacén de credenciales de Pandora FMS para las ejecuciones de tarea, donde la tarea referencia la credencial en lugar de contenerla.

### Módulos generados

Todos los módulos siguientes son `generic_data` salvo que se indique lo contrario, y se crean únicamente cuando está habilitada la opción que los gobierna.

**Siempre creado**

- `Azure Storage Connection`: `generic_proc`, `1` para una cuenta descubierta.

**Storage account metrics**

- `Account Used Capacity`: GiB.
- `Account Capacity Quota`: GiB; solo en cuentas Standard.
- `Account Used Capacity Percentage`: porcentaje; solo en cuentas Standard.
- `Account Transactions_Current`: peticiones.
- `Account Ingress_Current`: bytes.
- `Account Egress_Current`: bytes.
- `Account SuccessServerLatency_Current`: ms.
- `Account SuccessE2ELatency_Current`: ms.
- `Account Availability_Current`: porcentaje.
- `Data Lake Storage Gen2 Enabled`: `generic_proc`; se crea cuando la cuenta tiene espacio de nombres jerárquico.

**Blob service metrics**

- `Blob Used Capacity`: GiB.
- `Blob Object Count`.
- `Blob Container Count`.
- `Blob Index Capacity`: GiB.
- `Blob Transactions_Current`: peticiones.
- `Blob Ingress_Current`: bytes.
- `Blob Egress_Current`: bytes.
- `Blob SuccessServerLatency_Current`: ms.
- `Blob SuccessE2ELatency_Current`: ms.
- `Blob Availability_Current`: porcentaje.

**File service metrics**

- `File Used Capacity`: GiB.
- `File Object Count`.
- `File Share Count`.
- `File Snapshot Count`.
- `File Snapshot Size`: GiB.
- `File Capacity Quota`: GiB.
- `File Transactions_Current`: peticiones.
- `File Ingress_Current`: bytes.
- `File Egress_Current`: bytes.
- `File SuccessServerLatency_Current`: ms.
- `File SuccessE2ELatency_Current`: ms.
- `File Availability_Current`: porcentaje.

**File share metrics**

- `File Share <nombre> Used Capacity`: GiB.
- `File Share <nombre> Capacity Quota`: GiB.
- `File Share <nombre> Used Capacity Percentage`: porcentaje.

**Queue service metrics**

- `Queue Used Capacity`: GiB.
- `Queue Count`.
- `Queue Message Count`.
- `Queue Transactions_Current`: peticiones.
- `Queue Ingress_Current`: bytes.
- `Queue Egress_Current`: bytes.
- `Queue SuccessServerLatency_Current`: ms.
- `Queue SuccessE2ELatency_Current`: ms.
- `Queue Availability_Current`: porcentaje.

**Table service metrics**

- `Table Used Capacity`: GiB.
- `Table Count`.
- `Table Entity Count`.
- `Table Transactions_Current`: peticiones.
- `Table Ingress_Current`: bytes.
- `Table Egress_Current`: bytes.
- `Table SuccessServerLatency_Current`: ms.
- `Table SuccessE2ELatency_Current`: ms.
- `Table Availability_Current`: porcentaje.

**Advanced container metrics**

- `Blob Container Metrics Enabled`: `generic_proc`, `1` cuando la regla de Azure está habilitada y `0` cuando no lo está.
- `Container <nombre> Used Capacity`: GiB.
- `Container <nombre> Blob Count`.
- `Container <nombre> Blob Capacity Percentage`: porcentaje; se crea cuando **Blob service metrics** también está habilitado y Azure devuelve `BlobCapacity`.

### Identidad del plugin

| Campo | Valor |
|-------|-------|
| Nombre corto de la aplicación | `pandorafms.azure_storage` |
| Versión del plugin | `1.0` |
| Tipo | Aplicación de Discovery (`.disco`) |
| Sección | Discovery → Cloud |
