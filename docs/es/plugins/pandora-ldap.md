# Pandora LDAP

*Última actualización del artículo: 2026-10-26.*

## Qué hace

El plugin Pandora LDAP monitoriza un directorio OpenLDAP desde Pandora FMS. En
cada ejecución se autentica en el directorio con un DN de enlace y una
contraseña, mide cuánto tarda el enlace y lee el subárbol `cn=Monitor` del
backend de monitorización del servidor. El resultado se convierte en módulos de
Pandora FMS: el tiempo de respuesta del enlace, los totales de operaciones
iniciadas y completadas, contadores de conexiones y estadísticas, y dos tasas
por segundo.

El plugin tiene tres rutas de entrega:

- **Modo plugin de agente** (`--as_agent_plugin 1`): imprime un bloque
  `<module>` por módulo en la salida estándar.
- **Modo archivo de datos** (por defecto, `--as_agent_plugin 0`): escribe un
  documento `agent_data` del agente en el directorio de datos de Pandora FMS e
  imprime `1`.
- **Entrega por Tentacle** (`--tentacle_address`): escribe el documento, lo
  envía con el cliente de Tentacle e imprime `1`. Esta ruta tiene prioridad
  sobre `--as_agent_plugin`.

Cada ejecución es independiente: el plugin no guarda estado entre ejecuciones.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
|--------|--------|-----------|
| Pandora FMS NG 784 y posteriores | `Soportado` | El Marketplace indica que todas sus integraciones son compatibles con Pandora FMS NG 784 y versiones posteriores. Es una declaración general, no un registro de pruebas de este plugin |
| Un servidor OpenLDAP que exponga el subárbol `cn=Monitor` | `Requerido` | El plugin busca en `cn=Monitor` y lee sus atributos de monitorización en cada ejecución |
| Una cuenta del directorio con acceso de lectura a `cn=Monitor` | `Requerido` | Requisito previo, no una declaración de compatibilidad: el plugin se autentica con las credenciales de `-b` y `-p` |
| Acceso de red desde el host que ejecuta el plugin al listener LDAP | `Requerido` | El plugin se conecta a la URL indicada en `-s` |
| `tentacle_client` en el `PATH` | `Requerido` cuando se usa `--tentacle_address` | El plugin ejecuta el cliente de Tentacle para entregar el documento |
| Otros servidores de directorio, como Active Directory | `Sin validar` | El plugin lee el árbol de monitorización de OpenLDAP; no se ha registrado ningún otro servidor de directorio |
| Versiones de OpenLDAP | `Sin validar` | No se ha registrado una matriz de versiones para este plugin |
| Sistema operativo del host que ejecuta el plugin | `Sin validar` | No se ha registrado ningún sistema operativo para esta versión |

### Requisitos

