# Pandora Spark

*Última actualización del artículo: 2026-10-26.*

## Qué hace

Pandora Spark lee la API REST de un servidor Apache Spark y convierte las
métricas de los ejecutores de cada aplicación en módulos de Pandora FMS. En cada
ejecución se listan las aplicaciones que conoce el endpoint y, después, los
ejecutores de cada aplicación, y se crea **un agente por aplicación** con un
módulo por cada métrica de ejecutor.

El addon es un **plugin de servidor**. En cada ejecución construye los
documentos de datos de los agentes y los escribe directamente en el directorio
de datos de Pandora FMS, de donde los lee el Data Server. No entrega por
Tentacle, no imprime el XML de los módulos en la salida estándar y no crea
tareas de Discovery: el agente aparece en la consola porque llega su fichero de
datos, no porque lo haya generado una tarea.

El plugin solo lee de Spark: hace dos peticiones HTTP `GET` por aplicación y
nunca escribe en el servidor Spark.

- `http://<ip>/api/v1/applications`: las aplicaciones que se van a monitorizar.
- `http://<ip>/api/v1/applications/<application-id>/executors`: los ejecutores
  de cada una de esas aplicaciones.

El mismo host y el mismo puerto deben servir ambos recursos: el plugin construye
las dos URL a partir del único valor de `-i` (consulte
[Configuración](#configuracion)).

## Preparación

### Compatibilidad

| Alcance | Estado | Evidencia |
|---------|--------|-----------|
| Addon `pandorafms.spark`, versión `1.0` | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del addon](#identidad-del-addon) |
| Pandora FMS NG 784 y posteriores | `Soportado` | El Marketplace indica que todas sus integraciones son compatibles con estas versiones. Es una declaración publicada de compatibilidad que cubre el addon, no un registro de pruebas del mismo |
| Acceso HTTP desde el servidor de Pandora FMS al endpoint REST de Spark | `Requerido` | El plugin consulta `http://<host:puerto>/api/v1/applications` y el recurso de ejecutores de cada aplicación |
| Un host y un puerto que sirvan tanto `/api/v1/applications` como `/api/v1/applications/<application-id>/executors` | `Requerido` | Las dos URL se construyen a partir del único valor que se pasa a `-i` |
| Un endpoint REST de Spark que responda sin autenticación | `Requerido` | El plugin no envía credenciales, token ni sesión |
| Permiso de escritura en el directorio de datos de Pandora FMS | `Requerido` | El plugin escribe los documentos de los agentes en `--data_dir`; no tiene otra vía de entrega |
| Versiones de Spark | `Sin validar` | No se ha publicado ningún registro de pruebas para este addon. La guía antigua indicaba que se había probado en CentOS 7 y Fedora; ninguna evidencia disponible establece un rango de versiones de Spark ni de sistema operativo |
| Sistema operativo del servidor de Pandora FMS | `Sin validar` | No se ha registrado ningún sistema operativo para esta versión |
| Modos de despliegue de Spark (standalone, YARN, Kubernetes) | `Sin validar` | El addon depende de los recursos REST anteriores, no del modo de despliegue |

### Requisitos

1. **Un endpoint de Spark con la API REST accesible** desde el servidor de
   Pandora FMS: la interfaz de aplicación de una aplicación en ejecución, o el
   servidor de historial de Spark para las aplicaciones ya finalizadas.
2. **Un endpoint REST que responda sin autenticación.** Si Spark está configurado
   para exigir autenticación en su API REST, el plugin no tiene forma de
   proporcionarla (consulte
   [Operación y resolución de problemas](#operacion-y-resolucion-de-problemas)).
3. **Un servidor de Pandora FMS con permiso de escritura en el directorio de
   datos**, por defecto `/var/spool/pandora/data_in/`. El plugin escribe ahí, así
   que se ejecuta en el propio servidor de Pandora FMS o en un host que escriba
   en ese mismo directorio.
4. **El Data Server habilitado**, para que se lean los documentos escritos en el
   directorio de datos y los agentes aparezcan en la consola.
5. **El Plugin Server habilitado**, cuando el plugin se registra en la consola y
   se ejecuta desde ella.
6. **El ejecutable `pandora_spark`** del paquete del addon.

### Exponer la API REST de Spark

El plugin puede leer dos vistas distintas de un despliegue de Spark, y el puerto
que se pasa a `-i` decide cuál:

| Qué se quiere monitorizar | Endpoint que lo sirve | Puerto por defecto |
|---------------------------|-----------------------|--------------------|
| Aplicaciones en ejecución | La interfaz de aplicación del driver | `4040` |
| Aplicaciones ya finalizadas | El servidor de historial de Spark | `18080` |

Son los puertos por defecto de Spark; el plugin no presupone ninguno de los dos,
consulta el puerto que se le pase.

En aplicaciones en ejecución, la interfaz de la primera aplicación ocupa el
`4040` y cada aplicación concurrente adicional que no pueda ocuparlo toma el
siguiente puerto libre. Por tanto, una ejecución con
`-i <SPARK_HOST>:4040` ve las aplicaciones publicadas en ese puerto, no todas
las del clúster.

Para las aplicaciones finalizadas, habilite el registro de eventos y el servidor
de historial en el lado de Spark. En `spark-defaults.conf`, por ejemplo:

```apache
spark.eventLog.enabled           true
spark.eventLog.dir               <EVENT_LOG_PATH>
spark.history.fs.logDirectory    <EVENT_LOG_PATH>
```

Las dos claves de ruta deben apuntar a la misma ubicación, y el servidor de
historial debe poder leerla. Inicie el servidor de historial con el script que acompaña a
la instalación de Spark, junto a los de arranque del maestro y de los workers:

```bash
<SPARK_HOME>/sbin/start-history-server.sh
```

Solo debe ser accesible desde el servidor de Pandora FMS el puerto que realmente
se consulte. El plugin hace peticiones HTTP simples a ese puerto y nada más, así
que los puertos de maestro, worker y envío que un clúster de Spark necesita para
su propio funcionamiento no forman parte de esta configuración.

Compruebe el endpoint antes de configurar el plugin:

```bash
curl -s 'http://<SPARK_HOST>:<SPARK_PORT>/api/v1/applications'
```

La respuesta debe ser una lista JSON de aplicaciones. Una lista vacía (`[]`)
significa que el endpoint está vivo pero no conoce ninguna aplicación: el
servidor de historial todavía no tiene registros de eventos, o no se ha enviado
ninguna aplicación en ese puerto de interfaz.

### Instalar el addon

Descargue el paquete desde la entrada del Marketplace de Pandora FMS, cuya
descarga está limitada a usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.spark](https://marketplace.pandorafms.com/entries/pandorafms.spark)

El paquete es `pandorafms.spark.1.0.pspz2`. Cárguelo con el gestor de paquetes de
la consola o registre el plugin a mano:

1. Copie el ejecutable `pandora_spark` al servidor de Pandora FMS, por ejemplo en
   `/usr/share/pandora_server/util/plugin/`, y dele permiso de ejecución:

    ```bash
    sudo chmod 0755 /usr/share/pandora_server/util/plugin/pandora_spark
    ```

2. Regístrelo en **Servidores → Plugins**, como se describe en
   [Registrar el plugin en la consola](#registrar-el-plugin-en-la-consola).

No hay que instalar nada en el servidor Spark ni se necesitan herramientas
cliente de Spark en el servidor de Pandora FMS.

## Configuración

Toda la configuración del plugin es su línea de comandos. No lee ningún fichero
de configuración ni ninguna variable de entorno.

### Línea de comandos

```bash
./pandora_spark -i <SPARK_HOST>:<SPARK_PORT>
```

- **`-i`, `--ip`** es obligatorio y recibe `host:puerto` **sin esquema**. El
  plugin antepone `http://` al valor, así que incluya el puerto del endpoint que
  sirve la API REST (`4040` u `18080` por defecto, consulte
  [Exponer la API REST de Spark](#exponer-la-api-rest-de-spark)). Un valor con
  su propio esquema construye una URL inválida y la ejecución termina con el
  error de conectividad.
- **`-g`, `--group`** establece el grupo de los agentes generados. Su valor por
  defecto es `weblogic`, de modo que una ejecución que lo omita deja todos los
  agentes de Spark en ese grupo; indique explícitamente el grupo que quiera.
- **`--data_dir`** establece el directorio donde se escriben los documentos de
  los agentes. Su valor por defecto es `/var/spool/pandora/data_in/`.

La misma ejecución con todas las opciones:

```bash
./pandora_spark -i <SPARK_HOST>:<SPARK_PORT> -g <GROUP_NAME> --data_dir /var/spool/pandora/data_in/
```

No hay fichero de opciones, ni entrega por Tentacle, ni TLS, ni proxy, ni entrada
de credenciales: el endpoint se consulta por HTTP simple y cualquiera que pueda
alcanzarlo puede leer las métricas.

`-h` y `--help` imprimen el resumen de uso. Una ejecución sin `-i` imprime la
línea de uso y el error de argumento obligatorio en la salida de error y termina
con estado `2` sin consultar nada.

### Registrar el plugin en la consola

El plugin está pensado para que lo ejecute el Plugin Server de Pandora FMS, de
modo que Pandora FMS lo lanza con la programación de un módulo de plugin:

1. Abra **Servidores → Plugins** y registre el plugin con un nombre, la
   descripción que prefiera y el tiempo de espera máximo que quiera para una
   ejecución.
2. En **Comando del plugin**, indique la ruta absoluta del ejecutable en el
   servidor de Pandora FMS, por ejemplo
   `/usr/share/pandora_server/util/plugin/pandora_spark`.
3. En **Parámetros del plugin**, use las macros de plugin `_field1_`, `_field2_`,
   ... como marcadores:

    ```text
    -i _field1_ -g _field2_ --data_dir _field3_
    ```

4. En **Parámetros macro**, describa cada campo. El ejemplo usa estos valores:

    | Campo | Descripción | Valor de ejemplo |
    |-------|-------------|------------------|
    | `_field1_` | Endpoint REST de Spark como `host:puerto`, sin esquema | `<SPARK_HOST>:4040` |
    | `_field2_` | Grupo de los agentes generados | `Spark` |
    | `_field3_` | Directorio de datos de Pandora FMS | `/var/spool/pandora/data_in/` |

<!-- SCREENSHOT NEEDED: formulario de registro de plugin de servidor en Pandora FMS para pandora_spark, con los tres parámetros macro rellenos y sin hosts reales. -->

Una vez registrado, cree un módulo de plugin que lo ejecute, con los mismos
valores de campo. El módulo se ejecuta en el servidor de Pandora FMS y cada
ejecución crea los agentes de Spark. El módulo recibe la salida del plugin (`1`
en una ejecución correcta), mientras que las métricas de Spark llegan por el
directorio de datos, en los agentes con el nombre de cada aplicación.

El valor de `-g` que definan las macros lo usa cada ejecución de ese módulo. Si
se monitorizan dos endpoints de Spark, registre el plugin una vez y cree un
módulo por endpoint con sus propios campos, usando un grupo distinto para cada
uno, de forma que los dos conjuntos de agentes queden separados.

<!-- SCREENSHOT NEEDED: formulario de creación del módulo de plugin para pandora_spark con los valores de campo y el servidor de Pandora FMS de destino. -->

### Entrega y permisos

- Cada ejecución escribe ficheros con el nombre
  `<nombre-del-agente>.<segundos-epoch>.data` en `--data_dir`. Cada aplicación de
  Spark tiene su propio nombre de agente, así que las aplicaciones no comparten
  documentos.
- El directorio debe existir y ser escribible por el usuario que ejecuta el
  plugin. Cuando la escritura falla, el plugin no informa de nada y aun así
  termina con `1` (consulte
  [Operación y resolución de problemas](#operacion-y-resolucion-de-problemas)).
- El Data Server de Pandora FMS debe poder leer los ficheros. No cambie su
  propietario ni los mueva: el Data Server los elimina después de procesarlos.
- No viaja nada por la red hacia Pandora FMS. Si el plugin se ejecuta en un
  servidor de Pandora FMS remoto, `--data_dir` debe apuntar al directorio de
  datos de ese mismo servidor, no al del servidor principal.

## Verificación

1. Confirme que el endpoint responde con una lista JSON:

    ```bash
    curl -s 'http://<SPARK_HOST>:<SPARK_PORT>/api/v1/applications'
    ```

2. Ejecute el plugin una vez desde un terminal en el servidor de Pandora FMS:

    ```bash
    ./pandora_spark -i <SPARK_HOST>:<SPARK_PORT> -g <GROUP_NAME>
    ```

3. Una ejecución correcta imprime `1` y termina con estado `0`. Después, los
   ficheros de datos están en el directorio de datos:

    ```bash
    ls -l /var/spool/pandora/data_in/Spark_application*
    ```

    Los ficheros desaparecen a medida que el Data Server los procesa, así que un
    listado vacío poco después de la ejecución también puede significar que los
    documentos ya se han consumido. Compruébelo en la consola.

4. En la consola aparece un agente por cada aplicación de Spark, con sus módulos,
   en el siguiente ciclo de datos.

<!-- SCREENSHOT NEEDED: vista de detalle de un agente de aplicación de Spark en Pandora FMS con los módulos de ejecutor recibidos. -->

Si no se puede alcanzar el endpoint, la ejecución imprime `0` en la salida
estándar y este mensaje en la salida de error, y termina con estado `1`:

```text
Error requesting http://<SPARK_HOST>:<SPARK_PORT>/api/v1/applications, please check conectivity
```

## Entender los resultados

### Agentes generados

El addon crea **un agente por aplicación** de las que devuelve la primera
petición. El agente se nombra a partir del identificador de la aplicación, de
modo que un identificador como `application_1630567890123_0001` produce el
nombre de agente `Spark_applicationapplication_1630567890123_0001`: el prefijo
`Spark_application` se antepone al identificador tal como lo informa Spark, sin
separador.

| Propiedad | Valor |
|-----------|-------|
| Nombre del agente | `Spark_application` seguido del identificador de la aplicación |
| Alias del agente | `Spark_application` seguido del nombre de la aplicación |
| Descripción | `Spark_application_detailed stats` |
| Dirección | `127.0.0.1` |
| Grupo | El valor de `-g`; `weblogic` cuando se omite la opción |
| Agente padre | Ninguno |
| Intervalo | Sin definir: el agente conserva el intervalo que Pandora FMS asigna por defecto |

Hay dos consecuencias que conviene conocer antes de construir alertas sobre
estos agentes:

- La dirección está fijada en `127.0.0.1` y no identifica al servidor Spark. En
  la consola el agente parece local aunque el endpoint sea remoto.
- El nombre de la aplicación se copia en el alias del agente sin escapar. Un
  nombre que contenga una comilla simple (`'`) produce un documento que Pandora
  FMS no puede leer y el agente no se crea.

### Qué entrega una ejecución

- El plugin pide la lista de ejecutores de cada aplicación, una aplicación tras
  otra, y construye el documento de cada agente con los datos de ejecutor de esa
  aplicación.
- **Se escribe un documento por ejecutor.** Los documentos se nombran a partir
  del agente y del segundo de la ejecución, así que todos los ejecutores
  procesados dentro del mismo segundo producen el mismo nombre de fichero: se
  conserva el primero y los siguientes se descartan sin ningún mensaje. En la
  práctica, una ejecución entrega los módulos del primer ejecutor de cada
  aplicación, más los de aquellos ejecutores que se procesen en un segundo
  posterior.
- **La lista de módulos no se reinicia entre aplicaciones.** El documento de la
  segunda aplicación y de las siguientes arrastra además una copia de los
  módulos de las aplicaciones procesadas antes en la misma ejecución, de modo
  que los nombres de módulo se repiten dentro de un mismo documento. Con una
  sola aplicación, que es el caso habitual, esto no tiene efecto.

### Módulos

Cada ejecutor produce 14 módulos cuyo nombre es el identificador del ejecutor
seguido del nombre de la métrica, concatenado sin separador: un ejecutor con
identificador `1` publica `1hostPort`, `1rddBlocks`, `1memoryUsed`, etc. El
identificador es `driver` para el driver y un número para el resto de
ejecutores. Dos aplicaciones que reutilicen los mismos identificadores de
ejecutor producen módulos con los mismos nombres, un conjunto por agente.

`id` y `hostPort` son módulos de texto (`generic_data_string`); los otros doce
son módulos numéricos (`generic_data`) sin unidad. El plugin copia cada valor tal
como lo devuelve la API: no convierte, redondea, reescala ni añade unidades, y no
define umbrales ni alertas. La lista completa con el significado de cada valor
está en [Módulos generados](#modulos-generados).

## Operación y resolución de problemas

### Operación diaria

- El plugin no guarda estado entre ejecuciones: cada ejecución consulta el
  endpoint en ese momento, así que puede lanzarse a mano en cualquier momento sin
  afectar a la siguiente ejecución programada.
- No hay tiempo de espera en las peticiones. Un endpoint que acepta la conexión y
  no responde mantiene la ejecución bloqueada hasta que el tiempo de espera del
  Plugin Server la termine, así que defina un tiempo de espera máximo en la
  definición del plugin.
- No hay soporte de autenticación: ni usuario, ni contraseña, ni token, ni
  certificado de cliente TLS. Una API REST de Spark que exija autenticación
  responde `401`, el plugin no puede leer la respuesta como lista de aplicaciones
  y la ejecución termina con el error de conectividad.
- Solo se usa HTTP simple: todas las peticiones van a `http://`, así que un
  endpoint que solo ofrezca HTTPS no se puede monitorizar con este addon.
- El grupo por defecto es `weblogic`. Los agentes creados por una ejecución que
  omita `-g` quedan en ese grupo y pasan desapercibidos con facilidad en la
  consola.
- Un fallo de escritura es silencioso: cuando el directorio de datos no existe o
  no es escribible, la ejecución imprime `1` y no informa de nada. No use la
  salida del plugin para decidir que los datos han llegado; compruébelo en la
  consola.
- Una ejecución contra un endpoint de Spark sin aplicaciones imprime `1` y no
  crea ningún agente. Es el resultado esperado, no un error.

### Resolución de problemas

- **La ejecución imprime `0` y el mensaje `Error requesting .../api/v1/applications`**:
  la primera petición no devolvió una lista de aplicaciones legible. Compruebe el
  puerto, el cortafuegos entre el servidor de Pandora FMS y Spark, y que el
  endpoint responde a `curl` desde ese mismo host. El mismo mensaje aparece
  cuando la respuesta no es JSON, incluido un `401` de un endpoint que exige
  autenticación.
- **La ejecución imprime `0` y el mensaje nombra `.../executors`**: se leyó la
  lista de aplicaciones, pero no los ejecutores de la aplicación indicada en el
  mensaje. La ejecución se detiene ahí: los documentos de las aplicaciones ya
  procesadas se escriben y los de las restantes no. Compruebe que el mismo puerto
  sirve el recurso de ejecutores de esa aplicación, lo que no ocurre si la
  aplicación ha pasado al servidor de historial entretanto.
- **La ejecución imprime `1` pero no aparece ningún agente en la consola**: los
  documentos no se escribieron o no se leyeron. Confirme que `--data_dir` es el
  directorio de datos del servidor de Pandora FMS que está en marcha, que es
  escribible por el usuario del plugin y que el Data Server está habilitado.
  Recuerde que el plugin no informa de los fallos de escritura.
- **Un agente muestra menos ejecutores de los que tiene la aplicación**: los
  documentos de los demás ejecutores se escribieron dentro del mismo segundo y se
  descartaron por la colisión de nombres de fichero. Vuelva a ejecutar el plugin
  más tarde o acepte que el addon publica el primer ejecutor de cada aplicación
  por ejecución.
- **El agente muestra módulos de otra aplicación**: las dos aplicaciones se
  procesaron en la misma ejecución y la lista de módulos se comparte entre ellas.
  Ejecute el plugin con una aplicación por ejecución cuando necesite un agente
  limpio.
- **Un módulo no tiene valor o falta el agente entero**: revise si el nombre de
  la aplicación contiene una comilla simple, que rompe el documento como se
  explica en [Agentes generados](#agentes-generados).
- **Los agentes están en el grupo equivocado**: se omitió `-g` y se aplicó el
  valor por defecto `weblogic`, o la macro registrada tiene un valor vacío.
- **Las métricas parecen congeladas**: el plugin informa de los contadores del
  ejecutor en el momento de la consulta. Una aplicación finalizada conserva en el
  servidor de historial los valores de su último estado, así que un endpoint de
  historial muestra los mismos números ejecución tras ejecución. Use `4040` para
  seguir una aplicación en vivo.

## Referencia

### Opciones de línea de comandos

| Nombre | Obligatorio | Por defecto | Descripción |
|--------|-------------|-------------|-------------|
| `-i`, `--ip` | Sí | — | Endpoint REST de Spark como `host:puerto`, sin esquema. El plugin llama a `http://<valor>/api/v1/applications` y a `http://<valor>/api/v1/applications/<application-id>/executors`. |
| `-g`, `--group` | No | `weblogic` | Grupo asignado a los agentes generados. |
| `--data_dir` | No | `/var/spool/pandora/data_in/` | Directorio donde se escriben los documentos de los agentes. Debe existir y ser escribible por el usuario que ejecuta el plugin. |
| `-h`, `--help` | No | — | Imprime el resumen de uso y termina. |

El plugin no lee ningún fichero de configuración ni ninguna variable de entorno,
y no acepta credenciales. Una ejecución sin `-i` termina con estado `2`.

### Salida y código de salida

| Situación | Salida estándar | Salida de error | Código de salida |
|-----------|-----------------|-----------------|------------------|
| Ejecución correcta | `1` | — | `0` |
| Falla la petición de aplicaciones, o su respuesta no es una lista JSON | `0` | `Error requesting <url>, please check conectivity` | `1` |
| Falla la petición de ejecutores de una aplicación | `0` | `Error requesting <url>, please check conectivity` | `1` |
| Falta `-i` | — | Línea de uso y error de argumento obligatorio | `2` |

Una ejecución que no puede escribir un documento de datos sigue informando de
éxito: el fallo no se refleja ni en la salida ni en el código de salida.

### Agentes generados

| Propiedad | Valor |
|-----------|-------|
| Nombre del agente | `Spark_application` + identificador de la aplicación, concatenado sin separador |
| Alias del agente | `Spark_application` + nombre de la aplicación |
| Descripción | `Spark_application_detailed stats` |
| Dirección | `127.0.0.1` |
| Grupo | Valor de `-g`; `weblogic` por defecto |
| Agente padre | Ninguno |
| Intervalo | Sin definir |
| Marca de tiempo | Momento de la ejecución, `AAAA/MM/DD HH:MM:SS` |
| Cardinalidad | Un agente por aplicación devuelta por el endpoint |

### Módulos generados

`<ejecutor>` es el identificador de ejecutor que informa Spark: `driver` para el
driver y un número para cada ejecutor.

| Nombre del módulo | Tipo | Valor |
|-------------------|------|-------|
| `<ejecutor>id` | `generic_data_string` | Identificador del ejecutor |
| `<ejecutor>hostPort` | `generic_data_string` | Host y puerto del ejecutor |
| `<ejecutor>rddBlocks` | `generic_data` | Bloques RDD que retiene el ejecutor |
| `<ejecutor>memoryUsed` | `generic_data` | Memoria usada, en bytes |
| `<ejecutor>diskUsed` | `generic_data` | Espacio en disco usado, en bytes |
| `<ejecutor>activeTasks` | `generic_data` | Tareas en ejecución en el ejecutor |
| `<ejecutor>failedTasks` | `generic_data` | Tareas fallidas en el ejecutor |
| `<ejecutor>completedTasks` | `generic_data` | Tareas completadas por el ejecutor |
| `<ejecutor>totalTasks` | `generic_data` | Tareas asignadas al ejecutor |
| `<ejecutor>totalDuration` | `generic_data` | Tiempo de tarea acumulado, en milisegundos |
| `<ejecutor>totalInputBytes` | `generic_data` | Bytes leídos por el ejecutor |
| `<ejecutor>totalShuffleRead` | `generic_data` | Bytes leídos en shuffles |
| `<ejecutor>totalShuffleWrite` | `generic_data` | Bytes escritos en shuffles |
| `<ejecutor>maxMemory` | `generic_data` | Memoria disponible para el ejecutor |

Los dos módulos de texto se publican con la unidad vacía; los numéricos no llevan
unidad. Los valores se envían tal como los devuelve la API, de modo que un campo
que Spark informa con su unidad en el texto (como ocurre con `maxMemory`) llega
al módulo con ese texto, y la comparación, los umbrales y la representación del
módulo quedan en manos de Pandora FMS.

### Identidad del addon

| Campo | Valor |
|-------|-------|
| Identificador del Marketplace | `pandorafms.spark` |
| Nombre en el Marketplace | Pandora Spark |
| Versión del addon | `1.0` |
| Paquete del Marketplace | `pandorafms.spark.1.0.pspz2` |
| Última actualización en el Marketplace | 2025-06-27 |
| Licencia | One — descarga limitada a usuarios con licencia |
| Tipo en el Marketplace | Miscelaneus |
| Flujo de trabajo | Plugin de monitorización, modo plugin de servidor |
| Ejecutable | `pandora_spark` |
