# Plugin Pandora Azure SQL

*Última actualización del artículo: 2026-10-26.*

!!! warning "Se recomienda la integración de Discovery"
    Para instalaciones nuevas use [Azure SQL Discovery](../discovery/azure-sql.md), que es la integración recomendada para este servicio. Este plugin es la ruta heredada.

## Qué hace

El plugin Pandora Azure SQL convierte las métricas de Azure Monitor de una base de datos Azure SQL en módulos de Pandora FMS. Cada ejecución se autentica en Microsoft Entra con una entidad de servicio, lee 23 métricas de la base de datos de la última hora con resolución de cinco minutos y las publica como un agente nuevo con 23 módulos.

La base de datos se identifica por su ID de recurso completo de Azure, que usted escribe en un archivo de configuración local junto con las credenciales. El plugin nunca abre una conexión SQL: lee las métricas que Azure Monitor ya almacena para el recurso, así que no se instala nada en el servidor de base de datos y no hace falta que ningún puerto sea accesible en él.

Cada ejecución cubre una base de datos y produce un agente. Monitorizar varias bases de datos significa una ejecución por base de datos, cada una con su propio archivo de configuración y su propio nombre de agente.

El addon admite los dos modelos de ejecución de un plugin de Pandora FMS:

- **Modo plugin de servidor** (por defecto): cada ejecución construye el documento de agente y lo copia en el directorio de datos de Pandora FMS o lo envía con Tentacle.
- **Modo plugin de agente** (`--as_agent_plugin 1`): cada ejecución imprime el XML de los módulos en la salida estándar, para que lo ingiera el agente de Pandora FMS.

