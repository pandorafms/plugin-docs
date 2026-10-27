# Plugin de monitorización de Kafka

*Última actualización del artículo: 2026-10-26.*

## Qué hace

El plugin de monitorización de Kafka recoge las métricas de rendimiento de un
cliente de Kafka y las publica como módulos de Pandora FMS. En cada ejecución
crea un productor y un consumidor contra un endpoint de Kafka, toma una
instantánea de las métricas que ambos clientes informan y escribe el resultado
en un agente de Pandora FMS.

El plugin es un **plugin de servidor**: lo ejecuta el Plugin Server de Pandora
FMS y cada ejecución entrega el XML del agente a Pandora FMS mediante Tentacle o
en un directorio de datos local. No se instala nada en el broker de Kafka.

Lo que mide el plugin tiene tres consecuencias que conviene conocer antes de
configurarlo:

- **No lee métricas JMX del broker de Kafka.** Los módulos describen los
  clientes productor y consumidor que crea el propio plugin, no los productores
  y consumidores de sus aplicaciones ni los MBeans del broker.
- **No envía ni consume registros.** El plugin crea ambos clientes,
  opcionalmente suscribe el consumidor a topics, lee la instantánea de métricas
  y los cierra. No hace `poll` del consumidor y no confirma ningún offset.
- **Crea un agente por cada entrada de `--bootstrap_servers`.** Dos endpoints
  procesados correctamente producen dos agentes, aunque ambos apunten al mismo
  clúster.

