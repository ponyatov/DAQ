import pytest
from metaL import *

hello = Object('Hello')
world = Object('World')

def test_hello():
    assert hello.test() == '\n<object:Hello>'

def test_world():
    assert world.test() == '\n<object:World>'
    assert (hello // world).test() == \
        '\n<object:Hello>' +\
        '\n\t0: <object:World>'

def test_shifts():
    left = Object('left')
    right = Object('right')
    assert (hello << left >> right).test() == \
        '\n<object:Hello>' +\
        '\n\tobject = <object:left>' +\
        '\n\tright = <object:right>' +\
        '\n\t0: <object:World>'
