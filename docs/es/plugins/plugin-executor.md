# Pandora Plugin Executor

*Última actualización del artículo: 2026-10-26.*

## Qué hace

`pandora-plugin_exec` es un único ejecutable autónomo que monitoriza cualquier cosa accesible mediante una petición HTTP o un comando local, y convierte el resultado en agentes y módulos de Pandora FMS. Sustituye un plugin por tecnología por un solo programa más un catálogo de **plantillas** YAML.

Cada ejecución lee una plantilla y la ejecuta una vez:

```text
plantilla.yml → ejecutar tareas → filtrar su salida en variables → construir agentes y módulos → entregar
```

Una plantilla declara cuatro cosas:

- **Tareas** — peticiones HTTP o comandos locales, ejecutados de forma secuencial. Una tarea posterior puede usar valores producidos por una anterior, así que la cadena inicio de sesión → token → petición autenticada cabe en una sola ejecución.
- **Filtros** — una expresión `jq` o una expresión regular que extrae valores de la salida de una tarea hacia una **variable**.
- **Agentes y módulos** — construidos a partir de esas variables con expresiones `{{ }}`. Un módulo por bloque declarado, o uno por cada elemento de un array.
- **Transferencia** — cómo llega el resultado a Pandora FMS: Tentacle, un directorio de datos local de Pandora o la salida estándar de un plugin de agente software.

El ejecutor es **one-shot**: ejecuta la plantilla una vez y termina. La planificación sigue donde ya estaba: el agente de Pandora FMS, `cron` o el propio servidor de Pandora FMS.

El addon incluye plantillas ya construidas, entre ellas sustitutos de los plugins de agente `pandora_df_used_go`, `pandora_mem_used` y `pandora_netusage`. Consulte [Plantillas incluidas](#plantillas-incluidas).

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
|--------|--------|-----------|
| Addon `Pandora-Plugin-Executor`, versión `1.0` | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del addon](#identidad-del-addon) |
| Un host que pueda ejecutar `pandora-plugin_exec` | `Requerido` | El addon es un ejecutable autónomo sin dependencias de runtime; lo arranca el agente, `cron` o una persona |
| `/bin/sh` y los comandos que invoquen sus plantillas | `Requerido` | Las tareas `local` se ejecutan mediante `/bin/sh -c`; los binarios y ficheros que nombre la plantilla (`df`, `awk`, `/proc/meminfo`, ...) deben existir en ese host |
| Acceso de red desde ese host a las URL de la plantilla | `Requerido` cuando la plantilla tiene tareas `request` | El ejecutor abre la conexión por sí mismo |
| El cliente Tentacle (`tentacle_client`) | `Requerido` cuando `transfer.mode: tentacle` | El documento se envía invocando el cliente Tentacle |
| Permiso de escritura en `transfer.local.directory` | `Requerido` cuando `transfer.mode: local` | El documento de agente se escribe en ese directorio |
| Un agente software de Pandora FMS capaz de ejecutar comandos `module_plugin` | `Requerido` cuando `transfer.mode: agent_plugin` | El agente es quien arranca el ejecutor e ingiere los fragmentos de módulo que imprime |
| Sistema operativo, distribución y arquitectura | `Sin validar` | No hay matriz de plataformas registrada para este addon. El registro de diseño menciona ejecuciones de extremo a extremo en un host real, pero no identifica distribución, versión ni arquitectura, y la etiqueta `linux` del Marketplace es una etiqueta, no una declaración de compatibilidad |
| Windows | `Sin validar` | Esta página no describe ninguna ruta de instalación en Windows, y no hay ningún artefacto de Windows identificado para este addon |
| Versiones de Pandora FMS | `Sin validar` | El aviso del Marketplace («All integrations are compatible with Pandora FMS NG 784 and later versions») es general para todas las integraciones, no una declaración sobre este addon |

### Requisitos

1. **Un host para ejecutar el ejecutable.** Se entrega como un fichero autónomo llamado `pandora-plugin_exec`; no hay instalador, ni servicio, ni runtime que instalar.
2. **Un shell y las herramientas que invoquen sus plantillas.** Cada tarea `local` es un comando de shell, así que los binarios y los ficheros a los que hace referencia deben existir en ese host y ser legibles por el usuario que ejecuta el ejecutor.
3. **Pandora FMS** para recibir el resultado: el servidor en modo `tentacle` o `local`, o el agente software de Pandora FMS del host monitorizado en modo `agent_plugin`.
4. **El cliente Tentacle**, solo cuando la plantilla entrega con `transfer.mode: tentacle`.

El ejecutor se ejecuta con los privilegios del usuario que lo arranca. Ese usuario necesita el cliente Tentacle en su `PATH` (o una ruta absoluta en la plantilla), o permiso de escritura en el directorio de datos de Pandora, según el modo elegido.

### Instalar el addon

Descargue el paquete desde la entrada gratuita del Marketplace:

[https://marketplace.pandorafms.com/entries/Pandora-Plugin-Executor](https://marketplace.pandorafms.com/entries/Pandora-Plugin-Executor)

El fichero identificado para la versión 1.0 es `Pandora-Plugin-Executor.1.0.zip`. El artefacto que distribuye el addon es el ejecutable `pandora-plugin_exec`.

1. Copie el ejecutable al host que lo va a ejecutar y dele permiso de ejecución, por ejemplo `/usr/bin/pandora-plugin_exec`.
2. Copie las plantillas que vaya a usar a un directorio que el usuario del ejecutor pueda leer, por ejemplo `/etc/pandora/templates/`. El ejecutor solo lee la plantilla indicada con `-t`; nunca recorre un directorio.

No se instala nada en el sistema monitorizado salvo que ese sistema sea también el host que ejecuta el ejecutor, lo que solo ocurre en modo `agent_plugin`.

## Configuración

### Elegir un modo de entrega

`transfer.mode` es obligatorio y decide dónde se ejecuta el ejecutor y qué imprime.

| Modo | Se ejecuta en | Produce | Requisito |
|------|---------------|---------|-----------|
| `agent_plugin` | El host monitorizado | Fragmentos `<module>` en la salida estándar; el agente real de Pandora FMS añade la cabecera del agente | El agente software de Pandora FMS lo arranca como `module_plugin` |
| `tentacle` | Cualquier host con acceso de red al servidor de Pandora FMS | Un documento `<agent_data>` completo por cada agente de la plantilla, enviado con el cliente Tentacle | `tentacle_client` disponible y `transfer.tentacle.address` |
| `local` | El servidor de Pandora FMS, o cualquier host que pueda escribir en un directorio de datos de Pandora | Un documento `<agent_data>` completo por cada agente de la plantilla, escrito como fichero `.data` | `transfer.local.directory` escribible por el usuario del ejecutor |

Esta es la plantilla completa más corta, en modo `agent_plugin`: lee el uso del sistema de archivos raíz y publica un módulo.

```yaml
tasks:
  - name: disk_root
    type: local
    local:
      command: "df --output=pcent / | tail -1 | tr -d ' %'"
    variable: disk_pct

modules:
  - name: "Root disk used"
    type: generic_data
    data: "{{ disk_pct }}"
    unit: "%"
    min_warning: 80
    min_critical: 90

transfer:
  mode: agent_plugin
```

La misma plantilla en modo `tentacle`, con un bloque `agents` en lugar de módulos de nivel superior, porque un documento de agente completo necesita un nombre de agente:

```yaml
tasks:
  - name: api_stats
    type: request
    request:
      url: "https://<TARGET_HOST>/api/stats"
      headers:
        Authorization: "Bearer <API_TOKEN>"
      timeout: 10
    filter:
      type: jq
      expression: ".users.active"
    variable: active_users

agents:
  - name: "myapp"
    group: "Applications"
    interval: 300
    modules:
      - name: "Active users"
        type: generic_data
        data: "{{ active_users }}"

transfer:
  mode: tentacle
  tentacle:
    address: "<PANDORA_FMS_URL>"
```

Para el modo `local`, sustituya el último bloque:

```yaml
transfer:
  mode: local
  local:
    directory: "/var/spool/pandora/data_in"
```

### Registrar el ejecutor en Pandora FMS

El ejecutor no se instala en ninguna parte ni planifica nada. Elija el registro que corresponda al modo.

**Como plugin de agente software** (`agent_plugin`). Añada la invocación al fichero de configuración del agente y reinicie el agente:

```text
module_plugin /usr/bin/pandora-plugin_exec -t /etc/pandora/templates/disk_load.yml
```

El agente lo ejecuta con el intervalo configurado para el plugin e ingiere los fragmentos de módulo que imprime. El agente aporta el nombre, el grupo y el intervalo: todo lo que la plantilla declare en un bloque `agents:` se ignora en este modo (consulte [Qué llega a Pandora FMS](#que-llega-a-pandora-fms)).

<!-- SCREENSHOT NEEDED: sección del fichero de configuración del agente de Pandora FMS con una línea module_plugin que invoca pandora-plugin_exec con la ruta de una plantilla. -->

**Desde `cron` o el servidor** (`tentacle` o `local`). La línea de crontab *es* la planificación:

```cron
*/5 * * * * pandora-plugin_exec -t /etc/pandora/templates/myapp.yml
```

En modo `tentacle` el documento se envía a la dirección de servidor de la plantilla. En modo `local` el documento se escribe en `transfer.local.directory`; apuntar ese directorio al directorio de entrada de Pandora FMS (`/var/spool/pandora/data_in` por defecto) en el servidor hace que la ejecución sea autosuficiente.

### Pasar parámetros a una ejecución

Los tokens que quedan después de los flags alimentan dos variables reservadas, sembradas antes de que se ejecute ninguna tarea:

- `args` — lista ordenada de tokens posicionales: `{{ args[0] }}`, `{{ len(args) }}`, `for_each: args`.
- `params` — mapa de tokens con nombre: `{{ params.host }}`, `{{ params.threshold + 5 }}`.

Cada token se divide por el **primer `=` sin escapar**, y se convierte en parámetro con nombre solo cuando la clave resultante coincide con `[A-Za-z_][A-Za-z0-9_]*`. Cualquier otro token es posicional. Los valores con aspecto numérico se convierten en números, así que la aritmética funciona con ellos, y una clave repetida conserva el último valor.

| Token | Se convierte en |
|-------|-----------------|
| `sda1` | `args[0]` = `"sda1"` |
| `90` | `args[0]` = `90` (número) |
| `host=db01` | `params.host` = `"db01"` |
| `conn=user=a;pw=b` | `params.conn` = `"user=a;pw=b"` (solo divide el primer `=`) |
| `'query\=a=b'` | posicional `"query=a=b"` (la clave contendría `=` y no es un identificador) |
| `k=1 k=2` | `params.k` = `2` (gana el último) |

Dos reglas deciden si una ejecución funciona:

- **Los flags van antes de los argumentos.** El parseo de flags se detiene en el primer token que no es un flag, y un argumento que empieza por `-` se rechaza con un error en lugar de aceptarse en silencio como posicional.
- **Bash consume el escapado.** Para pasar un `=` literal que no debe dividir, entrecomille el token para que la barra invertida sobreviva: `'query\=a=b'`, o duplíquela: `query\\=a=b`.

Referenciar una variable no definida no renderiza una cadena vacía: el módulo afectado se omite, y el aviso llega a la salida de error solo con `-v`. Un parámetro es opcional solo cuando la plantilla lo dice de forma explícita. Los tres patrones documentados son:

| Patrón | Efecto |
|--------|--------|
| `{{ params.missing ?? "default" }}` | Renderiza un valor por defecto cuando falta la clave |
| `when: "'k' in params"` | Incluye el módulo solo cuando se pasó la clave |
| `{{ len(args) > 1 ? args[1] : "all" }}` | Protege un acceso posicional según el tamaño |

Las variables de tarea no pueden llamarse `args` ni `params`; `for_each: args` sí es válido.

### Escribir una plantilla

Una plantilla es un fichero YAML con tres secciones: `tasks`, `agents` (o `modules` de nivel superior) y `transfer`. El parseo es **estricto**: un nombre de campo desconocido es un error, así que una errata detiene la ejecución con código de salida 1 en lugar de ignorarse.

- **`tasks`** se ejecutan en el orden declarado. Cada una tiene un `name` único, un `type` (`request` o `local`), el bloque correspondiente, un `filter` opcional y una `variable` opcional que almacena el resultado filtrado. Sin `variable` la tarea se ejecuta igualmente y su salida se descarta. Una tarea solo usa variables producidas por tareas declaradas antes.
- **Una tarea `request`** necesita `url` y admite `method` (`GET` por defecto), `headers`, `body`, `timeout` (segundos, `30` por defecto) y `skip_tls_verify` (`false` por defecto). Un estado fuera de 2xx es un fallo de tarea.
- **Una tarea `local`** necesita `command`, que se ejecuta mediante `/bin/sh -c`, y admite `timeout` (segundos, `30` por defecto). Un código de salida distinto de cero es un fallo de tarea. El `$` de shell no se toca, así que `awk '{print $5}'` funciona tal cual; solo se sustituye `{{ }}`.
- **Un `filter`** declara `type: jq` o `type: regexp` y una `expression`. Sin filtro, el valor es la salida bruta recortada de la tarea.
- **`agents`** contiene un bloque por agente con sus `modules`; los **`modules` de nivel superior** son la alternativa, válida solo con `transfer.mode: agent_plugin`. Ambas formas son mutuamente excluyentes.
- **`transfer`** declara el modo y sus opciones.

Las tablas completas de campos están en [Referencia](#referencia). El resto de la página usa este ejemplo más largo, que convierte un resultado regexp en dos módulos por elemento:

```yaml
tasks:
  - name: df
    type: local
    local:
      command: "df -kTP"
    filter:
      type: regexp
      expression: '(?m)^(?P<fs>\S+)\s+(?P<fstype>\S+)\s+(?P<total>\d+)\s+(?P<used>\d+)\s+\d+\s+(?P<pct>\d+)%\s+(?P<mount>.+)$'
    variable: filesystems

modules:
  - for_each: filesystems
    when: 'value.fstype != "tmpfs"'
    name: "DiskUsed_{{ value.mount }}"
    type: generic_data
    data: "{{ value.pct }}"
    unit: "%"

  - for_each: filesystems
    when: 'value.fstype != "tmpfs"'
    name: "DiskUsed_{{ value.mount }} bytes"
    type: generic_data
    data: "{{ value.used }}"
    unit: "KB"

transfer:
  mode: agent_plugin
```

## Verificación

Valide una plantilla sin entregar nada. Para los modos `tentacle` y `local`, `--dry-run` imprime el documento de agente en la salida estándar y no lo transfiere ni lo escribe:

```bash
pandora-plugin_exec -t <PATH_TO_CONFIG> --dry-run
```

Añada `-v` para ver, en la salida de error, qué variables se almacenaron y qué módulos se omitieron:

```bash
pandora-plugin_exec -t <PATH_TO_CONFIG> --dry-run -v
```

Una ejecución correcta termina con estado `0`. Compruébelo de forma explícita cuando lo use en un script:

```bash
pandora-plugin_exec -t <PATH_TO_CONFIG> --dry-run; echo "exit=$?"
```

En los modos `tentacle` y `local` el documento empieza con una declaración XML y un elemento `agent_data` cuyos atributos son los campos de agente de la plantilla:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<agent_data agent_name="myapp" timestamp="2026/10/27 08:00:00" group="Applications" interval="300" agent_mode="1">
  <module>
    <name><![CDATA[Active users]]></name>
    <type>generic_data</type>
    <data><![CDATA[42]]></data>
  </module>
</agent_data>
```

En modo `agent_plugin` no hay nada que simular: el ejecutor solo imprime fragmentos de módulo, así que una ejecución normal ya es la verificación. `--dry-run` no cambia nada en este modo.

```bash
pandora-plugin_exec -t /etc/pandora/templates/disk_load.yml
```

```xml
<module>
  <name><![CDATA[Root disk used]]></name>
  <type>generic_data</type>
  <data><![CDATA[81]]></data>
  <unit><![CDATA[%]]></unit>
  <min_warning><![CDATA[80]]></min_warning>
  <min_critical><![CDATA[90]]></min_critical>
</module>
```

Como comprobación final, entregue de verdad y mire el resultado en Pandora FMS: en modo `agent_plugin` los módulos aparecen bajo el agente que ejecuta el plugin, y en modo `tentacle` o `local` el agente nombrado en la plantilla aparece con sus módulos tras la siguiente ingesta de datos.

<!-- SCREENSHOT NEEDED: vista de detalle de un agente de Pandora FMS con la lista de módulos generados por pandora-plugin_exec a partir de una plantilla. -->

## Entender los resultados

### Variables y valores de módulo

Cada tarea con `variable` almacena exactamente un valor, y su forma depende del filtro:

| Resultado del filtro | Valor almacenado |
|----------------------|------------------|
| 0 coincidencias | Nada: la variable queda sin definir y la tarea se trata como fallida |
| 1 coincidencia | Un escalar |
| N coincidencias | Un array, con un elemento por coincidencia |

Una tarea sin filtro produce siempre un elemento: la salida recortada.

Toda cadena capturada con aspecto numérico se convierte en número, de forma recursiva dentro de objetos y arrays. Los valores de módulo se renderizan después desde números, lo que mantiene la aritmética pero pierde el texto original:

- un `1.0` capturado se publica como `1`, y `007` como `7`;
- una versión capturada como `2.30` se publica como `2.3`;
- un contador más largo que la precisión de un número en coma flotante pierde sus últimos dígitos.

Cuando un valor deba conservar su texto exacto, haga que no sea numérico a propósito (por ejemplo con un prefijo en la captura de la expresión regular) o publíquelo como `generic_data_string`.

Una expresión `jq` que emite `null` cuenta como una coincidencia, y la referencia a ese valor queda sin definir, así que el módulo se omite como cualquier otra referencia sin resolver. Donde el módulo deba publicar de todas formas, dé el valor por defecto dentro de la expresión, como en `{{ value ?? "n/a" }}`.

### Expansión de módulos y condiciones

`for_each` nombra una variable array y expande el bloque en **un módulo por elemento**. Dentro del bloque, `{{ value }}` es el elemento actual y `{{ index }}` su posición base 0, que es lo que permite el acceso sincronizado a dos arrays paralelos. Escribir varios bloques con el mismo `for_each` es la forma de que un elemento produzca varios módulos.

- Una variable escalar itera como un array de un elemento.
- Una variable `for_each` sin definir omite el bloque completo; el aviso se escribe solo con `-v`.
- Los filtros regexp con grupos de captura con nombre hacen que cada elemento sea un **objeto**, así que los campos se leen como `{{ value.mount }}`; dos o más grupos sin nombre hacen que cada elemento sea un **array posicional**, que se lee como `{{ value[0] }}`.

`when` contiene una expresión booleana sin `{{ }}`. Se evalúa por elemento dentro de un bloque `for_each` y contra todo el almacén de variables fuera de él. Una condición falsa omite ese elemento sin error; una condición que no se puede evaluar, o que no devuelve un booleano, se reporta y el módulo se omite.

El ejecutor no deduplica nombres de módulo. Dos elementos que renderizan el mismo nombre producen dos módulos con ese nombre en el mismo documento, así que haga el nombre único con el propio elemento, como hace el ejemplo anterior con `{{ value.mount }}`.

### Qué llega a Pandora FMS

En los modos `tentacle` y `local` el ejecutor construye **un documento `<agent_data>` por cada agente de la plantilla**. Los atributos del agente salen de la plantilla: `agent_name`, `agent_alias`, `parent_agent_name`, `description`, `version`, `os_name`, `os_version`, `timestamp`, `address`, `group`, `interval` y `agent_mode`. Cuando se omite `timestamp` se usa la hora de la ejecución, y cuando se omite `interval` el documento lleva `300`.

Cada módulo se convierte en un elemento `<module>` con `<name>`, `<type>` y `<data>`; `description`, `unit`, los umbrales y el resto de campos admitidos se añaden cuando la plantilla los define. Un módulo cuyo campo `data` está vacío o ausente publica el valor `0`.

En modo `agent_plugin` no se emite nada de esa cabecera: solo se imprimen los elementos `<module>`, concatenados, sin declaración XML y sin elemento raíz. Por tanto, los campos de agente de la plantilla —`group`, `interval`, `alias`, `description`, `os_*`, `address`— **no se aplican**, porque el agente real aporta su propia identidad e intervalo. Cuando la plantilla declara más de un agente, cada nombre de módulo se prefija con `<nombre de agente>` + `transfer.module_prefix_separator` (` - ` por defecto) para que los módulos no colisionen bajo ese único agente.

Un módulo cuyo valor no se puede resolver **no aparece** en el documento. Pandora FMS no recibe datos suyos en esa ejecución: el ejecutor no envía un estado desconocido explícito, así que el módulo simplemente deja de recibir valores. Ese es el comportamiento que debe esperar cuando una tarea falla, un filtro no coincide con nada o una condición es falsa.

## Operación y resolución de problemas

### Operación diaria

- **One-shot y sin estado.** Cada ejecución lee su plantilla, la ejecuta y termina. No se guarda nada en caché, así que una ejecución manual en cualquier momento equivale a una planificada.
- **Registro.** Los errores se escriben siempre en la salida de error con el prefijo `pandora-plugin_exec:` y una marca de tiempo. `-v` añade ahí el flujo de depuración —variables almacenadas, omisiones y resultados de entrega— y deja la salida estándar limpia para el XML. No hay fichero de log ni niveles de log.
- **Nombres de fichero en modo `local`.** El documento se escribe como `<md5 del nombre de agente>.<segundos epoch>.data` dentro de `transfer.local.directory`, que se crea con modo `0755` si no existe. Dos ejecuciones del mismo agente dentro del mismo segundo esperan al segundo siguiente antes de escribir, así que un bucle rápido no sobrescribe datos.
- **Preparación en modo `tentacle`.** El documento se escribe en un directorio temporal bajo el directorio temporal del sistema, se envía con el cliente Tentacle y se elimina al terminar la ejecución.
- **Las plantillas son contenido ejecutable.** Una plantilla decide qué comandos se ejecutan en el host. Mantenga los ficheros de plantilla escribibles solo por el usuario que ejecuta el ejecutor y trate una plantilla recibida de otra persona como código que está a punto de ejecutar.
- **Credenciales.** No hay almacén de secretos: una credencial se escribe en la plantilla, se pasa como parámetro en tiempo de ejecución o la lee el propio comando. Una credencial pasada como parámetro es visible en la lista de procesos y en el historial de shell de quien la escribió, así que mantenga las plantillas en modo `0600` y prefiera el patrón de comando que lee la credencial cuando el destino lo admita.

### Límites

- Solo dos tipos de tarea: peticiones HTTP y comandos locales. No hay tareas SNMP ni de base de datos, y la plantilla no tiene ejecución condicional de tareas.
- Sin planificación y sin modo demonio: la ejecución ocurre cuando la arranca el agente, `cron` o una persona.
- Las tareas son secuenciales. Una petición lenta retrasa todas las tareas posteriores de la misma ejecución, y la ejecución no tiene tiempo máximo global: solo el de cada tarea.
- Las respuestas HTTP se leen hasta 10 MiB. Un cuerpo mayor se trunca en silencio, y el truncado suele aparecer más tarde como error de parseo JSON en el filtro.
- El tiempo máximo de una tarea `local` termina el proceso `/bin/sh` que ejecuta el comando; un comando que arranca sus propios procesos hijos es responsable de detenerlos.
- Sin reintentos. Una tarea fallida deja su variable sin definir, y solo `--strict` convierte eso en un código de salida distinto de cero; sin él, el motivo solo se ve con `-v`.
- La entrega `webhook`, la planificación por plantilla y tipos de tarea adicionales están anunciados como no disponibles todavía en la documentación del propio addon.

### Resolución de problemas

- **`error: argument "--dry-run" looks like a flag; flags must come before the arguments`** — los flags se escribieron después de un token posicional. Mueva todos los flags antes de los argumentos.
- **Código de salida 1 con `invalid template: ...`** — la plantilla no se pudo parsear. El mensaje nombra el campo o la línea culpable: un campo desconocido, un nombre de tarea duplicado, un `type` que no coincide con su bloque, un tipo de filtro inválido, un nombre de variable inválido, `agents` junto con `modules` de nivel superior, `modules` de nivel superior sin modo `agent_plugin`, un `tentacle.address` ausente o un `transfer.mode` ausente.
- **Código de salida 1 con `a template is required`** — no se pasó `-t`, o un flag anterior consumió su valor.
- **Código de salida 2** — una tarea falló bajo `--strict`. Vuelva a ejecutar con `-v` para ver qué tarea y por qué.
- **Un módulo falta en la consola** — su valor nunca se resolvió. Ejecute con `-v` y busque `left unset`, `skipped` o `filter matched nothing`; las causas habituales son una tarea que falló, un filtro que no coincidió con nada y un parámetro que no se pasó.
- **Un módulo publica `0`** — la plantilla no define `data`, o el valor capturado era la cadena vacía.
- **Un número llega sin dígitos o sin sus decimales** — coerción numérica (consulte [Variables y valores de módulo](#variables-y-valores-de-modulo)). Publique el valor como texto cuando su forma exacta importe.
- **Código de salida 3 con `tentacle send failed`** — el cliente Tentacle no pudo entregar. Compruebe que `tentacle_client` está en `PATH` o defina `transfer.tentacle.binary`, la dirección y el puerto de la plantilla, y el acceso de red al servidor. Con varios agentes, los agentes ya enviados en esa ejecución se entregan y los restantes no.
- **El modo `local` escribe ficheros pero no aparece ningún agente** — los documentos se escribieron en un directorio que el servidor no ingiere. Confirme `transfer.local.directory` carácter a carácter: una ruta equivocada se crea en silencio en lugar de reportarse.
- **`task output is not valid JSON`** — el filtro `jq` recibió algo que no es JSON: una página de error HTML, un cuerpo vacío, un cuerpo truncado por encima de 10 MiB o un comando `local` que imprimió un aviso antes del JSON.
- **`unexpected status 401` / `403` / `500`** — la petición falló. El mensaje lleva el estado y los primeros 200 caracteres del cuerpo de la respuesta, que normalmente bastan para distinguir un problema de autenticación de un error del servidor.
- **Una petición falla por certificado** — el destino presenta un certificado en el que el host no confía. `skip_tls_verify: true` acepta certificados inválidos en esa tarea y desactiva la protección, así que úselo solo con un destino que controle.
- **Un comando `local` se cuelga hasta el tiempo máximo** — el tiempo máximo de la tarea expiró y el shell se terminó. Suba `timeout` en esa tarea si el comando necesita legítimamente más tiempo, y compruebe si el proceso hijo que quedó atrás sigue reteniendo un bloqueo o un puerto.
- **`when` se ignora o el módulo nunca aparece** — `when` es una expresión en bruto, así que rodearla con `{{ }}` es un error; dentro de un bloque `for_each` ve `value` e `index`, no la variable array.

## Referencia

### Flags de línea de comandos

```text
pandora-plugin_exec -t <plantilla.yml> [flags] [args...] [clave=valor...]
```

| Flag | Efecto |
|------|--------|
| `-t`, `--template <ruta>` | Plantilla a ejecutar. Obligatorio |
| `--dry-run` | Imprime el documento generado en la salida estándar y no lo transfiere ni lo escribe. No tiene efecto en modo `agent_plugin`, que siempre imprime |
| `--strict` | Aborta en el primer fallo de tarea o módulo sin resolver, en lugar de omitirlo |
| `-v`, `--verbose` | Registro de depuración en la salida de error: resultados de tareas, omisiones, avisos, entrega |
| `--version` | Imprime la versión y termina |

Los flags deben preceder a los argumentos, y un argumento que empieza por `-` se rechaza con código de salida 1.

### Códigos de salida

| Código | Significado |
|--------|-------------|
| `0` | Éxito |
| `1` | Error de parseo o validación de la plantilla, y errores de uso como la ausencia de `-t` |
| `2` | Fallo de tarea bajo `--strict`, y cualquier error al construir un documento de agente |
| `3` | Error de transferencia: falló el envío con Tentacle o la escritura local |

Sin `--strict`, una tarea fallida o un módulo sin resolver no cambian el código de salida: la ejecución entrega los módulos que sí se resolvieron y termina con `0`, y el motivo se escribe en la salida de error solo con `-v`.

### Clasificación de parámetros en tiempo de ejecución

| Token | Clave | Valor | Se almacena como |
|-------|-------|-------|------------------|
| `sda1` | — | `sda1` | `args[0]` |
| `90` | — | `90` | `args[0]`, número |
| `host=db01` | `host` | `db01` | `params.host` |
| `threshold=90` | `threshold` | `90` | `params.threshold`, número |
| `conn=user=a;pw=b` | `conn` | `user=a;pw=b` | `params.conn` |
| `'query\=a=b'` | — | `query=a=b` | posicional, porque la clave no es un identificador |
| `=foo` | — | `=foo` | posicional, porque la clave está vacía |
| `k=1 k=2` | `k` | `2` | `params.k`, gana el último valor |

`args` es siempre una lista, incluso vacía, así que `for_each: args` y `len(args)` son seguros. `params` es siempre un mapa. Ambos están reservados: una `variable` de tarea no puede usar esos nombres.

### Plantilla: tareas

| Campo | Obligatorio | Descripción |
|-------|-------------|-------------|
| `name` | Sí | Identificador único de tarea, usado en las líneas de log |
| `type` | Sí | `request` o `local`, y debe coincidir con el bloque presente |
| `request` | Cuando `type: request` | Especificación de petición HTTP |
| `local` | Cuando `type: local` | Especificación de comando |
| `filter` | No | Filtro de extracción. Sin él, el valor es la salida bruta recortada |
| `variable` | No | Nombre que almacena el resultado, con la forma `[A-Za-z_][A-Za-z0-9_]*`. Sin él, la salida se descarta |

Las tareas admiten `{{ }}` en sus campos de cadena: URL, cuerpo, valores de cabecera y comando. El `name` de la tarea, su `variable` y `filter.expression` no se renderizan.

#### `request`

| Campo | Obligatorio | Por defecto | Descripción |
|-------|-------------|-------------|-------------|
| `url` | Sí | — | URL de destino. Admite `{{ }}` |
| `method` | No | `GET` | `GET`, `POST`, `PUT`, `DELETE`, `PATCH` o `HEAD`. No se renderiza |
| `headers` | No | — | Cabecera a valor. Los valores admiten `{{ }}` |
| `body` | No | — | Cuerpo de la petición. Admite `{{ }}` |
| `timeout` | No | `30` | Segundos, aplicados a la petición completa |
| `skip_tls_verify` | No | `false` | Acepta certificados TLS inválidos |

Un estado fuera de 2xx falla la tarea, y el error lleva el estado y los primeros 200 caracteres del cuerpo. El cuerpo de la respuesta se lee hasta 10 MiB.

#### `local`

| Campo | Obligatorio | Por defecto | Descripción |
|-------|-------------|-------------|-------------|
| `command` | Sí | — | Se ejecuta con `/bin/sh -c`. Admite `{{ }}`; el `$` de shell no se toca |
| `timeout` | No | `30` | Segundos; el proceso shell se termina al expirar |

Un código de salida distinto de cero falla la tarea, y el error lleva los primeros 200 caracteres de la salida de error.

### Plantilla: filtros

| Campo | Obligatorio | Descripción |
|-------|-------------|-------------|
| `type` | Sí | `jq` o `regexp` |
| `expression` | Sí | La expresión del filtro. No se renderiza |

**`jq`** — la salida de la tarea debe ser JSON válido, y la expresión se ejecuta en un motor incorporado, así que no hace falta el ejecutable `jq`. Cada valor que emite la expresión es un elemento: `.token` da un escalar, `.items[].name` un array de cadenas, `.items[]` un array de objetos y `.` el documento completo como un objeto.

**`regexp`** — sintaxis RE2, aplicada a la salida bruta: sin backtracking y sin lookahead, mientras que `(?m)` y `(?i)` están disponibles. La forma de cada coincidencia depende de sus grupos de captura:

| Forma del patrón | Cada coincidencia se convierte en |
|------------------|-----------------------------------|
| Sin grupo de captura (`cpu\d`) | La coincidencia completa, como cadena |
| Un grupo sin nombre (`(\d+)%`) | El grupo de captura 1, como cadena |
| Dos o más grupos sin nombre (`(a)(b)(c)`) | Un array posicional: `[[a, b, c], ...]` |
| Grupos con nombre (`(?P<mount>...)`) | Un objeto: nombre del grupo a texto capturado |

Los grupos con nombre y sin nombre en la misma expresión regular no son una combinación admitida para un acceso predecible: en cuanto un grupo tiene nombre, cada coincidencia se convierte en un objeto construido solo con los grupos con nombre.

La cardinalidad es la misma para ambos tipos: 0 coincidencias dejan la variable sin definir, 1 coincidencia almacena un escalar y N coincidencias almacenan un array.

### Plantilla: agentes

Obligatorio salvo que la plantilla use `modules` de nivel superior.

| Campo | Obligatorio | Descripción |
|-------|-------------|-------------|
| `name` | Sí | Nombre del agente |
| `modules` | Sí | Al menos un bloque de módulo |
| `alias` | No | Alias del agente |
| `parent_agent_name` | No | Agente padre |
| `description` | No | Descripción |
| `version` | No | Cadena de versión del agente |
| `os_name`, `os_version` | No | Identificación del sistema operativo |
| `timestamp` | No | Sobrescribe la marca de tiempo del documento. Por defecto, la hora de la ejecución |
| `address` | No | Dirección IP o nombre de host |
| `group` | No | Grupo de destino |
| `interval` | No | Segundos. El documento lleva `300` cuando se omite |
| `agent_mode` | No | Modo del agente. El documento lleva `1` cuando se omite |

Todos los campos de cadena admiten `{{ }}`. Estos campos solo se usan en modo `tentacle` y `local`.

### Plantilla: módulos

#### Campos de control

Son semántica del ejecutor y no se envían a Pandora FMS.

| Campo | Descripción |
|-------|-------------|
| `for_each` | Nombre de una variable array. El bloque se expande a un módulo por elemento, con `{{ value }}` y `{{ index }}` disponibles. Una variable escalar itera como un elemento, y un elemento con grupos con nombre se lee como `{{ value.field }}` mientras que uno posicional se lee como `{{ value[0] }}` |
| `when` | Expresión booleana en bruto, sin `{{ }}`. Falso omite el módulo, o ese elemento dentro de un bloque `for_each` |

#### Campos de datos

`name` y `type` son obligatorios; el resto son opcionales. Los valores pueden ser números o cadenas en YAML, y todos admiten `{{ }}`. El ejecutor pasa cada campo al documento de datos; solo `interval` cambia de nombre, a `module_interval`.

| Campo | Descripción |
|-------|-------------|
| `name` | Nombre del módulo |
| `type` | Tipo de módulo: `generic_data`, `generic_proc`, `generic_data_string`, `generic_data_inc`, `async_data`, ... |
| `data` | Valor del módulo. Un `data` vacío o ausente publica `0` |
| `description` | Descripción |
| `unit` | Etiqueta de unidad |
| `interval` | Intervalo del módulo, enviado como `module_interval` |
| `tags` | Etiquetas |
| `module_group` | Grupo de módulo |
| `module_parent`, `module_parent_unlink` | Relación de módulo padre |
| `min_warning`, `max_warning`, `min_critical`, `max_critical` | Umbrales numéricos |
| `min_warning_forced`, `max_warning_forced`, `min_critical_forced`, `max_critical_forced` | Variantes de umbral forzado |
| `str_warning`, `str_critical` | Umbrales por coincidencia de cadena |
| `str_warning_forced`, `str_critical_forced` | Umbrales de cadena forzados |
| `warning_inverse`, `critical_inverse` | Invertir la lógica del umbral |
| `min`, `max` | Rango de datos válido |
| `post_process` | Multiplicador aplicado por el servidor |
| `disabled` | Crear el módulo deshabilitado |
| `status` | Forzar el estado del módulo |
| `timestamp` | Sobrescribe la marca de tiempo de los datos |
| `custom_id` | Identificador personalizado |
| `critical_instructions`, `warning_instructions`, `unknown_instructions` | Instrucciones del operador |
| `quiet` | Modo silencioso |
| `min_ff_event`, `min_ff_event_normal`, `min_ff_event_warning`, `min_ff_event_critical` | Umbrales FlipFlop |
| `module_ff_interval`, `ff_type`, `ff_timeout`, `each_ff` | Comportamiento FlipFlop |
| `crontab` | Planificación del módulo estilo cron |
| `extra_data` | Carga adicional |
| `alert_templates` | Lista de nombres de plantilla de alerta a vincular |

### Plantilla: transferencia

| Campo | Obligatorio | Descripción |
|-------|-------------|-------------|
| `mode` | Sí | `tentacle`, `local` o `agent_plugin` |
| `tentacle.address` | Para `tentacle` | Dirección del servidor de Pandora FMS |
| `tentacle.port` | No | Puerto Tentacle, `41121` por defecto |
| `tentacle.binary` | No | Ruta al cliente Tentacle cuando no está en `PATH` |
| `tentacle.extra_args` | No | Argumentos extra del cliente Tentacle, como lista |
| `local.directory` | Para `local` | Directorio donde se escribe el documento `.data` |
| `module_prefix_separator` | No | Separador del prefijo multiagente en modo `agent_plugin`, `" - "` por defecto |

| Modo | Salida | Caso de uso |
|------|--------|-------------|
| `tentacle` | Documento `<agent_data>` completo enviado con el cliente Tentacle | Ejecución remota desde `cron` o el servidor |
| `local` | Documento `<agent_data>` completo escrito como fichero `.data` | Ejecución en el propio servidor de Pandora FMS |
| `agent_plugin` | Fragmentos `<module>` en la salida estándar | Ejecución como `module_plugin` de un agente software |

### Lenguaje de expresiones

Los placeholders `{{ }}` y las condiciones `when` son expresiones con la sintaxis documentada en [expr-lang.org](https://expr-lang.org/docs/language-definition). Funciones útiles para autores de plantillas:

| Categoría | Funciones y operadores |
|-----------|------------------------|
| Cadenas | `split(s, sep)` · `join(list, sep)` · `upper(s)` · `lower(s)` · `trim(s)` · `replace(s, old, new)` · `contains(s, sub)` · `startsWith(s, pre)` · `endsWith(s, suf)` · `s matches "patrón-re2"` |
| Colecciones | `x in list` · `len(list)` · `list[i]` · `first(list)` · `last(list)` · `filter(list, pred)` · `map(list, expr)` · `all`/`any`/`none(list, pred)` · `sort(list)` · `uniq(list)` · `concat(a, b)` |
| Lógica y nil | `a ?? "default"` · `obj?.field` · `cond ? a : b` · `'clave' in map` |
| Números | `+ - * / %` · `abs(x)` · `min`/`max(a, b)` · `sum(list)` · `avg(list)` · `int(x)` · `float(x)` · `string(x)` |
| JSON | `toJSON(x)` · `fromJSON(s)` |

Dentro de los predicados de `filter`, `map`, `all`, `any` y `none` el elemento actual es `#`, como en `filter(filesystems, #.pct > 90)`.

El lenguaje de expresiones se usa solo en `{{ }}` y en `when`. El `filter.expression` de una tarea es `jq` o una expresión regular RE2, nunca una expresión de este lenguaje. En las expresiones regulares escritas dentro de `when`, duplique la barra invertida (`\\d`), porque los literales de cadena de las expresiones procesan escapes y el motor debe recibir un `\d` literal.

### Plantillas incluidas

| Plantilla | Propósito |
|-----------|-----------|
| `templates/df_used.yml` | Uso de sistemas de archivos: un módulo de porcentaje y otro de tamaño por sistema de archivos. Sustituye a `pandora_df_used_go`, con umbrales 90 y 95 en el módulo de porcentaje |
| `templates/pandora_mem_used.yml` | Uso de memoria y swap en porcentaje y en bytes. Sustituye a `pandora_mem_used` |
| `templates/pandora_netusage.yml` | Total de bytes recibidos y transmitidos de `/proc/net/dev`, publicado como módulo incremental. Sustituye a `pandora_netusage` |
| `templates/http_api_example.yml` | Cadena de autenticación por token contra una API JSON: inicio de sesión → token → dos peticiones autenticadas |
| `templates/local_commands_example.yml` | Comandos locales como plugin de agente, con las tres formas de resultado de regexp |

Los tres sustitutos terminan en `transfer.mode: agent_plugin` y esperan la invocación que indica su propio comentario de cabecera, con la plantilla en `/etc/pandora/templates/`.

Copie estas plantillas del paquete si incluye un directorio `templates/`: el ejecutor no instala ninguna plantilla ni lee una que no se le pase con `-t`.

| Plantilla | Parámetro | Por defecto | Efecto |
|-----------|-----------|-------------|--------|
| `df_used.yml` | `include` | — | Fuerza la monitorización de un montaje cuyo `fstype` está fuera de la lista por defecto. Coincidencias exactas de montaje, separadas por comas |
| `df_used.yml` | `exclude` | — | Nunca monitoriza un montaje. Coincidencias exactas de montaje, separadas por comas. Exclude gana sobre include |
| `pandora_netusage.yml` | `include` | — | Monitoriza solo estas interfaces. Nombres exactos, separados por comas |
| `pandora_netusage.yml` | `exclude` | — | Nunca monitoriza una interfaz. Nombres exactos, separados por comas. Exclude gana sobre include |
| `pandora_mem_used.yml` | `mem_critical` | `95` | Umbral crítico del módulo de porcentaje `Memory_Used` |
| `pandora_mem_used.yml` | `swap_critical` | `95` | Umbral crítico del módulo de porcentaje `Swap_Used` |

Los dos módulos de bytes de `pandora_mem_used.yml` calculan su umbral crítico dentro del comando, al 95 % del total correspondiente, e ignoran esos parámetros.

El módulo de tamaño de `df_used.yml` publica la columna `Used` de `df -kTP`, que `df` expresa en bloques de 1K, mientras que la plantilla declara `unit: "bytes"`. Un sistema de archivos cuya columna muestre `1000000` se publica como `1000000 bytes`, un valor 1024 veces menor que el uso real. Si depende de ese módulo, convierta el valor en la plantilla o corrija la unidad.

### Identidad del addon

| Campo | Valor |
|-------|-------|
| Identificador del Marketplace | `Pandora-Plugin-Executor` |
| Nombre en el Marketplace | Pandora Plugin Executor |
| Versión del addon | `1.0` |
| Última actualización en el Marketplace | 2026-08-19 |
| Paquete del Marketplace | `Pandora-Plugin-Executor.1.0.zip` |
| Licencia | Descarga gratuita |
| Tipo en el Marketplace | Miscelaneus |
| Descargas | 4 |
| Ejecutable | `pandora-plugin_exec` |
| Versión impresa por `--version` | `0.1.0` |
| Flujo de trabajo | Ejecutor autónomo guiado por plantillas YAML, con tres modos de entrega |
