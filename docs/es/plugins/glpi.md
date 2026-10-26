# GLPI

*Última actualización del artículo: 2026-10-26.*

## Qué hace

El addon GLPI conecta las alertas de Pandora FMS con la mesa de servicio de
GLPI. No es un plugin de monitorización: no crea agentes ni módulos de
monitorización. Un comando de alerta de Pandora FMS lo ejecuta una vez por cada
evento de alerta, y esa ejecución crea, comenta o sustituye un ticket de GLPI a
través de la API REST de GLPI.

Cada ejecución trabaja sobre **un grupo de GLPI** y hace una de estas tres cosas:

- **Crear un ticket** cuando el módulo de Pandora FMS no tiene ningún ticket
  registrado para ese grupo.
- **Añadir un comentario de seguimiento** al ticket registrado mientras está
  abierto.
- **Sustituir el ticket** cuando el registrado está resuelto o cerrado, de forma
  que el siguiente incidente abra un ticket nuevo en lugar de reabrir uno
  terminado.

El addon guarda el vínculo entre un módulo y sus tickets en el campo **ID
personalizado** del módulo, con una entrada por grupo de GLPI, y lee y escribe
ese campo a través de la API de la consola de Pandora FMS. No almacena nada en
disco: el fichero de log es el único artefacto local.

Dos modos de ejecución gobiernan el ciclo de vida del ticket:

- `--recovery 0` (disparo) crea tickets y actualiza su contenido.
- `--recovery 1` (recuperación) comenta el ticket abierto y elimina la
  asociación cuando el ticket ya está cerrado.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
|--------|--------|-----------|
| Pandora FMS NG 784 y posteriores | `Supported` | El Marketplace indica que sus integraciones son compatibles con Pandora FMS NG 784 y versiones posteriores |
| Una instancia de GLPI cuya API REST responda en `/apirest.php`, accesible desde el host que ejecuta el comando de alerta | `Required` | Todas las operaciones usan ese punto de entrada; el addon añade `/apirest.php/...` a `--url` |
| Una consola nodo de Pandora FMS cuya API pueda leer y escribir el ID personalizado del módulo, con el host incluido en la *Lista de IPs con acceso al API* de la consola | `Required` | La asociación se lee y se escribe mediante `include/api.php` antes y después de las llamadas a GLPI |
| Versiones de GLPI | `Not validated` | No hay una matriz de versiones de GLPI registrada para este addon |
| Sistema operativo del host que ejecuta el comando de alerta | `Not validated` | No hay un sistema operativo registrado para la versión `1.0` |
| Plugins de GLPI instalados o campos de ticket personalizados | `Not validated` | El addon solo usa tipos de elemento estándar |

La versión de GLPI, la cuenta de GLPI y la consola nodo son requisitos de
operación, no declaraciones de compatibilidad.

### Requisitos

1. **Conectividad** desde el servidor de Pandora FMS que ejecuta el comando de
   alerta hasta la instancia de GLPI, preferiblemente por HTTPS.
2. **Una cuenta de GLPI y un token de aplicación de la API.** Todas las
   peticiones llevan las credenciales de la cuenta como autenticación básica HTTP
   y el token en la cabecera `App-Token`. La cuenta debe poder leer los
   ordenadores de GLPI, buscar y leer tickets, crear tickets, añadir
   seguimientos y vincular un ordenador a un ticket.
3. **Una consola nodo de Pandora FMS** que almacene el módulo al que pertenece la
   alerta, con la API de consola habilitada. El host que ejecuta el comando debe
   figurar en la *Lista de IPs con acceso al API* de la consola, y el usuario de
   la API debe poder leer el agente del módulo y tener permiso de escritura sobre
   él: el cambio del ID personalizado del módulo se comprueba contra la ACL de
   escritura. Las funciones de ID personalizado no se sirven en modo metaconsola,
   así que `--api_url` debe apuntar a la consola nodo.
