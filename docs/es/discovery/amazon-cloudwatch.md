# Amazon CloudWatch Discovery

*Última actualización del artículo: 2026-10-26.*

## Qué monitoriza

El addon de Discovery de Amazon CloudWatch convierte el resultado de consultas de Amazon CloudWatch en agentes y módulos de Pandora FMS. Usted define las consultas, con CloudWatch Metrics Insights o cualquier otra expresión `MetricDataQueries`, y define cómo se convierte cada resultado en un módulo. Una sola consulta puede producir cientos de módulos, por ejemplo un módulo de CPU por cada instancia EC2 que devuelva.

Una tarea de Discovery:

1. Lee las consultas que usted ha escrito, cada una con su región y su ventana de tiempo.
2. Las ejecuta contra la API de CloudWatch con una clave de acceso de AWS.
3. Crea un módulo por cada serie de resultados y lo coloca en el agente por defecto o en el agente que indique en la configuración del módulo.

Los agentes y módulos que aparecen dependen por completo de su configuración; el addon no crea ningún recurso por sí mismo.

## Preparación

### Compatibilidad

| Alcance | Estado | Evidencia |
|---------|--------|-----------|
| Addon `pandorafms.aws.cloudwatch`, versión de paquete `1.0` | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del addon](#identidad-del-addon) |
| Acceso de red desde el servidor de Discovery a la API de AWS CloudWatch | `Requerido` | El addon llama a la API de CloudWatch en cada región usada por sus consultas |
| Clave de acceso de AWS con el permiso de [Permisos de AWS](#permisos-de-aws) | `Requerido` | Prerrequisito, no una declaración de compatibilidad |
| Sistema operativo del servidor de Discovery | `Sin validar` | No se ha registrado ningún sistema operativo para esta versión |
| Versiones concretas de Pandora FMS | `Sin validar` | No se ha registrado una matriz de versiones para este addon |

### Prerrequisitos

1. **Conectividad** desde el servidor de Discovery a la API de AWS, de forma directa o a través de un proxy HTTPS.
2. **Una clave de acceso de AWS** (ID de clave de acceso y clave de acceso secreta) registrada en el almacén de credenciales de Pandora FMS como credencial de AWS. La credencial debe aportar las claves `access_key_id` y `secret_access_key`.
3. **Pandora FMS**: un servidor de Discovery para ejecutar la tarea y la consola para definirla.

El addon se distribuye como un paquete listo para ejecutar, por lo que no hay que instalar nada más en el servidor de Discovery.

### Permisos de AWS

El addon realiza únicamente peticiones de lectura y solo usa la operación `GetMetricData` de CloudWatch. La clave de acceso necesita la siguiente acción de IAM:

| Acción de AWS | Uso |
|---------------|-----|
| `cloudwatch:GetMetricData` | Ejecutar cada consulta que usted define |

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:GetMetricData"
      ],
      "Resource": "*"
    }
  ]
}
```

Asocie la política a un usuario IAM dedicado a Pandora FMS y genere una clave de acceso para él.

### Instalar el addon

Descargue el paquete `.disco` desde la entrada del Marketplace de Pandora FMS, limitada a usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.aws.cloudwatch](https://marketplace.pandorafms.com/entries/pandorafms.aws.cloudwatch)

Cárguelo en Pandora FMS. Una vez cargado, el paquete aparece en la lista de paquetes de Discovery como **Amazon Cloudwatch**, en la sección `cloud`:

![Paquete Amazon Cloudwatch cargado en Pandora FMS](../assets/images/discovery/amazon-cloudwatch/cloudwatch-package-loaded.png)

**Amazon Cloudwatch** queda disponible en la sección **Cloud** al crear tareas de Discovery.

## Configurar la tarea de Discovery

Cree la tarea desde las aplicaciones cloud de Discovery y elija **Amazon Cloudwatch**. La consola presenta los campos en dos pasos; cada campo se documenta en [Parámetros de la tarea](#parametros-de-la-tarea).

1. **Cloudwatch base** — credenciales, agente por defecto y destino de Tentacle:

    - **AWS Credentials**: la credencial de AWS registrada en el almacén de credenciales.
    - **Default agent name**: el agente que recibe cada módulo cuya configuración no indica otro agente.
    - **Tentacle IP**, **Tentacle port** y **Tentacle extra options**: destino al que se envían los datos de los agentes generados. Rara vez hace falta cambiarlos.

    ![Paso Cloudwatch base de la tarea de Discovery](../assets/images/discovery/amazon-cloudwatch/cloudwatch-base-step.png)

2. **Cloudwatch detailed** — ejecución, proxy, consultas y módulos:

    - **Max threads**: número de procesos en paralelo.
    - **Use proxy**, **Proxy url** y **Verify proxy SSL**: enrutan las peticiones a AWS a través de un proxy HTTPS.
    - **Configure Cloudwatch queries**: las consultas a ejecutar, como se describe en [Configuración de consultas](#configuracion-de-consultas).
    - **Configure module data**: cómo se convierte cada resultado en un módulo, como se describe en [Configuración de módulos](#configuracion-de-modulos).

    ![Paso Cloudwatch detailed de la tarea de Discovery](../assets/images/discovery/amazon-cloudwatch/cloudwatch-detailed-step.png)

El grupo y el intervalo de la tarea proceden del paso genérico de definición de la tarea. El grupo se aplica a los agentes que crea la tarea, y el intervalo es a la vez el periodo de ejecución y el intervalo de esos agentes.

### Configuración de consultas

El campo de consultas contiene una lista JSON. Cada elemento es un bloque de consulta y los bloques se ejecutan de forma independiente:

```json
[
  {
    "time_frame": "5m",
    "region_name": "us-east-1",
    "MetricDataQueries": [
      {
        "Id": "q1",
        "Expression": "SELECT AVG(CPUUtilization) FROM SCHEMA(\"AWS/EC2\", InstanceId) GROUP BY InstanceId",
        "Label": "avg_cpu",
        "Period": 300
      }
    ]
  }
]
```

| Clave | Obligatoria | Valor por defecto | Descripción |
|-------|-------------|-------------------|-------------|
| `time_frame` | No | `15m` | Ventana de datos solicitada, contada hacia atrás desde el momento en que se ejecuta la consulta. Un número entero seguido de `m` (minutos) o `h` (horas), por ejemplo `5m`, `30m` o `1h` |
| `region_name` | No | `us-east-1` | Región de AWS que consulta el bloque |
| `MetricDataQueries` | No | lista vacía | Lista de elementos `MetricDataQueries` de CloudWatch, con la estructura de la API `GetMetricData` de AWS (`Id`, `Expression`, `Label`, `Period`, `ReturnData`, ...) |

El `Id` de cada elemento enlaza el resultado con su [configuración de módulo](#configuracion-de-modulos). Las comillas dobles internas de una expresión `SCHEMA("...")` se pueden escribir como `\"` o sin escapar, como en los ejemplos de la documentación de AWS; el addon las escapa por usted. Escape con `\"` cualquier otra comilla doble dentro de una expresión.

