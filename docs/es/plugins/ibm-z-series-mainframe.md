# IBM Z Series Mainframe

*Última actualización del artículo: 2026-10-26.*

## Qué hace

Pandora FMS Mainframe monitoriza mainframes IBM Z con z/OS a través del Portal
de Datos RMF Monitor III. El addon tiene dos partes que se instalan y se
configuran por separado:

- **El servidor Mainframe** (`mf_server`), un servicio instalado en un host
  Linux. Lee el Portal de Datos RMF por HTTP con autenticación básica,
  convierte la respuesta en módulos de Pandora FMS y entrega un documento de
  agente por cada mainframe. No se instala nada en el mainframe y no se ejecuta
  ningún agente en él.
- **La extensión de consola Z/OS**, que añade **Operation → Z/OS** a la consola
  de Pandora FMS: un navegador del árbol de recursos del portal que genera la
  definición del módulo que se elija, una lista de los agentes mainframe y una
  vista del estado de los módulos.

No es un plugin de agente ni un plugin de servidor registrado por módulo. El
servicio es un componente con licencia, con su propio directorio de
configuración, su propia clave de licencia, su propia planificación y su propia
ruta de entrega, y una sola instancia recoge datos de todos los mainframes que
se definan en su directorio de configuración.

El addon se distribuye a través del Marketplace de Pandora FMS como
`pandorafms.mainframe`. Su descarga está limitada a usuarios con licencia.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Addon `pandorafms.mainframe`, versión `2.0` | Objetivo documentado | Versión del Marketplace que describe esta página. Consulte [Identidad del addon](#identidad-del-addon) |
| Pandora FMS NG 784 y posteriores | `Soportado` | El Marketplace declara que todas sus integraciones son compatibles con Pandora FMS NG 784 y versiones posteriores. Es una declaración publicada para el catálogo, no un registro de prueba de este addon |
| Una consola de Pandora FMS con el directorio de extensiones Enterprise | `Requerido` | La extensión de consola se instala en `enterprise/extensions` y registra su opción de menú a través de la interfaz de extensiones Enterprise |
| Una clave de licencia de Pandora FMS | `Requerido` | El servicio registra un error de licencia no válida y se detiene cuando `pandora_license` no contiene una clave válida |
| Un sistema operativo llamado `Mainframe` en la consola | `Requerido` | Los agentes se publican con `os_name` `Mainframe` y las dos vistas de consola seleccionan los agentes por ese nombre de sistema operativo |
| El Portal de Datos RMF Monitor III, accesible por HTTP con autenticación básica | `Requerido` | Todos los módulos dataportal leen `gpm/perform.xml` del portal |
| Acceso de red desde el host del servicio al portal y al puerto Tentacle de Pandora FMS | `Requerido` | El servicio recoge por HTTP y entrega con el cliente Tentacle |
| Un host Linux con systemd | `Requerido` | El instalador escribe una unidad systemd y la habilita |
| RHEL, CentOS, Rocky Linux y AlmaLinux 8, 9 y 10, y Ubuntu 22.04 | `Sin validar` | El instalador reconoce estas versiones y en cualquier otra distribución imprime `WARNING: Not supported OS found`. No existe registro de prueba |
| Versiones de z/OS | `Sin validar` | La guía antigua afirma que el addon se probó en z/OS 1.10 y 1.13; ningún registro de prueba lo respalda |
| Versiones del Portal de Datos RMF | `Sin validar` | No hay matriz de versiones registrada para este addon |

### Requisitos

1. **Un mainframe IBM Z** con RMF Monitor III activo y el Portal de Datos RMF
   sirviendo los informes que se quieran recoger. El portal debe aceptar
   autenticación básica por HTTP y responder a los recursos `gpm` descritos en
   [Peticiones al portal](#peticiones-al-portal).
2. **Un host Linux con systemd** para el servicio. Puede ser el host del
   servidor de Pandora FMS o cualquier otro host que alcance tanto el portal
   como el servidor Tentacle.
3. **Una consola de Pandora FMS** con el directorio de extensiones Enterprise,
   para instalar la extensión Z/OS y recibir los datos de los agentes.
4. **Una clave de licencia de Pandora FMS**, configurada en el servicio.
5. **Acceso de red**: HTTP al portal y el puerto Tentacle (`41121` por defecto)
   al servidor de Pandora FMS, en ambos sentidos cuando se use configuración
   remota.

### Instalar el servidor Mainframe

Descomprima el paquete y ejecute el instalador como `root` desde el directorio
que crea:

```bash
tar zxf pandorafms_mf_server-<version>.tar.gz
cd mf_server
sudo ./mf_server_installer --install
```

El instalador:

- copia el ejecutable `mf_server` y el cliente Tentacle a `/usr/bin`;
- copia `mf_server.conf` y `mf_server.env` a `/etc/pandora`;
- crea el directorio de configuración de agentes `/etc/pandora/conf`;
- escribe `/etc/systemd/system/mf_server.service`, recarga la configuración de
  systemd y habilita la unidad.

**No** arranca el servicio y no modifica la consola. Edite primero
`/etc/pandora/mf_server.conf` ([Configuración](#configuracion)) y arránquelo
después:

```bash
sudo systemctl start mf_server
```

La unidad ejecuta el servicio como `root`, lo reinicia si se detiene y espera
que se separe en segundo plano, así que `daemon 1` es obligatorio.

### Instalar la extensión de consola Z/OS

El paquete incluye la extensión de consola en el directorio `extensions`.
Cópiela en el directorio de extensiones Enterprise de la consola:

```bash
sudo cp -r ./extensions/* <PANDORA_CONSOLE>/enterprise/extensions/
```

`<PANDORA_CONSOLE>` es el directorio de instalación de la consola. Tras la
copia, **Operation → Z/OS** aparece en el menú de la consola; las vistas que abre
requieren el privilegio de lectura de agentes (`AR`).

<!-- SCREENSHOT NEEDED: Menú Operation de la consola de Pandora FMS con la entrada Z/OS resaltada. -->

La extensión no la instala el instalador del servicio y su desinstalador no la
elimina: es una copia de archivos de consola que se gestiona aparte.

### Crear el sistema operativo Mainframe

El servicio publica todos los agentes con el sistema operativo `Mainframe`. Si
la consola no tiene ese sistema operativo, créelo en
**Administration → Setup → OS** antes de arrancar el servicio; las vistas Z/OS
seleccionan los agentes por ese nombre, así que un sistema operativo ausente
las deja vacías aunque los agentes existan.

## Configuración

La configuración se reparte entre el servicio y la consola:

- `/etc/pandora/mf_server.conf` contiene los ajustes comunes a todos los
  mainframes.
- `/etc/pandora/conf/*.conf` contiene un archivo por mainframe: el agente, sus
  credenciales del portal y sus bloques de módulos.
- La consola contiene lo que Pandora FMS hace con los módulos: los umbrales
  definidos en un bloque de módulo y la configuración remota de cada agente.

### Archivo de configuración del servicio

`/etc/pandora/mf_server.conf` usa un par `token valor` por línea. Las líneas que
empiezan por `#` son comentarios, los espacios sobrantes se recortan, un token
desconocido se almacena sin aviso y la última aparición de un token repetido
prevalece. Las rutas deben ser absolutas: el servicio cambia a `/tmp` cuando se
separa en segundo plano.

Este extracto contiene lo que normalmente hay que ajustar:

```ini
# Clave de licencia de Pandora FMS: el servicio no arranca sin ella.
pandora_license <PANDORA_LICENSE_KEY>

# Dirección Tentacle del servidor de Pandora FMS, usada para entregar los agentes.
server_ip <PANDORA_FMS_SERVER>

# Grupo de consola de todos los agentes mainframe (debe existir en la consola).
group Servers

# Directorio que se recorre en busca de un archivo de configuración por mainframe.
agent_conf_dir /etc/pandora/conf
```

Todos los tokens, su valor por defecto interno y el valor que trae el archivo
distribuido están en
[Tokens de configuración del servicio](#tokens-de-configuracion-del-servicio).
Reinicie el servicio después de editar el archivo; el servicio no lo vigila.

### Registrar un agente mainframe

Cree un archivo por mainframe en `/etc/pandora/conf`. El paquete incluye
`agent.conf.sample` como punto de partida:

```bash
sudo cp agent.conf.sample /etc/pandora/conf/<MAINFRAME_AGENT_NAME>.conf
sudo chmod 600 /etc/pandora/conf/<MAINFRAME_AGENT_NAME>.conf
```

```ini
agent_name <MAINFRAME_AGENT_NAME>
dataportal_url http://<RMF_DATA_PORTAL_HOST>:8803
dataportal_user <USERNAME>
dataportal_pass <PASSWORD>

module_begin
module_plugin dataportal
module_resource <RESOURCE>
module_metric <METRIC_ID>
module_end
```

Puntos clave:

- El archivo debe terminar en `.conf`. Al arrancar, el servicio lo renombra a
  `<md5 del nombre del agente>.conf`, que es también el nombre que usa la
  configuración remota. Ese nombre md5 es el archivo que se sigue editando
  después.
- `agent_name`, `dataportal_url`, `dataportal_user` y `dataportal_pass` son
  obligatorios en todos los archivos, incluidos los que solo definen módulos de
  almacenamiento.
- El servicio lee el directorio solo al arrancar. Un archivo nuevo, un módulo
  nuevo o un archivo editado requieren `sudo systemctl restart mf_server`; solo
  los cambios hechos por la configuración remota de la consola se aplican con el
  servicio en marcha.
- El intervalo del agente no es por agente: todos toman `agent_interval` de la
  configuración del servicio.

### Definiciones de módulo

Un bloque de módulo empieza por `module_begin`, termina en `module_end` y
contiene líneas `module_<token> valor`. Un bloque sin `module_plugin` se acepta
y nunca se ejecuta, así que es lo primero que hay que revisar cuando un módulo
no produce datos. El navegador de la consola escribe el bloque por usted
([Crear un módulo con el navegador del Portal de Datos
RMF](#crear-un-modulo-con-el-navegador-del-portal-de-datos-rmf)); la lista
completa de tokens está en
[Tokens de definición de módulo](#tokens-de-definicion-de-modulo).

Solo unos pocos tokens afectan a lo que recibe Pandora FMS: el selector de
plugin, el recurso y la métrica (o la URL del conjunto de datos y su longitud de
registro), el intervalo de recogida y los cuatro umbrales con sus dos
indicadores de inversión. `module_type`, `module_unit`, `module_description`,
`module_group` y el resto de tokens `module_*` se leen pero no llegan a los
módulos publicados; configure esos valores en la consola.

### Crear un módulo con el navegador del Portal de Datos RMF

El navegador recorre el árbol de recursos del portal y devuelve un bloque listo
para pegar correspondiente a la métrica que se elija.

1. Abra **Operation → Z/OS** y la pestaña **RMF Data Portal Browser**.
2. Rellene la dirección del portal, el usuario, la contraseña y la profundidad,
   y pulse **Browse**. Una dirección sin puerto recibe `:8803`.
3. El árbol empieza en la raíz del portal: el primer nivel es un sysplex, el
   segundo las imágenes MVS y después los subsistemas de E/S y los procesadores.
4. Pulse el icono del ojo de un recurso para listar sus métricas.
5. Pulse una métrica para abrir un diálogo con su bloque de módulo:

    ```text
    module_begin
    module_plugin dataportal
    module_description <DESCRIPTION FROM THE PORTAL>
    module_type generic_data
    module_resource <RESOURCE>
    module_metric <METRIC_ID>
    module_end
    ```

6. Copie el bloque en la configuración del agente: el archivo del agente en
   disco y un reinicio, o la configuración remota del agente en la consola
   (**Operation → Z/OS → Mainframes**, icono de edición), que el servicio en
   marcha aplica por sí mismo.

<!-- SCREENSHOT NEEDED: Pestaña RMF Data Portal Browser con los campos de dirección, usuario, contraseña enmascarada, profundidad y el botón Browse. -->

<!-- SCREENSHOT NEEDED: Lista de métricas de un recurso con el diálogo del bloque de módulo abierto. -->

El navegador no guarda las credenciales del portal: se escriben de nuevo en cada
visita y viajan del navegador a la consola en cada petición.

### Módulos de almacenamiento

El plugin `storage` lee un conjunto de datos por FTP(S) en lugar del portal
HTTP, lo convierte desde EBCDIC y publica cuatro módulos por cada grupo de
almacenamiento que encuentra. El conjunto de datos se obtiene de `module_url`;
el portal RMF no interviene en esa petición:

```text
module_begin
module_plugin storage
module_url ftp://<FTP_HOST>/<DATASET>
module_lrecl 80
module_end
```

Cada registro del conjunto de datos debe contener, en este orden, `P=` seguido
del grupo de almacenamiento, `Es=` seguido de la capacidad, `Libre=` seguido del
porcentaje libre y `T=` seguido de la descripción. `module_lrecl` es la longitud
de registro y vale `80` por defecto.

El plugin `storage_sms` lee un conjunto de datos con los totales SMS y publica
nueve módulos fijos. Cada total debe aparecer como `Gb.` seguido de la
etiqueta —`Usado SMS`, `Reservado SMS`, `Usado No SMS` o `Reservado No SMS`—,
uno o más caracteres no numéricos y el valor numérico:

```text
module_begin
module_plugin storage_sms
module_url ftp://<FTP_HOST>/<DATASET>
module_lrecl 80
module_end
```

Las etiquetas son literales: un conjunto de datos en otro idioma no produce
ninguna coincidencia y los nueve módulos se publican entonces con `0`.

### Entrega a Pandora FMS

El servicio entrega cada documento con el cliente Tentacle o lo copia a un
directorio de datos local:

| `transfer_mode` | Qué hace el servicio | Ajustes que importan |
| --- | --- | --- |
| `tentacle` (por defecto) | Ejecuta `tentacle_client` contra `server_ip:server_port` | `tentacle_client`, `server_ip`, `server_port`, `server_opts` opcional |
| `local` | Copia el documento a `server_path` | `server_path`, que debe ser escribible |

Cualquier otro valor no está soportado y el documento no se entrega. Con
`xml_buffer 1` un documento que no se pudo entregar permanece en `temporal` y se
reintenta en cada pasada, hasta que el espacio libre de ese directorio baja de
`temporal_min_size` bytes.

### Licencia

El servicio requiere una clave de licencia de Pandora FMS en `pandora_license`:

- Sin clave, o con una clave que no valida, el log registra `Invalid license` y
  el servicio termina.
- El límite de la clave se aplica al número de agentes de `agent_conf_dir` o al
  número de bloques de módulo, según el modo de la licencia. Por encima del
  límite el servicio termina; una licencia de cliente caducada solo registra un
  aviso, mientras que una licencia de prueba caducada lo detiene.
- El servicio informa del titular al arrancar (`Licensed to: ...`) y registra
  siempre `Remote configuration enabled.`, diga lo que diga `remote_config`.

### Credenciales y transporte

- La contraseña del portal se guarda en texto claro en el archivo del agente.
  Mantenga el archivo legible solo por `root` (`chmod 600`), junto con la clave
  de licencia de `mf_server.conf`.
- Las credenciales del portal viajan en la cabecera `Authorization` de cada
  petición HTTP. Con un portal `http://` no van cifradas, así que mantenga el
  portal en una red de confianza o publíquelo con TLS y use un
  `dataportal_url` `https://`.
- El navegador de la consola desactiva la verificación del certificado TLS. No
  exponga la consola por HTTP simple ni a redes no confiables, porque el usuario
  y la contraseña del portal pasan por ella en cada navegación.
- Use un usuario de portal dedicado con acceso de solo lectura. Ninguna fuente
  oficial identifica un rol más restrictivo para el Portal de Datos RMF, y el
  addon no realiza ninguna operación de escritura contra él.

## Verificación

1. **El servicio está en marcha.** `systemctl status mf_server` informa la
   unidad como activa. Si no lo está, lea el log: la unidad reinicia el
   servicio, así que un fallo se repite cada pocos segundos.
2. **El log muestra un arranque completo.** `/var/log/mf_server.log` se
   reescribe en cada arranque. Un arranque correcto contiene estos mensajes en
   orden:

    - `Configuration file loaded.`
    - `Reading agent configuration directory.`
    - un `Loading file <name>.conf.` por cada archivo de agente
    - `Valid enterprise license found.` y `Licensed to: <holder>`
    - `modules: <n> Threads: <t> modules per thread: <m>`
    - un `Launched thread <id>.` por cada hilo
    - `Waiting for data...`

    Sin ningún archivo de agente el recuento de módulos es `0`: el servicio
    funciona y no entrega datos de agente.

3. **El mainframe aparece en la consola.** **Operation → Z/OS → Mainframes**
   lista una fila por agente, con el icono del sistema operativo `Mainframe` y
   un último contacto reciente. El agente aparece también en la lista normal de
   agentes.

    <!-- SCREENSHOT NEEDED: Pestaña Mainframes de la extensión Z/OS con un agente de demostración y sin datos reales de ningún host. -->

4. **Los módulos llevan datos.** **Operation → Z/OS → Metrics** muestra los
   módulos de todos los agentes mainframe con su estado, dato y marca de tiempo.
   El filtro **Monitor status** empieza en **Not init**, así que póngalo en
   **All** para ver los módulos que ya reciben datos.

    <!-- SCREENSHOT NEEDED: Pestaña Metrics con el filtro Monitor status en All y varios módulos con datos. -->

5. **El portal responde.** Desde el host del servicio, repita una de las
   peticiones que hace el servicio, con las mismas credenciales, y compruebe que
   devuelve el XML. El servicio encierra el recurso entre comillas dobles, como
   en el ejemplo:

    ```bash
    curl -s -u <USERNAME>:<PASSWORD> \
      'http://<RMF_DATA_PORTAL_HOST>:8803/gpm/perform.xml?resource="<RESOURCE>"&id=<METRIC_ID>'
    ```

## Entender los resultados

Cada mainframe se convierte en un agente de primer nivel en el grupo tomado de
la configuración del servicio, con el sistema operativo `Mainframe` y el
intervalo de `agent_interval`. Cada ciclo de recogida produce un documento de
agente por bloque de módulo: el servicio lee el informe, convierte cada fila o
total en un módulo y entrega el documento. No se acumula nada en local más allá
del búfer de reintentos.

**Módulos dataportal.** Cada fila del informe se convierte en un módulo. El
nombre concatena el recurso, un espacio, el identificador de la métrica y la
descripción de la métrica o de la fila, sin separador entre los dos últimos, así
que los nombres resultan técnicos y no descriptivos. El tipo es siempre
`generic_data` y la descripción es la que el portal publica para esa métrica o
fila; los umbrales del bloque se copian a todos los módulos que genera. Un
informe sin filas produce un documento sin módulos: el agente conserva su último
contacto, pero no se publica nada nuevo. La descripción del agente se sustituye
por la descripción de la métrica en cada ciclo.

**Módulos de almacenamiento.** Cuatro módulos por grupo de almacenamiento, en
GB, con los umbrales del bloque solo en `STORGRP % free <group>`.

**Módulos SMS.** Nueve totales fijos en GB, todos con los umbrales del bloque.
El addon traduce literalmente las etiquetas del conjunto de datos: `Used` es el
importe `Usado`, `Free` es el importe `Reservado` y `Available` es su suma. Un
valor llamado `Free` contiene por tanto espacio reservado, no espacio libre.

**Comportamiento ante fallos.** Cuando el portal no responde o responde con un
error, el log recibe el cuerpo de la respuesta y el ciclo no publica módulos
para ese bloque. El servicio lo reintenta en la siguiente ejecución programada;
no conserva estado.

## Operar y resolver problemas

### Control del servicio

```bash
sudo systemctl start mf_server
sudo systemctl status mf_server
sudo systemctl stop mf_server
sudo systemctl restart mf_server
tail -f /var/log/mf_server.log
```

El archivo de log se trunca en cada arranque, así que un reinicio borra la
ejecución anterior. Cópielo antes de reiniciar si necesita el historial.

El desinstalador elimina la unidad, los ejecutables,
`/etc/pandora/mf_server.conf`, `/etc/pandora/mf_server.env` y el directorio
completo `/etc/pandora/conf`. En un host que también ejecute otros componentes
de Pandora FMS, haga copia de ese directorio antes de ejecutar
`mf_server_installer --uninstall`.

### Ejecutar en primer plano

Ponga `daemon 0` en la configuración del servicio y ejecútelo como `root`:

```bash
sudo /usr/bin/mf_server /etc/pandora/mf_server.conf
```

El servicio sigue escribiendo en `log_file`, no en la salida estándar, y no se
separa, así que el proceso permanece en el terminal hasta que se interrumpa.
Recuerde restaurar `daemon 1` antes de volver a arrancar la unidad systemd: la
unidad espera que el servicio se separe.

Sin argumentos, o con más de uno, el servicio imprime un resumen de uso y
termina. Ese resumen todavía lista `-r` y `-m`; ninguna de las dos opciones se
acepta, y el navegador del Portal de Datos RMF de la consola sustituye a ambas.

### Limitaciones conocidas de esta versión

- **Todos los módulos son numéricos.** El tipo publicado es `generic_data` para
  todos los módulos, diga lo que diga `module_type`, así que un informe que
  devuelve texto (nombres de partición, texto de estado) no puede convertirse en
  un valor de módulo utilizable.
- **La mayoría de tokens `module_*` no llegan a la consola:** `module_type`,
  `module_unit`, `module_description`, `module_group`, `module_tags`,
  `module_disabled`, `module_quiet`, los umbrales de cadena, las instrucciones y
  los tokens de detección de rebote se leen y se ignoran. Un bloque enviado con
  `module_group` llega con el grupo vacío. Configure esos valores en la consola.
- **`timeout` en `mf_server.conf` no tiene efecto.** El tiempo de espera HTTP de
  las peticiones al portal es el token `timeout` del agente (`5` segundos por
  defecto) y el tiempo de espera FTP es `ftp_timeout`.
- **`secondary_mode` y `secondary_server_ip` no tienen efecto.** Solo añaden una
  línea al log; no hay entrega secundaria implementada.
- **La configuración remota del propio servicio no se aplica.** Solo se
  intercambian archivos de configuración de agentes con la consola;
  `mf_server.conf` es siempre el archivo en disco.
- **La tolerancia de la licencia no se aplica al número de agentes.** En modo
  agente el servicio se detiene en cuanto el número de agentes supera el límite
  de la clave; el margen del diez por ciento que calcula el código no se usa
  nunca y la línea de aviso es inalcanzable. En modo módulo el margen sí se
  aplica y el aviso aparece entre el límite y el margen.
- **Con `xml_buffer 1` el servicio recorre todo el directorio `temporal`** y
  envía y borra todos los archivos `*.data` que encuentra allí, no solo los
  suyos. Mantenga `temporal` en un directorio privado: el valor distribuido de
  `temporal` es `/tmp` y el de `xml_buffer` es `0`.
- **Las etiquetas del conjunto de datos SMS están en español** (`Usado`,
  `Reservado`). Cualquier otro idioma produce nueve valores a cero sin error.
- **El puerto por defecto del portal solo lo aplica el navegador.** El servicio
  usa el puerto por defecto del esquema cuando `dataportal_url` no lleva puerto,
  así que escriba `:8803` de forma explícita.
- **El selector de agentes del navegador usa un identificador de sistema
  operativo fijo** mientras las tablas filtran por el nombre de sistema
  operativo `Mainframe`. Cuando la consola asigna otro identificador, el selector
  **Agent name** puede no listar ningún agente aunque la tabla los muestre.
- **La pestaña Metrics empieza filtrada por Not init**, así que un agente sano no
  muestra filas hasta que se cambia **Monitor status** a **All**.
- **`--destdir` no reubica la unidad systemd**, que siempre se escribe en
  `/etc/systemd/system`.
- **La unidad systemd declara `PIDFile=/var/run/mf_server.pid`**, pero el
  servicio nunca crea ese archivo. Cuando `systemctl status` no muestra el
  proceso, búsquelo con `ps`. El desinstalador elimina la ruta de todos modos.

### Resolución de problemas

| Síntoma | Causa y comprobación |
| --- | --- |
| El servicio no arranca y el log termina en `Invalid license` | `pandora_license` está vacío o no es válido. Configure una clave válida y reinicie |
| El log termina en `Error opening file .../mf_server.conf` | La unidad pasa `/etc/pandora/mf_server.conf`; el archivo falta o el servicio se arrancó con otra ruta. Reinstale o corrija la ruta |
| El log termina en `Error opening directory .../conf` | `agent_conf_dir` no existe o `root` no puede leerlo |
| `Agent name not defined in file <file>!` | El archivo del agente no tiene `agent_name`. El archivo no se renombra y el agente se omite |
| `Dataportal not configured in file <file>` | Falta `dataportal_url`, `dataportal_user` o `dataportal_pass` |
| `Invalid module definition in: <file>` | Un bloque no tiene `module_metric` y `module_resource`, ni `module_plugin` |
| El agente existe en la consola pero no tiene módulos | Los bloques no tienen `module_plugin`, o el informe no devolvió filas. Revise el log y repita la petición al portal |
| `Error sending file '<file>'` | Falló la entrega: compruebe `server_ip`, `server_port`, la ruta del cliente Tentacle y el cortafuegos. Con `xml_buffer 1` el documento se reintenta |
| Los módulos dejan de actualizarse con el servicio en marcha | El portal responde con un error o no responde. El log contiene el cuerpo de la respuesta; repita la petición con `curl` |
| El árbol del navegador RMF está vacío | El puerto es incorrecto, las credenciales se rechazan o **Depth** está vacío. Una dirección sin puerto recibe `:8803` |
| Un nombre de módulo parece `RESOURCE METRICID...` | Es la regla de nombres de los módulos dataportal, no un error |
| Los datos aparecen con otra hora que en el portal | El servicio marca cada documento con la hora de recogida. Use `autotime 1` para que Pandora FMS lo marque al recibirlo |

## Referencia

### Tokens de configuración del servicio

| Nombre | Obligatorio | Por defecto | Descripción |
| --- | --- | --- | --- |
| `agent_conf_dir` | Sí | `./conf` (distribuido: `/etc/pandora/conf`) | Directorio que se recorre en busca de un archivo `*.conf` por mainframe. Use una ruta absoluta |
| `group` | No | vacío (distribuido: `Servers`) | Grupo de consola de todos los agentes. Debe existir; un archivo de agente puede sobrescribirlo |
| `agent_interval` | No | `300` | Intervalo del agente en segundos, común a todos y enviado en cada documento |
| `conf_interval` | No | sin valor (distribuido: `300`) | Segundos entre comprobaciones de configuración remota. Sin valor, la comprobación se hace en cada pasada del bucle principal |
| `daemon` | No | sin valor (distribuido: `1`) | `1` se separa en segundo plano y redirige las salidas estándar a `/dev/null`. Cualquier otro valor o su ausencia mantiene el servicio en primer plano, algo que la unidad systemd no espera |
| `log_file` | Sí | `/var/log/mf_server.log` | Archivo de log, truncado en cada arranque |
| `module_interval` | No | `300` | Intervalo de recogida por defecto, en segundos, de los bloques que no fijan `module_interval` |
| `module_threads` | No | `2` (distribuido: `5`) | Hilos que ejecutan los bloques. Los bloques se reparten a partes iguales |
| `pandora_license` | Sí | vacío (distribuido: comentado) | Clave de licencia de Pandora FMS |
| `remote_config` | No | `0` (distribuido: `1`) | `1` habilita el intercambio de configuración remota para todos los agentes que no lo sobrescriban |
| `server_ip` | Sí | `127.0.0.1` | Dirección del servidor Tentacle, usada para entregar y para recibir archivos |
| `server_port` | No | `41121` | Puerto Tentacle |
| `server_path` | Obligatorio para entrega local | `/var/spool/pandora/data_in` | Directorio de destino de `transfer_mode local` |
| `temporal` | Sí | `/tmp` | Directorio donde se escriben los documentos antes de entregarlos y donde se reintenta el búfer. Use un directorio privado |
| `tentacle_client` | Sí para entrega Tentacle | `/usr/bin/tentacle_client` | Ruta completa al cliente Tentacle |
| `timeout` | No | — | Se acepta y se almacena, nunca se usa. El tiempo de espera del portal es el token `timeout` del agente |
| `ftp_timeout` | No | `10` | Tiempo de espera en segundos de las peticiones FTP(S) de los módulos de almacenamiento |
| `transfer_mode` | No | `tentacle` | `tentacle` entrega con el cliente Tentacle; `local` copia a `server_path`. Cualquier otro valor no está soportado |
| `xml_buffer` | No | `1` (distribuido: `0`) | `1` conserva en `temporal` un documento no entregado y lo reintenta en cada pasada |
| `temporal_min_size` | No | `1` (distribuido: `1024`) | Bytes libres que debe tener `temporal` para que el búfer conserve un documento fallido. Por debajo, el documento se borra |
| `keepalive` | No | `300` | Segundos entre los documentos `server_data` que el servicio envía para identificarse |
| `startup_delay` | No | `2` | Segundos que espera cada hilo de recogida tras el arranque |
| `send_udelay` | No | `1000` | Microsegundos entre peticiones de configuración remota |
| `server_name` | No | nombre del host | Nombre enviado en el documento `server_data` |
| `server_opts` | No | vacío | Opciones extra pasadas al cliente Tentacle, sin validación |
| `secondary_mode`, `secondary_server_ip` | No | `0`, sin valor | Se aceptan y solo se reflejan en el log. No hay entrega secundaria implementada |

### Tokens de configuración del agente

| Nombre | Obligatorio | Por defecto | Descripción |
| --- | --- | --- | --- |
| `agent_name` | Sí | — | Nombre del agente en la consola. El archivo se renombra al md5 de este nombre al arrancar |
| `dataportal_url` | Sí | — | URL del portal. Solo se usan esquema, host y puerto: el servicio siempre pide `<scheme>://<host>:<port>/gpm/...`, así que la ruta se descarta y el puerto debe escribirse de forma explícita |
| `dataportal_user` | Sí | — | Usuario de autenticación básica del portal |
| `dataportal_pass` | Sí | — | Contraseña de ese usuario. Se guarda en texto claro |
| `description` | No | `Mainframe agent` | Descripción del agente. Los bloques dataportal la sustituyen por la descripción de la métrica en cada ciclo |
| `group` | No | el `group` del servicio | Grupo del agente |
| `remote_config` | No | el `remote_config` del servicio | Interruptor de configuración remota por agente |
| `timeout` | No | `5` | Tiempo de espera HTTP en segundos de las peticiones al portal de este agente |
| `encoding` | No | `UTF-8` | Codificación declarada en el documento |
| `autotime` | No | `0` | `1` omite la marca de tiempo del documento, de modo que Pandora FMS la pone al recibirlo |
| `custom_id`, `url_address` | No | vacío | Se envían como `custom_id` y `url_address` |
| `address` | No | no se envía | Dirección del agente, solo se envía si está definida |
| `parent_agent_name` | No | no se envía | Agente padre, solo se envía si está definido |
| `os_name` | No | `Mainframe` | Sistema operativo del agente. Cámbielo solo junto con las vistas de consola |
| `os_version` | No | vacío | Versión del sistema operativo del agente |
| `include <file>` | No | — | Fusiona tokens de agente desde otro archivo. Los bloques de módulo no se leen de los archivos incluidos. Use una ruta absoluta |

### Tokens de definición de módulo

Un bloque se delimita con `module_begin` y `module_end`. Solo estos tokens
cambian lo que el servicio recoge o publica:

| Token | Se aplica a | Descripción |
| --- | --- | --- |
| `module_plugin` | Todos | `dataportal`, `storage` o `storage_sms`. Sin él el bloque se carga y nunca se ejecuta |
| `module_resource` | `dataportal` | Etiqueta del recurso, tal como la devuelve el portal |
| `module_metric` | `dataportal` | Identificador de la métrica, tal como lo devuelve el portal |
| `module_url` | `storage`, `storage_sms` | URL `ftp://` o `ftps://` del conjunto de datos |
| `module_lrecl` | `storage`, `storage_sms` | Longitud de registro del conjunto de datos. Por defecto `80` |
| `module_interval` | Todos | Intervalo de recogida del bloque en segundos; por defecto el `module_interval` del servicio |
| `module_min_warning`, `module_max_warning` | Todos | Umbrales de aviso, copiados a todos los módulos del bloque |
| `module_min_critical`, `module_max_critical` | Todos | Umbrales críticos, copiados a todos los módulos del bloque |
| `module_warning_inverse`, `module_critical_inverse` | Todos | Indicadores de umbral inverso, copiados a todos los módulos del bloque |

Estos tokens se aceptan y se leen, y no tienen ningún efecto en los módulos
publicados: `module_type`, `module_unit`, `module_description`, `module_group`,
`module_tags`, `module_disabled`, `module_quiet`, `module_custom_id`,
`module_min_ff_event`, `module_ff_interval`, `module_str_warning`,
`module_str_critical`, los tokens de instrucciones y `module_postprocess`.

### Módulos generados

**Los bloques dataportal** publican un módulo `generic_data` por fila del
informe, llamado `<RESOURCE> <METRIC_ID><DESCRIPTION>`, donde la descripción
final es la etiqueta de la fila en un informe de lista o la descripción de la
métrica en el resto de casos. Las filas sin valor se omiten.

**Los bloques storage** publican cuatro módulos `generic_data` por cada grupo de
almacenamiento encontrado en el conjunto de datos:

| Módulo | Unidad | Valor |
| --- | --- | --- |
| `STORGRP available <group>` | `GB` | Valor de `Es=`: capacidad del grupo de almacenamiento |
| `STORGRP % free <group>` | ninguna | Valor de `Libre=`. Es el único módulo de almacenamiento que lleva los umbrales del bloque |
| `STORGRP %used <group>` | ninguna | `100` menos el valor de `Libre=` |
| `Free Space (DASD) - <group>` | `GB` | Capacidad multiplicada por el porcentaje libre y dividida por `100` |

**Los bloques SMS** publican nueve módulos `generic_data` en `GB`, todos con los
umbrales del bloque:

| Módulo | Valor |
| --- | --- |
| `Total Space (SMS) - Available` | `Usado SMS` más `Reservado SMS` |
| `Total Space (SMS) - Used` | `Usado SMS` |
| `Total Space (SMS) - Free` | `Reservado SMS` |
| `Total Space (NOSMS) - Available` | `Usado No SMS` más `Reservado No SMS` |
| `Total Space (NOSMS) - Used` | `Usado No SMS` |
| `Total Space (NOSMS) - Free` | `Reservado No SMS` |
| `Total Space (DASD) - Used` | `Usado SMS` más `Usado No SMS` |
| `Total Space (DASD) - Free` | `Reservado SMS` más `Reservado No SMS` |
| `Total Space (DASD) - Available` | Suma de los cuatro importes |

### Peticiones al portal

El servicio y el navegador de la consola leen estos recursos del Portal de Datos
RMF. El servicio envía autenticación básica en cada uno de ellos.

| Petición | La usa | Propósito |
| --- | --- | --- |
| `gpm/perform.xml?resource="<resource>"&id=<metric>` | Servicio | Informe de métrica de un recurso |
| `gpm/root.xml` | Navegador | Raíz del árbol de recursos |
| `gpm/contained.xml?resource=<resource>` | Navegador | Hijos de un nodo del árbol |
| `gpm/listmetrics.xml?resource=<resource>` | Navegador | Métricas disponibles para un recurso |

### Opciones del instalador

| Opción | Efecto |
| --- | --- |
| `--install` | Instala el servicio, el cliente Tentacle, los archivos de configuración, el directorio de agentes y la unidad systemd, y habilita la unidad |
| `--uninstall` | Detiene y deshabilita la unidad y después la elimina junto con los ejecutables, `/etc/pandora/mf_server.conf`, `/etc/pandora/mf_server.env`, `/var/run/mf_server.pid` y el directorio completo `/etc/pandora/conf` |
| `--destdir <dir>` | Instala todo bajo `<dir>` excepto la unidad systemd, que siempre se escribe en `/etc/systemd/system` |
| `--force-perl` | Reinstala el entorno incluido aunque ya haya uno más reciente |
| sin opción, o con una desconocida | Imprime el resumen de uso y termina |

### Extensión de consola

| Superficie | Detalle |
| --- | --- |
| Menú | **Operation → Z/OS**, con el título de página `Z/OS Monitoring` |
| Pestañas | `RMF Data Portal Browser`, `Mainframes`, `Metrics` |
| Privilegio necesario | `AR` (lectura de agentes) para el navegador y la lista de mainframes; `AR` o `AW` para la vista de módulos; `AW` para ver el icono de configuración remota |
| Pestaña Mainframes | Agentes cuyo sistema operativo es `Mainframe`, de primer nivel y habilitados: agente, descripción, sistema operativo, intervalo, grupo, módulos, estado, alertas, último contacto y el icono de edición de la configuración remota |
| Pestaña Metrics | Módulos de los agentes mainframe, filtrables por nombre de agente, nombre de módulo, estado de monitorización y una búsqueda de texto libre; columnas de agente, tipo, nombre de módulo, intervalo, estado, gráfica, aviso, dato y marca de tiempo |

Campos del navegador:

| Campo | Detalle |
| --- | --- |
| **RMF IP address** | Host del portal, con o sin puerto. Se añade `:8803` cuando no se escribe puerto |
| **Username** | Usuario de autenticación básica |
| **Password** | Contraseña de ese usuario. Enmascarada en el formulario y no se almacena |
| **Depth** | Profundidad máxima del árbol. El formulario empieza en `3`; un valor vacío detiene el árbol de inmediato |
| **Browse** | Construye el árbol. La petición puede tardar en árboles grandes |
| **Search options** | Búsqueda de texto en el árbol, con primera, anterior, siguiente y última coincidencia, además de expandir y contraer |

### Identidad del addon

| Propiedad | Valor |
| --- | --- |
| Identificador del Marketplace | `pandorafms.mainframe` |
| Nombre | IBM Z Series Mainframe |
| Versión | `2.0` |
| Categoría | Miscelaneus |
| Licencia | One |
| Disponibilidad | Descarga limitada a usuarios con licencia |
| Última actualización en el Marketplace | 2026-07-08 |
| Paquete | `pandorafms.mainframe.2.0.zip` |
| Versión del servicio informada en los documentos de agente | `7.0 (Build 191107)` |

La versión del servicio de la última fila es su propio identificador de
compilación, que aparece en los documentos de agente y en el resumen de uso. Es
independiente de la versión del addon de la entrada del Marketplace.
