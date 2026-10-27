# Plugin SAP HANA Database

*Última actualización del artículo: 2026-10-26.*

## Qué hace

El addon SAP HANA Database monitoriza una base de datos SAP HANA desde
Pandora FMS con las consultas SQL que usted escriba. Cada ejecución abre una
conexión al puerto SQL de una única base de datos, ejecuta todas las consultas
de un fichero de consultas y convierte cada resultado en un módulo de Pandora
FMS. No se instala nada en el servidor de base de datos y no hace falta ninguna
herramienta de línea de comandos de SAP en el host que ejecuta el addon.

Cada ejecución es puntual: conecta, recoge, entrega y termina, y no guarda
estado entre ejecuciones. Los módulos llegan a Pandora FMS de una de estas tres
formas:

- **Carpeta de datos** (por defecto): la ejecución escribe un documento de
  datos de agente en una carpeta de datos de Pandora FMS e imprime `1`.
- **Plugin de agente**: con `--as_agent_plugin 1` la ejecución imprime el XML de
  los módulos por la salida estándar, para que lo ingiera un agente de Pandora
  FMS, y no escribe ningún fichero.
- **Tentacle**: con `--tentacle_address` la ejecución escribe el documento y lo
  envía a un servidor Tentacle.

> La entrada de Marketplace `pandorafms.sap_hana_database` distribuye este
> colector basado en fichero de consultas. Existe una variante anterior del
> mismo addon que necesita las herramientas de cliente `hdbsql` y `sapcontrol`
> de SAP en el host de monitorización y ejecuta un conjunto fijo de consultas
> desde un fichero `clave=valor`; sus opciones y los nombres de sus módulos son
> distintos. Esta página no describe esa variante.

SAP HANA Discovery (`pandorafms.sap.hana`) es otro addon: se ejecuta desde el
asistente de tareas de Discovery y crea un agente por base de datos de forma
automática, con un conjunto fijo de grupos de métricas. Este addon se configura
en cada ejecución y publica lo que devuelven sus consultas. Consulte
[SAP HANA Discovery](../discovery/sap-hana.md).

## Preparar

