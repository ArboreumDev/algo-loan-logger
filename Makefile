dev-api-local:
	uvicorn main:app --app-dir app/ --reload --port 8000 --host 0.0.0.0

test-local:
	cd app && python -m pytest

lint:
	flake8 app app/routes app/test app/utils --max-line-length=120

lint-format:
	black app app/routes app/test app/utils --line-length=120
	autoflake app app/routes app/test app/utils --remove-unused-variables --remove-all-unused-imports --in-place -r
	isort app app/routes app/test app/utils

