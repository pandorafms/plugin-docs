# Inventory SSH plugin

*Última actualización del artículo: 2026-10-26.*

## Qué hace

El plugin Inventory SSH ejecuta un comando en un dispositivo de red por SSH y almacena la salida del comando en el inventario de Pandora FMS de un agente. El comando lo elige el operador, por lo que el mismo addon puede recoger una configuración en ejecución, una versión de firmware o cualquier otra salida de la CLI. Cada ejecución se conecta al dispositivo, entra opcionalmente en modo enable, envía opcionalmente un comando de paginación, ejecuta el comando configurado, filtra la respuesta y escribe el resultado en la salida estándar. Pandora FMS almacena ese texto como valor del módulo de inventario que ejecuta el addon.

El addon es un recolector de inventario, no un plugin de monitorización: no crea agentes ni módulos de monitorización. Produce un resultado de texto por ejecución y el módulo de inventario decide qué agente lo recibe. Para el addon que recoge siempre `show running-config`, consulte [Cisco Inventory configuration](cisco-inventory-configuration.md).

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Pandora FMS NG 784 y posteriores | `Soportado` | El Marketplace indica que todas las integraciones son compatibles con Pandora FMS NG 784 y versiones posteriores |
| Un servicio SSH en el dispositivo que proporcione una shell interactiva | `Requerido` | El addon abre una shell SSH interactiva para ejecutar el comando |
| Acceso SSH al dispositivo en el puerto SSH predeterminado (`22`) | `Requerido` | El addon se conecta al servicio SSH sin opción de puerto |
| Un usuario del dispositivo autorizado a ejecutar el comando configurado | `Requerido` | El addon envía el comando con el usuario configurado |
| Fabricantes, modelos y versiones de firmware de dispositivos de red | `Sin validar` | No se ha registrado una matriz de dispositivos ni de firmware |
| Sistema operativo del host que ejecuta el módulo de inventario | `Sin validar` | No se ha registrado una matriz de sistemas operativos |

### Requisitos

1. **Conectividad de red** desde el host que ejecuta el módulo de inventario hasta el dispositivo, por SSH en el puerto predeterminado.
2. **Credenciales**: un usuario del dispositivo y su contraseña SSH, además de la contraseña de enable cuando el dispositivo requiera el modo enable.
3. **El ejecutable `ssh_inventory`** en el host que ejecuta el módulo de inventario, con permiso de ejecución.
4. **Pandora FMS** con un módulo de inventario asignado al agente que almacenará la salida del comando.

No se instala ningún componente en el dispositivo de red.

### Instalar el addon

