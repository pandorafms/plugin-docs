# Oculix

## Introducción

**Ver**. 03-06-2026

Este documento describe la funcionalidad del plugin de Oculix y su integración con PandoraFMS. El plugin de Oculix permite la automatización visual de transacciones mediante capturas de pantalla, comparación de imágenes y ejecución de scripts, generando módulos de monitorización en PandoraFMS.

**Tipo**: Plug-in server

## Matriz de compatibilidad

| **Sistemas donde se ha probado** | Rocky linux, windows server 2022 |
| --- | --- |
| **Sistemas donde funciona** | Cualquier sistema linux y windows |

## Prerrequisitos

**1. Java Runtime Environment**  
El plugin ejecuta un archivo JAR de Oculix, por lo que es necesario tener Java instalado y accesible en el PATH del sistema. Se recomienda Java 17 o superior.

**2. Entorno gráfico**  
El plugin utiliza `mss` para realizar capturas de pantalla, por lo que requiere un servidor X11 en ejecución (entorno gráfico). Si se ejecuta en un entorno sin interfaz gráfica, se puede usar un servidor X virtual como `Xvfb`.

**3. Agente en modo proceso y no se puede bloquear o cerrar sesión.**  
Una vez en ejecución por el Agente de Pandora FMS éste debe correr en **modo proceso**, ya que de correr en modo servicio no funcionará. Además, no será posible bloquear la sesión de escritorio, por lo que se recomienda su uso en máquinas virtuales.

**4. Permisos de escritura**  
El plugin necesita permisos de escritura en el directorio de artefactos (`--artifacts`) para almacenar capturas de pantalla, imágenes baseline y diferencias.

**5. Tentacle (opcional)**  
Si se utiliza el modo de transferencia `tentacle`, es necesario tener instalado y accesible el binario `tentacle_client` en el sistema.

## Parámetros

**Parámetros de ejecución del script**

| Parámetro | Descripción |
| --- | --- |
| **--script** | Ruta al script de Oculix a ejecutar. Este parámetro es obligatorio. **Soporta comas** para múltiples fases: `--script a.py,b.py,c.py` |
| **--jar** | Ruta al archivo JAR de Oculix. Este parámetro es obligatorio. |
| **--conf** | Archivo de configuración .conf con los parámetros de Pandora y conexión. Este parámetro es obligatorio. |
| **--workspace** | Directorio de trabajo para la ejecución del script Oculix. Opcional. |
| **--debug** | Nivel de detalle de debug (0 silencioso → 3 muy detallado) |
| **--console** | Activa el modo consola de Oculix. Se activa con el flag. |
| **--native-access** | Habilita `--enable-native-access=ALL-UNNAMED` en la ejecución de Java. Se activa con el flag. |
| **--checkpoint** | Activa la lógica de baseline: si no existe una imagen de referencia, crea una a partir de la captura actual. Se activa con el flag. |
| **--artifacts** | Directorio donde se almacenan las capturas, baselines y diferencias. Por defecto "artifacts". |
| **--phase-names** | Nombres de fase separados por coma (ej: `Login,Search,Logout`). Si se omite, se usa el stem del script. También configurable en .conf como `phase_names`. **CLI sobrescribe al .conf.** |
| **--transaction** | Nombre global de la transacción. Si se define, se generan módulos `Global_Status_{name}`, `Global_Time_{name}` y `Global_Last_Image_{name}`. También configurable en .conf como `transaction_name`. **CLI sobrescribe al .conf.** |
| **--retries** | Número de reintentos de toda la transacción (default: 1). Si alguna fase falla, se reintentan todas desde el principio. También configurable en .conf como `phase_retries`. **CLI sobrescribe al .conf.** |
| **--post-command** | Comando a ejecutar al finalizar todas las fases. Solo disponible como argumento CLI, no en .conf. |

**Parámetros de configuración Pandora (archivo .conf)**

| Parámetro | Descripción |
| --- | --- |
| **agent_name** | Nombre del agente que contendrá los módulos. Por defecto: "{script} Oculix". |
| **agents_group_name** | Grupo del agente en PandoraFMS. Por defecto "Oculix". |
| **module_prefix** | Prefijo para todos los módulos creados por el plugin. |
| **interval** | Intervalo de monitorización del agente en segundos. Por defecto 300. |
| **agent_plugin** | Modo de salida: 1 imprime el XML por consola, 0 escribe a fichero y transfiere. Por defecto 0. |
| **temporal** | Directorio temporal para archivos XML. Por defecto "/tmp". |
| **transfer_mode** | Modo de transferencia: "tentacle" o "local". Por defecto "tentacle". |
| **tentacle_client** | Ruta al binario de tentacle_client. Por defecto "tentacle_client". |
| **tentacle_ip** | Dirección IP del servidor tentacle. Por defecto "127.0.0.1". |
| **tentacle_port** | Puerto de conexión tentacle. Por defecto "41121". |
| **tentacle_opts** | Opciones extra para la conexión tentacle. |
| **data_dir** | Directorio de datos de PandoraFMS para transferencia local. Por defecto "/var/spool/pandora/data_in/". |

