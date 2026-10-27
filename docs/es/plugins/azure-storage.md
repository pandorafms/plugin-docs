# Plugin de monitorización Pandora Azure Storage

*Última actualización del artículo: 2026-10-27.*

!!! warning "Se recomienda la integración de Discovery"
    Para instalaciones nuevas use [Azure Storage Discovery](../discovery/azure-storage.md), que es la integración recomendada para este servicio. Este plugin es la ruta heredada.

## Qué hace

El plugin Pandora Azure Storage lee las métricas de Azure Monitor de una cuenta
de almacenamiento de Azure y de los servicios de esa cuenta que habilite —Blob,
File, Queue, Table y Data Lake Storage— y las publica como módulos de Pandora
FMS, agrupados en un agente por servicio.

Cada ejecución trabaja sobre los identificadores de recurso escritos en un
archivo de configuración: la propia cuenta de almacenamiento y cada servicio
que quiera leer. El plugin pide a Azure Monitor la última hora de cada métrica
y construye los módulos con la respuesta. No hay paso de descubrimiento ni
enumeración de recursos de Azure: la cuenta y los servicios son los que usted
escribe en ese archivo.

El plugin tiene tres rutas de ejecución:

- **Sin opción de entrega (por defecto).** Imprime un bloque XML `<module>` por
  módulo en la salida estándar, para que lo recoja un agente de Pandora FMS.
- **`--as_agent_plugin 1`.** Construye un documento XML `agent_data` por cada
  servicio habilitado, escribe cada uno en `data_dir` e imprime `1`. A pesar de
  su nombre, esta opción produce la ejecución del lado del servidor.
- **`--tentacle_address`.** Construye los mismos documentos `agent_data`, los
  entrega con el cliente de Tentacle e imprime `1`.

Esta página documenta el plugin **`pandorafms.azure_storage`**, distribuido como
paquete `.pspz2`. El **Discovery** de Azure Storage es otro addon: se ejecuta
desde una tarea de Discovery, enumera las cuentas de almacenamiento de una
suscripción o de un grupo de recursos, crea un agente por cuenta descubierta y
no necesita archivo de configuración. Consulte
[Azure Storage Discovery](../discovery/azure-storage.md). La aplicación de
Discovery usa además `pandorafms.azure_storage` como nombre corto, así que
compruebe el tipo de paquete antes de instalar: `.pspz2` es este plugin,
`.disco` es Discovery.

## Preparación

### Compatibilidad y disponibilidad

