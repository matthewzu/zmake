"""
    zmake.generator
    ~~~~~~~~~~

    Supply ZMake generator functions.

    :copyright: (c) 2023 by Matthew Zu.
    :license: Mozilla Public License, Version 2.0, see LICENSE for more details.
"""

import sys, os, re, argparse, pprint, subprocess, logging, fnmatch, time
import zmake.core
import zmake.kconfig
import zmake.yaml
import zmake.entity

# generator

def _sys_var_create():
    zmake.core.LOGGER.info("creating zmake system variables...")
    zmake.entity.variable("SRC_PATH", zmake.core.SRC_TREE, "source code path")
    zmake.entity.variable("PRJ_PATH", zmake.core.PRJ_DIR, "project path")
    zmake.entity.variable("KCONFIG_CONFIG", zmake.core.PRJ_DIR, "Kconfig makefile output")

def _sys_target_create():
    zmake.core.LOGGER.info("creating zmake system targets...")

    config_cmd = "zmake -m $(SRC_PATH) $(PRJ_PATH)"
    if zmake.core.PRJ_GEN == zmake.core.PRJ_GEN_TYPE_NINJA:
        config_cmd += " -g ninja"

    if zmake.core.PRJ_VERB:
        config_cmd += " -V"

    zmake.entity.target("config",
        desc = "configure project and generate header and mk",
        cmd = config_cmd)

    zmake.entity.target("all", desc = "Build all applications and libraries",
        deps = zmake.entity.library.find_libs() + zmake.entity.application.find_apps())

    zmake.entity.target("clean",
        cmd = "rm -rf $(PRJ_PATH)/objs $(PRJ_PATH)/libs $(PRJ_PATH)/apps",
            desc = "Clean all generated files")

def _parse():
    """Parse YAML configuration file and generate ZMake objects.
    """

    yaml_data = zmake.yaml.data()
    del yaml_data['includes']
    zmake.core.LOGGER.info("parsing YAML...")

    for name, config in yaml_data.items():
        zmake.core.LOGGER.debug("parse YAML object %s:\n%s", name, pprint.pformat(config))
        obj_type = config.get("type", "")
        if obj_type == zmake.entity.ENTITY_TYPE_VAR:
            zmake.entity.variable(name, config.get("val", ""), config.get("desc", ""))
        elif obj_type == zmake.entity.ENTITY_TYPE_LIB:
            if zmake.kconfig.options_find(config.get("opt", "")):
                zmake.entity.library(name, config.get("src", ""), config.get("desc", ""),
                    config.get("hdrdirs", ""), config.get("cflags", ""),
                    config.get("cppflags", ""), config.get("asmflags", ""))
        elif obj_type == zmake.entity.ENTITY_TYPE_APP:
            if zmake.kconfig.options_find(config.get("opt", "")):
                zmake.entity.application(name, config.get("src", []), config.get("desc", ""),
                    config.get("cflags", {}), config.get("cppflags", {}),
                    config.get("asmflags", {}), config.get("linkflags", ""),
                    config.get("libs", []))
        elif obj_type == zmake.entity.ENTITY_TYPE_TGT:
            zmake.entity.target(name, config.get("desc", ""), config.get("cmd", ""),
                config.get("deps", []))
        else:
            zmake.core.LOGGER.warning("invalid object type %s for YAML Object %s", obj_type, name)
            continue

def _make_gen():
    path = os.path.join(zmake.core.PRJ_DIR, "Makefile")
    zmake.core.LOGGER.info("generating %s ...", path)
    fd = open(path, 'w', encoding='utf-8')

    cur_time = time.asctime()
    fd.write("# Generated by %s on %s\n\n" %(zmake.core.ver(), cur_time))

    fd.write("default: all\n")
    fd.write("\n")

    fd.write("# variables\n")
    fd.write("\n")
    fd.flush()

    zmake.entity.variable.all_make_gen(fd)

    fd.write("ifneq ($(V), )\n")
    fd.write("\tVREBOSE_BUILD = $(V)\n")
    fd.write("else\n")
    fd.write("\tVREBOSE_BUILD = 0\n")
    fd.write("endif\n")
    fd.write("\n")

    fd.write("ifeq ($(VREBOSE_BUILD),1)\n")
    fd.write("\tQUIET =\n")
    fd.write("\tQ =\n")
    fd.write("\tVERBOSE = v\n")
    fd.write("else\n")
    fd.write("\tQUIET = quiet\n")
    fd.write("\tQ = @\n")
    fd.write("\tVERBOSE =\n")
    fd.write("endif\n")
    fd.write("\n")
    fd.flush()

    zmake.entity.library.all_make_gen(fd)
    zmake.entity.application.all_make_gen(fd)
    zmake.entity.target.all_make_gen(fd)

def _ninja_gen():
    path = os.path.join(zmake.core.PRJ_DIR, "build.ninja")
    zmake.core.LOGGER.info("generating %s ...", path)
    fd = open(path, 'w', encoding='utf-8')

    cur_time = time.asctime()
    fd.write("# Generated by %s on %s\n" %(zmake.core.ver(), cur_time))
    fd.write("\n")
    fd.flush()

    fd.write("# variables\n")
    fd.write("\n")
    fd.flush()

    zmake.entity.variable.all_ninja_gen(fd)

    fd.write("# common rules\n")
    fd.write("\n")

    fd.write("rule rule_cmd\n")
    fd.write("    command = $CMD\n")
    fd.write("    description = $DESC\n")
    fd.write("\n")

    fd.write("rule rule_mkdir\n")
    fd.write("    command = mkdir -p $out\n")
    fd.write("    description = Creating $out\n")
    fd.write("\n")

    fd.write("rule rule_cc\n")
    fd.write("    depfile = $DEP\n")
    fd.write("    deps = gcc\n")
    fd.write("    command = $CC -MF $DEP -c $in -o $out $FLAGS\n")
    fd.write("    description = '<$MOD>': Compiling $SRC to $OBJ\n")
    fd.write("\n")

    fd.write("rule rule_ar\n")
    fd.write("    command = $AR crs $PRJ_PATH/libs/$LIB $in\n")
    fd.write("    description = '<$MOD>': Packaging\n")
    fd.write("\n")

    fd.write("rule rule_ld\n")
    fd.write("    command = $LD -o $PRJ_PATH/apps/$out $in -L$PRJ_PATH/libs $FLAGS\n")
    fd.write("    description = '<$MOD>': Linking\n")
    fd.write("\n")
    fd.flush()

    zmake.entity.library.all_ninja_gen(fd)
    zmake.entity.application.all_ninja_gen(fd)
    zmake.entity.target.all_ninja_gen(fd)

def generate():
    """Generate build files
    """

    _sys_var_create()
    _parse()
    _sys_target_create()

    if zmake.core.PRJ_GEN == zmake.core.PRJ_GEN_TYPE_MAKE:
        _make_gen()
    else:
        _ninja_gen()