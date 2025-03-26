.PHONY: all

all:
	cd backend && \
	pipenv install -r requirements.txt && \
	pipenv install && \
	pipenv run python -m litestar run --host 0.0.0.0 --port 8000
