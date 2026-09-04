# Pandora CLI

## Introducción

**Ver**. 04-09-2026

`pandora-cli` es un cliente de línea de comandos para la **API v2** de Pandora FMS. Permite consultar
y modificar los datos de la consola desde un terminal o un script, sin pasar por la interfaz web.

**Tipo**: Herramienta de línea de comandos independiente

Todos los comandos siguen la misma forma:

```
pandora-cli <entidad> <verbo> [argumentos] [opciones]
```

```bash
pandora-cli user list
pandora-cli event list --size 10
pandora-cli tag get 5
pandora-cli group create --set name=Servers
```

Es un único ejecutable autocontenido, sin dependencias en tiempo de ejecución. Realiza una llamada a
la API por comando: toda la validación, los permisos y las reglas de negocio permanecen en la
consola.

## Matriz de compatibilidad

| **Consolas donde se ha probado** | Pandora FMS v8.0NG.800.4 (LTS), v8.0NG.804 (RRR) |
| --- | --- |
| **Consolas donde funciona** | Consolas que publiquen la API v2. Las consolas antiguas carecen de algunas funciones de filtrado; consulte [Funciones de filtrado según la consola](#funciones-de-filtrado-segun-la-consola). |
| **Sistemas donde se ha probado** | Linux x86-64 |
| **Ejecutables disponibles para** | Linux (x86-64, ARM64), macOS (Intel, Apple silicon), Windows (x86-64) |

## Requisitos previos

**Un token de la API v2.** Créelo en la consola bajo el usuario cuyos permisos deba emplear la
herramienta. Cada comando se ejecuta con el perfil ACL de ese usuario.

**Acceso de red a la consola** por HTTP o HTTPS.

**La dirección del cliente autorizada en la ACL de la API.** La consola restringe el acceso a la API
por IP. Si la dirección no está en la lista, todas las llamadas fallan con:

```
401 IP 10.0.0.5 is not in ACL list
```

Es un ajuste de la consola, no de la herramienta: añada la dirección a la lista ACL de la API en la
configuración de la consola antes de continuar.

## Configurar el acceso

### Guardar un token

`auth login` comprueba el token contra la consola **antes** de escribir nada. Si lo rechaza, no se
guarda ningún dato.

```bash
pandora-cli auth login --token <token> --url https://consola.ejemplo.com/pandora_console/api/v2/
```

La URL por defecto es `http://localhost/pandora_console/api/v2/`. Debe apuntar a la raíz de la API y
terminar en `/api/v2/`.

Las credenciales se escriben en `~/.pandora-cli/config.json`, con el directorio en `0700` y el
fichero en `0600`. El token se guarda codificado en base64, lo que evita que aparezca a simple vista
en la salida del terminal; lo que realmente lo protege son los permisos del fichero. La herramienta
se niega a leer un fichero de configuración con permisos más abiertos que `0600`.

Defina `PANDORA_CLI_HOME` para guardar la configuración en otra ubicación.

### Varias consolas

Cada consola es un contexto con nombre.

```bash
pandora-cli auth login --token <token> --url https://prod/pandora_console/api/v2/ --context prod
pandora-cli auth login --token <token> --url https://lab/pandora_console/api/v2/  --context lab --insecure

pandora-cli auth context list
pandora-cli auth context use prod
pandora-cli user list --context lab      # un comando contra otra consola
```

`--token` y `--url` también pueden pasarse directamente a cualquier comando. Usados así, el token no
se escribe nunca en disco, lo que resulta adecuado para un trabajo de integración continua que ya lo
tiene en un secreto.

### Certificados autofirmados

`--insecure` omite la verificación TLS. Nunca se aplica por defecto. Pasada a `auth login`, la
opción queda recordada para ese contexto; pasada a cualquier otro comando, se aplica solo a ese
comando.

## Verificar

```bash
pandora-cli auth status
```

```
Context:  prod
URL:      https://consola.ejemplo.com/pandora_console/api/v2/
Insecure: false
Config:   /home/usuario/.pandora-cli/config.json
Token:    valid
Probed:   2026-09-04T08:01:42Z

Capabilities:
  filter.fieldConditions   supported (--where)
  filter.multipleSearch    supported (--in)
  filter.requestedFields   supported (--fields)

Console specification: 137 operations, 22 entities (read 2026-09-04T08:01:42Z)
```

`Token: valid` indica que la consola lo aceptó. El comando termina con un código distinto de cero si
no fue así.

Después, consulte datos reales:

```bash
pandora-cli user list
```

```
IDUSER  FULLNAME  EMAIL              ISADMIN  DISABLED
admin   Pandora   admin@example.com  true     false

1 shown, 1 total.
```

## Interpretar la salida

La salida es una **tabla en un terminal** y **JSON cuando se redirige o se encadena**, de modo que
los scripts obtienen una salida analizable sin necesidad de indicar ninguna opción:

```bash
pandora-cli user list                      # tabla
pandora-cli user list | jq '.[].idUser'    # JSON
pandora-cli user list > usuarios.json      # JSON
```

Fuerce un formato con `-o json`, `-o table` o `-o yaml`.

Las líneas informativas como `1 shown, 1 total.` solo aparecen en formato tabla. En JSON y YAML se
suprimen, de manera que la salida encadenada siempre es válida.

Los listados los pagina la consola. `1 shown, 1 total.` indica cuántas filas se han devuelto y
cuántas existen; use `--page` y `--size` para recorrer un resultado extenso.

### Funciones de filtrado según la consola

Tres funciones de filtrado dependen de un soporte de la API que las consolas antiguas no tienen. La
herramienta detecta cuáles ofrece la consola al iniciar sesión y guarda la respuesta para ese
contexto:

| Función | Opción |
| --- | --- |
| `fieldConditions` | `--where` |
| `requestedFields` | `--fields` |
| `multipleSearchString` | `--in` |

Si una consola no admite alguna, el comando se rechaza localmente con una explicación en lugar de
producir un error de servidor poco claro:

```
Error: --fields (requestedFields) is not available on this console.
The console at https://consola.ejemplo.com/pandora_console/api/v2/ rejects that parameter.
```

Tras actualizar una consola, refresque la respuesta almacenada:

```bash
pandora-cli auth status --refresh
```

## Uso habitual

### Filtrar un listado

```bash
pandora-cli user list --filter isAdmin=true
pandora-cli user list --where 'fullName like admin' --sort fullName
pandora-cli user list --search backup
pandora-cli user list --in idUser=admin,root
pandora-cli user list --fields idUser,email --size 50
```

Todas las opciones de filtrado son repetibles y se combinan con **AND**.

**Cada entidad tiene dos conjuntos de campos distintos.** `--filter` acepta cualquier campo de la
entidad, mientras que `--where`, `--fields` y `--in` aceptan un conjunto más reducido: en `user` son
únicamente `idUser` y `fullName`. Los dos conjuntos no están anidados: una entidad puede aceptar en
`--fields` un campo que no es un campo normal de la entidad. La herramienta valida ambos localmente
y enumera los nombres válidos cuando rechaza uno, así que conviene leer el error en lugar de volver
a probar a ciegas.

Los valores se convierten a su tipo JSON: `true` y `false` pasan a booleanos, los dígitos a números
y `null` a nulo. Entrecomille para forzar una cadena:

```bash
pandora-cli tag list --filter name='"42"'
```

### Crear y modificar

```bash
pandora-cli user create --set idUser=jdoe --set fullName='Jane Doe' --set password=secret
pandora-cli user update jdoe --set email=jane@example.com
pandora-cli user delete jdoe --yes
```

`--set` es repetible. Para un cuerpo completo, lea el JSON desde un fichero o desde la entrada
estándar:

```bash
pandora-cli user create --from-file usuario.json
cat usuario.json | pandora-cli user create --from-file -
```

`--set` y `--from-file` no pueden combinarse.

`delete` pide confirmación. En una sesión no interactiva **se niega** en lugar de preguntar, de modo
que un script que haya olvidado `--yes` falla de forma visible en vez de borrar en silencio.

### Entidades anidadas

Algunas entidades dependen de una entidad superior. Sus comandos reciben primero el identificador de
la entidad superior:

```bash
pandora-cli report-design-page list 12
pandora-cli report-design-page-widget list 12 3
```

### Documentación y uso por agentes

```bash
pandora-cli docs                  # referencia completa de comandos de esta versión
pandora-cli docs --out ref.md
```

Para agentes de programación que trabajan en un terminal, instale una skill de uso que describe esta
versión:

```bash
pandora-cli skill install         # escribe ~/.claude/skills/pandora-cli/SKILL.md
pandora-cli skill install --print # muestra el contenido sin instalarlo
pandora-cli skill install --force # sobrescribe una skill existente
```

Vuelva a ejecutarlo tras una actualización para que la skill siga correspondiéndose con el
ejecutable.

### Diagnosticar una llamada

`--verbose` traza la línea de petición, el cuerpo enviado y el estado de la respuesta por la salida
de error estándar, dejando limpia la salida estándar para poder encadenarla:

```bash
pandora-cli user list --filter isAdmin=true -v -o json > usuarios.json
```

```
→ POST https://consola.ejemplo.com/pandora_console/api/v2/user/list
→ body: {"isAdmin":true}
← 200, 1834 bytes
```

## Resolución de problemas

| Síntoma | Causa y solución |
| --- | --- |
| `401 ... token was rejected` | El token es incorrecto o ha caducado. Vuelva a ejecutar `auth login`. |
| `401 IP ... is not in ACL list` | La dirección del cliente no está autorizada en la ACL de la API. Añádala en la configuración de la consola. |
| `403 ... lacks permission` | El token es válido, pero el perfil ACL del usuario propietario no permite la operación. |
| `404 ... or the API base URL is wrong` | Revise `auth status`; la URL debe terminar en `/api/v2/`. |
| `TLS verification failed` | Certificado autofirmado. Repita con `--insecure` o guárdelo para el contexto al iniciar sesión. |
| `has permissions 0644` | El fichero de configuración es legible por otros usuarios. Ejecute `chmod 0600 ~/.pandora-cli/config.json`. |
| `--fields ... is not available on this console` | La consola carece de esa función de filtrado. Consulte [Funciones de filtrado según la consola](#funciones-de-filtrado-segun-la-consola). |
| `unknown field "..."` | El campo no existe en esa entidad. El mensaje enumera los nombres válidos. |
| `the "..." entity does not exist on this console` | La consola no publica esa entidad. Ejecute `auth status --refresh` si se ha actualizado. |
| `--... is required by this endpoint` | No se ha indicado un parámetro que la API declara como obligatorio. |

Un comando termina con `0` si tiene éxito y con un valor distinto de cero si falla, de modo que
puede emplearse directamente en el flujo de control de un script.

## Referencia

### Opciones globales

| Opción | Significado |
| --- | --- |
| `--context <nombre>` | Contexto con nombre que se debe usar. Por defecto, el actual. |
| `--url <url>` | URL base de la API, que prevalece sobre el contexto. |
| `--token <token>` | Token solo para este comando. No se escribe nunca en disco. |
| `--insecure` | Omite la verificación del certificado TLS. |
| `-o, --output json\|table\|yaml` | Formato de salida. Tabla en terminal, JSON en el resto de casos. |
| `-v, --verbose` | Traza las peticiones por la salida de error estándar. |
| `--timeout <duración>` | Tiempo máximo de la petición. Por defecto, `30s`. |

### Opciones de listado

| Opción | Efecto | Ejemplo |
| --- | --- | --- |
| `--filter <campo>=<valor>` | Igualdad de campo. | `--filter isAdmin=true` |
| `--where '<campo> <op> <valor>'` | Condición avanzada. | `--where 'fullName like admin'` |
| `--search <texto>` | Búsqueda de texto libre. | `--search backup` |
| `--in <campo>=<v1,v2>` | Campo dentro de una lista de valores. | `--in idUser=admin,root` |
| `--fields <a,b,c>` | Limita los campos devueltos. | `--fields idUser,email` |
| `--page <n>` | Número de página. | `--page 2` |
| `--size <n>` | Filas por página. | `--size 50` |
| `--sort <campo>` | Campo por el que ordenar. | `--sort fullName` |
| `--order asc\|desc` | Sentido de la ordenación. | `--order desc` |

Operadores admitidos por `--where`: `=`, `like`, `regex`, `in`, `between`, `is_not_empty`. Para una
columna JSON, indique una ruta con `--where '<campo>:<rutaJson> <op> <valor>'`.

### Opciones de escritura

| Opción | Efecto |
| --- | --- |
| `--set <campo>=<valor>` | Un campo del cuerpo. Repetible. |
| `--from-file <ruta>` | Lee el cuerpo JSON completo de un fichero, o `-` para la entrada estándar. |
| `--yes` | Omite la confirmación en un comando destructivo. |

### Comandos de autenticación

| Comando | Efecto |
| --- | --- |
| `auth login` | Valida un token y lo guarda en un contexto. |
| `auth status` | Muestra el contexto activo y verifica el token. Con `--refresh` vuelve a comprobar las funciones de la consola. |
| `auth context list` | Enumera los contextos guardados. |
| `auth context use <nombre>` | Selecciona el contexto actual. |
| `auth logout [contexto]` | Elimina un contexto guardado. |

### Entidades

Cada entidad admite los verbos indicados. Ejecute `pandora-cli <entidad> --help` para conocer sus
comandos y argumentos exactos, y `pandora-cli docs` para la referencia completa de la versión
instalada.

| Entidad | Contenido | Verbos |
| --- | --- | --- |
| `agent-extended-data` | Datos extendidos asociados a agentes | `list`, `get`, `create`, `update`, `delete` |
| `bulk-draft` | Borradores de operaciones masivas | `list`, `get`, `delete` + 1 más |
| `bulk-queue` | Cola de operaciones masivas | `list`, `get`, `delete` |
| `data-translation` | Definiciones de traducción de datos | `list`, `get`, `create`, `update`, `delete` |
| `event` | Eventos de monitorización | `list`, `get`, `create`, `update`, `delete` + 10 más |
| `event-filter` | Filtros de eventos guardados | `list`, `get`, `create`, `update`, `delete` |
| `event-tag` | Etiquetas de eventos | `list`, `get`, `create`, `update`, `delete` |
| `group` | Grupos de agentes | `list`, `get`, `create`, `update`, `delete` |
| `monitoring` | Envío de datos de monitorización | `create` |
| `pandora-itsm-inventory` | Inventario de Pandora ITSM | `list`, `get` |
| `profile` | Perfiles ACL | `list`, `get`, `create`, `update`, `delete` |
| `report-datasource` | Orígenes de datos de informes | `list`, `get`, `create`, `update`, `delete` |
| `report-datasource-agent` | Agentes asociados a un origen de datos | `list`, `get`, `create`, `update`, `delete` |
| `report-datasource-group` | Grupos asociados a un origen de datos | `list`, `get`, `create`, `update`, `delete` |
| `report-design` | Diseños de informe | `list`, `get`, `create`, `update`, `delete` + 5 más |
| `report-design-page` | Páginas de un diseño de informe | `list`, `get`, `create`, `update`, `delete` |
| `report-design-page-widget` | Widgets de una página de diseño de informe | `list`, `get`, `create`, `update`, `delete` |
| `report-design-report` | Informes de un diseño de informe | `list`, `get`, `create`, `update`, `delete` |
| `report-design-template` | Plantillas de un diseño de informe | `list`, `get`, `create`, `update`, `delete` |
| `siem-group` | Grupos SIEM | `list`, `get`, `create`, `update`, `delete` |
| `siem-rule` | Reglas SIEM | `list`, `get`, `create`, `update`, `delete` + 4 más |
| `tag` | Etiquetas de módulos | `list`, `get`, `create`, `update`, `delete` |
| `token` | Tokens de la API | `list`, `get`, `create`, `update`, `delete` |
| `user` | Usuarios de la consola y sus perfiles asignados | `list`, `get`, `create`, `update`, `delete` + 5 más |
| `widget` | Widgets de dashboard | `list`, `get` |

Las entidades que conoce un ejecutable son las de la versión de la API con la que se construyó. Una
consola más reciente que el ejecutable puede publicar más; `pandora-cli auth status` informa de lo
que publica la propia consola.

### Ficheros y variables de entorno

| Ruta o variable | Finalidad |
| --- | --- |
| `~/.pandora-cli/config.json` | Contextos y tokens guardados. Permisos `0600`. |
| `~/.pandora-cli/schema-<contexto>.json` | Descripción almacenada de la API de esa consola. |
| `PANDORA_CLI_HOME` | Cambia el directorio de configuración. |
| `CLAUDE_CONFIG_DIR` | Cambia dónde escribe `skill install`. |
