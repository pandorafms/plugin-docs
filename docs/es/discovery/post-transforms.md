# Post-transforms

*Última actualización del artículo: 2026-11-23.*

## Qué son

Los post-transforms permiten que el **operador de la tarea** enriquezca los
módulos que crea una tarea de Discovery — umbrales, umbrales de cadena,
tags, grupo de módulo, plantillas de alerta y configuración flip-flop —
mediante reglas con expresiones regulares escritas como bloques de texto
plano en el formulario de la tarea. Sin tocar el código del plugin: las
reglas viajan con la tarea y el plugin las aplica en cada ejecución, sobre
la estructura completa recolectada, justo antes de enviar los datos. Una
regla errónea se salta y se reporta en lugar de detener la monitorización.

Las reglas se aplican antes de la serialización, por lo que las mismas
reglas sirven para una tarea con transferencia `native` (JSON de Discovery)
y para una con `tentacle` (XML de agente).

Cada plugin lo incorpora exponiendo el campo **Post transforms** en el
asistente. NGINX es el primer plugin que lo implementa.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
|--------|--------|-----------|
| `pandora-plugintools-basic` `1.2.0` (motor Python) | `Probado` | Parser de bloques, whitelist tipada, ambos caminos de salida y el comportamiento de error con continuación, ejercidos end-to-end contra un stack de Pandora FMS. Pendiente de publicación en PyPI; la verificación se realizó contra el checkout de desarrollo 1.2.0 |
| `pandoraplugintools-go` (motor Go) | `Probado` | Contrastado contra el motor Python mediante el harness de paridad compartido (15/15 escenarios, incluido un fichero de reglas parcialmente inválido) |
| Plugin que expone el campo Post transforms | `Requerido` | NGINX `1.1` (pendiente de liberación) es la primera implementación |
| Patrones compatibles con RE2 | `Requerido` | El motor Go usa RE2: las reglas deben evitar backreferences y lookaround para comportarse igual en ambos motores |

### Requisitos previos en la consola

1. **Los grupos de módulo deben existir.** `set_module_group` resuelve el
   grupo por nombre en la ingesta: un grupo que no existe en la gestión de
   grupos de módulo no se aplica. Verificado contra un stack real.
2. **Los tags deben existir antes de la ejecución.** `set_tags` transporta
   una lista de nombres de tag separados por comas; los tags del módulo se
   relacionan en la creación del módulo solo cuando cada tag existe ya en
   la gestión de tags. Verificado: una ejecución con tags inexistentes no
   creó relaciones de tag; tras crear los tags y reejecutar, ambos tags se
   relacionaron.
3. **Plantillas de alerta:** `set_alert_template` referencia una plantilla
   por nombre; la resolución del nombre de la plantilla en el servidor no
   está aún validada.

## Configurar la tarea de Discovery

Cada plugin compatible expone un textarea **Post transforms** en el paso
avanzado del asistente. Escribe una regla por bloque; los bloques se
aplican en orden.

`SCREENSHOT NEEDED`: campo Post transforms en el asistente de la tarea de
Discovery.

Ejemplo — avisar cuando las conexiones activas pasan de cien, sin límite
superior:

```text
transform_begin
transform_name       active connections thresholds
match_module         .*Active_connections.*
set_min_warning      100
set_max_critical     0
set_module_group     Application
set_tags             infra:nginx,team:web
transform_end
```

Semántica:

- `match_module` (nombre del módulo) y `match_extra_data` (la clave
  semántica estable del plugin) son expresiones regulares con matching por
  subcadena; ancla con `^...$` para exigir coincidencia completa. Dentro de
  un bloque se combinan en AND, y una regla necesita al menos una.
- Las reglas se aplican en orden; por cada campo gana la última regla que
  matchea. Un bloque que asigna el grupo del módulo no impide que otro
  posterior añada umbrales.
- `name`, `type`, `data`, `value`, `extra_data`, `timestamp` y `status`
  están protegidos: ninguna regla reescribe la identidad del módulo ni el
  valor recolectado.
