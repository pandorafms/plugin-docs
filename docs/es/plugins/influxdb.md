# Pandora InfluxDB

*Última actualización del artículo: 2026-10-26.*

## Qué hace

El plugin Pandora InfluxDB recopila las estadísticas internas de una instancia
de InfluxDB y las publica como módulos de Pandora FMS. Cada ejecución se conecta
a la API HTTP de InfluxDB, ejecuta una vez la sentencia InfluxQL `SHOW STATS` y
convierte en módulos las secciones `runtime`, `queryExecutor`, `httpd`, `write`,
`subscriber` y `cq` de la respuesta. No se instala nada en el servidor de
InfluxDB y el plugin no guarda estado entre ejecuciones: cada ejecución informa
de los contadores de ese momento.

El plugin admite dos modelos de ejecución:

- **Modo plugin de servidor** (por defecto): cada ejecución construye un
  documento de agente y lo escribe en el directorio de datos de Pandora FMS,
  donde lo ingiere el servidor. Las estadísticas se reparten en cinco agentes
  con el nombre de la sección de InfluxDB de la que proceden.
- **Modo plugin de agente** (requiere `--as_agent_plugin 1`): cada ejecución
  imprime los módulos como XML en la salida estándar, y el agente de Pandora FMS
  que ejecuta el plugin los guarda en su propio agente.

