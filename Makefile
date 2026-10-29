PORT ?= 8765
HOST ?= 127.0.0.1

ifeq ($(OS),Windows_NT)
    VENV_PYTHON := $(wildcard .venv/Scripts/python.exe)
    ifeq ($(strip $(VENV_PYTHON)),)
        PYTHON ?= python
    else
        PYTHON ?= .venv/Scripts/python.exe
    endif
else
    VENV_PYTHON := $(wildcard .venv/bin/python)
    ifeq ($(strip $(VENV_PYTHON)),)
        PYTHON ?= python3
    else
        PYTHON ?= .venv/bin/python
    endif
endif

.PHONY: findjob serve run ingest score install help

help:
	@echo make findjob  — ingest watchlist + inbox, score new jobs, open the review UI
	@echo make serve    — review UI only (http://$(HOST):$(PORT))
	@echo make run      — ingest + score, then exit
	@echo make ingest   — pull jobs, do not score
	@echo make score    — score status=new jobs only

install:
ifeq ($(OS),Windows_NT)
	@if not exist .venv (python -m venv .venv)
	$(PYTHON) -m pip install -q -e .
else
	@test -d .venv || python3 -m venv .venv
	$(PYTHON) -m pip install -q -e .
endif

findjob:
	$(PYTHON) -m jobcopilot run
	@echo Opening review UI at http://$(HOST):$(PORT)
	$(PYTHON) -m jobcopilot serve --host $(HOST) --port $(PORT)

serve:
	$(PYTHON) -m jobcopilot serve --host $(HOST) --port $(PORT)

run:
	$(PYTHON) -m jobcopilot run

ingest:
	$(PYTHON) -m jobcopilot ingest

score:
	$(PYTHON) -m jobcopilot score