- Los rangos de umbrales son half-open `[min, max)`: el propio valor max
  pertenece al siguiente tramo. `max_warning=0` / `max_critical=0`
  significan "sin límite superior", no el cero literal.
- `set_tags` transporta una lista separada por comas en una sola cadena —
  la misma convención que `module_tags` del agente.

## Verificar

1. Ejecuta la tarea con la regla del ejemplo anterior (ajustada a los
   nombres de módulo del plugin).
2. Abre el módulo creado: los umbrales, el grupo y los tags de la regla
   que matchea están aplicados; los módulos que la regla no matchea quedan
   intactos.
3. Introduce un typo en una regla (`set_min_warnig`) y vuelve a ejecutar.
   La tarea termina, se entregan todos los agentes y módulos como siempre,
   la información de la tarea reporta la regla con su bloque y línea, la
   ejecución manual imprime el mismo error por stderr y la ejecución
   termina con código distinto de cero.

## Entender los resultados

El asistente entrega el textarea como su propio fichero de reglas al
plugin. El plugin carga y valida todas las reglas una sola vez, antes de
recolectar nada. Las reglas inválidas se saltan y se reportan — nunca son
fatales: la ejecución continúa con las reglas válidas.

Las reglas válidas se aplican sobre la estructura recolectada **completa**,
cuando ya está terminada y antes de serializarse: sobre todo el payload de
monitorización en modo `native`, y sobre la lista de módulos de cada agente
justo antes de generar el XML en modo `tentacle`. Por eso un único fichero
de reglas cubre ambos modos de transferencia, y la información de todos los
módulos de la ejecución está disponible para cada regla.

## Solucionar problemas

