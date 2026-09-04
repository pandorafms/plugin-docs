# KVM monitoring plugin

*Última actualización del artículo: 2026-09-03.*

## Qué hace

El plugin de monitorización de KVM monitoriza el estado de un entorno KVM en ejecución desde Pandora FMS. Para obtener ese estado utiliza dos elementos: `virsh`, que devuelve el estado de las máquinas virtuales (VM) y sus métricas de rendimiento, y `libvirtd`, que informa del estado del servidor KVM y de los recursos que consume.

El plugin se ejecuta como un plugin de agente de Pandora FMS: cada ejecución imprime los módulos generados como XML en la salida estándar, y todos los módulos pertenecen al grupo de módulos `KVM`.

## Preparación

### Compatibilidad y disponibilidad

El plugin se ha probado en CentOS, Ubuntu 24.04 y Rocky Linux 9, y se espera que funcione en sistemas basados en Linux. El paquete requiere libvirt (`libvirt-bin` o `libvirt`) junto con el comando `virsh`.

### Requisitos

1. **Un Pandora FMS Endpoint desplegado en su sistema.**
2. **Perl 5.x o superior.**
3. **Permiso para ejecutar `virsh` y conectarse a la instancia de libvirtd**, para el usuario que ejecuta el plugin.
4. **El comando `unzip`**, necesario únicamente cuando el plugin se despliega mediante colecciones.

### Instalar el plugin

El plugin se distribuye como el script `pandora_kvm.pl` y su archivo de configuración `pandora_kvm.conf`. Hay dos formas de desplegarlo:

- **Subida manual** — suba `pandora_kvm.pl` y `pandora_kvm.conf` al endpoint que ejecutará el plugin.
- **Colecciones** — despliegue ambos archivos en los endpoints mediante Enterprise collections.

## Configuración

Una vez colocados los archivos del plugin, regístrelo en la sección **Endpoint Plugins** del endpoint:

![El plugin configurado en la sección Endpoint Plugins](../assets/images/plugins/kvm/endpoint-plugins.png)

El plugin lee la lista de servidores KVM que debe monitorizar de su archivo de configuración, `pandora_kvm.conf`, que el script recibe como argumento:

- Una entrada `user@server` por línea monitoriza ese host KVM remoto.
- Varias líneas monitorizan varios servidores KVM con una única ejecución del plugin.
- El archivo incluido en el paquete contiene una única entrada, `root@localhost`, que monitoriza la instancia de libvirtd que se ejecuta en el propio host.
- Las líneas que empiezan por `#` son comentarios y se omiten.

El acceso a los hosts monitorizados debe realizarse sin intervención del usuario. Cuando una entrada apunta a un servidor remoto, copie la clave pública SSH del equipo que ejecuta el plugin a los servidores de destino.

## Verificación

Ejecute el plugin manualmente desde el directorio que lo contiene:

```bash
./pandora_kvm.pl pandora_kvm.conf
```

Una ejecución correcta imprime un bloque XML `<module>` por cada módulo generado en la salida estándar. La siguiente muestra corresponde a una ejecución en modo local — prefijo `(local)` — en un entorno KVM con dos VM, `ubuntu22.04` en ejecución y `crc` apagada:

