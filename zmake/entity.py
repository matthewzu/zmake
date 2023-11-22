"""
    zmake.entity
    ~~~~~~~~~~

    Supply zmake entity functions.

    :copyright: (c) 2023 by Matthew Zu.
    :license: Mozilla Public License, Version 2.0, see LICENSE for more details.
"""

import os, re, pprint, logging, fnmatch
import zmake.core

# source file types

_ZMAKE_SRC_TYPE_C   = "c"
_ZMAKE_SRC_TYPE_CPP = "cpp"
_ZMAKE_SRC_TYPE_ASM = "asm"
_ZMAKE_SRC_TYPES    = {"c": "*.c", "cpp": "*.cpp", "asm": "*.[sS]"}

# ZMake entity types

ENTITY_TYPE_VAR = "var"
ENTITY_TYPE_TGT = "target"
ENTITY_TYPE_APP = "app"
ENTITY_TYPE_LIB = "lib"
ENTITY_TYPE_OBJ = "obj"
ENTITY_TYPES = ("var", "target", "app", "lib", "obj")

# ZMake Entity classes

class entity(object):
    """ZMake Entity:
        name: string, the name of the entity, must be unique for all entities
        type: string, the type of the entity
        desc: string, optional, the description of the entity
    """

    def __new__(cls, name, type, desc= ""):
        if not isinstance(name, str):
            raise zmake.core.exception("'name' MUST be str for ZMake Entity" %str(name))

        if type not in ENTITY_TYPES:
            raise zmake.core.exception("invalid type for ZMake Entity(%s)" %(str(type), name))

        if not isinstance(desc, str):
            raise zmake.core.exception("'desc' MUST be str for ZMake Entity(%s)" %(str(name), name))

        return super(entity, cls).__new__(cls)

    def __str__(self):
        return '[ZMake Entity: %s Type: %s description: %s]' %(self.name, self.type, self.desc)

class variable(entity):
    """ZMake variable
        name: string, the name of the entity
        desc: string, optional, the description of the entity
        val:  string that could include references to other variable'
        that have beed defined, such as '$(var_name)', or any value
    """

    _vars = {}

    def __new__(cls, name, val, desc = ""):
        if val == None:
            raise zmake.core.exception("invalid value for ZMake variable %s" %name)
        else:
            return super(variable, cls).__new__(cls, name, ENTITY_TYPE_VAR, desc)

    def __init__(self, name, val, desc = ""):
        self.name       = name
        self.desc       = desc

        if not isinstance(val, str):
            self.val    = val
        else:
            self.val    = variable.dereference(val)

        zmake.core.LOGGER.debug("create ZMake variable %s", name)
        zmake.core.LOGGER.debug("\tdesc = %s val = %s", desc, str(self.val))
        variable._vars.setdefault(name, self)

    @staticmethod
    def _find(name):
        """
        internal function, find ZMake variable object by name
            name:   string, name of ZMake variable object
            return: ZMake variable object, or None if not found
        """

        if name in variable._vars:
            return variable._vars[name]
        else:
            return None

    @staticmethod
    def _is_reference(var_expr):
        """
        internal functions, check whether a string is a reference
        to ZMake variable object
            var_expr:   string
            return:     ZMake variable name,
            or None if not a reference string to ZMake variable object
        """

        reg_var = re.compile('\$\((\S*)\)')
        temp = reg_var.search(var_expr)
        if temp != None:
            var_name = temp.group(1)
            return var_name
        else:
            return None

    @staticmethod
    def dereference(expr: str):
        """
        dereference a string including some reference strings to ZMake
        variable objects, and replace reference strings to value of ZMake
        variable object.
            expr:   string, a string including reference strings to ZMake
            variable objects
            return: string, in which reference strings have been replaced with
                value of ZMake variable object
        """

        pattern = r'(\$\(.*?\))'
        fragments = re.split(pattern, expr)
        for idx in range(len(fragments)):
            var_name = variable._is_reference(fragments[idx])
            if var_name == None:
                continue    # not a reference string, so need to replace

            var = variable._find(var_name)
            if var == None:
                raise zmake.core.exception("%s could NOT be referenced before defined" %var_name)
            else:
                fragments[idx]  = var.val

        return ''.join(fragments)

    @staticmethod
    def ninja_reference_format(expr: str):
        return re.sub(r"\(([^()]+)\)", r"\1", expr)

    @staticmethod
    def all_make_gen(fd):
        """
        generate makefile segments for all ZMake variables and write fo file
        """
        for key, val in variable._vars.items():
            zmake.core.LOGGER.debug("generate variable %s", key)
            fd.write("%s\t= %s\n" %(key, str(val.val)))

        fd.write("\n")
        fd.flush()

    @staticmethod
    def all_ninja_gen(fd):
        """
        generate ninja segments for all ZMake variables and write fo file
        """
        for key, val in variable._vars.items():
            zmake.core.LOGGER.debug("generate variable %s", key)
            fd.write("%s = %s\n" %(key, str(val.val)))

        fd.write("\n")
        fd.flush()

