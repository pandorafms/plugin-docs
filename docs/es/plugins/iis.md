# IIS

*Última actualización del artículo: 2026-11-12.*

## Qué hace

El addon IIS monitoriza Microsoft Internet Information Services (IIS) desde Pandora FMS.
Cada ejecución inspecciona los servicios de IIS, los sitios y los grupos de aplicaciones,
lee los contadores de rendimiento, comprueba opcionalmente una lista de URL, lee los
eventos de Windows y analiza los logs de IIS, y escribe el resultado como módulos de
Pandora FMS en la salida estándar. El agente Windows de Pandora FMS que ejecuta el addon
ingiere esa salida, de modo que cada pasada actualiza los módulos del agente instalado en
el host de IIS.

El addon es un plugin de agente: se ejecuta una vez, imprime un bloque `<module>` por
resultado y termina. No crea ningún agente propio —los módulos pertenecen al agente que lo
ejecuta— y mantiene un fichero de estado JSON para el registro de eventos y los logs de
IIS, de forma que las ejecuciones consecutivas no repiten datos.

Una sola ejecución sustituye a los antiguos scripts separados de estado, logs y eventos de
IIS, por lo que el agente ejecuta un único plugin en lugar de tres.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Windows Server 2025 con IIS 10 | `Probado` | Una ejecución real en Windows Server 2025 build 26100 con IIS 10 y una instalación en español produjo 51 módulos en dos ejecuciones consecutivas |
| Windows PowerShell 5.1 | `Requerido` | El addon se ejecuta con Windows PowerShell 5.1; la prueba real se ejecutó en Windows PowerShell 5.1.26100 |
| IIS instalado con el módulo `WebAdministration` | `Requerido` | La sección de estado lee los servicios, los sitios y los grupos de aplicaciones mediante `Get-Website`, `Get-IISAppPool` y `Get-WebAppPoolState` |
| Un agente Windows de Pandora FMS en el host de IIS | `Requerido` | El agente ejecuta el addon e ingiere su salida `<module>` |
| Otras versiones de Windows Server, IIS 7/7.5/8/8.5 y Windows PowerShell 7 | `Sin validar` | No se han producido registros de prueba para esas combinaciones |
| Versiones de Pandora FMS NG | `Sin validar` | No se ha registrado una declaración oficial de compatibilidad para este addon |

### Requisitos

1. **Un host Windows con IIS instalado.** La sección de estado necesita el módulo
   `WebAdministration` de IIS. Instale el rol de servidor web de IIS junto con sus
   herramientas de gestión; un servidor web instalado sin las herramientas de gestión no
   proporciona el módulo.

2. **Windows PowerShell 5.1.** El agente inicia el addon con `powershell.exe`, y el addon
   utiliza sintaxis y cmdlets disponibles en Windows PowerShell 5.1.

3. **Un agente Windows de Pandora FMS en el mismo host.** El agente ejecuta el addon e
   ingiere los módulos que imprime. No se instala nada en otros hosts.

4. **Una cuenta que pueda leer los datos monitorizados y escribir el fichero de estado.**
   El addon no tiene credenciales propias: se ejecuta con la cuenta del servicio del agente
   de Pandora FMS. Esa cuenta debe poder leer la configuración de IIS, el registro de
   eventos de Windows y el directorio de logs de IIS, y escribir el fichero de estado JSON.

5. **Pandora FMS** para recibir los módulos, accesible desde el agente a través de su
   conexión Tentacle habitual.

### Instalar el addon

Coloque el fichero del plugin en una carpeta legible por la cuenta del agente. Los
ejemplos siguientes utilizan la carpeta `util` del agente:

```text
%PANDORA_HOME%\util\Pandora_Plugin_IIS.ps1
```

Los ficheros opcionales de configuración y de listas pueden estar en la misma carpeta:

```text
%PANDORA_HOME%\util\Pandora_Plugin_IIS.json
%PANDORA_HOME%\util\iis_urls.txt
%PANDORA_HOME%\util\iis_counters.txt
```

## Configuración

### El fichero de configuración

