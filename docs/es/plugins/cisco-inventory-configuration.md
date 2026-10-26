# Cisco Inventory configuration

*Última actualización del artículo: 2026-10-26.*

## Qué hace

El addon Cisco Inventory configuration lee la configuración en ejecución de un dispositivo de red Cisco y la almacena en el inventario de Pandora FMS de un agente. Cada ejecución se conecta al dispositivo por SSH, entra en modo privilegiado (enable), desactiva la paginación del terminal, ejecuta `show running-config` y escribe la configuración devuelta en la salida estándar. Pandora FMS almacena ese texto como valor del módulo de inventario que ejecuta el addon.

El addon es un recolector de inventario, no un plugin de monitorización: no crea agentes ni módulos de monitorización. Produce un resultado de texto por ejecución y el módulo de inventario decide qué agente lo recibe. Para un addon que ejecuta un comando arbitrario en lugar del fijo `show running-config`, consulte [Inventory SSH plugin](inventory-ssh.md).

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Pandora FMS NG 784 y posteriores | `Supported` | El Marketplace indica que todas las integraciones son compatibles con Pandora FMS NG 784 y versiones posteriores |
| Un dispositivo Cisco cuya CLI acepte `enable`, `terminal length 0` y `show running-config` | `Required` | Son los comandos que el addon ejecuta en cada pasada |
| Acceso SSH al dispositivo en el puerto SSH predeterminado (`22`) | `Required` | El addon se conecta al servicio SSH sin opción de puerto |
| Un usuario del dispositivo autorizado a entrar en modo privilegiado y ejecutar `show running-config` | `Required` | El addon entra en modo enable antes de leer la configuración |
| Modelos de dispositivo Cisco y versiones de IOS, IOS XE, IOS XR o NX-OS | `Not validated` | No se ha registrado una matriz de modelos ni de firmware |
| Sistema operativo del host que ejecuta el módulo de inventario | `Not validated` | No se ha registrado una matriz de sistemas operativos |

### Requisitos

1. **Conectividad de red** desde el host que ejecuta el módulo de inventario hasta el dispositivo, por SSH en el puerto predeterminado.
2. **Credenciales**: un usuario del dispositivo y su contraseña SSH, además de la contraseña de enable cuando el dispositivo la solicite.
3. **El ejecutable `get-config`** en el host que ejecuta el módulo de inventario, con permiso de ejecución.
4. **Pandora FMS** con un módulo de inventario asignado al agente que almacenará la configuración.

No se instala ningún componente en el dispositivo Cisco.

### Instalar el addon

