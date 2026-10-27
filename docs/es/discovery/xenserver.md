# XenServer Discovery

*Última actualización del artículo: 2026-10-26.*

## Qué monitoriza

El addon de Discovery de XenServer monitoriza los hosts, los repositorios de almacenamiento y las máquinas virtuales de un entorno XenServer. Una tarea de Discovery se conecta a un XenServer, lee su inventario y sus datos de rendimiento mediante la XenAPI y los datos RRD del servidor, y crea agentes y módulos de Pandora FMS con el resultado.

Una tarea de Discovery genera tres tipos de agentes:

- **Un agente por cada host**, con el número de máquinas virtuales en ejecución e instaladas, el uso de memoria y la carga media de CPU.
- **Un agente por cada máquina virtual**, con su estado de energía, uso de memoria, carga por CPU, estado de las herramientas del invitado y tamaño y rendimiento por disco. El agente de la máquina virtual es hijo del agente del host que la ejecuta.
- **Un agente por cada repositorio de almacenamiento (SR)**, con su tamaño físico, espacio usado, espacio libre y porcentaje de uso.

La tarea decide cuáles de los tres tipos se escanean, y los hosts, las máquinas virtuales y los repositorios de almacenamiento se pueden excluir o renombrar por nombre.

## Preparación

### Compatibilidad

