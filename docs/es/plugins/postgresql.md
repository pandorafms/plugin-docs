# Plugin de monitorización de PostgreSQL

*Última actualización del artículo: 2026-10-26.*

<!-- DRAFT: Datos verificados contra la definición del paquete del addon y la superficie documentada del ejecutable distribuido. No se realizó ninguna ejecución real, conexión a base de datos ni captura de consola para esta página. -->

## Qué hace

El plugin de monitorización de PostgreSQL convierte sus propias consultas SQL en módulos de Pandora FMS. En cada ejecución se conecta a un servidor PostgreSQL, ejecuta todas las consultas indicadas en un archivo de configuración y genera un módulo por consulta. Es un plugin de servidor: Pandora FMS lo ejecuta en un servidor, o usted lo lanza manualmente desde una terminal.

El plugin está dirigido por consultas. No incorpora un modelo fijo de métricas de PostgreSQL: la configuración de ejemplo que acompaña al addon consulta conexiones, roles, versión, bloqueos, confirmaciones, reversiones y contadores de tuplas, y usted puede sustituir esas consultas por sus propias sentencias `SELECT`.

Cada ejecución recorre una vez todas las consultas del archivo y entrega el resultado de una de estas tres formas:

- **Archivo de datos de agente** (opción por defecto): el plugin escribe un archivo XML de datos de agente en el directorio de datos de Pandora FMS e imprime `1`.
- **Tentacle**: con `--tentacle_address`, el plugin escribe el mismo archivo, lo envía con `tentacle_client` y después imprime `1`.
- **XML de módulos por la salida estándar**: con `--as_agent_plugin 1`, el plugin imprime un bloque `<module>` por consulta en la salida estándar y no escribe ningún archivo.

El plugin no conserva estado entre ejecuciones, de modo que los valores que publica son los que PostgreSQL devuelve en el momento de la ejecución.

## Preparación

### Compatibilidad y disponibilidad

| Ámbito | Estado | Evidencia |
|--------|--------|-----------|
| Acceso de red desde la máquina que ejecuta el plugin al listener de PostgreSQL (TCP, `--port`, `5432` por defecto) | `Required` | Los parámetros de conexión `-i` y `--port` |
| Un rol de PostgreSQL con permiso de lectura sobre `pg_stat_activity`, `pg_roles`, `pg_locks`, `pg_stat_database` y `pg_database` | `Required` | Las consultas de ejemplo que acompañan al addon |
| PostgreSQL 9.6 o posterior mientras se mantengan las consultas de `wait_event` incluidas | `Required` | `pg_stat_activity.wait_event` existe desde PostgreSQL 9.6; en servidores anteriores esas dos consultas fallan y sus módulos se omiten |
| Plugin Server de Pandora FMS habilitado con el auxiliar `plugin_exec` instalado, cuando el plugin se registra en Pandora FMS | `Required` | Pandora FMS ejecuta los módulos de plugin a través del Plugin Server |
| Un directorio de datos de Pandora FMS con permiso de escritura para el usuario que ejecuta el plugin, para la entrega por archivo y por Tentacle | `Required` | `--data_dir`, `/var/spool/pandora/data_in/` por defecto |
| Sistema operativo y distribución de la máquina que ejecuta el plugin | `Not validated` | No hay ningún sistema operativo registrado para la versión `1.1` |
| Versiones del servidor PostgreSQL | `Not validated` | No hay matriz de versiones de PostgreSQL registrada para este addon |
| Versiones concretas de Pandora FMS | `Not validated` | No hay matriz de versiones registrada para este addon |
| Entrega por Tentacle | `Not validated` | `--tentacle_address` necesita un `tentacle_client` accesible; no hay ninguna ejecución de ese tipo registrada |