Descargue el addon desde su entrada del Marketplace, limitada a usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.cisco_inventory_configuration](https://marketplace.pandorafms.com/entries/pandorafms.cisco_inventory_configuration)

Extraiga el paquete y copie el ejecutable `get-config` a una ruta legible y ejecutable por el usuario que ejecuta el módulo de inventario, por ejemplo `/usr/local/bin/get-config`. Mantenga su permiso de ejecución:

```bash
chmod 0755 /usr/local/bin/get-config
```

## Configuración

### Argumentos y orden

Pandora FMS ejecuta el ejecutable con argumentos posicionales. Configure el módulo de inventario para que los valores lleguen en este orden:

| Posición | Argumento | Obligatorio | Descripción |
| --- | --- | --- | --- |
| 1 | `address` | Sí | Dirección IP o nombre de host del dispositivo |
| 2 | `username` | Sí | Usuario del dispositivo |
| 3 | `sshpassword` | Sí | Contraseña SSH de ese usuario |
| 4 | `enablepassword` | Sí | Contraseña de enable; use un valor vacío cuando el dispositivo no la solicite |
| 5 | `sleep` | No | Segundos de espera después de cada comando; valor predeterminado `5` |

Los nombres de los argumentos son los que muestra la ayuda del ejecutable. El módulo de inventario pasa los valores por posición, así que el orden importa más que cualquier etiqueta que muestre la consola. Si el módulo de inventario envía siempre el quinto valor, introduzca un número: un valor vacío se rechaza porque el argumento se interpreta como entero. Omita el argumento por completo para usar el valor predeterminado.

### Modo enable

Cada ejecución envía `enable` y la contraseña de enable antes de leer la configuración. Si el dispositivo no solicita contraseña de enable, pase un valor vacío en la cuarta posición:

```bash
./get-config <TARGET_HOST> <USERNAME> <PASSWORD> ""
```

Si el dispositivo la solicita, indíquela en la misma posición:

```bash
./get-config <TARGET_HOST> <USERNAME> <PASSWORD> "<ENABLE_PASSWORD>"
```

El addon no detecta si el paso de enable tuvo éxito. Una contraseña de enable incorrecta o un usuario sin privilegios no se informa como un fallo de enable: el módulo almacena lo que devuelva el dispositivo, que puede ser un mensaje de error o una configuración incompleta.

### Registrar el módulo de inventario

Cree un módulo de inventario en la consola de Pandora FMS y apúntelo al ejecutable en su host. Añada el módulo al agente que almacenará la configuración e introduzca los cinco valores en el orden anterior. Marque la contraseña SSH y la contraseña de enable como valores ocultos donde la consola ofrezca esa opción. Si la consola ofrece un modo de código en línea, déjelo desactivado: el addon se ejecuta como un ejecutable.

El módulo se ejecuta en el host del agente al que está asignado, por lo que ese host debe alcanzar el dispositivo. El addon no copia nada al dispositivo.

<!-- SCREENSHOT NEEDED: Formulario de registro del módulo de inventario para el addon Cisco Inventory configuration, con la ruta del ejecutable y la opción de código en línea desactivada. -->

<!-- SCREENSHOT NEEDED: Configuración del módulo de inventario en el agente con los cinco campos posicionales (address, username, contraseña SSH, contraseña de enable, sleep) y ambos campos de contraseña enmascarados. -->

### Credenciales y transporte

- La contraseña SSH y la contraseña de enable se pasan como argumentos de línea de comandos. En una ejecución manual aparecen en el historial del intérprete de comandos y en la lista de procesos mientras el addon se ejecuta. En la consola se almacenan en la configuración del módulo de inventario. Restrinja el acceso a la consola y a la configuración del agente.
- La sesión SSH cifra las credenciales en tránsito. El addon acepta cualquier clave de host SSH y no la verifica, por lo que un intermediario en la ruta de red puede suplantar al dispositivo. Ejecute el addon solo desde una red de gestión de confianza o refuerce la identidad del dispositivo en la capa de red.
- La configuración en ejecución se almacena como datos de inventario y puede contener `enable secret`, hashes de contraseñas de usuario, comunidades SNMP, claves criptográficas y otros valores sensibles. Cualquiera que pueda leer el inventario del agente puede leer esos valores. Restrinja el acceso al inventario en consecuencia.

El addon no tiene opción de archivo de credenciales, ni opción de puerto, ni opción de verificación de clave de host.

## Verificación

Ejecute el ejecutable manualmente desde el host que ejecutará el módulo de inventario:

```bash
./get-config <TARGET_HOST> <USERNAME> <PASSWORD> ""
```

Una ejecución correcta termina con estado `0`, escribe la configuración en ejecución en la salida estándar y muestra mensajes de progreso en la salida de error:

```text
Connected. Enabling...
Now dumping running-config...
```

Se elimina la última línea de la respuesta; en una ejecución normal es el indicador del dispositivo. El texto restante es la configuración que almacena el módulo de inventario.

Con el valor predeterminado `sleep` de `5` segundos, el addon espera unos 25 segundos por ejecución antes de terminar: espera una vez tras abrir la shell, una vez después de cada uno de los pasos de enable, contraseña y paginación, y una vez después de `show running-config`. Permita un tiempo de espera del módulo superior a ese valor.

Después, compruebe el inventario del agente. El valor del módulo es el texto de configuración devuelto por el dispositivo.

<!-- SCREENSHOT NEEDED: Vista de inventario del agente con una configuración en ejecución almacenada por el módulo Cisco Inventory configuration, capturada en un dispositivo de laboratorio sin credenciales reales ni datos de cliente. -->

Si la ejecución muestra un error o ninguna configuración, consulte [Operar y resolver problemas](#operar-y-resolver-problemas).

## Entender los resultados

El addon almacena el texto sin procesar de la configuración en ejecución. No analiza la configuración en interfaces, rutas, usuarios u otros objetos, y no crea un módulo por sección: el texto completo es el valor del módulo de inventario.

- El valor de inventario puede ser grande. El addon lee una sola respuesta de hasta aproximadamente 1 MB; una configuración mayor, o un dispositivo que devuelve su salida en varios bloques más lentos, puede quedar truncada.
- El addon elimina siempre la última línea de la respuesta, asumiendo que es el indicador del dispositivo. Cuando la respuesta no termina con un indicador, se pierde la última línea de la configuración.
- El addon no filtra la configuración. Se almacena cada línea que devuelve el dispositivo, salvo la última línea que elimina, incluidas credenciales y claves.
- El addon no valida que el texto sea una configuración. Si el dispositivo devuelve un mensaje de error, el mensaje se almacena como valor del módulo.
- Cada ejecución produce la configuración de ese momento. El addon no compara ejecuciones ni informa de cambios por sí mismo.

## Operar y resolver problemas

### Programación y tiempos

Ejecute el módulo de inventario con el intervalo que necesite. Cada ejecución abre una sesión SSH nueva y la cierra al terminar. El valor `sleep` controla cuánto espera el addon después de cada comando; auméntelo para dispositivos lentos o configuraciones grandes. Los valores más bajos aceleran la ejecución, pero pueden capturar una respuesta incompleta.

### Estado de salida y diagnóstico

| Condición | Estado | Salida |
| --- | --- | --- |
| Captura correcta | `0` | Configuración en la salida estándar; mensajes de progreso en la salida de error |
| Fallo de conexión SSH | `1` | `Connection error: <motivo>` en la salida de error |
| Argumento posicional ausente o no válido | `2` | Resumen de uso en la salida de error |

### Fallos habituales

- **`Connection error: ...`** — el dispositivo no es accesible, el servicio SSH no está en el puerto predeterminado, el usuario o la contraseña son incorrectos, o el dispositivo rechaza la conexión. Compruebe la dirección, el servicio SSH y las credenciales desde el mismo host.
- **La salida es un error del dispositivo o una configuración incompleta** — el paso de enable falló, el usuario no tiene privilegios o el dispositivo no acepta `terminal length 0`. Compruebe la contraseña de enable, los privilegios del usuario y la CLI del dispositivo.
- **La salida está vacía** — `show running-config` no devolvió nada, la sesión no llegó al modo privilegiado o la espera fue demasiado corta. Aumente `sleep` y ejecute el comando manualmente en el dispositivo.
- **La salida está truncada** — la configuración superó la lectura única de aproximadamente 1 MB o el dispositivo necesitó más tiempo. Esta versión no tiene opción para leer más; obtenga la configuración con un comando más acotado fuera del addon si necesita el texto completo.
- **La ejecución no termina** — el addon no tiene un tiempo de espera configurable de conexión ni de lectura. Un dispositivo que deja de responder puede dejar la ejecución esperando. Use el tiempo de espera del módulo de inventario donde la consola lo ofrezca y compruebe el dispositivo.

### Limitaciones

- Sin opción de puerto SSH: el addon usa el puerto SSH predeterminado.
- Sin opción de tiempo de espera de conexión o de lectura.
- Una lectura de respuesta de hasta aproximadamente 1 MB por ejecución.
- Sin archivo de credenciales: las credenciales son argumentos posicionales.
- Sin verificación de clave de host: se acepta cualquier clave de host SSH.
- Sin filtrado ni ocultación de la salida: se almacena la configuración completa.

## Referencia

### Argumentos de línea de comandos

| Argumento | Posición | Obligatorio | Valor predeterminado | Descripción |
| --- | --- | --- | --- | --- |
| `address` | 1 | Sí | — | Dirección IP o nombre de host del dispositivo Cisco |
| `username` | 2 | Sí | — | Usuario del dispositivo |
| `sshpassword` | 3 | Sí | — | Contraseña SSH |
| `enablepassword` | 4 | Sí | — | Contraseña de enable; pase `""` cuando el dispositivo no la solicite |
| `sleep` | 5 | No | `5` | Segundos de espera después de cada comando |

`-h` o `--help` muestra el resumen de uso y termina.

### Ejecución y salida

```bash
./get-config <TARGET_HOST> <USERNAME> <PASSWORD> <ENABLE_PASSWORD> [SLEEP]
```

| Flujo | Contenido |
| --- | --- |
| Salida estándar | Configuración en ejecución, con CRLF normalizado a LF y la última línea eliminada |
| Salida de error | `Connected. Enabling...`, `Now dumping running-config...` o un error de conexión |
| Estado de salida | `0` si tiene éxito, `1` ante un error de conexión, `2` ante un error de argumentos |

El addon usa el puerto SSH predeterminado y no tiene opción para cambiarlo. Lee una sola respuesta de hasta 999999 bytes; no itera para recopilar más.

### Identidad del addon

| Propiedad | Valor |
| --- | --- |
| Identificador del Marketplace | `pandorafms.cisco_inventory_configuration` |
| Nombre | Cisco Inventory configuration |
| Versión | `1.0` |
| Última actualización en el Marketplace | 2025-06-25 |
| Paquete | `pandorafms.cisco_inventory_configuration.1.0.zip` |
| Ejecutable | `get-config` |
| Disponibilidad | Descarga limitada a usuarios con licencia (licencia One) |
