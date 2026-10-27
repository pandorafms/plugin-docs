# Citrix monitoring plugin

*Última actualización del artículo: 2026-10-26.*

## Qué hace

El plugin de monitorización de Citrix recoge el estado de un servidor Citrix a
través del agente Windows de Pandora FMS y lo publica como módulos de
Pandora FMS. Cada ejecución lee cuatro grupos de datos del servidor en el que
se ejecuta:

- **Contadores de rendimiento.** Cada ruta de contador incluida en el fichero
  de contadores, muestreada con `Get-Counter`.
- **Estado de servicios.** Para cada nombre de presentación de servicio de
  Windows incluido en el fichero de servicios, `1` mientras el servicio está en
  ejecución y `0` en caso contrario, consultado a través de WMI.
- **Sesiones.** El número de sesiones activas que el servidor informa en ese
  momento.
- **Usuarios conectados.** El número de sesiones de usuario iniciadas que el
  servidor informa en ese momento.

El plugin se ejecuta como **plugin de agente**: el agente Windows de Pandora FMS
lo lanza en cada intervalo del agente e ingiere los bloques `<module>` que
escribe en la salida estándar. No tiene modo de plugin de servidor, no envía
nada por la red y no entrega nada mediante Tentacle: todo lo que informa
proviene del servidor en el que corre el agente. Por eso lo habitual es un
agente por servidor Citrix, con el plugin instalado junto a ese agente.

Toda su configuración es una línea de comandos y dos listas de texto plano. El
plugin no lee ningún otro fichero de configuración, no guarda estado entre
ejecuciones y no crea agentes propios.

