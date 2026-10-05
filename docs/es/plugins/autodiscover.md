# Autodiscover

*Última actualización del artículo: 2026-10-05.*

## Qué hace

El plugin Autodiscover localiza los servicios del sistema de un endpoint y los convierte en módulos
de Pandora FMS. Se ejecuta como **plugin de agente**: el agente lo lanza, el plugin escribe las
definiciones de los módulos en formato XML en la salida estándar y el agente las incorpora.

El plugin tiene dos modos de funcionamiento y necesita uno de ellos para hacer algo:

- **Lista integrada** (`--default`): monitoriza una lista de servicios habituales (bases de datos,
  servidores web, servidores de correo, contenedores...) incluida en el propio plugin. Cada entrada
  se compara con el nombre completo del servicio, de modo que `ssh` nunca selecciona
  `sshd-keygen@rsa`.
- **Lista propia** (`--list`): monitoriza exactamente los servicios que se indiquen, como
  subcadenas o como expresiones regulares.

Un endpoint tiene muchas unidades que no están en ejecución y no tiene instalados todos los
servicios de la lista integrada; el plugin informa solo de lo que coincide con la lista que recibe,
por lo que una ejecución no es un informe sobre el estado de todo el endpoint.

- **Resultado.** Un módulo de estado `generic_proc` por cada servicio que existe en el gestor de
  servicios y coincide con la lista activa: `1` mientras el servicio está en ejecución y `0`
  mientras está detenido o inactivo. Un nombre de la lista que no existe en el endpoint no genera
  ningún módulo.
- **Uso de recursos opcional.** Con `--usage` el plugin añade además un módulo de uso de CPU y otro
  de uso de memoria por cada servicio en ejecución cuyo proceso se puede resolver y cuyo uso es
  mayor que cero.
- **Alcance.** El plugin consulta el gestor de servicios del endpoint: systemd en Linux, el comando
  `service` y `/etc/init.d` cuando systemd no está disponible, y el Administrador de servicios
  (Service Control Manager) en Windows.
- **Cobertura.** Se informa de los servicios que coinciden; no se descubre nada fuera de la lista
  elegida.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
