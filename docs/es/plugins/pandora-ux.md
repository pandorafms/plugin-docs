# Pandora UX

*Última actualización del artículo: 2026-10-26.*

## Qué hace

Pandora UX reproduce una comprobación grabada, la cronometra y comunica el
resultado a Pandora FMS junto con una captura de la pantalla o de la página en
el momento del fallo. La comprobación es una sesión web ejecutada a través de un
servidor Selenium, una sesión de escritorio reproducida en la máquina que
ejecuta el plugin, o un guion de automatización que ya tenga.

Cada ejecución convierte el resultado en módulos de Pandora FMS: un módulo de
estado por comprobación y fase, un módulo de latencia por comprobación y fase, y
un módulo de imagen cuando una comprobación falla. Las comprobaciones de
escritorio guardan además una imagen de referencia del resultado correcto y
comparan con ella cada ejecución.

El modo de ejecución lo elige el valor de `-exe`, que se busca como subcadena
sin distinguir mayúsculas:

| Valor de `-exe` | Modo | Qué se reproduce |
| --- | --- | --- |
| `PWR` | Comprobaciones web | Una suite de Selenium IDE, en formato `.side` o en el formato heredado `.html` |
| `goliat` | Comprobaciones web con Pandora Webserver | Un archivo de tareas de Goliat. Solo Linux |
| `stats` | Rendimiento web | Una o varias URL cronometradas con `curl` |
| Cualquier otro valor | Escritorio o automatización de terceros | Un proyecto SikuliX a través de `pdr.cmd`, o cualquier ejecutable con `-args` |

Como el modo se elige por subcadena, una utilidad cuya ruta contenga `pwr`,
`goliat` o `stats` selecciona el modo interno en lugar de ejecutar su binario.

El plugin entrega sus módulos de dos formas:

- **Modo plugin de agente** (por defecto): imprime el XML de los módulos en la
  salida estándar y el agente de Pandora FMS del equipo los ingiere.
- **Modo plugin de servidor** (`-agent <nombre>`): construye un documento
  `agent_data` y lo entrega mediante Tentacle o una carpeta de datos local.

El addon no tiene tarea de Discovery: se ejecuta desde un terminal, desde el
agente de Pandora FMS o como plugin de servidor registrado.

## Preparación

### Compatibilidad

