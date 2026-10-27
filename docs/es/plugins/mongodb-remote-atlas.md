# Plugin Pandora MongoDB remote / Atlas

*Última actualización del artículo: 2026-10-26.*

## Qué hace

El addon `pandorafms.mongodb_remote_atlas` monitoriza bases de datos MongoDB
desde Pandora FMS a través de la red. Cada ejecución se conecta a un despliegue
de MongoDB con una cadena de conexión estándar de MongoDB y convierte el
resultado en agentes y módulos de Pandora FMS: contadores de tamaño y de
objetos de la base de datos, estadísticas de cada colección y, cuando se
habilita, los contadores de conexiones, red, operaciones y latencias del
servidor.

Un despliegue alojado en MongoDB Atlas se monitoriza de la misma forma, con la
cadena de conexión `mongodb+srv://` que proporciona Atlas. No se instala nada en
el host de la base de datos y no se usa ninguna clave de API de Atlas: la cadena
de conexión es la única entrada.

El addon admite dos modelos de ejecución:

- **Modo plugin de servidor** (por defecto): cada ejecución escribe un archivo
  XML `agent_data` en el directorio de datos de Pandora FMS y el servidor de
  Pandora FMS lo ingiere.
- **Modo plugin de agente** (`--as_agent_plugin 1`): cada ejecución imprime los
  módulos generados como XML en la salida estándar, para que los ingiera el
  agente de Pandora FMS. Este modo recopila una sola base de datos.

El addon no guarda estado entre ejecuciones: cada ejecución lee las métricas en
ese momento.

Esta página documenta el plugin de monitorización remota. El addon MongoDB
Discovery ([MongoDB Discovery](../discovery/mongodb-discovery.md)) es un
producto distinto: ejecuta tareas de Discovery y crea sus agentes a partir de
ellas, mientras que este plugin crea sus agentes a partir de sus propias
ejecuciones.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
|--------|--------|-----------|
| Acceso de red desde el host que ejecuta el plugin al listener de MongoDB | `Requerido` | El addon se conecta por red; no se instala nada en el host de la base de datos |
| Un usuario de MongoDB autorizado a ejecutar `dbStats` y `collStats` en las bases de datos monitorizadas | `Requerido` | Prerrequisito de los módulos de base de datos y de colección, no una declaración de compatibilidad |
| Un usuario de MongoDB con el rol `clusterMonitor` cuando se habilita el grupo de estado del servidor | `Requerido` | Prerrequisito del comando `serverStatus`, no una declaración de compatibilidad |
| Versiones de servidor MongoDB | `Sin validar` | Ningún registro de pruebas establece compatibilidad con una versión concreta de MongoDB |
| Niveles de clúster de MongoDB Atlas | `Sin validar` | Ningún registro de pruebas establece compatibilidad con un nivel concreto de Atlas |
| Versiones de Pandora FMS | `Sin validar` | Ningún registro de pruebas establece compatibilidad con una versión concreta de consola o servidor |
| Sistema operativo del host que ejecuta el plugin | `Sin validar` | Ningún registro de pruebas establece compatibilidad de sistema operativo |

### Requisitos

1. **Un despliegue de MongoDB** — un servidor autogestionado, un conjunto de
   réplicas, un clúster fragmentado o un clúster de Atlas — accesible desde el
   host que ejecuta el plugin.