|--------|--------|-----------|
| Versión del plugin `2.1` | Objetivo documentado | La versión que describe esta página |
| Linux con systemd | `Tested` | Probado en Fedora 44 (systemd 259) y Rocky Linux 10.2 (systemd 257): lista integrada, listas propias, exclusiones, diagnósticos detallados y filtrado de `oneshot` |
| Linux sin systemd (SysV) | `Not validated` | No se ha registrado ningún equipo solo con SysV |
| Windows (Administrador de servicios, amd64) | `Tested` | Probado en Windows 11: lista integrada, correspondencia por subcadena y exacta, exclusiones, sufijo `.service`, regla de tres caracteres y `--usage` |
| Nombres de servicio de Windows de menos de tres caracteres | `Required` | El plugin descarta en Windows las entradas de la lista de menos de tres caracteres, consulte [Reglas de correspondencia](#reglas-de-correspondencia) |
| Un agente capaz de ejecutar entradas `module_plugin` en el endpoint | `Required` | Prerrequisito, consulte [Requisitos](#requisitos) |

### Requisitos

1. **Un agente de Pandora FMS instalado en el endpoint.** El plugin lo ejecuta el agente: no es un
   plugin de servidor y no necesita el servidor de Pandora FMS.
2. **Linux**: systemd, o el comando `service` junto con los scripts de `/etc/init.d` cuando systemd
   no está arrancado. El plugin detecta systemd en tiempo de ejecución y recurre a SysV
   automáticamente.
3. **Windows**: ningún componente adicional. El plugin consulta el Administrador de servicios.
4. **Permisos para consultar los servicios del endpoint.** Leer el estado de todos los servicios y
   el consumo de recursos de su proceso puede requerir privilegios elevados.

### Instalación

El plugin se distribuye dentro del paquete del agente y no necesita una instalación aparte. El agente
lo lanza mediante `module_plugin`, por lo que en Linux no hace falta la ruta completa:

| Plataforma | Ejecutable |
|------------|------------|
| Linux | `/usr/share/pandora_agent/plugins/autodiscover` |
| Windows | `%PROGRAMFILES%\Pandora_Agent\util\autodiscover.exe` |

## Configuración

Toda la superficie de configuración del plugin es el fichero de configuración del agente: no tiene
fichero de configuración propio. Añada una entrada `module_plugin` por cada ejecución que desee,
usando el bloque `module_begin` / `module_end` para fijar un tiempo de espera.

La configuración del agente que se distribuye con el agente ya incluye este bloque:

```ini
# Service autodiscovery plugin
module_begin
module_plugin autodiscover --default
module_timeout 30
module_end
```

En Windows el mismo bloque nombra el ejecutable de forma explícita:

```ini
# Service autodiscovery plugin
module_begin
module_plugin "%PROGRAMFILES%\Pandora_Agent\util\autodiscover.exe" --default
module_timeout 30
module_end
```

### Elegir qué monitorizar

- **Lista integrada.** Mantenga `--default` para monitorizar los servicios habituales de la mayoría
  de servidores. La lista de cada plataforma está en
  [Lista de servicios integrada](#lista-de-servicios-integrada).
- **Lista propia.** Sustitúyalo por `--list "<servicio1,servicio2>"`. Escriba el valor entre
  comillas para que el intérprete de órdenes no lo expanda y separe las entradas con comas.

```ini
# Monitorizar solo el servidor web y SSH, por su nombre
module_plugin autodiscover --list "httpd,sshd"
```

```ini
# Monitorizar los servicios que coinciden con un patrón
module_plugin autodiscover --list "apache.*,php[0-9.]*-fpm" --exact-match
```

### Acotar y depurar la selección

- **`--exclude "<servicio1,servicio2>"`** elimina servicios de la lista activa, tanto si procede de
  `--default` como de `--list`. No es una acción por sí misma: se puede repetir y sus valores se
  acumulan. Una entrada que no coincide con nada es solo informativa.
- **`--exact-match`** hace que cada entrada de `--list` se compare con el nombre completo del
  servicio en lugar de con una subcadena. Úselo cuando un nombre como `cron` seleccione también
  `cronie` o `crond`. La lista integrada siempre compara el nombre completo.
- **`--skip-oneshot`** (solo Linux con systemd) ignora las unidades cuyo tipo es `oneshot`. Estas
  unidades se ejecutan una vez y permanecen inactivas por diseño, por lo que su módulo de estado
  estaría siempre a `0`.
- **`-v`, `--verbose`** escribe en la salida de error los diagnósticos descritos en
  [Diagnósticos](#diagnosticos). Nunca cambia el código de salida, por lo que es seguro dejarlo
  activado mientras se ajusta una lista.

### Combinar y ordenar los parámetros

- `--default`, `--list` y `--help` son acciones: **gana la primera bien formada de la línea de
  órdenes** y las acciones posteriores no se ejecutan. El valor de `--list` y de `--exclude` se
  valida aunque su acción no gane, por lo que `--default --list` falla en lugar de ejecutar
  `--default`. Para acotar una selección añada `--exclude`, nunca una segunda acción.
- `--usage`, `--exact-match`, `--skip-oneshot`, `-v` y `--exclude` no son acciones, por lo que
  pueden aparecer en cualquier posición y combinarse libremente.
- Un `--list` o un `--exclude` sin valor, o con un valor que empieza por `-`, se rechaza: el plugin
  escribe el error y la pantalla de ayuda.
- Un parámetro desconocido se informa y va seguido de la pantalla de ayuda. El código de salida se
  mantiene en `0` ante cualquier problema de parámetros, porque el agente interpreta un código
  distinto de cero como un fallo del plugin y no como un error de configuración. Un sistema
  operativo no reconocido es el único caso con código distinto de cero. Consulte
  [Códigos de salida y flujos](#codigos-de-salida-y-flujos).

## Verificar

Ejecute el plugin manualmente en el endpoint con la misma lista que haya configurado y lea el XML de
los módulos que escribe:

```bash
/usr/share/pandora_agent/plugins/autodiscover --default
```

```xml
<module>
	<name><![CDATA[Service sshd - Status]]></name>
	<type>generic_proc</type>
	<data><![CDATA[1]]></data>
</module>
```

- **Un bloque `<module>` por cada servicio encontrado.** Una ejecución que no encuentra nada no
  escribe nada.
- **El código de salida es `0`** en todos los casos salvo un sistema operativo no reconocido. No lo
  use para detectar una lista incorrecta: use `-v`.
- **En Pandora FMS**, el agente incorpora los módulos escritos en su siguiente ejecución, por lo que
  `Service sshd - Status` aparece en la lista de módulos del agente que ejecutó el plugin.

## Interpretar los resultados

Cada servicio de la lista activa que existe en el gestor de servicios genera un módulo de estado;
`--usage` añade hasta dos módulos más por cada servicio en ejecución.

| Nombre del módulo | Tipo | Dato | Unidad | Padre | Se genera cuando |
|-------------------|------|------|--------|-------|------------------|
| `Service <nombre> - Status` | `generic_proc` | `1` en ejecución, `0` detenido o inactivo | — | — | El servicio existe en el gestor de servicios y coincide con la lista activa |
| `Service <nombre> - CPU usage` | `generic_data` | Uso de CPU del proceso del servicio | `%` | `Service <nombre> - Status` | Con `--usage`, servicio en ejecución y proceso localizado |
| `Service <nombre> - Memory usage` | `generic_data` | Uso de memoria del proceso del servicio | `%` | `Service <nombre> - Status` | Con `--usage`, servicio en ejecución y proceso localizado |

- **`<nombre>` es el nombre del servicio sin el sufijo de la plataforma.** En systemd, la unidad
  `sshd.service` genera `Service sshd - Status`.
- **Un `0` no es necesariamente un problema.** El estado es `1` solo mientras el servicio está en
  ejecución. Un servicio detenido y una unidad inactiva generan `0`, y el módulo permanece en
  Pandora FMS hasta que se elimine. Un servicio que no está instalado no genera ningún módulo, por
  lo que un nombre de la lista sin módulo propio simplemente no existe en el endpoint.
- **Los módulos de uso son condicionales.** Solo se generan para un servicio en ejecución cuyo
  proceso se puede resolver y cuyo uso de CPU o de memoria es mayor que cero, por lo que una primera
  ejecución puede generar únicamente el módulo de estado.
- **Cómo se lee el estado.** En systemd la unidad está en ejecución cuando su estado `active` es
  `active`; el plugin lista todas las unidades, incluidas las inactivas. Con SysV se lee la salida de
  `service <nombre> status` buscando `is running` / `is stopped`. En Windows se usa el informe del
  Administrador de servicios.

## Uso diario y solución de problemas

### Diagnósticos

Con `-v` (o `--verbose`) el plugin escribe una línea por cada hallazgo en la salida de error, con el
prefijo `autodiscover: warning:`. El código de salida nunca cambia.

```bash
/usr/share/pandora_agent/plugins/autodiscover --list "nope" -v
```

```text
autodiscover: warning: entry "nope" matched no service
```

- Se informa de cada entrada de `--list` o de `--exclude` que no ha coincidido con ningún servicio.
  Con `--default` se informa igual de las entradas de servicios que no están instalados en el
  endpoint, y por eso los diagnósticos son opcionales: de lo contrario, una ejecución con la lista
  integrada informaría de todos los servicios que el endpoint no tiene.
- En Windows se informa de las entradas de la lista de menos de tres caracteres que se descartan.
- Una ejecución con `--skip-oneshot` que no haya podido leer los tipos de las unidades informa de
  que el filtro se ha ignorado.

### Límites de ejecución

- Las unidades se listan, y su tipo se lee con `--skip-oneshot`, con un **límite interno de 30
  segundos** por llamada a `systemctl`; la consulta del proceso por servicio que usa `--usage` tiene
  un **límite de 5 segundos**, y una llamada a `service` tiene un **límite de 10 segundos**.
- El `module_timeout` del bloque distribuido es de **30 segundos**. Auméntelo si el endpoint tiene un
  número muy elevado de unidades, porque el límite del agente se aplica a toda la ejecución y no a
  una sola orden.
- `--usage` añade una consulta de proceso por cada servicio en ejecución, por lo que es más lento
  que una ejecución que solo obtiene estados.
- El plugin termina por sí mismo al acabar y atiende la señal `SIGTERM` escribiendo un mensaje en la
  salida de error y terminando con código `0`.

### Solución de problemas

- **El plugin no escribe nada.** Ningún servicio de la lista activa ha coincidido. Revise la lista
  con `-v` y recuerde que `--default` compara el nombre completo del servicio.
- **Un servicio no se monitoriza.** El nombre de la lista no coincide con el nombre de la unidad o
  del servicio del endpoint, o el servicio no está instalado. Use el nombre exacto, o un patrón que
  coincida con él, y confírmelo con `-v`.
- **Un módulo de estado está siempre a `0`.** El servicio está detenido o inactivo, o la unidad es
  de tipo `oneshot`. Use `--skip-oneshot` para descartar el último caso. Un servicio que no está
  instalado no genera ningún módulo, por lo que la ausencia de módulo no es un estado `0`.
- **Aparecen servicios que no se han pedido.** Una entrada de `--list` es una subcadena o una
  expresión regular salvo que se use `--exact-match`, por lo que `httpd` selecciona también
  `httpd-init` en un host Linux con systemd, y `Spool` selecciona también `Spooler` en Windows. Añada
  `--exact-match` o acote el patrón.
- **No aparece módulo de uso para un servicio en ejecución.** No se ha podido resolver el proceso
  del servicio, o su uso de CPU y de memoria era cero en ambos casos.
- **Aparece una línea inesperada en la salida de error y los módulos son correctos.** Un código de
  salida distinto de cero de `systemctl` se informa como un fallo real y, en ese caso, la ejecución
  no genera módulos. Los mensajes de `-v` son informativos y no afectan al resultado.
- **El agente informa de un tiempo de espera del plugin.** Aumente `module_timeout`, reduzca la lista
  o prescinda de `--usage`.

## Referencia

### Parámetros de línea de órdenes

| Nombre | Valor | Obligatorio | Valor por defecto | Descripción |
|--------|-------|-------------|-------------------|-------------|
| `--default` | — | Se requiere una acción | — | Monitoriza la lista integrada de la plataforma, comparando el nombre completo |
| `--list` | `<nombre1,nombre2,...>` | Se requiere una acción | — | Monitoriza la lista indicada, como subcadenas o expresiones regulares salvo que se use `--exact-match` |
| `--exclude` | `<nombre1,nombre2,...>` | No | — | Elimina de la lista activa los servicios que coinciden, con el mismo modo de correspondencia que la lista activa. Se puede repetir; los valores se acumulan |
| `--exact-match` | — | No | Desactivado | Compara cada entrada de `--list` con el nombre completo del servicio, sin distinguir mayúsculas y minúsculas |
| `--skip-oneshot` | — | No | Desactivado | Solo Linux con systemd: ignora las unidades cuyo tipo es `oneshot` |
| `--usage` | — | No | Desactivado | Añade un módulo de uso de CPU y otro de uso de memoria por cada servicio en ejecución |
| `-v`, `--verbose` | — | No | Desactivado | Escribe diagnósticos en la salida de error; nunca cambia el código de salida |
| `--help` | — | No | — | Escribe la pantalla de ayuda, incluida la lista integrada de la plataforma |

En la práctica una acción (`--default`, `--list`, `--help`) es obligatoria: sin argumentos, y sin
ninguna acción reconocida, el plugin escribe la pantalla de ayuda y no monitoriza nada.

### Reglas de correspondencia

- Cada entrada de un valor de `--list` o de `--exclude` es un **patrón que no distingue mayúsculas
  y minúsculas**.
- Con `--exact-match`, y siempre con `--default`, el patrón debe coincidir con el nombre **completo**
  del servicio (`cron` no coincide con `cronie`). Sin esta opción, el patrón se busca en cualquier
  parte del nombre (`cron` coincide con `cronie` y con `crond`) y se admiten expresiones regulares
  como `php[0-9.]*-fpm`.
- Antes de comparar se elimina el sufijo `.service` de la entrada, de modo que `httpd.service` se
  acepta como el servicio `httpd`. El sufijo se conserva cuando el resto de la entrada contiene
  alguno de los caracteres `\ ^ $ * + ? ( ) [ ] { } |`, por lo que un patrón como `.*\.service` se
  usa tal cual. El punto no se considera aquí un metacaracter, de modo que un nombre real como
  `dbus-org.freedesktop.NetworkManager.service` sigue funcionando.
- En Windows se descartan las entradas de menos de tres caracteres.
- En Linux sin systemd, las entradas de `--list` se usan como nombres literales de scripts de
  `/etc/init.d`, por lo que las expresiones regulares no se aplican en ese caso.

### Lista de servicios integrada

`--default` compara cada entrada con el nombre completo del servicio, sin distinguir mayúsculas y
minúsculas. Las entradas son patrones, por lo que cubren nombres con versión o con instancia. Las
entradas que no existen en el endpoint se ignoran.

**Linux**

```text
httpd, apache2, nginx, slapd, postfix, mysqld, mysql, mariadb, postgresql(-\d+)?, oracle,
oracle(-\w+)*, mongod, mongodb, redis, redis-server, elasticsearch, rabbitmq-server, ssh, sshd,
cron, crond, cronie, chronyd, chrony, ntpd, ntp, docker, containerd, php-fpm, php[\d.]*-fpm,
haproxy, keepalived, tomcat, tomcat\d*
```

**Windows**

```text
MySQL(\d+)?, postgresql(-x64-\d+)?, pgsql, OracleService\w*, Oracle\w*TNSListener, MSSQLSERVER,
MSSQL\$\w+, SQLSERVERAGENT, IISADMIN, Apache2\.\d+, nginx, W3svc, NTDS, DNS,
MSExchangeADTopology, MSExchangeServiceHost, MSExchangeSA, MSExchangeTransport, MSExchangeIS,
Spooler, TermService, wuauserv, DHCP, TeamViewer, AnyDesk
```

### Códigos de salida y flujos

| Flujo | Contenido |
|-------|-----------|
| Salida estándar | El XML de los módulos, un bloque `<module>` por módulo. También la pantalla de ayuda, que se escribe cuando no hay acción, con `--help` y después de un parámetro desconocido |
| Salida de error | El error de un parámetro desconocido o incompleto, los mensajes con el prefijo `autodiscover: warning:` cuando se usa `-v`, y los fallos reales, como una llamada a `systemctl` que no se ha podido ejecutar |

| Código de salida | Significado |
|------------------|-------------|
| `0` | Ejecución normal, pantalla de ayuda, aviso, parámetro desconocido o error interno del plugin |
| `1` | El sistema operativo no se reconoce |
