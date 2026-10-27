# Active Directory

*Última actualización del artículo: 2026-10-26.*

## Qué hace

El addon Active Directory monitoriza un dominio de Microsoft Active Directory desde
Pandora FMS. Cada ejecución lee el bosque y las cuentas de usuario del dominio, ejecuta
los diagnósticos de dominio `dcdiag` y `repadmin`, y escribe el resultado como módulos de
Pandora FMS en la salida estándar. El agente Windows de Pandora FMS que ejecuta el addon
ingiere esa salida, de modo que cada pasada actualiza los módulos del agente instalado en
el controlador de dominio.

El addon es un plugin de agente: recibe un fichero de parámetros como único argumento, se
ejecuta una vez, imprime un bloque `<module>` por resultado y termina. No crea ningún
agente propio —los módulos pertenecen al agente que lo ejecuta— y no guarda estado entre
ejecuciones.

La salida cubre el estado de las cuentas de usuario, las cuentas que no se han utilizado,
la identidad del bosque, los servicios de los que depende Active Directory, las
comprobaciones de disponibilidad y los resultados de los diagnósticos del dominio.

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Pandora FMS NG 784 y posteriores | `Soportado` | El Marketplace indica que todas las integraciones son compatibles con Pandora FMS NG 784 y versiones posteriores |
| Un controlador de dominio como host que ejecuta el addon | `Requerido` | El addon ejecuta `dcdiag` y `repadmin /showrepl` sin servidor de destino, por lo que ambos actúan sobre el equipo local y sobre su rol en el dominio |
| Windows PowerShell 5.0 o posterior con el módulo Active Directory | `Requerido` | El addon lee el bosque y las cuentas a través de los cmdlets del módulo, y esta compilación no puede ejecutarse en versiones anteriores de Windows PowerShell |
| `dcdiag` y `repadmin` disponibles para la cuenta que ejecuta el addon | `Requerido` | El addon ejecuta ambas herramientas en cada pasada |
| Un agente Windows de Pandora FMS en el mismo host | `Requerido` | Es lo que ingiere los módulos que imprime el addon |
| Versiones de Windows Server, y niveles funcionales de dominio y bosque | `Sin validar` | No se ha registrado una matriz de versiones ni de niveles funcionales |
| Versiones del agente Windows de Pandora FMS | `Sin validar` | No se ha registrado una matriz de versiones del agente para este addon |

### Requisitos

1. **Un controlador de dominio Windows** que ejecute el agente Windows de Pandora FMS. El
   addon ejecuta `dcdiag` y `repadmin /showrepl` sin servidor de destino: diagnostican el
   equipo local y su rol en el dominio. Ejecute el addon en un controlador de dominio.
2. **Windows PowerShell 5.0 o posterior**, con el **módulo Active Directory** y las
   **herramientas de línea de comandos de AD DS** (`dcdiag`, `repadmin`). En un
   controlador de dominio, el rol instala los tres. En otro host Windows, instale la
   capacidad RSAT que los proporciona, por ejemplo:

   ```powershell
   Add-WindowsCapability -Online -Name "Rsat.ActiveDirectory.DS-LDS.Tools~~~~0.0.1.0"
   ```

   Compruebe que las tres piezas están realmente disponibles antes de registrar la
   ejecución:

   ```powershell
   Get-Command Get-ADForest
   dcdiag /?
   repadmin /?
   ```

3. **Una cuenta autorizada a leer el directorio y ejecutar los diagnósticos.** El addon no
   tiene credenciales propias: todo se ejecuta con la cuenta que lo inicia —de forma
   predeterminada, la cuenta del servicio del agente de Pandora FMS—. Utilice esa cuenta,
   o configure el agente para ejecutarse con una cuenta de dominio que tenga los permisos
   que necesitan los diagnósticos. Ninguna fuente oficial identifica un conjunto de roles
   más restrictivo que el que exigen los propios diagnósticos.
4. **Pandora FMS** para recibir los módulos, accesible desde el agente a través de su
   conexión Tentacle habitual.

No se instala nada en el resto de controladores de dominio, en los servidores miembro ni en
las estaciones de trabajo del dominio.

### Instalar el addon

Descargue el addon desde su entrada del Marketplace, cuya descarga está limitada a
usuarios con licencia:

