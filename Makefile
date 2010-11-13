TESTS	= $(shell ls -1 tests/*.py)
PYTHON  = /usr/bin/env python

ifeq ($(V), 1)
	Q:=
else
	Q:=@
endif

.PHONY: all

all:

run:
	$(Q)PYTHONPATH=$(shell pwd) $(PYTHON) $(shell pwd)/cli/__init__.py

test: .FORCE $(TESTS)

tests/%.py: .FORCE
	$(Q)echo "Running test: $@" >&2
	$(Q)PYTHONPATH=$(shell pwd) $(PYTHON) $@ --verbose
	@echo ""

.FORCE:
