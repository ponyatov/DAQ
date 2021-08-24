import config

import os, sys, re
import datetime as dt

## base object (hyper)graph node = Marvin Minsky's Frame
class Object:
    def __init__(self, V):
        ## type/class tag /required for PLY/
        self.type = self.tag()
        ## scalar value: name, number, string..
        self.value = V
        ## associative array: map = env/namespace = grammar attributes
        self.slot = {}
        ## ordered container: vector = stack = queue = AST subtree
        self.nest = []

    ## Python types wrapper
    def box(self, that):
        if isinstance(that, Object): return that
        if isinstance(that, str): return S(that)
        if that is None: return Nil()
        raise TypeError(['box', type(that), that])

    ## @name text tree dump

    ## `print` callback
    def __repr__(self): return self.dump(test=False)

    ## repeatable print for tests
    def test(self): return self.dump(test=True)

    ## full tree dump
    def dump(self, cycle=[], depth=0, prefix='', test=False):
        # head
        ret = self.pad(depth) + self.head(prefix, test)
        # cycle block
        if not depth: cycle = []
        if self in cycle: return ret + ' _/'
        else: cycle.append(self)
        # slot{}s
        for i in self.keys():
            ret += self[i].dump(cycle, depth + 1, f'{i} = ', test)
        # nest[]ed
        for j, k in enumerate(self):
            ret += k.dump(cycle, depth + 1, f'{j}: ', test)
        # subtree
        return ret

    def pad(self,depth,tab='\t'): return '\n' + tab * depth

    ## single `<T:V>` header
    def head(self, prefix='', test=False):
        gid = '' if test else f' @{id(self):x}'
        return f'{prefix}<{self.tag()}:{self.val()}>{gid}'

    ## `<T:`
    def tag(self): return self.__class__.__name__.lower()
    ## `:V>`
    def val(self): return f'{self.value}'
    
    ## @name operator

    ## `A.keys()`
    def keys(self):
        return sorted(self.slot.keys())

    ## `len(A)`
    def __len__(self):
        return len(self.nest)

    ## `for i in A`
    def __iter__(self):
        return iter(self.nest)

    ## `A[key]`
    def __getitem__(self, key):
        assert isinstance(key, str)
        return self.slot[key]

    ## `A[key] = B`
    def __setitem__(self, key, that):
        assert isinstance(key, str)
        that = self.box(that)
        self.slot[key] = that; return self

    ## `A << B -> A[B.type] = B`
    def __lshift__(self, that):
        that = self.box(that)
        return self.__setitem__(that.tag(), that)

    ## `A >> B -> A[B.value] = B`
    def __rshift__(self, that):
        that = self.box(that)
        return self.__setitem__(that.val(), that)

    ## `A // B -> A.push(B)`
    def __floordiv__(self, that):
        that = self.box(that)
        self.nest.append(that); return self

class Primitive(Object): pass

class S(Primitive):
    def __init__(self,V=None,pfx=None,sfx=None):
        super().__init__(V)
        self.pfx=pfx;self.sfx=sfx
    def gen(self,to,depth=0):
        ret = f'{to.tab*depth}{self.value}\n'
        return ret

class Sec(S):
    def gen(self,to,depth=0):
        ret = ''
        if self.value is not None:
            ret += f'{to.tab*depth}{to.comment} \\ {self.value}\n'
        for i in self: ret += i.gen(to,depth+0)
        if self.value is not None:
            ret += f'{to.tab*depth}{to.comment} / {self.value}\n'
        if self.sfx is not None:
            if self.pfx: ret += f'{to.tab*depth}{self.pfx}\n'
            else: ret += '\n'
        return ret


class IO(Object):
    def __init__(self,V):
        super().__init__(V)
        self.path = V

class Dir(IO):
    def sync(self):
        try: os.mkdir(self.path)
        except FileExistsError: pass
        for i in self: i.sync()
    def __floordiv__(self,F):
        assert isinstance(F,IO)
        F.path = f'{self.path}/{F.path}'
        return super().__floordiv__(F)

class File(IO):
    def __init__(self,V,ext='',tab='\t',comment='#'):
        super().__init__(V+ext)
        self.tab=tab;self.comment=comment
        self.bot = Sec()
    def sync(self):
        with open(self.path,'w') as F:
            for i in self: F.write(i.gen(self))
            F.write(self.bot.gen(self))

class giti(File):
    def __init__(self,V='',ext='.gitignore'):
        super().__init__(V+ext)
        self.bot // '!.gitignore'

class Meta(Object): pass

class Module(Meta):
    def __format__(self,spec):
        assert not spec
        return f'{self.value}'

class mkFile(File):
    def __init__(self,V='Makefile',ext='',tab='\t',comment='#'):
        super().__init__(V,ext,tab,comment)

class Project(Module):
    def __init__(self,V=None):
        if V is None: V = os.getcwd().split('/')[-1]
        super().__init__(V)
        self.d = Dir(f'{self}')
        self.d_dirs()
        self.vs_code()
        self.f_giti()
        self.f_mk()

    def f_mk(self):
        self.mk = mkFile();self.d//self.mk

    def vs_code(self):
        self.vscode = Dir('.vscode');self.d//self.vscode

    def d_dirs(self):
        self.bin = Dir('bin');self.d//self.bin
        self.bin // (giti() // '*')
        #
        self.doc = Dir('doc');self.d//self.doc
        #
        self.lib = Dir('lib');self.d//self.lib
        #
        self.src = Dir('src');self.d//self.src
        #
        self.tmp = Dir('tmp');self.d//self.tmp
    def f_giti(self):
        self.giti = giti();self.d//self.giti
        self.giti \
            // '*~' // '*.swp' // '*.log' // '' \
            // '/docs/' // f'/{self}/' // ''

    def sync(self):
        self.d.sync()

    def __or__(self,mod):
        assert isinstance(mod,Mod)
        return mod.pipe(self)

## Project modifier
class Mod(Module):
    def __init__(self):
        super().__init__('mod')
    def pipe(self,p):
        self.f_giti(p)
        return p
    def f_giti(self,p):
        pass

class pyFile(File):
    def __init__(self,V,ext='.py',tab=' '*4,comment='#'):
        super().__init__(V,ext,tab,comment)

class Python(Mod):
    def pipe(self,p):
        p = super().pipe(p)
        self.f_src(p)
        return p
    def f_src(self,p):
        p.py = pyFile(f'{p}');p.d//p.py
        p.test = pyFile(f'test_{p}');p.d//p.test
        p.config = pyFile('config');p.d//p.config
    def f_giti(self,p):
        p.giti // (Sec('py',sfx='')
            // '/.cache/' // '/__pycache__/' // '*.pyc')

class Rust(Mod):
    def pipe(self,p):
        p = super().pipe(p)
        return p

prj = Project() | Python() | Rust()
prj.sync()