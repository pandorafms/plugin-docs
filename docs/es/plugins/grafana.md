# Grafana

*Última actualización del artículo: 2026-10-26.*

## Qué hace

El addon Grafana es un **plugin de origen de datos para Grafana**. No es un
plugin de monitorización de Pandora FMS: se instala dentro de Grafana, no
ejecuta ningún proceso en un servidor de Pandora FMS y no crea agentes ni
módulos. Añade **Pandorafms Grafana** a la lista de orígenes de datos de
Grafana, de forma que los paneles de Grafana pueden representar el histórico de
los módulos numéricos de Pandora FMS.

Los datos proceden de la **extensión API de Grafana de la consola de Pandora
FMS**, situada en `pandora_console/extensions/grafana`. El addon guarda la URL
base de esa extensión y un usuario y una contraseña de Pandora FMS, pide a la
extensión los grupos, agentes y módulos que ese usuario puede ver, y después
solicita los valores de un módulo para el rango de tiempo de cada panel.

Dos rutas de ejecución usan el origen de datos configurado:

- **Los paneles consultan desde el cliente web de Grafana.** El navegador de
  cada usuario de Grafana envía las peticiones a la consola de Pandora FMS, así
  que el navegador —no solo el servidor de Grafana— debe poder alcanzarla.
