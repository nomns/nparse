
PACKAGE=nparse

##############################################################################
# do this while not in venv
venv:
	python -m venv .$(PACKAGE).venv

venv.clean:
	rm -rfd .$(PACKAGE).venv



##############################################################################
# do these while in venv
run: libs.quiet
	py $(PACKAGE).py


# libs make targets ###########################
libs: requirements.txt
	pip install -r requirements.txt

libs.quiet: requirements.txt
	pip install -q -r requirements.txt

libs.clean:
	pip uninstall -r requirements.txt


# exe make targets ###########################
exe: libs
	pyinstaller nparse_py.spec

exe.clean:
	rm -rfd build
	rm dist/$(PACKAGE).exe


# install make targets ###########################
#DIRS=dist/data dist/xxx
DIRS=dist/data dist/data/maps dist/data/spells
install: exe
	$(shell mkdir $(DIRS))
	cp -r ./data/maps/* ./dist/data/maps/
	cp -r ./data/spells/* ./dist/data/spells/

install.clean:
	rm -rfd $(DIRS)


# general make targets ###########################

all: libs exe install

all.clean: libs.clean exe.clean install.clean

clean: all.clean
