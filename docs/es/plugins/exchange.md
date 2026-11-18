# Exchange

*Última actualización del artículo: 2026-11-12.*

## Qué hace

El addon Exchange monitoriza el estado de un servidor Microsoft Exchange Server
desde Pandora FMS. Se ejecuta en el propio servidor Exchange, bajo el agente de
Pandora FMS, como plugin de agente: una ejecución lanza las comprobaciones de
estado de Exchange seleccionadas y escribe un bloque XML `<module>` por resultado, y el agente
convierte esos bloques en módulos de su propio agente.

Las comprobaciones se agrupan en bloques independientes, cada uno habilitado por
su propio conmutador:

- **Buzón** (`-mailbox`) — estado de la replicación de bases de datos,
  conectividad MAPI y estado de las copias locales de base de datos del DAG.
- **Acceso de cliente** (`-cas`) — OWA, ActiveSync, servicios web (EWS),
  PowerShell remoto, POP, IMAP, ECP, Autodiscover, conectividad de cliente de
  Outlook y conectividad SMTP.
- **Carga** — la cola de envío (`-queue`), la carga de procesador (`-cpu`) y el
  uso de memoria (`-memory`).
- **Almacenamiento** (`-storage`) — un triplete de módulos por volumen.
- **Servicios de Exchange** (`-services`) — un módulo por cada servicio de
  Exchange instalado.

Una ejecución sin ningún conmutador habilita todos los bloques excepto el de
servicios. `-all` habilita el mismo conjunto; el bloque de servicios siempre se
activa explícitamente con `-services`. Los conmutadores se combinan, así que una
ejecución puede recoger solo los bloques que se seleccionen.

Cada ejecución cubre un servidor. El addon no tiene ningún parámetro que nombre
un servidor Exchange remoto: inspecciona el servidor donde el agente lo ejecuta,
así que hay que instalarlo en el agente de cada servidor Exchange que se quiera
monitorizar.

El paquete contiene un único punto de entrada. Los bloques se seleccionan con
conmutadores de línea de comandos (véase
[Elegir qué comprobar](#elegir-que-comprobar)), no con un script por bloque.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
|--------|--------|-----------|
| Pandora FMS NG 784 y posteriores | `Soportado` | El Marketplace indica que todas sus integraciones son compatibles con Pandora FMS NG 784 y versiones posteriores |
| Microsoft Exchange Server 2013, 2016 y 2019 | `Soportado` | La entrada del Marketplace indica que el plugin está diseñado para monitorizar Exchange Server 2013, 2016 y 2019 |
| Microsoft Exchange Server 2016 | `Probado` | La guía oficial del addon nombra Exchange 2016 como la versión en la que se probó |
| Microsoft Exchange Server 2010 y anteriores | `Sin validar` | La entrada del Marketplace limita el plugin a Exchange 2013 y posteriores |
| Versión de Windows Server que aloja Exchange | `Sin validar` | No hay ninguna versión de Windows registrada para este addon |
| Agente Windows de Pandora FMS en el servidor Exchange | `Requerido` | El plugin es un plugin de agente: escribe el XML de módulos para el agente que lo ejecuta |
| `powershell.exe` disponible para la cuenta que ejecuta el agente | `Requerido` | La invocación documentada llama a `powershell.exe` |
| Los cmdlets de administración de Exchange cargados en la sesión que ejecuta el plugin | `Requerido` | Las comprobaciones llaman a cmdlets de administración de Exchange y el addon no carga ninguno por sí mismo |

La versión de Exchange es un requisito operativo del addon, no una afirmación
sobre la versión de Windows que la aloja.

### Requisitos

1. **Microsoft Exchange Server 2013, 2016 o 2019** instalado en el servidor
   monitorizado.
2. **El agente de Pandora FMS instalado en ese servidor**, y en ejecución.
3. **Una cuenta para el agente que pueda ejecutar los cmdlets de administración
   de Exchange** que usan las comprobaciones: `Test-ReplicationHealth`,
   `Test-MAPIConnectivity`, `Get-MailboxDatabaseCopyStatus`, `Get-HealthReport` y
   `Test-SmtpConnectivity` para las comprobaciones de estado, más `Get-Queue` y
   `Get-Service` para los módulos de carga y de servicios. Los bloques de
   procesador, memoria y volúmenes también leen datos WMI locales. Ninguna fuente
   oficial indica un grupo de roles más restringido para este addon; conceda solo
   los permisos que necesiten esos cmdlets y esas consultas WMI.
4. **Esos cmdlets cargados en la sesión de PowerShell** que ejecuta el plugin.
   Véase
   [Cargar los cmdlets de administración de Exchange](#cargar-los-cmdlets-de-administracion-de-exchange).
5. **`powershell.exe` en la ruta de búsqueda** de la cuenta que ejecuta el
   agente.

El addon no almacena credenciales ni las pide: cada comprobación se ejecuta con
la identidad de la cuenta que ejecuta el agente, así que el acceso lo necesita
esa cuenta, no un usuario de monitorización aparte. Manténgala tan restringida
como permitan los cmdlets y no ejecute el agente como administrador del dominio
para hacer funcionar las comprobaciones.

### Instalar el plugin

Descargue el addon desde su entrada del Marketplace:

[pandorafms.exchange](https://marketplace.pandorafms.com/entries/pandorafms.exchange)

El paquete contiene el script del plugin. No tiene fichero de configuración:
todo ajuste es un conmutador de línea de comandos. Extraiga el paquete y copie el
script a una carpeta que la cuenta que ejecuta el agente pueda leer, por ejemplo
`C:\Program Files\pandora_agent\plugins`. Los comandos de esta página escriben
esa carpeta como `<PATH_TO_PLUGIN>` y el fichero del script como
`<PLUGIN_SCRIPT>`, según el nombre que tenga dentro del paquete descargado.

## Configuración

### Añadir el plugin al agente

El plugin se configura en el fichero de configuración del agente
(`pandora_agent.conf`) como una línea `module_plugin`. Esta línea ejecuta todos
los bloques excepto los módulos de servicios en el servidor que aloja el agente:

```apache
module_plugin powershell.exe -PSConsoleFile "<PATH_TO_EXCHANGE_SHELL>\<EXCHANGE_CONSOLE_FILE>" -command "& '<PATH_TO_PLUGIN>\<PLUGIN_SCRIPT>' -all 3> $NULL"
```

- `<PATH_TO_EXCHANGE_SHELL>\<EXCHANGE_CONSOLE_FILE>` es el fichero de consola de
  la shell de Exchange de la versión instalada, que carga los cmdlets de
  administración en la sesión (véase
  [Cargar los cmdlets de administración de Exchange](#cargar-los-cmdlets-de-administracion-de-exchange)).
- `-command "& '...' -all"` ejecuta el script con el conmutador `-all`. Las
  comillas simples protegen la ruta, así que una carpeta con espacios funciona
  sin cambios.
- `3> $NULL` descarta el flujo de advertencias de la sesión, de modo que solo el
  XML de módulos llega al agente.
- La línea se ejecuta una vez por intervalo del agente. Reinicie o recargue el
  agente después de editar el fichero.

Cuando el agente lee su configuración desde la consola (configuración remota), la
línea `module_plugin` pertenece a la configuración del agente guardada allí, y una
edición local de `pandora_agent.conf` es sobrescrita por el agente.

El addon no tiene timeout propio. Para acotar una ejecución, use la forma de
bloque con un timeout de módulo, en segundos:

```apache
module_begin
module_plugin powershell.exe -PSConsoleFile "<PATH_TO_EXCHANGE_SHELL>\<EXCHANGE_CONSOLE_FILE>" -command "& '<PATH_TO_PLUGIN>\<PLUGIN_SCRIPT>' -all 3> $NULL"
module_timeout 300
module_end
```

Una ejecución cortada por el timeout produce menos módulos que una completa.

### Elegir qué comprobar

Los conmutadores son indicadores independientes y se pueden combinar. Una
ejecución sin ningún conmutador se comporta como `-all`:

| Línea de comandos | Qué cubre la ejecución |
|-------------------|------------------------|
| Sin conmutador | Todos los bloques excepto servicios |
| `-all` | Todos los bloques excepto servicios |
| `-mailbox` | Comprobaciones de buzón |
| `-cas` | Comprobaciones de acceso de cliente |
| `-queue` | Módulo de cola de mensajes |
| `-cpu` | Módulo de procesador |
| `-memory` | Módulo de memoria |
| `-storage` | Módulos de volúmenes |
| `-services` | Módulos de servicios de Exchange |
| `-all -services` | Todos los bloques, servicios incluidos |
| `-queue -storage` | Módulos de cola de mensajes y de volúmenes |

Los bloques añaden sus módulos a la ejecución: un conmutador nunca elimina un
bloque seleccionado por otro. El bloque de servicios no forma parte de `-all` ni
de la ejecución por defecto; se activa explícitamente con `-services`.

Las comprobaciones de acceso de cliente usan el nombre del servidor local cuando
la ejecución no incluye las comprobaciones de buzón, así que `-cas` por sí solo
produce el conjunto completo de acceso de cliente. Cuando se ejecutan las
comprobaciones de buzón, las peticiones de informe de estado reutilizan la
identidad de servidor que informa `Test-ReplicationHealth`.

Los bloques de carga y almacenamiento son opcionales como cualquier otro: `-all`
y la ejecución por defecto los incluyen, y `-queue`, `-cpu`, `-memory` y
`-storage` los seleccionan uno a uno.

### Cargar los cmdlets de administración de Exchange

Las comprobaciones llaman a cmdlets de administración de Exchange y el addon no
importa ninguno por sí mismo. Por tanto, la invocación tiene que cargarlos en la
misma sesión de PowerShell antes de ejecutar el script. Pase el fichero de consola
de la versión de Exchange instalada con `-PSConsoleFile`, o cargue ese mismo
módulo al principio de la cadena `-command` —abajo como
`<EXCHANGE_SHELL_LOADER>`— y después llame al script:

```apache
module_plugin powershell.exe -PSConsoleFile "<PATH_TO_EXCHANGE_SHELL>\<EXCHANGE_CONSOLE_FILE>" -command "<EXCHANGE_SHELL_LOADER>; & '<PATH_TO_PLUGIN>\<PLUGIN_SCRIPT>' -all 3> $NULL"
```

Sin esos cmdlets toda comprobación falla y la ejecución escribe solo los módulos
que no los necesitan, normalmente ninguno. Véase
[Resolución de problemas](#resolucion-de-problemas).

## Verificación

Ejecute el plugin a mano antes de conectarlo al agente. Abra una Exchange
Management Shell en el servidor, o cualquier sesión de PowerShell con los cmdlets
de administración cargados, y ejecute:

```powershell
& '<PATH_TO_PLUGIN>\<PLUGIN_SCRIPT>' -all
```

Una ejecución correcta escribe un bloque `<module>` por resultado en la salida
estándar y nada más. Este es un extracto de una ejecución contra un único
servidor; los valores son ilustrativos y `EXCHANGE01` representa el nombre del
servidor:

```xml
<module>
<name>Message queue - EXCHANGE01</name>
<type>generic_data</type>
<data><![CDATA[0]]></data>
<description><![CDATA[Number of messages waiting to be processed under MessageCount column.]]></description>
</module>
<module>
<name>Database replication - EXCHANGE01</name>
<type>generic_proc</type>
<data><![CDATA[1]]></data>
<description><![CDATA[Test-ReplicationHealth cmdlet]]></description>
</module>
<module>
<name>DAG Status - EXCHANGE01</name>
<type>generic_proc</type>
<data><![CDATA[1]]></data>
<description><![CDATA[Get-MailboxDatabaseCopyStatus cmdlet]]></description>
</module>
<module>
<name>OWA - EXCHANGE01</name>
<type>generic_proc</type>
<data><![CDATA[1]]></data>
<description><![CDATA[OWA HealthSet .Monitors the overall health of the Outlook Web App service.]]></description>
</module>
```

Cuando la línea `module_plugin` está puesta y el agente la ha ejecutado, el
agente aparece en la consola en Recursos > Gestionar agentes:

![Agente Exchange en la lista de agentes](../assets/images/plugins/exchange/agents.png)

Los módulos aparecen bajo el agente del servidor Exchange:

![Módulos de Exchange en la vista principal del agente](../assets/images/plugins/exchange/modules.png)

Compruebe en este orden:

1. **Los módulos del agente.** El agente que ejecuta el plugin tiene un módulo por
   cada bloque de la última ejecución.
2. **Los valores.** Los módulos `generic_proc` informan `1` cuando toda la
   comprobación pasó. Un `0` es una comprobación fallida de verdad, no una
   ausente.
3. **La cobertura.** El número de módulos de una ejecución depende de los
   conmutadores y de lo que respondió el servidor; véase
   [Cobertura por rol](#cobertura-por-rol).

## Entender los resultados

### Cobertura por rol

Qué comprobaciones realiza una ejecución depende de los conmutadores, y qué
módulos aparecen depende además de si cada comprobación produjo un resultado:

| Grupo de módulos | Conmutador |
|------------------|------------|
| Buzón (replicación, MAPI, DAG) | `-mailbox` |
| Acceso de cliente, comprobaciones de informe de estado | `-cas` |
| `SMTP Connectivity` | `-cas` |
| Cola de mensajes | `-queue` |
| Procesador | `-cpu` |
| Memoria | `-memory` |
| Volúmenes | `-storage` |
| Servicios de Exchange | `-services` |

La ejecución por defecto y `-all` habilitan todos los grupos de la tabla excepto
los servicios de Exchange. Un conmutador añade solo su grupo y no cambia ningún
otro valor; combine los conmutadores que necesite.

### Cómo informa cada comprobación

Todas las comprobaciones de estado siguen el mismo patrón, y eso es lo que da
significado a un módulo ausente:

- **`1`** — el cmdlet devolvió al menos una fila y todas pasaron.
- **`0`** — el cmdlet devolvió filas y al menos una no pasó.
- **Sin módulo** — el cmdlet no devolvió nada, o no pudo ejecutarse. La ejecución
  no envía ningún valor para ese módulo.

Un módulo `generic_proc` con el valor `0` se muestra como no normal en la
consola, así que una alerta configurada sobre él salta ante una comprobación que
se ejecutó y falló. Una comprobación que nunca se ejecuta, o que el servidor no
puede responder, produce silencio: el módulo o no existe todavía o conserva el
último valor recibido.

El valor que cuenta como aprobado forma parte del addon: `Passed` o `Correcto`
para la comprobación de replicación, `Success` o `Correcto` para MAPI, y
`Healthy` para las comprobaciones de informe de estado. Véase
[Limitaciones conocidas](#limitaciones-conocidas).

### Módulos de carga y almacenamiento

Estos módulos describen el servidor y no necesitan ningún rol de Exchange:

| Nombre del módulo | Tipo | Valor |
|-------------------|------|-------|
| `Message queue - <host>` | `generic_data` | Mensajes en espera en la cola `Submission` |
| `CPU % - <host>` | `generic_data` | Porcentaje medio de carga de procesador |
| `Memory % - <host>` | `generic_data` | Porcentaje de memoria física en uso, redondeado a dos decimales |
| `Capacity(GB) - <host>-<volume>` | `generic_data` | Tamaño total del volumen, en GB, redondeado a dos decimales |
| `FreeSpace(GB) - <host>-<volume>` | `generic_data` | Espacio libre del volumen, en GB, redondeado a dos decimales |
| `Free(%) - <host>-<volume>` | `generic_data` | Espacio libre del volumen, en porcentaje redondeado sin decimales |

`<host>` es el nombre del servidor que ejecuta el plugin. `<volume>` es el nombre
del volumen tal como lo informa el sistema operativo, sin su barra invertida
final: un volumen `C:\` produce `Capacity(GB) - EXCHANGE01-C:`. Se escribe un
triplete por cada volumen que informa el servidor, incluidos los volúmenes sin
capacidad, como una unidad óptica.

Cuando su bloque está seleccionado, cada uno de estos módulos se escribe solo si
la consulta correspondiente devuelve datos; el módulo de memoria se escribe
siempre que su bloque esté seleccionado. Las consultas de procesador y de
memoria no tienen respaldo ante errores, así que un fallo en cualquiera de ellas
detiene la ejecución: los bloques que vienen después, como el triplete de
volúmenes y los módulos de servicios, no se escriben en esa ejecución.

### Comprobaciones de buzón

| Nombre del módulo | Tipo | `1` cuando |
|-------------------|------|------------|
| `Database replication - <server>` | `generic_proc` | Todas las filas de `Test-ReplicationHealth` informan aprobado |
| `MAPI Connectivity` | `generic_proc` | Todas las filas de `Test-MAPIConnectivity` informan aprobado |
| `DAG Status - <host>` | `generic_proc` | Todas las copias locales de base de datos informan una longitud de cola de copia inferior a 7 |

`<server>` en el módulo de replicación es el servidor que informa la última fila
del resultado, y ese módulo no tiene un sufijo fijo: su nombre depende de ese
valor. `MAPI Connectivity` no lleva sufijo de servidor.

La comprobación de DAG lee las copias alojadas en el servidor que ejecuta el
plugin, y considera un fallo una cola de siete registros o más. Un servidor sin
ninguna copia local de base de datos no escribe módulo de DAG.

### Comprobaciones de acceso de cliente

Cada uno de estos módulos es el estado de un conjunto de estado (health set) de
Exchange, más la prueba SMTP:

| Nombre del módulo | Conjunto de estado o prueba |
|-------------------|-----------------------------|
| `OWA - <host>` | `OWA` |
| `ActiveSync - <host>` | `ActiveSync` |
| `Web Services - <host>` | `EWS` |
| `Remote Powershell - <host>` | `RPS` |
| `POP - <host>` | `POP` |
| `IMAP - <host>` | `IMAP` |
| `ECP - <host>` | `ECP` |
| `Autodiscover - <host>` | `Autodiscover` |
| `Outlook - <host>` | `Outlook` |
| `Outlook client connectivity - <host>` | `Outlook`, solicitado por segunda vez en la misma ejecución |
| `SMTP Connectivity - <host>` | `Test-SmtpConnectivity` |

Un conjunto de estado informa `1` cuando todos sus monitores informan `Healthy`.
Los dos módulos de Outlook proceden de dos comprobaciones separadas que
consultan el mismo conjunto de estado, así que normalmente llevan el mismo valor.

### Módulos de servicios

Con `-services`, cada servicio instalado cuyo nombre contenga `MSExchange`
produce un módulo:

| Nombre del módulo | Tipo | Valor |
|-------------------|------|-------|
| `Service <service name>` | `generic_proc` | `1` mientras el servicio está en ejecución, `0` en caso contrario |

El conjunto de módulos sigue por tanto a los servicios instalados en el servidor,
y un servicio que se elimina del servidor deja de producir su módulo. Un servicio
en cualquier estado distinto de en ejecución —detenido, iniciándose,
deteniéndose— informa `0`.

## Operar y resolver problemas

### Funcionamiento diario

- El addon no guarda estado. Cada ejecución vuelve a lanzar las comprobaciones,
  así que una ejecución manual reproduce exactamente lo que hace el agente.
- Una ejecución que incluye los bloques de buzón y de acceso de cliente hace que
  el servidor Exchange realice pruebas en vivo: una prueba de estado de
  replicación, una prueba de inicio de sesión MAPI, una consulta del estado de las
  copias de base de datos de buzón y diez peticiones de informe de estado. Dé al
  módulo un intervalo acorde con ese coste, evite ejecutarlo cada minuto en un
  servidor con carga y deje fuera los bloques que no necesite.
- Los módulos los crea el agente a partir de la salida del script, así que una
  comprobación que empieza a informar un módulo nuevo no requiere cambios en la
  consola.
- Para cambiar lo que cubre una ejecución, edite los conmutadores de la línea
  `module_plugin` y reinicie el agente. No se almacena nada más, así que no hay
  estado que migrar.

### Limitaciones conocidas

Estos son comportamientos de esta versión, no errores de configuración:

- **`Outlook - <host>` y `Outlook client connectivity - <host>` son la misma
  prueba dos veces.** Ambos leen el conjunto de estado `Outlook`; el segundo
  módulo no lleva descripción.
- **Los valores de aprobado se reconocen solo en inglés y en español.** Un
  servidor Exchange localizado a otro idioma informa sus resultados con otras
  palabras, y el módulo afectado informa `0` aunque la comprobación haya pasado.
- **Un volumen sin capacidad sigue produciendo un módulo `Free(%)`.** El addon
  escribe el triplete para todos los volúmenes, así que una unidad óptica o
  cualquier otro volumen sin capacidad aparece con un porcentaje que no significa
  nada. Ignórelo o fíltrelo en la consola.

### Resolución de problemas

- **La ejecución no escribe ningún módulo de estado.** O los cmdlets de
  administración de Exchange no están cargados en la sesión, o la ruta del
  fichero de consola es incorrecta, o la cuenta no puede usarlos; o los cmdlets
  se ejecutan y no devuelven nada porque la cuenta se autentica contra otra
  organización o porque el servidor no tiene ningún rol que responda a esa
  comprobación. Si la ejecución incluye los bloques de carga o de
  almacenamiento, esos módulos aparecen igualmente, porque no dependen de
  cmdlets de Exchange. Ejecute el script a mano en una Exchange Management Shell
  para ver el error que produjo la sesión y revise después la cuenta.
- **Un módulo informa `0` en todas las comprobaciones.** Confirme el idioma del
  servidor antes de buscar un fallo real: los valores de aprobado se reconocen
  solo en inglés y en español.
- **Falta un módulo después de un cambio.** La comprobación no devolvió resultado.
  La consola conserva el último valor recibido para ese módulo, lo que puede
  ocultar el hueco.
- **Aparecen los módulos de carga pero no los tripletes de volúmenes ni los
  módulos de servicios.** Una consulta de procesador o de memoria falló y detuvo
  la ejecución en ese punto. El error va al flujo de errores de la sesión, así que
  ejecute el script a mano para leerlo.
- **El log del agente muestra un timeout.** Una ejecución completa con `-all`
  realiza una docena de pruebas en vivo. Suba el timeout del módulo, o separe los
  bloques que necesite en líneas `module_plugin` distintas, cada una con su
  propio timeout y su propio conmutador.

## Referencia

### Conmutadores

| Conmutador | Tipo | Valor por defecto | Efecto |
|------------|------|-------------------|--------|
| `-all` | indicador | Activo cuando no se da ningún conmutador | Bloques de buzón, acceso de cliente, cola, procesador, memoria y volúmenes |
| `-mailbox` | indicador | Desactivado | Comprobaciones de buzón |
| `-cas` | indicador | Desactivado | Comprobaciones de acceso de cliente |
| `-queue` | indicador | Desactivado | Módulo de cola de mensajes |
| `-cpu` | indicador | Desactivado | Módulo de procesador |
| `-memory` | indicador | Desactivado | Módulo de memoria |
| `-storage` | indicador | Desactivado | Módulos de volúmenes |
| `-services` | indicador | Desactivado | Un módulo por cada servicio de Exchange instalado |

El addon declara estos ocho conmutadores y ningún otro parámetro. No tiene
parámetros de verbosidad, timeout, destino ni credenciales, y escribe únicamente
en la salida estándar.

### Módulos generados

| Nombre del módulo | Tipo | Grupo |
|-------------------|------|-------|
| `Message queue - <host>` | `generic_data` | Carga |
| `CPU % - <host>` | `generic_data` | Carga |
| `Memory % - <host>` | `generic_data` | Carga |
| `Capacity(GB) - <host>-<volume>` | `generic_data` | Almacenamiento |
| `FreeSpace(GB) - <host>-<volume>` | `generic_data` | Almacenamiento |
| `Free(%) - <host>-<volume>` | `generic_data` | Almacenamiento |
| `Database replication - <server>` | `generic_proc` | Buzón |
| `MAPI Connectivity` | `generic_proc` | Buzón |
| `DAG Status - <host>` | `generic_proc` | Buzón |
| `OWA - <host>` | `generic_proc` | Acceso de cliente |
| `ActiveSync - <host>` | `generic_proc` | Acceso de cliente |
| `Web Services - <host>` | `generic_proc` | Acceso de cliente |
| `Remote Powershell - <host>` | `generic_proc` | Acceso de cliente |
| `POP - <host>` | `generic_proc` | Acceso de cliente |
| `IMAP - <host>` | `generic_proc` | Acceso de cliente |
| `ECP - <host>` | `generic_proc` | Acceso de cliente |
| `Autodiscover - <host>` | `generic_proc` | Acceso de cliente |
| `Outlook - <host>` | `generic_proc` | Acceso de cliente |
| `Outlook client connectivity - <host>` | `generic_proc` | Acceso de cliente |
| `SMTP Connectivity - <host>` | `generic_proc` | Acceso de cliente |
| `Service <service name>` | `generic_proc` | Servicios |

Los nombres de módulo conservan la ortografía del addon: `Remote Powershell` se
escribe con la `s` minúscula y `MAPI Connectivity` no lleva sufijo de servidor.

### Salida

- Cada resultado es un bloque `<module>` en la salida estándar, con `name`,
  `type`, `data` y `description`. El agente los lee y crea los módulos.
- El addon descarta los errores de las comprobaciones de estado: una comprobación
  que falla no deja módulo ni mensaje. Para ver el error, ejecute el script a
  mano en una sesión que no redirija el flujo de errores.
- El addon no define ningún estado de salida propio. Una ejecución que se detiene
  por un error escribe los módulos que había producido hasta ese punto.

### Identidad del addon

| Propiedad | Valor |
|-----------|-------|
| Identificador del Marketplace | `pandorafms.exchange` |
| Nombre | Exchange |
| Versión | `1.1` — la versión del paquete `pandorafms.exchange.1.1.zip` del Marketplace |
| Categoría | Miscelaneus |
| Etiquetas | applications |
| Licencia | Free |
| Última actualización en el Marketplace | 2026-11-12 |
| Disponibilidad | Descarga gratuita |
| Entrada del Marketplace | [pandorafms.exchange](https://marketplace.pandorafms.com/entries/pandorafms.exchange) |
| Modelo de ejecución | Plugin de agente de Pandora FMS (`module_plugin`) en el servidor Exchange |
