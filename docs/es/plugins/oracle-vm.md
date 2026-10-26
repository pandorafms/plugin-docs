# Plugin de monitorización Oracle VM

*Última actualización del artículo: 2026-10-26.*

## Qué hace

El plugin de monitorización Oracle VM monitoriza un entorno Oracle VM desde
Pandora FMS a través de la API REST de su Oracle VM Manager. Cada ejecución lee
el manager y lo que este gestiona, y convierte el resultado en agentes y módulos
de Pandora FMS: el estado del manager y sus contadores de tareas, la capacidad de
los pools de servidores, los OVM Server con sus puertos de red, las máquinas
virtuales con su memoria y sus discos, y los servidores de ficheros con sus
sistemas de ficheros. No se instala nada en los hosts de Oracle VM: el plugin se
ejecuta desde un host que pueda alcanzar la API del OVM Manager.

Cada ejecución es puntual: se autentica contra la API, recopila todo el entorno y
entrega un documento de datos de agente por elemento. La entrega se hace a través
de Tentacle o copiando los documentos en una carpeta de datos de Pandora FMS. El
plugin no tiene modo de plugin de agente y no imprime XML de módulos por la
salida estándar.

La monitorización Oracle VM es un addon distinto de Oracle Discovery
(`pandorafms.oracle`), que monitoriza instancias de Oracle Database y se documenta
en [Oracle Discovery](../discovery/oracle.md). Esta página cubre únicamente el
manager de virtualización Oracle VM.

## Preparación

### Compatibilidad y disponibilidad

| Ámbito | Estado | Evidencia |
|--------|--------|-----------|
| Oracle VM Manager 3.4.5 | `Known compatible` | La guía del addon enlazada desde la entrada del Marketplace indica que el plugin se desarrolló contra Oracle VM Manager 3.4.5 |
| Versiones de Oracle VM Manager distintas de 3.4.5 | `Not validated` | No se ha registrado una matriz de versiones para este addon |
| Acceso desde el host que ejecuta el plugin a la API REST del OVM Manager | `Required` | Cada ejecución consulta la API |
| Un usuario del OVM Manager con permiso de lectura sobre los recursos de la API | `Required` | Cada petición se autentica con credenciales HTTP Basic |
| La librería de plugins de Pandora FMS (`PandoraFMS::PluginTools`) | `Required` | La guía del addon la enumera como requisito previo |
| Un servidor Tentacle accesible en `tentacle_ip` y `tentacle_port` | `Required` cuando `transfer_mode=tentacle` | Cada documento generado se envía a esa dirección y ese puerto |
| Una carpeta de datos con permiso de escritura | `Required` cuando `transfer_mode` no es `tentacle` | Cada documento generado se copia en `local_folder` |
| Las guest additions de Oracle VM en las máquinas virtuales monitorizadas | `Required` para las direcciones IP de las VM | La guía del addon indica que la recogida de IP necesita las guest additions |
| Una versión concreta de Pandora FMS | `Not validated` | No se ha registrado una matriz de versiones para este addon. El Marketplace indica que sus integraciones son compatibles con Pandora FMS NG 784 y posteriores |
| Un sistema operativo concreto del host | `Not validated` | No se ha registrado un sistema operativo para esta versión |

El addon se distribuye a través del Marketplace de Pandora FMS y su descarga está
limitada a usuarios con licencia.

### Requisitos

1. **Acceso de red** desde el host que ejecuta el plugin a la API REST del OVM
   Manager. La configuración de ejemplo usa HTTPS en el puerto `7002`.
2. **Un usuario del OVM Manager y su contraseña.** El plugin solo lee: solicita el
   manager, la lista de tareas, los pools de servidores, los servidores, las
   máquinas virtuales, las NIC virtuales, los discos, los servidores de ficheros y
   los sistemas de ficheros. Utilice una cuenta con acceso de lectura a esos
   recursos.
3. **Un host para ejecutar el plugin** con la librería de plugins de Pandora FMS
   (`PandoraFMS::PluginTools`), que forma parte de una instalación de Pandora FMS.
   La opción habitual es el servidor de Pandora FMS que ejecuta el plugin.