1. **Un directorio OpenLDAP** accesible desde el host que ejecuta el plugin, con
   el backend de monitorización habilitado y legible. Consulte
   [Preparar el servidor LDAP](#preparar-el-servidor-ldap).
2. **Una cuenta de enlace con acceso de lectura a `cn=Monitor`.** El plugin no
   necesita ningún otro permiso, porque solo lee el subárbol de monitorización.
3. **Pandora FMS** para recibir la salida: el servidor de plugins para la
   entrega por archivo de datos y por Tentacle, o un agente de Pandora FMS para
   el modo plugin de agente.
4. **Un directorio de datos escribible** cuando el plugin escribe el documento
   por sí mismo. El valor por defecto es `/var/spool/pandora/data_in/`.
5. **El cliente de Tentacle** (`tentacle_client`) en el `PATH`, solo para la
   entrega por Tentacle.

### Preparar el servidor LDAP

El plugin lee el backend de monitorización de OpenLDAP. Compruebe que el módulo
está cargado; ejecute esto en el servidor de directorio como root:

```bash
ldapsearch -Y EXTERNAL -H ldapi:/// -b "cn=module{0},cn=config" -s base '(objectClass=*)' olcModuleLoad
```

Si `back_monitor` aparece entre los valores de `olcModuleLoad` de la respuesta,
el backend de monitorización está habilitado. En caso contrario, cárguelo en
`cn=config`; en una instalación por defecto la entrada del módulo es
`cn=module{0},cn=config`. Use un archivo LDIF:

```ldif
dn: cn=module{0},cn=config
changetype: modify
add: olcModuleLoad
olcModuleLoad: back_monitor
```

```bash
ldapmodify -Y EXTERNAL -H ldapi:/// -f <PATH_TO_CONFIG>
```

Después conceda a la cuenta de enlace acceso de lectura a todo el subárbol de
monitorización: en la ACL de `cn=config` de la base de datos `Monitor`, dé
`read` sobre `dn.subtree="cn=Monitor"` al DN de enlace y deniegue el acceso al
resto. El índice de la entrada de base de datos (`olcDatabase={n}Monitor`)
depende del servidor, así que liste las bases de datos de `cn=config` antes de
editar la entrada.

Verifique el acceso con la cuenta que usará el plugin:

```bash
ldapsearch -x -LLL -H 'ldap://<TARGET_HOST>:389' -D '<BIND_DN>' -W -b 'cn=Monitor' -s sub '(objectClass=*)' monitorCounter
```

Una cuenta correcta recibe las entradas del árbol de monitorización con sus
valores `monitorCounter`. `-W` solicita la contraseña de forma interactiva, de
modo que no queda en el historial del intérprete ni se expone en la lista de
procesos.

### Instalar el addon

Descargue el paquete `.pspz2` desde su entrada del Marketplace, que está
limitada a usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.pandoraldap](https://marketplace.pandorafms.com/entries/pandorafms.pandoraldap)

Súbalo en la consola de Pandora FMS con el registro de plugins, descrito en
[Registrar el plugin en la consola](#registrar-el-plugin-en-la-consola). El
paquete contiene el ejecutable `pandora_ldap` y su definición de plugin: el
nombre **Pandora LDAP**, un tiempo de espera máximo de 20 segundos, la cadena
de parámetros y siete macros. El paquete distribuido es autocontenido: el host
que lo ejecuta no necesita ninguna instalación de Python.

Pandora FMS instala el ejecutable en su directorio de plugins, normalmente
`/usr/share/pandora_server/util/plugin/`, y lo ejecuta desde el servidor
seleccionado para el módulo.

## Configuración

### Modelos de ejecución

El plugin selecciona la ruta de entrega en este orden:

1. **`--tentacle_address` está presente.** El plugin escribe el documento
   `agent_data` en `--data_dir` y lo envía con `tentacle_client` a
   `<tentacle_address>:<tentacle_port>`. Imprime `1` y elimina el archivo tras
   una transferencia correcta. `--as_agent_plugin` se ignora en esta ruta.
2. **`--as_agent_plugin 1`.** El plugin imprime un bloque `<module>` por módulo
   en la salida estándar, sin el envoltorio `agent_data`, y no escribe ningún
   archivo. Es la salida que espera un plugin de agente de Pandora FMS.
3. **Cualquier otro valor, o la opción omitida.** El plugin escribe el documento
   `agent_data` en `--data_dir` e imprime `1`. El valor por defecto es `0`, que
   selecciona esta ruta.

`--as_agent_plugin` solo acepta un número entero: un valor como `true` es un
error de uso y la ejecución termina con estado de salida 2.

### Ejecución desde la línea de comandos

Una ejecución mínima como plugin de agente necesita las cuatro opciones
obligatorias:

```bash
./pandora_ldap -s 'ldap://<TARGET_HOST>:389' -b 'cn=monitor,dc=example,dc=com' \
    -p '<PASSWORD>' -a ldap-lab --as_agent_plugin 1
```

Una ejecución en modo archivo de datos, con el grupo de destino y el directorio
de datos explícitos:

```bash
./pandora_ldap -s 'ldap://<TARGET_HOST>:389' -b 'cn=monitor,dc=example,dc=com' \
    -p '<PASSWORD>' -a ldap-lab -g ldap --data_dir /var/spool/pandora/data_in/
```

Una ejecución con Tentacle:

```bash
./pandora_ldap -s 'ldap://<TARGET_HOST>:389' -b 'cn=monitor,dc=example,dc=com' \
    -p '<PASSWORD>' -a ldap-lab --tentacle_address <PANDORA_FMS_SERVER> --tentacle_port 41121
```

- `-s` recibe la URL LDAP, incluidos el esquema y el puerto. Se aceptan tanto
  `ldap://` como `ldaps://`; el plugin no tiene opciones TLS propias, así que la
  URL y la configuración del cliente LDAP del host determinan la conexión.
- `-a` da nombre al agente que el documento `agent_data` crea o actualiza en la
  consola. También es la base del nombre del archivo de salida.
- `-g` es el grupo de destino de ese agente. El valor por defecto es `ldap`.
- `-m` añade un prefijo a todos los nombres de módulo, de modo que un mismo
  directorio puede alimentar varios agentes con módulos distinguibles. No tiene
  valor por defecto.
- `--data_dir` debe existir y ser escribible por el usuario que ejecuta el
  plugin.
- La ruta de Tentacle usa `tentacle_client` del `PATH` y no existe ninguna
  opción para una contraseña de Tentacle.

### Registrar el plugin en la consola

1. Abra **Servers → Plugins** y suba el paquete `.pspz2` con **Register
   Plugin**. La carga registra el plugin, su ejecutable y sus macros.
2. Abra el plugin en la lista. La definición muestra el nombre **Pandora LDAP**,
   un tiempo de espera máximo de 20 segundos y esta cadena de parámetros:

```text
-s _field1_ -b _field2_ -p _field3_ -a _field4_ --as_agent_plugin _field5_ -g _field6_ --data_dir _field7_
```

3. Rellene cada macro con los valores del directorio. Las macros son la
   superficie de registro del addon:

| Campo | Opción | Valor que introducir |
|-------|--------|----------------------|
| `_field1_` | `-s` | URL LDAP con el puerto, por ejemplo `ldap://<TARGET_HOST>:389` |
| `_field2_` | `-b` | DN de enlace, por ejemplo `cn=monitor,dc=example,dc=com` |
| `_field3_` | `-p` | Contraseña del DN de enlace. Active **Hide value** |
| `_field4_` | `-a` | Nombre del agente que contendrá los módulos |
| `_field5_` | `--as_agent_plugin` | `1` para imprimir el XML de módulos, `0` para escribir el archivo de datos |
| `_field6_` | `-g` | Grupo de destino del agente, por ejemplo `ldap` |
| `_field7_` | `--data_dir` | Directorio de datos de Pandora FMS, por ejemplo `/var/spool/pandora/data_in/` |

<!-- SCREENSHOT NEEDED: Formulario de registro de plugins de Pandora FMS para el paquete Pandora LDAP, con la cadena de parámetros y las siete macros. -->

Una vez registrado, el plugin está disponible al crear módulos de plugin y cada
módulo rellena las macros de forma individual.

La cadena de parámetros pasa un valor a todas las opciones, así que funciona
tal cual solo cuando todas las macros tienen valor. Una macro vacía deja su
opción seguida de la siguiente, y la ejecución termina con un error de uso como
`error: argument -g/--group: expected one argument`. En la práctica hay que
rellenar `_field6_` y `_field7_` aunque el paquete las describa como opcionales,
o editar la cadena de parámetros para quitar `-g` y `--data_dir` y dejar que se
apliquen los valores por defecto.

El paquete define todas las macros con `hide = 0`, incluida la contraseña. Por
tanto la consola muestra el valor de `_field3_` en claro en el editor de
macros: active **Hide value** para esa macro al registrar el plugin y trate el
acceso a la definición del plugin como acceso a la credencial.

### Credenciales y transporte

- La contraseña de enlace se pasa con `-p`, así que el comando queda visible en
  el historial del intérprete y, mientras el plugin se ejecuta, en la lista de
  procesos del host.
- En la consola la contraseña vive en la macro de módulo o de plugin
  `_field3_`. Con `hide = 0` no está enmascarada; active **Hide value** y
  restrinja quién puede leer la configuración del plugin.
- Una conexión `ldap://` sin cifrar envía la contraseña de enlace y los
  resultados sin cifrar. Prefiera `ldaps://` cuando el directorio lo admita, o
  mantenga el tráfico en una red de confianza.
- El documento `agent_data` generado contiene solo métricas: no se escribe en él
  ningún DN de enlace ni ninguna contraseña.

## Verificación

Ejecute el plugin manualmente desde un terminal con las opciones obligatorias y
`--as_agent_plugin 1`:

```bash
./pandora_ldap -s 'ldap://<TARGET_HOST>:389' -b 'cn=monitor,dc=example,dc=com' \
    -p '<PASSWORD>' -a ldap-lab --as_agent_plugin 1
```

`./pandora_ldap -h` imprime la lista de opciones y el encabezado de uso, que
además informa de la versión del ejecutable.

En el modo plugin de agente, una ejecución correcta imprime un bloque `<module>`
por módulo. El extracto siguiente muestra la forma de la salida; los valores
dependen del directorio:

```xml
<module>
	<name><![CDATA[Response time]]></name>
	<type>generic_data</type>
	<data><![CDATA[0.004]]></data>
	<description><![CDATA[response time un sec]]></description>
	<unit><![CDATA[s]]></unit>
</module>
<module>
	<name><![CDATA[active operations]]></name>
	<type>generic_data</type>
	<data><![CDATA[3]]></data>
	<description><![CDATA[Number of active operations]]></description>
</module>
```

En el modo archivo de datos la ejecución imprime `1` y escribe
`<data_dir>/<agent_name>.<epoch>.data`, donde `<epoch>` es el número de segundos
de la ejecución. En el modo Tentacle la ejecución también imprime `1` y el
documento se envía al servidor de Tentacle configurado.

**Antes de confiar en esta salida, revise la limitación de la versión en
[Operar y resolver problemas](#operar-y-resolver-problemas).** Con el paquete
actual, una ejecución contra un directorio que devuelve solo los atributos que
el plugin solicita termina con un `KeyError` antes de entregar ningún módulo, en
todas las rutas de entrega.

<!-- SCREENSHOT NEEDED: El agente LDAP y sus módulos en la consola de Pandora FMS tras una ejecución correcta. -->

## Entender los resultados

### Agente generado

La entrega por archivo de datos y por Tentacle crea un agente, con el nombre de
`-a`:

| Propiedad | Valor |
|-----------|-------|
| Nombre y alias | El valor de `-a` |
| Descripción | `Ldap metrics` |
| Grupo | El valor de `-g`, `ldap` por defecto |
| Dirección | Vacía |
| Sistema operativo y versión | Vacíos |
| Intervalo | Vacío: el plugin no lo establece |
| Marca de tiempo | Hora local de la ejecución, en formato `YYYY/MM/DD HH:MM:SS` |

El modo plugin de agente no crea ningún agente: los módulos pertenecen al agente
de Pandora FMS que ejecuta el plugin.

### Módulos generados

El plugin construye siempre cuatro módulos fijos y añade los módulos derivados
del subárbol de monitorización:

- **Response time.** Segundos que tardó el enlace. El temporizador cubre solo el
  enlace, no la búsqueda, así que este módulo no mide la ejecución completa.
- **Contadores totales de operaciones.** `active operations`, `operations/sec` y
  `authentications/sec` proceden de la entrada agregada
  `cn=Operations,cn=Monitor` y de su hijo `Bind`: `active operations` es la
  diferencia entre los totales iniciados y completados, mientras que los dos
  módulos `/sec` reciben los totales acumulados como módulos incrementales, de
  modo que Pandora FMS calcula la tasa entre muestras.
- **Contadores de conexiones y estadísticas.** Un módulo por cada entrada de
  monitorización que tenga un valor `monitorCounter`, renombrada a partir del DN
  de la entrada: contadores de conexiones, estadísticas y waiters.
- **Contadores de operaciones por tipo.** Por cada entrada de operación, un
  módulo `<operation>initiated` y un módulo `<operation>completed`.

`-m` añade un prefijo a todos los nombres de módulo de la ejecución. Los nombres
se construyen concatenando el prefijo, el nombre y, en los módulos de operación,
el sufijo `initiated` o `completed` sin espacio, así que los nombres son
`Bind operationsinitiated` y `Bind operationscompleted`, no
`Bind operations initiated`.

Los nombres amigables de los contadores proceden del DN de la entrada, no del
valor del atributo: toda entrada cuyo DN contenga `Current` se publica como
`Current connections`, incluidas las entradas que describen otra cosa. Cuando
dos entradas del árbol de monitorización colapsan en el mismo nombre, gana la
última leída y el otro valor se pierde. Una entrada cuyo DN no coincide con
ninguna palabra clave conserva su DN completo como nombre de módulo.

La lista completa de nombres, incluida la palabra clave del DN que produce cada
uno, está en [Catálogo de módulos](#catalogo-de-modulos).

## Operar y resolver problemas

- Ejecute el plugin de forma periódica desde el servidor de plugins, o desde un
  agente de Pandora FMS en modo plugin de agente. Cada ejecución consulta el
  directorio una vez; no hay caché ni estado que reiniciar.
- En el modo archivo de datos el nombre del archivo incluye el segundo epoch de
  la ejecución. Dos ejecuciones del mismo agente dentro del mismo segundo
  colisionan: la segunda informa de
  `ERROR - Could not write file: [Errno 17] File exists: ... please check directory permissions`
  y termina con estado de salida 1. El mensaje habla de permisos, pero la causa
  real es el archivo existente.
- En el modo Tentacle el plugin imprime `1` y termina con estado 0 aunque el
  cliente falle. El fallo aparece en la salida de error estándar como
  `Tentacle error`, y el archivo de datos se conserva en lugar de eliminarse,
  así que puede enviarse de nuevo.
- **`KeyError: 'cn=Operations,cn=Monitor'` y ninguna salida.** Es la limitación
  del paquete actual. El plugin busca en `cn=Monitor` solicitando solo el
  atributo `monitorCounter`, mientras que los totales y los módulos de
  operaciones por tipo se construyen a partir de `monitorOpInitiated` y
  `monitorOpCompleted`. Un directorio devuelve solo los atributos solicitados,
  así que esos valores quedan vacíos y la ejecución se detiene antes de
  construir o entregar ningún módulo. El plugin no tiene ninguna opción que
  cambie los atributos solicitados, y la ejecución termina con estado de salida
  1.
- **`Your username or password is incorrect.`** El enlace fue rechazado. El
  plugin imprime el mensaje y termina con estado 0, y no entrega nada, así que
  un planificador puede registrar la ejecución como correcta. Compruebe el DN de
  enlace, la contraseña y el estado de la cuenta.
- **`AttributeError: type object 'LDAPError' has no attribute 'message'` en una
  traza.** El enlace falló por un motivo distinto de credenciales no válidas,
  por ejemplo un servidor inaccesible o una conexión rechazada, y el propio
  gestor de errores falla. El estado de salida es 1. Compruebe que el host
  resuelve la URL de `-s` y que el listener LDAP es accesible.
- **`error: argument -g/--group: expected one argument`** o el mismo mensaje
  para `--data_dir`: la macro que alimenta la opción está vacía en la cadena de
  parámetros de la consola. Rellénela o edite la cadena de parámetros.
- **`JSONDecodeError` al leer el árbol de monitorización.** Un valor de
  `monitorCounter` o de operación no es numérico y el plugin no puede
  interpretarlo. Revise la entrada que indica la traza.
- **Falta un módulo o muestra el valor de otro contador.** Varias entradas de
  monitorización pueden compartir una palabra clave del DN y, por tanto, un
  nombre de módulo. Consulte [Módulos generados](#modulos-generados).

## Referencia

### Opciones de línea de comandos

```text
pandora_ldap -s <server> -b <binddn> -p <password> -a <agent> [options]
```

| Opción | Valor por defecto | Obligatoria | Descripción |
|--------|-------------------|-------------|-------------|
| `-s`, `--server` | — | Sí | URL LDAP con esquema y puerto, por ejemplo `ldap://<TARGET_HOST>:389` o `ldaps://<TARGET_HOST>:636` |
| `-b`, `--binddn` | — | Sí | DN de la cuenta que se enlaza al directorio |
| `-p`, `--password` | — | Sí | Contraseña de la cuenta de enlace |
| `-a`, `--agent` | — | Sí | Nombre del agente que crea o actualiza el documento |
| `--as_agent_plugin` | `0` | No | `1` imprime el XML de módulos en la salida estándar; cualquier otro entero escribe el archivo de datos |
| `--tentacle_address` | ninguno | No | Dirección del servidor de Tentacle. Si se indica, la entrega usa Tentacle y tiene prioridad sobre `--as_agent_plugin` |
| `--tentacle_port` | `41121` | No | Puerto del servidor de Tentacle, usado solo con `--tentacle_address` |
| `-m`, `--module_prefix` | vacío | No | Texto que se antepone a todos los nombres de módulo. No se expone como macro de consola |
| `-g`, `--group` | `ldap` | No | Grupo de destino del agente generado |
| `--data_dir` | `/var/spool/pandora/data_in/` | No | Directorio donde se escribe el archivo de datos |
| `-h`, `--help` | — | No | Imprime el uso y termina |

### Macros de la consola

El paquete registra siete macros. Todas son valores de texto de una sola línea.

| Macro | Opción | Tipo | Valor por defecto en el paquete | Obligatoria | Oculta | Descripción |
|-------|--------|------|---------------------------------|-------------|--------|-------------|
| `_field1_` | `-s` | texto | vacío | Sí | No | URL LDAP con el puerto |
| `_field2_` | `-b` | texto | vacío | Sí | No | DN de enlace |
| `_field3_` | `-p` | texto | vacío | Sí | No | Contraseña de enlace. El paquete define `hide = 0`; active **Hide value** |
| `_field4_` | `-a` | texto | vacío | Sí | No | Nombre del agente |
| `_field5_` | `--as_agent_plugin` | texto | `0` | No | No | `0` escribe el archivo de datos; `1` imprime el XML de módulos |
| `_field6_` | `-g` | texto | vacío | No | No | Grupo de destino. En la práctica hay que rellenarla: véase abajo |
| `_field7_` | `--data_dir` | texto | vacío | No | No | Directorio de datos. En la práctica hay que rellenarla: véase abajo |

La cadena de parámetros siempre pasa `-g _field6_` y `--data_dir _field7_`. Un
valor vacío en cualquiera de las dos macros deja la opción sin valor y la
ejecución termina con `error: argument ...: expected one argument`. Rellene
ambas macros, o quite las opciones de la cadena de parámetros y deje que se
apliquen los valores por defecto del ejecutable (`ldap` y
`/var/spool/pandora/data_in/`).

`-m`, `--tentacle_address` y `--tentacle_port` no tienen macro en el paquete;
solo están disponibles cuando el plugin se ejecuta desde la línea de comandos o
cuando se edita la cadena de parámetros.

### Catálogo de módulos

`<prefix>` es el valor de `-m`. `<DN>` es un DN de entrada de monitorización que
no coincide con ninguna palabra clave.

| Nombre del módulo | Tipo | Origen |
|-------------------|------|--------|
| `<prefix>Response time` | `generic_data`, unidad `s` | Duración del enlace |
| `<prefix>active operations` | `generic_data` | Entrada agregada `cn=Operations,cn=Monitor`: iniciadas menos completadas |
| `<prefix>operations/sec` | `generic_data_inc` | Entrada agregada `cn=Operations,cn=Monitor`: total iniciado |
| `<prefix>authentications/sec` | `generic_data_inc` | Entrada `Bind`: total iniciado |
| `<prefix>Max Descriptor connections` | `generic_data` | Cualquier entrada con `monitorCounter` cuyo DN contenga `Max` |
| `<prefix>Total connections` | `generic_data` | Cualquier entrada con `monitorCounter` cuyo DN contenga `Total` |
| `<prefix>Current connections` | `generic_data` | Cualquier entrada con `monitorCounter` cuyo DN contenga `Current` |
| `<prefix>Bytes statics` | `generic_data` | Cualquier entrada con `monitorCounter` cuyo DN contenga `Bytes` |
| `<prefix>PDU statics` | `generic_data` | Cualquier entrada con `monitorCounter` cuyo DN contenga `PDU` |
| `<prefix>Entries statics` | `generic_data` | Cualquier entrada con `monitorCounter` cuyo DN contenga `Entries` |
| `<prefix>Referrals statics` | `generic_data` | Cualquier entrada con `monitorCounter` cuyo DN contenga `Referrals` |
| `<prefix>Read waiters` | `generic_data` | Cualquier entrada con `monitorCounter` cuyo DN contenga `Read` |
| `<prefix>Write waiters` | `generic_data` | Cualquier entrada con `monitorCounter` cuyo DN contenga `Write` |
| `<prefix><DN>` | `generic_data` | Una entrada con `monitorCounter` que no coincide con ninguna palabra clave |
| `<prefix><operation>initiated` | `generic_data` | `monitorOpInitiated` de una entrada de operación |
| `<prefix><operation>completed` | `generic_data` | `monitorOpCompleted` de una entrada de operación |

Las entradas de operación se renombran a partir de su DN con estos nombres, en
este orden de evaluación:

| El DN contiene | `<operation>` |
|----------------|---------------|
| `Bind` | `Bind operations` |
| `Unbind` | `Unbind Operations` |
| `Search` | `Search operations` |
| `Compare` | `Compare operations` |
| `Modify` | `Modify operations` |
| `Modrdn` | `Modrdn` |
| `Add` | `Add operations` |
| `Delete` | `Delete operations` |
| `Abandon` | `Abandon operations` |
| `Extended` | `Extended operations` |
| ninguno de ellos | El DN completo, por ejemplo `cn=Operations,cn=Monitor` |

El sufijo se añade sin espacio: `Bind operationsinitiated`,
`Bind operationscompleted`, `cn=Operations,cn=Monitorinitiated`.

### Archivo de salida

En los modos archivo de datos y Tentacle el plugin escribe un archivo por
ejecución:

```text
<data_dir>/<agent_name>.<epoch>.data
```

El archivo contiene un documento `agent_data` con los atributos de
[Agente generado](#agente-generado) y un bloque `<module>` por módulo. El plugin
crea el archivo en exclusiva: una segunda ejecución del mismo agente dentro del
mismo segundo falla en lugar de sobrescribir el primero. En el modo Tentacle el
archivo se elimina tras una transferencia correcta y se conserva cuando la
transferencia falla.

### Identidad del addon

| Propiedad | Valor |
|-----------|-------|
| Identificador del Marketplace | `pandorafms.pandoraldap` |
| Nombre | Pandora LDAP |
| Versión | `1.1` |
| Versión que informa la ayuda del plugin | `050821` |
| Licencia | One |
| Disponibilidad | Descarga limitada a usuarios con licencia |
| Última actualización en el Marketplace | 2025-10-01 |
| Autor (Marketplace) | Pandora FMS |
