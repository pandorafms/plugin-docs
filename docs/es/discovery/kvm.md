# Discovery de KVM

*Última actualización del artículo: 2026-10-19.*

## Qué monitoriza

El plugin de Discovery de KVM se conecta a hipervisores KVM y lee su inventario y su estado a través de `virsh` y `ps`, ya sea por SSH o localmente en la máquina que ejecuta la tarea. Crea una jerarquía de dos niveles de agentes en Pandora FMS:

- un agente por cada host KVM, con el nombre `KVM <host>`;
- un agente por cada máquina virtual, con el nombre `<vm> (<host>)` y creado como hijo de su agente del host.

Los agentes del host llevan el estado de libvirtd y, cuando **Monitor KVM server performance** está activado, el uso de RAM y de CPU del servidor KVM, incluido su consumo de RAM en bytes. Los agentes de máquina virtual llevan el estado de encendido de la VM y, para las VM en ejecución, el número de vCPU asignadas, el uso de CPU por vCPU, el uso de memoria en porcentaje y el consumo de memoria en bytes. El uso de CPU es un valor instantáneo, no un contador acumulado: el plugin muestrea `virsh domstats --vcpu` dos veces alrededor de una ventana de un segundo y traduce el delta de tiempo de vCPU a un porcentaje por vCPU. Para las VM en ejecución, el plugin también resuelve la dirección IPv4 de la VM con `virsh domifaddr` y la usa como dirección del agente cuando está disponible. El plugin solo genera datos de Discovery; la tarea se vuelve a ejecutar en su intervalo configurado para refrescar el inventario y los valores de los módulos.

El plugin se ejecuta como una tarea de Discovery: la consola crea la tarea, el servidor de Discovery ejecuta el plugin y los agentes y módulos generados se crean automáticamente.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Versión del plugin `1.0` (`pandorafms.kvm`) | Objetivo documentado | Versión descrita en esta página, identificada por la definición del paquete. |
| Un servidor Pandora FMS con Discovery habilitado | `Requerido` | La integración se ejecuta como una tarea de Discovery creada desde la consola. |
| libvirt con `virsh` en cada host monitorizado | `Requerido` | Todas las métricas se leen a través de `virsh`, y la comprobación del proceso libvirtd decide si un host está activo. |
| Acceso SSH a cada destino remoto | `Requerido` | Los destinos remotos se monitorizan por SSH en el puerto configurado; solo los destinos `local` se ejecutan sin él. |
| Una distribución Linux, una versión de KVM o de libvirt de los hosts monitorizados | `Sin validar` | Ningún registro de pruebas publicado establece compatibilidad con una distribución o una versión de libvirt concretas. |
| Sistema operativo del servidor que ejecuta la tarea | `Sin validar` | Ningún registro de pruebas publicado establece compatibilidad con sistemas operativos. |

### Requisitos

- Un servidor Pandora FMS con Discovery habilitado para ejecutar la tarea y una consola para definirla.
- En cada host KVM monitorizado: libvirt instalado con el comando `virsh` disponible y el demonio **libvirtd** en ejecución. Un host sin libvirtd se genera igualmente, con `KVM Server status = 0` y sin módulos de rendimiento ni de máquinas virtuales.
- Una cuenta SSH en cada host remoto con permiso para ejecutar `ps` y `virsh`. La lectura de libvirt requiere normalmente pertenecer al grupo `libvirt` o ser `root`.
- Para la autenticación **SSH key**: una clave privada legible por el usuario que ejecuta la tarea de Discovery, con su clave pública instalada en cada host monitorizado. Opcionalmente, un archivo `known_hosts` con las claves de host de esos hosts para habilitar la verificación de claves de host.
- Para la autenticación **Pandora credentials**: una credencial personalizada en el gestor de credenciales de Pandora que almacene el usuario y la contraseña de SSH.
- Un grupo de agentes de destino y un intervalo de monitorización para los agentes generados. Ambos proceden de la tarea de Discovery y los hereda cada agente generado.
- Un destino `local` ejecuta `ps` y `virsh` en la máquina que ejecuta la tarea, así que úsalo solo cuando la tarea se ejecute en el propio host KVM.
- Accesibilidad de red desde el servidor de Discovery a cada host remoto en el puerto SSH. Con **Transfer mode** en `tentacle`, el destino de Tentacle configurado también debe ser accesible.
- El plugin se distribuye como una aplicación de Discovery de Pandora FMS (paquete `.disco`) que el servidor de Discovery ejecuta en el servidor Pandora FMS.

