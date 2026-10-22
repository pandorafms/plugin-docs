# Network bandwidth SNMP

*Última actualización del artículo: 2026-09-30.*

## Qué hace

El plugin Network bandwidth SNMP obtiene mediante SNMP el uso de ancho de banda de un dispositivo de red, expresado como porcentaje. Informa de la cantidad de información enviada y recibida durante un periodo determinado, ya sea para todo el dispositivo o para una única interfaz seleccionada por su índice.

El plugin se ejecuta como plugin de servidor de Pandora FMS: cada ejecución consulta el dispositivo, imprime un único valor numérico en la salida estándar y Pandora FMS almacena ese valor en el módulo.

- **Resultado.** Un único número, el uso de ancho de banda como porcentaje, con 9 decimales (por ejemplo `12.345678901`).
- **Qué se mide.** Por defecto, el uso global de ancho de banda. Con `-inUsage 1` informa solo del uso de entrada y con `-outUsage 1` solo del uso de salida. Si ambos están activados, se informa del uso de entrada.
- **Alcance.** Con `-ifIndex <n>` el plugin mide esa interfaz. Sin esta opción, mide todas las interfaces del dispositivo e imprime la media de los porcentajes por interfaz, calculada sobre las interfaces que tienen una velocidad utilizable.
- **Ventana de medida.** El valor se calcula a partir de la diferencia entre los contadores leídos en la ejecución actual y los almacenados por la ejecución anterior. Por tanto, el intervalo del módulo es la ventana de medida.

## Preparación

### Requisitos

1. **Acceso de lectura SNMP al dispositivo** desde el equipo que ejecuta el plugin, normalmente el servidor de Pandora FMS. El puerto SNMP por defecto es UDP 161.
2. **Un dispositivo que exponga los objetos de IF-MIB** `ifIndex`, `ifInOctets`, `ifOutOctets`, `ifHighSpeed` e `ifSpeed`, y preferiblemente los contadores de 64 bits `ifHCInOctets` e `ifHCOutOctets`. El objeto `dot3StatsDuplexStatus` de EtherLike-MIB es opcional y se utiliza para detectar el modo dúplex.
3. **Permiso de escritura en el directorio temporal** (`/tmp` por defecto) para el usuario que ejecuta el plugin. El plugin guarda allí los contadores de cada ejecución para calcular la siguiente.

### Instalación

El plugin se distribuye con el servidor de Pandora FMS y no requiere una instalación aparte. Su ejecutable es:

```text
/usr/share/pandora_server/util/plugin/pandora_snmp_bandwidth
```

Está registrado en Pandora FMS como el plugin de servidor **Network bandwidth SNMP**, con un tiempo de espera máximo de 300 segundos.

### Elegir la versión de SNMP

- **SNMP v1** utiliza siempre contadores de 32 bits, porque los contadores de 64 bits no existen en SNMP v1.
- **SNMP v2c y v3** utilizan contadores de 64 bits cuando el dispositivo los proporciona.

En enlaces rápidos, prefiera SNMP v2c o v3. Un contador de octetos de 32 bits se desborda tras 4.294.967.295 octetos, lo que ocurre en unos 34 segundos a 1 Gbit/s. El plugin corrige como máximo un desbordamiento por intervalo, de modo que los intervalos largos en enlaces rápidos con contadores de 32 bits informan de valores inferiores a los reales.

## Configuración

Cree un módulo por cada métrica y cada interfaz que desee monitorizar, utilizando el plugin de servidor **Network bandwidth SNMP**, y rellene los campos del plugin. El plugin devuelve un porcentaje numérico; elija los umbrales que se ajusten a su entorno.

