# Plugin de monitorización de Azure PostgreSQL

*Última actualización del artículo: 2026-10-26.*

<!-- DRAFT: Datos verificados contra el ejecutable del addon y su archivo de configuración. No se realizó ninguna ejecución real contra Azure Monitor, ni ingesta en la consola, ni captura de consola para esta página. -->

## Qué hace

El plugin de monitorización de Azure PostgreSQL lee las métricas de Azure Monitor de un recurso de Azure Database for PostgreSQL y las convierte en un agente de Pandora FMS: 16 métricas de CPU, memoria, E/S de disco, almacenamiento, conexiones, tráfico de red y retardo de replicación. Es un plugin de servidor: Pandora FMS lo ejecuta en un servidor con el intervalo del módulo, o usted lo lanza manualmente desde una terminal.

En cada ejecución se autentica con una entidad de servicio de Microsoft Entra, pide a Azure Monitor el promedio de cada métrica sobre una ventana de tiempo y construye un documento de datos de agente. Trabaja únicamente con el identificador de recurso de su archivo de configuración: no se conecta a PostgreSQL, así que no necesita usuario ni contraseña de base de datos y funciona aunque la base de datos no sea accesible desde el servidor de Pandora FMS.

Cada ejecución entrega el resultado de una de estas tres formas:

- **Archivo de datos de agente** (opción por defecto): el plugin escribe un archivo XML de datos de agente en el directorio de datos de Pandora FMS e imprime `1`.
- **Tentacle**: con `--tentacle_address`, el plugin escribe el mismo archivo, lo envía con `tentacle_client` y después imprime `1`.
- **XML de módulos por la salida estándar**: con `--as_agent_plugin 1`, el plugin imprime un bloque `<module>` por valor en la salida estándar y no escribe ningún archivo.

El plugin no conserva estado entre ejecuciones: cada valor que publica es el promedio que Azure Monitor devuelve para la ventana solicitada en el momento de la ejecución.

## Preparación

### Compatibilidad y disponibilidad

