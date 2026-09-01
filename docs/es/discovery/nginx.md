# NGINX Discovery

*Última actualización del artículo: 2026-09-01.*

## Introducción

Este plugin de discovery de NGINX para Pandora FMS está diseñado para automatizar la monitorización de tus servidores NGINX, aprovechando la información que proporciona el módulo `ngx_http_stub_status_module` (stub_status). Al interactuar con dicho endpoint, el plugin puede recopilar métricas en tiempo real que son cruciales para entender el rendimiento y la salud de tu entorno NGINX, incluyendo conexiones activas, conexiones aceptadas y gestionadas, peticiones procesadas, y el estado de las conexiones en lectura, escritura y espera. Por cada URL de NGINX se creará un agente en Pandora FMS, con un módulo por cada métrica disponible.

## Matriz de compatibilidad

| **Sistemas donde se ha probado** | Contenedores NGINX `nginx:alpine` expuestos por HTTP plano y por HTTPS con autenticación básica (el entorno de pruebas del propio plugin) |
| --- | --- |
| **Sistemas donde funciona** | Sin validar. El plugin se distribuye como binario compilado que incluye sus dependencias, por lo que no necesita instalar Python en el equipo. No hay constancia de los sistemas operativos anfitriones en los que se ha ejecutado. |

## Prerrequisitos

