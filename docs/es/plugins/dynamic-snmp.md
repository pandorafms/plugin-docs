# Plugin Dynamic SNMP

*Última actualización del artículo: 2026-09-23.*

## Qué hace

El plugin Dynamic SNMP realiza un escaneo SNMP de un dispositivo objetivo y genera módulos de Pandora FMS de forma dinámica. En lugar de predefinir la OID de cada interfaz, el plugin recorre la tabla de interfaces, utiliza el nombre de la interfaz (`ifName`) para identificar cada una y crea un módulo por interfaz y métrica. De este modo la monitorización sobrevive a los cambios de OID que se producen entre reinicios del dispositivo.

Por defecto, para cada interfaz el plugin monitoriza:

- `ifOperStatus`.
- El tráfico de entrada y salida: `ifHCInOctets` e `ifHCOutOctets` cuando el dispositivo expone contadores de 64 bits, o `ifInOctets` e `ifOutOctets` en caso contrario.

Permite filtrar interfaces por nombre, asignar umbrales numéricos y de cadena a los módulos generados y adjuntar plantillas de alerta a dichos módulos.

El plugin se ejecuta de dos formas:

- **Plugin de agente** — sin `-agent`, imprime los módulos generados como XML en la salida estándar y el agente de Pandora FMS que lo ejecuta los recoge.
- **Plugin de servidor** — con `-agent <name>`, construye el informe del agente y lo transfiere al servidor de Pandora FMS, creando el agente y sus módulos cuando ese agente todavía no existe.

## Preparación

### Compatibilidad

El plugin se ha desarrollado y probado en Rocky Linux y Fedora 34, y se espera que funcione en cualquier sistema Linux.

### Requisitos

1. **Un despliegue de Pandora FMS** con el servidor o el agente que ejecutará el plugin.
2. **Perl 5.x.**
3. **Los comandos `snmpget` y `snmpwalk`** del paquete net-snmp, disponibles en el `PATH`.
4. **La librería Perl `PandoraFMS::PluginTools`.**
5. **Conectividad de red hacia el dispositivo objetivo**, además de su comunidad SNMP (v1/v2c) o su usuario y claves SNMPv3.
6. **Para el modo plugin de servidor**, un `tentacle_client` accesible (transferencia tentacle) o permiso de escritura en el directorio `data_in` (transferencia localcopy).

### Instalar el plugin

El plugin se distribuye como el script `dynamic_snmp`. Súbalo a la máquina que lo vaya a ejecutar:

- **Plugin de servidor** — `/usr/share/pandora_server/util/plugin/`.
- **Plugin de agente** — el directorio de plugins del endpoint.

Dele permisos de ejecución al archivo y compruebe que `snmpwalk` y `snmpget` están instalados en esa máquina.

## Configuración

El plugin no tiene archivo de configuración: todas las opciones se pasan por línea de comandos. Elija el modo según dónde se ejecute el plugin.

### Ejecución como plugin de agente

Registre el plugin como plugin de agente en el endpoint, con su comando y sus parámetros, y **no** utilice `-agent`. En cada ejecución el plugin imprime el XML de los módulos en la salida estándar y el agente los almacena bajo su propio agente.

### Registrar como plugin de servidor

Para que el plugin cree y alimente otro agente, regístrelo en la consola como plugin de servidor y pase `-agent` en cada ejecución:

1. Suba el script del plugin a `/usr/share/pandora_server/util/plugin/` en el servidor de Pandora FMS.
2. Vaya a **Servers → Plugins** y haga clic en **Add plugin**:

   ![Botón Add plugin en Servers > Plugins](../assets/images/plugins/dynamic-snmp/add-plugin.png)

3. Indique un **Name**, deje **Plugin type** en `Standard` y configure el **Max timeout**. Los escaneos SNMP pueden tardar, por lo que se recomienda un timeout de al menos 20 segundos; también puede ser necesario subir el `plugin_timeout` global de `pandora_server.conf`.

   ![Configuración general del plugin con nombre, tipo, timeout y descripción](../assets/images/plugins/dynamic-snmp/plugin-general.png)

   Descripción de ejemplo:

   ```text
   This plugin generates modules dynamically in the agent it's created in.
   Based on the ifName, it generates modules for:
   - ifOperStatus
   - ifInOctets (ifHCInOctets, if available)
   - ifOutOctets (ifHCOutOctets, if available)
   The value returned by the module represents the number of modules generated.
   ```

