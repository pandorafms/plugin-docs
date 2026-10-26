# Prometheus Discovery

*Última actualización del artículo: 2026-10-26.*

## Qué monitoriza

El addon de Discovery de Prometheus convierte el resultado de sus propias consultas PromQL en módulos de Pandora FMS. Una tarea de Discovery se conecta a la API HTTP de un servidor Prometheus, ejecuta cada consulta que usted define y crea agentes y módulos con los valores devueltos. Usted decide qué métricas se recogen, qué umbrales llevan los módulos y a qué agente pertenece cada métrica.

Una tarea de Discovery genera:

- **Un agente principal**, con el nombre indicado en **Agent name** (`Prometheus` por defecto), que recibe todas las métricas que no se asignan a otro agente.
- **Agentes adicionales** (opcional), uno por cada nombre de agente distinto que asigne a una consulta.

El addon recoge únicamente lo que devuelven sus consultas. No define consultas propias, por lo que una tarea sin consultas no genera módulos y notifica un error.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
|--------|--------|-----------|
| Addon `pandorafms.prometheus`, versión `1.0` | Objetivo documentado | La versión que describe esta página. La entrada del Marketplace ofrece el paquete `pandorafms.prometheus.1.0.disco` |
| Acceso de red desde el servidor de Discovery a la API HTTP de Prometheus | `Required` | El addon llama a `<URL>/api/v1/query` |
| Versiones del servidor Prometheus | `Not validated` | No se ha registrado una matriz de versiones para este addon |
| Sistema operativo del servidor de Discovery | `Not validated` | No se ha registrado ningún sistema operativo para esta versión |
| Versiones concretas de Pandora FMS | `Not validated` | El Marketplace indica únicamente una compatibilidad general de sus entradas con Pandora FMS NG 784 y posteriores; no se ha registrado una matriz para este addon |

### Prerrequisitos

1. **Conectividad** desde el servidor de Discovery al servidor Prometheus, por ejemplo `http://<PROMETHEUS_HOST>:9090`.
2. **Certificado TLS válido** cuando la URL usa `https`. El addon siempre verifica el certificado del servidor Prometheus y no ofrece ninguna opción para desactivar la verificación.
3. **Credenciales** solo cuando el servidor Prometheus está protegido con autenticación HTTP básica.
4. **Pandora FMS**: un servidor de Discovery para ejecutar la tarea y la consola para definirla.

No hace falta instalar nada más en el servidor de Discovery para ejecutar una tarea.

### Instalar el addon

