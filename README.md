
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
	- [Colección de Postman](#coleccion-de-postman)
	- [Api keys](#api-keys)
- [Configuración para el api extractor](#configuracion)
	- [Estructura general](#coleccion-de-postman)
	- [Autenticación por tokens](#autenticacion-por-tokens)
- [Extracciones](#extracciones)
	- [Endpoint a extraer](#endpoint)
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
De todo esto lo que nos instere es el `HttpApiUrl` y el `RootApiKey` que nos servirán para consumir el api del lambda extractor.

> **Nota:** una vez hecho el depliegue, por seguridad, borre el usuario que creó con permisos de administrador para propositos del despliegue
