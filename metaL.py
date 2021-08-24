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

    def ins(self, idx, that):
        assert isinstance(idx, int)
        that = self.box(that)
        self.nest.insert(idx, that); return self

    def replace(self, idx, that):
        assert isinstance(idx, int)
        that = self.box(that)
        self.nest[idx] = that; return self

class Primitive(Object): pass

class S(Primitive):
    def __init__(self,V=None,end=None,pfx=None,sfx=None):
        super().__init__(V)
        self.end=end
        self.pfx=pfx;self.sfx=sfx
    def gen(self,to,depth=0):
        ret = ''
        if self.pfx is not None:
            if self.pfx: ret += f'{to.tab*depth}{self.pfx}\n'
            else: ret += '\n'
        if self.value is not None:
            ret += f'{to.tab*depth}{self.value}\n'
        for i in self: ret += i.gen(to,depth+1)
        if self.end is not None:
            ret += f'{to.tab*depth}{self.end}\n'
        if self.sfx is not None:
            if self.sfx: ret += f'{to.tab*depth}{self.sfx}\n'
            else: ret += '\n'
        return ret

class Sec(S):
    def gen(self,to,depth=0):
        ret = ''
        if self:
            if self.pfx is not None:
                if self.pfx: ret += f'{to.tab*depth}{self.pfx}\n'
                else: ret += '\n'
            if self.value is not None:
                ret += f'{to.tab*depth}{to.comment} \\ {self.value}\n'
            for i in self: ret += i.gen(to,depth+0)
            if self.value is not None:
                ret += f'{to.tab*depth}{to.comment} / {self.value}\n'
            if self.sfx is not None:
                if self.sfx: ret += f'{to.tab*depth}{self.sfx}\n'
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
        self.top = Sec(); self.bot = Sec()
    def sync(self):
        with open(self.path,'w') as F:
            F.write(self.top.gen(self))
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

