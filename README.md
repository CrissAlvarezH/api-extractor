


# API Extractor
Esta aplicación serverles permite consumir un api que sigue estandares REST y guardar la data en un archivo `.csv` o `.json`, según se configure, en un bucket de [aws s3](https://aws.amazon.com/es/s3/) especificado en la configuración.

**Caracteristicas**

- Autenticación por token
- Refresco de token automaticamente
- Parseo de información de JSON a csv
- Permite programar la ejecución o ejecutar manualmente
- Permite seleccionar los campos especificos que se desea extraer
- Soporta paginación en las apis, ya sea por links o por paginas sequenciales
- La data sensible como tokens, client ids, etc, se pueden guardar en [aws secrets](https://aws.amazon.com/es/secrets-manager/) y referencialos en la configuración del extractor
- Permite aplicar transformaciones a la data
- El extractor tiene api propia para hacer la configuración y ejecución del mismo
- Etc.

## Documentación

- [Infraestructura](#infraestructura)
- [Despliegue](#despliegue)
	- [Destrucción de recursos](#destrucción-de-recursos)
- [API](#api)
	- [Colección de Postman](#colección-de-postman)
	- [Api keys](#api-keys)
- [Configuración para el api extractor](#configuración-para-el-api-extractor)
	- [Estructura general](#estructura-general)
		- [Endpoint](#endpoint)
		- [JsonField](#jsonfield)
	- [Autenticación por tokens](#autenticación-por-tokens)
		- [Refresco de token automatico](#refresco-de-token-automatico)
	- [Ejecutar una configuración](#ejecutar-una-configuración)
		- [Logs de ejecución](#logs-de-ejecución)
- [Extracciones](#extracciones)
	- [Endpoint a extraer](#endpoint-a-extraer)
	- [Transformaciones](#transformaciones)
		- [Actions](#actions)
	- [Paginación](#paginación)
		- [PaginationParameters](#paginationparameters)
		- [ConditionExpression](#conditionexpression)
	- [Esquema de la data](#esquema-de-la-data)
	- [Destino en S3](#destino-en-s3)
- [Referencias a **secret**, **last** y **self**](#referencias)
- [Ejemplos](#ejemplos)
	- [Zoho](#zoho)

# Infraestructura 
<img src='https://github.com/CrissAlvarezH/api-extractor/blob/main/docs/imgs/aws-arch-diagram.png'/>


# Despliegue
El despliegue se hace en una cuenta de [AWS](https://aws.amazon.com/), para eso es necesario los siguientes pre-requisitos

- Instalar [Serverless framework](https://www.serverless.com/framework/docs/getting-started) en la maquina local, el cual es el framework usado para desplegar el proyecto en los ambientes en aws.
- `access key id` y `access secret key` de un usuario de [AWS IAM](https://aws.amazon.com/es/iam/) con permisos de administrador que será usado por `serverless framework` para crear la infraestructura vía linea de comandos.
- Configurar los access key del usuario del paso anterior en la maquina local, esto se puede hacer usando el [CLI de aws](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) y corriendo el comando: `aws configure`
- (Opcional o en caso de obtener un error) Configurar variables de entorno del proyecto, para esto copiamos y pegamosel archivo `.env.example` y lo renombramos a `.env`, esto lo podemos hacer a mano, o con el siguiente comando (dentro de la carpeta del proyecto):
	```
	cp .env.example .env
	```
	luego establecemos los valores como queramos, el primer valor es **EVENT_BRIDGE_SCHEDULE** el cual por defecto es `0 1 * * ? *` y es la expresión cron que indica la ejecución automatica de las extracciones.
	
	La segunda variable de entorno es **DEFAULT_OUTPUT_BUCKET_SUFFIX** que por defecto es `1` y es un texto que se pone al final del nombre del bucket por defecto donde se guarda el output de las extracciones, el cual es `api-extractor-output-prod` y al final del nombre se agregar este suffix.
	Esto será necesario configurarlo porque el nombre de los bucket deben ser unicos y si el nombre actual ya esta ocupado entonces debemos añadir un sufijo para hacerlo unico, usando esta variable de entorno, el error que arroja el deploy que nos indica esto es el siguiente:
	```
	Error:
	CREATE_FAILED: ExtractorOutputBucket (AWS::S3::Bucket)
	api-extractor-output-prod-1 already exists
	```

- (Opcional) Si estamos en Linux o Mac podemos instalar Make usando

	    # Linux
	    sudo apt install make

		# Mac
	    brew install make
	    
Una vez cumplidos los puntos anteriores estamos listo para desplegar, para esto corremos el comando

    make deploy
Usando make, o si no queremos instalar make, podemos correr

    sls deploy --verbose --stage prod

El anterior comando nos debe dar un output al final como el siguiente:

    Stack Outputs:
	  ApiExtractorLambdaFunctionQualifiedArn: *******
	  ConfigApiLambdaFunctionQualifiedArn: *******
	  RootApiKey: 8b189c1d8fadhf8h4nk0fadh3nd8848667
	  HttpApiId: ********
	  ServerlessDeploymentBucketName: *********
	  HttpApiUrl: https://had73had0.us-east-2.amazonaws.com
De todo esto lo que nos insteresa es el `HttpApiUrl` y el `RootApiKey` que nos servirán para consumir el api del lambda extractor.

> **Nota:** una vez hecho el depliegue, por seguridad, borre el usuario que creó con permisos de administrador para propositos del despliegue

### Destrucción de recursos
En algunos casos será necesario destruir todos los recursos de aws que fueron creados en el deploy, para esto primero tenemos que limpiar el bucket creado para guardar el output de las extracciones `api-extractor-output-prod`, luego podemos proceder a destruir los recursos con el siguiente comando

**Usando make:**
``` 
make remove
```
**Sin make:**
```
sls remove --stage prod
```

# API

El lamnda api extractor tiene un api para realizar la configuración, ejecutar manualmente y monitorear las ejecuciones del mismo

## Colección de Postman

El archivo `docs/postman_collection.json` dentro de este repo lo podemos importar en [Postman](https://www.postman.com/).
Una vez importado veremos los siguientes endpoints para consumir

<img width="300px" src='https://github.com/CrissAlvarezH/api-extractor/blob/main/docs/imgs/postman-collection.png'/>

## Api keys

Para poder hacer uso del api es necesario usar un api key, al realizar el despliegue este nos arroja un api key que pertenece al usuario root llamada `RootApiKey`, con esta key podemos consumir el api pero es recomendable crear mas api key para cada persona que va a hacer cambios en la configuración del api, ya que el nombre de cada api key queda guardado en el historial de cambios de la configuración, por lo que al tener un api key para cada persona podemos rastrear cada cambio de cada persona.

Para crear, refrescar y borrar api keys usaremos la carpeta

<img width="300px" src='https://github.com/CrissAlvarezH/api-extractor/blob/main/docs/imgs/postman-api-keys.png'/>

> **Importante:** Solo el api key del root puede crear otras api keys y no se puede borrar desde el api

Estas api keys se guardan en un [secret de aws](https://aws.amazon.com/es/secrets-manager/) el cual es creado en el deploy y tiene el nombre `api-extractor-config/prod/apikeys`, desde aquí es la unica forma de borrar el api key del root, el resto se pueden borrar desde el api por Postman.

<img width="700px" src='https://github.com/CrissAlvarezH/api-extractor/blob/main/docs/imgs/aws-api-keys-secrets.png'/>


# Configuración para el api extractor

La configuración del extractor se hace mediante el api, si usted importó la colección de Postman podrá ver los siguientes endpoints ahí

<img width="300px" src='https://github.com/CrissAlvarezH/api-extractor/blob/main/docs/imgs/postman-api-config-folder.png'/>

De los cuales los endpoints que nos sirven para crear, modificar y borrar una configuración para un api extractor son 

- `List api configs` para listar todas las configuraciones existentes
- `Retrieve api config` para ver una configuracion especificada por el id en los parametros del endpoint
- `Create api config` para crear una configuración nueva
- `Update api config` para actualizar pasando el id
- `Delete api config` para borrar una configuración

## Estructura general

``` json
{
	"name":  "<string>",
	"auth":  {
		"refresh_token":  {
			"endpoint":  <Endpoint>,
			"response_token_key":  <JsonField>
		},
		"access_token":  "<string>"
	},
	"extractions":  [
		{...},
		{...},
		{...}
	]
}
```

## Endpoint
El endpoint es la representació, en la configuración del extractor, de un endpoint en la vida real, con su `url` y demas parametros como los `query_params` que son los parametros que van en la url, los `headers` y el `body`.
El unico campo obligatorio es la `url`, el resto son opcionales si no se necesitan.
``` json
{
	"url": "<string>",
	"query_params": "<json>",
	"headers": "<json>",
	"body": "<json>"
}
```

Este objeto se usa en el modulo de `auth` para especificar el endpoint al cual se tiene que apuntar para obtener el refresco del token, y tambien se usa en cada extracción para especificar el endpoint del cual se va a extraer la data



## JsonField

Se usa para especificar un campo en un json, cada campo se separa por un punto, por ejemplo, para el json

``` json
{
	"user": {
		"name": "Cristian",
		"account": {
			"number": 2334,
			"type": "credit"
		}
	}
}
```

Para obtener el number del account el user, se usa el JsonField

    user.account.number

El cual retornará `2334`


## Autenticación por tokens

En la configuración se puede especificar el access token que se va a usar en el apartado de `auth.access_token` y este se puede usar luego en las extracciones usando referencias.

### Refresco de token automatico

Si el token tiene algun tiempo limite de uso y luego explira, podemos configurar el refresco del token, para esto debemos introducir la configuración en `auth.refresh_token` en el cual podemos especificar el endpoit en el cual se realiza el refresh y luego, especificar cual campo de la respuesta de ese endpoint contiene el token renovado, usando el campo `auth.refresh_token.response_token_key`

**Por ejemplo:** 
suponiendo que para renovar un token debo hacer una petición al endpoint

    https://accounts.com/oauth/v2/token?refresh_token=afe21e5ac3f9ea12639

Y este responde con:

``` json
{
	"mytoken":  "fa146b8e6a67366fd991c7d65",
	"api_domain":  "https://www.api.com",
	"token_type":  "Bearer",
	"expires_in":  3600
}
```
Para este caso la configuración deberá ser la siguiente

``` json
{
	"auth": {
		"endpoint": {
			"url": "https://accounts.com/oauth/v2/",
			"query_params": {
				"refresh_token": "afe21e5ac3f9ea12639"
			}
		},
		"response_token_key": "mytoken"
	}
}
```

## Ejecutar una configuración

Para ejecutar una configuració ya creada manualmente usamos el endpoint

<img width="800px" src='https://github.com/CrissAlvarezH/api-extractor/blob/main/docs/imgs/postman-execute-config.png'/>

En el parametro **config_id** debemos poner el id de la configuración antes de dar click en **send**

Una vez enviada, se lanzará el lambda de extracción para ejecutar dicha configuración, el endpoint responderá de inmediato pero el proceso de ejecución tardará segun la configuración del mismo y la cantidad de data que deba extraer.

### Logs de ejecución

Para ver los logs del proceso debemos utilizar el siguiente endpoint

<img width="800px" src='https://github.com/CrissAlvarezH/api-extractor/blob/main/docs/imgs/postman-execution-logs.png'/>

Es importante poner el **extraction_id** el cual no se debe confundir con el id de la configuración, el **extraction_id** es el id que tiene cada item dentro de el campo `extractions` dentro de la configuración

Los logs tienen la siguiente estructura:

``` json
{
	"extraction_name": "",
	"extraction_id": "",
	"config_name": "",
	"config_id": "",
	"success": "true | false",
	"error": "null | error_message", // error en caso de ocurrir
	"data_inserted_len": "number", // cantidad de data extraida
	"destiny": "", // ruta en s3 del archivo .csv
	"last": "<json>", // ultimo item extraido la
	"created_at": "", // fecha de inserción del log
}
```

# Extracciones

Las extracciones van configuradas en el capo `extractions` de la configuración del extractor vista en el punto de la [estructura general](#estructura-general).
Cada extracción tiene la siguiente estructura

``` json
{
	"name": "<string>",
	"endpoint": <Endpoint>,
	"data_key": <JsonField>,
	"format": "csv | json", # formato a guardar en el destino
	"pagination": {
		"type": "sequential | link",
		"parameters": <PaginationParameters>
	},
	"data_schema": "<json>",
	"s3_destiny": {
		"bucket": "<string>",
		"folder": "<string>"
	}
}
```
## Endpoint a extraer
Este es el `endpoint` de la configuración de la extracción, y funciona exactamente igual que el [Endpoint](#endpoint) explicado previamente.

En este caso representa el endpoint al cual se le va a consulta la data a extraer, para obtener esta data se usa el campo `data_key` el cual indica en cual campo de la respuesta del endpoint esta la data a extraer.

Por ejemplo, si la respuesta del endpoint es

``` json
{
	"result": [
		...
	],
	"pagination": {
		"current_page": 1,
		"total_page": 3,
		"on_page": 50
	}
}
```
Entonces el `data_key` debería ser `result`

## Transformaciones
Las transformaciones permite aplicar funciones que modifiquen la data de las columnas despues de mapearlas por el `data_schema`, existen varios tipos de normalizaciones, a continuación se explica la estructura a definir:
``` json
{
	"extractions": [
		...
		{
			...
			"transformations": [
				...
				{
					"action": "<string>",
					"priority": "<number>"
					"on": [],
					"new_column_prefix": "<string>",
					"params": {}
				}
			]
		}
	]
}
```
`action` es el nombre de la transformación, dependiendo de esta los `params` serán unos u otros, en la siguiente sección están todas las `action` disponibles y sus respectivos parametros.
`priority` le indica al programa en que orden va a ejecutar las transformaciones, se ordenan de mayor a menos, por defecto es 0.
`on` es una lista de nombres de columnas sobre las cuales se va a aplicar la transformación.
`new_column_prefix` lo usamos cuando queremos que el resultado de la transformación no sobreescriba la columna sobre la cual se está aplicando, si no mas bien, que cree una nueva columna, y esta nueva columna usará este valor como prefijo en su nombre, si no se define este parametro entonces se sobreescribirá la columna con el resultado de la normalización.
`params` son los parametros que recibe la normalización, los cuales cambian dependiendo de cual sea esta.

### Actions
A continuación se enumaran las actions disponibles para usar en las transformaciones, así como tambien sus respectivos params:

-  **replace**
	Es usado para remplazar unos caracteres por otros, los `params` de esta `action` son **to_replace** el cual el string que 	 se va a reemplazar por el parametro **value**
- **trim**
	Se utilia para borrar los espacios en blanco a la derecha e izquierda de los valores de la columna donde se aplique, si solo queremos borrar los espacios de la derecha, usamos en su lugar **rtrim**, o si es a la izquierda, entonces usamos **ltrim**
- **lower**
	Nos permite pasar a minusculas los valores
- **upper**
	Nos permite pasar a mayusculas los valores
- **title**
	Pone en mayusculas solo la primera letra de cada palabra
- **capitalize**
	Unicamente la primera letra de todo el texto será establecida en mayusculas
- **split**
	Divide el texto partiendolo por un determinado caracter, devolviendo así una lista de strings, para especificar el caracter por el cual se va a devidir el texto, usamor el `param` **char**
- **join**
Nos permite unir una lista convirtiendola en una cadena de texto, los elementos de la lista serán unidos usando un caracter el cual es parado por `params` como **sep**
- **slice**
Es usado para obtener un sub porción de un texto, para esto debemos especificar la posición desde la empieza y termina esta extracción, para eso usamos los `params` **start** y **stop** respectivamente.

## Paginación

Muchas apis estan paginadas, por lo que es necesario dar soporte a la paginación, por lo general existen dos tipos de paginación

-  **Paginación secuencial**
Se trata simplemente de una paginación donde existe un parametro **page** que indica en cual pagina nos encontramos, y cada pagina corresponde a un numero

- **Paginación por link**
En este caso no necesariamente hay un parametro llamado `page`, mas bien en la paginación nos dan el siguiente link al cual debemos apuntar para obtener la siguiente pagina de la data

Dependiendo de cual sea la paginación del api que queremos consumir, debemos agregar unos parametros u otros, estos parametros se explican a continuación

### PaginationParameters
Dependiendo del tipo de paginación los parametros son distintos.
Para una paginación de tipo `sequential` los parametros son:
``` json
{
	"param_name": "<string>",
	"start_from": "<number>",
	"there_are_more_pages": <ConditionExpression | JsonField>
}
```
- **param_name**:  expresa cual es el nombre del parametro que le indica al api el numero de la pagina, usualmente es `page`
- **start_from**: indica desde cual pagina empezaremos
- **there_are_more_pages**: es una expression condicional explicada mas adelante, o un field del json de la respuesta del api el cual es boolean e indica si hay mas paginas por recorrer


Cuando es de tipo `link` los parametros son

``` json
{
	"next_link": <JsonField>
}
```
Este `next_link` hace referencia al link de la proxima pagina, el cual viene en el json del body, por tanto se debe especificar como accederlo, por ejemplo, un valor valido sería `pagination.next_link` para el caso de que el response tenga el link ubicado ahí.


#### ConditionExpression
Hace referencia a una condición que puede ser verdadera o falsa que tiene la siguiente estructura

    <field> <operator> <field>

Los `field` pueden ser, ya sea, un campo en el json de la respuesta de endpoint (por ejemplo `info.current_page`) o un valor como tal (por ejemplo `23`)
El `operator` puede ser `==`, `<=`, `>=`, `!=`, `>` ó `<`.

Ejemplo:

Para el response:
``` json
{
	"data": [
		// ...
	],
	"info": {
		"current_page": 2,
		"total_pages": 10
	}
}
```

La condición podría ser

    info.current_page < info.total_pages

**Lo cual retornará `false` siempre que aun falten paginas por recorrer, el cual es el objetivo de este expression, retornar `true` cuando hay mas paginas por recorrer y `false` cuando ya no hay mas**


## Esquema de la data

Este campo es el `data_schema`, si no se especifica va a tomar toda la data tal cual como viene del api y la va a guardar en el archivo .csv o .json, pero si queremos darle un formato especifico a la data y seleccionar solo ciertos campos podemos usar este esquema para eso, de la siguiente manera:

El esquema es un json en el cual especificas los campos a guardar en el .csv, el nombre del key en cada json corresponde al key en la data del endpoint, y el nombre del value es el nombre de la columna que tendrá en el .csv, por ejemplo:

Si el response del endpoint es:

``` json
{
	"result": [
		{
			"name": "Cristian",
			"age": 26,
			"acount": 11111,
			"city": "Montería"
		},
		{
			"name": "Jose",
			"age": 23,
			"acount": 2222,
			"city": "Bogotá"
		}
	]
}
```

Y queremos guardar solo el `name`, `account` y `city`, podemos crear un `data_schema` así:

``` json
{
	"name": "user_name", 
	"account": "user_account",
	"city": "city"
}
```

Esto dará como resultado el siguiente .csv


| user_name         | user_account  | city          |
|-------------------|---------------|---------------|
| Cristian   	    | 11111         | Montería      |
| Juan              | 2222          | Bogotá        |


### Subelementos

Si necesitas acceder a un elemento que esta anidado, la sintaxis seriá la siguiente.

**Data:**
``` json
[
	{
		"type": "A",
		"user": {
			"name": "Cristian",
			"account": {
				"number": 3344
			}
		}
	},
	{
		"type": "B",
		"user": {
			"name": "Juan",
			"account": {
				"number": 5555
			}
		}
	}
]
```
**Esquema:**
``` json
{
	"type": "type",
	"user": {
		"name": "user_name",
		"account": {
			"number": "user_acc_number"
		}
	}
}
```

**Resultado:**

| type       | user_name         | user_acc_number   |
|------------|-------------------|-------------------|
|  A         | Cristian          | 3344   	         |
|  B         | Juan              | 5555              | 


## Destino en S3

Es la ruta en donde guardará el archivo .csv con el resultado de la extracción, en la configuración es `s3_destiny` y se compone por un `bucket` y un `folder`

``` json
{
	"bucket": "<string>",// default: api-extractor-output-prod
	"folder": "<string>" // default: sin folder
}
```
Si no se especifica el `s3_destinty` tomará los valores default

# Referencias

En la sitaxis de la configuración es permitido agregar referencias a valores que son dinamicos, ya sea porque estan guardados en otro lugar como en la base de datos o en un secreto de aws, o porque es un valor cambiante dentro de la misma configuración y necesitamos referenciar siempre el valor actual de ese campo.

Un ejemplo de sintaxis para declarar una referencia es `$(self::auth.access_token, token_default)`. 
La estructura es `$(<tipo>::<referencia>, <valor por defecto>)`

Los tipos de referencia son

- ## self

Este hace referencia al mismo json de configuración, es muy usado por ejemplo para hacer referencia al token, ya que este se refresca cada vez que se ejecuta, para poder usarlo podemos usar la referencia, por ejemplo:

``` json
{
	"auth": {
		"refresh_token": {
			"endpoint": {
				"url": "https://accounts.com/oauth/v2/",
				"query_params": {
					"refresh_token": "afe21e5ac3f9ea12639"
				}
			},
			"response_token_key": "mytoken"
		},
		"access_token": ""
	},
	"extractions": [
		{
			...,
			"endpoint": {
				...,
				"headers": {
					"Authorization": "Bearer ${self::auth.access_token}"
				}
			}
		}
	]
}
```

En este caso estamo mandando el token guardado en `auth.access_token` dentro de la misma configuració y que es renovado cada vez gracias a la configuracion del `refresh_token`.

- ## last

Cada vez que se ejecuta una extracción se insertan [logs de la ejecución](#logs-de-ejecución) dentro del cual se guarda el ultimo item extraido, el **last** hace referencia a este ultimo item, por lo que si queremos hacer referencia a algun campo del ultimo item de la ejecución previa lo podemos hacer de esta forma:

``` json
{
	...,
	"extractions": [
		{
			...,
			"endpoint": {
				...,
				"query_params": {
					"start_from": "$(last::id, 1)"
				}
			}
		}
	]
}
```

Es esta configuración estamos mandando al endpoint de extracción el `id` del ultimo item extraido a travez del query param `start_from` y en caso de ser la primera vez en ejecutar o de no tener un item previo guardado, tomará el valor por dejecto `1`

- ## secret

Esta referencia va a buscar el valor dentro del secret llamado `api-extractor-config/prod/extractor-secrets` el cual es creado en el deploy.
La sintaxis es igual que el resto, y esta tiene especial uso para el modulo de `auth` ya que ahí se suele colocar valores delicados como api keys, client ids, etc, por ejemplo:

``` json
{
	"auth": {
		"refresh_token": {
			"endpoint": {
				"url": "https://accounts.com/oauth/v2/token",
				"query_params": {
					"refresh_token": "${secret::refresh_token}",
					"client_id": "${secret::client_id}",
					"client_secret": "${secret::client_secret}",
					"grant_type": "refresh_token"
				}
			},
			"response_token_key": "access_token"
		},
		"access_token": ""
	}
}
```


# Ejemplos

## Zoho

La configuración para el [api de zoho](https://www.zoho.com/crm/developer/docs/api/v3/get-records.html) es la siguiente:

``` json
{
	"name":  "Zoho",
	"auth":  {
		"refresh_token":  {
			"endpoint":  {
				"url":  "https://accounts.zoho.com/oauth/v2/token",
				"query_params":  {
					"refresh_token":  "${secret::zoho_refresh_token}",
					"client_id":  "${secret::zoho_client_id}",
					"client_secret":  "${secret::zoho_client_secret}",
					"grant_type":  "refresh_token"
				}
			},
			"response_token_key":  "access_token"
		},
		"access_token":  ""
	},
	"extractions":  [
		{
			"name":  "deals",
			"endpoint":  {
				"url":  "https://www.zohoapis.com/crm/v2/deals",
				"headers":  {
					"Authorization":  "Bearer ${self::auth.access_token}",
					"If-Modified-Since":  "${last::Modified_Time, 2020-09-03T17:40:53-05:00}"
				},
				"query_params":  {
					"sort_by":  "Modified_Time",
					"sort_order":  "asc"
				}
			},
			"s3_destiny":  {
				"folder":  "zoho/deals/"
			},
			"data_key":  "data",
			"format": "csv",
			"data_schema": {
				"Owner": {
					"name": "owner_name",
					"id": "owner_id",
					"email": "owner_email"
				},
				"Description": "description",
				"$currency_symbol": "currency_symbol",
				"$field_states": "field_states",
				"$review_process": {
					"approve": "review_process_approve",
					"reject": "review_process_reject",
					"resubmit": "review_process_resubmit"
				},
				"Duraci_n_del_contrato": "duracion_del_contrato",
				"$followers": "followers",
				"Numero_de_cotizaci_n": "numero_de_cotizacion",
				"Closing_Date": "closing_date",
				"Causas_de_perdida": "causas_de_perdida",
				"Last_Activity_Time": "last_activity_time",
				"Opex": "opex",
				"Modified_By": {
					"name": "modified_by_name",
					"id": "modified_by_id",
					"email": "modified_by_email"
				},
				"$review": "review",
				"Lead_Conversion_Time": "lead_conversion_time",
				"$state": "state",
				"$process_flow": "process_flow",
				"Deal_Name": "deal_name",
				"Expected_Revenue": "expected_revenue",
				"Overall_Sales_Duration": "overall_sales_duration",
				"Stage": "stage",
				"Account_Name": {
					"name": "account_name_name",
					"id": "account_name_id"
				},
				"id": "id",
				"Preventa_2": "preventa_2",
				"$approved": "approved",
				"$approval": {
					"delegate": "approval_delegate",
					"approve": "approval_approve",
					"reject": "approval_reject",
					"resubmit": "approval_resubmit"
				},
				"Modified_Time": "modified_time",
				"Created_Time": "created_time",
				"Amount": "amount",
				"$followed": "followed",
				"Probability": "probability",
				"$editable": "editable",
				"$orchestration": "orchestration",
				"Contact_Name": {
					"name": "contact_name_name",
					"id": "contact_name_id"
				},
				"Sales_Cycle_Duration": "sales_cycle_duration",
				"Type": "type",
				"$in_merge": "in_merge",
				"Capex": "capex",
				"Lead_Source": "lead_source",
				"Servicio": "servicio",
				"Created_By": {
					"name": "created_by_name",
					"id": "created_by_id",
					"email": "created_by_email"
				},
				"Tag": "tag",
				"$approval_state": "approval_state",
				"$pathfinder": "pathfinder"
			},
			"pagination":  {
				"type":  "sequential",
				"parameters":  {
					"param_name":  "page",
					"start_from":  1,
					"there_are_more_pages":  "info.more_records"
				}
			}
		}
	]
}
```

Una vez creada esta configuracioón se debe agregar al secret `api-extractor-config/prod/extractor-secrets` lo valores que estan en la parte de `auth`, así:

<img width="800px" src='https://github.com/CrissAlvarezH/api-extractor/blob/main/docs/imgs/example-zoho-secrets.png'/>