class _object(entity):
    """ZMake Object
        name:   string, full source path including file name('*.c', '*.cpp', '*.s' or '*.S')
        type:   string, one of `c`, `cpp` and `asm`
        desc:   string, ignored
        flags:  string, compiler flags
    """

    def __new__(cls, name, desc = "", flags = '', libname = ''):
            return super(_object, cls).__new__(cls, name, ENTITY_TYPE_OBJ, desc)

    def __init__(self, name, desc = "", flags = '', libname = ''):
        self.name   = name
        self.flags  = '-I$(PRJ_PATH)/config ' + flags
        zmake.core.LOGGER.debug("create ZMake Object %s", name)

        self._obj_dir   = os.path.join('$(PRJ_PATH)/objs', libname)
        self._obj_name  = os.path.join(self._obj_dir,
            os.path.splitext(os.path.basename(name))[0] + '.o')
        self._dep_name  = os.path.splitext(self._obj_name)[0] + '.d'

    def make_gen(self, fd, mod_name, added_flags):
        """
        generate makefile segments for specified ZMake objects with module name and write fo file
        """

        zmake.core.LOGGER.debug("generate object %s", self.name)
        fd.write("%s: %s\n" %(self._obj_name, self.name))
        fd.write("\t$(Q)$(if $(QUIET), echo '<%s>': Compiling %s to %s)\n"
                %(mod_name, os.path.basename(self.name), (os.path.basename(self._obj_name))))
        fd.write("\t$(Q)mkdir -p$(VERBOSE) %s\n" %self._obj_dir)
        fd.write("\t$(Q)$(CC) %s %s -c $< -o $@\n" %(added_flags, self.flags))
        fd.write("\n")

    def ninja_gen(self, fd, mod_name, added_flags):
        """
        generate ninja segments for specified ZMake objects with module name and write fo file
        """

        self.name       = variable.ninja_reference_format(self.name)
        self.flags      = variable.ninja_reference_format(self.flags)
        self._obj_dir   = variable.ninja_reference_format(self._obj_dir)
        self._obj_name  = variable.ninja_reference_format(self._obj_name)
        self._dep_name  = variable.ninja_reference_format(self._dep_name)

        zmake.core.LOGGER.debug("generate object %s", self.name)
        fd.write("build %s: rule_mkdir\n" %self._obj_dir)
        fd.write("build %s: rule_cc %s | %s\n" %(self._obj_name, self.name, self._obj_dir))
        fd.write("    DEP = %s\n" %self._dep_name)
        fd.write("    FLAGS = %s %s\n" %(added_flags, self.flags))
        fd.write("    MOD = %s\n" %mod_name)
        fd.write("    SRC = %s\n" %os.path.basename(self.name))
        fd.write("    OBJ = %s\n" %os.path.basename(self._obj_name))
        fd.write("\n")

