# MarkLogic monitoring plugin

*Última actualización del artículo: 2026-10-26.*

## Qué hace

El plugin monitoriza una instalación de MarkLogic desde Pandora FMS. En cada
ejecución lee la API REST de gestión de MarkLogic, obtiene el inventario de la
instalación —hosts, bases de datos, bosques y servidores de aplicaciones— y crea un
agente de Pandora FMS por cada entidad, con los módulos que describen su estado, su
carga y su replicación.

No se instala nada en los nodos de MarkLogic: el plugin se ejecuta en un host,
conecta por HTTP o HTTPS y entrega a Pandora FMS los agentes generados. Cada
ejecución vuelve a leer el inventario completo, de modo que el plugin no conserva
estado entre ejecuciones y los agentes reflejan siempre la instalación en el momento
de la ejecución.

Tres grupos de ajustes definen una ejecución:

- **Qué se recopila.** Cada tipo de entidad (hosts, bases de datos, bosques y
  servidores de aplicaciones) se habilita o deshabilita por separado, se pueden
  excluir entidades concretas por su nombre y cada tipo genera un conjunto resumido
  de módulos o un conjunto detallado.
- **Cómo se identifica.** Un prefijo común da nombre a todos los agentes generados,
  que se crean en un grupo y con un intervalo configurados.
- **Dónde se entrega.** Los documentos de agente generados viajan con Tentacle o se
  copian en una carpeta de datos local de Pandora FMS.

Los agentes de entidad se entregan siempre así. El ajuste `as_agent_plugin` solo
selecciona qué imprime el plugin en la salida estándar: activado, imprime un módulo
`Plugin message` para que lo recoja un agente de Pandora FMS; desactivado, imprime el
resultado de la ejecución como un número, para un módulo de plugin de servidor o una
tarea programada.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| API REST de gestión de MarkLogic accesible en el host y el puerto configurados | `Required` | Toda la recopilación lee `/manage/<api-version>/...` con `format=json` desde ese host y ese puerto |
| Un valor de `ml_api_version` que la instalación acepte: `V1`, `V2` o `LATEST` | `Required` | El valor es un segmento de ruta de todas las peticiones; el archivo de configuración distribuido documenta esos tres valores |
| Un usuario de MarkLogic con permiso para leer la API de gestión | `Required` | El plugin se autentica con `ml_user`, `ml_pass` y `ml_realm` |
| Un entorno de ejecución de Perl con `LWP::UserAgent`, `JSON`, `IO::Socket::INET6` y `PerlIO::encoding` | `Required` | El plugin no arranca sin ellos |
| Acceso de red desde el host del plugin a `ml_server:ml_port` | `Required` | El plugin conecta con la API de gestión desde ese host |
| Acceso de red desde el host del plugin al puerto de cada servidor de aplicaciones, cuando la comprobación de puertos está activada | `Required` | La comprobación de puertos abre una conexión TCP por cada servidor de aplicaciones |
| Acceso de red al puerto de Tentacle de Pandora FMS, `41121` por defecto, cuando se entrega con Tentacle | `Required` | La entrega con Tentacle es el modo por defecto |
| Versión del servidor MarkLogic | `Not validated` | No se ha registrado una matriz de versiones de MarkLogic para este addon; el archivo distribuido documenta `LATEST` como la versión de API de MarkLogic 8 |
| Sistema operativo del host que ejecuta el plugin | `Not validated` | No se ha registrado un sistema operativo para esta versión |
| Pandora FMS NG 784 y posteriores | `Supported` | El Marketplace indica que todas sus entradas son compatibles con Pandora FMS NG 784 y versiones posteriores; es una declaración del catálogo que cubre este addon, no un registro de pruebas |

### Requisitos

1. **Una instalación de MarkLogic** cuya API de gestión responda en el host y el
   puerto configurados. El plugin y su archivo de configuración distribuido usan
   `8002`.
2. **Una cuenta de MarkLogic** con permiso para leer la API de gestión en
   `/manage/<api-version>/`.