4. Configure el **Plugin command** y los **Plugin parameters**. Cada parámetro se escribe como una macro `_fieldX_`, donde `X` es el número posicional del parámetro:

   ![Comando y parámetros del plugin con macros](../assets/images/plugins/dynamic-snmp/plugin-command.png)

   Las macros de servidor `_agentname_` y `_address_` rellenan automáticamente el nombre del agente y la dirección del dispositivo, por lo que los parámetros del ejemplo son:

   ```text
   -agent "_agentname_" -h "_address_" -v "_field1_" -c "_field2_" -only "_field3_" -reject "_field4_" -wmin "_field5_" -wmax "_field6_" -cmin "_field7_" -cmax "_field8_"
   ```

5. Defina cada macro en **Macro parameters**, con una descripción, un valor por defecto y, opcionalmente, un texto de ayuda:

   ![Parámetros de macro con descripción, valor por defecto y ayuda](../assets/images/plugins/dynamic-snmp/plugin-macros.png)

6. En el agente de destino, cree un módulo nuevo y elija **Create a new plugin server module**:

   ![Diálogo de creación de un módulo plugin de servidor](../assets/images/plugins/dynamic-snmp/create-module.png)

7. En la configuración del módulo, seleccione el plugin **Dynamic SNMP** y rellene los campos de las macros:

   ![Configuración del módulo plugin de servidor con el plugin Dynamic SNMP](../assets/images/plugins/dynamic-snmp/configure-module.png)

En cada ejecución el plugin de servidor transfiere el informe con el modo de transferencia seleccionado e imprime el número de módulos generados. Si el agente indicado en `-agent` no existe, se crea automáticamente.

## Verificación

Ejecute el plugin manualmente en el host donde se vaya a lanzar. Este ejemplo escanea un dispositivo por SNMPv2c en modo plugin de agente:

```bash
./dynamic_snmp -h "192.168.51.1" -v "2c" -c "mycommunity"
```

Una ejecución correcta como plugin de agente imprime un bloque XML `<module>` por cada módulo generado en la salida estándar. Una ejecución correcta como plugin de servidor transfiere el informe e imprime en su lugar el número de módulos generados.

Los módulos generados aparecen entonces en el agente de destino:

![Módulos por defecto generados para cada interfaz](../assets/images/plugins/dynamic-snmp/generated-modules.png)

Con filtros y umbrales aplicados solo se generan las interfaces que coinciden y los umbrales se adjuntan a sus módulos:

![Módulos filtrados con umbrales de warning y critical](../assets/images/plugins/dynamic-snmp/filtered-modules.png)

## Entender los resultados

El plugin recorre primero la rama de nombres de interfaz y, para cada nombre, consulta cada rama configurada. El nombre del módulo es el nombre de la interfaz seguido del nombre de la rama, separados por un guion bajo, por ejemplo `ge-0/0/0_ifHCInOctets` o `FastEthernet0/0_OperStatus`.

- **Estado de la interfaz.** `ifOperStatus` se genera como un módulo `generic_proc`: vale `1` mientras la interfaz está operativa. Los valores mayores que `1` se fuerzan a `0` por compatibilidad con Pandora FMS.
- **Tráfico.** `ifHCInOctets`, `ifHCOutOctets`, `ifInOctets` y `ifOutOctets` se generan como módulos incrementales (`generic_data_inc`).
- **Contadores de 64 bits.** Cuando el dispositivo responde al recorrido de la rama de contadores de 64 bits (`.1.3.6.1.2.1.31.1.1.1.6`), el plugin usa las ramas HC; en caso contrario recurre a las ramas de 32 bits.
- **Tipado automático.** Para ramas personalizadas el plugin detecta el tipo del módulo a partir del tipo de dato SNMP del valor devuelto; el tipo no se predefine.
- **Filtros.** `-only` conserva únicamente las interfaces cuyo nombre coincide con alguna de sus expresiones regulares, y `-reject` descarta las interfaces cuyo nombre coincide con alguna de ellas.

## Operación y resolución de problemas

