# HA History Plugin

*Última actualización del artículo: 2026-10-23.*

## Qué hace

`pandora_history_ha` es un plugin autónomo para la alta disponibilidad (HA) de
la base de datos de histórico de Pandora FMS sobre MySQL. Es un plugin de
gestión para un clúster de HA existente; no proporciona el mecanismo de HA en
sí. Se ejecuta en un único host, sondea todos los nodos en cada ciclo de
comprobación, decide qué nodo es el primario activo (maestro) y promueve una
réplica cuando ningún nodo es escribible. Supervisa el estado de las réplicas
y, con `splitbrain_autofix` habilitado, reconfigura las réplicas detenidas o
que apuntan a un origen incorrecto. También puede actualizar la base de datos
principal de Pandora FMS para que sus componentes lean el nodo activo como host
de la base de datos de histórico.

El servicio trabaja a nivel de servidor: consulta `read_only` y el estado de
réplica, y ejecuta sentencias administrativas, pero nunca lee ni escribe las
tablas de datos de histórico. No genera módulos de Pandora FMS ni tiene
interfaz en la consola, por lo que no es un plugin de servidor, un plugin de
agente ni un plugin de Discovery.

Se instala como el servicio de systemd `pandora_history_ha` y se distribuye a
través de la entrada de Marketplace `pandorafms.pandora_history_ha`. La descarga
está limitada a usuarios con licencia.

## Preparación

### Requisitos

1. **Un host Linux con systemd.** El servicio se instala y se gestiona como una
   unidad de systemd. La instalación requiere root, porque el instalador escribe
   en `/opt` y en `/etc/systemd/system` y gestiona el servicio. La unidad
   generada no reduce privilegios: el servicio se ejecuta como root.
2. **MySQL 8.0.22 o posterior en todos los nodos del clúster de histórico.**
   El paquete declara compatibilidad con MySQL 8.0.22 o posterior.
3. **Acceso de red desde el host del servicio a todos los nodos del clúster**,
   en el puerto de base de datos configurado con `dbport`. El acceso a la base
   de datos principal de Pandora FMS solo es necesario cuando se habilita la
   actualización de la base de datos principal.
4. **Privilegios de base de datos**, necesarios para el funcionamiento:

| Credencial | Privilegios | Se aplica a |
| --- | --- | --- |
| `dbuser` | `REPLICATION CLIENT`, `RELOAD`, más `SUPER`, o `SYSTEM_VARIABLES_ADMIN` y `REPLICATION_SLAVE_ADMIN` | Todos los nodos de `ha_hosts` |
| `repl_dbuser` | `REPLICATION SLAVE` | Todos los nodos que puedan actuar como origen de replicación, solo con `splitbrain_autofix 1` |
| `main_dbuser` | `UPDATE` sobre la tabla `tconfig` | Base de datos principal de Pandora FMS, solo cuando se habilita la actualización de la base de datos principal |

5. **Registro binario habilitado en todos los nodos y un `server_id` único.** El
   servicio lee la posición del binlog del maestro elegido para reconfigurar las
   réplicas.

**Nota:** `REPLICATION_SLAVE_ADMIN` por sí solo no puede cambiar las variables
globales `read_only` ni `super_read_only`. Se necesita `RELOAD` para restablecer
los metadatos de réplica durante la reconfiguración automática.

**Nota:** el fichero de configuración guarda todas las contraseñas de base de
datos en texto plano, y el instalador no restringe sus permisos. Protéjalo antes
o inmediatamente después de la instalación, por ejemplo con `chown root:root` y
`chmod 600`. El servicio debe ejecutarse en un único host: no hay bloqueo
distribuido, así que no ejecute dos instancias contra el mismo clúster.

### Instalación

