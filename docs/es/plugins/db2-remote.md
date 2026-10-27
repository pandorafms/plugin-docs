# DB2 Remote plugin

*Última actualización del artículo: 2026-10-26.*

## Qué hace

El addon DB2 Remote monitoriza bases de datos IBM Db2 desde Pandora FMS por
TCP/IP. No se instala nada en el servidor de base de datos: cada ejecución abre
una conexión desde el host que ejecuta el addon, lanza las sentencias que
guarde en un archivo de consultas y publica el resultado como módulos de
Pandora FMS.

Una ejecución produce dos tipos de salida:

- **Módulos de consulta.** Un módulo por cada sentencia del archivo de
  consultas, con una entrada de lista de datos por cada fila que devuelve la
  sentencia.
- **Módulos de rendimiento predeterminados.** Un conjunto fijo de métricas de
  buffer pools y de log de transacciones, leídas de vistas administrativas de
  Db2. Están habilitados salvo que los desactive.

Cada ejecución es independiente: conecta, recoge, entrega y termina. El addon
no guarda estado entre ejecuciones, de modo que una ejecución en cualquier
momento informa de los valores que la base de datos tiene en ese momento.

Los módulos llegan a Pandora FMS como XML de módulos por la salida estándar,
para que los ingiera un agente de Pandora FMS, o como documentos de datos de
agente escritos en una carpeta de datos de Pandora FMS (consulte
[Configuración](#configuracion)).

DB2 Discovery (`pandorafms.db2`) es otro addon: se ejecuta desde el asistente de
tareas de Discovery y genera automáticamente un agente por base de datos. El
plugin DB2 Remote se configura en cada ejecución y publica los módulos que
producen las sentencias que usted escribe. Consulte
[DB2 Discovery](../discovery/db2.md).

## Preparación

### Compatibilidad y disponibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Addon `pandorafms.db2_remote`, versión `1.0` | Objetivo documentado | Versión de la entrada del Marketplace, que el addon imprime además en su resumen de uso. Consulte [Identidad del addon](#identidad-del-addon) |
| Acceso TCP desde el host que ejecuta el addon hasta el listener de Db2 (puerto `50000` por defecto) | `Requerido` | El addon conecta con `--hostname`, `--port` y `--protocol` |
| Un usuario de Db2 con permiso de lectura sobre cada objeto que lean sus sentencias | `Requerido` | Es un requisito previo, no una declaración de compatibilidad |
| Un intérprete `python3` con el driver `ibm-db` `3.1.4` | `Requerido` | El `requirements.txt` del paquete fija `ibm-db==3.1.4` |
| Versiones y plataformas del servidor Db2 | `Sin validar` | No hay matriz de versiones registrada para este addon |
| Sistema operativo del host que ejecuta el addon | `Sin validar` | No hay sistema operativo registrado para la versión `1.0` |
| Versión de Pandora FMS | `Sin validar` | No existe un registro de validación por versión. El Marketplace indica que sus integraciones son compatibles con Pandora FMS NG 784 y posteriores |

La entrada del Marketplace indica que este addon ya no se mantiene ni se
actualiza activamente y remite a las alternativas publicadas en su biblioteca.

### Requisitos

1. **Acceso de red** desde el host que ejecuta el addon hasta el listener de
   Db2, por defecto en el puerto TCP `50000`.
2. **Un usuario de Db2 y su contraseña**, con permiso de lectura sobre cada
   objeto que lean sus sentencias y, cuando los módulos de rendimiento
   predeterminados están habilitados, sobre las vistas administrativas que se
   indican en [Acceso a la base de datos](#acceso-a-la-base-de-datos).
3. **Un host para ejecutar el addon**: el servidor de Pandora FMS para un
   plugin de servidor en la consola, un host con un agente de Pandora FMS para
   el modo plugin de agente, o cualquier host cuya carpeta de datos lea el
   servidor de datos de Pandora FMS.
4. **Un intérprete `python3`** con el driver `ibm-db` instalado, en la versión
   que fija el `requirements.txt` del paquete.
5. **Una instalación de Pandora FMS** que reciba la salida: el servidor de
   plugins que ejecuta el plugin registrado, el agente que lo ejecuta, o el
   servidor de datos que lee la carpeta de datos.
6. **Permiso de escritura en la carpeta de datos** para el usuario que ejecuta
   el addon, cuando los documentos se entregan allí.
7. **Un archivo de consultas.** El addon lo lee en cada ejecución, incluidas
   las ejecuciones que solo necesitan los módulos de rendimiento
   predeterminados (consulte [Limitaciones conocidas](#limitaciones-conocidas)).

### Acceso a la base de datos

El addon lee únicamente lo que piden sus sentencias y los módulos de
rendimiento predeterminados:

| Lectura | Cuándo |
| --- | --- |
| Los objetos que leen sus propias sentencias | En cada ejecución |
| `SYSCAT.BUFFERPOOLS`, `SYSIBMADM.BP_HITRATIO`, `SYSIBMADM.LOG_UTILIZATION` | Con los módulos de rendimiento predeterminados habilitados, que es lo predeterminado |

Db2 define qué autoridad exige cada vista administrativa. Ninguna fuente
oficial de este addon documenta un permiso más restrictivo, así que conceda al
usuario el mínimo que Db2 acepte para las lecturas que habilite.

El addon ejecuta el texto de la sentencia tal como está escrito y no lo limita a
`SELECT`. Use un usuario dedicado con acceso de solo lectura y mantenga
únicamente sentencias de lectura en el archivo de consultas.

### Instalar el addon

Descargue el paquete desde la entrada del Marketplace de Pandora FMS, que está
limitada a usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.db2_remote](https://marketplace.pandorafms.com/entries/pandorafms.db2_remote)

Copie el script del addon `pandora_db2.py` y su archivo de consultas de ejemplo
`db2.conf` al host que lo vaya a ejecutar. Para un plugin de servidor en la
consola, la carpeta recomendada es `/usr/share/pandora_server/util/plugin/`.

Instale el driver que fija el `requirements.txt` del paquete (`ibm-db==3.1.4`)
para el intérprete que vaya a ejecutar el addon.

## Configuración

El addon no tiene archivo de configuración propio: todo es opción de línea de
comandos, y las consultas viven en el archivo separado que indica `--conf`.

### Conexión

Una ejecución necesita el host, la base de datos, un usuario y una contraseña:

```bash
python3 pandora_db2.py --hostname <TARGET_HOST> --port 50000 --database <DB_NAME> \
    --uid <USERNAME> --password <PASSWORD> --conf <PATH_TO_CONFIG> --as_agent_plugin 1
```

`--port` vale `50000` por defecto y `--protocol` vale `TCPIP`, así que ambos
pueden omitirse. El addon construye una cadena de conexión completa a partir de
estas opciones, por lo que no necesita un cliente Db2 local, una entrada de
catálogo ni un DSN en el host que lo ejecuta.

La opción `--password` en la línea de comandos queda en el historial del shell y
es visible en la lista de procesos mientras dura la ejecución. El addon no
tiene opción de archivo de credenciales en esta versión; en la consola, marque
como oculto el campo que contiene la contraseña (consulte
[Registrar el plugin en la consola](#registrar-el-plugin-en-la-consola)).

### Elegir el modo de entrega

| Modo | Opción | Comportamiento |
| --- | --- | --- |
| Carpeta de datos (predeterminado) | ninguna | Escribe un documento `<agent_name>.<timestamp>.data` en `--data_dir` (`/var/spool/pandora/data_in/` por defecto) por cada documento que produce, e imprime `1` por documento |
| Plugin de agente | `--as_agent_plugin 1` | Imprime un bloque `<module>` por módulo en la salida estándar y no escribe archivos |
| Tentacle | `--tentacle_address <ADDRESS>` | Se configura con `--tentacle_address` y `--tentacle_port`; no entrega en la versión `1.0` (consulte [Limitaciones conocidas](#limitaciones-conocidas)) |

`--tentacle_address` tiene prioridad sobre `--as_agent_plugin`; cualquier valor
de `--as_agent_plugin` distinto de `1` selecciona la carpeta de datos.

Use el modo plugin de agente cuando un agente de Pandora FMS ejecute el addon:
el agente ingiere los módulos impresos. Use la carpeta de datos cuando lo
ejecute el servidor de plugins en la consola y el servidor de datos local
recoja los documentos.

`--default_metrics` vale `1` por defecto; cualquier otro valor publica solo los
módulos de consulta.

### Definir las consultas

El archivo de consultas tiene una sentencia por línea, dividida en campos
separados por dos puntos:

```text
name:statement:module_type[:description]
```

Este es el ejemplo que incluye el paquete:

```text
query_test:select * from department:generic_data:testing query
```

- `name` se convierte en el nombre del módulo, `module_type` en el tipo de
  módulo y el cuarto campo opcional en la descripción del módulo. Los tres
  primeros campos son obligatorios.
- La sentencia no puede contener dos puntos. La línea se divide por cada dos
  puntos, de modo que un `:` dentro de la sentencia desplaza el tipo y la
  descripción y produce un módulo distinto sin avisar.
- Una línea que contiene `#` en cualquier posición se omite como comentario, no
  solo las que empiezan por `#`.
- Las líneas en blanco se ignoran.
- `_database_` se sustituye por el nombre de la base de datos conectada entre
  comillas simples, así que puede usarse donde se espera un literal de cadena.
  Con `--database <DB_NAME>`, la línea `select * from syscat.tables where
  tabschema = _database_` llega a la base de datos como `select * from
  syscat.tables where tabschema = '<DB_NAME>'`.
- Cada sentencia produce un módulo. Cada fila devuelta se convierte en una
  entrada de la lista de datos del módulo, con la fila como correspondencia de
  columna y valor.
- Todas las sentencias del archivo se ejecutan en cada ejecución.

### Registrar el plugin en la consola

Un plugin de servidor en la consola ejecuta el addon desde el servidor de
Pandora FMS. El servidor de plugins lo ejecuta, el addon escribe sus documentos
en la carpeta de datos y el servidor de datos los ingiere, de modo que los
agentes y sus módulos aparecen en la consola.

1. Abra **Servers → Plugins** y haga clic en **Register Plugin**.
2. Indique el nombre, el tipo de plugin **Standard**, un tiempo máximo de
   ejecución opcional y una descripción.
3. En **Plugin command**, escriba la ruta a `pandora_db2.py` en el servidor de
   Pandora FMS, por ejemplo
   `/usr/share/pandora_server/util/plugin/pandora_db2.py`.
4. En **Plugin parameters**, pase la conexión con las macros de plugin
   `_field1_`, `_field2_`, ... y mantenga el archivo de consultas en una ruta
   fija del servidor:

```text
--hostname _field1_ --port 50000 --database _field2_ --uid _field3_ --password _field4_ --conf /etc/pandora/plugins/db2.queries --agent_name db2-remote
```

5. En **Macro parameters**, describa cada campo. El ejemplo usa estos valores:

| Campo | Descripción | Valor de ejemplo |
| --- | --- | --- |
| `_field1_` | Nombre o dirección IP del host Db2 | `<TARGET_HOST>` |
| `_field2_` | Nombre de la base de datos | `<DB_NAME>` |
| `_field3_` | Usuario de Db2 que ejecuta las sentencias | `<USERNAME>` |
| `_field4_` | Contraseña de ese usuario; marque **Hide value** | — |

<!-- SCREENSHOT NEEDED: Formulario de registro en Servers → Plugins del addon DB2 Remote, con la ruta del comando y los cuatro parámetros _fieldN_. -->

`--agent_name` da nombre al agente que recibe los módulos de consulta; sin él,
el addon usa `DB2` y el agente de métricas es `<agent_name>_metrics`.

En este modo el valor del módulo es el texto que imprime el addon, normalmente
`1` por documento entregado. Una ejecución que deba entregar varios documentos
está sujeta a la limitación de la carpeta de datos descrita en
[Limitaciones conocidas](#limitaciones-conocidas).

## Verificación

Ejecute el addon manualmente con `--as_agent_plugin 1`, para que imprima los
módulos en lugar de escribir archivos:

```bash
python3 pandora_db2.py --hostname <TARGET_HOST> --database <DB_NAME> \
    --uid <USERNAME> --password <PASSWORD> --conf <PATH_TO_CONFIG> --as_agent_plugin 1
```

Una ejecución correcta imprime un bloque `<module>` por módulo y termina con
estado `0`. Los valores siguientes son ilustrativos; los suyos proceden de su
base de datos. Este es el módulo que produce la consulta de ejemplo:

```xml
<module>
	<name><![CDATA[query_test]]></name>
	<type>generic_data</type>
	<datalist>
	<data>
		<value><![CDATA[{'DEPTNO': 'A00', 'DEPTNAME': 'SPIFFY COMPUTER SERVICE DIV.'}]]></value>
	</data>
	</datalist>
	<description><![CDATA[testing query]]></description>
</module>
```

Cuando los módulos de rendimiento predeterminados están habilitados se imprimen
después de los módulos de consulta, un bloque por métrica:

```xml
<module>
	<name><![CDATA[no_of_bufferpools_<DB_NAME>]]></name>
	<type>generic_data</type>
	<data><![CDATA[3]]></data>
	<description><![CDATA[]]></description>
	<unit><![CDATA[count]]></unit>
</module>
```

Con la entrega predeterminada en la carpeta de datos, la misma ejecución imprime
`1` una vez por documento y escribe archivos con el nombre
`<agent_name>.<timestamp>.data` en `--data_dir`:

```text
/var/spool/pandora/data_in/db2-remote.<timestamp>.data
```

Después de la primera ejecución programada, compruebe la consola:

1. El agente indicado por `--agent_name` (`DB2` por defecto), con un módulo por
   cada sentencia del archivo de consultas.
2. El agente `<agent_name>_metrics`, con los módulos de rendimiento
   predeterminados.
3. El valor del módulo de plugin que lanzó la ejecución.

<!-- SCREENSHOT NEEDED: Lista de módulos del agente DB2 Remote tras una ejecución correcta, con un módulo de consulta y el agente de métricas separado. -->

El addon imprime su resumen de uso, con un ejemplo de ejecución manual, cuando
se ejecuta con `-h`.

## Entender los resultados

Una ejecución crea como máximo dos agentes. Ambos se asignan al grupo indicado
con `--group` y ambos llevan la descripción `Agent generated by pandora_db2`.

| Agente | Nombre | Alias | Contenido | Condición |
| --- | --- | --- | --- | --- |
| Agente de consulta | `--agent_name` (`DB2` por defecto) | Igual que el nombre | Un módulo por cada sentencia del archivo de consultas | El archivo de consultas tiene al menos una sentencia |
| Agente de métricas | `<agent_name>_metrics` | `<agent_name>` | Los módulos de rendimiento predeterminados | `--default_metrics 1` |

El agente de métricas repite el alias del agente de consulta, así que la consola
muestra el mismo alias para los dos agentes.

### Módulos de consulta

Cada módulo toma el nombre del primer campo de su línea y el tipo del tercer
campo. Su valor es una lista de datos con una entrada por fila, y cada entrada
mantiene visibles en los datos del módulo los nombres de columna de la fila. La
descripción del módulo es el cuarto campo, y queda vacía cuando ese campo no
está.

### Módulos de rendimiento predeterminados

Las métricas cubren tres grupos: el número de buffer pools, los contadores de
lectura de los buffer pools y la utilización del log de transacciones. Todos los
nombres de módulo terminan con el nombre de la base de datos. La lista completa
está en [Módulos generados](#modulos-generados).

## Operación y diagnóstico

### Comportamiento en ejecución

- Una ejecución conecta una vez, lanza en orden todas las sentencias del
  archivo de consultas, después los módulos de rendimiento predeterminados,
  entrega y termina.
- Los módulos de consulta se entregan antes que las métricas, de modo que un
  fallo de las métricas no deshace lo que ya publicaron las sentencias.
- El addon no tiene opción de verbose ni de depuración. Su salida es el XML de
  módulos con `--as_agent_plugin 1`, un `1` por documento en el modo de carpeta
  de datos, o un mensaje de error.
- El addon no guarda estado entre ejecuciones. El archivo de consultas se lee
  de nuevo en cada ejecución.

### Limitaciones conocidas

Estos son comportamientos de la versión `1.0`, documentados tal como son.

- **El archivo de consultas es obligatorio en la práctica.** Cada ejecución lee
  `--conf` antes que nada. Sin él, la ejecución imprime `Error al conectarse ...`
  y `0`, termina con estado `0` y no publica nada, tampoco los módulos de
  rendimiento predeterminados. Para recoger solo los módulos de rendimiento,
  pase un archivo de consultas vacío.
- **La entrega por Tentacle no funciona.** Con `--tentacle_address` la ejecución
  escribe el documento en `--data_dir` y después se detiene con un error no
  controlado antes de enviar nada, de modo que ningún documento llega al
  servidor de Tentacle. Use la carpeta de datos o el modo plugin de agente.
- **Los documentos de la carpeta de datos pueden colisionar.** Los nombres de
  documento tienen resolución de un segundo
  (`<agent_name>.<timestamp>.data`) y se crean de forma exclusiva. Cuando una
  ejecución produce varios documentos para el mismo agente dentro del mismo
  segundo y Pandora FMS todavía no ha recogido el archivo anterior, la escritura
  falla con `ERROR - Could not write file: ... please check directory
  permissions` y se pierden los documentos restantes de la ejecución. Una
  ejecución con los módulos de rendimiento predeterminados produce, con todas las
  métricas disponibles, diecisiete documentos para el agente de métricas, diez
  de ellos con un módulo, así que esto es probable en ese modo. Mantenga un
  documento por ejecución (`--default_metrics 0` y una sola sentencia) o ejecute
  el addon en modo plugin de agente, que no escribe archivos.
- **Cuatro métricas recogidas no se publican.** `total_hit_ratio_percent`,
  `data_hit_ratio_percent`, `index_hit_ratio_percent` y
  `xda_hit_ratio_percent` se leen de la base de datos, pero no se crea ningún
  módulo para ellas.
- **Una sentencia no puede contener dos puntos.** El formato de línea usa los
  dos puntos como separador, así que una sentencia con dos puntos se
  interpreta mal sin avisar.
- **Una línea de consulta mal formada detiene la ejecución con estado `0`.** Una
  línea con menos de tres campos imprime
  `It is mandatory to specify name, query and type!` y termina la ejecución,
  incluidas las sentencias que aún no se habían lanzado.
- **Una consulta fallida de los módulos de rendimiento detiene esa fase.** Si el
  usuario no puede leer una de las tres vistas, la fase termina con un error no
  controlado después de que los módulos de consulta ya se hayan entregado.
  Desactive las métricas con `--default_metrics 0` o conceda las lecturas.
- **El resumen de uso muestra un comando que no se ejecuta tal cual.** `-h`
  imprime la ejecución manual como `./pandora_db2`, pero el script distribuido no
  es ejecutable por sí mismo: invóquelo con `python3 pandora_db2.py`.

### Diagnóstico

| Síntoma | Causa y acción |
| --- | --- |
| `no connection:` seguido del error del driver, estado `1` | La conexión falló. Compruebe el host, el puerto, el nombre de la base de datos, el usuario y la contraseña, y la ruta de red hasta el listener de Db2 |
| `Error al conectarse ...` y después `0`, estado `0` | No se pudo abrir el archivo de consultas. Compruebe `--conf`, su ruta y sus permisos de lectura |
| `It is mandatory to specify name, query and type!` | Una línea del archivo de consultas tiene menos de tres campos separados por dos puntos |
| `error with the query:<statement>.<error>` en la salida de error estándar | La base de datos rechazó esa sentencia. Las líneas siguientes se siguen procesando |
| `ERROR - Could not write file: ...` | La carpeta de datos no permite escritura, o ya existe un documento con el mismo nombre (consulte [Limitaciones conocidas](#limitaciones-conocidas)) |
| No se imprime nada y no se escribe ningún archivo | `--as_agent_plugin 1` imprime los módulos y no escribe nada; sin esa opción el addon escribe en `--data_dir` e imprime `1` por documento |
| Falta un módulo de rendimiento | La base de datos no devolvió valor para esa métrica, o la fase de métricas falló (consulte [Limitaciones conocidas](#limitaciones-conocidas)) |

## Referencia

### Opciones de línea de comandos

| Opción | Obligatoria | Valor por defecto | Descripción |
| --- | --- | --- | --- |
| `--hostname` | Sí | — | Nombre o dirección IP del host Db2 |
| `--port` | No | `50000` | Puerto del listener de Db2 |
| `--protocol` | No | `TCPIP` | Protocolo usado en la cadena de conexión |
| `--database` | Sí | — | Nombre de la base de datos en el servidor Db2 |
| `--uid` | Sí | — | Usuario que ejecuta las sentencias |
| `--password` | Sí | — | Contraseña de ese usuario |
| `--conf` | Sí | — | Archivo de consultas. El addon lo lee en cada ejecución, antes de los módulos de rendimiento predeterminados |
| `--default_metrics` | No | `1` | `1` publica los módulos de rendimiento predeterminados; cualquier otro valor los desactiva |
| `--agent_name` | No | `DB2` | Nombre del agente de consulta; el agente de métricas es `<agent_name>_metrics` |
| `-g`, `--group` | No | `db2` | Grupo escrito en los datos de agente de ambos agentes |
| `--data_dir` | No | `/var/spool/pandora/data_in/` | Carpeta de los documentos de datos de agente en el modo de carpeta de datos |
| `--as_agent_plugin` | No | `0` | `1` imprime los módulos en la salida estándar; cualquier otro valor escribe documentos en `--data_dir` |
| `--tentacle_address` | No | — | Dirección del servidor de Tentacle. Tiene prioridad sobre `--as_agent_plugin`, y la entrega no funciona en la versión `1.0` |
| `--tentacle_port` | No | `41121` | Puerto del servidor de Tentacle |
| `-h`, `--help` | No | — | Imprime el resumen de uso y termina |

### Archivo de consultas

| Campo | Obligatorio | Descripción |
| --- | --- | --- |
| `name` | Sí | Nombre del módulo |
| `statement` | Sí | Sentencia ejecutada contra la base de datos conectada. No puede contener dos puntos |
| `module_type` | Sí | Tipo de módulo de Pandora FMS, escrito tal cual en el módulo |
| `description` | No | Descripción del módulo |

El campo `_database_` de una sentencia se sustituye por el nombre de la base de
datos conectada entre comillas simples.

### Módulos generados

| Agente | Módulo | Tipo | Unidad | Origen |
| --- | --- | --- | --- | --- |
| Consulta | Según el archivo de consultas | Según el archivo de consultas | — | Un módulo por sentencia |
| Métricas | `no_of_bufferpools_<DB_NAME>` | `generic_data` | `count` | Número de buffer pools definidos en la base de datos |
| Métricas | `total_logical_reads_<DB_NAME>` | `generic_data` | `count` | Suma de las lecturas lógicas totales informadas por los buffer pools |
| Métricas | `total_physical_reads_<DB_NAME>` | `generic_data` | `count` | Suma de las lecturas físicas totales informadas por los buffer pools |
| Métricas | `data_logical_reads_<DB_NAME>` | `generic_data` | `count` | Suma de las lecturas lógicas de datos |
| Métricas | `data_physical_reads_<DB_NAME>` | `generic_data` | `count` | Suma de las lecturas físicas de datos |
| Métricas | `index_logical_reads_<DB_NAME>` | `generic_data` | `count` | Suma de las lecturas lógicas de índices |
| Métricas | `xda_logical_reads_<DB_NAME>` | `generic_data` | `count` | Suma de las lecturas lógicas XDA |
| Métricas | `log_utilization_percent_<DB_NAME>` | `generic_data` | `%` | Utilización media del log de transacciones |
| Métricas | `total_log_used_kb_<DB_NAME>` | `generic_data` | `KB` | Espacio total del log de transacciones en uso |
| Métricas | `total_log_available_kb_<DB_NAME>` | `generic_data` | `KB` | Espacio total disponible del log de transacciones |

### Estado de salida

| Estado | Significado |
| --- | --- |
| `0` | Ejecución correcta. También se usa cuando no se puede abrir el archivo de consultas o una línea de este está mal formada |
| `1` | Falló la conexión, falló una consulta de los módulos de rendimiento o no se pudo escribir un documento |
| `2` | Una opción recibió un valor de tipo incorrecto, por ejemplo un `--as_agent_plugin` que no es entero |

### Identidad del addon

| Propiedad | Valor |
| --- | --- |
| Identificador en el Marketplace | `pandorafms.db2_remote` |
| Nombre | DB2 Remote |
| Versión | `1.0` |
| Categoría | Miscelaneus |
| Licencia | One |
| Última actualización en el Marketplace | 2025-06-25 |
| Disponibilidad | Descarga limitada a usuarios con licencia |
| Mantenimiento | La entrada del Marketplace indica que el addon ya no se mantiene ni se actualiza activamente |