- **Activar la salida de depuración.** Añada `-debug 1` para imprimir mensajes de diagnóstico, precedidos por una marca de tiempo, en la salida de error estándar.
- **No se genera ningún módulo.** Compruebe la conectividad con el dispositivo, la versión de SNMP, la comunidad o las credenciales SNMPv3, y que `snmpwalk` y `snmpget` están instalados y accesibles en el `PATH`.
- **Faltan algunas interfaces.** Revise las expresiones regulares de `-only` y `-reject`; se comparan contra el nombre de la interfaz, por lo que un valor como `0/0/5` excluye toda interfaz cuyo nombre contenga esa cadena.
- **La ejecución agota el tiempo de espera.** Las tablas de interfaces grandes tardan más en recorrerse. Suba el timeout del módulo o del plugin y ajuste el intervalo (`-interval`) al tiempo de ejecución esperado.
- **Una ejecución como plugin de servidor no informa de módulos.** Verifique que la consola puede recibir desde el servidor: la dirección y el puerto de `tentacle_client` en modo tentacle, o la ruta `data_in` en modo localcopy.

## Referencia

### Parámetros generales

| Nombre | Requerido | Por defecto | Descripción |
| --- | --- | --- | --- |
| `-agent <name>` | No | — | Nombre del agente de destino. Si se indica, el plugin se ejecuta como plugin de servidor y transfiere el informe; si se omite, se ejecuta como plugin de agente e imprime los módulos en la salida estándar |
| `-interval <seconds>` | No | `300` | Intervalo del agente escrito en el informe generado (modo plugin de servidor). Un valor no numérico o `0` vuelve a `300` |
| `-group <name>` | No | — | Grupo de módulos asignado a cada módulo generado |
| `-debug 0\|1` | No | `0` | Si vale `1`, imprime mensajes de diagnóstico con marca de tiempo en la salida de error estándar |

### Parámetros SNMP

| Nombre | Requerido | Por defecto | Descripción |
| --- | --- | --- | --- |
| `-v <version>` | Sí | — | Versión de SNMP: `1`, `2`, `2c` o `3` |
| `-h <host>` | Sí | — | Dirección IP o nombre del dispositivo que se va a escanear |
| `-c <community>` | Para `1`, `2` y `2c` | — | Comunidad SNMP |
| `-p <port>` | No | `161` | Puerto SNMP del dispositivo |
| `-d <type>` | No | — | Tipo de dato. El plugin determina automáticamente el tipo de cada módulo, por lo que este valor se acepta pero no se aplica |

Parámetros de SNMPv3:

| Nombre | Requerido | Por defecto | Descripción |
| --- | --- | --- | --- |
| `-n <context>` | No | — | Contexto SNMPv3 |
| `-l <level>` | Para `3` | — | Nivel de seguridad: `noAuthNoPriv`, `authNoPriv` o `authPriv` |
| `-u <name>` | No | — | Nombre de seguridad (usuario) SNMPv3 |
| `-a <protocol>` | Con `authNoPriv` y `authPriv` | — | Protocolo de autenticación, como `MD5` o `SHA` |
| `-A <key>` | Con `authNoPriv` y `authPriv` | — | Clave de autenticación |
| `-x <protocol>` | Con `authPriv` | — | Protocolo de privacidad, como `DES` o `AES` |
| `-X <key>` | Con `authPriv` | — | Clave de privacidad |

### Parámetros de monitorización y filtrado

| Nombre | Requerido | Por defecto | Descripción |
| --- | --- | --- | --- |
| `-o <oid>` | No | `.1.3.6.1.2.1` | OID base a la que se añaden las subramas de las ramas |
| `-names <subtree>` | No | Automático | Subrama bajo `-o` utilizada como origen de los nombres de interfaz |
| `-branches <name:subtree,...>` | No | Automático | Ramas que se deben recuperar, con el formato `Rama1:SubOID1,Rama2:SubOID2`. La subrama se añade a `-o` |
| `-nodefaults 1` | No | — | Desactiva las ramas por defecto, de modo que solo se usan `-names` y `-branches` |
| `-only <regex,...>` | No | — | Lista de expresiones regulares separadas por comas. Solo se monitorizan las interfaces cuyo nombre coincide con alguna de ellas |
| `-reject <regex,...>` | No | — | Lista de expresiones regulares separadas por comas. Se excluyen las interfaces cuyo nombre coincide con alguna de ellas |

### Parámetros de umbrales y alertas