4. **Identificadores numéricos de GLPI** para la categoría y el grupo del ticket,
   además de la prioridad y el tipo de petición que se quieran usar. El addon los
   envía como números; no resuelve nombres.
5. **Un ordenador de GLPI cuyo nombre coincida con el alias del agente de Pandora
   FMS** cuando el ticket deba quedar vinculado a ese ordenador. La comparación
   no distingue mayúsculas de minúsculas. Sin coincidencia el ticket se crea
   igualmente, pero no se vincula a ningún ordenador y queda en la entidad `0`.

### Instalar el addon

La entrada del Marketplace distribuye el addon como `pandorafms.glpi.1.0.zip`, con
descarga gratuita. Extraiga el ejecutable `pandora_glpi` y cópielo al servidor de
Pandora FMS que ejecuta el comando de alerta — por ejemplo
`/usr/share/pandora_server/util/plugin/pandora_glpi` — y déle permiso de
ejecución.

El addon no tiene fichero de configuración: todos los ajustes son argumentos de
línea de comandos, y el comando de alerta es el lugar donde se guardan.

### Preparar el fichero de log

El log por defecto es `/tmp/glpi_logfile.txt`. Para conservar el registro entre
reinicios, cree antes el directorio de otra ruta, por ejemplo `/var/log/pandora`,
y dé permiso de escritura al usuario que ejecuta el proceso del servidor de
Pandora FMS. El addon crea el fichero cuando falta, pero no su directorio; una
ruta no escribible solo muestra un error y la ejecución continúa.

## Configuración

Pandora FMS ejecuta el addon desde un **comando de alerta**, y cada **acción de
alerta** guarda los valores de los campos para el evento de disparo y para el de
recuperación. Un comando y dos conjuntos de valores cubren los dos modos de
`--recovery`.

### Crear el comando de alerta

1. Abra **Alertas → Comandos → Crear**.
2. Rellene **Nombre**, **Grupo** y **Descripción** con algo que los operadores de
   la alerta reconozcan, por ejemplo `Ticket GLPI`.
3. Pegue el comando, manteniendo una línea por grupo de argumentos:

```bash
/usr/share/pandora_server/util/plugin/pandora_glpi \
  -u _field1_ -x _field2_ -i _field3_ -a _field4_ \
  -n _agent_ -m _id_module_ \
  -t "_alert_name_ - _module_" \
  -d "_timestamp_ | _module_ | _data_" \
  -p _field5_ -c _field6_ -g _field7_ -k _field8_ \
  -l /var/log/pandora/glpi.log -r _field9_
```

4. Dé una descripción a cada campo. El comando usa estos campos:

| Campo | Descripción que debe introducir | Valores sugeridos |
|-------|---------------------------------|-------------------|
| `_field1_` | Usuario de GLPI | La cuenta que crea los tickets |
| `_field2_` | Contraseña de GLPI — marque **Ocultar** | — |
| `_field3_` | URL base de GLPI, sin barra final | `https://<GLPI_URL>` |
| `_field4_` | Token de aplicación de GLPI — marque **Ocultar** | `<APP_TOKEN>` |
| `_field5_` | Prioridad del ticket de GLPI | `1` a `6`, consulte [Prioridad del ticket](#prioridad-del-ticket) |
| `_field6_` | ID de categoría de GLPI | `<CATEGORY_ID>` |
| `_field7_` | ID de grupo de GLPI | `<GROUP_ID>` |
| `_field8_` | Título del ticket cuando no se encuentra el ordenador en GLPI | `Ordenador desconocido` |
| `_field9_` | Modo: `0` disparo, `1` recuperación | `0` o `1` |

5. En **Valores del campo 9**, escriba `0,Disparo;1,Recuperación` para que el
   campo sea una lista de selección en lugar de una caja de texto libre.

<!-- SCREENSHOT NEEDED: Formulario de creación de comando de alerta en español con el comando de GLPI, las nueve descripciones de campo y los campos de contraseña y token ocultos, sin credenciales reales visibles. -->

`_agent_`, `_id_module_`, `_alert_name_`, `_module_`, `_data_` y `_timestamp_`
son macros de alerta de Pandora FMS, que se expanden antes de que arranque el
addon. `_agent_` devuelve el alias del agente, que es exactamente el valor que el
addon compara con el nombre del ordenador en GLPI. Mantenga `-m` como
`_id_module_` salvo que el comando sirva a un único módulo fijo: el ID del módulo
decide qué módulo guarda la asociación del ticket.

### Crear la acción de alerta

1. Abra **Alertas → Acciones → Crear**.
2. En **Comando**, elija el comando creado arriba y rellene sus campos en
   **Disparo** con `_field9_` = `0`.
3. Rellene los mismos campos en **Recuperación** con `_field9_` = `1`.
4. Ajuste **Umbral** a un valor que evite que un módulo inestable ejecute el
   comando repetidamente en un intervalo corto.
5. Guarde la acción y aplíquela mediante una plantilla de alerta o directamente
   sobre el módulo.

<!-- SCREENSHOT NEEDED: Formulario de acción de alerta en español con el comando de GLPI seleccionado, los valores de campo de disparo y los de recuperación, sin credenciales reales visibles. -->

Los dos conjuntos de valores se guardan en la acción, así que el mismo comando
sirve para todos los módulos. Los valores que cambian por módulo son los que
Pandora FMS expande como macros; los que cambian por alerta son los valores de
los campos.

### Prioridad del ticket

`--ticket_priority` es la prioridad numérica de GLPI. GLPI define esta escala:

| Valor | Prioridad |
|-------|-----------|
| `1` | Muy baja |
| `2` | Baja |
| `3` | Media |
| `4` | Alta |
| `5` | Muy alta |
| `6` | Mayor |

`--ticket_request_type` también es un identificador numérico — `8` por defecto —
y debe ser un tipo de petición que exista en su instancia de GLPI.

### Contenido del ticket y la macro `%ticketID%`

`--ticket_name` y `--ticket_description` se convierten en el título y el
contenido del ticket. Ambos aceptan la macro `%ticketID%`, que el addon sustituye
por el ID del ticket que acaba de crear. GLPI almacena el contenido tal como se
envía, así que puede incluir su marcado en `--ticket_description` cuando quiera
un cuerpo de ticket con formato.

La macro se resuelve actualizando el ticket justo después de crearlo, así que el
ticket existe durante un instante con el texto literal `%ticketID%`. Si esa
actualización es rechazada, el ticket conserva el texto literal.

`--ticket_name_error` es el título que se usa cuando ningún ordenador de GLPI
coincide con el alias del agente, pero el addon renombra el ticket nuevo al
`--ticket_name` resuelto inmediatamente después: en la práctica ambos títulos
acaban siendo el mismo. Consulte [Limitaciones](#limitaciones).

### El ID personalizado del módulo

El addon guarda su estado en el campo **ID personalizado** del módulo indicado por
`--id_module`, como un mapa de grupo de GLPI → ID de ticket. Lee ese mapa antes de
crear o comentar un ticket y lo escribe después de crear o cerrar uno.

- Trate ese campo como propiedad del addon. Si lo sobrescribe con texto libre, el
  addon no puede interpretarlo, toma el mapa como vacío y crea un ticket nuevo la
  próxima vez que se dispare la alerta.
- `--ticket_group` es a la vez el grupo de GLPI asignado al ticket y la clave del
  mapa. Cambiar el grupo en un comando inicia una asociación nueva, así que el
  siguiente disparo crea un ticket nuevo en lugar de comentar el existente.
- Un módulo puede mantener un ticket abierto por grupo. Use grupos distintos — en
  comandos o acciones separados — cuando un mismo módulo deba abrir tickets en
  colas diferentes de GLPI.

## Verificación

Ejecute el addon a mano antes de confiarle una alerta. Use un módulo y un agente
de prueba, porque una ejecución correcta crea un ticket real.

```bash
/usr/share/pandora_server/util/plugin/pandora_glpi \
  -u '<USERNAME>' -x '<PASSWORD>' -i 'https://<GLPI_URL>' -a '<APP_TOKEN>' \
  -n 'agente-de-prueba' -m <MODULE_ID> \
  -t 'Prueba Pandora FMS - %ticketID%' \
  -d 'Ejecución manual de verificación' \
  -p 3 -c <CATEGORY_ID> -g <GROUP_ID> -k 'Ordenador desconocido' \
  -l /var/log/pandora/glpi.log -r 0
```

Una ejecución que crea un ticket termina con líneas como estas en la salida
estándar:

```text
Succesful: Added custom id ' <GROUP_ID> : <TICKET_ID> ' in module with id <MODULE_ID>
Succesful: Ticket created successfully.
```

Compruebe los cuatro resultados:

1. **La salida estándar** muestra las dos líneas anteriores.
2. **El fichero de log** contiene los mismos mensajes con la marca de tiempo
   delante.
3. **GLPI** tiene el ticket nuevo, con el título y el contenido del comando.
4. **El módulo** de Pandora FMS muestra la asociación en su campo de ID
   personalizado.

Después repita la ejecución con `-r 1` y los mismos argumentos. Esta vez el addon
añade un comentario de seguimiento al ticket existente en lugar de crear uno:

```text
Succesful: Added tracking in the ticket : <TICKET_ID>
```

<!-- SCREENSHOT NEEDED: Ticket de GLPI creado por el addon en español, con título, contenido, prioridad, categoría, grupo asignado y el ordenador vinculado, solo con datos de laboratorio. -->

<!-- SCREENSHOT NEEDED: Campo de ID personalizado del módulo en el editor de módulos de Pandora FMS en español tras una ejecución, mostrando la asociación de grupo y ticket. -->

## Entender los resultados

El addon decide qué hacer a partir de dos datos: la asociación guardada en el
módulo y el estado actual del ticket asociado.

| Asociación del grupo | `--recovery 0` (disparo) | `--recovery 1` (recuperación) |
|----------------------|--------------------------|-------------------------------|
| Ninguna | Crea un ticket, vincula el ordenador cuando existe y guarda el ID del ticket | No crea nada; registra `Error: There is no ticket open for the module with id <MODULE_ID> and group <GROUP_ID>` |
| Ticket abierto — cualquier estado distinto de `5` o `6` | Añade un comentario de seguimiento con el `--ticket_description` resuelto; ningún ticket nuevo | Añade el mismo comentario de seguimiento |
| Ticket resuelto (`5`) o cerrado (`6`) | Crea un ticket nuevo, sustituye el ID guardado por el nuevo y vincula el ordenador | Elimina la entrada guardada y añade el comentario de seguimiento al ticket cerrado |

Un ticket creado lleva estos valores:

| Campo del ticket | Valor |
|------------------|-------|
| Título | `--ticket_name`, con `%ticketID%` resuelto |
| Contenido | `--ticket_description`, con `%ticketID%` resuelto |
| Prioridad | `--ticket_priority` |
| Categoría | `--ticket_category` |
| Grupo asignado | `--ticket_group` |
| Tipo de petición | `--ticket_request_type` |
| Entidad | La entidad del ordenador de GLPI que coincide; `0` cuando no coincide ninguno. Al sustituir un ticket cerrado, la entidad del ticket anterior |
| Ordenador vinculado | El ordenador de GLPI cuyo nombre coincide con `--alias_agent`, sin distinguir mayúsculas |

Consecuencias que conviene conocer:

- **Un ticket resuelto cuenta como cerrado.** El estado `5` (Resuelto) de GLPI
  basta para que el siguiente disparo abra un ticket nuevo, aunque el ticket
  todavía no se haya cerrado.
- **El addon nunca cierra, resuelve ni borra el ticket.** Una recuperación solo
  comenta; cerrar el ticket es un flujo manual o del lado de GLPI.
- **Los disparos repetidos no duplican tickets** mientras el ticket siga abierto:
  todos los disparos posteriores al primero añaden un comentario.
- **El comentario usa los valores actuales del comando.** El seguimiento que se
  añade en la recuperación lleva la descripción resuelta para esa ejecución, así
  que el historial del ticket conserva la secuencia de eventos que reportó la
  alerta.

## Operar y resolver problemas

### Planificación y concurrencia

- Cada ejecución es puntual: se autentica, trabaja sobre un grupo, cierra la
  sesión de GLPI y termina. No hay demonio, ni estado en disco, ni ejecución en
  segundo plano, así que una ejecución manual en cualquier momento es segura.
- El addon se apoya en el sentido de la alerta. No lee el estado del módulo para
  decidir entre disparo y recuperación; por eso `--recovery` debe venir de los
  valores de campo de la acción.
- **Evite ejecuciones solapadas para el mismo módulo y grupo.** La asociación se
  lee al principio y se escribe después de crear el ticket, así que dos
  ejecuciones que empiecen a la vez pueden crear dos tickets. Un **Umbral** de
  acción distinto de cero reduce esa ventana.
- Toda ejecución que tenga que crear un ticket recorre todo el inventario de
  ordenadores de GLPI página a página para buscar el alias del agente. Con un
  inventario grande esto es lento: suba `--pagination_results` desde su valor por
  defecto `1` cuando la ejecución tarde demasiado.

### Credenciales y transporte

- La contraseña de GLPI, el token de aplicación y las credenciales de consola son
  argumentos de línea de comandos. Son visibles en la lista de procesos mientras
  el addon se ejecuta, y quedan guardados en el comando y en la acción de alerta
  dentro de la consola. Marque los campos secretos con **Ocultar**, restrinja
  quién puede leer los comandos de alerta y proteja la lista de procesos del
  servidor.
- La contraseña de la API de consola y la del usuario de consola viajan en la
  cadena de consulta de la URL de `include/api.php`, así que pueden quedar
  registradas en el log de acceso del servidor web de la consola. Use un usuario
  de API dedicado con los permisos mínimos que permitan leer el módulo y cambiar
  su ID personalizado.
- Los certificados HTTPS se verifican contra el almacén de confianza del host. El
  addon no tiene opción para desactivar la verificación ni para aportar un
  certificado de CA: una instancia de GLPI con certificado de una CA privada
  necesita esa CA instalada en el host.
- Con HTTP simple las credenciales de GLPI viajan sin cifrar en la cabecera
  `Authorization`. Restrinja GLPI a una red de confianza o sitúelo detrás de TLS.

### Estado de salida y log

Todos los errores gestionados se imprimen en la salida estándar y se añaden al
fichero de log con el prefijo `YYYY-MM-DD HH:MM:SS - `. El estado de salida no es
una señal fiable de éxito:

| Estado | Significado |
|--------|-------------|
| `0` | La ejecución terminó. La mayoría de los fallos gestionados — credenciales rechazadas, creación de ticket rechazada, comentario rechazado — también terminan con `0` después de imprimir el error |
| `2` | La línea de comandos se rechazó antes de cualquier petición: falta un argumento obligatorio o un valor tiene un tipo incorrecto, por ejemplo el nombre de una categoría en lugar de su ID numérico |

Lea el fichero de log, o compruebe el ticket en GLPI, para decidir si una
ejecución funcionó. El log solo se añade y lo comparten todas las ejecuciones,
así que rótelo.

### Fallos habituales

| Síntoma | Causa y comprobación |
|---------|----------------------|
| `Unauthorized: Check your credentials.` | GLPI rechazó el inicio de sesión. Compruebe `--user`, `--password` y `--app_token`, y que la cuenta de GLPI esté activa |
| `Error logging in: <estado> - <cuerpo>` | La API de GLPI respondió con un error distinto de un fallo de autenticación. El cuerpo es el mensaje de GLPI |
| `Bad Request: <cuerpo>` al leer o escribir el ID personalizado | La API de consola rechazó la petición. Compruebe `--api_pass`, `--api_user`, `--api_user_pass`, la entrada del host en la *Lista de IPs con acceso al API* y que `--api_url` apunte a una consola nodo |
| `Error getting custom id: <estado> - <cuerpo>` / `Error setting custom id: ...` | La API de consola respondió con un error distinto de una petición mal formada. El cuerpo lo identifica |
| `Bad Request: <cuerpo>` después de un disparo | GLPI rechazó el ticket. El cuerpo nombra el campo culpable: normalmente una categoría, un grupo o un tipo de petición que no existe en esa instancia |
| `Error: There is no ticket open for the module with id <MODULE_ID> and group <GROUP_ID>` | Una recuperación se ejecutó sin asociación. Confirme que la recuperación usa el mismo `--id_module` y el mismo `--ticket_group` que el disparo |
| Dos tickets para el mismo incidente | Dos disparos solapados, o un cambio de `--ticket_group` entre ejecuciones |
| Cada disparo crea un ticket nuevo y el ID personalizado del módulo sigue vacío | `--api_url` apunta a una metaconsola, donde no se sirven las funciones de ID personalizado. Use la consola nodo que almacena el módulo |
| La ejecución se detiene con un error inesperado tras el inicio de sesión | La sesión de GLPI caducó o el ticket no se pudo leer. El log registra lo que el addon había hecho hasta ese punto |
| No se escribe nada en el log | La ruta del log no es escribible. El addon muestra el error de escritura y continúa |

### Limitaciones

- Una instancia de GLPI por ejecución. Los tickets en dos instancias requieren dos
  comandos.
- Un ticket por módulo y grupo a la vez.
- `--ticket_name_error` no sobrevive a la ejecución: el addon renombra el ticket al
  `--ticket_name` resuelto justo después de crearlo, así que el título para un
  ordenador desconocido se sustituye. Use `%ticketID%` y la descripción para
  señalar el ordenador ausente.
- No se establece tiempo de espera de petición. Si GLPI acepta la conexión y deja
  de responder, el comando de alerta se queda esperando; envuelva la llamada en el
  comando `timeout` del sistema si ese riesgo importa en su instalación.
- El addon cierra la sesión de GLPI solo al final de una ejecución completada. Una
  ejecución que sale antes deja su sesión abierta hasta que GLPI la caduque.
- El fichero de log es el único rastro de auditoría que guarda el addon; el
  historial del ticket en GLPI es el registro de lo que reportaron las alertas.

## Referencia

### Argumentos de línea de comandos

| Argumento | Obligatorio | Por defecto | Descripción |
|-----------|-------------|-------------|-------------|
| `-u`, `--user` | Sí | — | Cuenta de GLPI con la que se autentica |
| `-x`, `--password` | Sí | — | Contraseña de la cuenta de GLPI |
| `-i`, `--url` | Sí | — | URL base de GLPI; el addon añade `/apirest.php/...` |
| `-a`, `--app_token` | Sí | — | Token de aplicación de GLPI, enviado en la cabecera `App-Token` |
| `-n`, `--alias_agent` | Sí | — | Alias del agente, comparado sin distinguir mayúsculas con los nombres de ordenador de GLPI |
| `-m`, `--id_module` | Sí | — | ID numérico del módulo de Pandora FMS que guarda la asociación de tickets |
| `-t`, `--ticket_name` | Sí | — | Título del ticket. Acepta `%ticketID%` |
| `-d`, `--ticket_description` | Sí | — | Contenido del ticket y comentario de seguimiento. Acepta `%ticketID%` |
| `-p`, `--ticket_priority` | Sí | — | Prioridad numérica de GLPI, de `1` a `6` |
| `-c`, `--ticket_category` | Sí | — | ID numérico de la categoría de GLPI |
| `-g`, `--ticket_group` | Sí | — | ID numérico del grupo de GLPI asignado al ticket, y clave de la asociación guardada |
| `-k`, `--ticket_name_error` | Sí | — | Título usado cuando ningún ordenador de GLPI coincide con el alias del agente. Se sustituye por `--ticket_name` justo después de crear el ticket |
| `-j`, `--ticket_request_type` | No | `8` | ID numérico del tipo de petición de GLPI |
| `-l`, `--log_file` | No | `/tmp/glpi_logfile.txt` | Fichero de log, al que se añaden líneas con marca de tiempo |
| `-r`, `--recovery` | No | `0` | `0` para disparo, `1` para recuperación |
| `--api_url` | No | `http://localhost` | URL base de la consola nodo de Pandora FMS; el addon añade `/pandora_console/include/api.php` |
| `--api_user` | No | `admin` | Usuario de la API de consola |
| `--api_pass` | No | `1234` | Contraseña de la API de consola, enviada como `apipass` |
| `--api_user_pass` | No | `pandora` | Contraseña del usuario de la API de consola |
| `--pagination_results` | No | `1` | Paso de página usado al recorrer el inventario de ordenadores de GLPI |
| `-h`, `--help` | No | — | Muestra el resumen de uso y termina |

El resumen de uso del addon documenta un argumento `--ticket_message`. Ese
argumento no existe: el contenido del ticket es `--ticket_description`.

### Ejecución y salida

| Condición | Comportamiento |
|-----------|----------------|
| La línea de comandos no incluye un argumento obligatorio | El addon muestra el resumen de uso, nombra los argumentos que faltan y termina con estado `2` |
| Un argumento numérico recibe texto, por ejemplo el nombre de una categoría | El addon muestra el valor rechazado y termina con estado `2` |
| GLPI rechaza el inicio de sesión | Muestra `Unauthorized: Check your credentials.`, lo añade al log y termina |
| No se puede leer el ID personalizado del módulo | Muestra la respuesta de la API de consola y se detiene sin tocar GLPI |
| Sin asociación y `--recovery 0` | Crea el ticket, guarda el ID y muestra dos líneas de confirmación |
| Sin asociación y `--recovery 1` | Muestra `Error: There is no ticket open for the module with id ... and group ...` |
| Asociación a un ticket abierto | Añade un comentario de seguimiento y muestra `Succesful: Added tracking in the ticket : <TICKET_ID>` |
| Asociación a un ticket resuelto o cerrado, `--recovery 0` | Crea un ticket nuevo y sustituye el ID guardado |
| Asociación a un ticket resuelto o cerrado, `--recovery 1` | Elimina la entrada guardada y añade el comentario de seguimiento al ticket cerrado |
| La ejecución termina | Cierra la sesión de GLPI y sale |

### Identidad del addon

| Propiedad | Valor |
|-----------|-------|
| Identificador del Marketplace | `pandorafms.glpi` |
| Nombre | GLPI |
| Versión | `1.0` — la versión del paquete del Marketplace `pandorafms.glpi.1.0.zip`, que también muestra el resumen de uso del addon |
| Categoría | Miscelaneus |
| Licencia | Free |
| Última actualización del Marketplace | 2026-01-28 |
| Disponibilidad | Descarga gratuita |
| Entrada del Marketplace | [pandorafms.glpi](https://marketplace.pandorafms.com/entries/pandorafms.glpi) |
