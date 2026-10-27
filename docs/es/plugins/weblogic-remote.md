# Plugin de monitorización Weblogic remote

*Última actualización del artículo: 2026-10-26.*

## Qué hace

El addon `Weblogic remote` monitoriza un dominio de Oracle WebLogic Server desde Pandora FMS mediante SNMP. En cada ejecución recorre el agente SNMP de WebLogic de un dominio y convierte la respuesta en módulos de Pandora FMS: el estado y el heap de cada instancia de servidor, el uso de los datasources JDBC, los mensajes pendientes de JMS, el estado de los pools de conexiones Jolt, la carga de los work managers, las sesiones de las aplicaciones desplegadas, los contadores de espera de los EJB y el uso del heap de JRockit.

El colector no se autentica contra WebLogic y no necesita la consola de administración: lee el árbol de monitorización que publica el agente SNMP de WebLogic, así que la única credencial que interviene es la comunidad SNMP.

El colector se ejecuta como **plugin de servidor** de Pandora FMS. Cada ejecución imprime en la salida estándar un bloque XML `<module>` por cada valor, y Pandora FMS los almacena en el agente al que pertenece la definición del módulo. No crea ningún agente ni entrega ningún documento por sí mismo.

## Preparación

### Compatibilidad y disponibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Addon `pandorafms.weblogic_remote`, versión `1.0` | Objetivo documentado | Entrada del Marketplace; consulte [Identidad del addon](#identidad-del-addon) |
| CentOS 7 y Fedora | `Compatible conocido` | La edición anterior de esta guía registra ambos como sistemas probados para el addon. Sin revalidar para la versión `1.0` |
| Otros sistemas operativos del servidor de Pandora FMS que ejecuta el colector | `Sin validar` | No hay registro de pruebas. La edición anterior afirma que debería funcionar en cualquier sistema Linux, sin evidencia |
| Versiones y ediciones de WebLogic Server | `Sin validar` | No se ha registrado una matriz de versiones para este addon |
| Versiones de Pandora FMS | `Sin validar` | No hay registro por versión. El Marketplace indica que sus integraciones son compatibles con Pandora FMS NG 784 y posteriores |
| Un dominio de WebLogic con el agente SNMP activado y accesible | `Requerido` | Todos los módulos se construyen a partir de objetos bajo `1.3.6.1.4.1.140.625` |
| Una comunidad SNMP de lectura aceptada por el agente SNMP de WebLogic | `Requerido` | Todas las consultas se envían con esa comunidad |
| La utilidad `snmpwalk` de net-snmp en `PATH` | `Requerido` | Toda lectura de datos es una llamada a `snmpwalk` |
| Un Plugin Server de Pandora FMS con acceso al puerto SNMP de WebLogic | `Requerido` | El colector es un plugin de servidor |

### Requisitos

1. **Un dominio de WebLogic Server** con su agente SNMP activado. El agente no está activado de forma predeterminada en todos los dominios: confirme que está en ejecución y que es accesible desde la máquina que ejecuta el colector.
2. **El puerto SNMP de ese agente.** El colector envía al UDP `161` cuando no se indica puerto. Si el dominio ejecuta el agente SNMP de WebLogic en otro puerto, indíquelo como tercer argumento; los ejemplos de esta página usan `40161`.
3. **Una comunidad SNMP con acceso de lectura** al árbol de monitorización de WebLogic. La versión 1 es la única versión de SNMP que envía el colector, así que use una comunidad definida para v1.
4. **El comando `snmpwalk`**, de las utilidades de net-snmp, instalado en el servidor de Pandora FMS que ejecuta el colector y accesible a través de `PATH`.
5. **Un Plugin Server de Pandora FMS** en ejecución y con acceso al puerto SNMP de WebLogic. El colector lo ejecuta el Plugin Server, por lo que se ejecuta en un servidor de Pandora FMS, no en el host de WebLogic.

### Instalar el colector