class _module(entity):
    """ZMake module - application/library
        name:       string, the name of the entity
        type:       string, the content is "var" and need not be specified\n
        src:                    # list, source files or directories
            - $(ZMake variable name)/xxx/xxx.c
            - $(ZMake variable name)/xxx  # for directory, all source
                                            files in it will be involved\n
        desc:       string, optional, the description of the entity\n
        cflags:                 # optional, additional compiler flags for C files\n
            all:      xxx       # string, compiler flags for all C files
            xxx.c:    xxx       # string, compiler flags for xxx.c
        cppflags:               # optional, additional compiler flags for cpp files
            all:      xxx       # string, compiler flags for all CPP files
            xxx.cpp:  xxx       # string, compiler flags for xxx.cpp
        asmflags:   xxx         # optional, additional compiler flags for assembly files
            all:      xxx       # string, compiler flags for all assembly files
            xxx.s:    xxx       # string, compiler flags for xxx.s
            xxx.S:    xxx       # string, compiler flags for xxx.S
    """

    def __new__(cls, name, type, src, desc = "", cflags = {}, cppflags = {}, asmflags = {}):
        if type != ENTITY_TYPE_APP and type != ENTITY_TYPE_LIB:
            raise zmake.core.exception("invalid type %s for ZMake module(%s)" %(type, name))

        if not isinstance(src, list):
            raise zmake.core.exception("'src' (%s) MUST be list for ZMake module(%s)" %(str(src), name))

        return super(_module, cls).__new__(cls, name, type, desc)

    def __init__(self, name, type, src, desc = "", cflags = {}, cppflags = {}, asmflags = {}):
        self.name   = name
        self.desc   = desc
        self.src    = {}

        for path in src:
            final_path = variable.dereference(path)
            srcs = _module.src_find(final_path)
            for file, type in srcs.items():
                file_name = os.path.basename(file)
                file_flags = _module._find_flags(file_name, type,
                    cflags, cppflags, asmflags)

                self.src.setdefault(file_name,
                    _object(file.replace(zmake.core.SRC_TREE, "$(SRC_PATH)"), type,
                        flags = file_flags, libname = name))

    def objs(self):
        """
        find all objects of this module and return a string includes all objects
        """
        found = []
        for obj in self.src.values():
            found.append(obj._obj_name)

        return ' '.join(found)

    def make_gen(self, fd, libname, added_flags):
        """
        generate makefile segments for all objects of this module and write fo file
        """

        deps = ""
        for key, obj in self.src.items():
            deps += " " + obj._dep_name
            obj.make_gen(fd, libname, added_flags)

        fd.write("-include %s\n\n" %deps)
        fd.flush()

    def ninja_gen(self, fd, libname, added_flags):
        """
        generate ninja segments for all objects of this module and write fo file
        """
        for key, obj in self.src.items():
            obj.ninja_gen(fd, libname, added_flags)

        fd.flush()

    @staticmethod
    def src_find(path: str):
        """
        find source files from specified path
            1) if path is a file and exists, then return a list including given path\n
            2) if path is a directory and exists, then search and return a list
            including paths of all source file('*.c', '*.cpp', '*.s' or '*.S')\n
            3) otherwise return {}\n
        """
        #

        if not os.path.exists(path):
            zmake.core.LOGGER.warning("invalid path: %s", path)
            return {}

        srcs = {}
        if os.path.isfile(path):
            for type, pattern in _ZMAKE_SRC_TYPES.items():
                if fnmatch.fnmatch(path, pattern):
                    srcs.setdefault(os.path.abspath(path), type)
                    return srcs

        if os.path.isdir(path):
            for base, subdirs, files in os.walk(path):
                for type, pattern in _ZMAKE_SRC_TYPES.items():
                    matches = fnmatch.filter(files, pattern)
                    for src in matches:
                        srcs.setdefault(os.path.join(base, src), type)

        return srcs

    @staticmethod
    def _find_flags(file_name, type, cflags, cppflags, asmflags) -> str:
        """
        find flags for specified file and type
            return: string, compiler flags
        """
        if type == _ZMAKE_SRC_TYPE_C:
            flags = cflags
        elif type == _ZMAKE_SRC_TYPE_CPP:
            flags = cppflags
        elif type == _ZMAKE_SRC_TYPE_ASM:
            flags = asmflags
        else:
            raise zmake.core.exception("invalid source type %s" %type)

        if not isinstance(flags, dict):
            if isinstance(flags, list):
                if len(flags) == 1 and isinstance(flags[0], dict):
                    flags = flags[0]
                else:
                    raise zmake.core.exception("compiler flags(%s) MUST be dict" %str(flags))
            else:
                raise zmake.core.exception("compiler flags(%s) MUST be dict" %str(flags))

        if not isinstance(flags.get("all", ""), str):
            raise zmake.core.exception("compiler flags(%s) for 'all' MUST be string" %str(flags))

        if not isinstance(flags.get(file_name, ""), str):
            raise zmake.core.exception("compiler flags(%s) for '%s' MUST be string" %(str(flags), file_name))

        return flags.get("all", "") + " " + flags.get(file_name, "")

