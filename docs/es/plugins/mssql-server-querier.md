# MSSQL Server Querier Tool

*Última actualización del artículo: 2026-10-26.*

## Qué hace

`msql_query` ejecuta una consulta SQL contra una base de datos Microsoft SQL
Server e imprime el resultado en la salida estándar. Pandora FMS lo ejecuta
como plugin de servidor, por lo que esa salida es el valor del módulo que lo
llama: un contador, un tamaño, un código de estado o cualquier otro valor
único que pueda devolver una consulta.

Cada ejecución abre una conexión, ejecuta una consulta y termina. El comando
no guarda estado ni crea agentes. El módulo, su intervalo, sus umbrales y sus
alertas pertenecen a Pandora FMS; la consulta solo aporta el valor.

El addon documenta dos formas de invocación bajo el mismo nombre `msql_query`:

- **Forma con opciones.** La conexión y la consulta se pasan como opciones
  (`-Q`, `-U`, `-P`, `-H`, `-D`). La salida empieza por una línea de cabecera
  con los nombres de las columnas y continúa con una línea por fila, separada
  por tabuladores. La conexión no selecciona ninguna base de datos, por lo que
  SQL Server usa la base de datos predeterminada del usuario.
- **Forma posicional.** La conexión y la consulta se pasan como argumentos
  ordenados. La salida no tiene línea de cabecera y los campos de cada fila se
  unen con un delimitador, `,` por defecto.

Ambas formas devuelven texto sin formato: los resultados van a la salida
estándar y los errores al error estándar. Ninguna escribe ficheros, envía
datos a Pandora FMS por sí misma ni devuelve el resultado en un formato
estructurado.

La entrada del Marketplace indica que este addon ya no se mantiene ni
actualiza activamente.

Esta página no describe el addon Microsoft SQL Server Discovery
(`pandorafms.mssql`), que crea agentes y módulos a partir de tareas de
Discovery; consulte [Microsoft SQL Server Discovery](../discovery/mssql-discovery.md).

## Preparación

### Compatibilidad