Descargue el paquete `.disco` de la entrada del Marketplace de Pandora FMS, cuya descarga está limitada a usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.prometheus](https://marketplace.pandorafms.com/entries/pandorafms.prometheus)

Cárguelo en Pandora FMS. Una vez cargado, **Prometheus** está disponible en la sección de aplicaciones del asistente de tareas de Discovery.

<!-- SCREENSHOT NEEDED: sección de aplicaciones de Discovery en la consola mostrando la entrada Prometheus, sin datos reales. -->

## Configurar la tarea de Discovery

Cree una tarea de Discovery y elija **Prometheus**. La consola presenta los campos en tres pasos; todos los campos se documentan en [Parámetros de la tarea](#parametros-de-la-tarea).

1. **prometheus base** — conexión:

    - **Url**: dirección del servidor Prometheus, por ejemplo `http://<PROMETHEUS_HOST>:9090`. Obligatorio. No la termine con una barra.
    - **Tentacle IP**, **Tentacle port** y **Tentacle extra options**: destino de los datos de los agentes generados. Rara vez hace falta cambiarlos.

    ![Paso prometheus base con Url y campos de Tentacle](../assets/images/discovery/prometheus/prometheus-base-step.png)

2. **prometheus detailed** — opciones de agente y autenticación:

    - **Agent name**: nombre del agente principal.
    - **Use prefix** y **Prefix**: texto que se antepone al nombre de todos los agentes creados.
    - **Auth basic**, **Username** y **Password**: autenticación HTTP básica.

    ![Paso prometheus detailed con agente, prefijo y autenticación](../assets/images/discovery/prometheus/prometheus-detailed-step.png)

3. **prometheus custom** — las consultas, tres cajas de texto libre con una definición por línea:

    - **Custom queries**: `<NOMBRE_METRICA> = <CONSULTA_PROMQL>`.
    - **Define tresholds**: `<NOMBRE_METRICA> = <UMBRAL> <VALOR>|<UMBRAL> <VALOR>`.
    - **Define agents**: `<NOMBRE_METRICA> = <NOMBRE_AGENTE>`.

    ![Paso prometheus custom con las cajas de consultas, umbrales y agentes](../assets/images/discovery/prometheus/prometheus-custom-step.png)

El grupo y el intervalo de la tarea proceden del paso genérico de definición de la tarea y se aplican a los agentes que crea.

### Definir consultas, umbrales y agentes

El nombre anterior al `=` es la **clave** de la métrica. Es el prefijo del nombre de los módulos que genera la consulta y enlaza la consulta con sus líneas de umbral y de agente. Las claves no distinguen mayúsculas de minúsculas (se convierten a minúsculas) y no pueden contener `=` ni `:`.

```ini
node_cpu_avg = avg_over_time(node_cpu_seconds_total[15m])
up_status = up
cpu_idle_avg = node_cpu_seconds_total{mode="idle",cpu="0"}
disk_free_last = node_filesystem_avail_bytes{mountpoint="/"}
node_cpu_seconds = node_cpu_seconds_total{mode="idle",cpu="0"}[15m]
```

Umbrales, una línea por clave, con varios umbrales separados por `|`:

```ini
cpu_idle_avg = min_critical 75|min_warning 60
```

Agentes, una línea por clave. Las claves sin línea van al agente principal:

```ini
node_cpu_seconds = Prometheus cpu
```

Reglas:

- Las líneas que empiezan por `#` son comentarios.
- Una línea de umbral o de agente solo se aplica si existe una consulta con la misma clave; en caso contrario se ignora.
- Cada umbral es un nombre y un valor separados por un espacio. Los elementos que no tienen exactamente dos palabras se ignoran. El nombre se pasa al módulo tal cual; el addon no lo valida.
- El signo de porcentaje (`%`) no se puede usar en las tres cajas de texto. Hace que la tarea falle con `Error while reading specification configuration file`.

Los ejemplos de consulta anteriores están escritos para un servidor Prometheus que exporta las métricas de `node_exporter`. Adapte los nombres de métrica a su propio servidor.

## Verificar la primera ejecución

Fuerce la tarea desde la lista de tareas de Discovery y compruebe el resultado en este orden.

1. **El resumen de la tarea.** Una tarea que termina correctamente informa de:

    - **Total agents**: agentes generados.
    - **Total modules**: módulos generados.

    Si la tarea no genera módulos, la información de ejecución muestra `Error: The task has not generated modules. Please check your access to the environment, permissions, or queries.`

    ![Resumen de la tarea con Total agents y Total modules](../assets/images/discovery/prometheus/prometheus-task-summary.png)

2. **Los agentes.** El agente principal y uno por cada nombre asignado en **Define agents**.

3. **Los módulos.** Uno o más módulos por consulta; consulte [Interpretar los resultados](#interpretar-los-resultados).

## Interpretar los resultados

### Agentes generados

| Agente | Alias | Notas |
|--------|-------|-------|
| Agente principal | **Prefix** + **Agent name** | Contiene todas las métricas sin agente asignado |
| Agente adicional | **Prefix** + el nombre indicado en **Define agents** | Uno por nombre distinto. Varias claves pueden compartirlo |

Un agente solo se crea si recibe al menos un módulo. Todos los agentes pertenecen al grupo de la tarea e informan con el intervalo de la tarea.

La identidad del agente se deriva del alias, es decir, **Prefix** + nombre del agente, y no de la tarea ni de la URL de Prometheus. Dos tareas con el mismo prefijo y nombre de agente informan al mismo agente, aunque apunten a servidores Prometheus distintos. Use un **Prefix** distinto por servidor Prometheus para mantener separados sus agentes.

### Módulos generados

Cada serie devuelta por una consulta se convierte en un módulo. Su nombre es la clave de la consulta seguida de las etiquetas de la serie, con la forma `<CLAVE> {'etiqueta': 'valor', ...}`, por ejemplo `up_status {'__name__': 'up', 'instance': '<HOST>:9100', 'job': 'node'}`. Una consulta que devuelve varias series crea por tanto varios módulos con la misma clave.

| Resultado de la consulta | Tipo de módulo | Valor |
|--------------------------|----------------|-------|
| Consulta instantánea, un valor por serie | `generic_data` | El valor devuelto, como número |
| Selector de rango, como `metric[15m]` | `generic_data_string` | La lista de valores devueltos, cada uno con su marca de tiempo |

Las consultas sin resultados se omiten. Los umbrales definidos para una clave se aplican a todos los módulos de esa clave.

## Operación

### Ejecución manual

El addon puede ejecutarse fuera de una tarea de Discovery. El ejecutable recibe un único parámetro, la ruta al fichero de configuración descrito en [Fichero de configuración](#fichero-de-configuracion):

```bash
./pandora_prometheus --conf <PATH_TO_CONFIG>
```

Imprime un resultado de ejecución en JSON y envía un fichero de datos por agente con el modo de transferencia configurado. La tarea de Discovery usa el mismo ejecutable con un fichero de configuración temporal construido a partir de los campos de la tarea.

Si un fichero de configuración contiene `password`, protéjalo con permisos restrictivos.

### Limitaciones

- Las consultas deben devolver vectores instantáneos o de rango. Una consulta que devuelva un escalar, como `scalar(up)`, hace fallar la tarea.
- El addon siempre verifica los certificados TLS.
- La autenticación básica solo se aplica cuando **Username** y **Password** están informados.
- Cada consulta es una consulta instantánea que Prometheus evalúa en el momento de la ejecución.

## Solución de problemas

El addon no tiene modo detallado ni de depuración. Su canal de diagnóstico es el campo de información del resultado de ejecución, que se muestra en la información de ejecución de la tarea.

- **`HTTP Error querying Prometheus: <CODE> ...`**: el servidor respondió con un estado HTTP distinto de 200. El mensaje incluye el cuerpo de la respuesta y la consulta que falló. Un `401` indica que falta la autenticación básica o es incorrecta; un `404` suele indicar una **Url** incorrecta. El resto de consultas se siguen ejecutando.
- **`Prometheus query error: ...`**: Prometheus rechazó la consulta, por ejemplo por un error de sintaxis. El mensaje incluye la consulta que falló. El resto de consultas se siguen ejecutando.
- **`[Error] Please, check and change your configuration ...`**: la tarea no pudo completarse, seguido del texto del error. Causas típicas son un servidor inalcanzable, un certificado TLS que no se puede verificar o una consulta que devuelve un escalar.
- **`Error while reading specification configuration file`**: una de las tres cajas de texto no es válida. Revise los caracteres `%` y las líneas sin `=`.
- **`Error: The task has not generated modules ...`**: ninguna consulta devolvió datos. Ejecute la misma consulta en el navegador de expresiones de Prometheus y revise **Url**, credenciales y claves de consulta.
- **Menos módulos de los esperados**: las consultas que no devuelven series no producen módulos, y dos series con el mismo nombre de módulo se reducen a un único módulo.
- **Umbrales o asignación de agente no aplicados**: la clave de la línea de umbral o de agente no coincide con la clave de ninguna consulta. Las claves no distinguen mayúsculas de minúsculas.
- **Tentacle extra options no tiene efecto**: el addon no lee este valor, por lo que no puede cambiar cómo se envían los datos.

## Referencia

### Parámetros de la tarea

#### prometheus base

| Campo | Macro | Tipo | Obligatorio | Valor por defecto | Descripción |
|-------|-------|------|-------------|-------------------|-------------|
| Url | `_url_` | cadena | Sí | — | URL de Prometheus, por ejemplo `http://localhost:9090` |
| Tentacle IP | `_tentacleIP_` | cadena | Sí | `127.0.0.1` | Servidor que recibe los datos de los agentes |
| Tentacle port | `_tentaclePort_` | número | Sí | `41121` | Puerto de Tentacle |
| Tentacle extra options | `_tentacleExtraOpt_` | cadena | No | — | El addon no lo utiliza |

#### prometheus detailed

| Campo | Macro | Tipo | Obligatorio | Valor por defecto | Descripción |
|-------|-------|------|-------------|-------------------|-------------|
| Agent name | `_agentName_` | cadena | Sí | `Prometheus` | Nombre del agente principal |
| Use prefix | `_usePrefix_` | casilla | No | desactivada | Muestra **Prefix** |
| Prefix | `_prefix_` | cadena | No | — | Visible con **Use prefix** activado. Se antepone al nombre de todos los agentes |
| Auth basic | `_authBasic_` | casilla | No | desactivada | Muestra **Username** y **Password** |
| Username | `_userName_` | cadena | No | — | Visible con **Auth basic** activado |
| Password | `_password_` | cadena | No | — | Visible con **Auth basic** activado |

#### prometheus custom

| Campo | Macro | Tipo | Obligatorio | Valor por defecto | Descripción |
|-------|-------|------|-------------|-------------------|-------------|
| Custom queries | `_configQueries_` | área de texto | Sí, en la práctica | Ejemplo comentado | Una línea `<CLAVE> = <CONSULTA>` por consulta |
| Define tresholds | `_configTresholds_` | área de texto | No | Ejemplo comentado | Una línea `<CLAVE> = <UMBRAL> <VALOR>\|...` por clave |
| Define agents | `_configAgents_` | área de texto | No | Ejemplo comentado | Una línea `<CLAVE> = <NOMBRE_AGENTE>` por clave |

### Fichero de configuración

El fichero de configuración que se pasa con `--conf` es un fichero INI. Las secciones `[QUERIES]`, `[THRESHOLDS]` y `[AGENTS]` admiten las mismas líneas que las cajas de texto del tercer paso del asistente. Las claves de la sección `[CONF]` que no figuran a continuación se ignoran.

| Clave | Obligatoria | Valor por defecto | Descripción |
|-------|-------------|-------------------|-------------|
| `url` | Sí | `http://localhost:9090` | URL de Prometheus |
| `agents_group` | No | `0` | ID numérico del grupo de los agentes |
| `interval` | No | `300` | Intervalo de los agentes, en segundos |
| `prefix` | No | vacío | Prefijo de los nombres de agente. Escríbalo sin comillas: las comillas pasan a formar parte del prefijo |
| `agent_name` | No | `Prometheus` | Nombre del agente principal |
| `username` | No | vacío | Usuario para la autenticación básica |
| `password` | No | vacío | Contraseña para la autenticación básica |
| `transfer_mode` | No | `tentacle` | Cómo se entregan los ficheros de datos |
| `tentacle_ip` | No | `127.0.0.1` | Dirección del servidor Tentacle |
| `tentacle_port` | No | `41121` | Puerto de Tentacle |

```ini
[CONF]
agents_group = <GROUP_ID>
interval = 300
prefix = <PREFIX>
agent_name = Prometheus
url = http://<PROMETHEUS_HOST>:9090
username = <USERNAME>
password = <PASSWORD>
tentacle_ip = <TENTACLE_IP>
tentacle_port = 41121

[QUERIES]
up_status = up
cpu_idle_avg = node_cpu_seconds_total{mode="idle",cpu="0"}
node_cpu_seconds = node_cpu_seconds_total{mode="idle",cpu="0"}[15m]

[THRESHOLDS]
cpu_idle_avg = min_critical 75|min_warning 60

[AGENTS]
node_cpu_seconds = Prometheus cpu
```

### Línea de comandos

| Parámetro | Obligatorio | Valor por defecto | Descripción |
|-----------|-------------|-------------------|-------------|
| `-c`, `--conf` | Sí | — | Ruta al fichero de configuración. Si el fichero no existe, la ejecución termina con `Configuration file not found: <PATH>` |
