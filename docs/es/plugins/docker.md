# Docker

*Última actualización del artículo: 2026-10-23.*

<!-- DRAFT: Solo verificación estática del artefacto; faltan validar instalación del paquete distribuido, recopilación real de Docker e ingesta del EndPoint. -->

## Qué monitoriza

El plugin de Docker recopila estadísticas de contenedores en ejecución y escribe XML de módulos de Pandora FMS en la salida estándar. Ejecútelo como plugin de EndPoint mediante `module_plugin` para que este incluya los módulos en los datos de su agente. No es una aplicación de Discovery y no crea ni transfiere agentes separados.

Seleccione el modo **global** para estadísticas agregadas del daemon o **container** para módulos individuales por nombre de contenedor. Ambos informan de CPU, memoria, red y E/S de bloques; solo el modo global incluye estado del daemon y número de contenedores en ejecución.

## Preparación

### Requisitos y compatibilidad

| Ámbito | Estado | Requisito o limitación |
| --- | --- | --- |
| Acceso al daemon de Docker | Requerido | La cuenta ejecutora debe poder conectar, comprobar el daemon, listar contenedores en ejecución y leer sus estadísticas |
| EndPoint de Pandora FMS | Requerido para la ingesta | El EndPoint ejecuta `module_plugin` e incluye el XML devuelto en los datos de su propio agente |
| Grupo de módulos | Preparar antes de usar | El valor predeterminado es `Docker`; cree o seleccione el grupo previsto en Pandora FMS |
| Versiones concretas de Docker, EndPoint y sistema operativo | Sin validar | La referencia de desarrollo con Docker 18.03.1-ce de la guía antigua no establece compatibilidad para este artefacto |

Coloque el ejecutable distribuido `docker_stats` y su configuración en el equipo donde lo ejecutará el EndPoint. Elija rutas accesibles para la cuenta del EndPoint y compruebe que puede ejecutar el plugin y leer el archivo. Aún deben validarse la instalación y los requisitos de ejecución del paquete suministrado; esta página no prescribe un procedimiento de compilación ni instalación de dependencias.

La conexión utiliza el entorno de conexión a Docker del proceso. La configuración del plugin no tiene campos de host del daemon, token, contraseña ni certificado. Compruebe el acceso con la **cuenta y el entorno de ejecución del EndPoint**, no solo desde una sesión interactiva de administrador. No se establece un procedimiento con `docker_machine` para este artefacto; `docker` no selecciona la conexión ni invoca un ejecutable Docker.

No conceda acceso administrativo general solo para ejecutar el ejemplo. El administrador debe autorizar el acceso necesario al daemon según la política de seguridad del despliegue. Proteja las credenciales de conexión proporcionadas mediante el entorno; no incluya secretos en comandos, registros ni capturas.

## Configuración

### Escribir la configuración del plugin

Use texto plano con líneas `key=value`, sin cabecera de sección. Este ejemplo conserva los valores predeterminados y no se ha ejecutado:

```ini
docker=Docker
module_interval=1
module_group=Docker
mode=global
```

- Configure `mode=container` para obtener módulos por contenedor en ejecución en lugar de los globales.
- En modo container, `docker` es el **prefijo del nombre de módulos**. Por ejemplo, `docker=Docker` produce nombres como `Docker - <CONTAINER_NAME> - CPU Usage`. No es una ruta de ejecutable ni un precomando. Los nombres globales ignoran este ajuste.
- `module_group` y `module_interval` se escriben en cada módulo de salida. `module_interval` es el multiplicador del intervalo de módulo respecto al intervalo del agente, no una pausa ni un planificador interno. Use el valor adecuado a la planificación del EndPoint; el plugin lo transmite sin validación numérica.

### Registrar la ejecución en el EndPoint

Añada la siguiente línea a la configuración del EndPoint y sustituya ambos marcadores por las rutas instaladas:

```text
module_plugin <PATH_TO_PLUGIN> --conf <PATH_TO_CONFIG>
```

Puede usar las rutas convencionales documentadas si instaló los archivos en ellas:

```text
module_plugin /usr/share/pandora_agent/plugins/docker_stats --conf /usr/share/pandora_agent/plugins/docker_stats.conf
```

Aplique la configuración mediante el procedimiento habitual del EndPoint. Es un registro de plugin de agente, no una configuración de plugin de servidor ni una tarea de Discovery. Los ejemplos anteriores no se han ejecutado contra un EndPoint.

## Verificación

1. Ejecute manualmente el ejecutable instalado con la misma cuenta y entorno de conexión que el EndPoint:

   ```bash
   <PATH_TO_PLUGIN> --conf <PATH_TO_CONFIG>
   ```