El registro del Marketplace indica que este plugin ya no se mantiene ni actualiza activamente y recomienda un plugin alternativo para instalaciones nuevas. Ese mismo registro limita la descarga a usuarios con licencia; consulte [Identidad del addon](#identidad-del-addon).

### Requisitos

1. **Conectividad** entre la máquina que ejecuta el plugin y el servidor PostgreSQL. Cuando el plugin se ejecuta como plugin de servidor, esa máquina es el servidor de Pandora FMS que ejecuta el módulo, que puede ser un servidor remoto.
2. **Un rol y una contraseña de PostgreSQL** para la monitorización. Las consultas incluidas leen vistas de todo el clúster, así que un rol que solo ve sus propias sesiones cuenta de menos en los módulos de conexiones: para ver todas las sesiones, use un superusuario o, en PostgreSQL 10 y posterior, un rol con `pg_read_all_stats`.
3. **Una instalación de Pandora FMS** con el Plugin Server habilitado, la consola para registrar el plugin y crear el módulo, y un directorio de datos con permiso de escritura para el modo de entrega elegido.
4. **El archivo de consultas**. El addon incluye un ejemplo; puede editarlo o escribir el suyo. Consulte [Archivo de configuración de consultas](#archivo-de-configuracion-de-consultas).

### Instalar el addon

Descargue el paquete `.pspz2` desde la entrada del Marketplace, limitada a usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.postgresql_plugin](https://marketplace.pandorafms.com/entries/pandorafms.postgresql_plugin)

Regístrelo en la consola:

1. Abra **Servers → Register plugin** y suba el archivo `.pspz2` con **Upload file**.
2. Pandora FMS descomprime el paquete en el almacén de adjuntos de plugins de la consola, registra el plugin **Pandora PostgreSQL** con un tiempo de espera máximo de 20 segundos y 10 macros, y apunta el comando del plugin al ejecutable instalado.
3. Si el nombre del plugin ya está registrado, el paquete se rechaza con `Plugin already registered. Aborting!`.

<!-- SCREENSHOT NEEDED: Pantalla de registro de plugins con un paquete de plugin seleccionado y sin datos de plugin cargados todavía. -->

El ejecutable se llama `pandora_postgresql`. Si prefiere registrar el plugin a mano en lugar de importar el paquete, coloque el ejecutable en el servidor de Pandora FMS e indique su ruta absoluta como comando del plugin; los parámetros y las macros son los de [Registrar el plugin de servidor](#registrar-el-plugin-de-servidor).

## Configuración

### Registrar el plugin de servidor

Un plugin registrado de esta forma queda disponible al crear módulos de plugin, y cada módulo rellena las macros individualmente. La definición empaquetada usa esta cadena de parámetros:

```text
-d _field1_ -u _field2_ -p _field3_ -i _field4_ --port _field5_ --conf _field6_ --agent_name _field7_ --prefix_module _field8_ -g _field9_ _field10_
```

La definición empaquetada encierra cada macro entre comillas. Si registra el plugin manualmente, use la forma sin comillas de arriba para que cada valor llegue al ejecutable sin espacios alrededor.

| Campo | Descripción | Valor de ejemplo |
|-------|-------------|------------------|
| `_field1_` | Nombre de la base de datos | `<DB_NAME>` |
| `_field2_` | Usuario de PostgreSQL | `<USERNAME>` |
| `_field3_` | Contraseña de ese usuario | `<PASSWORD>` |
| `_field4_` | Host o dirección IP de PostgreSQL | `<TARGET_HOST>` |
| `_field5_` | Puerto de la base de datos; `5432` por defecto | `5432` |
| `_field6_` | Ruta absoluta al archivo de consultas | `<PATH_TO_CONFIG>` |
| `_field7_` | Nombre del agente; `_agentname_` por defecto | `_agentname_` |
| `_field8_` | Prefijo de los nombres de módulo | `<DB_NAME>` |
| `_field9_` | Grupo de destino; `Postgres` por defecto | `<GROUP_NAME>` |
| `_field10_` | Argumentos extra sin procesar, añadidos al final | `--data_dir /var/spool/pandora/data_in/` |

Dos valores por defecto del paquete requieren atención antes de la primera ejecución:

- **La macro de contraseña no está oculta.** El paquete importa `_field3_` como macro visible, así que la contraseña que introduzca se guarda sin cifrar y se muestra en la lista de macros. Active la opción **Hide value** de la macro, que guarda el valor como macro oculta y cifrada, y establezca la contraseña después.
- **El prefijo por defecto es un punto.** El plugin une el prefijo al nombre del módulo con un guion bajo, así que si deja el `.` del paquete obtendrá nombres como `._number_connections`. Sustitúyalo por un prefijo significativo, como el nombre de la base de datos, o déjelo vacío.

<!-- SCREENSHOT NEEDED: Lista de macros del plugin Pandora PostgreSQL registrado con una base de datos, usuario, contraseña enmascarada, host, puerto, ruta de configuración, nombre de agente, prefijo y grupo de laboratorio, sin credenciales reales. -->

### Archivo de configuración de consultas

El archivo es texto plano con una consulta por línea y cuatro campos separados por dos puntos:

```text
nombre_modulo:SELECT ...:tipo_modulo:descripción
```

- La descripción es opcional. Una línea con menos de tres campos detiene la ejecución antes de generar ningún módulo, con `It is mandatory to specify name, query and type!`.
- Se ignoran las líneas que contienen `#` y las líneas vacías. Use los comentarios en su propia línea.
- El nombre del módulo se escribe tal cual como nombre del módulo de Pandora FMS, con el prefijo de `--prefix_module` delante.
- El tipo de módulo se escribe en la definición del módulo tal como aparece. Use tipos de módulo de Pandora FMS: `generic_data`, `generic_data_inc`, `generic_data_string` o `generic_proc`.
- `_database_` en una consulta se sustituye por el nombre de base de datos indicado con `-d`, entre comillas simples, de modo que `WHERE db.datname = _database_` pasa a ser `WHERE db.datname = '<DB_NAME>'`.
- La línea completa se divide por todos los dos puntos. No use `:` dentro de la sentencia, incluidos los casts `::` y las horas literales: la consulta se trunca y el módulo falla.

Ejemplo mínimo:

```text
number_connections:SELECT count(*) FROM pg_stat_activity;:generic_data:Number of sessions
database_size_mb:SELECT ROUND(pg_database_size(current_database())/1024/1024);:generic_data:Database size in MB
db_version:SELECT version();:generic_data_string:PostgreSQL version
commits:SELECT sum(xact_commit) FROM pg_stat_database WHERE datname = _database_;:generic_data:Commits in the monitored database
```

Coloque el archivo donde el usuario que ejecuta el plugin pueda leerlo. La macro por defecto del paquete apunta a `/var/www/html/pandora_console/attachment/plugin/pandora_postgresql.conf`, junto al ejecutable en una instalación estándar; cámbiela por la ruta que use realmente.

El addon ejecuta todas las sentencias que encuentra. Mantenga el archivo con sentencias `SELECT` de solo lectura y verifique cada consulta manualmente antes de añadirla a un archivo de producción.

### Crear el módulo de plugin

1. Abra el agente que alojará los módulos y cree un módulo de tipo plugin.
2. Seleccione el plugin **Pandora PostgreSQL** registrado y rellene las macros de la base de datos de destino.
3. Guarde el módulo.

<!-- SCREENSHOT NEEDED: Formulario de creación de un módulo de plugin con el plugin Pandora PostgreSQL seleccionado y sus macros rellenas con valores de laboratorio. -->

Cada ejecución de un módulo de plugin recorre todo el archivo de consultas y publica todos sus módulos. Cree un módulo de plugin por archivo de consultas y base de datos; varios módulos apuntando al mismo archivo repiten las mismas consultas en cada intervalo.

`_agentname_` se resuelve al agente propietario del módulo, así que en este modo los módulos generados quedan en ese agente en lugar de crear uno aparte. Sustitúyalo por un nombre literal solo cuando quiera un agente distinto.

Un módulo de plugin almacena como valor la salida estándar del plugin. Mantenga el modo de entrega por defecto, que escribe el archivo de datos de agente e imprime `1`, para que el módulo registre `1` y el archivo de datos de agente lleve las métricas. Añada `--as_agent_plugin 1` solo cuando el módulo deba recibir XML de módulos.

### Credenciales y transporte

- La contraseña forma parte de los parámetros del plugin. En un módulo de plugin vive en la macro almacenada; con una macro oculta se guarda cifrada. Evite pasar `-p <PASSWORD>` en una línea de comandos interactiva: el historial del shell y la lista de procesos pueden exponerla mientras el plugin se ejecuta.
- El addon no expone parámetros de TLS. El cifrado y la autenticación de la conexión a la base de datos dependen de la configuración del servidor PostgreSQL y del cliente de la máquina que ejecuta el plugin.
- Use un rol de PostgreSQL dedicado a Pandora FMS y conceda solo lo que necesiten sus consultas.

## Verificación

Ejecute el plugin manualmente en el servidor de Pandora FMS, con el mismo usuario que ejecuta los módulos de plugin:

```bash
./pandora_postgresql -d <DB_NAME> -u <USERNAME> -p <PASSWORD> -i <TARGET_HOST> \
    --port 5432 --conf <PATH_TO_CONFIG> --agent_name PostgreSQL
```

El modo por defecto escribe un archivo de datos de agente en `--data_dir` e imprime `1`. Un `0` impreso significa que la ejecución ha fallado; consulte [Operar y resolver problemas](#operar-y-resolver-problemas).

Para inspeccionar los módulos generados sin escribir archivo, añada `--as_agent_plugin 1`. El plugin imprime entonces un bloque `<module>` por consulta, por ejemplo:

```xml
<module>
	<name><![CDATA[number_connections]]></name>
	<type>generic_data</type>
	<datalist>
	<data>
		<value><![CDATA[12]]></value>
	</data>
	</datalist>
	<description><![CDATA[Number of sessions]]></description>
</module>
```

Los valores del ejemplo son ilustrativos. Cuando el módulo de plugin se ejecute en su intervalo, confirme en la consola que el agente contiene un módulo por consulta y que el propio módulo de plugin informa `1`.

<!-- SCREENSHOT NEEDED: Lista de módulos del agente tras la primera ejecución del plugin, con los módulos de PostgreSQL generados y el valor 1 del módulo de plugin. -->

No se realizó ninguna ejecución real, conexión a base de datos ni ingesta en consola durante la redacción de esta página. Los pasos anteriores son comprobaciones del operador, no resultados observados.

## Entender los resultados

Una ejecución correcta genera un agente y un módulo por consulta:

| Propiedad | Valor |
|-----------|-------|
| Nombre del agente | `--agent_name`; `PostgreSQL` por defecto, `_agentname_` en el plugin registrado |
| Descripción del agente | `PostgreSQL agent` |
| Grupo | `--group`; `Postgres` por defecto |
| Intervalo | Vacío en la definición del agente; un agente que ya existe conserva su propio intervalo |
| Nombre del módulo | El primer campo de la línea de consulta, con el prefijo `<prefijo>_` cuando se define `--prefix_module` |
| Tipo de módulo | El tercer campo de la línea de consulta, tal como se escribe |
| Descripción del módulo | El cuarto campo de la línea de consulta, vacío si se omite |

Cada módulo se emite con un `<datalist>`: una entrada por fila devuelta por la consulta, con las columnas de una fila unidas por `;`. Una consulta de una fila y una columna —un `count(*)`, por ejemplo— produce una lista con una sola entrada. Mantenga las consultas de monitorización en una fila y una columna cuando espere un valor único.

El plugin no define umbrales, unidades ni plantillas de alerta. Los umbrales y el intervalo del módulo se configuran en Pandora FMS sobre el módulo generado.

### Consultas de ejemplo

El archivo de ejemplo que acompaña al addon define estas consultas:

| Módulo | Consulta | Notas |
|--------|----------|-------|
| `number_connections` | `SELECT count(*) FROM pg_stat_activity;` | Sesiones de todo el clúster, de todas las bases de datos, incluida la sesión de monitorización |
| `connections_waiting_in_locks` | `SELECT count(*) FROM pg_stat_activity WHERE wait_event = 'Lock';` | Sesiones en espera de un bloqueo pesado |
| `connections_idle_in_transaction` | `SELECT count(*) FROM pg_stat_activity WHERE wait_event = 'idle in transaction';` | Siempre `0`: `idle in transaction` es un estado de sesión, no un evento de espera, así que el filtro no coincide con ninguna fila |
| `number_users` | `SELECT COUNT(usename) FROM pg_stat_activity;` | Sesiones que tienen nombre de usuario, no roles distintos |
| `number_roles` | `SELECT count(*) FROM pg_roles;` | Roles del clúster |
| `psql_version` | `SELECT version();` | Cadena con la versión del servidor |
| `num_blocks` | `SELECT COUNT(*) FROM pg_locks;` | Filas de `pg_locks`, es decir, entradas de bloqueo actuales, no interbloqueos |
| `number_commits` | `sum(xact_commit)` de la base de datos monitorizada | Contador acumulado |
| `number_rollbacks` | `sum(xact_rollback)` de la base de datos monitorizada | Contador acumulado |
| `tuples_returned` | `sum(tup_returned)` de la base de datos monitorizada | Contador acumulado |
| `tuples_searched` | `sum(tup_fetched)` de la base de datos monitorizada | Contador acumulado |
| `tuples_inserted` | `sum(tup_inserted)` de la base de datos monitorizada | Contador acumulado |
| `tuples_updated` | `sum(tup_updated)` de la base de datos monitorizada | Contador acumulado |
| `tuples_removed` | `sum(tup_deleted)` de la base de datos monitorizada | Contador acumulado |
| `state` | `SELECT state FROM pg_stat_activity WHERE datname = _database_;` | Una fila por sesión de la base de datos |
| `number_connections_list` | `SELECT * FROM pg_stat_activity;` | Una fila por sesión, con las columnas unidas por `;` |
| `number_databases_list` | `select * from pg_database;` | Una fila por base de datos |

Los contadores usan `generic_data`, así que Pandora FMS almacena el valor acumulado que devuelve PostgreSQL. Defina el módulo como `generic_data_inc` en el archivo de consultas si quiere el incremento entre ejecuciones.

Una consulta que falla no detiene la ejecución: el plugin escribe el error en la salida de error y continúa con la consulta siguiente, de modo que su módulo falta en esa ejecución mientras los demás se publican igualmente.

## Operar y resolver problemas

- Cada ejecución abre una conexión, ejecuta las consultas de forma secuencial y cierra la conexión. No hay paralelismo ni opción de depuración o de modo detallado; los canales de diagnóstico son la salida estándar, la salida de error y el código de salida.
- Cuando el plugin se ejecuta como plugin de servidor, Pandora FMS lo programa en el intervalo del módulo. Ejecútelo manualmente solo con el mismo usuario y las mismas macros que el módulo.
- El paquete registra un tiempo de espera máximo de 20 segundos por ejecución, y Pandora FMS aplica el menor entre ese valor y el `plugin_timeout` del servidor. Un archivo con sentencias lentas puede agotarlo; mantenga las consultas baratas.

| Señal | Causa y comprobación |
|-------|----------------------|
| `the following arguments are required: -d/--database, -u/--user, -p/--password, -i/--ip, --conf` | Falta un argumento obligatorio. El analizador muestra su ayuda y termina con estado `2` |
| `Error while creating PostgreSQL table ...` seguido de `Error: ...` y `0` | La conexión falló: host o puerto inaccesible, base de datos incorrecta, credenciales erróneas o `pg_hba.conf` rechazando al cliente. El primer mensaje se imprime en la salida estándar y el resto en la salida de error |
| `Error al conectarse ...` | No se pudo abrir el archivo de consultas. Compruebe `--conf` y los permisos del archivo para el usuario que ejecuta el plugin |
| `error with the query:<consulta>.<error>` | PostgreSQL rechazó una consulta. Las demás se ejecutan igualmente; corrija la sentencia o los privilegios del rol |
| `It is mandatory to specify name, query and type!` | Una línea de consulta tiene menos de tres campos separados por dos puntos. La ejecución se detiene sin generar módulos |
| Falta un módulo mientras aparecen los demás | Su consulta falló, su línea está mal formada o usa una columna que no existe en esa versión de PostgreSQL |
| `ERROR - Could not write file: ..., please check directory permissions` | `--data_dir` no existe o el usuario que ejecuta el plugin no puede escribir en él. La ejecución termina con estado `1` |
| `Tentacle error` o `Tentacle error: ...` y ningún `1` | Falló la entrega por Tentacle: falta `tentacle_client` o `--tentacle_address`/`--tentacle_port` son incorrectos. El archivo de datos permanece en `--data_dir` |
| Se imprime `0` en lugar de `1` | La ejecución falló antes de generar módulos; lea los mensajes anteriores |
| El módulo informa `1` pero no llegan datos a Pandora FMS | El archivo de datos se escribió donde el Data Server no lo lee. Compruebe `--data_dir` frente al `incomingdir` del servidor |

El plugin termina con estado `0` tanto en una ejecución correcta como en una ejecución que falló después de leer sus argumentos —un error de conexión, un archivo de consultas ilegible o una línea mal formada—, porque esos fallos se comunican con el `0` impreso y los mensajes de error, no con el código de salida. Use el valor impreso y el texto de los mensajes, y no solo el código de salida, para valorar una ejecución manual.

## Referencia

### Línea de comandos

```bash
./pandora_postgresql -d <DB_NAME> -u <USERNAME> -p <PASSWORD> -i <TARGET_HOST> [opciones]
```

| Nombre | Obligatorio | Por defecto | Descripción |
|--------|-------------|-------------|-------------|
| `-d`, `--database` | Sí | — | Base de datos a la que conectarse y valor sustituido en `_database_` |
| `-u`, `--user` | Sí | — | Usuario de PostgreSQL |
| `-p`, `--password` | Sí | — | Contraseña de ese usuario. No es el puerto |
| `-i`, `--ip` | Sí | — | Host o dirección IP de PostgreSQL |
| `--conf` | Sí | — | Ruta al archivo de configuración de consultas |
| `--port` | No | `5432` | Puerto de PostgreSQL |
| `--agent_name` | No | `PostgreSQL` | Nombre del agente escrito en el archivo de datos de agente |
| `--prefix_module` | No | Vacío | Prefijo unido a cada nombre de módulo con `_` |
| `-g`, `--group` | No | `Postgres` | Grupo escrito en la definición del agente |
| `--data_dir` | No | `/var/spool/pandora/data_in/` | Directorio donde se escribe el archivo de datos de agente |
| `--tentacle_address` | No | Vacío | Dirección del servidor Tentacle. Si se define, el archivo de datos se envía con `tentacle_client` |
| `--tentacle_port` | No | `41121` | Puerto del servidor Tentacle |
| `--as_agent_plugin` | No | `0` | `1` imprime el XML de los módulos en la salida estándar; cualquier otro valor escribe el archivo de datos de agente |
| `-h`, `--help` | No | — | Muestra la ayuda y termina |

### Campos del archivo de consultas

| Posición | Campo | Obligatorio | Descripción |
|----------|-------|-------------|-------------|
| 1 | Nombre del módulo | Sí | Nombre del módulo de Pandora FMS, sin el prefijo |
| 2 | Consulta | Sí | Sentencia SQL ejecutada tal cual, tras la sustitución de `_database_` |
| 3 | Tipo | Sí | Tipo de módulo de Pandora FMS escrito en la definición del módulo |
| 4 | Descripción | No | Descripción del módulo; vacía si se omite |

### Identidad del addon

| Propiedad | Valor |
|-----------|-------|
| Identificador en el Marketplace | `pandorafms.postgresql_plugin` |
| Nombre | PostgreSQL monitoring |
| Versión | `1.1` |
| Última actualización en el Marketplace | 2025-08-20 |
| Paquete | `pandorafms.postgresql_plugin.1.1.pspz2` |
| Nombre del plugin registrado | Pandora PostgreSQL |
| Licencia | One; la descarga está limitada a usuarios con licencia |
| Mantenimiento | El registro del Marketplace indica que el plugin ya no se mantiene activamente |
| Tiempo de espera máximo de ejecución | 20 segundos |
