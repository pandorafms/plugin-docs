# Citrix NetScaler Discovery

*Última actualización del artículo: 2026-11-04.*

## Qué monitoriza

El addon Citrix NetScaler Discovery monitoriza appliances Citrix NetScaler ADC a través de la API REST NITRO y convierte el estado del appliance, la alta disponibilidad, los servidores virtuales, los servicios, los grupos de servicios y las interfaces de red en agentes y módulos de Pandora FMS.

Una tarea de Discovery crea un agente por cada appliance configurado. Con **Create agent per virtual server** activado, también crea un agente por cada servidor virtual de balanceo de carga y por cada servidor virtual GSLB. El agente del appliance contiene el estado de la conexión, las estadísticas del sistema, el estado de alta disponibilidad, los servicios, los grupos de servicios y las interfaces de red. Los agentes de servidor virtual contienen los módulos de estado y tráfico de su servidor virtual.

La tarea selecciona qué familias de recursos se recopilan, de modo que los agentes y módulos generados se ajustan a la parte del entorno ADC que se quiere monitorizar.

Una extensión de consola complementaria, **Dashboard Citrix NetScaler**, presenta los datos de estos agentes como un panel. Véase [Dashboard Citrix NetScaler](#dashboard-citrix-netscaler).

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Versión del plugin `1.0` (`pandorafms.citrix_netscaler`) | Objetivo documentado | La versión que describe esta página, identificada por la definición del paquete. Véase [Identidad del plugin](#identidad-del-plugin). |
| Un appliance Citrix NetScaler ADC con la API de estadísticas NITRO accesible por HTTP o HTTPS | `Requerido` | El addon lee los objetos de estadísticas de cada appliance configurado a través de la API REST NITRO. Es un requisito previo, no una declaración de compatibilidad. |
| Una credencial con acceso de lectura a la API de estadísticas NITRO | `Requerido` | El addon se autentica contra la API NITRO y solo lee estadísticas. Es un requisito previo, no una declaración de compatibilidad. |
| Un modelo o versión de firmware concreta de Citrix NetScaler | `No validado` | Ningún registro de pruebas publicado establece una matriz de compatibilidad de modelo o firmware para esta versión. |
| Pandora FMS NG 784 y posteriores | Indicado por el Marketplace | Aviso general mostrado en el Marketplace para todas las entradas, no específico de este addon. |
| El sistema operativo del entorno que ejecuta el addon | `No validado` | No se ha registrado ningún sistema operativo para esta versión. |

### Requisitos

1. **Un entorno Pandora FMS con Discovery habilitado** para ejecutar la tarea y una consola para definirla.
2. **Uno o varios appliances Citrix NetScaler ADC** con la API de estadísticas NITRO accesible desde el entorno que ejecuta el addon, por HTTP o HTTPS.
3. **Una credencial con acceso de lectura a la API de estadísticas NITRO**, almacenada en el almacén de credenciales de Pandora FMS y seleccionada en la tarea.
4. **Un grupo de agentes de destino y un intervalo de monitorización** para los agentes generados, tomados de la tarea de Discovery.
5. **Acceso TLS según lo requiera el appliance.** La verificación del certificado es opcional y está desactivada por defecto; actívela cuando el certificado del appliance se pueda validar, o déjela desactivada para un certificado autofirmado de confianza.

El addon se distribuye como una aplicación de Discovery de Pandora FMS (paquete `.disco`) que la consola carga y el servidor de Discovery ejecuta. No hay que instalar ningún runtime adicional para una ejecución normal de la tarea.

### Instalación del addon

Cargue el paquete `.disco` desde **Management → Discovery → Extension manager** (la vista *Manage disco packages*). Una vez cargado, **Citrix NetScaler** aparece en la categoría **Applications** del asistente de Discovery.

## Configuración de la tarea de Discovery

Cree la tarea desde **Management → Discovery → Applications → Citrix NetScaler**. El primer paso genérico define la tarea; el paquete añade **Citrix NetScaler Base** y **Citrix NetScaler Detailed**. Todos los campos se documentan en [Parámetros de la tarea](#parametros-de-la-tarea).

**Paso 1 - Definición de la tarea.** Nombre, grupo de agentes, servidor de Discovery e intervalo. El ID del grupo y el intervalo se pasan al addon y se aplican a todos los agentes generados.

**Paso 2 - Citrix NetScaler Base.** A qué conectarse y cómo:

- **NetScaler targets** es la lista de URL de la API de estadísticas NITRO que se van a monitorizar, separadas por comas o una por línea. Las líneas que empiezan por `#` son comentarios. Un destino sin esquema usa HTTPS. A un destino sin la ruta `/nitro/v1/stat` se le añade esa ruta. Añada `|AgentName` para sobrescribir el nombre del agente del appliance generado para ese destino.
- **NetScaler Credentials** selecciona una credencial del almacén de credenciales de Pandora FMS. La credencial debe contener un usuario y una contraseña con acceso de lectura a la API de estadísticas NITRO.
- **Verify SSL certificate** activa la verificación del certificado TLS. Está desactivada por defecto, lo que permite certificados autofirmados del appliance.
- **Connection timeout** es el tiempo máximo en segundos permitido para establecer la conexión. El valor por defecto es `10`.
- **Read timeout** es el tiempo máximo en segundos permitido para esperar cada respuesta de la API. El valor por defecto es `30`.
- **Enable debug** escribe trazas de ejecución y de llamadas a la API, y **Debug log directory** (por defecto `/tmp`) es el directorio donde se guardan. El campo del directorio solo se muestra cuando la depuración está activada.

**Paso 3 - Citrix NetScaler Detailed.** Ejecución, estructura de agentes y familias de recursos que se recopilan:

- **Max threads** distribuye los appliances configurados entre trabajadores paralelos.
- **Agent prefix** se antepone al nombre de todos los agentes generados.
- **Custom module prefix** se antepone al nombre de todos los módulos generados.
- **Create agent per virtual server** crea un agente por cada servidor virtual de balanceo de carga y por cada servidor virtual GSLB. Está activado por defecto. Cuando se desactiva, sus módulos se añaden al agente del appliance.
- **Autodisabled agents** crea los agentes generados en modo deshabilitado, de modo que permanecen inactivos hasta que se habilitan en la consola.
- Los interruptores de **Monitoring modules** seleccionan las familias de recursos recopiladas: estadísticas del sistema, estadísticas de alta disponibilidad, servidores virtuales de balanceo de carga, servidores virtuales GSLB, servicios, grupos de servicios e interfaces de red. Todos están activados por defecto excepto los servidores virtuales GSLB.
- **Rename default modules** y **Modules names** permiten sustituir las etiquetas de módulo por defecto con un bloque `[MODULE_NAMES]`. El renombrado está desactivado por defecto.

![Paso Detailed de la tarea Citrix NetScaler Discovery: estructura de agentes, interruptores de monitorización y renombrado de módulos.](../assets/images/discovery/citrix-netscaler/detailed-step.png)

## Verificación de la primera ejecución

Fuerce la tarea desde **Management → Discovery → Task list** y compruebe el resultado en este orden.

1. **El resultado de la tarea** muestra los agentes generados y los recursos encontrados:

    - **Total agents**: agentes de appliance más agentes de servidor virtual.
    - **Targets up** y **Targets down**: appliances configurados que respondieron o que no respondieron.
    - **Virtual servers**: servidores virtuales de balanceo de carga y GSLB encontrados.
    - **Services**, **Service groups** e **Interfaces**: recursos encontrados en esas familias.

2. **Los agentes.** Aparece un agente de appliance por cada destino accesible. Con **Create agent per virtual server** activado, aparece un agente hijo por cada servidor virtual de balanceo de carga y GSLB. Un destino al que no se puede acceder se cuenta en **Targets down** y aun así genera un agente de appliance cuyo módulo **Connection Status** informa de `0`.

3. **Los módulos del appliance.** Un appliance accesible contiene el estado de la conexión, los módulos de sistema seleccionados en la tarea, los módulos de alta disponibilidad cuando el objeto de estadísticas `ns` está disponible, y los módulos de servicios, grupos de servicios e interfaces seleccionados en la tarea.

4. **Los módulos de servidor virtual.** Cada agente de servidor virtual contiene los módulos de estado y tráfico de su servidor virtual. Cuando **Create agent per virtual server** está desactivado, esos módulos aparecen en el agente del appliance con `Virtual server <name>` o `GSLB virtual server <name>` como prefijo.

![Resultado de la tarea Citrix NetScaler Discovery con agentes generados, destinos y recuentos de recursos.](../assets/images/discovery/citrix-netscaler/task-summary.png)

## Interpretación de los resultados

### Agentes e identidad

El addon crea un agente de appliance por cada destino configurado. Su nombre es **Agent prefix** seguido del nombre sobrescrito del destino, del hostname del appliance informado por la API NITRO, o del host del destino cuando no se puede leer el hostname. Su dirección es el host del destino, su sistema operativo es `NetScaler` y su versión es la versión de firmware y el build informados por el appliance cuando la configuración `ns` es legible. El agente pertenece al grupo de la tarea y hereda su intervalo.

Con **Create agent per virtual server** activado, el addon también crea un agente hijo por cada servidor virtual de balanceo de carga y por cada servidor virtual GSLB. El nombre del agente hijo es **Agent prefix** seguido del nombre del servidor virtual, y su padre es el agente del appliance. Si dos agentes generados fueran a compartir nombre, el addon añade el tipo de entidad y un contador para mantenerlos distintos.

Cambiar **Agent prefix** cambia los nombres de los agentes generados. Los agentes anteriores no se renombran ni se eliminan automáticamente.

Un destino al que no se puede acceder aun así genera un agente de appliance cuyo módulo **Connection Status** informa de `0`. El error de conexión se registra en la información de la tarea. Como en esa situación no se puede leer el hostname del appliance, el nombre del agente usa el host del destino y puede diferir del nombre usado en una ejecución correcta.

### Módulos por agente

| Agente | Se crea cuando | Módulos que contiene |
| --- | --- | --- |
| Agente de appliance | Hay un destino configurado, tanto si la conexión funciona como si no | Estado de la conexión, identidad del firmware, estadísticas del sistema, estadísticas de alta disponibilidad, servicios, grupos de servicios e interfaces de red, según los interruptores activados |
| Agente de servidor virtual de balanceo de carga | **Create agent per virtual server** está activado y la API NITRO devuelve un servidor virtual de balanceo de carga | Estado, salud, conexiones, tasas de peticiones y respuestas, tasas de bytes, totales, sesiones de persistencia, surge count y recuentos de servicios |
| Agente de servidor virtual GSLB | **Create agent per virtual server** está activado y la API NITRO devuelve un servidor virtual GSLB | Estado, salud, conexiones, tasa de peticiones y total de peticiones |

Los nombres de los módulos llevan el prefijo **Custom module prefix**. Las etiquetas de módulo por defecto y los grupos a los que pertenecen se enumeran en [Módulos y agentes generados](#modulos-y-agentes-generados).

![Lista de módulos del agente de appliance Citrix NetScaler.](../assets/images/discovery/citrix-netscaler/modules.png)

![Agentes Citrix NetScaler generados por la tarea de Discovery.](../assets/images/discovery/citrix-netscaler/agents.png)

### Dashboard Citrix NetScaler

La extensión **Dashboard Citrix NetScaler** es un panel de consola que lee los agentes y módulos creados por este plugin. No consulta el appliance: solo muestra los datos ya recopilados en Pandora FMS. Aparece en el menú **Monitoring** como **Citrix NetScaler** y está disponible con permiso de lectura de agentes (`AR` o `RR`).

El panel presenta:

- **Tarjetas de resumen** de los appliances, servidores virtuales de balanceo de carga, servidores virtuales GSLB, servicios, grupos de servicios e interfaces de red seleccionados.
- **Gráficas** del estado de los servidores virtuales, de los servidores virtuales con más conexiones de cliente y del estado de los servicios.
- **Un panel por appliance** con el estado de la conexión, CPU, memoria, uso de disco, uptime y número de serie, una gráfica de evolución del uso del sistema, una tabla de servicios, una tabla de interfaces de red y una tabla de grupos de servicios.
- **Un panel por servidor virtual** con su estado, salud, conexiones, tasas de peticiones y totales, gráficas de evolución de las métricas disponibles y una tabla de valores actuales.

Un filtro lateral acota la vista por **Agents**, **Resource type**, **State**, **Evolution period** y **Top results**. El filtro de estado se aplica a los estados de servidores virtuales y servicios. El panel necesita los marcadores `extra_data` que escribe el plugin de Discovery; los agentes creados antes de añadir el marcador deben refrescarse volviendo a ejecutar la tarea. La extensión se instala por separado en la consola y no necesita credenciales ni acceso NITRO adicionales.

## Operación

### Ejecución manual

El addon puede ejecutarse fuera de una tarea de Discovery con un fichero de configuración y un fichero de destinos:

```bash
./pandora_citrix_netscaler --conf <PATH_TO_CONFIG> --targets <PATH_TO_TARGETS>
```

El fichero de configuración y el fichero de destinos se describen en [Fichero de configuración](#fichero-de-configuracion) y [Fichero de destinos](#fichero-de-destinos). El addon imprime un documento JSON con el resumen, los agentes y módulos generados, y un campo `info` cuando se registran errores. El código de salida es `1` cuando un error de configuración impide la ejecución.

El fichero de configuración contiene el material de la credencial generado por la consola a partir de la credencial seleccionada. Protéjalo con permisos restrictivos y manténgalo fuera de directorios compartidos, logs y control de versiones.

### Logs de depuración

Con **Enable debug** activado, el addon escribe `pandora_citrix_netscaler_debug.log` en **Debug log directory** (por defecto `/tmp`). El log registra cada petición NITRO, los objetos de estadísticas que expone el appliance y los errores de conexión. La depuración es una ayuda de diagnóstico; déjela desactivada en las ejecuciones normales.

### Timeouts y recuperación de conexión

**Connection timeout** y **Read timeout** limitan cada petición. Cuando la conexión inicial con un destino falla o agota el tiempo, el destino se informa en **Targets down** y su agente de appliance mantiene **Connection Status** en `0`. Los demás destinos continúan de forma independiente. Una familia de recursos que falla dentro de un appliance accesible se registra como advertencia en la información de la tarea y no detiene las demás familias.

## Resolución de problemas

| Síntoma | Comprobación |
| --- | --- |
| La tarea falla con `Parameter [credentials] not defined or invalid` | Seleccione una credencial en **NetScaler Credentials**. La credencial debe contener un usuario y una contraseña. |
| La tarea falla con `NetScaler targets not defined` | Añada al menos una URL válida de la API de estadísticas NITRO en **NetScaler targets**. |
| Un destino se informa como **Targets down** y su **Connection Status** es `0` | Confirme que el appliance es accesible desde el entorno que ejecuta el addon, que la URL resuelve, que la API de estadísticas NITRO está habilitada y que la credencial se acepta. |
| La tarea informa de un error de autenticación | Confirme el usuario y la contraseña de la credencial, que la cuenta puede leer la API de estadísticas NITRO y que el appliance acepta autenticación por cabecera o por sesión. |
| La tarea informa de un error SSL | Active o desactive **Verify SSL certificate** según el certificado del appliance, o instale la autoridad de certificación usada por el appliance. |
| Faltan módulos GSLB esperados | Active **Retrieve GSLB virtual servers** y confirme que el appliance expone el objeto de estadísticas `gslbvserver`. |
| Faltan módulos de alta disponibilidad esperados | Confirme que el appliance expone el objeto de estadísticas `ns` y que la alta disponibilidad está configurada. |
| Faltan la versión de firmware, el build o el número de serie | El appliance no permitió leer la configuración `ns`. El addon continúa con el resto de módulos. |
| Faltan módulos de sistema esperados | Confirme que el objeto de estadísticas `system` está disponible y que el firmware del appliance expone la estadística correspondiente. |
| Faltan módulos de servicio o de interfaz esperados | Confirme que el objeto de estadísticas correspondiente está disponible y devuelve al menos un recurso. |
| Un destino es lento o la tarea agota el tiempo | Reduzca **Connection timeout** y **Read timeout**, y confirme que el appliance responde a la API de estadísticas NITRO. |
| Los agentes generados aparecen deshabilitados | **Autodisabled agents** está activado. Habilite los agentes en la consola o desactive la opción y vuelva a ejecutar la tarea. |
| Quedan agentes antiguos tras cambiar la estructura o el prefijo | El addon no elimina agentes. Elimine los agentes obsoletos en la consola o mantenga un prefijo y una estructura estables. |

## Referencia

### Identidad del plugin

| Campo | Valor |
| --- | --- |
| Nombre corto | `pandorafms.citrix_netscaler` |
| Nombre mostrado | Citrix NetScaler |
| Versión | `1.0` |
| Sección | Applications |
| Flujo de trabajo principal | Tarea de Discovery |

### Parámetros de la tarea

La consola presenta los campos de la tarea en dos pasos después de la definición genérica. La columna de macro es el identificador usado en la configuración generada de la tarea.

#### Citrix NetScaler Base

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| NetScaler targets | `_nsTargets_` | textarea | - | Lista de URL de la API de estadísticas NITRO. Obligatorio. Separadas por comas o una por línea; `#` inicia un comentario; `|AgentName` sobrescribe el nombre del agente del appliance |
| NetScaler Credentials | `_credentials_` | select | - | Credencial del almacén de credenciales de Pandora FMS. Obligatorio |
| Verify SSL certificate | `_verifySSL_` | checkbox | desactivado | Activa la verificación del certificado TLS |
| Connection timeout | `_connectionTimeout_` | number | `10` | Segundos máximos para establecer la conexión |
| Read timeout | `_readTimeout_` | number | `30` | Segundos máximos de espera para cada respuesta de la API |
| Enable debug | `_debug_` | checkbox | desactivado | Escribe trazas de ejecución y de llamadas a la API |
| Debug log directory | `_debugDirectory_` | string | `/tmp` | Directorio del log de depuración. Solo se muestra cuando **Enable debug** está activado |

#### Citrix NetScaler Detailed

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Max threads | `_threads_` | number | `1` | Trabajadores que distribuyen los appliances configurados |
| Agent prefix | `_agentPrefix_` | string | - | Prefijo de todos los nombres de agente generados |
| Custom module prefix | `_prefixModuleName_` | string | - | Prefijo de todos los nombres de módulo generados |
| Create agent per virtual server | `_agentPerVServer_` | checkbox | activado | Crea un agente por cada servidor virtual de balanceo de carga y GSLB |
| Autodisabled agents | `_autodisabledAgents_` | checkbox | desactivado | Crea los agentes generados en modo deshabilitado |
| Retrieve system statistics | `_scanSystem_` | checkbox | activado | Recopila las estadísticas del sistema del appliance |
| Retrieve high availability statistics | `_scanHA_` | checkbox | activado | Recopila las estadísticas de alta disponibilidad |
| Retrieve load balancing virtual servers | `_scanLBVServer_` | checkbox | activado | Recopila servidores virtuales de balanceo de carga |
| Retrieve GSLB virtual servers | `_scanGSLBVServer_` | checkbox | desactivado | Recopila servidores virtuales GSLB |
| Retrieve services | `_scanService_` | checkbox | activado | Recopila servicios |
| Retrieve service groups | `_scanServiceGroup_` | checkbox | activado | Recopila grupos de servicios |
| Retrieve network interfaces | `_scanInterfaces_` | checkbox | activado | Recopila interfaces de red |
| Rename default modules | `_renameModules_` | checkbox | desactivado | Aplica las etiquetas de `[MODULE_NAMES]` |
| Modules names | `_ModulesNames_` | textarea | Mapeo por defecto | Bloque `[MODULE_NAMES]` que renombra los módulos por defecto. Solo se muestra cuando **Rename default modules** está activado |

### Fichero de configuración

La tarea de Discovery genera un fichero temporal `--conf` a partir de sus propios campos. Una ejecución manual lo proporciona directamente. El fichero tiene una sección `[CONF]` y una sección opcional `[MODULE_NAMES]`.

| Clave | Por defecto | Descripción |
| --- | --- | --- |
| `agents_group_id` | `10` | ID del grupo donde se crean los agentes generados |
| `interval` | `300` | Intervalo de monitorización en segundos, heredado por los agentes generados |
| `credentials` | Vacío | Material de la credencial generado por la consola a partir de la credencial seleccionada. Obligatorio |
| `threads` | `1` | Número de trabajadores paralelos entre los appliances configurados |
| `agent_prefix` | Vacío | Prefijo de todos los nombres de agente generados |
| `modules_prefix` | Vacío | Prefijo de todos los nombres de módulo generados |
| `verify_ssl` | `0` | Activa la verificación del certificado TLS |
| `connection_timeout` | `10` | Segundos máximos para establecer la conexión |
| `read_timeout` | `30` | Segundos máximos de espera para cada respuesta de la API |
| `agent_per_vserver` | `1` | Crea un agente por cada servidor virtual de balanceo de carga y GSLB |
| `autodisabled_agents` | `0` | Crea los agentes generados en modo deshabilitado |
| `scan_system` | `1` | Recopila estadísticas del sistema |
| `scan_ha` | `1` | Recopila estadísticas de alta disponibilidad |
| `scan_lbvserver` | `1` | Recopila servidores virtuales de balanceo de carga |
| `scan_gslbvserver` | `0` | Recopila servidores virtuales GSLB |
| `scan_service` | `1` | Recopila servicios |
| `scan_servicegroup` | `1` | Recopila grupos de servicios |
| `scan_interfaces` | `1` | Recopila interfaces de red |
| `rename_modules` | `0` | Aplica las etiquetas de `[MODULE_NAMES]` |
| `debug` | `0` | Escribe trazas de ejecución y de llamadas a la API |
| `debug_directory` | `/tmp` | Directorio del log de depuración |

La credencial se guarda en el fichero de configuración en la forma generada por la consola. Un fichero de configuración sin `credentials` puede usar las claves heredadas `user` y `password`; la tarea de Discovery siempre escribe `credentials`. Restrinja el fichero a la cuenta que ejecuta el addon y manténgalo fuera de directorios compartidos, logs y control de versiones.

### Fichero de destinos

El fichero `--targets` contiene una o varias URL de la API de estadísticas NITRO. Las entradas pueden estar separadas por comas o una por línea. Las líneas que empiezan por `#` se ignoran.

```text
https://ns1.example.com/nitro/v1/stat
https://ns2.example.com/nitro/v1/stat|NetScaler 2
# https://ns3.example.com/nitro/v1/stat
```

- Un destino sin esquema usa `https://`.
- A un destino sin la ruta `/nitro/v1/stat` se le añade esa ruta.
- `|AgentName` sobrescribe el nombre del agente del appliance para ese destino. El **Agent prefix** se sigue anteponiendo.

### Ejecución por línea de comandos

| Opción | Obligatoria | Descripción |
| --- | --- | --- |
| `--conf` | Sí | Ruta al fichero de configuración |
| `--targets` | Sí | Ruta al fichero de destinos |
| `--help`, `-h` | No | Muestra la ayuda del comando |

### Módulos y agentes generados

Los nombres de los módulos llevan el prefijo **Custom module prefix**; las etiquetas siguientes omiten ese prefijo. Los módulos de estado son `generic_proc` e informan de `1` cuando el estado es `UP` o `7`, y de `0` en caso contrario. Los contadores totales usan `generic_data_inc`; los indicadores usan `generic_data`; la identidad y las etiquetas de estado de alta disponibilidad usan `generic_data_string`.

**Agente de appliance**

| Grupo | Módulos por defecto | Unidad o notas |
| --- | --- | --- |
| Conexión | `Connection Status` | `1` cuando la API NITRO respondió, `0` en caso contrario |
| Identidad | `Version`, `Build`, `Serial Number` | Leídos de la configuración `ns` cuando está disponible |
| Sistema | `CPU Usage`, `Memory Usage`, `Disk 0 Usage`, `Disk 1 Usage` | `%` |
| Sistema | `CPU Count`, `Memory Size`, `Memory Used`, `Uptime` | `MB`, `s` |
| Sistema | `Network Receive Rate`, `Network Transmit Rate` | `Mbps` |
| Sistema | `Client Connections`, `Server Connections` | Conexiones en estado establecido |
| Sistema | `HTTP Requests Rate`, `SSL Transactions Rate` | `req/s`, `tx/s` |
| Sistema | `SSL Cards Up`, `SSL Cards`, `Power Supply 1` a `Power Supply 4` | Presentes solo cuando el appliance expone la estadística |
| Alta disponibilidad | `HA State`, `HA Node Status`, `HA Master State`, `HA Sync State`, `HA Sync Failures` | Presentes cuando el objeto de estadísticas `ns` está disponible |
| Servicios | `Service <name> State`, `Service <name> Client Connections`, `Service <name> Server Connections`, `Service <name> Requests Rate`, `Service <name> Responses Rate`, `Service <name> Surge Count`, `Service <name> Total Requests`, `Service <name> Active Transactions` | Hay módulos por cada servicio devuelto |
| Grupos de servicios | `Service group <name> State` | Un módulo por grupo de servicios |
| Interfaces de red | `Interface <id> Link State`, `Interface <id> RX Bytes Rate`, `Interface <id> TX Bytes Rate`, `Interface <id> RX Packets Rate`, `Interface <id> TX Packets Rate`, `Interface <id> RX Errors Rate`, `Interface <id> TX Errors Rate`, `Interface <id> Link Uptime` | Un grupo por interfaz |
| Servidores virtuales con **Create agent per virtual server** desactivado | `Virtual server <name> <module>`, `GSLB virtual server <name> <module>` | Usa las etiquetas de los agentes de servidor virtual |

**Agente de servidor virtual de balanceo de carga**

| Módulo por defecto | Tipo | Unidad |
| --- | --- | --- |
| `State` | `generic_proc` | |
| `Health` | `generic_data` | `%` |
| `Client Connections` | `generic_data` | conexiones |
| `Server Connections` | `generic_data` | conexiones |
| `Established Connections` | `generic_data` | conexiones |
| `Requests Rate` | `generic_data` | `req/s` |
| `Responses Rate` | `generic_data` | `resp/s` |
| `Request Bytes Rate` | `generic_data` | `B/s` |
| `Response Bytes Rate` | `generic_data` | `B/s` |
| `Total Requests` | `generic_data_inc` | peticiones |
| `Total Responses` | `generic_data_inc` | respuestas |
| `Persistence Sessions` | `generic_data` | sesiones |
| `Surge Count` | `generic_data` | peticiones |
| `Active Services` | `generic_data` | servicios |
| `Inactive Services` | `generic_data` | servicios |

**Agente de servidor virtual GSLB**

| Módulo por defecto | Tipo | Unidad |
| --- | --- | --- |
| `State` | `generic_proc` | |
| `Health` | `generic_data` | `%` |
| `Client Connections` | `generic_data` | conexiones |
| `Requests Rate` | `generic_data` | `req/s` |
| `Total Requests` | `generic_data_inc` | peticiones |

**Renombrar módulos por defecto.** El campo `Modules names` acepta un bloque `[MODULE_NAMES]`. Cada clave identifica un módulo por defecto y el valor sustituye su etiqueta. Las claves son los identificadores usados por el addon, por ejemplo `lbvserver_state`, `lbvserver_health`, `service_state` e `interface_state`. El mapeo por defecto viene precargado en el campo cuando el renombrado está activado.
