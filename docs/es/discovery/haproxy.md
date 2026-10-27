# HAProxy Discovery

*Última actualización del artículo: 2026-10-26.*

## Qué monitoriza

El addon HAProxy Discovery monitoriza balanceadores HAProxy a través de la exportación CSV del endpoint de estadísticas de HAProxy (`/stats;csv`). Lee esa exportación y convierte cada estadística de cada proxy en un módulo de Pandora FMS: sesiones, bytes transferidos, colas, errores, comprobaciones de salud, clases de respuesta HTTP, tiempos y el estado operativo de cada frontend, backend y servidor.

El addon crea **un agente por cada URL de HAProxy**. Una tarea de Discovery admite varias URL a la vez, de modo que una sola tarea cubre un conjunto completo de instancias HAProxy. Cada agente contiene un módulo por cada estadística disponible y por cada fila de proxy, además de un módulo numérico `status` por cada fila que sirve para alertar sobre los estados `DOWN`, `MAINT` o `STOP`.

## Preparar

### Compatibilidad

| Ámbito | Estado | Evidencia |
|--------|--------|-----------|
| Addon `pandorafms.haproxy`, versión `1.0` | Objetivo documentado | La versión que describe esta página. Consulta [Identidad del addon](#identidad-del-addon) |
| Endpoint de estadísticas de HAProxy que sirva la exportación CSV, por HTTP o HTTPS, con o sin autenticación básica | `Requerido` | Requisito previo, no una declaración de compatibilidad. Consulta [Habilitar el endpoint de estadísticas](#habilitar-el-endpoint-de-estadisticas) |
| Conectividad de red desde el servidor Discovery al endpoint de estadísticas | `Requerido` | El addon realiza una petición HTTP por URL |
| Versiones concretas de HAProxy | `No validado` | No se ha registrado una matriz de versiones para este addon |
| Sistema operativo del servidor Discovery | `No validado` | No se ha registrado ningún sistema operativo para esta versión |
| Versiones concretas de Pandora FMS | `No validado` | No se ha registrado una matriz de versiones para este addon |

### Requisitos previos

1. **El endpoint de estadísticas debe estar habilitado y ser accesible** desde la máquina que ejecuta el addon. Cómo habilitarlo se explica en [Habilitar el endpoint de estadísticas](#habilitar-el-endpoint-de-estadisticas).
2. **Credenciales**, solo cuando el endpoint está protegido con autenticación básica HTTP.
3. **Pandora FMS**: un servidor Discovery que ejecute la tarea y la consola que la defina.

El addon se distribuye como un ejecutable autocontenido, `bin/pandora_haproxy`, por lo que no hay que instalar nada más en el servidor Discovery para ejecutar una tarea.

### Instalar el addon

Descarga el paquete `.disco` desde la entrada del Marketplace de Pandora FMS, cuya descarga está limitada a usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.haproxy](https://marketplace.pandorafms.com/entries/pandorafms.haproxy)

Cárgalo en Pandora FMS. Una vez cargado, **HAProxy** estará disponible en **Management → Discovery → Application** al crear tareas de Discovery.

### Habilitar el endpoint de estadísticas

Para que el addon obtenga las estadísticas, HAProxy debe exponer su página de estadísticas. Se habilita editando el fichero de configuración de HAProxy, `haproxy.cfg` (por defecto `/etc/haproxy/haproxy.cfg`). Elige la variante que se corresponda con la protección que quieras para el endpoint. Ninguna necesita la opción `stats admin`, porque el addon solo lee datos.

#### Configuración mínima (sin autenticación, sin SSL)

Añade un `frontend` dedicado a las estadísticas:

```
frontend stats
    bind *:8404
    stats enable
    stats uri /stats
    stats refresh 10s
```

La URL que hay que facilitar al addon es el host y el puerto, sin ruta:

```
http://<HAPROXY_HOST>:8404
```

El addon añade `/stats;csv` a la ruta que se le indica en lugar de sustituirla, por lo que la dirección de la página de estadísticas no sirve tal cual: `http://<HAPROXY_HOST>:8404/stats` se solicita como `http://<HAPROXY_HOST>:8404/stats/stats;csv` y HAProxy responde `404`. Indica solo el host y el puerto, o una URL que ya termine en `stats;csv`. Consulta [Cómo se normaliza la URL](#como-se-normaliza-la-url).

#### Autenticación básica

Define una `userlist` y exige autenticación en el frontend de estadísticas:

```
frontend stats
    bind *:8404
    stats enable
    stats uri /stats
    stats refresh 10s

    acl auth_ok http_auth(stats_users)
    http-request auth realm stats if !auth_ok

userlist stats_users
    user <USERNAME> password <PASSWORD_HASH>
```

Genera el hash de la contraseña, que HAProxy lee en formato `crypt(3)`, con:

```bash
openssl passwd -6 <PASSWORD>
```

Facilita al addon el mismo usuario y contraseña en los campos **Username** y **Password**.

#### SSL/TLS

Sirve las estadísticas por HTTPS añadiendo `ssl crt` a la línea `bind`:

```
frontend stats
    bind *:8404 ssl crt /etc/haproxy/certs/stats.pem
    stats enable
    stats uri /stats
    stats refresh 10s
```

Para crear un certificado autofirmado de pruebas:

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/haproxy/certs/stats.key \
  -out /etc/haproxy/certs/stats.crt \
  -subj "/CN=localhost"
cat /etc/haproxy/certs/stats.crt /etc/haproxy/certs/stats.key > /etc/haproxy/certs/stats.pem
```

Usa una URL con esquema `https://` en la tarea. Activa **Verify SSL** solo cuando el certificado sea válido para el nombre de host de la URL y su emisor sea de confianza para el servidor Discovery; déjalo desactivado con certificados autofirmados.

#### SSL y autenticación a la vez

Combina ambos bloques en el frontend de estadísticas:

```
frontend stats
    bind *:8404 ssl crt /etc/haproxy/certs/stats.pem
    stats enable
    stats uri /stats
    stats refresh 10s

    acl auth_ok http_auth(stats_users)
    http-request auth realm stats if !auth_ok

userlist stats_users
    user <USERNAME> password <PASSWORD_HASH>
```

Tras editar `haproxy.cfg`, recarga el servicio:

```bash
sudo systemctl reload haproxy
```

### Comprobar que el endpoint responde

Antes de crear la tarea, solicita la exportación CSV a mano desde el servidor Discovery. Entrecomilla la URL, porque `;` es un carácter especial de la shell:

```bash
curl -u <USERNAME>:<PASSWORD> 'http://<HAPROXY_HOST>:8404/stats;csv'
```

Pasar una contraseña por la línea de comandos la expone en el historial de la shell y en la lista de procesos del sistema operativo. Omite `-u` cuando el endpoint no tenga autenticación. Para un endpoint HTTPS con certificado autofirmado añade `-k`.

La primera línea de la respuesta debe ser una cabecera que empiece por `# pxname,svname,qcur,qmax,...`, seguida de una fila por cada frontend, backend y servidor. Si esta petición falla, la tarea también fallará: corrígelo aquí y no en la consola.

## Configurar la tarea de Discovery

Crea la tarea desde **Management → Discovery → Application → HAProxy**. Tras el paso genérico de definición de la tarea, la consola presenta los campos en dos pasos. Todos los campos se documentan en [Parámetros de la tarea](#parametros-de-la-tarea).

1. **HAProxy Basic** — los endpoints y cómo acceder a ellos:

    - **HAProxy Stats URLs**: URL de estadísticas, separadas por comas o una por línea. **Cada URL genera un agente.** Obligatorio.
    - **Username** y **Password**: solo cuando el endpoint requiere autenticación básica HTTP. La autenticación solo se envía cuando ambos están rellenos.
    - **Verify SSL**: valida el certificado de una URL `https://`. Desactivado por defecto.
    - **Transfer mode**, **Tentacle IP** y **Tentacle port**: cómo llegan los datos a Pandora FMS. `native` permite que el servidor Discovery lea los datos directamente; `tentacle` los envía con el cliente Tentacle. Los campos de Tentacle solo importan en modo `tentacle`.

    <!-- SCREENSHOT NEEDED: Paso HAProxy Basic del asistente con el área de URL, Username, Password, Verify SSL y Transfer mode con los campos de Tentacle, usando marcadores de documentación (por ejemplo http://<HAPROXY_HOST>:8404) y sin direcciones IP privadas. -->

2. **HAProxy Advanced** — ajuste opcional del resultado:

    - **Module prefix**: se antepone a todos los nombres de módulo creados.
    - **Monitor frontends**, **Monitor backends** y **Monitor servers**: eligen qué tipos de fila de proxy generan módulos. Los tres están habilitados por defecto.
    - **Allow list** y **Deny list**: expresiones regulares para incluir o excluir módulos por nombre.

    ![Paso HAProxy Advanced del asistente con los campos Module prefix, Monitor frontends, Monitor backends, Monitor servers, Allow list y Deny list](../assets/images/discovery/haproxy/haproxy-advanced-step.png)

El grupo y el intervalo de la propia tarea proceden del paso genérico de definición de la tarea: se aplican a los agentes que crea la tarea.

## Verificar la primera ejecución

Fuerza la tarea desde **Management → Discovery → Task list** y comprueba el resultado en este orden.

1. **El resumen de la tarea.** Una tarea que finaliza correctamente informa de:

    - **Total Agents**: número de agentes generados por la tarea.
    - **Total Modules**: número de módulos generados por la tarea.

    Espera un agente por cada URL indicada. Una URL que no se haya podido leer se notifica como error en la información de ejecución.

    <!-- SCREENSHOT NEEDED: Resumen de ejecución de una tarea Discovery de HAProxy mostrando Total Agents y Total Modules. -->

2. **Los agentes.** Uno por URL, con el alias igual al `host:puerto` de la URL, por ejemplo `<HAPROXY_HOST>:8404`.

3. **Los módulos de cada agente.** Los módulos se llaman `<prefijo><proxy>_<servidor>_<estadística>`, por ejemplo `app_FRONTEND_scur` o `app_BACKEND_status`. Cada fila de proxy tiene un módulo `status`, cuyo valor sigue la correspondencia de [El módulo status](#el-modulo-status).

Si la tarea no informa de agentes, repasa [Comprobar que el endpoint responde](#comprobar-que-el-endpoint-responde) y después [Resolución de problemas](#resolucion-de-problemas).

## Comprender los resultados

### Agentes generados

El addon crea **un agente por cada URL de HAProxy**. El nombre del agente es el hash MD5 del `host:puerto` de la URL, y el alias es ese mismo `host:puerto`, por ejemplo `<HAPROXY_HOST>:8404`. Cuando una URL no tiene `host:puerto`, se usa la URL completa. La descripción del agente es `HAProxy stats agent created by discovery plugin`.

Como la identidad procede del endpoint y no de la tarea, mover una URL entre tareas sigue reportando al mismo agente y conserva su histórico. Por tanto, dos URL con el mismo `host:puerto` se resuelven en el mismo agente.

### Módulos generados

HAProxy informa de una fila CSV por cada frontend, una por cada backend y una por cada servidor, y el addon crea módulos a partir de cada fila:

- **Módulo `status`**: se crea para cada fila, con independencia de las opciones **Monitor frontends**, **Monitor backends** y **Monitor servers**, de modo que siempre puedas alertar sobre `DOWN`, `MAINT` y `STOP`. Consulta [El módulo status](#el-modulo-status).
- **Módulos de estadísticas**: un módulo por cada estadística de la fila que tenga valor. Los valores numéricos se crean como módulos `generic_data` y los valores de texto como `generic_data_string`. Las estadísticas con valor vacío no se crean.

Un módulo de estadística solo se crea cuando su tipo de fila está habilitado: las filas de tipo frontend (`type=0`), backend (`type=1`) o servidor (`type=2`) siguen a **Monitor frontends**, **Monitor backends** y **Monitor servers**. Las filas de cualquier otro tipo, como los sockets (`type=3`), no dependen de esas opciones.

Los nombres de módulo tienen la forma `<prefijo><proxy>_<servidor>_<estadística>`, donde `<proxy>` y `<servidor>` son las columnas `pxname` y `svname` de la fila. En las filas de frontend y backend, `svname` es `FRONTEND` o `BACKEND`. Se eliminan los apóstrofos y las comillas dobles de los nombres y las descripciones.

El addon crea un módulo por cada columna que devuelve el endpoint, salvo las columnas indicadas en [Estadísticas que no crean módulos](#estadisticas-que-no-crean-modulos). Una versión de HAProxy que exporte columnas numéricas adicionales produce, por tanto, módulos adicionales. La [Referencia](#modulos-por-estadistica) describe las columnas que documenta el addon.

### El módulo status

El módulo `status` es `generic_data` y convierte el texto de estado de HAProxy en un número, de mejor a peor:

| Estado de HAProxy | Valor |
|-------------------|-------|
| `UP` | `5` |
| `OPEN` | `4` |
| `NOLB` | `3` |
| `MAINT` | `2` |
| `STOP`, `STOPPING` | `1` |
| `DOWN` | `0` |
| Cualquier otro estado | `-1` |

Solo se usa la primera palabra del estado de HAProxy, por lo que `UP 2/3` se interpreta como `UP`. El módulo se crea con los umbrales warning de `2` a `4` y critical de `0` a `2`, de modo que una fila `DOWN` o `MAINT` genera un estado crítico y una fila `NOLB` un aviso, sin configuración adicional.

### Filtrado de módulos

**Allow list** y **Deny list** son expresiones regulares que se buscan (sin anclar) en el nombre del módulo tal como se construye a partir de la fila, `<proxy>_<servidor>_<estadística>`, sin el **Module prefix**. Por ejemplo, `.*_wredis|.*_wretr` coincide con todos los módulos `wredis` y `wretr`, y `status|scur|smax` coincide con todos los módulos cuyo nombre contiene una de esas tres palabras.

- Primero se aplica la lista de permitidos y después la de denegados.
- Una lista vacía no hace nada. Una expresión regular no válida se ignora: una lista de permitidos no válida permite todo y una lista de denegados no válida no excluye nada.
- Ambas listas también se aplican al módulo `status`. Una lista de permitidos que no coincida con `status` lo elimina.

### Cómo se normaliza la URL

Para cada URL, el addon solicita la exportación CSV. Añade `/stats;csv` a la ruta de la URL cuando la ruta no termina ya en `stats;csv`, y añade el parámetro `norefresh` a la consulta cuando falta. Cada petición tiene un tiempo de espera fijo de 10 segundos. Como el sufijo se añade y no se sustituye, `http://<HAPROXY_HOST>:8404` se solicita como `http://<HAPROXY_HOST>:8404/stats;csv?norefresh`, mientras que `http://<HAPROXY_HOST>:8404/stats` se solicita como `http://<HAPROXY_HOST>:8404/stats/stats;csv?norefresh` y falla con `404`.

## Operar

### Ejecución manual

El addon puede ejecutarse fuera de una tarea de Discovery, que es la forma más rápida de confirmar un endpoint antes de incorporarlo a una tarea. Tiene dos modos de entrada:

- **Modo simple**: pasa las URL por línea de comandos con `--urls`.
- **Modo avanzado**: pasa un fichero de configuración con `--conf` más un fichero de destinos con `--conf_targets`. Es el modo que usa la propia tarea de Discovery.

```bash
# Modo simple
./pandora_haproxy --urls http://<HAPROXY_HOST_1>:8404,http://<HAPROXY_HOST_2>:8404 \
    --user <USERNAME> --password <PASSWORD> --ssl false

# Modo avanzado
./pandora_haproxy --conf <PATH_TO_CONFIG> --conf_targets <PATH_TO_TARGETS>
```

Pasar una contraseña por la línea de comandos la expone en el historial de la shell y en la lista de procesos del sistema operativo. Prefiere el fichero de configuración para cualquier uso que no sea una comprobación puntual, y protege ese fichero con permisos restrictivos.

La ejecución imprime un resumen JSON. En modo `native`, los datos recogidos se exponen en el campo `monitoring_data` del resumen, para que los consuma el servidor Discovery; en modo `tentacle`, el addon genera un fichero XML por agente y lo envía al servidor de Pandora FMS con el cliente Tentacle. Cuando se producen errores, el resumen los incluye en su campo `info`.

`--as_server_plugin true` sustituye el resumen por un único `1` (se creó al menos un agente sin errores) o `0`, de modo que el addon pueda usarse como plugin de servidor.

> En modo simple (`--urls`), los parámetros de prefijo de módulo, modo de transferencia, dirección de Tentacle e intervalo se aceptan pero no se aplican: el addon usa los valores por defecto (sin prefijo, `native`, `127.0.0.1:41121` y `300` segundos), y no se envía ningún grupo de agentes con los agentes. Para cambiarlos, usa el modo avanzado con `--conf`.

## Resolución de problemas

El addon no tiene opción verbose ni de depuración. Su canal de diagnóstico es la información de ejecución de la tarea (el campo `info` del resumen JSON en una ejecución manual), que nombra la URL que falla.

- **`HTTP error for <url>: HTTP Error <code> for <url>`** — el endpoint respondió con un estado de error. `401` significa que las credenciales faltan o son incorrectas: comprueba **Username** y **Password** (ambos deben estar rellenos para que se envíe la autenticación) frente a la `userlist`. `404` normalmente significa que la URL y el `stats uri` de HAProxy no encajan: el addon añade `/stats;csv` a la ruta indicada, así que una URL que ya termina en `/stats` solicita `/stats/stats;csv`. Indica solo el host y el puerto, o una URL que ya termine en `stats;csv`.
- **`Request error for <url>: ...`** — no se pudo completar la petición: conexión rechazada o con tiempo agotado (10 segundos), puerto incorrecto, cortafuegos o error de certificado. Ante un error de certificado en un endpoint HTTPS, desactiva **Verify SSL** si el certificado es autofirmado o instala la CA emisora en el servidor Discovery.
- **`Error parsing CSV for <url>` o `No stats data returned for <url>`** — la URL respondió, pero no con la exportación CSV o sin filas. Compruébalo con el comando `curl` de [Comprobar que el endpoint responde](#comprobar-que-el-endpoint-responde).
- **`No modules created for <url>`** — los filtros de filas eliminaron todo. Revisa **Allow list**, **Deny list** y las opciones **Monitor**.
- **`All requests failed when trying to obtain HAProxy stats`** — ninguna URL produjo un agente.
- **`No URLs provided` o `No valid URLs after parsing`** — **HAProxy Stats URLs** está vacío tras separar por comas y saltos de línea.
- **`Error: --conf_targets is required when using --conf` o `Error: no valid targets found in <file>`** — en una ejecución manual en modo avanzado, el fichero de destinos falta o está vacío.
- **El endpoint responde a mano pero no desde la tarea** — la petición sale desde el servidor Discovery, no desde tu estación de trabajo. Revisa la ruta de red y las reglas `acl` del frontend de estadísticas.
- **El prefijo de módulo, el modo de transferencia, la dirección de Tentacle o el intervalo parecen ignorados en una ejecución manual** — consulta la nota de [Ejecución manual](#ejecucion-manual).
- **Un módulo `status` tiene el valor `-1`** — HAProxy informó de un estado que no está en la tabla de [El módulo status](#el-modulo-status), por ejemplo una fila sin comprobación de salud.
- **Menos módulos de los esperados** — revisa las opciones de tipo de fila y las listas de permitidos y denegados, y recuerda que las estadísticas vacías y las columnas de [Estadísticas que no crean módulos](#estadisticas-que-no-crean-modulos) nunca crean módulos.

## Referencia

### Parámetros de la tarea

La consola presenta los campos de la tarea en dos pasos.

#### HAProxy Basic

| Campo | Macro | Tipo | Valor por defecto | Notas |
|-------|-------|------|-------------------|-------|
| HAProxy Stats URLs | `_haproxyUrls_` | textarea | — | Obligatorio. Separadas por comas o una por línea. Cada URL crea un agente |
| Username | `_haproxyUser_` | string | vacío | Usuario de autenticación básica HTTP, opcional |
| Password | `_haproxyPassword_` | password | vacío | Contraseña de autenticación básica HTTP, opcional. La autenticación solo se envía cuando usuario y contraseña están rellenos |
| Verify SSL | `_verifySSL_` | checkbox | desactivado | Valida el certificado de una URL HTTPS. Déjalo desactivado con certificados autofirmados |
| Transfer mode | `_transferMode_` | select | `native` | `native`: el servidor Discovery lee directamente los datos del agente. `tentacle`: el addon envía los datos con el cliente Tentacle |
| Tentacle IP | `_tentacleIp_` | string | `127.0.0.1` | Dirección del servidor Tentacle, usada en modo `tentacle` |
| Tentacle port | `_tentaclePort_` | number | `41121` | Puerto del servidor Tentacle, usado en modo `tentacle` |

#### HAProxy Advanced

| Campo | Macro | Tipo | Valor por defecto | Notas |
|-------|-------|------|-------------------|-------|
| Module prefix | `_prefixModules_` | string | vacío | Se antepone a todos los nombres de módulo |
| Monitor frontends | `_monitorFrontends_` | checkbox | activado | Crea módulos de estadísticas para las filas de frontend (`type=0`) |
| Monitor backends | `_monitorBackends_` | checkbox | activado | Crea módulos de estadísticas para las filas de backend (`type=1`) |
| Monitor servers | `_monitorServers_` | checkbox | activado | Crea módulos de estadísticas para las filas de servidor (`type=2`) |
| Allow list | `_allowList_` | string | vacío (todos) | Expresión regular; solo se crean los módulos cuyo nombre coincide |
| Deny list | `_denyList_` | string | vacío (ninguno) | Expresión regular; no se crean los módulos cuyo nombre coincide |

### Parámetros de línea de comandos

```bash
./pandora_haproxy --urls <URLs> [opciones]
./pandora_haproxy --conf <ruta> --conf_targets <ruta>
```

| Parámetro | Valor por defecto | Descripción |
|-----------|-------------------|-------------|
| `--urls` | — | URL de estadísticas de HAProxy, separadas por comas. Cada URL genera un agente. Se requiere `--urls` o `--conf` |
| `--user` | — | Usuario de autenticación básica HTTP, opcional |
| `--password` | — | Contraseña de autenticación básica HTTP, opcional |
| `--ssl` | `true` | Verifica el certificado HTTPS (`true` o `false`) |
| `--prefix` | vacío | Prefijo de los nombres de módulo. No se aplica en modo simple |
| `-tm`, `--transfer_mode` | `native` | `native` o `tentacle`. No se aplica en modo simple |
| `-ti`, `--tentacle_ip` | `127.0.0.1` | Dirección del servidor Tentacle. No se aplica en modo simple |
| `-tp`, `--tentacle_port` | `41121` | Puerto del servidor Tentacle. No se aplica en modo simple |
| `-in`, `--interval` | `300` | Intervalo de monitorización en segundos. No se aplica en modo simple |
| `--allow_list` | vacío (todos) | Expresión regular para incluir solo los módulos cuyo nombre coincide |
| `--deny_list` | vacío (ninguno) | Expresión regular para excluir los módulos cuyo nombre coincide |
| `--monitor_frontends` | `true` | Crea módulos de estadísticas para las filas de frontend (`type=0`) |
| `--monitor_backends` | `true` | Crea módulos de estadísticas para las filas de backend (`type=1`) |
| `--monitor_servers` | `true` | Crea módulos de estadísticas para las filas de servidor (`type=2`) |
| `--as_server_plugin` | `false` | Devuelve un único `1` o `0` en lugar del resumen JSON |
| `--conf` | — | Ruta del fichero de configuración |
| `--conf_targets` | — | Ruta del fichero con las URL de HAProxy. Obligatorio al usar `--conf` |

Los valores booleanos aceptan `true`, `yes`, `t`, `y` y `1` (con cualquier combinación de mayúsculas y minúsculas) como verdadero; cualquier otro valor es falso.

### Fichero de configuración

La tarea de Discovery construye este fichero a partir de sus propios campos; una ejecución manual en modo avanzado lo aporta con `--conf`. Usa una sección `[CONF]` con un `clave=valor` por línea. Las URL no se leen de este fichero sino del fichero de destinos.

| Clave | Valor por defecto si falta | Descripción |
|-------|----------------------------|-------------|
| `username` | vacío | Usuario de autenticación básica HTTP |
| `password` | vacío | Contraseña de autenticación básica HTTP |
| `verify_ssl` | `false` | Verifica el certificado HTTPS |
| `prefix` | vacío | Prefijo de los nombres de módulo |
| `transfer_mode` | ninguno | `native` o `tentacle`. Indícalo siempre: si la clave falta, la ejecución no usa `native` |
| `tentacle_ip` | vacío | Dirección del servidor Tentacle, usada en modo `tentacle` |
| `tentacle_port` | vacío | Puerto del servidor Tentacle, usado en modo `tentacle` |
| `agents_group` | vacío | Nombre del grupo de agentes, usado en modo `tentacle` |
| `agents_group_id` | vacío | Id del grupo de agentes, usado en modo `native` |
| `interval` | `0` | Intervalo de monitorización en segundos. Indícalo siempre |
| `allow_list` | vacío | Expresión regular para incluir solo los módulos cuyo nombre coincide |
| `deny_list` | vacío | Expresión regular para excluir los módulos cuyo nombre coincide |
| `monitor_frontends` | `true` | Crea módulos de estadísticas para las filas de frontend |
| `monitor_backends` | `true` | Crea módulos de estadísticas para las filas de backend |
| `monitor_servers` | `true` | Crea módulos de estadísticas para las filas de servidor |

Ejemplo:

```ini
[CONF]
username=<USERNAME>
password=<PASSWORD>
verify_ssl=true
prefix=haproxy_
transfer_mode=native
tentacle_ip=127.0.0.1
tentacle_port=41121
interval=300
agents_group_id=<GROUP_ID>
allow_list=
deny_list=.*_wredis|.*_wretr
monitor_frontends=true
monitor_backends=true
monitor_servers=true
```

Fichero de destinos (`--conf_targets`), una URL por línea, separadas por comas, o ambas cosas:

```
http://<HAPROXY_HOST_1>:8404
http://<HAPROXY_HOST_2>:8404
```

### Módulos por estadística

Cada estadística siguiente crea un módulo llamado `<prefijo><proxy>_<servidor>_<estadística>`, sujeto a las opciones de tipo de fila y a las listas de permitidos y denegados. La descripción del módulo es el texto de la tabla, en inglés tal como la define el addon.

#### Sesiones, tráfico y tasas

| Estadística | Descripción |
|-------------|-------------|
| `scur` | Current sessions |
| `smax` | Max sessions |
| `slim` | Configured session limit |
| `stot` | Cumulative sessions |
| `bin` | Bytes in |
| `bout` | Bytes out |
| `rate` | Sessions per second (last second) |
| `rate_lim` | Configured limit on new sessions/s |
| `rate_max` | Max sessions per second |
| `req_rate` | HTTP requests per second |
| `req_rate_max` | Max HTTP requests per second |
| `req_tot` | Total HTTP requests received |
| `conn_rate` | Connections over last elapsed second |
| `conn_rate_max` | Highest known conn_rate |
| `conn_tot` | Cumulative number of connections |
| `intercepted` | Cumulative intercepted requests |
| `lbtot` | Times server was selected |
| `lastsess` | Seconds since last session assigned |

#### Cola

| Estadística | Descripción |
|-------------|-------------|
| `qcur` | Current queued requests |
| `qmax` | Max queued requests |
| `qlimit` | Configured maxqueue for server |

#### Peticiones denegadas, errores y abortos

| Estadística | Descripción |
|-------------|-------------|
| `dreq` | Requests denied (security) |
| `dresp` | Responses denied (security) |
| `dcon` | Requests denied by tcp-request connection rules |
| `dses` | Requests denied by tcp-request session rules |
| `ereq` | Request errors |
| `econ` | Connection errors to backend |
| `eresp` | Response errors |
| `wretr` | Connection retries |
| `wredis` | Redispatches to another server |
| `cli_abrt` | Data transfers aborted by client |
| `srv_abrt` | Data transfers aborted by server |

#### Servidores, peso y comprobaciones de salud

| Estadística | Descripción |
|-------------|-------------|
| `weight` | Total weight / server weight |
| `act` | Active servers (backend) / server active |
| `bck` | Backup servers (backend) / server backup |
| `chkfail` | Failed health checks |
| `chkdown` | UP->DOWN transitions |
| `lastchg` | Seconds since last UP<->DOWN transition |
| `downtime` | Total downtime (seconds) |
| `throttle` | Current throttle percentage |
| `tracked` | ID of proxy/server if tracking enabled |
| `check_code` | Layer 5-7 check code |
| `check_duration` | Time in ms of last health check |
| `check_rise` | Server's rise parameter used by checks |
| `check_fall` | Server's fall parameter used by checks |
| `check_health` | Server's health check value |
| `agent_code` | Numeric code reported by agent |
| `agent_duration` | Time in ms of last agent check |
| `agent_rise` | Agent's rise parameter |
| `agent_fall` | Agent's fall parameter |
| `agent_health` | Agent's health parameter |

#### Respuestas HTTP y tiempos

| Estadística | Descripción |
|-------------|-------------|
| `hrsp_1xx` | HTTP responses with 1xx code |
| `hrsp_2xx` | HTTP responses with 2xx code |
| `hrsp_3xx` | HTTP responses with 3xx code |
| `hrsp_4xx` | HTTP responses with 4xx code |
| `hrsp_5xx` | HTTP responses with 5xx code |
| `hrsp_other` | HTTP responses with other codes |
| `qtime` | Average queue time (ms) over last 1024 requests |
| `ctime` | Average connect time (ms) over last 1024 requests |
| `rtime` | Average response time (ms) over last 1024 requests |
| `ttime` | Average total session time (ms) over last 1024 requests |

#### Compresión

| Estadística | Descripción |
|-------------|-------------|
| `comp_in` | HTTP response bytes fed to compressor |
| `comp_out` | HTTP response bytes emitted by compressor |
| `comp_byp` | Bytes that bypassed HTTP compressor |
| `comp_rsp` | HTTP responses that were compressed |

#### Identificadores

| Estadística | Descripción |
|-------------|-------------|
| `pid` | Process ID |
| `iid` | Unique proxy ID |
| `sid` | Server ID (unique inside proxy) |

### Estadísticas que no crean módulos

Las siguientes columnas de la exportación de HAProxy nunca crean un módulo: `pxname`, `svname` (forman el nombre del módulo), `type` (selecciona el tipo de fila), `status` (tiene su propio módulo, consulta [El módulo status](#el-modulo-status)), `check_status`, `check_desc`, `agent_status`, `agent_desc`, `last_chk`, `last_agt`, `hanafail`, `addr`, `cookie`, `mode` y `algo`.

### Identidad del addon

| Elemento | Valor |
|----------|-------|
| Nombre | HAProxy |
| Identificador | `pandorafms.haproxy` |
| Versión | `1.0` |
| Tipo y sección | Discovery, `app` (**Management → Discovery → Application**) |
| Paquete | `pandorafms.haproxy.1.0.disco` |
| Entrada del Marketplace | [pandorafms.haproxy](https://marketplace.pandorafms.com/entries/pandorafms.haproxy), actualizada el 2026-06-04 |
| Disponibilidad | La entrada del Marketplace indica que la descarga está limitada a usuarios con licencia |