Descargue el addon desde su entrada del Marketplace, limitada a usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.inventoryssh](https://marketplace.pandorafms.com/entries/pandorafms.inventoryssh)

Extraiga el paquete y copie el ejecutable `ssh_inventory` a una ruta legible y ejecutable por el usuario que ejecuta el módulo de inventario, por ejemplo `/usr/local/bin/ssh_inventory`. Mantenga su permiso de ejecución:

```bash
chmod 0755 /usr/local/bin/ssh_inventory
```

## Configuración

### Argumentos y orden

Pandora FMS ejecuta el ejecutable con argumentos posicionales. Configure el módulo de inventario para que los valores lleguen en este orden:

| Posición | Argumento | Obligatorio | Descripción |
| --- | --- | --- | --- |
| 1 | `address` | Sí | Dirección IP o nombre de host del dispositivo |
| 2 | `username` | Sí | Usuario del dispositivo |
| 3 | `password` | Sí | Contraseña SSH, o `<PASSWORD>/<ENABLE_PASSWORD>` cuando el dispositivo requiera el modo enable |
| 4 | `command` | Sí | Comando que se ejecutará, incluido su terminador de línea como secuencia de escape |
| 5 | `extra_command` | Sí | Comando que se envía antes del comando principal, normalmente para desactivar la paginación; use `""` si no se necesita |
| — | `--debug` | No | Requiere un valor; al indicar la opción se activan los mensajes de progreso |

`extra_command` es posicional y, por tanto, obligatorio: pase una cadena vacía cuando no lo necesite. `--debug` es una opción y puede aparecer antes o después de los valores posicionales.

Los nombres de los argumentos son los que muestra la ayuda del ejecutable. El módulo de inventario pasa los valores por posición, así que el orden importa más que cualquier etiqueta que muestre la consola.

### Comando y paginación

El comando se envía al dispositivo tal como se configura, después de que el addon interprete las secuencias de escape. Debe contener el terminador de línea: use `\n` y añada `\r` cuando el dispositivo lo requiera. El addon no añade un salto de línea al comando, por lo que un comando sin `\n` se escribe en el dispositivo pero no se ejecuta.

```bash
./ssh_inventory <TARGET_HOST> <USERNAME> '<PASSWORD>' 'show running-config\n' 'terminal length 0'
```

El mismo addon en un dispositivo con otra CLI, por ejemplo un dispositivo MikroTik:

```bash
./ssh_inventory <TARGET_HOST> <USERNAME> '<PASSWORD>' 'system resource print\n\r' ''
```

Use comillas simples alrededor del comando para que el intérprete de comandos conserve las barras invertidas y el addon pueda interpretarlas.

Si el comando contiene dos puntos (`:`), el addon descarta el texto anterior a los primeros dos puntos y envía el resto. Evite los dos puntos en el comando o tenga en cuenta ese recorte.

`extra_command` se envía como texto plano seguido de un salto de línea; sus secuencias de escape no se interpretan. Se ejecuta después del paso opcional de enable y antes del comando principal. Úselo para el comando del fabricante que desactiva la paginación, como `terminal length 0` o `no page`. Pase una cadena vacía cuando no necesite ningún comando adicional.

### Contraseña y modo enable

El argumento `password` acepta un valor o dos valores separados por `/`:

| Forma | Contraseña SSH | Contraseña de enable |
| --- | --- | --- |
| `<PASSWORD>` | `<PASSWORD>` | ninguna |
| `<PASSWORD>/<ENABLE_PASSWORD>` | `<PASSWORD>` | `<ENABLE_PASSWORD>` |

El addon divide el valor por `/` y usa el primer segmento como contraseña SSH y el segundo como contraseña de enable. Una contraseña que contenga `/` no se puede representar; los segmentos posteriores al segundo se ignoran. El addon envía `enable` y la contraseña de enable solo cuando hay una contraseña de enable, por lo que un dispositivo que requiera modo enable sin el segundo valor puede devolver un error de privilegios o un resultado vacío.

### Salida de depuración

`--debug <valor>` requiere un valor. Al indicar la opción se activan dos mensajes de progreso en la salida de error independientemente del valor, incluido `--debug 0`; omita la opción para mantenerlos desactivados. El primer mensaje es `Connected. Enabling...` y el segundo es siempre `Now dumping running-config...`, sea cual sea el comando configurado.

El addon no tiene ninguna otra opción de verbosidad.

### Registrar el módulo de inventario

Cree un módulo de inventario en la consola de Pandora FMS y apúntelo al ejecutable en su host. Añada el módulo al agente que almacenará la salida e introduzca los cinco valores en el orden anterior. Marque el campo de contraseña como valor oculto donde la consola ofrezca esa opción. Si la consola ofrece un modo de código en línea, déjelo desactivado: el addon se ejecuta como un ejecutable.

El módulo se ejecuta en el host del agente al que está asignado, por lo que ese host debe alcanzar el dispositivo. El addon no copia nada al dispositivo.

<!-- SCREENSHOT NEEDED: Formulario de registro del módulo de inventario para el plugin Inventory SSH, con la ruta del ejecutable y la opción de código en línea desactivada. -->

<!-- SCREENSHOT NEEDED: Configuración del módulo de inventario en el agente con los cinco campos posicionales (address, username, contraseña, comando, comando adicional) y el campo de contraseña enmascarado. -->

### Credenciales y transporte

- La contraseña SSH y la contraseña de enable se pasan como argumentos de línea de comandos. En una ejecución manual aparecen en el historial del intérprete de comandos y en la lista de procesos mientras el addon se ejecuta. En la consola se almacenan en la configuración del módulo de inventario. Restrinja el acceso a la consola y a la configuración del agente.
- La sesión SSH cifra las credenciales en tránsito. El addon acepta cualquier clave de host SSH y no la verifica, por lo que un intermediario en la ruta de red puede suplantar al dispositivo. Ejecute el addon solo desde una red de gestión de confianza o refuerce la identidad del dispositivo en la capa de red.
- La salida del comando se almacena como datos de inventario. Puede contener credenciales, claves, comunidades SNMP y otros valores sensibles. Cualquiera que pueda leer el inventario del agente puede leerlos. Restrinja el acceso al inventario en consecuencia.
- El filtro de líneas descrito en [Entender los resultados](#entender-los-resultados) no es un control de ocultación. Use un usuario del dispositivo con privilegios de solo lectura y elija comandos cuya salida esté dispuesto a almacenar.

El addon no tiene opción de archivo de credenciales, ni opción de puerto, ni opción de verificación de clave de host.

## Verificación

Ejecute el ejecutable manualmente desde el host que ejecutará el módulo de inventario:

```bash
./ssh_inventory <TARGET_HOST> <USERNAME> '<PASSWORD>' 'show version\n' 'terminal length 0' --debug 1
```

Una ejecución correcta termina con estado `0` y escribe la salida filtrada del comando en la salida estándar. Con `--debug 1`, también muestra los dos mensajes de progreso en la salida de error:

```text
Connected. Enabling...
Now dumping running-config...
```

El segundo mensaje es texto fijo y nombra `running-config` aunque el comando sea `show version`. Es un mensaje de progreso, no una afirmación sobre el comando ejecutado.

Después, compruebe el inventario del agente. El valor del módulo es el texto filtrado que devolvió el dispositivo para el comando configurado.

<!-- SCREENSHOT NEEDED: Vista de inventario del agente con la salida de un comando almacenada por el módulo del plugin Inventory SSH, capturada en un dispositivo de laboratorio sin credenciales reales ni datos de cliente. -->

Si la ejecución muestra un error o ninguna salida, consulte [Operar y resolver problemas](#operar-y-resolver-problemas).

## Entender los resultados

### Qué almacena el módulo

El addon almacena la salida del comando como texto plano. No analiza la salida en interfaces, rutas, campos de firmware u otros objetos, y no crea un módulo por línea: el texto filtrado es el valor del módulo de inventario.

Antes de imprimir, el addon elimina el texto del comando enviado, el texto capturado antes del comando (normalmente el indicador del dispositivo), la última línea de la respuesta, los espacios en blanco al principio y al final, y las líneas vacías. Si el comando no produce salida, el valor del módulo está vacío.

### Filtrado

El filtro se aplica siempre; esta versión no tiene opción para desactivarlo. Elimina cualquier línea que contenga uno de estos valores:

- `enable`
- `Password:`
- el texto del comando

La coincidencia distingue mayúsculas y minúsculas y se aplica en cualquier parte de la línea. Después se eliminan las líneas vacías. El valor de `extra_command` no se añade a la lista del filtro.

Como `enable` coincide en cualquier posición, se eliminan líneas como `enable secret ...` y también líneas legítimas de configuración que contengan esa palabra. Como se busca el texto del comando, se elimina cualquier línea de salida que repita el comando. El filtro puede eliminar líneas útiles y no garantiza que se eliminen todos los secretos; trátelo como una limpieza de salida, no como una ocultación.

### Contenido sensible

Una configuración en ejecución, un inventario de firmware o un comando de diagnóstico pueden exponer credenciales, claves y direcciones internas. El filtro elimina algunas líneas, pero no todos los valores sensibles. Restrinja el acceso al inventario del agente y elija el comando con el mismo cuidado que las credenciales.

## Operar y resolver problemas

### Programación y tiempos

Ejecute el módulo de inventario con el intervalo que necesite. Cada ejecución abre una sesión SSH nueva y la cierra al terminar. Después de enviar el comando, el addon deja de esperar cuando detecta el indicador o cuando el dispositivo no produce salida durante 5 segundos. No hay un tiempo de espera configurable de conexión ni de indicador inicial; un dispositivo que deja de responder puede dejar la ejecución esperando.

### Estado de salida y diagnóstico

| Condición | Estado | Salida |
| --- | --- | --- |
| Comando correcto | `0` | Salida filtrada del comando en la salida estándar |
| Fallo de conexión SSH | Distinto de cero | El error SSH en la salida de error |
| Argumento ausente o no válido | `2` | Resumen de uso en la salida de error |

### Fallos habituales

- **La conexión falla con un estado distinto de cero** — el dispositivo no es accesible, el servicio SSH no está en el puerto predeterminado, el usuario o la contraseña son incorrectos, o el dispositivo rechaza la conexión. Compruebe la dirección, el servicio SSH y las credenciales desde el mismo host.
- **La salida está vacía** — el comando no tiene `\n` y no se ejecutó, el comando no es válido para el dispositivo, el usuario no tiene el privilegio necesario, se necesitaba el modo enable y no se aportó, o `extra_command` falló. Ejecute el mismo comando manualmente en el dispositivo.
- **Faltan líneas esperadas** — el filtro las eliminó porque contienen `enable`, `Password:` o el texto del comando. Compruebe la respuesta completa en el dispositivo y ajuste el comando. No hay opción para desactivar el filtro.
- **La salida está truncada** — el dispositivo no produjo datos durante 5 segundos antes de devolver el indicador, o el comando tarda más que la espera fija. No hay un tiempo de espera configurable; use un comando que devuelva la salida de forma continua o más rápida.
- **El comando se trunca en dos puntos** — el addon envía solo el texto posterior a los primeros dos puntos. Elimine los dos puntos del comando o use otro comando.
- **La contraseña se divide de forma inesperada** — el addon divide el valor de `password` por `/`. Una contraseña que contenga `/` no se puede pasar correctamente.
- **`--debug` falla con un error de uso** — la opción requiere un valor; use `--debug 1`.

### Limitaciones

- Sin opción de puerto SSH: el addon usa el puerto SSH predeterminado.
- Sin tiempo de espera configurable de conexión, de indicador inicial o de lectura.
- El comando debe incluir su propio terminador de línea como secuencia de escape.
- El texto anterior a los primeros dos puntos del comando se descarta.
- Una contraseña que contenga `/` no se puede representar.
- El filtro está siempre activo, distingue mayúsculas y minúsculas y no se puede desactivar.
- Sin archivo de credenciales: las credenciales son argumentos posicionales.
- Sin verificación de clave de host: se acepta cualquier clave de host SSH.

## Referencia

### Argumentos de línea de comandos

| Argumento | Posición | Obligatorio | Valor predeterminado | Descripción |
| --- | --- | --- | --- | --- |
| `address` | 1 | Sí | — | Dirección IP o nombre de host del dispositivo |
| `username` | 2 | Sí | — | Usuario del dispositivo |
| `password` | 3 | Sí | — | Contraseña SSH, o `<PASSWORD>/<ENABLE_PASSWORD>` |
| `command` | 4 | Sí | — | Comando que se ejecutará, con su terminador de línea como secuencia de escape |
| `extra_command` | 5 | Sí | — | Comando que se envía antes del comando principal; use `""` si no se necesita |
| `--debug` | opción | No | `0` | Requiere un valor; al indicar la opción se activan los mensajes de progreso independientemente del valor |

`-h` o `--help` muestra el resumen de uso y termina.

### Preprocesamiento del comando

| Paso | Comportamiento |
| --- | --- |
| División por dos puntos | Se descarta el texto anterior a los primeros dos puntos; se envía el resto, incluidos los dos puntos posteriores |
| Interpretación de escapes | Se interpretan secuencias de escape como `\n`, `\r` y `\t` en `command` |
| Terminador de línea | No se añade un salto de línea a `command`; incluya `\n` (y `\r` cuando sea necesario) |
| Comando adicional | `extra_command` se envía como texto plano más un salto de línea; sus secuencias de escape no se interpretan |

### Procesamiento de la salida

| Paso | Comportamiento |
| --- | --- |
| Eliminación del comando | Se elimina de la respuesta el texto del comando enviado |
| Eliminación del indicador | Se elimina el texto capturado antes del comando, normalmente el indicador |
| Última línea | La última línea de la respuesta se elimina siempre |
| Espacios en blanco | Se eliminan los espacios en blanco al principio y al final |
| Filtro de líneas | Se eliminan las líneas que contienen `enable`, `Password:` o el texto del comando, distinguiendo mayúsculas y minúsculas |
| Líneas vacías | Se eliminan las líneas vacías |

### Ejecución y salida

```bash
./ssh_inventory <TARGET_HOST> <USERNAME> <PASSWORD> <COMMAND> <EXTRA_COMMAND> [--debug <VALUE>]
```

| Flujo | Contenido |
| --- | --- |
| Salida estándar | Salida filtrada del comando |
| Salida de error | Mensajes de progreso con `--debug`; errores SSH |
| Estado de salida | `0` si tiene éxito, distinto de cero ante un fallo SSH, `2` ante un error de argumentos |

El addon usa el puerto SSH predeterminado y no tiene opción para cambiarlo.

### Identidad del addon

| Propiedad | Valor |
| --- | --- |
| Identificador del Marketplace | `pandorafms.inventoryssh` |
| Nombre | Inventory SSH plugin |
| Versión | `1.0` |
| Última actualización en el Marketplace | 2025-06-25 |
| Paquete | `pandorafms.inventoryssh.1.0.zip` |
| Ejecutable | `ssh_inventory` |
| Disponibilidad | Descarga limitada a usuarios con licencia (licencia One) |
