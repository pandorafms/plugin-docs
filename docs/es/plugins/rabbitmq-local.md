# RabbitMQ Local monitoring plugin

*Última actualización del artículo: 2026-10-19.*

## Qué hace

El plugin `rabbitmq-local` monitoriza el estado de un clúster de
RabbitMQ desde Pandora FMS. Cada ejecución consulta la API HTTP de gestión de
RabbitMQ y convierte el resultado en módulos de Pandora FMS: totales del
clúster, métricas de recursos por nodo, actividad de los exchanges, contadores
de conexiones y una comprobación de disponibilidad.

El plugin admite dos modelos de ejecución:

- **Modo plugin de servidor** (por defecto; se selecciona cuando
  `as_agent_plugin` está ausente, es `0` o está vacío): cada ejecución
  construye un documento `agent_data` y lo entrega a Pandora FMS mediante
  Tentacle o mediante una carpeta de datos local.
- **Modo plugin de agente** (requiere `as_agent_plugin=1` explícito): cada
  ejecución imprime los módulos generados como XML en la salida estándar,
  para que los ingiera el agente de Pandora FMS.

## Preparación

### Compatibilidad y disponibilidad

El plugin se ha validado en Rocky Linux 9 contra un bróker RabbitMQ 3.13.7 con
el plugin de gestión habilitado. El bróker debe exponer su API HTTP de gestión
en el puerto de gestión — `15672` por defecto en RabbitMQ — y la máquina que
ejecuta el plugin debe poder alcanzarla. El plugin no añade ningún puerto por
defecto: incluya el puerto de gestión en `host` (consulte
[Configuración](#configuracion)).

### Requisitos

1. **Un bróker RabbitMQ con el plugin de gestión habilitado.**
2. **Un usuario de RabbitMQ con permiso para consultar la API de gestión.**
3. **Una instalación de Pandora FMS** que reciba la salida del plugin: el
   servidor de Pandora FMS cuando se ejecuta en modo servidor, o el endpoint
   monitorizado cuando se ejecuta en modo plugin de agente.
4. **El cliente de Tentacle (`tentacle_client`) disponible en el `PATH`**, solo
   cuando el modo servidor entrega mediante Tentacle.

### Instalar el plugin

El plugin se distribuye como el ejecutable `rabbitmq-local` y su archivo de
configuración `rabbitmq-local.conf`. Copie ambos archivos a la máquina que
vaya a ejecutar el plugin. El archivo de configuración es opcional: cuando se
usa, se pasa al ejecutable como su único argumento posicional.

## Configuración

El plugin combina tres fuentes de configuración, en orden creciente de
precedencia:

```text
valores por defecto < archivo de configuración < opciones de línea de comandos
```

El archivo de configuración es opcional. Cuando se usa, debe ser el único
argumento posicional: el primer argumento de la línea de comandos que no
empieza por `-`, y ningún otro. Es un archivo de texto plano con líneas
`key=value`. Cada clave puede pasarse también como opción de línea de
comandos, en cualquiera de estas cuatro formas:

```text
-key value    --key value    -key=value    --key=value
```

Las claves y las opciones son literales y se escriben siempre en inglés: se
copian tal cual.

Las opciones sustituyen los valores del archivo, de modo que un archivo
compartido puede contener la configuración común y cada ejecución sustituir lo
que necesite. La configuración se valida de forma estricta: una opción
desconocida, una opción sin valor al final de la línea de comandos y un
segundo argumento posicional son errores de configuración que se informan por
la salida de error estándar con estado de salida 1.

El modo plugin de servidor es el modo por defecto y necesita un nombre de
agente y un destino de entrega. Esta es la configuración mínima para una
ejecución como plugin de servidor con Tentacle:

```ini
host=<RABBITMQ_HOST>:<MANAGEMENT_PORT>
user=<RABBITMQ_USER>
pass=<RABBITMQ_PASSWORD>
agent_name=rabbitmq-local
interval=300
transfer_mode=tentacle
tentacle_ip=<PANDORA_FMS_SERVER>
tentacle_port=41121
```

O copie el XML generado a una carpeta de datos local:

```ini
host=<RABBITMQ_HOST>:<MANAGEMENT_PORT>
user=<RABBITMQ_USER>
pass=<RABBITMQ_PASSWORD>
agent_name=rabbitmq-local
transfer_mode=local
local_folder=/var/spool/pandora/data_in
```

El modo plugin de agente requiere `as_agent_plugin=1` explícito. Esta es la
configuración mínima para una ejecución como plugin de agente:

```ini
host=<RABBITMQ_HOST>:<MANAGEMENT_PORT>
user=<RABBITMQ_USER>
pass=<RABBITMQ_PASSWORD>
as_agent_plugin=1
```

La misma configuración de plugin de agente solo con opciones, sin archivo de
configuración:

```bash
./rabbitmq-local -host <RABBITMQ_HOST>:<MANAGEMENT_PORT> -user <RABBITMQ_USER> -pass <RABBITMQ_PASSWORD> -as_agent_plugin 1
```

Las credenciales también pueden leerse de un archivo aparte, de modo que ni el
usuario ni la contraseña aparecen en la línea de comandos ni en la lista de
procesos del sistema operativo:

```bash
# Credenciales leídas de un archivo (legible solo por el usuario del plugin).
./rabbitmq-local -host <RABBITMQ_HOST>:<MANAGEMENT_PORT> \
    -cred_file /etc/pandora/plugins/rabbitmq-local.creds -as_agent_plugin 1
```

El archivo de credenciales usa líneas `key=value`:

```ini
user=<RABBITMQ_USER>
pass=<RABBITMQ_PASSWORD>
```

Las claves `agent_name`, `interval`, `transfer_mode`, `local_folder` y
`tentacle_*` son exclusivas del modo servidor: se ignoran mientras el plugin
se ejecuta en modo plugin de agente. La misma ejecución en modo servidor con
opciones, sustituyendo los valores del archivo:

```bash
./rabbitmq-local rabbitmq-local.conf -agent_name rabbitmq-local \
    -transfer_mode tentacle -tentacle_ip <PANDORA_FMS_SERVER>
```

Puntos clave:

- `host` admite `host`, `host:port`, `http://host:port` o `https://host:port`;
  cuando no se indica esquema, el plugin consulta `http://<host>`. El plugin no
  añade ningún puerto por defecto: un `host` sin puerto usa el puerto por
  defecto del esquema (`80` para HTTP, `443` para HTTPS), así que incluya el
  puerto de gestión — `15672` es el valor por defecto de RabbitMQ — salvo que un
  proxy sirva la API en el puerto por defecto del esquema.
- `ca_file` apunta a un bundle PEM con la CA que firma el certificado de la API
  de gestión. Solo se usa con un host `https`; sin él, HTTPS verifica contra el
  almacén de confianza del sistema.
- Las credenciales pueden indicarse en línea (`user` y `pass`) o en un archivo
  `key=value` aparte (`cred_file`) con las líneas `user` y `pass`. Cuando
  `cred_file` está definido — en el archivo de configuración o como opción —
  tiene precedencia sobre `user` y `pass`. Un archivo ilegible, o un archivo
  sin `user` o sin `pass`, es un error.
- En modo servidor, `agent_name` da nombre al agente creado en Pandora FMS e
  `interval` es el intervalo del agente en segundos.
- El modo de transferencia es Tentacle solo cuando
  `transfer_mode=tentacle`; cualquier otro valor, incluido el valor por
  defecto, copia el XML en `local_folder`.
- Las opciones de línea de comandos sustituyen los valores del archivo, por
  ejemplo `./rabbitmq-local rabbitmq-local.conf -interval 60`.
- El archivo `rabbitmq-local.conf` distribuido activa `as_agent_plugin=1` y
  deja las claves del modo servidor comentadas, por lo que arranca en modo
  plugin de agente tal cual.

### Credenciales y transporte

- Prefiera HTTPS: con un host `https://` las credenciales y las métricas
  recopiladas viajan cifradas. Con HTTP sin cifrar viajan sin protección, así
  que restrinja la API de gestión a una red de confianza o sitúe un proxy TLS
  por delante.
- HTTPS verifica el certificado del servidor contra el almacén de confianza del
  sistema, o contra el bundle `ca_file` cuando se configura.
- La contraseña en línea (`pass`) se almacena en el archivo de configuración en
  texto plano: restrinja los permisos del archivo al usuario que ejecuta el
  plugin.
- Evite `-pass` en la línea de comandos: el comando queda en el historial del
  shell y la lista de procesos del sistema operativo puede exponerla mientras
  el plugin se ejecuta. Use `-cred_file` con un archivo de credenciales legible
  solo por el usuario del plugin (por ejemplo `chmod 600`).
- El archivo de credenciales también se guarda en texto plano: su protección es
  el modelo de permisos del sistema de archivos, así que manténgalo propiedad
  del usuario del plugin y sin acceso para nadie más.

### Registrar el plugin en la consola

El plugin también puede registrarse en la consola de Pandora FMS como plugin de
servidor, de modo que Pandora FMS lo ejecute en el servidor que ejecuta los
módulos — el servidor principal o un servidor remoto — en lugar de en una línea
de comandos. Registrado así, el plugin mantiene su modo servidor: cada
ejecución construye el XML del agente y lo entrega, y el agente con sus módulos
aparece en la consola.

1. Abra **Servers → Plugins** y haga clic en **Register Plugin**.
2. Indique el nombre, el tipo de plugin **Standard**, un tiempo de espera
   máximo opcional y una descripción.
3. En **Plugin command**, escriba la ruta al ejecutable `rabbitmq-local` en el
   servidor de Pandora FMS, por ejemplo
   `/usr/share/pandora_server/util/plugin/rabbitmq-local`.
4. En **Plugin parameters**, mantenga el modo servidor (sin la clave
   `as_agent_plugin`) y use las macros del plugin `_field1_`, `_field2_`, ...
   como marcadores:

```text
-host _field1_ -user _field2_ -pass _field3_ -agent_name _field4_ -transfer_mode tentacle -tentacle_ip 127.0.0.1
```

5. En **Macro parameters**, describa cada campo. El ejemplo usa estos valores:

| Campo | Descripción | Valor de ejemplo |
| --- | --- | --- |
| `_field1_` | Host de la API de gestión, incluido el puerto | `http://rabbit.example.com:15672` |
| `_field2_` | Usuario de RabbitMQ con permiso para consultar la API de gestión | `monitoring` |
| `_field3_` | Contraseña de ese usuario; marque **Hide value** | — |
| `_field4_` | Nombre del agente que contendrá los módulos en la consola | `RabbitMQ-remote-agent` |

![Registro del plugin RabbitMQ Local como plugin de servidor en la consola de Pandora FMS](../assets/images/plugins/rabbitmq-local/plugin-registration.png)

`-transfer_mode tentacle -tentacle_ip 127.0.0.1` entrega el agente al servidor
de Tentacle de la máquina que ejecuta el plugin, de modo que el agente llega al
servidor de Pandora FMS que ejecuta el módulo. Para copiar el XML a una carpeta
de datos local, sustituya esas opciones por
`-transfer_mode local -local_folder /var/spool/pandora/data_in`.

Una vez registrado, el plugin está disponible al crear módulos de plugin, y
cada módulo rellena sus campos de forma individual. El módulo se ejecuta en el
servidor seleccionado para él, incluido un servidor remoto de Pandora FMS, de
modo que cada bróker se monitoriza desde el servidor de Pandora FMS más cercano
sin instalar nada en la máquina del bróker. El mismo plugin registrado sirve
para varias instancias de RabbitMQ, y los valores de los campos pueden usar las
macros de Pandora FMS documentadas en la ayuda *Plug-in macros* de la consola.

![Campos del plugin al crear un módulo](../assets/images/plugins/rabbitmq-local/module-plugin-fields.png)

Los parámetros registrados pueden incluir también `-cred_file` — con una ruta
fija o como campo — para que los módulos lean las credenciales de un archivo en
el servidor de Pandora FMS en lugar de guardarlas en los campos del módulo. Los
parámetros también pueden apuntar a un archivo de configuración del servidor —
una ruta literal o un campo `_fieldN_` — de modo que el archivo aporte la
configuración compartida.

## Verificación

Ejecute el plugin manualmente desde una terminal, pasando el archivo de
configuración como su único argumento posicional:

```bash
./rabbitmq-local /etc/pandora/plugins/rabbitmq-local.conf
```

La forma relativa `./rabbitmq-local rabbitmq-local.conf` funciona si la
terminal ya está situada en el directorio que contiene ambos archivos. Cada
ejecución se realiza una vez y termina.

El plugin imprime su resumen de uso (todos los parámetros y cinco ejemplos)
con `./rabbitmq-local -h`.

En modo plugin de agente, una ejecución correcta imprime un bloque XML
`<module>` por cada módulo generado en la salida estándar. El ejemplo muestra
un fragmento de una ejecución contra un clúster de un solo nodo:

```xml
<module>
  <name><![CDATA[Cluster name]]></name>
  <type>generic_data_string</type>
  <data><![CDATA[rabbit@node01]]></data>
</module>
<module>
  <name><![CDATA[Total queue messages]]></name>
  <type>generic_data</type>
  <data><![CDATA[12]]></data>
</module>
<module>
  <name><![CDATA[Availability]]></name>
  <type>generic_proc</type>
  <data><![CDATA[1]]></data>
  <description><![CDATA[Rabbit MQ API availability]]></description>
</module>
<module>
  <name><![CDATA[Memory used - rabbit@node01]]></name>
  <type>generic_data</type>
  <data><![CDATA[174895104]]></data>
  <description><![CDATA[Usually in bytes. Represents the total memory that the RabbitMQ node is using at that instant.]]></description>
</module>
```

En modo servidor, una ejecución correcta imprime `1 ` y el agente configurado
en `agent_name` aparece en Pandora FMS con sus módulos. Si la ejecución no
genera módulos, consulte
[Operar y resolver problemas](#operar-y-resolver-problemas).

![Los módulos del agente RabbitMQ en la consola de Pandora FMS](../assets/images/plugins/rabbitmq-local/console-modules.png)

## Entender los resultados

El plugin genera el mismo catálogo de módulos en ambos modelos de ejecución.
Los módulos cubren cinco grupos:

- **Nivel de clúster.** `Cluster name`, `Total queue messages`,
  `Messages unacknowledged`, `Total exchanges` y los módulos
  `Queue publish rate`, `Queue deliver get rate` y
  `Queue deliver noack rate` informan de los totales y las tasas de todo el
  clúster.
- **Nivel de nodo.** Para cada nodo del clúster, `Memory used - <node>` y
  `Memory rate - <node>` informan de su consumo de memoria, `Proc used - <node>`
  y `Proc details - <node>` de sus procesos Erlang, y `Node status - <node>` de
  si el nodo está en ejecución.
- **Nivel de exchange.** `Exchanges in rate` y `Exchanges out rate` informan de
  la tasa de publicación de entrada y de salida del último exchange que
  reporta actividad; cuando ningún exchange reporta una tasa, ambos módulos
  informan de `0`.
- **Nivel de conexión.** `Total connections`, `Connections running` y
  `Connections blocked` cuentan las conexiones abiertas, y
  `Total received octets` y `Total sent octets` suman sus tasas de octetos
  recibidos y enviados.
- **Disponibilidad.** `Availability` vale `1` cuando la petición de resumen del
  clúster tiene éxito y `0` en caso contrario.

Cuando no se puede alcanzar la API de gestión — credenciales incorrectas,
problema de red, plugin de gestión deshabilitado — `Availability` informa de
`0`, los módulos de nodo se omiten de la salida y los módulos de exchange y de
conexión informan de `0`.

## Operar y resolver problemas

- El plugin no guarda estado entre ejecuciones: cada ejecución consulta el
  bróker en ese momento, por lo que puede ejecutarse manualmente en cualquier
  instante.
- En modo servidor, programe el plugin desde Pandora FMS (por ejemplo, mediante
  el planificador de plugins del servidor o `cron`) y use `interval` para
  ajustar el intervalo del agente. En modo plugin de agente, el agente de
  Pandora FMS lo ejecuta según la planificación configurada para el plugin.
- **`Availability` informa de `0`** — la petición de resumen del clúster ha
  fallado. Compruebe que el plugin de gestión está habilitado, que `host`
  indica el puerto de gestión y que las credenciales pueden consultar la API de
  gestión. Con un host `https`, compruebe además que el certificado del
  servidor verifica: apunte `ca_file` al bundle de la CA cuando la API use un
  certificado privado.
- **No se imprime XML de módulos** — ejecutar sin ningún argumento, o con
  `-h`/`--help`, imprime el resumen de uso y se detiene en lugar de generar
  módulos. Ejecute el plugin con las opciones de configuración o con la ruta
  de un archivo de configuración existente. Cuando a la configuración le falta
  un valor obligatorio (`host`, `user`, la contraseña de cualquiera de sus
  fuentes, `agent_name` en modo servidor, `tentacle_ip` para la entrega por
  Tentacle o `local_folder` en caso contrario), el plugin imprime el error y un
  aviso que apunta a `-h` sin generar módulos.
- **El plugin termina con `cannot read cred_file`, `cred_file ... is missing
  user` o `cred_file ... is missing pass`** — el archivo de credenciales debe
  existir, ser legible por el usuario del plugin y definir tanto `user` como
  `pass`. Corrija el archivo o vuelva a las credenciales en línea (`user` y
  `pass`).
- **No aparecen módulos de nodo** mientras `Availability` informa de `1` — la
  petición de nodos ha fallado; el resto de módulos del clúster se siguen
  generando. Repita la ejecución y compruebe la lista de nodos del bróker.
- **El modo servidor no imprime `1 `** — la entrega ha fallado. Compruebe que
  `tentacle_client` está disponible y puede alcanzar
  `tentacle_ip:tentacle_port`, o que `local_folder` existe y tiene permisos de
  escritura.
- **Los datos parecen obsoletos en Pandora FMS** — el plugin siempre informa de
  los valores que el bróker devuelve en el momento de la ejecución; compruebe
  el propio bróker y la planificación de ejecución.

## Referencia

### Archivo de configuración

El archivo de configuración es opcional: sin él, el plugin se ejecuta con los
valores por defecto más las opciones.

| Nombre | Obligatorio | Valor por defecto | Descripción |
| --- | --- | --- | --- |
| `host` | Sí | — | Host de la API de gestión, en forma `host`, `host:port`, `http://host:port` o `https://host:port`. HTTP es el valor por defecto. Incluya el puerto de gestión: no se añade ningún puerto por defecto. |
| `ca_file` | No | — | Bundle PEM con la CA que firma el certificado de la API de gestión (solo se usa con un host `https`). |
| `user` | Sí, salvo que se defina `cred_file` | — | Usuario de RabbitMQ con permiso para consultar la API de gestión. |
| `pass` | Sí, salvo que se defina `cred_file` | — | Contraseña de `user`. |
| `cred_file` | No | — | Archivo con las credenciales en líneas `key=value` (`user` y `pass`), con el mismo formato que el archivo de configuración. Cuando se define, tiene precedencia sobre `user` y `pass`. Use una ruta absoluta legible solo por el usuario del plugin. Un archivo ilegible, o un archivo sin `user` o sin `pass`, es un error. |
| `agent_name` | Obligatorio en modo servidor | — | Exclusivo del modo servidor. Nombre del agente creado en Pandora FMS. |
| `interval` | No | `300` | Exclusivo del modo servidor. Intervalo del agente en segundos. |
| `as_agent_plugin` | No | `0` (plugin de servidor) | `1` (o cualquier valor distinto de `0`) imprime el XML de módulos en la salida estándar; `0` (o un valor vacío) construye y entrega un agente. |
| `tmp` | No | Carpeta temporal del sistema | Carpeta donde se escribe el documento XML antes de la entrega. |
| `transfer_mode` | Condicional | Vacío (copia local) | Exclusivo del modo servidor. `tentacle` entrega con el cliente de Tentacle; cualquier otro valor, incluido el valor por defecto, copia el XML en `local_folder`. |
| `local_folder` | Obligatorio cuando no se usa Tentacle | — | Exclusivo del modo servidor. Carpeta de destino de la copia del XML. |
| `tentacle_ip` | Obligatorio cuando `transfer_mode=tentacle` | — | Exclusivo del modo servidor. Dirección del servidor de Tentacle. |
| `tentacle_port` | No | `41121` | Exclusivo del modo servidor. Puerto del servidor de Tentacle. |
| `tentacle_opts` | No | Vacío | Exclusivo del modo servidor. Opciones adicionales que se pasan al cliente de Tentacle, separadas por espacios. |

El archivo usa líneas `key=value`. Las líneas en blanco y las que empiezan
por `#` se omiten, las claves y los valores se recortan, y la última aparición
de una clave repetida prevalece.

Cuando `cred_file` está definido — en el archivo de configuración o en la línea
de comandos — las credenciales se leen de ese archivo y se usan en lugar de
`user` y `pass`.

### Ejecución por línea de comandos

```bash
./rabbitmq-local [archivo-de-configuración] [ -key value ... ]
```

| Condición | Comportamiento |
| --- | --- |
| La línea de comandos está vacía | El plugin imprime el resumen de uso y se detiene |
| No hay argumento posicional, pero sí opciones | El plugin se ejecuta con los valores por defecto más las opciones |
| El argumento posicional nombra un archivo existente | El plugin se ejecuta con la configuración del archivo, sustituida por las opciones |
| El argumento posicional nombra un archivo que no existe | El plugin informa del error por la salida de error estándar y sale con estado 1 |
| `-key value`, `--key value`, `-key=value` o `--key=value` | Cada opción sustituye el valor de la misma clave del archivo o de los valores por defecto |
| `-h` o `--help` en cualquier posición de la línea de comandos | El plugin imprime el resumen de uso y se detiene |
| Una opción desconocida, una opción sin valor o un segundo argumento posicional | El plugin informa del error por la salida de error estándar y sale con estado 1 |

Las opciones pueden aparecer antes o después de la ruta del archivo de
configuración.

### Módulos generados

En los nombres siguientes, `<node>` es el nombre de un nodo del clúster:

| Nombre del módulo | Tipo | Significado |
| --- | --- | --- |
| `Cluster name` | `generic_data_string` | Nombre del clúster informado por el bróker |
| `Total queue messages` | `generic_data` | Total de mensajes en todas las colas |
| `Messages unacknowledged` | `generic_data` | Total de mensajes entregados pero no confirmados |
| `Total exchanges` | `generic_data` | Número total de exchanges |
| `Queue publish rate` | `generic_data` | Tasa de publicación del clúster |
| `Queue deliver get rate` | `generic_data` | Tasa de mensajes obtenidos directamente de las colas |
| `Queue deliver noack rate` | `generic_data` | Tasa de mensajes entregados a consumidores sin confirmación |
| `Availability` | `generic_proc` | `1` cuando la petición de resumen del clúster tiene éxito, `0` en caso contrario |
| `Memory used - <node>` | `generic_data` | Memoria usada por el nodo, en bytes |
| `Memory rate - <node>` | `generic_data` | Tasa a la que se consume o libera la memoria del nodo |
| `Proc used - <node>` | `generic_data` | Procesos Erlang usados por el nodo |
| `Proc details - <node>` | `generic_data` | Tasa a la que se crean o terminan los procesos Erlang del nodo |
| `Node status - <node>` | `generic_proc` | `1` mientras el nodo está en ejecución, `0` en caso contrario |
| `Exchanges in rate` | `generic_data` | Tasa de publicación de entrada del último exchange que la informa; `0` cuando ninguno reporta actividad |
| `Exchanges out rate` | `generic_data` | Tasa de publicación de salida del último exchange que la informa; `0` cuando ninguno reporta actividad |
| `Total connections` | `generic_data` | Número de conexiones de cliente abiertas |
| `Connections running` | `generic_data` | Conexiones en estado running |
| `Connections blocked` | `generic_data` | Conexiones que no están en estado running |
| `Total received octets` | `generic_data` | Suma de la tasa de octetos recibidos de todas las conexiones |
| `Total sent octets` | `generic_data` | Suma de la tasa de octetos enviados de todas las conexiones |
