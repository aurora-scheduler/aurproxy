# Aurproxy build file

default: dist

.PHONY: clean setup dist init

version := $(shell date "+%Y%m%d")

# Clean up intermediate files.
clean:
	rm -rf venv dist tellapart/aurproxy/templates

# Install Python dependencies in a local virtual environment.
setup: venv/bin/activate

venv/bin/activate: requirements.txt
	test -d venv || virtualenv venv
	. venv/bin/activate; pip install -r requirements.txt
	touch venv/bin/activate

# Package up Aurproxy for distribution.
dist: dist/aurproxy-$(version).tar.gz

dist/aurproxy-$(version).tar.gz: aurproxy requirements.txt tellapart templates
	@mkdir -p dist
	tar -cvzf $@ Makefile $^

# Initialize Aurproxy for running locally.
init: setup
	cp -r templates tellapart/aurproxy/
	mkdir -p logs