El addon acepta parámetros de línea de comandos y, de forma opcional, un fichero de
configuración JSON que se pasa con `-Config`. Cada clave de configuración tiene el mismo
nombre que su parámetro de línea de comandos, y un parámetro escrito en la línea de
comandos tiene prioridad sobre el valor del fichero.

Un fichero de configuración que habilita las secciones de estado, rendimiento, URL,
eventos y logs y deja los ficheros de listas en la carpeta `util` del agente:

```json
{
  "Sections": "status,performance,urls,events,logs",
  "UrlList": "C:\\Program Files\\pandora_agent\\util\\iis_urls.txt",
  "LogPath": "C:\\inetpub\\logs\\LogFiles",
  "LogFormat": "auto",
  "EventLogs": "System",
  "EventProviders": "W3SVC,WAS,APPHOSTSVC,IISReset,WMSVC,Microsoft-Windows-IIS-W3SVC,Microsoft-Windows-IIS-APPHOSTSVC,Microsoft-Windows-HttpService",
  "PerfPreset": "basic",
  "PerfCounters": "C:\\Program Files\\pandora_agent\\util\\iis_counters.txt",
  "StateFile": "C:\\Program Files\\pandora_agent\\util\\Pandora_Plugin_IIS.state.json",
  "Services": "W3SVC,WAS,WMSVC",
  "MaxSeconds": 55,
  "RequestTimeout": 10,
  "MaxLinesPerLog": 5000,
  "MaxBytesPerLog": 8388608
}
```

Sin `-Config`, el addon ejecuta las secciones `status` y `performance` con sus valores
predeterminados.

### Ficheros auxiliares

La sección `urls` lee un fichero de texto plano con una entrada por línea. Una entrada es
una URL, o un nombre y una URL separados por `|`. Las líneas que empiezan por `#` y las
líneas vacías se ignoran:

```text
Default Web Site|http://localhost/
API health|https://localhost/api/health
```

La sección `performance` lee un fichero de contadores personalizados con una ruta de
contador de rendimiento por línea, en su forma canónica en inglés. Las líneas que empiezan
por `#` y las líneas vacías se ignoran:

```text
\Web Service(_Total)\Current Connections
\Web Service(_Total)\Get Requests/sec
\Web Service(_Total)\Not Found Errors/sec
\Web Service(_Total)\Service Uptime
```

Los ficheros de contadores y de URL pueden guardarse en UTF-8 (con o sin BOM), UTF-16 o la
codificación ANSI del sistema.

### Registrar la ejecución

Pandora FMS ejecuta el addon como plugin de agente: el agente ejecuta el comando en su
intervalo y analiza los bloques `<module>` que el comando imprime. Registre la ejecución en
la lista de plugins del agente, o añada la línea `module_plugin` equivalente a
`pandora_agent.conf`:

```apache
module_plugin powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PANDORA_HOME%\util\Pandora_Plugin_IIS.ps1" -Config "%PANDORA_HOME%\util\Pandora_Plugin_IIS.json"
```

Utilice `-All` en lugar de `-Config` para habilitar todas las secciones con los valores
predeterminados:

```apache
module_plugin powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PANDORA_HOME%\util\Pandora_Plugin_IIS.ps1" -All
```

El addon limita su propio tiempo de ejecución con `-MaxSeconds` (55 segundos de forma
predeterminada) y procesa los logs y los eventos en lotes acotados. Configure el intervalo
del agente por encima de ese presupuesto para que una ejecución termine antes de que
empiece la siguiente.

## Verificación