El plugin imprime `1` cuando procesa todos los endpoints sin una excepción y `0`
cuando alguno provoca una. Ese valor impreso es el que recibe un módulo de
plugin de Pandora FMS. Un broker al que no se puede llegar hace que la ejecución
imprima `0`; el valor no demuestra que el agente generado se haya entregado, así
que verifique la entrega por separado (consulte [Verificación](#verificacion)).

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
|--------|--------|-----------|
| Addon `pandorafms.apache_kafka`, versión `1.1` | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del addon](#identidad-del-addon) |
| Pandora FMS NG 784 y posteriores | `Soportado` | El Marketplace indica que todas las integraciones son compatibles con Pandora FMS NG 784 y versiones posteriores. Es una declaración de catálogo que cubre el addon, no un registro de prueba del mismo |
| Un listener de Kafka accesible por TCP desde el servidor de Pandora FMS | `Requerido` | El plugin se conecta a cada endpoint indicado en `--bootstrap_servers` |
| Un listener que acepte conexiones PLAINTEXT sin autenticación | `Requerido` | El addon no expone opciones de autenticación SASL ni de TLS, así que solo puede usar la configuración de conexión predeterminada del cliente de Kafka |
| Rocky Linux | `Compatible conocido` | La guía antigua de este addon registra Rocky Linux como el sistema donde se probó. No se ha revalidado para la versión `1.1` |
| Otras distribuciones de Linux | `Sin validar` | No se ha registrado un rango de distribuciones ni una matriz de versiones para este addon |
| Versiones de broker de Kafka | `Sin validar` | No se ha registrado una matriz de versiones de broker para este addon |
| `tentacle_client` en `PATH` | `Requerido` cuando `--transfer_mode` no es `local` | La entrega por Tentacle ejecuta ese comando |
| Permiso de escritura en `/tmp` | `Requerido` | El plugin prepara el XML generado en `/tmp` antes de entregarlo |
| Permiso de escritura en `/var/spool/pandora/data_in/` | `Requerido` cuando se usa `--transfer_mode local` | El documento XML se mueve a ese directorio |

Ninguna declaración de compatibilidad establece un rango de versiones de Kafka,
una distribución de broker ni una distribución de Linux distinta del registro de
Rocky Linux anterior. Mantenga cada afirmación en el ámbito que demuestra su
fuente.

### Requisitos de Kafka

1. **Un listener de Kafka accesible.** Use la dirección y el puerto del listener
   en `--bootstrap_servers`, por ejemplo `<TARGET_HOST>:9092`. Incluya el puerto
   explícitamente en cada endpoint; el puerto predeterminado del cliente de
   Kafka es `9092`.
2. **Un listener que acepte la conexión predeterminada del cliente.** El addon
   no tiene opciones de `security_protocol`, SASL ni TLS. Un clúster cuyos
   listeners exijan autenticación SASL, certificados de cliente TLS u otro
   protocolo autenticado no se puede monitorizar con esta versión.
3. **Ninguna cuenta de Kafka ni acceso JMX.** El plugin no se autentica, así que
   no necesita un usuario de Kafka, un puerto JMX ni credenciales RMI. Si el
   acceso anónimo al listener está deshabilitado, la conexión falla y la
   ejecución solo lo refleja como un error de procesamiento del broker.

El plugin no lee ni escribe datos de los topics, así que no necesita ninguna ACL
de topic para las aplicaciones que monitoriza. Restrinja el listener a la red del
servidor de Pandora FMS en lugar de abrirlo de forma general.

### Requisitos de Pandora FMS

1. **Pandora FMS con el Plugin Server habilitado** en el servidor que ejecutará
   el plugin.
2. **Un servidor Tentacle** accesible en `--tentacle_ip` y `--tentacle_port`
   cuando se usa la entrega predeterminada por Tentacle, además del comando
   `tentacle_client` en `PATH`.
3. **Un directorio de datos con permiso de escritura** cuando se usa
   `--transfer_mode local`. El plugin mueve el XML a
   `/var/spool/pandora/data_in/`; la opción no permite elegir otro directorio.
4. **Permiso de escritura en `/tmp`** para el usuario que ejecuta el Plugin
   Server. El XML generado se prepara allí antes de la entrega.

### Instalar el plugin

Descargue el addon desde su entrada del Marketplace, cuya descarga está limitada
a usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.apache_kafka](https://marketplace.pandorafms.com/entries/pandorafms.apache_kafka)

Copie el ejecutable `pandora_kafka` al servidor de Pandora FMS y dele permiso de
ejecución. El directorio recomendado para los plugins de servidor es:

```text
/usr/share/pandora_server/util/plugin/
```

```bash
sudo chmod 755 /usr/share/pandora_server/util/plugin/pandora_kafka
```

No se instala nada en el broker de Kafka y el servidor de Kafka no necesita JMX
habilitado.

## Configuración

El plugin no tiene fichero de configuración. Toma todos sus ajustes de la línea
de comandos, partiendo de valores predeterminados integrados:

```text
valores predeterminados integrados < opciones de línea de comandos
```

Todas las opciones están documentadas en
[Parámetros de línea de comandos](#parametros-de-linea-de-comandos). Esta
sección explica las decisiones que cambian lo que mide el plugin y dónde va el
resultado.

### Endpoints

`--bootstrap_servers` es obligatorio y acepta una lista de endpoints de Kafka
separados por comas en formato `host:puerto`:

```text
--bootstrap_servers <KAFKA_HOST_1>:9092,<KAFKA_HOST_2>:9092
```

Cada elemento no vacío se procesa de forma independiente y produce un agente.
Los elementos vacíos entre comas se ignoran. El plugin no crea un agente por
cada broker del clúster: crea un productor y un consumidor por elemento y nombra
el agente con ese elemento.

### Topics

El consumidor puede suscribirse a una lista de topics, a una expresión regular o
a nada:

- `--topics orders,payments` suscribe a los topics indicados.
- `--topic_regex '^prod-.*'` suscribe a los topics que coinciden con el patrón.
- Cuando se indican ambos, `--topic_regex` tiene prioridad y `--topics` se
  ignora.
- Cuando no se indica ninguno, el consumidor se crea sin suscripción.

La suscripción no hace que el plugin lea mensajes. Nunca hace `poll` del
consumidor, así que no consume registros ni confirma offsets. El consumidor usa
el identificador de grupo fijo `monitoring-client` con la confirmación
automática deshabilitada.

Una expresión regular no válida no se rechaza antes de empezar la ejecución: el
error solo se imprime con `--verbose` y después la suscripción falla durante el
procesamiento de ese endpoint, lo que hace que la ejecución imprima `0`. Pruebe
el patrón con `--verbose` antes de registrarlo.

### Prefijos de agentes y módulos

`--agent_prefix` se antepone al nombre y al alias de cada agente generado, y
`--module_prefix` se antepone a cada nombre de módulo generado. Ambos tienen como
valor predeterminado una cadena vacía.

```text
--agent_prefix KAFKA_ --module_prefix METRIC_
```

Con el broker `kafka1:9092`, el agente se llama `KAFKA_kafka1:9092` y el módulo
`producer-metrics.request-rate` pasa a ser
`METRIC_producer-metrics.request-rate`.

### Entrega

La entrega predeterminada es por Tentacle. `--transfer_mode` acepta un único
valor significativo:

| Valor | Comportamiento |
|-------|----------------|
| `tentacle` (predeterminado) | Envía el documento XML con `tentacle_client` a `--tentacle_ip`:`--tentacle_port` |
| `local` | Mueve el documento XML a `/var/spool/pandora/data_in/` |
| Cualquier otro valor, incluida una errata | También usa Tentacle; el plugin solo trata como local el valor exacto `local` |

`--tentacle_ip` tiene como valor predeterminado `127.0.0.1` y `--tentacle_port`
`41121`. Solo los usa la entrega por Tentacle. La entrega local no tiene un
directorio configurable: si el servidor de Pandora FMS no usa
`/var/spool/pandora/data_in/`, use Tentacle en su lugar.

Los fallos de Tentacle se imprimen en la salida de error, pero no cambian el `1`
o el `0` que imprime el plugin. Consulte
[Salida y código de salida](#salida-y-codigo-de-salida).

### Registrar el plugin en la consola

1. Abra **Servidores → Plugins** y pulse **Registrar plugin**.
2. Indique un nombre, el tipo de plugin **Standard**, un tiempo máximo de
   ejecución opcional y una descripción.
3. En **Comando del plugin**, introduzca la ruta completa del ejecutable en el
   servidor de Pandora FMS:
   `/usr/share/pandora_server/util/plugin/pandora_kafka`.
4. En **Parámetros del plugin**, combine el endpoint obligatorio con las
   opciones que necesite, usando las macros de plugin `_field1_`, `_field2_`,
   ... como marcadores de posición:

```text
--bootstrap_servers _field1_ --agent_prefix _field2_ --module_prefix _field3_ --transfer_mode tentacle --tentacle_ip 127.0.0.1 --tentacle_port 41121
```

5. En **Parámetros de macro**, describa cada campo. El ejemplo usa estos
   valores:

| Campo | Descripción | Valor de ejemplo |
|-------|-------------|------------------|
| `_field1_` | Endpoint de Kafka, incluido el puerto; varios endpoints separados por comas | `<KAFKA_HOST>:9092` |
| `_field2_` | Prefijo para los nombres y alias de los agentes generados | `KAFKA_` |
| `_field3_` | Prefijo para los nombres de los módulos generados | `METRIC_` |

<!-- SCREENSHOT NEEDED: Formulario de registro de plugin de servidor en la consola de Pandora FMS con la ruta del comando pandora_kafka y los campos de parámetros, con marcadores de laboratorio y sin hosts reales. -->

Añada `--topics _field4_` o `--topic_regex _field4_` solo cuando quiera una
suscripción. Toda opción que permanezca en la cadena de parámetros debe recibir
un valor: una macro vacía deja la opción sin argumento y el plugin termina con
un error de análisis de argumentos en lugar de ejecutarse. Elimine la opción en
lugar de dejar su campo vacío.

Una vez creado el plugin de servidor, abra un agente, cree un módulo de tipo
**plugin** y seleccione el plugin registrado. Ese módulo recibe el `1` o el `0`
impreso. Las métricas de Kafka no van a ese módulo: llegan en los agentes
separados que crea el plugin.

<!-- SCREENSHOT NEEDED: Formulario de módulo de plugin en la consola de Pandora FMS con el plugin de Kafka seleccionado y sus campos de macro rellenos, sin credenciales ni nombres de host reales. -->

### Seguridad

- El addon no tiene opciones de usuario, contraseña ni token, ni ajustes de SASL
  o TLS. Se conecta con la configuración predeterminada del cliente de Kafka:
  PLAINTEXT sin autenticación.
- Como no hay cifrado de transporte, las métricas y los metadatos de conexión
  viajan en claro entre el servidor de Pandora FMS y el listener de Kafka.
  Restrinja el listener a una red de confianza o no use este addon donde la
  autenticación o el cifrado sean obligatorios.
- El plugin no almacena credenciales, así que no hay ningún secreto que proteger
  en un fichero de configuración. Su línea de comandos solo contiene direcciones
  de broker, prefijos y ajustes de entrega.
- `--verbose` imprime detalles de errores de broker en la salida estándar. Esos
  mensajes pueden incluir direcciones de broker y texto de excepciones, así que
  revíselos antes de compartir una ejecución manual.

## Verificación

Ejecute el plugin manualmente desde un terminal en el servidor de Pandora FMS:

```bash
./pandora_kafka \
  --bootstrap_servers <TARGET_HOST>:9092 \
  --topics <TOPIC> \
  --agent_prefix KAFKA_ \
  --transfer_mode tentacle \
  --tentacle_ip <PANDORA_FMS_SERVER> \
  --tentacle_port 41121 \
  --verbose
```

Una ejecución correcta termina con `1` en la salida estándar. Con entrega por
Tentacle, el agente `KAFKA_<TARGET_HOST>:9092` y sus módulos aparecen en Pandora
FMS tras el siguiente ciclo de procesamiento de datos. Con entrega `local`,
compruebe que se ha movido un fichero `.data` a
`/var/spool/pandora/data_in/` y que el agente aparece después de que el servidor
de datos lo procese.

El valor impreso por sí solo no basta para verificar la integración:

- `1` significa que el plugin creó el productor y el consumidor de todos los
  endpoints y recogió sus métricas sin una excepción. La creación del cliente
  resuelve la versión del broker por la red, así que un broker que rechaza o no
  responde a la conexión produce `0` en su lugar.
- `1` no demuestra la entrega: un fallo de Tentacle se imprime en la salida de
  error pero deja `1` en la salida estándar.

Verifique los datos, no solo la línea final:

1. Confirme que el agente generado existe y que su nombre sigue la regla del
   prefijo.
2. Abra sus módulos y compruebe que las métricas de conexión y peticiones
   informan actividad.
3. Si todos los valores son cero, compruebe la conectividad antes de dar por
   hecho que el plugin entregó correctamente.

<!-- SCREENSHOT NEEDED: Agente de Kafka en la consola de Pandora FMS con los módulos generados y sus valores actuales para un broker de laboratorio. -->

Use `./pandora_kafka -h` para imprimir el resumen de uso, la versión del plugin
y el ejemplo de ejecución.

## Entender los resultados

### Agentes

El plugin crea un agente por cada elemento no vacío de `--bootstrap_servers`
procesado correctamente. Nombre y alias usan el mismo valor:

```text
<agent_prefix><host:puerto>
```

Por ejemplo, con `--agent_prefix KAFKA_` y el endpoint `kafka1:9092`, el agente
es `KAFKA_kafka1:9092`. Todos los agentes generados tienen un intervalo de 300
segundos, la descripción `Created by plugin` y ningún grupo de agentes asignado.

Ejecutar el plugin dos veces con el mismo endpoint actualiza el mismo nombre de
agente. Ejecutarlo con dos endpoints que pertenecen al mismo clúster crea dos
agentes con conjuntos de módulos duplicados.

### Módulos

El plugin recorre todos los grupos y nombres de métricas que informan el
productor y el consumidor. El nombre del módulo es:

```text
<module_prefix><metric_group>.<metric_name>
```

Todos los módulos se crean como `generic_data`, sin unidad y sin descripción. Los
valores de coma flotante que son `NaN`, infinito positivo o infinito negativo se
escriben como `0.0`.

El catálogo exacto depende del estado del cliente de Kafka y de la versión de
Kafka. Los grupos estables y los módulos representativos son:

| Origen | Grupo de métricas | Módulos representativos sin prefijo |
|--------|-------------------|--------------------------------------|
| Productor y consumidor | `kafka-metrics-count` | `kafka-metrics-count.count` |
| Productor | `producer-metrics` | `producer-metrics.connection-count`, `producer-metrics.request-rate`, `producer-metrics.request-latency-avg`, `producer-metrics.outgoing-byte-rate` |
| Productor | `producer-node-metrics.node-<node>` | `producer-node-metrics.node-<node>.outgoing-byte-rate`, `producer-node-metrics.node-<node>.request-rate`, `producer-node-metrics.node-<node>.response-rate` |
| Consumidor | `consumer-metrics` | `consumer-metrics.connection-count`, `consumer-metrics.request-rate`, `consumer-metrics.incoming-byte-rate`, `consumer-metrics.request-latency-avg` |
| Consumidor | `consumer-node-metrics.node-<node>` | `consumer-node-metrics.node-<node>.incoming-byte-rate`, `consumer-node-metrics.node-<node>.request-rate`, `consumer-node-metrics.node-<node>.response-rate` |
| Consumidor | `consumer-fetch-manager-metrics` | `consumer-fetch-manager-metrics.fetch-size-avg`, `consumer-fetch-manager-metrics.bytes-consumed-rate`, `consumer-fetch-manager-metrics.records-consumed-rate`, `consumer-fetch-manager-metrics.records-lag-max` |
| Consumidor | `consumer-coordinator-metrics` | `consumer-coordinator-metrics.commit-rate`, `consumer-coordinator-metrics.assigned-partitions` |

En los grupos de nodo, `<node>` es el identificador numérico del nodo de Kafka,
por ejemplo `node-1`. El nombre del grupo ya lo contiene, así que un nombre de
módulo completo es similar a
`producer-node-metrics.node-1.outgoing-byte-rate`. Los grupos de nodo aparecen
solo para los nodos con los que el cliente de sondeo contacta realmente; el
conjunto depende de los metadatos del clúster que recibe ese cliente.

Ambos clientes registran su propio grupo `kafka-metrics-count`, así que el XML
del agente contiene `kafka-metrics-count.count` dos veces: una con el recuento
del productor y otra con el del consumidor. Es el comportamiento esperado, no un
agente duplicado.

### Qué representan los valores

Cada ejecución crea clientes nuevos y lee sus métricas de inmediato. Los valores
son, por tanto, una instantánea de un sondeo recién creado, no una muestra
continua de su aplicación:

- Los contadores de conexión, los contadores de peticiones y la latencia de
  peticiones describen las conexiones del propio cliente del plugin.
- Las tasas de registros y confirmación describen tráfico que el cliente de
  sondeo no genera: el plugin no envía registros, no hace `poll` de registros y
  no confirma offsets, así que esas tasas normalmente permanecen en sus valores
  iniciales. Las tasas de bytes y peticiones reflejan solo el tráfico de conexión
  y metadatos del propio sondeo, no el rendimiento de su aplicación.
- Las medias que necesitan muestras de la vida del cliente pueden ser `0.0`
  porque el plugin convierte su `NaN` inicial en cero.
- Las métricas de grupo de consumidores no reflejan los grupos de consumidores de
  su aplicación. El consumidor usa el identificador de grupo fijo
  `monitoring-client`, con la confirmación automática deshabilitada, y nunca se
  une a un grupo durante la ejecución.

Use las métricas de conexión y peticiones para observar si el listener de Kafka
es accesible y responde desde el servidor de Pandora FMS. No use este addon como
sustituto de la monitorización JMX del broker de Kafka ni de la instrumentación
de los productores y consumidores de sus aplicaciones.

## Operación y resolución de problemas

El plugin no conserva estado entre ejecuciones. Cada ejecución crea sus clientes,
recoge una instantánea, entrega un documento de agente y termina, así que se
puede ejecutar manualmente en cualquier momento sin afectar a offsets ni a datos
de los topics.

Programe el módulo de plugin registrado con el intervalo que desee. Los agentes
generados mantienen su intervalo fijo de 300 segundos, pero sus valores solo se
actualizan cuando se ejecuta el módulo del plugin; alinee el intervalo del módulo
con la cadencia de datos deseada. Use `--verbose` para el diagnóstico manual,
pero no lo deje en la cadena de parámetros registrada: sus líneas de diagnóstico
se escriben en la salida estándar y pasan a formar parte del valor que recibe el
módulo del plugin.

### Salida y código de salida

| Resultado | Significado |
|-----------|-------------|
| Salida estándar `1` | Todos los endpoints se procesaron sin una excepción: se crearon sus clientes y se recogieron sus métricas. No se garantiza la entrega |
| Salida estándar `0` | Al menos un endpoint provocó una excepción, por ejemplo porque el broker era inaccesible o rechazó la conexión. Ejecute de nuevo con `--verbose` para ver el detalle |
| Sin salida estándar sin `--verbose` | La lista de bootstrap no contenía ningún elemento no vacío. El proceso termina con código `0` |
| Error de análisis de argumentos en la salida de error | Falta una opción obligatoria o una opción no tiene valor, por ejemplo un campo de macro vacío. El proceso termina con código `2` |
| Código de salida `0` con `1` o `0` en la salida estándar | Ejecución normal. El número impreso es el valor del módulo, no el estado del proceso |

### Problemas habituales

- **La ejecución imprime `1` pero no aparece ningún agente.** El procesamiento
  del broker fue correcto pero la entrega falló. Compruebe que `tentacle_client`
  existe en `PATH` y que puede alcanzar `--tentacle_ip`:`--tentacle_port`.
  Ejecute manualmente con `--verbose` y lea la salida de error; los errores de
  Tentacle no cambian el `1` impreso. Para entrega local, compruebe que
  `/var/spool/pandora/data_in/` existe y tiene permiso de escritura.
- **La ejecución imprime `0`.** Al menos un endpoint falló. Ejecute con
  `--verbose` y lea la línea `Error with broker ...`. Las causas habituales son
  una dirección o un puerto incorrectos, un listener que exige autenticación o
  TLS, un `--topic_regex` no válido o un endpoint mal formado.
- **La ejecución no imprime nada sin `--verbose`.** `--bootstrap_servers` se
  aceptó pero no contenía ningún elemento no vacío, por ejemplo solo una coma o
  espacios. El proceso termina con `0` sin agente ni valor. Corrija la lista de
  endpoints.
- **El plugin termina antes de conectar.** Una opción no tiene valor. Es el
  resultado habitual de dejar vacía una macro `_fieldN_` de una opción que se
  mantuvo en la cadena de parámetros. Elimine la opción que no use o rellene el
  campo.
- **El agente existe pero todos los valores son cero.** El sondeo conectó, pero
  no intercambió más datos con el clúster. Compruebe la dirección y el puerto del
  listener, y si el listener acepta conexiones PLAINTEXT sin autenticación.
  Recuerde que las tasas de registros y confirmación deben permanecer en sus
  valores iniciales porque el sondeo no envía ni consume registros, y que las
  tasas de bytes y peticiones reflejan solo el tráfico del propio sondeo.
- **El clúster exige SASL o TLS.** Esta versión no puede conectarse a él. El
  addon no tiene ninguna opción para configurar autenticación ni cifrado; use una
  vía de monitorización de Kafka que admita esos ajustes.
- **`--transfer_mode local` no entrega.** El plugin siempre mueve el XML a
  `/var/spool/pandora/data_in/`. Si el servidor de Pandora FMS usa otro
  directorio de datos, use la entrega por Tentacle.
- **Un modo de transferencia mal escrito sigue intentando Tentacle.** Solo el
  valor exacto `local` selecciona la entrega local; cualquier otro valor recurre
  a Tentacle.
- **Los valores parecen obsoletos.** Cada ejecución devuelve la instantánea
  tomada en ese momento. Compruebe el intervalo del módulo del plugin y el estado
  del broker en lugar de esperar una serie continua.

## Referencia

### Parámetros de línea de comandos

```text
./pandora_kafka --bootstrap_servers <host:port> [--topics <topic1,topic2>] [--topic_regex <regex>] [--agent_prefix <prefix>] [--module_prefix <prefix>] [--transfer_mode <mode>] [--tentacle_ip <ip>] [--tentacle_port <port>] [--verbose]
```

| Nombre | Obligatorio | Valor predeterminado | Descripción |
|--------|-------------|----------------------|-------------|
| `-h`, `--help` | No | — | Imprime el resumen de uso, la versión del plugin y el ejemplo de ejecución, y termina |
| `--bootstrap_servers` | Sí | — | Endpoints de Kafka separados por comas en formato `host:puerto`. Los elementos vacíos se ignoran. Cada elemento restante produce un agente |
| `--topics` | No | Vacío | Topics separados por comas para la suscripción del consumidor. Se ignoran cuando se define `--topic_regex` |
| `--topic_regex` | No | Vacío | Expresión regular para la suscripción del consumidor. Tiene prioridad sobre `--topics`. Un patrón no válido falla durante la ejecución |
| `--agent_prefix` | No | Vacío | Prefijo añadido al nombre y al alias de cada agente generado |
| `--module_prefix` | No | Vacío | Prefijo añadido a cada nombre de módulo generado |
| `--transfer_mode` | No | `tentacle` | `local` mueve el XML a `/var/spool/pandora/data_in/`. Cualquier otro valor, incluido el predeterminado, usa Tentacle |
| `--tentacle_ip` | No | `127.0.0.1` | Dirección del servidor Tentacle para la entrega por Tentacle |
| `--tentacle_port` | No | `41121` | Puerto del servidor Tentacle para la entrega por Tentacle |
| `--verbose` | No | Deshabilitado | Imprime errores de broker y mensajes de diagnóstico en la salida estándar |

### Entrega

| Ajuste | Valor |
|--------|-------|
| Entrega predeterminada | Tentacle |
| Comando del cliente Tentacle | `tentacle_client`, resuelto mediante `PATH` |
| Dirección y puerto de Tentacle | `--tentacle_ip` y `--tentacle_port` |
| Selector de entrega local | `--transfer_mode local` (valor exacto) |
| Destino local | `/var/spool/pandora/data_in/` |
| Destino local configurable | No |
| Directorio de preparación del XML | `/tmp` |
| Dependencia en tiempo de ejecución del broker | Ninguna; no se instala nada en el broker de Kafka |

### Agentes generados

| Atributo | Valor |
|----------|-------|
| Cardinalidad | Un agente por cada elemento no vacío de `--bootstrap_servers` procesado correctamente |
| Nombre | `<agent_prefix><host:puerto>` |
| Alias | Igual que el nombre |
| Descripción | `Created by plugin` |
| Intervalo | `300` segundos |
| Grupo | Sin definir |
| Origen de datos | Métricas del productor y del consumidor de los clientes creados en esa ejecución |

### Comportamiento del consumidor

| Comportamiento | Valor |
|----------------|-------|
| Identificador de grupo de consumidores | `monitoring-client` |
| Confirmación automática de offsets | Deshabilitada |
| Registros consumidos | Ninguno; el plugin nunca hace `poll` del consumidor |
| Offsets confirmados | Ninguno |
| Suscripción | Opcional, mediante `--topics` o `--topic_regex` |
| Efecto sobre los datos de los topics | Ninguno |

### Grupos de métricas

El plugin antepone `<module_prefix>` a cada nombre de módulo. La parte de métrica
es `<metric_group>.<metric_name>`, donde `<node>` es el identificador numérico del
nodo de Kafka.

| Origen | Grupo de métricas | Nombres de métrica de ejemplo |
|--------|-------------------|-------------------------------|
| Productor y consumidor | `kafka-metrics-count` | `count` |
| Productor | `producer-metrics` | `connection-count`, `request-rate`, `request-latency-avg`, `outgoing-byte-rate`, `incoming-byte-rate` |
| Productor | `producer-node-metrics.node-<node>` | `outgoing-byte-rate`, `incoming-byte-rate`, `request-rate`, `response-rate`, `request-latency-avg` |
| Consumidor | `consumer-metrics` | `connection-count`, `request-rate`, `request-latency-avg`, `incoming-byte-rate`, `outgoing-byte-rate` |
| Consumidor | `consumer-node-metrics.node-<node>` | `incoming-byte-rate`, `outgoing-byte-rate`, `request-rate`, `response-rate`, `request-latency-avg` |
| Consumidor | `consumer-fetch-manager-metrics` | `fetch-size-avg`, `fetch-size-max`, `bytes-consumed-rate`, `records-consumed-rate`, `records-lag-max` |
| Consumidor | `consumer-coordinator-metrics` | `commit-latency-avg`, `commit-latency-max`, `commit-rate`, `assigned-partitions` |

Esta lista es un catálogo funcional, no un contrato fijo: el conjunto exacto de
métricas depende de la versión del cliente de Kafka y del estado de los clientes
en el momento de la ejecución. Todos los módulos generados usan `generic_data`,
sin unidad y sin descripción.

Las definiciones de métricas que publica Kafka para sus clientes ayudan a
interpretar los valores:

- [Consumer monitoring](https://kafka.apache.org/documentation/#consumer_monitoring)
- [Producer monitoring](https://kafka.apache.org/documentation/#producer_monitoring)

### Identidad del addon

| Campo | Valor |
|-------|-------|
| Identificador del Marketplace | `pandorafms.apache_kafka` |
| Nombre en el Marketplace | Kafka monitoring |
| Versión | `1.1` — la versión actual del Marketplace, también indicada por `-h` |
| Última actualización en el Marketplace | 2026-08-28 |
| Licencia | One — la descarga está limitada a usuarios con licencia |
| Tipo en el Marketplace | Miscelaneus |
| Descargas | 9 |
| Flujo de trabajo | Plugin de monitorización, modo plugin de servidor |
| Ejecutable | `pandora_kafka` |
| Entrada del Marketplace | [pandorafms.apache_kafka](https://marketplace.pandorafms.com/entries/pandorafms.apache_kafka) |
