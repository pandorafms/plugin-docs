# Apache Discovery

*Última actualización del artículo: 2026-09-01.*

## Qué monitoriza

Apache Discovery consulta el endpoint legible por máquinas que proporciona `mod_status` de Apache HTTP Server. Una tarea de Discovery crea un agente de Pandora FMS por cada ubicación de red distinta de las URL (o por cada valor `agent_name` configurado distinto) y añade un módulo de disponibilidad, además de un módulo por cada línea `clave: valor` interpretada y no filtrada que devuelve Apache.

El plugin puede procesar URL introducidas en la tarea de Discovery, un archivo de configuración de pares clave/valor o un archivo con varias secciones de configuración con nombre. Genera y transfiere archivos de datos XML de Pandora FMS para los agentes resultantes.

## Preparación

### Compatibilidad y disponibilidad

| Ámbito | Evidencia |
| --- | --- |
| Versión del plugin | El paquete distribuido y su entrada de Marketplace identifican la versión `1.5`. |
| Compatibilidad publicada con Pandora FMS | Marketplace indica que sus integraciones son compatibles con Pandora FMS NG 784 y versiones posteriores. Se trata de compatibilidad publicada, no de un registro de pruebas de este plugin. |
| Entornos probados | Ningún registro de pruebas publicado demuestra una compatibilidad amplia con sistemas operativos o versiones de Apache para este plugin. |
| Disponibilidad del paquete | El paquete está disponible para usuarios con licencia de Pandora FMS ONE en [Pandora FMS Marketplace](https://marketplace.pandorafms.com/entries/pandorafms.apache). La distribución se rige por el modelo de licencia de Pandora FMS ONE; la entrada de Marketplace indica las condiciones aplicables. |

### Requisitos

- Un ejecutable `pandora_apache` empaquetado.
- Acceso de red desde el sistema que ejecuta el plugin hasta cada URL de estado de Apache.
- `mod_status` de Apache habilitado con una respuesta `server-status?auto` legible por máquinas.
- Credenciales de autenticación básica cuando el endpoint de estado las requiera. El plugin solo aplica la autenticación cuando existen el nombre de usuario y la contraseña.
- Un destino de transferencia aceptado por las herramientas empaquetadas del plugin de Pandora.

### Configuración de `mod_status` de Apache

Habilita una ubicación de estado en la configuración de Apache correspondiente y restríngela al sistema que ejecuta el plugin:

```apache
<Location "/server-status">
    SetHandler server-status
    Require ip <MONITORING_HOST_IP>
</Location>
```

`Require all granted` expone ampliamente información operativa del servidor. No lo utilices salvo que dicha exposición sea intencionada y esté protegida por otros controles. Consulta la [documentación de Apache sobre `mod_status`](https://httpd.apache.org/docs/2.4/mod/mod_status.html) para conocer la configuración en el objetivo y sus consideraciones de seguridad.

Después de aplicar la configuración de Apache mediante el procedimiento adecuado para el sistema objetivo, verifica el endpoint legible por máquinas:

```bash
curl "https://<TARGET_HOST>/server-status?auto"
```

La respuesta debe contener líneas de texto sin formato `clave: valor`. Protege el endpoint mediante restricciones de red, autenticación y TLS adecuadas.

### Instalación del paquete de Discovery

Obtén el paquete Apache Discovery desde [Pandora FMS Marketplace](https://marketplace.pandorafms.com/entries/pandorafms.apache) y carga el paquete `.disco` en Pandora FMS. El plugin se distribuye bajo la licencia de Pandora FMS ONE; consulta la entrada de Marketplace para conocer las condiciones aplicables.

## Configuración de la tarea de Discovery

Crea una tarea de Discovery de aplicaciones para Apache después de cargar el paquete. El paquete define dos pasos de configuración: `Apache Basic` y `Apache Detailed`.

En `Apache Basic`, configura las URL directas de los objetivos y los ajustes de transferencia. Todos los campos de la interfaz son opcionales individualmente, pero la tarea necesita al menos una URL en este paso o una sección de objetivo en `Apache Detailed` para recopilar datos.

| Nombre | Obligatorio | Valor predeterminado | Descripción |
| --- | --- | --- | --- |
| `Apache Urls` | No | Vacío | Una o varias URL de estado de Apache, separadas por comas o saltos de línea. |
| `User` | No | Vacío | Nombre de usuario para autenticación básica. Solo se utiliza si también existe una contraseña. |
| `Password` | No | Vacío | Contraseña para autenticación básica. Solo se utiliza si también existe un nombre de usuario. |
| `Verify SSL` | No | `true` | Cuando está habilitado, exige una URL HTTPS y verifica su certificado. |
| `transfer mode` | No | `tentacle` | Modo de transferencia de XML que se pasa a las herramientas del plugin. |
| `tentacle ip` | No | `127.0.0.1` | Destino IPv4 utilizado por la transferencia mediante Tentacle. |
| `tentacle port` | No | `41121` | Puerto de destino de Tentacle. |
| `Module Group` | No | Vacío | Grupo de módulos seleccionado para los módulos generados; un valor vacío se procesa como grupo `0`. |

![Paso Apache Basic de la tarea de Discovery](../assets/images/discovery/apache-discovery/wizard-basic.png)

En `Apache Detailed`, utiliza `Advance Apache` para una o varias secciones de configuración con nombre y, opcionalmente, establece el valor `User-Agent` en el ámbito de la tarea.

| Nombre | Obligatorio | Valor predeterminado | Descripción |
| --- | --- | --- | --- |
| `Advance Apache` | No | Plantilla de ejemplo comentada | Contenido INI con una sección de nombre único por objetivo. Cada sección requiere `urls` para recopilar datos. |
| `User-Agent` | No | Vacío | Cabecera HTTP `User-Agent` personalizada que se aplica únicamente a los objetivos de `Apache Urls`. Se escribe en la configuración temporal de pares clave/valor que consume el plugin, por lo que nunca llega a las secciones de `Advance Apache`; cada una de esas secciones aplica únicamente su propia clave `user_agent`. |

Las credenciales introducidas en la tarea se escriben en una configuración temporal de pares clave/valor que consume el plugin. Restringe el acceso a Pandora FMS y a sus archivos de configuración y temporales según la política de seguridad del despliegue.

## Verificación

Ejecuta la tarea y confirma estos resultados observables:

1. El resumen de ejecución indica que se ha generado al menos un agente y un módulo.
2. Cada ubicación de red de URL distinta (o cada valor `agent_name` configurado distinto) produce un agente con un módulo `Apache Connection`.
3. Un endpoint de estado accesible asigna el valor `1` a `Apache Connection`; si falla la solicitud, el plugin crea o actualiza igualmente el agente y asigna el valor `0` a este módulo, con el error de la solicitud en su descripción.
4. Los valores de Apache interpretados aparecen como módulos adicionales. El conjunto exacto depende de la respuesta.

![Resumen de ejecución de Apache Discovery](../assets/images/discovery/apache-discovery/task-summary.png)

Una tarea puede crear un agente y, aun así, comunicar información de diagnóstico cuando faltan métricas esperadas. Revisa la información de ejecución en lugar de considerar que la creación del agente demuestra por sí sola un éxito completo.

## Interpretación de los resultados

Para cada URL sin un valor `agent_name` configurado, el plugin deriva el nombre interno del agente de Pandora FMS como el MD5 de la ubicación de red de la URL, que también se convierte en el alias legible. Cuando se configura `agent_name`, el nombre interno es el MD5 de ese valor, que también se convierte en el alias. Por tanto, la identidad del agente no es por URL: las URL que comparten una ubicación de red, como distintas rutas en el mismo host y puerto, comparten un único agente y sus módulos se acumulan en él. Las URL o secciones configuradas con el mismo valor `agent_name` también comparten un único agente.

Cada agente recibe `Apache Connection` como módulo `generic_proc`. Cada valor `clave: valor` restante, interpretado y no filtrado, se convierte en `generic_data` si es numérico o en `generic_data_string` en caso contrario. Se filtran `CurrentTime`, `RestartTime`, `Scoreboard`, `ServerUptime` y `TLSSessionCacheStatus`. Las demás claves interpretadas se emiten aunque no estén en la lista de descripciones conocidas del plugin.

Entre las claves conocidas están `ServerVersion`, `ServerMPM`, `Server Built`, `ParentServerConfigGeneration`, `ParentServerMPMGeneration`, `ServerUptimeSeconds`, `Load1`, `Load5`, `Load15`, `Total Accesses`, `Total kBytes`, `Total Duration`, `CPUUser`, `CPUSystem`, `CPUChildrenUser`, `CPUChildrenSystem`, `CPULoad`, `Uptime`, `ReqPerSec`, `BytesPerSec`, `BytesPerReq`, `DurationPerReq`, `BusyWorkers`, `GracefulWorkers`, `IdleWorkers`, `Processes`, `Stopping`, `ConnsTotal`, `ConnsAsyncWriting`, `ConnsAsyncKeepAlive`, `ConnsAsyncClosing` y las métricas `Cache*` definidas por el plugin. Esta lista proporciona descripciones; no es una lista permitida que limite la salida. En particular, `ReqPerSec` y `BytesPerSec` se emiten cuando Apache las devuelve.

![Módulos generados por la tarea de Apache Discovery](../assets/images/discovery/apache-discovery/module-list.png)

Cuando se configura `module_prefix`, el plugin lo antepone directamente a todos los nombres de módulo generados, incluido `Apache Connection`, sin añadir un separador.

## Solución de problemas

| Síntoma | Comprobación |
| --- | --- |
| La tarea indica que las entradas de URL y configuración están vacías | Proporciona al menos un objetivo mediante `Apache Urls`, `--conf` o `--string_conf`. |
| Falla la verificación de HTTPS | Confirma que la URL utiliza HTTPS y presenta un certificado de confianza para el host del plugin. `Verify SSL`/`--ssl` con valor `true` rechaza las URL HTTP. |
| La tarea solo funciona con la verificación deshabilitada | Corrige el certificado o la cadena de confianza del objetivo. El valor `false` deshabilita la verificación del certificado y suprime el aviso relacionado; utilízalo solo después de evaluar el riesgo de interceptación. |
| `Apache Connection` tiene el valor `0` | Comprueba la conectividad de red, la autenticación, el estado HTTP, la URL del objetivo y las restricciones de acceso a `server-status`. La descripción del módulo contiene el error de la solicitud. |
| Aparecen menos módulos de los esperados | Examina la respuesta `?auto` sin procesar. Las versiones de Apache, los MPM y los módulos opcionales pueden exponer claves distintas; la información de Discovery enumera un subconjunto acotado de claves conocidas ausentes. |
| El modo de plugin de servidor imprime `0` aunque existe un agente | Este modo solo imprime `1` cuando se ha contado al menos un agente y `info_value` está vacío. Por tanto, las métricas esperadas ausentes u otro diagnóstico pueden producir `0` después de crear un agente. |
| Falla la transferencia del XML | Verifica el modo de transferencia seleccionado y su destino. Los errores de transferencia se añaden a la información de ejecución. |

El plugin no dispone de una opción CLI de modo detallado o depuración. Sus diagnósticos se devuelven mediante la información de ejecución de Discovery.

## Referencia

### Parámetros de CLI

Se requiere operativamente al menos uno de `--urls`, `--conf` o `--string_conf`. Cuando se proporcionan varios, el plugin procesa cada superficie aplicable.

| Nombre | Obligatorio | Valor predeterminado | Descripción |
| --- | --- | --- | --- |
| `--urls` | Condicional | Sin definir | URL de estado separadas por comas o saltos de línea. Es obligatorio cuando ningún archivo de configuración proporciona un objetivo. |
| `--conf` | Condicional | Sin definir | Ruta a una configuración de pares clave/valor sin cabecera de sección; el plugin antepone `[CONF]`. |
| `--string_conf` | Condicional | Sin definir | Ruta a un archivo INI que contiene una o varias secciones de objetivo con nombre. |
| `--user` | No | Sin definir | Nombre de usuario para autenticación básica con `--urls`; solo se utiliza junto con `--password`. |
| `--password` | No | Sin definir | Contraseña para autenticación básica con `--urls`; solo se utiliza junto con `--user`. |
| `--user_agent` | No | Sin definir | Cabecera HTTP `User-Agent` personalizada para `--urls`. |
| `--ssl` | No | `true` | Interpreta `yes`, `true`, `t`, `y` o `1` como habilitado; los demás valores deshabilitan la verificación. La verificación habilitada también exige HTTPS. |
| `-tm`, `--transfer_mode` | No | `tentacle` | Modo de transferencia del XML. |
| `-ti`, `--tentacle_ip` | No | `127.0.0.1` | Destino de Tentacle; el validador de CLI acepta el formato IPv4. |
| `-tp`, `--tentacle_port` | No | `41121` | Puerto de destino de Tentacle. |
| `-in`, `--interval` | No | Sin definir | Intervalo del agente en segundos. |
| `--as_server_plugin` | No | `false` | Imprime únicamente `1` o `0` y termina en lugar de imprimir la salida de Discovery. |

Pasar `--user` y `--password` expone las credenciales en la línea de comandos, donde el historial del shell y la lista de procesos del sistema operativo pueden revelarlas. Cuando una ejecución manual requiera autenticación, utiliza preferentemente un archivo de configuración protegido y restríngelo a la cuenta que ejecuta el plugin.

### Parámetros del archivo de configuración

El archivo indicado mediante `--conf` contiene únicamente líneas de pares clave/valor. No añadas `[CONF]`, porque el plugin incorpora esa cabecera de sección antes de interpretar el archivo. En cambio, un archivo indicado mediante `--string_conf` requiere una o varias secciones INI con nombres únicos.

| Nombre | Obligatorio | Valor predeterminado | Descripción |
| --- | --- | --- | --- |
| `urls` | Sí por objetivo | Vacío | URL de estado separadas por comas o saltos de línea. |
| `agent_name` | No | Vacío | Origen del alias legible; el nombre interno es su valor MD5. |
| `module_prefix` | No | Vacío | Texto que se antepone directamente a los nombres de módulo. |
| `username` | No | Vacío | Nombre de usuario para autenticación básica; solo se utiliza con `password`. |
| `password` | No | Vacío | Contraseña para autenticación básica; solo se utiliza con `username`. |
| `verify_ssl` | No | `false` | Booleano de verificación del certificado para los objetivos definidos en archivos de configuración. |
| `transfer_mode` | No | Vacío | Modo de transferencia del XML. |
| `tentacle_ip` | No | Vacío | Destino de Tentacle. |
| `tentacle_port` | No | Vacío | Puerto de destino de Tentacle. |
| `interval` | No | `0` | Intervalo del agente tras la conversión a entero cuando se omite o no es válido. |
| `user_agent` | No | Vacío | Cabecera HTTP `User-Agent` personalizada. |
| `module_group` | No | `0` | Los valores vacíos se normalizan al grupo de módulos `0`. |

Protege los archivos de configuración como secretos en texto sin cifrar cuando contengan credenciales. No los almacenes en directorios compartidos, registros ni sistemas de control de versiones.

Ejemplo de archivo para `--conf`:

```ini
urls=https://<TARGET_HOST>/server-status
agent_name=<READABLE_ALIAS>
username=<USERNAME>
password=<PASSWORD>
verify_ssl=true
transfer_mode=tentacle
tentacle_ip=<PANDORA_FMS_SERVER_IPV4>
tentacle_port=41121
interval=300
module_group=0
```

Ejemplo de archivo para `--string_conf`:

```ini
[apache_target_1]
urls=https://<TARGET_HOST>/server-status
agent_name=<READABLE_ALIAS>
verify_ssl=true
transfer_mode=tentacle
tentacle_ip=<PANDORA_FMS_SERVER_IPV4>
tentacle_port=41121
```

### Ejecución manual

Ejecuta el archivo empaquetado con marcadores de posición seguros:

```bash
./pandora_apache \
  --urls "https://<TARGET_HOST>/server-status" \
  --ssl true \
  --transfer_mode tentacle \
  --tentacle_ip <PANDORA_FMS_SERVER_IPV4> \
  --tentacle_port 41121
```

El plugin añade `?auto` cuando la consulta de la URL todavía no contiene `auto`. La ejecución normal imprime la salida de Discovery con resúmenes del total de agentes y módulos, y transfiere un archivo de datos XML por cada agente generado.

Con `--as_server_plugin true`, la salida es `1` únicamente cuando se ha contado al menos un agente y no se ha registrado ningún mensaje informativo. Cualquier otro resultado imprime `0`.