class library(_module):
    """ZMake library
        name:       string, the name of the entity
        src:                    # list, source files or directories:
            - $(ZMake variable name)/xxx/xxx.c
            - $(ZMake variable name)/xxx  # for directory, all source files in it will be involved
        desc:       string, optional, the description of the entity
        hdrdirs:                # string, optional, list, public header file directories
            - $(ZMake variable name)/xxx
        cflags:                 # optional, additional compiler flags for C files
            all:      xxx       # string, compiler flags for all C files
            xxx.c:    xxx       # string, compiler flags for xxx.c
        cppflags:               # optional, additional compiler flags for cpp files
            all:      xxx       # string, compiler flags for all CPP files
            xxx.cpp:  xxx       # string, compiler flags for xxx.cpp
        asmflags:   xxx         # optional, additional compiler flags for assembly files
            all:      xxx       # string, compiler flags for all assembly files
            xxx.s:    xxx       # string, compiler flags for xxx.s
            xxx.S:    xxx       # string, compiler flags for xxx.S
    """

    _libs = {}

    def __new__(cls, name, src, desc = "", hdrdirs = [], cflags = {}, cppflags = {}, asmflags = {}):
        if not isinstance(hdrdirs, list):
            raise zmake.core.exception("'hdrdirs' MUST be list for ZMake library(%s)" %(str(hdrdirs), name))

        return super(library, cls).__new__(cls,
            name, ENTITY_TYPE_LIB, src, desc, cflags, cppflags, asmflags)

    def __init__(self, name, src, desc = "", hdrdirs = [], cflags = {}, cppflags = {}, asmflags = {}):
        zmake.core.LOGGER.debug("create ZMake library %s", name)
        super(library, self).__init__(name, ENTITY_TYPE_LIB,
            src, desc, cflags, cppflags, asmflags)

        zmake.core.LOGGER.debug("ZMake library %s details:", name)
        zmake.core.LOGGER.debug("\tsrc(final) = %s", pprint.pformat(self.src))

        self.hdrdirs = []
        for dir in hdrdirs:
            self.hdrdirs.append(dir)
        self._lib_name = 'lib' + name + '.a'

        zmake.core.LOGGER.debug("\thdrdirs(final) = %s", pprint.pformat(self.hdrdirs))
        zmake.core.LOGGER.debug("\t_lib_name = %s", self._lib_name)
        library._libs.setdefault(name, self)

    @staticmethod
    def find(name):
        """
        internal function, find ZMake library object by name
            name:   string, name of ZMake library object
            return: ZMake library object, or None if not found
        """

        return library._libs.get(name, None)

    @staticmethod
    def find_libs() -> []:
        """
        find all libraries
        """
        return list(library._libs.keys())

    @staticmethod
    def all_make_gen(fd):
        """
        generate makefile segments for all libraries and write fo file
        """
        fd.write("# libraries\n\n")

        for name, lib in library._libs.items():
            zmake.core.LOGGER.debug("generate library %s", name)
            fd.write("# %s\n\n" %name)
            lib.make_gen(fd, name, "")

            fd.write("%s: %s\n" %(name, lib.objs()))
            fd.write("\t$(Q)$(if $(QUIET), echo '<%s>': Packaging)\n" %name)
            fd.write("\t$(Q)mkdir -p$(VERBOSE) $(PRJ_PATH)/libs\n")
            fd.write("\t$(Q)$(AR) crs$(VERBOSE) $(PRJ_PATH)/libs/%s $^\n" %lib._lib_name)
            fd.write("\n")
            fd.flush()

    @staticmethod
    def all_ninja_gen(fd):
        """
        generate ninja segments for all libraries and write fo file
        """

        fd.write("# libraries\n\n")
        fd.write("build $PRJ_PATH/libs: rule_mkdir\n")
        fd.write("\n")

        for name, lib in library._libs.items():
            zmake.core.LOGGER.debug("generate library %s", name)
            fd.write("# %s\n\n" %name)
            lib.ninja_gen(fd, name, "")

            fd.write("build %s: rule_ar %s | $PRJ_PATH/libs\n" %(name, lib.objs()))
            fd.write("    LIB = %s\n" %lib._lib_name)
            fd.write("    MOD = %s\n" %name)
            fd.write("\n")
            fd.flush()

class application(_module):
    """ZMake application
        name:       string, the name of the entity\n
        src:                    # list, source files or directories:
            - $(ZMake variable name)/xxx/xxx.c
            - $(ZMake variable name)/xxx  # for directory, all source
                                            files in it will be involved\n
        desc:       string, optional, the description of the entity
        cflags:                 # optional, additional compiler flags for C files
            all:      xxx       # string, compiler flags for all C files
            xxx.c:    xxx       # string, compiler flags for xxx.c
        cppflags:               # optional, additional compiler flags for cpp files
            all:      xxx       # string, compiler flags for all CPP files
            xxx.cpp:  xxx       # string, compiler flags for xxx.cpp
        asmflags:               # optional, additional compiler flags for assembly files
            all:      xxx       # string, compiler flags for all assembly files
            xxx.s:    xxx       # string, compiler flags for xxx.s
            xxx.S:    xxx       # string, compiler flags for xxx.S
        linkflags:    xxx       # string, optional, additional linker flags
        libs:       xxx         # list, optional, libraries depended:
            - xxx
    """

    _apps = {}
    def __new__(cls, name, src, desc = "", cflags = {}, cppflags = {}, asmflags = {}, linkflags = '', libs = []):
        if not isinstance(linkflags, str):
            raise zmake.core.exception("'linkflags' MUST be string for ZMake application(%s)" %(str(linkflags), name))

        if not isinstance(libs, list):
            raise zmake.core.exception("'linkflags' MUST be string for ZMake application(%s)" %(str(linkflags), name))

        return super(application, cls).__new__(cls,
            name, ENTITY_TYPE_APP, src, desc, cflags, cppflags, asmflags)

    def __init__(self, name, src, desc = "", cflags = {}, cppflags = {}, asmflags = {}, linkflags = '', libs = []):
        zmake.core.LOGGER.debug("create ZMake application %s", name)
        super(application, self).__init__(name, ENTITY_TYPE_APP, src, desc, cflags, cppflags, asmflags)
        self.linkflags  = linkflags
        self._lib_dep   = ""
        self._lib_ld    = ""
        self._lib_hdrs  = ""
        zmake.core.LOGGER.debug("ZMake application %s details:", name)
        zmake.core.LOGGER.debug("\tsrc(final) = %s", pprint.pformat(self.src))

        for libname in libs:
            lib = library.find(libname)
            if lib == None:
                zmake.core.LOGGER.warning("invalid library(%s) for ZMake application(%s)", str(libname), name)
            else:
                self._lib_dep += " " + libname
                self._lib_ld  += " -l" + libname
                for libhdr in lib.hdrdirs:
                    self._lib_hdrs += " -I" + libhdr

        zmake.core.LOGGER.debug("\t_lib_dep = %s", self._lib_dep)
        zmake.core.LOGGER.debug("\t_lib_ld = %s", self._lib_ld)
        zmake.core.LOGGER.debug("\t_lib_hdrs = %s", self._lib_hdrs)
        application._apps.setdefault(name, self)

    @staticmethod
    def find_apps() -> []:
        """
        find all applications
        """
        return list(application._apps.keys())

    @staticmethod
    def all_make_gen(fd):
        """
        generate makefile segments for all applications and write fo file
        """
        fd.write("# applications\n\n")

        for name, app in application._apps.items():

            zmake.core.LOGGER.debug("generate application %s", name)
            fd.write("# %s\n\n" %name)
            app.make_gen(fd, name, app._lib_hdrs)

            objs = app.objs()
            fd.write("%s: %s %s\n" %(name, objs, app._lib_dep))
            fd.write("\t$(Q)$(if $(QUIET), echo '<%s>': Linking)\n" %name)
            fd.write("\t$(Q)mkdir -p$(VERBOSE) $(PRJ_PATH)/apps\n")
            fd.write("\t$(Q)$(LD) -o $(PRJ_PATH)/apps/$@ %s %s -L$(PRJ_PATH)/libs %s\n"
                %(objs, app.linkflags, app._lib_ld))
            fd.write("\n")
            fd.flush()

    @staticmethod
    def all_ninja_gen(fd):
        """
        generate ninja segments for all applications and write fo file
        """
        fd.write("# applications\n\n")
        fd.write("build $PRJ_PATH/apps: rule_mkdir\n")
        fd.write("\n")

        for name, app in application._apps.items():
            zmake.core.LOGGER.debug("generate application %s", name)
            fd.write("# %s\n\n" %name)
            app.ninja_gen(fd, name, variable.ninja_reference_format(app._lib_hdrs))

            fd.write("build %s: rule_ld %s | $PRJ_PATH/apps %s\n"
                %(name, app.objs(), app._lib_dep))
            fd.write("    FLAGS = %s %s\n" %(app.linkflags, app._lib_ld))
            fd.write("    MOD = %s\n" %name)
            fd.write("\n")
            fd.flush()