1. Indique **SNMP Version(1,2c,3)** (`1`, `2c` o `3`) y las credenciales correspondientes a esa versión.
   - Para SNMP v1 y v2c, rellene **Community**.
   - Para SNMP v3, rellene **securityName** y, según **securityLevel**, los campos de autenticación y privacidad. Consulte [Parámetros de SNMPv3](#parametros-de-snmpv3).
2. Deje **Host** con su valor por defecto `_address_`, que es la dirección del agente, o introduzca la dirección del dispositivo.
3. Indique **Port** si el dispositivo no utiliza el puerto 161 por defecto.
4. Rellene **Interface Index (filter)** con el `ifIndex` de la interfaz que se va a medir. Déjelo vacío para medir todas las interfaces y obtener su media.
5. Seleccione la métrica:
   - Uso global de ancho de banda: deje **inUsage** y **outUsage** vacíos.
   - Uso de entrada: indique `1` en **inUsage**.
   - Uso de salida: indique `1` en **outUsage**.
6. Indique en **UniqId** un identificador único para cada módulo, sin espacios ni símbolos.
7. Ajuste **timeout** (segundos por intento) y **retries** si el dispositivo responde con lentitud.

!!! warning "Cada módulo necesita su propio UniqId"
    El plugin guarda los contadores de la ejecución anterior en un archivo de estado que se nombra según el host o, si se indica, según el **UniqId**. Todos los módulos que utilicen el plugin contra el mismo host deben tener un **UniqId** distinto. En caso contrario, los módulos se sobrescriben mutuamente las muestras anteriores e informan de `0` o de valores incorrectos.

### Parámetros de SNMPv3

| Campo | Comportamiento |
| --- | --- |
| **securityName** | Obligatorio para SNMP v3. |
| **securityLevel** | `noAuthNoPriv` (por defecto), `authNoPriv` o `authPriv`. No distingue mayúsculas de minúsculas. |
| **authProtocol**, **authKey** | Obligatorios con `authNoPriv` y `authPriv`. |
| **privProtocol**, **privKey** | Obligatorios con `authPriv`. |
| **context** | Nombre de contexto SNMPv3 opcional. Déjelo vacío para no utilizar contexto. |

Una combinación o un valor no válidos hacen que el plugin no imprima nada.

Para los protocolos AES de 192 y 256 bits, elija el que corresponda a la variante de localización de claves que implementa el dispositivo: `AES192` y `AES256` utilizan la extensión Blumenthal (estilo Net-SNMP), mientras que `AES192C` y `AES256C` utilizan la extensión Reeder (estilo Cisco).

### Opciones no disponibles en la consola

Las opciones `-max`, `-f`, `-debug`, `-parallel`, `-tmp`, `-tmp_file`, `-tmp_separator` y `-log` no son campos del registro del plugin. Solo pueden utilizarse desde la línea de comandos o desde un archivo de configuración. Consulte [Operación](#operacion) y [Referencia](#referencia).

### Proteger las credenciales

La comunidad y las contraseñas de SNMPv3 pasadas como opciones de línea de comandos pueden ser visibles en la lista de procesos del sistema operativo. Para mantenerlas fuera de la línea de comandos, guárdelas en un archivo de configuración y pase su ruta como primer argumento. Consulte [Usar un archivo de configuración](#usar-un-archivo-de-configuracion).

## Verificación

Ejecute el plugin manualmente con un `-uniqid` distinto del que utilice cualquier módulo de producción, para que la prueba no altere las muestras de ese módulo:

```bash
/usr/share/pandora_server/util/plugin/pandora_snmp_bandwidth -version 2c -community <COMMUNITY> -host <TARGET_HOST> -ifIndex <IFINDEX> -uniqid <UNIQUE_ID>
```

1. La primera ejecución imprime `0.000000000`, porque todavía no hay datos anteriores.
2. Espere unos segundos mientras la interfaz cursa tráfico y ejecute de nuevo el mismo comando. La segunda ejecución imprime el valor real, por ejemplo `12.345678901`.

Una salida vacía indica que el plugin ha fallado. Ejecute de nuevo el comando con `-debug 1` y lea el archivo de registro, como se describe en [Registro de depuración](#registro-de-depuracion).

## Interpretación de los resultados

### Salida y código de salida

- El plugin termina siempre con código de salida 0.
- Ante un fallo (sin respuesta SNMP, parámetros no válidos, dispositivo inaccesible) no imprime nada.
- Si se ejecuta sin argumentos, imprime el texto de ayuda.

### Significado del valor

Para cada interfaz, el plugin calcula un porcentaje a partir de las diferencias de los contadores de octetos (`Δin`, `Δout`), los segundos transcurridos entre ejecuciones (`Δt`) y la velocidad de la interfaz en bit/s:

| Métrica | Fórmula |
| --- | --- |
| Ancho de banda, dúplex medio o dúplex desconocido | `(Δin + Δout) × 8 / (Δt × speed) × 100` |
| Ancho de banda, dúplex completo | `(Δin × 8 / (Δt × speed) + Δout × 8 / (Δt × speed)) / 2 × 100` |
| Uso de entrada | `Δin × 8 / (Δt × speed) × 100`, limitado a 100 |
| Uso de salida | `Δout × 8 / (Δt × speed) × 100`, limitado a 100 |

- Si la velocidad o `Δt` es 0, el valor de la interfaz es 0.
- Si un contador es menor que en la ejecución anterior, el plugin lo trata como un desbordamiento y calcula la diferencia como `max − previous + current + 1`, donde `max` es 4.294.967.295 para contadores de 32 bits y 18.446.744.073.709.551.615 para contadores de 64 bits.
- Sin `-ifIndex`, el resultado es la media aritmética de los valores por interfaz.

### Primera ejecución y valores cero

El plugin imprime `0.000000000` cuando no dispone de datos anteriores de los contadores. Ocurre en la primera ejecución, después de que cambie el ancho de los contadores (por ejemplo, cuando el dispositivo deja de devolver valores de 64 bits) y la primera vez que el plugin se ejecuta sobre un archivo de estado escrito por una versión anterior del plugin.

### Ancho de los contadores

- Sin `-ifIndex`, el plugin lee la tabla de interfaces y utiliza los contadores de 64 bits `ifHCInOctets` e `ifHCOutOctets` cuando el dispositivo devuelve valores numéricos para `ifHCInOctets`. En caso contrario, utiliza los contadores de 32 bits `ifInOctets` e `ifOutOctets`.
- Con `-ifIndex <n>`, utiliza los contadores de 64 bits cuando `ifHCInOctets.<n>` devuelve un número y, en caso contrario, los de 32 bits.
- Con SNMP v1 utiliza siempre los contadores de 32 bits.

### Velocidad de la interfaz

La velocidad, en bit/s, se selecciona en este orden:

1. El valor de `-max`, cuando está definido. Sustituye a la velocidad informada por el dispositivo para todas las interfaces medidas y está pensado para port channels y enlaces agregados, en los que la velocidad informada no es la real.
2. `ifHighSpeed` (en Mbit/s) multiplicado por 1.000.000, cuando es mayor que 0.
3. `ifSpeed` (en bit/s), cuando es mayor que 0.

Una interfaz sin velocidad utilizable se omite: no se mide y no se incluye en la media. Con `-ifIndex`, en ese caso el plugin imprime `0.000000000`.

!!! warning "El valor de -max está en bit/s"
    `-max` se expresa en bit/s, no en Mbit/s, aunque `ifHighSpeed` se informe en Mbit/s. Para un port channel de 2 × 1 Gbit/s, utilice `-max 2000000000`. El valor `-max 2000` equivale a 2 kbit/s: el uso de entrada y de salida se satura al 100 % y el ancho de banda total informa valores muy superiores a 100.

### Modo dúplex

El plugin lee el modo dúplex de `dot3StatsDuplexStatus`: el valor `2` significa dúplex medio y `3` dúplex completo. Cualquier otro valor, o la ausencia de respuesta, es un modo dúplex desconocido, que se trata como dúplex medio. Utilice `-f 1` para tratar un modo dúplex desconocido como dúplex completo.

### Valores de ifIndex duplicados

Cuando el plugin mide todas las interfaces, identifica cada interfaz por el valor de `ifIndex`. Si el dispositivo informa del mismo valor en varias filas, el plugin conserva una única entrada para ese valor:

- La última fila que tiene una velocidad utilizable sustituye a las anteriores.
- Una fila posterior sin velocidad utilizable no elimina una anterior válida.
- El archivo de estado tiene una línea por cada valor distinto y la media se divide por el número de valores distintos.

## Operación

### Usar un archivo de configuración

Si el primer argumento es un archivo existente, el plugin lo lee como archivo de configuración. Utilícelo para mantener las credenciales fuera de la línea de comandos:

```bash
/usr/share/pandora_server/util/plugin/pandora_snmp_bandwidth <PATH_TO_CONFIG> -ifIndex 5
```

- Cada línea tiene la forma `key=value`. Las claves son los nombres de las opciones sin el guion inicial.
- Las líneas que empiezan por `#` son comentarios.
- La directiva `include=<file>` incluye otro archivo.
- Las opciones indicadas en la línea de comandos prevalecen sobre los valores del archivo.

### Registro de depuración

Con `-debug 1`, el plugin escribe un archivo de registro mientras se ejecuta. El valor impreso en la salida estándar no cambia.

- El archivo es `<tmp>/pandora_bandwidth_<host o uniqid>.log`, con la misma sustitución de caracteres que el archivo de estado (consulte [Archivo de estado](#archivo-de-estado)). Utilice `-log` para escribirlo en otra ruta.
- Cada línea tiene la forma `<date> - [info] <message>`. El primer mensaje de una ejecución trunca el archivo.
- El registro incluye el destino, la versión de SNMP, el tiempo de espera y los reintentos, el archivo de estado, cada petición y respuesta SNMP con sus tiempos, el ancho de contador seleccionado y el motivo, el origen de la velocidad y el modo dúplex de cada interfaz, las interfaces omitidas y el motivo, el estado anterior y el guardado, las fórmulas con sus valores sustituidos, las medias y el valor impreso.
- La comunidad, las contraseñas de autenticación y privacidad y el usuario de SNMPv3 no se escriben nunca en el registro. Los valores secretos se enmascaran como `***` si llegan a aparecer.

### Concurrencia y tiempos

- `-parallel <N>` define el número máximo de peticiones SNMP concurrentes cuando se miden todas las interfaces. El valor por defecto es 8. Un valor que no sea un entero positivo mantiene el valor por defecto.
- `-timeout` define los segundos de espera por intento y `-retries` el número de reintentos. Los valores fuera de rango hacen que el plugin no imprima nada.
- Mantenga el intervalo del módulo lo bastante corto para que un contador de 32 bits no pueda desbordarse más de una vez entre ejecuciones.

### Sintaxis de línea de comandos

- Las opciones son pares `-nombre valor`. Una opción final sin valor se ignora.
- Las opciones booleanas (`-inUsage`, `-outUsage`, `-f`, `-debug`) se activan con un número mayor que 0, por ejemplo `1`.
- Las opciones de conexión tienen alias cortos. Consulte [Opciones de línea de comandos y archivo de configuración](#opciones-de-linea-de-comandos-y-archivo-de-configuracion).
- La opción `-extra` se acepta y se ignora.

### Comprobación de conectividad

Antes de medir nada, el plugin lee `sysObjectID` (`.1.3.6.1.2.1.1.2.0`) del dispositivo. Si el dispositivo no responde, el plugin se detiene sin imprimir nada.

## Resolución de problemas

- **El plugin no imprime nada.** El dispositivo no respondió a la petición de `sysObjectID`, algún parámetro no es válido, `-timeout` o `-retries` están fuera de rango, o la configuración de SNMPv3 está incompleta. Ejecute el plugin con `-debug 1` y lea el [registro de depuración](#registro-de-depuracion).
- **El valor es siempre 0.**
  - Es la primera ejecución y la segunda todavía no se ha realizado.
  - Otro módulo utiliza el mismo **UniqId** (o el mismo host sin **UniqId**) y ambos se sobrescriben las muestras anteriores. Asigne a cada módulo su propio **UniqId**.
  - La interfaz no tiene una velocidad utilizable. Consulte "La interfaz no se mide" más abajo.
  - El tiempo transcurrido entre ejecuciones es 0.
  - El ancho de los contadores cambió desde la ejecución anterior.
- **El uso de entrada o de salida se queda fijo en el 100 %, o el ancho de banda supera el 100 %.** La velocidad utilizada es demasiado baja. Compruebe que `-max` se expresa en bit/s y no en Mbit/s, y revise los valores de `ifHighSpeed` e `ifSpeed` que informa el dispositivo.
- **Los valores son inferiores a los esperados en un enlace rápido.** El plugin utiliza contadores de 32 bits que se desbordan más de una vez por intervalo. Utilice SNMP v2c o v3 para que se usen contadores de 64 bits, o acorte el intervalo del módulo.
- **La interfaz no se mide.** Ni `ifHighSpeed` ni `ifSpeed` son mayores que 0. Defina la velocidad con `-max`.
- **El modo dúplex es desconocido.** Si el enlace es dúplex completo, utilice `-f 1`.

## Referencia

### Campos de la consola (Network bandwidth SNMP)

| Campo | Obligatorio | Valor por defecto | Descripción |
| --- | --- | --- | --- |
| SNMP Version(1,2c,3) | No | `2c` | Versión de SNMP: `1`, `2c` o `3`. Se pasa como `-version`. |
| Community | Sí en v1 y v2c | — | Comunidad SNMP. Puede estar vacía. Se pasa como `-community`. |
| Host | No | `_address_` | Dirección del dispositivo. Por defecto, la dirección del agente. Se pasa como `-host`. |
| Port | No | `161` | Puerto UDP del servicio SNMP. Se pasa como `-port`. |
| Interface Index (filter) | No | Vacío | `ifIndex` de la interfaz que se va a medir. Vacío mide todas las interfaces. Se pasa como `-ifIndex`. |
| securityName | Sí en v3 | — | Nombre de usuario de SNMPv3. Se pasa como `-securityName`. |
| context | No | Vacío | Nombre de contexto SNMPv3. Vacío significa sin contexto. Se pasa como `-context`. |
| securityLevel | No | `noAuthNoPriv` | `noAuthNoPriv`, `authNoPriv` o `authPriv`. Se pasa como `-securityLevel`. |
| authProtocol | Sí con `authNoPriv` y `authPriv` | — | `MD5`, `SHA` (o `SHA1`), `SHA224`, `SHA256`, `SHA384` o `SHA512`. Se pasa como `-authProtocol`. |
| authKey | Sí con `authNoPriv` y `authPriv` | — | Contraseña de autenticación. Se pasa como `-authKey`. |
| privProtocol | Sí con `authPriv` | — | `DES`, `AES` (o `AES128`), `AES192`, `AES256`, `AES192C` o `AES256C`. Se pasa como `-privProtocol`. |
| privKey | Sí con `authPriv` | — | Contraseña de privacidad. Se pasa como `-privKey`. |
| UniqId | Sí, uno por módulo | — | Identificador único del módulo, sin espacios ni símbolos. El plugin necesita guardar información en el directorio temporal para calcular el ancho de banda. Se pasa como `-uniqid`. |
| inUsage | No | Vacío | Indique `1` para obtener el uso de entrada (%). Se pasa como `-inUsage`. |
| outUsage | No | Vacío | Indique `1` para obtener el uso de salida (%). Se pasa como `-outUsage`. |
| timeout | No | `2` | Segundos de espera por intento. Se pasa como `-timeout`. |
| retries | No | `1` | Número de reintentos. Se pasa como `-retries`. |

El registro del plugin construye esta línea de parámetros:

```text
-version '_field1_' -community '_field2_' -host '_field3_' -port '_field4_' -ifIndex '_field5_' -securityName '_field6_' -context '_field7_' -securityLevel '_field8_' -authProtocol '_field9_' -authKey '_field10_' -privProtocol '_field11_' -privKey '_field12_' -uniqid '_field13_' -inUsage '_field14_' -outUsage '_field15_' -timeout '_field16_' -retries '_field17_'
```

### Opciones de línea de comandos y archivo de configuración

Los mismos nombres son válidos como claves del archivo de configuración, sin el guion inicial.

| Nombre | Alias | Obligatorio | Valor por defecto | Descripción |
| --- | --- | --- | --- | --- |
| `-version` | `-v` | No | `2c` | Versión de SNMP: `1`, `2`, `2c` o `3`. |
| `-community` | `-c` | Sí en v1 y v2c | — | Comunidad SNMP. Puede estar vacía. |
| `-host` | `-h` | No | `127.0.0.1` | Dirección del dispositivo. |
| `-port` | `-p` | No | `161` | Puerto UDP, de 0 a 65535. |
| `-timeout` | — | No | `2` | Segundos por intento, de 1 a 60. Se admiten decimales. |
| `-retries` | — | No | `1` | Reintentos, de 0 a 20. |
| `-securityName` | `-u` | Sí en v3 | — | Nombre de usuario de SNMPv3. |
| `-context` | `-n` | No | Vacío | Nombre de contexto SNMPv3. |
| `-securityLevel` | `-l` | No | `noAuthNoPriv` | `noAuthNoPriv`, `authNoPriv` o `authPriv` (sin distinguir mayúsculas de minúsculas). |
| `-authProtocol` | `-a` | Sí con `authNoPriv` y `authPriv` | — | `MD5`, `SHA` (o `SHA1`), `SHA224`, `SHA256`, `SHA384` o `SHA512`. |
| `-authKey` | `-A` | Sí con `authNoPriv` y `authPriv` | — | Contraseña de autenticación. |
| `-privProtocol` | `-x` | Sí con `authPriv` | — | `DES`, `AES` (o `AES128`), `AES192`, `AES256`, `AES192C` o `AES256C` (sin distinguir mayúsculas de minúsculas). |
| `-privKey` | `-X` | Sí con `authPriv` | — | Contraseña de privacidad. |
| `-ifIndex` | — | No | Vacío | `ifIndex` de la interfaz que se va a medir. Sin esta opción se miden todas las interfaces y se calcula su media. |
| `-inUsage` | — | No | Desactivado | Un número mayor que 0 informa solo del uso de entrada. |
| `-outUsage` | — | No | Desactivado | Un número mayor que 0 informa solo del uso de salida. Si `-inUsage` también está activado, se informa del uso de entrada. |
| `-max` | — | No | Sin definir | Velocidad de la interfaz en bit/s, utilizada para todas las interfaces medidas en lugar de la velocidad informada por el dispositivo. |
| `-f` | — | No | Desactivado | Un número mayor que 0 trata un modo dúplex desconocido como dúplex completo. |
| `-uniqid` | — | No | Sin definir | Identificador que nombra el archivo de estado y el registro en lugar del host. Necesario en la práctica cuando varios módulos consultan el mismo host. |
| `-parallel` | — | No | `8` | Máximo de peticiones SNMP concurrentes cuando se miden todas las interfaces. |
| `-tmp` | — | No | `/tmp` | Directorio del archivo de estado y del registro. |
| `-tmp_file` | — | No | Sin definir | Ruta completa del archivo de estado. |
| `-tmp_separator` | — | No | `;` | Separador de campos del archivo de estado. |
| `-debug` | — | No | Desactivado | Un número mayor que 0 escribe el registro de depuración. |
| `-log` | — | No | Sin definir | Ruta del archivo de registro de depuración. |

### Archivo de estado

El plugin guarda los contadores de cada ejecución en un archivo de estado:

- Ruta por defecto: `<tmp>/pandora_bandwidth_<host>.idx`, o `<tmp>/pandora_bandwidth_<uniqid>.idx` cuando se indica `-uniqid`.
- Cada `.` de toda la ruta se sustituye por `_`. Para el host `192.0.2.10`, el archivo es `/tmp/pandora_bandwidth_192_0_2_10.idx`.
- `-tmp` cambia el directorio, `-tmp_file` define la ruta completa y `-tmp_separator` define el separador de campos.

El archivo tiene una línea por interfaz, con este formato:

```text
timestamp;ifIndex;inOctets;outOctets;width;
```

`width` es `32` o `64`. Las líneas con un ancho ausente o distinto se ignoran, lo que se trata como la ausencia de datos anteriores. Cada ejecución reescribe el archivo solo con las interfaces medidas en esa ejecución.

### OID utilizados

| Objeto | OID | Uso |
| --- | --- | --- |
| `sysObjectID` | `.1.3.6.1.2.1.1.2.0` | Comprobación de conectividad |
| `ifIndex` | `.1.3.6.1.2.1.2.2.1.1` | Lista de interfaces |
| `ifInOctets` | `.1.3.6.1.2.1.2.2.1.10` | Contador de entrada de 32 bits |
| `ifOutOctets` | `.1.3.6.1.2.1.2.2.1.16` | Contador de salida de 32 bits |
| `ifHCInOctets` | `.1.3.6.1.2.1.31.1.1.1.6` | Contador de entrada de 64 bits |
| `ifHCOutOctets` | `.1.3.6.1.2.1.31.1.1.1.10` | Contador de salida de 64 bits |
| `ifHighSpeed` | `.1.3.6.1.2.1.31.1.1.1.15` | Velocidad en Mbit/s |
| `ifSpeed` | `.1.3.6.1.2.1.2.2.1.5` | Velocidad en bit/s |
| `dot3StatsDuplexStatus` | `.1.3.6.1.2.1.10.7.2.1.19` | Modo dúplex (`2` medio, `3` completo) |