| Nombre | Requerido | Por defecto | Descripción |
| --- | --- | --- | --- |
| `-wmin <value>` | No | — | Umbral mínimo de warning para los módulos generados |
| `-wmax <value>` | No | — | Umbral máximo de warning para los módulos generados |
| `-cmin <value>` | No | — | Umbral mínimo de critical para los módulos generados |
| `-cmax <value>` | No | — | Umbral máximo de critical para los módulos generados |
| `-string_warning <string>` (`-wstr`) | No | — | Umbral de warning de tipo cadena para los módulos generados |
| `-string_critical <string>` (`-cstr`) | No | — | Umbral de critical de tipo cadena para los módulos generados |
| `-warning_inverse 0\|1` (`-winv`) | No | — | Invierte la comparación del umbral de warning |
| `-critical_inverse 0\|1` (`-cinv`) | No | — | Invierte la comparación del umbral de critical |
| `-alrt <name,...>` | No | — | Lista de plantillas de alerta separadas por comas, aplicadas a cada módulo generado |

### Parámetros de transferencia de datos

Se usan únicamente en modo plugin de servidor.

| Nombre | Requerido | Por defecto | Descripción |
| --- | --- | --- | --- |
| `-m <mode>` | No | `tentacle` | Modo de transferencia: `tentacle` o `localcopy` |
| `-t_ip <ip>` | No | `127.0.0.1` | Dirección del servidor de Pandora FMS de destino para la transferencia tentacle |
| `-t_port <port>` | No | `41121` | Puerto de Tentacle |
| `-t_opts <options>` | No | — | Opciones adicionales de Tentacle |
| `-t_file_path <path>` | No | `/var/spool/pandora/data_in/` | Directorio de destino para la transferencia localcopy |

### Módulos generados

Para cada interfaz y cada rama, el nombre del módulo es `<ifName>_<rama>`. Las ramas por defecto son:

| Nombre del módulo | Significado | Tipo |
| --- | --- | --- |
| `<ifName>_ifOperStatus` | Estado operativo de la interfaz: `1` cuando está operativa, `0` en caso contrario (los valores mayores que `1` se fuerzan a `0`) | `generic_proc` |
| `<ifName>_ifHCInOctets` | Octetos de entrada, contador de 64 bits | `generic_data_inc` |
| `<ifName>_ifHCOutOctets` | Octetos de salida, contador de 64 bits | `generic_data_inc` |
| `<ifName>_ifInOctets` | Octetos de entrada, contador de 32 bits | `generic_data_inc` |
| `<ifName>_ifOutOctets` | Octetos de salida, contador de 32 bits | `generic_data_inc` |

Las ramas personalizadas se generan con el mismo nombrado `<ifName>_<rama>` y su tipo se detecta a partir del tipo de dato SNMP.

### Árbol de OID por defecto

Las subramas siguientes se añaden a la OID base (`-o`, `.1.3.6.1.2.1` por defecto).

| Rama | Árbol de 32 bits | Árbol de 64 bits |
| --- | --- | --- |
| Nombres de interfaz (`__names__`) | `.2.2.1.2` | `.31.1.1.1.1` |
| `ifInOctets` / `ifHCInOctets` | `.2.2.1.16` | `.31.1.1.1.6` |
| `ifOutOctets` / `ifHCOutOctets` | `.2.2.1.10` | `.31.1.1.1.10` |
| `ifOperStatus` | `.2.2.1.8` | `.2.2.1.8` |

### Ejemplos

Escaneo básico por SNMPv2c en modo plugin de agente, con todos los valores por defecto:

```bash
./dynamic_snmp -h "192.168.51.1" -v "2c" -c "mycommunity"
```

Modo plugin de servidor con filtros de inclusión y exclusión. Solo se monitorizan las interfaces cuyo nombre contiene `Ge`, y se excluyen las que contienen `0/3`:

```bash
./dynamic_snmp -agent "Test-agentname" -h "192.168.51.1" -v "2c" -c "mycommunity" -only "Ge" -reject "0/3"
```

El mismo ejemplo por SNMPv3:

```bash
./dynamic_snmp -agent "Test-agentname" -h "192.168.51.1" -v "3" \
  -l "authPriv" -u "snmpv3user" -a "SHA" -A "PASSWORD1" -x "AES" -X "PASSWORD2" \
  -only "Ge" -reject "0/3"
```

Ramas personalizadas con la monitorización por defecto desactivada:

```bash
./dynamic_snmp -agent "Test-agentname" -h "192.168.51.1" -v "2c" -c "mycommunity" \
  -o ".1.3.6.1.2.1" -names ".2.2.1.2" \
  -branches "OperStatus:.2.2.1.8,AdminStatus:.2.2.1.7" -nodefaults 1
```

Las comillas de los ejemplos no son obligatorias, pero evitan problemas de interpretación del shell.
