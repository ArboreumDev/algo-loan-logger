dev-api-local:
	uvicorn main:app --app-dir app/ --reload --port 8000 --host 0.0.0.0

test-local:
	cd app && python -m pytest