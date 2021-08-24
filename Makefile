# \ var
# detect module/project name by current directory
MODULE  = $(notdir $(CURDIR))
# detect OS name (only Linux/MinGW)
OS      = $(shell uname -s)
# current date in the `ddmmyy` format
NOW     = $(shell date +%d%m%y)
# release hash: four hex digits (for snapshots)
REL     = $(shell git rev-parse --short=4 HEAD)
# current git branch
BRANCH  = $(shell git rev-parse --abbrev-ref HEAD)
# number of CPU cores (for parallel builds)
CORES   = $(shell grep processor /proc/cpuinfo| wc -l)
# / var

# \ dir
# current (project) directory
CWD     = $(CURDIR)
# compiled/executable files (target dir)
BIN     = $(CWD)/bin
# documentation & external manuals download
DOC     = $(CWD)/doc
# libraries / scripts
LIB     = $(CWD)/lib
# source code (not for all languages, Rust/C/Java included)
SRC     = $(CWD)/src
# temporary/flags/generated files
TMP     = $(CWD)/tmp
# Rust toolchain
CAR     = $(HOME)/.cargo/bin
# / dir

# \ tool
# http/ftp download
CURL    = curl -L -o
PY      = $(BIN)/python3
PIP     = $(BIN)/pip3
PYT     = $(BIN)/pytest
PEP     = $(BIN)/autopep8
RUSTUP  = $(CAR)/rustup
CARGO   = $(CAR)/cargo
RUSTC   = $(CAR)/rustc
# / tool

# \ src
P += config.py
Y += $(MODULE).py test_$(MODULE).py
Y += metaL.py test_metaL.py
R += $(shell find src -type f -regex ".+.rs$$")
# / src
S += $(Y)
S += $(R)

# \ all
.PHONY: all
all: Cargo.toml $(R)
	$(CARGO) test && $(CARGO) fmt
	RUST_LOG=trace $(CARGO) run

# \ test
.PHONY: test
test: test_py test_rs

test_py: $(PYT) test_$(MODULE).py test_metaL.py
	$^

test_rs: Cargo $(R)
	$(CARGO) test
# / test

# \ format
.PHONY: format
format: tmp/format
tmp/format: tmp/format_py tmp/format_rs
	touch $@

tmp/format_py: $(Y)
	$(PEP) --ignore=E26,E302,E305,E401,E402,E701,E702 --in-place $?

tmp/format_rs: $(Y)
	$(CARGO) fmt
# / format

.PHONY: meta
meta: $(PY) metaL.py
	$(MAKE) test_py tmp/format_py
	$^ $@
# / all

# \ install
.PHONY: install update
install: $(OS)_install
	$(MAKE) $(PIP)
	$(MAKE) $(RUSTUP)
	$(MAKE) update
update: $(OS)_update
	$(PIP) install -U pytest autopep8
	$(PIP) install -U -r requirements.txt
	$(RUSTUP) update
	$(CARGO) update

Linux_install Linux_update:
ifneq (,$(shell which apt))
	sudo apt update
	sudo apt install -u `cat apt.txt`
endif

$(PY) $(PIP) $(PYT) $(PEP):
	python3 -m venv .

rust: $(RUSTUP)
$(RUSTUP):
	curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
# / install

# \ merge
MERGE  = Makefile README.md apt.* .gitignore $(S)
MERGE += .vscode bin doc lib src tmp
MERGE += requirements.txt $(Y)
MERGE += Cargo.toml $(R)

.PHONY: dev
dev:
	git push -v
	git checkout $@
	git pull -v
	git checkout ponymuck -- $(MERGE)

.PHONY: ponymuck
ponymuck:
	git push -v
	git checkout $@
	git pull -v

.PHONY: release
release:
	git push -v
	$(MAKE) ponymuck

.PHONY: zip
zip:
# / merge