### Configuración de módulos

El campo de módulos contiene una sección por cada `Id` definido en las consultas, en formato INI. Las líneas que empiezan por `#` son comentarios.

```ini
[q1]
name = __label__
type = generic_data
description = Average CPU utilization
unit = percent
value = average
min_warning = 75
min_critical = 85
agent = AWS EC2
```

| Clave | Obligatoria | Valor por defecto | Descripción |
|-------|-------------|-------------------|-------------|
| Nombre de la sección | Sí | — | Debe coincidir con el `Id` del elemento de consulta que configura |
| `name` | No | `module <Id>` | Nombre del módulo. `__label__` toma el nombre de la etiqueta que CloudWatch devuelve para cada serie |
| `type` | Sí | — | Tipo de módulo de Pandora FMS: `generic_data` (numérico), `generic_data_string` (cadena) o `async_string` |
| `value` | No | `last` | Cómo se convierten los puntos de datos de la serie en el valor del módulo: `last` o `average` (media aritmética de los puntos de datos devueltos) |
| `description`, `unit`, `min_warning`, `max_warning`, `min_critical`, `max_critical` | No | — | Descripción, unidad y umbrales de aviso y crítico del módulo |
| `agent` | No | **Default agent name** | Agente que recibe el módulo. Se crea si no existe |

Cualquier otra clave distinta de `name`, `type`, `value` y `agent` se reenvía a la definición del módulo. Cualquier `value` distinto de `average` se procesa como `last`: `max`, `min` y `sum` no se calculan. No use el carácter `%` en ningún valor, por ejemplo `unit = %`; use una palabra como `percent`.

Un elemento de consulta sin sección en la configuración de módulos, o cuya sección no tenga `type`, no produce ningún módulo.

## Verificar la primera ejecución

Fuerce la tarea desde la lista de tareas de Discovery y compruebe el resultado en este orden.

