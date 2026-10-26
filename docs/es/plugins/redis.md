# Redis monitoring plugin

*Última actualización del artículo: 2026-10-26.*

## Qué hace

El plugin de monitorización de Redis convierte las estadísticas de un servidor Redis en módulos de Pandora FMS. Cada ejecución se conecta a una instancia de Redis, lee las secciones de `INFO` que usted seleccione y publica cada campo que devuelve Redis como un módulo con el nombre exacto de ese campo: identidad y tiempo de actividad del servidor, clientes conectados, memoria, persistencia, estadísticas, replicación, CPU, contadores por comando, estado del clúster y tamaño de las bases de datos.

No se instala nada en el servidor Redis. El plugin se conecta por TCP desde el host que lo ejecuta, con una contraseña opcional.

El plugin admite dos modelos de ejecución:

- **Modo plugin de servidor** (por defecto cuando no se define ninguna clave de modo): cada ejecución construye un documento de agente y lo entrega a Pandora FMS mediante Tentacle o una carpeta de datos local.
- **Modo plugin de agente** (requiere `as_agent_plugin=1`): cada ejecución imprime los módulos generados como XML en la salida estándar, para que los ingiera el agente de Pandora FMS.

Esta página documenta el plugin de monitorización, que lee las estadísticas de una instancia por ejecución. El descubrimiento de instancias Redis y la generación de sus agentes es un addon distinto, documentado en [Redis Discovery](../discovery/redis.md).

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
|--------|--------|-----------|
| Addon `redis`, versión `1.1` | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del addon](#identidad-del-addon) |
| Acceso de red desde el host que ejecuta el plugin al puerto de escucha de Redis (TCP, `6379` por defecto en Redis) | `Required` | El plugin abre una conexión de cliente a la dirección de `server` |
| Una contraseña de Redis, cuando la instancia exige autenticación | `Required` cuando la autenticación está habilitada | Requisito previo de la clave `password`, no una declaración de compatibilidad |
| `tentacle_client` en el host que ejecuta el plugin | `Required` cuando `mode=tentacle` | Entrega en modo plugin de servidor |
| Versiones del servidor Redis | `Not validated` | No hay una matriz de versiones registrada. La guía heredada solo indica que el plugin se desarrolló contra Redis `3.2.12`; el plugin no necesita nada más allá de un servidor que responda a `INFO` |
| Sistema operativo del host que ejecuta el plugin | `Not validated` | No hay un sistema operativo registrado para esta versión |
| Versiones de Pandora FMS | `Not validated` | El Marketplace muestra un aviso general para todas sus integraciones, no una declaración específica de este addon |

### Requisitos

1. **Acceso de red** desde el host que ejecuta el plugin hasta el host y el puerto de Redis.
2. **Una contraseña de Redis**, cuando la instancia tiene la autenticación habilitada. El plugin solo envía una contraseña: no tiene clave de nombre de usuario, así que una instancia que exija un usuario ACL no puede monitorizarse con este plugin. Use el usuario `default` con `requirepass`, o un usuario ACL que se autentique únicamente con contraseña.
3. **Pandora FMS** para recibir la salida: el servidor de Pandora FMS en modo plugin de servidor, o el agente de Pandora FMS del host monitorizado en modo plugin de agente.
4. **El cliente de Tentacle (`tentacle_client`) disponible en el `PATH`**, solo cuando el modo plugin de servidor entrega mediante Tentacle.

La cuenta que usa el plugin solo lee `INFO`. Ninguna fuente oficial identifica un conjunto de permisos de Redis más restrictivo; conceda únicamente lo que la instancia necesite para responder a ese comando.

### Instalar el plugin

Descargue el paquete desde la entrada gratuita del Marketplace:

[https://marketplace.pandorafms.com/entries/redis](https://marketplace.pandorafms.com/entries/redis)

Copie el ejecutable `redis_monitor` al host que vaya a ejecutar el plugin y cree su archivo de configuración junto a él (consulte [Configuración](#configuracion)). No se instala nada en el servidor Redis y no se necesitan herramientas cliente de Redis en el host de monitorización.

## Configuración

El plugin combina sus valores por defecto con dos fuentes de entrada, en orden creciente de precedencia:

```text
valores por defecto < archivo de configuración < argumentos de línea de comandos
```

El archivo de configuración es opcional. Cuando se usa, debe ser el **primer argumento** de la línea de comandos: una ruta de archivo situada después de una opción no se lee. Es un archivo de texto plano con un par `key=value` por línea. Las líneas en blanco y las que empiezan por `#` se omiten, las claves y los valores se recortan, y la última aparición de una clave repetida prevalece.

El archivo no tiene secciones. El plugin lee solo las claves que se listan en [Claves del archivo de configuración](#claves-del-archivo-de-configuracion); una cabecera entre corchetes como `[THRESHOLDS]` se almacena como una clave sin uso con valor vacío y no tiene ningún efecto.

Las dos claves que definen qué se lee son:

- **`server`** — la instancia que se lee, como `<REDIS_HOST>:<REDIS_PORT>`. Incluya el puerto: la configuración de ejemplo siempre lo hace.
- **`metrics`** — las secciones de `INFO` que se leen, separadas por espacios. `all` lee todas las secciones que informa el servidor.

### Modos de ejecución

El modo plugin de agente es la configuración más corta: el agente de Pandora FMS ejecuta el plugin e ingiere el XML de módulos que imprime.

```ini
server=<REDIS_HOST>:<REDIS_PORT>
password=<PASSWORD>
metrics=all
module_group=Redis
as_agent_plugin=1
as_server_plugin=0
```

El modo plugin de servidor necesita un nombre de agente y un destino de entrega. Con Tentacle:

```ini
server=<REDIS_HOST>:<REDIS_PORT>
password=<PASSWORD>
metrics=all
module_group=Redis
as_agent_plugin=0
as_server_plugin=1
agent_name=redis-monitoring
temp=/tmp
mode=tentacle
tentacle_ip=<PANDORA_FMS_SERVER>
tentacle_port=41121
```

O copie el documento de agente en una carpeta de datos local en lugar de usar Tentacle:

```ini
server=<REDIS_HOST>:<REDIS_PORT>
password=<PASSWORD>
metrics=all
as_agent_plugin=0
as_server_plugin=1
agent_name=redis-monitoring
temp=/tmp
mode=local
local_folder=/var/spool/pandora/data_in
```

La misma ejecución en modo plugin de agente solo con argumentos, sin archivo de configuración:

```bash
./redis_monitor -server <REDIS_HOST>:<REDIS_PORT> -password <PASSWORD> -metrics all -as_agent_plugin 1
```

Puntos clave:

- `as_agent_plugin` y `as_server_plugin` seleccionan el modelo de ejecución. Cuando no se define ninguno, el plugin se ejecuta como plugin de servidor. Cuando ambos valen `1`, los dos modelos se ejecutan en la misma ejecución: el XML de módulos se imprime **y** el documento de agente se entrega.
- `agent_name` es obligatorio en modo plugin de servidor: es el nombre del agente que se crea en Pandora FMS. El plugin envía solo ese nombre; no lee ninguna clave de intervalo, grupo o versión del agente.
- `mode` selecciona la entrega: `tentacle` usa el cliente de Tentacle, y cualquier otro valor, incluido `local`, copia el documento de agente en `local_folder`.
- `module_group` es el nombre del grupo de módulos que se asigna a cada módulo generado. Pandora FMS lo resuelve sin distinguir mayúsculas y minúsculas contra los grupos existentes; cuando el nombre no coincide con ninguno, los módulos se crean sin ese grupo.
- `temp` es la carpeta donde se escribe el documento de agente antes de la entrega. En Linux vale `/tmp` por defecto cuando la clave no está presente.
- `metrics` es un valor único: los nombres de sección se separan por espacios, así que la lista completa va en una sola línea.
- Los nombres de módulo son los nombres de campo de Redis, sin prefijo. Ejecute **un agente por instancia de Redis**: dos instancias entregadas al mismo agente sobrescriben sus módulos mutuamente.

### Credenciales y transporte

- La conexión con Redis no está cifrada: el plugin no tiene opción TLS, por lo que la contraseña y las estadísticas viajan en texto claro. Mantenga la conexión en una red de confianza o sitúe un túnel TLS delante de Redis.
- La `password` en línea se guarda en el archivo de configuración en texto plano: restrinja los permisos del archivo al usuario que ejecuta el plugin.
- Evite `-password` en la línea de comandos: el comando se guarda en el historial del intérprete y la lista de procesos del sistema operativo puede exponerlo mientras el plugin se ejecuta. Prefiera el archivo de configuración con permisos restrictivos (por ejemplo `chmod 600`).
- `debug=1` imprime volcados de diagnóstico en la salida estándar, incluida la respuesta completa de `INFO`. Trate esa salida como sensible: no la pegue en tickets públicos y no habilite `debug` junto con el modo plugin de agente (consulte [Operación y resolución de problemas](#operacion-y-resolucion-de-problemas)).

### Registrar el plugin en Pandora FMS

`redis_monitor` también puede registrarse en la consola de Pandora FMS como plugin de servidor estándar, de modo que Pandora FMS lo ejecute en el servidor que ejecuta los módulos en lugar de en una línea de comandos. Registrado así, el plugin mantiene el modo plugin de servidor: cada ejecución construye el documento de agente y lo entrega, y el agente con sus módulos aparece en la consola.

Use la ruta absoluta del ejecutable como comando del plugin y las claves documentadas como parámetros. La consola sustituye sus macros `_fieldN_` en el momento de la ejecución, de modo que los valores de cada módulo pueden aportarse sin editar el plugin:

```text
-server _field1_ -password _field2_ -metrics _field3_ -agent_name _field4_ -mode tentacle -tentacle_ip 127.0.0.1 -tentacle_port 41121
```

| Campo | Descripción | Valor de ejemplo |
| --- | --- | --- |
| `_field1_` | Dirección de Redis, incluido el puerto | `<REDIS_HOST>:<REDIS_PORT>` |
| `_field2_` | Contraseña de Redis. Viaja en la línea de comandos del módulo, así que trate la definición del módulo como sensible | — |
| `_field3_` | Secciones de `INFO` que se leen, separadas por espacios | `all` |
| `_field4_` | Nombre del agente que contendrá los módulos | `redis-monitoring` |

`-tentacle_ip 127.0.0.1` entrega al servidor de Tentacle de la máquina que ejecuta el plugin, de modo que el agente llega al servidor de Pandora FMS que ejecuta el módulo. Para copiar el documento en una carpeta de datos local, sustituya las opciones de Tentacle por `-mode local -local_folder /var/spool/pandora/data_in`.

<!-- SCREENSHOT NEEDED: Formulario de registro de plugins de servidor en la consola de Pandora FMS, mostrando el comando del plugin redis_monitor y sus campos de parámetros y macros. -->

Una vez registrado, el plugin está disponible al crear módulos de plugin, y cada módulo rellena los campos individualmente. El módulo se ejecuta en el servidor seleccionado para él, incluido un servidor de Pandora FMS remoto, de modo que cada instancia de Redis se monitoriza desde el servidor de Pandora FMS más cercano sin instalar nada en el host de Redis.

## Verificación

Ejecute el plugin manualmente desde un terminal, pasando el archivo de configuración como primer argumento:

```bash
./redis_monitor /etc/pandora/plugins/redis_config.conf
```

La forma relativa `./redis_monitor redis_config.conf` funciona cuando el terminal ya está en el directorio que contiene ambos archivos. Cada ejecución se realiza una vez y termina.

En modo plugin de agente, una ejecución correcta imprime un bloque XML `<module>` por campo en la salida estándar, con esta forma:

```xml
<module>
	<name><![CDATA[redis_version]]></name>
	<type>generic_data_string</type>
	<data><![CDATA[7.2.4]]></data>
	<module_group>Redis</module_group>
</module>
<module>
	<name><![CDATA[connected_clients]]></name>
	<type>generic_data</type>
	<data><![CDATA[3]]></data>
	<module_group>Redis</module_group>
</module>
<module>
	<name><![CDATA[db0]]></name>
	<type>generic_data_string</type>
	<data><![CDATA[keys=12,expires=4,avg_ttl=0]]></data>
	<module_group>Redis</module_group>
</module>
```

`<module_group>` aparece solo cuando `module_group` está definido.

En modo plugin de servidor, una ejecución correcta no imprime nada y el agente configurado en `agent_name` aparece en Pandora FMS con sus módulos. El plugin no informa el resultado de la entrega en su estado de salida, así que confirme la llegada en la consola en lugar de confiar en el comando.

<!-- SCREENSHOT NEEDED: Vista del agente en Pandora FMS con los módulos generados por redis_monitor para una instancia de Redis. -->

## Entender los resultados

Cada módulo es un campo de la respuesta `INFO` de Redis. El plugin lee las secciones indicadas en `metrics` y, por cada campo, crea un módulo con el nombre del campo y con un grupo cuando `module_group` está definido.

### Nombres y tipos de módulo

- El nombre del módulo es el nombre del campo de Redis exactamente como lo devuelve el servidor: sin prefijo y sin prefijo de sección. `used_memory` sigue siendo `used_memory`, y una línea de keyspace llega como `db0`.
- Un valor que contiene una letra se convierte en un módulo `generic_data_string`: `redis_version`, `role`, `maxmemory_policy`, `used_memory_human` (`1.05M`), `rdb_last_bgsave_status` y `db0` (`keys=12,expires=4,avg_ttl=0`).
- Un valor solo con dígitos se convierte en un módulo `generic_data`: `connected_clients`, `used_memory`, `uptime_in_seconds`, `maxmemory`, `mem_fragmentation_ratio`, y también los indicadores numéricos `redis_git_dirty` y `aof_enabled`.
- El plugin no añade descripción, unidad ni umbral, y tampoco un módulo de disponibilidad. El catálogo de módulos es exactamente el conjunto de campos que devuelven las secciones seleccionadas para su versión y configuración de Redis.

No hay módulo de conectividad: cuando una ejecución no puede leer la instancia, no publica ningún módulo y los módulos existentes no reciben datos nuevos.

### Secciones que puede leer

`metrics` acepta cualquier nombre de sección que acepte el servidor Redis, separado por espacios; el plugin solo pasa cada nombre a `INFO`, de modo que los nombres coinciden sin distinguir mayúsculas y minúsculas, como hace Redis. `all` lee todas las secciones. Las secciones que suelen usarse con este plugin son:

| Valor de `metrics` | Qué lee | Módulos representativos |
| --- | --- | --- |
| `server` | Identidad, versión y tiempo de actividad | `redis_version`, `redis_mode`, `os`, `arch_bits`, `process_id`, `run_id`, `tcp_port`, `uptime_in_seconds`, `uptime_in_days`, `executable`, `config_file` |
| `clients` | Conexiones de cliente | `connected_clients`, `blocked_clients`, `client_longest_output_list`, `client_biggest_input_buf` |
| `memory` | Memoria | `used_memory`, `used_memory_human`, `used_memory_rss`, `used_memory_peak`, `maxmemory`, `maxmemory_policy`, `mem_fragmentation_ratio`, `mem_allocator` |
| `persistence` | Estado de RDB y AOF | `loading`, `rdb_changes_since_last_save`, `rdb_last_bgsave_status`, `rdb_last_save_time`, `aof_enabled`, `aof_last_write_status`, `aof_current_size` |
| `stats` | Contadores y tasas | `total_connections_received`, `total_commands_processed`, `instantaneous_ops_per_sec`, `keyspace_hits`, `keyspace_misses`, `evicted_keys`, `expired_keys` |
| `replication` | Rol y réplicas | `role`, `connected_slaves`, `master_replid`, `master_repl_offset`; los campos `master_*` y `slave*` dependen del rol de la instancia |
| `cpu` | CPU consumida por el servidor | `used_cpu_sys`, `used_cpu_user`, `used_cpu_sys_children`, `used_cpu_user_children` |
| `commandstats` | Contadores por comando | `cmdstat_get`, `cmdstat_set`, con valores como `calls=1,usec=2,usec_per_call=2.00` |
| `cluster` | Estado del clúster | `cluster_enabled` |
| `keyspace` | Claves por base de datos | `db0`, `db1`, con valores como `keys=12,expires=4,avg_ttl=0` |
| `all` | Todas las secciones anteriores | — |

Los campos aparecen o desaparecen según la versión de Redis y la configuración de la instancia (por ejemplo, los campos de AOF existen solo cuando AOF está habilitado), así que un módulo que falta en la salida es un campo que el servidor no informó en esa ejecución.

## Operación y resolución de problemas

### Operación diaria

- El plugin no guarda estado: cada ejecución lee la instancia en ese momento, así que puede ejecutarse manualmente en cualquier momento.
- En modo plugin de servidor, prográmelo desde Pandora FMS, por ejemplo mediante el planificador de plugins de servidor o `cron`. En modo plugin de agente, el agente de Pandora FMS lo ejecuta según la planificación de plugin configurada.
- Use `debug=1` en las ejecuciones manuales para imprimir los detalles de conexión, la lista de secciones y la respuesta completa de `INFO`. `debug` escribe en la salida estándar, así que en modo plugin de agente se intercala con el XML de módulos y el agente no puede interpretar la salida: no lo habilite nunca en una ejecución programada en modo plugin de agente.
- Como los nombres de módulo no llevan prefijo de instancia, mantenga un agente por instancia y use `module_group` para separar estos módulos de otros del mismo agente.

### Resolución de problemas

- **No se imprime XML de módulos en modo plugin de agente** — compruebe que `as_agent_plugin=1` está en efecto (cuando ambas claves de modo están vacías, el plugin se ejecuta como plugin de servidor), que `metrics` no está vacío y que el archivo de configuración es el primer argumento del comando.
- **El agente nunca aparece en Pandora FMS en modo plugin de servidor** — la entrega falló de forma silenciosa. Ejecute una vez con `debug=1` para ver el motivo: la falta de `mode` y la falta de `local_folder` solo se informan con `debug` habilitado, y un fallo de Tentacle imprime el mensaje del cliente solo con `debug` habilitado.
- **No se encuentra `tentacle_client` o no puede conectar** — asegúrese de que el cliente está instalado y en el `PATH` (o defina `tentacle_client` con su ruta absoluta) y de que `tentacle_ip` y `tentacle_port` alcanzan el servidor de Tentacle.
- **Falla la entrega en la carpeta local** — compruebe que `local_folder` existe, que el usuario que ejecuta el plugin puede escribir en ella y que designa una carpeta, no un archivo. El error se imprime solo con `debug=1`.
- **`NOAUTH` o un error de autenticación de Redis** — la instancia exige una contraseña y `password` está vacío o es incorrecto. Si la instancia exige además un nombre de usuario ACL, este plugin no puede autenticarse (no tiene clave de nombre de usuario).
- **Conexión rechazada o tiempo de espera agotado** — el plugin no puede alcanzar `server`. Compruebe el host, el puerto, el cortafuegos y que Redis escucha en una dirección alcanzable desde el host de monitorización.
- **Algunos módulos antiguos dejan de actualizarse tras una actualización o un cambio de configuración de Redis** — el campo ya no existe en la salida de `INFO`. Ajuste `metrics` o las alertas de ese módulo.
- **La lista de módulos está vacía** — `metrics` está vacío o nombra secciones que la instancia no informa. Empiece con `metrics=all` y redúzcalo cuando vea qué módulos llegan.

## Referencia

### Claves del archivo de configuración

| Nombre | Obligatoria | Valor por defecto | Descripción |
| --- | --- | --- | --- |
| `server` | Sí | — | Dirección de Redis, como `<REDIS_HOST>:<REDIS_PORT>`. Incluya el puerto. |
| `password` | No | Vacío (sin autenticación) | Contraseña que se envía a Redis. El plugin no tiene clave de nombre de usuario. |
| `metrics` | Sí | — | Secciones de `INFO` que se leen, separadas por espacios. `all` lee todas las secciones. |
| `as_agent_plugin` | No | `0` | `1` (o cualquier valor mayor que `0`) imprime el XML de módulos en la salida estándar. |
| `as_server_plugin` | No | `1` cuando no se define ninguna clave de modo | `1` (o cualquier valor mayor que `0`) construye y entrega el documento de agente. Cuando ambas claves de modo valen `1`, se ejecutan los dos modelos. |
| `agent_name` | Obligatoria en modo plugin de servidor | — | Nombre del agente que se crea en Pandora FMS. |
| `module_group` | No | Vacío (no se envía grupo) | Nombre de un grupo de módulos existente que se asigna a cada módulo generado. Se resuelve sin distinguir mayúsculas y minúsculas; un nombre desconocido deja los módulos sin ese grupo. |
| `mode` | Obligatoria en modo plugin de servidor | Vacío | `tentacle` entrega con el cliente de Tentacle; cualquier otro valor copia el documento de agente en `local_folder`. |
| `transfer_mode` | No | Vacío | Clave alternativa de `mode`, que solo se lee cuando `mode` está vacío. |
| `local_folder` | Obligatoria cuando `mode` no es `tentacle` | — | Carpeta de destino de la copia del documento de agente. |
| `temp` | No | `/tmp` en Linux | Carpeta donde se escribe el documento de agente antes de la entrega. Se acepta `tmp` como clave alternativa. |
| `tentacle_ip` | Obligatoria cuando `mode=tentacle` | — | Dirección del servidor de Tentacle. |
| `tentacle_port` | No | `41121` | Puerto del servidor de Tentacle. |
| `tentacle_client` | No | `tentacle_client` | Ejecutable del cliente de Tentacle, resuelto en el `PATH` o indicado con ruta absoluta. |
| `tentacle_opts` | No | Vacío | Opciones adicionales que se pasan al cliente de Tentacle, separadas por espacios. |
| `debug` | No | `0` | `1` (o cualquier valor mayor que `0`) imprime los detalles de conexión, la lista de secciones y mensajes de diagnóstico en la salida estándar. |

Las claves booleanas se habilitan con cualquier valor numérico mayor que `0`; `0`, un valor vacío o un valor no numérico significan deshabilitado.

### Ejecución por línea de comandos

```bash
./redis_monitor [config-file] [ -key value ... ]
```

| Condición | Comportamiento |
| --- | --- |
| El primer argumento nombra un archivo existente | El plugin lo lee como archivo de configuración y aplica los argumentos restantes sobre sus valores |
| El primer argumento no es un archivo, o la ruta del archivo va después de una opción | El archivo no se lee; el plugin se ejecuta con los valores por defecto y los argumentos |
| `-key value` | Sustituye el valor de `key` |
| `--key value` o `-key=value` | No se reconocen: el par se lee como una clave distinta que el plugin ignora, así que la clave documentada conserva su valor por defecto o el del archivo |
| Argumentos que no forman un par `-key value` | Se ignoran; un argumento final sin valor no se informa |
| La línea de comandos está vacía | El plugin se ejecuta con los valores por defecto; no se imprime ningún texto de uso |
| `-h` o `--help` | No existe opción de ayuda: no produce salida de ayuda y se trata como cualquier otra opción desconocida |

Las claves desconocidas se aceptan y se ignoran: el plugin no valida el conjunto de claves.

### Comportamiento de la entrega

| Situación | Resultado |
| --- | --- |
| `mode=tentacle` y la transferencia con Tentacle tiene éxito | El archivo temporal se elimina tras la transferencia |
| `mode=tentacle` y la transferencia falla | El documento no se entrega; el mensaje del cliente se imprime solo con `debug=1` |
| Cualquier otro `mode` | El documento se copia en `local_folder` y el archivo temporal se elimina |
| `mode` vacío y sin alternativa `transfer_mode` | No se entrega nada; el motivo se imprime solo con `debug=1` |
| Resultado de la entrega | No se refleja en el estado de salida; verifíquelo en la consola de Pandora FMS |

### Identidad del addon

| Campo | Valor |
| --- | --- |
| Identificador en el Marketplace | `redis` |
| Nombre en el Marketplace | Redis monitoring |
| Versión del addon | `1.1` |
| Última actualización en el Marketplace | 2025-11-03 |
| Paquete del Marketplace | `redis.1.1.zip` |
| Licencia | Descarga gratuita |
| Tipo del Marketplace | Miscelaneus |
| Flujo de trabajo | Plugin de monitorización, en modo plugin de agente o de servidor |
| Ejecutable | `redis_monitor` |