```xml
<module>
    <name><![CDATA[(local) KVM Server status]]></name>
    <type></type>
    <data><![CDATA[1]]></data>
    <description><![CDATA[Status of the KVM server. 1 instances of libvirtd]]></description>
    <module_group>KVM</module_group>
</module>
<module>
    <name><![CDATA[(local) KVM Server RAM usage]]></name>
    <type>generic_data</type>
    <data><![CDATA[0]]></data>
    <description><![CDATA[RAM usage by the KVM server]]></description>
    <module_group>KVM</module_group>
</module>
<module>
    <name><![CDATA[(local) KVM Server CPU usage]]></name>
    <type>generic_data</type>
    <data><![CDATA[0]]></data>
    <description><![CDATA[CPU usage by the KVM server]]></description>
    <module_group>KVM</module_group>
</module>
<module>
    <name><![CDATA[(local) Number of VMs]]></name>
    <type>generic_data</type>
    <data><![CDATA[2]]></data>
    <description><![CDATA[Shows the number of available VMs in the KVM system]]></description>
    <module_group>KVM</module_group>
</module>
<module>
    <name><![CDATA[(local) Status of ubuntu22.04]]></name>
    <type>generic_proc</type>
    <data><![CDATA[1]]></data>
    <description><![CDATA[Status of ubuntu22.04: running]]></description>
    <module_group>KVM</module_group>
</module>
<module>
    <name><![CDATA[(local) Status of crc]]></name>
    <type>generic_proc</type>
    <data><![CDATA[0]]></data>
    <description><![CDATA[Status of crc: shut]]></description>
    <module_group>KVM</module_group>
</module>
<module>
    <name><![CDATA[(local) CPU usage of ubuntu22.04]]></name>
    <type></type>
    <data><![CDATA[4,5]]></data>
    <description><![CDATA[CPU usage of ubuntu22.04]]></description>
    <module_group>KVM</module_group>
</module>
<module>
    <name><![CDATA[(local) Virtual CPU usage of ubuntu22.04]]></name>
    <type></type>
    <data><![CDATA[0,5]]></data>
    <description><![CDATA[Virtual CPU usage of ubuntu22.04]]></description>
    <unit><![CDATA[%]]></unit>
    <module_group>KVM</module_group>
</module>
<module>
    <name><![CDATA[(local) Virtual memory usage of ubuntu22.04]]></name>
    <type></type>
    <data><![CDATA[100.00]]></data>
    <description><![CDATA[Mem usage of ubuntu22.04 4194304 of 4194304]]></description>
    <unit><![CDATA[%]]></unit>
    <module_group>KVM</module_group>
</module>
```

Los módulos generados son visibles en la consola de Pandora FMS:

![Módulos KVM en la consola de Pandora FMS](../assets/images/plugins/kvm/console-modules.png)