### Compatibilidad y disponibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Addon `pandorafms.sap_hana_database`, versión `1.1` | Objetivo documentado | Versión de la entrada de Marketplace, actualizada el 2026-06-02. Consulte [Identidad del addon](#identidad-del-addon) |
| Versión de Pandora FMS | `Sin validar` | No existe un registro de validación para este addon. El Marketplace indica que sus integraciones son compatibles con Pandora FMS NG 784 y posteriores |
| Sistema del host que ejecuta el addon | `Sin validar` | No registrado para la versión `1.1`. La documentación anterior de este addon registró una prueba en CentOS 7 |
| Versión de SAP HANA | `Sin validar` | No registrada para la versión `1.1`. La documentación anterior de este addon registró SAP HANA `2.00.059` |
| Acceso SQL desde el host que ejecuta el addon al puerto de la base de datos | `Requerido` | El addon abre una conexión con `--ip` y `--port` |
| Un usuario de SAP HANA con permiso de lectura sobre todos los objetos que lean sus consultas | `Requerido` | Es un requisito previo, no una declaración de compatibilidad. Consulte [Acceso a la base de datos](#acceso-a-la-base-de-datos) |
| Un servidor de datos de Pandora FMS que lea `--data_dir` | `Requerido` para el modo de carpeta de datos | El documento solo se recoge si el servidor de datos lee la carpeta donde escribe el addon |
| Un servidor de Pandora FMS para ejecutar el plugin de consola | `Requerido` para el modo de consola | El servidor de plugins ejecuta el plugin registrado |

La descarga de este addon está limitada a usuarios con licencia, según su
entrada de Marketplace. Esta página no describe ninguna otra condición de
licencia.

### Requisitos

1. **Acceso de red** desde el host que ejecuta el addon al puerto SQL de la
   base de datos de destino. El addon no tiene puerto por defecto: `--port` es
   obligatorio.
2. **Un usuario de SAP HANA y su contraseña**, con permiso de lectura sobre
   todos los objetos que lean sus consultas. Las consultas de ejemplo leen las
   vistas de [Acceso a la base de datos](#acceso-a-la-base-de-datos).
3. **Un host para ejecutar el addon**: el servidor de Pandora FMS para un
   plugin de servidor en consola, un host con agente de Pandora FMS para el
   modo de plugin de agente, o cualquier host cuya carpeta de datos lea el
   servidor de datos de Pandora FMS. El addon conecta directamente al puerto de
   la base de datos, así que no necesita allí las herramientas de cliente de
   SAP.
4. **Un fichero de consultas.** El addon lo lee en cada ejecución; sin él la
   ejecución no publica nada (véase [Limitaciones conocidas](#limitaciones-conocidas)).
5. **Un extremo de Pandora FMS** que reciba la salida: el servidor de plugins
   que ejecuta el plugin registrado, el servidor de datos que lee la carpeta de
   datos, el agente que ejecuta el addon o el servidor Tentacle.
6. **Permiso de escritura en la carpeta de datos** para el usuario que ejecuta
   el addon, cuando los documentos se entregan allí.
7. **El cliente Tentacle (`tentacle_client`) en `PATH`**, solo cuando la
   ejecución entrega por Tentacle.

### Acceso a la base de datos

El addon lee únicamente lo que piden sus consultas. El usuario necesita permiso
de lectura sobre esos objetos; SAP HANA define qué privilegio exige cada vista
y para este addon no hay documentado un permiso más restrictivo. Las consultas
del fichero de ejemplo leen:

| Objeto | Se lee para |
| --- | --- |
| `DUMMY`, `M_DATABASE` | Marca de tiempo y versión |
| `M_CONVERTER_STATISTICS` | Estimación del tamaño de copia de seguridad |
| `M_DATA_VOLUMES` | Lista de volúmenes |
| `SYS_DATABASES.M_SERVICE_STATISTICS` | Peticiones por segundo y tiempo de respuesta |
| `M_SERVICE_THREADS` | Tiempo de CPU |
| `M_RS_MEMORY` | Fragmentación del row store |
| `M_LICENSE` | Validez, permanencia y uso de la licencia |
| `M_VOLUME_IO_TOTAL_STATISTICS` | Ancho de banda de lectura y escritura |
| `PUBLIC.M_CONNECTIONS` | Conexiones en ejecución |
| `M_HOST_RESOURCE_UTILIZATION` | Uso de memoria |
| `M_BLOCKED_TRANSACTIONS` | Transacciones bloqueadas |
| `SYS.M_BACKUP_CATALOG` | Solo las dos consultas de copia de seguridad del conjunto de ejemplo |

El addon envía cada línea del fichero de consultas a la base de datos tal como
está escrita, sin restringirla a `SELECT`. Use un usuario dedicado con acceso
de solo lectura y mantenga únicamente sentencias de lectura en el fichero.

### Instalar el addon

Descargue el paquete desde la entrada de Marketplace de Pandora FMS, que está
limitada a usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.sap_hana_database](https://marketplace.pandorafms.com/entries/pandorafms.sap_hana_database)

Copie el ejecutable del addon `pandora_hana` y el fichero de consultas de
ejemplo `pandora_hana.conf` al host que lo vaya a ejecutar. Para un plugin de
servidor en consola, la carpeta recomendada es
`/usr/share/pandora_server/util/plugin/`. Esta página invoca el ejecutable como
`pandora_hana`; use en los comandos siguientes el nombre que lleve su copia.

## Configurar

El addon no tiene fichero de configuración propio: todos los ajustes son
opciones de línea de comandos y las consultas viven en el fichero aparte que
indica `--conf`.

### Conexión

Una ejecución necesita la dirección de la base de datos, su puerto SQL, un
usuario, una contraseña y el fichero de consultas:

```bash
./pandora_hana --ip <TARGET_HOST> --port 30013 --user <USERNAME> \
    --password <PASSWORD> --conf <PATH_TO_CONFIG> --agent_name sap-hana
```

SAP HANA publica un puerto SQL por base de datos, y el puerto codifica el
número de instancia `NN`:

| Base de datos | Puerto |
| --- | --- |
| Base de datos de tenant | `3NN13` |
| Base de datos del sistema (`SYSTEMDB`) de un sistema multitenant | `3NN13` |
| Base de datos del sistema de un sistema single-tenant | `3NN15` |

Con la instancia `00`, por ejemplo, una base de datos de tenant escucha en
`30013` y la base de datos del sistema de un sistema single-tenant en `30015`.

`--password` se pasa en la línea de comandos: el shell la guarda en su
historial y la lista de procesos del sistema operativo la muestra mientras dura
la ejecución. En la consola, marque como oculto el campo que contiene la
contraseña y restrinja quién puede leer la lista de procesos del servidor. El
addon no tiene ninguna opción para leer la contraseña desde un fichero.

### Elegir el modo de entrega

| Modo | Opciones | Comportamiento |
| --- | --- | --- |
| Carpeta de datos (por defecto) | ninguna | Escribe un documento `<agent_name>.<epoch>.data` en `--data_dir` (por defecto `/var/spool/pandora/data_in/`) e imprime `1` |
| Plugin de agente | `--as_agent_plugin 1` | Imprime un bloque `<module>` por módulo por la salida estándar y no escribe ningún fichero |
| Tentacle | `--tentacle_address <ADDRESS>` | Escribe el documento en `--data_dir`, lo envía con `tentacle_client` e imprime `1` |

`--tentacle_address` tiene prioridad sobre `--as_agent_plugin`. Cualquier valor
de `--as_agent_plugin` distinto de `1` selecciona el modo de carpeta de datos,
que también es el valor por defecto. `--tentacle_port` vale `41121` por defecto
y solo se usa cuando se define `--tentacle_address`.

Use el modo de plugin de agente cuando un agente de Pandora FMS ejecute el
addon: el agente ingiere los módulos impresos. Use el modo de carpeta de datos
cuando el servidor de plugins ejecute el addon en la consola y el servidor de
datos local recoja el documento. Use Tentacle cuando el addon se ejecute en un
host que deba entregar a un servidor de Pandora FMS remoto.

`--agent_name` da nombre al agente que contiene los módulos; sin él el addon usa
`Sap_Hana`. `--prefix_module` antepone `<prefix>_` a todos los nombres de
módulo, de modo que varias ejecuciones pueden publicar en el mismo agente sin
nombres de módulo duplicados. `-g`/`--group` fija el nombre del grupo de
Pandora FMS que se escribe en el documento de agente; su valor por defecto es
`SAP`.

### Definir las consultas

El fichero de consultas tiene una consulta por línea, dividida en campos
separados por dos puntos:

```text
nombre:consulta:tipo_de_módulo[:descripción]
```

- `nombre` pasa a ser el nombre del módulo, `tipo_de_módulo` el tipo de módulo
  de Pandora FMS y el cuarto campo opcional la descripción del módulo. Los tres
  primeros campos son obligatorios.
- La consulta no puede contener dos puntos. La línea se divide por todos los
  dos puntos, así que un `:` dentro de la consulta desplaza el tipo y la
  descripción, y un `:` dentro de la descripción la trunca, ambos sin aviso.
- Una línea que contenga `#` en cualquier posición se omite como comentario, no
  solo las líneas que empiezan por `#`.
- Una línea se omite solo cuando está completamente vacía. Una línea con
  espacios se lee como consulta incompleta y detiene la ejecución (véase
  [Limitaciones conocidas](#limitaciones-conocidas)).
- Cada consulta produce un módulo. Cada fila devuelta se convierte en una
  entrada de la lista de datos del módulo, con las columnas de la fila unidas
  por `;`.
- Todas las consultas del fichero se ejecutan en cada ejecución, en el orden
  del fichero.

El fichero de ejemplo que se distribuye con el addon tiene esta forma:

```text
Timestamp:SELECT CURRENT_TIMESTAMP FROM DUMMY;:generic_data_string:Current timestamp
Hana_version:SELECT VERSION FROM M_DATABASE;:generic_data_string:version
Hana_Memory:SELECT HOST, round ( 100 * INSTANCE_TOTAL_MEMORY_USED_SIZE / INSTANCE_TOTAL_MEMORY_ALLOCATED_SIZE, 2), round (INSTANCE_TOTAL_MEMORY_ALLOCATED_SIZE / 1024/1024/1024, 2), round (INSTANCE_TOTAL_MEMORY_USED_SIZE / 1024/1024/1024, 2) from M_HOST_RESOURCE_UTILIZATION:generic_data_string:retrieve memory usages
```

El fichero completo está en
[Fichero de consultas de ejemplo](#fichero-de-consultas-de-ejemplo). Mantenga el
fichero legible solo por el usuario que ejecuta el addon: no contiene
credenciales, pero revela los objetos de base de datos que monitoriza.

### Registrar el plugin en la consola

Un plugin de servidor en consola ejecuta el addon desde el servidor de Pandora
FMS. El servidor de plugins lo ejecuta en modo de carpeta de datos, el addon
escribe su documento y el servidor de datos lo ingiere, de modo que el agente y
sus módulos aparecen en la consola.

1. Abra **Servers → Plugins** y pulse **Register Plugin**.
2. Indique el nombre, el tipo de plugin **Standard**, un tiempo máximo de
   espera opcional y una descripción.
3. En **Plugin command**, escriba la ruta a `pandora_hana` en el servidor de
   Pandora FMS, por ejemplo
   `/usr/share/pandora_server/util/plugin/pandora_hana`.
4. En **Plugin parameters**, pase la conexión mediante las macros de plugin
   `_field1_`, `_field2_`, ... y mantenga el fichero de consultas en una ruta
   fija del servidor:

```text
--ip _field1_ --port _field2_ --user _field3_ --password _field4_ --conf /etc/pandora/plugins/pandora_hana.conf --agent_name _field5_
```

5. En **Macro parameters**, describa cada campo. El ejemplo usa estos valores:

| Campo | Descripción | Valor de ejemplo |
| --- | --- | --- |
| `_field1_` | Nombre o dirección IP del host de la base de datos | `<TARGET_HOST>` |
| `_field2_` | Puerto SQL de la base de datos | `30013` |
| `_field3_` | Usuario de SAP HANA que ejecuta las consultas | `<USERNAME>` |
| `_field4_` | Contraseña de ese usuario; marque **Hide value** | — |
| `_field5_` | Nombre del agente que contendrá los módulos | `sap-hana` |

<!-- SCREENSHOT NEEDED: formulario de registro de Servers → Plugins para el addon SAP HANA Database, con la ruta del comando y los cinco parámetros _fieldN_. -->

No añada `--as_agent_plugin 1` aquí: la ejecución en consola debe quedarse en el
modo de carpeta de datos, porque el valor del módulo de plugin es lo que imprime
el addon, y en el modo de plugin de agente imprime el XML de los módulos en
lugar de `1`.

Una vez registrado, el plugin está disponible al crear módulos de plugin. Cada
módulo rellena los campos individualmente, y los valores de los campos pueden
usar las macros de Pandora FMS documentadas en la ayuda *Plug-in macros* de la
consola.

<!-- SCREENSHOT NEEDED: formulario de módulo de plugin con el plugin SAP HANA Database seleccionado, mostrando los parámetros por campo de una base de datos. -->

## Verificar

Ejecute el addon a mano con `--as_agent_plugin 1`, para que imprima los módulos
en lugar de escribir un fichero:

```bash
./pandora_hana --ip <TARGET_HOST> --port 30013 --user <USERNAME> \
    --password <PASSWORD> --conf <PATH_TO_CONFIG> --as_agent_plugin 1
```

Una ejecución correcta imprime un bloque `<module>` por consulta y termina con
estado `0`. Los valores siguientes son ilustrativos; los suyos vendrán de su
base de datos:

```xml
<module>
	<name><![CDATA[Timestamp]]></name>
	<type>generic_data_string</type>
	<datalist>
	<data>
		<value><![CDATA[2026-10-26 10:14:32.123456789]]></value>
	</data>
	</datalist>
	<description><![CDATA[Current timestamp]]></description>
</module>
<module>
	<name><![CDATA[Hana_get_stated_connections]]></name>
	<type>generic_data</type>
	<datalist>
	<data>
		<value><![CDATA[7]]></value>
	</data>
	</datalist>
	<description><![CDATA[retrieve connection status]]></description>
</module>
```

Con el modo de carpeta de datos por defecto, la misma ejecución imprime `1` y
escribe un documento:

```text
/var/spool/pandora/data_in/sap-hana.1793001234.data
```

Tras la primera ejecución programada, abra el agente indicado en `--agent_name`
(por defecto `Sap_Hana`) y compruebe que contiene un módulo por cada consulta
del fichero.

`-h` imprime el resumen de uso con sus opciones y un ejemplo de ejecución. El
resumen incluye la marca de compilación del addon, `270622`, que no coincide
con la versión del Marketplace (véase
[Limitaciones conocidas](#limitaciones-conocidas)).

## Entender los resultados

Una ejecución crea un agente, o actualiza el existente, y nunca más de uno. El
documento de agente declara estas propiedades:

| Propiedad | Valor |
| --- | --- |
| Nombre y alias del agente | `--agent_name` (por defecto `Sap_Hana`) |
| Descripción | `SAP Hana` |
| Grupo | `--group` (por defecto `SAP`) |
| Intervalo | Vacío; Pandora FMS asigna el intervalo de un agente nuevo |
| Dirección | Vacía |

Cada línea del fichero de consultas produce exactamente un módulo:

- El nombre del módulo es el primer campo, con el prefijo `<prefix>_` cuando se
  define `--prefix_module`.
- El tipo del módulo es el tercer campo, escrito tal cual. Use el tipo de módulo
  de Pandora FMS que pidan sus datos: `generic_data` para números y
  `generic_data_string` para texto.
- La descripción es el cuarto campo, y queda vacía cuando el campo no aparece.
- El valor es una lista de datos con una entrada por fila devuelta. Las columnas
  de una fila se unen con `;` dentro de la entrada, así que una consulta de tres
  columnas devuelve entradas como `host01;30003;7`.

Como todas las columnas de todas las filas forman parte de un único valor,
escriba los módulos numéricos con una consulta que devuelva una fila y una
columna. Una consulta que devuelve varias filas publica varias entradas en la
misma lista de datos, y una consulta que devuelve varias columnas las publica
concatenadas.

Una consulta que no devuelve filas produce igualmente su módulo, con la lista
de datos vacía. Una consulta que la base de datos rechaza no produce ningún
módulo: el fallo se informa por la salida de error y las consultas siguientes se
ejecutan igualmente.

El fichero de ejemplo agrupa sus consultas por tema:

- **Copias de seguridad y volúmenes.** `Backups_Size` estima el tamaño de la
  copia de seguridad y `Data_disk_information` lista los volúmenes de datos.
- **Versión y tiempo.** `Timestamp` y `Hana_version` identifican la base de
  datos y fechan la ejecución.
- **Rendimiento.** `Hana_service_statics` informa de las peticiones por segundo
  y el tiempo de respuesta, `Hana_cpu_time` del tiempo de CPU de los servicios
  y `Hana_IO_Stats` del ancho de banda de lectura y escritura por volumen.
- **Memoria.** `Hana_Memory` informa de la memoria en uso sobre la memoria
  asignada, y `Hana_rs_fragmentation` del porcentaje libre del row store.
- **Capacidad y salud.** `Hana_license` informa de la validez, permanencia y uso
  de la licencia, `Hana_get_stated_connections` de las conexiones en ejecución y
  `Hana_Transactions` de las transacciones bloqueadas.

## Operar y solucionar problemas

### Comportamiento en ejecución

- Una ejecución abre una conexión, ejecuta todas las consultas del fichero en
  orden, entrega y termina. La conexión se abre antes de leer el fichero de
  consultas, así que una base de datos inaccesible detiene la ejecución antes de
  interpretar ninguna consulta.
- El addon no guarda estado entre ejecuciones. El fichero de consultas se relee
  en cada ejecución, de modo que una consulta añadida se recoge desde la
  ejecución siguiente.
- No hay opción de verbosidad ni de depuración. La salida es el XML de los
  módulos con `--as_agent_plugin 1`, un `1` en los otros dos modos, o un mensaje
  de error.
- El addon escribe un documento por ejecución, así que una ejecución recoge
  todos los módulos del agente con la misma marca de tiempo.

### Limitaciones conocidas

Son comportamientos de la versión `1.1`, documentados tal como son.

- **El fichero de consultas es obligatorio de hecho.** Una ejecución sin un
  `--conf` legible imprime `Error al conectarse` seguido del error del sistema
  operativo, después `Error: name 'f' is not defined` y `0`, y termina con
  estado `0` sin publicar nada.
- **Una línea en blanco con espacios detiene la ejecución con estado `0`.**
  Solo se ignora una línea completamente vacía. Una línea con espacios o
  tabuladores tiene menos de tres campos, así que la ejecución imprime
  `It is mandatory to specify name, query and type!`, termina de inmediato y no
  publica nada, y el estado de salida es `0`.
- **Una consulta no puede contener dos puntos y una descripción pierde todo lo
  que sigue a uno.** La línea se divide por todos los dos puntos, así que un `:`
  dentro de la consulta desplaza el tipo de módulo y un `:` dentro de la
  descripción la trunca. En ninguno de los dos casos se imprime un aviso.
- **Una línea con `#` en cualquier posición se omite.** Un `#` dentro de una
  consulta o de una descripción elimina la línea completa de la ejecución, no
  solo las líneas de comentario.
- **Una entrega Tentacle fallida imprime `1` igualmente.** Con
  `--tentacle_address`, el addon escribe el documento, lo envía e imprime `1`
  aunque `tentacle_client` falle o no exista; el error va a la salida de error y
  el documento se queda en `--data_dir`.
- **Dos ejecuciones del mismo agente en un segundo colisionan.** El nombre del
  documento usa resolución de un segundo y el fichero se crea en exclusiva. Una
  ejecución que empieza mientras el documento anterior del mismo agente sigue en
  la carpeta termina con
  `ERROR - Could not write file: ... please check directory permissions` y
  estado `1`, y los módulos de esa ejecución se pierden.
- **La marca de compilación no coincide con la versión del Marketplace.** El
  resumen de uso imprime la marca de compilación `270622`, la fecha de la
  compilación, mientras que la entrada de Marketplace publica la versión `1.1`.
- **No hay ninguna opción de TLS ni de certificados.** El addon pasa la
  dirección, el puerto, el usuario y la contraseña al cliente de base de datos y
  deja cualquier ajuste de cifrado a los valores por defecto de ese cliente. No
  tiene opción para fijar un certificado ni para exigir una conexión cifrada.
- **La contraseña solo existe como opción de línea de comandos.** No hay fichero
  de credenciales ni forma de pasarla por la entrada estándar, así que la
  contraseña aparece en el historial del shell y en la lista de procesos del host
  que ejecuta el addon.
- **`--tentacle_port` se ignora sin `--tentacle_address`.** El puerto solo lo usa
  la rama de Tentacle.

### Diagnóstico

| Síntoma | Causa y acción |
| --- | --- |
| Una traza del cliente de base de datos que acaba en la llamada de conexión, estado `1` | La conexión falló. Compruebe `--ip`, `--port`, el usuario, la contraseña y el camino de red hasta el puerto SQL. Recuerde que una base de datos de tenant y la base de datos del sistema escuchan en puertos distintos |
| `Error al conectarse` y después `Error: ...` y `0`, estado `0` | No se pudo abrir `--conf`. Compruebe la ruta y sus permisos de lectura |
| `It is mandatory to specify name, query and type!` | Una línea del fichero de consultas tiene menos de tres campos separados por dos puntos, normalmente porque está vacía o solo tiene espacios |
| `error with the query:<consulta>.<error>` por la salida de error | La base de datos rechazó esa consulta. Las líneas siguientes se siguen procesando |
| Falta un módulo en el agente | Su consulta falló, o su línea se omitió porque contenía `#` |
| Un módulo numérico recibe más de una entrada de datos por ejecución | La consulta devuelve más de una fila. Redúzcala a una fila y una columna para los módulos numéricos |
| `Tentacle error` por la salida de error y un `1` almacenado | La transferencia falló. Compruebe `--tentacle_address`, `--tentacle_port` y que `tentacle_client` esté en `PATH`; el documento permanece en `--data_dir` |
| `ERROR - Could not write file: ...` | La carpeta de datos no es escribible, o ya existe un documento con el mismo nombre (véase [Limitaciones conocidas](#limitaciones-conocidas)) |
| El agente no aparece en la consola | El documento se escribió en un `--data_dir` que el servidor de datos de Pandora FMS no lee, o la ejecución terminó con error. Compruebe la carpeta y la salida de la ejecución |
| `bad interpreter` o un mensaje de intérprete ausente | El intérprete declarado en la primera línea del ejecutable no está instalado en este host, o el fichero perdió el permiso de ejecución. Ejecute el addon desde un host que tenga ese intérprete, o restaure el permiso con `chmod +x` |

## Referencia

### Opciones de línea de comandos

| Opción | Obligatoria | Por defecto | Descripción |
| --- | --- | --- | --- |
| `--ip` | Sí | — | Nombre o dirección IP del host de la base de datos |
| `--port` | Sí | — | Puerto SQL de la base de datos (`3NN13` para una base de datos de tenant, `3NN15` para la base de datos del sistema de un sistema single-tenant) |
| `--user` | Sí | — | Usuario de SAP HANA que ejecuta las consultas |
| `--password` | Sí | — | Contraseña de ese usuario |
| `--conf` | Sí | — | Fichero de consultas. Se lee en cada ejecución |
| `--agent_name` | No | `Sap_Hana` | Nombre y alias del agente que contiene los módulos |
| `--prefix_module` | No | — | Prefijo unido a cada nombre de módulo como `<prefix>_<nombre>` |
| `-g`, `--group` | No | `SAP` | Nombre del grupo de Pandora FMS que se escribe en el documento de agente |
| `--data_dir` | No | `/var/spool/pandora/data_in/` | Carpeta del documento de datos de agente en los modos de carpeta de datos y Tentacle |
| `--as_agent_plugin` | No | `0` | `1` imprime el XML de los módulos por la salida estándar; cualquier otro valor escribe el documento en `--data_dir` |
| `--tentacle_address` | No | — | Dirección del servidor Tentacle. Tiene prioridad sobre `--as_agent_plugin` |
| `--tentacle_port` | No | `41121` | Puerto del servidor Tentacle, solo se usa con `--tentacle_address` |
| `-h`, `--help` | No | — | Imprime el resumen de uso y termina |

### Fichero de consultas

| Campo | Obligatorio | Descripción |
| --- | --- | --- |
| `nombre` | Sí | Nombre del módulo. Con `--prefix_module`, el nombre del módulo es `<prefix>_<nombre>` |
| `consulta` | Sí | Sentencia SQL ejecutada contra la base de datos. No puede contener dos puntos |
| `tipo_de_módulo` | Sí | Tipo de módulo de Pandora FMS, escrito tal cual en el módulo |
| `descripción` | No | Descripción del módulo. No puede contener dos puntos |

Una línea que contenga `#` se omite. Una línea completamente vacía se omite.
Cualquier otra línea se divide por `:` y se ejecuta.

### Fichero de consultas de ejemplo

Este es el fichero de ejemplo que se distribuye con el addon:

```text
Backups_Size:SELECT SUM(allocated_page_size) FROM M_CONVERTER_STATISTICS;:generic_data:Estimated backup size
Timestamp:SELECT CURRENT_TIMESTAMP FROM DUMMY;:generic_data_string:Current timestamp
Hana_version:SELECT VERSION FROM M_DATABASE;:generic_data_string:version
Data_disk_information:SELECT HOST,PORT,FILE_NAME,STATE,SIZE,MAX_SIZE FROM M_DATA_VOLUMES:generic_data_string:Retrieve Hana disk info
Hana_service_statics:SELECT SERVICE_NAME, DATABASE_NAME, REQUESTS_PER_SEC, RESPONSE_TIME FROM SYS_DATABASES.M_SERVICE_STATISTICS:generic_data_string:Retrieve Hana Requests per second
Hana_cpu_time:SELECT HOST,PORT,SERVICE_NAME, SUM(CPU_TIME_SELF),SUM(CPU_TIME_CUMULATIVE) FROM M_SERVICE_THREADS GROUP BY HOST,PORT,SERVICE_NAME:generic_data_string:Retrieve Hana cpu usage
Hana_rs_fragmentation:SELECT HOST, PORT, TO_DECIMAL(SUM(FREE_SIZE) * 100 / SUM(ALLOCATED_SIZE),10,2), TO_DECIMAL( SUM(FREE_SIZE)/(1024*1024), 10, 2), TO_DECIMAL( SUM(ALLOCATED_SIZE)/(1024*1024), 10, 2) FROM M_RS_MEMORY WHERE CATEGORY = 'TABLE' OR CATEGORY = 'CATALOG'  GROUP BY HOST, PORT:generic_data_string:Retrieve Hana row store fragmentation
Hana_license:SELECT VALID, PERMANENT, PRODUCT_LIMIT, PRODUCT_USAGE FROM M_LICENSE;:generic_data_string:Retrieve license usage
Hana_IO_Stats:SELECT HOST,PORT,TYPE, TO_DECIMAL((TOTAL_READ_SIZE * 1.048576 / (TOTAL_READ_TIME+1)),10,2), TO_DECIMAL((TOTAL_WRITE_SIZE * 1.048576 / (TOTAL_WRITE_TIME+1)),10,2) FROM M_VOLUME_IO_TOTAL_STATISTICS:generic_data_string:Retrieve IO bandwidth
Hana_get_stated_connections:SELECT COUNT(*) FROM PUBLIC.M_CONNECTIONS WHERE CONNECTION_STATUS ='RUNNING':generic_data:retrieve connection status
Hana_Memory:SELECT HOST, round ( 100 * INSTANCE_TOTAL_MEMORY_USED_SIZE / INSTANCE_TOTAL_MEMORY_ALLOCATED_SIZE, 2), round (INSTANCE_TOTAL_MEMORY_ALLOCATED_SIZE / 1024/1024/1024, 2), round (INSTANCE_TOTAL_MEMORY_USED_SIZE / 1024/1024/1024, 2) from M_HOST_RESOURCE_UTILIZATION:generic_data_string:retrieve memory usages
Hana_Transactions:SELECT count(*) FROM M_BLOCKED_TRANSACTIONS;:generic_data:retrieve SAP transaction status
```

La entrada de Marketplace nombra además dos módulos del catálogo de copias de
seguridad, `Check_no_running_backups` y `Backup_id_running_backup`, que esta
copia del fichero no incluye, y su lista no nombra `Data_disk_information`, que
el fichero sí incluye. Añada las líneas de copia de seguridad como propias si
necesita monitorizar las copias:

```text
Check_no_running_backups:select * from SYS.M_BACKUP_CATALOG where STATE_NAME = 'running':generic_data_string:Check that no backup is still running
Backup_id_running_backup:select BACKUP_ID from SYS.M_BACKUP_CATALOG where entry_type_name = 'complete data backup' and state_name = 'running' order by sys_start_time desc:generic_data_string:Query to find the BACKUP_ID of the running data backup
```

### Módulos generados

Módulos del fichero de ejemplo, en el orden del fichero:

| Módulo | Tipo en el fichero | Qué lee |
| --- | --- | --- |
| `Backups_Size` | `generic_data` | Suma de `allocated_page_size` en `M_CONVERTER_STATISTICS` |
| `Timestamp` | `generic_data_string` | `CURRENT_TIMESTAMP` de la base de datos |
| `Hana_version` | `generic_data_string` | `VERSION` de `M_DATABASE` |
| `Data_disk_information` | `generic_data_string` | Host, puerto, nombre de fichero, estado, tamaño y tamaño máximo de cada volumen de datos |
| `Hana_service_statics` | `generic_data_string` | Servicio, base de datos, peticiones por segundo y tiempo de respuesta |
| `Hana_cpu_time` | `generic_data_string` | Tiempo de CPU por host, puerto y servicio |
| `Hana_rs_fragmentation` | `generic_data_string` | Porcentaje libre y tamaños del row store por host y puerto |
| `Hana_license` | `generic_data_string` | Validez, permanencia, límite y uso de la licencia |
| `Hana_IO_Stats` | `generic_data_string` | Ancho de banda de lectura y escritura por host, puerto y tipo de volumen |
| `Hana_get_stated_connections` | `generic_data` | Número de conexiones en estado `RUNNING` |
| `Hana_Memory` | `generic_data_string` | Porcentaje de memoria usada, memoria asignada y memoria usada |
| `Hana_Transactions` | `generic_data` | Número de transacciones bloqueadas |
| `Check_no_running_backups` | `generic_data_string` | Entradas del catálogo de copias de seguridad aún en ejecución, cuando añade la línea |
| `Backup_id_running_backup` | `generic_data_string` | Identificador de la copia de seguridad completa en ejecución, cuando añade la línea |

### Documento de agente

| Propiedad | Valor |
| --- | --- |
| Nombre del fichero | `<agent_name>.<epoch>.data` en `--data_dir` |
| Modo de agente | `1` |
| Marca de tiempo | Hora local de la ejecución, como `YYYY/MM/DD HH:MM:SS` |
| Módulos | Uno por consulta, todos con la marca de tiempo de la ejecución |

### Código de salida

| Estado | Significado |
| --- | --- |
| `0` | Ejecución correcta. También se usa cuando no se puede abrir el fichero de consultas, cuando una línea suya está mal formada y cuando un error interrumpe la fase de consultas |
| `1` | La conexión falló, o no se pudo escribir el documento |
| `2` | Falta una opción o recibió un valor de tipo incorrecto, por ejemplo un `--as_agent_plugin` no entero |

### Identidad del addon

| Propiedad | Valor |
| --- | --- |
| Identificador del Marketplace | `pandorafms.sap_hana_database` |
| Nombre | SAP HANA Database |
| Versión | `1.1` |
| Paquete | `pandorafms.sap_hana_database.1.1.zip` |
| Otra versión publicada | `1.0`, paquete `pandorafms.sap_hana_database.1.0.zip`, de fecha 2025-06-25 |
| Licencia | One; la descarga está limitada a usuarios con licencia |
| Última actualización en el Marketplace | 2026-06-02 |
| Descargas | 16 |
| Autor | Pandora FMS |
| Tipo en el Marketplace | Miscelaneus |
| Etiquetas | `applications`, `databases` |
| Ejecutable | `pandora_hana` |
| Fichero de consultas de ejemplo | `pandora_hana.conf` |
