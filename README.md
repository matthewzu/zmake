# ZMake - A Make/ninja-build file generator from Kconfig/YAML

- [ZMake - A Make/ninja-build file generator from Kconfig/YAML](#zmake---a-makeninja-build-file-generator-from-kconfigyaml)
  - [1. Overview](#1-overview)
  - [2. How to intsall](#2-how-to-intsall)
  - [3. How to use](#3-how-to-use)
  - [4. YAML Configuration](#4-yaml-configuration)
  - [5. How to add one module](#5-how-to-add-one-module)
  - [6. TODO](#6-todo)

## 1. Overview

This is a Make/ninja-build file generator from Kconfig/YAML config files for the modularized softwares. It makes use of `Make`, `Ninja-build` and `Kconfiglib`. For `Kconfiglib`, more details could be found at [github.com/ulfalizer/Kconfiglib](https://github.com/ulfalizer/Kconfiglib).

The following features are supplied:

1. Project are configured by **YAML file**;
2. Tools and basic options for **CC/AR/LD** could be specified;
3. Multiple applications and libraries are supported;
4. Multiple level modules are supported;
5. Each module has its own public and/or private header files, source files(C/C++/assembly), **Kconfig scripts** and **YAML configuration file**;
6. All the files that belongs to one module are placed in one directory;
7. The following attribute of the libraries could be specified:

   - Name;
   - corresponding Kconfig option that are used to enable/disable this module;
   - Source files;
   - Public header directory;
   - Compiler flags;

8. The following attribute of the applications could be specified:

   - Name;
   - corresponding Kconfig option that are used to enable/disable this module;
   - Source files;
   - Compiler flags;
   - linker flags;
   - libraries depended that are used to include corresponding hedear files and libraries for this module;

9. The following attribute of the source files could be specified:

    - Compiler flags;

10. The `YAML` root file is by default `top.yml` in the root directory, or can be specified with `-y "YAML file"`;
11. The `Kconfig` file root is by default `Kconfig` in the root directory, or can be specified with`-k "Kconfig file"`;
12. The `defconfig` file for `Kconfig` is unsued by default, or can be specified with `-d "defconfig file"`;
13. Build order are decided by the defined order in YAML configuration files for Makefile;
14. Build order are decided by the depends in YAML configuration files for Ninja build.

## 2. How to intsall

`Python3`  must be installed for **ZMake**, and at least one of `GNU Make` or `Ninja-build` should be installed.

`Kconfiglib` package should be installed too:

  ```bash
  $ pip3 install kconfiglib
  ```

**Note** that `Kconfiglib` path may be need to be added to 'PATH' environment variable; for Linux, execute `export PATH=$PATH:~/.local/bin` in the shell or add this command to `~/.bashrc` or `~/.bash_profile`;

**ZMake** could be installed by `pip3`:

```bash
$ pip3 install zmake
```

**ZMake** could be installed from source code also:

```bash
$ git clone https://github.com/matthewzu/zmake.git
$ cd zmake
zmake $ python setup.py sdist bdist_wheel
zmake $ pip3 install dist/zmake-0.1.0.tar.gz
```

## 3. How to use

1. **ZMake** provides a command to directly generate a source code directory as a demo:

    ```bash
    $ zmake-demo <path/of/demo>
    ```

2. Use the following command to generate a project from the demo directory:

    ```bash
    <path/of/demo>$ zmake <path/of/project>                     # generate Makefile
    <path/of/demo>$ zmake <path/of/project> -g ninja            # generate build.ninja
    <path/of/demo>$ zmake <path/of/project> -V                  # generate Makefile with verbose output enabled
    <path/of/demo>$ zmake <path/of/project> -d test_defconfig   # generate Makefile with defconfig file
    <path/of/demo>$ zmake <path/of/project> -k xxx.config       # generate Makefile with xxx.config
    <path/of/demo>$ zmake <path/of/project> -y xxx.yml          # generate Makefile with xxx.yml
    ```

    **Note** that:
       * The build log will be saved in `<path/of/project>/zmake.log`;
       * `Makefile` or `build.ninja` will be egnerated in <path/of/project>;
       * The more options could be used:

      ```bash
      $ zmake -h
      usage: zmake [-h] [-v] [-V] [-k "Kconfig file"] [-y "YAML file"]
                  [-d "defconfig file" | -m "Source Code Path"] [-g {make,ninja}]
                  project

      ZMake build Generator

      positional arguments:
        project               project path

      optional arguments:
        -h, --help            show this help message and exit
        -v, --version         show version
        -V, --verbose         enable verbose output
        -k "Kconfig file", --kconfig "Kconfig file"
                              specify Kconfig root configuration file, "Kconfig" by default
        -y "YAML file", --yaml "YAML file"
                              specify YAML root configuration file, "top.yml" by default
        -d "defconfig file", --defconfig "defconfig file"
                              specify defconfig file
        -m "Source Code Path", --menuconfig "Source Code Path"
                              enable menuconfig method, used after project created ONLY
        -g {make,ninja}, --generator {make,ninja}
                              build generator, "make" by default
      ```

3. Configure/build/clean project:

    ```bash
    <path/of/project>$ make config     # configuration project
    <path/of/project>$ make            # build project
    <path/of/project>$ make clean      # clean project
    <path/of/project>$ make config V=1 # configuration project with verbose output enabled
    <path/of/project>$ make V=1        # build project with verbose output enabled
    <path/of/project>$ make clean V=1  # clean project with verbose output enabled
    <path/of/project>$
    <path/of/project>$ ninja config    # configuration project
    <path/of/project>$ ninja           # build project
    <path/of/project>$ ninja clean     # clean project
    <path/of/project>$ ninja config -v # configuration project with verbose output enabled
    <path/of/project>$ ninja -v        # build project with verbose output enabled
    <path/of/project>$ ninja clean -v  # clean project with verbose output enabled
    ```

## 4. YAML Configuration

The source directory should contain a `YAML` root configuration file (`top.yml` by default). It should include the the references to other configuration files or ZMake Entity configurations. For example:

```yaml
# zmake top configuration

# includes, note that file contents MUST NOT be overlapped,
# otherwise the latter will overwrite the former.

includes:
  - mod1/mod11/mod11.yml  # library mod11 yaml
  - mod1/mod12/mod12.yml  # library mod12 yaml
  - mod2/mod2.yml         # library mod2 yaml
  - main/main.yml         # application main/mani2 yaml

# entities defines for the following types:
#   1)'var':    variables that is used to save build arguments or intermediate variables,
#   could be be referenced by '$(variable name)';
#   2)'target': target for build command(make/ninja...);
#   3)'app':    applications that could be executed;
#   4)'lib':    libraries that could be linked to applications.

# system variables
#   1)SRC_PATH: path for source code
#   2)PRJ_PATH: path for project
#   3)CC:       compiler with parameters for objects, must be specified
#   3)AR:       archiver with parameters for libraries, must be specified
#   3)LD:       linker with parameters for applications, must be specified

CC:
  type: var
  desc: compiler with parameters for objects
  val:  gcc -MD

AR:
  type: var
  desc: archiver with parameters for libraries
  val:  ar

LD:
  type: var
  desc: linker with parameters for applications
  val:  gcc

# customer variables
#
# example:
#
#   variable name:  # must be unique for all entities
#     type: var
#     desc: xxx # optional, description that is only for display
#     val:  xxx # value of the variable, which can be of any type; if string, it can contain
#               # references to other variables defined previously, such as '$(var_name)'

MOD11_PATH:
  type: var
  desc: path for moudle11 library
  val:  $(SRC_PATH)/mod1/mod11

# libraries
#
# example:
#
# library name:             # must be unique for all entities
#   type:       lib
#   desc:       xxx         # optional, description that is only for display
#   opt:        CONFIG_XXX  # optional, Kconfig option that decides whether library is enabled:
#                           #   if present, it must be a Kconfig option that will be 'y' or 'n';
#                           #   if absent, library will be will be forced to enable.
#   src:                    # list, source files or directories:
#     - $(ZMake variable name)/xxx/xxx.c
#     - $(ZMake variable name)/xxx  # for directory, all source files in the directory (subdirectories involved) will be involved
#   hdrdirs:                # optional, list, public header file directories
#     - $(ZMake variable name)/xxx
#   cflags:                 # optional, additional compiler flags for C files
#     all:      xxx         # compiler flags for all C files
#     xxx.c:    xxx         # compiler flags for xxx.c
#   cppflags:               # optional, additional compiler flags for cpp files
#     all:      xxx         # compiler flags for all CPP files
#     xxx.cpp:  xxx         # compiler flags for xxx.cpp
#   asmflags:   xxx         # optional, additional compiler flags for assembly files
#     all:      xxx         # compiler flags for all assembly files
#     xxx.s:    xxx         # compiler flags for xxx.s
#     xxx.S:    xxx         # compiler flags for xxx.S

mod11:
  type:         lib
  desc:         moudle11 library
  opt:          CONFIG_MODULE11
  src:
    - $(MOD11_PATH)
  hdrdirs:
    - $(MOD11_PATH)/include
  cflags:
    all:      -DMOD11
    mod11.c:  -DMOD11_MOD11 -I$(MOD11_PATH)/include

# applications
#
# example:
#
# application name:         # must be unique for all entities
#   type:       app
#   desc:       xxx         # optional, description that is only for display
#   opt:        CONFIG_XXX  # optional, Kconfig option that decides whether application is enabled:
#                           #   if present, it must be a Kconfig option that will be 'y' or 'n';
#                           #   if absent, application will be will be forced to enable.
#   src:                    # list, source files or directories:
#     - $(ZMake variable name)/xxx/xxx.c
#     - $(ZMake variable name)/xxx  # for directory, all source files in the directory (subdirectories involved) will be involved
#   cflags:                 # optional, additional compiler flags for C files
#     all:      xxx         # compiler flags for all C files
#     xxx.c:    xxx         # compiler flags for xxx.c
#   cppflags:               # optional, additional compiler flags for cpp files
#     all:      xxx         # compiler flags for all CPP files
#     xxx.cpp:  xxx         # compiler flags for xxx.cpp
#   asmflags:   xxx         # optional, additional compiler flags for assembly files
#     all:      xxx         # compiler flags for all assembly files
#     xxx.s:    xxx         # compiler flags for xxx.s
#     xxx.S:    xxx         # compiler flags for xxx.S
#   linkflags:  xxx         # optional, additional linker flags
#   libs:       xxx         # optional, library dependency list:
#     - xxx                 #   library defined previously

main:
  type:   app
  desc:   main application
  src:
    - $(SRC_PATH)/main/main.c
  cflags:
    - all:  -DMAIN
  libs:
    - mod11
    - mod12

# system targets
#
#   1)config:     configure Kconfig option for project
#   2)all:        building all applications/libraries, default target
#   3)clean:      clean all compiled files
#
#   To enable verbose output, add "V=1" option for make or add "-v" for ninja.

# customer targets
#
# example:
#
# target name:      # must be unique for all entities
#   type: target
#   desc: xxx # optional, description that is only for display
#   cmd:  xxx # string, optional, commands that need be executed with description
#   deps: xxx # optional, library/application/target dependency list:
#     - xxx   #   library/application/target defined previously
#
# Note that 'cmd' and 'deps' MUST NOT be absent at the same time.

info:
  type: target
  desc: display hello world
  cmd:  echo hello world
```

## 5. How to add one module

1. Create one directory in the framework for this module;
2. Add source files and `YAML configuration file` to this directory;
3. Add public header directory with public header files to this directory as you need;
4. Add private header files to this directory as you need;
5. Add `Kconfig` files(`*.config`) to this directory and include it from `Kconfig` in the root directory of the framework.

## 6. TODO

1. Add support for dynamic library, dynamic module and pre-compiled library.
