# Digital Ocean Discovery

*Última actualización del artículo: 2026-10-26.*

## Qué monitoriza

El addon de Discovery de Digital Ocean monitoriza los droplets de una cuenta de DigitalOcean. Consulta la API de DigitalOcean con un token de API y convierte el resultado en agentes y módulos de Pandora FMS: estado del droplet, CPU, memoria, carga y tráfico de red, uso de los sistemas de ficheros, la fecha del último backup, la fecha de cada snapshot y el saldo de la cuenta.

Una tarea de Discovery genera dos tipos de agentes:

- **Un agente global** de la cuenta, con el número de droplets y las cifras de saldo y consumo de la cuenta.
- **Un agente por cada droplet monitorizado**, con su estado y sus módulos de rendimiento y de backup.

Por defecto se monitoriza cada droplet que devuelve la API. Puede limitar la tarea a los droplets de un proyecto de DigitalOcean y descartar droplets concretos por nombre.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
|--------|--------|-----------|
| Addon `pandorafms.digitalocean`, versión `1.0` | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del addon](#identidad-del-addon) |
| Acceso de red desde el servidor de Discovery a `api.digitalocean.com` | `Required` | El addon llama a la API de DigitalOcean por HTTPS |
| Token de API de DigitalOcean | `Required` | Consulte [Crear el token de API](#crear-el-token-de-api) |
| Sistema operativo del servidor de Discovery | `Not validated` | No se ha registrado ningún sistema operativo para esta versión |
| Versiones concretas de Pandora FMS | `Not validated` | No se ha registrado ninguna matriz de versiones para este addon |

### Prerrequisitos

1. **Conectividad** desde el servidor de Discovery a la API de DigitalOcean.
2. **Un token de API de DigitalOcean** con acceso de lectura, descrito a continuación.
3. **Monitorización de droplets activada** en DigitalOcean en cada droplet del que necesite los módulos de CPU, memoria, carga y tráfico. Los droplets sin ella generan igualmente un agente, con los módulos `Status`, de backup, de snapshot y de sistemas de ficheros, pero sin los módulos de CPU, memoria, carga y tráfico.
4. **Pandora FMS**: un servidor de Discovery para ejecutar la tarea y la consola para definirla.

El addon incluye su propio ejecutable, `bin/pandora_digitalocean`, por lo que no hay que instalar nada más en el servidor de Discovery para ejecutar una tarea.

### Crear el token de API

El addon envía únicamente peticiones de lectura (`GET`) a la API de DigitalOcean. Cree un token de acceso personal en el panel de control de DigitalOcean (sección **API**) y péguelo en la tarea. El token debe permitir al addon leer:

| Datos | Uso |
|-------|-----|
| Droplets | Listar los droplets y su estado, características y redes (siempre) |
| Métricas de droplets | Módulos de CPU, memoria, carga, ancho de banda y sistemas de ficheros |
| Backups y snapshots de droplets | Módulos de backup y de snapshot |
| Saldo de la cuenta | Módulos del agente global (siempre) |
| Proyectos y recursos de proyecto | Solo con **Filter project** activado |

DigitalOcean muestra el token una única vez al crearlo; guárdelo en un lugar seguro. DigitalOcean permite crear uno nuevo en cualquier momento.

El token se almacena en la definición de la tarea y se escribe, en texto claro, en el fichero de configuración temporal que el servidor de Discovery usa para ejecutar el addon. Restrinja el acceso a los usuarios de la consola de Pandora FMS que pueden editar tareas de Discovery y utilice preferiblemente un token creado solo para Pandora FMS.

### Instalar el addon

Descargue el paquete `.disco` de la entrada del Marketplace de Pandora FMS:

[https://marketplace.pandorafms.com/entries/pandorafms.digitalocean](https://marketplace.pandorafms.com/entries/pandorafms.digitalocean)

Cárguelo en Pandora FMS.

<!-- SCREENSHOT NEEDED: pantalla Load DISCO de Discovery con el addon Digital Ocean listado tras cargarlo, mostrando su sección. -->

Una vez cargado, **Digital Ocean** está disponible en la sección **Cloud** al crear tareas de Discovery.

## Configurar la tarea de Discovery

Cree la tarea desde las aplicaciones cloud de Discovery y elija **Digital Ocean**. La consola presenta todos los campos en un único paso, **Digital Ocean base**; cada campo está documentado en [Parámetros de la tarea](#parametros-de-la-tarea).

- **Digital Ocean token**: el token de API.
- **Use prefix** y **Prefix**: texto que se antepone al nombre y al alias de cada agente generado. **Prefix** se muestra con **Use prefix** activado.
- **Filter project** y **Project**: monitoriza solo los droplets del proyecto de DigitalOcean con ese nombre. **Project** se muestra con **Filter project** activado.
- **Discard droplets** y **Select the droplets to be discarded**: omite droplets concretos por nombre. La lista es un array JSON de nombres de droplet, por ejemplo `["ubuntu-s-1vcpu-1gb-sfo3-01","ubuntu-s-1vcpu-4gb-sfo3-03"]`. Se muestra con **Discard droplets** activado.
- **Max threads**: número de grupos en los que se dividen los droplets.
- **Tentacle IP** y **Tentacle port**: dónde se envían los datos de los agentes generados. Rara vez necesitan cambiarse.

![Asistente de la tarea Digital Ocean con el token, el prefijo, el filtro de proyecto, el descarte de droplets, Max threads y los campos de Tentacle](../assets/images/discovery/digital-ocean/digital-ocean-task-wizard.png)

La imagen muestra el asistente con **Use prefix** activado; **Project** y la lista de descarte aparecen al activar **Filter project** y **Discard droplets**.

El grupo y el intervalo de la tarea proceden del paso genérico de definición de la tarea y se aplican a los agentes que crea.

## Verificar la primera ejecución

Fuerce la ejecución de la tarea desde la lista de tareas de Discovery y compruebe el resultado en este orden.

1. **El resumen de la tarea.** Una tarea que finaliza correctamente informa de **Total agents**: el agente global más un agente por cada droplet monitorizado. Una tarea que no finaliza correctamente registra los errores en su información de ejecución.

    ![Resumen de la tarea de Discovery con Total agents](../assets/images/discovery/digital-ocean/digital-ocean-task-summary.png)

2. **Los agentes.** Un agente global, cuyo alias es `Digital Ocean` (con el prefijo, si se definió), y un agente por droplet, con el nombre del droplet como alias.

3. **Los módulos.** Cada agente de droplet tiene un módulo `Status`. Los módulos de rendimiento aparecen solo en droplets con la monitorización activada; consulte [Interpretar los resultados](#interpretar-los-resultados).

## Interpretar los resultados

### Agentes generados

| Agente | Alias | Notas |
|--------|-------|-------|
| Agente global | `<prefix>Digital Ocean` | Uno por tarea. Descripción `DigitalOcean global agent` |
| Agente de droplet | `<prefix><droplet name>` | Uno por droplet monitorizado. Descripción `DigitalOcean Droplet`. Su dirección es la segunda entrada de red IPv4 que DigitalOcean informa para el droplet |

La identidad del agente se deriva del prefijo y del nombre, no de la tarea ni del ID del droplet. La misma tarea u otra que produzca el mismo prefijo y nombre reporta al mismo agente y conserva su historial. Renombrar un droplet en DigitalOcean o cambiar el prefijo crea agentes nuevos. Dos droplets con el mismo nombre comparten un agente.

### Módulos por agente

**Agente global**

| Módulo | Tipo | Descripción |
|--------|------|-------------|
| `Droplets` | `generic_data` | Número de droplets que DigitalOcean informa para la cuenta |
| `Month to data balance` | `generic_data` | Cargos incurridos en el mes en curso (`month_to_date_balance`) |
| `Account balance` | `generic_data` | Fondos totales disponibles en la cuenta |
| `Month to date usage` | `generic_data` | Consumo de servicios del mes en curso |

**Agente de droplet**

| Módulo | Tipo | Condición | Descripción |
|--------|------|-----------|-------------|
| `Status` | `generic_proc` | Siempre | `1` cuando el estado del droplet es `active`, `0` en caso contrario |
| `Cpu %` | `generic_data` | Monitorización del droplet activada | CPU utilizada, en `%` |
| `Mem %` | `generic_data` | Monitorización del droplet activada | Memoria utilizada, en `%` |
| `Load 1`, `Load 5`, `Load 15` | `generic_data` | Monitorización del droplet activada | Carga media del sistema en el último minuto, los últimos cinco y los últimos quince minutos |
| `Public inbound`, `Public outbound` | `generic_data` | Monitorización del droplet activada | Tráfico entrante y saliente de la interfaz pública |
| `Private inbound`, `Private outbound` | `generic_data` | Monitorización del droplet activada | Tráfico entrante y saliente de la interfaz privada |
| `<backup name>` | `generic_data` | El droplet tiene backups | Fecha de creación del último backup. Unidad `_timeticks_` |
| `<snapshot name>` | `generic_data` | El droplet tiene snapshots | Un módulo por snapshot con su fecha de creación. Unidad `_timeticks_` |
| `<device>` | `generic_data` | DigitalOcean devuelve métricas de sistemas de ficheros del droplet | Un módulo por dispositivo de sistema de ficheros con su uso, en `%` |

Los módulos de backup, snapshot y sistema de ficheros toman su nombre del backup, del snapshot y del dispositivo. Un snapshot nuevo o un último backup distinto crea, por tanto, un módulo nuevo.

### Cómo se obtienen los valores

- El addon lee en cada ejecución las métricas de monitorización de DigitalOcean de la última hora.
- `Cpu %` es 100 menos la proporción de tiempo de CPU en reposo (`idle`) de la media horaria por modo.
- `Mem %` se calcula a partir de las muestras más recientes de memoria total y disponible de esa hora.
- Los valores de carga, ancho de banda y sistemas de ficheros son la media de las muestras de esa hora. El addon no convierte los valores de ancho de banda: se muestran tal como los devuelve la API de monitorización de DigitalOcean.
- Los valores de backup y snapshot son la fecha de creación expresada en timeticks, que la consola muestra como tiempo transcurrido.

## Operación

### Ejecución manual

El addon puede ejecutarse fuera de una tarea de Discovery. El ejecutable recibe un único parámetro, la ruta de un fichero de configuración descrito en [Fichero de configuración](#fichero-de-configuracion):

```bash
./pandora_digitalocean --conf <PATH_TO_CONFIG>
```

Envía un fichero de datos por agente e imprime un resumen JSON:

```json
{"summary": {"Total agents": 12}}
```

Cuando se producen errores, el JSON contiene además una clave `info` con los mensajes y el código de salida es `1`. El fichero de configuración contiene el token de API en texto claro; protéjalo con permisos restrictivos.

## Solución de problemas

El addon no tiene opción de verbose ni de depuración. Su canal de diagnóstico es el campo `info` del resultado JSON de la ejecución, que se muestra en la información de ejecución de la tarea.

- **La tarea falla y no se genera ningún agente**: el token falta, no es válido o ha caducado, o el servidor de Discovery no alcanza `api.digitalocean.com`.
- **La tarea falla tras listar los droplets y no aparece ningún agente de droplet**: el agente global lee el saldo de la cuenta antes de crear ningún agente de droplet. Compruebe que el token puede leer el saldo de la cuenta.
- **`Error extracting information from droplets`**: con **Filter project** activado, no se encontró el nombre del proyecto. La coincidencia es exacta y distingue mayúsculas de minúsculas; compruebe la ortografía con el proyecto en DigitalOcean.
- **`Error while parsing configuration zones or instances`**: la lista de descarte no es un array JSON válido. Use comillas dobles, por ejemplo `["<DROPLET_NAME>"]`. Mientras la lista no sea válida, no se descarta ningún droplet.
- **Un droplet se sigue monitorizando tras descartarlo**: el nombre debe coincidir exactamente con el del droplet, incluidas las mayúsculas.
- **Agentes de droplet sin los módulos `Cpu %`, `Mem %`, carga y tráfico**: la monitorización no está activada en ese droplet en DigitalOcean.
- **`Error while running threads`**: no había droplets que monitorizar tras aplicar el filtro de proyecto y la lista de descarte.
- **Agentes que dejan de actualizarse tras renombrar**: la identidad del agente depende del nombre del droplet y del prefijo; consulte [Agentes generados](#agentes-generados).

## Referencia

### Parámetros de la tarea

#### Digital Ocean base

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|-------------|-------|
| Digital Ocean token | `_token_` | área de texto | vacío | Token bearer usado para autenticarse en la API. El asistente no lo marca como obligatorio, pero la tarea no puede leer ningún dato sin él |
| Use prefix | `_usePrefix_` | casilla | desactivada | Muestra **Prefix** |
| Prefix | `_prefix_` | cadena | vacío | Opcional. Se antepone al nombre y al alias de cada agente. Se muestra con **Use prefix** activado |
| Filter project | `_filterProject_` | casilla | desactivada | Muestra **Project** |
| Project | `_project_` | cadena | vacío | Opcional. Nombre exacto, sensible a mayúsculas, del proyecto de DigitalOcean cuyos droplets se monitorizan. Se muestra con **Filter project** activado |
| Discard droplets | `_discardActivate_` | casilla | desactivada | Muestra la lista de descarte |
| Select the droplets to be discarded | `_discardDroplets_` | área de texto | `[]` | Opcional. Array JSON de nombres exactos de droplet. Se muestra con **Discard droplets** activado |
| Max threads | `_threads_` | número | `1` | Opcional. Número de grupos en los que se dividen los droplets, nunca más grupos que droplets |
| Tentacle IP | `_tentacleIP_` | cadena | `127.0.0.1` | Servidor que recibe los datos de los agentes |
| Tentacle port | `_tentaclePort_` | número | `41121` | Puerto de Tentacle |

La tarea de Discovery envía siempre los datos con Tentacle.

### Fichero de configuración

Lo usa la ejecución manual. Un `clave = valor` por línea. Los valores de lista son arrays JSON. Un valor numérico que no es un número se lee como `0`.

| Clave | Por defecto | Descripción |
|-------|-------------|-------------|
| `token` | vacío | Token de API. Obligatorio en la práctica |
| `agents_group_name` | vacío | Grupo de los agentes generados |
| `interval` | `300` | Intervalo del agente, en segundos |
| `use_prefix` | vacío | Indicador de prefijo escrito por la tarea de Discovery. El prefijo se aplica cuando `prefix` no está vacío |
| `prefix` | vacío | Prefijo de los nombres y alias de los agentes |
| `applicate_project` | vacío | Indicador de filtro de proyecto escrito por la tarea de Discovery. El filtro se aplica cuando `filter_project` no está vacío |
| `filter_project` | vacío | Nombre del proyecto |
| `discard_activate` | vacío | Indicador de descarte escrito por la tarea de Discovery. Se descartan los droplets indicados en `discard_droplets` |
| `discard_droplets` | `[]` | Array JSON de nombres de droplet que se descartan |
| `threads` | `1` | Número de grupos en los que se distribuyen los droplets |
| `transfer_mode` | vacío | La tarea de Discovery establece `tentacle` |
| `data_dir` | vacío | Directorio de datos, leído por el addon |
| `tentacle_ip` | vacío | Dirección del servidor Tentacle |
| `tentacle_port` | `41121` | Puerto del servidor Tentacle |

Ejemplo:

```ini
agents_group_name = <AGENT_GROUP>
interval          = 300
transfer_mode     = tentacle
token             = <DIGITALOCEAN_API_TOKEN>
prefix            = do-
applicate_project = 1
filter_project    = <PROJECT_NAME>
discard_droplets  = ["<DROPLET_NAME>"]
threads           = 1
tentacle_ip       = <TENTACLE_SERVER_IP>
tentacle_port     = 41121
```

### Identidad del addon

| Elemento | Valor |
|----------|-------|
| Nombre | Digital Ocean |
| Identificador | `pandorafms.digitalocean` |
| Versión | `1.0` |
| Tipo y sección | Discovery, `cloud` |
| Entrada del Marketplace | [pandorafms.digitalocean](https://marketplace.pandorafms.com/entries/pandorafms.digitalocean), actualizada el 2025-06-01 |
| Disponibilidad | La entrada del Marketplace marca la descarga como gratuita |
