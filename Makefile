.PHONY: all install run

all: install

install:
	cd backend && \
	pipenv install -r requirements.txt && \
	pipenv install && \
	pipenv run python -m litestar run --host 0.0.0.0 --port 8000

run:
	cd backend && \
	pipenv run python -m litestar run --host 0.0.0.0 --port 8000