class target(entity):
    """ZMake target
        name: string, the name of the entity
        desc: string, optional, the description of the entity
        cmd:  string, optional, commands that need be executed with description
        deps: list, optional, modules depended
            - xxx

        Note that 'cmd' and 'deps' MUST NOT be absent at the same time.
    """

    _targets = {}

    def __new__(cls, name, desc = "", cmd = "", deps = []):
        if not isinstance(cmd, str):
            raise zmake.core.exception("'cmd' MUST be string for ZMake target(%s)" %(str(cmd), name))

        if not isinstance(deps, list):
            raise zmake.core.exception("'deps' MUST be list for ZMake target(%s)" %(str(deps), name))

        if cmd == "" and deps == []:
            raise zmake.core.exception("'cmd' and 'deps' MUST NOT be absent at the same time for ZMake target(%s)" %name)

        return super(target, cls).__new__(cls, name, ENTITY_TYPE_TGT, desc)

    def __init__(self, name, desc = "", cmd = "", deps = []):
        self.name   = name
        self.desc   = desc
        self.cmd    = cmd
        self.deps   = deps
        zmake.core.LOGGER.debug("create ZMake target %s\n\tdesc = %s\n\tcmd = %s\n\tdeps = %s",
            name, desc, pprint.pformat(cmd), pprint.pformat(deps))
        target._targets.setdefault(name, self)

    def make_gen(self, fd):
        """
        generate makefile segments for specified target and write fo file
        """
        if self.deps == []:
            fd.write(".PHONY: %s\n" %self.name)
            fd.write("%s:\n" %self.name)
        else:
            fd.write("%s: %s\n" %(self.name, ' '.join(self.deps)))

        if self.desc != "":
            fd.write("\t@echo %s\n" %self.desc)

        if self.cmd != "":
            fd.write("\t$(Q)%s\n" %self.cmd)

        fd.write("\n")

    def ninja_gen(self, fd):
        """
        generate ninja segments for specified target and write fo file
        """
        if self.cmd == "":
            fd.write("build %s: phony %s\n" %(self.name, ' '.join(self.deps)))
        else:
            fd.write("build cmd_%s: rule_cmd\n" %self.name)
            fd.write("    pool = console\n")
            fd.write("    CMD = %s\n" %variable.ninja_reference_format(self.cmd))

        if self.desc != "":
            fd.write("    DESC = %s\n" %self.desc)

        if self.cmd != "":
            fd.write("build %s: phony cmd_%s\n" %(self.name, self.name))

        fd.write("\n")

    @staticmethod
    def find_targets() -> []:
        """
        find all targets
        """
        return list(target._targets.keys())

    @staticmethod
    def all_make_gen(fd):
        """
        generate makefile segments for all targets and write fo file
        """
        fd.write("# targets\n\n")

        for name, tgt in target._targets.items():
            fd.write("# %s\n\n" %name)
            tgt.make_gen(fd)
            fd.flush()

    @staticmethod
    def all_ninja_gen(fd):
        """
        generate ninja segments for all targets and write fo file
        """
        fd.write("# targets\n\n")

        for name, tgt in target._targets.items():
            fd.write("# %s\n\n" %name)
            tgt.ninja_gen(fd)

        fd.write("default all\n\n")
        fd.flush()