[https://marketplace.pandorafms.com/entries/pandorafms-active_directory](https://marketplace.pandorafms.com/entries/pandorafms-active_directory)

Extraiga el paquete y coloque el ejecutable `active_directory.exe` junto con el fichero de
parámetros `adparams.txt` en una carpeta legible por la cuenta que ejecuta el agente. Los
ejemplos de esta página usan:

```text
%ProgramFiles%\Pandora_Agent\plugins\active-directory\
```

Pandora FMS también puede distribuir ambos ficheros mediante una colección; consulte
[Colocar los ficheros en el host del agente](#colocar-los-ficheros-en-el-host-del-agente).

## Configuración

### El fichero de parámetros

El addon lee un único fichero de parámetros, que recibe como único argumento de línea de
comandos. El fichero es texto plano con líneas `clave=valor`, y el `adparams.txt`
distribuido es la referencia:

```ini
user=all
unused=1
spnm=0
upnm=0
tests=1
```

El formato es estricto y no avisa de los errores:

- Escriba la clave y el valor sin espacios alrededor de `=`. `user = all` no coincide con
  la clave y el ajuste se ignora.
- Escriba una sola línea por clave: una clave repetida se lee como una lista de valores en
  lugar de un único valor.
- Solo se utiliza el texto entre el primer `=` y el siguiente `=`, por lo que un valor no
  debe contener `=`.
- Comente una línea con `#` al principio para deshabilitarla. Una clave comentada o
  ausente deja su bloque deshabilitado: sin `user` no hay módulos de usuario, sin `unused`
  no hay módulos de cuentas sin usar y sin `tests` no hay módulos de diagnóstico.
- No mueva el fichero: el addon recibe su ruta, y una ruta incorrecta no se informa como
  error de fichero (consulte [No aparece nada en la consola](#no-aparece-nada-en-la-consola)).

`user` acepta el literal `all` —un módulo por cada cuenta habilitada del directorio— o el
nombre de una sola cuenta, como un `SamAccountName`, para informar únicamente esa cuenta.
`unused`, `spnm`, `upnm` y `tests` son interruptores: `1` habilita el bloque, `0` o un
valor vacío lo deshabilita.

### Colocar los ficheros en el host del agente

Hay dos opciones, equivalentes una vez que los ficheros están en disco:

**Copiar los ficheros.** Coloque `active_directory.exe` y `adparams.txt` en cualquier
carpeta que la cuenta del agente pueda leer —los ejemplos usan
`%ProgramFiles%\Pandora_Agent\plugins\active-directory\`— y utilice esa ruta al registrar
la ejecución.

**Distribuirlos con una colección.** Cree una colección en la sección **Collections** de la
consola de Pandora FMS con un nombre corto, suba a ella el ejecutable y el fichero de
parámetros, y asigne la colección al agente. El agente escribe los ficheros de la colección
bajo su carpeta de instalación, en una subcarpeta con el nombre corto, de modo que la
ejecución apunta a `%ProgramFiles%\Pandora_Agent\collections\<COLLECTION_NAME>\`.

<!-- SCREENSHOT NEEDED: Pandora FMS console Collections section showing a collection whose Files tab contains active_directory.exe and adparams.txt. -->

### Registrar la ejecución

Pandora FMS ejecuta el addon como plugin de agente: el agente lanza el comando en su
intervalo y analiza los bloques `<module>` que imprime. Registre una ejecución por
controlador de dominio, cada una apuntando al ejecutable y a su propio fichero de
parámetros.

En la consola, la ejecución se configura en la lista de plugins del agente; esa misma
ejecución aparece en el host como una entrada `module_plugin` en `pandora_agent.conf`:

```apache
module_begin
module_plugin "%ProgramFiles%\Pandora_Agent\plugins\active-directory\active_directory.exe" "%ProgramFiles%\Pandora_Agent\plugins\active-directory\adparams.txt"
module_timeout 300
module_end
```

Sustituya ambas rutas por las de la carpeta de la colección si distribuyó los ficheros de
esa forma.

`module_timeout` es relevante aquí: una pasada ejecuta un ciclo completo de `dcdiag`,
`repadmin /showrepl` y, con `tests=1`, un segundo ciclo de `dcdiag` con quince pruebas.
Ajuste un tiempo de espera superior al total de esas llamadas en su controlador de dominio,
en lugar de confiar en el valor predeterminado del agente.

Una entrada `module_plugin` sin un bloque `module_begin`/`module_end` que la envuelva se
ejecuta en cada intervalo del agente, que en la configuración distribuida del agente es
`interval 300`. Para ejecutar el addon con menos frecuencia que el resto del agente,
conserve el bloque y añada dentro `module_absoluteinterval 1d` (o la frecuencia que
necesite).

<!-- SCREENSHOT NEEDED: Agent plugin execution configuration showing the Active Directory executable path and its parameter file argument. -->

## Verificación

Ejecute el addon manualmente en el controlador de dominio, desde una consola de PowerShell,
pasando el fichero de parámetros como único argumento:

```powershell
& "%ProgramFiles%\Pandora_Agent\plugins\active-directory\active_directory.exe" "%ProgramFiles%\Pandora_Agent\plugins\active-directory\adparams.txt"
```

Una ejecución correcta imprime los bloques de módulos y termina. Extracto de la salida,
reducido a la identidad del bosque, las comprobaciones de disponibilidad y un servicio:

```xml
<module>
<name><![CDATA[AD: Schema Master]]></name>
<type><![CDATA[generic_data_string]]></type>
<data><![CDATA[dc01.example.com]]></data>
<description>Schema Master in Active Directory</description>
</module>
<module>
<name><![CDATA[CONNECTIVITY]]></name>
<type><![CDATA[generic_proc]]></type>
<data><![CDATA[1]]></data>
<description>Active Directory connectivity</description>
</module>
<module>
<name><![CDATA[AD: Service NTDS]]></name>
<type><![CDATA[generic_proc]]></type>
<data><![CDATA[1]]></data>
<description>Active Directory related services status. OK if Running</description>
</module>
```

Ejecutado sin argumentos, el ejecutable imprime su resumen de uso —el nombre del plugin,
la forma `active_directory.exe [config_file]` y una referencia al fichero de
configuración— y termina sin generar módulos. No hay opciones: el primer argumento siempre
se interpreta como el fichero de configuración, incluido `-h`.

Después compruebe el agente: tras la siguiente pasada, sus módulos incluyen los anteriores
más los grupos de usuario, cuentas sin usar y diagnóstico. Si la consola no muestra
ninguno, consulte [No aparece nada en la consola](#no-aparece-nada-en-la-consola).

<!-- SCREENSHOT NEEDED: Agent module list in the Pandora FMS console showing the modules generated by the Active Directory addon. -->

## Entender los resultados

El addon agrupa sus módulos por lo que describen:

- **Estado de los usuarios.** Con `user=all`, cada cuenta habilitada del directorio genera
  un módulo `AD User <cuenta>` cuyo valor es `Enabled: <cuenta>`. Las cuentas
  deshabilitadas no generan módulo. Con el nombre de una sola cuenta, un único módulo con
  ese nombre informa `True` o `False`.
- **Cuentas sin usar.** Con `unused=1`, un módulo `Unused AD User <cuenta>` por cada cuenta
  que no sea un objeto crítico del sistema y que esté deshabilitada, tenga la contraseña
  caducada, no se haya conectado nunca o no se haya conectado en más de 60 días.
- **Identidad del bosque.** `AD: Schema Master`, `AD: Root Domain`, `AD: Forest Domains` y
  `AD: Global Catalogs` se generan siempre a partir del bosque. Los dos últimos son valores
  de varias líneas cuando el bosque tiene varios dominios o varios catálogos globales. Con
  `spnm=1` y `upnm=1` el addon añade un bloque por sufijo SPN y UPN.
- **Servicios.** Un módulo `AD: Service <servicio>` por cada servicio que comprueba el
  addon: `DNS`, `DFSR`, `IsmServ`, `Kdc`, `NetLogon` y `NTDS`. El valor es `1` mientras el
  servicio está en ejecución y `0` en caso contrario.
- **Disponibilidad.** `CONNECTIVITY` y `Replication admin` acompañan a las llamadas a
  `dcdiag` y `repadmin`; lea la limitación siguiente antes de usarlos como comprobación.
- **Diagnóstico.** Con `tests=1`, un módulo `AD: Test <prueba>` por cada prueba que `dcdiag`
  informa como iniciada, excepto `Connectivity`. El valor es `1` cuando la prueba se superó
  y `0` cuando se ejecutó y falló.

Hay dos comportamientos que debe conocer antes de confiar en estos módulos. En primer
lugar, `CONNECTIVITY` y `Replication admin` informan `1` en todas las ejecuciones de esta
versión, sea cual sea el resultado de los diagnósticos; consulte
[Limitación conocida: conectividad y replicación](#limitacion-conocida-conectividad-y-replicacion).
En segundo lugar, todos los sufijos SPN comparten un mismo nombre de módulo, igual que
todos los UPN: la consola mantiene un único módulo por nombre, así que lea la salida de la
ejecución cuando necesite ver cada sufijo.

## Operar y resolver problemas

### Coste de ejecución y planificación

Cada pasada lanza dos diagnósticos externos y, con `tests=1`, un tercero. En un controlador
de dominio sano terminan en segundos o minutos, según el tamaño del directorio y el número
de socios de replicación; ajuste `module_timeout` en consecuencia. El addon no guarda
estado, por lo que una ejecución manual en cualquier momento equivale a una programada.

Con `user=all` el addon consulta cada cuenta del directorio individualmente, de modo que el
tiempo de ejecución crece con el número de cuentas. En un directorio grande, programe el
addon con menos frecuencia que el intervalo del agente y aumente el tiempo de espera.

### Limitación conocida: conectividad y replicación

`CONNECTIVITY` y `Replication admin` informan `1` en todas las ejecuciones de esta versión:
la condición que evalúa la salida de `dcdiag` y `repadmin` es siempre verdadera, por lo que
una prueba de conectividad fallida o un estado de replicación roto no se refleja en el
módulo. Trate esos dos módulos como un indicador de que la ejecución se produjo, no como una
comprobación de disponibilidad, y utilice los módulos `AD: Test <prueba>` y la salida de
`dcdiag` y `repadmin` para conocer el estado real del dominio.

### No aparece nada en la consola

- **Ruta incorrecta del fichero de parámetros.** El addon no informa de un fichero
  ilegible: las claves quedan con valores vacíos, los bloques de usuario, cuentas sin usar
  y diagnóstico siguen deshabilitados, y la ejecución aun así imprime los módulos de bosque
  y de servicios. Compruebe la ruta en la línea `module_plugin` o en la ejecución de la
  consola.
- **La ejecución no está registrada en el agente.** El addon no imprime nada hasta que el
  agente lo ejecuta, y el agente ignora la salida que no puede analizar. Ejecute el comando
  manualmente primero y después revise el log del agente para esa ejecución.
- **La cuenta del agente no puede leer el ejecutable o el fichero de parámetros.** Copie
  ambos ficheros a una carpeta que la cuenta pueda leer o asigne la colección al agente.

### Falta el módulo de un servicio

Cuando un servicio no está instalado en el host, el addon escribe un error para él y omite
ese módulo: no informa un `0`. Si falta el módulo de un servicio que espera que exista,
ejecute `Get-Service <servicio>` en el host: el módulo depende de la presencia del servicio,
no solo de su estado.

### El fichero de parámetros no surte efecto

La mayoría de los problemas de configuración provienen de la sintaxis del fichero: espacios
alrededor de `=`, varias líneas para la misma clave o un valor que contiene `=`. Reescriba
la línea afectada como `clave=valor` y ejecute el addon manualmente para confirmar que
aparecen los nuevos módulos.

Con el nombre de una sola cuenta en `user`, el addon escribe un `\n` literal después de las
etiquetas `<module>` y `</module>` de su bloque, por lo que ese bloque no es XML limpio. Si
el módulo de una sola cuenta no aparece en la consola mientras que `user=all` funciona,
utilice `user=all` y filtre en la consola, o mantenga un fichero de parámetros por cuenta y
revise primero la salida de la ejecución.

### No hay módulos de pruebas de diagnóstico

- Con `tests` vacío o `0`, el bloque de diagnóstico está deshabilitado por diseño:
  establezca `tests=1`.
- El addon crea un módulo solo para una prueba que `dcdiag` informa como iniciada, y lee el
  resultado en inglés o en español. Cuando el sistema operativo o `dcdiag` se ejecutan en
  otro idioma, no se encuentran nombres de prueba y no se producen módulos
  `AD: Test <prueba>`.
- Ejecute el mismo comando `dcdiag` a mano (consulte [Diagnósticos ejecutados](#diagnosticos-ejecutados))
  y lea su salida: un error sobre una prueba desconocida, o una prueba que nunca se inicia,
  termina en un módulo ausente en lugar de un `0`.

## Referencia

### Fichero de parámetros

Se pasa como único argumento de línea de comandos: el fichero es obligatorio y todas las
claves que contiene son opcionales. Líneas `clave=valor`, sin espacios alrededor de `=`.

| Nombre | Obligatorio | Predeterminado | Descripción |
| --- | --- | --- | --- |
| `user` | No | `all` en el fichero distribuido | `all` genera un módulo `AD User <cuenta>` por cada cuenta habilitada. Cualquier otro valor se interpreta como el nombre de una sola cuenta y genera un módulo con ese nombre. Comente la línea para deshabilitar el bloque de usuarios. |
| `unused` | No | `1` en el fichero distribuido | `1` genera un módulo `Unused AD User <cuenta>` por cada cuenta sin usar. Cualquier otro valor, o una clave ausente, deshabilita el bloque. |
| `spnm` | No | `0` en el fichero distribuido | `1` genera un bloque `AD SPN Suffixes` por cada sufijo SPN del bosque. Cualquier otro valor deshabilita el bloque. |
| `upnm` | No | `0` en el fichero distribuido | `1` genera un bloque `AD UPN Suffixes` por cada sufijo UPN del bosque. Cualquier otro valor deshabilita el bloque. |
| `tests` | No | `1` en el fichero distribuido | `1` ejecuta las pruebas nombradas de `dcdiag` y genera un módulo `AD: Test <prueba>` por cada prueba iniciada. Cualquier otro valor deshabilita el bloque. |

Solo se lee el primer segmento del valor: el texto posterior a un segundo `=` se descarta.
Una clave que aparece más de una vez se lee como varios valores.

### Línea de comandos

```text
active_directory.exe [config_file]
```

| Condición | Comportamiento |
| --- | --- |
| Sin argumentos | Imprime el resumen de uso y termina sin generar módulos |
| Un argumento | Lo lee como la ruta del fichero de parámetros |
| Cualquier argumento adicional | Se ignora |
| Un argumento que empieza por `-`, como `-h` | Se interpreta como la ruta del fichero de parámetros; no hay análisis de opciones |
| La ruta no existe | La ejecución continúa con valores vacíos e imprime solo los módulos de bosque, disponibilidad y servicios |

### Diagnósticos ejecutados

El addon ejecuta estos comandos en cada pasada:

| Comando | Propósito | Cuándo |
| --- | --- | --- |
| `dcdiag` | Conjunto completo de pruebas predeterminadas del controlador de dominio local | En cada pasada |
| `repadmin /showrepl` | Estado de replicación del controlador de dominio local | En cada pasada |

Con `tests=1` ejecuta además:

```text
dcdiag /test:Advertising /test:FrsEvent /test:DRSRevent /test:SysVolCheck /test:KccEvent /test:KnowsOfRoleHolders /test:MachineAccount /test:NCSecDesc /test:NetLogons /test:ObjectsReplicated /test:Replications /test:RidManager /test:Services /test:Systemlog /test:VerifyReferences
```

| Prueba informada por `dcdiag` | Módulo |
| --- | --- |
| Cada prueba iniciada excepto `Connectivity` | `AD: Test <prueba>` |

El addon lee los resultados en inglés y en español.

### Módulos generados

| Nombre del módulo | Tipo | Valor |
| --- | --- | --- |
| `AD User <cuenta>` | `generic_data_string` | `Enabled: <cuenta>` con `user=all`; `True` o `False` para una sola cuenta |
| `Unused AD User <cuenta>` | `generic_data_string` | `<cuenta> is not beign used` (escrito así en la salida) |
| `AD: Schema Master` | `generic_data_string` | Maestro de esquema del bosque |
| `AD: Root Domain` | `generic_data_string` | Dominio raíz del bosque |
| `AD: Forest Domains` | `generic_data_string` | Dominios del bosque, uno por línea |
| `AD: Global Catalogs` | `generic_data_string` | Servidores de catálogo global del bosque, uno por línea |
| `AD SPN Suffixes` | `generic_data_string` | Un bloque por sufijo SPN, todos con este nombre de módulo |
| `AD UPN Suffixes` | `generic_data_string` | Un bloque por sufijo UPN, todos con este nombre de módulo |
| `CONNECTIVITY` | `generic_proc` | `1` en todas las ejecuciones de esta versión |
| `Replication admin` | `generic_proc` | `1` en todas las ejecuciones de esta versión |
| `AD: Service <servicio>` | `generic_proc` | `1` mientras el servicio está en ejecución, `0` en caso contrario; se omite cuando el servicio no está instalado |
| `AD: Test <prueba>` | `generic_proc` | `1` cuando `dcdiag` informa la prueba como superada, `0` cuando se ejecutó y falló |

Los servicios comprobados son `DNS`, `DFSR`, `IsmServ`, `Kdc`, `NetLogon` y `NTDS`.

### Identidad del addon

| Propiedad | Valor |
| --- | --- |
| Identificador del Marketplace | `pandorafms-active_directory` |
| Nombre | Active Directory |
| Versión | `1.1` |
| Paquete | `pandorafms-active_directory.1.1.zip` |
| Licencia | One; la descarga está limitada a usuarios con licencia |
| Última actualización en el Marketplace | 2026-02-09 |
| Descargas | 30 |
| Autor | Pandora FMS |
| Tipo en el Marketplace | Miscelaneus |
| Ejecutable | `active_directory.exe` |
| Fichero de parámetros | `adparams.txt` |