Todos los módulos generados son de tipo `generic_data`.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
|--------|--------|-----------|
| Plugin `pandorafms.influxdb`, versión `1.0` | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del plugin](#identidad-del-plugin) |
| Pandora FMS NG `784` y posteriores | `Supported` | El Marketplace indica que todas sus integraciones son compatibles con Pandora FMS NG 784 y versiones posteriores. Es una declaración general de compatibilidad que cubre el plugin, no un registro de prueba del mismo |
| Un endpoint de InfluxDB que acepte un usuario y una contraseña y responda a `SHOW STATS` | `Required` | El plugin expone `--user` y `--password` y ejecuta esa sentencia; no tiene opción de autenticación por token |
| Versiones del servidor InfluxDB | `Not validated` | No se ha registrado una matriz de versiones de InfluxDB para este plugin |
| Sistema operativo del host que ejecuta el plugin | `Not validated` | No se ha registrado un sistema operativo para esta versión |
| Acceso de red desde ese host a la API HTTP de InfluxDB | `Required` | El plugin se conecta al host y al puerto que configure |

### Requisitos

1. **Una instancia de InfluxDB accesible por TCP** desde el host que ejecutará
   el plugin, con su API HTTP escuchando en el puerto configurado (`8086` por
   defecto) y capaz de responder a `SHOW STATS`.
2. **Credenciales para esa instancia** cuando requiera autenticación: un usuario
   y una contraseña. El plugin solo se autentica cuando se proporcionan ambos.
3. **Pandora FMS**:
    - En modo plugin de servidor, el servidor de plugins de Pandora FMS para
      ejecutar el plugin registrado, y un directorio de datos que procese el
      servidor de datos.
    - En modo plugin de agente, un agente que ejecute el plugin e ingiera su
      salida.
4. **El paquete del plugin instalado en Pandora FMS** a través de la consola.

### Instalar el plugin

Descargue el paquete desde la entrada del Marketplace de Pandora FMS, que está
limitada a usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.influxdb](https://marketplace.pandorafms.com/entries/pandorafms.influxdb)

Cárguelo en Pandora FMS. Una vez cargado, el plugin queda registrado con sus
parámetros y disponible en la lista de plugins.

<!-- SCREENSHOT NEEDED: Lista de plugins de la consola de Pandora FMS tras cargar el paquete pandorafms.influxdb, con el plugin Pandora InfluxDB registrado. -->

No ha sido posible inspeccionar el contenido del paquete distribuido para esta
página, por lo que no se prescribe aquí ningún procedimiento de compilación ni
de instalación de dependencias. Utilice el ejecutable que instala el paquete y
que muestra la definición del plugin.

## Configuración

El plugin no tiene archivo de configuración: todas las opciones son de línea de
comandos y se documentan en [Parámetros de línea de
comandos](#parametros-de-linea-de-comandos). Elija primero el modelo de
ejecución; las opciones de conexión son las mismas en ambos.

### Modo plugin de servidor

El modo plugin de servidor es el predeterminado: se aplica salvo que
`--as_agent_plugin` valga `1`. Cada ejecución escribe un documento de agente por
cada sección de estadísticas en `--data_dir`:

```text
--host <INFLUXDB_URL> --port 8086 --user <USERNAME> --password <PASSWORD> --group <GROUP_ID> --data_dir /var/spool/pandora/data_in
```

- **`--host`** recibe el nombre de host o la dirección IP de la instancia de
  InfluxDB, sin el esquema y sin el puerto. Indique el puerto en `--port`.
- **`--group`** establece el grupo de Pandora FMS que se escribe en los cinco
  documentos de agente generados. Su valor por defecto es el literal
  `genieacs`, que no es un identificador de grupo, así que indique el ID
  numérico de un grupo existente. Sin esta opción, los documentos generados
  llevan ese valor literal en su campo de grupo.
- **`--data_dir`** toma por defecto `/var/spool/pandora/data_in/`, el directorio
  de datos de un servidor de Pandora FMS. Debe existir y ser escribible por el
  usuario que ejecuta el plugin.
- Los cinco agentes se llaman `InfluxDB_Runtime`, `InfluxDB_queryExecutor`,
  `InfluxDB_Httpd`, `InfluxDB_Write` e `InfluxDB_Subscriber_cq`. El plugin no
  ofrece ninguna opción para renombrarlos ni para cambiar su intervalo.

### Modo plugin de agente

El modo plugin de agente requiere `--as_agent_plugin 1`. La ejecución imprime
los módulos como XML en la salida estándar en lugar de escribir documentos de
agente:

```text
--host <INFLUXDB_URL> --port 8086 --user <USERNAME> --password <PASSWORD> --as_agent_plugin 1
```

En este modo se ignoran `--group` y `--data_dir`: los módulos se guardan en el
agente que ejecuta el plugin, no en los cinco agentes de sección.

### Credenciales y transporte

- La autenticación se activa solo cuando se establecen `--user` y `--password`
  a la vez. Con una sola de las dos opciones el plugin se conecta sin
  credenciales, y una instancia que requiera autenticación rechaza la petición.
- El plugin se comunica con la API HTTP de InfluxDB sin TLS: no expone ninguna
  opción para habilitarlo ni para verificar un certificado. Las credenciales y
  las estadísticas viajan sin cifrar, así que mantenga la API en un segmento de
  red de confianza o proteja el trayecto con un túnel.
- La contraseña se pasa como opción de línea de comandos. Puede aparecer en el
  historial del intérprete de comandos de una ejecución manual y en la lista de
  procesos mientras el plugin se ejecuta, incluidas las ejecuciones iniciadas
  por Pandora FMS. Restrinja el acceso al host que ejecuta el plugin y rote la
  credencial si queda expuesta.

### Registrar el plugin en la consola

1. Instale el paquete (consulte [Instalar el plugin](#instalar-el-plugin)).
2. Cree un módulo de plugin en un agente y seleccione **Pandora InfluxDB**.
3. Rellene los parámetros de host, puerto y credenciales que expone el paquete,
   y mantenga `8086` cuando la API HTTP escuche en su puerto por defecto.
4. En modo plugin de servidor, establezca además el grupo y el directorio de
   datos cuando difieran de los valores por defecto.

<!-- SCREENSHOT NEEDED: Formulario del módulo de plugin para Pandora InfluxDB con host, puerto, usuario y una contraseña enmascarada, usando valores de laboratorio. -->

En modo plugin de servidor el módulo solo dispara la ejecución: las
estadísticas aparecen en los cinco agentes `InfluxDB_*`, no en el agente que
posee el módulo. En modo plugin de agente los módulos aparecen en el agente que
ejecuta el plugin.

## Verificación

Ejecute el ejecutable instalado del plugin en el host que lo vaya a ejecutar, en
modo plugin de servidor y con un directorio de datos de prueba, para poder
inspeccionar la salida sin alimentar el servidor de Pandora FMS:

```bash
<PLUGIN_EXECUTABLE> --host <INFLUXDB_URL> --port 8086 --user <USERNAME> --password <PASSWORD> --group <GROUP_ID> --data_dir /tmp/influxdb-check
```

Cree antes el directorio: el plugin no lo crea y una escritura fallida no
informa de error. Una ejecución correcta imprime `1` como última línea y escribe
un documento de agente por cada sección de estadísticas:

```text
InfluxDB_Runtime.<EPOCH>.data
InfluxDB_queryExecutor.<EPOCH>.data
InfluxDB_Httpd.<EPOCH>.data
InfluxDB_Write.<EPOCH>.data
InfluxDB_Subscriber_cq.<EPOCH>.data
```

`<EPOCH>` es la hora de la ejecución en segundos. Cada archivo es un documento
de agente con sus módulos:

```xml
<?xml version='1.0' encoding='UTF-8'?>
<agent_data agent_name='InfluxDB_Runtime' agent_alias='InfluxDB_Runtime' parent_agent_name='' description='InfluxDB_Runtime' version='' os_name='' os_version='' timestamp='2026/10/26 10:00:00' address='127.0.0.1' group='10' interval=''>
<module>
	<name><![CDATA[Alloc]]></name>
	<type>generic_data</type>
	<data><![CDATA[4194304]]></data>
</module>
<module>
	<name><![CDATA[Frees]]></name>
	<type>generic_data</type>
	<data><![CDATA[1024]]></data>
</module>
</agent_data>
```

Es un extracto con valores ilustrativos; los contadores reales dependen de la
instancia. En modo plugin de agente la misma conexión imprime bloques `<module>`
en la salida estándar, sin envoltorio `<agent_data>`:

```bash
<PLUGIN_EXECUTABLE> --host <INFLUXDB_URL> --port 8086 --user <USERNAME> --password <PASSWORD> --as_agent_plugin 1
```

```xml
<module>
	<name><![CDATA[Alloc]]></name>
	<type>generic_data</type>
	<data><![CDATA[4194304]]></data>
</module>
```

El `1` final se imprime después de los bloques de módulos. `--help` imprime la
lista de opciones y termina sin recopilar nada.

<!-- SCREENSHOT NEEDED: Los cinco agentes InfluxDB_* y sus módulos en la consola de Pandora FMS tras una ejecución correcta en modo plugin de servidor. -->

## Entender los resultados

### Agentes generados

En modo plugin de servidor el plugin escribe cinco agentes, uno por cada grupo
de estadísticas:

| Agente | Sección de estadísticas | Módulos |
|--------|-------------------------|---------|
| `InfluxDB_Runtime` | `runtime` | 15 |
| `InfluxDB_queryExecutor` | `queryExecutor` | 5 |
| `InfluxDB_Httpd` | `httpd` | 24 |
| `InfluxDB_Write` | `write` | 9 |
| `InfluxDB_Subscriber_cq` | `subscriber` y `cq` | 5 |

| Propiedad del agente | Valor |
|----------------------|-------|
| Nombre, alias y descripción | El nombre fijo de la sección, por ejemplo `InfluxDB_Runtime` |
| Dirección | `127.0.0.1` |
| Grupo | El valor de `--group` |
| Intervalo | No lo establece el plugin |
| Tipo de módulo | `generic_data` en todos los módulos |

### Cómo leer los módulos

El plugin publica los contadores exactamente como los devuelve `SHOW STATS`. No
calcula tasas, incrementos ni umbrales.

- `runtime` informa de contadores de asignación de memoria y de ejecución del
  proceso de InfluxDB.
- `queryExecutor` cuenta la carga de consultas.
- `httpd` cuenta las peticiones atendidas por la API HTTP, incluidas las de
  Flux, Prometheus y escritura.
- `write` cuenta la ruta de escritura.
- `subscriber` cuenta las escrituras de suscriptores y `cq` las ejecuciones de
  consultas continuas.

Los campos cuyo nombre termina en `Ns` son nanosegundos y los que terminan en
`Bytes` son bytes. Los campos `*Req` son recuentos de peticiones.

En modo plugin de agente se pierde la agrupación por secciones: todos los
módulos se guardan en el agente que ejecuta el plugin y no se crean los cinco
agentes de sección. Dos nombres de módulo describen entonces dos secciones
distintas, porque `req` aparece en `httpd` y en `write`, y `recoveredPanics` en
`queryExecutor` y en `httpd`. En modo plugin de servidor, los contadores de
`subscriber` y `cq` se entregan juntos en un único documento
`InfluxDB_Subscriber_cq`.

Una sección de estadísticas que devuelve más de una fila produce los mismos
nombres de módulo una vez por fila.

## Operación y resolución de problemas

### Operación

- El plugin es una única ejecución de recopilación: consulta InfluxDB, entrega
  el resultado y termina. No guarda estado y puede ejecutarse manualmente en
  cualquier momento.
- Prográmelo desde Pandora FMS (planificación de plugins de servidor) o con
  `cron`. No hay opción de intervalo: los documentos de agente generados no
  llevan intervalo, así que la frecuencia de ejecución es la que configure en el
  planificador.
- El documento de agente de cada sección se escribe como
  `<agent_name>.<EPOCH>.data`. Un archivo existente no se sobrescribe y la
  escritura se omite sin error, así que no ejecute la misma configuración más de
  una vez por segundo.
- Use un `--data_dir` dedicado mientras prueba, como se muestra en
  [Verificación](#verificacion), para inspeccionar los documentos antes de que
  lleguen al servidor de Pandora FMS.

### Resolución de problemas

- **El plugin imprime su resumen de uso y termina con estado 2** — falta
  `--host`. Es la única opción obligatoria.
- **La ejecución se detiene con un error del cliente de InfluxDB y un estado de
  salida distinto de cero** — la petición falló. Compruebe que `--host` no
  incluya esquema ni puerto, que `--port` coincida con la API HTTP, que
  `--user` y `--password` estén ambos establecidos cuando la instancia requiera
  autenticación, y que la instancia responda a `SHOW STATS`.
- **La autenticación falla aunque haya un usuario configurado** — solo se
  proporcionó una de las dos opciones `--user` y `--password`, así que el plugin
  se conectó sin credenciales. Establezca ambas.
- **La ejecución falla con un error de valor en `--as_agent_plugin`** — la
  opción espera un entero. Use `1` para el modo plugin de agente y `0`, o nada,
  para el modo plugin de servidor.
- **La ejecución imprime `1` pero no aparece ningún agente en Pandora FMS** — en
  modo servidor los documentos se escribieron en un directorio que el servidor
  no procesa, o el directorio no existe. Compruebe `--data_dir` y sus permisos.
- **No se imprime XML de módulos en modo plugin de agente** — el agente debe
  ingerir la salida de la ejecución del plugin. Compruebe que el plugin se
  ejecuta bajo el agente y que la salida empieza por los bloques `<module>`.
- **Falta una sección en la salida** — la ejecución se detiene cuando la
  respuesta de `SHOW STATS` no contiene una sección que el plugin espera, así
  que las secciones posteriores no se publican. Compare la salida con una
  consulta `SHOW STATS` directa en la instancia.
- **Nombres de módulo repetidos** — la sección devolvió varias filas. Consulte
  [Cómo leer los módulos](#como-leer-los-modulos).

## Referencia

### Parámetros de línea de comandos

| Nombre | Obligatorio | Valor por defecto | Descripción |
|--------|-------------|-------------------|-------------|
| `--host` | Sí | — | Nombre de host o dirección IP de InfluxDB. No incluya el esquema ni el puerto |
| `--port` | No | `8086` | Puerto TCP de la API HTTP de InfluxDB |
| `--user` | No | — | Usuario para la autenticación en InfluxDB. Se usa solo junto con `--password` |
| `--password` | No | — | Contraseña para `--user`. Se usa solo junto con `--user` |
| `--as_agent_plugin` | No | `0` | `1` imprime los módulos como XML en la salida estándar. Cualquier otro entero mantiene el modo plugin de servidor. Un valor no numérico detiene la ejecución con un error |
| `-g`, `--group` | No | `genieacs` | Solo en modo servidor. Grupo de Pandora FMS que se escribe en los documentos de agente generados. El valor por defecto no es un ID de grupo numérico; indique un ID de grupo existente |
| `--data_dir` | No | `/var/spool/pandora/data_in/` | Solo en modo servidor. Directorio donde se escriben los documentos de agente. Debe existir y ser escribible por el usuario que ejecuta el plugin |

### Ejecución por línea de comandos

```text
<PLUGIN_EXECUTABLE> [--host <HOST>] [--port <PORT>] [--user <USER>] [--password <PASSWORD>] [-g <GROUP>] [--data_dir <DIR>] [--as_agent_plugin <0|1>]
```

| Condición | Comportamiento |
|-----------|----------------|
| Falta `--host` | El plugin imprime el resumen de uso en la salida de error estándar y termina con estado 2 |
| `--help` | El plugin imprime el resumen de uso y termina con estado 0 |
| Solo se establece una de `--user` y `--password` | El plugin se conecta sin autenticación |
| `--as_agent_plugin` tiene un valor no numérico | La ejecución se detiene con un error |
| La petición a InfluxDB falla | La ejecución se detiene con un error y las secciones restantes no se publican |
| Modo servidor, el archivo de destino ya existe | La escritura se omite sin error |
| `--group` o `--data_dir` en modo plugin de agente | Se ignoran |

### Agentes generados

| Agente | Sección de estadísticas | Descripción |
|--------|-------------------------|-------------|
| `InfluxDB_Runtime` | `runtime` | Contadores de asignación de memoria y de ejecución |
| `InfluxDB_queryExecutor` | `queryExecutor` | Contadores de carga de consultas |
| `InfluxDB_Httpd` | `httpd` | Contadores de peticiones de la API HTTP |
| `InfluxDB_Write` | `write` | Contadores de la ruta de escritura |
| `InfluxDB_Subscriber_cq` | `subscriber`, `cq` | Contadores de suscriptores y de consultas continuas |

### Módulos generados

Todos los módulos son de tipo `generic_data`.

#### InfluxDB_Runtime

Sección `runtime`, 15 módulos:

| Módulo |
|--------|
| `Alloc` |
| `Frees` |
| `HeapAlloc` |
| `HeapIdle` |
| `HeapInUse` |
| `HeapObjects` |
| `HeapReleased` |
| `HeapSys` |
| `Lookups` |
| `Mallocs` |
| `NumGC` |
| `NumGoroutine` |
| `PauseTotalNs` |
| `Sys` |
| `TotalAlloc` |

#### InfluxDB_queryExecutor

Sección `queryExecutor`, 5 módulos:

| Módulo |
|--------|
| `queriesActive` |
| `queriesExecuted` |
| `queriesFinished` |
| `queryDurationNs` |
| `recoveredPanics` |

#### InfluxDB_Httpd

Sección `httpd`, 24 módulos:

| Módulo |
|--------|
| `authFail` |
| `clientError` |
| `fluxQueryReq` |
| `fluxQueryReqDurationNs` |
| `pingReq` |
| `pointsWrittenDropped` |
| `pointsWrittenFail` |
| `pointsWrittenOK` |
| `promReadReq` |
| `promWriteReq` |
| `queryReq` |
| `queryReqDurationNs` |
| `queryRespBytes` |
| `recoveredPanics` |
| `req` |
| `reqActive` |
| `reqDurationNs` |
| `serverError` |
| `statusReq` |
| `valuesWrittenOK` |
| `writeReq` |
| `writeReqActive` |
| `writeReqBytes` |
| `writeReqDurationNs` |

#### InfluxDB_Write

Sección `write`, 9 módulos:

| Módulo |
|--------|
| `pointReq` |
| `pointReqLocal` |
| `req` |
| `subWriteDrop` |
| `subWriteOk` |
| `writeDrop` |
| `writeError` |
| `writeOk` |
| `writeTimeout` |

#### InfluxDB_Subscriber_cq

Secciones `subscriber` y `cq`, 5 módulos:

| Módulo |
|--------|
| `createFailures` |
| `pointsWritten` |
| `writeFailures` |
| `queryFail` |
| `queryOk` |

### Identidad del plugin

| Propiedad | Valor |
|-----------|-------|
| Identificador del Marketplace | `pandorafms.influxdb` |
| Nombre | Pandora InfluxDB |
| Versión | `1.0` |
| Paquete | `pandorafms.influxdb.1.0.pspz2` |
| Última actualización del Marketplace | 2025-06-26 |
| Autor | Pandora FMS |
| Disponibilidad | Descarga limitada a usuarios con licencia |
| Licencia | `One` |
