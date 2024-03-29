stage='prod'

api-logs:
	sls logs --function ConfigApi --stage $(stage)

ext-logs:
	sls logs --function ApiExtractor --stage $(stage)

deploy:
	sls deploy --verbose --stage $(stage)

remove:
	sls remove --stage $(stage)

fakeapi:
	uvicorn fake-api.main:app --reload --host 0.0.0.0

ngrok:
	ngrok http 8000