- **Las reglas de alerta las evalúa el servidor de Grafana.** El servidor también
  debe alcanzar la consola, y la ruta del lado del servidor de esta versión no
  recibe datos (véase [Reglas de alerta](#reglas-de-alerta)).

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
|--------|--------|-----------|
| Pandora FMS NG 784 y posteriores | `Supported` | El Marketplace indica que sus integraciones son compatibles con Pandora FMS NG 784 y versiones posteriores |
| Grafana `10.0.3` o posterior | `Required` | El plugin declara `grafanaDependency` `>=10.0.3` |
| Una consola nodo de Pandora FMS con la extensión API de Grafana disponible | `Required` | El addon añade `/search` y `/query` a la URL configurada de la extensión, y la extensión responde `403` en una metaconsola |
| Un usuario de Pandora FMS con el privilegio de lectura de agentes (`AR`) | `Required` | Ambos puntos de la extensión comprueban ese privilegio antes de devolver ningún grupo |
| Versiones de Grafana posteriores al mínimo declarado | `Not validated` | No hay una matriz de versiones de Grafana registrada para este addon |
| Sistema operativo del host de Grafana | `Not validated` | El addon se ejecuta dentro de Grafana; no hay un sistema operativo registrado |

La versión de Pandora FMS, la versión de Grafana y la consola nodo son
requisitos de instalación, no declaraciones de compatibilidad sobre otras
versiones.

### Requisitos

#### En el lado de Pandora FMS

1. **Una consola nodo, no la metaconsola.** La extensión responde `403` cuando se
   ejecuta en un nodo de metaconsola. Apunte el origen de datos a la consola nodo
   que almacena los agentes que quiere representar.
2. **La extensión API de Grafana servida por esa consola.** Forma parte del
   directorio de la consola (`pandora_console/extensions/grafana`) y no necesita
   una instalación aparte en el lado de Pandora FMS. Responde en
   `https://<PANDORA_FMS_URL>/pandora_console/extensions/grafana/`.
3. **Un usuario de Pandora FMS con el privilegio de lectura de agentes (`AR`)**
   y su contraseña. La extensión no devuelve datos cuando el usuario no tiene
   ese privilegio, y solo devuelve los grupos en los que lo tiene.
4. **Un origen CORS que permita la URL de Grafana.** La extensión envía
   `Access-Control-Allow-Origin` con el valor de
   **Configuración → General → Seguridad**, campo
   **Grafana Access-Control-Allow-Origin**. El valor predeterminado es `*`, que
   permite cualquier origen. Indique el origen del servidor de Grafana —esquema,
   host y puerto— para restringirlo.

#### En el lado de Grafana

1. **Grafana `10.0.3` o posterior.**
2. **Permiso de escritura en el directorio de plugins de Grafana y en
   `grafana.ini`**, además de permiso para reiniciar Grafana. En los paquetes de
   Linux el directorio de plugins es `/var/lib/grafana/plugins`.
3. **El plugin cargado como plugin sin firmar** (véase
   [Permitir el plugin sin firmar](#permitir-el-plugin-sin-firmar)).

#### Red

- El navegador de cada usuario de Grafana que abre un panel debe alcanzar la
  consola de Pandora FMS.
- El servidor de Grafana debe alcanzar la consola para evaluar las reglas de
  alerta.

### Instalar el origen de datos

1. Descargue `pandorafms.grafana.1.0.zip` desde la
   [entrada del Marketplace](https://marketplace.pandorafms.com/entries/pandorafms.grafana).
   La descarga está limitada a usuarios con licencia.
2. Extraiga el archivo dentro del directorio de plugins de Grafana, de forma que
   la carpeta del plugin quede directamente debajo de él:

```bash
cd /var/lib/grafana/plugins
sudo unzip /path/to/pandorafms.grafana.1.0.zip
```

3. Reinicie Grafana para que cargue el plugin.

<!-- SCREENSHOT NEEDED: Lista de orígenes de datos de Grafana tras la instalación, mostrando el tipo de origen de datos Pandorafms Grafana. -->

### Permitir el plugin sin firmar

El plugin no está firmado, así que Grafana solo lo carga cuando su identificador
figura como permitido. Añada la clave a `/etc/grafana/grafana.ini`:

```ini
[plugins]
allow_loading_unsigned_plugins = "pandorafms-pandorafmsgrafana-datasource"
```

Si la clave ya enumera otros plugins, añada este identificador a la lista
separada por comas. Reinicie Grafana de nuevo tras el cambio.

`pandorafms-pandorafmsgrafana-datasource` es el identificador del plugin de
origen de datos y debe coincidir exactamente. Sin él, Grafana no carga el plugin
y **Pandorafms Grafana** no aparece en la lista de orígenes de datos.

## Configuración

### Crear el origen de datos

1. En Grafana abra **Connections → Data sources** y seleccione
   **Add data source**.
2. Elija **Pandorafms Grafana**.
3. Rellene los tres campos:

| Campo | Obligatorio | Por defecto | Descripción |
|-------|-------------|-------------|-------------|
| **Pandora extension** | Sí | — | URL base de la extensión API de Grafana de Pandora FMS, con el esquema y sin barra final ni sufijo de punto de entrada: `https://<PANDORA_FMS_URL>/pandora_console/extensions/grafana`. El addon añade `/search` y `/query`. |
| **Pandora user** | Sí | — | Usuario de Pandora FMS con el privilegio `AR`. Todos los usuarios de Grafana consultan con esta identidad. |
| **Password** | Sí | — | Contraseña de ese usuario. Se guarda en los ajustes JSON del origen de datos, no en los campos seguros cifrados de Grafana, porque el navegador la envía en cada petición. |

4. Seleccione **Save & Test**. La prueba no contacta con Pandora FMS (véase
   [Verificación](#verificacion)).

<!-- SCREENSHOT NEEDED: Ajustes del origen de datos Pandorafms Grafana con una URL de extensión de laboratorio, un usuario y una contraseña enmascarada, sin credenciales reales. -->

Notas:

- Use una URL de extensión `https` siempre que la consola se sirva por TLS. Si
  Grafana se sirve por HTTPS, el navegador bloquea una URL de extensión `http`
  por contenido mixto.
- Cualquier usuario de Pandora FMS con el privilegio `AR` es válido; no necesita
  permisos de administración. Sí necesita ver todos los grupos cuyos módulos
  deban aparecer en los paneles, porque la lista de grupos solo contiene los
  grupos en los que el usuario tiene `AR`.

### Crear una consulta de panel

1. Cree un panel de dashboard, añada un panel y seleccione **Pandorafms Grafana**
   en **Query**.
2. Elija **Group**, después **Agent** y después **Module**. Las listas se
   estrechan en ese orden, y **Module** permanece vacía hasta que se selecciona
   un **Agent**.
3. El panel muestra una serie por consulta.

| Campo | Por defecto | Descripción |
|-------|-------------|-------------|
| **Label** | Vacío | No se usa. El addon no lo envía, y la serie conserva el nombre del módulo. |
| **Tip** | Desmarcado | Conmutador de escala completa. Marcado, Pandora FMS devuelve las muestras almacenadas. Desmarcado, devuelve valores compactados (medias) y el nombre de la serie termina en ` (avg)`. |
| **Group** | Vacío | Restringe la lista de agentes. `All` (valor `0`) enumera todos los agentes. Solo aparecen los grupos en los que el usuario del origen de datos tiene `AR`. |
| **Agent** | Vacío | Restringe la lista de módulos a los agentes habilitados del grupo seleccionado; con `All`, a todos los agentes habilitados. |
| **Module** | Vacío | Módulo que se representa: módulos habilitados y no de cadena del agente seleccionado. La petición lleva el identificador del módulo. |

- Solo **Module** decide los datos. La extensión lee el identificador del módulo
  e ignora el valor del agente.
- Cambiar **Group** o **Agent** no borra el **Agent** ni el **Module**
  seleccionados anteriormente. El panel sigue consultando el módulo antiguo hasta
  que se elige uno nuevo, así que vuelva a seleccionar el módulo después de
  restringir las listas.
- Cada cambio en el editor recarga las tres listas completas, y un cambio de
  **Tip**, **Group**, **Agent** o **Module** ejecuta además la consulta. En
  instalaciones con muchos grupos, agentes o módulos esto hace más lento el
  editor.
- El origen de datos devuelve valores numéricos sin metadatos de unidad. Fije la
  unidad del panel según el módulo.
- Para comparar módulos, añada una consulta por módulo al mismo panel.

<!-- SCREENSHOT NEEDED: Editor de consulta de un panel de Grafana con el origen de datos Pandorafms Grafana y los campos Label, Tip, Group, Agent y Module con valores de laboratorio. -->

### Reglas de alerta

El origen de datos declara compatibilidad con alertas, así que una regla de
alerta de Grafana puede usar una consulta de Pandora FMS. Grafana evalúa las
reglas de alerta en el servidor, no en el navegador. En esta versión la ruta del
lado del servidor no lleva la URL de la extensión ni la contraseña guardadas en
el formulario, de modo que una regla evaluada por el servidor no recibe datos.
Consulte [Limitaciones](#limitaciones) antes de crear una, y pruebe cualquier
regla de extremo a extremo antes de confiar en ella.

## Verificación

**Save & Test no comprueba la conexión.** El origen de datos devuelve éxito sin
contactar con Pandora FMS, así que un resultado correcto solo significa que
Grafana guardó el formulario. Ejecute las dos comprobaciones siguientes.

### Comprobar la extensión directamente

```bash
curl -sS -u <USERNAME> \
  -H 'Content-Type: application/json' \
  -d '{"type":"group"}' \
  'https://<PANDORA_FMS_URL>/pandora_console/extensions/grafana/search'
```

`curl` pide la contraseña de forma interactiva, así que no aparece en el
historial del shell ni en la lista de procesos. La extensión acepta la
autenticación básica HTTP estándar que envía `curl`.

Un usuario con el privilegio `AR` recibe un array JSON con la entrada `All` en
primer lugar, seguida de una entrada por grupo:

```json
[{"value":0,"text":"All"},{"value":"<GROUP_ID>","text":"<GROUP_NAME>"}]
```

Interprete el resultado así:

| Resultado | Significado |
|-----------|-------------|
| Un array JSON con `All` y sus grupos | La extensión, la consola y las credenciales funcionan |
| `[]` | La extensión alcanzó Pandora FMS pero rechazó las credenciales, o el usuario no tiene el privilegio `AR`. Un inicio de sesión rechazado **no** es un error HTTP |
| `403` | La URL apunta a un nodo de metaconsola |
| `404` | La URL, el directorio de la extensión o la regla de reescritura del servidor web son incorrectos |

### Ejecutar una consulta desde Grafana

1. Abra un panel o Explore con el origen de datos **Pandorafms Grafana**.
2. Seleccione un grupo, un agente y un módulo con datos conocidos en el rango de
   tiempo elegido.
3. El resultado esperado es una serie con el nombre del módulo —con el sufijo
   ` (avg)` mientras **Tip** esté desmarcado— y puntos a lo largo del rango.
4. Marque **Tip** y ejecute la consulta de nuevo. Aparece la misma serie sin el
   sufijo y con las muestras originales.

Si la comprobación de la extensión funciona y el panel sigue sin datos, lea
[Operar y resolver problemas](#operar-y-resolver-problemas).

## Entender los resultados

- **Una serie por consulta.** Su nombre es el nombre del módulo que informa
  Pandora FMS. Con **Tip** desmarcado el addon añade ` (avg)` para indicar que
  los valores son medias compactadas; con **Tip** marcado la serie conserva las
  muestras originales. El campo **Label** no renombra la serie.
- **El rango de tiempo es el del panel.** La extensión calcula el periodo a
  partir del rango y devuelve el histórico del módulo dentro de él.
- **Los periodos desconocidos son huecos.** Cuando Pandora FMS no tiene valor, o
  marca los datos del módulo como desconocidos, el punto es nulo y el panel
  dibuja un hueco en lugar de un cero.
- **Solo módulos numéricos.** El selector de módulos excluye los módulos de
  cadena, así que no se pueden representar con este origen de datos. Los agentes
  y módulos deshabilitados también quedan fuera de los selectores.
- **Los permisos se detienen en la lista de grupos.** La extensión autentica al
  usuario de Pandora FMS, exige `AR` en al menos un grupo y filtra la lista de
  grupos por ese privilegio. Las búsquedas de agentes y módulos y la petición de
  datos se resuelven con los identificadores que envía el navegador, sin volver a
  comprobar el permiso de grupo. Considere que cualquier usuario de Grafana que
  pueda usar este origen de datos puede leer cualquier módulo numérico cuyo
  identificador se solicite.
- **Una sola identidad de Pandora FMS por origen de datos.** Todos los usuarios
  de Grafana que pueden usar el origen de datos leen los mismos datos con el
  mismo usuario de Pandora FMS. Los permisos propios de Grafana sobre el origen
  de datos deciden quién puede usarlo.

## Operar y resolver problemas

### Operación diaria

- El addon no tiene planificador: consulta Pandora FMS cuando se carga o se
  refresca un panel, y cuando se evalúa una regla de alerta. No guarda nada en el
  lado de Grafana más allá de los ajustes del origen de datos.
- Cada consulta es una petición a la extensión. Un panel con tres consultas de
  módulo envía tres peticiones.
- Mantenga la URL del origen de datos y la URL de la consola de Pandora FMS
  accesibles desde el navegador y desde el servidor de Grafana; un cambio en
  cortafuegos, proxies inversos o certificados TLS rompe los paneles.

### Permisos y transporte

- La contraseña se guarda en los ajustes JSON del origen de datos, porque el
  navegador la necesita para cada consulta. No se guarda en los campos seguros
  cifrados de Grafana y se devuelve al cliente web de Grafana. Restrinja quién
  puede leer o editar orígenes de datos en Grafana y use un usuario dedicado de
  Pandora FMS para el addon.
- La autenticación básica HTTP codifica las credenciales, no las cifra. Use una
  URL de extensión `https` para que las credenciales viajen cifradas.
- El origen CORS predeterminado es `*`: cualquier origen web puede llamar a la
  extensión cuando puede enviar credenciales. Indique el origen de Grafana en
  **Grafana Access-Control-Allow-Origin** para restringirlo.
- El usuario de Pandora FMS solo necesita el privilegio `AR`. No use una cuenta
  de administración para el origen de datos.

### Fallos habituales

| Síntoma | Causa y comprobación |
|---------|----------------------|
| **Save & Test** informa de éxito pero el panel no muestra datos | Es lo esperado: la prueba no contacta con Pandora FMS. Compruebe la extensión con el comando `curl` de [Verificación](#verificacion) |
| La lista **Group** está vacía | Credenciales rechazadas, un usuario sin `AR` o un bloqueo CORS. Ejecute la comprobación de la extensión y lea la consola del navegador |
| La lista **Module** está vacía | Todavía no se ha seleccionado ningún **Agent**; los agentes y módulos deshabilitados también quedan excluidos |
| El panel muestra **No data** | No hay valores almacenados en el rango de tiempo, el módulo es de cadena, o quedó seleccionado un módulo de un agente anterior. Vuelva a seleccionar el módulo y amplíe el rango |
| La consola del navegador muestra un error CORS | **Grafana Access-Control-Allow-Origin** no coincide con el origen de Grafana, o la URL de la extensión es `http` mientras Grafana es `https` |
| La extensión responde `403` | La URL apunta a un nodo de metaconsola; use la consola nodo |
| La extensión responde `404` | Ruta incorrecta (debe terminar en `/pandora_console/extensions/grafana`), directorio de la extensión ausente, o un servidor web que no aplica las reglas de reescritura que resuelven `/search` y `/query` |
| **Pandorafms Grafana** no aparece en la lista de orígenes de datos | La carpeta del plugin no está en el directorio de plugins, `allow_loading_unsigned_plugins` no incluye el identificador, o Grafana no se reinició |
| El nombre de la serie termina en ` (avg)` | **Tip** está desmarcado; márquelo para recibir las muestras originales |
| Una regla de alerta no devuelve datos | Véase [Limitaciones](#limitaciones): la ruta de evaluación del lado del servidor no usa los datos de conexión guardados en el formulario |

### Limitaciones

- **El campo `Label` no hace nada.** La serie siempre se llama como el módulo,
  con el sufijo ` (avg)` cuando los valores son compactados.
- **`Save & Test` siempre informa de éxito.** No abre ninguna conexión con
  Pandora FMS, así que no puede detectar una URL incorrecta, credenciales
  rechazadas ni una consola inalcanzable.
- **Un inicio de sesión rechazado no es un error.** Cuando el usuario o la
  contraseña son incorrectos, o el usuario no tiene el privilegio `AR`, la
  extensión responde HTTP `200` con un array vacío. El panel muestra **No data**
  en lugar de un error de autenticación.
- **Las reglas de alerta no alcanzan la consola en esta versión.** Grafana las
  evalúa en el servidor, y la ruta del lado del servidor construye su petición a
  partir de los campos de URL y contraseña del origen de datos, mientras que el
  formulario guarda la URL de la consola y la contraseña en campos propios que el
  lado del servidor no lee. Por eso una regla falla o se evalúa sin datos. Las
  consultas de panel no se ven afectadas porque las ejecuta el navegador.
- **Los ajustes contienen un único usuario de Pandora FMS, con un único conjunto
  de permisos.** Todos los usuarios de Grafana que pueden usar el origen de datos
  ven los mismos datos.
- **Los módulos de cadena no se pueden representar** y no se ofrecen en el
  selector de módulos.
- **Los selectores cargan listas completas.** El addon no envía ningún filtro
  de texto: las listas de grupos, agentes y módulos se descargan enteras cada
  vez que cambia el editor, y Grafana las filtra en el navegador.

## Referencia

### Ajustes del origen de datos

| Ajuste | Obligatorio | Por defecto | Descripción |
|--------|-------------|-------------|-------------|
| **Pandora extension** | Sí | — | URL base de la extensión, con esquema: `https://<PANDORA_FMS_URL>/pandora_console/extensions/grafana`. Sin barra final y sin sufijo `/search` ni `/query` |
| **Pandora user** | Sí | — | Usuario de Pandora FMS con el que consulta cada petición |
| **Password** | Sí | — | Contraseña de ese usuario, guardada en los ajustes JSON del origen de datos |

### Campos de consulta

| Campo | Por defecto | Descripción |
|-------|-------------|-------------|
| **Label** | Vacío | No se usa |
| **Tip** | Desmarcado | Marcado: muestras originales. Desmarcado: medias compactadas con el sufijo ` (avg)` en la serie |
| **Group** | Vacío | Filtro de grupo para la lista de agentes; `All` es el valor `0` |
| **Agent** | Vacío | Filtro de agente para la lista de módulos |
| **Module** | Vacío | Identificador de módulo que se envía a la extensión |

### Puntos de entrada de la extensión

El addon usa dos puntos de entrada relativos a la URL base configurada. Ambos
aceptan autenticación básica HTTP y devuelven JSON.

| Punto de entrada | Propósito | Cuerpo de la petición | Respuesta |
|------------------|-----------|-----------------------|-----------|
| `<extension>/search` | Listas de grupos, agentes y módulos | `{"type":"group"}`, `{"type":"agent","extra":"<group-id>"}` o `{"type":"module","extra":"<agent-id>"}` | Array de `{"value": <id>, "text": "<name>"}`; los grupos incluyen `{"value":0,"text":"All"}` |
| `<extension>/query` | Valores de un módulo para un rango de tiempo | `{"targets":[{"target":{"agent":"<agent-id>","module":"<module-id>","tip":<boolean>}}],"range":{"from":"<date>","to":"<date>"}}` | Array de objetos con el nombre de la serie en `target` y pares de `[<value>, <timestamp en milisegundos>]` en `datapoints` |

En `/query` solo se leen `module` y `tip`: el nombre de la serie es el nombre del
módulo que informa Pandora FMS, y el valor del agente se ignora. Las fechas se
aceptan en cualquier formato que Pandora FMS pueda interpretar, por ejemplo
ISO 8601.

### Identidad del addon

| Propiedad | Valor |
|-----------|-------|
| Identificador del Marketplace | `pandorafms.grafana` |
| Nombre | Grafana |
| Versión | `1.0` — la versión del paquete del Marketplace `pandorafms.grafana.1.0.zip` |
| Identificador del plugin de origen de datos | `pandorafms-pandorafmsgrafana-datasource`, el valor que exige `allow_loading_unsigned_plugins` |
| Categoría | Miscelaneus |
| Licencia | One — la descarga está limitada a usuarios con licencia |
| Disponibilidad | Descarga con licencia |
| Última actualización del Marketplace | 2025-06-25 |
| Versión mínima de Grafana | `10.0.3`, declarada por el plugin |
| Entrada del Marketplace | [pandorafms.grafana](https://marketplace.pandorafms.com/entries/pandorafms.grafana) |