Ejecute el addon manualmente en el host de IIS, desde una consola de PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PANDORA_HOME%\util\Pandora_Plugin_IIS.ps1" -Sections status,performance
```

Una ejecución correcta imprime los bloques de módulos y termina. Extracto de la salida,
reducido a la versión, un servicio, un sitio y un contador global:

```xml
<module>
<name><![CDATA[IIS Version]]></name>
<type><![CDATA[generic_data_string]]></type>
<data><![CDATA[10.0]]></data>
<description><![CDATA[IIS registry version: Version 10.0]]></description>
</module>
<module>
<name><![CDATA[IIS Service - W3SVC]]></name>
<type><![CDATA[generic_proc]]></type>
<data><![CDATA[1]]></data>
<description><![CDATA[Windows service W3SVC status: Running]]></description>
</module>
<module>
<name><![CDATA[IIS Site Status - Default Web Site]]></name>
<type><![CDATA[generic_proc]]></type>
<data><![CDATA[1]]></data>
<description><![CDATA[Site ID: 1; State: Started; Physical path: %SystemDrive%\inetpub\wwwroot]]></description>
</module>
<module>
<name><![CDATA[IIS Global - Current Connections]]></name>
<type><![CDATA[generic_data]]></type>
<data><![CDATA[1]]></data>
<description><![CDATA[Web Service counter CurrentConnections for instance _Total]]></description>
</module>
```

Los avisos y la información de depuración se escriben en el flujo de error y no impiden que
se impriman los módulos. Después compruebe el agente: tras la siguiente ejecución, su lista
de módulos incluye los módulos generados.

![Lista de agentes con el agente IIS creado por el plugin](../assets/images/plugins/iis/agent-list.png)

![Lista de módulos del agente con los módulos de IIS generados por el plugin](../assets/images/plugins/iis/console-modules.png)

![Lista de módulos del agente con los módulos de rendimiento, URL, eventos y logs de IIS](../assets/images/plugins/iis/console-modules-performance.png)

## Entender los resultados

El addon agrupa sus módulos por lo que describen. Los módulos de sitios y grupos de
aplicaciones se crean de forma automática: un módulo por cada sitio y por cada grupo de
aplicaciones encontrado en el host, con el nombre del sitio o del grupo en el nombre del
módulo. La instancia `_Total` de los contadores se reporta como `Global`.

- **Estado.** `IIS Version` reporta la versión mayor y menor de IIS. Un módulo
  `IIS Service - <servicio>` por cada servicio configurado reporta `1` mientras el servicio
  está en ejecución y `0` en caso contrario. Un módulo `IIS Site Status - <sitio>` por cada
  sitio reporta `1` mientras el sitio está iniciado. Un módulo
  `IIS AppPool Status - <grupo>` por cada grupo de aplicaciones reporta `1` mientras el
  grupo está iniciado.
- **Rendimiento.** `IIS Global - <métrica>` e `IIS Site <sitio> - <métrica>` reportan los
  contadores de Web Service para la instancia `_Total` y para cada sitio.
  `IIS AppPool <grupo> - <métrica>` reporta los contadores del grupo de aplicaciones, e
  `IIS AppPool <grupo> - Running` reporta `1` mientras el estado del grupo es `Running`.
  Cuando las clases de rendimiento de ASP.NET están instaladas,
  `IIS ASP.NET <grupo> - <métrica>` e `IIS ASP.NET Global - <métrica>` reportan los
  contadores de ASP.NET.
- **Contadores personalizados.** `IIS PerfCounter - <ruta>` reporta cada contador del
  fichero de contadores personalizados. El nombre del módulo conserva la ruta canónica en
  inglés aunque el contador se lea a través de su nombre localizado.
- **URL.** `IIS URL <nombre> - Status` reporta `1` cuando la petición tiene éxito y `0`
  cuando falla, `IIS URL <nombre> - HTTP Code` reporta el código de estado HTTP e
  `IIS URL <nombre> - Response Time` reporta el tiempo de la petición en milisegundos.
- **Eventos.** `IIS Events <log> - Critical`, `- Error` y `- Warning` cuentan los eventos
  nuevos del registro configurado desde la ejecución anterior, e `IIS Last Event - <log>`
  conserva el último evento como cadena.
- **Logs.** `IIS HTTP Requests - <sitio>` cuenta las entradas de log procesadas en el
  intervalo, e `IIS HTTP 4xx - <sitio>` e `IIS HTTP 5xx - <sitio>` cuentan las respuestas de
  error de cliente y de servidor.

Las métricas de rendimiento integradas se leen a través de clases de rendimiento de Windows
cuyos nombres no dependen del idioma del sistema operativo, por lo que funcionan en
instalaciones de Windows en cualquier idioma. Los contadores personalizados se escriben en
su forma canónica en inglés y se traducen al idioma de Windows en tiempo de ejecución.

![Gráfica real de IIS Global Current Connections](../assets/images/plugins/iis/graph-current-connections.png)

![Gráfica real de IIS Global Bytes Sent/sec](../assets/images/plugins/iis/graph-bytes-sent.png)

## Operación y resolución de problemas

### Coste de ejecución y planificación

Las secciones predeterminadas (`status,performance`) son las más ligeras. Las secciones
`urls`, `events` y `logs` añaden trabajo: cada URL se solicita con un tiempo de espera, el
registro de eventos se consulta desde la ejecución anterior y los ficheros de log se leen
desde la posición guardada en el fichero de estado.

El addon acota ese trabajo con `-MaxSeconds` (55 segundos de forma predeterminada),
`-MaxBytesPerLog` (8 MiB de forma predeterminada) y `-MaxLinesPerLog` (5000 líneas de forma
predeterminada). Cuando un fichero de log supera un límite, el contenido restante se procesa
en la siguiente ejecución. Cuando se agota el presupuesto de tiempo, se omiten las secciones
restantes y los módulos ya recogidos se imprimen igualmente.

El fichero de estado guarda la última posición procesada de cada fichero de log, los sitios
vistos en esos ficheros, el último identificador de evento por registro de eventos y la
marca de tiempo de la última ejecución. Se puede borrar sin riesgo: la siguiente ejecución
parte del final actual de los logs y de los eventos. Si no se establece `StateFile`, el
addon utiliza `%PANDORA_HOME%\util\Pandora_Plugin_IIS.state.json` cuando esa carpeta existe,
y la carpeta temporal del sistema en caso contrario.

### Ejecución manual y modo de depuración

Ejecute el addon manualmente para comprobar la configuración antes de registrarlo. Añada
`-Debug` para escribir información de depuración en el flujo de error, incluido el número
de módulos recogidos y los candidatos de contador que se han probado.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PANDORA_HOME%\util\Pandora_Plugin_IIS.ps1" -All -Debug
```

