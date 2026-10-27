# Pandora Office 365 Monitoring

*Última actualización del artículo: 2026-10-27.*

!!! warning "Se recomienda la integración de Discovery"
    Para instalaciones nuevas use [Office 365 Discovery](../discovery/office-365.md), que es la integración recomendada para este servicio. Este plugin es la ruta heredada. La entrada del Marketplace indica que este addon ya no recibe mantenimiento activo.

## Qué hace

El plugin Pandora Office 365 Monitoring informa del estado de un tenant de
Microsoft 365 en Pandora FMS. Cada ejecución se autentica en Microsoft Entra ID
con las credenciales de un registro de aplicación, lee el resumen de estado de
todos los servicios de Microsoft 365 a los que está suscrito el tenant y lo
publica como un agente con dos módulos por servicio: el estado que Microsoft
informa para ese servicio y la lista de sus incidencias sin resolver.

El plugin se ejecuta como plugin de servidor: construye el documento de agente y
lo entrega a un directorio de datos de Pandora FMS o lo envía por Tentacle. No
imprime el XML de los módulos en la salida estándar, por lo que no se puede
ejecutar como plugin de agente.

También puede leer los anuncios de servicio —los mensajes que Microsoft publica
sobre incidencias y mantenimientos planificados— y enviarlos al colector de logs
de Pandora FMS.

