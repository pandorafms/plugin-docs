# Plugin de monitorización de Google Drive

*Última actualización del artículo: 2026-10-26.*

## Qué hace

El plugin de monitorización de Google Drive informa de cuánta cuota de
almacenamiento de Google Drive está en uso y, opcionalmente, de cuándo se
modificó por última vez un archivo concreto. En cada ejecución lee la cuota de
almacenamiento de la cuenta de Google que autorizó el plugin, convierte la parte
usada en un porcentaje y entrega un agente de Pandora FMS con ese valor.

El addon es un **plugin de servidor**: lo ejecuta el Plugin Server de Pandora FMS
y cada ejecución construye el documento del agente y lo entrega a Pandora FMS por
Tentacle o en un directorio de datos local. No se instala nada en el lado de
Google y el plugin nunca escribe en Google Drive.

Lo que mide tiene tres consecuencias que conviene conocer antes de configurarlo:

- **Informa de una cuota, no de un inventario de archivos.** Los únicos módulos
  son el porcentaje de cuota en uso y, cuando se indica un archivo, la fecha de su
  última modificación. El plugin no lista el Drive, no informa de tamaños por
  carpeta y no monitoriza cuántos archivos se almacenan.
- **Es de solo lectura.** La autorización que solicita es el ámbito de metadatos
  de Google Drive, `https://www.googleapis.com/auth/drive.metadata.readonly`. El
  plugin lee solo cuota y metadatos: nunca el contenido de los archivos, y no
  borra, mueve ni sube nada.
- **Monitoriza la cuenta que lo autoriza.** La cuota y el archivo indicado
  pertenecen a la cuenta de Google cuya autorización está guardada en el host, de
  modo que una configuración del plugin cubre una cuenta de Google.

La ejecución imprime un único número, `1` o `0`, en la salida estándar. Ese número
es el valor que recibe un módulo de plugin de Pandora FMS; el porcentaje de cuota
y la fecha del archivo van al agente aparte que crea el plugin.

## Preparación

### Compatibilidad

