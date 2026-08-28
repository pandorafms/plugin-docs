# Apache Discovery

## Introducción

Este plugin de discovery de Apache (versión 1.5) para Pandora FMS está diseñado para automatizar la monitorización de instancias de Apache HTTP Server, aprovechando la información que proporciona `mod_status`. Al interactuar con la página de estado del servidor (`server-status`), el plugin recopila métricas en tiempo real que son cruciales para entender el rendimiento y la salud de tu entorno Apache. El plugin crea un agente por instancia de Apache configurada, con un módulo por cada métrica disponible más un módulo fijo de conexión/disponibilidad.

## Matriz de compatibilidad

| **Sistemas donde se ha probado** | Un contenedor `httpd:alpine` que expone `server-status` por HTTP simple (el propio entorno de pruebas del plugin) |
| --- | --- |
| **Sistemas donde funciona** | Cualquier sistema Linux compatible con Pandora FMS. El plugin se distribuye como binario compilado que incluye sus dependencias, por lo que no requiere Python instalado en el host. No hay registro de los sistemas operativos concretos en los que se ha ejecutado. |

## Prerrequisitos

- El plugin es un compilado que contiene todas las dependencias necesarias para su uso, por lo que no requiere instalar Python ni librerías adicionales.
- El módulo `mod_status` de Apache debe estar habilitado y la ruta `server-status` accesible. Consulta la sección [Configuración de Apache](#configuracion-de-apache) para los pasos.

## Configuración de Apache

Para que el plugin pueda obtener las estadísticas, Apache debe exponer el endpoint `server-status` a través de `mod_status`. Actívalo editando la configuración de Apache (por ejemplo, en un archivo incluido desde `httpd.conf`):

```apache
LogFormat "%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-agent}i\"" combined-status

<Location "/server-status">
    SetHandler server-status
    Require all granted
</Location>

SetEnvIf Request_URI "^/server-status" log_combined_status
CustomLog /proc/self/fd/1 combined-status env=log_combined_status
```

En producción, restringe el acceso al host de confianza que ejecuta el plugin en lugar de `Require all granted`, por ejemplo `Require ip 192.168.1.50`.

Tras modificar la configuración de Apache, recarga el servicio para aplicar los cambios:

```bash
sudo systemctl reload apache2
```

### Verificación

Para verificar que el endpoint responde correctamente, haz una petición manual a la página de estado con la cadena de consulta `?auto`, que devuelve el formato `clave: valor` que interpreta el plugin:

```bash
curl http://192.168.0.1/server-status?auto
```

La salida debe ser texto plano con formato `Clave: valor` por línea, por ejemplo:

```
Total Accesses: 14733
Total kBytes: 2461799
CPULoad: .0828951
Uptime: 11979
ReqPerSec: 1.2299
BytesPerSec: 210442
BytesPerReq: 171104
BusyWorkers: 6
IdleWorkers: 35
```

El conjunto exacto de campos presentes depende de la versión de Apache, el MPM activo y qué módulos opcionales (como `mod_cache`) estén compilados.

## Parámetros

**Modo simple**

| Parámetro | Descripción |
| --- | --- |
| `--urls` | URL(s) del endpoint `server-status` de Apache, separadas por comas o saltos de línea. Cada URL genera un agente, salvo que se indique `agent_name`. |
| `--user` | nombre de usuario, si el servidor de Apache lo requiere, opcional |
| `--password` | contraseña, si el servidor de Apache lo requiere, opcional |
| `--ssl` | si se debe exigir y verificar el certificado HTTPS de la URL, opcional |
| `--transfer_mode` | modo de transferencia de datos, opcional |
| `--tentacle_ip` | IP del tentacle, opcional |
| `--tentacle_port` | puerto del tentacle, opcional |
| `--user_agent` | encabezado User-Agent personalizado que se envía a Apache, opcional |
| `-in` / `--interval` | intervalo de monitorización en segundos, opcional |
| `--as_server_plugin` | cuando es `true`, imprime un único `1` (los agentes se crearon sin errores) o `0` en lugar del resumen JSON de Discovery, para poder usar el plugin como plugin de servidor normal, opcional (por defecto `false`) |

**Modo avanzado**

| Parámetro | Descripción |
| --- | --- |
| `--conf` | ruta a un archivo de configuración con un único bloque `[CONF]`, equivalente al modo simple |
| `--string_conf` | ruta a un archivo de configuración con uno o varios bloques con nombre (`[nombre_bloque]`), cada uno describiendo un objetivo Apache distinto |

**Archivo de configuración (bloque `--conf` / `--string_conf`)**

```
urls= URL(s) de server-status de Apache
agent_name= nombre específico del agente, opcional
module_prefix= prefijo añadido a cada nombre de módulo, opcional
username= nombre de usuario, si el servidor de Apache lo requiere, opcional
password= contraseña, si el servidor de Apache lo requiere, opcional
verify_ssl= si se debe exigir y verificar el certificado HTTPS, opcional
transfer_mode= modo de transferencia de datos, opcional
tentacle_ip= IP del tentacle, opcional
tentacle_port= puerto del tentacle, opcional
interval= intervalo de monitorización en segundos, opcional
user_agent= encabezado User-Agent personalizado que se envía a Apache, opcional
module_group= grupo de módulos para los módulos creados, opcional
```

**Ejemplo**

```bash
urls=https://192.168.0.1/example
agent_name=example
module_prefix=apache
username=admin
password=12345
verify_ssl=true
transfer_mode=tentacle
tentacle_ip=127.0.0.1
tentacle_port=41121
user_agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36
```

Los archivos `--string_conf` pueden contener varios bloques con nombre, cada uno convertido en un objetivo Apache independiente con su propio agente:

```ini
[conf1]
urls=http://192.168.0.1/example
agent_name=local
module_prefix=apache
username=admin
password=12345
verify_ssl=true
tentacle_ip=127.0.0.1
tentacle_port=41121
```

## Ejecución manual

La ejecución devuelve una salida en formato JSON con información sobre la ejecución, y genera un fichero XML por cada agente monitorizado, que se envía al servidor de Pandora FMS por el método de transferencia indicado en la configuración.

### Formato de ejecución

El formato de ejecución del plugin es el siguiente:

```bash
./pandora_apache --urls <URL(s) de server-status de Apache> --user <nombre de usuario> --password <contraseña> --ssl <true|false> --transfer_mode <modo de transferencia> --tentacle_ip <IP del tentacle> --tentacle_port <puerto del tentacle> --user_agent <User-Agent> --interval <segundos> --conf <ruta al fichero de configuración> --string_conf <ruta al fichero de configuración con bloques con nombre> --as_server_plugin <true|false>
```

#### Ejemplos

para ejecutar en modo simple

```bash
./pandora_apache --urls http://192.168.0.1/server --ssl false --transfer_mode tentacle --tentacle_ip 127.0.0.1 --tentacle_port 41121
```

para ejecutar en modo avanzado

```bash
./pandora_apache --urls http://192.168.0.1/server --ssl false --transfer_mode tentacle --tentacle_ip 127.0.0.1 --tentacle_port 41121 --conf /file/file.conf
```

#### Modo verbose

El plugin no dispone de opción de verbose o depuración. Su único canal de diagnóstico es el texto informativo incluido en la salida JSON/Discovery, que reporta errores de petición y, cuando se encuentran menos métricas de las esperadas para un objetivo, cuáles faltan.

## Configuración en PandoraFMS

Este plugin puede integrarse con el *Discovery* de Pandora FMS.

Para ello se debe cargar el paquete ".disco" que puede descargarse desde la librería de Pandora FMS:

[https://marketplace.pandorafms.com/](https://marketplace.pandorafms.com/)

Una vez cargado, se pueden monitorizar instancias de Apache creando tareas de *Discovery* desde la sección *Management &gt; Discovery &gt; Application &gt; Apache*.

Para cada tarea se solicitan los siguientes datos mínimos en el paso **Apache Basic**:

- **Apache urls:** URL(s) del server-status de Apache
- **User:** usuario del servidor, si es requerido, opcional
- **Password:** contraseña del servidor, si es requerida, opcional
- **Verify SSL:** activo si es necesario verificar el certificado SSL de la URL, activo por defecto
- **Tentacle Mode:** modo de transferencia, opcional
- **Tentacle IP:** IP del tentacle, opcional
- **Tentacle port:** puerto del tentacle, opcional
- **Module group:** selector con los grupos de módulos disponibles

![Paso Apache Basic de la tarea de Discovery](../assets/images/discovery/apache-discovery/wizard-basic.png)

En el paso **Apache Detailed** se ofrece un área de texto para añadir la configuración de cada bloque de Apache que se quiera monitorizar:

- **Block:** nombre del bloque, por ejemplo `[conf]`, requerido.
- **Apache urls:** URL del server-status de Apache.
- **Agent name:** nombre específico para el agente, opcional.
- **Module prefix:** prefijo para cada módulo, opcional.
- **User:** usuario del servidor, si es requerido, opcional.
- **Password:** contraseña del servidor, si es requerida, opcional.
- **Verify SSL:** activo si es necesario verificar el certificado SSL de la URL, activo por defecto.
- **User_agent:** encabezado User-Agent personalizado que se envía a Apache, opcional.
- **Tentacle Mode:** modo de transferencia, opcional.
- **Tentacle IP:** IP del tentacle, opcional.
- **Tentacle port:** puerto del tentacle, opcional.

También hay un campo a nivel de tarea para establecer un User-Agent personalizado.

![Paso Apache Detailed de la tarea de Discovery](../assets/images/discovery/apache-discovery/wizard-advanced.png)

Las tareas completadas con éxito muestran un resumen de ejecución con la siguiente información:

- **Total agents:** número total de agentes generados por la tarea.
- **Total modules:** número total de módulos generados por la tarea.

![Resumen de ejecución de la tarea de Discovery](../assets/images/discovery/apache-discovery/task-summary.png)

## Agentes y módulos generados por el plugin

El plugin crea un agente por instancia. En modo simple, el nombre del agente se toma de la URL. En modo avanzado, se crea un agente por cada bloque enviado, nombrado según el campo **agent name**; si no se especifica, el nombre se toma de la URL. Cada agente incluye siempre un módulo **Apache Connection** (`generic_proc`), que refleja si el endpoint `server-status` respondió: valor `1` si respondió, `0` si no se pudo alcanzar, con el error descrito en la descripción del módulo en caso de fallo. Este módulo de conexión se crea incluso cuando la petición falla, de modo que la disponibilidad se monitoriza independientemente del resto de métricas.

El resto de módulos depende de la configuración y la versión del servidor Apache: una instalación reciente de Apache con todos los módulos relevantes activos expone todas las métricas. Se crean como `generic_data` (valores numéricos) o `generic_data_string` (valores no numéricos) según el tipo del valor interpretado:

| Módulo | Descripción |
| --- | --- |
| ServerVersion | La versión del servicio Apache (p. ej., Apache/2.4.62) |
| ServerMPM | El módulo de multiprocesamiento (MPM) que Apache utiliza actualmente (p. ej., event, prefork, worker) |
| ServerBuilt | La fecha y hora de compilación del binario del servidor Apache |
| ParentServerConfigGeneration | La generación de la configuración del proceso Apache principal. Se incrementa con cada reinicio elegante |
| ParentServerMPMGeneration | La generación del MPM del proceso Apache principal |
| ServerUptimeSeconds | El tiempo de actividad del servicio expresado en segundos |
| Load1 | El promedio de carga del sistema durante el último minuto |
| Load5 | El promedio de carga del sistema durante los últimos 5 minutos |
| Load15 | El promedio de carga del sistema durante los últimos 15 minutos |
| Total Accesses | El número total de solicitudes de cliente recibidas por el servidor desde su último inicio/reinicio |
| Total kBytes | La cantidad total de kilobytes de datos servidos por el servidor Apache desde su último inicio/reinicio |
| Total Duration | El tiempo acumulado dedicado al procesamiento de todas las solicitudes desde que se inició el servidor (en microsegundos o milisegundos, según la versión y configuración de Apache) |
| CPUUser | Tiempo de CPU utilizado por los procesos Apache en modo de usuario desde el inicio del servidor, expresado como porcentaje |
| CPUSystem | Tiempo de CPU utilizado por los procesos Apache en modo de sistema (kernel) desde el inicio del servidor, expresado como porcentaje |
| CPUChildrenUser | Tiempo de CPU utilizado por los procesos secundarios de Apache en modo de usuario |
| CPUChildrenSystem | Tiempo de CPU utilizado por los procesos secundarios de Apache en modo de sistema (kernel) |
| CPULoad | Porcentaje de carga de CPU total consumida por todos los procesos Apache combinados desde el inicio del servidor |
| Uptime | Representación legible del tiempo de actividad del servidor (p. ej., "2 días, 4 horas y 40 minutos"), derivada de ServerUptimeSeconds |
| ReqPerSec | Número promedio de solicitudes atendidas por segundo desde el inicio/reinicio del servidor. El plugin no lo utiliza, ya que cuenta el promedio desde el último inicio de Apache |
| BytesPerSec | Promedio de bytes servidos por segundo desde el inicio/reinicio del servidor. El plugin no lo utiliza, ya que cuenta el promedio desde el último inicio de Apache |
| BytesPerReq | Promedio de bytes servidos por solicitud desde el inicio/reinicio del servidor |
| DurationPerReq | Tiempo promedio de procesamiento de cada solicitud desde el inicio/reinicio del servidor (en milisegundos o microsegundos) |
| BusyWorkers | Número total de subprocesos/procesos de trabajo actualmente ocupados gestionando solicitudes |
| GracefulWorkers | Número de procesos de trabajo en estado de apagado elegante |
| IdleWorkers | Número total de subprocesos/procesos de trabajo actualmente inactivos y listos para gestionar nuevas solicitudes |
| Processes | Número de procesos Apache activos (no subprocesos) ejecutándose actualmente |
| Stopping | Número de procesos de trabajo en estado de detención |
| ConnsTotal | Número total de conexiones al servidor Apache |
| ConnsAsyncWriting | Número de conexiones asíncronas en estado de escritura (aplicable solo al MPM event) |
| ConnsAsyncKeepAlive | Número de conexiones asíncronas en estado de mantenimiento activo (aplicable solo al MPM event) |
| ConnsAsyncClosing | Número de conexiones asíncronas en estado de cierre (aplicable solo al MPM event) |
| CacheType | Tipo de mecanismo de caché utilizado por Apache (p. ej., SHMCB para memoria compartida) |
| CacheSharedMemory | Cantidad total de memoria compartida asignada a la caché |
| CacheCurrentEntries | Número actual de entradas almacenadas en la caché |
| CacheSubcaches | Número de subcachés dentro de la caché principal |
| CacheIndexesPerSubcaches | Número de entradas de índice por subcaché |
| CacheIndexUsage | Porcentaje del espacio de índice de la caché actualmente en uso |
| CacheUsage | Porcentaje total de la memoria de caché actualmente en uso |
| CacheStoreCount | Número total de veces que un elemento se ha almacenado correctamente en la caché |
| CacheReplaceCount | Número total de veces que se ha reemplazado una entrada de caché existente |
| CacheExpireCount | Número total de veces que una entrada de caché ha expirado |
| CacheDiscardCount | Número total de veces que una entrada de caché ha sido descartada |
| CacheRetrieveHitCount | Número total de veces que un elemento solicitado se encontró en la caché (acierto) |
| CacheRetrieveMissCount | Número total de veces que un elemento solicitado no se encontró en la caché (fallo) |
| CacheRemoveHitCount | Número total de veces que un elemento se eliminó correctamente de la caché al encontrarlo |
| CacheRemoveMissCount | Número total de veces que se intentó eliminar un elemento de la caché pero no se encontró |

![Módulos generados para un agente Apache](../assets/images/discovery/apache-discovery/module-list.png)
