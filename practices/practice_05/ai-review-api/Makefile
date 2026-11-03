# Работает и в Git Bash на Windows, и в Linux/macOS.
ifeq ($(OS),Windows_NT)
PY ?= python
VENV_PY := .venv/Scripts/python.exe
else
PY ?= python3
VENV_PY := .venv/bin/python
endif

.PHONY: install test check mcp-demo

install:
	$(PY) -m venv .venv
	$(VENV_PY) -m pip install -r requirements.txt

test check:
	sh scripts/check.sh

# Ручной вызов собственного MCP-сервера: корректный вход и ошибочный вход.
mcp-demo:
	$(VENV_PY) scripts/mcp_demo.py
