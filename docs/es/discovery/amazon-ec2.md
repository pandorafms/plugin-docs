# Amazon EC2 Discovery

*Última actualización del artículo: 2026-10-26.*

## Qué monitoriza

El addon de Discovery de Amazon EC2 monitoriza instancias EC2 de Amazon Web Services y las regiones que las contienen. Consulta las API de AWS y convierte el resultado en agentes y módulos de Pandora FMS: estado de la instancia, rendimiento de CPU, disco, IOPS y red, almacenamiento de volúmenes, direcciones IP elásticas y, opcionalmente, el coste por región.

Una tarea de Discovery genera tres tipos de agentes:

- **Un agente global de estadísticas** (opcional) con el número de instancias y el coste total.
- **Un agente por cada región monitorizada**, con módulos de resumen agregados sobre las instancias de esa región.
- **Un agente por cada instancia monitorizada**, con su estado y sus módulos de rendimiento. El agente de la instancia es hijo del agente de su región.

Una región se puede seleccionar completa, y entonces se monitoriza cada instancia que contiene, incluidas las que se creen más adelante. También se pueden seleccionar instancias individuales sin seleccionar su región.

## Preparación

### Compatibilidad

| Alcance | Estado | Evidencia |
|---------|--------|-----------|
| Addon `pandorafms.aws.ec2`, versión `1.5` | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del addon](#identidad-del-addon) |
| Acceso de red desde el servidor de Discovery a las API de AWS | `Requerido` | El addon llama a las API de AWS EC2, CloudWatch y Cost Explorer |
| Clave de acceso de AWS con los permisos de [Permisos de AWS](#permisos-de-aws) | `Requerido` | Prerrequisito, no una declaración de compatibilidad |
| Sistema operativo del servidor de Discovery | `Sin validar` | No se ha registrado ningún sistema operativo para esta versión |
| Versiones concretas de Pandora FMS | `Sin validar` | No se ha registrado una matriz de versiones para este addon |

### Prerrequisitos

1. **Conectividad** desde el servidor de Discovery a las API de AWS, de forma directa o a través de un proxy HTTPS.
2. **Una clave de acceso de AWS** (ID de clave de acceso y clave de acceso secreta) con los permisos descritos a continuación, registrada en el almacén de credenciales de Pandora FMS como credencial de AWS.
3. **Pandora FMS**: un servidor de Discovery para ejecutar la tarea y la consola para definirla.

El addon incluye sus propios ejecutables, `bin/pandora_aws_ec2` y `bin/aws_ec2`, por lo que no hay que instalar nada más en el servidor de Discovery para ejecutar una tarea.

### Permisos de AWS

El addon realiza únicamente peticiones de lectura. Las que emite dependen de las opciones que active:

| Acción de AWS | Uso |
|---------------|-----|
| `ec2:DescribeInstances` | Listar regiones e instancias (siempre) |
| `cloudwatch:GetMetricStatistics` | Métricas de CPU, disco, IOPS y red (con **Scan and general monitoring** activado) |
| `ec2:DescribeVolumes` | Módulos de almacenamiento (con **Storage** activado) |
| `ec2:DescribeAddresses` | Módulos de IP elásticas (con **Elastic IP Adresses** activado) |
| `ce:GetCostAndUsage` | Módulos de coste (con **Total cost** activado) |

Una política IAM que concede todas ellas:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeVolumes",
        "ec2:DescribeAddresses",
        "cloudwatch:GetMetricStatistics",
        "ce:GetCostAndUsage"
      ],
      "Resource": "*"
    }
  ]
}
```

Asigne la política a un usuario IAM dedicado a Pandora FMS y genere una clave de acceso para él. Omita las acciones de las opciones que no vaya a activar.

La credencial almacenada en Pandora FMS debe proporcionar las claves `access_key_id` y `secret_access_key`; el plugin falla con `Error while parsing credentials` cuando falta alguna.

### Instalar el addon

Descargue el paquete `.disco` desde la entrada del Marketplace de Pandora FMS, cuya descarga está limitada a usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.aws.ec2](https://marketplace.pandorafms.com/entries/pandorafms.aws.ec2)

Cárguelo en Pandora FMS. Una vez cargado, **Amazon EC2** está disponible en la sección **Cloud** al crear tareas de Discovery.

## Configurar la tarea de Discovery

Cree la tarea desde las aplicaciones cloud de Discovery y elija **Amazon EC2**. La consola presenta los campos en cuatro pasos; todos los campos se documentan en [Parámetros de la tarea](#parametros-de-la-tarea).

1. **EC2 Basic** — credenciales, ejecución y opciones de agente:

    - **AWS Credentials**: la credencial de AWS registrada en el almacén de credenciales.
    - **Max threads**: número de grupos en los que se reparten las regiones e instancias monitorizadas.
    - **Use proxy**, **Proxy url** y **Verify proxy SSL**: enrutan las peticiones a AWS a través de un proxy HTTPS.
    - **Tentacle IP**, **Tentacle port** y **Tentacle extra options**: dónde y cómo se envían los datos de los agentes generados. Rara vez necesitan cambiarse.
    - **Add global stats agent** y **Stats agent name**: crean el agente global y permiten nombrarlo.
    - **Agent autodisable mode**: deshabilita el agente cuando todos sus módulos pasan a desconocido hasta que vuelvan a llegar datos.

    <!-- SCREENSHOT NEEDED: paso EC2 Basic del asistente con credenciales, Max threads, proxy, Tentacle y agente de estadísticas, sin credenciales ni direcciones reales. -->

2. **EC2 Instances** — un árbol de regiones e instancias leído de su cuenta de AWS con la credencial seleccionada. Marque una región para monitorizarla junto con todas sus instancias, o marque instancias individuales. Bajo cada región, las instancias se agrupan por tipo de instancia.

    <!-- SCREENSHOT NEEDED: paso EC2 Instances del asistente con el árbol de regiones e instancias y una región y una instancia seleccionadas, solo con identificadores de laboratorio. -->

3. **Instances monitoring** — las métricas recopiladas:

    - **Scan and general monitoring**: habilita las opciones de CPU, IOPs, disco y red.
    - **Cpu performance summary**, **IOPs performance summary**, **Disk performance summary**, **Network performance summary**: solo se muestran con **Scan and general monitoring** activado.
    - **Storage** y **Elastic IP Adresses**: independientes de **Scan and general monitoring**.

    <!-- SCREENSHOT NEEDED: paso Instances monitoring del asistente con las casillas de monitorización. -->

4. **EC2 Costs** — monitorización de costes:

    - **Total cost**: habilita los módulos de coste.
    - **Cost by region**: regiones a consultar. Se muestra con **Total cost** activado.
    - **Cost interval**: periodo de tiempo que abarca el coste. Se muestra con **Total cost** activado.

    <!-- SCREENSHOT NEEDED: paso EC2 Costs del asistente con Total cost, Cost by region y Cost interval. -->

El grupo y el intervalo de la tarea proceden del paso genérico de definición de la tarea y se aplican a los agentes que la tarea crea.

## Verificar la primera ejecución

Fuerce la tarea desde la lista de tareas de Discovery y compruebe el resultado en este orden.

1. **El resumen de la tarea.** Una tarea que finaliza correctamente informa de:

    - **Total agents**: todos los agentes generados, incluido el agente global cuando está activado.
    - **Zones agents**: regiones monitorizadas.
    - **Instances agents**: instancias monitorizadas.

    Una tarea que no finaliza correctamente registra los errores en su información de ejecución.

    <!-- SCREENSHOT NEEDED: resumen de ejecución de una tarea de Discovery de Amazon EC2 con Total agents, Zones agents e Instances agents. -->

2. **Los agentes.** Uno por cada región seleccionada, uno por instancia y, si está activado, el agente global. Los agentes de instancia son hijos del agente de su región.

3. **Los módulos.** Todo agente de instancia tiene `State` e `Instance State (bool)`. Los módulos de rendimiento solo aparecen en instancias en ejecución; consulte [Interpretar los resultados](#interpretar-los-resultados).

## Interpretar los resultados

### Agentes generados

| Agente | Alias | Padre | Notas |
|--------|-------|-------|-------|
| Agente global | El **Stats agent name**, o `Aws` si está vacío | Ninguno | Solo se crea con **Add global stats agent** activado |
| Agente de región | El nombre de la región, por ejemplo `eu-west-1` | El agente global solo cuando se indicó un **Stats agent name** | Uno por región seleccionada |
| Agente de instancia | El ID de la instancia | Su agente de región | Uno por instancia, creado una sola vez aunque se seleccionen la instancia y su región. La versión del agente es el tipo de instancia y la dirección es la IP pública, si la tiene |

La identidad del agente no depende de la tarea: los agentes de región se identifican por la clave de acceso y la región, y los de instancia por la clave de acceso y el ID de la instancia. Mover una región o instancia entre tareas que usan la misma clave de acceso sigue reportando al mismo agente y conserva su histórico.

Todos los agentes informan `Aws` como nombre de sistema operativo, y `ec2` como versión del sistema operativo en regiones e instancias.

### Módulos por agente

**Agente global**

| Módulo | Tipo | Descripción |
|--------|------|-------------|
| `AWS EC2 Instances count` | `generic_data` | Instancias encontradas en las regiones e instancias seleccionadas |
| `AWS EC2 Total cost` | `generic_data` | Coste de las regiones de coste seleccionadas durante el intervalo de coste. Solo se crea con **Total cost** activado |

**Agente de región**

| Módulo | Condición | Descripción |
|--------|-----------|-------------|
| `summary.aws.ec2.instances` | Región seleccionada completa | Instancias de la región |
| `cost` | **Total cost** activado, región en **Cost by region** y al menos una instancia en la región | Coste de la región durante el intervalo de coste |
| `summary.aws.ec2.CPUUtilization` | **Scan and general monitoring** y **Cpu performance summary** | CPU de las instancias en ejecución dividida entre el número de instancias de la región |
| `summary.aws.ec2.DiskReadBytes`, `summary.aws.ec2.diskWriteBytes` | **Scan and general monitoring** y **Disk performance summary** | Suma sobre las instancias en ejecución, en `Bytes` |
| `summary.aws.ec2.DiskReadOps`, `summary.aws.ec2.DiskWriteOps` | **Scan and general monitoring** y **IOPs performance summary** | Suma sobre las instancias en ejecución |
| `summary.aws.ec2.NetworkPacketsIn`, `summary.aws.ec2.NetworkPacketsOut` | **Scan and general monitoring** y **Network performance summary** | Suma sobre las instancias en ejecución, en `packets` |
| `summary.aws.ec2.addresses.count` | **Elastic IP Adresses** | Direcciones IP elásticas de la región |
| `summary.aws.ec2.storage.count`, `summary.aws.ec2.storage.size` | **Storage** | Volúmenes de la región y su tamaño total en `GB` |

**Agente de instancia**

| Módulo | Tipo | Condición | Descripción |
|--------|------|-----------|-------------|
| `State` | `generic_data_string` | Siempre | Estado de la instancia según AWS |
| `Instance State (bool)` | `generic_proc` | Siempre | `1` cuando el estado es `running`, `0` en caso contrario |
| `CPUUtilization` | `generic_data` | En ejecución, **Cpu performance summary** | Uso de CPU |
| `DiskReadBytes`, `DiskWriteBytes` | `generic_data` | En ejecución, **Disk performance summary** | Bytes leídos y escritos en disco, en `Bytes` |
| `DiskReadOps`, `DiskWriteOps` | `generic_data` | En ejecución, **IOPs performance summary** | Operaciones de lectura y escritura en disco |
| `NetworkPacketsIn`, `NetworkPacketsOut` | `generic_data` | En ejecución, **Network performance summary** | Paquetes de red recibidos y enviados, en `packets` |

### Cómo se obtienen los valores

- Los valores de rendimiento son la última media de cinco minutos que AWS CloudWatch devuelve para los últimos 150 minutos. Cuando CloudWatch no devuelve ningún punto de datos en esa ventana, el valor del módulo es `0`.
- Los módulos de rendimiento solo se crean para instancias en estado `running`.
- Los módulos de coste usan el **Cost interval** como periodo y se refrescan con ese intervalo, no con el de la tarea.

## Operación

### Ejecución manual

El addon puede ejecutarse fuera de una tarea de Discovery. El ejecutable admite un único parámetro, la ruta a un fichero de configuración descrito en [Fichero de configuración](#fichero-de-configuracion):

```bash
./pandora_aws_ec2 --conf <PATH_TO_CONFIG>
```

Imprime un resumen JSON y envía un fichero de datos por agente con el modo de transferencia configurado:

```json
{"summary": {"Total agents": 23, "Zones agents": 5, "Instances agents": 17}}
```

Cuando se producen errores, el JSON contiene además una clave `info` con los mensajes y el código de salida es `1`.

En modo de transferencia `local` los ficheros de datos se mueven a `data_dir`. En modo `tentacle`, el ejecutable `tentacle_client` debe estar disponible en el `PATH` del usuario que ejecuta el addon.

Un fichero de configuración contiene la clave de acceso de AWS codificada en `creds_b64`. Protéjalo con permisos restrictivos.

## Solución de problemas

El addon no tiene opción verbose ni de depuración. Su canal de diagnóstico es el campo `info` del resultado JSON de la ejecución, que se muestra en la información de ejecución de la tarea.

- **`Error while parsing credentials`**: la credencial no proporciona `access_key_id` y `secret_access_key`, o `creds_b64` no es JSON válido codificado en base64.
- **El árbol de instancias está vacío o le falta una región**: las regiones cuya petición `DescribeInstances` falla se omiten del árbol sin error. Compruebe el permiso `ec2:DescribeInstances` de la clave y el estado de la región en AWS.
- **Menos agentes de los esperados**: solo se monitorizan las regiones e instancias marcadas. Una región seleccionada sin instancias produce igualmente su agente de región.
- **`Error getting cost for <region>`**: falló la consulta de costes de esa región. Compruebe que la clave de acceso tiene `ce:GetCostAndUsage`; el mensaje incluye el error devuelto por AWS.
- **Los módulos de rendimiento valen `0`**: CloudWatch no devolvió ningún punto de datos en los últimos 150 minutos para esa instancia y métrica.
- **Una instancia no tiene módulos de rendimiento**: la instancia no está en `running`, o **Scan and general monitoring** está desactivado.
- **`Error getting volumes for <region>` o `Error getting addresses for <region>`**: la clave carece de `ec2:DescribeVolumes` o `ec2:DescribeAddresses`.
- **Errores al llegar a AWS a través de un proxy**: revise **Proxy url**; solo las peticiones HTTPS se enrutan a través de él.

## Referencia

### Parámetros de la tarea

#### EC2 Basic

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|-------------|-------|
| AWS Credentials | `_credentials_` | selector de credencial (AWS) | — | Obligatorio. Credencial registrada en el almacén de credenciales |
| Max threads | `_threads_` | número | `1` | Opcional. Las regiones e instancias se reparten en grupos, nunca más grupos que destinos |
| Use proxy | `_useProxy_` | casilla | desactivada | Enruta las peticiones a AWS a través de un proxy |
| Proxy url | `_proxyUrl_` | cadena | — | Opcional. Se muestra con **Use proxy** activado. Se aplica a las peticiones HTTPS |
| Verify proxy SSL | `_sslCheck_` | casilla | desactivada | Se muestra con **Use proxy** activado. Desactivada, el addon no valida los certificados TLS en sus conexiones a AWS |
| Tentacle IP | `_tentacleIP_` | cadena | `127.0.0.1` | Servidor que recibe los datos de los agentes |
| Tentacle port | `_tentaclePort_` | número | `41121` | Puerto de Tentacle |
| Tentacle extra options | `_tentacleExtraOpt_` | cadena | — | Opcional. Opciones adicionales del cliente Tentacle |
| Add global stats agent | `_statsAgent_` | casilla | activada | Crea el agente global |
| Stats agent name | `_statsAgentName_` | cadena | `Aws` | Opcional. Se muestra con **Add global stats agent** activado |
| Agent autodisable mode | `_agentautodisable_` | casilla | desactivada | Deshabilita el agente cuando todos sus módulos pasan a desconocido hasta que vuelvan a llegar datos |

Como **Verify proxy SSL** solo se muestra con **Use proxy**, una tarea que no usa proxy se ejecuta siempre con la validación de certificados TLS desactivada. Ejecute estas tareas únicamente desde una red de confianza.

#### EC2 Instances

| Campo | Macro | Tipo | Notas |
|-------|-------|------|-------|
| EC2 zones and instances | `_ec2Zones_`, `_ec2Instance_` | árbol | Las regiones rellenan la lista de regiones y las instancias la lista de instancias. Opcional |

#### Instances monitoring

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|-------------|-------|
| Scan and general monitoring | `_ec2InstanceSummary_` | casilla | desactivada | Habilita los módulos de rendimiento |
| Cpu performance summary | `_ec2CpuPerfSummary_` | casilla | desactivada | Se muestra con **Scan and general monitoring** |
| IOPs performance summary | `_ec2IopsPerfSummary_` | casilla | desactivada | Se muestra con **Scan and general monitoring** |
| Disk performance summary | `_ec2DiskPerfSummary_` | casilla | desactivada | Se muestra con **Scan and general monitoring** |
| Network performance summary | `_ec2NetworkPerfSummary_` | casilla | desactivada | Se muestra con **Scan and general monitoring** |
| Storage | `_ec2StorageSummary_` | casilla | desactivada | Módulos de volúmenes |
| Elastic IP Adresses | `_ec2ElasticAddressesSummary_` | casilla | desactivada | Módulos de IP elásticas |

#### EC2 Costs

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|-------------|-------|
| Total cost | `_globalTotalCost_` | casilla | desactivada | Habilita los módulos de coste |
| Cost by region | `_globalCostRegion_` | selección múltiple | ninguna | Regiones: `us-east-1`, `us-east-2`, `us-west-1`, `us-west-2`, `ca-central-1`, `eu-central-1`, `eu-west-1`, `eu-west-2`, `eu-west-3`, `ap-northeast-1`, `ap-northeast-2`, `ap-southeast-1`, `ap-southeast-2`, `ap-south-1`, `sa-east-1` |
| Cost interval | `_globalCostInterval_` | selector | `604800` (segundos) | Periodo que abarca el coste |

### Fichero de configuración

Se usa en la ejecución manual. Un `clave = valor` por línea. Los valores de lista son arrays JSON. Las opciones numéricas aceptan `1` para activar y `0` para desactivar; un valor que no es un número se lee como `0`.

| Clave | Por defecto | Descripción |
|-------|-------------|-------------|
| `agents_group_name` | `aws` | Grupo de los agentes generados |
| `interval` | `300` | Intervalo de los agentes, en segundos |
| `interval_cost` | `300` | Periodo que abarcan los módulos de coste, en segundos. Use un número entero de segundos |
| `threads` | `1` | Número de grupos en los que se reparten los destinos |
| `transfer_mode` | `local` | `local` escribe los ficheros de datos en `data_dir`; cualquier otro valor los envía con Tentacle |
| `tentacle_client` | `tentacle_client` | Ejecutable del cliente Tentacle |
| `tentacle_ip` | `127.0.0.1` | Dirección del servidor Tentacle |
| `tentacle_port` | `41121` | Puerto del servidor Tentacle |
| `tentacle_opts` | vacío | Opciones adicionales del cliente Tentacle |
| `data_dir` | `/var/spool/pandora/data_in/` | Destino de los ficheros de datos en modo `local` |
| `temporal` | `/tmp` | Directorio donde se escriben los ficheros de datos antes de enviarlos |
| `storage` | `1` | Módulos de almacenamiento |
| `elastic_ip_address` | `1` | Módulos de IP elásticas |
| `advance_monitoring` | `1` | Módulos de rendimiento; necesaria para las cuatro opciones siguientes |
| `cpu_summary` | `1` | Módulos de CPU |
| `iops_summary` | `1` | Módulos de IOPS |
| `disk_summary` | `1` | Módulos de disco |
| `network_summary` | `1` | Módulos de red |
| `total_cost` | `1` | Módulos de coste |
| `cost_regions` | `[]` | Regiones a consultar para costes |
| `aws_regions` | `[]` | Regiones a monitorizar |
| `aws_instances` | `[]` | IDs de instancia a monitorizar |
| `stats_agent` | `1` | Agente global |
| `stats_agent_name` | vacío | Nombre del agente global; alias `Aws` si está vacío |
| `agent_autodisable` | `0` | Modo autodisable |
| `use_proxy` | `0` | Usar un proxy |
| `proxy_url` | vacío | URL del proxy |
| `ssl_check` | `0` | `1` valida los certificados TLS; `0` no |
| `creds_b64` | vacío | Obligatorio. Base64 del JSON `{"access_key_id": "<ACCESS_KEY_ID>", "secret_access_key": "<SECRET_ACCESS_KEY>"}` |

Ejemplo:

```ini
agents_group_name  = Aws
interval           = 300
interval_cost      = 604800
threads            = 4
transfer_mode      = tentacle
tentacle_ip        = <TENTACLE_SERVER_IP>
tentacle_port      = 41121

storage            = 1
elastic_ip_address = 1
advance_monitoring = 1
cpu_summary        = 1
iops_summary       = 1
disk_summary       = 1
network_summary    = 1

stats_agent        = 1
stats_agent_name   = AwsCloud

total_cost         = 1
cost_regions       = ["us-east-1","us-west-1"]

aws_regions        = ["us-east-1","eu-west-1"]
aws_instances      = ["<INSTANCE_ID>"]

creds_b64          = <BASE64_CREDENTIALS>
```

### Identidad del addon

| Elemento | Valor |
|----------|-------|
| Nombre | Amazon EC2 |
| Identificador | `pandorafms.aws.ec2` |
| Versión | `1.5` |
| Tipo y sección | Discovery, `cloud` |
| Entrada del Marketplace | [pandorafms.aws.ec2](https://marketplace.pandorafms.com/entries/pandorafms.aws.ec2), actualizada el 2026-08-31 |
| Disponibilidad | La entrada del Marketplace indica que la descarga está limitada a usuarios con licencia |
