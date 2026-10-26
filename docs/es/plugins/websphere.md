# Pandora WebSphere plugin

*Última actualización del artículo: 2026-10-26.*

## Qué hace

El plugin Pandora WebSphere lee el estado de cada servidor de aplicaciones en
ejecución de una celda de IBM WebSphere Application Server y lo publica en
Pandora FMS. Cada ejecución invoca el cliente de administración `wsadmin` de un
perfil de WebSphere con un pequeño script de administración, lee la lista de
instancias que devuelve y, por cada servidor de aplicaciones informado como
proceso gestionado, construye un agente de Pandora FMS con el nombre de ese
servidor y nueve módulos: tipo de proceso, ID de proceso, estado, sistema
operativo, tamaño del heap, memoria libre del heap, dos cifras del pool de hilos
de `WebContainer` y el número de aplicaciones en ejecución.

No se instala nada dentro de WebSphere y el addon no abre ningún puerto propio:
usa la conexión de administración que ya define el perfil de WebSphere. Por eso
el host que ejecuta el addon debe tener los ficheros de cliente de WebSphere y
el perfil de la celda.

Cada ejecución produce dos superficies distintas:

- **La salida estándar** lleva dos módulos para el host que ejecuta el addon,
  `Websphere_status` y `Websphere_count`, de modo que el agente de Pandora FMS o
  el módulo de plugin que lo ejecuta informa del resultado de la ejecución.
- **Un documento de agente por instancia** se envía a un servidor Tentacle, de
  forma que la consola recibe un agente por servidor de aplicaciones de
  WebSphere con los módulos de ese servidor.