2. **Un usuario de MongoDB** con los roles descritos en
   [Acceso a MongoDB](#acceso-a-mongodb).
3. **Python 3 y las dependencias del addon** en el host que ejecuta el plugin.
   El addon incluye un archivo `requirements.txt`; instálelo con
   `pip3 install -r requirements.txt` desde el directorio del addon. El
   controlador de MongoDB que enumera es necesario en todos los casos, y la
   biblioteca DNS que enumera es la que resuelve la lista de semillas de una
   URI `mongodb+srv://`.
4. **Pandora FMS**: el servidor de plugins, cuando el addon se ejecuta en modo
   plugin de servidor, o un agente de Pandora FMS, cuando se ejecuta en modo
   plugin de agente.

### Acceso a MongoDB

El addon no utiliza ninguna interfaz de administración de Atlas, de modo que un
despliegue de Atlas se autoriza como cualquier otro despliegue de MongoDB:

- **Monitorizar las bases de datos** requiere las acciones `dbStats` y
  `collStats` en cada base de datos monitorizada. El rol integrado `read` de
  MongoDB incluye ambas.
- **Recopilar todas las bases de datos** (`-a 1`) además enumera las bases de
  datos del despliegue, lo que requiere la acción `listDatabases`. Los roles
  integrados `readAnyDatabase` y `clusterMonitor` la incluyen.
- **El grupo de estado del servidor** (`-s`) lee el comando `serverStatus`, que
  requiere el rol `clusterMonitor`. En Atlas, `clusterMonitor` es un rol
  integrado que se puede asignar al usuario de base de datos.

Ninguna fuente oficial identifica un conjunto de privilegios más restringido
que estas acciones; otorgue solo lo que necesiten las opciones que habilite.

Para Atlas, añada también la dirección del host que ejecuta el plugin a la lista
de acceso del despliegue y utilice la cadena de conexión que la interfaz de
Atlas devuelve para el clúster.

### Instalar el addon

Descargue el paquete del addon desde su entrada de Marketplace, que está
limitada a usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.mongodb_remote_atlas](https://marketplace.pandorafms.com/entries/pandorafms.mongodb_remote_atlas)

Regístrelo en la consola como plugin de servidor, o copie el script del addon y
su `requirements.txt` al host que lo vaya a ejecutar y registre el plugin a
mano. En ambos casos el plugin lo ejecuta el servidor de plugins de Pandora FMS,
en el servidor que seleccione para cada módulo. El comando del plugin es la ruta
al script del addon en ese servidor; los parámetros son las opciones documentadas
en [Línea de comandos](#linea-de-comandos) y en [Registrar el plugin en la consola](#registrar-el-plugin-en-la-consola).

La entrada de Marketplace indica que este addon ya no se mantiene ni se
actualiza activamente.

Los comandos de esta página usan `pandora_mongodb` como nombre del script, que
es como lo registra la consola. Si la copia de su servidor conserva la extensión
`.py`, use ese nombre en los comandos.

## Configuración

### Modelos de ejecución

El modo plugin de servidor es el predeterminado: el addon escribe un archivo XML
por agente en el directorio de datos de Pandora FMS y el servidor los ingiere.
Se selecciona omitiendo `--as_agent_plugin` o dándole un valor distinto de `1`.

El modo plugin de agente requiere `--as_agent_plugin 1` y una sola base de datos
en `-d`. En este modo el addon imprime los módulos de la ejecución como bloques
`<module>` en la salida estándar, sin envoltorio `agent_data`, y no escribe
ningún archivo. El agente que ejecuta el plugin es el propietario de los
módulos, por lo que el nombre de agente, el grupo y el prefijo no tienen efecto
en este modo.

### Recopilar una base de datos o todas

Se debe seleccionar exactamente uno de los dos ámbitos de recopilación, y el
addon termina sin recopilar nada cuando no hay ninguno:

| Ámbito | Opción | Agentes creados |
|--------|--------|-----------------|
| Una sola base de datos | `-d appdb` | Un agente por ejecución |
| Todas las bases de datos que el usuario pueda enumerar | `-a 1` | Un agente por base de datos |

Cuando se dan ambas opciones, `-a 1` prevalece y `-d` se ignora. El modo de
todas las bases de datos omite todas aquellas cuyo nombre contenga `local` y
procesa cualquier otra que el usuario pueda enumerar, incluidas `admin` y
`config` cuando el usuario pueda verlas.

### Modo plugin de servidor

Este es el comando mínimo para una base de datos, escribiendo el archivo del
agente en el directorio de datos predeterminado:

```bash
./pandora_mongodb -u '<MONGODB_URI>' -d appdb
```

Añada el grupo, el prefijo de agente y las estadísticas de todas las colecciones
de esa base de datos:

```bash
./pandora_mongodb -u '<MONGODB_URI>' -d appdb \
    -c 1 -p atlas_ -g mongodb --data_dir /var/spool/pandora/data_in
```

Recopile todas las bases de datos, con los contadores de estado del servidor:

```bash
./pandora_mongodb -u '<MONGODB_URI>' -a 1 -s 1 -p atlas_
```

`appdb` es un nombre de base de datos de ejemplo. `<MONGODB_URI>` es la cadena
de conexión completa: para un despliegue autogestionado, la forma `mongodb://`
con el host, el puerto, el usuario y la contraseña, y para Atlas, la cadena
`mongodb+srv://` que devuelve la interfaz de Atlas. Las opciones de conexión,
como la base de datos de autenticación, el nombre de un conjunto de réplicas,
TLS y un archivo de CA, forman parte de la URI; el addon no tiene una opción
aparte para ellas y pasa la cadena al controlador de MongoDB sin modificarla.

El prefijo se antepone al nombre de cada agente que crea la ejecución; no cambia
los nombres de los módulos. Utilice el nombre de un grupo existente en la
consola: el addon escribe el nombre de grupo que recibe y no crea grupos. El
usuario que ejecuta el addon debe poder escribir en `--data_dir`.

### Modo plugin de agente

```bash
./pandora_mongodb -u '<MONGODB_URI>' -d appdb -c 1 --as_agent_plugin 1
```

Los módulos de la ejecución se imprimen en la salida estándar. Este modo admite
una sola base de datos: con `-a 1` el addon escribe los archivos de agente como
de costumbre y la opción no tiene efecto.

### Registrar el plugin en la consola

Abra **Servers → Plugins → Register Plugin**, o suba el paquete del addon, que
registra el plugin con su comando y su cadena de parámetros. La cadena de
parámetros contiene una macro por opción:

```text
-u _field1_ -s _field2_ -d _field3_ -a _field4_ -p _field5_ -c _field6_ -g _field7_ --data_dir _field8_ --as_agent_plugin _field9_
```

![Comando y cadena de parámetros del plugin MongoDB remote](../assets/images/plugins/mongodb-remote-atlas/plugin-command-and-parameters.png)

Cada macro se rellena cuando el plugin se usa en un módulo:

| Campo | Descripción | Valor de ejemplo |
|-------|-------------|------------------|
| `_field1_` | URI de conexión, con las credenciales incluidas. Active **Hide value** | `<MONGODB_URI>` |
| `_field2_` | Grupo de estado del servidor | `1` |
| `_field3_` | Base de datos a monitorizar | `appdb` |
| `_field4_` | Todas las bases de datos | `1` |
| `_field5_` | Prefijo del nombre de agente | `atlas_` |
| `_field6_` | Estadísticas de colecciones | `1` |
| `_field7_` | Grupo de destino | `mongodb` |
| `_field8_` | Directorio de datos de Pandora FMS | `/var/spool/pandora/data_in` |
| `_field9_` | `1` para el modo plugin de agente, `0` para el modo plugin de servidor | `0` |

Esa cadena funciona tal cual solo cuando todas las macros tienen valor: una
opción cuya macro se deja vacía queda seguida de la opción siguiente en lugar de
un valor, y el addon termina con `error: argument -X/--X: expected one
argument`. Tampoco puede expresar una ejecución de una sola base de datos,
porque `-a` no tiene ningún valor que la deshabilite. Edite la cadena de
parámetros según la ejecución que necesite:

| Ejecución | Cadena de parámetros |
|-----------|----------------------|
| Una base de datos | `-u _field1_ -d _field2_ -p _field3_ -g _field4_ --data_dir _field5_` |
| Una base de datos, con estadísticas de colecciones | `-u _field1_ -d _field2_ -c _field3_ -p _field4_ -g _field5_ --data_dir _field6_` |
| Todas las bases de datos | `-u _field1_ -a 1 -p _field2_ -g _field3_ --data_dir _field4_` |
| Modo plugin de agente | `-u _field1_ -d _field2_ -p _field3_ -g _field4_ --as_agent_plugin 1` |

Omita una opción para deshabilitarla: `-s 0` sigue habilitando el grupo de
estado del servidor y `-c 0` sigue habilitando las estadísticas de colecciones.

Después, el plugin está disponible al crear módulos de plugin y cada módulo
rellena las macros individualmente. El módulo se ejecuta en el servidor de
Pandora FMS seleccionado para él, de modo que un plugin registrado sirve para
varios despliegues.

### Credenciales y transporte

- La cadena de conexión transporta el usuario y la contraseña de la base de
  datos. El addon solo la acepta como argumento de línea de comandos, de modo
  que es visible en la lista de procesos del host mientras dura la ejecución y
  permanece en el historial del shell cuando se escribe. Consérvela en un campo
  de módulo con **Hide value** activado, restrinja quién puede leer la
  configuración de módulos en la consola y evite pasarla en un shell compartido.
- Una conexión `mongodb://` sin TLS envía las credenciales y las métricas
  recopiladas sin cifrar. Utilice las opciones `tls` de la URI, que el addon
  pasa al controlador, o restrinja el despliegue a una red de confianza.
- El addon no almacena credenciales propias: no tiene archivo de configuración y
  no guarda estado entre ejecuciones.

## Verificación

Ejecute el addon desde un terminal en el host que lo vaya a ejecutar, con las
mismas opciones que usará el plugin:

```bash
./pandora_mongodb -u '<MONGODB_URI>' -d appdb
```

Una ejecución correcta de una sola base de datos imprime `1` y después el número
de agentes creados, así que una ejecución sin el grupo de estado del servidor
imprime `1` dos veces, y escribe un archivo por agente en el directorio de datos:

```text
/var/spool/pandora/data_in/mongo_appdb.1761483000.data
```

Una ejecución de todas las bases de datos imprime el número de agentes creados:
uno por base de datos, más uno cuando el grupo de estado del servidor está
habilitado.

```bash
./pandora_mongodb -u '<MONGODB_URI>' -a 1 -p atlas_
```

En modo plugin de agente, una ejecución correcta imprime un bloque `<module>` por
cada módulo generado. Este es un extracto de una ejecución sobre una base de
datos con estadísticas de colecciones:

```xml
<module>
	<name><![CDATA[collections]]></name>
	<type>generic_data</type>
	<data><![CDATA[12]]></data>
	<description><![CDATA[database collections]]></description>
	<unit><![CDATA[]]></unit>
</module>
<module>
	<name><![CDATA[dataSize]]></name>
	<type>generic_data</type>
	<data><![CDATA[5242880]]></data>
	<description><![CDATA[database dataSize]]></description>
	<unit><![CDATA[b]]></unit>
</module>
<module>
	<name><![CDATA[size appdb.orders]]></name>
	<type>generic_data</type>
	<data><![CDATA[1048576]]></data>
	<description><![CDATA[size of appdb.orders]]></description>
	<unit><![CDATA[b]]></unit>
</module>
<module>
	<name><![CDATA[status]]></name>
	<type>generic_data</type>
	<data><![CDATA[1]]></data>
	<description><![CDATA[database status]]></description>
	<unit><![CDATA[]]></unit>
</module>
```

En la consola, el agente aparece con el nombre `<prefijo><base de datos>` y sus
módulos después de que el servidor haya procesado el archivo de datos. El
inventario de agentes y módulos se describe en
[Entender los resultados](#entender-los-resultados).

## Entender los resultados

### Agentes creados

| Propiedad | Valor |
|-----------|-------|
| Nombre y alias del agente | El prefijo de `-p` seguido del nombre de la base de datos, por ejemplo `mongo_appdb` |
| Descripción | `database stats` para un agente de base de datos, `server status stats` para el agente de estado del servidor |
| Grupo | El valor de `-g`, `mongodb` por defecto |
| Dirección | `127.0.0.1` |
| Sistema operativo y versión | Vacíos: el addon no los informa |
| Intervalo | Vacío: se aplica el valor predeterminado de la consola |
| Marca de tiempo | La hora local de la ejecución |

El número de agentes depende del ámbito de recopilación y del grupo de estado del
servidor:

| Ejecución | Agentes |
|-----------|---------|
| `-d` | Un agente, con el nombre de la base de datos |
| `-d -s` | Dos agentes: el agente de base de datos, que además contiene los módulos de estado del servidor, y un segundo agente llamado `<prefijo><host>`, con los `:` del host sustituidos por `.` |
| `-a 1` | Un agente por base de datos, con el nombre de la base de datos |
| `-a 1 -s` | Los agentes de base de datos, más un agente aparte llamado `<prefijo><host>` con los módulos de estado del servidor |

Por tanto, los módulos de estado del servidor forman parte del agente de base de
datos solo en una ejecución de una sola base de datos.

### Grupos de módulos

- **Grupo de base de datos.** Se recopila siempre para todos los agentes de la
  ejecución. Informa de los contadores y tamaños de la base de datos y termina
  con `status`, que lleva el valor `ok` del comando de estadísticas.
- **Grupo de colecciones.** Se recopila cuando `-c` está presente. Cada colección
  de la base de datos aporta un módulo por estadística, con el nombre del espacio
  de nombres `<base de datos>.<colección>`.
- **Grupo de estado del servidor.** Se recopila cuando `-s` está presente.
  Informa de los contadores `connections`, `network`, `opcounters` y
  `opLatencies` del servidor MongoDB como un módulo por clave devuelta por el
  despliegue.

Todos los módulos de los grupos de base de datos y de colecciones se crean solo
cuando el despliegue informa del campo correspondiente, por lo que la lista que
recibe un agente depende de su versión de servidor y de su motor de
almacenamiento. Los contadores del grupo de estado del servidor siguen las claves
presentes en la salida de `serverStatus` de ese despliegue.

El inventario completo está en [Módulos generados](#modulos-generados).

## Operar y resolver problemas

### Programación y ejecución manual

- El addon no tiene modo demonio ni planificador interno: se ejecuta una vez y
  termina. Cuando se registra como plugin de servidor, Pandora FMS lo ejecuta con
  el intervalo del módulo; fuera de Pandora FMS, planifíquelo con `cron`.
- Cada ejecución abre su propia conexión y la cierra al terminar, así que el
  addon se puede ejecutar manualmente en cualquier momento sin alterar el
  despliegue.
- Una ejecución que recopila todas las bases de datos de un despliegue grande lee
  las estadísticas de cada colección y de cada base de datos en un solo proceso.
  Mantenga deshabilitado el grupo de colecciones, o reduzca el ámbito a bases de
  datos individuales, cuando la ejecución no termine dentro del tiempo de espera
  del módulo.

### Limitaciones conocidas

- **Los grupos opcionales no se pueden deshabilitar con un valor.** `-s 0` y
  `-c 0` siguen habilitando los grupos de estado del servidor y de colecciones,
  porque el addon solo comprueba si la opción se ha indicado. Omita la opción
  para deshabilitar el grupo.
- **`-a` admite un único valor de habilitación.** Utilice `-a 1`. Cualquier otro
  valor deja los dos ámbitos de recopilación deshabilitados y la ejecución
  termina con un error.
- **El addon necesita `-d` o `-a 1`.** Sin ninguna de las dos, imprime una traza
  `NameError` de Python en lugar de un mensaje de uso.
- **El modo plugin de agente ignora `-a`.** Con `-a 1` los archivos de agente se
  escriben aunque esté presente `--as_agent_plugin 1`; la opción solo funciona
  con `-d`.
- **El prefijo se aplica solo a los nombres de agente**, no a los nombres de
  módulo.
- **`avgObjSize` por colección se recopila solo en el modo de una sola base de
  datos.** Una ejecución de todas las bases de datos lo omite del grupo de
  colecciones.
- **Las estadísticas de colecciones no tienen filtro de colecciones.** Se lee
  cada colección de la base de datos.
- **No hay opción de tiempo de espera, reintento ni depuración.** El tiempo de
  espera del servidor de plugins se aplica a toda la ejecución, y el diagnóstico
  se limita al error impreso.

### Diagnóstico

- **`Error: <mensaje>` seguido del estado de salida 1** — la ejecución se
  detuvo. El mensaje es la excepción devuelta por el controlador de MongoDB o por
  el comando de estadísticas. Ante un fallo de conexión o de autenticación,
  revise la URI, las credenciales que transporta, el camino de red y, en Atlas,
  la lista de acceso del despliegue.
- **`Error: not authorized on <base de datos> to execute command ...`** — el
  usuario no puede ejecutar `dbStats` o `collStats` en esa base de datos. Otorgue
  las acciones descritas en [Acceso a MongoDB](#acceso-a-mongodb).
- **`error: argument -s/--server_status: expected one argument`** (estado de
  salida 2) — una opción de la línea de comandos o de la cadena de parámetros de
  la consola está seguida de otra opción en lugar de un valor. Déle un valor o
  elimine la opción.
- **`NameError: name 'count' is not defined`** — no se indicó `-d` ni un `-a 1`
  válido, o `-a` recibió un valor distinto de `1`.
- **`NameError: name 'db' is not defined`** — se habilitó el grupo de estado del
  servidor en una ejecución que no recopiló ninguna base de datos.
- **`KeyError: 'freeStorageSize'`, `KeyError: 'scaleFactor'` u otro `KeyError`**
  — el despliegue no informa de ese campo en las estadísticas de la colección, así
  que el grupo de colecciones no se puede construir. Deshabilite `-c` para ese
  despliegue.
- **`KeyError: 'opLatencies'` u otro `KeyError` en el grupo de estado del
  servidor** — la salida de `serverStatus` del despliegue no incluye esa sección.
  Deshabilite `-s`.
- **`Error: [Errno 13] Permission denied`** — el usuario que ejecuta el addon no
  puede escribir en `--data_dir`. Corrija los permisos o apunte la opción a un
  directorio con permisos de escritura.
- **`Error: [Errno 17] File exists`** — ya existe un archivo de datos para el
  mismo agente y el mismo segundo. Repita la ejecución.
- **El agente aparece con menos módulos de los esperados** — el despliegue no
  informa de esos campos. Compare el agente con las condiciones de
  [Módulos generados](#modulos-generados).
- **No aparece ningún agente en la consola** — compruebe que el directorio de
  datos de la ejecución es el que lee el servidor de Pandora FMS, que el archivo
  se creó y que el grupo de `-g` existe en la consola.

## Referencia

### Línea de comandos

```text
./pandora_mongodb -u <MONGODB_URI> [opciones]
```

| Nombre | Obligatorio | Predeterminado | Descripción |
|--------|-------------|----------------|-------------|
| `-u`, `--uri` | Sí | — | Cadena de conexión de MongoDB. Transporta los hosts, las credenciales y las opciones de conexión, incluidas las de TLS |
| `-d`, `--database` | Uno de `-d` o `-a 1` | — | Base de datos a monitorizar |
| `-a`, `--alldatabases` | Uno de `-d` o `-a 1` | `0` | `1` monitoriza todas las bases de datos que el usuario pueda enumerar, excepto aquellas cuyo nombre contenga `local` |
| `-s`, `--server_status` | No | Deshabilitado | Cualquier valor, incluido `0`, habilita el grupo de estado del servidor. Omita la opción para deshabilitarlo |
| `-c`, `--collectionstats` | No | Deshabilitado | Cualquier valor, incluido `0`, habilita las estadísticas de colecciones. Omita la opción para deshabilitarlas |
| `-p`, `--prefix` | No | `mongo_` | Prefijo del nombre de cada agente que crea la ejecución |
| `-g`, `--group` | No | `mongodb` | Grupo del agente en la consola; el addon no crea grupos |
| `--data_dir` | No | `/var/spool/pandora/data_in/` | Directorio donde se escriben los archivos de agente en el modo plugin de servidor |
| `--as_agent_plugin` | No | `0` | `1` imprime los módulos en la salida estándar en lugar de escribir archivos de agente. Solo con `-d` |
| `--as_discovery_plugin` | No | `0` | `1` sustituye el recuento final por un resumen JSON de los agentes creados. No cambia lo que se recopila ni lo que se escribe |

`-h` y `--help` imprimen la lista de opciones. La cabecera de ayuda informa de la
versión del plugin como `250821`.

### Salida del comando

| Ejecución | Salida estándar |
|-----------|-----------------|
| `-d`, modo plugin de servidor | `1`, y el número de agentes creados en la línea siguiente |
| `-a 1`, modo plugin de servidor | El número de agentes creados: uno por base de datos, más uno cuando el grupo de estado del servidor está habilitado |
| `-d --as_agent_plugin 1` | Un bloque `<module>` por módulo y después el número de agentes creados |
| Cualquier ejecución con `--as_discovery_plugin 1` | Un resumen JSON con `Agents (databases) created by the plugin` y la lista de bases de datos, en lugar del recuento final |

### Módulos generados

#### Módulos de base de datos

Se recopilan para todos los agentes de la ejecución. La columna **Campo** es el
campo de la salida de `dbStats` que lee cada módulo; el módulo se crea solo
cuando el despliegue lo devuelve.

| Módulo | Tipo | Campo | Unidad |
|--------|------|-------|--------|
| `collections` | `generic_data` | `collections` | — |
| `views` | `generic_data` | `views` | — |
| `objects` | `generic_data` | `objects` | — |
| `avgObjSize` | `generic_data` | `avgObjSize` | `b` |
| `dataSize` | `generic_data` | `dataSize` | `b` |
| `storageSize` | `generic_data` | `storageSize` | `b` |
| `totalFreeStorageSize` | `generic_data` | `totalFreeStorageSize` | `b` |
| `numExtents` | `generic_data` | `numExtents` | — |
| `indexes` | `generic_data` | `indexes` | — |
| `indexSize` | `generic_data` | `indexSize` | — |
| `fileSize` | `generic_data` | `fileSize` | `b` |
| `nsSizeMB` | `generic_data` | `nsSizeMB` | `mb` |
| `status` | `generic_data` | `ok` | — |

#### Módulos de colección

Se recopilan cuando `-c` está presente, un conjunto por colección. `<ns>` es el
espacio de nombres de la colección, por ejemplo `appdb.orders`.

| Módulo | Tipo | Campo | Unidad |
|--------|------|-------|--------|
| `size <ns>` | `generic_data` | `size` | `b` |
| `count <ns>` | `generic_data` | `count` | `b` |
| `avgObjSize <ns>` | `generic_data` | `avgObjSize` | `b` |
| `storageSize <ns>` | `generic_data` | `storageSize` | `b` |
| `freeStorageSize <ns>` | `generic_data` | `freeStorageSize` | `b` |
| `capped<ns>` | `generic_data` | `capped`, como `1` o `0` | — |
| `nindexes <ns>` | `generic_data` | `nindexes` | — |
| `totalIndexSize <ns>` | `generic_data` | `totalIndexSize` | — |
| `totalSize <ns>` | `generic_data` | `totalSize` | `b` |
| `scaleFactor <ns>` | `generic_data` | `scaleFactor` | — |
| `status <ns>` | `generic_data` | `ok` | — |

`avgObjSize <ns>` se genera solo en el modo de una sola base de datos, y
`capped<ns>` no tiene espacio entre el nombre y el espacio de nombres.

#### Módulos de estado del servidor

Se recopilan cuando `-s` está presente, un módulo por clave devuelta por el
despliegue. Todos son `generic_data` sin unidad.

| Módulo | Sección de `serverStatus` |
|--------|---------------------------|
| `server_status.connections <key>` | `connections` |
| `server_status.network <key>` | `network` |
| `server_status.operations <key>` | `opcounters` |
| `server_status.opetationlatencies.reads <key>` | `opLatencies.reads` |
| `server_status.opetationlatencies.writes <key>` | `opLatencies.writes` |
| `server_status.opetationlatencies.commands <key>` | `opLatencies.commands` |

El segmento `opetationlatencies` del nombre se escribe así en los nombres de
módulo que genera el addon.

### Archivos de salida

En el modo plugin de servidor el addon escribe un archivo por agente:

```text
<data_dir>/<nombre_de_agente>.<epoch>.data
```

El archivo contiene un documento `agent_data` con los atributos de
[Agentes creados](#agentes-creados) y un bloque `<module>` por módulo. El addon
crea el archivo en exclusiva, de modo que una segunda ejecución para el mismo
agente dentro del mismo segundo falla en lugar de sobrescribir el primer
archivo.

### Identidad del addon

| Propiedad | Valor |
|-----------|-------|
| Identificador de Marketplace | `pandorafms.mongodb_remote_atlas` |
| Nombre | Pandora MongoDB remote/ Atlas |
| Versión | `1.0` |
| Versión informada por la ayuda del plugin | `250821` |
| Licencia | One |
| Disponibilidad | Descarga limitada a usuarios con licencia |
| Última actualización en Marketplace | 2025-07-01 |
| Mantenimiento | La entrada de Marketplace indica que el addon ya no se mantiene ni se actualiza activamente |