> Esta página documenta el plugin de servidor `pandorafms.office365_plugin`. El
> descubrimiento de tenants de Microsoft 365 y la generación de sus agentes desde
> una tarea de Discovery son otro addon: consulte
> [Office 365 Discovery](../discovery/office-365.md).

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
|--------|--------|-----------|
| Plugin `pandorafms.office365_plugin`, versión `1.0` | Objetivo documentado | La versión que describe esta página. Consulte [Identidad del plugin](#identidad-del-plugin) |
| Pandora FMS NG `784` y posteriores | `Soportado` | El Marketplace indica que todas sus integraciones son compatibles con Pandora FMS NG 784 y versiones posteriores. Es una declaración general de compatibilidad que cubre el plugin, no un registro de prueba del mismo |
| El servidor de plugins de Pandora FMS, habilitado | `Requerido` | El addon es un plugin de servidor y lo ejecuta el servidor de plugins |
| Acceso de red desde el host que ejecuta el plugin hasta `login.microsoftonline.com` y `graph.microsoft.com` por HTTPS | `Requerido` | El plugin obtiene su token y lee sus datos de esos dos hosts; no expone ninguna opción para cambiar ninguno de los dos endpoints |
| Una aplicación de Microsoft Entra ID con los permisos de [Permisos de Microsoft Graph](#permisos-de-microsoft-graph) | `Requerido` | Es un requisito previo, no una declaración de compatibilidad |
| Sistema operativo del host que ejecuta el plugin | `Sin validar` | No se ha registrado un sistema operativo para esta versión |

La entrada del Marketplace indica que este addon ya no se mantiene ni se
actualiza activamente y que deben considerarse los plugins alternativos de la
biblioteca. Es un aviso de mantenimiento del editor; esta página describe el
comportamiento de la versión `1.0` tal y como se distribuye.

### Requisitos

1. **Conectividad** desde el host que ejecuta el plugin hasta
   `login.microsoftonline.com` y `graph.microsoft.com`.
2. **Una aplicación de Microsoft Entra ID registrada en el tenant que se va a
   monitorizar**, con un secreto de cliente y los permisos de aplicación que se
   describen a continuación.
3. **El ID de tenant, el ID de cliente y el secreto de cliente** de esa
   aplicación.
4. **Pandora FMS**:
    - El servidor de plugins habilitado, para ejecutar el plugin registrado.
    - Un directorio de datos que procese el servidor de datos, o un servidor
      Tentacle que reciba el documento de agente. Cuando la entrega usa Tentacle,
      el ejecutable `tentacle_client` debe estar disponible en `PATH` en el host
      que ejecuta el plugin.
5. **El paquete del addon instalado en Pandora FMS** a través de la consola.

### Permisos de Microsoft Graph

El plugin solicita un token de aplicación con el ámbito
`https://graph.microsoft.com/.default`, de modo que recibe los permisos de
aplicación concedidos al registro, sin ningún usuario que inicie sesión. Cada
conjunto de datos que lee está cubierto por los siguientes permisos de aplicación
de Microsoft Graph:

| Petición a Microsoft Graph | Se usa para | Permiso de aplicación |
|----------------------------|-------------|-----------------------|
| `/admin/serviceAnnouncement/healthOverviews?$expand=issues` | Estado de los servicios e incidencias sin resolver | `ServiceHealth.Read.All` |
| `/admin/serviceAnnouncement/messages` | Anuncios de servicio enviados como entradas de log | `ServiceMessage.Read.All` |

Conceda solo lo que recoja la ejecución: `ServiceMessage.Read.All` hace falta
únicamente cuando se habilita la recogida de logs con `-l`. Ambos permisos
requieren consentimiento del administrador. No conceda las variantes
`ReadWrite`.

El secreto de cliente es una credencial: guárdelo solo en la configuración del
plugin y revóquelo en Microsoft Entra ID cuando ya no lo necesite.

### Registrar la aplicación en Microsoft Entra ID

1. Abra Microsoft Entra ID y registre una aplicación nueva en **Registros de
   aplicaciones**. Regístrela en el tenant que quiera monitorizar.
2. En **Certificados y secretos**, cree un secreto de cliente y copie su valor de
   inmediato: Azure solo lo muestra una vez.
3. En la información general de la aplicación, copie el **ID de aplicación
   (cliente)** y el **ID de directorio (tenant)**.
4. En **Permisos de API**, añada los permisos de aplicación de Microsoft Graph
   indicados arriba y conceda consentimiento del administrador.

<!-- SCREENSHOT NEEDED: Página de permisos de API de la aplicación con los permisos de aplicación de Microsoft Graph ServiceHealth.Read.All y ServiceMessage.Read.All y el consentimiento del administrador concedido. -->

### Instalar el plugin

Descargue el paquete desde la entrada del Marketplace de Pandora FMS, que está
limitada a usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms.office365_plugin](https://marketplace.pandorafms.com/entries/pandorafms.office365_plugin)

Cárguelo en Pandora FMS. Una vez cargado, el plugin queda registrado con sus
parámetros y disponible al crear módulos de plugin.

No ha sido posible inspeccionar el contenido del paquete distribuido para esta
página, por lo que no se prescribe aquí ningún procedimiento de compilación ni de
instalación de dependencias. Utilice el ejecutable `pandora_o365` que instala el
paquete en el servidor de Pandora FMS.

### Credenciales y transporte

- El secreto de cliente se pasa como valor de `-s`. Aparece en el historial del
  shell de una ejecución manual y en la lista de procesos del sistema operativo
  mientras el plugin se ejecuta, incluidas las ejecuciones lanzadas por el
  servidor de plugins.
- El plugin no tiene ninguna opción para leer las credenciales de un archivo
  protegido: los campos del plugin en la consola y la línea de comandos son sus
  únicas superficies de entrada. Restrinja el acceso al host que ejecuta el
  plugin y a los usuarios que pueden editar módulos de plugin, y revoque y vuelva
  a emitir el secreto si se expone.
- La autenticación y todas las peticiones de datos van a los endpoints fijos de
  Microsoft por HTTPS. El plugin no ofrece forma de cambiarlos y no expone
  ninguna opción de proxy, así que un proxy en el camino queda fuera de su
  configuración.

## Configuración

El plugin no tiene archivo de configuración: todas las opciones son de línea de
comandos y se documentan en [Parámetros de línea de
comandos](#parametros-de-linea-de-comandos). Elija primero cómo se ejecuta.

### Registrar el plugin en la consola

1. Abra **Servidores → Plugins** y haga clic en **Registrar plugin**.
2. Indique el nombre, el tipo de plugin **Estándar**, un tiempo máximo de
   ejecución opcional y una descripción.
3. En **Comando del plugin**, escriba la ruta completa del ejecutable
   `pandora_o365` en el servidor de Pandora FMS, por ejemplo
   `<PATH_TO_PLUGIN>/pandora_o365`.
4. En **Parámetros del plugin**, pase las opciones con las macros de plugin
   `_field1_`, `_field2_`, ... como marcadores:

```text
-c _field1_ -t _field2_ -s _field3_ -a _field4_ -g _field5_
```

5. En **Parámetros macro**, describa cada campo. El ejemplo usa estos valores:

| Campo | Descripción | Valor de ejemplo |
|-------|-------------|------------------|
| `_field1_` | ID de aplicación (cliente) | `<CLIENT_ID>` |
| `_field2_` | ID de directorio (tenant) | `<TENANT_ID>` |
| `_field3_` | Valor del secreto de cliente; marque **Ocultar valor** | — |
| `_field4_` | Valor del que se deriva el nombre del agente y que se usa como alias | `Pandora_O365` |
| `_field5_` | Grupo de Pandora FMS del agente generado | `<GROUP_NAME>` |

<!-- SCREENSHOT NEEDED: Formulario de registro de plugin de servidor para Pandora Office 365 Monitoring con el comando, los parámetros y la lista de parámetros macro, con valores de laboratorio y el secreto oculto. -->

El plugin escribe el documento de agente por sí mismo, así que el directorio de
datos importa:

- Cuando el plugin se registra en el servidor de Pandora FMS que procesa los
  documentos, el valor por defecto `-d /var/spool/pandora/data_in/` es el destino
  correcto y no hace falta ninguna opción adicional.
- Cuando se registra en un servidor de Pandora FMS remoto, añada
  `--tentacle_address 127.0.0.1` (y `--tentacle_port` si el servidor Tentacle no
  escucha en `41121`), para que el documento se envíe al servidor Tentacle de la
  máquina que ejecuta el módulo.

El módulo que usa el plugin no contiene el estado de los servicios: los módulos
de estado e incidencias aparecen en el agente `O365_…` generado, no en el agente
que contiene el módulo. Lo que el plugin imprime en la salida estándar es el
número de resumen descrito en [El número de resumen
impreso](#el-numero-de-resumen-impreso).

### Línea de comandos

Esta es la ejecución mínima: recoge el estado y las incidencias de los servicios
y escribe el documento de agente en el directorio de datos local.

```bash
./pandora_o365 -c <CLIENT_ID> -t <TENANT_ID> -s <CLIENT_SECRET>
```

Una ejecución completa, con identificador de agente, prefijo, grupo, intervalo y
recogida de logs explícitos:

```bash
./pandora_o365 -c <CLIENT_ID> -t <TENANT_ID> -s <CLIENT_SECRET> \
    -a Pandora_O365 -p O365 -g <GROUP_NAME> -i 300 \
    -d /var/spool/pandora/data_in/ -l
```

`./pandora_o365 -h` imprime el resumen de uso con todas las opciones y termina
sin contactar con Microsoft.

### Nombre, alias y grupo del agente

El valor de `-a` no da nombre al agente: se convierte en un hash para el nombre y
se copia al alias.

- **Nombre del agente**: `<prefijo>_<hash MD5 del valor de -a>`.
- **Alias del agente**: `<prefijo>_<valor de -a>`.

Con los valores por defecto (`-a Pandora_O365`, `-p O365`) el agente se llama
`O365_dab294b287a0bc7a39f3596e17e2ef50` y su alias es `O365_Pandora_O365`. El
nombre es el identificador que usa Pandora FMS para el agente, así que la cadena
legible vive en el alias. Cambiar `-a` o `-p` produce un **nombre de agente
distinto** y, por tanto, un agente nuevo en la consola: fije ambos valores de
forma explícita y manténgalos estables entre ejecuciones.

El valor de `-g` se escribe en el documento de agente. Debe ser un grupo que
exista en la consola; en caso contrario, el agente se asigna al grupo por defecto
`unknown`.

### Elegir qué recopilar

| Objetivo | Opciones |
|----------|----------|
| Solo módulos de estado e incidencias | Por defecto; no pase `-l` |
| Estado, incidencias y anuncios de servicio | Añada `-l` |
| Solo anuncios de servicio | Añada `-l -n`; `-n` omite los módulos de estado e incidencias |

La recogida de logs envía los mensajes al colector de logs configurado para el
agente generado, así que ese colector debe existir en el entorno de Pandora FMS.

## Verificación

Ejecute el plugin manualmente con un directorio de datos de prueba, para
inspeccionar el documento antes de que Pandora FMS lo ingiera:

```bash
mkdir -p /tmp/o365-check/
./pandora_o365 -c <CLIENT_ID> -t <TENANT_ID> -s <CLIENT_SECRET> -a Pandora_O365 -d /tmp/o365-check/
```

El directorio debe existir y ser escribible, y el valor de `-d` debe terminar en
`/`: el plugin concatena el directorio y el nombre del archivo sin añadir
separador, así que `-d /tmp/o365-check` genera un archivo llamado
`/tmp/o365-checkO365_….data` junto al directorio en lugar de dentro de él.

Una ejecución correcta imprime un único número como última línea (consulte [El
número de resumen impreso](#el-numero-de-resumen-impreso)) y escribe:

```text
/tmp/o365-check/O365_dab294b287a0bc7a39f3596e17e2ef50.<EPOCH>.data
```

`<EPOCH>` es el momento de la ejecución en segundos. El documento tiene un par de
módulos por cada servicio al que está suscrito el tenant; este es un extracto con
valores ilustrativos:

```xml
<?xml version='1.0' encoding='UTF-8'?>
<agent_data agent_name='O365_dab294b287a0bc7a39f3596e17e2ef50' agent_alias='O365_Pandora_O365' parent_agent_name='' description='Agent generated by pandora_o365 plugin' version='' os_name='' os_version='' timestamp='2026/10/26 10:00:00' address='127.0.0.1' group='unknown' interval='300'>
<module>
	<name><![CDATA[O365_Exchange_status]]></name>
	<type>generic_data_string</type>
	<data><![CDATA[serviceOperational]]></data>
	<description><![CDATA[O365_Exchange Online]]></description>
</module>
<module>
	<name><![CDATA[O365_Exchange_active_issues]]></name>
	<type>generic_data_string</type>
	<data><![CDATA[EX1: Mail flow delay]]></data>
	<description><![CDATA[Exchange Online Issues Ids]]></description>
</module>
</agent_data>
```

En la consola, el agente generado aparece con sus dos módulos por servicio una vez
que el servidor de Pandora FMS procesa el documento:

<!-- SCREENSHOT NEEDED: El agente O365_ generado en la consola de Pandora FMS, con los módulos _status y _active_issues de varios servicios y sin datos reales de tenant. -->

Compruebe, en este orden:

1. La última línea de la salida es un número y no se ha impreso ninguna línea
   `ERROR` ni `Error` en la salida de error.
2. El archivo `.data` existe en el directorio pasado a `-d`, y su nombre y alias
   de `<agent_data>` son los esperados.
3. Cada servicio al que está suscrito el tenant tiene un módulo `_status` y un
   módulo `_active_issues`.
4. El agente aparece en la consola en el grupo configurado, con los módulos
   recibiendo datos en la siguiente ejecución.

## Entender los resultados

### El agente

Una ejecución produce **un agente**, sea cual sea el número de servicios: los
servicios son módulos de ese agente, no agentes separados.

| Propiedad del agente | Valor |
|----------------------|-------|
| Nombre | `<prefijo>_<hash MD5 del valor de -a>` |
| Alias | `<prefijo>_<valor de -a>` |
| Descripción | `Agent generated by pandora_o365 plugin` |
| Dirección | `127.0.0.1` |
| Grupo | El valor de `-g` (`unknown` por defecto) |
| Intervalo | El valor de `-i` (`300` por defecto) |
| Campos de sistema operativo | Vacíos |

### Módulos por servicio

Por cada servicio que devuelve Microsoft Graph, el agente tiene:

| Módulo | Tipo | Descripción |
|--------|------|-------------|
| `<prefijo>_<id de servicio>_status` | `generic_data_string` | El `status` que Microsoft Graph informa para el servicio, tal cual |
| `<prefijo>_<id de servicio>_active_issues` | `generic_data_string` | `<id de incidencia>: <título de incidencia>` por cada incidencia no resuelta, concatenadas sin separador entre incidencias; el literal `None` cuando el servicio no tiene ninguna incidencia sin resolver |

El `<id de servicio>` es el `id` que devuelve Graph para el servicio, y la
descripción del módulo de estado es `<prefijo>_<nombre del servicio>` (por ejemplo
`O365_Exchange Online`); la descripción del módulo de incidencias es
`<nombre del servicio> Issues Ids`.

El conjunto de servicios no lo fija el plugin: es el que el tenant tiene suscrito
en el momento de la ejecución, así que dos tenants, o el mismo tenant tras un
cambio de suscripción, no producen necesariamente los mismos nombres de módulo.

Dos consecuencias del formato del valor:

- El módulo de estado lleva un estado en texto. El plugin no aplica ningún umbral
  ni ninguna conversión a estados warning o critical de Pandora FMS, así que un
  servicio degradado no genera por sí mismo una alerta. Si necesita una, alerte
  sobre el valor en la definición del módulo.
- Como las incidencias se concatenan sin separador, dos incidencias sin resolver
  producen un valor del tipo `EX1: Mail flow delayEX2: Mailbox access`, difícil
  de leer y de comparar. Una sola incidencia no tiene ese problema, y `None` es
  inequívoco.

Microsoft documenta los valores posibles de `status` de un objeto de estado de
servicio (`serviceOperational`, `investigating`, `restoringService`,
`serviceDegradation`, `serviceInterruption` y el resto de valores de la
enumeración `serviceHealthStatus`). El módulo publica la cadena exactamente como
la recibe.

### Entradas de log

Con `-l`, el plugin lee los anuncios de servicio y escribe una entrada de log por
anuncio, con el origen `<prefijo>_<servicio>` del primer servicio que enumera el
anuncio.

- La petición omite los primeros 100 anuncios (`$skip=100`) y no sigue la
  paginación de la respuesta. Por tanto, un tenant con menos de 100 anuncios no
  produce ninguna entrada de log, y solo se recogen los anuncios posteriores a
  los 100 primeros.
- El valor de la entrada es el anuncio completo convertido a texto: el mensaje se
  serializa como un texto de clave/valor con el cuerpo HTML pasado a texto plano,
  no como JSON ni como el cuerpo solo. Las entradas son largas y sus claves
  conservan las comillas de esa serialización.
- Las entradas de log se entregan en un segundo documento de agente con el mismo
  nombre de agente que el documento de estado; consulte [Operación](#operacion)
  para ver la consecuencia en la entrega local.

## Operación y resolución de problemas

### Operación

- El plugin no guarda estado entre ejecuciones: cada ejecución lee el estado del
  tenant en ese momento y entrega un documento completo, así que se puede
  ejecutar a mano en cualquier momento.
- Prográmelo desde Pandora FMS mediante el módulo de plugin o la planificación
  del servidor de plugins. `-i` solo fija el intervalo que se anota en el
  documento de agente; la frecuencia real es la de la planificación, y `-i` debe
  ser igual o mayor que ella.
- **El código de salida es `0` en casi todos los casos**, incluida una recogida de
  datos o de logs fallida: el plugin imprime un número de resumen y termina
  correctamente. Lea el número, no el código de salida.
- **Entrega por Tentacle**: el documento se escribe en `--tmp` y se envía con
  `tentacle_client`. Si el envío falla, el plugin escribe `Tentacle error` en la
  salida de error, el archivo se queda en `--tmp` y aun así imprime su número de
  resumen y termina con `0`. Revise la salida de error cuando el agente no
  aparezca.
- **Entrega local con `-l`**: el documento de estado y el de log tienen el mismo
  nombre de agente y se nombran con el segundo de la ejecución. Cuando ambos se
  escriben en el mismo segundo, la segunda escritura falla con
  `ERROR - Could not write file: [Errno 17] File exists` y la ejecución termina
  con código de salida `1`. El documento de estado de esa ejecución ya está en el
  directorio de datos; las entradas de log se pierden. Cuando la recogida de los
  anuncios tarda más de un segundo, las dos escrituras caen en segundos distintos
  y ambas tienen éxito.
- **`--utf8 0`** escribe el valor de incidencias como una cadena de bytes (`b'…'`)
  en lugar de texto. Deje el valor por defecto `1` salvo que el entorno requiera
  bytes crudos.
- Los valores de `-d` y `--tmp` se concatenan con el nombre del archivo sin añadir
  separador: mantenga la `/` final en ambos.

#### El número de resumen impreso

La última línea de una ejecución es la suma de una contribución por etapa de
recogida:

| Recogida de estado | Recogida de logs (`-l`) | Número impreso |
|--------------------|-------------------------|----------------|
| Recogido | No solicitada | `2` |
| Recogido | Recogida | `3` |
| Recogido | Fallida | `1` |
| Fallida | Recogida | `0` |
| Fallida | Fallida | `-2` |
| Omitida (`-n`) | Recogida | `1` |
| Omitida (`-n`) | Fallida | `-1` |
| Omitida (`-n`) | No solicitada | `0` |

Una ejecución que no puede autenticarse, o cuya petición de estado rechaza
Microsoft Graph, no llega a este resumen: termina con código de salida `1` e imprime un
error.

### Resolución de problemas

- **`Error Auth Token: 'dict' object has no attribute 'reason'`, código de salida
  `1`** — Microsoft Entra ID rechazó la petición de token (ID de tenant, ID de
  cliente o secreto incorrectos, o secreto caducado). El mensaje es un error del
  propio plugin, no el texto que devuelve Microsoft: el gestor de errores de
  autenticación falla antes de poder imprimir el motivo HTTP, así que no se
  muestra la causa real. Verifique los tres valores y la caducidad del secreto en
  Microsoft Entra ID y repita la ejecución.
- **`Error requesting url: <motivo> (<estado>) on https://graph.microsoft.com/...`,
  código de salida `1`** — Microsoft Graph rechazó la petición de estado. Un
  `401` apunta a un token que Microsoft no aceptó; un `403` apunta a un permiso de
  aplicación ausente o a un consentimiento no concedido. Revise los permisos de
  [Permisos de Microsoft Graph](#permisos-de-microsoft-graph) y conceda de nuevo
  el consentimiento del administrador.
- **La ejecución termina con código de salida `157` y no imprime resumen** — falló la
  petición de anuncios de servicio. Esta etapa termina con ese estado en lugar de
  informarlo, así que un `403` aquí significa que falta
  `ServiceMessage.Read.All` con `-l` habilitado. Añada el permiso o quite `-l`.
- **`error data: ...` o `error logs: ...` con un número de resumen** — Microsoft
  respondió, pero la respuesta no tenía la estructura esperada y el documento de
  esa etapa no se escribió. Repita la ejecución; si persiste, compruebe la misma
  petición a mano contra Microsoft Graph y verifique los permisos.
- **No aparece ningún agente en la consola** — compruebe, en este orden: el
  archivo `.data` se escribió en el directorio que procesa el servidor de Pandora
  FMS; el valor de `-d` o `--tmp` termina en `/`; el valor de `-g` nombra un grupo
  existente; en la entrega por Tentacle, la salida de error no muestra `Tentacle
  error`.
- **El agente aparece, pero los módulos no tienen datos** — el documento lo
  escribió un usuario de ejecución distinto del que lee el servidor de datos, o el
  directorio de datos no es el que procesa el servidor. Compare el propietario del
  archivo y el directorio con la configuración del servidor de datos.
- **Aparece un segundo agente tras un cambio de configuración** — el nombre del
  agente se deriva de `-p` y `-a`. Restaure los valores anteriores o acepte el
  agente nuevo y borre el antiguo en la consola.
- **No hay entradas de log aunque `-l` esté activo** — el tenant tiene menos de 100
  anuncios, la petición de mensajes falló (código `157`), o el colector de logs no
  está configurado para el agente.

## Referencia

### Parámetros de línea de comandos

| Nombre | Obligatorio | Valor por defecto | Descripción |
|--------|-------------|-------------------|-------------|
| `-c`, `--clientid` | Sí | — | ID de aplicación (cliente) de la aplicación de Microsoft Entra ID |
| `-t`, `--tenantid` | Sí | — | ID de directorio (tenant); forma parte del endpoint del token |
| `-s`, `--secret` | Sí | — | Valor del secreto de cliente de la aplicación |
| `-a`, `--agent_name` | No | `Pandora_O365` | Valor del que se deriva el nombre del agente y que se usa como alias. No es el nombre del agente, y su texto de ayuda anuncia otro valor por defecto (`pandora_o365`) |
| `-p`, `--prefix` | No | `O365` | Prefijo del nombre y del alias del agente, de los nombres de módulo y del origen de log |
| `-g`, `--group` | No | `unknown` | Grupo de Pandora FMS que se escribe en el documento de agente. Debe existir en la consola |
| `-i`, `--interval` | No | `300` | Intervalo del agente en segundos, que se escribe en el documento |
| `-d`, `--data_in` | No | `/var/spool/pandora/data_in/` | Directorio de datos local del documento de agente. Se usa solo cuando no hay dirección de Tentacle. Mantenga la `/` final |
| `-l`, `--logs` | No | Desactivado | Envía los anuncios de servicio al colector de logs de Pandora FMS |
| `-n`, `--nodata` | No | Desactivado | Omite los módulos de estado e incidencias; útil junto con `-l` |
| `--tentacle_address` | No | Ninguna | Dirección del servidor Tentacle. Cuando se indica, el documento se envía por Tentacle en lugar de escribirse en `-d` |
| `--tentacle_port` | No | `41121` | Puerto del servidor Tentacle |
| `--tmp` | No | `/tmp/` | Directorio donde se escribe el documento antes del envío por Tentacle. Mantenga la `/` final |
| `--utf8` | No | `1` | `1` escribe los valores como texto. `0` los escribe como bytes crudos |

### Ejecución por línea de comandos

```text
pandora_o365 -c <CLIENT_ID> -t <TENANT_ID> -s <CLIENT_SECRET> [-a <NAME>] [-p <PREFIX>] [-g <GROUP>] [-i <SECONDS>] [-d <DIR>] [-l] [-n] [--tentacle_address <HOST>] [--tentacle_port <PORT>] [--tmp <DIR>] [--utf8 <0|1>]
```

| Condición | Comportamiento |
|-----------|----------------|
| Falta una opción obligatoria (`-c`, `-t`, `-s`) | Se imprime el resumen de uso en la salida de error y la ejecución termina con código de salida `2`, sin contactar con Microsoft |
| `-h` o `--help` | Se imprime el resumen de uso y la ejecución termina con código de salida `0`, sin contactar con Microsoft |
| Se rechaza la petición de token | Se imprime un error de autenticación en la salida de error y la ejecución termina con código de salida `1` |
| Se rechaza la petición de estado | Se imprimen el motivo y el estado HTTP y la ejecución termina con código de salida `1` |
| Se rechaza la petición de anuncios | La ejecución termina con código de salida `157` |
| Falla una etapa de recogida tras una petición correcta | `error data: …` o `error logs: …` en la salida de error; la ejecución continúa e imprime el número de resumen |
| Falla un envío por Tentacle | `Tentacle error` en la salida de error; la ejecución continúa, imprime el número de resumen y termina con código de salida `0` |
| El nombre del archivo de destino ya existe | `ERROR - Could not write file: … File exists` y la ejecución termina con código de salida `1` |
| Cualquier otra ejecución completada | Se imprime el número de resumen y la ejecución termina con código de salida `0` |

### Agente generado

| Propiedad | Valor |
|-----------|-------|
| Nombre | `<prefijo>_<hash MD5 del valor de -a>` |
| Alias | `<prefijo>_<valor de -a>` |
| Descripción | `Agent generated by pandora_o365 plugin` |
| Dirección | `127.0.0.1` |
| Grupo | El valor de `-g` |
| Intervalo | El valor de `-i` |
| Archivo del documento | `<directorio de datos><nombre del agente>.<EPOCH>.data`, o el mismo nombre en `--tmp` antes de un envío por Tentacle |

### Módulos generados

| Módulo | Tipo | Valor |
|--------|------|-------|
| `<prefijo>_<id de servicio>_status` | `generic_data_string` | El estado del servicio que devuelve Microsoft Graph |
| `<prefijo>_<id de servicio>_active_issues` | `generic_data_string` | Incidencias sin resolver como `<id>: <título>`, concatenadas sin separador; `None` cuando no hay ninguna |

El número de módulos depende de los servicios a los que está suscrito el tenant;
el plugin no crea módulos para nada más y no crea los módulos de licencias que
ofrece el addon de Discovery.

### Identidad del plugin

| Propiedad | Valor |
|-----------|-------|
| Identificador del Marketplace | `pandorafms.office365_plugin` |
| Nombre | Pandora Office 365 Monitoring |
| Versión | `1.0` |
| Paquete | `pandorafms.office365_plugin.1.0.zip` |
| Última actualización en el Marketplace | 2025-07-01 |
| Autor | Pandora FMS |
| Disponibilidad | Descarga limitada a usuarios con licencia |
| Licencia | `One` |
| Mantenimiento | El Marketplace indica que el addon ya no se mantiene activamente y sugiere las alternativas que figuran en la entrada |