| Alcance | Estado | Evidencia |
| --- | --- | --- |
| Addon `pandorafms.pandora_ux`, versión `1.0` | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del addon](#identidad-del-addon) |
| Un servidor Selenium accesible desde el equipo, para las comprobaciones web | `Requerido` | Las comprobaciones web abren una sesión contra `-pwr_host`:`-pwr_port`, `localhost:4444` por defecto |
| Versiones de servidor Selenium 3 | `Sin validar` | El cliente informa como incompatible un servidor Selenium 3 anterior a 3.14 cuando no puede crear una sesión; no hay matriz de versiones registrada para este addon |
| Un entorno de ejecución de Java en el equipo, para `PDR` y para el servidor PWR | `Requerido` | `pdr.cmd` usa `JAVA_HOME`, después el `java` de la ruta y después las carpetas estándar de Java; el readme de PWR pide Java 8 |
| `curl` en el `PATH`, para el modo `stats` | `Requerido` | El plugin lo comprueba al construir su ayuda y lo usa para cronometrar cada URL |
| El componente Goliat de Pandora FMS, para el modo `goliat` | `Requerido` | El modo Goliat carga sus bibliotecas y se detiene si no están |
| Una sesión de escritorio interactiva y desbloqueada, para las comprobaciones de escritorio | `Requerido` | La comprobación captura el escritorio de la sesión que ejecuta el plugin |
| Sistemas operativos | `Sin validar` | La ayuda del plugin limita PWR a Windows y Linux, PDR a Windows y Goliat a Linux; no hay registro de pruebas para esta versión |
| Herramientas de automatización de terceros usadas con `-exe` | `Sin validar` | Se acepta cualquier ejecutable; no hay ninguna herramienta registrada como validada |
| Versiones concretas de Pandora FMS | `Sin validar` | El aviso del Marketplace es general para todas sus integraciones, no una declaración de este addon |

### Requisitos

1. **Pandora FMS** para recibir los módulos: el agente instalado en el equipo
   en modo plugin de agente, o un servidor de Pandora FMS en modo plugin de
   servidor.
2. **El paquete del addon**: el ejecutable `pandora_ux_x64.exe`, además del
   paquete del servidor PWR y del lanzador PDR cuando use esos modos.
3. **Para las comprobaciones web**: un servidor Selenium que el equipo pueda
   alcanzar, un entorno de ejecución de Java para ese servidor y un navegador
   que pueda arrancar.
4. **Para las comprobaciones de escritorio**: un equipo Windows, un entorno de
   ejecución de Java y SikuliX. El lanzador PDR del paquete proporciona el punto
   de entrada de SikuliX.
5. **Una sesión de escritorio interactiva** en el equipo que ejecuta las
   comprobaciones de escritorio.
6. **`curl` en el equipo** cuando use el modo `stats`.
7. **Goliat**, de Pandora FMS, cuando use el modo `goliat`.

El plugin no guarda credenciales propias. En modo plugin de agente necesita
permiso de lectura sobre los guiones y de escritura sobre la carpeta de
capturas; en modo plugin de servidor escribe el archivo `agent_data` en una
carpeta temporal y después lo entrega. Ejecútelo con el usuario cuyo escritorio
se comprueba, para que la sesión de escritorio y la captura pertenezcan al mismo
usuario.

### Instalar el addon

Descargue el paquete desde la entrada del Marketplace de Pandora FMS, limitada a
usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.pandora_ux](https://marketplace.pandorafms.com/entries/pandorafms.pandora_ux)

Descomprímalo en el equipo que vaya a ejecutar las comprobaciones. El ejecutable
es `pandora_ux_x64.exe`. El paquete proporciona también el conjunto del servidor
PWR y el lanzador PDR; prepárelos como se describe a continuación cuando use
esos modos.

### Preparar el servidor PWR

Las comprobaciones web necesitan un servidor Selenium, en el mismo equipo o en
otro al que el plugin pueda llegar. El servidor no tiene que compartir máquina
con el plugin: `-pwr_host` y `-pwr_port` apuntan a él. En Windows el paquete
incluye un conjunto del servidor PWR; el readme que se distribuye con el addon
documenta esta secuencia:

1. Instale un entorno de ejecución de Java 8.
2. Prepare el perfil de Firefox que usará el servidor.
3. Descomprima `PWR_Server.zip` en `C:\PWR`.
4. Ejecute `C:\PWR\server\service_installer.bat` como administrador.
5. Arranque el servicio con `net start PWRSRV`.

El instalador registra un servicio de Windows llamado `PWRSRV` que ejecuta el
servidor Selenium con el perfil de Firefox de `C:\PWR\profile`. Usa el envoltorio
de servicio de 64 bits del paquete y el `java` que encuentra en el `PATH`, así
que necesita un Windows de 64 bits y un entorno de Java en la ruta de la cuenta
que lo ejecuta. El readme también documenta cómo arrancar el servidor en primer
plano, en el puerto `4444`, en lugar de instalarlo como servicio.

### Preparar un equipo de escritorio

Las comprobaciones de escritorio reproducen una sesión que interactúa con el
escritorio real, así que se ejecutan en Windows, en una sesión interactiva:

1. Instale un entorno de ejecución de Java. `pdr.cmd` usa `JAVA_HOME` cuando
   está definido y es utilizable, después el `java` de la ruta y, por último,
   `Program Files\Java\jre8`, `jre7` y `jre6`, incluida la carpeta de programas
   de 32 bits. Cuando no encuentra ninguno imprime
   `Java not found in standard places` y se detiene.
2. Copie la carpeta `PDR` del paquete en `C:\PDR`. Contiene `pdr.cmd` y el punto
   de entrada de SikuliX que ejecuta el lanzador.
3. Apunte `-exe` a `C:\PDR\pdr.cmd` y pase `-args -r`, para que el lanzador
   reproduzca el proyecto indicado en `-script`.

La sesión de escritorio debe permanecer desbloqueada y en primer plano: una
sesión bloqueada, una sesión de escritorio remoto desconectada o una máquina sin
usuario con la sesión iniciada no tienen escritorio que capturar, y la
comprobación falla.

## Configuración

### Modos de ejecución

Dos decisiones definen una ejecución: cómo entrega el plugin sus módulos y qué
comprobaciones ejecuta.

| Modo | Se selecciona con | Módulos en la salida estándar |
| --- | --- | --- |
| Plugin de agente | Ningún valor en `-agent` | El XML de los módulos, listo para el agente de Pandora FMS |
| Plugin de servidor | `-agent <nombre>` | Una línea con el estado global, `1` o `0`, después de entregar el agente |

La línea de comandos mínima para una comprobación web es el modo, el servidor
Selenium y la suite:

```bash
pandora_ux_x64.exe -exe PWR -script C:\pandora_ux\tests\std.side
```

Pase cada argumento como un par `-opción valor`. El analizador lee la línea de
comandos como pares consecutivos, así que `-opción=valor` se interpreta como una
opción llamada `opción=valor`, y una opción sin valor al final se ignora.

### Guiones y fases de PWR

En modo web, `-script` acepta una o varias suites de Selenium IDE separadas por
comas. Cada suite se ejecuta en secuencia y produce su propio conjunto de
módulos; un fallo dentro de una suite detiene los comandos restantes de esa
suite, pero no las suites siguientes.

Las fases salen de la propia suite. Añada un comentario a la suite de Selenium
IDE para abrirlas y cerrarlas:

```text
phase_start:Login
... comandos grabados ...
phase_end:Login
```

Cada fase entre los marcadores se cronometra y se informa por separado. Una
suite sin marcadores produce un único resultado para toda la suite.

Otros dos comentarios publican módulos adicionales de la página:

```text
getValue;Cart total;generic_data;([0-9.]+) items
getScreenshot;Cart page
```

`getValue` lee el código fuente de la página y publica la primera captura de la
expresión regular como un módulo con el nombre y el tipo indicados.
`getScreenshot` captura la página completa y la publica como módulo de imagen.
Ambos se ejecutan solo mientras la suite sigue teniendo éxito.

Hay dos clientes que pueden hablar con el servidor Selenium:

- El cliente WebDriver, que se usa por defecto, maneja servidores Selenium 2 y
  Selenium 3 y acepta tanto el formato `.side` como el heredado `.html`. Contra
  un servidor Selenium 2 solo admite Firefox; Chrome, Internet Explorer y Edge
  necesitan un servidor Selenium 3. En esta ruta el contenido del comentario se
  parte por `:` y `;`, así que no use esos dos caracteres en una expresión de
  `getValue`.
- `-pwr_classic 1` usa el cliente heredado de Selenium 2 RC. Necesita un
  servidor Selenium 2 y el formato heredado `.html`.

Con Selenium 3, indique el navegador sin prefijo (`firefox`, `chrome`): el `*`
inicial del valor por defecto se elimina solo para Firefox. Chrome admite
además `-user_data_dir` y `-profile_folder`, y `-accept_insecure_certs` acepta
cualquier certificado TLS que presente el sitio comprobado.

### Comprobaciones de escritorio e imágenes de referencia

En modo escritorio `-script` acepta uno o varios proyectos SikuliX o
ejecutables, separados por comas, y `-folder` es la carpeta donde el plugin
guarda sus imágenes. La carpeta debe existir ya y terminar en el separador de
ruta, porque el plugin añade el nombre del archivo directamente.

Para cada fase el plugin trabaja con tres archivos en esa carpeta:

| Archivo | Función |
| --- | --- |
| `screenshot_<fase>.png` | Imagen de resultado de la ejecución. Si la escribe su herramienta de automatización, el plugin la usa en lugar de capturar la pantalla |
| `ctrl_screenshot_<fase>.png` | Imagen de referencia del resultado correcto |
| `err_screenshot_<fase>.png` | Copia de la imagen de resultado de una ejecución fallida |

La primera ejecución de una fase, o cualquier ejecución con `-checkpoint`,
reconstruye la imagen de referencia a partir de la imagen de resultado y la
publica como módulo `UX_Control_Snapshot`. Las ejecuciones posteriores comparan
el resultado con la referencia y fallan cuando difieren en más de
`-max_differences`, que es un porcentaje de caracteres distintos de la imagen
codificada (`0.5` por defecto). Como la comparación trabaja sobre la imagen
codificada, un cambio de un solo píxel suele cambiar todos los caracteres
siguientes, así que trate el valor por defecto como una coincidencia casi exacta
y refresque la referencia con `-checkpoint` cuando cambie el resultado esperado.

`-ss_config` elige qué se captura: `active` captura la ventana activa en
Windows; cualquier otro valor, incluida una lista de coordenadas como
`0,0,100,100`, recurre a la pantalla completa.

La herramienta externa se ejecuta como `"<utilidad>" <args> <script>`, así que
la ruta de la utilidad va entre comillas pero `-args` y la ruta del guion no:
mantenga la ruta del guion sin espacios. Si la herramienta ya escribió
`screenshot_<fase>.png`, esa imagen es el resultado de la ejecución.

`-k` resulta útil con archivos por lotes y de comandos, que siempre informan de
código de salida 0: con `-k 1` solo decide el código de salida del proceso; sin
él, un código de salida 0 con `[error]` en la salida de la herramienta también
cuenta como fallo.

### Macros

`-s nombre=valor` sustituye cada `_nombre_` del guion antes de ejecutarlo:

```bash
pandora_ux_x64.exe -exe PWR -script C:\pandora_ux\tests\std.side -s today=now+1 -f "%Y%m%d"
```

`now`, `now+<días>` y `now-<días>` producen una fecha con el formato de `-f`, que
por defecto es `%Y%m%d`. El plugin copia el guion en una carpeta temporal, aplica
allí la sustitución, ejecuta la copia y elimina la carpeta después. Su guion
original nunca se modifica.

La línea de comandos admite un valor de `-s` por ejecución: un segundo `-s`
sustituye al primero, y lo mismo ocurre con un segundo `-f`. Para un proyecto
SikuliX la sustitución necesita además el soporte de copia recursiva del entorno
de ejecución; cuando falta, el plugin termina con estado 1 antes de ejecutar la
comprobación, y el motivo solo se imprime con `-debug 1`.

### Modo plugin de agente

Añada el plugin a la configuración del agente de Pandora FMS, o a la
configuración remota del agente en la consola, como una línea `module_plugin`:

```text
module_plugin C:\pandora_ux\pandora_ux_x64.exe -exe C:\PDR\pdr.cmd -args -r -script C:\PDR\checkout.sikuli -folder C:\PDR\ -checkpoint
```

El agente ejecuta el plugin en su propio intervalo e ingiere los módulos que
imprime. Los módulos generados llevan el grupo `UX` y ninguna etiqueta salvo que
configure `-g` y `-tag_list`.

### Modo plugin de servidor

`-agent <nombre>` cambia el plugin al modo plugin de servidor. Crea un agente con
ese nombre, guarda los módulos bajo él y entrega el documento según `-mode`:

| `-mode` | Comportamiento |
| --- | --- |
| `local` (por defecto) | Copia el archivo `agent_data` en `-local_folder` |
| `tentacle` | Lo envía con el cliente de Tentacle a `-tentacle_ip`:`-tentacle_port` |

Para ejecutarlo desde la consola, regístrelo como plugin de servidor:

1. Abra **Servers → Plugins** y haga clic en **Register Plugin**.
2. Indique un nombre, el tipo de plugin **Standard**, un tiempo máximo opcional y
   una descripción.
3. En **Plugin command**, escriba la ruta de `pandora_ux_x64.exe` en el servidor
   de Pandora FMS.
4. En **Plugin parameters**, use las macros del plugin `_field1_`, `_field2_`, ...
   para los valores que cambian entre módulos:

```text
-exe PWR -script _field1_ -pwr_host _field2_ -pwr_port _field3_ -agent _field4_ -mode local -local_folder /var/spool/pandora/data_in
```

<!-- SCREENSHOT NEEDED: formulario de registro de Servers → Plugins para Pandora UX, con el comando del plugin, su línea de parámetros y los campos de macro. -->

5. En **Macro parameters**, describa cada campo. El ejemplo usa estos valores:

| Campo | Descripción | Valor de ejemplo |
| --- | --- | --- |
| `_field1_` | Ruta de la suite de Selenium en el servidor de Pandora FMS | `/opt/pandora_ux/tests/std.side` |
| `_field2_` | Host del servidor Selenium | `<TARGET_HOST>` |
| `_field3_` | Puerto del servidor Selenium | `4444` |
| `_field4_` | Nombre del agente que guardará los módulos | `Pandora UX checkout` |

<!-- SCREENSHOT NEEDED: formulario de creación de un módulo de plugin con el plugin Pandora UX seleccionado y sus parámetros _field1_..._field4_ rellenos. -->

Una vez registrado, cree un **módulo de servidor de complementos** en un agente,
elija el plugin Pandora UX y rellene sus campos. Cada ejecución del módulo lanza
una ejecución en el servidor seleccionado para el módulo, así que el servidor
Selenium debe ser accesible desde ese servidor de Pandora FMS.

El modo plugin de servidor está pensado para comprobaciones que pueden
ejecutarse sin escritorio. Las comprobaciones de escritorio necesitan la sesión
interactiva del usuario monitorizado, así que normalmente se ejecutan como
plugin de agente en el propio equipo.

### Correo en caso de fallo

Configurar `-to` hace que el plugin envíe un mensaje cuando falla una fase.
`-from`, `-subject` y `-content` establecen el remitente, el asunto y el cuerpo;
el asunto es por defecto `Pandora UX test failed: ` seguido del nombre de la
fase. `-smtp_gw` y `-smtp_port` apuntan a un relay SMTP (`127.0.0.1` y `25` por
defecto).

El mensaje no tiene autenticación ni opciones de TLS: use un relay que acepte el
equipo. Cuando la fase fallida tiene un archivo de imagen, el plugin lo adjunta;
las comprobaciones web no informan de ningún archivo, así que su mensaje lleva
solo el contenido configurado.

## Verificación

### Ejecución manual

Ejecute el plugin desde un terminal con los mismos argumentos que va a
programar. Una comprobación web con Selenium en el mismo equipo:

```bash
pandora_ux_x64.exe -exe PWR -script C:\pandora_ux\tests\std.side -debug 1
```

La ejecución se realiza una vez y termina. El XML de los módulos va a la salida
estándar; use `-debug 1` para ver en la salida de error los mensajes de progreso,
incluido qué modo se está ejecutando y el resultado del comando posterior. `-v`
se acepta pero no cambia la salida.

Una ejecución web correcta de una sola fase imprime los módulos de estado y de
tiempo. Las descripciones que siguen son las del cliente WebDriver por defecto,
que escribe `<fase> OK`; el cliente heredado escribe `Test OK`.

```xml
<module>
	<name><![CDATA[UX_Status_std.side]]></name>
	<type>generic_proc</type>
	<data><![CDATA[1]]></data>
	<description><![CDATA[std.side OK]]></description>
	<module_group>UX</module_group>
</module>
<module>
	<name><![CDATA[UX_Time_std.side]]></name>
	<type>generic_data</type>
	<data><![CDATA[16.317]]></data>
	<description><![CDATA[std.side OK]]></description>
	<module_group>UX</module_group>
	<module_parent>UX_Status_std.side</module_parent>
</module>
```

Una ejecución fallida informa de `0` en el módulo de estado, el texto del error
en la descripción y añade un módulo de imagen con la captura del fallo:

```xml
<module>
	<name><![CDATA[UX_Snapshot_std.side]]></name>
	<type>async_string</type>
	<data><![CDATA[data:image/png;base64, iVBORw0KGgoAAAANSUhEUg...]]></data>
	<description><![CDATA[Image (last error)]]></description>
</module>
```

En modo plugin de servidor la ejecución no imprime nada más: la última línea es
el estado global, `1` o `0`, y el agente aparece en Pandora FMS con sus módulos.

### En la consola

Con el plugin de agente configurado, los módulos aparecen en el agente del
equipo en su siguiente intervalo. Como los nombres no llevan prefijo de equipo
ni de instancia, un agente por máquina mantiene legible el árbol de módulos, y
los módulos `UX_Status` son los que conviene usar para alertar.

<!-- SCREENSHOT NEEDED: lista de módulos de un agente con un módulo UX_Status y sus hijos UX_Time, y el módulo de captura de una ejecución fallida. -->

## Entender los resultados

### Estado, tiempo e imágenes

Las tres familias significan lo mismo en las comprobaciones web y de escritorio:

- `UX_Status_*` es `generic_proc`: `1` cuando la comprobación o la fase tuvo
  éxito, `0` cuando falló.
- `UX_Time_*` es `generic_data`: la duración en segundos.
- `UX_Snapshot_*` y `UX_Control_Snapshot_*` son módulos `async_string` cuyo valor
  es un URI `data:image/png;base64,` del PNG.

La descripción de un módulo de estado o de tiempo lleva el resultado:
`<fase> OK` (`Test OK` con el cliente heredado), el error del comando de
Selenium o la salida de la herramienta de automatización.

<!-- SCREENSHOT NEEDED: detalle de un módulo UX_Snapshot con la imagen capturada del fallo. -->

### Nombres de transacción y de fase

Cuando existe un nombre de transacción, el plugin informa además de la
transacción completa y etiqueta cada fase con su posición. El nombre de
transacción procede de `-t`, o se toma del nombre de la suite cuando una suite
web define más de una fase. La etiqueta cuenta desde `0` y dice `Phase <n>: `,
así que forma parte del nombre del módulo:

| Ejecución | Nombres de módulo |
| --- | --- |
| Comprobación web, una suite, sin marcadores de fase y sin `-t` | `UX_Status_<suite>`, `UX_Time_<suite>` |
| Comprobación web con marcadores de fase o con `-t` | `UX_Status_Phase <n>: <transacción>.<fase>`, `UX_Time_Phase <n>: <transacción>.<fase>`, más `UX_Global_Status_<transacción>`, `UX_Global_Time_<transacción>` y, si falla, `UX_Global_Snapshot_<transacción>` |
| Comprobación de escritorio sin `-t` | `UX_Status_<fase>`, `UX_Time_<fase>`, `UX_Control_Snapshot_<fase>` y, si falla, `UX_Snapshot_<fase>` |
| Comprobación de escritorio con `-t` | `UX_Status_Phase <n>: <fase>`, `UX_Time_Phase <n>: <fase>`, las imágenes de fase y los módulos `UX_Global_*` |

`<transacción>` es el valor de `-t` o, en una suite web sin `-t`, el nombre de la
suite. `<fase>` es el marcador de fase de la suite en las comprobaciones web, y
el valor de `-name` para esa posición o el nombre base del guion en las
comprobaciones de escritorio.

De la numeración se derivan dos detalles: el resumen global web se enumera antes
que las fases en la ruta WebDriver, así que la primera fase se informa como
`Phase 1: `; el cliente heredado lo enumera al final, así que su numeración
empieza en `0`. Y el prefijo de transacción queda dentro del nombre de la fase,
que es la razón de que una fase web aparezca como `Phase 1: std.side.Login`
cuando la suite es `std.side` y el marcador es `Login`.

`UX_Global_Status_<transacción>` vale `1` solo cuando todas las fases tuvieron
éxito, y su descripción es la lista de resultados de las fases.
`UX_Global_Time_<transacción>` es la duración total: el tiempo real de la
ejecución web, o la suma de las duraciones de las fases en modo escritorio. Con
`-pwr_override_global_phase_time 1` una ejecución web usa también la suma de las
fases, y `-pwr_phases_time 1` añade un módulo aparte
`UX_Phases_Time_<transacción>` con esa suma.

### Resultados de stats y Goliat

`stats` informa de los tiempos de una URL sin navegador. Para cada URL la
etiqueta es el valor de `-name` para esa posición; sin `-name` es el último
segmento de ruta de la URL, o la URL completa cuando ese segmento está vacío.
Los módulos son `<etiqueta>_Global_Status` (`generic_proc`) y
`<etiqueta>_UX_Stats_TT`, `_DNS`, `_TTCP`, `_TST` y `_TTC` (`generic_data`, en
milisegundos), más `_TSSL` para una URL `https`. `Global_Status` vale `1` solo
cuando `curl` devolvió el código de salida 0; en caso contrario la descripción
indica el error de `curl`.

`goliat` informa de un módulo `UX_Status_<tarea>` y otro `UX_Time_<tarea>` por
cada bloque `task_begin` del archivo de tareas, con la duración que Goliat midió
para esa tarea. No publica módulos de imagen.

## Operación y solución de problemas

### Reintentos y comando posterior

`-retries` establece cuántas veces se intenta la transacción completa; por
defecto es un intento. Un intento fallido se repite entero, con todas las fases,
no fase por fase, y el intento siguiente empieza por el primer guion. Los
reintentos se aplican a las comprobaciones web y de escritorio; las ejecuciones
`stats` y `goliat` se realizan una sola vez.

`-post` ejecuta un comando una vez, después de generar los módulos, sea cual sea
el resultado de la comprobación. Úselo para cerrar lo que la comprobación abrió:

```text
-post "taskkill /F /IM calc.exe"
```

No se ejecuta en el modo `stats`, que termina antes de la fase de informe.

### Operación de un equipo de escritorio

- Mantenga el agente ejecutándose dentro de la sesión interactiva del usuario
  monitorizado, con el escritorio desbloqueado. Una máquina en la pantalla de
  inicio de sesión no tiene escritorio que capturar.
- Arranque el agente automáticamente al iniciar el equipo, para que un reinicio
  no deje las comprobaciones detenidas hasta que alguien inicie sesión.
- Restablezca una imagen de referencia borrando `ctrl_screenshot_<fase>.png`, o
  ejecutando la comprobación una vez con `-checkpoint` cuando cambie el
  resultado esperado.
- Mantenga `-folder` en un disco local: el plugin escribe y vuelve a leer las
  imágenes allí en cada ejecución.

### Fallos habituales

- **El plugin imprime su lista de parámetros y termina con estado 1** — no hay
  ningún argumento, solo `-h`, o falta `-exe` o `-script`. El mensaje menciona
  `Missing <script> in arguments` incluso cuando el valor que falta es `-exe`;
  compruebe ambos.
- **Una ejecución web informa de `0` en todos los módulos de estado con un error
  de conexión en la descripción** — el servidor Selenium no es accesible o no
  está listo. Compruebe `-pwr_host` y `-pwr_port`, el servicio del servidor
  (`net start PWRSRV` en Windows) y el cortafuegos entre el equipo y el servidor.
- **Una ejecución web no publica nada y termina con estado 0** — la ejecución
  llevaba `-exit_on_fail 1` y no pudo llegar al servidor Selenium. La opción hace
  que el plugin abandone la ejecución en lugar de publicar un estado fallido, así
  que úsela solo donde un planificador externo vigile el código de salida.
- **Una ejecución de escritorio informa de `Control image not found, please
  check directory permissions`** — la carpeta de `-folder` no existe, no termina
  en el separador de ruta o el usuario que ejecuta el plugin no puede escribir en
  ella.
- **Una ejecución de escritorio falla con `Error: Snapshot doesn't match the
  control one` en una comprobación que funciona** — la imagen de referencia ya no
  coincide con la pantalla esperada. Revise la imagen en el módulo `UX_Snapshot`
  y refresque la referencia con `-checkpoint`.
- **`Java not found in standard places` al arrancar una ejecución PDR** — no hay
  `JAVA_HOME`, ni un `java` en la ruta, ni un entorno de ejecución en las carpetas
  estándar de Java. Instale un entorno de Java o configure `JAVA_HOME`.
- **No aparece ningún mensaje de progreso en la salida de error** — el plugin
  escribe sus mensajes solo con `-debug 1`. `-v` se acepta por compatibilidad y
  no cambia nada.
- **El plugin se detiene con `Goliat libraries not found`** o con un mensaje
  sobre el cliente Selenium 2 RC — el componente opcional de ese modo no está
  disponible en el equipo. Use la ruta WebDriver o instale el componente que
  falta.
- **No llega correo en caso de fallo** — no se ha configurado `-to`, el relay
  SMTP de `-smtp_gw`:`-smtp_port` rechaza el equipo, o el fallo ocurrió antes de
  la fase de informe (un error de configuración, por ejemplo).

## Referencia

### Parámetros de ejecución

| Nombre | Obligatorio | Valor por defecto | Descripción |
| --- | --- | --- | --- |
| `-exe` | Sí | — | Utilidad de automatización, o el modo interno `PDR`, `PWR`, `stats` o `goliat`. El valor se busca como subcadena sin distinguir mayúsculas |
| `-args` | No | Vacío | Argumentos que se pasan a la utilidad externa antes de la ruta del guion |
| `-script` | Sí | — | Lista separada por comas de suites, proyectos, ejecutables o URL, uno por fase |
| `-name` | No | Nombre base del guion | Nombres separados por comas que coinciden con `-script` posición por posición, usados en los nombres de módulo y, en el modo `stats`, como prefijo de los módulos |
| `-folder` | No | `%TEMP%\` en Windows, `/tmp/` en el resto | Carpeta de las imágenes de resultado, referencia y error de las comprobaciones de escritorio. Debe terminar en el separador de ruta. No se usa en las comprobaciones web |
| `-retries` | No | `1` | Número de intentos de la transacción completa, en los modos web y de escritorio |
| `-t` | No | — | Nombre de transacción. Activa los módulos `UX_Global_*` y la etiqueta `Phase <n>: ` |
| `-k` | No | `0` | `1` usa solo el código de salida del proceso; por defecto, un código de salida 0 con `[error]` en la salida también falla |
| `-post` | No | — | Comando que se ejecuta una vez después de generar los módulos. No se ejecuta en el modo `stats` |
| `-debug` | No | `0` | `1` imprime mensajes de progreso y detalle de Selenium en la salida de error |
| `-v` | No | `0` | Se acepta por compatibilidad. No cambia la salida; use `-debug 1` |

### Parámetros de PWR

| Nombre | Obligatorio | Valor por defecto | Descripción |
| --- | --- | --- | --- |
| `-pwr_host` | No | `localhost` | Host del servidor Selenium |
| `-pwr_port` | No | `4444` | Puerto del servidor Selenium |
| `-pwr_browser` | No | `*firefox` | Navegador que arranca el servidor Selenium. Con Selenium 3 use el nombre sin prefijo (`firefox`, `chrome`) |
| `-pwr_classic` | No | `0` | `1` usa el cliente heredado de Selenium 2 RC y el formato heredado `.html` |
| `-pwr_phases_time` | No | `0` | `1` añade `UX_Phases_Time_<transacción>`. Requiere un nombre de transacción |
| `-pwr_override_global_phase_time` | No | Sin definir | `1` sustituye el módulo de tiempo global por la suma de los tiempos de fase. Requiere un nombre de transacción |
| `-accept_insecure_certs` | No | `0` | `1` acepta cualquier certificado TLS. Solo Selenium 3 |
| `-pageLoadTimeout` | No | `300000` | Tiempo máximo de carga de página, en milisegundos |
| `-user_data_dir` | No | — | Carpeta de datos de usuario de Chrome. Solo Selenium 3 |
| `-profile_folder` | No | — | Carpeta de perfil de Chrome dentro de `-user_data_dir`. Solo Selenium 3 |
| `-exit_on_fail` | No | `0` | `1` abandona la ejecución cuando no se puede llegar al servidor Selenium, sin publicar módulos y con estado de salida 0 |
| `-phase_snapshot` | No | `0` | `1` adjunta la imagen del fallo a la fase fallida en el cliente heredado |

### Parámetros de escritorio e imágenes

| Nombre | Obligatorio | Valor por defecto | Descripción |
| --- | --- | --- | --- |
| `-ss_config` | No | Pantalla completa | `active` captura la ventana activa en Windows. Cualquier otro valor recurre a la pantalla completa |
| `-checkpoint` | No | `0` | Reconstruye la imagen de referencia a partir del resultado actual y publica `UX_Control_Snapshot_*` |
| `-max_differences` | No | `0.5` | Porcentaje máximo de caracteres distintos entre la imagen de referencia y la de resultado |
| `-classic_mode` | No | `0` | `1` publica los módulos de latencia solo cuando la comprobación tuvo éxito |

### Parámetros de macros

| Nombre | Obligatorio | Valor por defecto | Descripción |
| --- | --- | --- | --- |
| `-s nombre=valor` | No | — | Sustituye `_nombre_` en el guion. `now`, `now+<días>` y `now-<días>` producen una fecha. Una macro por ejecución |
| `-f formato` | No | `%Y%m%d` | Formato de fecha para las macros de fecha. Un formato por ejecución |

### Parámetros de correo

| Nombre | Obligatorio | Valor por defecto | Descripción |
| --- | --- | --- | --- |
| `-to` | No | — | Destinatario del aviso de fallo. Sin él no se envía correo |
| `-from` | No | `pandora_ux@artica.es` | Remitente del mensaje |
| `-subject` | No | `Pandora UX test failed: ` | Prefijo del asunto; se añade el nombre de la fase |
| `-content` | No | Vacío | Cuerpo del mensaje |
| `-smtp_gw` | No | `127.0.0.1` | Relay SMTP |
| `-smtp_port` | No | `25` | Puerto del relay SMTP |

### Parámetros de módulo, agente y entrega

| Nombre | Obligatorio | Valor por defecto | Descripción |
| --- | --- | --- | --- |
| `-agent` | No | — | Nombre del agente. Cambia el plugin al modo plugin de servidor |
| `-agent_group` | No | Vacío | Grupo del agente creado en el modo plugin de servidor |
| `-agent_interval` | No | `300` | Intervalo del agente creado en el modo plugin de servidor |
| `-interval` | No | `1` | Se acepta y se guarda, pero los módulos generados se publican sin intervalo |
| `-g` | No | `UX` | Grupo de los módulos generados |
| `-tag_list` | No | Vacío | Etiquetas separadas por comas que se añaden a los módulos generados |
| `-mode` | No | `local` | `local` copia el documento del agente en `-local_folder`; `tentacle` lo envía a `-tentacle_ip`:`-tentacle_port` |
| `-tentacle_ip` | No | `127.0.0.1` | Dirección del servidor de Tentacle |
| `-tentacle_port` | No | `41121` | Puerto del servidor de Tentacle |
| `-tentacle_opts` | No | Vacío | Opciones adicionales que se pasan al cliente de Tentacle |
| `-local_folder` | No | `/var/spool/pandora/data_in` | Carpeta de destino en el modo `local` |
| `-temp` | No | Carpeta temporal del sistema | Carpeta donde se escribe el documento del agente antes de entregarlo |

Cuando el primer argumento es la ruta de un archivo existente, el plugin lo lee
como líneas `key=value` antes de procesar las opciones, y las opciones tienen
precedencia sobre él. La ayuda del plugin no documenta esta forma.

### Módulos generados

| Módulo | Tipo | Modo | Significado |
| --- | --- | --- | --- |
| `UX_Status_<fase>` | `generic_proc` | Web, escritorio y Goliat | `1` cuando la fase tuvo éxito, `0` cuando falló |
| `UX_Time_<fase>` | `generic_data` | Web, escritorio y Goliat | Duración de la fase, en segundos |
| `UX_Control_Snapshot_<fase>` | `async_string` | Escritorio | Imagen de referencia reconstruida en esta ejecución |
| `UX_Snapshot_<fase>` | `async_string` | Web y escritorio | Imagen en el momento del fallo |
| `UX_Global_Status_<transacción>` | `generic_proc` | Web y escritorio con nombre de transacción | `1` cuando todas las fases tuvieron éxito |
| `UX_Global_Time_<transacción>` | `generic_data` | Web y escritorio con nombre de transacción | Duración de la ejecución, o la suma de las fases con `-pwr_override_global_phase_time 1` |
| `UX_Global_Snapshot_<transacción>` | `async_string` | Web y escritorio con nombre de transacción | Imagen del fallo, o `No image available` |
| `UX_Phases_Time_<transacción>` | `generic_data` | Cualquier modo con nombre de transacción y `-pwr_phases_time 1` | Suma de los tiempos de fase |
| `<etiqueta>_Global_Status` | `generic_proc` | `stats` | `1` cuando `curl` terminó con código de salida 0 |
| `<etiqueta>_UX_Stats_TT` | `generic_data` | `stats` | Tiempo total de la petición, en milisegundos |
| `<etiqueta>_UX_Stats_DNS` | `generic_data` | `stats` | Tiempo de resolución de nombres, en milisegundos |
| `<etiqueta>_UX_Stats_TTCP` | `generic_data` | `stats` | Tiempo de conexión TCP, en milisegundos |
| `<etiqueta>_UX_Stats_TSSL` | `generic_data` | `stats`, URL `https` | Tiempo del saludo TLS, en milisegundos |
| `<etiqueta>_UX_Stats_TST` | `generic_data` | `stats` | Tiempo hasta el primer byte, en milisegundos |
| `<etiqueta>_UX_Stats_TTC` | `generic_data` | `stats` | Tiempo de transferencia, en milisegundos |

Los módulos que publica el comentario `getValue` conservan el nombre y el tipo
declarados en el comentario. La etiqueta de transacción `Phase <n>: ` y el
prefijo `<transacción>.` forman parte del nombre del módulo cuando existe un
nombre de transacción, como se describe en
[Nombres de transacción y de fase](#nombres-de-transaccion-y-de-fase).

### Estado de salida

| Estado | Significado |
| --- | --- |
| `0` | Fin normal, incluida una ejecución cuyos módulos informan de fallos. En el modo plugin de servidor se imprime en su lugar el estado global: `1` o `0` |
| `1` | El plugin imprimió su lista de parámetros, o falta un componente opcional del modo seleccionado |
| Otro | Un error interno detuvo el proceso antes de poder informar |

### Identidad del addon

| Propiedad | Valor |
| --- | --- |
| Identificador en el Marketplace | `pandorafms.pandora_ux` |
| Nombre | Pandora UX |
| Versión | `1.0` |
| Cadena de versión que imprime la ayuda del plugin | `8.0NG.805`, build `260915` |
| Categoría | Miscelaneus |
| Licencia | One |
| Última actualización en el Marketplace | 2025-07-02 |
| Disponibilidad | Descarga limitada a usuarios con licencia |
