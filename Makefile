.PHONY: backend-test backend-lint backend-format-check frontend-build check

backend-test:
	cd backend && pytest

backend-lint:
	ruff check backend

backend-format-check:
	ruff format --check backend

frontend-build:
	cd frontend && npm run build

check: backend-lint backend-format-check backend-test frontend-build