| Alcance | Estado | Evidencia |
|---------|--------|-----------|
| Addon `pandorafms.xenserver`, versión `1.3` | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del addon](#identidad-del-addon) |
| XenServer `6.2` o superior | `Requerido` | Prerrequisito indicado por la entrada del Marketplace; no hay registro de pruebas para esta versión |
| Pandora FMS NG `784` y posteriores | Indicado por el Marketplace | Aviso general del Marketplace para todas las entradas, no específico de este addon |
| Sistema operativo del servidor de Discovery | `Sin validar` | No se ha registrado ningún sistema operativo para esta versión |
| Versiones concretas de XenServer | `Sin validar` | No se ha registrado una matriz de pruebas para esta versión |

### Prerrequisitos

1. **Un host XenServer** accesible desde el servidor de Discovery, con el puerto TCP `80` abierto para las consultas RRD y la conexión a la XenAPI. La entrada del Marketplace indica además el puerto TCP `443` para las consultas a la XenAPI.
2. **Credenciales de XenServer** (usuario y contraseña) capaces de consultar la XenAPI. Para este addon no se documenta un conjunto de roles o permisos más reducido.
3. **Pandora FMS**: el servidor de Discovery para ejecutar la tarea y la consola para definirla. Los agentes generados se envían con Tentacle.
4. **Herramientas del invitado** (guest tools) instaladas en las máquinas virtuales. Sin ellas la información del invitado es limitada: el agente de la máquina virtual no obtiene la dirección IP del invitado y el módulo `XenServer tools` informa `0`.

!!! warning
    El addon se conecta al XenServer con URL HTTP y envía el usuario y la contraseña en la autenticación básica HTTP de las peticiones RRD. Ejecútelo solo desde una red de confianza y use credenciales dedicadas a la monitorización.

El addon incluye su propio ejecutable, `bin/pandora_xenserver`, por lo que no hay que instalar nada más en el servidor de Discovery para ejecutar una tarea.

### Instalar el addon

Descargue el paquete `.disco` desde la entrada del Marketplace de Pandora FMS, cuya descarga está limitada a usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.xenserver](https://marketplace.pandorafms.com/entries/pandorafms.xenserver)

Cárguelo en Pandora FMS. Una vez cargado, **XenServer** está disponible en la sección **Applications** al crear tareas de Discovery.

## Configurar la tarea de Discovery

Cree la tarea desde las aplicaciones de Discovery y elija **XenServer**. La consola presenta los campos en dos pasos; cada campo se documenta en [Parámetros de la tarea](#parametros-de-la-tarea).

![Sección Applications de Discovery con la aplicación XenServer](../assets/images/discovery/xenserver/xenserver-discovery-applications.png)

1. **XenServer base** — conexión y entrega de datos:

    - **XenServer IP**, **XenServer user** y **Password**: dirección y credenciales del XenServer a monitorizar.
    - **ID as Name**: usa el identificador (UUID) del SR como nombre de los agentes de repositorio de almacenamiento. El alias sigue siendo el nombre del SR.
    - **Tentacle IP**, **Tentacle port** y **Tentacle extra options**: dónde y cómo se envían los datos de los agentes generados. Rara vez hay que cambiarlos.

    ![Paso XenServer base del asistente](../assets/images/discovery/xenserver/xenserver-base-step.png)

2. **XenServer detailed** — alcance y ajustes:

    - **Autodisabled agents**: crea los agentes en modo autodeshabilitado.
    - **Time adjustment**: segundos que se restan a la hora actual para fijar el inicio de la ventana de consulta RRD.
    - **Scan VM IP**, **Scan all Hosts**, **Scan all VM** y **Scan all SR**: qué datos recoge la tarea.
    - **Extra settings**: bloque opcional que se añade tal cual al final de la configuración del plugin. Úselo para las secciones `REJECT` y `RENAME` descritas en [Excluir y renombrar elementos](#excluir-y-renombrar-elementos).

    <!-- SCREENSHOT NEEDED: paso XenServer detailed del asistente con las opciones de escaneo y el área de texto Extra settings. -->

El grupo y el intervalo de la tarea proceden del paso genérico de definición de la tarea y se aplican a los agentes que esta crea.

## Verificar la primera ejecución

Fuerce la tarea desde la lista de tareas de Discovery y compruebe el resultado en este orden.

1. **El resumen de la tarea.** Una tarea que se completa correctamente informa de:

    - **Hosts**: hosts monitorizados.
    - **Storage**: repositorios de almacenamiento monitorizados.
    - **VMs**: máquinas virtuales monitorizadas, sin plantillas, instantáneas ni dominios de control. Un dominio de control es la máquina virtual especial que gestiona cada host.
    - **Hosts VMs running**: máquinas virtuales en ejecución en los hosts monitorizados, sin dominios de control. Se cuenta durante el escaneo de hosts, por lo que es `0` cuando **Scan all Hosts** está desactivado.

    Una tarea que no se completa correctamente registra los errores en su información de ejecución.

    <!-- SCREENSHOT NEEDED: resumen de ejecución de una tarea XenServer en Discovery con Hosts, Storage, VMs y Hosts VMs running. -->

2. **Los agentes.** Uno por host, uno por máquina virtual y uno por repositorio de almacenamiento, según las opciones de escaneo activadas.
3. **Los módulos.** Todo agente de máquina virtual tiene `Status`, `Memory used` y `XenServer tools`. Los módulos de CPU y de rendimiento de disco aparecen solo en máquinas virtuales en ejecución; consulte [Interpretar los resultados](#interpretar-los-resultados).

## Interpretar los resultados

### Agentes generados

| Agente | Nombre y alias | Padre | Notas |
|--------|----------------|-------|-------|
| Host | El nombre del host | Ninguno | La dirección es la del host. Sistema operativo `Xen Server`, versión: la marca y versión del producto que informa el host |
| Máquina virtual | El nombre de la máquina virtual | El host que la ejecuta, vacío si la máquina no reside en un host | La dirección es la lista de IP del invitado, separadas por comas, cuando **Scan VM IP** está activado y el invitado las informa |
| Repositorio de almacenamiento | Nombre: el UUID del SR con **ID as Name** activado, o el nombre del SR en caso contrario. Alias: siempre el nombre del SR | Ninguno | La descripción lista los hosts y el dispositivo o la ubicación del repositorio |

En los nombres de agente de host y de máquina virtual el carácter `/` se sustituye por `_`; los nombres de agente de repositorio de almacenamiento no se modifican. Las plantillas, las instantáneas y los dominios de control nunca se monitorizan como máquinas virtuales. Los repositorios de almacenamiento cuyo nombre contiene `XenServer Tools` o cuyo tamaño físico es `0` no generan agente.

### Módulos por agente

**Agente de host**

| Módulo | Tipo | Unidad | Descripción |
|--------|------|--------|-------------|
| `VMs running` | `generic_data` | | Máquinas virtuales en ejecución, sin el dominio de control |
| `VMs installed` | `generic_data` | | Máquinas virtuales residentes en el host, incluido el dominio de control |
| `Memory used` | `generic_data` | `%` | Porcentaje de RAM en uso |
| `Load CPU avg` | `generic_data` | `%` | Carga media de CPU |

**Agente de máquina virtual**

| Módulo | Tipo | Unidad | Condición | Descripción |
|--------|------|--------|-----------|-------------|
| `Status` | `generic_proc` | | Siempre | `1` cuando la máquina está en `Running`, `0` en otro caso. La descripción contiene el estado de energía |
| `Memory used` | `generic_data` | `%` | Siempre | Porcentaje de RAM en uso; `0.0` cuando la máquina no está en ejecución |
| `cpu<N>` | `generic_data` | `%` | En ejecución | Carga de cada CPU virtual |
| `XenServer tools` | `generic_proc` | | Siempre | `1` cuando el invitado informa de herramientas instaladas, `0` en otro caso |
| `VDI_<nombre del disco>_size` | `generic_data` | `GB` | Uno por disco conectado | Tamaño del disco tal como se presenta al invitado |
| `VDI_<nombre del disco>_used` | `generic_data` | `%` | Uno por disco conectado | Porcentaje del tamaño del disco que ocupa la imagen en el repositorio de almacenamiento, limitado a `100`. Los discos de aprovisionamiento grueso (thick) siempre informan `100` |
| `vbd_<dispositivo>_write`, `vbd_<dispositivo>_read` | `generic_data` | `bytes/sec` | En ejecución | Velocidad de escritura y de lectura de cada dispositivo de bloque virtual |

**Agente de repositorio de almacenamiento**

| Módulo | Tipo | Unidad | Descripción |
|--------|------|--------|-------------|
| `physical_size` | `generic_data` | `GB` | Tamaño físico del repositorio |
| `physical_utilisation` | `generic_data` | `GB` | Espacio físico en uso |
| `free space` | `generic_data` | `GB` | Espacio libre, como número entero de GB |
| `used percent` | `generic_data` | `%` | Porcentaje del repositorio en uso |

### Cómo se obtienen los valores

- Los datos de inventario proceden de la XenAPI. La memoria, la CPU y el rendimiento de disco proceden de los datos RRD del XenServer, consultados desde el instante que fija **Time adjustment** (por defecto `10` segundos antes de la ejecución).
- Cada ejecución vuelve a crear los datos de todos los elementos seleccionados; los hosts, máquinas virtuales y repositorios de almacenamiento nuevos se incluyen en la siguiente ejecución sin cambiar la tarea.

## Excluir y renombrar elementos

Incluya estas secciones en **Extra settings** (o en el fichero de configuración en la ejecución manual). Los nombres son los del host, la máquina virtual o el repositorio de almacenamiento; un nombre que contiene `/` se escribe con `_`.

```ini
[REJECT]
<NOMBRE_ELEMENTO> = 1
regexp_host = <REGEX>
regexp_vm = <REGEX>
regexp_sr = <REGEX>

[RENAME]
<NOMBRE_ELEMENTO> = <NUEVO_NOMBRE>
```

- `<NOMBRE_ELEMENTO> = 1` excluye ese host, máquina virtual o repositorio de almacenamiento. En un repositorio de almacenamiento el nombre es el nombre del SR, no su UUID.
- `regexp_host`, `regexp_vm` y `regexp_sr` excluyen todo elemento cuyo nombre coincida con la expresión regular desde el inicio del nombre. En los repositorios de almacenamiento la expresión se compara con el nombre del agente, es decir, con el UUID cuando **ID as Name** está activado.
- `RENAME` cambia el nombre del agente. En hosts y máquinas virtuales cambia también el alias; los repositorios de almacenamiento conservan el nombre del SR como alias.

## Operación

### Ejecución manual

El addon puede ejecutarse fuera de una tarea de Discovery. El ejecutable recibe la ruta a un fichero de configuración descrito en [Fichero de configuración](#fichero-de-configuracion):

```bash
./pandora_xenserver --conf <PATH_TO_CONFIG>
```

Añada `--as_discovery_plugin 1` para imprimir el resumen de ejecución en JSON en lugar de un módulo de estado:

```bash
./pandora_xenserver --conf <PATH_TO_CONFIG> --as_discovery_plugin 1
```

```json
{"summary": {"Hosts": 1, "Storage": 7, "VMs": 23, "Hosts VMs running": 10}}
```

Cuando se producen errores, el JSON contiene además una clave `info` con los mensajes y el código de salida es `1`. Sin `--as_discovery_plugin 1`, una ejecución correcta imprime un módulo de estado:

```xml
<module>
<name><![CDATA[XenServer Plugin]]></name>
<type><![CDATA[async_string]]></type>
<description><![CDATA[Result of XenServer Plugin execution]]></description>
<data><![CDATA[OK]]></data>
</module>
```

En el modo de transferencia `local` los ficheros de datos se mueven a `data_dir`. En el modo `tentacle` el ejecutable `tentacle_client` debe estar disponible en el `PATH` del usuario que ejecuta el addon.

El `interval` del fichero de configuración es el intervalo de los agentes generados. Debe coincidir con el intervalo de ejecución del plugin; en caso contrario los módulos pasan a `unknown` cuando un agente espera datos antes de la siguiente ejecución.

El fichero de configuración contiene la contraseña del XenServer en texto plano. Protéjalo con permisos restrictivos.

## Solución de problemas

El addon no tiene opción de modo detallado ni de depuración. Su canal de diagnóstico es el campo `info` del resultado JSON de la ejecución, que se muestra en la información de ejecución de la tarea, y el fichero de log indicado en `logfile` en la ejecución manual.

- **`CRITICAL: Cant get XenServer session`** o **`CRITICAL: Cant login to XenServer`**: falló la conexión o el inicio de sesión. El mensaje incluye el error recibido. Compruebe **XenServer IP**, las credenciales y que el puerto `80` es accesible desde el servidor de Discovery.
- **`ERROR - Could not write file`**: el directorio de los ficheros de datos temporales no es escribible.
- **`Tentacle error`**: no se pudo enviar el fichero de datos. El mensaje incluye el error del cliente de Tentacle; compruebe **Tentacle IP** y **Tentacle port**.
- **Un agente de máquina virtual no tiene dirección IP**: **Scan VM IP** está desactivado, o el invitado no informa de direcciones porque no tiene instaladas las herramientas del invitado.
- **No hay módulos `cpu<N>` ni `vbd_` en una máquina virtual**: la máquina no está en ejecución.
- **Un repositorio de almacenamiento no tiene agente**: su tamaño físico es `0`, su nombre contiene `XenServer Tools`, **Scan all SR** está desactivado o coincide con una regla `REJECT`.
- **Menos agentes de los esperados**: compruebe cuáles de **Scan all Hosts**, **Scan all VM** y **Scan all SR** están activados, y las reglas `REJECT`.

## Referencia

### Parámetros de la tarea

#### XenServer base

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|-------------|-------|
| XenServer IP | `_serverIP_` | cadena | — | Dirección del XenServer |
| XenServer user | `_user_` | cadena | — | Usuario del XenServer |
| Password | `_password_` | contraseña | — | Contraseña del usuario |
| ID as Name | `_idAsName_` | casilla | activada | UUID del SR como nombre del agente de repositorio de almacenamiento |
| Tentacle IP | `_tentacleIP_` | cadena | `127.0.0.1` | Servidor que recibe los datos de los agentes |
| Tentacle port | `_tentaclePort_` | número | `41121` | Puerto de Tentacle |
| Tentacle extra options | `_tentacleExtraOpt_` | cadena | — | Opcional. Opciones adicionales del cliente de Tentacle |

#### XenServer detailed

| Campo | Macro | Tipo | Por defecto | Notas |
|-------|-------|------|-------------|-------|
| Autodisabled agents | `_autodisabledAgents_` | casilla | desactivada | Crea los agentes en modo autodeshabilitado |
| Time adjustment | `_timeAdjustment_` | número | `10` | Opcional. Segundos que se restan a la hora actual para fijar el inicio de la ventana de consulta RRD |
| Scan VM IP | `_scanVMIP_` | casilla | activada | Lee las direcciones IP de las máquinas virtuales |
| Scan all Hosts | `_scanAllHosts_` | casilla | activada | Crea agentes de host |
| Scan all VM | `_scanAllVM_` | casilla | activada | Crea agentes de máquina virtual |
| Scan all SR | `_scanAllSR_` | casilla | activada | Crea agentes de repositorio de almacenamiento |
| Extra settings | `_extraSettings_` | área de texto | — | Opcional. Bloque en bruto que se añade al final de la configuración del plugin |

### Fichero de configuración

Se usa en la ejecución manual. La tarea de Discovery genera el mismo fichero a partir de sus campos, con `transfer_mode = tentacle`, el grupo y el intervalo de la tarea, y `data_dir` fijado por el servidor de Discovery. Todas las claves de `CONF` y `PANDORA` excepto `id_as_name` y `autodisabled_agents` son obligatorias; las claves de `TUNNING` y `REJECT` son opcionales. Las opciones numéricas aceptan `1` para activar y `0` para desactivar.

| Sección | Clave | Por defecto | Descripción |
|---------|-------|-------------|-------------|
| `CONF` | `xen_server_ip` | — | Dirección del XenServer |
| `CONF` | `user` | — | Usuario del XenServer |
| `CONF` | `password` | — | Contraseña del XenServer |
| `CONF` | `temporal` | — | Directorio de ficheros temporales |
| `PANDORA` | `group` | — | Grupo de los agentes generados |
| `PANDORA` | `logfile` | — | Fichero de log. Se sobrescribe en cada ejecución |
| `PANDORA` | `interval` | — | Intervalo de los agentes, en segundos. Debe coincidir con el intervalo de ejecución |
| `PANDORA` | `transfer_mode` | — | `local` mueve los ficheros de datos a `data_dir`; cualquier otro valor los envía con Tentacle |
| `PANDORA` | `tentacle_client` | — | Ejecutable del cliente de Tentacle. Esta versión lee el valor pero no lo utiliza: el comando siempre ejecuta `tentacle_client` del `PATH` del servidor Discovery |
| `PANDORA` | `tentacle_ip` | — | Dirección del servidor de Tentacle |
| `PANDORA` | `tentacle_port` | — | Puerto del servidor de Tentacle |
| `PANDORA` | `tentacle_opts` | — | Opciones adicionales del cliente de Tentacle; puede estar vacía |
| `PANDORA` | `data_dir` | — | Destino de los ficheros de datos en modo `local` |
| `PANDORA` | `id_as_name` | `1` | UUID del SR como nombre del agente de repositorio de almacenamiento |
| `PANDORA` | `autodisabled_agents` | `0` | Modo autodeshabilitado |
| `TUNNING` | `time_adjustment` | `10` | Segundos que se restan a la hora actual para fijar el inicio de la ventana de consulta RRD |
| `TUNNING` | `scan_vm_ip` | `1` | Leer las direcciones IP de las máquinas virtuales |
| `TUNNING` | `scan_all_host` | `1` | Crear agentes de host |
| `TUNNING` | `scan_all_vm` | `1` | Crear agentes de máquina virtual |
| `TUNNING` | `scan_all_sr` | `1` | Crear agentes de repositorio de almacenamiento |
| `REJECT`, `RENAME` | | | Consulte [Excluir y renombrar elementos](#excluir-y-renombrar-elementos) |

Ejemplo:

```ini
[CONF]
xen_server_ip = <XENSERVER_IP>
user = <USERNAME>
password = <PASSWORD>
temporal = /tmp

[PANDORA]
group = Unknown
logfile = /tmp/pandora_xenserver.log
interval = 300
transfer_mode = tentacle
tentacle_client = tentacle_client
tentacle_ip = <TENTACLE_SERVER_IP>
tentacle_port = 41121
tentacle_opts =
data_dir = /tmp/data_in
id_as_name = 1

[TUNNING]
time_adjustment = 10
scan_vm_ip = 1
scan_all_vm = 1
scan_all_sr = 1
scan_all_host = 1

[REJECT]
<VM_NAME> = 1

[RENAME]
<VM_NAME_2> = <NEW_NAME>
```

### Identidad del addon

| Elemento | Valor |
|----------|-------|
| Nombre | XenServer |
| Identificador | `pandorafms.xenserver` |
| Versión | `1.3` |
| Tipo y sección | Discovery, `app` |
| Entrada del Marketplace | [pandorafms.xenserver](https://marketplace.pandorafms.com/entries/pandorafms.xenserver), actualizada el 2026-09-16 |
| Disponibilidad | La entrada del Marketplace indica que la descarga está limitada a usuarios con licencia |