Esta página documenta el addon del Marketplace `pandorafms.websphere`. No es el
plugin de PMI de WebSphere cuyos módulos se llaman `Wbs_*`: la entrada del
Marketplace, su paquete y la guía enlazada desde ella coinciden con el addon
descrito aquí. Consulte [Identidad del addon](#identidad-del-addon).

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Addon `pandorafms.websphere`, versión `1.0` | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del addon](#identidad-del-addon) |
| CentOS 7, Fedora, AIX 7.1, AIX 7.2 | `Known compatible` | La guía del addon enlazada desde la entrada del Marketplace registra estos sistemas como aquellos donde se probó el plugin. No se ha revalidado para la versión `1.0` |
| Otras distribuciones de Linux y otros sistemas operativos | `Not validated` | No se ha registrado una matriz de distribuciones ni de versiones para este addon |
| Versiones de IBM WebSphere Application Server | `Not validated` | No se ha registrado ninguna versión de WebSphere. El addon lee atributos de `AdminControl` y `AdminConfig` y las propiedades `heapSize` y `freeMemory` de la JVM |
| Al menos un servidor de aplicaciones en ejecución de tipo `ManagedProcess` | `Required` | Solo se publican las instancias que informan ese tipo de proceso; un gestor de despliegue o un agente de nodo no |
| `wsadmin` de un perfil de WebSphere, con soporte de Jython | `Required` | Es la única fuente de datos: se ejecuta en cada pasada |
| La librería Perl `PandoraFMS::PluginTools` | `Required` | Sin ella el addon no arranca. La guía del addon la enumera como requisito previo |
| Un servidor Tentacle accesible desde el host que ejecuta el addon | `Required` cuando `mode=tentacle` | Cada agente de instancia se entrega en `tentacle_ip:tentacle_port` |
| Una carpeta de datos con permiso de escritura | `Required` cuando `mode` no es `tentacle` | Cada documento de agente de instancia se copia en `local_folder` |
| Pandora FMS NG 784 y posteriores | `Supported` | El Marketplace declara que todas sus integraciones son compatibles con Pandora FMS NG 784 y versiones posteriores; es una declaración de catálogo que cubre este addon, no un registro de prueba del mismo |

### Requisitos

1. **Una celda de WebSphere con los servidores de aplicaciones que desea
   monitorizar en ejecución.** El plugin lista los servidores mediante los
   objetos de administración de celda y nodo, así que `wsadmin` debe poder
   alcanzar los metadatos de la celda.
2. **El cliente `wsadmin` de un perfil de WebSphere** en el host que ejecuta el
   addon, con soporte de Jython (`-lang jython`). El addon no pasa host ni puerto
   a `wsadmin`, de modo que este usa la conexión configurada en ese perfil.
3. **Un usuario de administración de WebSphere** que pueda ejecutar consultas
   `AdminConfig` y `AdminControl` sobre la celda. El par de credenciales viaja a
   `wsadmin` en su línea de comandos.
4. **Un script de administración** que el addon pasa a `wsadmin` con `-f`. La
   guía del addon sitúa `pandora_websphere.pl`, `pandora_websphere.conf` y este
   script en la misma carpeta.
5. **La librería Perl `PandoraFMS::PluginTools`, en un directorio `PandoraFMS`
   junto al ejecutable.** El addon añade su propio directorio a la ruta de
   librerías de Perl, así que una copia colocada ahí siempre se encuentra; una
   instalación de la librería en el sistema también sirve. Si el paquete
   distribuido ya la coloca junto al ejecutable, no hay que hacer nada.
6. **El cliente de Tentacle (`tentacle_client`) disponible en `PATH`** en el host
   que ejecuta el addon. Cada agente de instancia se entrega con él cuando
   `mode=tentacle`.
7. **Una cuenta del Marketplace con licencia**: la descarga de este addon está
   limitada a usuarios con licencia.
8. **Pandora FMS** para recibir los datos: el Data Server de Pandora FMS
   habilitado para aceptar las entregas de Tentacle, y el Plugin Server
   habilitado si registra el addon como módulo de plugin de consola.

### Instalar el addon

Descargue el paquete desde la entrada del Marketplace:

[https://marketplace.pandorafms.com/entries/pandorafms.websphere](https://marketplace.pandorafms.com/entries/pandorafms.websphere)

El paquete contiene el ejecutable del addon `pandora_websphere.pl`, su archivo de
configuración de ejemplo `pandora_websphere.conf` y el script de administración
`list_servers.py`. Cópielos al host que ejecutará el addon —la carpeta
recomendada para un plugin de servidor es
`/usr/share/pandora_server/util/plugin/`— y edite una copia del archivo de
configuración, porque sus valores son ejemplos.

Coloque `PluginTools.pm` en un subdirectorio `PandoraFMS` de esa carpeta si el
paquete no lo incluye. La librería se distribuye con Pandora FMS.

## Configuración

### Archivo de configuración

El addon lee exactamente un archivo de configuración, que se pasa como primer
argumento. Cada línea contiene un par `clave;valor` separado por punto y coma.
Los valores se recortan, las líneas en blanco y las que empiezan por `#` se
omiten, y la última aparición de una clave repetida prevalece. No hay secciones y
el conjunto de claves no se valida.

```ini
wsadmin;<PATH_TO_WSADMIN>
jython;<PATH_TO_JYTHON_SCRIPT>
user;<USERNAME>
password;<PASSWORD>
mode;tentacle
tentacle_ip;<PANDORA_FMS_URL>
tentacle_port;41121
```

Los nombres del archivo de ejemplo, `pandora_websphere.conf` y
`list_servers.py`, son convenciones: el nombre del archivo es libre y el script
es la ruta que ponga en `jython`.

### Puntos clave

- **`wsadmin` es la ruta absoluta al cliente `wsadmin` del perfil**, por ejemplo
  `/opt/IBM/WebSphere/AppServer/profiles/AppSrv01/bin/wsadmin.sh` en Linux o
  AIX. El addon lo ejecuta como
  `<wsadmin> -lang jython -user <user> -password <password> -f <jython>`.
- **`jython` es la ruta absoluta al script de administración.** Un valor relativo
  se resuelve desde el directorio de trabajo del proceso que ejecuta el addon. El
  ejemplo distribuido escribe `listservers.py`, mientras que el script entregado
  con el addon es `list_servers.py`: ponga el nombre que exista en su copia,
  porque el valor se pasa a `wsadmin` sin cambios.
- **`user` y `password` son las credenciales de administración de WebSphere.**
  `wsadmin` las recibe en su línea de comandos y el archivo de configuración
  guarda la contraseña en texto plano.
- **`mode` selecciona la entrega.** `tentacle` (en minúsculas) ejecuta el cliente
  de Tentacle para cada agente de instancia. Cualquier otro valor no vacío copia
  el documento de agente en `local_folder`. La clave `transfer_mode` se acepta
  como alias cuando falta `mode`, pero la comprobación previa del propio addon
  solo lee `mode`, así que use `mode`.
- **`tentacle_ip` y `tentacle_port` son el destino de Tentacle.** El puerto vale
  `41121` por defecto. La dirección se usa tal cual se escribe; no hay host por
  defecto.
- **`module_group`, `module_interval` y `module_tag_list` se aplican a todos los
  módulos de la ejecución**, incluidos `Websphere_status` y `Websphere_count`.
  Las variantes en mayúsculas `MODULE_GROUP`, `MODULE_INTERVAL` y
  `MODULE_TAG_LIST` tienen prioridad cuando están las dos grafías.
- **`debug` imprime los diagnósticos del addon en la salida de error.** Sin él,
  los errores de entrega, la salida de Tentacle y los errores de ficheros
  temporales son silenciosos.
- **`temp` (o `tmp`) fija la carpeta donde se escriben los documentos de
  agente.** En Linux es `/tmp` cuando no se indica. En otros sistemas operativos
  no hay valor por defecto: indíquela explícitamente, porque de lo contrario la
  ruta del documento se resuelve en la raíz del sistema de ficheros.

### Rutas de ejecución

El addon puede ejecutarse en dos sitios. Ambos producen las mismas dos
superficies, así que elija el que corresponda a donde esté el cliente de
administración de WebSphere.

**Como plugin del agente de Pandora FMS en el host de WebSphere
(recomendado).** Declárelo en la configuración del agente para que este lo
ejecute en cada intervalo:

```text
module_plugin perl /opt/pandora/plugins/websphere/pandora_websphere.pl /opt/pandora/plugins/websphere/pandora_websphere.conf
```

El agente ingiere los dos módulos impresos en la salida estándar y los informa en
su propio agente, mientras que los agentes de instancia llegan por Tentacle. Es
la única ruta en la que la máquina que ejecuta `wsadmin` es también la
monitorizada por el agente.

**Como módulo de plugin de consola.** La guía del addon describe registrar el
addon en Pandora FMS y llamarlo después desde un módulo de plugin de un agente:

1. Abra **Servers → Plugins**.
2. Registre el addon, ya sea subiendo el paquete `.pspz2` de la entrada del
   Marketplace o añadiéndolo manualmente con el comando que ejecuta
   `pandora_websphere.pl` y la macro `_field1_` como ruta del archivo de
   configuración.
3. En el agente, cree un módulo de plugin y seleccione el plugin registrado, con
   la ruta del archivo de configuración como valor del campo.

<!-- SCREENSHOT NEEDED: Formulario de registro de plugins de servidor en la consola de Pandora FMS, mostrando el comando pandora_websphere.pl y su campo de macro _field1_. -->

Pandora FMS ejecuta un módulo de plugin de consola en el servidor que lo procesa,
no en el host del agente, así que esta ruta exige los ficheros de cliente de
WebSphere y el perfil en ese servidor de Pandora FMS. También cambia lo que
muestra el módulo: toda la salida estándar de la ejecución se guarda como valor
del módulo, de modo que el módulo muestra el XML de `Websphere_status` y
`Websphere_count` en lugar de un único número. Los agentes de instancia siguen
llegando por Tentacle, porque el addon los entrega con independencia de cómo se
haya arrancado.

### Credenciales y transporte

- El archivo de configuración guarda la contraseña de WebSphere en texto plano:
  restrínjalo al usuario que ejecuta el addon, por ejemplo con `chmod 600`, y
  manténgalo fuera de carpetas compartidas.
- `wsadmin` recibe la contraseña como valor de `-password`, así que es visible en
  la lista de procesos del host mientras el cliente se ejecuta. Use una cuenta de
  administración de WebSphere dedicada a este addon en lugar de una personal.
- El comando se compone por interpolación directa: una ruta o una contraseña que
  contenga espacios o metacaracteres del shell (`;`, `&`, `$`, comillas) se
  parte o se interpreta, y la ejecución falla. Elija una contraseña sin esos
  caracteres y rutas sin espacios.
- El addon no tiene opciones de transporte propias. La conexión de `wsadmin` es
  la configurada en el perfil de WebSphere, y los agentes de instancia viajan al
  servidor Tentacle de `tentacle_ip:tentacle_port` tal como se configure.

## Verificación

Ejecute el addon manualmente desde un terminal, pasando el archivo de
configuración como único argumento:

```bash
perl pandora_websphere.pl pandora_websphere.conf
```

La forma relativa funciona cuando el terminal ya está en la carpeta que contiene
ambos archivos. Cada ejecución se realiza una vez y termina.

Una ejecución correcta imprime dos bloques de módulo en la salida estándar y nada
más. Esta es su forma exacta; los valores son ilustrativos:

```xml
<module>
	<name><![CDATA[Websphere_status]]></name>
	<type>generic_proc</type>
	<data><![CDATA[1]]></data>
	<description><![CDATA[Estado de la ejecucion del plugin de websphere]]></description>
</module>
<module>
	<name><![CDATA[Websphere_count]]></name>
	<type>generic_data</type>
	<data><![CDATA[3]]></data>
	<description><![CDATA[Numero de instancias (application servers) recopiladas por el plugin de websphere]]></description>
</module>
```

`Websphere_count` debe coincidir con el número de servidores de aplicaciones en
ejecución de tipo `ManagedProcess` de la celda. Cada uno de ellos se convierte
además en un agente de Pandora FMS, con el nombre exacto del servidor de
WebSphere, y con los módulos que se listan en
[Módulos generados](#modulos-generados).

<!-- SCREENSHOT NEEDED: Lista de agentes de la consola de Pandora FMS, o vista de un agente, mostrando los agentes creados por el addon de WebSphere, uno por servidor de aplicaciones, con los nueve módulos de uno de ellos. -->

Una ejecución que imprime `Websphere_status` con `1` solo demuestra que el addon
llegó al final. No demuestra que `wsadmin` devolviera datos: compruebe
`Websphere_count`.

## Entender los resultados

El addon produce dos superficies independientes en cada ejecución:

- **El agente que lo ejecuta recibe `Websphere_status` y `Websphere_count`.**
  Son los únicos módulos que se escriben en la salida estándar. Cuando una
  entrega falla, el addon imprime un tercer módulo, `Pandora_websphere`, con
  valor `0`, y termina la ejecución antes de los dos módulos de estado.
- **Cada instancia publicada se convierte en su propio agente.** El documento de
  agente lleva el nombre del servidor de WebSphere como nombre del agente y los
  nueve módulos siguientes, cada uno con ese mismo nombre como prefijo. El
  documento no fija dirección, ni grupo de agentes, ni intervalo, así que el
  agente nuevo toma los valores que el servidor de Pandora FMS aplica por
  defecto.

Cómo se lee la lista de instancias:

- **Solo se publican los servidores cuyo tipo de proceso es exactamente
  `ManagedProcess`.** Los gestores de despliegue, los agentes de nodo y otros
  tipos de proceso se omiten en silencio y no incrementan `Websphere_count`.
- **El addon descarta los dos primeros segmentos separados por punto y coma de
  la salida de `wsadmin`** antes de analizar las instancias, porque espera ahí el
  banner de conexión de `wsadmin`. Si una versión de `wsadmin`, otro tipo de
  conector o una línea adicional cambian esa cuenta, los segmentos descartados
  pueden incluir la primera instancia: compare en las primeras ejecuciones el
  número de agentes creados con el número de servidores de aplicaciones en
  ejecución.
- **Se eliminan todos los espacios en blanco de la salida de `wsadmin` antes de
  analizarla.** Un nombre de servidor que contenga espacios se publica sin ellos,
  y un valor que contenga una coma o un punto y coma rompe la separación de
  campos de esa instancia.
- **Un agente por nombre de servidor.** Dos servidores de aplicaciones con el
  mismo nombre en celdas distintas, o en nodos distintos de la misma celda, se
  entregan al mismo agente, donde sus módulos se sobrescriben entre sí.

Cómo se leen los valores:

- `Heapsize` y `Free memory` son los atributos `heapSize` y `freeMemory` de la
  JVM de la instancia, en bytes.
- `Status` es el estado que `AdminControl` informa para el servidor, como
  `STARTED`; `OS` es la propiedad `os.name` de la JVM de la instancia, y `Proceso`
  es el tipo de proceso.
- `Threadpool ActiveCount` y `Threadpool PoolSize` proceden de las estadísticas
  del pool de hilos de `WebContainer`. Cuando esas estadísticas no aportan los
  dos valores esperados, ambos módulos se publican vacíos, lo que la consola
  muestra como desconocido.
- `Numero de aplicaciones` cuenta las aplicaciones que la instancia informa como
  en ejecución.

Los módulos de instancia no llevan unidad, ni descripción, ni umbral: cree en la
consola las unidades, los umbrales y las alertas que necesite. Los dos módulos de
estado solo llevan las descripciones que se muestran arriba. Los nombres de los
módulos se publican en el idioma que usa el addon, así que
`Numero de aplicaciones` y `Free memory` conservan esa grafía en las dos
versiones de idioma de esta página.

## Operación y resolución de problemas

### Operación diaria

- El addon no guarda estado entre ejecuciones: cada pasada consulta la celda en
  ese momento, así que puede ejecutarse manualmente cuando se quiera.
- En la ruta de plugin de agente, el agente de Pandora FMS lo ejecuta según la
  planificación de plugins de su configuración. En la ruta de consola, Pandora
  FMS lo ejecuta según el intervalo del módulo.
- Cada documento de instancia se escribe en la carpeta `temp` como
  `<servidor>.<epoch>.data` y se elimina tras una entrega correcta. Una entrega
  fallida deja el fichero en su sitio: revise esa carpeta cuando las entregas
  fallen de forma repetida.
- Active `debug` a `1` mientras diagnostica. Sin él, el addon no escribe en
  ningún sitio los errores de entrega, la salida de Tentacle ni los errores de
  ficheros temporales.

### Resolución de problemas

- **`Websphere_status` vale `1` pero `Websphere_count` vale `0`** — `wsadmin`
  no devolvió nada utilizable. Compruebe que `wsadmin` y `jython` apuntan a
  ficheros existentes, que las credenciales pueden ejecutar consultas de
  administración y que el comando `wsadmin` funciona cuando lo lanza a mano en
  ese host. El módulo de estado no refleja el resultado de `wsadmin`.
- **Aparece `Pandora_websphere` con `0`** — falló la entrega por Tentacle de una
  instancia. Compruebe que `tentacle_client` está instalado y en `PATH`, que
  `tentacle_ip` nombra un servidor Tentacle accesible con `tentacle_port` abierto
  y que `mode` es exactamente `tentacle`. Ejecute una vez con `debug` a `1` para
  ver el mensaje del cliente. La ejecución se detiene en el primer fallo, así que
  las instancias restantes de esa pasada no se entregan.
- **Aparece una línea que empieza por `ERROR:` en la salida estándar** — `mode`
  es `tentacle` y `tentacle_ip` está vacío. El addon imprime el mensaje pero no
  se detiene; la entrega falla después como se describe arriba. En la ruta de
  plugin de agente, esa línea se mezcla con el XML de los módulos.
- **No aparece el agente de una instancia** — puede que esa instancia se haya
  consumido como parte del banner de `wsadmin`, puede que no sea un
  `ManagedProcess`, o puede que su nombre contenga un carácter que rompa la
  separación de campos. Compare el inventario de la celda con `Websphere_count`.
- **`Can't locate PandoraFMS/PluginTools.pm` y ninguna salida** — la librería no
  está junto al ejecutable. Coloque `PluginTools.pm` en una carpeta `PandoraFMS`
  en el mismo directorio que `pandora_websphere.pl`.
- **El addon imprime `Websphere_status` y `Websphere_count` con una configuración
  vacía** — un primer argumento que no nombra un fichero existente no se lee como
  archivo de configuración. La ejecución continúa sin valores, no se llama a
  `wsadmin` y la cuenta es `0`. Revise la ruta del archivo de configuración.
- **Un módulo muestra valores desconocidos mientras su agente existe** — alguna
  de las cifras de la instancia llegó vacía, típicamente las estadísticas del pool
  de hilos. Revise la instancia en la consola de WebSphere.
- **En AIX, o en cualquier host donde no se indique `temp`,
  `Pandora_websphere` informa `0`** — el addon solo aplica `/tmp` como carpeta
  temporal por defecto en Linux. En el resto, la ruta del documento se resuelve
  en la raíz del sistema de ficheros y la escritura falla antes de que empiece la
  entrega. Indique en el archivo de configuración una carpeta con permiso de
  escritura en `temp`.

## Referencia

### Claves del archivo de configuración

| Nombre | Obligatoria | Por defecto | Descripción |
| --- | --- | --- | --- |
| `wsadmin` | Sí | — | Ruta absoluta al cliente `wsadmin` del perfil de WebSphere. Se invoca con `-lang jython -user <user> -password <password> -f <jython>`. |
| `jython` | Sí | — | Ruta al script de administración que se pasa a `wsadmin` con `-f`. Un valor relativo se resuelve desde el directorio de trabajo del proceso. |
| `user` | Sí | — | Usuario de administración de WebSphere que se pasa a `wsadmin` con `-user`. |
| `password` | Sí | — | Contraseña que se pasa a `wsadmin` con `-password`. Se guarda en texto plano en este archivo. |
| `mode` | Sí | — | `tentacle` entrega cada agente de instancia con el cliente de Tentacle; cualquier otro valor no vacío lo copia en `local_folder`. `transfer_mode` se acepta como alias cuando falta `mode`. |
| `tentacle_ip` | Obligatoria con `mode=tentacle` | — | Dirección del servidor Tentacle que recibe los agentes de instancia. |
| `tentacle_port` | No | `41121` | Puerto del servidor Tentacle. |
| `tentacle_client` | No | `tentacle_client` | Ejecutable del cliente de Tentacle, resuelto en `PATH` o indicado con ruta absoluta. |
| `tentacle_opts` | No | Vacío | Opciones adicionales que se pasan al cliente de Tentacle, separadas por espacios. |
| `local_folder` | Obligatoria cuando `mode` no es `tentacle` | — | Carpeta que recibe los documentos de agente de instancia cuando no se envían con Tentacle. |
| `temp` (`tmp`) | No | `/tmp` en Linux; ninguno en otros sistemas | Carpeta donde se escriben los documentos de agente de instancia antes de la entrega. Sin ella en un sistema distinto de Linux, la ruta se resuelve en la raíz del sistema de ficheros y la escritura falla. |
| `module_group` | No | Vacío (sin grupo) | Grupo de módulos asignado a todos los módulos generados, incluidos los dos que se imprimen en la salida estándar. `MODULE_GROUP` en mayúsculas tiene prioridad cuando están las dos. |
| `module_interval` | No | Intervalo del agente | Intervalo de módulo asignado a todos los módulos generados. `MODULE_INTERVAL` en mayúsculas tiene prioridad cuando están las dos. |
| `module_tag_list` | No | Vacío (sin etiquetas) | Etiquetas de módulo asignadas a todos los módulos generados, tal cual se indican. `MODULE_TAG_LIST` en mayúsculas tiene prioridad cuando están las dos. |
| `debug` | No | `0` | `1` (o cualquier valor numérico mayor que `0`) escribe en la salida de error los errores de entrega, la salida de Tentacle y los errores de ficheros temporales. |

Las claves booleanas se activan con cualquier valor numérico mayor que `0`. Las
claves desconocidas se aceptan y se ignoran.

### Ejecución por línea de comandos

```bash
perl pandora_websphere.pl <PATH_TO_CONFIG> [ -key value ... ]
```

| Condición | Comportamiento |
| --- | --- |
| El primer argumento nombra un fichero existente | Se lee como archivo de configuración y se retira de la lista de argumentos |
| El primer argumento nombra un fichero que no existe | No se lee como archivo de configuración; la ejecución continúa con los valores por defecto y los indicadores |
| Pares `-key value` después del archivo de configuración | Cada uno sustituye el valor de la misma clave |
| `--key value` o `-key=value` | No se reconocen como esa clave: solo se retira un guion inicial, así que el par se guarda bajo una clave que el addon ignora |
| Un argumento final sin valor | Se ignora |
| `-h`, `--help` | No es una opción de ayuda; se ignora y la ejecución continúa |
| Código de salida | `0` en una ejecución normal, en una entrega fallida y en errores de configuración; un código distinto de cero significa que Perl no pudo cargar el addon o su librería |

### Comportamiento de la entrega

| Situación | Resultado |
| --- | --- |
| `mode=tentacle` y la entrega funciona | El fichero temporal se elimina y la ejecución continúa con la instancia siguiente |
| `mode=tentacle` y la entrega falla | Se imprime `Pandora_websphere` con `0`, el fichero temporal queda en `temp` y la ejecución termina sin `Websphere_status` ni `Websphere_count` |
| `mode=tentacle` sin `tentacle_ip` | Se escribe una línea `ERROR:` en la salida estándar, la ejecución continúa y la entrega falla como arriba |
| Cualquier otro `mode` no vacío | El documento se copia en `local_folder`; una carpeta inexistente o sin permiso de escritura hace que la entrega falle como arriba |
| Sin `mode` ni `transfer_mode` | No se intenta ninguna entrega; el fallo solo se informa con `debug` activo y la ejecución termina como arriba |

### Módulos generados

Módulos de cada agente de instancia. `<servidor>` es el nombre del servidor de
WebSphere:

| Nombre del módulo | Tipo | Valor |
| --- | --- | --- |
| `<servidor>.Proceso` | `generic_data_string` | Tipo de proceso de la instancia, `ManagedProcess` |
| `<servidor>.Id` | `generic_data` | ID de proceso |
| `<servidor>.Status` | `generic_data_string` | Estado informado por `AdminControl`, como `STARTED` |
| `<servidor>.OS` | `generic_data_string` | `os.name` de la JVM de la instancia |
| `<servidor>.Heapsize` | `generic_data` | Tamaño del heap de la JVM de la instancia, en bytes |
| `<servidor>.Free memory` | `generic_data` | Memoria libre del heap de la JVM de la instancia, en bytes |
| `<servidor>.Threadpool ActiveCount` | `generic_data` | Cuenta activa del pool de hilos de `WebContainer` |
| `<servidor>.Threadpool PoolSize` | `generic_data` | Tamaño del pool de hilos de `WebContainer` |
| `<servidor>.Numero de aplicaciones` | `generic_data` | Número de aplicaciones en ejecución en la instancia |

Módulos del agente que ejecuta el addon:

| Nombre del módulo | Tipo | Valor | Se genera cuando |
| --- | --- | --- | --- |
| `Websphere_status` | `generic_proc` | `1` | La ejecución llega al final |
| `Websphere_count` | `generic_data` | Número de instancias publicadas en la pasada | La ejecución llega al final |
| `Pandora_websphere` | `generic_proc` | `0` | Falla una entrega; la ejecución se detiene entonces |

### Identidad del addon

| Campo | Valor |
| --- | --- |
| Identificador del Marketplace | `pandorafms.websphere` |
| Nombre en el Marketplace | Pandora websphere |
| Versión del addon | `1.0` |
| Última actualización en el Marketplace | 2025-06-27 |
| Paquete del Marketplace | `pandorafms.websphere.1.0.pspz2` |
| Licencia | `One` (descarga limitada a usuarios con licencia) |
| Tipo en el Marketplace | Miscelaneus |
| Etiquetas del Marketplace | applications, plugins, web |
| Autor | Pandora FMS |
| Flujo de trabajo | Monitorización de servidores de aplicaciones WebSphere desde un agente de Pandora FMS, con entrega por Tentacle de los agentes de instancia |
| Ejecutable del addon | `pandora_websphere.pl` |
| Archivo de configuración | `pandora_websphere.conf` |
