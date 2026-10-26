# Plugin de monitorización Citrix NetScaler

*Última actualización del artículo: 2026-10-26.*

## Qué hace

El plugin monitoriza un dispositivo Citrix NetScaler (ADC) desde Pandora FMS a
través de la API REST de estadísticas NITRO. En cada ejecución pregunta al
dispositivo qué objetos estadísticos expone, lee los que se indican en el archivo
de configuración y crea agentes de Pandora FMS a partir del resultado: un agente
por cada objeto devuelto para cada servicio configurado, más un módulo de estado
en el agente principal.

El plugin es un ejecutable autónomo que se lanza una vez por invocación y
termina. Recibe un único archivo de configuración, no conserva estado entre
ejecuciones y no arranca ningún servicio. No es un plugin de Discovery: Pandora
FMS no lo ejecuta desde una tarea.

Los agentes nunca se imprimen para que los recoja un agente local. Cada ejecución
construye documentos XML de agente de Pandora FMS y los entrega, ya sea mediante
Tentacle o copiándolos en una carpeta de datos local. Los únicos módulos de
Pandora FMS que el plugin escribe en la salida estándar son los de una ejecución
fallida (consulte [Verificación](#verificacion)).

No se instala nada en el dispositivo. El plugin lee estadísticas con peticiones
HTTP GET autenticadas mediante cabeceras NITRO, de modo que la cuenta solo
necesita permiso de lectura.

El catálogo de módulos no es fijo. Los módulos de un objeto son los campos
estadísticos que el dispositivo devuelve para él, filtrados por la lista del
archivo de configuración, de forma que el mismo plugin se adapta a los campos que
expone cada dispositivo o firmware.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Pandora FMS NG 784 y posteriores | `Supported` | El Marketplace indica que todas sus entradas son compatibles con Pandora FMS NG 784 y versiones posteriores; es una declaración de todo el catálogo que cubre este addon, no un registro de prueba |
| Un dispositivo Citrix NetScaler que exponga la API de estadísticas NITRO en `ns_url` | `Required` | La petición del catálogo se dirige a `<ns_url>` y cada lectura de servicio añade `/<servicio>` |
| Una cuenta de NetScaler autorizada a leer la API de estadísticas | `Required` | Las credenciales viajan en las cabeceras `X-NITRO-USER` y `X-NITRO-PASS` de cada petición |
| Un entorno de ejecución de Perl con `LWP::UserAgent` y `JSON` | `Required` | El plugin no arranca sin ellos |
| Acceso de red desde el host del plugin al dispositivo | `Required` | Las estadísticas se leen por HTTP o HTTPS desde ese host |
| Una carpeta temporal con permiso de escritura | `Required` | Cada documento de agente se escribe en `temp` antes de entregarse |
| Un destino de entrega: el servicio Tentacle de Pandora FMS o una carpeta de datos local con permiso de escritura | `Required` | `mode` selecciona uno de los dos |
| Modelos y versiones de firmware de NetScaler | `Not validated` | No se ha registrado una matriz de modelos ni de firmware para este addon. La guía heredada indica `NSMPX-10500` como plataforma probada; ningún registro actual lo confirma |
| Sistema operativo del host que ejecuta el plugin | `Not validated` | No se ha registrado un sistema operativo para esta versión |

### Requisitos

1. **Un dispositivo Citrix NetScaler** cuya API de estadísticas NITRO responda en
   la URL configurada y sea accesible desde el host que ejecuta el plugin.
2. **Una cuenta en el dispositivo** autorizada a leer las estadísticas de los
   servicios que se quieren monitorizar. Utilice una cuenta dedicada de solo
   lectura.
3. **Un host para ejecutar el plugin** con el entorno de ejecución de Perl y los
   dos módulos indicados en [Compatibilidad](#compatibilidad).
4. **Un destino para los agentes generados**: el servicio Tentacle de Pandora FMS,
   con el cliente Tentacle disponible, o una carpeta de datos local que lea el
   servidor de Pandora FMS.
5. **Permiso de escritura** en la carpeta `temp` y, en modo local, en
   `local_folder`.

### Instalación del plugin

Descargue el addon desde la entrada del Marketplace de Pandora FMS, limitada a
usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.citrix_netscaler](https://marketplace.pandorafms.com/entries/pandorafms.citrix_netscaler)

El addon consta del ejecutable `citrix_netscaler.pl` y de su archivo de
configuración `citrix_netscaler.conf`. Copie ambos al host que ejecutará el plugin
y conceda permiso de ejecución al ejecutable. El archivo de configuración puede
residir en cualquier ruta, porque cada ejecución recibe su ruta como único
argumento.

El archivo de ejemplo incluye hosts, una cuenta y direcciones de Tentacle y de la
API de ejemplo. Sustitúyalos antes de ejecutar el plugin (consulte
[Configuración](#configuracion)) y restrinja los permisos del archivo: contiene la
contraseña del dispositivo en texto plano.

## Configuración

El plugin recibe un argumento, la ruta de su archivo de configuración, y ninguna
opción de línea de comandos:

```bash
./citrix_netscaler.pl <PATH_TO_CONFIG>
```

La forma explícita equivalente, útil cuando no está establecido el permiso de
ejecución o hay que seleccionar el intérprete a mano:

```bash
perl citrix_netscaler.pl <PATH_TO_CONFIG>
```

No existe la opción `-h` ni `--help`: una ejecución sin ningún argumento imprime
el resumen de uso y termina con estado `1`.

### Formato del archivo de configuración

El archivo es texto plano con una línea `clave = valor` por cada ajuste:

- Una línea en blanco se ignora.
- Una línea cuyo primer carácter es `#` es un comentario. Un `#` en cualquier otra
  posición forma parte del valor, por lo que no se admiten comentarios al final de
  la línea.
- La clave y el valor se recortan de espacios iniciales y finales.
- Una clave repetida con valor escalar conserva la última aparición.
- `ns_services` es la excepción: cada aparición añade un servicio.
- El analizador acepta cualquier clave. Una clave que el plugin no lee no tiene
  efecto (consulte [Aceptadas pero no aplicadas](#aceptadas-pero-no-aplicadas)).
- Una línea sin `=` se guarda con valor vacío en lugar de notificarse.

Esta es una configuración completa para una primera ejecución que entrega con
Tentacle:

```ini
ns_url = https://<NETSCALER_HOST>/nitro/v1/stat/
ns_user = <USERNAME>
ns_pass = <PASSWORD>

ns_services = system;0
ns_services = lbvserver;1

modules_list = state,status,cpuusage,memusagepcnt

agent_name = netscaler-main
agent_interval = 300

mode = tentacle
tentacle_ip = <PANDORA_FMS_URL>
tentacle_port = 41121
```

La misma recopilación copiada en una carpeta de datos local:

```ini
ns_url = https://<NETSCALER_HOST>/nitro/v1/stat/
ns_user = <USERNAME>
ns_pass = <PASSWORD>

ns_services = system;0
ns_services = lbvserver;1

agent_name = netscaler-main

mode = local
local_folder = /var/spool/pandora/data_in
```

### Conexión y credenciales

- `ns_url` es la URL base de la API de estadísticas, por ejemplo
  `https://<NETSCALER_HOST>/nitro/v1/stat/`. El plugin solicita esa URL una vez
  para obtener el catálogo de objetos estadísticos y después le añade `/` y el
  nombre del servicio en cada lectura, por lo que el valor debe incluir la ruta de
  la API y no solo el host.
- Se admiten URL `http://` y `https://`. Utilice HTTPS: por HTTP simple, las
  cabeceras que transportan las credenciales y las estadísticas recopiladas viajan
  sin cifrar.
- Las credenciales se envían en las cabeceras `X-NITRO-USER` y `X-NITRO-PASS` en
  cada petición.
- El plugin no ofrece ninguna opción de certificado. El certificado del
  dispositivo debe ser de confianza para el host que ejecuta el plugin, incluida
  cualquier autoridad de certificación privada de su almacén de confianza.
- `lwp_timeout` establece el tiempo máximo de espera de cada petición HTTP, en
  segundos. No aparece en el archivo de ejemplo y, sin valor, el plugin no aplica
  un tiempo máximo explícito, de modo que un dispositivo que no responde puede
  retener la ejecución tanto como espere el cliente HTTP.
- El cliente HTTP respeta las variables de entorno `http_proxy`, `https_proxy` y
  `no_proxy`.
- `ns_pass` se guarda en texto plano. Restrinja el archivo al usuario que ejecuta
  el plugin, por ejemplo con `chmod 600`, y no lo mantenga en una carpeta
  compartida.

### Servicios y módulos que se recopilan

`ns_services` selecciona qué se lee. Cada línea tiene la forma
`ns_services=<servicio>;<valor>`:

- `<servicio>` es el nombre de un objeto estadístico NITRO, como `system` o
  `lbvserver`. Se compara con el catálogo que devuelve el dispositivo, y un
  servicio que el dispositivo no enumera se omite sin error.
- `<valor>` es `1` o `0` y solo controla el padre de los agentes generados: con
  `1` declaran como padre el `agent_name` configurado; con `0` (o sin valor) se
  generan sin padre.

No hay ningún servicio por defecto. Un archivo de configuración sin ninguna línea
`ns_services` lee el catálogo y nada más, de modo que la ejecución solo informa
del módulo de estado en el agente principal.

`modules_list` filtra los campos estadísticos de cada objeto. Es una lista de
nombres de campo exactos y sensibles a mayúsculas, separados por comas y sin
espacios:

```ini
modules_list = state,status,cpuusage,memusagepcnt
```

Cada nombre de la lista se convierte en un módulo solo cuando el objeto devuelve
ese campo. El archivo de ejemplo propone
`state,status,vbshealth,primaryaddress,cpuusage,disk1avail,memusagepcnt,powersupply2status`;
ajuste la lista a los campos que su dispositivo y firmware devuelven realmente.
Cuando `modules_list` no existe o está vacío, el filtro se desactiva y todos los
campos del objeto se convierten en módulos, incluido su campo de nombre.

El filtro se aplica a los campos estadísticos del propio objeto. Los módulos de
vinculaciones estadísticas descritos en
[Entender los resultados](#entender-los-resultados) no se filtran: se generan
para cada servicio que el dispositivo responde con una lista de objetos,
cualquiera que sea su valor.

`ns_service_prefix` antepone un texto fijo al nombre de los agentes generados para
los objetos de un servicio multiinstancia, lo que ayuda cuando varios dispositivos
entregan a la misma instalación de Pandora FMS. Un servicio de instancia única se
nombra con el valor que devuelve el dispositivo.

### Agentes y entrega

`agent_name` da nombre al agente principal y es también el padre que declaran los
agentes de objeto de un servicio configurado con valor `1`. Su valor por defecto
es `NetScaler`, así que establézcalo explícitamente para cada dispositivo
monitorizado.

`mode` selecciona cómo salen los documentos del host:

- `mode = tentacle` (el valor por defecto) escribe el documento en `temp` y lo
  envía con el cliente Tentacle:
  `tentacle_client -v -a tentacle_ip -p tentacle_port tentacle_opts <archivo>`.
  El documento se elimina tras una transferencia correcta. `tentacle_client`
  vale `tentacle_client` por defecto y se resuelve mediante `PATH`; indique una
  ruta completa cuando el cliente no esté en la ruta de búsqueda. `tentacle_opts`
  se inserta tal cual en esa línea de comandos, así que trate su valor como
  entrada de confianza del operador. `tentacle_ip` recibe la dirección del
  servidor de Pandora FMS, sin esquema ni ruta.
- Cualquier otro valor de `mode`, incluido `local`, copia el documento en
  `local_folder` y elimina la copia temporal si la copia tiene éxito.
  `local_folder` no tiene valor por defecto; sin él la copia falla y el plugin
  informa del error en la salida de error estándar.

`temp` es la carpeta donde se escribe el documento antes de entregarlo. Vale
`/tmp` por defecto y debe existir y tener permiso de escritura para el usuario que
ejecuta el plugin.

Una transferencia Tentacle fallida se reintenta una vez, tras un segundo. Si el
segundo intento también falla, el documento se descarta y el plugin escribe
`[<archivo>] discarted` en la salida de error estándar; el estado de salida de la
ejecución no cambia.

### Programación de la ejecución

El plugin no se programa solo. Ejecútelo desde `cron` con el periodo con el que
quiera monitorizar, por ejemplo cada cinco minutos. Esta entrada supone que el
ejecutable está instalado en la carpeta de plugins de servidor de Pandora FMS:

```cron
*/5 * * * * root /usr/share/pandora_server/util/plugin/citrix_netscaler.pl <PATH_TO_CONFIG>
```

`agent_interval` solo declara el intervalo del agente a Pandora FMS; no cambia
cuándo se ejecuta el plugin. Mantenga alineados el periodo de `cron` y
`agent_interval` para que el intervalo declarado coincida con la frecuencia real
de los datos.

## Verificación

Ejecute el plugin una vez desde una terminal:

```bash
cd /usr/share/pandora_server/util/plugin
./citrix_netscaler.pl <PATH_TO_CONFIG>
echo $?
```

Una ejecución correcta es silenciosa: el plugin no imprime nada en la salida
estándar y termina con estado `0`. Si tiene éxito:

- Con `mode = tentacle`, el documento se escribe en `temp`, se transfiere y se
  elimina. No queda nada en `temp` para el agente terminado.
- Con `mode = local`, aparece un archivo llamado `<agente>_<epoch>.data` en
  `local_folder`, y la copia de `temp` se elimina.
- En Pandora FMS aparece el agente principal configurado con el módulo
  `Plugin message`, seguido de los agentes de objeto de los servicios
  configurados.

Cuando falla la primera petición a `ns_url`, la ejecución toma el camino
contrario: imprime el documento de agente en la salida estándar, lo entrega igual
y termina con estado `1`. Ese documento contiene un único módulo:

```xml
<?xml version='1.0' encoding='UTF-8'?>
<agent_data description='' version='' os_version='NetScaler Plugin' os_name='NetScaler Plugin' timestamp='2026/10/26 09:00:00' interval='300' parent_agent_name='' agent_name='netscaler-main'>
<module>
	<name><![CDATA[Plugin message]]></name>
	<type>generic_proc</type>
	<data><![CDATA[0]]></data>
	<description><![CDATA[No response from https://netscaler.example.com/nitro/v1/stat/]]></description>
	<module_interval><![CDATA[1]]></module_interval>
</module>
</agent_data>
```

El mismo formato de documento se entrega con `Plugin message` a `1` y la
descripción `Execution OK` en una ejecución correcta, sin imprimirse. El orden de
los atributos de `<agent_data>` no es significativo y puede cambiar entre
ejecuciones.

## Entender los resultados

### Agentes generados

Todos los agentes generados declaran `NetScaler Plugin` como sistema operativo y
como versión del sistema operativo, una versión vacía, la marca de tiempo de la
ejecución, el `agent_interval` configurado y el `agent_desc` configurado como
descripción.

| Agente | Nombre | Padre |
| --- | --- | --- |
| Agente principal | `agent_name`, `NetScaler` cuando está vacío | Ninguno |
| Objeto de un servicio multiinstancia, valor `1` | `ns_service_prefix` + el campo `name` del objeto | El agente principal |
| Objeto de un servicio multiinstancia, valor `0` | `ns_service_prefix` + el campo `name` del objeto | Ninguno |
| Servicio de instancia única, como `system` | El campo `name` devuelto para el servicio; `ns_service_prefix` + `agent_name` cuando está vacío | Según el valor del servicio |

Como un servicio de instancia única nombra su agente con el nombre del
dispositivo, el agente llamado `agent_name` suele contener solo el módulo
`Plugin message`, y las estadísticas del dispositivo quedan en el agente nombrado
con el nombre del dispositivo. Ese es el comportamiento documentado, no un módulo
que falte: el módulo de estado se entrega siempre en el agente principal
configurado.

### Módulos generados

| Módulo | Tipo | Condición | Significado |
| --- | --- | --- | --- |
| `Plugin message` | `generic_proc` | Siempre, en el agente principal | `1` cuando la ejecución terminó y se leyó el catálogo; `0` cuando falló la petición a `ns_url`, con la URL fallida en la descripción |
| `<campo>` | `generic_data` si el valor es numérico, `generic_data_string` en caso contrario | El objeto devuelve el campo y `modules_list` lo permite, o el filtro está desactivado | El valor de la estadística tal como lo devuelve el dispositivo |
| `<objeto> statbindings` | `generic_data_string` | Servicio multiinstancia | `OK` cuando la petición de vinculaciones devolvió JSON válido, `UNREACHABLE` cuando no, con la causa en la descripción |
| `<objeto> <vinculación>` | `generic_data` si el estado es numérico, `generic_data_string` en caso contrario | Servicio multiinstancia y respuesta de vinculaciones válida | El estado de cada servidor vinculado al objeto; la descripción incluye su `Primary IP Address` |

Los nombres de los campos estadísticos son los identificadores que devuelve el
dispositivo, así que los nombres de módulo dependen del dispositivo y del
firmware. El nombre del módulo no lleva el nombre del servicio como prefijo: es el
nombre del campo a secas.

Todos los módulos llevan `<module_interval>` con `module_interval` (`1` en el
archivo de ejemplo) y `<module_group>` con `module_group` (`NetScaler` por
defecto, vacío en el archivo de ejemplo). Las claves `module_tags` y `agent_group`
se aceptan pero no tienen efecto, de modo que los documentos generados no llevan
etiquetas ni grupo.

## Operación y diagnóstico

### Comportamiento de la ejecución

- El plugin se ejecuta una vez, lee el dispositivo y termina. No conserva estado,
  así que dos ejecuciones consecutivas devuelven los valores que el dispositivo
  informa en su momento.
- La salida estándar está vacía cuando la ejecución es correcta. Los diagnósticos,
  los errores de copia y las transferencias descartadas van a la salida de error
  estándar. No hay archivo de registro ni opción de depuración o de salida
  detallada.
- Un fallo de entrega no cambia el estado de salida: `cron` informa de éxito
  incluso cuando el documento se descartó. Utilice la frescura de los agentes y de
  `Plugin message` en Pandora FMS, no solo el estado de salida, para confirmar la
  entrega.
- Establezca `lwp_timeout` en redes donde el dispositivo pueda tardar en
  responder; sin él la ejecución espera el valor por defecto del cliente HTTP.
- Guarde el archivo de configuración con permisos restrictivos: contiene la
  contraseña del dispositivo.

### Diagnóstico

- **Se imprime el resumen de uso y el estado es `1`** — el plugin no recibió
  ningún argumento. Indique la ruta del archivo de configuración.
- **No se informa de una ruta de configuración incorrecta** — el plugin no
  diagnostica un archivo de configuración ilegible: continúa con valores vacíos y
  falla más adelante, normalmente en la primera petición. Compruebe la ruta de la
  entrada de `cron`.
- **`Plugin message` informa `0` con `No response from ...`** — la petición a
  `ns_url` no devolvió una respuesta JSON correcta. Compruebe la URL y su ruta de
  API, que el dispositivo sea accesible desde el host del plugin, que la cuenta
  pueda autenticarse y que el certificado del dispositivo sea de confianza.
- **La ejecución se detiene con un error y no entrega nada** — el dispositivo
  respondió con un cuerpo que no es el JSON esperado y su decodificación termina
  la ejecución antes de construir ningún agente. Confirme que `ns_url` apunta a la
  API de estadísticas y no a una página de acceso u otro extremo.
- **Un servicio de `ns_services` no genera ningún agente** — su nombre no está en
  el catálogo que devuelve el dispositivo, o se escribió con mayúsculas distintas
  o con espacios. Compare el nombre con los objetos que expone el dispositivo.
- **La ejecución se detiene después de entregar algunos agentes** — un servicio
  enumerado en el catálogo respondió con error y esta versión no se recupera de
  ello: los servicios restantes no se procesan. Corrija las credenciales o los
  permisos del servicio y vuelva a ejecutar el plugin.
- **`<objeto> statbindings` informa `UNREACHABLE`** — la petición de vinculaciones
  falló o devolvió JSON no válido; el resto de módulos del objeto se generan
  igualmente.
- **`<objeto> statbindings` informa `OK` y no aparece ningún módulo por servidor**
  — la respuesta no contiene ningún servidor vinculado a ese objeto.
- **Un agente de objeto contiene solo unos pocos módulos** — `modules_list` no
  incluye los campos que devuelve el objeto, o el dispositivo no los devuelve.
  Quite el filtro para ver todos los campos en una ejecución de prueba.
- **Ningún documento llega a Pandora FMS** — compruebe que `temp` existe y tiene
  permiso de escritura y, después, el destino: `tentacle_client`, `tentacle_ip` y
  `tentacle_port` para Tentacle, o un `local_folder` existente y con permiso de
  escritura para el modo local. La causa se imprime en la salida de error
  estándar.
- **`There was a problem copying local file to ...`** — `mode` no es `tentacle` y
  la copia en `local_folder` falló. Compruebe que la carpeta existe y tiene
  permiso de escritura.
- **`[...] discarted`** — los dos intentos de Tentacle fallaron y el documento se
  eliminó. Compruebe el servicio Tentacle y la ruta del cliente.
- **Los valores parecen desactualizados** — el plugin informa siempre de lo que
  devuelve el dispositivo en el momento de la ejecución. Compruebe que `cron` lo
  sigue ejecutando y que `agent_interval` coincide con el periodo de `cron`.

## Referencia

### Archivo de configuración

| Nombre | Obligatorio | Valor por defecto | Descripción |
| --- | --- | --- | --- |
| `ns_url` | Sí | Vacío | URL base de la API de estadísticas NITRO, con esquema y ruta de la API. El plugin la solicita para leer el catálogo y le añade `/<servicio>` en cada lectura de servicio |
| `ns_user` | Sí | Vacío | Cuenta usada para leer la API de estadísticas, enviada en la cabecera `X-NITRO-USER` |
| `ns_pass` | Sí | Vacío | Contraseña de esa cuenta, enviada en la cabecera `X-NITRO-PASS`. Se guarda en texto plano |
| `ns_services` | Sí, al menos uno | Ninguno | Repetible. `ns_services=<servicio>;<valor>`, donde `<valor>` es `1` para declarar `agent_name` como padre, `0` o vacío para no tener padre |
| `modules_list` | No | Vacío, filtro desactivado | Lista de nombres de campo estadístico permitidos, separados por comas, exactos, sensibles a mayúsculas y sin espacios |
| `ns_service_prefix` | No | Vacío | Texto antepuesto a los nombres de los agentes generados para los objetos de un servicio multiinstancia |
| `agent_name` | No | `NetScaler` | Nombre del agente principal y referencia de padre de los agentes de objeto |
| `agent_desc` | No | Vacío | Descripción escrita en todos los agentes generados |
| `agent_interval` | No | `300` | Intervalo del agente declarado a Pandora FMS, en segundos |
| `module_interval` | No | `1` | Valor escrito como `module_interval` en todos los módulos |
| `module_group` | No | `NetScaler` | Valor escrito como `module_group` en todos los módulos |
| `mode` | No | `tentacle` | `tentacle` entrega con el cliente Tentacle; cualquier otro valor copia el documento en `local_folder` |
| `local_folder` | Sí cuando `mode` no es `tentacle` | Vacío | Carpeta de destino de los documentos de agente copiados |
| `tentacle_ip` | Sí cuando `mode = tentacle` | Vacío | Dirección del servidor Tentacle de Pandora FMS |
| `tentacle_port` | No | `41121` | Puerto del servidor Tentacle de Pandora FMS |
| `tentacle_client` | No | `tentacle_client` | Cliente Tentacle que se ejecuta, resuelto mediante `PATH` cuando es un nombre simple |
| `tentacle_opts` | No | Vacío | Opciones adicionales insertadas tal cual en la línea de comandos de Tentacle |
| `temp` | No | `/tmp` | Carpeta donde se escribe el documento de agente antes de entregarlo. Debe existir y tener permiso de escritura |
| `lwp_timeout` | No | Sin valor | Tiempo máximo de espera de cada petición HTTP, en segundos. Sin valor, el plugin no aplica un tiempo máximo explícito |

Las claves y los valores se recortan; una clave escalar repetida conserva su
último valor y `ns_services` se acumula.

### Aceptadas pero no aplicadas

Estas claves se leen sin error pero no tienen efecto en los documentos generados
en esta versión:

| Nombre | Efecto |
| --- | --- |
| `module_tags` | No se escriben etiquetas en los módulos |
| `agent_group` | El documento de agente no lleva grupo |
| `log` | No se escribe ningún archivo de registro |
| `api_url`, `api_user`, `api_user_pass`, `api_pass` | Nunca se llama a la API de Pandora FMS; no se crea ningún grupo ni etiqueta en la consola |

El archivo de configuración de ejemplo todavía las enumera, así que eliminarlas o
mantenerlas no cambia nada.

### Ejecución desde la línea de comandos

| Condición | Comportamiento |
| --- | --- |
| Sin argumentos | Imprime el resumen de uso y termina con estado `1` |
| Un argumento | Se ejecuta con ese archivo como configuración |
| Más de un argumento | Solo se lee el primero; el resto se ignora |
| Cualquier opción, como `-h` o `--help` | Se trata como la ruta del archivo de configuración; no hay análisis de opciones |
| El argumento nombra un archivo ilegible | La ejecución continúa con valores de configuración vacíos y falla más adelante, sin un diagnóstico sobre el archivo |

### Entorno

| Variable | Efecto |
| --- | --- |
| `http_proxy`, `https_proxy`, `no_proxy` | Las usa el cliente HTTP para las peticiones al dispositivo |

### Módulos que genera

| Módulo | Tipo | Se emite en | Descripción |
| --- | --- | --- | --- |
| `Plugin message` | `generic_proc` | `agent_name` | `1` con `Execution OK`, o `0` con `No response from <ns_url>` |
| Nombres de campo estadístico devueltos por el objeto | `generic_data` o `generic_data_string` | Agente del objeto | Un módulo por campo permitido y valor devuelto |
| `<objeto> statbindings` | `generic_data_string` | Agente del objeto, servicio multiinstancia | `OK` o `UNREACHABLE` |
| `<objeto> <vinculación>` | `generic_data` o `generic_data_string` | Agente del objeto, servicio multiinstancia y respuesta válida | Estado de un servidor vinculado, con su dirección IP primaria en la descripción |

### Identidad del addon

| Propiedad | Valor |
| --- | --- |
| Identificador del Marketplace | `pandorafms.citrix_netscaler` |
| Nombre | Citrix NetScaler monitoring |
| Versión | `1.0` |
| Paquete | `pandorafms.citrix_netscaler.1.0.zip` |
| Licencia | One; la descarga está limitada a usuarios con licencia |
| Última actualización en el Marketplace | 2025-07-09 |
| Descargas | 1 |
| Autor | Pandora FMS |