| Alcance | Estado | Evidencia |
| --- | --- | --- |
| Addon `pandorafms.mssql_querier`, versión `1.0` | Objetivo documentado | La versión del paquete del Marketplace que describe esta página. Consulte [Identidad del addon](#identidad-del-addon) |
| Pandora FMS NG 784 y posteriores | `Soportado` | El Marketplace indica que sus integraciones son compatibles con Pandora FMS NG 784 y versiones posteriores |
| Acceso de red desde el servidor de Pandora FMS a la instancia de SQL Server (TCP, `1433` por defecto) | `Requerido` | Ambas formas abren una conexión TCP a SQL Server. La forma posicional usa siempre el puerto `1433` |
| Un usuario de SQL Server autorizado a ejecutar la consulta | `Requerido` | El comando se autentica con el usuario y la contraseña que se le pasan |
| Microsoft ODBC Driver 18 for SQL Server en el servidor de Pandora FMS | `Requerido` | La forma posicional solicita ese controlador por su nombre |
| Un controlador ODBC para SQL Server y el paquete DBI ODBC en el servidor de Pandora FMS | `Requerido` | La forma con opciones se conecta mediante DBI sobre ODBC |
| Versiones de Microsoft SQL Server | `Sin validar` | No se ha registrado una matriz de versiones de SQL Server para este addon |
| Sistema operativo del servidor de Pandora FMS | `Sin validar` | No se ha registrado ningún sistema operativo para esta versión |

### Requisitos

1. **Un servidor de Pandora FMS** que pueda alcanzar la instancia de SQL
   Server por red. El comando se ejecuta en el servidor de Pandora FMS, no en
   el host de la base de datos.
2. **Un usuario y una contraseña de SQL Server** que puedan conectarse a la
   base de datos y ejecutar la consulta configurada. No se publica un conjunto
   de permisos más concreto para este addon: conceda al usuario solo aquello
   que lean las consultas.
3. **Los componentes de conectividad que exige la forma de invocación
   utilizada**, según [Compatibilidad](#compatibilidad).
4. **El ejecutable `msql_query`** del paquete del addon, copiado al servidor
   de Pandora FMS.

El comando no lee ningún fichero de configuración ni variables de entorno:
toda su configuración son argumentos de línea de comandos.

### Instalar el addon

Descargue el paquete desde la entrada del Marketplace, cuya descarga está
limitada a usuarios con licencia, y extraiga el ejecutable. La documentación
del fabricante llama al comando `msql_query`.

Cópielo al servidor de Pandora FMS y dele permisos de ejecución:

```bash
sudo cp msql_query /usr/share/pandora_server/util/plugin/msql_query
sudo chmod 0755 /usr/share/pandora_server/util/plugin/msql_query
```

No hay que instalar nada en el host de SQL Server y no interviene ningún
agente.

## Configuración

Toda la configuración es una línea de comandos: la forma de invocación, los
valores de conexión y la consulta. Pandora FMS ejecuta el comando de dos
maneras:

- **Como plugin de servidor.** Registre el ejecutable una vez en la consola y
  cree el módulo que lo llama. La salida estándar de cada ejecución pasa a ser
  el valor del módulo.
- **Manual o desde un planificador** como `cron`, para probar el comando u
  obtener el valor fuera de un módulo de la consola.

### Registrar el comando como plugin de servidor

1. Abra **Servers → Plugins** y registre un plugin de servidor nuevo.
2. Establezca su comando en la ruta absoluta del ejecutable, por ejemplo
   `/usr/share/pandora_server/util/plugin/msql_query`.
3. Escriba los parámetros con las opciones de la forma que utilice y sustituya
   la consulta y las credenciales por campos del plugin: `_field1_`,
   `_field2_`, ...

```text
-Q _field1_ -U _field2_ -P _field3_ -H _field4_
```

| Campo | Descripción |
| --- | --- |
| `_field1_` | Consulta SQL |
| `_field2_` | Usuario de SQL Server |
| `_field3_` | Contraseña de ese usuario; marque el valor como oculto |
| `_field4_` | Host de SQL Server, incluida la instancia cuando sea necesaria |

El mismo registro sirve para todas las consultas: cada módulo rellena los
campos con su propia consulta y sus propias credenciales. Para la forma
posicional, escriba los argumentos en su orden y use los campos en las mismas
posiciones.

<!-- SCREENSHOT NEEDED: formulario de registro de plugin de servidor para msql_query, con la ruta del comando y los campos de parámetros, una consulta y credenciales enmascaradas. -->

### Invocación con opciones

```bash
./msql_query -Q "SELECT 1 AS total" -U <USERNAME> -P <PASSWORD> -H <TARGET_HOST>
```

- `-Q` es la consulta. Sin esta opción, el comando imprime su resumen de uso y
  termina sin conectarse.
- `-H` toma `localhost` por defecto.
- `-D` establece el nombre del controlador ODBC y toma
  `ODBC Driver 17 for SQL Server` por defecto.
- No hay opción de base de datos: la conexión no selecciona ninguna y SQL
  Server usa la base de datos predeterminada del usuario. Cualifique los
  objetos como `base_de_datos.esquema.tabla` cuando la consulta deba leer otra
  base de datos.
- Las opciones se leen por parejas y su letra no distingue mayúsculas de
  minúsculas. Un argumento que el comando no reconoce hace que imprima el
  resumen de uso y termine.
- La salida contiene una primera línea con los nombres de las columnas y
  después una línea por fila, separada por tabuladores.

### Invocación posicional

```bash
./msql_query "<TARGET_HOST>" "<USERNAME>" "<PASSWORD>" "<DB_NAME>" "SELECT 1 AS total" "none"
```

- El orden es host, usuario, contraseña, base de datos, consulta, texto para
  resultado vacío y delimitador.
- En la práctica se requieren seis argumentos. Con menos, el comando imprime
  `Not enough arguments in call.` y el resumen de uso, aunque la documentación
  del fabricante marca el texto para resultado vacío como opcional. Pase
  cualquier valor, por ejemplo `none`, cuando no lo necesite.
- El texto para resultado vacío se acepta pero nunca se imprime en esta
  versión: cuando la consulta no devuelve filas, el comando no imprime nada.
- El puerto está fijado en `1433`. Esta forma no tiene ningún argumento para
  cambiarlo.
- El delimitador es `,` salvo que se pase un séptimo argumento. Un delimitador
  pasado como sexto argumento se lee como texto para resultado vacío y no
  tiene efecto.
- La salida no tiene línea de cabecera: cada fila se imprime con sus campos
  unidos por el delimitador.
- La conexión establece `TrustServerCertificate=yes` y acepta cualquier
  certificado del servidor.

La misma ejecución con `;` como delimitador de campos:

```bash
./msql_query "<TARGET_HOST>" "<USERNAME>" "<PASSWORD>" "<DB_NAME>" "SELECT 1 AS total" "none" ";"
```

### Credenciales y transporte

- Ambas formas reciben la contraseña como argumento de línea de comandos. Es
  visible en la lista de procesos mientras el comando se ejecuta y permanece
  en el historial de comandos. En la consola se guarda con la definición del
  plugin o del módulo. Use un usuario dedicado, limitado a lo que lean las
  consultas, y restrinja quién puede leer las definiciones de los módulos y
  quién puede inspeccionar los procesos del servidor.
- Si invoca el comando desde un script o una entrada de `cron`, ese fichero
  contiene la contraseña en texto plano. Protéjalo con permisos de fichero.
- La cadena de conexión se compone por concatenación: un usuario o una
  contraseña que contenga `;` la rompe y la conexión falla. Use credenciales
  que no incluyan ese carácter.
- La forma con opciones no pasa ninguna opción de cifrado. El cifrado y la
  validación de certificados dependen de la configuración del controlador
  ODBC en el servidor de Pandora FMS.
- La forma posicional establece siempre `TrustServerCertificate=yes`: el
  cliente acepta cualquier certificado que presente el servidor, por lo que la
  conexión no autentica a SQL Server. Úsela solo en una red de confianza o
  contra una instancia cuya identidad verifique por otro medio.

## Verificación

Ejecute manualmente la forma que haya configurado antes de confiar en el
módulo. Una consulta escalar sin dependencias de tablas demuestra a la vez la
conectividad, la autenticación y la forma de la salida.

Forma con opciones:

```bash
./msql_query -Q "SELECT 1 AS total" -U <USERNAME> -P <PASSWORD> -H <TARGET_HOST>
```

Salida esperada: el nombre de la columna y después el valor.

```text
total
1
```

Forma posicional:

```bash
./msql_query "<TARGET_HOST>" "<USERNAME>" "<PASSWORD>" "<DB_NAME>" "SELECT 1 AS total" "none"
```

Salida esperada:

```text
1
```

Repita la ejecución con una contraseña incorrecta. La forma con opciones
imprime `Can't connect to <TARGET_HOST>: ...` en el error estándar y termina
con un código de salida distinto de cero. La forma posicional imprime el error
del controlador de base de datos en el error estándar y termina con un código
de salida distinto de cero.

En la consola, el módulo que llama al comando muestra el valor que vio en la
ejecución manual. Confirme que el módulo usa la misma consulta y el mismo
usuario.

## Entender los resultados

El comando devuelve texto, y ese texto es todo el valor del módulo. No
clasifica el resultado, no añade unidades ni compara umbrales: los umbrales,
las alertas y la configuración de gráficas se definen en el módulo de Pandora
FMS, y la consulta solo aporta el valor sobre el que actúan.

- **Un valor por ejecución.** Un módulo guarda un valor. Escriba consultas que
  devuelvan una sola fila y, para módulos numéricos, una sola columna. Ambas
  formas imprimen todas las filas que devuelve la consulta, así que una
  consulta con varias filas produce varias líneas de salida.
- **Línea de cabecera (solo forma con opciones).** La primera línea de salida
  contiene los nombres de las columnas, por lo que un resultado de una fila
  ocupa dos líneas. La forma posicional imprime solo los datos de la fila.
- **Delimitador (solo forma posicional).** Los campos de una fila se unen con
  `,` salvo que se pase otro delimitador. Con varias columnas, el valor del
  módulo contiene los campos unidos.
- **Resultado vacío.** La forma con opciones imprime solo la línea de
  cabecera; la forma posicional no imprime nada. El argumento para resultado
  vacío de la forma posicional no tiene efecto.
- **Valores `NULL`.** Un valor `NULL` se imprime como `None` en la forma
  posicional y como un campo vacío en la forma con opciones. Use `ISNULL()` o
  `COALESCE()` en la consulta cuando un módulo numérico deba recibir siempre
  un número.
- **Código de salida.** Una ejecución correcta termina con `0`. Un error de
  conexión o de SQL termina con un código distinto de cero. Un error de
  argumentos imprime el resumen de uso y termina con `0`, por lo que el módulo
  puede recibir el texto de uso como valor.

## Operar y resolver problemas

- Cada ejecución es independiente: el comando se conecta, ejecuta la consulta
  y termina. No hay demonio, caché ni estado que reiniciar.
- El comando no tiene un tiempo de espera propio. Una consulta que se bloquea
  mantiene la ejecución abierta hasta que SQL Server o quien la invocó la
  detengan. Configure un tiempo de espera en el plugin o en el módulo de
  Pandora FMS cuando una consulta pueda tardar.
- Evite ejecutar el comando desde un intérprete interactivo con la contraseña
  real cuando ese intérprete guarde el historial. Use el módulo de la consola o
  un script protegido.

| Síntoma | Causa y solución |
| --- | --- |
| Aparece el resumen de uso en lugar de un valor (forma con opciones) | Falta `-Q` o un argumento no se reconoció como opción. Revise las letras de las opciones y que cada una tenga su valor. El comando termina con `0`, por lo que el módulo puede guardar el texto de uso. |
| `Not enough arguments in call.` o `Too much arguments in call.` (forma posicional) | Hay menos de seis argumentos o más de siete. Añada el argumento para resultado vacío aunque no lo necesite, elimine los argumentos sobrantes y escriba la consulta como un solo argumento. |
| `Can't connect to <TARGET_HOST>: ...` (forma con opciones) | El host, la instancia, el usuario o la contraseña son incorrectos, el puerto `1433` no es alcanzable o la instancia no acepta inicios de sesión de SQL Server. |
| `Can't prepare statement: ...` o `Problem while executing: ...` (forma con opciones) | La consulta no es válida para el usuario o para la base de datos predeterminada. Ejecute la misma consulta con el mismo usuario en otro cliente SQL. |
| Un error del controlador de base de datos en el error estándar (forma posicional) | La conexión falló o la consulta fue rechazada. El mensaje indica el error del controlador; revise el host, las credenciales, la base de datos y la sintaxis SQL. |
| Un error de controlador o de origen de datos de la capa ODBC | El nombre del controlador ODBC no existe en el servidor. Instale el controlador o indique en `-D` el nombre exacto que tenga el servidor. |
| El módulo no tiene valor | La consulta no devolvió filas o solo devolvió valores `NULL`. Revise la consulta y los datos. |
| Un módulo numérico no tiene datos o tiene un valor inesperado | La salida contiene una línea de cabecera, más de una fila, columnas unidas o `None`. Devuelva un único escalar numérico en una única fila. |
| La conexión falla con una contraseña que contiene `;` | El punto y coma termina el valor en la cadena de conexión. Use una contraseña sin `;`. |

## Referencia

### Identidad del addon

| Propiedad | Valor |
| --- | --- |
| Identificador del Marketplace | `pandorafms.mssql_querier` |
| Nombre | MSSQL Server Querier Tool |
| Versión | `1.0` |
| Última actualización en el Marketplace | 2025-06-27 |
| Categoría | Miscelaneous |
| Licencia | One; la descarga está limitada a usuarios con licencia |
| Estado de mantenimiento | Ya no se mantiene ni actualiza activamente, según el Marketplace |
| Entrada del Marketplace | [pandorafms.mssql_querier](https://marketplace.pandorafms.com/entries/pandorafms.mssql_querier) |

### Parámetros de la invocación con opciones

| Opción | Obligatoria | Por defecto | Descripción |
| --- | --- | --- | --- |
| `-Q` | Sí | — | Consulta SQL que se ejecuta |
| `-U` | Sí | — | Usuario de SQL Server |
| `-P` | Sí | — | Contraseña del usuario |
| `-H` | No | `localhost` | Host de SQL Server, o `host\instance` |
| `-D` | No | `ODBC Driver 17 for SQL Server` | Nombre del controlador ODBC usado en la conexión |

`-D` indica el controlador ODBC, no la base de datos. El comando no tiene
opción de base de datos ni opción de ayuda propia: imprime su resumen de uso
cuando falta la opción de consulta o cuando encuentra un argumento que no
reconoce.

### Parámetros de la invocación posicional

| Posición | Argumento | Obligatorio | Por defecto | Descripción |
| --- | --- | --- | --- | --- |
| 1 | host | Sí | — | `host` o `host\instance`. La conexión usa siempre el puerto TCP `1433` |
| 2 | usuario | Sí | — | Usuario de SQL Server |
| 3 | contraseña | Sí | — | Contraseña del usuario |
| 4 | base de datos | Sí | — | Base de datos que selecciona la conexión |
| 5 | consulta | Sí | — | Consulta SQL que se ejecuta |
| 6 | texto para resultado vacío | Sí en la práctica | — | Se acepta y nunca se imprime en esta versión; pase cualquier valor |
| 7 | delimitador | No | `,` | Separador de campos de cada fila |

### Salida y código de estado

| Condición | Forma con opciones | Forma posicional |
| --- | --- | --- |
| La consulta devuelve filas | Una línea de cabecera con los nombres de las columnas y después una línea por fila separada por tabuladores; código de salida `0` | Una línea por fila separada por el delimitador, sin cabecera; código de salida `0` |
| La consulta no devuelve filas | Solo la línea de cabecera; código de salida `0` | Ninguna salida; código de salida `0` |
| La conexión falla | `Can't connect to ...` en el error estándar; código de salida distinto de cero | El error del controlador en el error estándar; código de salida distinto de cero |
| La consulta falla | `Can't prepare statement: ...` o `Problem while executing: ...` en el error estándar; código de salida distinto de cero | El error del controlador en el error estándar; código de salida distinto de cero |
| Faltan argumentos o no se reconocen | El resumen de uso en la salida estándar; código de salida `0` | El resumen de uso en la salida estándar; código de salida `0` |

Ambas formas devuelven solo texto: los resultados en la salida estándar y los
errores en el error estándar. El comando no lee ningún fichero de
configuración ni variables de entorno y no guarda estado entre ejecuciones.
