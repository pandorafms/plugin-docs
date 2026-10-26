# Plugin Journalctl

*Última actualización del artículo: 2026-10-26.*

## Qué hace

El plugin Journalctl reenvía el journal de systemd de un host Linux a Pandora
FMS. En cada ejecución solicita a `journalctl` las entradas escritas desde la
ejecución anterior, las filtra con expresiones regulares y las imprime como
entradas de log de Pandora FMS en la salida estándar.

Es un **plugin de agente**: el agente de Pandora FMS lo ejecuta como una de sus
líneas `module_plugin`, en cada intervalo del agente, y añade las entradas que
imprime a sus propios datos. El plugin no crea ningún agente, no abre conexiones
de red y no necesita credenciales: solo lee el journal de la máquina donde se
ejecuta.

La recogida es incremental. El plugin guarda la hora de su última ejecución
correcta en un único archivo dentro de `/tmp` y solicita el journal escrito
después de ese momento, de forma que cada ejecución entrega las entradas nuevas
en lugar del journal completo. Una expresión regular acota lo que se entrega,
bien conservando solo las líneas que coinciden, bien descartando las que
coinciden.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
|-------|-------|----------|
| Addon `pandorafms.journalctl`, versión `1.0` | Objetivo documentado | La versión del paquete del Marketplace `pandorafms.journalctl.1.0.zip`. Ver [Identidad del addon](#identidad-del-addon) |
| Host Linux con systemd y `journalctl` en el `PATH` | `Required` | `journalctl` es la única fuente de datos del plugin: cuando el comando no está disponible, la ejecución termina con error y no imprime ninguna entrada |
| Cuenta con permiso para leer el journal | `Required` | El plugin lee el journal mediante `journalctl` con los permisos de la cuenta que ejecuta el agente; cuando el journal no se puede leer, el comando falla y la ejecución termina con error |
| Agente de Pandora FMS instalado en el host monitorizado | `Required` | El plugin lo ejecuta el agente y su salida se consume como salida de plugin de agente |
| Pandora FMS NG 784 y posteriores | `Supported` | El Marketplace indica que todas sus integraciones son compatibles con Pandora FMS NG 784 y versiones posteriores. Es una declaración general del Marketplace, no una declaración específica de este addon |
| Distribuciones y versiones concretas de Linux | `Not validated` | No hay ninguna matriz de distribuciones o versiones registrada para este addon |

El plugin se ejecuta en el propio host monitorizado: informa únicamente del
journal de ese host y no tiene modo de ejecución remota ni conexión con otro
sistema.

### Requisitos

1. **systemd, con el comando `journalctl` disponible en el `PATH` de la cuenta
   que ejecuta el agente.** El plugin no tiene alternativa: sin el comando no
   hay nada que leer.
2. **Permiso de lectura del journal para esa cuenta.** El agente ejecuta el
   plugin como su propio usuario y el plugin no eleva privilegios. Conceda a ese
   usuario el acceso de lectura al journal que corresponda en su distribución
   —habitualmente mediante el grupo `systemd-journal`— o ejecute el agente con una
   cuenta que ya lo tenga. Cuando la cuenta no puede leer el journal, `journalctl`
   falla y la ejecución se interrumpe.
3. **Un `/tmp` con permiso de escritura.** El plugin lo comprueba al inicio de
   cada ejecución y se detiene cuando no puede escribir allí, porque guarda su
   posición de recogida en `/tmp/journalctl_logs.index`.
4. **Un agente de Pandora FMS en el host.** El agente es lo que convierte las
   entradas impresas en datos de log en la consola.
5. **Una cuenta del Marketplace con licencia.** La descarga de este addon está
   limitada a usuarios con licencia.

### Instalar el plugin

Descargue el paquete desde la entrada del Marketplace:

[https://marketplace.pandorafms.com/entries/pandorafms.journalctl](https://marketplace.pandorafms.com/entries/pandorafms.journalctl)

El paquete distribuye el ejecutable `grep_journalctl` —ese es el nombre del
archivo, no el identificador del addon— y no incluye ningún archivo de
configuración.
Cópielo al directorio de plugins del agente y dele permiso de ejecución. En un
agente Linux el directorio de plugins es `/usr/share/pandora_agent/plugins`, al
que también se llega como `/etc/pandora/plugins`:

```bash
cp grep_journalctl /usr/share/pandora_agent/plugins/
chmod 755 /usr/share/pandora_agent/plugins/grep_journalctl
```

El agente añade su directorio de plugins al `PATH`, de modo que el nombre del
ejecutable basta en la línea `module_plugin`. Una ruta absoluta también
funciona y es la opción más segura cuando existe más de una copia del archivo.

En lugar de copiar el archivo a mano, el agente puede distribuirlo a sus hosts
como una colección de archivos; el destino es el mismo directorio de plugins.

## Configuración

### Añadir el plugin al agente

El plugin se configura en el archivo de configuración del agente
(`pandora_agent.conf`) como una línea `module_plugin`. Sin opciones entrega
todas las líneas nuevas del journal del host:

```apache
module_plugin grep_journalctl
```

La línea se ejecuta una vez por intervalo del agente, así que la cobertura de
cada ejecución es el tiempo transcurrido desde la ejecución anterior. Reinicie
o recargue el agente después de editar el archivo.

Limite la entrega con un filtro de inclusión y asigne el nombre del origen que
agrupará las entradas en la consola:

```apache
module_plugin grep_journalctl -in 'Failed password|authentication failure' -s AuthErrors
```

O descarte las líneas que no desea y conserve el resto:

```apache
module_plugin grep_journalctl -out 'session opened|session closed' -s SystemLog
```

Una sola línea `module_plugin` por host es suficiente: consulte
[Una posición de recogida por host](#una-posicion-de-recogida-por-host) antes de
añadir una segunda.

Para acotar la duración de la ejecución, use la forma de bloque y añada un
tiempo máximo de módulo. El bloque no necesita `module_name`: el plugin imprime
sus propias entradas y el agente las añade sin modificarlas.

```apache
module_begin
module_plugin grep_journalctl -in 'error|critical' -s SystemErrors
module_timeout 120
module_end
```

La forma de una sola línea no tiene tiempo máximo, lo que significa que una
ejecución que lea un acumulado grande puede durar más que el intervalo del
agente. `module_timeout` se expresa en segundos y se aplica solo a esa línea.

Cuando el agente lee su configuración desde la consola (configuración remota),
la línea `module_plugin` pertenece a la configuración del agente almacenada
allí, y el agente sobrescribe cualquier edición local de `pandora_agent.conf`.

### Entrecomillar los patrones

El agente ejecuta la línea `module_plugin` a través de un shell, antes de que el
plugin la vea. Un patrón que contenga caracteres como `|`, `(`, `)`, `$`, `*` o
`&` debe ir entrecomillado, o el shell lo interpretará y el plugin recibirá otra
cosa:

```apache
module_plugin grep_journalctl -in 'Failed password|authentication failure'
```

Use comillas simples: protegen todos los caracteres salvo una comilla simple.
Las comillas dobles también funcionan, pero dentro de ellas el shell sigue
expandiendo `$`, así que un patrón como `end$` debe escribirse con comillas
simples.

### Elegir el origen

`-s` / `--source` fija el nombre de origen con el que la consola agrupa las
entradas de esta línea. El valor por defecto es `Journalctl`, con J mayúscula.
Asigne siempre un valor no vacío: un `-s ''` vacío se acepta y produce entradas
con origen vacío, lo que las hace difíciles de encontrar y de distinguir.

Cambiar el origen no reinicia la posición de recogida. Las entradas entregadas
antes del cambio permanecen en el origen anterior y las nuevas aparecen en el
nuevo, de modo que un origen renombrado parece un journal distinto en la
consola.

### Filtrar las líneas

Ambos filtros reciben una expresión regular que se busca en cualquier parte de
la línea. Son opcionales y solo uno de ellos puede actuar:

- **`-in` / `--regex_in`** conserva solo las líneas que coinciden.
- **`-out` / `--regex_out`** descarta las líneas que coinciden.

Cuando se indican los dos, `-in` gana y `-out` se ignora sin ningún aviso. Un
valor vacío (`-in ''`) cuenta como ausente, así que no filtra nada.

Reglas de coincidencia:

- La expresión es una búsqueda, no una comparación de línea completa: `error`
  coincide con cualquier línea que contenga `error`.
- La coincidencia distingue mayúsculas y minúsculas salvo que el patrón lo
  desactive con `(?i)`: `-in '(?i)error'` coincide con `ERROR` y con `Error`.
- Se compara la línea completa del journal, incluidos la fecha, el nombre del
  host y el prefijo de la unidad que `journalctl` escribe en su formato de
  salida por defecto. Por eso un patrón anclado con `^` ve la marca de tiempo y
  no el texto del mensaje: `^error` no coincide con casi nada, mientras que
  `: error` o `(?i)error` funcionan como se espera.
- Cada línea física se compara y se entrega por separado. Una entrada cuyo
  mensaje ocupa varias líneas llega como varias entradas y un patrón no puede
  coincidir a través de ellas.
- Un patrón que no es una expresión regular válida interrumpe la ejecución
  antes de leer el journal, con un mensaje de error y código de salida `1`.

El filtro actúa sobre las líneas recogidas, después de que la posición de
recogida haya avanzado: una línea que el filtro descarta no se entrega más tarde
y nunca se reconsidera. Cambiar el patrón no vuelve a procesar el pasado.

## Verificación

Ejecute el plugin a mano antes de integrarlo en el agente. Desde el directorio
de plugins:

```bash
./grep_journalctl
```

Cada ejecución se realiza una vez y termina. Una ejecución correcta imprime un
bloque `<log_module>` por cada línea entregada en la salida estándar y escribe
la posición de recogida en `/tmp/journalctl_logs.index`:

```xml
<log_module>
	<source><![CDATA[Journalctl]]></source>
	<data>"Tm92IDExIDEyOjUzOjAyIGhvc3QwMSBzc2hkWzEzODJdOiBGYWlsZWQgcGFzc3dvcmQgZm9yIGludmFsaWQgdXNlciBhZG1pbiBmcm9tIDE5Mi4wLjIuMTA="</data>
	<encoding>base64</encoding>
</log_module>

<log_module>
	<source><![CDATA[Journalctl]]></source>
	<data>"Tm92IDExIDEyOjUzOjAzIGhvc3QwMSBzeXN0ZW1kWzFdOiBTdGFydGVkIFNlc3Npb24gNDIgb2YgdXNlciBtb25pdG9yaW5nLg=="</data>
	<encoding>base64</encoding>
</log_module>
```

El valor de `<data>` es la línea del journal codificada en Base64, entre comillas
dobles. Decodifíquelo para confirmar qué se ha recogido:

```bash
printf 'Tm92IDExIDEyOjUzOjAzIGhvc3QwMSBzeXN0ZW1kWzFdOiBTdGFydGVkIFNlc3Npb24gNDIgb2YgdXNlciBtb25pdG9yaW5nLg==' | base64 -d
```

```
Nov 11 12:53:03 host01 systemd[1]: Started Session 42 of user monitoring.
```

Ejecute el mismo comando otra vez de inmediato. Cuando no se ha escrito ninguna
línea del journal entre ambas ejecuciones, la ejecución no imprime nada en la
salida estándar, escribe `No new logs.` en la salida de error y termina con
código `0`:

```
19:51:45 [INFO] No new logs.
```

La posición de recogida que dejó la ejecución correcta puede leerse
directamente:

```bash
cat /tmp/journalctl_logs.index
```

```
2026-10-26 19:51:45
```

Una ejecución manual se comporta igual que una ejecución del agente, incluido el
avance de ese archivo. Úsela para instalar, para probar patrones y para
diagnosticar, y téngalo en cuenta cuando el agente ya esté ejecutando el mismo
plugin en ese host (consulte [Operación diaria](#operacion-diaria)).

Una vez que la línea `module_plugin` está puesta y el agente la ha ejecutado, las
entradas aparecen en el visor de logs de la consola bajo el agente que ejecuta
el plugin y el origen configurado:

<!-- SCREENSHOT NEEDED: Visor de logs de Pandora FMS filtrado por el agente que ejecuta el plugin y por el origen Journalctl, con varias entradas del journal y sin datos reales de cliente. -->

## Entender los resultados

### Entradas de log

Cada línea del journal entregada se convierte en una entrada `log_module` con
tres campos:

| Campo | Contenido |
| --- | --- |
| `source` | El valor de `-s` / `--source`, tal cual. La consola agrupa las entradas por este nombre. Por defecto `Journalctl` |
| `data` | La línea del journal codificada en Base64, entre comillas dobles |
| `encoding` | Siempre `base64` |

La codificación Base64 es lo que mantiene válido el XML generado: el journal
puede contener ángulos, comillas y caracteres de control, y la codificación los
transporta sin romper el documento. La consola decodifica el valor, así que el
visor de logs muestra la línea original.

El plugin no envía ningún módulo con valor numérico, ninguna comprobación de
disponibilidad y ninguna plantilla de alerta: las entradas de log son su única
salida. En las vistas de monitorización del agente no aparece ningún gráfico ni
ningún estado, de modo que cualquier alerta se configura en la consola sobre los
datos de log.

### Qué hace el agente con la salida

- El agente añade la salida del plugin a los datos que envía al servidor, así
  que los bloques `<log_module>` llegan a Pandora FMS sin modificaciones.
- **Cuando el plugin termina con un estado distinto de `0`, el agente descarta
  toda su salida** y anota el código de error en su propio log. Una ejecución
  que falla después de imprimir parte de sus entradas no entrega ninguna.
- El agente envía la salida de error de un plugin a `/dev/null`. Por tanto, en
  una ejecución programada no se ve ningún diagnóstico de este plugin: ni el
  error de expresión regular, ni el fallo de `journalctl`, ni la falta de
  permisos en `/tmp`, ni el aviso `No new logs.`, ni la línea de `-v`. Ejecute el
  comando a mano para leerlos.

### Cobertura y posición de recogida

El plugin guarda una única marca de tiempo, con el formato
`AAAA-MM-DD HH:MM:SS`, en `/tmp/journalctl_logs.index`. Cada ejecución solicita a
`journalctl` las entradas posteriores a ese momento:

```text
journalctl --since "<marca de tiempo guardada>" --no-pager
```

La ventana de una ejecución empieza donde terminó la ejecución correcta anterior
y acaba cuando la ejecución actual escribe su propia marca de tiempo. Esa
posición se escribe al final de la ejecución y solo cuando la ejecución termina.
De ahí se derivan tres consecuencias que conviene conocer antes de apoyarse en el
log para auditar:

- **La ejecución cubre todo lo ocurrido desde la última ejecución completada.**
  Esto incluye las entradas escritas mientras el plugin estaba parado, así que un
  host cuyo agente estuvo caído un día entrega un día de journal en la primera
  ejecución tras el arranque. No hay límite de líneas: la ventana completa se lee
  en memoria y se imprime una entrada por línea.
- **Una ejecución que falla no avanza la posición.** No se pierde nada, pero la
  siguiente ejecución correcta repite la misma ventana, de modo que las entradas
  pueden entregarse dos veces: tras un fallo de `journalctl`, tras una expresión
  regular no válida y tras una ejecución interrumpida con `Ctrl+C` o terminada
  antes de completarse.
- **Una parte pequeña de la ventana no se entrega nunca.** La posición es la hora
  del final de la ejecución, mientras que el journal se leyó antes, en esa misma
  ejecución. Las entradas escritas entre la lectura y la escritura de la marca de
  tiempo son anteriores a la posición guardada cuando empieza la ejecución
  siguiente, así que se omiten. El hueco es corto, pero existe.

Dos efectos menores del mismo diseño:

- La marca de tiempo tiene una resolución de un segundo y la consulta incluye las
  entradas escritas en ese segundo exacto, así que una línea escrita en el mismo
  segundo en que terminó la ejecución anterior puede entregarse dos veces.
- La marca de tiempo no lleva zona horaria y `journalctl` la interpreta en la hora
  local del host. Si el host cambia de zona horaria o cruza un cambio de hora
  estacional, la ventana entre dos ejecuciones se desplaza en consecuencia.

### Una posición de recogida por host

El nombre del archivo es fijo: todas las ejecuciones del plugin en el mismo host
usan `/tmp/journalctl_logs.index`, sea cual sea el origen, el filtro o la cuenta.
No hay estado por módulo ni por origen.

- Dos líneas `module_plugin` en el mismo host comparten la posición. La segunda
  encuentra una ventana casi vacía, porque la primera ya la ha consumido, y cada
  una recibe una parte arbitraria del journal. No ejecute dos líneas: mantenga una
  y use `-in` para seleccionar lo que necesite.
- Una ejecución manual y la ejecución programada también la comparten, así que una
  ejecución manual consume la ventana que habría entregado el agente.

!!! warning "El archivo de posición está en un directorio compartido"
    `/tmp` es escribible por todos y el nombre del archivo es fijo, así que
    cualquier cuenta local puede crearlo antes, reemplazarlo o convertirlo en un
    enlace simbólico. El plugin escribe su marca de tiempo con los privilegios de
    la cuenta del agente, de modo que un enlace simbólico colocado ahí hace que la
    ejecución sobrescriba otro archivo que esa cuenta pueda escribir. Ejecute el
    agente con una cuenta sin privilegios cuando su instalación lo permita y no
    trate el contenido del archivo como un registro a prueba de manipulaciones.

### Primera ejecución

Cuando `/tmp/journalctl_logs.index` no existe, o su contenido no se puede leer o
no es una marca de tiempo válida, la ejecución recoge **los últimos cinco
minutos** del journal. Es lo mismo que ocurre tras un reinicio que vacía `/tmp`:
las entradas de los cinco minutos anteriores al reinicio pueden entregarse por
segunda vez, porque el journal puede sobrevivir al reinicio mientras que la
posición no.

Para forzar de nuevo esa ventana de cinco minutos, borre el archivo:

```bash
rm -f /tmp/journalctl_logs.index
```

La siguiente ejecución empieza cinco minutos antes de su inicio, ocurra lo que
ocurra en el intervalo.

## Operar y resolver problemas

### Operación diaria

- **Una línea por host.** La posición de recogida única hace inútil una segunda
  línea (consulte [Una posición de recogida por host](#una-posicion-de-recogida-por-host)).
- **El intervalo fija la cobertura.** El agente ejecuta la línea en cada
  intervalo y cada ejecución cubre lo ocurrido desde la anterior. Un intervalo
  más corto entrega con más frecuencia y en lotes más pequeños; no cambia qué
  entradas se entregan.
- **Acote las ejecuciones largas.** Tras una parada prolongada, la primera
  ejecución lee la ventana completa. Fije `module_timeout` en un bloque para que
  un acumulado grande no retrase el agente más allá del intervalo, y ejecute el
  plugin a mano antes para vaciarlo.
- **Las ejecuciones manuales consumen datos.** Una ejecución manual imprime las
  entradas en su terminal y avanza la posición, así que el agente no las entrega
  después. Use la ejecución manual para instalar, para probar un patrón y para
  diagnosticar, y cuente con que la siguiente ejecución del agente llegue vacía.
- **`-v` solo informa de la escritura de la posición.** El modo detallado eleva
  el nivel de diagnóstico, pero el único mensaje que añade es la línea que
  registra la nueva posición de recogida, por ejemplo
  `19:51:53 [DEBUG] Saved execution time: 2026-10-26 19:51:53 -> /tmp/journalctl_logs.index`.
  No informa de los filtros aplicados, del número de líneas leídas ni del número
  de entradas entregadas.
- **Mantenga los patrones estables.** Un cambio de filtro se aplica desde la
  ejecución siguiente; las líneas ya descartadas se han perdido y una línea que
  el nuevo patrón habría conservado no se recupera.

### Resolución de problemas

| Síntoma | Causa probable | Comprobación |
| --- | --- | --- |
| No hay entradas en la consola y la ejecución manual no imprime nada | La ventana está vacía: otra ejecución (la del agente o una ejecución manual anterior suya) ya la ha consumido, o el filtro lo descarta todo | Ejecute el plugin a mano con las mismas opciones, justo después de escribir una línea de prueba que coincida con `logger 'test journalctl'` |
| `No new logs.` en todas las ejecuciones | La posición avanza pero ninguna línea pasa el filtro, o una segunda ejecución consume antes la ventana | Compruebe los filtros contra líneas reales con `journalctl --since '10 minutes ago' --no-pager`; mantenga una sola línea `module_plugin` |
| Las entradas aparecen con un origen equivocado | Falta `-s` (por defecto `Journalctl`), o se cambió y las entradas antiguas quedaron en su origen anterior | Fije `-s` de forma explícita y busque el origen anterior en el visor de logs |
| Un patrón que funciona en otro sitio no coincide con nada | La línea lleva la fecha y el host que añade `journalctl`, o las mayúsculas no coinciden | Quite el ancla `^` o añada `(?i)` |
| `Invalid regex: ...` y ninguna entrada | El patrón no es una expresión regular válida | Corrija el patrón; la ejecución se detiene antes de leer el journal, así que no se pierde nada |
| `Error: 'journalctl' command not found...` | `journalctl` no está instalado o no está en el `PATH` del agente | Instale systemd, o asegúrese de que el `PATH` del agente incluye el directorio que contiene `journalctl` |
| `Error executing journalctl: ...` seguido del error del comando | `journalctl` ha fallado: la cuenta no puede leer el journal, o el journal no es legible | Ejecute `journalctl --since '5 minutes ago' --no-pager` como el usuario del agente |
| `No write permissions for /tmp` | `/tmp` no tiene permiso de escritura para la cuenta que ejecuta el plugin | Corrija los permisos o las opciones de montaje de `/tmp` |
| La ejecución termina con estado `2` y un mensaje de uso | Una opción desconocida, o una opción sin valor | Compare la línea con [Parámetros de la línea de comandos](#parametros-de-la-linea-de-comandos) |
| Las entradas desaparecen en una ejecución que además falló | El estado de salida no era `0`, así que el agente descartó toda la salida | Busque el error en una ejecución manual: el agente ya ha enviado la salida de error a `/dev/null` |
| Faltan entradas entre dos ejecuciones | Se escribieron mientras la ejecución estaba en curso, o las descartó el filtro | Es lo esperado: la ventana termina en el momento en que se escribe la posición |
| Las mismas entradas llegan dos veces | La ejecución anterior no se completó, se borró la posición, se vació `/tmp`, o las dos ejecuciones terminaron en el mismo segundo | Acéptelo, o use la marca de tiempo de la entrada en la consola para identificar el duplicado |

## Referencia

### Parámetros de la línea de comandos

| Nombre | Obligatorio | Por defecto | Descripción |
| --- | --- | --- | --- |
| `-in <regex>`, `--regex_in <regex>` | No | Ninguno (todas las líneas) | Entrega solo las líneas del journal que coinciden con la expresión. Un valor vacío cuenta como ausente. Tiene prioridad sobre `-out` |
| `-out <regex>`, `--regex_out <regex>` | No | Ninguno (nada excluido) | Descarta las líneas del journal que coinciden con la expresión. Se ignora cuando `-in` está definido |
| `-s <nombre>`, `--source <nombre>` | No | `Journalctl` | Valor del campo `source` de cada entrada. Un valor vacío produce entradas con origen vacío |
| `-v`, `--verbose` | No | Desactivado | Eleva el nivel de diagnóstico. El único mensaje adicional es el que registra la nueva posición de recogida |
| `-h`, `--help` | No | — | Imprime el resumen de uso y termina con estado `0` |

Los valores se indican como `-in <valor>` o `--regex_in <valor>`; también se
aceptan las formas `-in=<valor>` y `--regex_in=<valor>`. Las opciones pueden
indicarse en cualquier orden.

El agente añade dos directivas propias alrededor de la misma línea, en la forma
de bloque: `module_timeout <segundos>` para acotar la ejecución y `module_end`
para cerrar el bloque. Pertenecen a la configuración del agente, no al plugin.

### Salida

| Situación | Salida estándar | Salida de error | Código de salida |
| --- | --- | --- | --- |
| Al menos una línea supera los filtros | Un bloque `<log_module>` por línea, cada uno seguido de una línea en blanco | Nada | `0` |
| El journal no contiene ninguna entrada en la ventana | Nada | `HH:MM:SS [INFO] No new logs.` | `0` |
| Todas las líneas recogidas se descartan por el filtro | Nada | Nada | `0` |
| La expresión regular no es válida | Nada | `HH:MM:SS [ERROR] Invalid regex: <motivo>` | `1` |
| `journalctl` no está disponible | Nada | `HH:MM:SS [ERROR] Error: 'journalctl' command not found...` | `1` |
| `journalctl` falla | Nada | `HH:MM:SS [ERROR] Error executing journalctl: ...` y el error del comando | `1` |
| `/tmp` no tiene permiso de escritura | Nada | `HH:MM:SS [ERROR] No write permissions for /tmp` | `1` |
| Un error de proceso al construir las entradas | Las entradas ya impresas | `HH:MM:SS [ERROR] Error processing logs: <motivo>` | `1` |
| Interrupción con `Ctrl+C` durante el proceso | Las entradas ya impresas | `HH:MM:SS [INFO] Execution interrupted.` | `0` |
| `-h`, `--help` | Resumen de uso | Nada | `0` |
| Opción desconocida o valor ausente | Nada | Mensaje de uso y el error | `2` |

El prefijo `HH:MM:SS` es la hora local del mensaje. Todos los diagnósticos del
plugin van a la salida de error y la salida estándar solo contiene el XML de las
entradas.

### Posición de recogida

| Propiedad | Valor |
| --- | --- |
| Ruta | `/tmp/journalctl_logs.index` |
| Contenido | Una sola línea con la marca de tiempo del final de la última ejecución correcta, con el formato `AAAA-MM-DD HH:MM:SS`, hora local sin zona horaria |
| Se escribe cuando | Al final de una ejecución que se completa, incluidas las ejecuciones en las que el filtro descartó todas las líneas |
| No se escribe cuando | `journalctl` falla, la expresión regular no es válida, `/tmp` no tiene permiso de escritura o la ejecución se interrumpe |
| Se lee cuando | Al inicio de cada ejecución. Un archivo ausente, o un contenido que no es una marca de tiempo válida, inicia la ventana cinco minutos antes de la ejecución |
| Alcance | Un archivo por host, compartido por todas las ejecuciones del plugin en ese host, sea cual sea el origen, el filtro o la cuenta |

### Identidad del addon

| Propiedad | Valor |
| --- | --- |
| Identificador del Marketplace | `pandorafms.journalctl` |
| Nombre | Journalctl |
| Versión | `1.0` — la versión del paquete del Marketplace `pandorafms.journalctl.1.0.zip` |
| Categoría | Miscelaneus |
| Licencia | One; la descarga está limitada a usuarios con licencia |
| Última actualización en el Marketplace | 2026-02-05 |
| Entrada del Marketplace | [pandorafms.journalctl](https://marketplace.pandorafms.com/entries/pandorafms.journalctl) |
| Flujo de trabajo | Plugin de agente, ejecutado por el agente de Pandora FMS en el host monitorizado |
| Ejecutable | `grep_journalctl` |