3. **Un host para ejecutar el plugin** con el entorno de Perl y los módulos indicados
   en [Compatibilidad](#compatibilidad).
4. **Un destino para los agentes generados**: el servicio Tentacle de Pandora FMS o
   una carpeta de datos local que lea el servidor de Pandora FMS.
5. **Opcionalmente**, acceso TCP desde el host del plugin al puerto de cada servidor
   de aplicaciones, solo cuando la comprobación de puertos está activada.

### Instalar el plugin

Descargue el addon desde la entrada del Marketplace de Pandora FMS, cuyo acceso está
limitado a usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.marklogic_monitoring](https://marketplace.pandorafms.com/entries/pandorafms.marklogic_monitoring)

Instálelo en el host que lo vaya a ejecutar y mantenga junto a él el archivo de
configuración `pandora_ml.conf`. El plugin recibe ese archivo como único argumento,
así que cualquier ubicación es válida siempre que la ejecución use la misma ruta.

## Configuración

El plugin recibe un argumento, la ruta de su archivo de configuración, y ninguna
opción de línea de comandos:

```bash
perl /usr/share/pandora_server/util/pandora_marklogic.pl <PATH_TO_CONFIG>
```

El archivo contiene líneas `key = value` y los valores que incluye sustituyen a los
valores por defecto. Se aplican dos reglas de lectura:

- Es un comentario toda línea cuyo primer carácter sea `#`. Una línea que empiece por
  espacios se lee como una clave, así que mantenga los comentarios en la primera
  columna.
- Las claves y los valores se recortan, y el valor conserva cualquier `=` posterior
  al primero. Una clave repetida conserva su último valor; `global_alerts` es la
  excepción, descrita en [Decoración de los módulos](#decoracion-de-los-modulos).

El archivo `pandora_ml.conf` distribuido es una base funcional: activa todos los
tipos de entidad, selecciona el detalle resumido para hosts, bases de datos y
bosques y la información detallada para los servidores de aplicaciones. Parta de él
en lugar de un archivo vacío. Las claves `check_*` y `show_detailed_*` no tienen
valor por defecto: una clave ausente del archivo se comporta como deshabilitada, de
modo que un archivo incompleto no recopila nada y aun así informa de una ejecución
correcta.

### Conexión con MarkLogic

Este bloque es obligatorio; sin él el plugin no tiene ninguna API que leer.

```ini
ml_server = <MARKLOGIC_HOST>
ml_port = 8002
ml_user = <USERNAME>
ml_pass = <PASSWORD>
ml_realm = public
use_ssl = 0
ml_api_version = LATEST
```

- `ml_server` y `ml_port` construyen la URL de todas las peticiones. El plugin usa
  exactamente el puerto indicado: no recurre al puerto por defecto del esquema.
- `use_ssl` cambia el esquema de `http` a `https`. Actívelo cuando la API de gestión
  se sirva por TLS.
- `ml_api_version` se inserta como segmento de ruta, así que `LATEST` lee
  `/manage/LATEST/hosts`, y `V1` o `V2` leen la versión de API correspondiente. Si la
  clave no está, se usa `LATEST`.
- `ml_realm` es el realm de autenticación que se envía con las credenciales. Si el
  servidor responde con un realm distinto, la autenticación falla.

### Entrega a Pandora FMS

Los documentos de agente generados salen del plugin de una de dos formas. Tentacle es
el modo por defecto y necesita la dirección de Tentacle:

```ini
mode = tentacle
tentacle_ip = <PANDORA_FMS_URL>
tentacle_port = 41121
tentacle_opts =
tentacle_client = /usr/bin/tentacle_client
```

La copia local escribe los documentos en una carpeta que lee el servidor de Pandora
FMS, que es la opción habitual cuando el plugin se ejecuta en el propio servidor de
Pandora FMS:

```ini
mode = local
local_folder = /var/spool/pandora/data_in
```

- `mode` usa Tentacle solo cuando su valor es exactamente `tentacle`. Cualquier otro
  valor, incluido uno vacío, copia los documentos en `local_folder`.
- `tentacle_ip` es obligatorio cuando se entrega con Tentacle. `tentacle_client` debe
  indicar un ejecutable: un valor vacío no recurre a `tentacle_client` en el `PATH` y
  la entrega falla.
- `tentacle_opts` pasa opciones adicionales al cliente de Tentacle, separadas por
  espacios.
- `temp` es donde se escribe cada documento antes de entregarlo, `/tmp` por defecto.
- **`temp` y `local_folder` deben existir ambos**, incluso cuando el plugin entrega
  con Tentacle y no copia nada. Una carpeta ausente detiene la ejecución antes de
  recopilar dato alguno.

### Qué se recopila

Cada tipo de entidad se recopila solo cuando su clave está habilitada. El archivo
distribuido habilita los cuatro tipos y la comprobación de puertos:

```ini
check_hosts = 1
check_databases = 1
check_forests = 1
check_servers = 1
check_server_ports = 1
```

Las claves booleanas son numéricas: un valor mayor que `0` habilita la función; `0`,
un valor vacío o uno no numérico la deshabilitan.

La comprobación de puertos vigila el puerto de cada servidor de aplicaciones y forma
parte de la recopilación de servidores, así que solo se genera mientras
`check_servers` está habilitada.

Para dejar entidades fuera, indique sus nombres exactos, separados por comas, en la
clave de exclusión de su tipo. Los nombres se comparan tal como los informa
MarkLogic:

```ini
exlude_hosts =
exlude_databases = Documents,Modules
exlude_forests =
exlude_servers = Manage
```

Las claves se escriben `exlude_*`, sin la `c`: la forma correcta `exclude_*` se lee
como una clave desconocida y no excluye nada.

El nivel de detalle añade módulos a cada tipo de entidad:

```ini
show_detailed_hosts = 0
show_detailed_databases = 0
show_detailed_forests = 0
show_detailed_servers = 1
```

Un tipo en `0` genera el conjunto resumido descrito en
[Entender los resultados](#entender-los-resultados); en `1` genera todos los campos
que la API informa para la entidad.

### Identidad de los agentes

Todos los agentes generados comparten cabecera, esquema de nombre, grupo e intervalo:

```ini
agent_name_header = ML_
agent_group = MarkLogic
agent_interval = 300
```

La cabecera es la única parte libre del nombre; el resto lo fijan el tipo de entidad
y el nombre que informa MarkLogic, como se describe en
[Agentes generados](#agentes-generados). Use una cabecera distintiva, como `ML_`,
para que los agentes de varias instalaciones no se mezclen.

`show_server_type_in_agentname` (habilitada en el archivo distribuido) añade el tipo
de servidor de aplicaciones a esos nombres de agente:

```ini
show_server_type_in_agentname = 1
```

Activarla o desactivarla renombra todos los agentes de servidor de aplicaciones. Los
agentes creados con el nombre anterior dejan de recibir datos y aparecen agentes
nuevos, así que decídalo antes de la primera ejecución.

`agent_group` es el grupo en el que se crean los agentes, por nombre, y
`agent_interval` es su intervalo en segundos. Ambos se aplican a todos los agentes
generados.

### Decoración de los módulos

Estos ajustes se aplican a los módulos generados:

```ini
#module_header = Custom_header_
#warning_instructions = Some text to guide the team
#critical_instructions = Some text to guide the team
#global_alerts = critical condition
```

- `module_header` añade un prefijo al nombre de todos los módulos de todas las
  entidades.
- `warning_instructions`, `critical_instructions` y `unknown_instructions` añaden el
  texto de instrucciones correspondiente a todos los módulos.
- `global_alerts` asocia una plantilla de alerta a todos los módulos. Repita la clave
  una vez por plantilla; el valor es el nombre de la plantilla de alerta.

### Crear el grupo de agentes

El plugin puede crear el grupo de agentes a través de la API de la consola de
Pandora FMS antes de entregar los agentes:

```ini
autocreate_group = 0
api_url = http://<PANDORA_FMS_URL>/pandora_console/include/api.php
api_user = <USERNAME>
api_user_pass = <PASSWORD>
api_pass = <PASSWORD>
group_icon = Servers
```

`api_url`, `api_user`, `api_user_pass` y `api_pass` se usan solo para esa creación;
`group_icon` es el icono que recibe el grupo nuevo. Active
`autocreate_group = 1` solo cuando el grupo no exista todavía:

> No active la creación de grupos cuando la instalación de Pandora FMS forme parte de
> un entorno con metaconsola. Crear grupos en un nodo con metaconsola activa puede
> romper la sincronización de grupos del conjunto completo de nodos.

### Ejecutarlo desde Pandora FMS

El plugin es un comando, así que Pandora FMS lo ejecuta igual que una persona: con la
ruta del archivo de configuración. Hay dos vías de integración disponibles y pueden
convivir:

- **Como módulo de plugin de un agente.** El agente de Pandora FMS ejecuta el comando
  en cada intervalo y recoge el módulo `Plugin message` que imprime el plugin. Active
  `as_agent_plugin = 1` en el archivo para esta vía.
- **Como módulo de plugin de servidor o tarea programada.** Mantenga
  `as_agent_plugin = 0`: el plugin imprime el resultado como un número y escribe los
  diagnósticos en la salida de error estándar, que es lo que registra un módulo de
  plugin de servidor. La programación con el `cron` del sistema se describe en
  [Operación y resolución de problemas](#operacion-y-resolucion-de-problemas).

<!-- SCREENSHOT NEEDED: pantalla de definición de módulo de Pandora FMS para el módulo de plugin o de plugin de servidor que ejecuta pandora_marklogic.pl, mostrando dónde se introducen el comando y la ruta del archivo de configuración. -->

La primera vía necesita un agente de Pandora FMS en el host que ejecuta el plugin; la
segunda no, y es la opción habitual cuando el plugin ya se ejecuta en el servidor de
Pandora FMS. Ninguna de las dos instala nada en los nodos de MarkLogic.

## Verificación

Ejecute el plugin sin argumentos para confirmar que el entorno de ejecución está
completo. Imprime su resumen de uso y termina:

```bash
perl /usr/share/pandora_server/util/pandora_marklogic.pl
```

```text
Pandora FMS Plugin for MarkLogic NoSQL Monitoring <version>

At least one parameter is needed by this plugin:
Usage: pandora_marklogic.pl pandora_ml.conf
```

Después ejecútelo con el archivo de configuración:

```bash
perl /usr/share/pandora_server/util/pandora_marklogic.pl <PATH_TO_CONFIG>
```

Con `as_agent_plugin = 1`, una ejecución correcta imprime un módulo `Plugin message`
en la salida estándar:

```xml
<module>
	<name><![CDATA[Plugin message]]></name>
	<type>generic_proc</type>
	<data><![CDATA[1]]></data>
	<description><![CDATA[Execution OK]]></description>
</module>
```

Con `as_agent_plugin = 0` imprime `1` en la salida estándar y el mismo mensaje en la
salida de error estándar:

```text
Plugin execution Result:[Execution OK]
```

Una ejecución que no puede leerlo todo imprime `0` en lugar de `1` y enumera las
peticiones fallidas en la descripción del módulo `Plugin message`, o después de
`Plugin execution Result:` en la salida de error estándar. Por ejemplo:

```text
Plugin execution Result:[ No response from http://<MARKLOGIC_HOST>:8002/manage/LATEST/hosts?format=json
  No response from http://<MARKLOGIC_HOST>:8002/manage/LATEST/databases?format=json
 ]
```

Por último, confirme que los agentes han llegado. El plugin borra cada documento
temporal solo cuando su entrega se completa, así que un documento que permanece en
`temp` es una entrega fallida. En Pandora FMS los agentes generados aparecen con la
cabecera configurada y cada uno lleva los módulos descritos en
[Entender los resultados](#entender-los-resultados).

<!-- SCREENSHOT NEEDED: lista de agentes de Pandora FMS tras una primera ejecución, filtrada por la cabecera de nombre configurada, mostrando los agentes generados de host, base de datos, bosque y servidor de aplicaciones. -->

Una ejecución que informa `Execution OK` no demuestra que se haya recopilado cada
entidad: un inventario vacío no produce ningún error. Compare el número de agentes con
el inventario de la instalación.

## Entender los resultados

El plugin crea un agente por entidad, en cuatro familias, más un módulo de estado
cuando se ejecuta como plugin de agente. Las familias son independientes: un tipo
deshabilitado, excluido o ilegible simplemente no produce ningún agente.

- **Hosts** informan de si el nodo está en línea, de si su vista de estado incluye
  algún problema crítico y de su tasa y su carga. Estos agentes no tienen padre.
- **Bases de datos** informan de disponibilidad, capacidad, retardo de replicación y,
  en modo resumido, de tamaño y de estado de indexación o rebalanceo.
- **Bosques** informan de si el bosque está abierto y habilitado, de su carga y de su
  retardo de replicación. Cada agente de bosque tiene como padre la base de datos que
  lo contiene, cuando se recopilan bases de datos.
- **Servidores de aplicaciones** informan de si el servicio está abierto y
  habilitado, de su estado detallado y de si su puerto acepta conexiones.

Los módulos de estado son módulos `generic_proc` o `async_proc`: `1` es un estado
normal, `0` es un fallo y un valor que el plugin no sabe interpretar se informa como
`3` con el estado original en la descripción del módulo. Una base de datos que no
informa de estado recibe `2`. Los módulos numéricos llevan la unidad que informa la
API, de modo que tasas, cargas y tamaños conservan su significado en MarkLogic. El
modo resumido conserva los módulos que responden «¿está sano y cuánta carga tiene?»;
el modo detallado añade los campos de la entidad y descarta los módulos exclusivos del
resumen, y por eso genera muchos más módulos.

`Plugin message` resume la ejecución, no la instalación: `1` significa que todas las
peticiones intentadas devolvieron datos y `0` significa que al menos una petición
falló o que no se pudo completar una entrega.

## Operación y resolución de problemas

### Ejecución programada

El plugin no tiene planificador propio, así que lo ejecuta uno externo. Una entrada
del `cron` del sistema en el host, por ejemplo:

```cron
*/5 * * * * root perl /usr/share/pandora_server/util/pandora_marklogic.pl <PATH_TO_CONFIG>
```

Ajuste la programación al intervalo de agente configurado, para que los agentes
reciban datos con la frecuencia que espera la consola.

### Registro

El plugin escribe un archivo de registro, `pandora_ml.log` en el directorio de trabajo
por defecto. Indique una ruta absoluta en `log` para ubicarlo en otro sitio. Cada
ejecución empieza un registro nuevo, y un registro anterior mayor de 3.200.000 bytes
se renombra a `.old` antes de empezar el nuevo. Todas las líneas llevan marca de
tiempo y el valor de `execution_id`, `MarkLogic` cuando la clave está vacía, lo que
ayuda a distinguir ejecuciones simultáneas.

### Tiempo de espera

`timeout` limita la ejecución completa, no una petición: cuando expira, el plugin
termina con `Exceeded execution time` en la salida de error estándar y un estado de
salida distinto de cero, antes de entregar nada. El valor está en segundos. El
archivo distribuido fija `2`, que es poco para una instalación con muchas entidades;
auméntelo cuando las ejecuciones se corten. Si la clave no está, el plugin usa `60`.

### Depuración de una ejecución

`extra_log = 1` escribe en el registro la respuesta JSON en bruto de cada base de
datos y de cada bosque, además de los mensajes habituales, mientras ese tipo está en
modo resumido. Úselo para comprobar qué devuelve la API para una entidad que genera
módulos inesperados y desactívelo después: la salida es voluminosa.

### Limitaciones conocidas de esta versión

- **Los agentes de servidor de aplicaciones solo se entregan mientras se recopilan
  bosques.** Con `check_forests = 0` y `check_servers = 1` los servidores se leen,
  pero sus agentes nunca se entregan.
- **`module_interval`, `module_tags` y `module_group` no tienen efecto.** Se aceptan y
  se ignoran, así que los módulos generados no llevan etiquetas ni grupo de módulo, y
  el plugin no fija el intervalo de los módulos.
- **`status min-capacity` lleva la cadena de unidad como valor.** El módulo informa la
  unidad que devuelve la API en lugar de la capacidad numérica, así que su valor no es
  una medida.
- **Las claves de exclusión se escriben `exlude_*`.** Las claves con la forma correcta
  `exclude_*` no excluyen nada.
- **Un `tentacle_client` vacío no recurre al `PATH`.**
- **No hay agente de clúster.** La instalación en sí no tiene agente y los agentes de
  servidor de aplicaciones no tienen padre; solo los bosques tienen padre, su base de
  datos.
- **El modo detallado nombra los módulos con el campo de la API.** Cuando el mismo
  nombre de campo aparece en más de una sección de una entidad, los módulos repiten el
  nombre, y los campos con unidad `enum` o `quantity` no producen ningún módulo.

### Resolución de problemas

- **`Error: Cannot found temporal directory` seguido del texto de uso** — no se pudo
  leer el archivo de configuración, o `temp` no existe. El plugin informa de la
  carpeta temporal ausente porque, cuando no puede abrir el archivo, vuelve a sus
  valores por defecto; compruebe primero la ruta y después la carpeta.
- **`Error: Cannot found target directory ...`** — `local_folder` no existe. La
  carpeta es obligatoria incluso cuando el plugin entrega con Tentacle.
- **`Plugin message` informa `0` con `No response from <url>`** — esa petición a la API
  de gestión falló. Compruebe `ml_server`, `ml_port`, `use_ssl`, las credenciales y
  `ml_realm`. Un puerto equivocado o una API de gestión deshabilitada hacen fallar
  todas las peticiones de la ejecución.
- **Solo un tipo de entidad informa `No response`** — su endpoint no está disponible o
  se rechaza para esa ruta, por ejemplo `/forests` con una cuenta restringida. Los
  demás tipos siguen generando agentes.
- **`Plugin message` informa `0` con `Failed to retrieve the group id for <server>`** —
  no se pudo leer la relación de grupo de un servidor de aplicaciones. Sus módulos se
  generan igualmente.
- **`Plugin message` informa `0` con `There was a problem sending file using
  tentacle`** — la entrega con Tentacle falló. Compruebe `tentacle_ip`,
  `tentacle_port`, `tentacle_client` y el camino de red hasta el servidor de
  Pandora FMS. El documento permanece en `temp`.
- **`Plugin message` informa `0` con `There was a problem copying local file`** — el
  usuario que ejecuta el plugin no puede escribir en `local_folder`.
- **`Exceeded execution time`** — la ejecución superó `timeout`. Auméntelo o reduzca el
  ámbito recopilado.
- **Ningún módulo en una entidad que existe** — su tipo está deshabilitado, su nombre
  está en la lista de exclusión o la ejecución terminó antes de llegar a ella. Active
  el tipo, revise el valor de exclusión y el registro.
- **Menos módulos de los esperados en una entidad** — está en modo resumido. Active la
  clave `show_detailed_*` correspondiente.
- **Los agentes dejaron de recibir datos tras un cambio de nombre** — el nombre del
  agente cambió, así que el agente anterior queda huérfano. Revise `agent_name_header`
  y `show_server_type_in_agentname`, y elimine los agentes que hayan quedado atrás.

## Referencia

### Archivo de configuración

El archivo se pasa como único argumento y contiene líneas `key = value`. Los valores
del archivo sustituyen a los valores por defecto que se indican a continuación.

| Clave | Obligatoria | Por defecto | Descripción |
| --- | --- | --- | --- |
| `ml_server` | Sí | Vacío | Host de MarkLogic que sirve la API de gestión |
| `ml_port` | No | `8002` | Puerto de la API de gestión |
| `ml_user` | Sí | Vacío | Usuario de MarkLogic con permiso para leer la API de gestión |
| `ml_pass` | Sí | Vacío | Contraseña de `ml_user` |
| `ml_realm` | No | `public` | Realm de autenticación que se envía con las credenciales |
| `use_ssl` | No | Sin definir (`0` en el archivo distribuido, HTTP) | Un valor mayor que `0` consulta `https://<ml_server>:<ml_port>`; cualquier otro valor consulta `http://` |
| `ml_api_version` | No | `LATEST` | Versión de la API usada como segmento de ruta: `V1`, `V2` o `LATEST` |
| `timeout` | No | `60` (`2` en el archivo distribuido) | Segundos que puede durar la ejecución completa |
| `log` | No | `pandora_ml.log` | Ruta del archivo de registro |
| `execution_id` | No | `MarkLogic` | Texto añadido a cada línea del registro; vacío usa `MarkLogic` |
| `temp` | No | `/tmp` | Carpeta donde se escribe cada documento antes de entregarlo; debe existir |
| `mode` | No | `tentacle` | `tentacle` entrega con el cliente de Tentacle; cualquier otro valor copia en `local_folder` |
| `tentacle_ip` | Sí con `mode=tentacle` | Vacío | Dirección del servidor de Tentacle |
| `tentacle_port` | No | `41121` | Puerto del servidor de Tentacle |
| `tentacle_opts` | No | Vacío | Opciones adicionales para el cliente de Tentacle, separadas por espacios |
| `tentacle_client` | No | `/usr/bin/tentacle_client` | Ejecutable del cliente de Tentacle; un valor vacío rompe la entrega |
| `local_folder` | No | `/var/spool/pandora/data_in` | Destino local de los documentos; debe existir incluso con Tentacle |
| `as_agent_plugin` | No | `0` | `1` imprime un módulo `Plugin message` en la salida estándar; cualquier otro valor imprime el resultado de la ejecución como número |
| `agent_name_header` | No | Vacío | Prefijo del nombre de todos los agentes generados |
| `agent_group` | No | `MarkLogic` | Grupo de los agentes generados, por nombre |
| `agent_interval` | No | `300` | Intervalo de los agentes generados, en segundos |
| `show_server_type_in_agentname` | No | Sin definir (deshabilitada) | `1` añade el tipo de servidor de aplicaciones a su nombre de agente |
| `check_hosts` | No | Sin definir (deshabilitada) | `1` recopila hosts; el archivo distribuido fija `1` |
| `check_databases` | No | Sin definir (deshabilitada) | `1` recopila bases de datos; el archivo distribuido fija `1` |
| `check_forests` | No | Sin definir (deshabilitada) | `1` recopila bosques y entrega los agentes de servidor de aplicaciones; el archivo distribuido fija `1` |
| `check_servers` | No | Sin definir (deshabilitada) | `1` recopila servidores de aplicaciones; el archivo distribuido fija `1` |
| `check_server_ports` | No | Sin definir (deshabilitada) | `1` añade la comprobación de puerto a cada agente de servidor de aplicaciones; el archivo distribuido fija `1` |
| `show_detailed_hosts` | No | Sin definir (resumido) | `1` genera todos los campos de cada host |
| `show_detailed_databases` | No | Sin definir (resumido) | `1` genera todos los campos de cada base de datos |
| `show_detailed_forests` | No | Sin definir (resumido) | `1` genera todos los campos de cada bosque |
| `show_detailed_servers` | No | Sin definir (resumido) | `1` genera todos los campos de cada servidor de aplicaciones; el archivo distribuido fija `1` |
| `exlude_hosts` | No | Vacío | Nombres de host que se omiten, separados por comas |
| `exlude_databases` | No | Vacío | Nombres de base de datos que se omiten, separados por comas |
| `exlude_forests` | No | Vacío | Nombres de bosque que se omiten, separados por comas |
| `exlude_servers` | No | Vacío | Nombres de servidor de aplicaciones que se omiten, separados por comas |
| `autocreate_group` | No | `0` | `1` crea `agent_group` a través de la API de la consola antes de entregar |
| `api_url` | Solo para crear el grupo | Vacío | URL de la API de la consola, terminada en `/include/api.php` |
| `api_user` | Solo para crear el grupo | `admin` | Usuario de la consola |
| `api_user_pass` | Solo para crear el grupo | `pandora` | Contraseña del usuario de la consola |
| `api_pass` | Solo para crear el grupo | `1234` | Contraseña de la API |
| `group_icon` | No | Sin definir (`Servers` en el archivo distribuido) | Icono del grupo creado |
| `module_header` | No | Vacío | Prefijo del nombre de todos los módulos |
| `warning_instructions`, `critical_instructions`, `unknown_instructions` | No | Vacío | Texto de instrucciones añadido a todos los módulos |
| `global_alerts` | No | Vacío | Plantilla de alerta asociada a todos los módulos; repita la clave por plantilla |
| `extra_log` | No | Sin definir (deshabilitada) | `1` escribe en el registro el JSON en bruto de cada base de datos y cada bosque |
| `module_interval` | No | — | Se acepta y se ignora en esta versión |
| `module_tags` | No | — | Se acepta y se ignora en esta versión |
| `module_group` | No | — | Se acepta y se ignora en esta versión |

### Ejecución por línea de comandos

```bash
perl pandora_marklogic.pl <PATH_TO_CONFIG>
```

| Condición | Comportamiento |
| --- | --- |
| Sin argumentos | Imprime el resumen de uso y termina con estado 1 |
| Un argumento que nombra un archivo legible | Se ejecuta con esa configuración |
| Un argumento que nombra un archivo que no se puede abrir | Informa de la carpeta temporal ausente, imprime el resumen de uso y termina con estado 1, porque los valores por defecto sustituyen al archivo ilegible |
| Más de un argumento | Solo se lee el primer argumento; el resto se ignoran |
| `temp` o `local_folder` no existe | Informa de la carpeta ausente, imprime el resumen de uso y termina con estado 1 |
| La ejecución termina | Termina con estado 0, haya fallado o no alguna petición; el resultado está en la salida |
| `timeout` expira | Termina con `Exceeded execution time` en la salida de error estándar y un estado distinto de cero |

### Agentes generados

`<header>` es el valor de `agent_name_header` y `<name>` es el nombre de la entidad
tal como lo informa MarkLogic.

| Entidad | Nombre del agente | Padre | Módulos |
| --- | --- | --- | --- |
| Host | `<header>H_<name>` | Ninguno | [Módulos de host](#modulos-de-host) |
| Base de datos | `<header>DB_<name>` | Ninguno | [Módulos de base de datos](#modulos-de-base-de-datos) |
| Bosque | `<header>F_<name>` | El agente `<header>DB_<database>` de la base de datos que lo contiene, cuando se recopilan bases de datos | [Módulos de bosque](#modulos-de-bosque) |
| Servidor de aplicaciones | `<header>S_<name>`, o `<header>S_<name> [<type>]` con `show_server_type_in_agentname` | Ninguno | [Módulos de servidor de aplicaciones](#modulos-de-servidor-de-aplicaciones) |

Todos los agentes se crean con el sistema operativo `MarkLogic`, sin dirección, con el
grupo y el intervalo configurados y con la marca de tiempo de la ejecución. La
instalación en sí no tiene agente.

### Módulos generados

Los nombres de módulo que aparecen a continuación son los que escribe el plugin;
`module_header` se antepone a cada uno. Un campo que la API omite no elimina el
módulo: se escribe con el valor vacío. Solo los campos `enum` y `quantity` del modo
detallado no producen ningún módulo.

#### Módulos de host

| Módulo | Tipo | Cuándo | Significado |
| --- | --- | --- | --- |
| `error` | `generic_proc` | Siempre | `1` cuando la vista de estado no informa de ningún problema crítico, `0` cuando informa de uno; la descripción lleva el mensaje informado |
| `online` | `generic_proc` | Siempre | `1` mientras el host está en línea |
| `total-rate` | `generic_data` | Siempre | Tasa total con la unidad que informa la API |
| `total-load` | `generic_data` | Siempre | Carga total con su unidad |
| `deadlock-wait-load` | `generic_data` | Modo resumido | Carga de espera por bloqueo con su unidad |
| `journal-write-rate` | `generic_data` | Modo resumido | Tasa de escritura del journal con su unidad; la descripción repite el valor |
| `secure` | `generic_proc` | Modo detallado | `1` cuando el host informa de un estado seguro |
| Un módulo por campo de detalle | `generic_data`, `generic_data_string` o `generic_data` de `0`/`1` | Modo detallado | El nombre del campo; los campos booleanos se describen como `0 => false, 1 => true` |

El modo detallado cubre las secciones `load-detail`, `rate-detail` y `status-detail`
de la vista de estado del host.

#### Módulos de base de datos

| Módulo | Tipo | Cuándo | Significado |
| --- | --- | --- | --- |
| `state` | `async_proc` | Siempre | `1` disponible, `0` no disponible, `2` cuando la API no informa de estado, `3` cualquier otro estado; la descripción es `State [<value>]` |
| `status min-capacity` | `generic_data` | Cuando se informa | `max_warning` `30` y `max_critical` `10` por defecto; el valor es la cadena de unidad, consulte [Limitaciones conocidas](#limitaciones-conocidas-de-esta-version) |
| `foreign-forests-lag-exceeded` | `generic_data` | Cuando se informa | `min_warning` `15`, `max_warning` `20` y `min_critical` `21` por defecto |
| `replication_pending-lag (<n>)` | `generic_data` | Por réplica externa | Retardo pendiente; `min_warning` `10` y `min_critical` `15` por defecto |
| `replication journal-archive pending-lag (<n>)` | `generic_data` | Por archivo de journal | Retardo pendiente; los mismos valores por defecto |
| `total-rate`, `total-load` | `generic_data` | Modo resumido | Tasa y carga con sus unidades |
| `forest-count` | `generic_data` | Modo resumido | Número de bosques de la base de datos |
| `indexing-state`, `rebalancing-state`, `local-disk-failover` | `generic_data` | Modo resumido | Indicadores `0`/`1`, descritos como `0 => false, 1 => true` |
| `device-space`, `data-size` | `generic_data` | Modo resumido | Espacio con la unidad que informa la API |
| Un módulo por campo de detalle | `generic_data`, `generic_data_string` o `generic_data` de `0`/`1` | Modo detallado | El nombre del campo, para cada sección de la vista de estado de la base de datos excepto `state` |

`<n>` numera las entradas de la lista desde `0`.

#### Módulos de bosque

| Módulo | Tipo | Cuándo | Significado |
| --- | --- | --- | --- |
| `state` | `generic_proc` | Siempre | `1` abierto, disponible o en replicación síncrona; `0` cerrado o no disponible; `3` un estado no reconocido, con el valor informado en la descripción |
| `replication_pending-lag (<n>)` | `generic_data` | Por réplica externa | Retardo pendiente; `min_warning` `10` y `min_critical` `15` por defecto |
| `replication journal-archive pending-lag (<n>)` | `generic_data` | Por archivo de journal | Retardo pendiente; los mismos valores por defecto |
| `enabled` | `generic_proc` | Modo resumido | `1` cuando el bosque está habilitado |
| `rebalancing-state`, `local-disk-failover` | `generic_data` | Modo resumido | Indicadores `0`/`1` |
| `total-rate`, `total-load`, `query-read-load`, `save-write-load` | `generic_data` | Modo resumido | Valor con su unidad, `sec/sec` cuando la API la omite |
| Un módulo por campo de detalle | `generic_data`, `generic_data_string` o `generic_data` de `0`/`1` | Modo detallado | El nombre del campo, para cada sección de la vista de estado del bosque excepto `state` |

#### Módulos de servidor de aplicaciones

| Módulo | Tipo | Cuándo | Significado |
| --- | --- | --- | --- |
| `state` | `generic_proc` | Siempre | `1` abierto, `0` cerrado, `3` un estado no reconocido |
| `port status` | `generic_proc` | `check_server_ports` y `check_servers` | `1` cuando se establece una conexión TCP con `ml_server` en el puerto del servidor de aplicaciones; la descripción es `Port <port>` |
| `enabled` | `generic_proc` | Modo resumido | `1` cuando el servidor está habilitado |
| Un módulo por campo de detalle | `generic_data`, `generic_data_string` o `generic_data` de `0`/`1` | Modo detallado | El nombre del campo, para cada sección de la vista de estado del servidor excepto `state` |

La comprobación de puerto conecta siempre con `ml_server`, no con el host que ejecuta
el servidor de aplicaciones.

#### Módulo global

| Módulo | Tipo | Cuándo | Significado |
| --- | --- | --- | --- |
| `Plugin message` | `generic_proc` | `as_agent_plugin` activado | `1` con la descripción `Execution OK`, o `0` con los diagnósticos recopilados en la descripción |

### Identidad del addon

| Propiedad | Valor |
| --- | --- |
| Identificador en el Marketplace | `pandorafms.marklogic_monitoring` |
| Nombre | Marklogic monitoring |
| Versión | `1.0` |
| Última actualización en el Marketplace | 2025-07-07 |
| Autor | Pandora FMS |
| Disponibilidad | Descarga limitada a usuarios con licencia |
