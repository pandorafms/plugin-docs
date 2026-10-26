# Amazon S3 Discovery

*Última actualización del artículo: 2026-10-26.*

## Qué monitoriza

El addon de Discovery de Amazon S3 monitoriza buckets de S3 de Amazon Web Services. Consulta las API de AWS y convierte el resultado en agentes y módulos de Pandora FMS: el número de buckets por región y, de cada bucket, su número de objetos y su tamaño.

Una tarea de Discovery genera dos tipos de agentes:

- **Un agente global de estadísticas** (opcional) con el número de buckets monitorizados.
- **Un agente por cada región monitorizada**, con un módulo de número de objetos y otro de tamaño por cada bucket monitorizado.

Una región se puede seleccionar completa, y entonces se monitoriza cada bucket que contiene, incluidos los que se creen más adelante. También se pueden monitorizar buckets individuales sin seleccionar su región (consulte [Fichero de configuración](#fichero-de-configuracion)).

## Preparación

### Compatibilidad

| Alcance | Estado | Evidencia |
|---------|--------|-----------|
| Addon `pandorafms.aws.s3`, versión `1.0` | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del addon](#identidad-del-addon) |
| Acceso de red desde el servidor de Discovery a las API de AWS | `Requerido` | El addon llama a la API de AWS S3 |
| Clave de acceso de AWS con los permisos de [Permisos de AWS](#permisos-de-aws) | `Requerido` | Prerrequisito, no una declaración de compatibilidad |
| Sistema operativo del servidor de Discovery | `Sin validar` | No se ha registrado ningún sistema operativo para esta versión |
| Versiones concretas de Pandora FMS | `Sin validar` | No se ha registrado una matriz de versiones para este addon |

### Prerrequisitos

1. **Conectividad** desde el servidor de Discovery a las API de AWS, de forma directa o a través de un proxy HTTPS.
2. **Una clave de acceso de AWS** (ID de clave de acceso y clave de acceso secreta) con los permisos descritos a continuación, registrada en el almacén de credenciales de Pandora FMS como credencial de AWS.
3. **Pandora FMS**: un servidor de Discovery para ejecutar la tarea y la consola para definirla.

El addon incluye sus propios ejecutables, `bin/pandora_aws_s3` y `bin/aws_s3`, por lo que no hay que instalar nada más en el servidor de Discovery para ejecutar una tarea.

### Permisos de AWS

El addon realiza únicamente peticiones de lectura:

| Acción de AWS | Uso |
|---------------|-----|
| `s3:ListAllMyBuckets` | Listar los buckets de la cuenta |
| `s3:GetBucketLocation` | Obtener la región de cada bucket |
| `s3:ListBucket` | Listar los objetos de un bucket para contarlos y sumar su tamaño |

Una política IAM que concede todas ellas:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListAllMyBuckets",
        "s3:GetBucketLocation",
        "s3:ListBucket"
      ],
      "Resource": "*"
    }
  ]
}
```

Asigne la política a un usuario IAM dedicado creado para Pandora FMS y genere una clave de acceso para él.

La credencial almacenada en Pandora FMS debe proporcionar las claves `access_key_id` y `secret_access_key`; el addon falla con `Error while parsing credentials` cuando falta alguna.

### Instalar el addon

Descargue el paquete `.disco` desde la entrada del Marketplace de Pandora FMS, cuya descarga está limitada a usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.aws.s3](https://marketplace.pandorafms.com/entries/pandorafms.aws.s3)

Cárguelo en Pandora FMS. Una vez cargado, **Amazon S3** estará disponible en la sección **Cloud** al crear tareas de Discovery.

## Configurar la tarea de Discovery

Cree la tarea desde las aplicaciones cloud de Discovery y elija **Amazon S3**. La consola presenta los campos en tres pasos; todos los campos se documentan en [Parámetros de la tarea](#parametros-de-la-tarea).

1. **S3 Basic** — credenciales, ejecución y opciones de agente:

    - **AWS Credentials**: la credencial de AWS registrada en el almacén de credenciales.
    - **Max threads**: número de grupos en los que se dividen las regiones monitorizadas.
    - **Use proxy**, **Proxy url** y **Verify proxy SSL**: enrutan las peticiones a AWS a través de un proxy HTTPS.
    - **Tentacle IP**, **Tentacle port** y **Tentacle extra options**: dónde y cómo se envían los datos de los agentes generados. Rara vez hay que cambiarlos.
    - **Add global stats agent** y **Stats agent name**: crean el agente global y, opcionalmente, le dan nombre.

    <!-- SCREENSHOT NEEDED: paso S3 Basic del asistente con credenciales, Max threads, proxy, Tentacle y agente de estadísticas, sin credenciales ni direcciones reales. -->

2. **S3 Buckets** — un árbol de regiones de S3 leído de su cuenta de AWS con la credencial seleccionada. Marque una región para monitorizar todos los buckets que contiene.

    ![Paso S3 Buckets de la tarea de Amazon S3 con el árbol de regiones de S3](../assets/images/discovery/amazon-s3/amazon-s3-task-s3-buckets-region-tree.png)

3. **Bucket monitoring** — las métricas recopiladas:

    - **S3 Monitoring**: habilita los módulos de bucket siguientes.
    - **Monitor bucket size** y **Monitor bucket total items**: solo se muestran con **S3 Monitoring** activado.

    ![Paso Bucket monitoring con S3 Monitoring, Monitor bucket size y Monitor bucket total items activados](../assets/images/discovery/amazon-s3/amazon-s3-task-bucket-monitoring.png)

El grupo y el intervalo de la tarea proceden del paso genérico de definición de la tarea y se aplican a los agentes que la tarea crea.

## Verificar la primera ejecución

Fuerce la tarea desde la lista de tareas de Discovery y compruebe el resultado en este orden.

1. **El resumen de la tarea.** Una tarea que finaliza correctamente informa de:

    - **Total buckets**: buckets monitorizados.
    - **Total regions**: regiones con buckets monitorizados o seleccionadas completas.

    Una tarea que no finaliza correctamente registra los errores en su información de ejecución.

    ![Resumen de ejecución de una tarea de Amazon S3 con Total regions y Total buckets](../assets/images/discovery/amazon-s3/amazon-s3-task-execution-summary.png)

2. **Los agentes.** Uno por cada región seleccionada y, si está activado, el agente global.

3. **Los módulos.** Cada agente de región tiene, por cada bucket monitorizado, `bucket.items <bucket>` y `bucket.size <bucket>`; consulte [Interpretar los resultados](#interpretar-los-resultados).

## Interpretar los resultados

### Agentes generados

| Agente | Alias | Padre | Notas |
|--------|-------|-------|-------|
| Agente global | El **Stats agent name**, o `Aws` si está vacío | Ninguno | Solo se crea con **Add global stats agent** activado |
| Agente de región | El nombre de la región, por ejemplo `eu-west-1` | El agente global solo cuando se indicó un **Stats agent name** | Uno por región seleccionada y por región que contiene un bucket seleccionado individualmente |

Los buckets no tienen agente propio: se reportan como módulos del agente de su región.

La identidad del agente de región no depende de la tarea: la definen la clave de acceso y la región. Mover una región entre tareas que usan la misma clave de acceso sigue reportando al mismo agente y conserva su histórico.

Todos los agentes informan `Aws` como nombre de sistema operativo. Los agentes de región informan `ec2` como versión del sistema operativo.

### Módulos por agente

**Agente global**

| Módulo | Tipo | Descripción |
|--------|------|-------------|
| `AWS S3 Buckets count` | `generic_data` | Buckets encontrados en las regiones y buckets seleccionados |

**Agente de región**

| Módulo | Tipo | Condición | Descripción |
|--------|------|-----------|-------------|
| `summary.Aws.ec2.buckets` | `generic_data` | Región seleccionada completa | Buckets de la región |
| `bucket.items <bucket>` | `generic_data` | **S3 Monitoring** y **Monitor bucket total items** | Número de objetos del bucket |
| `bucket.size <bucket>` | `generic_data` | **S3 Monitoring** y **Monitor bucket size** | Tamaño del bucket, en `GB`, con ocho decimales |

Un agente de región solo se crea si tiene al menos un módulo. Una región seleccionada completa siempre tiene `summary.Aws.ec2.buckets`.

## Operación

### Ejecución manual

El addon se puede ejecutar fuera de una tarea de Discovery. El ejecutable recibe un único parámetro, la ruta a un fichero de configuración descrito en [Fichero de configuración](#fichero-de-configuracion):

```bash
./pandora_aws_s3 --conf <PATH_TO_CONFIG>
```

Imprime un resumen JSON y envía un fichero de datos por agente con el modo de transferencia configurado:

```json
{"summary": {"Total buckets": 32, "Total regions": 7}}
```

Cuando se producen errores, el JSON contiene además una clave `info` con los mensajes y el código de salida es `1`.

En modo de transferencia `local` los ficheros de datos se mueven a `data_dir`. En modo `tentacle` el ejecutable `tentacle_client` debe estar disponible en el `PATH` del usuario que ejecuta el addon.

Un fichero de configuración contiene la clave de acceso de AWS codificada en `creds_b64`. Protéjalo con permisos restrictivos.

## Solución de problemas

El addon no tiene opción de modo detallado ni de depuración. Su canal de diagnóstico es el campo `info` del resultado JSON de la ejecución, que se muestra en la información de ejecución de la tarea.

- **`Error while parsing credentials`**: la credencial no proporciona `access_key_id` y `secret_access_key`, o `creds_b64` no es JSON válido codificado en base64.
- **`Error while reading configuration file`**: no se puede leer el fichero pasado a `--conf`.
- **`Error while parsing configuration zones or buckets`**: `aws_regions` o `aws_buckets` no es un array JSON válido.
- **Menos agentes de los esperados**: solo se monitorizan las regiones y buckets que seleccionó. Una región seleccionada sin buckets sigue generando su agente de región.
- **Sin módulos de bucket**: **S3 Monitoring** está desactivado, o lo están a la vez **Monitor bucket size** y **Monitor bucket total items**.
- **Errores de acceso al listar buckets u objetos**: compruebe que la clave de acceso tiene los tres permisos de [Permisos de AWS](#permisos-de-aws). El mensaje incluye el error devuelto por AWS.
- **Errores al llegar a AWS a través de un proxy**: revise **Proxy url**; solo las peticiones HTTPS se enrutan por él.
- **Errores de Tentacle**: el mensaje se registra en `info` con el prefijo `Tentacle error:`. Revise **Tentacle IP** y **Tentacle port**.

## Referencia

### Parámetros de la tarea

#### S3 Basic

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|-------------|-------|
| AWS Credentials | `_credentials_` | selector de credencial (AWS) | — | Obligatorio. Credencial registrada en el almacén de credenciales |
| Max threads | `_threads_` | número | `1` | Opcional. Las regiones se reparten en grupos, nunca más grupos que regiones |
| Use proxy | `_useProxy_` | casilla | desactivada | Enruta las peticiones a AWS a través de un proxy |
| Proxy url | `_proxyUrl_` | cadena | — | Opcional. Se muestra con **Use proxy** activado. Se aplica a peticiones HTTPS |
| Verify proxy SSL | `_sslCheck_` | casilla | desactivada | Se muestra con **Use proxy** activado. Desactivada, el addon no valida los certificados TLS en sus conexiones a AWS |
| Tentacle IP | `_tentacleIP_` | cadena | `127.0.0.1` | Servidor que recibe los datos de los agentes |
| Tentacle port | `_tentaclePort_` | número | `41121` | Puerto de Tentacle |
| Tentacle extra options | `_tentacleExtraOpt_` | cadena | — | Opcional. Opciones adicionales del cliente Tentacle |
| Add global stats agent | `_statsAgent_` | casilla | activada | Crea el agente global |
| Stats agent name | `_statsAgentName_` | cadena | `Aws` | Opcional. Se muestra con **Add global stats agent** activado |

Como **Verify proxy SSL** solo se muestra con **Use proxy**, una tarea que no usa proxy se ejecuta siempre con la validación de certificados TLS desactivada. Ejecute estas tareas únicamente desde una red de confianza.

#### S3 Buckets

| Campo | Macro | Tipo | Notas |
|-------|-------|------|-------|
| S3 zones and buckets | `_s3Zone_` | árbol | Regiones seleccionadas. Opcional |

#### Bucket monitoring

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|-------------|-------|
| S3 Monitoring | `_s3Monitoring_` | casilla | activada | Habilita los módulos de bucket |
| Monitor bucket size | `_s3Size_` | casilla | activada | Se muestra con **S3 Monitoring** |
| Monitor bucket total items | `_s3Items_` | casilla | activada | Se muestra con **S3 Monitoring** |

### Fichero de configuración

Se usa en la ejecución manual. Un `clave = valor` por línea. Los valores de lista son arrays JSON. Las opciones numéricas aceptan `1` para activar y `0` para desactivar; un valor que no sea numérico se interpreta como `0`.

| Clave | Por defecto | Descripción |
|-------|-------------|-------------|
| `agents_group_name` | `aws` | Grupo de los agentes generados |
| `interval` | `300` | Intervalo de los agentes, en segundos |
| `threads` | `1` | Número de grupos en los que se reparten las regiones |
| `transfer_mode` | `local` | `local` escribe los ficheros de datos en `data_dir`; cualquier otro valor los envía con Tentacle |
| `tentacle_client` | `tentacle_client` | Ejecutable del cliente Tentacle |
| `tentacle_ip` | `127.0.0.1` | Dirección del servidor Tentacle |
| `tentacle_port` | `41121` | Puerto del servidor Tentacle |
| `tentacle_opts` | vacío | Opciones adicionales del cliente Tentacle |
| `data_dir` | `/var/spool/pandora/data_in/` | Destino de los ficheros de datos en modo `local` |
| `temporal` | `/tmp` | Directorio donde se escriben los ficheros de datos antes de enviarlos |
| `s3_monitoring` | `1` | Módulos de bucket; necesario para las dos opciones siguientes |
| `size_monitoring` | `1` | Módulos de tamaño de bucket |
| `items_monitoring` | `1` | Módulos de número de objetos de bucket |
| `aws_regions` | `[]` | Regiones a monitorizar; se monitoriza cada bucket de una región indicada |
| `aws_buckets` | `[]` | Nombres de los buckets a monitorizar |
| `stats_agent` | `1` | Agente global |
| `stats_agent_name` | vacío | Nombre del agente global; alias `Aws` si está vacío |
| `use_proxy` | `0` | Usar un proxy |
| `proxy_url` | vacío | URL del proxy |
| `ssl_check` | `0` | `1` valida los certificados TLS; `0` no |
| `creds_b64` | vacío | Obligatorio. Base64 del JSON `{"access_key_id": "<ACCESS_KEY_ID>", "secret_access_key": "<SECRET_ACCESS_KEY>"}` |

Ejemplo:

```ini
agents_group_name  = Aws
interval           = 300
threads            = 4
transfer_mode      = tentacle
tentacle_ip        = <TENTACLE_SERVER_IP>
tentacle_port      = 41121

s3_monitoring      = 1
size_monitoring    = 1
items_monitoring   = 1

stats_agent        = 1
stats_agent_name   = AwsCloud

aws_regions        = ["us-east-1","eu-west-1"]
aws_buckets        = ["<BUCKET_NAME>"]

creds_b64          = <BASE64_CREDENTIALS>
```

### Identidad del addon

| Elemento | Valor |
|----------|-------|
| Nombre | Amazon S3 |
| Identificador | `pandorafms.aws.s3` |
| Versión | `1.0` |
| Tipo y sección | Discovery, `cloud` |
| Entrada del Marketplace | [pandorafms.aws.s3](https://marketplace.pandorafms.com/entries/pandorafms.aws.s3), actualizada 2025-06-01 |
| Disponibilidad | La entrada del Marketplace indica que la descarga está limitada a usuarios con licencia |