| Alcance | Estado | Evidencia |
| --- | --- | --- |
| Addon `pandorafms.azure_storage`, versión `1.0` | Objetivo documentado | Versión de la entrada del Marketplace y del paquete distribuido. Véase [Identidad del addon](#identidad-del-addon) |
| Pandora FMS NG 784 y posteriores | `Soportado` | El Marketplace indica que todas sus integraciones son compatibles con Pandora FMS NG 784 y posteriores. Es una declaración de catálogo que cubre este addon, no un registro de prueba del mismo |
| CentOS 7, Fedora y Rocky Linux como sistema del host | `Compatible conocido` | La edición anterior de esta guía registra esos sistemas como los que se probaron; no se ha revalidado para la versión `1.0` |
| Otros sistemas del host | `Sin validar` | No hay otro sistema registrado para este addon |
| Un registro de aplicación de Microsoft Entra capaz de leer las métricas de Azure Monitor de la cuenta | `Requerido` | Cada consulta de recolección se autentica con su identificador de inquilino, su identificador de cliente y su secreto |
| El identificador de recurso de Azure de la cuenta de almacenamiento y de cada servicio que habilite | `Requerido` | Cada valor se consulta directamente como recurso de métricas de ese servicio |
| `tentacle_client` en `PATH` | `Requerido` cuando se usa `--tentacle_address` | La entrega ejecuta el cliente de Tentacle |
| Un `data_dir` con permiso de escritura | `Requerido` cuando se escribe el documento de agente | El documento XML se crea en esa carpeta |
| Nubes soberanas o personalizadas de Azure | `Sin validar` | El addon no expone ninguna opción de endpoint, así que los endpoints de Microsoft no se pueden redirigir |

La entrada del Marketplace no declara ningún estado de mantenimiento ni de
ciclo de vida para este addon.

### Requisitos

1. **Una instalación de Pandora FMS con el servidor de plugins habilitado**,
   para ejecutar el plugin, y el servidor de datos para ingerir los documentos
   `agent_data` cuando la ejecución los escribe.
2. **Una suscripción de Azure con al menos una cuenta de almacenamiento** que
   monitorizar.
3. **Un registro de aplicación de Microsoft Entra** para el plugin: su
   identificador de inquilino, su identificador de cliente y un secreto de
   cliente.
4. **Los identificadores de recurso de Azure** de la cuenta de almacenamiento y
   de cada servicio que quiera leer, escritos en el archivo de configuración.
5. **El cliente de Tentacle (`tentacle_client`) disponible en `PATH`**, solo
   cuando la ejecución entrega mediante Tentacle.

### Prepare el acceso en Azure

Cree un registro de aplicación en Microsoft Entra ID y anote su
**identificador de inquilino**, su **identificador de cliente** y el **valor de
un secreto de cliente**. Estos tres valores van al archivo de configuración.

El plugin no indica qué rol de Azure asignar. Solo llama a la API de métricas
de Azure Monitor para los identificadores de recurso de la configuración, así
que el registro necesita permiso para leer las métricas de esos recursos.
Asigne el rol más restrictivo que conceda esa lectura sobre la cuenta de
almacenamiento o sobre su grupo de recursos.

Hacen falta dos grupos más de valores:

- **El identificador de recurso de la cuenta de almacenamiento**, el ámbito de
  cuenta que el plugin consulta para sus métricas de cuenta. Su forma es
  `/subscriptions/<SUBSCRIPTION_ID>/resourceGroups/<RESOURCE_GROUP>/providers/Microsoft.Storage/storageAccounts/<ACCOUNT>`.
- **El identificador de recurso de cada servicio** que habilite: Blob, File,
  Queue, Table y Data Lake Storage. La edición anterior de esta guía obtiene
  todos ellos de las propias páginas de la cuenta en el portal de Azure.

El plugin envía cada valor exactamente como está escrito. Un identificador mal
formado, o uno que el registro de aplicación no pueda leer, hace fallar la
ejecución con la excepción de Azure; un identificador válido que no tenga datos
para una métrica solo deja de producir el módulo de esa métrica. Copie los
identificadores desde Azure en vez de escribirlos a mano.

### Instalación del plugin

Cargue el paquete `.pspz2` desde la página de registro de plugins de la consola.
El paquete registra el plugin con la definición descrita en
[Registro del plugin en la consola](#registro-del-plugin-en-la-consola),
incluidas las tres macros del formulario de registro.

El plugin lee un archivo de configuración que debe aportar usted. El valor
distribuido de la primera macro es
`/var/www/html/pandora_console/attachment/plugin/pandora_azure.conf`, así que
escriba el archivo ahí o cambie la macro a la ruta que use. La sección
[Archivo de configuración](#archivo-de-configuracion) describe su contenido.

## Configuración

### Archivo de configuración

El archivo es texto plano y usa líneas `clave:valor`. Cada valor se recorta.
Tres reglas deciden qué lee el plugin:

- Una línea que contenga `#` en cualquier posición se omite, así que los
  comentarios empiezan en cualquier punto y un valor que contenga `#` se pierde
  con su línea.
- La línea se parte por `:` y solo se conserva el segundo fragmento: un valor
  que contenga `:` se trunca en los dos puntos.
- Las claves se buscan por subcadena, no como nombre exacto de clave: una línea
  que contenga el nombre de una clave conocida se lee como esa clave, una línea
  que no contenga ninguna se ignora, y una clave repetida conserva el último
  valor leído.

Este es el archivo completo que distribuye el addon, con marcadores:

```ini
#credentials
tenant_id:<TENANT_ID>
client_id:<CLIENT_ID>
secret:<CLIENT_SECRET>
#id resources
account_id:<ACCOUNT_RESOURCE_ID>
blobservice_id:<BLOB_SERVICE_RESOURCE_ID>
fileservice_id:<FILE_SERVICE_RESOURCE_ID>
queueservice_id:<QUEUE_SERVICE_RESOURCE_ID>
tableservice_id:<TABLE_SERVICE_RESOURCE_ID>
datalakestorage_id:<DATA_LAKE_SERVICE_RESOURCE_ID>
#active agents
account_agent:1
blobservice_agent:1
fileservice_agent:1
queueservice_agent:1
tableservice_agent:1
datalakestorage_agent:1
```

Las tres claves de credenciales y los seis interruptores `<servicio>_agent` son
obligatorios: el plugin los lee todos antes de recolectar nada, y si falta uno
la ejecución se detiene con una traza `NameError`. Cada `<servicio>_id` solo es
necesario cuando su interruptor vale `1`. Un interruptor vale `1` para
habilitar el servicio y `0` para dejarlo fuera; cualquier otro valor detiene la
ejecución con una `ValueError`.

Para monitorizar solo la cuenta y el servicio Blob, por ejemplo:

```ini
#credentials
tenant_id:<TENANT_ID>
client_id:<CLIENT_ID>
secret:<CLIENT_SECRET>
#id resources
account_id:<ACCOUNT_RESOURCE_ID>
blobservice_id:<BLOB_SERVICE_RESOURCE_ID>
#active agents
account_agent:1
blobservice_agent:1
fileservice_agent:0
queueservice_agent:0
tableservice_agent:0
datalakestorage_agent:0
```

Un valor vacío se lee como vacío y falla en el momento de la autenticación, no
al analizar el archivo. Mantenga el archivo legible solo por el usuario que
ejecuta el plugin: contiene el secreto de cliente en texto claro.

### Modos de ejecución y entrega

El plugin procesa los servicios habilitados en un orden fijo y empieza una
lista de módulos nueva para cada uno: primero la cuenta y después Blob, Queue,
File, Table y Data Lake Storage. Cada servicio entrega su propio agente, así
que una ejecución con los seis interruptores habilitados entrega seis agentes.

La entrega se elige por servicio, con estas reglas:

| Línea de comandos | Qué hace la ejecución |
| --- | --- |
| `--tentacle_address <TARGET_HOST>` | Escribe el documento `agent_data` del servicio y lo envía con `tentacle_client -v -a <TARGET_HOST> -p <puerto> <archivo>`. Imprime `1` después de cada servicio |
| `--as_agent_plugin 1` sin `--tentacle_address` | Escribe el documento `agent_data` del servicio en `data_dir` e imprime `1` |
| Ninguna de las dos opciones | Imprime los módulos del servicio como bloques XML `<module>` en la salida estándar y no escribe ningún archivo |

La ruta de Tentacle borra el documento local después de un envío correcto, así
que la carpeta `data_dir` queda sin archivos cuando la ejecución termina bien.
El plugin pasa al cliente de Tentacle solo la dirección y el puerto; no tiene
ninguna opción para una contraseña de Tentacle.

`--tentacle_address` tiene prioridad sobre `--as_agent_plugin`, así que una
ejecución con ambas opciones escribe el documento, lo entrega e imprime `1`.

El servicio Data Lake Storage no sigue la misma regla: con `--as_agent_plugin 1`
y sin dirección de Tentacle imprime sus módulos en la salida estándar en lugar
de escribir un documento, y solo escribe el documento cuando
`--as_agent_plugin` está ausente o es distinto de `1`. Véase
[Limitaciones](#limitaciones).

### Credenciales y transporte

- El secreto de cliente se guarda en el archivo de configuración en texto
  claro. Restrinja los permisos del archivo al usuario que ejecuta el plugin y
  manténgalo fuera de directorios compartidos y del control de versiones.
- El secreto no es una opción de línea de comandos, así que no aparece en el
  historial del shell ni en la lista de procesos. Sí aparece en el archivo de
  configuración al que apunta el comando del plugin de la consola.
- El addon no expone ninguna opción de endpoint: la autenticación y las
  consultas de métricas van a los endpoints de identidad y de gestión de
  Microsoft por defecto. No hay ajuste para una nube soberana, un endpoint
  personalizado ni un proxy.

### Registro del plugin en la consola

El plugin se puede registrar en la consola de Pandora FMS como plugin de
servidor, para que Pandora FMS lo ejecute desde el servidor que corre los
módulos en lugar de desde una línea de comandos. La definición de registro del
paquete `.pspz2` fija estos valores:

| Campo | Valor |
| --- | --- |
| Nombre del plugin | `Pandora Azure Storage` |
| Descripción | `Take data from azure storage` |
| Tipo de plugin | `Standard` (`plugin_type = 0`) |
| Tiempo máximo de espera | `20` segundos |
| Comando del plugin | El archivo `pandora_azure` del paquete |
| Parámetros del plugin | `-c " _field1_ " --agent_name " _field2_ " -g " _field3_ "` |
| Módulos que aporta | `0` (`total_modules_provided = 0`) |

La definición declara tres macros. El formato no tiene tipo por macro, y las
tres tienen `hide = 0`, así que la consola muestra los tres campos en texto
claro:

| Macro | ¿Obligatoria? | Valor por defecto | Ocultar | Descripción y ayuda |
| --- | --- | --- | --- | --- |
| `_field1_` | Sí, según su descripción | `/var/www/html/pandora_console/attachment/plugin/pandora_azure.conf` | No | `Conf path (obligatory)`. Ayuda: `Path conf` |
| `_field2_` | No | `_agentname_` | No | `Agent name (optional)`. Ayuda: `Name of the agent`. El valor por defecto es la macro de consola que se sustituye por el nombre del agente que contiene el módulo |
| `_field3_` | No | `azure` | No | `group (optional)`. Ayuda: `Pandora FMS Target Group ` |

<!-- SCREENSHOT NEEDED: Formulario de módulo de plugin en la consola de Pandora FMS con los tres campos de macro de Pandora Azure Storage, con una ruta de configuración de ejemplo y sin credenciales reales. -->

Los parámetros registrados no incluyen `--tentacle_address` ni
`--as_agent_plugin`, así que una ejecución de módulo lanzada desde esta
definición imprime el XML de los módulos en la salida estándar. Para que cada
ejecución entregue sus agentes por sí misma, añada la opción de entrega a
**Parámetros del plugin**, por ejemplo:

```text
-c " _field1_ " --agent_name " _field2_ " -g " _field3_ " --tentacle_address 127.0.0.1
```

Cada campo del plugin es un valor de configuración, no una selección de
servicio: los servicios se habilitan en el archivo de configuración, así que un
plugin registrado sirve para cualquier cuenta cuyo archivo se referencie. El
tiempo máximo de espera de `20` segundos es bajo para una ejecución que
consulta todos los servicios; auméntelo si la ejecución alcanza el tiempo
límite. Véase [Planificación y ejecución](#planificacion-y-ejecucion).

## Verificación

Ejecute el plugin a mano desde una terminal, pasando el archivo de
configuración después de `-c`. En el modo por defecto imprime los módulos de
cada servicio habilitado:

```bash
./pandora_azure -c <PATH_TO_CONFIG>
```

La ejecución se hace una vez y termina. Una ejecución correcta imprime bloques
`<module>` y nada en la salida de error. El ejemplo siguiente muestra la forma
de la salida para el servicio de cuenta, con un punto de datos por módulo:

```xml
<module>
	<name><![CDATA[UsedCapacity]]></name>
	<type>generic_data</type>
	<data><![CDATA[1099511627776.0]]></data>
	<description><![CDATA[2026-10-26 09:00:00+00:00 The amount of storage used by the storage account.]]></description>
	<unit><![CDATA[bytes]]></unit>
</module>
<module>
	<name><![CDATA[Transactions]]></name>
	<type>generic_data_string</type>
	<datalist>
	<data>
		<value><![CDATA[The Transactions at 2026-10-26 09:05:00+00:00 is 142.0]]></value>
	</data>
	<description><![CDATA[The number of requests made to a storage service or the specified API operation.]]></description>
</module>
```

El ejemplo está construido a partir de las definiciones de módulo del addon;
no es una ejecución capturada, porque los valores dependen de la cuenta.

Para comprobar la ruta del lado del servidor, ejecútelo con
`--as_agent_plugin 1` y una carpeta de datos desechable, y después inspeccione
el archivo:

```bash
mkdir -p /tmp/azure-storage-check
./pandora_azure -c <PATH_TO_CONFIG> --as_agent_plugin 1 --data_dir /tmp/azure-storage-check
ls /tmp/azure-storage-check
```

Una ejecución correcta imprime `1` una vez por servicio habilitado, y la
carpeta contiene un documento `<nombre de agente>.<segundos epoch>.data` por
servicio habilitado. El servicio Data Lake Storage es la excepción descrita en
[Limitaciones](#limitaciones). El nombre del archivo usa el valor de
`--agent_name` seguido del sufijo del servicio, así que los nombres por defecto
son `Azure_Monitor.Azure_Storage_Account_Metrics.<epoch>.data` y
`Azure_Monitor.Blob_Service_Metrics.<epoch>.data`.

En Pandora FMS, tras la primera ejecución entregada, los agentes aparecen con
sus módulos. El agente de cuenta lleva `UsedCapacity` y los seis módulos de
texto; cada agente de servicio lleva sus módulos de capacidad y sus propios
seis módulos de texto. Véase [Entienda los resultados](#entienda-los-resultados).

## Entienda los resultados

### Agentes

Una ejecución crea un agente por servicio habilitado, y el sufijo del servicio
se añade al valor de `--agent_name` sin separador:

| Interruptor del servicio | Sufijo del nombre de agente | Nombre de agente por defecto |
| --- | --- | --- |
| `account_agent` | `Azure_Storage_Account_Metrics` | `Azure_Monitor.Azure_Storage_Account_Metrics` |
| `blobservice_agent` | `Blob_Service_Metrics` | `Azure_Monitor.Blob_Service_Metrics` |
| `queueservice_agent` | `Queue_Service_Metrics` | `Azure_Monitor.Queue_Service_Metrics` |
| `fileservice_agent` | `File_Service_Metrics` | `Azure_Monitor.File_Service_Metrics` |
| `tableservice_agent` | `Tables_Service_Metrics` | `Azure_Monitor.Tables_Service_Metrics` |
| `datalakestorage_agent` | `Datalake_Storage_Service_Metrics` | `Azure_Monitor.Datalake_Storage_Service_Metrics` |

La cabecera `agent_data` fija `agent_mode` en `1` y toma el grupo de `-g`
(`Azure` cuando la opción no está), y el alias del mismo valor que el nombre.
El plugin no fija un intervalo de agente: `interval` viaja vacío en la
cabecera.

El agente del servicio File lleva la descripción `Blob Service Metrics`, el
mismo texto que el agente Blob. Véase [Limitaciones](#limitaciones).

### Módulos

Cada servicio publica dos clases de módulo:

- **Los módulos de capacidad y de recuento** son `generic_data`. Llevan el
  valor devuelto para una métrica, con la unidad `bytes` cuando la métrica es
  un tamaño. Solo aparecen cuando Azure devuelve datos para esa métrica.
- **Los módulos de tasa y de latencia** son `generic_data_string` con un
  `datalist`. Cada entrada es el texto `The <métrica> at <marca de tiempo> is
  <valor>`, una por punto de datos de la última hora, así que una ejecución
  escribe normalmente unas doce entradas. Estos módulos se crean aunque Azure
  no devuelva datos, y en ese caso el `datalist` llega vacío.

El conjunto de la cuenta es `UsedCapacity`, `Transactions`, `Ingress`,
`Egress`, `SucessServerLatency`, `SuccessE2ELatency` y `Availity`. Cada
servicio repite los seis módulos de tasa, latencia y disponibilidad con su
propio sufijo, por ejemplo `Transactions_blobs` o `Availity_tables`. La lista
exhaustiva está en [Agentes y módulos](#agentes-y-modulos).

Los nombres de módulo son los que publica el addon, incluidas las grafías
`SucessServerLatency` y `Availity`. Las alertas, informes y paneles deben usar
esos nombres exactos.

Un módulo de capacidad se crea una vez por cada punto de datos devuelto, y
todas las entradas tienen el mismo nombre. Una consulta de capacidad sobre una
hora con granularidad de sesenta minutos devuelve normalmente uno o dos puntos,
así que el mismo nombre de módulo puede aparecer dos veces en un documento.
Véase [Limitaciones](#limitaciones).

## Operación y resolución de problemas

### Planificación y ejecución

- El plugin no guarda estado entre ejecuciones: cada ejecución consulta Azure
  en ese momento. La ejecución se puede repetir a mano en cualquier momento.
- Una ejecución con los seis servicios habilitados hace 57 peticiones a Azure
  Monitor, una por métrica, una detrás de otra: 7 de la cuenta, 10 de Blob, 9
  de Queue, 12 de File, 9 de Table y 10 de Data Lake Storage. La definición de
  registro declara un tiempo máximo de espera de `20` segundos, que una
  ejecución completa puede superar; aumente el tiempo límite en la consola o
  habilite solo los servicios que necesite.
- En modo servidor, planifique el plugin desde Pandora FMS o desde `cron`. El
  plugin no fija el intervalo del agente: `interval` viaja vacío en la cabecera
  `agent_data`.

### Limitaciones

- **Sin opción de endpoint.** La autenticación y las consultas de métricas van
  a los endpoints de Microsoft por defecto, así que no se puede configurar una
  nube soberana o personalizada.
- **Sin opción de proxy, y el plugin no reintenta.** Una petición fallida
  termina la ejecución con la excepción que la produjo; repetir la recolección
  queda para la siguiente ejecución planificada.
- **La entrega de Data Lake está invertida.** Con `--as_agent_plugin 1` y sin
  dirección de Tentacle, el servicio Data Lake Storage imprime sus módulos en
  la salida estándar en lugar de escribir su documento, mientras que los otros
  cinco servicios escriben el suyo. Use `--tentacle_address` para entregar los
  seis en el lado del servidor.
- **La opción de entrega se llama como el modo contrario.**
  `--as_agent_plugin 1` produce el documento del lado del servidor; el modo por
  defecto es el de plugin de agente.
- **`--prefix_module` no tiene efecto.** La opción se acepta y se ignora: no
  prefija los nombres de módulo, y los módulos conservan los nombres de
  [Agentes y módulos](#agentes-y-modulos).
- **Una cuenta por archivo de configuración.** El archivo contiene un juego de
  identificadores de recurso, así que monitorizar varias cuentas necesita un
  archivo y una ejecución del plugin por cuenta.
- **Sin protección del secreto.** El secreto de cliente se guarda en texto
  claro en el archivo de configuración.
- **Las entradas de capacidad pueden repetirse.** Una métrica que devuelve más
  de un punto de datos produce varios módulos con el mismo nombre en el mismo
  documento.
- **El agente File lleva la descripción de Blob.** Ambos agentes informan de
  `Blob Service Metrics`.

### Resolución de problemas

- **La ejecución imprime una traza y termina con estado 1** — falló una llamada
  a Azure. Las causas habituales son un secreto de cliente erróneo o caducado,
  un identificador de inquilino o de cliente equivocado y un identificador de
  recurso que la identidad no puede leer. La traza nombra la llamada que falla.
- **La ejecución se detiene con `NameError`** — falta una clave obligatoria en
  el archivo de configuración: alguna de `tenant_id`, `client_id`, `secret` o
  alguno de los seis interruptores `<servicio>_agent`. Una línea que contenga
  `#` se omite como comentario, así que un secreto con `#` produce este error.
- **La ejecución se detiene con `ValueError`** — un valor de `<servicio>_agent`
  no es un número entero. Use `1` o `0`.
- **La ejecución se detiene con `IndexError`** — una línea contiene el nombre de
  una clave conocida pero no el separador `:`, así que el plugin no encuentra
  ningún valor que leer. Use `clave:valor`.
- **La autenticación falla aunque el secreto parezca correcto** — el valor se
  trunca en los dos puntos porque el analizador solo conserva el segundo
  fragmento de la línea. Un secreto que contenga `:` no se puede usar desde
  este archivo.
- **Un servicio no produce módulos de capacidad** — Azure no devolvió datos para
  esas métricas. Los módulos de tráfico, latencia y disponibilidad aparecen
  igualmente, con el `datalist` vacío.
- **`Could not write file: ...`** — la carpeta `data_dir` no existe o el usuario
  que ejecuta el plugin no puede escribir en ella. El documento se crea con un
  nombre exclusivo `<nombre de agente>.<segundos epoch>.data`; una segunda
  ejecución del mismo servicio dentro del mismo segundo falla con este mensaje.
- **`Tentacle error` en la salida de error con `1` en la salida estándar** — la
  entrega por Tentacle falló, y la ejecución imprime `1` igualmente y termina
  con estado 0. Compruebe que `tentacle_client` está en `PATH` y que la
  dirección y el puerto llegan al servidor de Tentacle. El documento permanece
  en `data_dir` cuando el envío falla.
- **No hay ninguna salida** — todos los interruptores `<servicio>_agent` valen
  `0`.

## Referencia

### Opciones de línea de comandos

```bash
./pandora_azure -c <PATH_TO_CONFIG> [--agent_name <AGENT_NAME>] [-g <GROUP>]
    [--data_dir <PATH>] [--as_agent_plugin <0|1>]
    [--tentacle_address <TARGET_HOST>] [--tentacle_port <PORT>]
    [--prefix_module <PREFIX>]
```

| Opción | ¿Obligatoria? | Valor por defecto | Descripción |
| --- | --- | --- | --- |
| `-c`, `--conf` | Sí | — | Ruta del archivo de configuración. Sin ella la ejecución muestra el resumen de uso y termina con estado 2 |
| `--agent_name` | No | `Azure_Monitor.` | Prefijo de los nombres de agente. El sufijo del servicio se añade sin separador |
| `-g`, `--group` | No | `Azure` | Grupo de Pandora FMS asignado a los agentes creados |
| `--data_dir` | No | `/var/spool/pandora/data_in/` | Carpeta donde se escriben los documentos `agent_data` |
| `--as_agent_plugin` | No | `0` | `1` escribe los documentos en `data_dir` e imprime `1`; cualquier otro valor imprime los módulos en la salida estándar. El servicio Data Lake Storage invierte esta regla; véase [Limitaciones](#limitaciones) |
| `--tentacle_address` | No | — | Dirección del servidor de Tentacle. Cuando se indica, cada documento se entrega con el cliente de Tentacle |
| `--tentacle_port` | No | `41121` | Puerto del servidor de Tentacle, que se pasa al cliente como `-p` |
| `--prefix_module` | No | — | Se acepta y se ignora. No prefija los nombres de módulo |
| `-h`, `--help` | No | — | Muestra el resumen de opciones y termina |

### Claves del archivo de configuración

| Clave | ¿Obligatoria? | Valor por defecto | Descripción |
| --- | --- | --- | --- |
| `tenant_id` | Sí | — | Identificador de inquilino de Microsoft Entra del registro de aplicación |
| `client_id` | Sí | — | Identificador de cliente del registro de aplicación |
| `secret` | Sí | — | Valor del secreto de cliente. Se guarda en texto claro |
| `account_id` | Cuando `account_agent` vale `1` | — | Identificador de recurso de Azure que se consulta para las métricas de cuenta |
| `blobservice_id` | Cuando `blobservice_agent` vale `1` | — | Identificador de recurso de Azure que se consulta para las métricas del servicio Blob |
| `fileservice_id` | Cuando `fileservice_agent` vale `1` | — | Identificador de recurso de Azure que se consulta para las métricas del servicio File |
| `queueservice_id` | Cuando `queueservice_agent` vale `1` | — | Identificador de recurso de Azure que se consulta para las métricas del servicio Queue |
| `tableservice_id` | Cuando `tableservice_agent` vale `1` | — | Identificador de recurso de Azure que se consulta para las métricas del servicio Table |
| `datalakestorage_id` | Cuando `datalakestorage_agent` vale `1` | — | Identificador de recurso de Azure que se consulta para las métricas de Data Lake Storage |
| `account_agent` | Sí | — | `1` recolecta las métricas de cuenta, `0` las omite |
| `blobservice_agent` | Sí | — | `1` recolecta las métricas del servicio Blob, `0` las omite |
| `fileservice_agent` | Sí | — | `1` recolecta las métricas del servicio File, `0` las omite |
| `queueservice_agent` | Sí | — | `1` recolecta las métricas del servicio Queue, `0` las omite |
| `tableservice_agent` | Sí | — | `1` recolecta las métricas del servicio Table, `0` las omite |
| `datalakestorage_agent` | Sí | — | `1` recolecta las métricas de Data Lake Storage, `0` las omite |

Cada valor se recorta, una clave repetida conserva el último valor leído y
cualquier línea que contenga `#` se omite.

### Agentes y módulos

Las consultas de métricas cubren la última hora. Las métricas de capacidad usan
granularidad de sesenta minutos; las de tasa, latencia y disponibilidad usan
cinco minutos. Todas piden la agregación `Average`.

#### Agente de la cuenta

| Módulo | Tipo | Unidad | Métrica |
| --- | --- | --- | --- |
| `UsedCapacity` | `generic_data` | bytes | Almacenamiento usado por la cuenta |
| `Transactions` | `generic_data_string` | — | Peticiones hechas al servicio de almacenamiento o a la operación de la API, correctas y fallidas |
| `Ingress` | `generic_data_string` | — | Datos de entrada, en bytes, desde clientes externos y desde dentro de Azure |
| `Egress` | `generic_data_string` | — | Datos de salida, en bytes, hacia clientes externos y dentro de Azure |
| `SucessServerLatency` | `generic_data_string` | — | Tiempo medio de proceso de una petición correcta, sin la latencia de red |
| `SuccessE2ELatency` | `generic_data_string` | — | Latencia media extremo a extremo de las peticiones correctas, en milisegundos |
| `Availity` | `generic_data_string` | — | Porcentaje de disponibilidad del servicio o de la operación de la API |

#### Agente del servicio Blob

| Módulo | Tipo | Unidad | Métrica |
| --- | --- | --- | --- |
| `BlobCapacity` | `generic_data` | bytes | Capacidad usada por el servicio Blob |
| `BlobCount` | `generic_data` | — | Número de blobs |
| `ContainerCount` | `generic_data` | — | Número de contenedores |
| `IndexCapacity` | `generic_data` | bytes | Capacidad usada por el índice |
| `Transactions_blobs` | `generic_data_string` | — | Peticiones, como en el agente de cuenta |
| `Ingress_blobs` | `generic_data_string` | — | Datos de entrada |
| `Egress_blobs` | `generic_data_string` | — | Datos de salida |
| `SucessServerLatency_blobs` | `generic_data_string` | — | Latencia del servidor |
| `SuccessE2ELatency_blobs` | `generic_data_string` | — | Latencia extremo a extremo |
| `Availity_blobs` | `generic_data_string` | — | Disponibilidad |

#### Agente del servicio Queue

| Módulo | Tipo | Unidad | Métrica |
| --- | --- | --- | --- |
| `QueueCapacity` | `generic_data` | bytes | Capacidad usada por el servicio Queue |
| `QueueCount` | `generic_data` | — | Número de colas |
| `QueueMessageCount` | `generic_data` | — | Número de mensajes |
| `Transactions_queues` | `generic_data_string` | — | Peticiones |
| `Ingress_queues` | `generic_data_string` | — | Datos de entrada |
| `Egress_queues` | `generic_data_string` | — | Datos de salida |
| `SucessServerLatency_queues` | `generic_data_string` | — | Latencia del servidor |
| `SuccessE2ELatency_queues` | `generic_data_string` | — | Latencia extremo a extremo |
| `Availity_queues` | `generic_data_string` | — | Disponibilidad |

#### Agente del servicio File

| Módulo | Tipo | Unidad | Métrica |
| --- | --- | --- | --- |
| `FileCapacity` | `generic_data` | bytes | Capacidad usada por el servicio File |
| `FileCount` | `generic_data` | — | Número de archivos |
| `FileShareCount` | `generic_data` | — | Número de recursos compartidos de archivos |
| `FileShareSnapshotCount` | `generic_data` | — | Número de instantáneas de los recursos compartidos |
| `FileShareSnapshotSize` | `generic_data` | bytes | Tamaño de las instantáneas de los recursos compartidos |
| `FileShareCapacityQuota` | `generic_data` | bytes | Cuota de los recursos compartidos de archivos |
| `Transactions_files` | `generic_data_string` | — | Peticiones |
| `Ingress_files` | `generic_data_string` | — | Datos de entrada |
| `Egress_files` | `generic_data_string` | — | Datos de salida |
| `SucessServerLatency_files` | `generic_data_string` | — | Latencia del servidor |
| `SuccessE2ELatency_files` | `generic_data_string` | — | Latencia extremo a extremo |
| `Availity_files` | `generic_data_string` | — | Disponibilidad |

#### Agente del servicio Table

| Módulo | Tipo | Unidad | Métrica |
| --- | --- | --- | --- |
| `TableCapacity` | `generic_data` | bytes | Capacidad usada por el servicio Table |
| `TableCount` | `generic_data` | — | Número de tablas |
| `TableEntityCount` | `generic_data` | — | Número de entidades |
| `Transactions_tables` | `generic_data_string` | — | Peticiones |
| `Ingress_tables` | `generic_data_string` | — | Datos de entrada |
| `Egress_tables` | `generic_data_string` | — | Datos de salida |
| `SucessServerLatency_tables` | `generic_data_string` | — | Latencia del servidor |
| `SuccessE2ELatency_tables` | `generic_data_string` | — | Latencia extremo a extremo |
| `Availity_tables` | `generic_data_string` | — | Disponibilidad |

#### Agente de Data Lake Storage

| Módulo | Tipo | Unidad | Métrica |
| --- | --- | --- | --- |
| `BlobCapacity` | `generic_data` | bytes | Capacidad usada por el servicio Data Lake Storage |
| `BlobCount` | `generic_data` | — | Número de blobs |
| `ContainerCount` | `generic_data` | — | Número de contenedores |
| `IndexCapacity` | `generic_data` | — | Capacidad usada por el índice. Este módulo no lleva unidad, a diferencia del de Blob |
| `Transactions_datalake` | `generic_data_string` | — | Peticiones |
| `Ingress_datalake` | `generic_data_string` | — | Datos de entrada |
| `Egress_datalake` | `generic_data_string` | — | Datos de salida |
| `SucessServerLatency_datalake` | `generic_data_string` | — | Latencia del servidor |
| `SuccessE2ELatency_datalake` | `generic_data_string` | — | Latencia extremo a extremo |
| `Availity_datalake` | `generic_data_string` | — | Disponibilidad |

### Identidad del addon

| Campo | Valor |
| --- | --- |
| Identificador del Marketplace | `pandorafms.azure_storage` |
| Nombre en el Marketplace | Pandora Azure Storage |
| Versión del addon | `1.0` |
| Última actualización en el Marketplace | 2026-02-25 |
| Paquete del Marketplace | `pandorafms.azure_storage.1.0.pspz2` |
| Licencia | One |
| Disponibilidad | Descarga limitada a usuarios con licencia |
| Tipo en el Marketplace | Miscelaneus |
| Flujo de trabajo | Plugin de servidor o de agente: métricas de Azure Monitor de una cuenta de almacenamiento |
| Ejecutable | `pandora_azure` |

[https://marketplace.pandorafms.com/entries/pandorafms.azure_storage](https://marketplace.pandorafms.com/entries/pandorafms.azure_storage)

<!-- SCREENSHOT NEEDED: Los agentes de cuenta y de servicio de Pandora Azure Storage en la consola de Pandora FMS, con sus listas de módulos y sin identificadores de inquilino, suscripción o cuenta visibles. -->