Citrix NetScaler es un addon distinto y no se trata en esta página.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Addon `pandorafms.citrix_monitoring_plugin`, versión `1.0` | Objetivo documentado | La versión del paquete de Marketplace que describe esta página. Consulte [Identidad del addon](#identidad-del-addon) |
| Pandora FMS NG 784 y posteriores | `Soportado` | Marketplace indica que sus integraciones son compatibles con Pandora FMS NG 784 y versiones posteriores |
| Windows Server 2008 con Citrix XenApp 6 | `Compatible conocido` | La guía del fabricante de este addon registra esa combinación como el sistema en el que se probó |
| Un servidor Windows con los componentes Citrix cuyos contadores y servicios se monitorizan | `Requerido` | La lista de contadores distribuida nombra conjuntos de contadores de Citrix Presentation Server, Citrix Licensing y XenApp, y la lista de servicios distribuida nombra servicios de Citrix XenApp |
| Windows PowerShell y el servicio WMI en el servidor monitorizado | `Requerido` | Requisito previo del plugin; no es una declaración de compatibilidad |
| `grep`, `gawk` y `wc` en el `PATH` de la cuenta que ejecuta el plugin | `Requerido` | Los grupos de servicios y de sesiones se calculan con esas herramientas; no forman parte de Windows |
| Una política de ejecución de PowerShell que permita ejecutar el script | `Requerido` | Requisito previo para que el agente pueda ejecutarlo |
| Versiones de Windows Server distintas de 2008 y versiones de Citrix distintas de XenApp 6 | `Sin validar` | No se ha registrado una matriz de versiones para este addon |
| Versiones del agente de Pandora FMS | `Sin validar` | La versión del agente no está registrada para este addon |

### Requisitos

1. **Un servidor Windows Server con el rol o los componentes Citrix que se
   quieran monitorizar.** Los contadores y servicios de las listas
   distribuidas pertenecen a Citrix Presentation Server / XenApp 6 y al propio
   Windows. Un servidor sin esos componentes simplemente no tiene tales
   contadores: el plugin informa los contadores de Windows y los servicios
   cuyo nombre de presentación coincide.
2. **Windows PowerShell y WMI habilitados.** El plugin es un script de
   PowerShell y lee el estado de los servicios a través de WMI.
3. **`grep`, `gawk` y `wc` disponibles en el `PATH`** de la cuenta que ejecuta
   el plugin, en el servidor monitorizado. La implementación distribuida los
   usa para extraer el estado del servicio y contar sesiones, y no tiene
   alternativa cuando faltan.
4. **El agente Windows de Pandora FMS**, instalado en el mismo servidor Citrix
   y configurado para ejecutar plugins de agente.
5. **Una política de ejecución de PowerShell que permita el script**, como se
   describe en [Permisos y política de ejecución](#permisos-y-politica-de-ejecucion).

No interviene ninguna base de datos, endpoint de API ni credencial remota: el
plugin lee el servidor local.

### Instalar el plugin

Descargue el paquete desde la entrada de Marketplace, cuya descarga está
limitada a usuarios con licencia, y copie sus ficheros al servidor Citrix:

- El script del plugin, `Pandora_Plugin_Citrix.ps1`.
- La lista de contadores, `counters.txt`.
- La lista de servicios, `services.txt`.

Colóquelos en cualquier carpeta que la cuenta del agente pueda leer,
normalmente la carpeta `util` de la instalación del agente, y mantenga las dos
listas junto al script: a lo largo de esta página, `<PATH_TO_CONFIG>` es esa
carpeta.

Las listas son ficheros de texto normales que usted edita. No las genera el
plugin y el plugin nunca escribe en ellas.

## Configuración

El plugin no tiene pantalla en la consola ni fichero de configuración propio.
Para ponerlo en marcha se añade una línea `module_plugin` a la configuración del
agente y se escriben las dos listas.

### Ejecutar el plugin desde el agente

Añada el plugin al fichero `pandora_agent.conf` del agente instalado en el
servidor Citrix. Basta una línea:

```text
module_plugin "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" -ExecutionPolicy Bypass -File <PATH_TO_CONFIG>\Pandora_Plugin_Citrix.ps1 -perf <PATH_TO_CONFIG>\counters.txt -serv <PATH_TO_CONFIG>\services.txt 2> <PATH_TO_CONFIG>\plugin_error.log
```

- `-File` debe ir seguido de la ruta absoluta del script del plugin.
- `-perf` recibe la ruta de la lista de contadores; `-serv` recibe la ruta de
  la lista de servicios.
- `-ExecutionPolicy Bypass` permite que este proceso ejecute el script sea cual
  sea la política de la máquina. Elimínelo cuando la política de la máquina ya
  permita el script; no tiene efecto cuando una directiva de grupo establece la
  política de ejecución.
- `2> <PATH_TO_CONFIG>\plugin_error.log` escribe los diagnósticos de la
  ejecución en un fichero, porque el agente solo lee la salida estándar. Sin
  esta redirección, la salida de error de PowerShell se pierde.

Reinicie o recargue el agente después de editar el fichero. El agente ejecuta el
plugin en cada intervalo e ingiere su salida como módulos del propio agente.

Las opciones del plugin son independientes, así que la misma línea cubre las
combinaciones admitidas:

| Línea de comandos | Módulos generados |
| --- | --- |
| Sin parámetros, o `-perf perfcounters` | Solo el resumen de uso; ningún módulo |
| `-perf <PATH>` | Contadores como `generic_data`, servicios, sesiones y usuarios |
| `-perf <PATH> -inc <cualquier valor distinto de incremental>` | Contadores como `generic_data_inc` **y** `generic_data`, servicios, sesiones y usuarios |
| `-perf none` | Servicios, sesiones y usuarios; ningún módulo de contador |
| `-serv none` | Contadores, sesiones y usuarios; ningún módulo de servicio |
| `-perf none -serv none` | Solo sesiones y usuarios |

`-perf` vale `perfcounters` por defecto, que es justo el valor que imprime el
resumen de uso. Ese valor por defecto es la razón de que la invocación sin
parámetros no genere ningún módulo: pase siempre la lista de contadores, o
`none`, de forma explícita.

### Escribir la lista de contadores

La lista de contadores contiene una ruta de contador de rendimiento por línea,
en la sintaxis `\Objeto(Instancia)\Contador` que acepta `Get-Counter`. Una línea
que nombra un objeto con varias instancias sin indicar instancia, o un objeto
que el servidor no tiene, no se puede muestrear: compruebe cada línea en el
servidor de destino.

La lista distribuida monitoriza procesador, memoria, archivo de paginación y
rendimiento de disco, además de Citrix Presentation Server, Citrix Licensing y
el servicio IMA. Consulte [Lista de contadores](#lista-de-contadores) para ver su
contenido exacto.

Dos propiedades del fichero importan en la práctica:

- **Espacios finales.** El fichero distribuido termina la mayoría de las líneas
  con un espacio. La ruta se pasa tal como se lee, así que elimine el espacio
  final cuando un contador no se recoja.
- **Nombres localizados.** Los nombres de contador siguen el idioma del sistema
  operativo. En un Windows que no esté en inglés las rutas distribuidas no
  resuelven; indique los nombres locales.

Para obtener los contadores que un servidor ofrece realmente:

```powershell
Get-Counter -ListSet * | Select-Object -ExpandProperty Paths > counters.txt
```

Ese fichero es un punto de partida: elimine los contadores que no necesite y
deje uno por línea.

### Escribir la lista de servicios

La lista de servicios contiene un **nombre de presentación** de servicio de
Windows por línea, como el que muestra la columna *Name* de la consola de
servicios, no el nombre corto del servicio. El plugin construye una consulta
WMI con la línea tal cual, así que el valor debe coincidir exactamente, sin
espacios finales y con las mayúsculas del nombre de presentación.

Una línea que no coincide con ningún servicio genera igualmente un módulo, con
valor `0`, de modo que una errata parece un servicio detenido. Consulte
[Lista de servicios](#lista-de-servicios) para ver las entradas distribuidas y
sus particularidades conocidas.

### Permisos y política de ejecución

- La cuenta del agente debe poder leer el script del plugin y los dos ficheros
  de lista, y ejecutar `powershell.exe`.
- La política de ejecución de PowerShell de la cuenta debe permitir el script.
  Normalmente se resuelve firmando el script, estableciendo una política que
  permita scripts locales o pasando `-ExecutionPolicy Bypass` en la invocación
  mostrada arriba.
- Ninguna fuente oficial de este addon documenta un rol concreto ni un conjunto
  de permisos más restrictivo. Conceda a la cuenta del agente solo lo que el
  plugin usa: leer el script y las dos listas, ejecutar `powershell.exe` y leer
  los contadores de rendimiento locales y los datos de servicios WMI locales.
- El plugin produce diagnósticos en la salida de error, y esos mensajes pueden
  incluir la ruta del script y de las listas: mantenga el fichero de errores
  legible solo por la cuenta del agente.

`counters.txt` y `services.txt` son texto plano y se pueden desplegar como
cualquier otro fichero de agente, por ejemplo con una colección de ficheros o
una política, de forma que las mismas listas lleguen a todos los servidores
Citrix sin editarlas uno a uno.

## Verificación

Ejecute el plugin manualmente en el servidor Citrix, desde una ventana de
PowerShell, antes de confiar en el agente:

```powershell
powershell.exe -ExecutionPolicy Bypass -File <PATH_TO_CONFIG>\Pandora_Plugin_Citrix.ps1 -perf <PATH_TO_CONFIG>\counters.txt -serv <PATH_TO_CONFIG>\services.txt
```

Una ejecución correcta imprime un bloque `<module>` por cada módulo generado en
la salida estándar y termina. El extracto siguiente muestra los dos últimos
bloques, el par que el plugin genera siempre:

```xml
<module>
<name><![CDATA[Citrix Sessions]]></name>
<type><![CDATA[generic_data]]></type>
<description><![CDATA[Opened active sessions on server]]></description>
<data><![CDATA[3]]></data>
</module>
<module>
<name><![CDATA[Users_Connected]]></name>
<type><![CDATA[generic_data]]></type>
<description><![CDATA[Users connected to this server]]></description>
<data><![CDATA[3]]></data>
</module>
```

`Citrix Sessions` y `Users_Connected` se generan en toda ejecución que genere
módulos, así que si no aparecen tampoco se generó nada más.

Para leer el resumen de uso, ejecute el script sin ningún parámetro:

```powershell
powershell.exe -ExecutionPolicy Bypass -File <PATH_TO_CONFIG>\Pandora_Plugin_Citrix.ps1
```

El plugin no tiene opción de ayuda: `-h` no es un parámetro del script y solo
produce un error de parámetros de PowerShell. El resumen es el comportamiento
por defecto del script, porque el valor inicial de `-perf` es `perfcounters`.

En Pandora FMS, abra el agente que ejecuta el plugin y confirme que la lista de
módulos de su último contacto contiene `Citrix Sessions`, `Users_Connected`, los
módulos `Status of service ...` y los módulos `PerfCounter ...`.

<!-- SCREENSHOT NEEDED: lista de módulos de un agente Citrix en la consola de Pandora FMS tras ejecutar el plugin, con los módulos Citrix Sessions, Users_Connected, Status of service y PerfCounter. -->

## Entender los resultados

El plugin genera el mismo catálogo de módulos en cada ejecución. Los cuatro
grupos responden a preguntas distintas y fallan de forma independiente:

- **Contadores.** Un módulo `generic_data` por cada muestra de contador,
  llamado `PerfCounter <ruta del contador>`. La ruta es la que devuelve el
  servidor, así que el nombre del módulo contiene el objeto, la instancia y, en
  muchos contadores, el nombre del servidor. Dos servidores nunca comparten
  esos nombres de módulo.
- **Servicios.** Un módulo `generic_proc` por cada línea de la lista de
  servicios, llamado `Status of service <nombre de presentación>`, con `1`
  cuando el estado extraído es exactamente `Running` y `0` en cualquier otro
  caso, incluido un servicio que no existe.
- **Sesiones.** `Citrix Sessions`, un módulo `generic_data` con el número de
  líneas de `query session` que contienen `Active`.
- **Usuarios.** `Users_Connected`, un módulo `generic_data` con el número de
  líneas de `quser` que contienen `Active`.

Ninguno de los dos recuentos elimina cuentas duplicadas: ambos cuentan líneas de
sesión activa, de dos comandos de Windows distintos, así que un usuario con dos
sesiones abiertas cuenta dos veces. Cuando uno de los comandos no está
disponible, el módulo correspondiente es el único indicio.

El grupo de contadores y el grupo de servicios son independientes entre sí y
también respecto al par de sesiones: un fichero de contadores que no se puede
leer deja vacío el grupo de contadores, un fichero de servicios que no se puede
leer deja vacío el grupo de servicios, y los módulos de sesión se siguen
generando.

Cuando se indica una lista de contadores, el tipo de módulo por defecto es
`generic_data`. El tipo `generic_data_inc` solo se añade cuando `-inc` recibe un
valor distinto de `incremental`, y se añade **además de** los módulos
absolutos, no en su lugar: ambos conjuntos se llaman
`PerfCounter <ruta del contador>` y leen el mismo fichero.

## Operar y resolver problemas

- Cada ejecución es independiente: el plugin muestrea el servidor, imprime los
  módulos y termina. No hay caché, ni estado, ni servicio que reiniciar.
- El plugin no tiene intervalo propio. El intervalo del agente en la línea
  `module_plugin` decide cada cuánto se ejecuta.
- No hay opción de detalle ni de depuración. El canal de diagnóstico es la
  salida de error, que la invocación de ejemplo redirige a
  `plugin_error.log`.
- El plugin redimensiona el búfer de consola al arrancar, así que espera un
  host con consola. Si una ejecución lanzada por el agente no produce nada
  mientras el mismo comando funciona en una ventana interactiva de PowerShell,
  esa diferencia es lo primero que hay que revisar.

| Síntoma | Causa y solución |
| --- | --- |
| La salida es el resumen de uso en lugar de módulos | `-perf` se quedó en su valor por defecto `perfcounters`, o se pasó `-perf perfcounters`. Pase la ruta de la lista de contadores, o `none`. |
| `A parameter cannot be found that matches parameter name 'h'` | El plugin no tiene `-h`. Ejecútelo sin parámetros para ver el resumen. |
| No aparece ningún módulo `PerfCounter` | No se pudo leer el fichero de contadores, o `Get-Counter` rechazó todas las rutas. Compruebe la ruta del fichero y después las rutas de [Lista de contadores](#lista-de-contadores) en ese servidor. |
| Faltan algunos contadores | Esas rutas no existen en ese servidor, nombran un contador localizado o necesitan una instancia como `(_Total)`. Compárelas con la salida de `Get-Counter -ListSet *`. |
| Un contador no se recoge y su línea termina en espacio | La ruta se pasa exactamente como está escrita. Elimine el espacio final. |
| Todos los servicios informan `0` | Los nombres de presentación no coinciden, o `grep`/`gawk` no están en el `PATH`. Compare una línea de la lista con el nombre de presentación que muestra la consola de servicios y compruebe que ambas herramientas resuelven. |
| `Get-Content : Cannot find path ...\services` | No se pasó `-serv`, así que el valor por defecto `services` se leyó como nombre de fichero. Pase la lista de servicios, o `-serv none` para omitir ese grupo. |
| `You cannot call a method on a null-valued expression` y la ejecución se detiene | Falta `wc`, así que el contador de sesiones no tiene valor al que aplicar el recorte. Añada `wc` al `PATH`. |
| `grep` o `gawk` no se reconoce | La herramienta no está disponible para la cuenta del agente. Instálela o añada su carpeta al `PATH` de esa cuenta. |
| El agente no crea módulos aunque la ejecución manual los imprime | Compruebe la ruta de `-File`, la política de ejecución de la cuenta del agente y el fichero de errores escrito por `2>`. |
| `... cannot be loaded because running scripts is disabled on this system` | La política de ejecución bloquea el script. Consulte [Permisos y política de ejecución](#permisos-y-politica-de-ejecucion). |
| Los nombres de módulo no son los de la lista | Los módulos de contador se llaman como la ruta que devuelve el servidor, que incluye el objeto, la instancia y el nombre del servidor. Es lo esperado. |

El plugin no establece un código de estado propio y no se detiene ante los
errores que produce: una ejecución que no puede leer un fichero de lista
informa el error en la salida de error y termina, de modo que el agente no
detecta el fallo. Revise `plugin_error.log` cuando un módulo deje de
actualizarse.

## Referencia

### Identidad del addon

| Propiedad | Valor |
| --- | --- |
| Identificador de Marketplace | `pandorafms.citrix_monitoring_plugin` |
| Nombre | Citrix monitoring plugin |
| Versión | `1.0` |
| Última actualización en Marketplace | 2025-07-29 |
| Categoría | Miscelaneus |
| Licencia | One; la descarga está limitada a usuarios con licencia |
| Paquete | `pandorafms.citrix_monitoring_plugin.1.0.zip` |
| Entrada de Marketplace | [pandorafms.citrix_monitoring_plugin](https://marketplace.pandorafms.com/entries/pandorafms.citrix_monitoring_plugin) |

El script imprime su propio rótulo de revisión, `v1.1, 02 Aug 2014`, cuando
muestra el resumen de uso. Esa cadena es interna del script y no es la versión
del paquete del addon, que es `1.0`.

### Parámetros de invocación

| Opción | Obligatoria | Por defecto | Descripción |
| --- | --- | --- | --- |
| `-perf` | No | `perfcounters` | Ruta de la lista de contadores. Cualquier valor distinto de `perfcounters` y `none` se lee como fichero. `none` omite el grupo de contadores. El valor por defecto `perfcounters` solo imprime el resumen de uso. |
| `-serv` | No | `services` | Ruta de la lista de servicios. Cualquier valor distinto de `none` se lee como fichero. `none` omite el grupo de servicios. El valor por defecto `services` es una palabra suelta, no una ruta, así que pase el fichero explícitamente. |
| `-inc` | No | `incremental` | Selector de modo, no una ruta. Con el valor por defecto `incremental` los módulos de contador son `generic_data`. Con cualquier otro valor el plugin emite además un módulo `generic_data_inc` por contador, leído del fichero de `-perf`, y los módulos `generic_data` se siguen emitiendo. |

Las opciones son parámetros de PowerShell: no distinguen mayúsculas de
minúsculas, cada una toma exactamente un valor y un nombre que el script no
define se rechaza antes de que empiece la ejecución. El script no define `-h`,
`-help` ni `-verbose`.

### Modos de ejecución

| Línea de comandos | Módulos de contador | Módulos de servicio | `Citrix Sessions` y `Users_Connected` |
| --- | --- | --- | --- |
| Sin parámetros | Ninguno (solo el resumen de uso) | Ninguno | Ninguno |
| `-perf perfcounters` | Ninguno (solo el resumen de uso) | Ninguno | Ninguno |
| `-perf <PATH>` | `generic_data` | Según `-serv` | Sí |
| `-perf <PATH> -inc <valor distinto de incremental>` | `generic_data_inc` y `generic_data` | Según `-serv` | Sí |
| `-perf none` | Ninguno | Según `-serv` | Sí |
| `-perf <PATH> -serv none` | `generic_data` | Ninguno | Sí |
| `-perf none -serv none` | Ninguno | Ninguno | Sí |

`Citrix Sessions` y `Users_Connected` se generan en toda ejecución que supere el
resumen de uso, sean cuales sean las opciones de contadores y de servicios.

### Lista de contadores

La lista siguiente es el contenido del fichero `counters.txt` distribuido, sin
el espacio final que termina cada línea en el fichero:

```text
\Processor(*)\% Processor Time
\System\Processor Queue Length
\Memory\Available Bytes
\Memory\Pages /sec
\Paging File\% Usage
\PhysicalDisk(_Total)\% Free Space
\LogicalDisk(_Total)\% Free Space
\LogicalDisk(_Total)\% Disk Time
\PhysicalDisk(_Total)\Current Disk Queue Length
\LogicalDisk(_Total)\Current Disk Queue Length
\LogicalDisk(_Total)\ Avg. Disk Sec/Read
\LogicalDisk(_Total)\ Avg. Disk Sec/Write
\LogicalDisk(_Total)\ Avg. Disk Sec/Transfer
\PhysicalDisk(_Total)\ Avg. Disk Sec/Read
\PhysicalDisk(_Total)\ Avg. Disk Sec/Write
\PhysicalDisk(_Total)\ Avg. Disk Sec/Transfer
\Citrix MetaFrame Presentation Server\Application Resolution Time (ms)
\Citrix MetaFrame Presentation Server\DataStore Connection Failure
\Citrix MetaFrame Presentation Server\Number of busy XML threads
\Citrix MetaFrame Presentation Server\Resolution WorkItem Queue Ready Count
\Citrix MetaFrame Presentation Server\WorkItem Queue Ready Count
\Citrix Licensing\Citrix Licensing - License Server Connection Failure
\Citrix Licensing\Citrix Licensing - Last Recorded License Check - Out Response Time
\Process(ImaSrv)\Private Bytes
```

Puntos que hay que comprobar en el servidor de destino:

- `\Processor(*)` genera un módulo por instancia de procesador.
- `\Paging File\% Usage` nombra un objeto con varias instancias sin indicar
  instancia; el servidor la expone como `\Paging File(_Total)\% Usage`.
- `\Memory\Pages /sec` contiene un espacio en el nombre del contador; el
  contador de Windows es `\Memory\Pages/sec`.
- `\PhysicalDisk(_Total)\% Free Space` nombra un contador de discos lógicos; los
  discos físicos no exponen `% Free Space`.
- Las seis líneas `Avg. Disk Sec/...` contienen un espacio entre la barra
  inversa y el nombre del contador. Elimínelo cuando el contador no se recoja.
- Todas las líneas del fichero distribuido terminan en un espacio. La ruta se
  pasa tal como se lee, así que recorte la línea cuando el contador no se
  recoja.
- Los conjuntos `Citrix MetaFrame Presentation Server` y `Citrix Licensing`
  existen solo donde está instalado ese componente de Citrix.
- Todas las rutas usan nombres de contador en inglés.

### Lista de servicios

La lista siguiente es el contenido del fichero `services.txt` distribuido:

```text
Citrix Independent Management Architecture
Citrix XML
Citrix XTE Server
Citrix CPU Utilization Management/Resource Management
Citrix CPU Utilization Management/User Session sync
Citrix CPU Utilization Management/CPU Rebalancer Estados Servicios
Citrix Print Manager
Citrix Virtual Memory Optimization
Citrix MF COM
Remote Desktop Services/Terminal Services
Citrix WMI
Citrix Client Network
Citrix Streaming/Citrix Streaming Helper
Server
Netlogon
Remote Procedure Call (RPC)
Workstation
Print Spooler
```

Puntos que hay que comprobar en el servidor de destino:

- Las entradas son **nombres de presentación**. `ImaSrv`, por ejemplo, es el
  nombre corto de `Citrix Independent Management Architecture`.
- Varias líneas del fichero distribuido terminan en un espacio, y el valor se
  usa tal cual: recorte la línea cuando el servicio informe `0` aunque esté en
  ejecución.
- La sexta entrada termina con `Estados Servicios`, que no sigue el patrón de
  un nombre de presentación de Windows. Se usa tal cual, así que sustitúyala
  por el nombre de presentación exacto de ese servicio en su servidor.
- `Server`, `Workstation`, `Netlogon`, `Print Spooler` y
  `Remote Procedure Call (RPC)` son servicios del sistema operativo. Se
  monitorizan con el mismo mecanismo que los de Citrix.
- La lista es un valor por defecto, no un límite: cualquier nombre de
  presentación que añada se convierte en un módulo.

### Módulos generados

| Nombre del módulo | Tipo | Valor |
| --- | --- | --- |
| `PerfCounter <ruta del contador>` | `generic_data`, o `generic_data_inc` para el conjunto incremental | El valor muestreado de ese contador |
| `Status of service <nombre de presentación>` | `generic_proc` | `1` cuando el estado extraído es `Running`, `0` en caso contrario |
| `Citrix Sessions` | `generic_data` | Número de líneas de `query session` que contienen `Active` |
| `Users_Connected` | `generic_data` | Número de líneas de `quser` que contienen `Active` |

Cada módulo se escribe como un bloque `<module>` con los elementos `name`,
`type`, `description` y `data`, y sin elemento `<agent>`: los módulos
pertenecen al agente que ejecuta el plugin.

### Salida y código de estado

| Condición | Comportamiento |
| --- | --- |
| Ejecución normal | Bloques `<module>` en la salida estándar; el proceso termina con estado `0` |
| Ruta del resumen de uso | El rótulo, la lista de parámetros y el ejemplo de uso en la salida estándar; ningún módulo |
| Lista de contadores ilegible o contadores rechazados | Error de PowerShell en la salida de error, ningún módulo de contador, el resto de la ejecución continúa |
| Lista de servicios ilegible | Error de PowerShell en la salida de error, ningún módulo de servicio, el resto de la ejecución continúa |
| Falta `grep` o `gawk` | Cada servicio informa `0`; el error aparece en la salida de error |
| Falta `wc` | La ejecución se detiene en el recuento de sesiones con `You cannot call a method on a null-valued expression` |
| Parámetro no definido | La ejecución termina antes de generar módulos, con el error de parámetros de PowerShell en la salida de error |

El script nunca llama a `exit`. Una ejecución que solo produce errores en la
salida de error termina igualmente con éxito, y por eso la invocación redirige
la salida de error a un fichero.