| Alcance | Estado | Evidencia |
|---------|--------|-----------|
| Addon `pandorafms.googledrive`, versión `1.0` | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del addon](#identidad-del-addon) |
| Pandora FMS NG 784 y posteriores | `Soportado` | El Marketplace indica que todas sus integraciones son compatibles con Pandora FMS NG 784 y versiones posteriores. Es una declaración de catálogo que cubre el addon, no un registro de prueba del mismo |
| Acceso HTTPS desde el host que ejecuta el plugin a la API de Google Drive | `Requerido` | Cada ejecución llama a la API de Drive v3 para leer la cuota y los metadatos del archivo |
| Un proyecto de Google Cloud con la API de Google Drive habilitada y un cliente OAuth 2.0 de tipo aplicación de escritorio | `Requerido` | El plugin se autentica con el JSON de secreto de cliente de un cliente OAuth de aplicación de escritorio |
| Una cuenta de Google que pueda autorizar el ámbito solicitado | `Requerido` | La lectura de cuota y la búsqueda del archivo se ejecutan como la cuenta que autoriza |
| Rocky Linux y Fedora 34 | `Compatible conocido` | La guía antigua de este addon registra ambos como los sistemas donde se probó. No se ha revalidado para la versión `1.0` |
| Otras distribuciones Linux | `Sin validar` | No se ha registrado un rango de distribuciones ni una matriz de versiones para este addon |
| `tentacle_client` en `PATH` | `Requerido` cuando `--transfer_mode` no es `local` | La entrega por Tentacle ejecuta ese comando; el plugin no tiene ninguna opción que cambie su nombre |
| Permiso de escritura en `/tmp` | `Requerido` | El XML del agente se prepara en `/tmp` antes de la entrega; `--temporal` no lo cambia |
| Permiso de escritura en `/var/spool/pandora/data_in/` | `Requerido` cuando se usa `--transfer_mode local` | La entrega local mueve el documento a ese directorio; `--data_dir` no lo cambia |
| Una sesión de navegador en el host que realiza la primera autorización | `Requerido` | La autorización abre un servidor web local y un navegador. En un host sin entorno gráfico, complétela en una máquina con navegador y copie `token.json` |

Ninguna declaración de compatibilidad establece una edición de Google Workspace,
un plan de Drive ni una distribución Linux distinta del registro anterior.
Mantenga cada afirmación en el alcance que su fuente demuestra.

### Requisitos de Google Cloud

El plugin necesita un cliente OAuth de tipo **aplicación de escritorio**. Prepárelo
una vez en el proyecto que será propietario de la integración:

1. Abra la [consola de Google Cloud](https://console.cloud.google.com/) y
   seleccione o cree un proyecto.
2. En **APIs y servicios → Biblioteca**, busque **Google Drive API** y habilítela
   para el proyecto.
3. En **APIs y servicios → Pantalla de consentimiento de OAuth**, configure la
   pantalla de consentimiento y añada el ámbito
   `https://www.googleapis.com/auth/drive.metadata.readonly`, que es el único
   ámbito que solicita el plugin.
4. En **APIs y servicios → Credenciales**, elija **Crear credenciales → ID de
   cliente de OAuth**, fije el tipo de aplicación en **Aplicación de escritorio** y
   descargue el archivo JSON. Ese archivo es la entrada de `--creds_json`.

Mientras la pantalla de consentimiento esté en estado **Testing**, solo las
cuentas de Google que añada como usuarios de prueba pueden autorizar el cliente.
Añada la cuenta que quiere monitorizar, o publique la aplicación, antes de la
primera ejecución.

### Requisitos

1. **Una cuenta de Google que monitorizar.** Una configuración del plugin lee la
   cuota de una cuenta. Para monitorizar varias cuentas, ejecute el plugin una vez
   por cuenta con un directorio `token.json` distinto y un `--agent_prefix`
   distinto.
2. **El JSON de secreto de cliente** del cliente OAuth de aplicación de
   escritorio, legible por el usuario que ejecuta el plugin.
3. **Pandora FMS con el Plugin Server habilitado** en el servidor que ejecutará el
   plugin.
4. **Un destino de entrega**: un servidor Tentacle accesible en
   `--tentacle_address` y `--tentacle_port` con `tentacle_client` en `PATH`, o un
   directorio `/var/spool/pandora/data_in/` escribible.
5. **Permiso de escritura en `/tmp`** para el usuario que ejecuta el Plugin
   Server, donde se prepara el XML del agente.
6. **Un nombre de archivo**, solo si desea el módulo de última modificación. El
   archivo debe ser visible para la cuenta autorizada.

Autorice el plugin con la cuenta cuya cuota desea monitorizar: la cuota y el
archivo indicado se leen como esa cuenta.

### Instalar el plugin

Descargue el paquete desde su entrada del Marketplace, cuya descarga está limitada
a usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.googledrive](https://marketplace.pandorafms.com/entries/pandorafms.googledrive)

Copie el ejecutable `pandora_googledrive` al servidor de Pandora FMS y dele permiso
de ejecución. El directorio recomendado para plugins de servidor es:

```text
/usr/share/pandora_server/util/plugin/
```

```bash
sudo chmod 755 /usr/share/pandora_server/util/plugin/pandora_googledrive
```

No se instala nada en Google Drive y la cuenta de Google no necesita ningún agente
ni conector.

## Configuración

El plugin no tiene archivo de configuración. Toma todos sus ajustes de la línea de
comandos, partiendo de valores por defecto internos:

```text
valores por defecto < opciones de línea de comandos
```

Todas las opciones están en [Parámetros de línea de
comandos](#parametros-de-linea-de-comandos). Esta sección explica las decisiones
que cambian lo que el plugin lee y dónde va el resultado.

### Autorizar la cuenta

El plugin se autentica como cliente OAuth y guarda la autorización que obtiene en
un archivo llamado `token.json`, en el **directorio de trabajo actual** del
proceso. Esa ruta relativa condiciona todo el modelo de autorización:

- Cuando `token.json` existe en el directorio de trabajo, el plugin lo carga y no
  lee `--creds_json` ni `--creds_base64`. Las ejecuciones posteriores no necesitan
  ninguna opción de credenciales.
- Cuando `token.json` no existe, el plugin abre el flujo OAuth con el JSON de
  secreto de cliente y escribe `token.json` al terminar. Ejecute el plugin desde
  el directorio donde debe vivir la autorización y conserve ese directorio para
  las ejecuciones programadas.

La primera autorización es interactiva: el plugin levanta un servidor web local en
el puerto indicado por `--port` (`8080` por defecto) y abre un navegador para
completar el inicio de sesión de Google. Consecuencias:

- El host necesita una sesión de navegador. En un servidor sin entorno gráfico,
  autorice en una máquina con navegador, en el directorio que prefiera, y copie el
  `token.json` resultante al directorio de trabajo del plugin en el servidor. El
  archivo contiene la autorización guardada para ese cliente OAuth.
- El puerto `8080` debe estar libre en el host que ejecuta el flujo. Cámbielo con
  `--port` cuando otro servicio ya escuche ahí.
- `token.json` debe seguir siendo legible solo por el usuario que ejecuta el
  plugin. Contiene un token de refresco, que es una credencial.

`--creds_base64` no autentica. El plugin decodifica el valor y lo escribe como
`cred.json`, pero después abre `creds.json` para el flujo OAuth:

- Si `creds.json` no existe en el directorio de trabajo, la ejecución termina con
  la traza de un `FileNotFoundError` y deja `cred.json` en el directorio.
- Si `creds.json` existe, se usa ese archivo y el valor decodificado se descarta
  tras una ejecución correcta.

Ambos desenlaces son el comportamiento actual, no un error de configuración. Use
`--creds_json <PATH_TO_CREDENTIALS_JSON>` para la primera autorización y
`token.json` después.

Cuando `token.json` no existe, debe indicarse exactamente una opción de
credenciales:

| Opciones en la línea de comandos | Resultado |
|----------------------------------|-----------|
| Ni `--creds_json` ni `--creds_base64` | El plugin escribe un mensaje en `--log_file`, imprime `0` y termina con estado `0`. No se genera ningún agente |
| Ambas opciones | El mismo resultado: el plugin imprime `0` y termina con estado `0`, y el log indica que solo puede elegirse una |
| Solo `--creds_json` | El flujo OAuth arranca con ese JSON de secreto de cliente |

### Elegir el archivo monitorizado

`--file_name` selecciona un archivo y es opcional. El plugin busca en el Drive de
la cuenta autorizada una **coincidencia exacta de nombre**, incluida la extensión
y las mayúsculas y minúsculas, y lee la fecha de modificación de la primera
coincidencia que recibe. Puntos a tener en cuenta:

- La búsqueda usa el buscador de archivos de Drive v3 sin opciones de unidades
  compartidas, así que resuelve archivos del Drive propio de la cuenta. Un archivo
  que solo vive en una unidad compartida no se encuentra.
- Un nombre de archivo que contenga una comilla simple no puede consultarse,
  porque el nombre se interpola tal cual en la expresión de búsqueda.
- Cuando el nombre no se resuelve, el plugin imprime
  `Error al obtener la fecha de modificación: ...` en la salida estándar, genera el
  agente **sin** el módulo del archivo y aun así imprime `1`. Por tanto, un módulo
  ausente es el síntoma visible de un nombre incorrecto.
- El nombre del módulo se construye con el texto que se pasó, no con el nombre que
  devuelve Google, así que ambos coinciden normalmente.

Sin `--file_name`, la ejecución hace solo la consulta de cuota.

### Prefijos de agente y módulos

`--agent_prefix` y `--module_prefix` tienen por defecto una cadena vacía y no se
comportan igual:

- **`--agent_prefix`** se antepone una sola vez al alias del agente,
  `<agent_prefix>GoogleDrive`, sin espacio intermedio. Pandora FMS identifica el
  agente por un hash derivado de ese alias, así que el mismo prefijo actualiza
  siempre el mismo agente y un prefijo distinto crea un segundo agente.
- **`--module_prefix`** se aplica dos veces a cada nombre de módulo, porque el
  prefijo se añade al componer el nombre del módulo y otra vez al construir el
  módulo. Sin prefijo, todos los nombres de módulo empiezan por un espacio.

Los nombres resultantes, con `--agent_prefix PROD_ --module_prefix PROD.` y el
archivo `report.csv`:

| Elemento | Nombre |
|----------|--------|
| Alias del agente | `PROD_GoogleDrive` |
| Identificador del agente | Hash derivado de `PROD_GoogleDrive` (lo muestra la consola, no se escribe) |
| Módulo de cuota | `PROD.PROD. Google Drive Used` |
| Módulo del archivo | `PROD.PROD. report.csv` |

Con ambos prefijos vacíos, esos mismos nombres son ` Google Drive Used` y
` report.csv`. Escriba el nombre combinado en alertas, informes y filtros de
módulos, y cuente con la duplicación: es el comportamiento actual, no un efecto de
representación.

### Entrega

La entrega por defecto es Tentacle. `--transfer_mode` acepta un único valor
significativo:

| Valor | Comportamiento |
|-------|----------------|
| `tentacle` (por defecto) | Envía el documento XML con `tentacle_client` a `--tentacle_address`:`--tentacle_port` |
| `local` | Mueve el documento XML a `/var/spool/pandora/data_in/` |
| Cualquier otro valor, incluida una errata | También usa Tentacle; el plugin solo trata el valor exacto `local` como entrega local |

`--tentacle_address` tiene por defecto `127.0.0.1` y `--tentacle_port` `41121`.
Cuatro opciones se aceptan pero no se usan en la entrega: `--temporal`,
`--data_dir`, `--tentacle_client` y `--tentacle_opts`. El documento se prepara
siempre en `/tmp`, la entrega local apunta siempre a
`/var/spool/pandora/data_in/` y el comando de Tentacle es siempre
`tentacle_client` resuelto por `PATH`. Como ninguna de esas rutas es configurable,
el host debe proporcionarlas: el cliente de Tentacle en `PATH`, un `/tmp`
escribible y el directorio de datos del servidor en la ubicación por defecto
cuando se usa la entrega local.

Los fallos de Tentacle se imprimen en la salida de error, pero no cambian el `1` o
el `0` que imprime el plugin. Consulte [Salida y código de
salida](#salida-y-codigo-de-salida).

### Registrar el plugin en la consola

1. Abra **Servidores → Plugins** y pulse **Registrar plugin**.
2. Indique un nombre, el tipo de plugin **Standard**, un tiempo máximo de espera
   opcional y una descripción.
3. En **Comando del plugin**, escriba la ruta completa al ejecutable en el servidor
   de Pandora FMS:
   `/usr/share/pandora_server/util/plugin/pandora_googledrive`.
4. En **Parámetros del plugin**, combine las opciones que necesite usando las
   macros de plugin `_field1_`, `_field2_`, ... como marcadores:

```text
--creds_json _field1_ --agent_prefix _field2_ --interval 300 --transfer_mode tentacle --tentacle_address 127.0.0.1 --tentacle_port 41121
```

5. En **Parámetros de macro**, describa cada campo. El ejemplo usa estos valores:

| Campo | Descripción | Valor de ejemplo |
|-------|-------------|------------------|
| `_field1_` | Ruta al JSON de secreto de cliente del cliente OAuth de aplicación de escritorio, legible por el usuario del Plugin Server | `<PATH_TO_CREDENTIALS_JSON>` |
| `_field2_` | Prefijo del alias del agente generado | `PROD_` |

<!-- SCREENSHOT NEEDED: Formulario de registro de plugin de servidor en la consola de Pandora FMS con la ruta del comando pandora_googledrive y los campos de parámetros, con marcadores de laboratorio y sin datos de cuenta reales. -->

Añada `--file_name _field3_` y `--module_prefix _field4_` solo cuando los
necesite. Cada opción que permanezca en la cadena de parámetros debe recibir un
valor: una macro vacía deja la opción sin argumento y el plugin se detiene con un
error de análisis de argumentos en lugar de ejecutarse. Elimine la opción en vez
de dejar su campo vacío.

La opción de credenciales solo es necesaria mientras falte `token.json` en el
directorio de trabajo del Plugin Server. Una vez existe la autorización, la cadena
de parámetros puede prescindir de `--creds_json`.

Después de crear el plugin de servidor, abra un agente, cree un módulo de tipo
**plugin** y seleccione el plugin registrado. Ese módulo recibe el `1` o el `0`
impreso. El porcentaje de cuota y la fecha del archivo no van a ese módulo: llegan
al agente aparte que crea el plugin.

<!-- SCREENSHOT NEEDED: Formulario de módulo de plugin en la consola de Pandora FMS con el plugin de Google Drive seleccionado y sus campos de macro rellenos, sin credenciales, nombres de cuenta ni nombres de host reales. -->

### Seguridad

- **La autorización es el secreto.** `token.json` contiene un token de refresco que
  concede acceso de solo lectura a los metadatos de la cuenta autorizada.
  Restríjalo al usuario del plugin (`chmod 600`) y no lo copie a tickets, imágenes
  ni repositorios.
- **El JSON de secreto de cliente también es un secreto.** Identifica el cliente
  OAuth del proyecto. Manténgalo legible solo por el usuario del plugin y fuera de
  cualquier directorio servido por un servidor web.
- **Ambos archivos son texto plano.** Su protección es el modelo de permisos del
  sistema de archivos, así que manténgalos propiedad del usuario del plugin.
- **El ámbito es de solo lectura y mínimo para este propósito.** El plugin solicita
  `drive.metadata.readonly`, que permite leer metadatos pero no el contenido de los
  archivos. No puede modificar el Drive.
- **No pase una credencial en base64 por la línea de comandos.** El valor es el
  propio secreto de cliente: aparecería en el historial del shell, en la lista de
  procesos del sistema operativo y en los parámetros del plugin que guarda la
  consola. Además, esa opción no completa la autorización, como se describió
  antes.
- **La primera autorización abre un navegador en el host.** Complétela en una
  máquina de confianza y copie `token.json`, en lugar de exponer una sesión
  interactiva en un servidor de producción.
- **Una autorización o una lectura de cuota fallida imprime una traza.** Esos
  mensajes pueden incluir el texto de error de la API de Google. Revíselos antes de
  compartir una ejecución manual.

## Verificación

Ejecute el plugin manualmente desde el directorio que contiene `token.json` en el
servidor de Pandora FMS:

```bash
./pandora_googledrive \
  --file_name report.csv \
  --agent_prefix PROD_ \
  --transfer_mode tentacle \
  --tentacle_address <PANDORA_FMS_SERVER> \
  --tentacle_port 41121
```

Una ejecución correcta termina con `1` en la salida estándar. El plugin crea o
actualiza entonces el agente `PROD_GoogleDrive`, cuyo módulo de cuota informa del
porcentaje actual y cuyo segundo módulo informa de la fecha del archivo. Con
entrega `local`, compruebe que un archivo `.data` se ha movido a
`/var/spool/pandora/data_in/` y que el agente aparece después de que el servidor de
datos lo procese.

El valor impreso por sí solo no basta para verificar la integración:

- `1` significa que la consulta de cuota funcionó y que el documento del agente se
  construyó. No demuestra la entrega: un fallo de Tentacle se imprime en la salida
  de error pero deja `1` en la salida estándar.
- `0` significa que no se construyó ningún agente. La causa habitual es que falte
  `token.json` y no se indique ninguna opción de credenciales, o que se indiquen
  las dos.
- Una traza con estado de proceso `1` significa que falló la autorización o la
  lectura de cuota. En ese caso no se imprime el valor `1`/`0`.

Verifique los datos, no solo la línea de salida:

1. Confirme que el agente existe con el alias `<agent_prefix>GoogleDrive`.
2. Abra sus módulos y compruebe que el porcentaje de cuota es plausible para la
   cuenta y que el módulo del archivo muestra una fecha ISO 8601.
3. Si falta el módulo del archivo mientras el módulo de cuota informa de un valor,
   el nombre no se resolvió. Revise el nombre y la limitación de unidades
   compartidas descrita antes.

<!-- SCREENSHOT NEEDED: El agente GoogleDrive generado en la consola de Pandora FMS con sus módulos de cuota y fecha de archivo y sus valores actuales para una cuenta de laboratorio. -->

Use `./pandora_googledrive -h` para imprimir el resumen de uso al estilo de
Pandora FMS. La cabecera indica `Version = 1.0` y el resumen muestra la forma de
ejecución manual. Esa forma es una plantilla esquemática: nunca indica cuál de las
dos opciones de credenciales usar, y `--creds_json/creds_base64` no es un nombre de
opción válido. Indique una de las dos opciones, como se mostró antes.

## Entender los resultados

### Agente

El plugin genera un único agente. Su identidad se deriva de `--agent_prefix`, de
modo que un prefijo corresponde a un agente:

| Atributo | Valor |
|----------|-------|
| Alias | `<agent_prefix>GoogleDrive`, sin espacio antes de `GoogleDrive` |
| Identificador | Hash derivado del alias |
| Descripción | Vacía |
| Intervalo | `--interval`, `300` segundos por defecto |
| Grupo | `--group`, vacío por defecto |
| Campos de sistema operativo | Vacíos |
| Agente padre | Ninguno |

Ejecutar el plugin dos veces con el mismo prefijo actualiza el mismo agente. Cambiar
el prefijo crea un segundo agente con su propio conjunto de módulos, que es la
forma de monitorizar dos cuentas de Google desde la misma instalación de Pandora
FMS.

### Módulos

El plugin genera siempre el módulo de cuota y el módulo del archivo solo cuando
`--file_name` está definido y el nombre se resuelve:

| Nombre del módulo | Tipo | Unidad | Valor |
|-------------------|------|--------|-------|
| `<module_prefix><module_prefix> Google Drive Used` | `generic_data` | `%` | Porcentaje de la cuota de almacenamiento en uso, sin redondear |
| `<module_prefix><module_prefix> <file_name>` | `generic_data_string` | Ninguna | Fecha de modificación que devuelve Google para el archivo, como cadena ISO 8601 en UTC, por ejemplo `2026-10-24T08:15:00.123Z` |

La descripción del módulo de cuota es `Percentage of space used` y la del módulo
del archivo es `Last change`.

El porcentaje se calcula como el almacenamiento usado dividido por el límite de
almacenamiento, multiplicado por 100. Google informa de ambas cifras para la cuenta
completa, así que el valor describe el uso de almacenamiento de la cuenta frente a
su cuota, no el tamaño de una carpeta ni el espacio ocupado solo por archivos de
Drive.

El módulo del archivo publica la cadena de fecha de Google. Pandora FMS la guarda
como valor de texto: no se convierte en una marca temporal de Pandora FMS, así que
un umbral sobre ese módulo compara cadenas. Para detectar cambios, compare valores
consecutivos o use el histórico del módulo en lugar de un umbral numérico.

## Operación y resolución de problemas

El plugin no guarda estado entre ejecuciones salvo `token.json`. Cada ejecución lee
la cuota de nuevo, así que puede ejecutarse manualmente en cualquier momento sin
afectar a la cuenta de Google.

Programe el módulo de plugin registrado con el intervalo al que quiera refrescar los
datos. El agente generado lleva su propio `--interval`, que es el intervalo que
Pandora FMS asigna al agente, pero sus valores cambian solo cuando se ejecuta el
módulo del plugin. Alinee ambos.

### Salida y código de salida

| Resultado | Significado |
|-----------|-------------|
| Salida estándar `1` | Se leyó la cuota y se construyó el documento del agente. La entrega no está garantizada |
| Salida estándar `0` | No se construyó ningún agente: faltaba `token.json` y las opciones de credenciales no estaban o estaban ambas. Estado del proceso `0` |
| Traza con estado de proceso `1` | La autorización o la lectura de cuota produjo un error. No se imprime el valor `1`/`0` y `--log_file` no recibe nada de ese fallo |
| Error de análisis de argumentos en la salida de error, estado de proceso `2` | Una opción se quedó sin valor, por ejemplo un campo de macro vacío |
| `Error al obtener la fecha de modificación: ...` seguido de `1` | El archivo indicado no se resolvió. El agente se entrega sin el módulo del archivo |

### Problemas habituales

- **La ejecución imprime `0`.** No hay `token.json` en el directorio de trabajo y
  las opciones de credenciales faltan o se contradicen. Autorice la cuenta, o
  ejecute el plugin desde el directorio que contiene `token.json`.
- **El flujo OAuth se repite en cada ejecución.** El `token.json` que escribió la
  primera autorización no está en el directorio de trabajo de la ejecución actual.
  Recuerde que el archivo se resuelve respecto al directorio de trabajo del
  proceso, no respecto al ejecutable. Dirija la ejecución al directorio correcto o
  mueva el archivo.
- **La ejecución termina con la traza de un `FileNotFoundError` en la etapa de
  autorización.** Se usó `--creds_base64` sin un `creds.json` en el directorio de
  trabajo. Use `--creds_json` para la primera autorización.
- **La ejecución termina con la traza de un `TypeError` después de la
  autorización.** Falló la lectura de cuota, por ejemplo porque la respuesta de
  cuota no incluye un límite o informa de un límite cero. En ese caso el plugin no
  puede publicar un porcentaje y el fallo se informa solo con esa traza.
- **No se abre ningún navegador o el flujo espera indefinidamente.** El host no
  tiene sesión de navegador o el puerto `8080` está ocupado. Autorice en una máquina
  con navegador y copie `token.json`, o cambie el puerto con `--port`.
- **Google rechaza la autorización.** La pantalla de consentimiento está en estado
  **Testing** y la cuenta no es un usuario de prueba, o el ámbito no se añadió a la
  pantalla de consentimiento. Corríjalo en el proyecto de Google Cloud y autorice
  de nuevo.
- **La ejecución imprime `1` pero no aparece ningún agente.** Se leyó la cuota pero
  falló la entrega. Compruebe que `tentacle_client` existe en `PATH` y alcanza
  `--tentacle_address`:`--tentacle_port`. El plugin no tiene ninguna opción para
  cambiar el nombre del cliente. Con entrega local, compruebe que
  `/var/spool/pandora/data_in/` existe y es escribible.
- **El módulo del archivo nunca aparece.** El nombre no se resolvió: revise
  mayúsculas y minúsculas, extensión, una comilla simple en el nombre o un archivo
  que solo vive en una unidad compartida. El módulo de cuota sigue informando.
- **Los nombres de módulo parecen incorrectos.** El prefijo aparece dos veces y el
  nombre empieza por un espacio cuando no se usa prefijo. Así compone los nombres
  esta versión; use el nombre exacto en alertas y filtros.
- **`--transfer_mode local` no entrega en otra carpeta.** El destino es fijo. Use
  la entrega por Tentacle cuando el servidor de Pandora FMS use otro directorio de
  datos.
- **Falta el archivo de log o tiene un nombre inesperado.** `--log_file` tiene por
  defecto `/tmp/exchangemail_logfile.txt`, una ruta heredada de otro addon.
  Defínalo explícitamente y tenga en cuenta que el log solo registra el aviso de
  autenticación y una línea de éxito que dice `getting mail data` aunque este
  plugin lea metadatos de Drive.

## Referencia

### Parámetros de línea de comandos

```text
./pandora_googledrive [--creds_json <ruta> | --creds_base64 <valor>] [--port <puerto>] [--file_name <nombre>] [--module_prefix <prefijo>] [--agent_prefix <prefijo>] [--group <grupo>] [--interval <segundos>] [--temporal <directorio>] [--data_dir <directorio>] [--transfer_mode <modo>] [--tentacle_client <ruta>] [--tentacle_opts <opciones>] [--tentacle_port <puerto>] [--tentacle_address <dirección>] [--log_file <ruta>]
```

| Nombre | Obligatorio | Por defecto | Descripción |
|--------|-------------|-------------|-------------|
| `-h`, `--help` | No | — | Imprime el resumen de uso, con `Version = 1.0`, y termina |
| `--creds_json` | Solo cuando falta `token.json` | — | Ruta al JSON de secreto de cliente del cliente OAuth de aplicación de escritorio. Inicia la autorización interactiva cuando no existe `token.json` |
| `--creds_base64` | No | — | Base64 del JSON de secreto de cliente. El contenido decodificado se escribe como `cred.json`, pero el flujo OAuth abre `creds.json`, así que esta opción no completa la autorización por sí sola |
| `--port` | No | `8080` | Puerto local del servidor de retorno OAuth usado durante la primera autorización |
| `--file_name` | No | Vacío | Nombre exacto del archivo cuya última fecha de modificación se publica. El módulo se omite cuando el nombre no se resuelve |
| `--module_prefix` | No | Vacío | Prefijo de los nombres de módulo. Se aplica dos veces a cada nombre de módulo |
| `--agent_prefix` | No | Vacío | Prefijo del alias del agente; el identificador del agente se deriva del alias |
| `--group` | No | Vacío | Grupo que se escribe en el agente generado. El valor no se valida antes de la entrega; el texto de ayuda menciona `exchange` como valor por defecto, pero el valor efectivo es vacío |
| `--interval` | No | `300` | Intervalo, en segundos, asignado al agente generado |
| `--temporal` | No | `/tmp` | Se acepta y no se usa: el XML del agente se prepara siempre en `/tmp` |
| `--data_dir` | No | `/var/spool/pandora/data_in/` | Se acepta y no se usa: la entrega local apunta siempre a `/var/spool/pandora/data_in/` |
| `--transfer_mode` | No | `tentacle` | `local` mueve el XML al directorio de datos. Cualquier otro valor, incluido el de por defecto, usa Tentacle |
| `--tentacle_client` | No | `tentacle_client` | Se acepta y no se usa: el comando de Tentacle es siempre `tentacle_client`, resuelto por `PATH` |
| `--tentacle_opts` | No | Vacío | Se acepta y no se usa: no se pasa ninguna opción adicional al cliente de Tentacle |
| `--tentacle_port` | No | `41121` | Puerto del servidor Tentacle para la entrega por Tentacle |
| `--tentacle_address` | No | `127.0.0.1` | Dirección del servidor Tentacle para la entrega por Tentacle |
| `--log_file` | No | `/tmp/exchangemail_logfile.txt` | Archivo de log para el aviso de autenticación y la línea de éxito |

### Entrega

| Ajuste | Valor |
|--------|-------|
| Entrega por defecto | Tentacle |
| Comando del cliente de Tentacle | `tentacle_client`, resuelto por `PATH`; no configurable |
| Dirección y puerto de Tentacle | `--tentacle_address` y `--tentacle_port` |
| Selector de entrega local | `--transfer_mode local` (valor exacto) |
| Destino local | `/var/spool/pandora/data_in/`; no configurable |
| Opciones adicionales de Tentacle | Ninguna; `--tentacle_opts` no se reenvía |
| Directorio de preparación del XML | `/tmp`; no configurable |

### Superficie de la API de Google

| Llamada | Campos leídos | Propósito |
|---------|---------------|-----------|
| `about().get` | `storageQuota` | Límite total y uso actual de la cuota de la cuenta |
| `files().list` | `id`, `name` | Resuelve `--file_name` por nombre exacto, primera coincidencia |
| `files().get` | `modifiedTime` | Fecha de modificación del archivo resuelto |
| Ámbito OAuth | `https://www.googleapis.com/auth/drive.metadata.readonly` | Acceso de solo lectura a metadatos para las tres llamadas anteriores |

El plugin no hace ninguna otra llamada a la API de Google: no enumera el Drive, no
lee el contenido de los archivos y no cambia nada.

### Agente generado

| Atributo | Valor |
|----------|-------|
| Cardinalidad | Un único agente. Su identidad se deriva de `--agent_prefix`, de modo que un prefijo corresponde a un agente |
| Alias | `<agent_prefix>GoogleDrive` |
| Identificador | Hash derivado del alias |
| Descripción | Vacía |
| Intervalo | `--interval` (`300` segundos por defecto) |
| Grupo | `--group` (vacío por defecto) |
| Campos de sistema operativo | Vacíos |
| Módulos | Siempre el módulo de cuota; el módulo del archivo cuando el nombre se resuelve |

### Módulos generados

| Nombre del módulo | Tipo | Unidad | Descripción |
|-------------------|------|--------|-------------|
| `<module_prefix><module_prefix> Google Drive Used` | `generic_data` | `%` | `Percentage of space used` |
| `<module_prefix><module_prefix> <file_name>` | `generic_data_string` | Ninguna | `Last change` |

### Identidad del addon

| Campo | Valor |
|-------|-------|
| Identificador del Marketplace | `pandorafms.googledrive` |
| Nombre en el Marketplace | Google Drive |
| Versión | `1.0` — la versión actual del Marketplace, que también imprime `-h` |
| Última actualización en el Marketplace | 2025-06-25 |
| Licencia | One — la descarga está limitada a usuarios con licencia |
| Tipo en el Marketplace | Miscelaneus |
| Categoría y etiqueta del Marketplace | Miscelaneus; `cloud` |
| Descargas | 5 |
| Flujo de trabajo | Plugin de monitorización, modo plugin de servidor |
| Ejecutable | `pandora_googledrive` |
