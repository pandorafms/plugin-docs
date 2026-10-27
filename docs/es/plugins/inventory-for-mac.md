# Inventory plugin for MAC

*Última actualización del artículo: 2026-10-26.*

## Qué hace

El addon Inventory plugin for MAC recoge el inventario de hardware y software de
un endpoint macOS y lo publica en Pandora FMS. Cada ejecución lee el modelo de
procesador, la memoria, las particiones de disco, los puertos de red y el
contenido de `/Applications`, y escribe el resultado como un documento de
inventario por la salida estándar.

El addon tiene un único modelo de ejecución: **plugin de agente**. No acepta
argumentos ni lee ningún archivo de configuración. El agente de Pandora FMS lo
ejecuta desde su archivo de configuración en cada ejecución del agente y reenvía
el documento de inventario a Pandora FMS, donde los datos aparecen en la vista de
inventario del agente.

El addon solo produce datos de inventario. No crea módulos de monitorización, de
modo que no añade gráficas, umbrales ni alertas.

## Preparación

### Compatibilidad y disponibilidad

| Alcance | Estado | Evidencia |
| --- | --- | --- |
| Addon `pandorafms.mac_inventory`, versión `1.0` | Objetivo documentado | Versión de la entrada del Marketplace. Consulte [Identidad del addon](#identidad-del-addon) |
| Un endpoint macOS | `Requerido` | El addon lee utilidades del sistema macOS que solo existen en macOS |
| El agente de Pandora FMS para macOS, capaz de ejecutar entradas `module_plugin` y reenviar datos de inventario | `Requerido` | El addon se inicia desde el archivo de configuración del agente |
| Un intérprete `perl` para el usuario que ejecuta el agente | `Requerido` | El agente inicia el addon mediante `perl` (consulte [Añadir el plugin al agente](#anadir-el-plugin-al-agente)) |
| Las utilidades macOS `sysctl`, `system_profiler`, `top`, `diskutil`, `networksetup` y `ls` | `Requerido` | Comandos de [Módulos de inventario generados](#modulos-de-inventario-generados) |
| macOS 10.13 High Sierra | `Sin validar` | No existe un registro reproducible para este addon |
| macOS 10.14 Mojave | `Sin validar` | No existe un registro reproducible para este addon |
| Cualquier otra versión de macOS | `Sin validar` | No hay una matriz de versiones registrada para este addon |
| Versión de Pandora FMS | `Sin validar` | No existe un registro específico por versión. El Marketplace indica que sus integraciones son compatibles con Pandora FMS NG 784 y posteriores |

La guía que sustituye esta página indica macOS High Sierra y macOS Mojave, con la
versión 755 del agente de Pandora FMS, como entorno probado. Ese registro no
puede reproducirse a partir del addon y aquí no se presenta como una declaración
de compatibilidad validada: las versiones de macOS de la tabla siguen en
`Sin validar` hasta que exista un registro de pruebas de este addon.

### Requisitos

1. **Un endpoint macOS** monitorizado por un agente de Pandora FMS.
2. **El agente de Pandora FMS para macOS**, instalado y reportando al servidor de
   Pandora FMS, y capaz de ejecutar entradas `module_plugin` y reenviar su salida
   de inventario.
3. **Un intérprete `perl`** disponible para el usuario y el entorno que ejecutan
   el agente.
4. **Las utilidades estándar de macOS** que llama el addon: `sysctl`,
   `system_profiler`, `top`, `diskutil`, `networksetup` y `ls`. No hay que
   instalar software adicional en el endpoint.
5. **Los cinco módulos de inventario** creados en Pandora FMS antes de la primera
   ejecución (consulte [Crear los módulos de inventario](#crear-los-modulos-de-inventario)).

### Instalar el plugin

Descargue el paquete desde la entrada del Marketplace de Pandora FMS, limitada a
usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.mac_inventory](https://marketplace.pandorafms.com/entries/pandorafms.mac_inventory)

La entrada distribuye la versión `1.0` como `pandorafms.mac_inventory.1.0.zip`.
Copie el archivo del plugin `mac_inventory.pl` al endpoint macOS, por ejemplo en
`/usr/local/pandora/mac_inventory.pl`, y dele permiso de lectura al usuario que
ejecuta el agente. No hay nada más que instalar: el addon no tiene dependencias
propias ni archivo de configuración.

## Configuración

### Crear los módulos de inventario

El addon suministra datos para cinco módulos de inventario, y Pandora FMS guarda
los datos de inventario en los módulos de inventario que ya existen. Cree estos
cinco módulos en la consola antes de la primera ejecución, con estos nombres
exactos:

| Módulo de inventario | Contenido |
| --- | --- |
| `CPU` | Modelo de procesador |
| `RAM` | Memoria instalada y uso de memoria actual |
| `DISK` | Particiones de disco |
| `CARDS` | Puertos de red |
| `APPS` | Contenido de `/Applications` |

El nombre es el vínculo entre el addon y la consola: se compara de forma exacta,
en mayúsculas, y el módulo de disco es `DISK` en singular, no `DISKS`. Un módulo
de inventario con otro nombre no recibe datos, y el addon no informa de esa
discrepancia.

<!-- SCREENSHOT NEEDED: Formulario de definición de módulo de inventario de Pandora FMS relleno con el nombre CPU, sin datos de cliente. -->

### Añadir el plugin al agente

Añada una línea al final del archivo de configuración del agente
`pandora_agent.conf` en el endpoint macOS:

```text
module_plugin perl /usr/local/pandora/mac_inventory.pl
```

Después, reinicie el agente. La línea indica el intérprete, `perl`, y la ruta del
archivo del plugin; use una ruta sin espacios. Esta es toda la configuración: el
addon no tiene parámetros, ni archivo de configuración, ni variables de entorno,
ni opciones, y el agente no le pasa argumentos.

`module_plugin` se ejecuta en cada ejecución del agente, así que el inventario se
recoge cada vez que el agente reporta. El addon no tiene intervalo ni
planificación propios: el intervalo del agente determina con qué frecuencia se
actualiza el inventario.

## Verificación

### Ejecutar el plugin manualmente

Ejecute el addon desde un terminal del endpoint, como el usuario que ejecuta el
agente:

```bash
perl /usr/local/pandora/mac_inventory.pl
```

Una ejecución correcta escribe un documento `<inventory>` con los cinco bloques
`<inventory_module>` y termina con estado `0`. Esta es la forma de la salida; los
valores son ilustrativos:

```xml
<inventory>
<inventory_module>
<name><![CDATA[CPU]]></name>
<datalist>
<data><![CDATA[Apple M1]]></data>
</datalist>
</inventory_module>
<inventory_module>
<name><![CDATA[RAM]]></name>
<datalist>
<data><![CDATA[      Memory: 16 GB]]></data>
<data><![CDATA[PhysMem: 12G used (2100M wired), 3900M unused.]]></data>
</datalist>
</inventory_module>
<inventory_module>
<name><![CDATA[DISK]]></name>
<datalist>
<data><![CDATA[   0:      GUID_partition_scheme                        *500.3 GB   disk0]]></data>
<data><![CDATA[   1:                        EFI EFI                     209.7 MB   disk0s1]]></data>
</datalist>
</inventory_module>
<inventory_module>
<name><![CDATA[CARDS]]></name>
<datalist>
<data><![CDATA[Hardware Port: Wi-Fi]]></data>
<data><![CDATA[Device: en0]]></data>
</datalist>
</inventory_module>
<inventory_module>
<name><![CDATA[APPS]]></name>
<datalist>
<data><![CDATA[drwxr-xr-x  3 root  wheel  96 Jan  1 00:00 Example.app]]></data>
</datalist>
</inventory_module>
</inventory>
```

El addon escribe el documento sin cabecera, sin mensajes de registro y sin
opciones. Cuando falla un comando al que llama, el error va a la salida de
error —y por tanto al registro del agente— mientras que el documento se sigue
escribiendo.

### Comprobar el inventario en la consola

Tras la siguiente ejecución del agente, abra la vista de inventario del agente
macOS en la consola de Pandora FMS. Los cinco módulos aparecen con los datos
recogidos en esa ejecución.

<!-- SCREENSHOT NEEDED: Vista de inventario del agente macOS en la consola, con los módulos CPU, RAM, DISK, CARDS y APPS y sus datos. -->

## Entender los resultados

Cada ejecución escribe los mismos cinco módulos de inventario, en este orden:
`CPU`, `RAM`, `DISK`, `CARDS` y `APPS`. Cada módulo contiene una lista de datos
cuyas entradas son las líneas de salida en bruto del comando que lo alimenta. El
addon no las analiza, convierte ni normaliza, así que cada entrada es texto tal y
como lo imprimió el comando.

- **`CPU`.** Una entrada con la cadena de modelo que informa el sistema.
- **`RAM`.** Dos entradas con dos lecturas distintas: la línea de memoria
  instalada de `system_profiler`, con su etiqueta y su sangría, y una instantánea
  del uso de memoria actual de `top`. Ambas conviven en el mismo módulo.
- **`DISK`.** Una entrada por cada línea de partición de `diskutil list`,
  incluida la línea del esquema de particiones de cada disco. El tamaño y el
  identificador del disco quedan dentro de la línea en bruto. Las líneas de
  cabecera del disco completo, como `/dev/disk0 (internal, physical):`, no
  coinciden y no se incluyen.
- **`CARDS`.** Una entrada por cada línea de la salida de
  `networksetup -listallhardwareports`, de modo que el módulo contiene el puerto
  de hardware, el dispositivo y la dirección de enlace de cada puerto. Las líneas
  en blanco de la salida del comando se convierten en entradas vacías.
- **`APPS`.** Una entrada por cada línea de `ls -l /Applications`: permisos,
  propietario, grupo, tamaño, fecha y nombre del bundle. Solo cubre
  `/Applications`, así que las aplicaciones instaladas en cualquier otra
  ubicación no aparecen.

Como las entradas son texto en bruto, los datos son informativos: no se pueden
representar en gráficas ni admiten umbrales, el módulo `RAM` mezcla dos formatos
en un mismo módulo, `CARDS` publica las direcciones de hardware del endpoint y
`APPS` publica los nombres de propietario de los archivos de las aplicaciones.

## Operación y diagnóstico

### Comportamiento en ejecución

- Una ejecución lee, imprime y termina. El addon no guarda estado entre
  ejecuciones, así que cada ejecución informa del inventario de ese momento.
- No escribe nada en disco ni abre conexiones de red: el documento va a la salida
  estándar, que el agente lee; lo que un comando escriba en la salida de error va
  al registro del agente.
- No lee argumentos. Cualquier argumento que reciba se ignora, y no tiene opción
  `-h` ni `--help`.
- Se ejecuta en cada ejecución del agente, porque así funciona `module_plugin`.
- Cada ejecución lanza `system_profiler` y `top -l 1`, que muestrean el sistema
  bajo demanda, así que elija el intervalo del agente teniendo en cuenta ese
  coste.

### Limitaciones conocidas

Estos son comportamientos de la versión `1.0`, documentados tal y como son.

- **Los nombres de módulo son fijos y se comparan de forma exacta.** `DISK` va en
  singular y todos los nombres en mayúsculas. Los datos de un nombre que no tenga
  un módulo de inventario correspondiente en la consola no tienen destino en el
  inventario, y el addon no lo informa.
- **El addon no gestiona errores.** Termina con estado `0` incluso cuando falla
  un comando al que llama. Cuando falta un comando o no devuelve nada, el módulo
  correspondiente se sigue escribiendo, con entradas vacías o parciales, y no se
  omite ningún módulo.
- **En un host que no sea macOS el resultado está vacío.** Los comandos no
  existen, así que los cinco módulos se escriben con listas de datos vacías y los
  errores de los comandos van a la salida de error.
- **Ejecutar el archivo directamente depende de su línea de intérprete.** Esa
  línea indica `/usr/bin/Perl`, con `P` mayúscula, que se resuelve en el volumen
  macOS predeterminado, insensible a mayúsculas, pero no en uno sensible a
  mayúsculas. Inicie el addon mediante `perl`, como hace la configuración del
  agente.
- **No hay filtrado ni límite.** Cada línea que imprimen los comandos se
  convierte en una entrada, así que el módulo `APPS` puede contener cientos de
  entradas en una estación de trabajo con muchas aplicaciones, y `CARDS` repite
  la disposición de la salida de `networksetup`, incluidas las líneas en blanco.
- **El inventario es solo texto.** No se crea ningún módulo numérico, así que no
  hay tendencia, ni umbral, ni superficie de alerta.

### Diagnóstico

| Síntoma | Causa y acción |
| --- | --- |
| La vista de inventario del agente no muestra datos | Falta la línea `module_plugin` en `pandora_agent.conf`, el agente no se ha ejecutado desde que se añadió la línea, o no existen los módulos de inventario. Compruebe la línea, reinicie el agente y cree los cinco módulos |
| Unos módulos tienen datos y otros no | El módulo de inventario que falta existe con otro nombre. La comparación es exacta: compruebe las mayúsculas y `DISK` en singular |
| `perl: command not found` en el registro del agente | El intérprete no está en el entorno del agente. Instálelo o corrija el `PATH` del agente |
| `diskutil: command not found`, `system_profiler: command not found` o similar en el registro del agente | El addon se está ejecutando en un host que no es macOS |
| Un módulo tiene entradas vacías | El comando que lo alimenta no imprimió nada para esa entrada, por ejemplo una línea en blanco en la salida de `networksetup` |
| Falta una aplicación en `APPS` | No está instalada en `/Applications` |
| Los datos no cambian entre ejecuciones | Los valores son estables en el endpoint, o el agente no está ejecutando el plugin: compruebe el intervalo y el registro del agente |

## Referencia

### Configuración del agente

| Directiva | Obligatoria | Valor |
| --- | --- | --- |
| `module_plugin` | Sí | `perl /usr/local/pandora/mac_inventory.pl` |

La línea va en `pandora_agent.conf` del endpoint macOS y se aplica tras reiniciar
el agente. No hay otra superficie de entrada: ni archivo de configuración, ni
opciones de línea de comandos, ni variables de entorno, ni registro del plugin en
la consola.

### Ejecución por línea de comandos

| Comando | Comportamiento |
| --- | --- |
| `perl /usr/local/pandora/mac_inventory.pl` | Escribe el documento de inventario y termina con estado `0` |
| `perl /usr/local/pandora/mac_inventory.pl -h` | La misma salida: el addon no lee argumentos y no tiene opción de ayuda |

### Módulos de inventario generados

| Módulo | Origen | Entradas |
| --- | --- | --- |
| `CPU` | `sysctl -n machdep.cpu.brand_string` | Una: la cadena de modelo del procesador |
| `RAM` | `system_profiler SPHardwareDataType` (línea de memoria) y `top -l 1 -s 0` (línea PhysMem) | Dos: memoria instalada y uso de memoria actual |
| `DISK` | `diskutil list` (líneas de partición) | Una por línea de partición, incluida la línea del esquema de particiones |
| `CARDS` | `networksetup -listallhardwareports` | Una por línea de salida, incluidas las líneas en blanco |
| `APPS` | `ls -l /Applications` | Una por línea de salida |

Estos son los comandos exactos de cada módulo:

```text
CPU    sysctl -n machdep.cpu.brand_string
RAM    system_profiler SPHardwareDataType | grep "Memory:"
RAM    top -l 1 -s 0 | grep PhysMem
DISK   diskutil list | grep -E "[ ]+[0-9]+:.*disk[0-9]+"
CARDS  networksetup -listallhardwareports
APPS   ls -l /Applications
```

### Identidad del addon

| Propiedad | Valor |
| --- | --- |
| Identificador del Marketplace | `pandorafms.mac_inventory` |
| Nombre | Inventory plugin for MAC |
| Versión | `1.0` |
| Categoría | Miscelaneus |
| Licencia | One |
| Última actualización en el Marketplace | 2025-06-26 |
| Disponibilidad | Descarga limitada a usuarios con licencia |