class jsonFile(File):
    def __init__(self,V,ext='.json',tab=' '*2,comment='//'):
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
        self.mk_var()
        self.mk_dir()
        self.mk_tool()
        self.mk_src()
        self.mk_cfg()
        self.mk_all()
        self.mk_rule()
        self.mk_doc()
        self.mk_install()
        self.mk_merge()

    def mk_var(self):
        self.mk.var_ = Sec('var');self.mk//self.mk.var_
        self.mk.var_ \
            // '# detect module/project name by current directory' \
            // f'{"MODULE":<7} = $(notdir $(CURDIR))' \
            // '# detect OS name (only Linux/MinGW)' \
            // f'{"OS":<7} = $(shell uname -s)' \
            // '# current date in the `ddmmyy` format' \
            // f'{"NOW":<7} = $(shell date +%d%m%y)' \
            // '# release hash: four hex digits (for snapshots)' \
            // f'{"REL":<7} = $(shell git rev-parse --short=4 HEAD)' \
            // '# current git branch' \
            // f'{"BRANCH":<7} = $(shell git rev-parse --abbrev-ref HEAD)' \
            // '# number of CPU cores (for parallel builds)' \
            // f'{"CORES":<7} = $(shell grep processor /proc/cpuinfo| wc -l)'

    def mk_dir(self):
        self.mk.dir_ = Sec('dir',pfx='');self.mk//self.mk.dir_
        self.mk.dir_ \
            // '# current (project) directory' \
            // f'{"CWD":<7} = $(CURDIR)' \
            // '# compiled/executable files (target dir)' \
            // f'{"BIN":<7} = $(CWD)/bin' \
            // '# documentation & external manuals download' \
            // f'{"DOC":<7} = $(CWD)/doc' \
            // '# libraries / scripts' \
            // f'{"LIB":<7} = $(CWD)/lib' \
            // '# source code (not for all languages, Rust/C/Java included)' \
            // f'{"SRC":<7} = $(CWD)/src' \
            // '# temporary/flags/generated files' \
            // f'{"TMP":<7} = $(CWD)/tmp'
    def mk_tool(self):
        self.mk.tool = Sec('tool',pfx='');self.mk//self.mk.tool
        self.mk.tool \
            // '# http/ftp download' \
            // f'{"CURL":<7} = curl -L -o'
    def mk_src(self):
        self.mk.var_ = Sec('var',pfx='');self.mk//self.mk.var_
    def mk_cfg(self):
        self.mk.cfg_ = Sec('cfg',pfx='');self.mk//self.mk.cfg_
    def mk_all(self):
        self.mk.all_ = Sec('all',pfx='');self.mk//self.mk.all_
    def mk_rule(self):
        self.mk.rule_ = Sec('rule',pfx='');self.mk//self.mk.rule_
    def mk_doc(self):
        self.mk.doc_ = Sec('doc',pfx='');self.mk//self.mk.doc_
    def mk_install(self):
        self.mk.install_ = Sec('install',pfx='');self.mk//self.mk.install_
    def mk_merge(self):
        self.mk.merge_ = Sec('merge',pfx='');self.mk//self.mk.merge_

    def vs_code(self):
        self.vscode = Dir('.vscode');self.d//self.vscode
        self.vs_settings()
        self.vs_tasks()
        self.vs_exts()

    def vs_settings(self):
        self.vscode.settings_ = jsonFile('settings')
        self.vscode//self.vscode.settings_
        self.vscode.settings = S('{','}')
        self.vscode.settings_//self.vscode.settings
        #
        self.vscode.multi = S('"multiCommand.commands": [','],')
        #
        self.vscode.files = (Sec('files',pfx=''))
        #
        self.vscode.exclude = Sec() // '"**/docs/**":true,'
        self.vscode.files \
            //(S('"files.exclude": {','},') \
                //self.vscode.exclude)
        #
        self.vscode.watcher = Sec();self.vscode.files//self.vscode.watcher
        self.vscode.files \
            //(S('"files.watcherExclude": {','},') \
                //self.vscode.watcher)
        #
        self.vscode.assoc = Sec();self.vscode.files//self.vscode.assoc
        self.vscode.files \
            //(S('"files.associations": {','},') \
                //self.vscode.assoc)
        #
        self.vscode.editor = (Sec('editor',pfx='')
            // '"editor.tabSize": 4,' \
            // '"editor.rulers": [80],' \
            // '"workbench.tree.indent": 32,')
        #
        self.vscode.browser = S('"browser-preview.startUrl": "127.0.0.1:12345/"',pfx='')
        #
        self.vscode.settings \
            // (Sec('multi')//self.vscode.multi) \
            // self.vscode.files \
            // self.vscode.editor \
            // self.vscode.browser

    def vs_tasks(self):
        self.vscode.tasks = jsonFile('tasks');self.vscode//self.vscode.tasks

    def vs_exts(self):
        self.vscode.exts = jsonFile('extensions');self.vscode//self.vscode.exts
        self.vscode.ext = (Sec()
		// '"ryuta46.multi-command",' \
		// '"stkb.rewrap",' \
		// '"tabnine.tabnine-vscode",' \
		// '// "auchenberg.vscode-browser-preview",' \
		// '// "ms-azuretools.vscode-docker",')
        self.vscode.exts \
            // (S('{','}') \
                // (S('"recommendations": [',']') \
                    //self.vscode.ext))

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
        self.f_mk(p)
        self.vs_code(p)
        return p
    def f_giti(self,p): pass
    def f_mk(self,p):pass
    def vs_code(self,p):pass

class pyFile(File):
    def __init__(self,V,ext='.py',tab=' '*4,comment='#'):
        super().__init__(V,ext,tab,comment)
        self.top // 'import config' // ''

class Python(Mod):
    def pipe(self,p):
        p = super().pipe(p)
        self.f_src(p)
        return p
    def f_src(self,p):
        p.config = pyFile('config');p.d//p.config
        p.config.top = Sec()
        self.p_py(p)
        self.p_test(p)

    def p_py(self,p):
        p.py = pyFile(f'{p}');p.d//p.py
        p.py // self.p_mods()

    def p_test(self,p):
        p.test = pyFile(f'test_{p}');p.d//p.test
        p.test \
            // 'import pytest' // f'from {p} import *' // ''
        p.test \
            // 'def test_any(): assert True'

    def f_giti(self,p):
        p.giti // (Sec('py',sfx='')
            // '/.cache/' // '/__pycache__/' // '*.pyc')

    PEP8 = '--ignore=E26,E302,E305,E401,E402,E701,E702'
    def vs_code(self,p):
        p.vscode.ext // '"tht13.python",'
        p.vscode.exclude \
            // '"*.pyc":true, "pyvenv.cfg":true,' \
            // '"**/.cache/**":true, "**/__pycache__/**":true,'
        p.vscode.settings.ins(0,(Sec('py',sfx='')
            // '"python.pythonPath"              : "./bin/python3",'
            // '"python.formatting.provider"     : "autopep8",'
            // '"python.formatting.autopep8Path" : "./bin/autopep8",'
            // f'"python.formatting.autopep8Args" : ["{Python.PEP8}"],'
        ))

    def p_mods(self):
        return (Sec() \
            // 'import os, sys, re'
            // 'import datetime as dt')

    def f_mk(self,p):
        p.mk.tool \
            // f'{"PY":<7} = $(BIN)/python3' \
            // f'{"PIP":<7} = $(BIN)/pip3' \
            // f'{"PYT":<7} = $(BIN)/pytest' \
            // f'{"PEP":<7} = $(BIN)/autopep8'

class Rust(Mod):
    def pipe(self,p):
        p = super().pipe(p)
        return p

class metaL(Python):
    def pipe(self,p):
        p = super().pipe(p)
        self.p_metal(p)
        return p
    def p_metal(self,p):
        p.metal = pyFile('metaL');p.d//p.metal
        p.metal // self.p_mods()
    def vs_code(self,p):
        p.vscode.exclude // f'"**/{p}/**":true,'
        super().vs_code(p)

class Java(Mod):
    pass

# from metaL import *
prj = Project() | metaL() | Rust()
prj.sync()