- El plugin se distribuye como un binario compilado que ya contiene todas las dependencias necesarias para su uso, por lo que no requiere instalar Python ni librerías adicionales.
- Es necesario que el módulo `stub_status` de NGINX esté habilitado y accesible. Consulta la sección [Configuración de NGINX](#configuracion-de-nginx) para ver los pasos.

## Configuración de NGINX

Para que el plugin pueda obtener las estadísticas, NGINX debe exponer el endpoint `stub_status`. La habilitación se realiza editando el fichero de configuración de NGINX (por defecto en `/etc/nginx/nginx.conf` o `/etc/nginx/sites-available/default`).

> El módulo `ngx_http_stub_status_module` no se incluye en todas las compilaciones de NGINX. Para verificar si está disponible, ejecuta `nginx -V 2>&1 | grep stub_status`. La mayoría de las distribuciones Linux lo incluyen por defecto.

### Configuración mínima (sin autenticación, sin SSL)

Añade una `location` dedicada al estado dentro de tu `server`:

```nginx
server {
    listen 80;
    server_name _;

    location /nginx_status {
        stub_status on;
        access_log off;
        allow <PANDORA_FMS_SERVER_IP>;   # IP del servidor de Pandora FMS
        deny all;
    }
}

```

Con esta configuración el plugin consumirá la URL:

```
http://<IP_SERVIDOR>/nginx_status

```

### Configuración con autenticación básica

Para proteger el endpoint con usuario y contraseña, define `auth_basic` y `auth_basic_user_file` en la location de status:

```nginx
server {
    listen 80;
    server_name _;

    location /nginx_status {
        stub_status on;
        access_log off;
        auth_basic "NGINX Status";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }
}

```

Genera el fichero `.htpasswd` con `htpasswd` o `openssl`:

```bash
htpasswd -c /etc/nginx/.htpasswd <USERNAME>
# o bien
echo "<USERNAME>:$(openssl passwd -apr1 <PASSWORD>)" > /etc/nginx/.htpasswd

```

En el plugin se deberá facilitar ese mismo `username` y `password` mediante `--user` / `--password` (o los campos `username` / `password` del archivo de configuración).

### Configuración con SSL/TLS

Para servir las estadísticas sobre HTTPS configura el certificado en el `server`:

```nginx
server {
    listen 443 ssl;
    server_name _;

    ssl_certificate     /etc/nginx/certs/status.pem;
    ssl_certificate_key /etc/nginx/certs/status.key;

    location /nginx_status {
        stub_status on;
        access_log off;
        allow <PANDORA_FMS_SERVER_IP>;
        deny all;
    }
}

```

Genera un certificado autofirmado de pruebas con:

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/certs/status.key \
  -out /etc/nginx/certs/status.crt \
  -subj "/CN=localhost"
cat /etc/nginx/certs/status.crt /etc/nginx/certs/status.key > /etc/nginx/certs/status.pem


```

En el plugin se indicará la URL con esquema `https://` y el parámetro `--ssl` (o `verify_ssl`) según se quiera validar el certificado:

- `verify_ssl = true` → para certificados válidos en producción.
- `verify_ssl = false` → para certificados autofirmados o entornos de prueba.

### Configuración completa (SSL + autenticación)

```nginx
server {
    listen 443 ssl;
    server_name _;

    ssl_certificate     /etc/nginx/certs/status.pem;
    ssl_certificate_key /etc/nginx/certs/status.key;

    location /nginx_status {
        stub_status on;
        access_log off;
        auth_basic "NGINX Status";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }
}

server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}

```

Tras modificar la configuración de NGINX recarga el servicio para aplicar los cambios:

```bash
sudo systemctl reload nginx


```

### Verificación

Para comprobar que el endpoint responde correctamente, puedes hacer una petición manual a la página de estado:

```bash
curl -u <USERNAME>:<PASSWORD> http://<SERVER_IP>/nginx_status


```

La salida debe ser texto plano con el siguiente formato:

```
Active connections: 291
server accepts handled requests
 16630948 16630948 31070465
Reading: 6 Writing: 179 Waiting: 106

```

- **Active connections**: número total de conexiones activas (incluye las en espera).
- **accepts**: conexiones aceptadas totales desde que se inició NGINX.
- **handled**: conexiones gestionadas totales desde que se inició NGINX.
- **requests**: peticiones de cliente procesadas totales desde que se inició NGINX.
- **Reading**: conexiones leyendo cabeceras de petición del cliente.
- **Writing**: conexiones escribiendo respuesta al cliente o procesando petición.
- **Waiting**: conexiones keep-alive inactivas esperando la siguiente petición.

## Configuración en PandoraFMS

Este plugin puede integrarse con el *Discovery* de Pandora FMS.

Para ello se debe cargar el paquete ".disco" que puede descargar desde la librería de Pandora FMS:

[https://marketplace.pandorafms.com/](https://marketplace.pandorafms.com/)

Una vez cargado, se podrán monitorizar las instancias de NGINX creando tareas de *Discovery* desde la sección *Management &gt; Discovery &gt; Application &gt; NGINX*

Para cada tarea se solicitarán los siguientes datos mínimos en el paso **NGINX Basic**:

- **NGINX Status URLs:** URLs del endpoint stub_status de NGINX, separadas por comas o una por línea. Cada URL generará un agente.
- **Username:** usuario del endpoint de NGINX si requiere autenticación básica HTTP, opcional
- **Password:** contraseña del endpoint de NGINX si requiere autenticación básica HTTP, opcional
- **Verify SSL:** activo si es necesario verificar que la URL tenga certificado SSL, por defecto inactivo
- **Transfer mode:** modo de transferencia (native o tentacle), opcional
- **Tentacle IP:** ip del tentacle, opcional
- **Tentacle port:** Puerto del tentacle, opcional

En el paso **NGINX Advanced** se podrán configurar opciones adicionales:

- **Module prefix:** prefijo para añadir a todos los nombres de módulos creados, opcional
- **Request timeout:** tiempo máximo de espera para la petición HTTP en segundos, opcional (por defecto 10)
- **Allow list:** expresión regular para incluir únicamente los módulos cuyo nombre coincida, opcional
- **Deny list:** expresión regular para excluir módulos cuyo nombre coincida, opcional

Las tareas completadas con éxito tendrán un resumen de ejecución con la siguiente información:

- **Total agents** : Número total de agentes generados por la tarea.
- **Total modules:** Número total de módulos generados por la tarea.

## Agentes y módulos generados por el plugin

El plugin creará un agente por cada URL de NGINX indicada. El nombre del agente se calcula aplicando un hash MD5 sobre el `netloc` de la URL (host:port), y el alias se corresponde con dicho `netloc` (por ejemplo, `nginx1.example.com`). En cada agente se incluirán los módulos obtenidos al parsear el texto plano del endpoint stub_status de NGINX.

El módulo `Status` se crea por defecto para cada agente, con valor `1` si el endpoint es alcanzable, indicando que NGINX está funcionando. Puede excluirse mediante la allow/deny list, como cualquier otro módulo. Si el endpoint no es alcanzable, el plugin reporta el error en la información de ejecución. El resto de campos numéricos se incluyen como módulos `generic_data` (valores instantáneos) o `generic_data_inc` (contadores incrementales con cálculo de tasa por segundo), siguiendo el formato `<prefix><MetricName>`.

Los campos disponibles en el stub_status de NGINX, y que dan lugar a módulos, son:

```bash
Status: Estado del endpoint stub_status (1=UP, 0=DOWN) — siempre se monitoriza (generic_proc).
Active_connections: Conexiones activas totales, incluyendo las en espera (generic_data).
Accepts: Conexiones aceptadas acumuladas desde el inicio de NGINX (generic_data_inc, tasa por segundo).
Handled: Conexiones gestionadas acumuladas desde el inicio de NGINX (generic_data_inc, tasa por segundo).
          Si el valor es menor que Accepts, NGINX está descartando tráfico.
Requests: Peticiones de cliente procesadas acumuladas desde el inicio de NGINX (generic_data_inc, tasa por segundo).
Reading: Conexiones leyendo cabeceras de petición del cliente (generic_data).
Writing: Conexiones escribiendo respuesta al cliente o procesando petición (generic_data).
Waiting: Conexiones keep-alive inactivas esperando la siguiente petición (generic_data).


```

### Mapeo de tipos de módulo

| Métrica | Tipo de módulo Pandora FMS | Descripción |
| --- | --- | --- |
| Status | `generic_proc` | Estado del endpoint (1=reachable, 0=DOWN). Permite configurar alertas críticas cuando el valor es 0. |
| Active_connections | `generic_data` | Conexiones activas actuales (gauge). Incluye conexiones en lectura, escritura y espera. |
| Accepts | `generic_data_inc` | Conexiones aceptadas acumuladas. Pandora FMS calcula la tasa por segundo automáticamente. |
| Handled | `generic_data_inc` | Conexiones gestionadas acumuladas. Pandora FMS calcula la tasa por segundo automáticamente. Si la tasa es menor que la de Accepts, NGINX está descartando conexiones. |
| Requests | `generic_data_inc` | Peticiones procesadas acumuladas. Pandora FMS calcula la tasa por segundo automáticamente (peticiones/s). |
| Reading | `generic_data` | Conexiones en estado de lectura de cabeceras (gauge). |
| Writing | `generic_data` | Conexiones en estado de escritura de respuesta (gauge). |
| Waiting | `generic_data` | Conexiones keep-alive inactivas (gauge). Un valor alto es normal con keep-alive habilitado. |

### Marcadores extra_data

El plugin asigna identificadores estables en el campo `extra_data` de cada agente y módulo, siguiendo el formato `nginx:<kind>:<identifier>`, para permitir su identificación posterior desde la consola, dashboards, extensiones o consultas SQL:

- **Agente**: `nginx:target:<url_saneada>` — identifica el target NGINX monitorizado.
- **Módulo Status**: `nginx:metric_status:<url_saneada>`
- **Módulos de métricas**: `nginx:metric_<metric_name>:<url_saneada>` — por ejemplo `nginx:metric_active_connections:...`, `nginx:metric_accepts:...`, etc.

Estos marcadores no contienen ni el nombre del agente ni el del módulo, sino el identificador externo (la URL del target), que es estable y significativo a nivel de dominio.

## Parámetros

**Modo simple**

| Parámetro | Descripción |
| --- | --- |
| `--urls` | URLs del endpoint stub_status de NGINX, separadas por comas. Cada URL generará un agente. |
| `--user` | nombre del usuario si el endpoint de NGINX requiere autenticación básica HTTP, opcional |
| `--password` | contraseña si el endpoint de NGINX requiere autenticación básica HTTP, opcional |
| `--ssl` | para verificar si la URL tiene certificado HTTPS o no, opcional (por defecto true) |
| `--prefix` | prefijo para los nombres de los módulos, opcional |
| `--transfer_mode` | modo de transferencia de datos (native o tentacle), opcional |
| `--tentacle_ip` | ip del tentacle, opcional |
| `--tentacle_port` | puerto del tentacle, opcional |
| `--interval` | intervalo de monitorización en segundos, opcional (por defecto 300) |
| `--allow_list` | expresión regular para incluir únicamente los módulos cuyo nombre coincida, opcional |
| `--deny_list` | expresión regular para excluir módulos cuyo nombre coincida, opcional |
| `--timeout` | tiempo máximo de espera para la petición HTTP en segundos, opcional (por defecto 10) |
| `--as_server_plugin` | devuelve un único `1` (se han creado agentes sin errores) o `0` en lugar del resumen JSON, para poder usar el plugin como plugin de servidor, opcional (por defecto false) |

> Al ejecutar en modo simple con `--urls`, los parámetros de prefijo de módulos, modo de transferencia, dirección del tentacle e intervalo indicados arriba no se aplican: el plugin usa los valores por defecto (`native`, `127.0.0.1:41121`, `300` segundos). Para cambiarlos, utiliza el archivo de configuración con `--conf`.

**Modo avanzado**

| Parámetro | Descripción |
| --- | --- |
| `--conf` | ruta del archivo de configuración |
| `--targets_file` | ruta del archivo con las URLs de NGINX (obligatorio al usar --conf) |

**Archivo de configuración (--conf)**

```
username= nombre del usuario si el endpoint de NGINX requiere autenticación básica HTTP, opcional
password= contraseña si el endpoint de NGINX requiere autenticación básica HTTP, opcional
verify_ssl= para verificar si la URL tiene certificado HTTPS o no, opcional
prefix= prefijo para los nombres de los módulos, opcional
transfer_mode= modo de transferencia de datos (native o tentacle), opcional
tentacle_ip= ip del tentacle, opcional
tentacle_port= puerto del tentacle, opcional
agents_group= nombre del grupo de agentes al que se asignarán los agentes creados, opcional
agents_group_id= id del grupo de agentes al que se asignarán los agentes creados, opcional
interval= intervalo de monitorización en segundos, opcional
allow_list= expresión regular para incluir únicamente los módulos cuyo nombre coincida, opcional
deny_list= expresión regular para excluir módulos cuyo nombre coincida, opcional
timeout= tiempo máximo de espera para la petición HTTP en segundos, opcional


```

**Ejemplo**

```ini
[CONF]
username=<USERNAME>
password=<PASSWORD>
verify_ssl=false
prefix=nginx_
transfer_mode=native
tentacle_ip=127.0.0.1
tentacle_port=41121
interval=300
allow_list=
deny_list=
timeout=10


```

Archivo de targets (`--targets_file`):

```
http://<TARGET_HOST_1>/nginx_status
http://<TARGET_HOST_2>/nginx_status


```

## Ejecución manual

La ejecución devolverá una salida en formato JSON con información sobre la ejecución, y generará un fichero XML por cada agente monitorizado (en modo tentacle) que enviará al servidor de Pandora FMS por el método de transferencia indicado en la configuración. En modo `native` los datos se exponen en el campo `monitoring_data` del JSON de salida para que los consuma el servidor de Discovery.

### Formato de ejecución

El formato de la ejecución del plugin es el siguiente:

```bash
./pandora_nginx --urls <urls del endpoint de NGINX separadas por comas> --user <usuario> --password <contraseña> --ssl <true|false> --prefix <prefijo> --transfer_mode <native|tentacle> --tentacle_ip <ip del tentacle> --tentacle_port <puerto del tentacle> --interval <intervalo> --allow_list <regex> --deny_list <regex> --timeout <segundos> --as_server_plugin <true|false> --conf <ruta al fichero de configuración> --targets_file <ruta al fichero de URLs>


```

#### Ejemplos

para ejecutar el modo simple

```bash
./pandora_nginx --urls http://<TARGET_HOST_1>/nginx_status,http://<TARGET_HOST_2>/nginx_status --user <USERNAME> --password <PASSWORD> --ssl false


```

para ejecutar el modo avanzado

```bash
./pandora_nginx --conf <PATH_TO_CONFIG> --targets_file <PATH_TO_TARGETS>


```

#### Modo verbose

El plugin no dispone de ningún parámetro de verbose o depuración. Su único canal de diagnóstico es el resumen de ejecución en formato JSON que imprime por la salida estándar, donde se indica el endpoint que ha fallado cuando no se puede completar una petición a `stub_status`.

## Extensión de consola

El plugin se acompaña de una extensión de consola, `nginx_view`, que muestra un cuadro de mando con todos
los nodos NGINX monitorizados por el plugin. No se instala con el paquete `.disco`: la extensión forma
parte de la consola, en `pandora_console_extensions/nginx_view/`.

Una vez disponible, aparece en la consola dentro de **Operation**, como **NGINX Monitoring**. Para verla
hacen falta permisos de lectura (`AR`) sobre los agentes.

A la extensión no hay que indicarle qué agentes debe leer. Los descubre consultando los marcadores
`extra_data` que escribe el plugin: selecciona todos los módulos cuyo `extra_data` empieza por
`nginx:metric_` y resuelve los agentes a los que pertenecen. Por tanto, cualquier agente creado por el
plugin aparece automáticamente, sin configurar nada en la extensión.

Muestra tarjetas de resumen con el número de nodos NGINX, cuántos están activos y caídos, el total de
conexiones activas, el contador agregado de peticiones y las conexiones inactivas, seguidas de una tabla por nodo.

<!-- SCREENSHOT NEEDED: el cuadro de mando de la extensión NGINX Monitoring, con las tarjetas de resumen y la tabla de nodos, con al menos dos nodos monitorizados -->