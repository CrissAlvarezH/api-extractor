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

- [Funcionamiento](#funcionamiento)
- [Prerequisitos](#prequisitos)
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