1. Descargue el paquete desde la entrada de Marketplace
   [`pandorafms.pandora_history_ha`](https://marketplace.pandorafms.com/entries/pandorafms.pandora_history_ha).
   La descarga está limitada a usuarios con licencia.
2. Transfiera el paquete al host que gestionará el clúster —normalmente el
   servidor de Pandora FMS— y extráigalo.
3. Como root, ejecute el instalador desde el directorio extraído:

```bash
./pandora_history_ha_installer --install
```

El directorio de instalación por defecto es
`/opt/pandorafms/pandora_history_ha`: el programa se instala en `bin/` y el
fichero de configuración es
`/opt/pandorafms/pandora_history_ha/pandora_history_ha.conf`.

`--destdir <directory>` antepone ese directorio a las rutas de instalación,
configuración y unidad. El `PIDFile` de la unidad sigue siendo
`/var/run/pandora_history_ha.pid`. En una instalación normal, el instalador
gestiona el systemd del host; con `--destdir`, la unidad se escribe bajo el
árbol de destino y el systemd del host no puede arrancarla, así que debe
arrancarla desde el entorno de destino. Úselo solo para instalaciones por etapas
o basadas en imágenes, porque la unidad generada referencia las rutas dentro de
ese directorio. En instalaciones por etapas o basadas en imagen, revise la unidad
generada y los enlaces bajo `/opt/pandorafms` antes de arrancar el servicio.

**Nota:** en una instalación normal, el instalador escribe y habilita la unidad
y arranca el servicio de inmediato, antes de que se edite la configuración. Con
`--destdir`, la unidad se escribe bajo el árbol de destino y el systemd del host
no puede arrancarla; arránquela desde el entorno de destino. El ejemplo incluido
no describe su clúster, así que revise la configuración (consulte
[Configuración](#configuracion)) y detenga el servicio si ya está en ejecución
con valores que no se aplican.

Reinstalar con `--install` es la vía de actualización: la configuración
existente permanece en `pandora_history_ha.conf`, el nuevo ejemplo se escribe
como `pandora_history_ha.conf.new` y el servicio se reinicia. Compare ambos
ficheros y fusione los tokens nuevos que necesite desde
`pandora_history_ha.conf.new` en `pandora_history_ha.conf`.

## Configuración

### Fichero de configuración

El fichero de configuración es
`/opt/pandorafms/pandora_history_ha/pandora_history_ha.conf`. Su ruta queda
fijada en el momento de la instalación.

El fichero contiene un par `<token> <valor>` por línea, con ambos separados por
espacios. No es un fichero `key=value`. Se aplican estas reglas:

- `#` inicia un comentario en cualquier punto de la línea; el resto se ignora.
  Como `#` inicia un comentario en cualquier punto, un valor no puede contener
  `#`.
- Las líneas en blanco se ignoran.
- Los tokens desconocidos se aceptan en silencio, así que un token mal escrito se
  ignora en lugar de notificarse.
- Si un token se repite, prevalece el último valor.
- No se pueden establecer valores vacíos.

`dbuser`, `dbpass` y `ha_hosts` son obligatorios. El servicio se niega a
arrancar si alguno falta o está vacío.

La configuración se lee solo al arrancar. Después de editarla, reinicie el
servicio (consulte [Gestión del servicio](#gestion-del-servicio)).

### Ejemplo de configuración

Este ejemplo describe un clúster de tres nodos con la actualización de la base
de datos principal habilitada. Sustituya todos los marcadores de posición.

```ini
# Clúster de base de datos de histórico
dbname              pandora
dbport              3306
dbuser              <DB_USER>
dbpass              <DB_PASSWORD>

# Credenciales de replicación (solo necesarias con splitbrain_autofix 1)
repl_dbuser         <REPLICATION_USER>
repl_dbpass         <REPLICATION_PASSWORD>

# Nodos del clúster; el orden es el criterio de desempate
ha_hosts            <HOST_1>,<HOST_2>,<HOST_3>

# Tiempos
ha_interval         30
ha_connect_retries  3
ha_connect_delay    2

# Comportamiento
splitbrain_autofix  0
verbose             0

# Ficheros
log_file            /opt/pandorafms/pandora_history_ha/bin/pandora_history_ha.log
pid_file            /var/run/pandora_history_ha.pid

# Base de datos principal de Pandora FMS (opcional)
main_dbhost         <PANDORA_DB_HOST>
main_dbport         3306
main_dbname         pandora
main_dbuser         <PANDORA_DB_USER>
main_dbpass         <PANDORA_DB_PASSWORD>
```

### Ajustes clave

Más allá de los tokens obligatorios, dos ajustes cambian el comportamiento del
servicio y merecen una decisión explícita.

`splitbrain_autofix` (por defecto `0`): cuando se establece a `1`, el servicio
reconfigura los hilos de réplica que están detenidos o apuntan a un origen
distinto, usando `repl_dbuser` y `repl_dbpass`. No controla el tratamiento del
split-brain: forzar `read_only=1` en los nodos escribibles restantes es siempre
automático. Habilítelo solo después de verificar las credenciales de réplica y
la topología del clúster, porque un origen o un usuario incorrecto reescribe la
configuración de la réplica.

`main_dbhost` (vacío por defecto): dirección IP o FQDN de la base de datos
principal de Pandora FMS. Cuando se establece, habilita la actualización de la
fila `history_db_host` de la tabla `tconfig` de esa base de datos después de
cada cambio de maestro. Así Pandora FMS apunta al nodo
activo sin intervención manual. Todos los tokens `main_db*` se ignoran mientras
`main_dbhost` esté vacío. El `main_dbuser` configurado necesita `UPDATE` sobre
`tconfig`.

El orden de `ha_hosts` también es una decisión: es el criterio de desempate
cuando hay más de un nodo elegible (consulte
[Elección del maestro](#eleccion-del-maestro)). Use en `ha_hosts` la misma forma
del host que la fuente de replicación configurada en las réplicas. El servicio
compara ambos valores como texto; una diferencia provoca una reconfiguración
innecesaria.

## Verificación

1. Compruebe que el servicio está activo:

```bash
systemctl status pandora_history_ha
```

2. Siga el fichero de log —por defecto,
   `/opt/pandorafms/pandora_history_ha/bin/pandora_history_ha.log`:

```bash
tail -f /opt/pandorafms/pandora_history_ha/bin/pandora_history_ha.log
```

Las líneas de arranque indican la versión, la ruta de configuración, la lista de
hosts, el nombre y el puerto de la base de datos y el estado de AutoFix. Después,
el servicio registra `Checking history DB cluster [...]` en cada ciclo y
establece un maestro. Secuencia de arranque representativa:

```text
2026-06-24 10:00:00 [LOG] pandora_history_ha v1.0 starting
2026-06-24 10:00:00 [LOG] Hosts  : <HOST_1>, <HOST_2>, <HOST_3>
2026-06-24 10:00:01 [LOG] Master established: <HOST_1>
```

3. El servicio instalado escribe su fichero PID en
   `/var/run/pandora_history_ha.pid`.
4. Cuando la actualización de la base de datos principal está habilitada,
   compruebe la fila:

```sql
SELECT value FROM tconfig WHERE token = 'history_db_host';
```

Debe contener el nodo activo. Se actualiza en la primera elección y después de
cada cambio de maestro.

El mismo valor se muestra en la consola de Pandora FMS en **Configuración → Base
de datos de histórico**. Las capturas siguientes muestran la instalación antes y
después de un failover. Los valores de host están redactados como `<HOST_1>`
(maestro anterior) y `<HOST_2>` (réplica promovida).

![Configuración de la base de datos de histórico antes del failover, host redactado como <HOST_1>](../assets/images/plugins/ha-history-plugin/history-db-before-failover.png)

![Configuración de la base de datos de histórico después del failover, host redactado como <HOST_2>](../assets/images/plugins/ha-history-plugin/history-db-after-failover.png)

## Cómo funciona el HA

### Elección del maestro

En cada ciclo, el servicio sondea cada host de `ha_hosts` de forma secuencial,
en el orden indicado. Un nodo que informa `read_only=0` es escribible y se trata
como candidato a maestro; un nodo que informa `read_only=1` es un candidato a
réplica, no necesariamente una réplica configurada. Los candidatos a réplica se
ordenan por su retardo de replicación, y un retardo desconocido se trata como el
peor posible.

- Exactamente un nodo escribible: ese nodo es el maestro.
- Ningún nodo escribible: se selecciona para promoción el nodo de solo lectura
  con el menor retardo de replicación. El servicio detiene la replicación y
  deshabilita `read_only` en él.
- Más de un nodo escribible: consulte
  [Failover y split-brain](#failover-y-split-brain).

### Failover y split-brain

Más de un nodo escribible es una condición de split-brain. El servicio conserva
el maestro actual si sigue siendo escribible; en caso contrario, conserva el
primer nodo escribible en el orden de `ha_hosts`. Después fuerza `read_only=1`
en los nodos escribibles restantes. Al arrancar el servicio el maestro actual es
desconocido, así que gana el primer nodo escribible de `ha_hosts`.

**Nota:** para degradar los nodos escribibles restantes, el servicio limpia
`super_read_only` y después establece `read_only=1`. Esto no bloquea a las
cuentas que tienen `SUPER`: esas cuentas todavía pueden escribir en un nodo
degradado.

Cuando ningún nodo es escribible, el servicio promueve el nodo de solo lectura
con el menor retardo de replicación. El servicio solicita la promoción: detiene
la replicación y deshabilita `read_only`. Compruebe que el nodo informa
`read_only=0` antes de confiar en él.

### Comprobaciones de réplica

Tras la elección, el servicio comprueba todos los nodos excepto el maestro
elegido. Un nodo está sano cuando sus hilos de réplica IO y SQL están en
ejecución y su origen configurado es el maestro elegido. Un nodo sano se
registra como `Replication OK: <replica> -> <master> (delay: <n>s)`.

Cuando un nodo no está sano, el resultado depende de `splitbrain_autofix`:

- `splitbrain_autofix 1`: el nodo se reconfigura como réplica del maestro
  elegido, usando la posición del binlog del maestro cuando está disponible.
- `splitbrain_autofix 0`: el servicio solo registra un aviso en cada ciclo, con
  el estado de los hilos IO y SQL y el origen esperado.

### Actualización de la base de datos principal

Después de un cambio de maestro —incluida la primera elección— y solo cuando
`main_dbhost` está establecido, el servicio actualiza el valor `history_db_host`
en la tabla `tconfig` de la base de datos principal de Pandora FMS. Solo se
actualiza ese token. La actualización se intenta solo en un cambio de maestro:
un fallo se reintenta tras el siguiente cambio de maestro, no en el ciclo
siguiente.

### Limitaciones

El servicio trabaja con replicación asíncrona de MySQL. No espera a que una
réplica aplique su relay log antes de promoverla, y la reconfiguración
automática de réplicas restablece los metadatos de la réplica y la posiciona en
la posición actual del binlog del maestro. Planifique los failovers con réplicas
al día y valide los datos en ambos nodos tras un failover no planificado. Las
escrituras aceptadas por un nodo mientras estuvo aislado no se reconcilian.

`pandora_history_ha` es un controlador, no un gestor de clúster completo:

- No proporciona quórum, fencing, IP virtual ni gestión de DNS.
- El orden de `ha_hosts` es el criterio de desempate cuando hay más de un nodo
  elegible.
- Solo actúa sobre la accesibilidad, `read_only`/`super_read_only` y el estado
  de réplica.
- El periodo del ciclo es el tiempo de trabajo más `ha_interval`. Una conexión
  a un nodo del clúster usa un tiempo de espera de 5 segundos y hasta
  `ha_connect_retries` intentos por nodo (intentos totales, no reintentos
  adicionales), con `ha_connect_delay` entre intentos. La conexión a la base de
  datos principal es un único intento con un tiempo de espera de 10 segundos.

## Operación y diagnóstico

### Gestión del servicio

```bash
systemctl start pandora_history_ha
systemctl stop pandora_history_ha
systemctl restart pandora_history_ha
systemctl status pandora_history_ha
systemctl enable pandora_history_ha
systemctl disable pandora_history_ha
```

Reinicie el servicio después de cada cambio de configuración: el fichero se lee
solo al arrancar. Con `Restart=always`, la unidad reinicia el servicio 10
segundos después de una salida inesperada; un `systemctl stop` lo mantiene
detenido. La unidad declara orden tras `network.target` y `mysql.service`.

### Logs

Una vez que la configuración es válida, el servicio escribe su salida de
aplicación solo en `log_file`
(`/opt/pandorafms/pandora_history_ha/bin/pandora_history_ha.log` por defecto) y
añade contenido al final; el servicio no rota el fichero, así que configure la
rotación y la retención externas. Los errores de validación del arranque se
escriben en la salida de error estándar y aparecen en `systemctl status` y en
`journalctl -u pandora_history_ha`.

Cada línea tiene el formato `YYYY-MM-DD HH:MM:SS [LEVEL] message`. Los niveles
son `LOG`, `WARNING` y `DEBUG`; los mensajes `DEBUG` se escriben solo con
`verbose 1`.

El directorio de `log_file` debe existir y ser escribible por el servicio, que
se ejecuta como root.

### Actualización

Ejecute el instalador con `--install` de nuevo:

```bash
./pandora_history_ha_installer --install
```

La configuración existente permanece en `pandora_history_ha.conf`, el nuevo
ejemplo se escribe como `pandora_history_ha.conf.new` y el servicio se reinicia.
Compare ambos ficheros y fusione los tokens nuevos que necesite desde
`pandora_history_ha.conf.new` en `pandora_history_ha.conf`.

Al actualizar, el instalador puede actualizar el runtime compartido bajo
`/opt/pandorafms` cuando el paquete incluye uno más reciente. Haga copia de
seguridad del host o planifique una ventana de mantenimiento antes de
actualizar.

### Desinstalación

Como root, ejecute:

```bash
./pandora_history_ha_installer --uninstall
```

El instalador detiene y deshabilita el servicio, y elimina la unidad y el
programa. El fichero de configuración
(`/opt/pandorafms/pandora_history_ha/pandora_history_ha.conf`), el fichero de log
y el directorio de instalación permanecen en su sitio; elimínelos manualmente si
ya no los necesita.

Durante la desinstalación, el instalador puede preguntar si desea eliminar un
directorio compartido bajo `/opt/pandorafms`. Si otros componentes de Pandora
FMS usan ese directorio, responda que no; no ejecute el desinstalador de forma
desatendida.

### Diagnóstico de problemas

- **El servicio no está en ejecución después de la instalación.** Compruebe
  `systemctl status pandora_history_ha` y `journalctl -u pandora_history_ha` en
  busca de errores de validación del arranque, y confirme los tokens
  obligatorios y el directorio de `log_file`.
- **Un host no es accesible.** El log muestra
  `Host '<host>' is unreachable, skipping` o
  `Cannot reach replica host '<host>'`. Compruebe la ruta de red, el puerto y
  las credenciales de ese nodo.
- **`Replication problem on '<host>' ... Set splitbrain_autofix=1 to
  auto-reconfigure.` se repite en cada ciclo.** Los hilos de réplica están
  detenidos o apuntan a un origen distinto. Verifique las credenciales de
  réplica y la topología antes de habilitar `splitbrain_autofix`.
- **`Error configuring replica ... Access denied; you need (at least one of) the
  RELOAD privilege(s) for this operation`.** El usuario de monitorización no
  tiene `RELOAD`, que el servicio necesita para restablecer los metadatos de
  réplica (`RESET REPLICA ALL`). Conceda `RELOAD` a `dbuser` en el nodo que se
  reconfigura.
- **Aparece `Split-brain detected! Writable hosts: ...`.** Hay más de un nodo
  escribible. El servicio conserva un maestro y fuerza `read_only=1` en los
  demás, pero investigue el clúster para eliminar la causa.
- **Aparece `tconfig(history_db_host) row not found...`.** La actualización no
  encontró ninguna fila. Compruebe que `tconfig` contiene la fila
  `history_db_host` y que la base de datos de histórico está habilitada en
  Pandora FMS.
- **Los cambios de configuración no tienen efecto.** El fichero se lee solo al
  arrancar, así que reinicie el servicio.
- **Aparece `Promoted '<host>' to master` pero fallan las escrituras.** El
  mensaje registra la solicitud de promoción; compruebe que el nodo informa
  `read_only=0` y que la replicación está detenida antes de enviarle escrituras.

## Referencia

### Parámetros del fichero de configuración

| Nombre | Obligatorio | Por defecto | Descripción |
| --- | --- | --- | --- |
| `dbname` | No | `pandora` | Se acepta por compatibilidad y se muestra en el log de arranque; el servicio se conecta a nivel de servidor y no selecciona esta base de datos. |
| `dbport` | No | `3306` | Puerto TCP usado para alcanzar cada nodo de `ha_hosts`. |
| `dbuser` | Sí | — | Usuario de monitorización. Necesita `REPLICATION CLIENT`, `RELOAD` y `SUPER`, o `SYSTEM_VARIABLES_ADMIN` y `REPLICATION_SLAVE_ADMIN`, en todos los nodos. |
| `dbpass` | Sí | — | Contraseña de `dbuser`. Se guarda en texto plano en el fichero de configuración. |
| `repl_dbuser` | Solo con `splitbrain_autofix 1` | — | Usuario de replicación. Necesita `REPLICATION SLAVE`. Se usa para reconfigurar los hilos de réplica. |
| `repl_dbpass` | Solo con `splitbrain_autofix 1` | — | Contraseña de `repl_dbuser`. Se guarda en texto plano. |
| `ha_hosts` | Sí | — | Direcciones IP o FQDN de todos los nodos del clúster, separadas por comas. El orden es el criterio de desempate cuando hay más de un nodo elegible. Use la misma forma que la fuente de replicación configurada en las réplicas. |
| `ha_interval` | No | `30` | Segundos de espera después de cada ciclo de comprobación. El periodo efectivo es el tiempo de trabajo del ciclo más este valor. Debe ser 1 o mayor. |
| `ha_connect_retries` | No | `3` | Intentos de conexión por nodo antes de considerarlo inalcanzable. También se usa al leer la posición del binlog del maestro. Debe ser 1 o mayor; `0` no realiza ningún intento de conexión. |
| `ha_connect_delay` | No | `2` | Segundos entre intentos de conexión al mismo nodo. |
| `splitbrain_autofix` | No | `0` | `1` reconfigura los hilos de réplica detenidos o que apuntan a un origen distinto; no controla el tratamiento del split-brain. La reconfiguración restablece los metadatos de la réplica y la posiciona en la posición actual del binlog del maestro. |
| `verbose` | No | `0` | `1` añade mensajes `DEBUG` al log. |
| `log_file` | No | `/opt/pandorafms/pandora_history_ha/bin/pandora_history_ha.log` | Ruta del fichero de log. Su directorio debe existir y ser escribible. |
| `pid_file` | No | `/var/run/pandora_history_ha.pid` | Fichero PID usado cuando el servicio arranca sin `-p`. La unidad instalada pasa `-p /var/run/pandora_history_ha.pid`, que tiene prioridad. |
| `main_dbhost` | No | — | Dirección IP o FQDN de la base de datos principal de Pandora FMS. Cuando se establece, habilita la actualización de la base de datos principal después de cada cambio de maestro. Los demás tokens `main_db*` se ignoran cuando está vacío. |
| `main_dbport` | No | `3306` | Puerto de la base de datos principal de Pandora FMS. |
| `main_dbname` | No | `pandora` | Nombre de la base de datos principal de Pandora FMS. |
| `main_dbuser` | No | — | Usuario de la base de datos principal. Necesita `UPDATE` sobre la tabla `tconfig`. |
| `main_dbpass` | No | — | Contraseña de `main_dbuser`. Se guarda en texto plano. |

El fichero usa un par `<token> <valor>` por línea. `#` inicia un comentario en
cualquier punto de la línea, las líneas en blanco se ignoran, los tokens
desconocidos se aceptan en silencio y prevalece la última aparición de un token
repetido.

Los valores no pueden contener `#`. `ha_interval` y `ha_connect_retries`
deben ser 1 o mayores.

### Opciones del instalador

El instalador requiere root. Se debe indicar exactamente una de las opciones
`--install` o `--uninstall`; `--destdir` es opcional.

| Opción | Obligatorio | Por defecto | Descripción |
| --- | --- | --- | --- |
| `--install` | Una de `--install` o `--uninstall` | — | Instala el servicio o lo actualiza cuando ya está instalado. Escribe y habilita la unidad y arranca el servicio. |
| `--uninstall` | Una de `--install` o `--uninstall` | — | Detiene y deshabilita el servicio, elimina la unidad y el programa, y conserva el fichero de configuración, el fichero de log y el directorio de instalación. |
| `--destdir <directory>` | No | — | Antepone el directorio indicado a las rutas de instalación, configuración y unidad. El `PIDFile` de la unidad sigue siendo `/var/run/pandora_history_ha.pid`, y el instalador gestiona el systemd del host. Úselo solo para instalaciones por etapas o basadas en imágenes, porque la unidad generada referencia las rutas dentro de ese directorio. Revise la unidad generada y los enlaces bajo `/opt/pandorafms` antes de arrancar el servicio. |

### Rutas y servicio

| Elemento | Valor |
| --- | --- |
| Directorio de instalación | `/opt/pandorafms/pandora_history_ha` |
| Directorio del programa | `/opt/pandorafms/pandora_history_ha/bin` |
| Fichero de configuración | `/opt/pandorafms/pandora_history_ha/pandora_history_ha.conf` |
| Unidad systemd | `/etc/systemd/system/pandora_history_ha.service` |
| Comportamiento de la unidad | Reinicia el servicio 10 segundos después de una salida inesperada, declara orden tras `network.target` y `mysql.service`, y ejecuta el servicio como root |
| Fichero de log por defecto | `/opt/pandorafms/pandora_history_ha/bin/pandora_history_ha.log` |
| Fichero PID | `/var/run/pandora_history_ha.pid` |
| Entrada de Marketplace | `pandorafms.pandora_history_ha`, versión 1.0, actualizada el 2026-06-24; descarga limitada a usuarios con licencia |

### Mensajes de log

Los mensajes siguientes son representativos; `<...>` marca un valor en tiempo de
ejecución y `...` indica detalle omitido.

| Mensaje | Significado |
| --- | --- |
| `pandora_history_ha v1.0 starting` | El servicio arranca e informa de su versión. |
| `Config : <path>` | Fichero de configuración en uso. |
| `Hosts  : <list>` | Hosts leídos de `ha_hosts`, en orden. |
| `DB     : <dbname> (port <port>)` | Nombre de la base de datos mostrado como referencia y puerto usado para conectar. |
| `AutoFix: enabled` / `AutoFix: disabled` | Estado de `splitbrain_autofix`. |
| `Checking history DB cluster [<hosts>]` | Inicio de un ciclo de comprobación. |
| `Host '<host>' is unreachable, skipping` | El nodo no respondió tras los intentos configurados; el ciclo continúa con el siguiente host. |
| `Split-brain detected! Writable hosts: <list>` | Más de un nodo informa `read_only=0`. |
| `Keeping '<host>' as master; forcing read_only=1 on remaining writable hosts` | Maestro que se conserva en una condición de split-brain. |
| `No writable host found. Best failover candidate: <host> (delay: <n>s or unknown)` | Ningún nodo es escribible; réplica seleccionada para la promoción. |
| `Promoted '<host>' to master (read_only disabled, replication stopped)` | Se solicitó la promoción en el candidato. |
| `Master established: <host>` | Primera elección tras el arranque. |
| `Master failover: <old> -> <new>` | Cambio de maestro tras un failover. |
| `Replication OK: <replica> -> <master> (delay: <n>s)` | Hilos de réplica en ejecución y apuntando al maestro. |
| `Replication problem on '<host>' (...)` | Hilos de réplica detenidos o apuntando a otro origen; consulte [Diagnóstico de problemas](#diagnostico-de-problemas). |
| `Cannot reach replica host '<host>'` | El nodo no se pudo alcanzar durante las comprobaciones de réplica; el ciclo continúa con el siguiente nodo. |
| `Updating main DB tconfig(history_db_host) -> '<new>' on <main>` | Comienza la actualización de la base de datos principal. |
| `tconfig(history_db_host) updated to '<new>'` | Se actualizó la fila de la base de datos principal. |
| `tconfig(history_db_host) row not found in main DB — history DB may not be enabled in Pandora` | La actualización no encontró ninguna fila; compruebe que la base de datos de histórico está habilitada y que la fila existe. |
| `Shutting down pandora_history_ha` | El servicio recibió una señal de parada y está saliendo. |
