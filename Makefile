.PHONY: unit integration all
unit:
	python -m pytest -q
integration:
	python -m pytest -q tests
all: unit integration
