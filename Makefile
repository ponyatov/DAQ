# \ var
MODULE  = $(notdir $(CURDIR))
OS      = $(shell uname -s)
# / var

# \ dir
CWD     = $(CURDIR)
BIN     = $(CWD)/bin
DOC     = $(CWD)/doc
LIB     = $(CWD)/lib
SRC     = $(CWD)/src
TMP     = $(CWD)/tmp
# / dir