## Ejecución manual

### Formato de ejecución

```
./pandora_oculix.exe --script <ruta al script oculix> \
--conf <ruta del fichero .conf> \
--jar <ruta al JAR de oculix> \
[--workspace <directorio de trabajo>] \
[--debug <nivel de debug>] \
[--console] \
[--native-access] \
[--checkpoint] \
[--artifacts <directorio de artefactos>] \
[--phase-names <nombres de fase, separados por coma>] \
[--transaction <nombre de la transacción>] \
[--retries <número de reintentos>] \
[--post-command <comando a ejecutar al finalizar>]

```

#### Ejemplos

Script único (retrocompatible):

```
./pandora_oculix.exe --script scripts/login.py --conf oculix.conf --jar oculix.jar --debug 1

```

Con baseline y consola:

```
./pandora_oculix.exe --script scripts/login.py --conf oculix.conf --jar oculix.jar --console --checkpoint

```

Transacción multi-fase con reintentos:

```
./pandora_oculix.exe --script login.py,search.py,logout.py --phase-names Login,Search,Logout --transaction "MiApp" --retries 2 --conf oculix.conf --jar oculix.jar --debug 1

```

Con post-comando al finalizar:

```
./pandora_oculix.exe --script login.py,search.py,logout.py --phase-names Login,Search,Logout --transaction "MiApp" --post-command "echo Done" --conf oculix.conf --jar oculix.jar --debug 1

```

## Configuración en PandoraFMS

Para configurar el plugin en PandoraFMS, se deben seguir los siguientes pasos:

**1. Subir el plugin a PandoraFMS, por ejemplo en la siguiente ruta:**

```
/usr/share/pandora_server/util/plugin
```

**2. Subir el JAR de Oculix y los scripts .ocx necesarios al servidor, en una ruta accesible por el plugin.**

**3. Crear el archivo de configuración .conf con los parámetros de Pandora:**

```ini
[CONF]
agent_name=Oculix Login Test
agents_group_name=Oculix
module_prefix=
interval=300
agent_plugin=1
temporal=/tmp
transfer_mode=tentacle
tentacle_client=tentacle_client
tentacle_ip=127.0.0.1
tentacle_port=41121
tentacle_opts=
data_dir=/var/spool/pandora/data_in/
```

**4. Dirigirse al apartado plugins y crear uno nuevo:**

Se le añade nombre, descripción y timeout.

**5. Se añade la ruta del plugin en el comando y los parámetros necesarios para la ejecución de este.**

<p class="callout info">Para cada parámetro se debe configurar una macro, siendo la sintaxis de esta macro la siguiente: `_fieldx_`, siendo x el numero posicional del parámetro.</p>

Ejemplo de comando para el plugin:

```
/usr/share/pandora_server/util/plugin/pandora_oculix.py --script _field1_ --jar _field2_ --conf _field3_
```

**6. Se configuran las macros anteriores, añadiendo en cada una el valor del parámetro:**

Ejemplo de macros:

- `_field1_` = /opt/oculix/scripts/login.py
- `_field2_` = /opt/oculix/oculix.jar
- `_field3_` = /opt/oculix/oculix.conf

**7. Una vez configurado se debe crear un módulo en un agente que ejecute el plugin. En el menú de módulos de un agente creamos un módulo de tipo plugin nuevo:**

**8. En el menú de configuración del módulo, le ponemos un nombre, seleccionamos el plugin antes configurado y se le debe dar a "crear".**

**9. Se creará el agente con los módulos en la siguiente ejecución del plugin.**

## Agentes y módulos generados por el plugin

El plugin crea un agente con el nombre especificado en `agent_name` (por defecto "{script} Oculix") que contendrá los siguientes módulos:

| **Nombre del módulo** | **Tipo** | **Descripción** |
| --- | --- | --- |
| {script_name} status | generic_proc | Estado de la ejecución del script. Valor 1 si la ejecución fue exitosa, 0 si hubo error o diferencia visual. |
| {script_name} time | generic_data | Tiempo de ejecución del script en segundos. |
| {script_name} last_image | async_string | Captura de pantalla en formato base64 (imagen PNG). Solo se genera si la ejecución tiene estado 0 (fallo o diferencia visual). |

Ejemplo: para un script llamado `login`, los módulos generados serían:

```
login status
login time
login last_image
```