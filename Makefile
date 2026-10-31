tables:
	./reproduce.sh tables
full:
	./reproduce.sh full
reproduce: tables
test:
	.venv/bin/python -m pytest -q tests
.PHONY: tables full reproduce test
