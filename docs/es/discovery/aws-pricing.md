# Discovery de AWS Pricing

*Última actualización del artículo: 2026-10-14.*

## Qué monitoriza

El plugin de Discovery de AWS Pricing consulta dos API de AWS para describir tanto el precio público de los servicios de AWS como los costes facturados a una cuenta de AWS:

- La **API Price List de AWS** devuelve los precios unitarios públicos bajo demanda de los servicios de catálogo que selecciones, por ejemplo EC2, S3 y RDS.
- La **API Cost Explorer de AWS** devuelve los costes facturados a la cuenta: los totales del día anterior, del mes actual hasta la fecha y del mes anterior, y desgloses opcionales del mes hasta la fecha por servicio facturado, región y cuenta enlazada.

El plugin genera un único agente de Pandora FMS que contiene cada precio de catálogo y cada coste de cuenta configurado como un módulo. Se ejecuta como una tarea de Discovery: la consola crea la tarea, el servidor de Discovery ejecuta el plugin y el agente y sus módulos se crean automáticamente. La tarea entrega los datos generados a través de Tentacle.

Una extensión de consola complementaria, **Dashboard AWS Pricing**, presenta los datos de estos agentes como un panel. Consulta [Dashboard AWS Pricing](#dashboard-aws-pricing).

## Preparación

### Compatibilidad

| Ámbito | Estado | Evidencia |
| --- | --- | --- |
| Versión del plugin `1.0` (`pandorafms.aws.pricing`) | Objetivo documentado | La versión que describe esta página, según la definición del paquete. |
| Una credencial de AWS con acceso de lectura a la API Price List de AWS y a la API Cost Explorer de AWS | `Requerido` | El plugin solo realiza consultas de lectura de productos, precios y costes con la entrada seleccionada del almacén de credenciales. |
| Una región, un servicio o un tipo de cuenta de AWS concretos | `No validado` | Ningún registro de pruebas publicado establece compatibilidad con una región, un catálogo de servicios o un tipo de cuenta concretos. |
| Sistema operativo del host donde se ejecuta el plugin | `No validado` | Ningún registro de pruebas publicado establece compatibilidad con un sistema operativo concreto. |

### Requisitos

- Un servidor de Pandora FMS con Discovery habilitado para ejecutar la tarea, y una consola para definirla.
- Una entrada del almacén de credenciales de AWS con acceso de lectura a la API Price List de AWS (para leer los precios de catálogo) y a la API Cost Explorer de AWS (para leer los costes de cuenta). El plugin solo lee datos; nunca modifica la cuenta de AWS. Concede los permisos de lectura mínimos que necesite tu monitorización.
- Los servicios que quieras tarifar, indicados por su código de servicio de AWS (EC2 es `AmazonEC2`, S3 es `AmazonS3`, RDS es `AmazonRDS`).
- Un grupo de agentes destino y un intervalo de monitorización para el agente generado. Ambos vienen de la tarea de Discovery y los hereda el agente.
- Conectividad de red con el destino de Tentacle, porque la tarea transfiere los datos generados a través de Tentacle.
- El plugin se distribuye como una aplicación de Discovery de Pandora FMS (paquete `.disco`) que el servidor de Discovery ejecuta en el servidor de Pandora FMS.

### Instalar el plugin

Carga el paquete `.disco` desde **Management → Discovery → Manage disco packages**: elige **Select a file**, selecciona el paquete y pulsa **Upload DISCO**. Tras cargarlo, **AWS Pricing** aparece en la lista de paquetes y en la sección **Applications** del asistente de Discovery.

## Configurar la tarea de Discovery

Crea la tarea desde **Management → Discovery → Applications → AWS Pricing**. El asistente recorre la definición genérica de la tarea y tres pasos del plugin: **AWS connection and services**, **Pricing filters and modules** y **Cost Explorer tokens**. Cada campo está documentado en [Parámetros de la tarea](#parametros-de-la-tarea).

### Paso 1 — Definición de la tarea

El paso genérico pide el **nombre** de la tarea, el **grupo de agentes** y el **servidor** en el que se ejecuta, y el **intervalo**. El grupo y el intervalo se pasan al plugin y los hereda el agente generado.

### Paso 2 — Conexión AWS y servicios

Datos de conexión y servicios de catálogo que tarifar:

- **AWS credentials** selecciona la entrada del almacén de credenciales que el plugin usa para llegar a las API de AWS. Obligatorio.
- **Custom API endpoint** sustituye el endpoint de las API de AWS usado tanto para las llamadas a Price List como a Cost Explorer. Déjalo vacío para usar AWS.
- **Catalog price tokens**, cuando está activado, recoge los precios unitarios públicos de los servicios de catálogo indicados abajo.
- **Catalog services** es la lista separada por comas de códigos de servicio de AWS que tarifar. Solo se muestra cuando **Catalog price tokens** está activado.

![Paso de conexión AWS y servicios](../assets/images/discovery/aws-pricing/aws-connection-and-services.png)

### Paso 3 — Filtros de precios y módulos

Filtros de los precios de catálogo y la identidad del agente generado:

- **AWS pricing API region** es la región del endpoint de la API Price List de AWS, normalmente `us-east-1`.
- **Rate codes** conserva opcionalmente solo las dimensiones de precio cuyo rate code de AWS coincida con uno de los indicados, uno por línea.
- **Product attribute filters** conserva opcionalmente solo los productos que coincidan exactamente con los atributos de producto de AWS, un par `Attribute=Value` por línea (por ejemplo `location=US East (N. Virginia)`).
- **Agent name** es el nombre del agente generado. Por defecto es `AWS Pricing`.
- **Module prefix** antepone opcionalmente un texto a cada nombre de módulo de precio de catálogo y coste de cuenta.
- **Agent autodisable mode**, cuando está activado, crea el agente generado en modo autodeshabilitado.

![Paso de filtros de precios y módulos](../assets/images/discovery/aws-pricing/pricing-filters-and-modules.png)

### Paso 4 — Tokens de Cost Explorer

Qué costes de cuenta leer y cómo consultarlos:

- **Yesterday cost**, **Month to date cost** y **Previous month cost** crean los módulos de total de cuenta del día anterior, del mes actual hasta la fecha y del mes natural anterior.
- **Cost by service**, **Cost by region** y **Cost by account** crean un módulo por servicio facturado, región y cuenta enlazada del mes actual hasta la fecha.
- **Cost metric** selecciona la métrica de Cost Explorer que leer. Usa `UnblendedCost` para costes directos o `AmortizedCost` para repartir costes de reservas prepagadas.
- **Cost services filter**, **Cost regions filter** y **Cost accounts filter** restringen la consulta de costes a los nombres de facturación, códigos de región y cuentas de 12 dígitos indicados. Déjalos vacíos para incluir todo lo que las credenciales puedan consultar.
- **Cost refresh interval** es el tiempo entre consultas a la API Cost Explorer. Entre refrescos el plugin reutiliza los costes en caché.
- **Modules allow regexp** y **Modules deny regexp** conservan o excluyen opcionalmente nombres de módulo que coincidan con las expresiones regulares indicadas, una por línea.

![Paso de tokens de Cost Explorer](../assets/images/discovery/aws-pricing/cost-explorer-tokens.png)

## Verificar la primera ejecución

Ejecuta la tarea desde **Management → Discovery → Task list** y comprueba el resultado en este orden.

1. **El resumen de la tarea** muestra el progreso general y un resumen con el número de recursos descubiertos y el número de módulos creados.
2. **El agente.** Espera un único agente cuyo nombre es el **Agent name** configurado. Aparece en la lista de agentes con `AWS` como sistema operativo.

   ![Agente AWS Pricing generado](../assets/images/discovery/aws-pricing/agents-list.png)

3. **Los módulos.** El agente contiene un módulo por cada punto de precio de catálogo descubierto y, por cada token de Cost Explorer habilitado, su módulo o módulos de coste.

   ![Módulos generados en el agente AWS Pricing](../assets/images/discovery/aws-pricing/module-list.png)

4. **La información de ejecución.** Una ejecución correcta no reporta errores. Cualquier fallo por API se registra ahí como información y el resto de módulos se sigue generando.

Si no se crea ningún agente, confirma que hay precios de catálogo o al menos un token de Cost Explorer habilitado, que hay al menos un servicio de catálogo listado cuando los precios de catálogo están habilitados, y que las credenciales y el grupo destino son válidos.

## Entender los resultados

### Agentes e identidad

El plugin crea exactamente un agente por tarea de Discovery y lo completa con cada precio de catálogo y cada coste de cuenta configurado. El agente pertenece al grupo de agentes de la tarea, hereda su intervalo, informa `AWS` como sistema operativo y usa la región de la API de precios de AWS como dirección. El nombre del agente es el **Agent name** configurado; cambiarlo después cambia la identidad del agente generado.

### Módulos por agente

El agente recibe dos familias de módulos, identificadas por el marcador `extra_data` que escribe el plugin para que los nombres puedan traducirse, truncarse o escaparse sin riesgos:

| Familia | Nombre del módulo | Valor |
| --- | --- | --- |
| Precio de catálogo | `<module prefix><código de servicio> <región> <tipo de uso> <rate code>` | Precio unitario público |
| Total de coste | `<module prefix>AWS Cost <token> <moneda>` | Coste de cuenta del periodo del token |
| Coste por servicio | `<module prefix>AWS Cost Month to date Service <nombre de facturación> <moneda>` | Coste del mes hasta la fecha de ese servicio facturado |
| Coste por región | `<module prefix>AWS Cost Month to date Region <región> <moneda>` | Coste del mes hasta la fecha de esa región |
| Coste por cuenta | `<module prefix>AWS Cost Month to date Account <cuenta> <moneda>` | Coste del mes hasta la fecha de esa cuenta enlazada |

Los módulos de precio de catálogo son de tipo *Generic data* y llevan la moneda y la medida como unidad, por ejemplo `USD per Hrs` o `USD per GB-Mo`. Los módulos de coste son de tipo *Generic data* y llevan como unidad la moneda devuelta por AWS. Los créditos y los importes negativos se conservan tal como los reporta AWS.

El nombre exacto y el estado por defecto de cada módulo se listan en [Módulos generados](#modulos-generados).

### Dashboard AWS Pricing

La extensión **Dashboard AWS Pricing** es un panel de la consola que lee los agentes y módulos creados por este plugin. No consulta AWS: solo muestra los módulos que el plugin ya recogió. Aparece en el menú **Monitoring** de la consola como **Dashboard AWS Pricing** y está disponible con permiso de lectura de agentes (`AR`).

Por cada agente muestra un panel con:

- **Tarjetas de resumen**: el número de **Price points**, **AWS services** y **Regions** del catálogo, los costes de cuenta de **Yesterday**, **Month to date** y **Previous month**, y una estimación de **Projected month** calculada a partir del coste del mes hasta la fecha y los días completados del mes.
- **Account costs**: un anillo **Cost by service**, una gráfica de líneas **Cost evolution** con las muestras diarias almacenadas del periodo seleccionado, y una tabla **Month to date by service**. Los desgloses por región y por cuenta aparecen cuando sus tokens están habilitados.
- **Catalog prices**: anillos **Price points by service** y **Price points by region**, una gráfica de barras **Top prices** por cada unidad de precio, y una tabla **Price points** con el servicio, la región, el módulo, el precio y la unidad de cada precio de catálogo.

Un filtro lateral acota la vista por **Agents**, **AWS services**, **Evolution period** y **Top results**. El panel necesita los mismos marcadores `extra_data` que escribe el plugin; los agentes y módulos creados antes de que existiera el marcador se reconocen a través de los marcadores heredados `aws-cost`, pero conviene refrescarlos ejecutando la tarea de nuevo.

![Dashboard AWS Pricing, costes de cuenta](../assets/images/discovery/aws-pricing/dashboard-account-costs.png)

![Dashboard AWS Pricing, precios de catálogo](../assets/images/discovery/aws-pricing/dashboard-catalog-prices.png)

## Operar

### Ejecución manual

El plugin también puede ejecutarse fuera del asistente de Discovery con un archivo de configuración, para probar la conectividad o para una ejecución puntual. Escribe un archivo de configuración (consulta [Archivo de configuración](#archivo-de-configuracion)) y ejecuta el punto de entrada del plugin con él:

```sh
pandora_aws_pricing --conf /ruta/a/aws_pricing.conf
```

La ejecución imprime los datos del agente y de los módulos generados como un único documento JSON. Cuando el plugin se ejecuta como tarea de Discovery, esa misma información pasa a ser la información de ejecución de la tarea.

### Caché de costes

Las consultas a Cost Explorer se cachean. El plugin guarda los módulos de coste devueltos en un archivo temporal y los reutiliza hasta que transcurre el **Cost refresh interval**, de modo que las ejecuciones repetidas de la tarea normalmente no lanzan consultas de coste adicionales. La caché se indexa por la configuración de costes y el día actual, y solo se reescribe cuando una consulta tiene éxito, así que una ejecución fallida conserva los datos anteriores. Usa un intervalo de refresco corto solo durante las pruebas.

El primer día del mes todavía no hay días completados del mes actual, por lo que los módulos de desglose del mes hasta la fecha (por servicio, región y cuenta) pueden no crearse hasta el segundo día.

## Resolución de problemas

| Síntoma | Comprobación |
| --- | --- |
| No se crea ningún agente | El plugin necesita precios de catálogo o al menos un token de Cost Explorer. Habilita uno de ellos. |
| La tarea informa de que hay que seleccionar al menos un servicio de catálogo | **Catalog price tokens** está habilitado pero **Catalog services** está vacío. Indica al menos un código de servicio. |
| La tarea informa de que no se pudieron decodificar las credenciales | Vuelve a crear la entrada del almacén de credenciales: debe contener un access key ID y un secret access key. |
| La tarea informa de que el ID de grupo debe ser mayor que 0 | Selecciona un **grupo de agentes** destino en la definición de la tarea. |
| Faltan los precios de catálogo pero los costes están presentes | La consulta a Price List falló. Comprueba los códigos de servicio de catálogo, los rate codes y los filtros de atributos de producto; cualquier fallo se reporta como información **AWS Pricing** en la ejecución. |
| Faltan los costes pero los precios de catálogo están presentes | La consulta a Cost Explorer falló. Comprueba la métrica de coste, los filtros de coste y los permisos de la credencial; el fallo se reporta como información **Cost Explorer** en la ejecución y se conservan los costes anteriores en caché. |
| Un módulo de coste está vacío o a cero en los primeros días del mes | El mes actual tiene pocos días completados. El valor crece a medida que avanza el mes. |
| Menos precios de catálogo de los esperados | La consulta de catálogo se detiene en el límite de productos configurado y avisa con **Product limit reached**. Acota los servicios de catálogo o los filtros de atributos de producto. |
| El panel no muestra datos de un agente | Confirma que el agente lo ha creado este plugin y que su lista de módulos está poblada. El panel solo lee los agentes y módulos del plugin. |

## Referencia

### Parámetros de la tarea

La consola presenta estos campos después de la definición genérica de la tarea. La columna macro es el identificador usado en la configuración de la tarea generada.

#### Conexión AWS y servicios

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| AWS credentials | `_credentials_` | select (credentials) | — | Entrada del almacén de credenciales con acceso de lectura a las API de AWS. Obligatorio |
| Custom API endpoint | `_apiEndpoint_` | string | — | Sustituye el endpoint de las API de AWS. Déjalo vacío para usar AWS |
| Catalog price tokens | `_catalogPrices_` | checkbox | on | Recoge los precios unitarios públicos de los servicios de catálogo |
| Catalog services | `_serviceCodes_` | string | `AmazonEC2,AmazonS3,AmazonRDS` | Códigos de servicio de AWS separados por comas. Solo se muestra cuando **Catalog price tokens** está activado |

#### Filtros de precios y módulos

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| AWS pricing API region | `_pricingRegion_` | string | `us-east-1` | Región del endpoint de la API Price List de AWS |
| Rate codes | `_rateCodes_` | textarea | — | Un rate code de AWS por línea para conservar solo esas dimensiones de precio |
| Product attribute filters | `_productFilters_` | textarea | — | Un par `Attribute=Value` por línea para conservar solo los productos que coincidan |
| Agent name | `_agentName_` | string | `AWS Pricing` | Nombre del agente generado |
| Module prefix | `_modulePrefix_` | string | — | Texto antepuesto a cada nombre de módulo de precio de catálogo y coste de cuenta |
| Agent autodisable mode | `_agentautodisable_` | checkbox | off | Crea el agente generado en modo autodeshabilitado |

#### Tokens de Cost Explorer

| Campo | Macro | Tipo | Por defecto | Notas |
| --- | --- | --- | --- | --- |
| Yesterday cost | `_costYesterday_` | checkbox | on | Coste total de la cuenta del día UTC anterior |
| Month to date cost | `_costMonthToDate_` | checkbox | on | Coste total de la cuenta desde el primer día de este mes hasta el día UTC anterior |
| Previous month cost | `_costPreviousMonth_` | checkbox | on | Coste total de la cuenta de todo el mes natural anterior |
| Cost by service | `_costByService_` | checkbox | on | Un módulo por servicio facturado del mes actual hasta la fecha |
| Cost by region | `_costByRegion_` | checkbox | off | Un módulo por región del mes actual hasta la fecha, incluidos los costes globales |
| Cost by account | `_costByAccount_` | checkbox | off | Un módulo por cuenta enlazada del mes actual hasta la fecha |
| Cost metric | `_costMetric_` | string | `UnblendedCost` | Métrica de Cost Explorer: `UnblendedCost`, `NetUnblendedCost`, `BlendedCost`, `AmortizedCost` o `NetAmortizedCost` |
| Cost services filter | `_costServices_` | string | — | Nombres de facturación separados por comas. Vacío selecciona todo |
| Cost regions filter | `_costRegions_` | string | — | Códigos de región separados por comas. Vacío incluye todo y los costes globales |
| Cost accounts filter | `_costAccounts_` | string | — | IDs de cuenta enlazada de 12 dígitos separados por comas. Vacío selecciona todas las cuentas accesibles |
| Cost refresh interval | `_costRefreshInterval_` | select (interval) | `1 day` | Tiempo entre consultas a Cost Explorer; entre medias se reutiliza la caché |
| Modules allow regexp | `_moduleAllow_` | textarea | — | Una expresión regular por línea; solo se conservan los nombres de módulo que coincidan |
| Modules deny regexp | `_moduleDeny_` | textarea | — | Una expresión regular por línea; se excluyen los nombres de módulo que coincidan |

### Archivo de configuración

La tarea de Discovery genera un archivo de configuración para el plugin. Se usa el mismo formato en una ejecución manual. Es un archivo de texto plano con líneas `clave=valor`; las líneas vacías, los comentarios y las cabeceras de sección se ignoran.

| Clave | Por defecto | Descripción |
| --- | --- | --- |
| `interval` | `300` | Intervalo de monitorización en segundos, heredado por el agente |
| `group_id` | — | ID del grupo donde se crea el agente. Obligatorio, mayor que 0 |
| `creds_b64` | — | Objeto de credenciales de AWS codificado en base64. Obligatorio |
| `api_endpoint` | — | Sustitución del endpoint de las API de AWS, usado para ambas API |
| `catalog_prices_enabled` | `1` | Recoge precios de catálogo cuando es verdadero |
| `service_codes` | `AmazonEC2,AmazonS3,AmazonRDS` | Códigos de servicio de catálogo que tarifar |
| `pricing_region` | `us-east-1` | Región del endpoint de la API Price List de AWS |
| `cost_yesterday` | `1` | Lee el coste total del día anterior |
| `cost_month_to_date` | `1` | Lee el coste total del mes hasta la fecha |
| `cost_previous_month` | `1` | Lee el coste total del mes anterior |
| `cost_by_service` | `1` | Lee el desglose por servicio del mes hasta la fecha |
| `cost_by_region` | `0` | Lee el desglose por región del mes hasta la fecha |
| `cost_by_account` | `0` | Lee el desglose por cuenta del mes hasta la fecha |
| `cost_metric` | `UnblendedCost` | Métrica de Cost Explorer |
| `cost_services` | — | Filtro de servicios de la consulta de costes, separado por comas |
| `cost_regions` | — | Filtro de regiones de la consulta de costes, separado por comas |
| `cost_accounts` | — | Filtro de cuentas de la consulta de costes, separado por comas |
| `cost_refresh_interval` | `86400` | Segundos entre consultas a Cost Explorer; `0` desactiva la caché |
| `cost_cache` | archivo temporal de la tarea | Ruta del archivo de caché de Cost Explorer |
| `rate_codes_file` | — | Archivo con un rate code de AWS por línea |
| `product_filters_file` | — | Archivo con un filtro de producto `Attribute=Value` por línea |
| `module_allow_file` | — | Archivo con una expresión regular de inclusión por línea |
| `module_deny_file` | — | Archivo con una expresión regular de exclusión por línea |
| `max_products` | `250` | Número máximo de dimensiones de precio de catálogo recogidas por ejecución; `0` elimina el límite |
| `module_prefix` | — | Prefijo de los nombres de módulo de precio de catálogo y coste de cuenta |
| `agent_name` | `AWS Pricing` | Nombre del agente generado |
| `agent_autodisable` | `0` | Crea el agente en modo autodeshabilitado cuando es verdadero |

### Línea de comandos

| Argumento | Descripción |
| --- | --- |
| `--conf <archivo>` | Ejecuta el plugin con el archivo de configuración indicado |
| `--mode discover` | Modo por defecto: lee precios y costes y escribe los datos del agente y de los módulos generados |
| `--mode get_services` | Devuelve la lista de servicios de catálogo que el asistente ofrece como servicios seleccionables |
| `--creds <base64>` | Objeto de credenciales de AWS codificado en base64 para las consultas del asistente |
| `--api-endpoint <url>` | Sustitución del endpoint de las API de AWS, usado para ambas API |

### Módulos generados

Se crea un agente con el nombre configurado. Sus módulos son:

#### Precio de catálogo

Un módulo por cada dimensión de precio recogida de los servicios seleccionados, después de aplicar los filtros de rate code, atributos de producto, inclusión y exclusión. El nombre sigue `<module prefix><código de servicio> <región> <tipo de uso> <rate code>`, la descripción repite el servicio, la familia de producto, el tipo de uso, la descripción del precio y el tipo de término, y la unidad es la moneda y la medida, por ejemplo `USD per Hrs` o `USD per GB-Mo`.

#### Totales de coste de cuenta

Se crean por cada token de total habilitado, con la moneda devuelta por AWS:

| Token | Nombre del módulo |
| --- | --- |
| **Yesterday cost** | `AWS Cost Yesterday <moneda>` |
| **Month to date cost** | `AWS Cost Month to date <moneda>` |
| **Previous month cost** | `AWS Cost Previous month <moneda>` |

#### Desgloses de coste de cuenta

Se crean por cada token de desglose habilitado, un módulo por entrada facturada:

| Token | Nombre del módulo |
| --- | --- |
| **Cost by service** | `AWS Cost Month to date Service <nombre de facturación> <moneda>` |
| **Cost by region** | `AWS Cost Month to date Region <región> <moneda>` |
| **Cost by account** | `AWS Cost Month to date Account <cuenta> <moneda>` |

### Identidad del plugin

El plugin marca su agente y sus módulos con valores `extra_data` para que la extensión de consola y cualquier otra vista puedan identificarlos sin depender del nombre del agente o del módulo:

| Superficie | Marcador |
| --- | --- |
| Agente | `aws-pricing:agent:<región de precios>:<métrica de coste>` |
| Módulo de precio de catálogo | `aws-pricing:catalog:<servicio>:<región>:<sku>:<rate code>` |
| Módulo de coste de cuenta | `aws-pricing:cost:<token>:<identidad>:<moneda>` |

Los módulos de coste creados por versiones anteriores del plugin pueden usar el marcador heredado `aws-cost:<token>:<identidad>:<moneda>`; el panel reconoce ambos.
