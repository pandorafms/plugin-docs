# Discovery de Azure backup

*Última actualización del artículo: 2026-10-26.*

## Qué monitoriza

El addon de Discovery de Azure backup monitoriza el estado de las copias de seguridad que Azure Backup mantiene para los recursos protegidos de una suscripción de Azure. Lee todos los almacenes de Recovery Services de la suscripción y, para cada elemento protegido, informa del tiempo transcurrido desde la última copia, el número de puntos de recuperación y los estados de protección, de la última copia y de salud. Permite detectar copias fallidas o antiguas y protecciones en pausa, detenidas o con error.

El addon crea agentes y módulos de Pandora FMS a partir de esos datos. Una tarea de Discovery genera:

- **Un agente** (por defecto) que contiene los módulos de todos los elementos protegidos.
- **Un agente por elemento protegido**, cuando se activa **Agent per item**.

Cada elemento protegido tiene seis módulos, descritos en [Comprender los resultados](#comprender-los-resultados). Una tarea cubre una única suscripción de Azure, la de la credencial que utiliza.

## Preparación

### Compatibilidad

| Alcance | Estado | Evidencia |
|---------|--------|-----------|
| Addon `pandorafms.azure.backup`, versión `1.0` | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del addon](#identidad-del-addon) |
| Acceso de red desde el servidor de Discovery a las API de Azure | `Requerido` | El addon consulta las API de Azure Recovery Services y Backup |
| Aplicación de Azure con acceso de lectura a los almacenes de copias de la suscripción | `Requerido` | Consulte [Credenciales de Azure](#credenciales-de-azure) |
| Sistema operativo del servidor de Discovery | `Sin validar` | No se ha registrado ningún sistema operativo para esta versión |
| Versiones concretas de Pandora FMS | `Sin validar` | No se ha registrado una matriz de versiones para este addon |

### Prerrequisitos

1. **Conectividad** desde el servidor de Discovery a las API de Azure, de forma directa o a través de un proxy.
2. **Una credencial de Azure** registrada en el almacén de credenciales de Pandora FMS, creada a partir de un registro de aplicación de Azure como se describe a continuación.
3. **Pandora FMS**: un servidor de Discovery para ejecutar la tarea y la consola para definirla.

El addon incluye su propio ejecutable, `bin/pandora_azure_backup`, por lo que no hay que instalar nada más en el servidor de Discovery para ejecutar una tarea.

### Credenciales de Azure

La credencial almacenada en Pandora FMS debe proporcionar estos cuatro valores:

| Clave | Qué introducir |
|-------|----------------|
| `subscription_id` | El ID de la suscripción cuyas copias de seguridad se quieren monitorizar. Aparece en la vista general de la suscripción del portal de Azure |
| `tenant_domain` | El ID del inquilino (directorio) de Microsoft Entra ID, que aparece en la vista general de Entra ID |
| `client_id` | El ID de aplicación (cliente) de un registro de aplicación |
| `application_secret` | Un secreto de cliente creado para ese registro de aplicación |

Cree el registro de aplicación en el portal de Azure siguiendo la documentación de Microsoft y genere un secreto de cliente para él. El addon se autentica con el ID de cliente y el secreto; si falta cualquiera de las cuatro claves, la tarea falla con `Error while parsing credentials`.

### Permisos en Azure

El addon realiza únicamente peticiones de lectura: lista los almacenes de la suscripción, los elementos protegidos de cada almacén y los puntos de recuperación de cada elemento. Por tanto, la aplicación necesita acceso de lectura a esos recursos. La guía anterior de este addon asignaba a la aplicación el rol integrado **Reader** en el ámbito de la suscripción, desde **Access control (IAM)** > **Add role assignment** y seleccionando la aplicación como miembro de tipo entidad de servicio. Esta página no establece ese rol como el mínimo necesario.

### Instalar el addon

Descargue el paquete `.disco` desde la entrada del Marketplace de Pandora FMS:

[https://marketplace.pandorafms.com/entries/pandorafms.azure.backup](https://marketplace.pandorafms.com/entries/pandorafms.azure.backup)

Cárguelo en Pandora FMS. Una vez cargado, **Azure backup** está disponible en la sección **Cloud** al crear tareas de Discovery.

## Configurar la tarea de Discovery

Cree la tarea desde las aplicaciones cloud de Discovery y elija **Azure backup**. La consola presenta los campos en dos pasos; todos los campos se documentan en [Parámetros de la tarea](#parametros-de-la-tarea).

1. **Azure Backup base** — credenciales, proxy y transferencia de datos:

    - **Azure credentials**: la credencial de Azure registrada en el almacén de credenciales.
    - **Use proxy** y **Proxy url**: enrutan las peticiones a Azure a través de un proxy. **Proxy url** es obligatoria cuando **Use proxy** está activado.
    - **Verify proxy SSL**: se muestra cuando **Use proxy** está activado.
    - **Tentacle IP**, **Tentacle port** y **Tentacle extra options**: dónde y cómo se envían los datos de los agentes generados. Rara vez hay que cambiarlos.

    ![Tarea de Azure backup, paso base](../assets/images/discovery/azure-backup/azure-backup-task-basic.png)

2. **Azure Backup Detailed** — organización de agentes y filtros:

    - **Agent name**: nombre del agente que contiene los módulos cuando **Agent per item** está desactivado.
    - **Use prefix for modules** y **Prefix for modules created**, **Use prefix for agents** y **Prefix for agents created**: anteponen un texto al nombre de cada módulo o agente.
    - **Regexp to filter modules** con **Allow regexp**, y **Regexp to discard modules** con **Deny regexp**: limitan qué elementos protegidos se monitorizan.
    - **Agent per item**: crea un agente por elemento protegido.
    - **Debug mode**.

    ![Tarea de Azure backup, paso detallado](../assets/images/discovery/azure-backup/azure-backup-task-detailed.png)

El grupo y el intervalo de la tarea proceden del paso genérico de definición de la tarea. El grupo se aplica a los agentes que crea la tarea.

## Verificar la primera ejecución

Fuerce la tarea desde la lista de tareas de Discovery y compruebe el resultado en este orden.

1. **El resumen de la tarea.** Una tarea que finaliza correctamente informa de `total_agents`, el número de agentes generados. Una tarea que no finaliza correctamente registra los errores en su información de ejecución.

    <!-- SCREENSHOT NEEDED: Resumen de ejecución de la tarea de Discovery de Azure backup con Total agents. -->

2. **Los agentes.** Un agente con el nombre de **Agent name** (por defecto `Azure Backups`), o uno por elemento protegido cuando **Agent per item** está activado.

3. **Los módulos.** Seis módulos por elemento protegido, llamados `<nombre del elemento> Last backup`, `<nombre del elemento> Recovery points`, etc.

    <!-- SCREENSHOT NEEDED: Agente generado por una tarea de Azure backup con los seis módulos de un elemento protegido, solo con identificadores de laboratorio. -->

Si no se crea ningún agente y `total_agents` es `0`, la suscripción no tiene elementos protegidos o los filtros los han excluido todos.

## Comprender los resultados

### Agentes generados

| Modo | Nombre del agente | Notas |
|------|-------------------|-------|
| **Agent per item** desactivado | **Agent name** (por defecto `Azure Backups`) con **Prefix for agents created** antepuesto | Un agente con los módulos de todos los elementos protegidos |
| **Agent per item** activado | El nombre del elemento protegido con **Prefix for agents created** antepuesto | Un agente por elemento protegido. Los elementos con el mismo nombre en distintos almacenes reportan al mismo agente |

El nombre del elemento protegido es el que Azure Backup asigna al elemento, con cada `;` sustituido por `_`. Los agentes se crean en el grupo de la tarea, con intervalo de 300 segundos y la descripción `Created by plugin Azure Backups`. Los agentes se identifican por nombre, por lo que renombrar el agente o cambiar un prefijo crea agentes nuevos.

### Módulos por elemento protegido

El nombre de cada módulo es **Prefix for modules created**, seguido del nombre del elemento y del sufijo siguiente.

| Sufijo del módulo | Tipo | Valor | Descripción |
|-------------------|------|-------|-------------|
| `Last backup` | `generic_data_string` | Tiempo transcurrido desde la última copia, en centésimas de segundo (unidad `_timeticks_`). `0` cuando Azure no informa de la fecha de la última copia | La descripción contiene el nombre del almacén y la fecha de la última copia |
| `Recovery points` | `generic_data` | Número de puntos de recuperación del elemento. `0` cuando no se pueden listar | |
| `Protection state` | `generic_data` | Código numérico, ver más abajo | La descripción contiene el estado de protección y el estado de salud |
| `Last backup status` | `generic_data` | Código numérico, ver más abajo | La descripción contiene el estado que informa Azure |
| `Health status` | `generic_data` | Código numérico, ver más abajo | La descripción contiene el estado que informa Azure |
| `Protection status` | `generic_data` | Código numérico, ver más abajo | La descripción contiene el estado que informa Azure |

#### Códigos numéricos

Un valor que Azure no informa, o que no figura en las tablas siguientes, es `0`.

| `Protection state` | Código |
|--------------------|--------|
| `Protected` | `1` |
| `IRPending` | `2` |
| `Invalid` | `3` |
| `BackupsSuspended` | `4` |
| `ProtectionPaused` | `5` |
| `ProtectionStopped` | `6` |
| `ProtectionError` | `7` |

| `Last backup status` | Código |
|----------------------|--------|
| `Failed` | `0` |
| `Completed`, `Healthy` | `1` |
| `IRPending` | `2` |
| `Invalid` | `3` |
| `Unhealthy` | `4` |

| `Health status` | Código |
|-----------------|--------|
| `Passed` | `1` |
| `ActionSuggested` | `2` |
| `ActionRequired` | `3` |
| `Invalid` | `4` |

| `Protection status` | Código |
|---------------------|--------|
| `Healthy` | `1` |
| `Unhealthy` | `2` |

`Failed` y un estado de última copia no informado producen ambos `0`; use la descripción del módulo para distinguirlos.

### Cómo funcionan los filtros

**Allow regexp** y **Deny regexp** se evalúan contra el nombre del elemento protegido, después de sustituir `;` y antes de aplicar ningún prefijo. Seleccionan elementos, no módulos individuales: los seis módulos de un elemento se crean todos o se omiten todos. El filtro de permitidos se aplica primero, y un elemento que coincide con el filtro de denegados se omite aunque coincida con el de permitidos. Ambos usan búsqueda, por lo que un patrón coincide en cualquier parte del nombre.

## Operar

### Ejecución manual

El addon puede ejecutarse fuera de una tarea de Discovery. El ejecutable recibe un único parámetro, la ruta a un archivo de configuración descrito en [Archivo de configuración](#archivo-de-configuracion):

```bash
./pandora_azure_backup --conf <PATH_TO_CONFIG>
```

Imprime un resultado JSON con el número de agentes generados y envía un archivo de datos por agente mediante Tentacle. Cuando se producen errores, el JSON contiene además la clave `info` con los mensajes y el código de salida es `1`.

El archivo de configuración contiene la credencial de Azure codificada en `creds_b64`. Protéjalo con permisos restrictivos.

### Limitaciones conocidas en esta versión

- **Verify proxy SSL** y **Debug mode** no cambian el comportamiento de una tarea. El valor SSL se lee pero no se utiliza, y el asistente no activa el modo debug del addon. Los mensajes de depuración solo están disponibles mediante ejecución manual con `debug_mode = 1`.
- **Tentacle extra options** se aceptan pero no se pasan al cliente de Tentacle al enviar los datos de los agentes.
- Los agentes generados usan siempre un intervalo de 300 segundos, sea cual sea el intervalo de la tarea.

## Solución de problemas

El canal de diagnóstico es el campo `info` del resultado JSON de la ejecución, que se muestra en la información de ejecución de la tarea.

- **`Error while parsing credentials`**: la credencial no proporciona `client_id`, `application_secret`, `tenant_domain` y `subscription_id`, o `creds_b64` no es JSON válido codificado en base64.
- **`[ERROR] The proxy URL needs to be specified.`**: **Use proxy** está activado y **Proxy url** está vacía.
- **`Error creating clients`**: no se pudo crear el cliente de Azure a partir de la credencial. El mensaje incluye el detalle.
- **`[Error]: ...`**: falló una petición a Azure al listar almacenes o elementos protegidos, por ejemplo porque la aplicación no tiene acceso de lectura a la suscripción o porque un patrón allow/deny no es una expresión regular válida. El mensaje incluye el error devuelto.
- **`total_agents` es `0`**: no hay elementos protegidos en la suscripción, o los filtros allow y deny los excluyeron todos.
- **`Recovery points` es `0`**: el elemento no tiene puntos de recuperación, o no se pudieron listar. En el segundo caso el addon no informa de ningún error.
- **Falta un elemento en un agente en modo `Agent per item`**: un fallo al construir los módulos de un elemento se omite en silencio salvo que `debug_mode` esté activado en la ejecución manual.

## Referencia

### Parámetros de la tarea

#### Azure Backup base

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|-------------|-------|
| Azure credentials | `_credentials_` | selector de credencial (Azure) | — | Obligatorio. Credencial registrada en el almacén de credenciales |
| Use proxy | `_useProxy_` | casilla | desactivado | Enruta las peticiones a Azure a través de un proxy |
| Proxy url | `_proxyUrl_` | cadena | — | Campo opcional. Se muestra con **Use proxy**; la tarea falla si está vacío con el proxy activado |
| Verify proxy SSL | `_sslCheck_` | casilla | desactivado | Se muestra con **Use proxy**. Sin efecto en esta versión |
| Tentacle IP | `_tentacleIP_` | cadena | `127.0.0.1` | Servidor que recibe los datos de los agentes |
| Tentacle port | `_tentaclePort_` | número | `41121` | Puerto de Tentacle |
| Tentacle extra options | `_tentacleExtraOpt_` | cadena | — | Opcional. Consulte [Limitaciones conocidas](#limitaciones-conocidas-en-esta-version) |

#### Azure Backup Detailed

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|-------------|-------|
| Agent name | `_agentName_` | cadena | `Azure Backups` | Solo se usa con **Agent per item** desactivado |
| Use prefix for modules | `_usePrefixModules_` | casilla | desactivado | |
| Prefix for modules created | `_prefixModules_` | cadena | — | Se muestra con **Use prefix for modules** |
| Use prefix for agents | `_usePrefixAgents_` | casilla | desactivado | |
| Prefix for agents created | `_prefixAgents_` | cadena | — | Se muestra con **Use prefix for agents** |
| Regexp to filter modules | `_regexpFilter_` | casilla | desactivado | |
| Allow regexp | `_allowRegexp_` | cadena | — | Se muestra con **Regexp to filter modules**. Solo se monitorizan los elementos protegidos cuyo nombre coincide |
| Regexp to discard modules | `_regexpDiscard_` | casilla | desactivado | |
| Deny regexp | `_denyRegexp_` | cadena | — | Se muestra con **Regexp to discard modules**. No se monitorizan los elementos protegidos cuyo nombre coincide |
| Agent per item | `_agentPerVm_` | casilla | desactivado | Un agente por elemento protegido |
| Debug mode | `_sslCheck_` | casilla | desactivado | Sin efecto en esta versión |

### Archivo de configuración

Se usa en la ejecución manual. Un `clave = valor` por línea. Las opciones numéricas aceptan `1` para activar y `0` para desactivar; un valor que no sea un número se lee como `0`.

| Clave | Por defecto | Descripción |
|-------|-------------|-------------|
| `agents_group_name` | vacío | Grupo de los agentes generados |
| `agent_name` | `Azure Backups` | Agente que contiene los módulos cuando `agent_per_vm` es `0` |
| `agent_prefix` | vacío | Prefijo de los nombres de agente |
| `module_prefix` | vacío | Prefijo de los nombres de módulo |
| `transfer_mode` | `tentacle` | Modo de transferencia de los datos generados |
| `tentacle_ip` | `127.0.0.1` | Dirección del servidor de Tentacle |
| `tentacle_port` | `41121` | Puerto del servidor de Tentacle |
| `tentacle_opts` | vacío | Se acepta, pero no se pasa al cliente de Tentacle en esta versión |
| `use_proxy` | `0` | Usar un proxy |
| `proxy_url` | vacío | URL del proxy. Obligatoria cuando `use_proxy` es `1` |
| `agent_per_vm` | `0` | Un agente por elemento protegido |
| `debug_mode` | `0` | Añade a la salida `info` mensajes sobre los elementos cuyo agente o módulos no se pudieron crear |
| `allow_regexp` | vacío | Filtro de permitidos |
| `deny_regexp` | vacío | Filtro de denegados |
| `creds_b64` | vacío | Obligatorio. Base64 del JSON `{"client_id": "<CLIENT_ID>", "application_secret": "<CLIENT_SECRET>", "tenant_domain": "<TENANT_ID>", "subscription_id": "<SUBSCRIPTION_ID>"}` |

Ejemplo:

```ini
agents_group_name = <AGENT_GROUP>
agent_name        = Azure Backups
transfer_mode     = tentacle
tentacle_ip       = <TENTACLE_SERVER_IP>
tentacle_port     = 41121
use_proxy         = 0
agent_per_vm      = 0
debug_mode        = 1
allow_regexp      =
deny_regexp       =
creds_b64         = <BASE64_CREDENTIALS>
```

### Identidad del addon

| Elemento | Valor |
|----------|-------|
| Nombre | Azure backup |
| Identificador | `pandorafms.azure.backup` |
| Versión | `1.0` |
| Tipo y sección | Discovery, `cloud` |
| Entrada del Marketplace | [pandorafms.azure.backup](https://marketplace.pandorafms.com/entries/pandorafms.azure.backup), actualizada el 2026-04-08 |
| Disponibilidad | La entrada del Marketplace no indica restricciones de licencia |
