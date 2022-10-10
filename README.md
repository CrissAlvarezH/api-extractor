

# API Extractor
Esta aplicación serverles permite consumir un api que sigue estandares REST y guardar la data en un archivo `.csv` en un bucket de [aws s3](https://aws.amazon.com/es/s3/) especificado en la configuración.

**Caracteristicas**

- Autenticación por token
- Refresco de token automaticamente
- Parseo de información de JSON a csv
- Permite programar la ejecución o ejecutar manualmente
- Permite seleccionar los campos especificos que se desea extraer
- Soporta paginación en las apis, ya sea por links o por paginas sequenciales
- La data sensible como tokens, client ids, etc, se pueden guardar en [aws secrets](https://aws.amazon.com/es/secrets-manager/) y referencialos en la configuración del extractor
- El extractor tiene api propia para hacer la configuración y ejecución del mismo
- Etc.

## Documentación

- [Infraestructura](#infraestructura)
- [Despliegue](#despliegue)
- [API](#api)
	- [Colección de Postman](#colección-de-postman)
	- [Api keys](#api-keys)
- [Configuración para el api extractor](#configuración-para-el-api-extractor)
	- [Estructura general](#estructura-general)
		- [Endpoint](#endpoint)
		- [PaginationParameters](#paginationparameters)
			- [ConditionExpression](#conditionexpression)
		- [JsonField](#jsonfield)
	- [Autenticación por tokens](#autenticacion-por-tokens)
	- [Ejecutar una configuración](#ejecutar-una-configuración)
- [Extracciones](#extracciones)
	- [Endpoint a extraer](#endpoint-a-extraer)
		- [Paginación](#paginacion)
	- [Esquema de la data](#esquema-de-la-data)
	- [Destino en S3](#destino-en-s3)
- [Referencias a **secret**, **last** y **self**](#referencias-a-secrets-last-y-self)
- [Ejemplos](#ejemplos)
	- [Zoho](#zoho)

# Infraestructura 
<img src='https://github.com/CrissAlvarezH/api-extractor/blob/main/docs/imgs/aws-arch-diagram.png'/>


# Despliegue
El despliegue se hace en una cuenta de [AWS](https://aws.amazon.com/), para eso es necesario los siguientes pre-requisitos

- Instalar [Serverless framework](https://www.serverless.com/framework/docs/getting-started) en la maquina local, el cual es el framework usado para desplegar el proyecto en los ambientes en aws.
- `access key id` y `access secret key` de un usuario de [AWS IAM](https://aws.amazon.com/es/iam/) con permisos de administrador que será usado por `serverless framework` para crear la infraestructura vía linea de comandos.
- Configurar los access key del usuario del paso anterior en la maquina local, esto se puede hacer usando el [CLI de aws](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) y corriendo el comando: `aws configure`

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

## PaginationParameters
Dependiendo del tipo de paginación los parametros son distintos.
Para una paginación de tipo `sequential` los parametros son:
``` json
{
	"param_name": "<string>"
	"start_from": "<number>"
	"there_are_more_pages": <ConditionExpression | JsonField>
}
```
Cuando es de tipo `link` los parametros son

``` json
{
	"next_link": <JsonField>
}
```
Este `next_link` hace referencia al link de la proxima pagina, el cual viene en el json del body, por tanto se debe especificar como accederlo, por ejemplo, un valor valido sería `pagination.next_link` para el caso de que el response tenga el link ubicado ahí.


### ConditionExpression
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