2. Revise la salida estándar. Una ejecución global sin errores produce 11 fragmentos `<module>`; el modo container produce seis por contenedor cuyas estadísticas se recopilen. La salida no es un documento `<agent_data>` completo ni incluye resumen de Discovery o resultado de transferencia de agentes.
3. Compruebe nombres, tipos, grupo e intervalo con la [referencia](#referencia) y contraste valores representativos con las estadísticas del daemon. Un cero también puede deberse a datos ausentes o recopilación parcial; revise los errores.
4. Tras un ciclo del EndPoint, confirme que los módulos esperados aparecen en **el agente de ese EndPoint**. La salida XML manual no verifica por sí sola la ingesta ni el transporte a Pandora FMS.

No se ha ejecutado Docker en un entorno real, instalado el paquete ni probado la ingesta del EndPoint para esta documentación. Estos son pasos de verificación para el operador, no resultados correctos observados.

## Interpretar los resultados

| Modo | Salida | Interpretación |
| --- | --- | --- |
| `global` | 11 módulos de nombre fijo | Estado, recuento, CPU media de contenedores, memoria total de contenedores frente al host, contadores de E/S y variantes incrementales |
| `container` | Seis módulos por nombre de contenedor recopilado | CPU, memoria frente al límite del contenedor, entrada/salida de red y lectura/escritura de bloques; sin módulos globales de estado/recuento |

Solo se consideran contenedores listados como `running`. Los detenidos no reciben nuevos módulos. Sin contenedores en ejecución, el modo global produce estado y valores cero de recuento/uso/E/S; el modo container no produce módulos.

### Significado de los valores

- **CPU:** se calcula con diferencias de contadores de CPU/sistema y el número de CPU indicado. La CPU global suma los porcentajes recopilados y divide por el número de contenedores en ejecución listados, incluidos aquellos cuya recopilación falló. No es la suma de porcentajes de contenedores ni un porcentaje de CPU de todo el host.
- **Memoria:** el modo global divide la suma del uso de memoria indicado por los contenedores entre `MemTotal` del host obtenido del daemon. El modo container divide el uso indicado entre el límite de memoria del contenedor. Ambos multiplican por 100. Un denominador ausente/cero produce `0`; por ello, un fallo al leer información del host puede dar memoria global a `0` aunque haya contenedores en ejecución.
- **E/S:** los bytes de red se suman entre interfaces devueltas del contenedor. Los bytes de bloques se suman de las entradas de lectura/escritura recibidas. Las estadísticas ausentes aportan `0`. El plugin emite contadores como `generic_data_inc`; no calcula por sí mismo una tasa por segundo.
- **CPU, memoria y recuento incrementales:** el modo global también emite esos valores como `generic_data_inc`. Repiten las muestras correspondientes; no interprete sus tasas procesadas como porcentajes ordinarios de CPU/memoria ni como número de contenedores en ejecución.

En modo container, los nombres dependen de `docker` y del nombre del contenedor, no de su ID corto. Cambiar cualquiera cambia los nombres de módulos; el ID corto aparece en descripciones. Use nombres sencillos de prefijo/contenedor sin caracteres especiales de XML: los valores se insertan en el XML sin escape, por lo que esos caracteres pueden invalidarlo.

## Operación y solución de problemas

La ejecución manual realiza una única recopilación. El EndPoint proporciona la ejecución programada. Un planificador puede invocar el ejecutable, pero programarlo por sí solo no incorpora los fragmentos impresos a Pandora FMS; este artefacto no implementa transferencia XML autónoma.

No hay opción debug/verbose, precomando, transferencia de agentes por contenedor ni modo de plugin de servidor. No reutilice `pre_command`, `metrics_per_container` ni `as_server_plugin` de otro artefacto Docker.

| Señal | Comprobación o limitación |
| --- | --- |
| `Error file: ... does not exist` | Indique una ruta de configuración existente, no vacía y legible para la cuenta ejecutora |
| `Error while reading configuration file: ...` | Revise acceso y sintaxis `key=value`; no añada cabecera de sección |
| `Could not connect to the Docker daemon...` | Revise disponibilidad y acceso al daemon con la cuenta/entorno del EndPoint. Las excepciones de conexión terminan con estado `1`, sin emitir un módulo `Docker state=0` |
| `Warning: The information could not be obtained from the Docker system: ...` | No se pudo leer información del host; la memoria global usa `0` si no se obtiene la memoria del host |
| `Statistics could not be obtained for the container ...` | La recopilación global continúa; los totales pueden ser parciales mientras recuento y divisor de CPU incluyen el contenedor listado |
| `Detailed statistics for the container could not be obtained. ...` | Continúa con otros contenedores; el afectado puede no aparecer |
| `Invalid operating mode: ...` | Use `global` o `container`; no distingue mayúsculas |
| `Fatal error in plugin execution: ...` | Un error de recopilación/salida impidió terminar normalmente; revise el detalle |
| Salida vacía en modo container | Puede no haber contenedores en ejecución o haber fallado las estadísticas de todos |
| Hay salida, pero no se incorporan módulos | Revise rutas de `module_plugin`, cuenta ejecutora, configuración, entorno de conexión y recopilación/transporte del EndPoint. Los errores pueden mezclarse en la salida estándar e invalidar el XML |

Los fallos de configuración, conexión, modo no válido y ejecución fatal terminan con estado `1`. Los errores de argumentos los gestiona la ayuda/analizador de la CLI. Los fallos por contenedor y avisos de información del host pueden dejar una salida normal pero parcial: el estado de salida no demuestra recopilación completa. Revise la salida antes de compartirla, ya que errores/descripciones pueden incluir identificadores del daemon o de contenedores.

## Referencia

### Línea de comandos

| Nombre | Requerido | Por defecto | Descripción |
| --- | --- | --- | --- |
| `--conf <PATH_TO_CONFIG>` | Sí | Ninguno | Ruta del archivo de configuración |
| `-h`, `--help` | No | No aplicable | Muestra ayuda de argumentos y termina |

### Archivo de configuración

| Nombre | Requerido | Por defecto | Descripción |
| --- | --- | --- | --- |
| `docker` | No | `Docker` | Prefijo de nombres en modo container; ignorado para nombres globales; no es ruta de ejecutable |
| `module_interval` | No | `1` | Se escribe como `<module_interval>` en cada módulo; sin validación numérica en el plugin |
| `module_group` | No | `Docker` | Se escribe como `<module_group>` en cada módulo; prepare el grupo previsto en Pandora FMS |
| `mode` | No | `global` | `global` o `container`, sin distinción de mayúsculas; otros valores causan error |

Son las cuatro claves de configuración consumidas por este artefacto. Una línea comentada `module_tags` de un ejemplo antiguo no define una entrada admitida aquí. El plugin no expone una referencia propia de variables de entorno de conexión; hereda la conexión del entorno de ejecución.

### Módulos globales

| Nombre | Tipo | Unidad | Valor |
| --- | --- | --- | --- |
| `Docker state` | `generic_proc` | — | Resultado del ping al daemon: `1` para verdadero, `0` para falso; las excepciones de conexión abortan antes de generar salida |
| `Docker containers running` | `generic_data` | — | Número de contenedores en ejecución listados |
| `Docker CPU usage` | `generic_data` | `%` | CPU media de contenedores según lo explicado, con dos decimales |
| `Docker memory usage` | `generic_data` | `%` | Memoria total indicada por contenedores frente a memoria del host, con dos decimales |
| `Docker network input` | `generic_data_inc` | `B` | Suma de bytes recibidos |
| `Docker network output` | `generic_data_inc` | `B` | Suma de bytes transmitidos |
| `Docker blocks in` | `generic_data_inc` | `B` | Suma de bytes leídos de bloques, no escrituras ni número de bloques |
| `Docker blocks out` | `generic_data_inc` | `B` | Suma de bytes escritos en bloques, no lecturas ni número de bloques |
| `Docker containers running incremental` | `generic_data_inc` | — | Mismo recuento que el módulo de muestra |
| `Docker CPU usage incremental` | `generic_data_inc` | `%` | Mismo valor medio de CPU que el módulo de muestra |
| `Docker memory usage incremental` | `generic_data_inc` | `%` | Mismo porcentaje de memoria que el módulo de muestra |

### Módulos de contenedor

Cada nombre completo es `<PREFIX> - <CONTAINER_NAME> - <SUFFIX>`, donde `<PREFIX>` es `docker`. Se emiten los seis por contenedor recopilado correctamente; los porcentajes de CPU y memoria tienen dos decimales.

| Sufijo | Tipo | Unidad | Valor |
| --- | --- | --- | --- |
| `CPU Usage` | `generic_data` | `%` | Porcentaje de CPU del contenedor |
| `Memory Usage %` | `generic_data` | `%` | Uso indicado frente al límite de memoria del contenedor; la descripción incluye uso/límite |
| `Network Input` | `generic_data_inc` | `B` | Bytes recibidos sumados entre interfaces |
| `Network Output` | `generic_data_inc` | `B` | Bytes transmitidos sumados entre interfaces |
| `Block Read` | `generic_data_inc` | `B` | Bytes leídos de bloques |
| `Block Write` | `generic_data_inc` | `B` | Bytes escritos en bloques |

Cada módulo contiene nombre, tipo, dato, descripción, grupo, intervalo y unidad. En módulos globales sin unidad definida, este artefacto emite el texto literal `None` en ese campo; `—` en la tabla indica que no hay unidad significativa. Verifique cómo lo trata el EndPoint receptor en lugar de considerar esta página una prueba de ingesta.
