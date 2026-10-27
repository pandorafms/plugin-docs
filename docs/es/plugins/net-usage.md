# Plugin Net usage

*Última actualización del artículo: 2026-10-26.*

## Qué hace

El plugin Net usage mide el tráfico de las interfaces de red de un host Linux y
lo publica en Pandora FMS. En cada ejecución lee los contadores del núcleo de la
máquina donde se ejecuta, suma los bytes recibidos y transmitidos de cada
interfaz seleccionada y escribe el resultado como módulos de Pandora FMS en la
salida estándar.

Es un **plugin de agente**: el agente de Pandora FMS lo ejecuta como una de sus
líneas `module_plugin` en cada intervalo del agente e ingiere los módulos que
imprime. No hay archivo de configuración, ni credenciales, ni petición de red:
todas las cifras proceden de los contadores locales de las interfaces del host
monitorizado.

Cada ejecución emite siempre un módulo incremental por interfaz seleccionada
más un módulo con el total de todas ellas. Los nombres de interfaz se pueden
acotar con filtros de inclusión y de exclusión, y se puede añadir un prefijo a
todos los nombres de módulo para que el mismo host, o varios hosts en el mismo
agente, mantengan sus módulos separados.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
|--------|--------|-----------|
| Addon `pandorafms.pandora_netusage`, versión `1.1` | Objetivo documentado | La versión que describe esta página. Ver [Identidad del addon](#identidad-del-addon) |
| Un host Linux que exponga `/proc/net/dev` | `Requerido` | Es la única fuente de datos del plugin: la ejecución falla en cualquier host que no ofrezca ese archivo |
| Rocky Linux 9 | `Compatible conocido` | La guía antigua de este addon registra Rocky 9 como el sistema donde se probó. No se ha revalidado para la versión `1.1` |
| Otras distribuciones Linux | `Sin validar` | No hay rango de distribuciones ni matriz de versiones registrada para este addon |
| Un agente de Pandora FMS en el host monitorizado | `Requerido` | El plugin lo ejecuta el agente y su salida se consume como módulos de plugin de agente |
| Versiones de Pandora FMS | `Sin validar` | El Marketplace muestra un aviso general para todas sus integraciones, no una declaración específica de este addon |

El plugin se ejecuta en el propio host monitorizado, así que informa únicamente
de las interfaces de ese host. No tiene modo de ejecución remota ni conexión con
ningún otro sistema.

### Requisitos

1. **Un host Linux** con `/proc/net/dev` legible por el usuario que ejecuta el
   agente. El plugin solo lee ese archivo; no necesita elevación ni ningún otro
   privilegio.
2. **Un agente de Pandora FMS** instalado en ese host y capaz de ejecutar
   plugins. El agente es lo que convierte los módulos impresos en módulos de la
   consola.
3. **Una cuenta del Marketplace con licencia**: la descarga de este addon está
   limitada a usuarios con licencia.

### Instalar el plugin

Descargue el paquete desde la entrada del Marketplace:

[https://marketplace.pandorafms.com/entries/pandorafms.pandora_netusage](https://marketplace.pandorafms.com/entries/pandorafms.pandora_netusage)

El paquete instala el ejecutable `pandora_netusage`. Cópielo al directorio de
plugins del agente y dele permiso de ejecución. Con las rutas por defecto de un
agente Linux:

```bash
cp pandora_netusage /usr/share/pandora_agent/plugins/
chmod 755 /usr/share/pandora_agent/plugins/pandora_netusage
```

En lugar de copiar el archivo a mano, el agente puede distribuirlo a sus hosts
como una colección de archivos; el destino es el mismo directorio de plugins.

!!! warning "El paquete del agente ya incluye un plugin con este nombre"
    La distribución del agente Linux incluye su propio
    `plugins/pandora_netusage`. Ese archivo es un plugin distinto: publica un
    único módulo `Network_Usage_Bytes` con la suma de todas las interfaces y no
    acepta ninguna opción. Ambos archivos tienen el mismo nombre en el mismo
    directorio, y el archivo de configuración por defecto del agente ya contiene
    una línea `module_plugin pandora_netusage`, así que una copia instalada con
    ese nombre sustituye al plugin incluido y empieza a ejecutarse desde esa
    línea existente sin ninguna opción. Revise esa línea, o instale este addon
    con otro nombre de archivo y use ese nombre en la línea `module_plugin`.

## Configuración

### Añadir el plugin al agente

El plugin se configura en el archivo de configuración del agente
(`pandora_agent.conf`), como una línea `module_plugin`. A la ruta del ejecutable
le siguen las opciones que quiera aplicar; el agente ejecuta la línea e ingiere
los módulos XML que imprime:

```apache
module_plugin /usr/share/pandora_agent/plugins/pandora_netusage
```

Sin opciones, el plugin informa de todas las interfaces del host, incluida la de
loopback, y añade el total. Reinicie o recargue el agente después de editar el
archivo para que la nueva línea surta efecto.

Cada línea `module_plugin` es una ejecución independiente que produce su propio
conjunto de módulos. Dos líneas con valores distintos de `--module_prefix` en el
mismo host publican dos conjuntos separados de módulos, que es la forma de
mantener, por ejemplo, una vista sin filtrar y otra filtrada de las mismas
interfaces.

!!! note "Una línea, muchos módulos"
    Una sola línea `module_plugin` basta para todo el host. El plugin no tiene
    ninguna opción para publicar una interfaz por módulo: cada ejecución emite
    todas las interfaces seleccionadas más el total, y el agente crea un módulo
    por cada una. Si la línea `module_plugin pandora_netusage` por defecto del
    agente sigue en el archivo, el plugin se ejecuta dos veces por intervalo; con
    el mismo prefijo, ambas ejecuciones publican módulos con los mismos nombres,
    así que deje una sola línea o dé a cada una su propio `--module_prefix`.

### Filtrar las interfaces

Dos opciones acotan el conjunto de interfaces. Ambas toman una expresión regular
que se compara con el nombre de la interfaz, y ambas son opcionales:

- **`--allow_regexp`** conserva solo las interfaces cuyo nombre coincide. Vacía o
  ausente, se miden todas las interfaces.
- **`--deny_regexp`** elimina las interfaces cuyo nombre coincide. Se aplica
  después del filtro de inclusión, así que una interfaz que coincida con los dos
  se elimina.

La expresión se busca en cualquier posición del nombre: `eth` coincide con
`eth0` y con `veth1`. Ancle con `^` y `$` para coincidir con el nombre completo.
Los nombres se comparan tal como los informa el núcleo, así que una interfaz
llamada `ens192` no coincide con `eth`.

```apache
module_plugin /usr/share/pandora_agent/plugins/pandora_netusage --allow_regexp "^eth|^ens" --deny_regexp "^lo$"
```

Con esa línea el plugin mide las interfaces `eth*` y `ens*`, deja fuera la de
loopback y publica su total. Entrecomille cada patrón: el agente ejecuta la línea
como un comando de shell, y caracteres como `|` o `$` se interpretan antes de que
el plugin los reciba.

Una interfaz filtrada desaparece de la salida del plugin, y con ella su parte
del total: el total es la suma de las interfaces que superan los dos filtros. Si
la combinación no selecciona ninguna interfaz, la ejecución sigue emitiendo el
módulo del total, con valor `0`.

Un patrón que no sea una expresión regular válida no se detecta al arrancar el
agente: la ejecución aborta con un error y no imprime módulos. Pruebe el patrón
manualmente antes de ponerlo en la configuración del agente (ver
[Verificación](#verificacion)).

### Prefijar los nombres de los módulos

`--module_prefix` añade texto delante de todos los nombres de módulo. El prefijo
se concatena sin separador, así que incluya el suyo:

```apache
module_plugin /usr/share/pandora_agent/plugins/pandora_netusage --module_prefix "host01-" --allow_regexp "^eth"
```

Esa línea produce `host01-eth0 Network_Usage_Bytes` y
`host01-Network_Usage_Bytes_Total`. Use un prefijo que identifique el host o el
entorno y manténgalo estable: cambiarlo crea un conjunto nuevo de módulos y deja
los anteriores sin datos.

## Verificación

Ejecute el plugin manualmente desde el directorio que contiene el ejecutable:

```bash
./pandora_netusage --allow_regexp "^eth"
```

Cada ejecución se realiza una vez y termina. Una ejecución correcta imprime un
bloque `<module>` por interfaz seleccionada, en el orden en que el núcleo las
lista, y el bloque del total al final:

```xml
<module>
	<name><![CDATA[eth0 Network_Usage_Bytes]]></name>
	<type>generic_data_inc</type>
	<data><![CDATA[4821936642]]></data>
	<description><![CDATA[Total bytes/sec transfered in this system]]></description>
	<unit><![CDATA[Bytes]]></unit>
</module>
<module>
	<name><![CDATA[Network_Usage_Bytes_Total]]></name>
	<type>generic_data_inc</type>
	<data><![CDATA[4821936642]]></data>
	<description><![CDATA[Total bytes/sec transfered in this system (all interfaces)]]></description>
	<unit><![CDATA[Bytes]]></unit>
</module>
```

Las cifras son los contadores acumulados de ese momento. Ejecute el comando dos
veces con unos segundos de diferencia y compare: en una interfaz con tráfico, el
segundo valor es mayor que el primero.

`./pandora_netusage --help` imprime el resumen de uso, con la versión y las tres
opciones.

Una vez que la línea `module_plugin` está puesta y el agente la ha ejecutado, los
módulos aparecen en el agente en la consola:

<!-- SCREENSHOT NEEDED: vista de agente de Pandora FMS con los módulos generados por pandora_netusage en un host Linux, con los módulos por interfaz y Network_Usage_Bytes_Total. -->

Para confirmar qué guarda la consola de uno de ellos, abra el módulo:

<!-- SCREENSHOT NEEDED: vista de definición de un módulo Network_Usage_Bytes con el tipo incremental, la unidad Bytes y el texto de descripción, sin datos reales de cliente. -->

## Entender los resultados

### Nombres de los módulos

| Nombre del módulo | Tipo | Unidad | Valor |
| --- | --- | --- | --- |
| `<PREFIX><interfaz> Network_Usage_Bytes` | `generic_data_inc` | `Bytes` | Bytes recibidos más bytes transmitidos por esa interfaz, acumulados |
| `<PREFIX>Network_Usage_Bytes_Total` | `generic_data_inc` | `Bytes` | Suma de los valores anteriores sobre las interfaces seleccionadas |

`<PREFIX>` es el valor de `--module_prefix`, vacío por defecto. Al nombre de la
interfaz le sigue un espacio y `Network_Usage_Bytes`, así que un host con `eth0`
y `eth1` y sin prefijo produce `eth0 Network_Usage_Bytes`,
`eth1 Network_Usage_Bytes` y `Network_Usage_Bytes_Total`.

El plugin no envía grupo de módulos, ni intervalo, ni umbrales: los módulos se
muestrean con el intervalo del agente, y cualquier alerta o agrupación se
configura en la consola sobre ellos.

### Qué significa el valor

Cada módulo lleva el contador del núcleo tal cual, que es lo que el host ha
acumulado desde que la interfaz se levantó, y el tipo de módulo es
**incremental**. Por tanto Pandora FMS registra el crecimiento entre dos muestras
consecutivas, no la cifra acumulada: una interfaz que lleva semanas funcionando
informa de un contador de miles de millones, mientras que el valor guardado es el
tráfico del último intervalo. Hacen falta dos muestras consecutivas para que
exista algún incremento.

El total se calcula después de los filtros, así que siempre coincide con los
módulos de interfaz de esa misma ejecución. Un host cuya selección esté vacía
informa de un total de `0`, que es el único módulo de esa ejecución.

No hay módulo de disponibilidad ni de estado. Cuando el plugin no puede leer
`/proc/net/dev`, no imprime ningún módulo y los módulos existentes simplemente no
reciben datos nuevos.

El texto de descripción de todos los módulos dice `Total bytes/sec transfered in
this system`, que describe el incremento derivado en la consola, no el contador
que imprime el plugin.

## Operar y resolver problemas

### Operación diaria

- El plugin no guarda estado: cada ejecución lee los contadores de ese momento,
  así que se puede ejecutar a mano en cualquier instante sin alterar los módulos
  del agente.
- Lo programa el agente. Elija el intervalo del agente según la resolución que
  necesite: el incremento guardado cubre el intervalo entre dos ejecuciones.
- Los nombres de interfaz forman parte de los nombres de módulo. Cuando una
  interfaz se renombra —un esquema nuevo de nombres de NIC, una interfaz virtual
  nueva—, los módulos anteriores dejan de recibir datos y aparecen otros. Mantenga
  estables los filtros y el prefijo para evitarlo.
- Los contadores vuelven a cero cuando el host se reinicia o cuando una interfaz
  se cae y se levanta. La muestra siguiente lleva un valor menor que el anterior;
  no es tráfico real.

### Resolución de problemas

- **No aparecen módulos en el agente** — compruebe que la línea `module_plugin`
  apunta al ejecutable que realmente está en el directorio de plugins y que el
  archivo tiene permiso de ejecución; después ejecútelo a mano. Recuerde que el
  paquete del agente incluye un plugin con el mismo nombre (ver
  [Instalar el plugin](#instalar-el-plugin)).
- **La ejecución imprime `Error:` y nada más** — no se ha podido leer
  `/proc/net/dev`. Confirme que el host es Linux, que el archivo existe y que el
  usuario del agente puede leerlo. El mensaje va a la salida estándar y el código
  de salida es `0`, así que el fallo pasa desapercibido en una ejecución
  programada: el agente ve una ejecución correcta y no registra nada. Busque el
  mensaje, no el código de salida.
- **La ejecución no imprime módulos y avisa de un error en el patrón** — una de
  las dos expresiones regulares no es válida. Pruebe cada patrón por separado.
  Bajo el agente, una ejecución que termina con un código distinto de cero ve
  descartada su salida y solo queda registrado el código de error, y la salida de
  errores de un plugin no se conserva: ejecute el comando a mano para leer el
  mensaje.
- **El total es `0`** — los filtros excluyen todas las interfaces. Simplifique
  `--allow_regexp`, o quite `--deny_regexp`, y vuelva a ejecutar el plugin.
- **El tráfico de loopback domina las cifras** — la interfaz de loopback se mide
  como cualquier otra. Exclúyala con `--deny_regexp "^lo$"`.
- **Aparecen módulos llamados `Network_Usage_Bytes` en lugar de los documentados** —
  ese nombre de módulo pertenece al plugin incluido en el paquete del agente, no a
  este addon. Compruebe qué ejecutable lanza la línea `module_plugin`.
- **Un módulo dejó de actualizarse tras un cambio de red** — el nombre de la
  interfaz ha cambiado. Compare los nombres de módulo con las interfaces actuales
  y ajuste los filtros.

## Referencia

### Parámetros de la línea de comandos

| Nombre | Obligatorio | Valor por defecto | Descripción |
| --- | --- | --- | --- |
| `--module_prefix` | No | Vacío | Texto colocado inmediatamente antes de cada nombre de módulo, sin separador añadido. |
| `--allow_regexp` | No | Vacío (todas las interfaces) | Expresión regular buscada en el nombre de la interfaz; solo se miden las que coinciden. Ancle con `^` y `$` para coincidir con el nombre completo. |
| `--deny_regexp` | No | Vacío (nada excluido) | Expresión regular buscada en el nombre de la interfaz; las que coinciden se excluyen. Se aplica después de `--allow_regexp`, así que gana cuando coinciden las dos. |
| `-h`, `--help` | No | — | Imprime el resumen de uso, con la versión y las tres opciones, y termina. |

Todas las opciones son opcionales y ninguna toma un valor obligatorio. Las
opciones se dan en la forma `--nombre valor`; también se acepta `--nombre=valor`.

### Módulos generados

| Nombre del módulo | Tipo | Unidad | Descripción enviada por el plugin |
| --- | --- | --- | --- |
| `<PREFIX><interfaz> Network_Usage_Bytes` | `generic_data_inc` | `Bytes` | `Total bytes/sec transfered in this system` |
| `<PREFIX>Network_Usage_Bytes_Total` | `generic_data_inc` | `Bytes` | `Total bytes/sec transfered in this system (all interfaces)` |

Los módulos por interfaz se emiten en el orden en que `/proc/net/dev` lista las
interfaces; el total es siempre el último bloque de la ejecución.

### Salida y código de salida

| Situación | Salida | Código de salida |
| --- | --- | --- |
| Ejecución correcta | Un bloque `<module>` por interfaz seleccionada y el bloque del total, en la salida estándar | `0` |
| `--help` | Resumen de uso en la salida estándar | `0` |
| Opción desconocida o línea de comandos mal formada | Error de uso en la salida de errores | `2` |
| No se puede leer `/proc/net/dev` | `Error: ` seguido del error del comando, en la salida estándar, y ningún módulo | `0` |
| Expresión regular no válida | Error en la salida de errores y ningún módulo | Distinto de cero |
| Interrumpido con `Ctrl+C` o `SIGTERM` | `Signal received, exiting cleanly...` | `0` |

### Identidad del addon

| Propiedad | Valor |
| --- | --- |
| Identificador del Marketplace | `pandorafms.pandora_netusage` |
| Nombre | Net usage |
| Versión | `1.1` — la versión del paquete del Marketplace `pandorafms.pandora_netusage.1.1.zip`, que también aparece en el resumen de uso |
| Categoría | Miscelaneus |
| Licencia | One; la descarga está limitada a usuarios con licencia |
| Última actualización en el Marketplace | 2026-02-05 |
| Entrada del Marketplace | [pandorafms.pandora_netusage](https://marketplace.pandorafms.com/entries/pandorafms.pandora_netusage) |
| Flujo de trabajo | Plugin de monitorización, ejecutado por el agente de Pandora FMS |
| Ejecutable | `pandora_netusage` |
