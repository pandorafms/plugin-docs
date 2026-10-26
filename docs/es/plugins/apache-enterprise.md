# Apache Enterprise Plugin

*Última actualización del artículo: 2026-10-26.*

## Qué hace

El plugin Apache Enterprise Plugin lee la página `mod_status` de un servidor
Apache HTTP Server y convierte sus contadores en módulos de Pandora FMS: tasas de
peticiones y de tráfico, accesos y tráfico totales, carga de CPU, tiempo de
actividad, hora de reinicio, peticiones en curso, workers inactivos y una
comprobación de disponibilidad.

El plugin se ejecuta como **plugin de agente**. El agente de software de Pandora
FMS lo ejecuta, lee el XML de módulos que imprime en la salida estándar y guarda
los valores en el agente que lo ejecuta. No se instala nada en el servidor
Apache: el plugin solo realiza una petición HTTP a una URL de estado que debe
existir previamente.

Esta página documenta el plugin de monitorización del servidor. El descubrimiento
de servidores Apache y la generación de sus agentes es un addon distinto,
documentado en [Apache Discovery](../discovery/apache-discovery.md).

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
|--------|--------|-----------|
| Addon `Apache`, versión `1.0` | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del addon](#identidad-del-addon) |
| Pandora FMS NG 784 y posteriores | `Supported` | El Marketplace indica que todas sus integraciones son compatibles con estas versiones. Es una declaración pública de compatibilidad que cubre el addon, no un registro de pruebas del mismo |
| `curl` en el host que ejecuta el plugin | `Required` | El plugin obtiene la página de estado ejecutando el comando `curl`; no tiene otro cliente HTTP |
| Acceso de red desde el agente de Pandora FMS a la URL de estado | `Required` | Prerrequisito, no una declaración de compatibilidad |
| Una página `mod_status` de Apache servida por HTTP | `Required` | El plugin analiza el texto de esa página. Consulte [Habilitar la página de estado](#habilitar-la-pagina-de-estado) |
| Credenciales de autenticación básica para la ubicación de estado, cuando está protegida | `Required` cuando la ubicación exige autenticación | El plugin las envía con `-user` y `-pass` |
| Versiones de Apache HTTP Server | `Not validated` | No se ha publicado ningún registro de pruebas de este addon. La guía heredada indicaba Apache 1.3 o posterior; nada en la evidencia disponible establece ese rango |
| Sistema operativo del host que ejecuta el plugin | `Not validated` | No hay un sistema operativo registrado para esta versión. La guía heredada indicaba que se desarrolló y probó en Rocky Linux y Fedora 34; ningún registro lo confirma |
| Conjunto de módulos y MPM de Apache | `Not validated` | Los contadores disponibles dependen de la configuración del servidor, no del plugin |

### Requisitos

1. **`mod_status` habilitado en Apache** y accesible desde el agente de Pandora
   FMS, con `ExtendedStatus On` para que existan los contadores que lee el
   plugin.
2. **Una URL de estado que sirva la página HTML de estado.** El plugin extrae los
   contadores del texto de esa página, así que una variante legible por máquina
   como `server-status?auto` no proporciona las líneas que busca.
3. **`curl` disponible en el `PATH`** del usuario que ejecuta el agente de
   Pandora FMS.
4. **Credenciales de autenticación básica**, cuando la ubicación de estado está
   protegida.
5. **Un agente de software de Pandora FMS** en el host que ejecuta el plugin,
   para ejecutarlo e ingerir sus módulos.

El plugin solo lee la página de estado. Ninguna fuente oficial identifica un
conjunto de permisos de Apache más restrictivo; restrinja quién puede alcanzar la
ubicación de estado, ya que expone datos de las peticiones.

### Habilitar la página de estado

Cree la ubicación de estado en un fichero incluido por la configuración de
Apache. La ruta exacta depende de la distribución; en un esquema de la familia
Red Hat es un fichero bajo `/etc/httpd/conf.d/`, por ejemplo
`/etc/httpd/conf.d/server-status.conf`:

```apache
ExtendedStatus On

<Location "/server-status">
    SetHandler server-status
    Require valid-user

    AuthType Basic
    AuthName "Restricted Access"
    AuthUserFile /etc/httpd/.htpasswd
</Location>
```

Cree el fichero de contraseñas y la cuenta que usará el plugin, y recargue o
reinicie el servicio:

```bash
sudo htpasswd -c /etc/httpd/.htpasswd <USERNAME>
```

La ubicación de estado queda abierta a cualquiera que pueda alcanzarla salvo que
la configuración la restrinja. El bloque anterior exige un usuario;
`Require ip <MONITORING_HOST_IP>` la restringe por dirección en su lugar, y ambos
criterios se pueden combinar.

Compruebe que la página carga antes de configurar el plugin:

```bash
curl -s -u <USERNAME>:<PASSWORD> 'http://<TARGET_HOST>/server-status'
```

La respuesta debe contener las líneas de contadores legibles (`Total accesses:`,
`requests/sec`, `idle workers`, ...). Una respuesta con `ExtendedStatus`
desactivado, o una página `?auto`, no incluye las líneas que lee el plugin.

### Instalar el plugin

Descargue el addon desde la entrada del Marketplace de Pandora FMS, limitada a
usuarios con licencia:

[https://marketplace.pandorafms.com/entries/Apache](https://marketplace.pandorafms.com/entries/Apache)

Copie el ejecutable `pandora_apache` al host que ejecuta el agente de Pandora FMS,
por ejemplo en `/etc/pandora/plugins/`, y dele permiso de ejecución:

```bash
sudo chmod 755 /etc/pandora/plugins/pandora_apache
```

No se instala nada en el servidor Apache y no hacen falta herramientas de cliente
de Apache en el host de monitorización más allá de `curl`.

## Configuración

El plugin toma su configuración de dos fuentes:

```text
valores por defecto < archivo de configuración < opciones de línea de comandos
```

El archivo de configuración es opcional. Cuando se usa, debe ser el primer
argumento de la línea de comandos y es un fichero de texto plano con un par
`clave=valor` por línea. Las opciones de línea de comandos prevalecen sobre los
valores del fichero.

### Configuración del agente

Declare el plugin en el archivo de configuración del agente de Pandora FMS,
`/etc/pandora/pandora_agent.conf`, con una línea `module_plugin`:

```text
module_plugin /etc/pandora/plugins/pandora_apache -url http://<TARGET_HOST>/server-status -user <USERNAME> -pass <PASSWORD>
```

El agente ejecuta la línea en cada ciclo de ejecución, lee el XML de módulos que
imprime el plugin y guarda los módulos en su agente. Use la ruta absoluta del
ejecutable y mantenga toda la invocación en una sola línea: el agente la divide
por espacios, así que una contraseña con espacios rompe la línea.

Si la instalación usa configuración centralizada de agentes, añada la misma línea
`module_plugin` allí en lugar de editar el fichero local.

<!-- SCREENSHOT NEEDED: Vista de configuración del agente de Pandora FMS con una línea module_plugin para pandora_apache, con una URL de estado de laboratorio, un usuario y una contraseña enmascarada. -->

### Archivo de configuración y opciones

Un archivo de configuración mantiene las credenciales fuera de la línea
`module_plugin`:

```ini
url=http://<TARGET_HOST>/server-status
user=<USERNAME>
pass=<PASSWORD>
```

El fichero se pasa como único argumento posicional:

```bash
./pandora_apache /etc/pandora/plugins/apache.conf
```

La misma ejecución solo con opciones, sin fichero:

```bash
./pandora_apache -url 'http://<TARGET_HOST>/server-status' -user <USERNAME> -pass <PASSWORD>
```

Puntos clave:

- **`url`** es la URL de estado completa, incluido el esquema. Su valor por
  defecto es `http://127.0.0.1/server-status`, así que una ejecución que la omite
  consulta el servidor local.
- Las opciones usan la forma de un solo guion con el valor separado:
  `-url <valor>`. Las formas `--url <valor>` y `-url=<valor>` se leen como claves
  distintas y no tienen efecto, y una opción final sin valor se descarta en
  silencio.
- Cualquier opción que el plugin no utiliza se acepta y se ignora, de modo que una
  errata no detiene la ejecución: deja en silencio el valor documentado.
- **`preffix`** (con doble `f`) se antepone a todos los nombres de módulo.
  Déjelo vacío para una sola instancia de Apache por agente. Para monitorizar dos
  instancias desde el mismo agente, dé a cada una un prefijo distinto; de lo
  contrario, la segunda ejecución sobrescribe los módulos de la primera, porque
  los nombres son idénticos.
- El archivo de configuración admite líneas de comentario con `#`. Las claves y
  los valores se recortan y la última aparición de una clave repetida prevalece.

### Credenciales y transporte

- El plugin solo se autentica con autenticación básica HTTP. Envía credenciales
  cuando **ambos** valores, `user` y `pass`, están definidos; con solo uno de
  ellos la petición sale sin autenticación y la página de estado responde con un
  error HTTP.
- La contraseña se pasa a `curl` como argumento de línea de comandos, así que es
  visible en la lista de procesos del sistema operativo mientras se ejecuta la
  petición (`ps`, por ejemplo), y se guarda en texto plano en el archivo de
  configuración o en la línea `module_plugin`.
- Restrinja el archivo de configuración y la configuración del agente al usuario
  que ejecuta el agente, por ejemplo con `chmod 600`. No hay un fichero de
  credenciales separado ni entrada por variables de entorno.
- Con una URL `http`, las credenciales y la página de estado viajan sin cifrar.
  Con una URL `https` el tráfico va cifrado, pero el plugin acepta cualquier
  certificado del servidor: no lo valida, así que HTTPS aporta confidencialidad
  sin autenticar el servidor.

## Verificación

Ejecute el plugin manualmente desde el host que ejecuta el agente, con el archivo
de configuración o con las opciones:

```bash
./pandora_apache -url 'http://<TARGET_HOST>/server-status' -user <USERNAME> -pass <PASSWORD>
```

Cada ejecución se realiza una vez y termina. Una ejecución correcta imprime en la
salida estándar un bloque XML `<module>` por métrica, con esta forma:

```xml
<module>
	<name><![CDATA[Apache Connection]]></name>
	<type>generic_proc</type>
	<data><![CDATA[1]]></data>
</module>
<module>
	<name><![CDATA[Apache requests/sec]]></name>
	<type>generic_data</type>
	<data><![CDATA[0.3400]]></data>
	<unit><![CDATA[rq/sec]]></unit>
</module>
<module>
	<name><![CDATA[Apache last restart]]></name>
	<type>generic_data_string</type>
	<data><![CDATA[Tuesday, 14-Oct-2025 08:12:34 CEST]]></data>
</module>
```

Un módulo solo lleva un elemento `<description>` cuando la URL de estado devolvió
un código HTTP distinto de 200; en ese caso la descripción contiene el error HTTP.

El código de salida es `0` siempre que se imprimen módulos, incluidas las
ejecuciones que no pudieron alcanzar el servidor, y `1` solo cuando la línea de
comandos está vacía. No use el código de salida para decidir si la petición
funcionó.

En la consola, el agente que ejecuta el plugin muestra los módulos en su
siguiente ejecución. Confirme que un módulo numérico como `Apache requests/sec`
recibe valores.

<!-- SCREENSHOT NEEDED: Vista de detalle del agente de Pandora FMS con los módulos generados por pandora_apache para un servidor Apache. -->

## Entender los resultados

El plugin genera los mismos once módulos en cada ejecución correcta. Cubren
cuatro áreas:

- **Disponibilidad.** `Apache Connection` informa de `1` cuando la URL de estado
  respondió HTTP 200 y de `0` para cualquier otro código de estado HTTP.
- **Rendimiento.** `Apache requests/sec`, `Apache KB/sec` y `Apache KB/request`
  informan de las tasas del momento, en peticiones por segundo, kilobytes por
  segundo y kilobytes por petición.
- **Totales desde el último reinicio.** `Apache total accesses`,
  `Apache total traffic` y `Apache last restart` describen los contadores
  acumulados, que se reinician cuando el servidor se reinicia.
- **Carga y workers.** `Apache CPU Load`, `Apache current requests` y
  `Apache iddle workers` informan de la cifra de carga, las peticiones en proceso
  y el número de workers inactivos.

Notas:

- La mayoría de los módulos numéricos se imprimen con cuatro decimales
  (`0.3400`, `1234.0000`), incluso para valores que en la página de estado son
  enteros. `Apache CPU Load` es la excepción, descrita a continuación.
- `Apache KB/sec` y `Apache KB/request` están siempre en kilobytes: el plugin
  convierte los bytes dividiéndolos por 1024 y los megabytes multiplicándolos por
  1024. `Apache total traffic` conserva como unidad la que informa la página de
  estado (`kB`, `MB`, ...).
- `Apache server uptime` se publica en segundos, calculado a partir de la línea
  `Server uptime`. En esa conversión, un año cuenta como 360 días.
- `Apache CPU Load` lee el segundo campo de la línea `Server load:` cuando la
  página la incluye; ese campo puede llevar el porcentaje entre paréntesis, por
  ejemplo `(5%)`, que no es un número simple. Cuando la página no tiene esa línea,
  el plugin publica la cifra de `% CPU load` con dos decimales.
- `Apache iddle workers` es el nombre del módulo tal como lo publica el plugin,
  con esa ortografía. Úselo literalmente al definir alertas o paneles.
- Cuando `preffix` está definido, se antepone a todos los nombres anteriores.
- Un contador que falta en la página de estado (normalmente porque
  `ExtendedStatus` está desactivado) se publica como cero — `0.0000` en los
  módulos con cuatro decimales, `0.00` en `Apache CPU Load` — y una línea
  `Restart Time` ausente se publica como cadena vacía. Un cero no significa
  necesariamente que el servidor informara de cero.
- `Apache Connection` vale `1` también cuando la respuesta no se pudo interpretar
  en absoluto, además de con HTTP 200. Consulte
  [Operación y resolución de problemas](#operacion-y-resolucion-de-problemas).

## Operación y resolución de problemas

### Operación diaria

- El plugin no guarda estado entre ejecuciones: cada ejecución lee la página de
  estado en ese momento, así que puede ejecutarse manualmente en cualquier
  momento sin afectar a la siguiente ejecución programada.
- El agente de Pandora FMS ejecuta el plugin con su propio ciclo de ejecución. Use
  la configuración del agente para cambiar la frecuencia con la que se leen los
  contadores.
- El plugin no fija ningún tiempo de espera en la petición: una ubicación de
  estado que acepta la conexión y nunca responde mantiene la ejecución bloqueada
  hasta que `curl` termina o el agente la interrumpe. La clave `timeout` se lee
  pero no se aplica, y `curl` se invoca sin límite de tiempo.
- No hay modo detallado ni de depuración: `-debug 1` se acepta pero no produce
  diagnósticos adicionales.
- Use un `preffix` distinto por instancia de Apache cuando un agente ejecuta el
  plugin contra varios servidores.

### Resolución de problemas

- **`Apache Connection` vale `1` pero todos los contadores están a cero** — la
  petición no se completó. Un fallo que detiene `curl` (sin `curl` en el `PATH`,
  fallo de DNS, conexión rechazada, error de TLS) deja el módulo de disponibilidad
  en `1` e imprime el resto de módulos con ceros, junto con un aviso de Perl en la
  salida de error estándar. Compruebe que `curl` existe para el usuario del
  agente y que la URL es alcanzable desde el host del agente; no confíe solo en
  `Apache Connection` para detectar un servidor inalcanzable.
- **`Apache Connection` vale `0` y la descripción del módulo muestra un error
  HTTP** — la ubicación de estado respondió con ese código. `401` significa que
  las credenciales faltan o son incorrectas: revise `user` y `pass`. El plugin
  envía credenciales solo cuando ambos están definidos, así que una ejecución con
  uno solo de ellos también produce un `401`. `403` es una regla de acceso que
  rechaza la dirección del agente. `404` es una ruta incorrecta. Un `301`/`302`
  significa que la URL redirige: el plugin no sigue redirecciones, así que apunte
  a la URL final.
- **La página carga en un navegador pero todos los contadores están a cero** — la
  URL no sirve la página HTML de estado que analiza el plugin (por ejemplo, un
  endpoint `?auto`), o `ExtendedStatus` está desactivado y los contadores no
  existen. Compare la URL con la que probó en
  [Habilitar la página de estado](#habilitar-la-pagina-de-estado).
- **No se imprime ningún XML de módulos** — la línea de comandos estaba vacía. El
  plugin imprime entonces su resumen de uso en la salida de error estándar y
  termina con código `1`. No existe una opción de ayuda: `-h` se trata como una
  clave desconocida y el plugin se ejecuta contra la URL por defecto.
- **Una ejecución contra el servidor equivocado** — se omitió `url` y se usó el
  valor por defecto `http://127.0.0.1/server-status`, o la opción se escribió como
  `--url`/`-url=...` y se ignoró.
- **El archivo de configuración parece ignorarse** — no era el primer argumento,
  o no se puede abrir. Un fichero ilegible imprime su error en la salida de error
  estándar y la ejecución continúa con los valores por defecto en lugar de
  detenerse, así que el plugin puede acabar consultando
  `http://127.0.0.1/server-status`. Revise el orden de los argumentos y los
  permisos del fichero.
- **Dos servidores Apache se sobrescriben los módulos** — ambas ejecuciones
  publican los mismos nombres de módulo. Dé a cada una un `preffix` distinto, o
  use un agente por servidor.
- **Las alertas saltan con ceros tras un reinicio de Apache** — los totales se
  reinician con el servidor. Compare `Apache total accesses` y
  `Apache total traffic` con el valor de `Apache last restart` antes de tratar una
  caída como un incidente.

## Referencia

### Claves de configuración

Las mismas claves se aceptan en el archivo de configuración y como opciones de un
solo guion.

| Nombre | Obligatoria | Valor por defecto | Descripción |
|--------|-------------|-------------------|-------------|
| `url` | No | `http://127.0.0.1/server-status` | URL completa de la página HTML de `mod_status`, incluido el esquema. |
| `user` | Obligatoria cuando la ubicación de estado está protegida | — | Usuario para autenticación básica HTTP. Se aplica solo junto con `pass`. |
| `pass` | Obligatoria cuando la ubicación de estado está protegida | — | Contraseña de `user`. Se aplica solo junto con `user`. |
| `preffix` | No | Vacío | Texto que se antepone a todos los nombres de módulo generados. Se escribe con doble `f`. |

Otras claves se aceptan y se ignoran, incluidas `timeout`, `tag` y `debug`. En el
archivo de configuración, las líneas en blanco y las que empiezan por `#` se
omiten, las claves y los valores se recortan y la última aparición de una clave
repetida prevalece.

### Ejecución por línea de comandos

```bash
./pandora_apache [archivo-config] [ -clave valor ... ]
```

| Situación | Comportamiento |
|-----------|----------------|
| La línea de comandos está vacía | El plugin imprime su resumen de uso en la salida de error estándar y termina con código `1`; no genera ningún módulo |
| El primer argumento nombra un fichero existente | El plugin lo lee como archivo de configuración y aplica las opciones restantes sobre sus valores |
| El primer argumento no nombra un fichero | Se lee como una opción o se ignora; el fichero no se carga |
| `-clave valor` | Sustituye el valor de `clave` del fichero o de los valores por defecto |
| `--clave valor` o `-clave=valor` | Se leen como una clave distinta y se ignoran, así que la clave documentada conserva su valor por defecto o del fichero |
| Una opción final sin valor | Se descarta en silencio; no se informa de ningún error |
| Una clave desconocida | Se acepta y se ignora; el conjunto de claves no se valida |
| `-h` o `--help` | No existe una opción de ayuda: se trata como una clave desconocida |
| Código de salida | `0` siempre que se imprimen módulos, incluidos los errores HTTP y los servidores inalcanzables; `1` solo con la línea de comandos vacía |

### Módulos generados

Los módulos se imprimen en este orden, con `preffix` antepuesto a cada nombre
cuando está definido.

| Módulo | Tipo | Valor | Unidad |
|--------|------|-------|--------|
| `Apache Connection` | `generic_proc` | `1` cuando la URL de estado respondió HTTP 200, `0` para cualquier otro código de estado HTTP | — |
| `Apache CPU Load` | `generic_data` | Cifra de carga de la página de estado | — |
| `Apache requests/sec` | `generic_data` | Peticiones por segundo | `rq/sec` |
| `Apache KB/sec` | `generic_data` | Tráfico por segundo, convertido a kilobytes | `KB/sec` |
| `Apache KB/request` | `generic_data` | Tráfico por petición, convertido a kilobytes | `KB/rq` |
| `Apache last restart` | `generic_data_string` | Valor de la línea `Restart Time` | — |
| `Apache server uptime` | `generic_data` | Tiempo de actividad en segundos | — |
| `Apache total accesses` | `generic_data` | Accesos desde el último reinicio | — |
| `Apache total traffic` | `generic_data` | Tráfico desde el último reinicio | Unidad informada por la página de estado |
| `Apache current requests` | `generic_data` | Peticiones en proceso | — |
| `Apache iddle workers` | `generic_data` | Workers inactivos | — |

### Identidad del addon

| Campo | Valor |
|-------|-------|
| Identificador en el Marketplace | `Apache` |
| Nombre en el Marketplace | Apache Enterprise Plugin |
| Versión del addon | `1.0` |
| Paquete del Marketplace | `Apache.1.0.64` |
| Última actualización en el Marketplace | 2025-06-10 |
| Licencia | One — descarga limitada a usuarios con licencia |
| Tipo en el Marketplace | Miscelaneus |
| Flujo de trabajo | Plugin de monitorización, modo plugin de agente |
| Ejecutable | `pandora_apache` |