1. **El resumen de la tarea.** Una tarea que termina correctamente informa de:

    - **Total agents**: agentes que han recibido datos.
    - **Total modules**: módulos enviados.

    ![Resumen de ejecución de una tarea de Amazon Cloudwatch](../assets/images/discovery/amazon-cloudwatch/cloudwatch-task-summary.png)

    Una tarea que no termina correctamente, o que termina con problemas en alguna consulta, registra los mensajes en su información de ejecución. Consulte [Solución de problemas](#solucion-de-problemas).

2. **Los agentes.** El agente por defecto, más cada agente indicado con una clave `agent`.

    <!-- SCREENSHOT NEEDED: Agents list after an Amazon Cloudwatch task showing the default agent and an agent named by the module configuration, with lab names only. -->

3. **Los módulos.** Un módulo por cada serie devuelta por cada consulta.

## Interpretar los resultados

### Agentes generados

| Agente | Nombre | Notas |
|--------|--------|-------|
| Agente por defecto | **Default agent name** | Recibe cada módulo sin clave `agent` |
| Agente indicado | El valor `agent` de la configuración del módulo | Se crea cuando un módulo lo indica. Varios módulos pueden indicar el mismo agente |

Los agentes se identifican por su nombre: las tareas que usan el mismo nombre de agente informan al mismo agente y conservan su historial. Todos los agentes pertenecen al grupo de la tarea y usan su intervalo.

### Módulos generados

| Resultado de un elemento de consulta | Módulos |
|--------------------------------------|---------|
| Una consulta que devuelve una serie | Un módulo |
| Una consulta que devuelve varias series, por ejemplo con `GROUP BY` | Un módulo por serie |

Para cada serie:

- El nombre del módulo es la etiqueta de la serie con `name = __label__`, el `name` fijo en otro caso, o `module <Id>` si no hay `name`. Con un `name` fijo, todas las series de la consulta producen módulos con el mismo nombre en el mismo agente; use `__label__` en las consultas que devuelven varias series.
- El valor del módulo es el valor `last` o la media (`average`) de los puntos de datos devueltos, según `value`.
- Una serie sin puntos de datos en la ventana de tiempo no produce módulo en esa ejecución.

### Cómo se solicitan los datos

- Cada ejecución solicita los datos de `time_frame` hacia atrás desde el momento de la ejecución.
- Cada bloque de consulta solicita como máximo 100 puntos de datos y el addon no solicita páginas adicionales, de modo que una consulta que devuelve muchas series con muchos puntos de datos puede quedar truncada. Acote la consulta o la ventana de tiempo.
- Los bloques de consulta se ejecutan en paralelo, hasta **Max threads** a la vez.

## Operación

### Ejecución manual

El addon puede ejecutarse fuera de una tarea de Discovery. Recibe tres parámetros, todos obligatorios:

```bash
./pandora_aws_cloudwatch \
  --creds <BASE64_CREDENTIALS> \
  --conf <PATH_TO_CONFIG> \
  --query_conf <PATH_TO_QUERY_FILE>
```

- `--creds`: Base64 del JSON `{"access_key_id": "<ACCESS_KEY_ID>", "secret_access_key": "<SECRET_ACCESS_KEY>"}`. Un valor pasado como argumento de línea de comandos puede quedar expuesto en el historial del shell y en la lista de procesos del sistema operativo. Ejecútelo solo en un equipo que usted controle.
- `--conf`: el [fichero de configuración](#fichero-de-configuracion), que contiene también la configuración de módulos a continuación de la sección `[CONF]`.
- `--query_conf`: un fichero con la [configuración de consultas](#configuracion-de-consultas).

Imprime un resumen JSON y envía un fichero de datos por agente:

```json
{"summary": {"Total agents": 3, "Total modules": 25}}
```

Cuando se producen errores, el JSON contiene además una clave `info` con los mensajes.

## Solución de problemas

El addon no tiene indicador verbose ni de depuración. Su canal de diagnóstico es la información de ejecución de la tarea, que muestra los mensajes siguientes.

| Mensaje | Significado y acción |
|---------|----------------------|
| `Error: empty creds` | No se ha seleccionado ninguna credencial |
| `Error with creds: ...` | La credencial no es un JSON válido con las claves `access_key_id` y `secret_access_key` |
| `Error parsing configuration: ...` | Las consultas no son JSON válido, o la configuración de módulos contiene una línea no válida, por ejemplo un valor con el carácter `%` |
| `ClientError AWS: ...`, `BotoCoreError AWS: ...` o `Error AWS: ...`, seguido de `Error: query_charge failed for region '<region>' or query '<queries>': ...` | Una consulta ha fallado. Compruebe la región, la sintaxis de la expresión, la credencial y el permiso `cloudwatch:GetMetricData`. El mismo mensaje aparece cuando `time_frame` no es un número entero seguido de `m` o `h` |
| `Empty values or invalid configuration for <Id>, aborting` | La consulta no devolvió puntos de datos en la ventana de tiempo. Aumente `time_frame` o revise la métrica |
| `Module '<Id>' is missing 'type' in module_configuration` | No hay sección de módulo para ese `Id`, o la sección no tiene `type` |
| **Total modules** inferior al esperado | Una consulta puede estar truncada por el límite de 100 puntos de datos, o sus series no devolvieron datos |
| Varias series se sobrescriben entre sí | El `name` del módulo es fijo. Use `name = __label__` |
| Errores al alcanzar AWS a través de un proxy | Compruebe **Proxy url**; solo las peticiones HTTPS se enrutan por el proxy |

## Referencia

### Parámetros de la tarea

#### Cloudwatch base

| Campo | Macro | Tipo | Valor por defecto | Notas |
|-------|-------|------|-------------------|-------|
| AWS Credentials | `_credentials_` | selector de credencial (AWS) | — | Obligatorio. Credencial registrada en el almacén de credenciales |
| Default agent name | `_agentName_` | cadena | — | Opcional en la definición de la tarea. Si se deja vacío, el agente se crea con el alias vacío |
| Tentacle IP | `_tentacleIP_` | cadena | `127.0.0.1` | Servidor que recibe los datos de los agentes |
| Tentacle port | `_tentaclePort_` | número | `41121` | Puerto de Tentacle |
| Tentacle extra options | `_tentacleExtraOpt_` | cadena | — | Opcional. Esta versión del addon no lo aplica |

#### Cloudwatch detailed

| Campo | Macro | Tipo | Valor por defecto | Notas |
|-------|-------|------|-------------------|-------|
| Max threads | `_threads_` | número | `1` | Opcional. Use `1` o más |
| Use proxy | `_useProxy_` | casilla | desactivada | Enruta las peticiones a AWS a través de un proxy |
| Proxy url | `_proxyUrl_` | cadena | — | Opcional. Se muestra con **Use proxy** activado. Se aplica a las peticiones HTTPS |
| Verify proxy SSL | `_sslCheck_` | casilla | desactivada | Se muestra con **Use proxy** activado. Desactivada, el addon no valida los certificados TLS en sus conexiones a AWS |
| Configure Cloudwatch queries | `_configQueries_` | área de texto | vacío | Obligatorio. Consulte [Configuración de consultas](#configuracion-de-consultas) |
| Configure module data | `_configModules_` | área de texto | plantilla comentada | Obligatorio. Consulte [Configuración de módulos](#configuracion-de-modulos). La plantilla comentada menciona `max` y `min` para `value`; no se calculan |

Como **Verify proxy SSL** solo se muestra con **Use proxy**, una tarea que no usa proxy se ejecuta siempre con la validación de certificados TLS desactivada. Ejecute esas tareas solo desde una red de confianza.

### Fichero de configuración

Se usa en la ejecución manual. La sección `[CONF]` contiene las opciones; cada sección adicional es una sección de [configuración de módulo](#configuracion-de-modulos).

| Clave | Valor por defecto | Descripción |
|-------|-------------------|-------------|
| `agents_group` | `0` | ID numérico del grupo de los agentes generados. Un valor que no sea un número se lee como `0` |
| `agent_name` | `AWS Cloudwatch` | Nombre del agente por defecto |
| `interval` | `300` | Intervalo del agente, en segundos |
| `threads` | `1` | Procesos en paralelo. Use `1` o más |
| `transfer_mode` | `tentacle` | Modo de transferencia de los ficheros de datos |
| `tentacle_ip` | `127.0.0.1` | Dirección del servidor Tentacle |
| `tentacle_port` | `41121` | Puerto del servidor Tentacle |
| `use_proxy` | `0` | `1` enruta las peticiones a AWS a través del proxy |
| `proxy_url` | vacío | URL del proxy, aplicada a las peticiones HTTPS |
| `ssl_check` | `0` | `1` valida los certificados TLS; `0` no los valida |

Ejemplo:

```ini
[CONF]
agents_group  = 1
agent_name    = AWS General
interval      = 300
threads       = 3
transfer_mode = tentacle
tentacle_ip   = <TENTACLE_SERVER_IP>
tentacle_port = 41121
use_proxy     = 0
ssl_check     = 1

[q1]
name = __label__
type = generic_data
description = Average CPU utilization
unit = percent
value = average
agent = AWS EC2
```

### Identidad del addon

| Elemento | Valor |
|----------|-------|
| Nombre | Amazon Cloudwatch |
| Identificador | `pandorafms.aws.cloudwatch` |
| Versión del paquete | `1.0` |
| Tipo y sección | Discovery, `cloud` |
| Entrada del Marketplace | [pandorafms.aws.cloudwatch](https://marketplace.pandorafms.com/entries/pandorafms.aws.cloudwatch), última actualización 2025-10-22 |
| Disponibilidad | La entrada del Marketplace indica que la descarga está limitada a usuarios con licencia |