| Ámbito | Estado | Evidencia |
|--------|--------|-----------|
| Versión del addon `1.0` (`pandorafms.azure_postgresql`) | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del addon](#identidad-del-addon) |
| Pandora FMS NG 784 y posteriores | `Soportado` | El Marketplace indica que todas sus integraciones son compatibles con Pandora FMS NG 784 y versiones posteriores. Es una declaración de todo el catálogo que cubre este addon, no un registro de pruebas |
| Una suscripción de Azure con el recurso de PostgreSQL que se va a monitorizar | `Requerido` | El plugin lee las métricas de Azure Monitor del recurso identificado en su archivo de configuración |
| Una entidad de servicio de Microsoft Entra con permiso de lectura sobre ese recurso | `Requerido` | La autenticación usa un identificador de inquilino, un identificador de aplicación y un secreto de cliente. Es un requisito previo, no una declaración de compatibilidad |
| Acceso HTTPS saliente desde el servidor de Pandora FMS a los extremos de Azure Monitor de la nube pública de Azure | `Requerido` | El plugin consulta Azure Monitor directamente y no expone ajustes de extremo, autoridad ni proxy |
| Un directorio de datos de Pandora FMS con permiso de escritura para el usuario que ejecuta el plugin, para la entrega por archivo y por Tentacle | `Requerido` | `--data_dir`, `/var/spool/pandora/data_in/` por defecto |
| Nubes soberanas o personalizadas de Azure | `Sin validar` | No existe ningún ajuste de extremo ni de autoridad, así que el plugin no permite seleccionar una nube no pública |
| Sistema operativo y distribución de la máquina que ejecuta el plugin | `Sin validar` | No hay ningún sistema operativo registrado para la versión `1.0` |
| Tipo y versión del servidor Azure Database for PostgreSQL | `Sin validar` | El plugin solicita una lista fija de 16 nombres de métrica. No hay matriz de tipos de servidor ni de versiones registrada |
| Entrega por Tentacle | `Sin validar` | `--tentacle_address` necesita un `tentacle_client` accesible; no hay ninguna ejecución de ese tipo registrada |

El registro del Marketplace limita la descarga a usuarios con licencia. No incluye ninguna declaración de mantenimiento ni de obsolescencia; consulte [Identidad del addon](#identidad-del-addon).

### Requisitos

1. **Una instalación de Pandora FMS** con el Plugin Server habilitado, la consola para registrar el plugin y crear el módulo, y un directorio de datos con permiso de escritura para el modo de entrega elegido.
2. **Una suscripción de Azure** con el recurso de Azure Database for PostgreSQL que se va a monitorizar.
3. **Una entidad de servicio de Microsoft Entra** y su secreto, con permiso de lectura sobre ese recurso.
4. **El identificador de recurso** del recurso de PostgreSQL, en la forma larga `/subscriptions/.../resourceGroups/.../providers/...`.
5. **Los archivos del addon** en el servidor de Pandora FMS que ejecutará el plugin.

### Preparar el acceso a Azure

1. En Microsoft Entra ID, elija o cree un registro de aplicación para la monitorización. En su información general, copie el **identificador de directorio (inquilino)** y el **identificador de aplicación (cliente)**.
2. Cree un secreto de cliente para esa aplicación y copie su **valor**, no su identificador: el valor solo se muestra al crear el secreto.
3. Conceda a la aplicación permiso de lectura sobre el recurso de PostgreSQL o sobre el grupo de recursos que lo contiene. El permiso de solo lectura es suficiente, porque el plugin únicamente lee el recurso y sus métricas de Azure Monitor.
4. Abra el recurso de PostgreSQL en el portal de Azure, seleccione **Vista JSON** en la información general y copie el valor de su campo `id`. Esa cadena es el identificador de recurso que necesita el plugin.

Mantenga el valor del secreto fuera de tiques, chats y capturas de pantalla. El plugin lo guarda en un archivo de texto plano (consulte [Archivo de credenciales y recurso](#archivo-de-credenciales-y-recurso)).

<!-- SCREENSHOT NEEDED: Vista general de un recurso Azure Database for PostgreSQL en el portal de Azure con la vista JSON abierta, mostrando el campo id y con los nombres de suscripción, inquilino, grupo de recursos y servidor tapados. -->

### Instalar el addon

Descargue el paquete del addon desde la entrada del Marketplace, limitada a usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.azure_postgresql](https://marketplace.pandorafms.com/entries/pandorafms.azure_postgresql)

El paquete contiene el ejecutable `pandora_azurepostgresql` y una plantilla de configuración `pandora_azurepostgresql.conf`. Copie el ejecutable al servidor de Pandora FMS que lo ejecutará y dele permiso de ejecución. El directorio recomendado para los plugins de servidor es `/usr/share/pandora_server/util/plugin/`; sirve cualquier directorio legible y ejecutable por el usuario que ejecuta los módulos de plugin.

Coloque el archivo de configuración donde ese mismo usuario pueda leerlo, fuera de la raíz web, y restrinja su acceso a su propietario, porque contiene el secreto de cliente.

## Configuración

### Archivo de credenciales y recurso

El plugin lee todos sus datos de conexión del archivo que se pasa con `--conf`. Es texto plano con una línea `clave:valor` por ajuste:

```ini
#credentials
tenant_id:<TENANT_ID>
client_id:<CLIENT_ID>
secret:<CLIENT_SECRET>
#id resources
serverpostgres_id:<POSTGRES_RESOURCE_ID>
```

| Clave | Obligatorio | Descripción |
|-------|-------------|-------------|
| `tenant_id` | Sí | Identificador de directorio (inquilino) de la aplicación de Microsoft Entra |
| `client_id` | Sí | Identificador de aplicación (cliente) |
| `secret` | Sí | Valor del secreto de cliente. Se guarda en texto plano: restrinja el archivo a su propietario |
| `serverpostgres_id` | Sí | Identificador de recurso de Azure del recurso de PostgreSQL cuyas métricas se leen |

El formato del archivo es rígido en cuatro puntos que importan al editarlo:

- El separador es `:` y solo se lee el texto posterior a los dos puntos, así que un valor no puede contener dos puntos. No añada espacios alrededor del valor; los espacios iniciales y finales se recortan.
- Se ignora cualquier línea que contenga `#` en cualquier posición. Un `#` detrás de un valor descarta ese ajuste completo en silencio, así que deje los comentarios en líneas propias.
- Cada clave se reconoce porque su nombre aparece en cualquier parte de la línea. No añada claves adicionales cuyos nombres contengan `tenant_id`, `client_id`, `secret` o `serverpostgres_id`.
- Las cuatro claves deben estar presentes. Un archivo al que le falte cualquiera de ellas detiene la ejecución con un error antes de generar ningún módulo. El mensaje no siempre nombra la clave, así que compruebe las cuatro cuando una ejecución falle al arrancar.

### Registrar el plugin de servidor

Registre el ejecutable en la consola para que Pandora FMS pueda ejecutarlo como plugin de servidor:

1. Abra **Servers → Plugins** y pulse **Register plugin**.
2. Indique un nombre y una descripción para el plugin.
3. En **Plugin command**, escriba la ruta absoluta del ejecutable en el servidor de Pandora FMS, por ejemplo `/usr/share/pandora_server/util/plugin/pandora_azurepostgresql`.
4. En **Plugin parameters**, combine las macros de plugin `_field1_`, `_field2_`, ... con los parámetros:

```text
--conf _field1_ --agent_name _field2_ --prefix_module _field3_ --data_dir _field4_
```

5. En **Macro parameters**, describa cada campo:

| Campo | Descripción | Valor de ejemplo |
|-------|-------------|------------------|
| `_field1_` | Ruta absoluta al archivo de credenciales y recurso en el servidor de Pandora FMS | `/etc/pandora/plugins/azure-postgresql.conf` |
| `_field2_` | Agente que contendrá los módulos | `Azure_PostgreSQL_prod` |
| `_field3_` | Prefijo que se añade a cada nombre de módulo | `prod` |
| `_field4_` | Directorio de datos de Pandora FMS, leído por el Data Server | `/var/spool/pandora/data_in/` |

<!-- SCREENSHOT NEEDED: Formulario de registro de plugins con el comando del plugin Azure PostgreSQL, la cadena de parámetros con macros _fieldN_ y la lista de macros rellena con los valores de ejemplo anteriores. -->

No añada `--as_agent_plugin 1` a los parámetros registrados. Ese parámetro hace que el plugin imprima XML de módulos en lugar de escribir el archivo de datos de agente, y el módulo de plugin publicaría ese XML como valor en lugar de `1`.

Un mismo plugin registrado sirve para varios recursos de PostgreSQL: regístrelo una vez y dé a cada módulo de plugin su propio archivo de credenciales, nombre de agente y prefijo.

### Crear el módulo de plugin

1. Abra el agente que contendrá los módulos y cree un módulo de tipo **Plugin**.
2. Seleccione el plugin registrado y rellene sus macros con el archivo, el nombre de agente, el prefijo y el directorio de datos del recurso de destino.
3. Guarde el módulo.

Cada ejecución publica todas las métricas que devuelve el recurso, así que cree un módulo de plugin por recurso de PostgreSQL. Varios módulos apuntando al mismo recurso repiten las mismas consultas en cada intervalo.

### Elegir el modo de entrega

- **Archivo de datos de agente** (opción por defecto): el plugin escribe el documento en `--data_dir` e imprime `1`. Úselo cuando el plugin se ejecuta en un servidor de Pandora FMS, incluido un servidor remoto.
- **Tentacle**: añada `--tentacle_address <PANDORA_FMS_SERVER>` y, cuando no sea `41121`, `--tentacle_port <PORT>`. El plugin envía el documento con `tentacle_client` e imprime `1`.
- **XML de módulos por la salida estándar**: añada `--as_agent_plugin 1` para inspeccionar los módulos generados desde una terminal sin escribir ningún archivo.

La entrega por Tentacle tiene dos límites que conviene conocer antes de confiar en ella:

- El plugin pasa al cliente de Tentacle solo la dirección y el puerto. No tiene opción de contraseña de Tentacle, así que un servidor de Tentacle que la exija rechaza la transferencia.
- Una transferencia rechazada imprime `Tentacle error` en la salida de error, pero el plugin sigue imprimiendo `1` y el archivo de datos permanece en `--data_dir`. Compruebe el agente en la consola, no el valor impreso.

La dirección y el puerto de Tentacle se pasan al cliente de Tentacle sin comillas. Use solo un nombre de host o una dirección IP, sin metacaracteres de shell.

### Credenciales y transporte

- El secreto de cliente está en el archivo de configuración en texto plano. Haga que el archivo solo sea legible por el usuario que ejecuta el plugin, por ejemplo con `chmod 600` y el mismo propietario.
- El secreto nunca se pasa por la línea de comandos: el plugin recibe solo la ruta del archivo, así que el secreto no aparece en el historial del shell ni en la lista de procesos.
- El plugin no ofrece ninguna opción para omitir la verificación del certificado TLS ni ajustes de proxy. La autenticación y las consultas de métricas usan los extremos de Azure y el almacén de confianza de certificados por defecto de la máquina que ejecuta el plugin. Mantenga actualizado el paquete de CA del sistema.
- Use una aplicación dedicada a Pandora FMS y concédale permiso de lectura solo sobre los recursos que monitoriza. Rotar su secreto consiste en editar una línea del archivo de configuración.

## Verificación

Ejecute el plugin manualmente en el servidor de Pandora FMS, con el mismo usuario que ejecuta los módulos de plugin, para inspeccionar los módulos que genera:

```bash
./pandora_azurepostgresql --conf <PATH_TO_CONFIG> --as_agent_plugin 1
```

Una ejecución correcta imprime un bloque `<module>` por cada valor de métrica. Cuando la ventana devuelve más de un valor para una métrica, la salida repite ese nombre de módulo:

```xml
<module>
	<name><![CDATA[cpu_percent]]></name>
	<type>generic_data</type>
	<data><![CDATA[12.5]]></data>
	<description><![CDATA[2026-10-27 09:00:00+00:00 Average CPU percentage]]></description>
</module>
<module>
	<name><![CDATA[active_connections]]></name>
	<type>generic_data</type>
	<data><![CDATA[3]]></data>
	<description><![CDATA[2026-10-27 09:00:00+00:00 Active connections]]></description>
</module>
```

Los valores y el texto de la descripción anteriores son ilustrativos; los nombres de módulo, los tipos y la estructura del documento son los que produce el plugin.

La misma ejecución sin el parámetro usa el modo por defecto:

```bash
./pandora_azurepostgresql --conf <PATH_TO_CONFIG> --agent_name <AGENT_NAME>
```

Escribe un archivo de datos de agente en `--data_dir` e imprime `1`. El módulo de plugin de un plugin registrado publica ese `1`, de modo que un valor de módulo `1` significa que la ejecución llegó a la entrega, no que los datos hayan llegado a la consola.

Para confirmar la ingesta, abra el agente indicado en `--agent_name` y compruebe que contiene los módulos de métricas con marcas de tiempo recientes. Los valores solo aparecen cuando Azure Monitor devolvió datos para la ventana: una métrica sin valor no aparece en esa ejecución.

<!-- SCREENSHOT NEEDED: Lista de módulos de un agente en la consola de Pandora FMS tras una ejecución del plugin, con los módulos de métricas de Azure PostgreSQL y marcas de tiempo recientes, y el módulo de plugin con valor 1. -->

## Entender los resultados

Una ejecución correcta produce un agente y sus módulos:

| Propiedad | Valor |
|-----------|-------|
| Nombre del agente | `--agent_name`; `Azure_Monitor_Postgresql` por defecto |
| Alias del agente | El mismo que el nombre del agente |
| Descripción del agente | `Azure PostgreSQL Metrics` |
| Grupo | `--group`; `Azure` por defecto. El grupo debe existir en la consola |
| Dirección del agente | Vacía |
| Intervalo del agente | Vacío en la definición del agente; un agente que ya existe conserva su propio intervalo |
| Nombres de módulo | El nombre de la métrica de Azure Monitor, con `<prefijo>_` delante cuando se define `--prefix_module` |
| Tipo de módulo | `generic_data` para las 16 métricas; `generic_data_string` para el módulo personalizado |
| Valor del módulo | El promedio que Azure Monitor devuelve para un punto de datos de la ventana |
| Descripción del módulo | La marca de tiempo del punto de datos seguida de la descripción que Azure Monitor da a la métrica |
| Unidades, umbrales, intervalo de módulo | Ninguno. Configúrelos en la consola sobre el módulo generado |

Las 16 métricas se agrupan en cinco bloques:

- **Consumo de recursos.** `cpu_percent`, `memory_percent` e `io_consumption_percent` informan del consumo de procesador, memoria y E/S de disco del servidor.
- **Almacenamiento.** `storage_percent`, `storage_used` y `storage_limit` informan del almacenamiento de datos en uso, y `backup_storage_used` del almacenamiento de copias de seguridad en uso.
- **Almacenamiento de registros del servidor.** `serverlog_storage_percent`, `serverlog_storage_usage` y `serverlog_storage_limit` informan del almacenamiento de registros del servidor.
- **Conexiones y red.** `active_connections` y `connections_failed` cuentan conexiones, y `network_bytes_egress` y `network_bytes_ingress` informan del tráfico de red.
- **Replicación.** `pg_replica_log_delay_in_seconds` y `pg_replica_log_delay_in_bytes` informan del retardo de replicación.

### Un registro de módulo por punto de datos

El plugin emite un registro de módulo por cada punto de datos con valor en la ventana. Cuando Azure Monitor devuelve más de un punto para una métrica, el documento repite ese nombre de módulo con un valor distinto y una marca de tiempo distinta en su descripción. La ventana por defecto es de una hora con un intervalo de 60 minutos; `--timespan` cambia la ventana y el intervalo a la vez.

Pandora FMS identifica un módulo por su nombre, de modo que los nombres repetidos se funden en un único módulo y solo se conserva uno de esos valores. Trate cada módulo como «el último promedio que devolvió Azure Monitor» y consulte la serie temporal en Azure Monitor cuando necesite la evolución dentro de la ventana. Una métrica que el recurso devuelve como nula no produce ningún registro, así que su módulo mantiene el valor anterior.

### El módulo de métrica personalizada

Con `--metric` y `--name_module` a la vez, el plugin añade un módulo `generic_data_string` llamado `--name_module`, con el prefijo cuando se define `--prefix_module`. Contiene una entrada de lista por cada punto de datos de esa métrica, con este texto fijo:

```text
The Availity at <marca de tiempo del punto de datos> is <promedio>
```

`Availity` es la grafía literal que escribe el plugin. El nombre de métrica indicado en `--metric` se pasa a Azure Monitor tal cual: debe existir para el recurso; de lo contrario, la ejecución se detiene antes de generar ningún módulo. Cuando ningún punto de datos tiene valor, el módulo se genera con una lista vacía.

El módulo personalizado es adicional: las 16 métricas estándar se siguen recogiendo en la misma ejecución. `--metric` solo, o `--name_module` solo, no añaden nada.

## Operar y resolver problemas

- Cada ejecución realiza una consulta a Azure Monitor por métrica: dieciséis por defecto, más una para el módulo personalizado. Las consultas son secuenciales y ninguna se reintenta, y una consulta rechazada detiene la ejecución antes de escribir el archivo de datos de agente, así que una ejecución publica el conjunto completo o nada.
- La ventana es de `--timespan` horas con el intervalo derivado de ella: `1` hora con 60 minutos, `6` horas con 360, `12` horas con 720 y `24` horas con 1440. Cualquier otro valor vuelve a `1` hora en silencio. `--granularity` se acepta y no tiene efecto: el intervalo siempre procede de `--timespan`.
- Cada ejecución publica promedios de una ventana completa, no el último valor instantáneo, así que ejecutar el plugin con más frecuencia que el intervalo no aporta más resolución. Ajuste el intervalo del módulo a la ventana que quiera seguir.
- El plugin no tiene parámetro de detalle ni de depuración. Los canales de diagnóstico son la salida estándar, la salida de error y el estado de salida. Una ejecución que llega a la entrega termina con estado `0`, una línea de comandos inválida termina con estado `2` y una ejecución que se detiene por un error termina con un estado distinto de cero.

| Señal | Causa y comprobación |
|-------|----------------------|
| `error: the following arguments are required: -c/--conf`, estado de salida `2` | No se pasó el archivo de configuración. El parámetro `--conf` es obligatorio |
| Un resumen de uso que nombra un valor inválido, estado de salida `2` | Un `--timespan` o un `--as_agent_plugin` que no son enteros, o un parámetro sin valor |
| Un error antes de generar ningún módulo y sin archivo de datos | Al archivo de configuración le falta una de las cuatro claves, o su credencial o identificador de recurso no se puede leer. Compruebe primero las cuatro claves y la regla del `#` |
| Un error de autenticación o autorización de Azure, sin módulos | Identificador de inquilino, de aplicación o secreto incorrectos, un secreto caducado, o una aplicación sin acceso al recurso. Pruebe la credencial fuera de Pandora FMS |
| Un error sobre una métrica y ningún módulo | Azure Monitor rechazó un nombre de métrica para ese recurso. Confirme que el recurso expone los 16 nombres de métrica de [Módulos generados](#modulos-generados) |
| `ERROR - Could not write file: ..., please check directory permissions` | `--data_dir` no existe o no tiene permiso de escritura, o dos ejecuciones empezaron en el mismo segundo y la segunda chocó con el nombre de archivo de la primera. Repita la ejecución y compruebe los permisos del directorio |
| `Tentacle error` en la salida de error y `1` en la salida estándar | Falló la transferencia por Tentacle: falta `tentacle_client` o no es accesible, el puerto es incorrecto, o el servidor de Tentacle exige contraseña. El archivo de datos permanece en `--data_dir` |
| El módulo de plugin tiene XML de módulos en lugar de `1` | `--as_agent_plugin 1` está en los parámetros registrados. Elimínelo |
| Se imprime `1` pero no aparece el agente en la consola | El archivo de datos se escribió donde el Data Server no lo lee. Compare `--data_dir` con el directorio de entrada del servidor y compruebe que el plugin se ejecutó como un usuario con permiso de escritura sobre él |
| El agente existe con menos módulos de los esperados | Esas métricas no tenían valor en la ventana, o el recurso no las informa. Ajuste sus expectativas, no la ejecución |
| Un módulo de métrica muestra un valor antiguo entre ejecuciones | El recurso no devolvió valor en las últimas ejecuciones, así que el módulo conservó el valor anterior. Confírmelo en Azure Monitor |
| El agente aparece en un grupo distinto del esperado | El nombre de `--group` se escribe tal cual y el grupo debe existir en la consola |

## Referencia

### Línea de comandos

```bash
./pandora_azurepostgresql --conf <PATH_TO_CONFIG> [opciones]
```

| Nombre | Obligatorio | Por defecto | Descripción |
|--------|-------------|-------------|-------------|
| `-c`, `--conf` | Sí | — | Ruta al archivo de credenciales y recurso |
| `--timespan` | No | `1` | Ventana en horas: `1`, `6`, `12` o `24`. Cualquier otro valor se sustituye por `1` |
| `--granularity` | No | Derivado de `--timespan` | Se acepta y se ignora. El intervalo es siempre de 60, 360, 720 o 1440 minutos, derivado de `--timespan` |
| `--metric` | No | Vacío | Nombre de métrica de Azure Monitor para el módulo personalizado. Solo se usa junto con `--name_module` |
| `--name_module` | No | Vacío | Nombre del módulo personalizado. Solo se usa junto con `--metric` |
| `--prefix_module` | No | Vacío | Prefijo unido a cada nombre de módulo con `_` |
| `--agent_name` | No | `Azure_Monitor_Postgresql` | Nombre del agente escrito en el archivo de datos de agente |
| `-g`, `--group` | No | `Azure` | Grupo escrito en la definición del agente |
| `--data_dir` | No | `/var/spool/pandora/data_in/` | Directorio donde se escribe el archivo de datos de agente |
| `--tentacle_address` | No | Vacío | Dirección del servidor Tentacle. Si se define, el archivo de datos se envía con `tentacle_client` |
| `--tentacle_port` | No | `41121` | Puerto del servidor Tentacle |
| `--as_agent_plugin` | No | `0` | `1` imprime el XML de los módulos en la salida estándar; cualquier otro valor entero escribe el archivo de datos de agente e imprime `1` |
| `-h`, `--help` | No | — | Muestra la ayuda y termina |

### Archivo de configuración

```ini
tenant_id:<TENANT_ID>
client_id:<CLIENT_ID>
secret:<CLIENT_SECRET>
serverpostgres_id:<POSTGRES_RESOURCE_ID>
```

| Clave | Obligatorio | Descripción |
|-------|-------------|-------------|
| `tenant_id` | Sí | Identificador de directorio (inquilino) de la aplicación de Microsoft Entra |
| `client_id` | Sí | Identificador de aplicación (cliente) |
| `secret` | Sí | Valor del secreto de cliente |
| `serverpostgres_id` | Sí | Identificador de recurso de Azure del recurso de PostgreSQL |

Líneas `clave:valor`, sin dos puntos dentro del valor, y toda línea que contenga `#` se ignora por completo. Las claves se reconocen por su nombre en cualquier parte de la línea.

### Módulos generados

El plugin solicita estos 16 nombres de métrica en cada ejecución. El nombre del módulo es el nombre de la métrica, o `<prefijo>_<métrica>` cuando se define `--prefix_module`, y el valor es el promedio que Azure Monitor devuelve para un punto de datos:

| Métrica | Qué informa |
|---------|-------------|
| `cpu_percent` | Consumo de procesador del servidor |
| `memory_percent` | Consumo de memoria del servidor |
| `io_consumption_percent` | Consumo de E/S de disco del servidor |
| `storage_percent` | Almacenamiento de datos en uso, como porcentaje del límite |
| `storage_used` | Almacenamiento de datos en uso |
| `storage_limit` | Límite de almacenamiento de datos |
| `serverlog_storage_percent` | Almacenamiento de registros del servidor en uso, como porcentaje del límite |
| `serverlog_storage_usage` | Almacenamiento de registros del servidor en uso |
| `serverlog_storage_limit` | Límite de almacenamiento de registros del servidor |
| `active_connections` | Conexiones activas |
| `connections_failed` | Conexiones fallidas |
| `backup_storage_used` | Almacenamiento de copias de seguridad en uso |
| `network_bytes_egress` | Tráfico de red enviado |
| `network_bytes_ingress` | Tráfico de red recibido |
| `pg_replica_log_delay_in_seconds` | Retardo de replicación en segundos |
| `pg_replica_log_delay_in_bytes` | Retardo de replicación en bytes |

El significado de cada valor es el que Azure Monitor asigna al nombre de la métrica; el plugin reenvía el promedio y no añade unidad, así que interprete el valor con el nombre de la métrica y configure la unidad en la consola.

Con `--metric <METRIC> --name_module <NAME>` la ejecución añade un módulo `generic_data_string`, llamado `--name_module` o `<prefijo>_<name_module>`, cuya lista contiene una entrada por punto de datos con la forma `The Availity at <marca de tiempo> is <promedio>`.

### Identidad del addon

| Propiedad | Valor |
|-----------|-------|
| Identificador en el Marketplace | `pandorafms.azure_postgresql` |
| Nombre | Azure PostgreSQL |
| Versión | `1.0` |
| Última actualización en el Marketplace | 2026-06-08 |
| Paquete | `pandorafms.azure_postgresql.1.0.zip` |
| Categoría | Miscelaneus |
| Etiquetas | `applications`, `databases` |
| Licencia | One; la descarga está limitada a usuarios con licencia |
| Mantenimiento | El registro del Marketplace no incluye ninguna declaración de mantenimiento ni de obsolescencia |
| Ejecutable | `pandora_azurepostgresql` |
| Archivo de configuración | `pandora_azurepostgresql.conf` |