4. **Un destino de entrega** que Pandora FMS pueda leer: un servidor Tentacle o una
   carpeta de datos que lea el servidor de datos de Pandora FMS.
5. **Las guest additions de Oracle VM** dentro de las máquinas virtuales
   monitorizadas, solo si desea sus direcciones IP en los datos del agente.

### Instalar el plugin

La guía del addon documenta el plugin como el ejecutable `ovm-plugin.64` junto con
el archivo de configuración `ovm-plugin.conf`. Copie ambos al host que ejecutará el
plugin; para un plugin de servidor de consola la carpeta recomendada es
`/usr/share/pandora_server/util/plugin/`.

Descargue el paquete desde la entrada del Marketplace de Pandora FMS, limitada a
usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.oracle_vm_monitoring](https://marketplace.pandorafms.com/entries/pandorafms.oracle_vm_monitoring)

El archivo de configuración distribuido contiene valores de ejemplo. Sustituya la
URL de la API, el usuario y la contraseña antes de la primera ejecución, y restrinja
los permisos del archivo al usuario que ejecuta el plugin. Si su paquete nombra el
ejecutable de otra forma, use ese nombre en lugar de `ovm-plugin.64` en los
ejemplos.

## Configuración

### Archivo de configuración

El plugin toma su configuración de tres fuentes, en orden creciente de prioridad:

```text
valores predeterminados < archivo de configuración < opciones de línea de comandos
```

El archivo de configuración es un archivo de texto plano con líneas `clave=valor`.
Se omiten las líneas en blanco y las que empiezan por `#`, se eliminan los espacios
sobrantes de claves y valores, y una clave repetida conserva su último valor. Para
usar un archivo, pase su ruta como primer y único argumento posicional. Cualquier
opción puede pasarse también en la línea de comandos como un par `-clave valor`, y
el valor de la línea de comandos sustituye al del archivo:

```bash
./ovm-plugin.64 -interval 600 -debug 1 <PATH_TO_CONFIG>
```

No hay opción de ayuda. Una ejecución sin un archivo de configuración legible y sin
las opciones obligatorias falla con el error que nombra los ajustes que faltan,
seguido de una línea de uso que muestra el archivo de configuración como único
argumento.

Esta es la configuración mínima para una entrega por Tentacle:

```ini
ovmm_api_url=https://<OVM_MANAGER_URL>:7002/ovm/core/wsapi/rest/
user=<USERNAME>
password=<PASSWORD>
transfer_mode=tentacle
tentacle_ip=<PANDORA_FMS_URL>
tentacle_port=41121
```

### Parámetros de conexión

`ovmm_api_url` es la URL base de la API REST del OVM Manager, hasta la raíz REST
incluida. El plugin añade los nombres de recurso (`Manager`, `Job`, `ServerPool`,
`Server`, `FileServer`) y sigue las URI de recurso que devuelve la API. La barra
final es opcional: el plugin la añade cuando falta.

El usuario y la contraseña se envían con autenticación HTTP Basic en cada petición.
Las peticiones solicitan `application/xml` y el plugin lee las respuestas XML.

### Credenciales y transporte

- Utilice una URL `https`. Con `http` las credenciales y los datos recopilados
  viajan sin cifrar; restrinja la API a una red de confianza si no puede usar
  HTTPS.
- **El plugin no verifica el certificado del OVM Manager.** Acepta cualquier
  certificado, incluido uno autofirmado, de modo que HTTPS protege las credenciales
  en tránsito pero no autentica al servidor. Mantenga la API en una red de gestión
  que usted controle.
- La contraseña se guarda en texto plano en el archivo de configuración. Mantenga
  el archivo propiedad del usuario del plugin y sin acceso para el resto, por
  ejemplo con `chmod 600`.
- Evite `-password` en la línea de comandos: el comando queda en el historial del
  shell y es visible en la lista de procesos mientras el plugin se ejecuta. El
  plugin no tiene una opción de archivo de credenciales independiente, así que
  prefiera el archivo de configuración y pase solo los ajustes no secretos como
  opciones.
- La clave `include` lee otro archivo de claves en ese punto de la configuración,
  de modo que un archivo compartido puede contener los parámetros de conexión y el
  principal el resto. Las claves leídas después de la línea `include` sustituyen a
  las incluidas.

### Nombres de agente y renombrado

Cada agente generado tiene un nombre predeterminado tomado de la API de OVM:

| Recurso | Nombre de agente predeterminado |
|---------|---------------------------------|
| OVM Manager | El UUID del manager |
| Pool de servidores | El ID del pool |
| OVM Server | El hash MD5 del ID del servidor, porque el ID con formato MAC del servidor no es un nombre de agente válido |
| Máquina virtual | El ID de la VM |
| Servidor de ficheros | El ID del servidor de ficheros |

El alias es el nombre del elemento que devuelve la API (el nombre del manager, del
pool, del servidor, de la VM o del servidor de ficheros). Establezca
`alias_as_name=1` para dejar el alias vacío y que Pandora FMS use el nombre del
agente como alias.

Los ID proceden de la interfaz del OVM Manager: abra el elemento y lea su campo
**ID**.

![El ID de una máquina virtual en el OVM Manager](../assets/images/plugins/oracle-vm/ovm-vm-id.png)

![El ID de un OVM Server en el OVM Manager](../assets/images/plugins/oracle-vm/ovm-server-id.png)

Para renombrar un agente, añada una clave de configuración cuyo nombre sea
exactamente el nombre de agente predeterminado. Se pueden añadir tantas claves de
renombrado como se quiera:

```ini
# Una máquina virtual, renombrada por su ID de VM.
0004fb0000060000ed21e30c8dbbbb65a=app-vm-01
# Un OVM Server, renombrado por el hash MD5 de su ID.
a62454d287e230c773f56d618b78500f=ovm-server-01
```

Las claves de renombrado son claves de configuración normales, así que siguen la
misma prioridad que el resto: una opción `-clave valor` sustituye al archivo. Para
un servidor, la clave debe ser el hash MD5, no el ID con formato MAC, porque el
hash es el nombre de agente predeterminado. El ejemplo comentado
`default_agent_name1` del archivo distribuido no renombra nada: la clave es el
valor del ID, no el nombre de un campo. Renombrar el manager, un pool o un servidor
deja a sus hijos apuntando al nombre predeterminado; consulte
[Limitaciones conocidas](#limitaciones-conocidas).

### Entrega

| `transfer_mode` | Comportamiento |
|-----------------|----------------|
| `tentacle` | El plugin escribe cada documento en `tmp` y lo envía con el cliente Tentacle a `tentacle_ip`:`tentacle_port` |
| Cualquier otro valor, incluido el vacío | El plugin escribe cada documento en `tmp` y lo copia en `local_folder` |

La entrega por Tentacle requiere `tentacle_ip`. Un modo de entrega distinto de
`tentacle` requiere `local_folder`. El plugin valida ambas condiciones antes de
contactar con el OVM Manager y se detiene con un error cuando falta el valor
necesario.

El documento generado se elimina de `tmp` tras una entrega correcta y se conserva
allí cuando la entrega falla. Los errores de entrega se informan por la salida de
error solo con `debug=1`; de forma predeterminada una entrega fallida es silenciosa
y la ejecución continúa con el siguiente agente.

### Registrar el plugin en la consola

El plugin se puede registrar en la consola de Pandora FMS como plugin de servidor,
de modo que el servidor de Pandora FMS lo ejecute periódicamente en lugar de una
ejecución manual o por `cron`. Cada ejecución recopila todo el entorno y entrega
todos sus agentes.

1. Abra **Servers → Plugins** y haga clic en **Register Plugin**.
2. Indique el nombre, el tipo de plugin **Standard**, un tiempo máximo de espera y
   una descripción. Aumente el tiempo máximo cuando una ejecución sobre un entorno
   grande tarde más que el valor predeterminado.
3. En **Plugin command**, escriba la ruta al ejecutable `ovm-plugin.64` en el
   servidor de Pandora FMS, por ejemplo
   `/usr/share/pandora_server/util/plugin/ovm-plugin.64`.
4. En **Plugin parameters**, pase la ruta del archivo de configuración como único
   argumento:

```text
/etc/pandora/plugins/ovm-plugin.conf
```

5. Mantenga el usuario y la contraseña de la API en ese archivo en lugar de en los
   campos de la consola.

<!-- SCREENSHOT NEEDED: Servers → Plugins registration form for the Oracle VM monitoring addon, showing the executable path and a configuration file path as the only parameter. -->

El mismo registro puede pasar ajustes individuales con las macros de plugin
`_field1_`, `_field2_`, ... en lugar de un archivo, por ejemplo
`-ovmm_api_url _field1_ -user _field2_ -password _field3_ -transfer_mode tentacle -tentacle_ip 127.0.0.1`.
En ese caso marque el campo de la contraseña como oculto.

El valor que imprime la ejecución no son los datos de monitorización: el plugin
entrega los agentes por sí mismo y los datos aparecen en los agentes generados.
Todos los agentes del entorno se crean o actualizan en la misma ejecución.

## Verificación

Ejecute el plugin manualmente con el archivo de configuración como único
argumento:

```bash
./ovm-plugin.64 <PATH_TO_CONFIG>
```

Una ejecución correcta termina con la línea `Complete!` y sale con estado `0`. No
imprime nada más salvo que `debug=1` esté activo. Con `debug=1` la ejecución
también muestra su progreso, por ejemplo:

```text
> Connecting to OVM Manager REST API...
 >> Collecting OVM Manager information...
 >> Creating XML structure for OVM Manager agent...
 >> Transferring OVM Manager agent XML...
> Scanning OVM servers pools...
```

Después, compruebe la consola tras la primera ejecución:

1. El agente OVM Manager, con el nombre del UUID del manager.
2. Un agente por pool de servidores, uno por OVM Server, uno por máquina virtual y
   uno por servidor de ficheros, bajo el padre descrito en
   [Agentes generados](#agentes-generados).
3. Los módulos de cada agente, enumerados en
   [Módulos generados](#modulos-generados).

<!-- SCREENSHOT NEEDED: Agent tree in the Pandora FMS console showing the OVM Manager agent with its pool, server, VM and file server children after a successful run. -->

Si no se puede alcanzar el manager, la ejecución imprime
`ERROR: Unable to connect to '<URL>' with user '<USER>'.` y sale con estado `1` sin
crear ni actualizar ningún agente. El mensaje repite la URL y el usuario
configurados, así que evite ejecutarlo en un terminal compartido.

## Entender los resultados

Una ejecución produce hasta cinco grupos de agentes. Cada grupo responde a una
pregunta distinta:

- **Manager.** Si el OVM Manager está en ejecución y cuántas de sus tareas
  terminaron en `SUCCESS` o en `FAILURE`.
- **Pools de servidores.** Cuántas máquinas virtuales contiene el pool, cuántos de
  sus servidores están en ejecución y qué parte de la memoria del pool sigue
  disponible.
- **OVM Server.** Si cada servidor está en ejecución, su parte de memoria
  disponible, el estado de cada puerto de red y cuántas de sus máquinas virtuales
  están en ejecución.
- **Máquinas virtuales.** Si cada VM está en ejecución, la parte de memoria del
  servidor que utiliza y cuánto ocupa cada disco virtual.
- **Servidores de ficheros.** La parte de espacio libre de cada sistema de
  ficheros, con su ruta.

Los módulos de estado son binarios: `1` cuando el recurso está en su estado
correcto (`RUNNING` para el manager, los servidores y las VM; `PORT_UP` para un
puerto) y `0` en caso contrario. La descripción de cada módulo de estado repite el
estado bruto que devuelve la API, de modo que un recurso detenido muestra el motivo
en la descripción del módulo.

Los módulos de porcentaje se calculan a partir de las capacidades que informa la
API:

- `Usable memory (%)` es la memoria todavía disponible para máquinas virtuales, no
  la memoria en uso. Es `usableMemory` dividido entre `memory`, para un servidor, o
  la suma sobre los servidores de un pool.
- `Used memory on server (%)` es la memoria actual de la VM como parte de la
  memoria **total del servidor**, no de la memoria asignada a la VM. La descripción
  del módulo indica la memoria actual, el total del servidor y la memoria asignada.
- `<disk name> on disk size (%)` es el espacio que ocupa el disco virtual en el
  almacenamiento como parte de su tamaño nominal, lo que muestra el
  aprovisionamiento fino.
- `<file system> free size (%)` es el espacio libre como parte del tamaño del
  sistema de ficheros.

Un denominador cero produce `0` en lugar de un error. El plugin no establece
umbrales de aviso ni críticos en los módulos generados; añada umbrales en los
módulos sobre los que quiera alertar.

Los alias de los agentes hacen legible la consola: el alias es el nombre del
elemento y el nombre del agente es el identificador de la API. En los OVM Server el
nombre del agente es el hash MD5 del ID del servidor, así que el nombre del
servidor solo aparece como alias y en la descripción.

## Operación y diagnóstico

### Comportamiento en ejecución

- El plugin no guarda estado entre ejecuciones. Cada ejecución recopila todo el
  entorno, así que puede ejecutarse manualmente en cualquier momento.
- Los recursos se recopilan en un orden fijo: manager, lista de tareas, pools de
  servidores, servidores, las VM de cada servidor y servidores de ficheros. Cada
  recurso cuesta al menos una petición a la API y las peticiones son secuenciales,
  de modo que un entorno grande tarda proporcionalmente más.
- Cada petición a la API usa un tiempo de espera de tres segundos. El archivo de
  configuración no tiene ninguna clave para cambiarlo; un manager que responda más
  despacio produce agentes o módulos ausentes.
- `debug=1` muestra el progreso de la ejecución y los errores de entrega. `debug=0`,
  el valor predeterminado, oculta ambos.
- La ejecución termina con `Complete!` y estado `0` aunque una o varias entregas
  hayan fallado. Compruebe la consola, o ejecute con `debug=1`, para confirmar que
  llegaron todos los agentes.
- El plugin recopila todo el entorno en cada ejecución: no hay ninguna opción para
  limitarlo a un pool, servidor, VM o servidor de ficheros.

### Limitaciones conocidas

Estos son comportamientos de la versión `1.0`, documentados tal como son.

- **Un manager con menos de dos tareas detiene la ejecución.** El contador de tareas
  espera una lista de tareas. Con cero tareas o exactamente una, la ejecución se
  detiene con un error no controlado justo después de entregar el agente Manager,
  de modo que no se produce ningún agente de pool, servidor, VM o servidor de
  ficheros. Esto afecta a un OVM Manager nuevo o con poca actividad.
- **`scan_vm_ip=0` no desactiva la recogida de IP de las VM.** El ajuste está
  activo salvo que su valor sea distinto de `0` y de `1`. Para dejar de recopilar
  direcciones, establezca `scan_vm_ip=2` u otro valor fuera de ese par.
- **La dirección de una VM solo se recoge de una NIC virtual con más de una
  dirección IP.** Una VM cuya NIC informa de una sola dirección obtiene una
  dirección de agente vacía, incluso con las guest additions instaladas.
- **El ejemplo de renombrado distribuido no funciona.** Las líneas comentadas
  `default_agent_name1=new_agent_name1` no renombran nada; la clave debe ser el
  nombre de agente predeterminado, como se describe en
  [Nombres de agente y renombrado](#nombres-de-agente-y-renombrado).
- **Renombrar un agente padre rompe la jerarquía.** Cada referencia al padre se
  escribe con el nombre predeterminado del padre (el UUID del manager, el ID del pool
  o el hash MD5 del servidor), no con el nombre renombrado. Si renombra el manager,
  un pool o un servidor, sus hijos (pools, servidores de ficheros, servidores y VM)
  siguen apuntando al nombre antiguo. Renombre solo agentes hoja, o mantenga los
  nombres predeterminados de los agentes que tienen hijos.
- **Los errores de entrega quedan ocultos de forma predeterminada.** Una
  transferencia Tentacle fallida o una copia fallida deja el documento en `tmp`, se
  informa solo con `debug=1` y no cambia el estado de salida.

### Diagnóstico

| Síntoma | Causa y acción |
|---------|----------------|
| `ERROR: No OVM API URL, user or password provided.` y una línea de uso, estado `1` | Falta `ovmm_api_url`, `user` o `password`, o la ruta del archivo de configuración no existe y por tanto no se leyó |
| `ERROR: transfer_mode set to tentacle, but no tentacle_ip provided.`, estado `1` | Se seleccionó la entrega por Tentacle sin una dirección de servidor Tentacle |
| `ERROR: transfer_mode set to local, but no local_folder provided.`, estado `1` | `transfer_mode` no es `tentacle` y `local_folder` está vacío |
| `ERROR: Unable to connect to '<URL>' with user '<USER>'.`, estado `1` | La URL del manager, las credenciales o la ruta de red son incorrectas. Compruebe que la URL es la raíz REST y que el usuario puede leer la API. El certificado no se verifica, así que TLS no es la causa |
| Solo aparece el agente Manager | La lista de tareas interrumpió la ejecución (consulte [Limitaciones conocidas](#limitaciones-conocidas)), o falló una petición posterior. Ejecute con `debug=1` para ver dónde se detiene |
| Aparecen el agente Manager y los agentes de pool, pero ningún agente de servidor | Falló la petición de la lista de servidores, o la API no devolvió los servidores. Ejecute con `debug=1` |
| Un agente de VM no tiene dirección | Faltan las guest additions, o la NIC informa de una sola dirección IP (consulte [Limitaciones conocidas](#limitaciones-conocidas)) |
| No hay error de entrega y no llegan datos nuevos a la consola | La entrega falló de forma silenciosa, o el destino no lo lee Pandora FMS. Ejecute con `debug=1` y compruebe `tentacle_ip`/`tentacle_port` o `local_folder` |
| Los agentes aparecen en un grupo distinto de `group` | El servidor de Pandora FMS está configurado con `autocreate_group_force 1`, que da prioridad al grupo de autocreación del servidor sobre el grupo de los datos del agente |
| La consola muestra un nombre de agente inesperado | El agente se nombra con el ID de la API de forma predeterminada; renómbrelo con una clave igual a ese nombre, o compruebe el hash MD5 en los OVM Server |

## Referencia

### Parámetros del archivo de configuración

El archivo usa líneas `clave=valor`. Se omiten las líneas en blanco y las que
empiezan por `#`.

| Nombre | Obligatorio | Valor predeterminado | Descripción |
|--------|-------------|----------------------|-------------|
| `ovmm_api_url` | Sí | — | URL base de la API REST del OVM Manager, hasta la raíz REST, por ejemplo `https://<OVM_MANAGER_URL>:7002/ovm/core/wsapi/rest/`. La barra final es opcional |
| `user` | Sí | — | Usuario del OVM Manager, enviado con autenticación HTTP Basic |
| `password` | Sí | — | Contraseña de `user`, guardada en texto plano |
| `group` | No | `Servers` | Nombre del grupo escrito en los datos de agente de los agentes generados |
| `interval` | No | `300` | Intervalo del agente, en segundos, escrito en los datos de agente |
| `tmp` | No | `/tmp` | Carpeta donde se escriben los documentos de agente antes de la entrega |
| `transfer_mode` | No | Vacío | `tentacle` entrega con el cliente Tentacle. Cualquier otro valor, incluido el vacío, copia los documentos en `local_folder` |
| `local_folder` | Obligatorio cuando `transfer_mode` no es `tentacle` | — | Carpeta de los documentos copiados, por ejemplo `/var/spool/pandora/data_in/` |
| `tentacle_ip` | Obligatorio cuando `transfer_mode=tentacle` | — | Dirección del servidor Tentacle |
| `tentacle_port` | No | `41121` | Puerto del servidor Tentacle |
| `tentacle_client` | No | `tentacle_client` | Nombre o ruta del ejecutable del cliente Tentacle |
| `tentacle_opts` | No | Vacío | Opciones adicionales pasadas al cliente Tentacle, separadas por espacios |
| `alias_as_name` | No | `0` | `1` deja el alias vacío para que se use el nombre del agente como alias; cualquier otro valor usa el nombre del elemento |
| `scan_vm_ip` | No | Activo | Recoge las direcciones IP de las VM. Los valores distintos de `0` y `1` desactivan la recogida; `0` no la desactiva (consulte [Limitaciones conocidas](#limitaciones-conocidas)) |
| `debug` | No | `0` | `1` muestra el progreso de la ejecución y los errores de entrega por la salida de error; `0` los oculta |
| `include` | No | — | Lee otro archivo de claves en ese punto. Las claves leídas después de la línea `include` sustituyen a las incluidas |
| `<nombre de agente predeterminado>` | No | — | Cualquier clave cuyo nombre coincida con un nombre de agente predeterminado lo sustituye. Se aplica al UUID del manager, a los ID de pool, a los ID de VM, a los ID de servidor de ficheros y al hash MD5 del ID de un servidor |

### Línea de comandos

```bash
./ovm-plugin.64 <PATH_TO_CONFIG> [ -clave valor ... ]
```

| Condición | Comportamiento |
|-----------|----------------|
| Un argumento posicional que nombra un archivo existente | Se lee el archivo y los pares `-clave valor` posteriores sustituyen sus valores |
| Ningún argumento posicional | El plugin lee solo los pares `-clave valor`; las claves de conexión obligatorias deben venir de ellos |
| Un argumento posicional que no nombra un archivo existente | El archivo no se lee y la ruta no se informa como error; la ejecución falla con el error de ajustes ausentes salvo que otra fuente los aporte |
| `-clave valor` | Sustituye el valor de la misma clave del archivo o de los valores predeterminados. Un token final sin su pareja se ignora |
| Una clave desconocida | Se acepta en silencio. Solo una clave igual a un nombre de agente tiene efecto más allá de la configuración |

### Agentes generados

| Agente | Uno por | Nombre predeterminado | Alias | Padre |
|--------|---------|-----------------------|-------|-------|
| OVM Manager | Ejecución: siempre uno | UUID del manager | Nombre del manager | Ninguno |
| Pool de servidores | Pool devuelto por la API | ID del pool | Nombre del pool | Agente Manager |
| OVM Server | Servidor devuelto por la API | Hash MD5 del ID del servidor | Nombre del servidor | Agente del pool, o el agente Manager cuando el servidor no tiene pool |
| Máquina virtual | VM listada por un servidor | ID de la VM | Nombre de la VM | Agente del servidor |
| Servidor de ficheros | Servidor de ficheros devuelto por la API | ID del servidor de ficheros | Nombre del servidor de ficheros | Agente Manager |

Atributos de los agentes:

| Atributo | Valor |
|----------|-------|
| Descripción | `OVM Manager <manager version>` para el manager; la descripción del elemento que devuelve la API cuando es utilizable; en caso contrario `OVM Server pool`, `OVM Server <version> (Hypervisor: <type> <version>)`, `VM on <server name>` u `OVM File server (Type: <type>)` |
| Dirección | La dirección IPv4 de `ovmm_api_url` para el manager (vacía cuando la URL usa un nombre de host); la `ipAddress` del servidor para un OVM Server; las direcciones recogidas de las NIC virtuales para una VM; vacía para pools y servidores de ficheros |
| Versión del sistema operativo | El `osType` de la VM para un agente de VM; vacía para el resto |
| Grupo e intervalo | Los valores `group` e `interval` de la configuración |
| Marca de tiempo | La hora local de la ejecución |

Una VM solo se monitoriza cuando el servidor al que pertenece la incluye en su
lista. Una VM que ningún servidor informa no obtiene agente.

### Módulos generados

Los nombres y descripciones de los módulos son los que escribe el plugin. La grafía
`Successfull jobs` es el nombre de módulo que usa el plugin.

#### OVM Manager

| Módulo | Tipo | Valor | Descripción |
|--------|------|-------|-------------|
| `Manager run state` | `generic_proc` | `1` cuando `managerRunState` es `RUNNING`, `0` en caso contrario | `Current state: <state>` |
| `Successfull jobs` | `generic_data` | Número de tareas cuyo estado resumido es `SUCCESS` | `Amount of successfull jobs in OVM manager` |
| `Failure jobs` | `generic_data` | Número de tareas cuyo estado resumido es `FAILURE` | `Amount of failure jobs in OVM manager` |

Los dos módulos de tareas solo se generan cuando la petición de la lista de tareas
se completa; una lista con menos de dos entradas detiene la ejecución (consulte
[Limitaciones conocidas](#limitaciones-conocidas)). El recuento abarca todas las
tareas que devuelve la API, sea cual sea su estado de ejecución.

#### Pool de servidores

| Módulo | Tipo | Valor | Descripción |
|--------|------|-------|-------------|
| `VMs count` | `generic_data` | Número de identificadores de VM del pool | `Amount of VMs in the server pool` |
| `Servers running` | `generic_data` | Servidores del pool cuyo estado de ejecución es `RUNNING` | `Total servers count in the pool: <n>` |
| `Usable memory (%)` | `generic_data` | Suma de `usableMemory` × 100 / suma de `memory` sobre los servidores del pool; `0` cuando el total es `0` | `Usable memory in the pool: <usable> of <total> MB`, unidad `%` |

#### OVM Server

| Módulo | Tipo | Valor | Descripción |
|--------|------|-------|-------------|
| `Server run state` | `generic_proc` | `1` cuando `serverRunState` es `RUNNING`, `0` en caso contrario | `Current state: <state>` |
| `Usable memory (%)` | `generic_data` | `usableMemory` × 100 / `memory`; `0` cuando el total es `0` | `Usable memory in the server: <usable> of <total> MB`, unidad `%` |
| `Port state (<port name>)` | `generic_proc` | `1` cuando `portState` es `PORT_UP`, `0` en caso contrario. Un módulo por puerto Ethernet | `Current state: <state>` |
| `VMs running` | `generic_data` | VM del servidor cuyo estado de ejecución es `RUNNING` | `Total VMs count in the server: <n>` |

#### Máquina virtual

| Módulo | Tipo | Valor | Descripción |
|--------|------|-------|-------------|
| `VM run state` | `generic_proc` | `1` cuando `vmRunState` es `RUNNING`, `0` en caso contrario | `Current state: <state>` |
| `Used memory on server (%)` | `generic_data` | `currentMemory` × 100 / `memory` del servidor; `0` cuando la memoria del servidor es `0` | `Memory used: <current> of <server total> MB (<assigned> MB assigned)`, unidad `%` |
| `<disk name> on disk size (%)` | `generic_data` | `onDiskSize` × 100 / `size`, para cada disco de la VM. Las unidades de CD-ROM virtual se omiten | `Size: <on-disk> of <size> MB`, unidad `%` |

#### Servidor de ficheros

| Módulo | Tipo | Valor | Descripción |
|--------|------|-------|-------------|
| `<file system> free size (%)` | `generic_data` | `freeSize` × 100 / `size`, para cada sistema de ficheros del servidor | `Free size (<path>): <free> of <total> MB`, unidad `%` |

### Estado de salida

| Estado | Significado |
|--------|-------------|
| `0` | La ejecución terminó. La salida acaba con `Complete!`. Los errores de entrega no cambian el estado |
| `1` | Falta `ovmm_api_url`, `user` o `password`; el modo de entrega está incompleto; o el OVM Manager no respondió |
| Otro | Un error no controlado detuvo la ejecución, por ejemplo una lista de tareas con menos de dos entradas |

### Identidad del addon

| Propiedad | Valor |
|-----------|-------|
| Identificador del Marketplace | `pandorafms.oracle_vm_monitoring` |
| Nombre | Oracle VM monitoring |
| Versión | `1.0` |
| Categoría | Miscelaneus |
| Licencia | One |
| Última actualización en el Marketplace | 2025-07-01 |
| Disponibilidad | Descarga limitada a usuarios con licencia |
