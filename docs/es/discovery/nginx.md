# NGINX Discovery

*Última actualización del artículo: 2026-09-01.*

## Qué monitoriza

El plugin de Discovery de NGINX automatiza la monitorización de servidores NGINX a través del endpoint del módulo `ngx_http_stub_status_module` (stub_status). Lee ese endpoint y convierte sus contadores en módulos de monitorización de Pandora FMS: conexiones activas, conexiones aceptadas y gestionadas, peticiones procesadas y conexiones en los estados de lectura, escritura y espera.

El plugin crea **un agente por cada URL de NGINX**, con un módulo por métrica disponible más un módulo de disponibilidad. Una tarea de Discovery puede apuntar a varias URL a la vez, así que una sola tarea cubre todo un conjunto de nodos NGINX.

Una extensión de consola complementaria, **NGINX Monitoring**, agrega en una única vista todos los nodos que monitoriza el plugin. Consulte [Extensión de consola NGINX Monitoring](#extension-de-consola-nginx-monitoring).

## Preparación

### Compatibilidad

| Alcance | Estado | Evidencia |
|---------|--------|-----------|
| Versión del plugin `1.0` (`pandorafms.nginx`) | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del plugin](#identidad-del-plugin) |
| NGINX exponiendo `stub_status` por HTTP plano | `Probado` | Verificado contra `nginx:alpine` |
| NGINX exponiendo `stub_status` por HTTPS con autenticación básica | `Probado` | Verificado contra `nginx:alpine` con certificado autofirmado |
| `ngx_http_stub_status_module` compilado en la build de NGINX | `Requerido` | Prerrequisito, no una declaración de compatibilidad. Consulte [Prerrequisitos](#prerrequisitos) |
| Alcance de red desde el servidor de Discovery al endpoint de estado | `Requerido` | El plugin realiza una petición HTTP por cada URL |
| Sistema operativo del host que ejecuta el plugin | `Sin validar` | No se ha registrado ningún sistema operativo de host |
| Cualquier versión o paquete de distribución concretos de NGINX | `Sin validar` | La compatibilidad se estableció contra el contrato del endpoint, no contra una matriz de versiones |

### Prerrequisitos

1. **El endpoint `stub_status` debe estar habilitado y ser accesible** desde la máquina que ejecuta el plugin. Su activación se explica en [Habilitar el endpoint de estado](#habilitar-el-endpoint-de-estado).
2. **Pandora FMS**: un servidor de Discovery para ejecutar la tarea y la consola para definirla.
3. **Credenciales**, solo cuando el endpoint esté protegido con autenticación básica HTTP.

El plugin se distribuye como un ejecutable autocontenido: la aplicación de Discovery empaquetada incluye `bin/pandora_nginx`, por lo que no hay que instalar ningún runtime adicional, ni en el servidor de Discovery ni para una ejecución manual.

### Instalar el plugin

Cargue el paquete `.disco` desde el marketplace de Pandora FMS:

[https://marketplace.pandorafms.com/](https://marketplace.pandorafms.com/)

Una vez cargado, la aplicación **NGINX** queda disponible al crear tareas de Discovery.

La extensión de consola complementaria **no** forma parte de ese paquete: se distribuye con la consola, en `pandora_console_extensions/nginx_view/`.

### Habilitar el endpoint de estado

Para que el plugin pueda obtener las estadísticas, NGINX debe exponer el endpoint `stub_status`. Se habilita editando el fichero de configuración de NGINX (por defecto en `/etc/nginx/nginx.conf` o `/etc/nginx/sites-available/default`).

> El módulo `ngx_http_stub_status_module` no está incluido en todas las builds de NGINX. Para comprobar si está disponible, ejecute `nginx -V 2>&1 | grep stub_status`. La mayoría de distribuciones Linux lo incluyen por defecto.

Elija la variante que corresponda a cómo deba protegerse el endpoint.

#### Configuración mínima (sin autenticación, sin SSL)

Añada un `location` dedicado para el estado dentro de su `server`:

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
http://<SERVER_IP>/nginx_status
```

#### Configuración con autenticación básica

Para proteger el endpoint con usuario y contraseña, defina `auth_basic` y `auth_basic_user_file` en el location de estado:

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

Genere el fichero `.htpasswd` con `htpasswd` u `openssl`:

```bash
htpasswd -c /etc/nginx/.htpasswd <USERNAME>
# o bien
echo "<USERNAME>:$(openssl passwd -apr1 <PASSWORD>)" > /etc/nginx/.htpasswd
```

La segunda forma coloca la contraseña en la línea de comandos, donde quedan expuestas en el historial del shell y en la lista de procesos del sistema operativo. Es preferible `htpasswd -c`, que la solicita de forma interactiva.

El mismo `username` y `password` deben facilitarse al plugin en los campos de la tarea, o mediante `--user` / `--password` en una ejecución manual.

#### Configuración con SSL/TLS

Para servir las estadísticas por HTTPS, configure el certificado en el `server`:

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

Genere un certificado autofirmado de prueba con:

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/certs/status.key \
  -out /etc/nginx/certs/status.crt \
  -subj "/CN=localhost"
cat /etc/nginx/certs/status.crt /etc/nginx/certs/status.key > /etc/nginx/certs/status.pem
```

La URL se indica entonces al plugin con el esquema `https://`, y **Verify SSL** decide si se valida la cadena del certificado:

- activado → para certificados válidos en producción.
- desactivado → para certificados autofirmados o entornos de prueba.

#### Configuración completa (SSL + autenticación)

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

Tras modificar la configuración de NGINX, recargue el servicio para aplicar los cambios:

```bash
sudo systemctl reload nginx
```

#### Confirmar que el endpoint responde

Antes de crear la tarea, solicite la página de estado a mano:

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

- **Active connections**: número total de conexiones activas (incluye las que están en espera).
- **accepts**: total de conexiones aceptadas desde que arrancó NGINX.
- **handled**: total de conexiones gestionadas desde que arrancó NGINX.
- **requests**: total de peticiones de cliente procesadas desde que arrancó NGINX.
- **Reading**: conexiones leyendo las cabeceras de la petición del cliente.
- **Writing**: conexiones escribiendo una respuesta al cliente o procesando una petición.
- **Waiting**: conexiones keep-alive inactivas esperando la siguiente petición.

Si esta petición falla, la tarea fallará también. Corríjalo aquí, no en la consola.

## Configurar la tarea de Discovery

Cree la tarea desde **Management → Discovery → Application → NGINX**. La consola presenta los campos en dos pasos, y todos están documentados en [Parámetros de la tarea](#parametros-de-la-tarea).

1. **NGINX Basic** — los endpoints y cómo alcanzarlos:

    - **NGINX Status URLs**: URL de los endpoints stub_status, separadas por comas o una por línea. **Cada URL genera un agente.**
    - **Username** y **Password**: solo cuando el endpoint requiera autenticación básica HTTP.
    - **Verify SSL**: valida la cadena del certificado de una URL `https://`. Desactivado por defecto.
    - **Transfer mode**, **Tentacle IP** y **Tentacle port**: cómo llegan los datos a Pandora FMS. `native` permite que el servidor de Discovery lea los datos directamente y es el valor por defecto.

    <!-- SCREENSHOT NEEDED: paso NGINX Basic del asistente mostrando el área de texto de URL, los campos de credenciales, Verify SSL y el selector de modo de transferencia, con valores de ejemplo y sin credenciales reales. -->

2. **NGINX Advanced** — ajuste opcional del resultado:

    - **Module prefix**: se antepone al nombre de cada módulo creado.
    - **Request timeout**: segundos de espera de cada petición HTTP. Por defecto `10`.
    - **Allow list** y **Deny list**: expresiones regulares para incluir o excluir módulos por nombre.

    <!-- SCREENSHOT NEEDED: paso NGINX Advanced del asistente mostrando module prefix, request timeout, allow list y deny list. -->

El grupo y el intervalo de la tarea proceden del paso genérico de definición de la tarea, y se pasan al plugin como grupo de los agentes e intervalo de los módulos.

## Verificar la primera ejecución

Fuerce la tarea desde **Management → Discovery → Task list** y compruebe el resultado en este orden.

1. **El resumen de la tarea.** Una tarea completada correctamente informa de:

    - **Total agents**: número total de agentes generados por la tarea.
    - **Total modules**: número total de módulos generados por la tarea.

    Espere un agente por cada URL introducida. Una URL que no haya podido leerse se reporta como error en la información de ejecución.

    <!-- SCREENSHOT NEEDED: resumen de ejecución de una tarea de Discovery de NGINX mostrando Total agents y Total modules. -->

2. **Los agentes.** Uno por URL, con el alias fijado al `host:puerto` del endpoint.

3. **Los módulos de cada agente.** Un endpoint accesible produce:

    | Módulo | Valor esperado |
    |--------|----------------|
    | `Status` | `1` — el endpoint respondió |
    | `Active_connections` | Conexiones activas actuales |
    | `Accepts`, `Handled`, `Requests` | Contadores acumulados; Pandora FMS deriva la tasa por segundo |
    | `Reading`, `Writing`, `Waiting` | Conexiones actuales en cada estado |

    Los nombres de módulo llevan el **Module prefix** cuando se haya definido, y las listas allow/deny pueden eliminar legítimamente cualquiera de ellos.

4. **La extensión de consola**, cuando esté instalada: el nodo debe aparecer en **Operation → NGINX Monitoring** sin configuración adicional.

Si la tarea no reporta agentes, vuelva sobre [Confirmar que el endpoint responde](#confirmar-que-el-endpoint-responde) y después sobre [Solución de problemas](#solucion-de-problemas).

## Interpretar los resultados

### Agentes y módulos generados

El plugin crea **un agente por cada URL de NGINX**. El nombre del agente es el hash MD5 del `netloc` (`host:puerto`) del endpoint, y el alias es ese mismo `netloc`, por ejemplo `nginx1.example.com`. Cuando una URL no tiene un `netloc` interpretable, se usa la URL completa.

Como la identidad procede del endpoint y no de la tarea, mover una URL de una tarea a otra sigue reportando al mismo agente y conserva su histórico.

El módulo `Status` se crea por defecto para cada agente, con valor `1` cuando el endpoint es accesible. Puede excluirse mediante las listas allow/deny como cualquier otro módulo. Cuando el endpoint no es accesible, el plugin reporta el fallo en la información de ejecución. El resto de campos se convierten en módulos `generic_data` (valores instantáneos) o `generic_data_inc` (contadores incrementales, de los que Pandora FMS deriva una tasa por segundo), con el nombre `<prefijo><NombreMétrica>`.

### Correspondencia de tipos de módulo

| Métrica | Tipo de módulo de Pandora FMS | Descripción |
| --- | --- | --- |
| Status | `generic_proc` | Estado del endpoint (1=accesible, 0=DOWN). Permite configurar alertas críticas cuando el valor es 0. |
| Active_connections | `generic_data` | Conexiones activas actuales (gauge). Incluye las conexiones en lectura, escritura y espera. |
| Accepts | `generic_data_inc` | Conexiones aceptadas acumuladas. Pandora FMS calcula automáticamente la tasa por segundo. |
| Handled | `generic_data_inc` | Conexiones gestionadas acumuladas. Pandora FMS calcula automáticamente la tasa por segundo. Si la tasa es menor que la de Accepts, NGINX está descartando conexiones. |
| Requests | `generic_data_inc` | Peticiones procesadas acumuladas. Pandora FMS calcula automáticamente la tasa por segundo (peticiones/s). |
| Reading | `generic_data` | Conexiones en estado de lectura de cabeceras (gauge). |
| Writing | `generic_data` | Conexiones en estado de escritura de respuesta (gauge). |
| Waiting | `generic_data` | Conexiones keep-alive inactivas (gauge). Un valor alto es normal cuando keep-alive está habilitado. |

### Marcadores extra_data

El plugin asigna identificadores estables en el campo `extra_data` de cada agente y módulo, con el formato `nginx:<tipo>:<identificador>`, para permitir su identificación posterior desde la consola, dashboards, extensiones o consultas SQL:

- **Agente**: `nginx:target:<url_saneada>` — identifica el destino NGINX monitorizado.
- **Módulo Status**: `nginx:metric_status:<url_saneada>`
- **Módulos de métricas**: `nginx:metric_<nombre_metrica>:<url_saneada>` — por ejemplo `nginx:metric_active_connections:...`, `nginx:metric_accepts:...`, etc.

Estos marcadores no contienen el nombre del agente ni del módulo, sino el identificador externo (la URL de destino), que es estable y significativo a nivel de dominio.

### Extensión de consola NGINX Monitoring

El plugin cuenta con una extensión de consola complementaria, `nginx_view`, que renderiza un cuadro de mando de todos los nodos NGINX que monitoriza el plugin. No la instala el paquete `.disco`: la extensión forma parte de la consola, en `pandora_console_extensions/nginx_view/`.

Una vez disponible, aparece en la consola bajo **Operation**, como **NGINX Monitoring**. Abrirla requiere el ACL **AR**.

La extensión no necesita que se le indique qué agentes leer. Los descubre a partir de los marcadores `extra_data` que escribe el plugin, seleccionando todos los módulos cuyo `extra_data` empieza por `nginx:metric_` y resolviendo los agentes que los poseen. Cualquier agente creado por el plugin aparece por tanto de forma automática, sin configuración por el lado de la extensión.

Muestra tarjetas de resumen con el número de nodos NGINX, cuántos están activos y caídos, el total de conexiones activas, el contador agregado de peticiones y las conexiones inactivas, seguidas de una tabla por nodo.

<!-- SCREENSHOT NEEDED: vista de la extensión NGINX Monitoring mostrando las tarjetas de resumen y la tabla por nodo, solo con nombres de host de laboratorio. -->

## Operación y solución de problemas

### Ejecutar el plugin fuera de Discovery

El plugin también puede ejecutarse a mano, que es la forma más rápida de confirmar un endpoint y sus credenciales antes de conectarlos a una tarea, y es además el modo en que se usa como plugin de servidor.

Tiene dos modos de entrada:

- El **modo simple** pasa los endpoints en la línea de comandos con `--urls`.
- El **modo avanzado** pasa un fichero de configuración con `--conf` más un fichero de destinos con `--targets_file`. Es el modo que usa la propia tarea de Discovery.

```bash
# Modo simple
./pandora_nginx --urls http://<TARGET_HOST_1>/nginx_status,http://<TARGET_HOST_2>/nginx_status \
    --user <USERNAME> --password <PASSWORD> --ssl false

# Modo avanzado
./pandora_nginx --conf <PATH_TO_CONFIG> --targets_file <PATH_TO_TARGETS>
```

Pasar una contraseña en la línea de comandos la expone en el historial del shell y en la lista de procesos del sistema operativo. Es preferible el fichero de configuración para todo lo que no sea una comprobación puntual.

La ejecución devuelve un resumen JSON. En modo `native` los datos recogidos se exponen en el campo `monitoring_data` de ese resumen, para que los consuma el servidor de Discovery; en modo `tentacle` el plugin genera un fichero XML por agente y lo envía al servidor de Pandora FMS.

`--as_server_plugin` sustituye el resumen JSON por un único `1` (agentes creados sin errores) o `0`, de modo que el plugin pueda conectarse como plugin de servidor.

### Diagnóstico

El plugin no tiene opción de modo detallado ni de depuración. Su único canal de diagnóstico es el resumen JSON de ejecución impreso por salida estándar, que indica el endpoint que ha fallado cuando no puede completarse una petición a `stub_status`.

### Solución de problemas

- **La tarea no crea agentes** — han fallado todas las URL. Reproduzca la petición con `curl` como en [Confirmar que el endpoint responde](#confirmar-que-el-endpoint-responde); el resumen JSON de una ejecución manual indica el endpoint que falló.
- **`stub_status` no está disponible** — el módulo no está en esta build de NGINX. Compruébelo con `nginx -V 2>&1 | grep stub_status` y use una build que lo incluya.
- **El endpoint responde a mano pero no desde la tarea** — la petición sale del servidor de Discovery, no de su equipo. Revise las reglas `allow`/`deny` del `location` de estado y la ruta de red desde ese servidor.
- **El endpoint HTTPS falla con un error de certificado** — un certificado autofirmado o emitido internamente no valida. Desactive **Verify SSL** para esa tarea, o instale la CA emisora en el servidor de Discovery.
- **`401` en un endpoint protegido** — las credenciales no coinciden con `auth_basic_user_file`. Regenere la entrada con `htpasswd` y vuelva a probar con `curl -u`.
- **El prefijo de módulos, el modo de transferencia, la dirección de tentacle o el intervalo parecen ignorados en una ejecución manual** — en modo simple (`--urls`) esos parámetros no se aplican; el plugin usa `native`, `127.0.0.1:41121` y `300` segundos. Use el fichero de configuración para cambiarlos.
- **`Handled` es sistemáticamente menor que `Accepts`** — no es un fallo del plugin: NGINX está descartando conexiones. Investigue los límites de recursos del servidor.

## Referencia

### Parámetros de la tarea

La consola presenta los campos de la tarea en dos pasos.

#### NGINX Basic

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|-------------|-------|
| NGINX Status URLs | `_nginxUrls_` | área de texto | — | Obligatorio. Separadas por comas o una por línea. Cada URL crea un agente |
| Username | `_nginxUser_` | cadena | — | Usuario de autenticación básica HTTP, opcional |
| Password | `_nginxPassword_` | contraseña | — | Contraseña de autenticación básica HTTP, opcional |
| Verify SSL | `_verifySSL_` | casilla | desactivada | Valida la cadena del certificado al usar HTTPS. Desactívelo para certificados autofirmados |
| Transfer mode | `_transferMode_` | selector | `native` | `native`: el servidor de Discovery lee directamente los datos del agente. `tentacle`: el plugin envía los datos con el cliente Tentacle |
| Tentacle IP | `_tentacleIp_` | cadena | `127.0.0.1` | Dirección del servidor Tentacle, usada en modo `tentacle` |
| Tentacle port | `_tentaclePort_` | número | `41121` | Puerto del servidor Tentacle, usado en modo `tentacle` |

#### NGINX Advanced

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|-------------|-------|
| Module prefix | `_prefixModules_` | cadena | — | Se antepone al nombre de cada módulo creado, por ejemplo `nginx_` |
| Request timeout | `_reqTimeout_` | número | `10` | Tiempo de espera de la petición HTTP en segundos |
| Allow list | `_allowList_` | cadena | — | Expresión regular; solo se incluyen los módulos cuyo nombre coincida. Vacío significa todos |
| Deny list | `_denyList_` | cadena | — | Expresión regular; se excluyen los módulos cuyo nombre coincida. Vacío significa ninguno |

El grupo y el intervalo de la tarea se toman del paso genérico de definición de la tarea y llegan al plugin como `agents_group`, `agents_group_id` e `interval`.

### Parámetros de línea de comandos

```bash
./pandora_nginx --urls <URLs> [opciones]
./pandora_nginx --conf <ruta> --targets_file <ruta>
```

| Parámetro | Descripción |
| --- | --- |
| `--urls` | URL de los endpoints stub_status de NGINX, separadas por comas. Cada URL genera un agente |
| `--user` | Usuario si el endpoint de NGINX requiere autenticación básica HTTP, opcional |
| `--password` | Contraseña si el endpoint de NGINX requiere autenticación básica HTTP, opcional |
| `--ssl` | Si se verifica o no el certificado HTTPS de la URL, opcional (por defecto true) |
| `--prefix` | Prefijo para los nombres de módulo, opcional |
| `--transfer_mode` | Modo de transferencia de datos (`native` o `tentacle`), opcional |
| `-ti`, `--tentacle_ip` | IP de tentacle, opcional (por defecto `127.0.0.1`) |
| `-tp`, `--tentacle_port` | Puerto de tentacle, opcional (por defecto `41121`) |
| `--interval` | Intervalo de monitorización en segundos, opcional (por defecto 300) |
| `--allow_list` | Expresión regular para incluir solo los módulos cuyo nombre coincida, opcional |
| `--deny_list` | Expresión regular para excluir los módulos cuyo nombre coincida, opcional |
| `--timeout` | Tiempo máximo de espera de la petición HTTP en segundos, opcional (por defecto 10) |
| `--as_server_plugin` | Devuelve un único `1` (agentes creados sin errores) o `0` en lugar del resumen JSON, opcional (por defecto false) |
| `--conf` | Ruta al fichero de configuración |
| `--targets_file` | Ruta al fichero que contiene las URL de NGINX (obligatorio al usar `--conf`) |

> En modo simple (`--urls`), los parámetros de prefijo de módulos, modo de transferencia, dirección de tentacle e intervalo listados arriba no se aplican: el plugin usa los valores por defecto (`native`, `127.0.0.1:41121`, `300` segundos). Para cambiarlos, use el fichero de configuración con `--conf`.

### Fichero de configuración

La tarea de Discovery construye este fichero a partir de sus propios campos; una ejecución manual en modo avanzado lo aporta con `--conf`.

| Clave | Descripción |
| --- | --- |
| `username` | Usuario de autenticación básica HTTP, opcional |
| `password` | Contraseña de autenticación básica HTTP, opcional |
| `verify_ssl` | Si se verifica el certificado HTTPS, opcional |
| `prefix` | Prefijo para los nombres de módulo, opcional |
| `transfer_mode` | Modo de transferencia de datos (`native` o `tentacle`), opcional |
| `tentacle_ip` | IP de tentacle, opcional |
| `tentacle_port` | Puerto de tentacle, opcional |
| `agents_group` | Nombre del grupo de agentes al que se asignan los agentes creados, opcional |
| `agents_group_id` | Identificador del grupo de agentes al que se asignan los agentes creados, opcional |
| `interval` | Intervalo de monitorización en segundos, opcional |
| `allow_list` | Expresión regular para incluir solo los módulos cuyo nombre coincida, opcional |
| `deny_list` | Expresión regular para excluir los módulos cuyo nombre coincida, opcional |
| `timeout` | Tiempo máximo de espera de la petición HTTP en segundos, opcional |

Ejemplo:

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

Fichero de destinos (`--targets_file`), una URL por línea o separadas por comas:

```
http://<TARGET_HOST_1>/nginx_status
http://<TARGET_HOST_2>/nginx_status
```

### Identidad del plugin

| Campo | Valor |
|-------|-------|
| Nombre corto de la aplicación | `pandorafms.nginx` |
| Versión del plugin | `1.0` |
| Tipo | Aplicación de Discovery (`.disco`) |
| Sección | Discovery → Applications |
| Extensión de consola | `nginx_view` (se distribuye con la consola, no con el paquete) |