### Instalar el plugin

**Desde el Marketplace.** Abre **Marketplace → Search** en la consola, localiza la entrada de KVM Discovery y haz clic en **Install**. La instalación requiere un usuario administrador. El paquete se instala directamente y **KVM** aparece en la sección **Applications** del asistente de Discovery.

<!-- SCREENSHOT NEEDED: la entrada de KVM Discovery en el Marketplace de la consola (vista Search y botón Install), a capturar cuando el plugin se publique en el Marketplace -->

**Instalación manual.** Carga el paquete `.disco` desde **Management → Discovery → Manage disco packages**: elige **Select a file**, selecciona el paquete y haz clic en **Upload DISCO**. Una vez cargado, **KVM** aparece en la lista de paquetes y en la sección **Applications** del asistente de Discovery.

![Página Manage disco packages con el paquete de Discovery de KVM instalado](../assets/images/discovery/kvm/manage-disco-packages.png)

![Aplicación KVM disponible en las aplicaciones de Discovery](../assets/images/discovery/kvm/applications-kvm.png)

## Configurar la tarea de Discovery

Crea la tarea desde **Management → Discovery → Applications → KVM**. El asistente recorre la definición genérica de la tarea y tres pasos del plugin: **KVM Connection**, **Authentication** y **KVM Monitoring Options**. Todos los campos se documentan en [Parámetros de la tarea](#parametros-de-la-tarea).

### Paso 1 — Definición de la tarea

El paso genérico solicita el **nombre** de la tarea, el **grupo de agentes** y el **servidor** en el que se ejecuta, y el **intervalo**. El grupo y el intervalo se pasan al plugin y los hereda cada agente generado.

### Paso 2 — KVM Connection

La lista de destinos y los datos de conexión:

- **KVM hosts** es la lista de destinos, con una entrada por línea; también se aceptan valores separados por comas dentro de una línea. Se requiere al menos una entrada. Cada entrada es `user@host`, `host` o `local`:
  - `user@host` conecta con `host` por SSH como `user`, lo que tiene prioridad sobre el usuario de autenticación configurado;
  - `host` conecta con `host` por SSH con el usuario SSH por defecto (modo de clave) o con el usuario de la credencial (modo de credenciales);
  - `local` ejecuta `ps` y `virsh` en la máquina que ejecuta la tarea y no usa autenticación.
- **SSH port** es el puerto SSH usado para conectar con los hosts remotos. Por defecto `22`.
- **Command timeout** es el tiempo de espera de la conexión SSH y de los comandos, en segundos. Por defecto `10`.
- **Authentication mode** selecciona cómo se autentica el plugin: **SSH key** o **Pandora credentials**. El paso siguiente muestra los campos del modo seleccionado.

![Paso KVM Connection del asistente de la tarea de Discovery](../assets/images/discovery/kvm/step-kvm-connection.png)

### Paso 3 — Authentication

Los campos de este paso dependen del **Authentication mode** seleccionado en el paso anterior.

En modo **SSH key**:

- **SSH private key path** es la ruta de la clave privada SSH en el servidor Pandora, legible por el usuario que ejecuta la tarea de Discovery. Obligatorio en este modo.
- **Default SSH user** es el usuario usado para los destinos sin un prefijo `user@` explícito. La parte `user@` de un destino tiene prioridad sobre él.
- **SSH known_hosts file**: cuando se establece, la clave de host de cada destino se verifica contra este archivo y los hosts desconocidos se rechazan. Cuando está vacío, se aceptan las claves de host desconocidas.

![Paso Authentication en modo de clave SSH](../assets/images/discovery/kvm/step-authentication-key.png)

En modo **Pandora credentials**:

- **Pandora credentials** es la credencial personalizada seleccionada del gestor de credenciales de Pandora. Obligatoria en este modo.
- **SSH known_hosts file** se comporta igual que en el modo de clave.

![Paso Authentication con una credencial personalizada de Pandora](../assets/images/discovery/kvm/step-authentication-credentials.png)

### Paso 4 — KVM Monitoring Options

Qué monitoriza la tarea y cómo se entregan los datos:

- **Monitor KVM server performance**, cuando está activado, añade los módulos `KVM Server RAM usage (%)`, `KVM Server RAM consumption (bytes)` y `KVM Server CPU usage (%)` al agente del host. El módulo `KVM Server status` se crea siempre.
- **Monitor virtual machines**, cuando está activado, crea un agente por cada máquina virtual y el módulo `Number of VMs` en el agente del host.
- **Allow list** es una expresión regular aplicada a los nombres de las VM: solo las VM que coinciden reciben un agente. Vacío permite todas las VM.
- **Deny list** es una expresión regular aplicada a los nombres de las VM después de la allow list: las VM que coinciden se excluyen. Vacío no excluye ninguna VM.
- **Transfer mode** selecciona cómo llegan los datos generados a Pandora FMS. `native` permite que el servidor de Discovery lea directamente los datos de los agentes; `tentacle` envía los archivos de agente generados a **Tentacle IP** en **Tentacle port** con el cliente de Tentacle.
- **Tentacle IP** y **Tentacle port** son el destino de Tentacle usado en el modo `tentacle`. Por defecto `127.0.0.1` y `41121`.

![Paso KVM Monitoring Options con los interruptores de monitorización y la configuración de transferencia](../assets/images/discovery/kvm/step-monitoring-options.png)

## Verificar la primera ejecución

Ejecuta la tarea desde **Management → Discovery → Task list** y comprueba el resultado en este orden.

1. **El resumen de la tarea** muestra el progreso general y un resumen con `Total Targets`, `Total Agents` y `Total Modules`.
2. **Los agentes.** Espera un agente del host (`KVM <host>`) por cada destino accesible, más un agente por cada máquina virtual monitorizada, creado como hijo de su agente del host.
3. **Los módulos.** Un host con libvirtd en ejecución incorpora `KVM Server status` y, según las opciones activadas, los módulos de rendimiento del servidor y `Number of VMs`. Cada agente de máquina virtual incorpora `Status of <vm>`; una VM en ejecución incorpora además sus módulos de vCPU y de memoria.
4. **La información de ejecución.** Una ejecución correcta no registra errores; los fallos de conexión o de comando, y el motivo por el que se omitió un módulo, se registran ahí.

![Resumen de la tarea de Discovery con 2 agentes y 10 módulos creados](../assets/images/discovery/kvm/task-summary.png)

El ejemplo anterior informa de un destino, dos agentes y diez módulos: el agente del host KVM con cinco módulos y una de sus máquinas virtuales con los otros cinco. Si la tarea falla antes de generar nada, lo primero que hay que revisar es la lista de destinos, la conectividad SSH y las credenciales seleccionadas.

## Entender los resultados

### Agentes e identidad

El plugin crea un agente por cada host KVM y un agente por cada máquina virtual, con el agente del host como padre de cada uno de sus agentes de VM. Todos los agentes generados pertenecen al grupo de la tarea, heredan su intervalo y llevan uno de los siguientes alias. Con **Transfer mode** `native`, los agentes generados informan además de `KVM` como sistema operativo.

| Elemento | Alias del agente | Agente padre |
| --- | --- | --- |
| Host KVM | `KVM <host>` | — |
| Máquina virtual | `<vm> (<host>)` | El agente del host |

`<host>` es la parte de host del destino tal como se escribe en **KVM hosts**. El agente del host informa de ese host como su dirección (sin dirección en los destinos `local`), y un agente de VM en ejecución usa la dirección IPv4 de la VM cuando se puede resolver.

Los datos generados llevan además marcadores `extra_data` estables que identifican el origen de cada elemento. Los nombres se normalizan a minúsculas y los caracteres que no son letras, dígitos, puntos, guiones o guiones bajos se sustituyen por guiones bajos:

| Elemento | Marcador |
| --- | --- |
| Agente del host | `kvm:host:<host>` |
| Agente de VM | `kvm:vm:<host>:<vm>` |
| Módulo del host | `kvm:metric:<host>:<metric>` |
| Módulo de VM | `kvm:metric:<host>:<vm>:<metric>` |

![Lista de agentes con el agente del host KVM y su agente hijo de máquina virtual](../assets/images/discovery/kvm/agents-list.png)

### Módulos por agente

Los valores de los módulos se leen de cada destino en cada ejecución de la tarea; el nombre exacto y la condición de creación de cada módulo se listan en [Módulos generados](#modulos-generados).

| Agente | Módulos que incorpora |
| --- | --- |
| Host KVM | Estado de libvirtd; con **Monitor KVM server performance**: uso de RAM, consumo de RAM y uso de CPU del servidor KVM; con **Monitor virtual machines**: el número de máquinas virtuales definidas |
| Máquina virtual | Estado de encendido de la VM; para las VM en ejecución: vCPU asignadas, uso de CPU por vCPU, uso de memoria en porcentaje y consumo de memoria en bytes |

Un host sin libvirtd conserva su agente con `KVM Server status = 0` y ningún otro módulo, y no genera agentes de VM.

El uso de memoria de una VM en ejecución se mide en el host como la memoria residente del dominio frente a su asignación de memoria actual, por lo que informa de lo que la VM consume en el host y no de la memoria que tiene asignada, y puede superar el 100%.

![Módulos del agente del host KVM con métricas reales del servidor](../assets/images/discovery/kvm/host-modules.png)

![Módulos del agente de máquina virtual con métricas reales de la VM](../assets/images/discovery/kvm/vm-modules.png)

## Operación

### Ejecución manual

El plugin también se puede ejecutar fuera del asistente de Discovery con un archivo de configuración y un archivo de destinos. Es útil para probar la conectividad, para una ejecución puntual o para una planificación propia.

Escribe un archivo de configuración `[CONF]` con al menos el modo de autenticación y sus valores, y un archivo de destinos con una entrada por línea en los mismos formatos que **KVM hosts**. Después ejecuta `pandora_kvm --conf <config_file> --targets_file <targets_file>`. Todos los parámetros se documentan en [Archivo de configuración](#archivo-de-configuracion).

```ini
[CONF]
auth_mode = key
ssh_key_path = <PATH_TO_SSH_KEY>
ssh_user = <USER>
ssh_port = 22
timeout = 10
transfer_mode = native
interval = 300
agents_group_id = <GROUP_ID>
monitor_host = 1
monitor_vms = 1
```

En el modo de credenciales usa `auth_mode = credentials` y `credentials = <BASE64_CREDENTIAL>` en lugar de `ssh_key_path`. El valor de la credencial es un usuario y una contraseña codificados, no cifrados, así que protege el archivo de configuración como un secreto.

### Comportamiento de la ejecución

- Los destinos se procesan de forma secuencial, en el orden en el que se listan. Un error de conexión o de comando en un destino se registra en la información de ejecución y el resto de destinos se siguen procesando.
- El uso de CPU de las VM se muestrea por host, no por VM: cuando al menos una VM está en ejecución, el plugin lee `virsh domstats --vcpu` dos veces, con un segundo de separación, y usa la ventana medida para el porcentaje. Una ejecución tarda aproximadamente un segundo extra por host con VM en ejecución, y la ventana de muestreo no es configurable.
- Cuando el listado por defecto de `virsh list --all` no devuelve máquinas virtuales, el plugin reintenta el listado con `/usr/bin/virsh -r -c qemu:///system` y usa esa conexión para las métricas de VM del host.
- Cuando la consola deja un marcador de macro sin resolver en la configuración generada, por ejemplo `credentials` en modo **SSH key**, el plugin trata el valor como vacío.
- Una máquina virtual que no está en ejecución recibe igualmente su agente con su módulo de estado; sus módulos de rendimiento no se crean.

## Resolución de problemas

| Síntoma | Comprobación |
| --- | --- |
| La tarea informa de `Error connecting to <host>` | Confirma la accesibilidad SSH y el puerto. En modo de clave revisa **SSH private key path** y **Default SSH user**; en modo de credenciales revisa la credencial seleccionada. |
| La tarea informa de `SSH key authentication requires a key path` | La tarea se ejecuta en modo **SSH key** pero **SSH private key path** está vacío. Establece la ruta o cambia a **Pandora credentials**. |
| La tarea informa de `Invalid Pandora credentials` | Falta la credencial, no es una credencial personalizada válida o tiene la contraseña vacía. Selecciona una credencial personalizada en el paso Authentication. |
| La conexión se rechaza y **SSH known_hosts file** está establecido | Falta la clave de host del destino o ha cambiado. Actualiza el archivo (`ssh-keyscan -p <port> <host>`) o vacía el campo. |
| La tarea informa de `No agents were created for any target` | Han fallado todos los destinos. Revisa los errores por destino en la información de ejecución, empezando por la conectividad y las credenciales. |
| La tarea informa de `Error listing VMs on <host>` | Ejecuta `virsh list --all` en el host con el mismo usuario y confirma los permisos de libvirt. |
| El agente del host tiene `KVM Server status = 0` | libvirtd no está en ejecución en ese host, o el usuario SSH no puede ver sus procesos. |
| No hay agentes de VM aunque el host esté activo | Confirma que **Monitor virtual machines** está activado y revisa las expresiones **Allow list** y **Deny list**. Una expresión regular no válida se ignora: no permite ni deniega nada. |
| El módulo `Number of VMs` no se crea | **Monitor virtual machines** está desactivado. |
| Falta `Assigned vCPUs of <vm>` o `Virtual CPU usage of <vm> (%)` | Faltó una muestra de `virsh domstats --vcpu` en alguna de las dos lecturas, el delta de tiempo de vCPU fue negativo (la VM se reinició entre muestras) o el comando falló. El motivo se registra en la información de ejecución. |
| Falta `Virtual memory consumption of <vm> (bytes)` | `virsh dommemstat` falló y el respaldo con `virsh dominfo` no pudo leer la memoria usada. `Virtual memory usage of <vm> (%)` se sigue creando e informa de `0`. El motivo se registra en la información de ejecución. |
| No se crean los módulos `KVM Server RAM` o `KVM Server CPU` | **Monitor KVM server performance** está desactivado, libvirtd no está en ejecución, o `virsh nodememstats` / `virsh nodecpustats --percent` fallaron. Los dos módulos de RAM se omiten juntos. |
| Un agente de VM no tiene dirección | `virsh domifaddr` no devolvió ninguna dirección IPv4 utilizable (sin NIC, sin concesión DHCP todavía o solo IPv6). Se trata de un intento de mejor esfuerzo y no de un error. |

## Referencia

### Parámetros de la tarea

La consola presenta estos campos después de la definición genérica de la tarea. La columna de macro es el identificador que se usa en la configuración generada de la tarea.

#### KVM Connection

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| KVM hosts | `_pluginTargets_` | textarea | — | Destinos, uno por línea: `user@host`, `host` o `local`. También se aceptan valores separados por comas. Obligatorio |
| SSH port | `_sshPort_` | number | `22` | Puerto SSH usado para conectar con los hosts KVM |
| Command timeout | `_timeout_` | number | `10` | Tiempo de espera de la conexión SSH y de los comandos, en segundos |
| Authentication mode | `_authMode_` | select | `SSH key` | `SSH key` o `Pandora credentials`. Obligatorio |

#### Authentication

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| SSH private key path | `_sshKeyPath_` | string | — | Solo modo de clave. Ruta de la clave privada SSH en el servidor Pandora. Obligatorio en modo de clave |
| Default SSH user | `_sshUser_` | string | — | Solo modo de clave. Se usa en los destinos sin un prefijo `user@` explícito |
| Pandora credentials | `_credentials_` | select | — | Solo modo de credenciales. Credencial personalizada del gestor de credenciales de Pandora. Obligatoria en modo de credenciales |
| SSH known_hosts file | `_knownHosts_` | string | — | Ambos modos. Cuando se establece, las claves de host se verifican contra este archivo y los hosts desconocidos se rechazan |

El paso muestra únicamente los campos del **Authentication mode** seleccionado.

#### KVM Monitoring Options

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Monitor KVM server performance | `_monitorHost_` | checkbox | on | Añade los módulos de RAM y CPU del servidor KVM al agente del host |
| Monitor virtual machines | `_monitorVms_` | checkbox | on | Crea un agente por máquina virtual y el módulo `Number of VMs` en el agente del host |
| Allow list | `_allowList_` | string | — | Expresión regular para los nombres de las VM. Vacío permite todas |
| Deny list | `_denyList_` | string | — | Expresión regular para los nombres de las VM, aplicada después de la allow list. Vacío no deniega ninguna |
| Transfer mode | `_transferMode_` | select | `native` | `native` o `tentacle` |
| Tentacle IP | `_tentacleIp_` | string | `127.0.0.1` | Destino de Tentacle usado en el modo `tentacle` |
| Tentacle port | `_tentaclePort_` | number | `41121` | Puerto de destino de Tentacle usado en el modo `tentacle` |

### Archivo de configuración

La tarea de Discovery construye un archivo de configuración para el plugin, y una ejecución manual usa el mismo formato. Es un archivo de texto plano con una sección `[CONF]` de líneas `clave = valor`.

| Parámetro | Por defecto | Descripción |
| --- | --- | --- |
| `auth_mode` | `key` | `key` o `credentials`. Un valor vacío recae en `credentials` cuando `credentials` tiene un valor, y en `key` en caso contrario |
| `ssh_key_path` | — | Ruta de la clave privada SSH. Obligatoria en el modo `key` |
| `ssh_user` | — | Usuario SSH por defecto para los destinos sin un prefijo `user@` explícito |
| `known_hosts` | — | Archivo known_hosts de SSH. Cuando se establece, las claves de host se verifican y los hosts desconocidos se rechazan |
| `credentials` | — | Credencial producida por el gestor de credenciales de Pandora: un valor JSON en base64 con `user` y `password` |
| `ssh_port` | `22` | Puerto SSH usado para conectar con los hosts KVM |
| `timeout` | `10` | Tiempo de espera de la conexión SSH y de los comandos, en segundos |
| `transfer_mode` | `native` | `native` o `tentacle` |
| `tentacle_ip` | `127.0.0.1` | Destino de Tentacle |
| `tentacle_port` | `41121` | Puerto de destino de Tentacle |
| `interval` | Intervalo de la tarea (`300` desde la línea de comandos) | Intervalo asignado a los agentes generados |
| `agents_group` | Grupo de la tarea | Nombre del grupo de agentes usado en el modo `tentacle` |
| `agents_group_id` | ID del grupo de la tarea | Grupo de agentes numérico usado en el modo `native` |
| `allow_list` | — | Lista de permitidos (expresión regular) para los nombres de las VM |
| `deny_list` | — | Lista de denegados (expresión regular) para los nombres de las VM |
| `monitor_host` | `1` | Ponlo a `0` para desactivar los módulos de rendimiento del servidor KVM |
| `monitor_vms` | `1` | Ponlo a `0` para desactivar el descubrimiento de máquinas virtuales |
| `prefix` | — | Prefijo que se añade a los alias de los agentes generados y a los nombres de los módulos. La tarea de Discovery nunca lo establece |

Los valores de la línea de comandos actúan como valores por defecto de este archivo; un parámetro presente en el archivo de configuración tiene prioridad sobre su equivalente en la línea de comandos.

En el modo `credentials` la credencial seleccionada se almacena como valor JSON en base64 en la configuración de la tarea o en `credentials` en un archivo de configuración manual. Es una codificación, no un cifrado: protege la consola de Pandora FMS, el archivo de configuración y los permisos de cualquier archivo que la almacene. La clave privada SSH permanece en el servidor y se referencia por ruta.

### Módulos generados

El plugin genera los siguientes módulos por agente. **Se crea cuando** es la condición en la que aparece el módulo.

#### Agente del host KVM

| Módulo | Tipo | Unidad | Se crea cuando |
| --- | --- | --- | --- |
| `KVM Server status` | generic_proc | — | Siempre. `1` cuando hay al menos un proceso libvirtd en el host, `0` en caso contrario |
| `KVM Server RAM usage (%)` | generic_data | % | **Monitor KVM server performance** activado y libvirtd en ejecución |
| `KVM Server RAM consumption (bytes)` | generic_data | bytes | La misma condición que el módulo de uso de RAM |
| `KVM Server CPU usage (%)` | generic_data | % | **Monitor KVM server performance** activado y libvirtd en ejecución |
| `Number of VMs` | generic_data | — | **Monitor virtual machines** activado y libvirtd en ejecución. Cuenta las entradas devueltas por `virsh list --all` |

#### Agente de máquina virtual

| Módulo | Tipo | Unidad | Se crea cuando |
| --- | --- | --- | --- |
| `Status of <vm>` | generic_proc | — | Siempre. `1` cuando la VM está en ejecución, `0` en caso contrario |
| `Assigned vCPUs of <vm>` | generic_data | — | VM en ejecución con una muestra de CPU completa |
| `Virtual CPU usage of <vm> (%)` | generic_data | % | VM en ejecución con una muestra de CPU completa |
| `Virtual memory usage of <vm> (%)` | generic_data | % | VM en ejecución |
| `Virtual memory consumption of <vm> (bytes)` | generic_data | bytes | VM en ejecución cuyo uso de memoria se puede determinar |

Un módulo que depende de una medición que no se ha podido leer se omite y el motivo se registra en la información de ejecución de la tarea; el resto de módulos del agente se siguen creando. `Virtual memory usage of <vm> (%)` se crea siempre para una VM en ejecución e informa de `0` cuando su medición falla.

### Comandos ejecutados en el destino

| Métrica | Comando |
| --- | --- |
| Estado de libvirtd | `ps aux \| grep libvirtd \| grep -v grep \| wc -l` |
| Listado de VM | `virsh list --all` (respaldo: `/usr/bin/virsh -r -c qemu:///system list --all`) |
| RAM del servidor KVM | `virsh nodememstats` |
| CPU del servidor KVM | `virsh nodecpustats --percent` |
| vCPU y uso de CPU de las VM | `virsh domstats --vcpu`, dos veces alrededor de una ventana de un segundo |
| Memoria de las VM | `virsh dommemstat <vm>` (respaldo: `virsh dominfo <vm>`) |
| Dirección IP de las VM | `virsh domifaddr <vm>` (VM en ejecución, mejor esfuerzo) |

El binario `virsh` se resuelve con `whereis virsh | cut -f2 -d' '` y recae en `/usr/bin/virsh`.

### Línea de comandos

| Comando | Descripción |
| --- | --- |
| `pandora_kvm --conf <config_file> --targets_file <targets_file>` | Ejecuta el plugin con un archivo de configuración y un archivo de destinos |
| `pandora_kvm --conf <config_file> --targets_file <targets_file> --as_server_plugin true` | Modo de plugin de servidor: devuelve `1` cuando se creó al menos un agente y `0` en caso contrario |

Cada parámetro de configuración tiene su equivalente en la línea de comandos con el mismo significado (`--auth_mode`, `--ssh_key_path`, `--monitor_vms`, etcétera), salvo `agents_group`, `agents_group_id` y `prefix`, que solo existen en el archivo de configuración. `--as_server_plugin` solo existe en la línea de comandos.