### No aparecen módulos en la consola

- **La ejecución no está registrada en el agente.** El addon no imprime nada hasta que el
  agente lo ejecuta. Ejecute el comando manualmente primero y después revise el log del
  agente para esa ejecución.
- **La ruta de `module_plugin` es incorrecta.** Utilice la ruta completa al fichero del
  plugin y entrecomíllela; los ejemplos usan `%PANDORA_HOME%\util\`.
- **La cuenta del agente no puede leer el plugin o los ficheros de listas.** Cópielos a una
  carpeta que la cuenta pueda leer o ajuste los permisos.
- **IIS no está instalado o falta el módulo `WebAdministration`.** La sección de estado
  informa de un error y se omiten los módulos de sitios y grupos de aplicaciones. Instale el
  rol de servidor web de IIS con sus herramientas de gestión y vuelva a ejecutar el addon.
- **El presupuesto de tiempo es demasiado pequeño.** Aumente `-MaxSeconds` o reduzca
  `Sections`.

### Falta el módulo de un servicio

El addon crea un módulo de servicio solo para un servicio que existe en el host. Cuando un
servicio no está instalado, escribe un aviso y omite el módulo —no se reporta ningún valor
`0`—. Por ejemplo, un host sin el servicio de administración de IIS no tiene módulo
`WMSVC`. Ejecute `Get-Service <servicio>` para confirmar si el servicio existe.

### No aparecen los contadores personalizados

El addon traduce cada ruta de contador canónica en inglés al idioma de Windows y prueba los
candidatos que encuentra en el registro de rendimiento. Un contador que no existe en el
idioma actual, o que no está registrado en el host, se omite con un aviso. Ejecute el addon
con `-Debug` para ver qué candidatos se han probado y compruebe el contador con
`Get-Counter` en el host. Las métricas integradas de `status` y `performance` ya cubren los
valores de IIS más habituales, por lo que el fichero de contadores personalizados es
opcional.

### No aparecen módulos de logs

- **La sección `logs` está deshabilitada.** Añada `logs` a `Sections` o utilice `-All`.
- **`LogPath` no apunta a los logs de IIS.** La carpeta predeterminada de logs de IIS es
  `C:\inetpub\logs\LogFiles`.
- **No hay líneas nuevas en el log.** El addon solo cuenta las líneas escritas desde la
  ejecución anterior. Una segunda ejecución sin tráfico nuevo reporta `0`.
- **Los ficheros de log superan los límites por ejecución.** Las líneas restantes se
  procesan en la siguiente ejecución; aumente `-MaxLinesPerLog` o `-MaxBytesPerLog` si
  necesita ponerse al día antes.

### No aparecen módulos de eventos

- **La sección `events` está deshabilitada.** Añada `events` a `Sections` o utilice `-All`.
- **Ningún evento coincide con el filtro.** Cuando no hay eventos en el intervalo, los
  módulos de conteo reportan `0` e `IIS Last Event` conserva el último evento conocido.
- **Los nombres de proveedor no coinciden con el host.** Ajuste `EventProviders`; el addon
  recurre a una consulta sin el filtro de proveedores cuando la consulta filtrada falla.

## Referencia

### Parámetros

| Nombre | Requerido | Predeterminado | Descripción |
| --- | --- | --- | --- |
| `-Config` | No | Vacío | Ruta a un fichero de configuración JSON. Los parámetros de línea de comandos tienen prioridad sobre el fichero. |
| `-Sections` | No | `status,performance` | Secciones separadas por comas: `status`, `performance`, `urls`, `events`, `logs`. |
| `-UrlList` | No | Vacío | Fichero con URL, una por línea o `nombre|url`. Lo utiliza `urls`. |
| `-LogPath` | No | Vacío | Fichero o directorio de logs de IIS. Lo utiliza `logs`. |
| `-LogFormat` | No | `auto` | Formato del log: `auto`, `W3C`, `IIS` o `NCSA`. |
| `-EventLogs` | No | `System` | Registros de eventos que se leen, separados por comas. |
| `-EventProviders` | No | `W3SVC,WAS,APPHOSTSVC,IISReset,WMSVC,Microsoft-Windows-IIS-W3SVC,Microsoft-Windows-IIS-APPHOSTSVC,Microsoft-Windows-HttpService` | Proveedores de eventos por los que filtrar, separados por comas. |
| `-PerfPreset` | No | `basic` | Preajuste de rendimiento: `none`, `basic` o `full`. `basic` y `full` leen las métricas integradas; los contadores personalizados se añaden cuando se establece `-PerfCounters` y el preajuste no es `none`. |
| `-PerfCounters` | No | Vacío | Fichero con rutas de contadores de rendimiento personalizados, una por línea. |
| `-StateFile` | No | `%PANDORA_HOME%\util\Pandora_Plugin_IIS.state.json` cuando está disponible; en caso contrario, `%TEMP%\Pandora_Plugin_IIS.state.json` | Fichero de estado JSON para logs y eventos incrementales. |
| `-Services` | No | `W3SVC,WAS,WMSVC` | Servicios de Windows que se comprueban, separados por comas. |
| `-MaxSeconds` | No | `55` | Presupuesto de tiempo de ejecución en segundos. |
| `-RequestTimeout` | No | `10` | Tiempo de espera de las peticiones URL en segundos. |
| `-MaxLinesPerLog` | No | `5000` | Número máximo de líneas de log procesadas por fichero y ejecución. |
| `-MaxBytesPerLog` | No | `8388608` | Número máximo de bytes de log procesados por fichero y ejecución. |
| `-All` | No | Desactivado | Habilita todas las secciones. |
| `-Debug` | No | Desactivado | Escribe información de depuración en el flujo de error. |
| `-Help` | No | Desactivado | Imprime el texto de ayuda y termina. |

### Fichero de configuración

El fichero JSON acepta los mismos nombres que los parámetros de línea de comandos, sin el
guion `-` inicial. Todas las claves son opcionales. El addon lee primero el fichero y
después aplica los parámetros escritos en la línea de comandos, por lo que un parámetro
indicado en la línea de comandos anula el valor del fichero.

### Módulos generados

| Nombre del módulo | Tipo | Valor |
| --- | --- | --- |
| `IIS Version` | `generic_data_string` | Versión mayor y menor de IIS |
| `IIS Service - <servicio>` | `generic_proc` | `1` mientras el servicio está en ejecución, `0` en caso contrario; se omite cuando el servicio no está instalado |
| `IIS Site Status - <sitio>` | `generic_proc` | `1` mientras el sitio está iniciado, `0` en caso contrario |
| `IIS AppPool Status - <grupo>` | `generic_proc` | `1` mientras el grupo de aplicaciones está iniciado, `0` en caso contrario |
| `IIS Global - <métrica>` | `generic_data` | Contador de Web Service para la instancia `_Total` |
| `IIS Site <sitio> - <métrica>` | `generic_data` | Contador de Web Service de un sitio |
| `IIS AppPool <grupo> - <métrica>` | `generic_data` | Contador del grupo de aplicaciones |
| `IIS AppPool <grupo> - Running` | `generic_proc` | `1` mientras el estado del grupo de aplicaciones es `Running` |
| `IIS ASP.NET <ámbito> - <métrica>` | `generic_data` | Contador de ASP.NET, cuando las clases de rendimiento de ASP.NET están instaladas |
| `IIS PerfCounter - <ruta>` | `generic_data` | Valor de un contador personalizado, nombrado según su ruta canónica en inglés |
| `IIS URL <nombre> - Status` | `generic_proc` | `1` cuando la petición tiene éxito, `0` en caso contrario |
| `IIS URL <nombre> - HTTP Code` | `generic_data` | Código de estado HTTP de la petición |
| `IIS URL <nombre> - Response Time` | `generic_data` | Tiempo de la petición en milisegundos |
| `IIS Events <log> - Critical` | `generic_data` | Eventos críticos del registro durante el intervalo |
| `IIS Events <log> - Error` | `generic_data` | Eventos de error del registro durante el intervalo |
| `IIS Events <log> - Warning` | `generic_data` | Eventos de advertencia del registro durante el intervalo |
| `IIS Last Event - <log>` | `async_string` | Último evento del registro |
| `IIS HTTP Requests - <sitio>` | `generic_data` | Entradas de log procesadas durante el intervalo |
| `IIS HTTP 4xx - <sitio>` | `generic_data` | Respuestas de error de cliente durante el intervalo |
| `IIS HTTP 5xx - <sitio>` | `generic_data` | Respuestas de error de servidor durante el intervalo |

### Métricas de Web Service

`Current Connections`, `Bytes Sent/sec`, `Bytes Received/sec`, `Get Requests/sec`,
`Post Requests/sec`, `Not Found Errors/sec`, `Total Method Requests/sec`,
`Current Anonymous Users`, `Current NonAnonymous Users`, `Maximum Connections`,
`Service Uptime`.

### Métricas de grupos de aplicaciones

`State`, `Uptime`, `Current Worker Processes`, `Maximum Worker Processes`,
`Recent Worker Process Failures`, `Total Application Pool Recycles`,
`Total Worker Process Ping Failures`, `Total Worker Process Startup Failures`,
`Total Worker Process Shutdown Failures`.

### Métricas de ASP.NET

`Application Restarts`, `Requests Queued`, `Request Wait Time`, `Requests Current`,
`Requests Total`, `Worker Processes Running`, `Worker Process Restarts`. Estos módulos
aparecen solo cuando las clases de rendimiento de ASP.NET correspondientes están instaladas
en el host.

### Identidad del plugin

| Propiedad | Valor |
| --- | --- |
| Nombre | IIS |
| Fichero del plugin | `Pandora_Plugin_IIS.ps1` |
| Versión | 2.0.0 |
| Modelo de ejecución | Plugin de agente software de Windows (`module_plugin`) |
| Secciones predeterminadas | `status,performance` |
| Fichero de estado | `Pandora_Plugin_IIS.state.json` |
| Licencia y disponibilidad | No documentadas en este repositorio |