Descargue el addon desde su entrada del Marketplace, limitada a usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.weblogic_remote](https://marketplace.pandorafms.com/entries/pandorafms.weblogic_remote)

La consola instala el paquete y registra la definición del plugin. Para ejecutar el colector fuera de la consola, copie el ejecutable a la carpeta de plugins de servidor de Pandora FMS, `/usr/share/pandora_server/util/plugin/`, y dele permiso de ejecución.

### Activar el agente SNMP de WebLogic

El colector solo lee lo que publica el agente SNMP de WebLogic. Active el agente en el dominio que quiera monitorizar y anote su puerto y su comunidad de lectura; la documentación de WebLogic describe la configuración del agente. El colector no necesita ninguna cuenta de administrador, ni un endpoint de RESTful Management Services, ni un usuario de WebLogic.

## Configuración

### Registrar el plugin en la consola

1. Abra **Servidores → Plugins** y registre el colector como plugin de servidor estándar.
2. En **Comando del plugin**, indique la ruta del ejecutable en el servidor de Pandora FMS, por ejemplo `/usr/share/pandora_server/util/plugin/plugin_weblogic_snmp.pl`.
3. En **Parámetros del plugin**, pase los tres argumentos como campos:

```text
_field1_ _field2_ _field3_
```

4. En los campos de macro, describa cada argumento. El ejemplo usa estos valores:

| Campo | Descripción | Valor de ejemplo |
| --- | --- | --- |
| `_field1_` | Nombre de host o dirección IP del agente SNMP de WebLogic | `<TARGET_HOST>` |
| `_field2_` | Comunidad SNMP de lectura de ese agente | `<COMMUNITY>` |
| `_field3_` | Puerto SNMP del agente | `40161` |

<!-- SCREENSHOT NEEDED: formulario de registro de plugin de servidor de Pandora FMS con la ruta al colector de WebLogic y _field1_ _field2_ _field3_ como parámetros, sin nombres de host ni comunidades reales. -->

Los tres argumentos son posicionales: el host y la comunidad son obligatorios y el puerto es opcional. El colector no tiene opciones con nombre ni fichero de configuración.

### Crear los módulos

Se necesita una definición de módulo por cada nombre de módulo que quiera recibir. Como el colector añade el nombre del objeto de WebLogic a la mayoría de los nombres de módulo, una definición de módulo cubre la instancia, el datasource, el destino, el pool o la aplicación que se indica en ella. Cuando aparezca una nueva instancia o un nuevo recurso en el dominio, cree el módulo con su nombre.

Registre cada módulo como módulo de plugin del agente que deba contenerlo, seleccione el plugin registrado arriba y mantenga los valores predeterminados de los campos: todos los módulos de este colector se rellenan con los mismos tres argumentos.

<!-- SCREENSHOT NEEDED: definición de módulo de plugin en la consola de Pandora FMS para un módulo de WebLogic, con el plugin seleccionado y los tres valores de campo, sin nombres de host ni comunidades reales. -->

### Acceso SNMP y secretos

- La comunidad viaja en texto claro por la red, porque el colector envía SNMP versión 1. Restrinja el puerto SNMP a los servidores de Pandora FMS o use una red de monitorización dedicada.
- La comunidad se escribe en los parámetros del plugin de cada módulo, así que queda almacenada en la base de datos de Pandora FMS y es visible para los usuarios que pueden leer la definición del módulo. Use una comunidad de solo lectura dedicada a la monitorización.
- El colector pasa la comunidad a `snmpwalk` como argumento de línea de comandos, por lo que también aparece en la lista de procesos del servidor de Pandora FMS mientras se ejecuta una recogida.

## Verificación

Ejecute el colector a mano en el servidor de Pandora FMS:

```bash
cd /usr/share/pandora_server/util/plugin/
./plugin_weblogic_snmp.pl <TARGET_HOST> <COMMUNITY> 40161
```

Cada ejecución se ejecuta una vez y termina. Una ejecución correcta imprime bloques `<module>` consecutivos, uno por cada valor recogido:

```xml
<module>
<name>WebLogic_SNMP_Status</name>
<type>generic_proc</type>
<data><![CDATA[1]]></data>
<description><![CDATA[Status of Weblogic SNMP Interface]]></description>
</module>
<module>
<name>WebLogic_ServerStatus_AdminServer</name>
<type>generic_proc</type>
<data><![CDATA[1]]></data>
<description><![CDATA[Status of Weblogic Instance 'AdminServer']]></description>
</module>
```

`WebLogic_SNMP_Status` es la comprobación de disponibilidad: informa de `1` cuando el agente SNMP de WebLogic responde al subárbol de disponibilidad y de `0` cuando no responde. Cuando informa de `0`, la ejecución no imprime ningún otro módulo; consulte [Operar y resolver problemas](#operar-y-resolver-problemas).

Una ejecución con menos de dos argumentos imprime el resumen de uso y termina con código de salida `1`. Cualquier otra ejecución termina con código de salida `0`, tanto si ha recogido datos como si no.

Después confirme la llegada a la consola: abra el agente al que pertenecen las definiciones de módulo y compruebe los módulos descritos en [Entender los resultados](#entender-los-resultados) una vez transcurrido un intervalo.

<!-- SCREENSHOT NEEDED: vista de detalle de un agente de WebLogic en Pandora FMS con los módulos WebLogic_ y sus datos, sin nombres de host ni comunidades reales. -->

## Entender los resultados

Una ejecución produce un módulo por cada objeto encontrado en el dominio, agrupados por el subsistema de WebLogic al que pertenecen:

- **Disponibilidad y estado del servidor.** `WebLogic_SNMP_Status` informa de si responde el agente SNMP de WebLogic. `WebLogic_ServerStatus_<instance>` informa de `1` en cada instancia de servidor cuyo estado es `RUNNING` y de `0` en el resto.
- **Memoria de la JVM.** `WebLogic_FreeHeap_<instance>` informa del heap libre y `WebLogic_FreeHeap%_<instance>` del porcentaje libre del heap de cada instancia de servidor. `Weblogic_FreeHeapJrokit%_<instance>` informa del porcentaje libre del heap de JRockit, solo en las instancias que publican el árbol de JRockit.
- **Datasources JDBC.** Por cada datasource, `WebLogic_DbpoolTime_<pool>` informa del tiempo medio de espera notificado por el datasource, en segundos, `WebLogic_Current_DbpoolConns_<pool>` de las conexiones actuales, `Weblogic_DbpoolConns%_<pool>` del porcentaje sobre el máximo y `Weblogic_DbpoolLeakConns_<pool>` de las conexiones con fuga.
- **Destinos JMS.** `Weblogic_PendingDST_<destination>` informa de los mensajes pendientes de un destino.
- **Pools de conexiones Jolt.** `Weblogic_joltpoolStatus_<machine>_<pool>` informa del estado de cada pool.
- **Work managers.** `Weblogic_QueueLength_<threadpool>` informa de la longitud de la cola y `Weblogic_FreeThreads_<threadpool>` de los hilos libres del pool de hilos que usa el work manager.
- **Aplicaciones y EJB.** `WebLogic_Sessions_<application>` informa de las sesiones abiertas de las aplicaciones desplegadas, y `WebLogic_EjbWaiter_<location>_<name>` del número de esperas de los EJB.

La parte de objeto de un nombre es el valor que WebLogic publica para ese objeto, así que los nombres cambian cuando el dominio se renombra o se vuelve a desplegar. Hay dos detalles de nomenclatura que conviene conocer al crear definiciones de módulo:

- **El prefijo no usa siempre las mismas mayúsculas.** Los módulos de estado, heap, JDBC, sesiones y EJB empiezan por `WebLogic_`; los de cola, hilos, destinos, Jolt y porcentaje de conexiones empiezan por `Weblogic_`. Los nombres de módulo distinguen mayúsculas y minúsculas en Pandora FMS, así que copie la grafía exacta de la ejecución.
- **Las aplicaciones internas quedan excluidas** de los módulos de sesiones: las aplicaciones internas de WebLogic, los contextos de administración y asíncronos, y las aplicaciones de despliegue y diagnóstico no producen ningún módulo.

Todos los módulos se declaran como `generic_data` o `generic_proc`, y ningún módulo lleva unidad, umbral ni grupo de módulos.

## Operar y resolver problemas

- **El colector no guarda estado entre ejecuciones.** Cada ejecución vuelve a consultar el agente SNMP de WebLogic, así que se puede ejecutar a mano en cualquier momento.
- **No ejecute dos recogidas a la vez en el mismo servidor de Pandora FMS.** El colector escribe todo el recorrido SNMP en el fichero fijo `/tmp/weblogic.snmp.dump`, lo descarta al principio y al final de cada ejecución y lee de él todos los módulos. Dos ejecuciones simultáneas — dos agentes, dos módulos ejecutados al mismo tiempo o una ejecución manual que se solape — reutilizan y borran el fichero de la otra, de modo que una ejecución puede informar de los datos de otro dominio de WebLogic. Escalone las ejecuciones o use un servidor de Pandora FMS distinto por dominio.
- **No hay modo detallado.** El colector no acepta ninguna opción de depuración y descarta los errores de `snmpwalk`. Para diagnosticar una ejecución, repita el recorrido a mano:

```bash
snmpwalk -On -v1 -c <COMMUNITY> <TARGET_HOST>:40161 .1.3.6.1.4.1.140.625.730
```

- **`WebLogic_SNMP_Status` informa de `0` y no aparece ningún otro módulo** — no ha respondido nada en el árbol SNMP. Compruebe que el agente SNMP de WebLogic está activado, que el puerto es el del agente y no el de administración, que la comunidad es válida para SNMP v1 y que `snmpwalk` está instalado en el servidor de Pandora FMS: la ausencia de `snmpwalk` produce el mismo resultado que un agente inaccesible.
- **`WebLogic_SNMP_Status` informa de `1` y faltan los módulos de servidor** — el árbol ha respondido pero la tabla de instancias no. El agente SNMP de WebLogic publica solo los subsistemas activos en el dominio, así que un resultado vacío o parcial refleja el dominio, no el colector.
- **Los módulos `Weblogic_PendingDST_` no aparecen nunca** — este módulo solo acepta servidores JMS cuyo nombre publicado encaja con el patrón `CRMNAModule!JMSServer_` seguido del nombre del destino. Los destinos de un servidor JMS con otro nombre se omiten aunque publiquen mensajes pendientes.
- **La ejecución se interrumpe a mitad de la salida** — una ejecución aborta cuando un datasource o una instancia informa de capacidad cero, porque el módulo de porcentaje divide por ella. Los módulos impresos antes de ese punto siguen siendo válidos.
- **Dos valores de módulo parecen pertenecer a dominios distintos** — una ejecución simultánea ha reutilizado el fichero de recorrido fijo descrito arriba. Repita la ejecución en solitario y compare los valores con un `snmpwalk` manual.
- **Un módulo muestra un valor de texto donde se espera un número** — los módulos de estado de los pools Jolt son módulos booleanos, pero publican el texto de estado que devuelve WebLogic. Léalos como texto y cree las condiciones de alerta en consecuencia.

## Referencia

### Línea de comandos

```text
./plugin_weblogic_snmp.pl <target_address> <target_community> [target_port]
```

| Argumento | Obligatorio | Valor predeterminado | Descripción |
| --- | --- | --- | --- |
| `target_address` | Sí | — | Nombre de host o dirección IP del agente SNMP de WebLogic |
| `target_community` | Sí | — | Comunidad SNMP v1 de lectura |
| `target_port` | No | `161` | Puerto SNMP del agente |

| Condición | Comportamiento |
| --- | --- |
| Menos de dos argumentos | Imprime el resumen de uso y termina con código de salida `1` |
| Dos o tres argumentos | Ejecuta la recogida y termina con código de salida `0` |
| Un cuarto argumento | Se ignora |
| El árbol SNMP no responde o falta `snmpwalk` | Imprime solo `WebLogic_SNMP_Status` con valor `0` y termina con código de salida `0` |

El colector envía únicamente SNMP versión 1. No ofrece opciones con nombre, ni fichero de configuración, ni variable de entorno, ni modo detallado.

### Orígenes de datos

Cada ejecución recorre estos subárboles del árbol de monitorización de WebLogic, identificados por el identificador de objeto `.1.3.6.1.4.1.140.625` más el sufijo indicado:

| Sufijo | Alimenta |
| --- | --- |
| `.161` | Módulos de espera de EJB |
| `.190` | Módulos de datasources JDBC |
| `.220` | Módulos de destinos JMS |
| `.280` | Módulos de pools de conexiones Jolt |
| `.302` | Módulo de heap de JRockit |
| `.340` | Módulos de heap del servidor |
| `.360` | Módulos de estado del servidor y de nombre de pool Jolt |
| `.367` | Módulos de work managers |
| `.430` | Módulos de sesiones de aplicaciones |
| `.730` | Comprobación de disponibilidad SNMP |

### Módulos generados

Los nombres se reproducen tal como los imprime el colector. `<instance>`, `<pool>`, `<destination>`, `<threadpool>`, `<application>`, `<machine>`, `<location>` y `<name>` son los nombres de objeto que publica WebLogic.

| Nombre del módulo | Tipo | Significado |
| --- | --- | --- |
| `WebLogic_SNMP_Status` | `generic_proc` | `1` cuando el agente SNMP de WebLogic responde al subárbol de disponibilidad, `0` en caso contrario |
| `WebLogic_ServerStatus_<instance>` | `generic_proc` | `1` cuando el estado de la instancia de servidor es `RUNNING`, `0` en caso contrario |
| `WebLogic_FreeHeap_<instance>` | `generic_data` | Heap libre de la instancia de servidor |
| `WebLogic_FreeHeap%_<instance>` | `generic_data` | Heap libre como porcentaje del heap total |
| `WebLogic_DbpoolTime_<pool>` | `generic_data` | Tiempo medio de espera notificado por el datasource, en segundos |
| `WebLogic_Current_DbpoolConns_<pool>` | `generic_data` | Conexiones en uso en el datasource |
| `Weblogic_DbpoolConns%_<pool>` | `generic_data` | Conexiones en uso como porcentaje de la capacidad máxima |
| `Weblogic_DbpoolLeakConns_<pool>` | `generic_data` | Conexiones notificadas como fugadas por el datasource |
| `WebLogic_EjbWaiter_<location>_<name>` | `generic_data` | Número de esperas del EJB |
| `WebLogic_Sessions_<application>` | `generic_data` | Sesiones abiertas de la aplicación desplegada |
| `Weblogic_QueueLength_<threadpool>` | `generic_data` | Peticiones en espera en la cola del work manager |
| `Weblogic_FreeThreads_<threadpool>` | `generic_data` | Hilos inactivos del work manager |
| `Weblogic_PendingDST_<destination>` | `generic_data` | Mensajes pendientes en el destino JMS |
| `Weblogic_joltpoolStatus_<machine>_<pool>` | `generic_proc` | Texto de estado del pool Jolt, por ejemplo `Active` |
| `Weblogic_FreeHeapJrokit%_<instance>` | `generic_data` | Porcentaje libre del heap de JRockit |

### Salida

El colector imprime en la salida estándar un fragmento de documento XML: un elemento `<module>` por cada valor, sin un elemento `<agent_data>` que los envuelva. Cada elemento lleva `name`, `type`, `data` y `description`. Los valores de los módulos numéricos que no son números se vacían, y los módulos de texto conservan su texto.

Los nombres de módulo incluyen el nombre del objeto de WebLogic, así que una misma definición de módulo solo recibe datos del objeto que se indica en ella.

### Identidad del addon

| Propiedad | Valor |
| --- | --- |
| Identificador del Marketplace | `pandorafms.weblogic_remote` |
| Nombre | Weblogic remote |
| Versión | `1.0` |
| Categoría | Miscelaneus |
| Licencia | One |
| Última actualización del Marketplace | 2025-06-27 |
| Disponibilidad | Descarga limitada a usuarios con licencia |
| Paquete | `pandorafms.weblogic_remote.1.0.pspz2` |
| Versión del colector | `v4r1`, según el resumen de uso |

El registro del Marketplace y la edición anterior de esta guía describen el addon con otra superficie de comandos, `-u <URL> -us <USER> -p <PASSWORD>` más un `-g` y un `--data_dir` opcionales, y una vía de recogida que necesita RESTful Management Services en WebLogic. Esta página documenta el colector SNMP, cuyos argumentos son posicionales. Compare el comando registrado en **Servidores → Plugins** con las dos listas antes de crear módulos: los parámetros que aparecen ahí son los que ejecuta la instalación.
