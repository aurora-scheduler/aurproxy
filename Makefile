# Aurproxy build file

default: dist

.PHONY: clean setup dist

version := $(shell date "+%Y%m%d")

# Clean up intermediate files.
clean:
	rm -rf venv dist

# Install Python dependencies in a local virtual environment.
setup: venv/bin/activate

venv/bin/activate: requirements.txt
	test -d venv || virtualenv venv
	. venv/bin/activate; pip install -r requirements.txt
	touch venv/bin/activate

# Package up Aurproxy for distribution.
dist: dist/aurproxy-$(version).tar.gz

dist/aurproxy-$(version).tar.gz: requirements.txt bin tellapart templates
	@mkdir -p dist
	tar -cvzf $@ $^