| Síntoma | Causa | Solución |
|---------|-------|----------|
| La información de la tarea reporta `unknown set field ... (not in the whitelist); rule skipped` | Typo en una clave `set_` | Usa un nombre exacto de la [whitelist](#set-whitelist) |
| La información de la tarea reporta `invalid regex in match key ...; rule skipped` | Patrón malformado, o una construcción solo de Python (backreferences, lookaround) | Corrige el patrón; mantenlo compatible con RE2 |
| La información de la tarea reporta `rule has no match_module or match_extra_data key; rule skipped` | Una regla sin selector | Añade al menos una clave `match_*` |
| Los umbrales no aparecen en un módulo | La expresión regular no matchea el nombre de ese módulo (o su `extra_data` cuando se usan ambas claves) | Prueba el patrón contra el nombre del módulo; revisa la semántica AND |
| Umbrales numéricos en un módulo de cadena | Los umbrales numéricos pertenecen a tipos de módulo numéricos | Usa `str_warning`/`str_critical` para módulos de cadena |
| Los tags no se relacionan con el módulo | Los tags no existían en el momento de la ejecución | Crea los tags en la gestión de tags y reejecuta; comportamiento verificado |
| El grupo de módulo no se aplica | El grupo no existe | Crea el grupo en la gestión de grupos de módulo |
| `post transforms file ... does not exist` | La ruta al fichero de reglas es errónea (ejecuciones manuales) | Revisa la ruta de `--post_transforms_conf` |

## Referencia

### Gramática de bloques

| Clave | Tipo | Significado |
|-------|------|-------------|
| `transform_begin` | delimitador | Abre un bloque de regla. Obligatorio |
| `transform_end` | delimitador | Cierra un bloque de regla. Obligatorio |
| `transform_name` | texto | Etiqueta opcional para logs y mensajes de error |
| `match_module` | regex | Matchea el nombre del módulo (subcadena; ancla con `^...$`) |
| `match_extra_data` | regex | Matchea la clave semántica estable del módulo |
| `set_<campo>` | valor tipado | Escribe un campo del módulo de la whitelist |

Los comentarios (`#`) y las líneas en blanco se ignoran en todo el
fichero. Granularidad de regla: una clave errónea invalida su regla
completa, porque aplicar la mitad de una configuración pretendida es peor
que saltarla.

### Whitelist de `set_`

<a id="set-whitelist"></a>

Exactamente los campos de módulo que la ingesta de Discovery ya acepta.
Los campos desconocidos se rechazan indicando el bloque y la clave que lo
provocaron.

Umbrales (numéricos):

| Campo | Significado |
|-------|-------------|
| `set_min_warning` / `set_max_warning` | Rango de aviso, half-open `[min, max)` |
| `set_min_critical` / `set_max_critical` | Rango crítico, half-open `[min, max)` |
| `set_min_warning_forced` / `set_max_warning_forced` | Rango de aviso forzado |
| `set_min_critical_forced` / `set_max_critical_forced` | Rango crítico forzado |
| `set_min` / `set_max` | Límites simples del módulo |
| `set_post_process` | Valor de post-proceso |

Umbrales de cadena:

| Campo | Significado |
|-------|-------------|
| `set_str_warning` / `set_str_critical` | Coincidencia de cadena para aviso / crítico |
| `set_str_warning_forced` / `set_str_critical_forced` | Variantes forzadas de cadena |

Dirección de umbrales:

| Campo | Significado |
|-------|-------------|
| `set_critical_inverse` / `set_warning_inverse` | `0` o `1`: invierte la comparación de umbral |

Flip-flop y planificación:

| Campo | Significado |
|-------|-------------|
| `set_min_ff_event` | Umbral flip-flop |
| `set_min_ff_event_normal` / `set_min_ff_event_warning` / `set_min_ff_event_critical` | Umbrales flip-flop por estado |
| `set_ff_type` / `set_ff_timeout` / `set_each_ff` | Tipo flip-flop, timeout y comportamiento keep-last (`0`/`1` donde aplique) |
| `set_module_ff_interval` | Intervalo flip-flop en segundos |
| `set_interval` | Intervalo del módulo en segundos |
| `set_crontab` | Programación cron del módulo |
| `set_quiet` / `set_disabled` | `0` o `1`: silencia o deshabilita el módulo |

Agrupación, identificación e instrucciones:

| Campo | Significado |
|-------|-------------|
| `set_tags` | Nombres de tag separados por comas, en una cadena; los tags deben existir previamente |
| `set_module_group` | Grupo de módulo por nombre; el grupo debe existir previamente |
| `set_module_parent` / `set_module_parent_unlink` | Relación con el módulo padre |
| `set_custom_id` | Identificador personalizado |
| `set_description` | Descripción del módulo |
| `set_critical_instructions` / `set_warning_instructions` / `set_unknown_instructions` | Instrucciones por estado para el operador |

Alertas:

| Campo | Significado |
|-------|-------------|
| `set_alert_template` | Nombre de plantilla de alerta; repetible entre bloques — cada match añade una plantilla |

### Campos protegidos

`name`, `type`, `data`, `value`, `extra_data`, `timestamp` y `status`
definen la identidad del módulo y el valor recolectado; ninguna regla puede
escribirlos.

### Catálogo de errores

Cada error indica su bloque (y su línea cuando se conoce) y termina con
`; rule skipped`:

- `unknown set field '<campo>' (not in the whitelist)` — clave fuera de la
  whitelist, o campo protegido.
- `field '<campo>' is protected and cannot be set`.
- `set_<campo> expects a number/an integer/0 or 1` — valor mal tipado.
- `invalid regex in match key '<clave>'` — patrón malformado o no RE2.
- `rule has no match_module or match_extra_data key` — regla sin selector.
- `cannot parse line` — una línea que no es `clave valor`.
- `missing transform_end` — regla sin cerrar.
- `content outside a transform block` — texto suelto entre reglas.

Un fichero de reglas inexistente se reporta igual
(`post transforms file ... does not exist`); en todos los casos la
monitorización continúa y la ejecución termina con nivel de error distinto
de cero.
