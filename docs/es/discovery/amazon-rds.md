# Amazon RDS Discovery

*Última actualización del artículo: 2026-10-26.*

## Qué monitoriza

El addon de Discovery de Amazon RDS monitoriza instancias de base de datos RDS de Amazon Web Services y las regiones que las contienen. Consulta las API de AWS y convierte el resultado en agentes y módulos de Pandora FMS: estado de la instancia, conexiones a la base de datos y rendimiento de CPU, disco, IOPS y red.

Una tarea de Discovery genera tres tipos de agentes:

- **Un agente global de estadísticas** (opcional) con el número de instancias encontradas.
- **Un agente por cada región monitorizada**, con módulos de resumen agregados sobre las instancias de esa región.
- **Un agente por cada instancia monitorizada**, con sus módulos de estado y rendimiento. El agente de instancia es hijo del agente de su región.

Una región se puede seleccionar completa, y entonces se monitoriza cada instancia que contiene, incluidas las que se creen más adelante. También se pueden seleccionar instancias individuales sin seleccionar su región.

## Preparación

### Compatibilidad

| Alcance | Estado | Evidencia |
|---------|--------|-----------|
| Addon `pandorafms.aws.rds`, versión `1.2` | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del addon](#identidad-del-addon) |
| Acceso de red desde el servidor de Discovery a las API de AWS | `Requerido` | El addon llama a las API de AWS RDS y CloudWatch |
| Clave de acceso de AWS con los permisos de [Permisos de AWS](#permisos-de-aws) | `Requerido` | Prerrequisito, no una declaración de compatibilidad |
| Sistema operativo del servidor de Discovery | `Sin validar` | No se ha registrado ningún sistema operativo para esta versión |
| Versiones concretas de Pandora FMS | `Sin validar` | No se ha registrado una matriz de versiones para este addon |

### Prerrequisitos

1. **Conectividad** desde el servidor de Discovery a las API de AWS, de forma directa o a través de un proxy HTTPS.
2. **Una clave de acceso de AWS** (ID de clave de acceso y clave de acceso secreta) con los permisos descritos a continuación, registrada en el almacén de credenciales de Pandora FMS como credencial de AWS.
3. **Pandora FMS**: un servidor de Discovery para ejecutar la tarea y la consola para definirla.

El addon incluye sus propios ejecutables, `bin/pandora_aws_rds` y `bin/aws_rds`, por lo que no hay que instalar nada más en el servidor de Discovery para ejecutar una tarea.

### Permisos de AWS

El addon realiza únicamente peticiones de lectura:

| Acción de AWS | Uso |
|---------------|-----|
| `rds:DescribeDBInstances` | Listar las instancias de cada región (siempre) |
| `cloudwatch:GetMetricData` | Métricas de conexiones, CPU, disco, IOPS y red (con **Scan and general monitoring** activado) |

Una política IAM que concede ambas:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "rds:DescribeDBInstances",
        "cloudwatch:GetMetricData"
      ],
      "Resource": "*"
    }
  ]
}
```

Asocie la política a un usuario IAM dedicado creado para Pandora FMS y genere una clave de acceso para él. Omita `cloudwatch:GetMetricData` si no va a activar **Scan and general monitoring**.

La credencial almacenada en Pandora FMS debe proporcionar las claves `access_key_id` y `secret_access_key`; el addon informa de `Error while parsing credentials` cuando falta alguna.

### Instalar el addon

Descargue el paquete `.disco` desde la entrada del Marketplace de Pandora FMS, cuya descarga está limitada a usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.aws.rds](https://marketplace.pandorafms.com/entries/pandorafms.aws.rds)

Cárguelo en Pandora FMS. Una vez cargado, **Amazon RDS** está disponible en la sección **Cloud** al crear tareas de Discovery.

## Configurar la tarea de Discovery

Cree la tarea desde las aplicaciones cloud de Discovery y elija **Amazon RDS**. La consola presenta los campos en tres pasos; todos los campos se documentan en [Parámetros de la tarea](#parametros-de-la-tarea).

1. **RDS Basic** — credenciales, ejecución y opciones de agente:

    - **AWS Credentials**: la credencial de AWS registrada en el almacén de credenciales.
    - **Max threads**: número de grupos en que se dividen las regiones e instancias monitorizadas.
    - **Use proxy**, **Proxy url** y **Verify proxy SSL**: enrutan las peticiones a AWS a través de un proxy HTTPS.
    - **Tentacle IP**, **Tentacle port** y **Tentacle extra options**: dónde y cómo se envían los datos de los agentes generados. Rara vez hay que cambiarlos.
    - **Add global stats agent** y **Stats agent name**: crean el agente global y, opcionalmente, le dan nombre.
    - **Agent autodisable mode**: deshabilita el agente cuando todos sus módulos pasan a desconocido hasta que vuelvan a llegar datos.

    ![Paso RDS Basic del asistente](../assets/images/discovery/amazon-rds/rds-basic-step.png)

2. **RDS Instances** — un árbol de regiones e instancias leído de su cuenta de AWS con la credencial seleccionada. Marque una región para monitorizarla junto con todas sus instancias, o marque instancias individuales. Las instancias se listan bajo su región, dentro de un nodo para su motor de base de datos. Seleccione al menos una región o instancia.

    ![Paso RDS Instances del asistente: árbol de regiones](../assets/images/discovery/amazon-rds/rds-instances-tree.png)

3. **Instances monitoring** — las métricas recopiladas:

    - **Scan and general monitoring**: habilita las conexiones a la base de datos y las opciones de CPU, IOPs, disco y red.
    - **Cpu performance summary**, **IOPs performance summary**, **Disk performance summary**, **Network performance summary**: solo se muestran con **Scan and general monitoring** activado.

    ![Paso Instances monitoring del asistente](../assets/images/discovery/amazon-rds/rds-instances-monitoring-step.png)

El grupo y el intervalo de la tarea proceden del paso genérico de definición de la tarea y se aplican a los agentes que la tarea crea.

## Verificar la primera ejecución

Fuerce la tarea desde la lista de tareas de Discovery y compruebe el resultado en este orden.

1. **El resumen de la tarea.** Una tarea que finaliza correctamente informa de:

    - **Total agents**: todos los agentes generados, incluido el agente global cuando está activado.
    - **Zones agents**: regiones monitorizadas.
    - **Instances agents**: instancias monitorizadas.

    Una tarea que no finaliza correctamente registra los errores en su información de ejecución.

    ![Resumen de ejecución de una tarea de Amazon RDS](../assets/images/discovery/amazon-rds/rds-task-summary.png)

2. **Los agentes.** Uno por cada región seleccionada, uno por instancia y, si está activado, el agente global. Los agentes de instancia son hijos del agente de su región.

3. **Los módulos.** Todo agente de instancia tiene `State` e `Instance State (bool)`. Los módulos de rendimiento solo aparecen en instancias en estado `available`; consulte [Interpretar los resultados](#interpretar-los-resultados).

## Interpretar los resultados

### Agentes generados

| Agente | Alias | Padre | Notas |
|--------|-------|-------|-------|
| Agente global | El **Stats agent name**, o `Aws.rds` si está vacío | Ninguno | Se crea solo con **Add global stats agent** activado |
| Agente de región | El nombre de la región, por ejemplo `eu-west-1` | El agente global solo si se indicó un **Stats agent name** | Uno por región seleccionada |
| Agente de instancia | El identificador de la instancia | Su agente de región | Uno por instancia, creado una sola vez aunque se seleccionen la instancia y su región. La versión del agente es la clase de la instancia y la dirección es la del endpoint de la instancia. El agente de región solo se crea cuando se selecciona la propia región |

La identidad del agente no depende de la tarea: los agentes de región se identifican por la clave de acceso y la región, y los de instancia por la clave de acceso y el identificador de la instancia. Mover una región o instancia entre tareas que usan la misma clave de acceso mantiene el reporte al mismo agente y conserva su histórico.

Los agentes de región e instancia informan del nombre de sistema operativo `Aws` y de la versión de sistema operativo `rds`. El agente global informa del nombre de sistema operativo `Aws`.

### Módulos por agente

**Agente global**

| Módulo | Tipo | Descripción |
|--------|------|-------------|
| `AWS RDS Instances count` | `generic_data` | Instancias encontradas en las regiones e instancias seleccionadas |

**Agente de región**

| Módulo | Condición | Descripción |
|--------|-----------|-------------|
| `summary.aws.rds.instances` | Siempre | Instancias de la región |
| `summary.aws.rds.DBconnections` | **Scan and general monitoring** | Suma de las conexiones a la base de datos de las instancias disponibles |
| `summary.aws.rds.CPUUtilization`, `summary.aws.rds.CPUCreditBalance`, `summary.aws.rds.CPUCreditUsage`, `summary.aws.rds.CPUSurplusCreditBalance`, `summary.aws.rds.CPUSurplusCreditsCharged` | **Scan and general monitoring** y **Cpu performance summary** | Suma sobre las instancias disponibles dividida por el número de instancias de la región |
| `summary.aws.rds.DiskReadBytes`, `summary.aws.rds.diskWriteBytes`, `summary.aws.rds.BinLogDiskUsage` | **Scan and general monitoring** y **Disk performance summary** | Suma sobre las instancias disponibles, en `Bytes` |
| `summary.aws.rds.DiskReadOps`, `summary.aws.rds.DiskWriteOps`, `summary.aws.rds.LVMReadIOPS`, `summary.aws.rds.LVMWriteIOPS` | **Scan and general monitoring** y **IOPs performance summary** | Suma sobre las instancias disponibles |
| `summary.aws.rds.NetworkReceiveThroughput`, `summary.aws.rds.NetworkTransmitThroughput` | **Scan and general monitoring** y **Network performance summary** | Suma sobre las instancias disponibles |

**Agente de instancia**

| Módulo | Tipo | Condición | Métrica de CloudWatch |
|--------|------|-----------|-----------------------|
| `State` | `generic_data_string` | Siempre | Ninguna. Estado de la instancia según AWS |
| `Instance State (bool)` | `generic_proc` | Siempre | Ninguna. `1` cuando el estado es `available`, `0` en otro caso |
| `DatabaseConnections` | `generic_data` | Disponible, **Scan and general monitoring** | `DatabaseConnections` |
| `CPUUtilization`, `CPUCreditBalance`, `CPUCreditUsage`, `CPUSurplusCreditBalance`, `CPUSurplusCreditsCharged` | `generic_data` | Disponible, **Cpu performance summary** | La métrica del mismo nombre |
| `DiskReadBytes`, `DiskWriteBytes` | `generic_data` | Disponible, **Disk performance summary** | `ReadThroughput`, `WriteThroughput` (unidad `Bytes`) |
| `BinLogDiskUsage` | `generic_data` | Disponible, **Disk performance summary** | `BinLogDiskUsage` (unidad `Bytes`) |
| `DiskReadOps`, `DiskWriteOps` | `generic_data` | Disponible, **IOPs performance summary** | `ReadIOPS`, `WriteIOPS` |
| `LVMReadIOPS`, `LVMWriteIOPS` | `generic_data` | Disponible, **IOPs performance summary** | La métrica del mismo nombre |
| `NetworkReceiveThroughput`, `NetworkTransmitThroughput` | `generic_data` | Disponible, **Network performance summary** | La métrica del mismo nombre |

### Cómo se obtienen los valores

- Cada valor de rendimiento es la media que devuelve AWS CloudWatch, en el espacio de nombres `AWS/RDS`, con un periodo de 10 minutos para los últimos 10 minutos. Cuando CloudWatch no devuelve ningún punto de datos en esa ventana, el valor del módulo es `0`. Esto incluye las métricas que AWS no publica para una instancia concreta.
- Los módulos de rendimiento solo se crean para instancias cuyo estado es `available`.

## Operación

### Ejecución manual

El addon puede ejecutarse fuera de una tarea de Discovery. El ejecutable recibe un único parámetro, la ruta a un fichero de configuración descrito en [Fichero de configuración](#fichero-de-configuracion):

```bash
./pandora_aws_rds --conf <PATH_TO_CONFIG>
```

Imprime un resumen JSON y envía un fichero de datos por agente con el modo de transferencia configurado:

```json
{"summary": {"Total agents": 5, "Zones agents": 2, "Instances agents": 2}}
```

Cuando se producen errores, el JSON contiene además una clave `info` con los mensajes y el código de salida es `1`.

En modo de transferencia `local` los ficheros de datos se mueven a `data_dir`. En modo `tentacle`, el ejecutable `tentacle_client` debe estar disponible en el `PATH` del usuario que ejecuta el addon.

Un fichero de configuración contiene la clave de acceso de AWS codificada en `creds_b64`. Protéjalo con permisos restrictivos.

## Solución de problemas

El addon no tiene opción verbose ni de depuración. Su canal de diagnóstico es el campo `info` del resultado JSON de la ejecución, que se muestra en la información de ejecución de la tarea.

- **`Error while parsing credentials`**: la credencial no proporciona `access_key_id` y `secret_access_key`, o `creds_b64` no es JSON válido codificado en base64.
- **El árbol de instancias está vacío o le falta una región**: las regiones cuya petición `DescribeDBInstances` falla se omiten del árbol sin error. Compruebe el permiso `rds:DescribeDBInstances` de la clave y el estado de la región en AWS.
- **Aparece un agente de región pero sin agentes de instancia**: la región no tiene instancias, o falló la petición de instancias de esa región.
- **`Error while running threads: list index out of range`**: la tarea no tiene ninguna región ni instancia seleccionada. Seleccione al menos una.
- **Menos agentes de los esperados**: solo se monitorizan las regiones e instancias marcadas.
- **`Error getting metric: <metric> : ...`**: falló la petición a CloudWatch. Compruebe que la clave de acceso tiene `cloudwatch:GetMetricData` y que el reloj del servidor de Discovery es correcto; el mensaje incluye la fecha actual que ve el addon.
- **Los módulos de rendimiento valen `0`**: CloudWatch no devolvió ningún punto de datos en los últimos 10 minutos para esa instancia y métrica.
- **Una instancia no tiene módulos de rendimiento**: el estado de la instancia no es `available`, o **Scan and general monitoring** está desactivado.
- **Errores al llegar a AWS a través de un proxy**: revise **Proxy url**; solo las peticiones HTTPS se enrutan a través de él.

## Referencia

### Parámetros de la tarea

#### RDS Basic

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
| Stats agent name | `_statsAgentName_` | cadena | vacío | Opcional. Se muestra con **Add global stats agent** activado. Si está vacío, el alias del agente global es `Aws.rds` |
| Agent autodisable mode | `_agentautodisable_` | casilla | desactivada | Deshabilita el agente cuando todos sus módulos pasan a desconocido hasta que vuelvan a llegar datos |

Como **Verify proxy SSL** solo se muestra con **Use proxy**, una tarea que no usa proxy se ejecuta siempre con la validación de certificados TLS desactivada. Ejecute estas tareas únicamente desde una red de confianza.

#### RDS Instances

| Campo | Macro | Tipo | Notas |
|-------|-------|------|-------|
| RDS zones and instances | `_rdsZones_`, `_rdsInstance_` | árbol | Las regiones rellenan la lista de regiones y las instancias la lista de instancias. Seleccione al menos una |

#### Instances monitoring

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|-------------|-------|
| Scan and general monitoring | `_rdsInstanceSummary_` | casilla | desactivada | Habilita las conexiones a la base de datos y los módulos de rendimiento |
| Cpu performance summary | `_rdsCpuPerfSummary_` | casilla | desactivada | Se muestra con **Scan and general monitoring** |
| IOPs performance summary | `_rdsIopsPerfSummary_` | casilla | desactivada | Se muestra con **Scan and general monitoring** |
| Disk performance summary | `_rdsDiskPerfSummary_` | casilla | desactivada | Se muestra con **Scan and general monitoring** |
| Network performance summary | `_rdsNetworkPerfSummary_` | casilla | desactivada | Se muestra con **Scan and general monitoring** |

### Fichero de configuración

Se usa en la ejecución manual. Un `key = value` por línea. Los valores de lista son arrays JSON. Las opciones numéricas aceptan `1` para activar y `0` para desactivar; un valor que no es un número se lee como `0`.

| Clave | Por defecto | Descripción |
|-------|-------------|-------------|
| `agents_group_name` | `aws` | Grupo de los agentes generados |
| `interval` | `300` | Intervalo del agente, en segundos |
| `threads` | `1` | Número de grupos en que se reparten los destinos |
| `transfer_mode` | `local` | `local` escribe los ficheros de datos en `data_dir`; cualquier otro valor los envía con Tentacle |
| `tentacle_client` | `tentacle_client` | Ejecutable del cliente Tentacle |
| `tentacle_ip` | `127.0.0.1` | Dirección del servidor Tentacle |
| `tentacle_port` | `41121` | Puerto del servidor Tentacle |
| `tentacle_opts` | vacío | Opciones adicionales del cliente Tentacle |
| `data_dir` | `/var/spool/pandora/data_in/` | Destino de los ficheros de datos en modo `local` |
| `temporal` | `/tmp` | Directorio donde se escriben los ficheros de datos antes de enviarlos |
| `advance_monitoring` | `1` | Conexiones a la base de datos y módulos de rendimiento; necesario para las cuatro opciones siguientes |
| `cpu_summary` | `1` | Módulos de CPU |
| `iops_summary` | `1` | Módulos de IOPS |
| `disk_summary` | `1` | Módulos de disco |
| `network_summary` | `1` | Módulos de red |
| `aws_regions` | `[]` | Regiones a monitorizar |
| `aws_instances` | `[]` | Identificadores de las instancias a monitorizar |
| `stats_agent` | `1` | Agente global |
| `stats_agent_name` | vacío | Nombre del agente global; alias `Aws.rds` si está vacío |
| `agent_autodisable` | `0` | Modo autodisable |
| `use_proxy` | `0` | Usar un proxy |
| `proxy_url` | vacío | URL del proxy |
| `ssl_check` | `0` | `1` valida los certificados TLS; `0` no los valida |
| `creds_b64` | vacío | Obligatorio. Base64 del JSON `{"access_key_id": "<ACCESS_KEY_ID>", "secret_access_key": "<SECRET_ACCESS_KEY>"}` |

Ejemplo:

```ini
agents_group_name  = aws
interval           = 300
threads            = 2
transfer_mode      = tentacle
tentacle_ip        = <TENTACLE_SERVER_IP>
tentacle_port      = 41121

advance_monitoring = 1
cpu_summary        = 1
iops_summary       = 1
disk_summary       = 1
network_summary    = 1

stats_agent        = 1
stats_agent_name   = Rds

aws_regions        = ["us-east-1","eu-west-1"]
aws_instances      = ["<DB_INSTANCE_IDENTIFIER>"]

creds_b64          = <BASE64_CREDENTIALS>
```

### Identidad del addon

| Elemento | Valor |
|----------|-------|
| Nombre | Amazon RDS |
| Identificador | `pandorafms.aws.rds` |
| Versión | `1.2` |
| Tipo y sección | Discovery, `cloud` |
| Entrada del Marketplace | [pandorafms.aws.rds](https://marketplace.pandorafms.com/entries/pandorafms.aws.rds), actualizada el 2026-08-31 |
| Disponibilidad | La entrada del Marketplace indica que la descarga está limitada a usuarios con licencia |
