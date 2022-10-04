stage='prod'

api-logs:
	sls logs --function ConfigApi --stage $(stage)

ext-logs:
	sls logs --function ApiExtractor --stage $(stage)

deploy:
	sls deploy --verbose --stage $(stage)

remove:
	sls remove --stage $(stage)