Si la ejecución no imprime XML de módulos, consulte [Solución de problemas](#solucion-de-problemas).

## Entender los resultados

Por cada nodo monitorizado, el plugin informa del estado del servidor KVM y de cada una de sus VM:

- **Nivel de servidor.** `(<node>) KVM Server status` vale `1` mientras libvirtd está en ejecución y `0` en caso contrario. `(<node>) KVM Server RAM usage` y `(<node>) KVM Server CPU usage` informan de los recursos que consume el servidor KVM, y `(<node>) Number of VMs` informa del número total de VM del sistema KVM.
- **Nivel de VM.** `(<node>) Status of <vm>` vale `1` mientras la VM está en ejecución y `0` en caso contrario; su descripción incluye el estado libvirt de la VM, como `running` o `shut`.
- **Solo VM en ejecución.** `(<node>) CPU usage of <vm>`, `(<node>) Virtual CPU usage of <vm>` y `(<node>) Virtual memory usage of <vm>` se generan únicamente mientras la VM está en ejecución; las dos últimas llevan la unidad `%`. El cálculo de cada módulo se describe en [Módulos generados](#modulos-generados).

Los nombres de los módulos empiezan con el nombre del nodo entre paréntesis: `(local)` cuando el plugin monitoriza la instancia de libvirtd local, y el host de cada entrada `user@server` para los nodos remotos. Todos los módulos se emiten con `module_group` `KVM`.

## Solución de problemas

- **Un nodo no genera módulos de VM ni de recursos** — el plugin comprueba primero si libvirtd está en ejecución (`ps aux | grep libvirtd | grep -v grep`) y, cuando no encuentra ningún proceso, emite únicamente `(<node>) KVM Server status` con valor `0` y omite el resto del nodo. Compruebe que libvirtd está en ejecución y que el usuario que ejecuta el plugin puede ver el proceso.
- **Un host KVM remoto no se monitoriza** — el plugin accede a cada entrada remota mediante SSH y la conexión no debe requerir intervención del usuario. Copie la clave pública SSH del equipo que ejecuta el plugin a todos los servidores de destino y asegúrese de que cada entrada usa la forma `user@server`.
- **El plugin imprime su texto de uso y no genera XML de módulos** — el archivo de configuración indicado como argumento no existe o se ha indicado más de un argumento. Compruebe la ruta y ejecute el plugin con un único archivo existente, por ejemplo `./pandora_kvm.pl pandora_kvm.conf`.
- **Un nodo con libvirtd en ejecución sigue sin informar de VM** — el plugin obtiene la lista de VM con `virsh list --all` y, cuando ese comando no devuelve ninguna lista, recurre a `/usr/bin/virsh -r -c qemu:///system`, en modo de solo lectura. Compruebe que `virsh` está instalado y que el usuario que ejecuta el plugin puede ejecutarlo y conectarse a la instancia de libvirtd (el paquete requiere libvirt, `libvirt-bin` o `libvirt`).

## Referencia

### Archivo de configuración

El plugin monitoriza los hosts KVM indicados en un archivo de configuración de texto plano, `pandora_kvm.conf`, que el script recibe como argumento:

| Entrada | Por defecto | Descripción |
| --- | --- | --- |
| `user@server` | `root@localhost` | Una entrada por línea. Cada entrada monitoriza un host KVM como usuario SSH `user` en el host `server`; varias entradas monitorizan varios servidores KVM con una única ejecución del plugin |
| Comentario `#` | — | Una línea que empieza por `#` es un comentario y se omite |

El archivo incluido en el paquete contiene una única entrada, `root@localhost`, que monitoriza la instancia de libvirtd que se ejecuta en el propio host. Para monitorizar servidores remotos, añada una entrada `user@server` por servidor, como se describe en [Configuración](#configuracion).

### Ejecución por línea de comandos

El plugin recibe su archivo de configuración como argumento de línea de comandos:

```bash
./pandora_kvm.pl <config-file>
```

| Condición | Comportamiento |
| --- | --- |
| El argumento indica un archivo existente | El plugin monitoriza todos los hosts indicados en el archivo e imprime un bloque XML `<module>` por cada módulo generado en la salida estándar |
| El argumento indica un archivo que no existe | El plugin imprime su texto de uso y se detiene sin generar módulos |
| Se indica más de un argumento | El plugin imprime su texto de uso y se detiene sin generar módulos |
| No se indica ningún argumento | El plugin se ejecuta en modo local contra la instancia de libvirtd local |

En caso de éxito, el XML de módulos impreso en la salida estándar es la secuencia que el agente de Pandora FMS ingiere para el endpoint.

### Módulos generados

Los nombres de los módulos empiezan con el nombre del nodo entre paréntesis: `(local)` cuando el plugin monitoriza la instancia de libvirtd local, o el host de la entrada para los nodos remotos (`server` en `user@server`). En los nombres de la tabla siguiente, `<node>` es ese prefijo y `<vm>` es el nombre de una VM:

| Nombre del módulo | Significado | Tipo | Unidad |
| --- | --- | --- | --- |
| `(<node>) KVM Server status` | Estado del servidor KVM: `1` mientras libvirtd está en ejecución, `0` en caso contrario | `generic_proc` | — |
| `(<node>) KVM Server RAM usage` | Uso de RAM del servidor KVM | `generic_data` | — |
| `(<node>) KVM Server CPU usage` | Uso de CPU del servidor KVM | `generic_data` | — |
| `(<node>) Number of VMs` | Número total de VM del sistema KVM (`virsh list --all`) | `generic_data` | — |
| `(<node>) Status of <vm>` | Estado de la VM: `1` en ejecución, `0` en caso contrario; la descripción incluye el estado libvirt, como `running` o `shut` | `generic_proc` | — |
| `(<node>) CPU usage of <vm>` | Media de los valores `CPU` que informa `virsh vcpuinfo` sobre las vCPU de la VM; solo VM en ejecución | `generic_data` | — |
| `(<node>) Virtual CPU usage of <vm>` | Media de los valores `VCPU` que informa `virsh vcpuinfo` sobre las vCPU de la VM; solo VM en ejecución | `generic_data` | `%` |
| `(<node>) Virtual memory usage of <vm>` | Memoria usada sobre la memoria máxima de la VM (`virsh dominfo`); solo VM en ejecución | `generic_data` | `%` |