> **Esta página documenta dos líneas de comandos distintas.** El registro del Marketplace y el archivo de registro del paquete describen únicamente el colector de métricas, `pandora_azuresql`, que es el objeto de esta página. Un segundo ejecutable, `pandora_azuresqlquery`, ejecuta sentencias SQL contra la misma base de datos mediante ODBC, con sus propias opciones, su propio formato de configuración y su propia salida. El registro del Marketplace no lo describe ni indica si su paquete lo contiene. Se documenta por separado en [El ejecutor de consultas](#el-ejecutor-de-consultas) para que nunca se confundan los dos.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Addon del Marketplace `pandorafms.azuresql`, versión `1.0` | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del addon](#identidad-del-addon) |
| Pandora FMS NG 784 y posteriores | `Soportado` | El Marketplace indica que todas sus integraciones son compatibles con Pandora FMS NG 784 y versiones posteriores. Es una declaración pública general que cubre todas las entradas, no un registro de pruebas de este addon |
| Una base de datos Azure SQL, identificada por su ID de recurso completo | `Requerido` | El archivo de configuración lleva un único `database_id` y todas las consultas de métricas se hacen contra él. Prerrequisito, no una declaración de compatibilidad |
| Una entidad de servicio de Microsoft Entra con permiso de lectura sobre ese recurso de base de datos y sus métricas | `Requerido` | El plugin se autentica con un inquilino, un identificador de aplicación y un secreto de cliente, y lee métricas de Azure Monitor del recurso. Ninguna fuente oficial identifica un rol más restrictivo para este addon |
| Acceso HTTPS a los puntos de conexión públicos de Azure | `Requerido` | El plugin no tiene opción de punto de conexión, así que solo se autentica y consulta la nube pública. Las nubes soberanas o personalizadas quedan como `Sin validar` |
| `tentacle_client` en el host que ejecuta el plugin | `Requerido` cuando se usa `--tentacle_address` | Entrega mediante Tentacle |
| Microsoft ODBC Driver 18 for SQL Server en el host que ejecuta el plugin | `Requerido` cuando se usa el ejecutor de consultas | El ejecutor de consultas solicita ese controlador por su nombre y no tiene opción para cambiarlo. Consulte [El ejecutor de consultas](#el-ejecutor-de-consultas) |
| Nivel de servicio y edición de Azure SQL | `Sin validar` | Algunas métricas solo están disponibles en bases de datos basadas en vCore o sin servidor, y otras no se aplican en absoluto a almacenes de datos. El plugin solicita las 23 independientemente del nivel |
| Sistema operativo del host que ejecuta el plugin | `Sin validar` | La guía heredada indica CentOS 7, Fedora y Rocky Linux como probados y «cualquier Linux» como esperado. Ningún registro de pruebas respalda ninguna de las dos afirmaciones |

### Requisitos

1. **Una base de datos Azure SQL** y su ID de recurso completo.
2. **Una entidad de servicio de Microsoft Entra**: identificador de inquilino, identificador de aplicación (cliente) y un secreto de cliente.
3. **Permiso de lectura para esa entidad de servicio** sobre el recurso de base de datos y sus métricas de Azure Monitor. Conceda el acceso de lectura en el ámbito más pequeño que cubra la base de datos.
4. **Acceso HTTPS de salida** desde el host que ejecuta el plugin hasta los puntos de conexión públicos de Azure.
5. **Pandora FMS** para recibir la salida: el servidor de Pandora FMS en modo plugin de servidor, o el agente de Pandora FMS del host monitorizado en modo plugin de agente.
6. **El cliente de Tentacle (`tentacle_client`) disponible en el `PATH`**, solo cuando entregue con `--tentacle_address`.

Las métricas se leen de Azure Monitor y nunca de la propia base de datos, así que la cuenta que las lee es una identidad de Azure, no un usuario de base de datos.

### Instalar el plugin

Descargue el paquete `pandorafms.azuresql.1.0.pspz2` desde la entrada del Marketplace:

[https://marketplace.pandorafms.com/entries/pandorafms.azuresql](https://marketplace.pandorafms.com/entries/pandorafms.azuresql)

Registre el paquete desde el gestor de plugins de la consola de Pandora FMS. El paquete incluye un archivo de registro que declara el comando del plugin y sus tres campos de módulo, documentados en [Registrar el plugin en la consola](#registrar-el-plugin-en-la-consola).

El ejecutable también puede desplegarse por separado y ejecutarse desde un terminal o desde un planificador; consulte [Ejecución por línea de comandos](#ejecucion-por-linea-de-comandos).

### Preparar el acceso a Azure

1. **Cree o seleccione un registro de aplicación** en Microsoft Entra ID y genere un secreto de cliente para él.
2. **Anote tres valores**: el identificador del inquilino (directorio), el identificador de la aplicación (cliente) y el **valor** del secreto. Copie el valor, no el identificador del secreto: el plugin lo envía tal cual al punto de conexión de autenticación.
3. **Conceda a la entidad de servicio permiso de lectura** sobre el recurso de base de datos y sus métricas.
4. **Copie el ID de recurso completo de la base de datos.** Tiene esta forma:

```text
/subscriptions/<SUBSCRIPTION_ID>/resourceGroups/<RESOURCE_GROUP>/providers/Microsoft.Sql/servers/<SQL_SERVER>/databases/<DATABASE>
```

El plugin envía esa cadena como URI del recurso en todas las consultas de métricas, así que debe ser el recurso de la **base de datos**, no el del servidor.

## Configuración

El plugin toma las credenciales y el destino de un único archivo de configuración, y todo lo demás de la línea de comandos. No hay precedencia entre ambos: ningún ajuste de entrega puede escribirse en el archivo y ninguna credencial puede pasarse como opción.

### El archivo de configuración

El archivo es obligatorio y se pasa con `-c`/`--conf`. Contiene un par `key:value` por línea:

```ini
# Azure credentials
tenant_id:<TENANT_ID>
client_id:<CLIENT_ID>
secret:<CLIENT_SECRET>
# Target database
database_id:/subscriptions/<SUBSCRIPTION_ID>/resourceGroups/<RESOURCE_GROUP>/providers/Microsoft.Sql/servers/<SQL_SERVER>/databases/<DATABASE>
```

El analizador aplica estas reglas:

- El separador es **dos puntos**, no el signo igual.
- Las líneas en blanco se omiten.
- **Se omite toda línea que contenga `#` en cualquier posición**, no solo las que empiezan por él. No añada comentarios al final de una línea de valor.
- Un valor termina en los siguientes dos puntos: un secreto de cliente que contenga `:` se trunca y la autenticación falla.
- Una clave repetida conserva su último valor.
- Las cuatro claves se buscan por nombre. Si falta una, la ejecución termina con una traza de `NameError` en lugar de un mensaje que nombre la clave ausente.

El archivo contiene el secreto de cliente en texto plano. Restrínjalo a la cuenta que ejecuta el plugin (por ejemplo con `chmod 600`) y mantenlo fuera de directorios compartidos y del control de versiones.

### Ejecución por línea de comandos

La ejecución mínima en modo plugin de servidor, que escribe el documento de agente en el directorio de datos de Pandora FMS:

```bash
./pandora_azuresql -c <PATH_TO_CONFIG>
```

La misma ejecución entregada con Tentacle, con nombre de agente y grupo explícitos:

```bash
./pandora_azuresql -c <PATH_TO_CONFIG> \
    --agent_name <AGENT_NAME> -g <GROUP> \
    --tentacle_address <PANDORA_FMS_SERVER> --tentacle_port 41121
```

Modo plugin de agente, que imprime el XML de los módulos en lugar de construir un agente:

```bash
./pandora_azuresql -c <PATH_TO_CONFIG> --as_agent_plugin 1
```

La línea de comandos selecciona una de tres ramas de salida. `--tentacle_address` tiene precedencia sobre la opción de modo:

| Línea de comandos | Qué hace la ejecución |
| --- | --- |
| `--tentacle_address` está definido, con o sin `--as_agent_plugin` | Construye el documento de agente, lo envía con `tentacle_client` e imprime `1` |
| Sin `--tentacle_address` y con `--as_agent_plugin` ausente o distinto de `1` | Construye el documento de agente, lo escribe en `--data_dir` e imprime `1` |
| `--as_agent_plugin 1` sin `--tentacle_address` | Imprime el XML de los módulos en la salida estándar y no escribe ningún archivo |

Puntos clave:

- **`--as_agent_plugin 1` selecciona el modo plugin de agente; el valor por defecto es el modo plugin de servidor.** El nombre de la opción es el inverso del valor por defecto, así que confirme el modo antes de interpretar cualquier salida.
- **`--data_dir`, `--agent_name` y `-g` no tienen efecto en modo plugin de agente.** No se construye ningún archivo ni documento de agente, así que el nombre de agente y el grupo nunca llegan a Pandora FMS.
- **`--prefix_module` se acepta y se ignora.** Ningún nombre de módulo recibe prefijo en este colector; consulte [Módulos generados](#modulos-generados).
- El grupo se escribe por nombre en el documento de agente, así que debe ser un grupo que exista en la consola. El archivo de registro sugiere `azuresql`; el valor por defecto interno es `Azure`.
- El documento de agente siempre declara modo de agente `1` e intervalo vacío, así que el intervalo lo aplica la consola, no el plugin.
- El plugin no guarda estado entre ejecuciones, así que cualquier ejecución puede repetirse manualmente.

### Registrar el plugin en la consola

1. Abra **Servidores → Plugins** y registre el paquete `pandorafms.azuresql.1.0.pspz2`, o añada el plugin manualmente con la ruta del ejecutable `pandora_azuresql` como comando.
2. Los parámetros que ya declara el paquete son:

```text
-c " _field1_ " --agent_name " _field2_ " -g " _field3_ "
```

3. El paquete define tres campos:

| Campo | Descripción en el paquete | Valor que debe indicar |
| --- | --- | --- |
| `_field1_` | `Conf path (obligatory)` | Ruta absoluta del archivo de configuración en el servidor de Pandora FMS |
| `_field2_` | `Agent name (optional)` | Nombre del agente que contendrá los 23 módulos |
| `_field3_` | Sin definición en el paquete | Nombre de un grupo de Pandora FMS existente |

!!! warning "Los parámetros del paquete rompen la ruta de configuración"
    Cada macro va entre comillas con un espacio dentro de ellas: `-c " _field1_ "`. Cuando la consola sustituye el valor del campo, el argumento conserva un espacio inicial y otro final, y el plugin abre esa ruta sin recortarla, así que la ejecución falla con `FileNotFoundError`. Elimine los espacios al registrar el plugin, por ejemplo `-c "_field1_" --agent_name "_field2_" -g "_field3_"`.

    El archivo de registro declara `total_macros_provided = 3` pero define `[macro_1]`, `[macro_2]` y `[macro_4]`. No existe `[macro_3]`, así que el tercer campo, que la línea de comandos usa como `_field3_`, es el que el paquete deja sin descripción, y la definición de `group` es la que no se usa.

4. Dé un valor a cada campo por módulo. El módulo del plugin es solo el disparador: en modo plugin de servidor su propio valor es `1`, y los 23 módulos de métricas llegan al agente indicado en `--agent_name`, no al agente que contiene el módulo disparador.
5. Cada módulo del plugin se ejecuta en el servidor de Pandora FMS seleccionado para él, incluido un servidor remoto, así que varias bases de datos pueden monitorizarse desde el servidor más cercano a cada una sin instalar nada en el host de la base de datos.

<!-- SCREENSHOT NEEDED: Pantalla de parámetros del plugin ya registrado en la consola de Pandora FMS, mostrando los tres campos de macro y cuál de ellos tiene descripción. -->

## Verificación

Ejecute el plugin manualmente en modo plugin de agente para ver la salida sin publicar nada:

```bash
./pandora_azuresql -c <PATH_TO_CONFIG> --as_agent_plugin 1
```

Una ejecución correcta imprime 23 bloques `<module>` en la salida estándar. Todos los bloques son módulos `generic_data_string` cuyo valor es una `<datalist>` con una entrada por cada punto de datos de la última hora:

```xml
<module>
	<name><![CDATA[cpu_percent]]></name>
	<type>generic_data_string</type>
	<datalist>
	<data>
		<value><![CDATA[The cpu_percent at 2026-10-27 09:05:00+00:00 is 2.4]]></value>
	</data>
	<data>
		<value><![CDATA[The cpu_percent at 2026-10-27 09:10:00+00:00 is 3.1]]></value>
	</data>
	</datalist>
	<description><![CDATA[CPU percentage]]></description>
</module>
```

Este fragmento muestra la estructura del documento que produce el plugin; no se capturó de una base de datos real.

Después ejecute el plugin sin `--as_agent_plugin` para entregar el agente:

```bash
./pandora_azuresql -c <PATH_TO_CONFIG> --agent_name <AGENT_NAME>
```

Una ejecución correcta en modo plugin de servidor imprime `1` y escribe `<AGENT_NAME>.<epoch>.data` en el directorio de datos, o lo envía con Tentacle. Cuando el servidor de datos procesa el archivo, el agente llamado `<AGENT_NAME>` aparece en Pandora FMS con sus 23 módulos.

El plugin imprime su resumen de uso con `./pandora_azuresql -h`.

<!-- SCREENSHOT NEEDED: Vista de detalle del agente en la consola de Pandora FMS con los 23 módulos generados por el plugin y un módulo de tipo datalist desplegado. -->

## Entender los resultados

### Qué publica cada ejecución

Un agente con 23 módulos, siempre el mismo conjunto, agrupados por la parte del servicio que describen:

| Familia | Módulos |
| --- | --- |
| Cómputo | `cpu_percent`, `cpu_limit`, `cpu_used`, `sqlserver_process_core_percent`, `app_cpu_percent`, `app_cpu_billed` |
| Almacenamiento | `storage`, `storage_percent`, `allocated_data_storage` |
| E/S y registro | `physical_data_read_percent`, `log_write_percent` |
| Conexiones y sesiones | `connection_successful`, `connection_failed`, `blocked_by_firewall`, `sessions_percent`, `workers_percent`, `sqlserver_process_memory_percent`, `app_memory_percent` |
| TempDB y OLTP en memoria | `tempdb_data_size`, `tempdb_log_size`, `tempdb_log_used_percent`, `xtp_storage_percent` |
| Contención | `deadlock` |

### Por qué cada módulo es una lista de texto

Cada módulo es un `generic_data_string` cuyo valor es una `<datalist>`, y cada entrada dice `The <metric> at <timestamp> is <value>`. Esto tiene consecuencias que conviene conocer antes de construir nada sobre los datos:

- **El valor es texto, no un número.** Pandora FMS no puede representar el módulo como una serie numérica ni aplicarle umbrales numéricos, y el plugin no define unidad, intervalo ni umbral en ningún módulo.
- **Cada ejecución vuelve a publicar la hora completa.** Con un intervalo de ejecución de cinco minutos, cada punto de datos aparece en el valor de módulo de 12 ejecuciones consecutivas.
- **Un punto sin valor se publica como `None`.** Azure Monitor no rellena todos los puntos de todas las métricas, y el plugin escribe lo que recibe.
- **Los 23 módulos se crean en todas las ejecuciones**, incluidas las métricas que la base de datos no informa. Ese módulo aparece con una `<datalist>` vacía. Un módulo vacío no es prueba de un fallo.
- **Los contadores se promedian igual que las magnitudes.** `connection_successful`, `connection_failed`, `blocked_by_firewall` y `deadlock` se solicitan con la agregación `Average` sobre la granularidad de cinco minutos, así que los números publicados son medias por intervalo, no totales.
- **No hay módulo de disponibilidad.** Nada en la salida indica si la ejecución pudo contactar con Azure. Una ejecución fallida no publica nada, y la ausencia de datos es la única señal.

### Un agente por base de datos

El nombre de agente y la base de datos de destino son ajustes de cada ejecución, así que monitorizar varias bases de datos significa un archivo de configuración por base de datos (con un `database_id` distinto) y una ejecución por base de datos (con un `--agent_name` distinto). Reutilizar el mismo nombre de agente para dos bases de datos mezcla ambos conjuntos de módulos en un solo agente, y la segunda ejecución sobrescribe la primera.

### Comparación con Azure SQL Discovery

[Azure SQL Discovery](../discovery/azure-sql.md) atiende el mismo servicio mediante una tarea de Discovery. Las diferencias que importan al elegir:

| | Este plugin | Azure SQL Discovery |
| --- | --- | --- |
| Bases de datos monitorizadas | Una, indicada por su ID de recurso en el archivo de configuración | Todas las de la suscripción o el grupo de recursos, o las que coincidan con los filtros de nombre |
| Agentes | Un agente por ejecución, con el nombre de `--agent_name` | Un agente por base de datos, o un único agente de destino |
| Módulos | 23 listas de datos de texto que cubren la última hora | Módulos numéricos, uno por familia de métricas habilitada |
| Credenciales | Un archivo de texto plano en el host que ejecuta el plugin | El almacén de credenciales de Pandora FMS, referenciado por la tarea |
| Configuración | Opciones de línea de comandos | Una tarea de Discovery |
| Recomendado para instalaciones nuevas | No | Sí |

## Operación y resolución de problemas

- **23 peticiones secuenciales por ejecución.** El paquete declara un tiempo de espera del plugin de `20` segundos. Con una conexión lenta, o cuando el cliente reintenta una petición, la ejecución puede cortarse antes de terminar; fuerce el módulo y compruebe la marca de tiempo de los datos del agente.
- **Una ejecución correcta en modo plugin de servidor imprime `1`.** Ese `1` es el valor del módulo disparador, no un resumen de la entrega. Con Tentacle, una transferencia fallida también imprime `1`: el plugin ignora el resultado del envío e imprime `1` incondicionalmente, y deja el archivo `.data` en `--data_dir` porque solo lo borra tras una transferencia correcta. Compruebe los datos del agente en la consola, no el `1`.
- **El archivo de datos se abre en modo exclusivo.** Dos ejecuciones del mismo nombre de agente dentro del mismo segundo terminan con `ERROR - Could not write file: ... please check directory permissions`, que es además el mensaje de un problema real de permisos.
- **No hay modo de depuración.** Los errores llegan a la salida de error como una traza, y los mensajes de la tabla siguiente son los que hay que buscar.

| Síntoma | Causa y acción |
| --- | --- |
| La ejecución termina con estado `2` y un error de uso en la salida de error | Falta `-c`. Es un argumento obligatorio. |
| Traza que acaba en `NameError` nombrando `tenant_id`, `client_id`, `secret` o `database_id` | El archivo de configuración no tiene línea para esa clave, o la línea se omitió porque contiene `#`. El plugin no tiene mensaje para una clave ausente. |
| `FileNotFoundError` sobre la ruta de configuración | La ruta es incorrecta, o llegó con espacios alrededor por la plantilla de parámetros del paquete. Consulte el aviso en [Registrar el plugin en la consola](#registrar-el-plugin-en-la-consola). |
| `ERROR - Could not write file` | `--data_dir` no es escribible por el usuario del plugin, o otra ejecución del mismo agente escribió en el mismo segundo. |
| Se imprime `1` pero no aparece ningún agente en la consola | Con `--tentacle_address`, la transferencia falló. Compruebe la dirección, el puerto y el registro del servidor de Tentacle. Sin Tentacle, compruebe que el servidor de datos está en marcha y leyendo `--data_dir`. |
| Traza en el paso de autenticación | El inquilino, el identificador de cliente o el secreto son incorrectos, el secreto ha caducado, o la entidad de servicio no tiene acceso de lectura al recurso. |
| Traza que nombra una métrica o un error de respuesta de Azure | Azure rechazó una de las 23 peticiones. La ejecución no tiene manejo de errores, así que se detiene y no publica nada. Compruebe el nivel de la base de datos y el ID de recurso. |
| Un módulo muestra solo valores `None` | Azure Monitor no tiene puntos de datos para esa métrica y esa base de datos. |
| Se define `--prefix_module` pero los nombres de módulo no cambian | La opción no tiene efecto en este colector. |

## Referencia

### Opciones de línea de comandos

| Opción | Obligatoria | Valor por defecto | Descripción |
| --- | --- | --- | --- |
| `-c`, `--conf` | Sí | — | Ruta del archivo de configuración con las credenciales y el ID de recurso de la base de datos |
| `--agent_name` | No | `Azure_SQL` | Nombre del agente creado en Pandora FMS. No tiene efecto en modo plugin de agente |
| `-g`, `--group` | No | `Azure` | Nombre del grupo de Pandora FMS asignado al agente. No tiene efecto en modo plugin de agente |
| `--data_dir` | No | `/var/spool/pandora/data_in/` | Directorio donde se escribe el documento de agente. No tiene efecto en modo plugin de agente |
| `--tentacle_address` | No | — | Dirección del servidor de Tentacle. Cuando se define, se envía el documento de agente y se ignoran los otros dos modos de entrega |
| `--tentacle_port` | No | `41121` | Puerto del servidor de Tentacle |
| `--as_agent_plugin` | No | `0` | `1` imprime el XML de los módulos en la salida estándar. Cualquier otro valor construye el documento de agente |
| `--prefix_module` | No | — | Se acepta y se ignora |
| `-h`, `--help` | No | — | Imprime el resumen de uso y termina |

### Claves del archivo de configuración

| Clave | Obligatoria | Descripción |
| --- | --- | --- |
| `tenant_id` | Sí | Identificador del inquilino (directorio) de Microsoft Entra |
| `client_id` | Sí | Identificador de aplicación (cliente) de la entidad de servicio |
| `secret` | Sí | Valor del secreto de cliente |
| `database_id` | Sí | ID de recurso completo de la base de datos Azure SQL |

El archivo usa líneas `key:value`. Consulte [El archivo de configuración](#el-archivo-de-configuracion) para las reglas de análisis, incluidas las líneas que se omiten.

### Módulos generados

Todos los módulos son `generic_data_string` con una `<datalist>` de los puntos de datos de la última hora, muestreados cada cinco minutos. El plugin no define unidad ni umbral; la descripción es el texto que escribe en el módulo.

| Nombre del módulo | Familia | Descripción escrita por el plugin |
| --- | --- | --- |
| `cpu_percent` | Cómputo | CPU percentage |
| `cpu_limit` | Cómputo | CPU limit. Applies to vCore-based databases |
| `cpu_used` | Cómputo | CPU used. Applies to vCore-based databases |
| `sqlserver_process_core_percent` | Cómputo | CPU usage as a percentage of the SQL DB process. Not applicable to data warehouses |
| `app_cpu_percent` | Cómputo | App CPU percentage. Applies to serverless databases |
| `app_cpu_billed` | Cómputo | App CPU billed. Applies to serverless databases |
| `storage` | Almacenamiento | Data space used. Not applicable to data warehouses |
| `storage_percent` | Almacenamiento | Data space used percent. Not applicable to data warehouses or hyperscale databases |
| `allocated_data_storage` | Almacenamiento | Allocated data storage. Not applicable to data warehouses |
| `physical_data_read_percent` | E/S y registro | Data IO percentage |
| `log_write_percent` | E/S y registro | Log IO percentage. Not applicable to data warehouses |
| `connection_successful` | Conexiones | Successful connections |
| `connection_failed` | Conexiones | Failed connections |
| `blocked_by_firewall` | Conexiones | Blocked by firewall |
| `sessions_percent` | Conexiones | Sessions percentage. Not applicable to data warehouses |
| `workers_percent` | Conexiones | Workers percentage. Not applicable to data warehouses |
| `sqlserver_process_memory_percent` | Conexiones | Memory usage as a percentage of the SQL DB process. Not applicable to data warehouses |
| `app_memory_percent` | Conexiones | App memory percentage. Applies to serverless databases |
| `tempdb_data_size` | TempDB y XTP | Space used in tempdb data files, in kilobytes. Not applicable to data warehouses |
| `tempdb_log_size` | TempDB y XTP | Space used in the tempdb transaction log file, in kilobytes. Not applicable to data warehouses |
| `tempdb_log_used_percent` | TempDB y XTP | Space used percentage in the tempdb transaction log file. Not applicable to data warehouses |
| `xtp_storage_percent` | TempDB y XTP | In-Memory OLTP storage percent. Not applicable to data warehouses |
| `deadlock` | Contención | Not applicable to data warehouses |

### El ejecutor de consultas

Un segundo ejecutable, `pandora_azuresqlquery`, es una herramienta distinta: ejecuta sentencias SQL contra la base de datos mediante ODBC y convierte sus filas en módulos. No comparte ni las opciones ni el formato de configuración del colector de métricas descrito más arriba. El registro del Marketplace no lo describe ni indica si su paquete lo contiene; confirme que el archivo existe antes de confiar en él.

```bash
./pandora_azuresqlquery -s <TARGET_HOST> -d <DATABASE> -u <USERNAME> -p <PASSWORD> \
    --conf <PATH_TO_CONFIG> --agent_name <AGENT_NAME>
```

| Opción | Obligatoria | Valor por defecto | Descripción |
| --- | --- | --- | --- |
| `-s`, `--servidor` | Sí | — | Nombre del servidor, que se pasa al controlador como `tcp:<TARGET_HOST>` |
| `-d`, `--database` | Sí | — | Nombre de la base de datos |
| `-u`, `--user` | Sí | — | Usuario de la base de datos |
| `-p`, `--password` | Sí | — | Contraseña de ese usuario |
| `--conf` | Sí | — | Ruta del archivo con las consultas |
| `--agent_name` | No | `AzureSQL` | Nombre del agente creado en Pandora FMS |
| `-g`, `--group` | No | `Azure` | Nombre del grupo de Pandora FMS |
| `--data_dir` | No | `/var/spool/pandora/data_in/` | Directorio donde se escribe el documento de agente |
| `--tentacle_address` | No | — | Dirección del servidor de Tentacle; tiene precedencia sobre `--as_agent_plugin` |
| `--tentacle_port` | No | `41121` | Puerto del servidor de Tentacle |
| `--as_agent_plugin` | No | `0` | `1` imprime el XML de los módulos en la salida estándar |
| `--prefix_module` | No | — | Prefijo que se antepone a cada nombre de módulo, seguido de `_` |

El archivo de consultas contiene una consulta por línea, con esta forma:

```text
<nombre del módulo>:<sentencia SQL>:<tipo de módulo>:<descripción>
```

El tercer campo se escribe tal cual como tipo de módulo, sin validación, y el cuarto es opcional. Un ejemplo de la configuración que se distribuye con la herramienta:

```text
User_connections:SELECT count(*) FROM sys.dm_exec_connections:generic_data_string:shows user connections.
```

El analizador aplica las reglas del colector de métricas con las mismas consecuencias: se omite toda línea que contenga `#` en cualquier posición, y un valor termina en los siguientes dos puntos, así que **una sentencia SQL que contenga dos puntos se trunca**. Una línea con menos de tres campos detiene la ejecución y descarta todas las consultas posteriores. Una consulta que falla imprime su error en la salida de error, se omite y la ejecución continúa con la siguiente.

El valor de cada módulo es una `<datalist>` en la que cada fila es una cadena con las columnas devueltas unidas por `;`, así que estos módulos también son de texto. El token `_database_` de una consulta se sustituye por el nombre de la base de datos, entrecomillado.

Hay dos comportamientos que conviene conocer antes de usarlo en producción:

- **Un fallo de conexión se informa como una ejecución correcta.** La herramienta imprime `Error while creating PostgreSQL table` y el error del controlador, después una segunda línea `Error:` en la salida de error, después `0`, y termina con estado `0`. Los mensajes nombran PostgreSQL, no Azure SQL: la descripción del agente que escribe es literalmente `PostgreSQL agent`.
- **La contraseña de la base de datos es un argumento de línea de comandos.** Es visible en la lista de procesos y en el historial de shell de la cuenta que ejecuta la herramienta.

### Identidad del addon

| Campo | Valor |
| --- | --- |
| Identificador en el Marketplace | `pandorafms.azuresql` |
| Nombre en el Marketplace | Pandora Azure SQL |
| Versión del addon | `1.0` |
| Última actualización en el Marketplace | 2025-06-26 |
| Paquete del Marketplace | `pandorafms.azuresql.1.0.pspz2` |
| Licencia | Descarga limitada a usuarios con licencia (etiqueta `One` del Marketplace) |
| Tipo del Marketplace | Miscelaneus |
| Flujo de trabajo | Plugin de monitorización, en modo plugin de servidor o de agente |
| Ejecutable | `pandora_azuresql` |
| Ejecutable secundario | `pandora_azuresqlquery`, ejecutor de consultas no descrito por el registro del Marketplace |
