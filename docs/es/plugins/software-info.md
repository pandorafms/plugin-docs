# Software Info

*Última actualización del artículo: 2026-09-25.*

## Qué hace

Software Info es un plugin de agente de Pandora FMS que informa de los paquetes de software con una actualización pendiente en el host donde se ejecuta el agente. En cada ejecución imprime, en la salida estándar, un documento `extended_data` de categoría `software` con una entrada por cada paquete pendiente.

Cuando el envío de eventos está activado, el plugin imprime además un bloque hermano `events` con un evento por cada actualización pendiente, de forma que la actualización se pueda lanzar desde la consola, por ejemplo mediante una ejecución RMM.

El plugin solo consulta los gestores de paquetes ya presentes en el host mediante comandos de solo lectura. Nunca instala, actualiza ni modifica software. La salida estándar contiene únicamente el XML generado; los diagnósticos van a un archivo de log.

## Preparación

### Compatibilidad y disponibilidad

El plugin es compatible con hosts Linux y Windows. En Linux puede consultar apt, dnf, yum, pacman, zypper y apk; en Windows consulta winget. Un gestor de paquetes que no está instalado se omite de forma silenciosa.

### Requisitos

1. Un agente de Pandora FMS instalado y en ejecución en el host monitorizado.
2. El gestor o gestores de paquetes que se van a consultar instalados en el host, con los metadatos necesarios para informar de las versiones disponibles.
3. Permiso para ejecutar los comandos de consulta del gestor de paquetes por parte del usuario que ejecuta el agente.
4. Una ubicación con permiso de escritura para el log de diagnósticos y el archivo de estado, o rutas personalizadas indicadas en la ejecución.

### Instalar el plugin

El plugin se distribuye como el binario `software_info` para Linux y `software_info.exe` para Windows. Despliéguelo en el endpoint que lo ejecutará y regístrelo en la configuración del agente como se describe en Configuración.

## Configuración

Registre el plugin en la configuración del agente como plugin de agente. El agente lo ejecuta periódicamente y añade su salida en bruto al XML que envía:

```
module_begin
module_absoluteinterval 1d
module_plugin software_info
module_end
```

Las opciones de línea de comandos se pueden añadir a la línea `module_plugin`:

```
module_begin
module_absoluteinterval 1d
module_plugin software_info -timeout 60s -event-mode changes
module_end
```

Todas las opciones son opcionales. Consulte la Referencia para la lista completa.

## Verificación

Ejecute primero el plugin manualmente para confirmar que recopila datos y genera XML bien formado:

```
software_info
```

Una ejecución correcta escribe un documento `extended_data` en la salida estándar. Cuando un paquete tiene una actualización pendiente, el documento contiene un `extended_data_module` llamado `Software`:

```xml
<extended_data>
	<extended_data_module>
		<name><![CDATA[Software]]></name>
		<category><![CDATA[software]]></category>
		<datalist>
			<data>
				<field name="available_version"><![CDATA[3.0.13-1]]></field>
				<field name="current_version"><![CDATA[3.0.7-1]]></field>
				<field name="fms_object_unique_id"><![CDATA[apt:openssl]]></field>
				<field name="manager"><![CDATA[apt]]></field>
				<field name="name"><![CDATA[openssl]]></field>
			</data>
		</datalist>
	</extended_data_module>
</extended_data>
```

Cuando el envío de eventos está activado y hay algo que informar, a continuación aparece un bloque hermano `events`. Cuando no hay nada pendiente se imprime un campo `message` con `No pending software updates`. Con el inventario desactivado y sin eventos no se imprime nada.

## Entender los resultados

### Inventario de software pendiente

El plugin siempre emite un documento `extended_data` de categoría `software`. Cuando hay algo que actualizar, cada elemento expone los siguientes campos; cuando no hay nada pendiente, el documento incluye un único campo `message` (`No pending software updates`) para que la categoría siempre esté presente:

| Campo | Contenido |
| --- | --- |
| `name` | Nombre del paquete tal y como lo informa el gestor de paquetes. |
| `current_version` | Versión instalada. Vacío cuando el método de consulta no puede informarla de forma económica. |
| `available_version` | Versión que ofrece el gestor de paquetes. |
| `manager` | Gestor de paquetes que informó de la actualización (apt, dnf, yum, pacman, zypper, apk, winget). |
| `fms_object_unique_id` | Identificador estable `<manager>:<name>`. |

Los elementos se ordenan alfabéticamente por gestor y nombre.

### Eventos

Cuando los eventos están activados, cada actualización emitida genera una entrada en el bloque `events`. El contenido es la codificación base64 de un objeto JSON con el mensaje (`data`) y la severidad, el formato que acepta el procesamiento de eventos del servidor. Los eventos se controlan con `-event-mode` y el archivo de estado persistido, de modo que una actualización pendiente sin cambios no se repite en cada ejecución.

## Operación y resolución de problemas

### Detección de cambios

Por defecto el plugin persiste el conjunto de paquetes pendientes en un archivo de estado y emite un evento solo para un paquete que pasa a estar pendiente o cuya versión disponible ha cambiado. Use `-event-mode always` para emitir un evento por cada paquete pendiente en cada ejecución, o `-event-mode off` para no emitir nunca eventos. El archivo de estado solo se lee y escribe en el modo de cambios.

### Ejecución y código de salida

El comando es de una sola ejecución. Devuelve el código 0 en caso de éxito, incluidas recopilaciones parciales o degradadas, y solo devuelve un valor distinto de cero ante un fallo grave al interpretar argumentos o generar el XML.

### Diagnósticos

Los diagnósticos se escriben en el archivo de log configurado y, si este no se puede escribir, pasan a la salida de error estándar. Nunca llegan a la salida estándar. El log se rota y el archivo de estado se escribe de forma atómica con permisos restrictivos.

### Limitaciones conocidas

- En Windows, la salida de winget depende del idioma; las filas que no se pueden leer con fiabilidad se descartan en lugar de informarse mal.
- En sistemas que usan dnf o zypper, las versiones disponibles reflejan la última actualización de metadatos de repositorios realizada por el host; el plugin nunca actualiza metadatos.
- El bloque `events` es una superficie del servidor no documentada; no existe otro productor de él en el producto.
- No existe un tipo de esquema de inventario ITSM para los datos extendidos de categoría `software`.

## Referencia

### Parámetros de línea de comandos

| Nombre | Obligatorio | Por defecto | Descripción |
| --- | --- | --- | --- |
| `-timeout` | No | `60s` | Tiempo máximo permitido para la recopilación. |
| `-log-path` | No | `/var/log/pandora/software_info.log` (Linux), `%ProgramData%\PandoraFMS\software_info.log` (Windows) | Ruta del log de diagnósticos. |
| `-state-path` | No | `/var/lib/pandora/software_info.state` (Linux), `%ProgramData%\PandoraFMS\software_info.state` (Windows) | Ruta del archivo de estado para la detección de cambios. |
| `-severity` | No | `3` | Severidad de los eventos emitidos (0-6). |
| `-inventory` | No | `true` | Emitir el inventario `extended_data` de actualizaciones pendientes. Use `-inventory=false` para informar solo eventos. La combinación de `-inventory=false` con `-event-mode off` se rechaza. |
| `-event-mode` | No | `changes` | Política de eventos: `changes`, `always` u `off`. |
| `-managers` | No | todos los disponibles | Subconjunto de gestores de paquetes separado por comas. |

### Gestores de paquetes compatibles

| Plataforma | Gestor | Consulta de solo lectura |
| --- | --- | --- |
| Linux | apt | `apt-get -s -q upgrade` |
| Linux | dnf | `dnf -q check-update` |
| Linux | yum | `yum -q check-update` |
| Linux | pacman | `pacman -Qu` |
| Linux | zypper | `zypper --quiet list-updates` |
| Linux | apk | `apk version -l '<'` |
| Windows | winget | `winget list --upgrade-available --disable-interactivity` |

Todos los comandos de consulta se ejecutan sin shell y con un locale C fijo.
