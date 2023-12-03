**ZMake**是一个基于`YAML`和`Kconfig`的编译和配置框架，可以生成`GNU Make`和`Ninja build`的编译脚本。这是最近写作和准备[嵌入式操作系统的编译和配置框架 - 概述](https://zhuanlan.zhihu.com/p/669538982)系列文章的一个副产品。

# 1. 概述

常见嵌入式操作系统的编译和配置框架都多多少存在一些问题，因此尝试结合各个嵌入式操作系统的优点组织了一个编译和配置框架。该框架基于几年前做的的一个基于`KConfig`和`GNU Make`的实验性编译框架[simple-build-framework](https://github.com/matthewzu/simple-build-framework)。

本框架的初步方案是全面转向`KConfig + CMake`模式，并选择[jameswalmsley/cmake-kconfig](https://github.com/jameswalmsley/cmake-kconfig.git)作为基础。但是尝试之后发现该仓库具有以下问题：

* 与`Zephyr`绑定太紧，解耦非常困难；
* 必须通过`-D BOARD=xxx`指定`xxx_defconfig`文件；
* 使用`CMake`定义模块还是有点复杂。

实际上嵌入式操作系统的编译和配置框架主要解决4个问题：

1. 组织结构定义，即每个模块包含的源文件、私有头文件、公共头文件、配置文件和可能的目标文件；
2. 编译框架定义，即编译需要的可执行文件、库文件、目标文件以及编译工具、编译参数等等；
3. 配置框架定义，即模块的使能、依赖关系、配置参数等等；
4. 初始化控制定义，即模块的初始化顺序和交互等等。

基于上述分析，**ZMake**决定:

1. 配置框架定义采用[Kconfig Language](https://www.kernel.org/doc/html/latest/kbuild/kconfig-language.html)；这是非常成熟且广泛应用于`Linux`、`U-Boot`、`Zephyr`、`VxWorks`等项目。
2. 采用`YAML`来定义组织结构、编译框架和初始化控制；这是一种流行的数据序列化语言，通常用于编写配置文件，并且适用于各种编程语言；
3. 采用`Python`脚本基于`YAML`和`Kconfig`生成`GNU Make`和`Ninja-build`的编译脚本。

**ZMake**具有以下特点：

1. 基于模块来组织整个框架，目前模块包括应用程序和静态库，后续会包括动态库、动态模块和预编译库；
2. 支持多级模块；
3. 模块采用**YAML**进行配置；
4. 每个模块都有自己的公共和/或私有头文件、源文件（C/C++/汇编）、`Kconfig`和`YAML`配置文件；
5. 属于一个模块的所有文件都放在一个目录下；
6. 支持一个项目包含多个应用程序；
7. 可指定应用程序的以下属性：

   * 名称；
   * 用于启用/禁用该模块的相应`Kconfig`选项；
   * 源文件；
   * 编译器标志
   * 链接器标志；
   * 所依赖的库，用于包含该模块的相应对数文件和库；

8. 可以指定库的以下属性：

   * 名称；
   * 用于启用/禁用该模块的相应 Kconfig 选项；
   * 源文件；
   * 公共头文件目录
   * 编译器标志；
9. 可指定源文件的以下属性：

    * 编译器标志；
10. 可为 **CC/AR/LD** 指定工具和基本选项；
11. `YAML`文件根文件默认是根目录中的`top.yml`，也可以通过 `-y "YAML file"`指定；
12. `Kconfig`的根文件默认是根目录中的`Kconfig`，也可以通过 `-k "Kconfig file"`指定；
13. `Kconfig`的`defconfig`文件默认为空，也可以通过 `-d "defconfig file"`指定；
14. 对于`GNU Make`，编译顺序由`YAML`配置文件中定义的顺序决定；
15. 对于`Ninja build`，构建顺序由`YAML`配置文件中`Ninja build`的依赖关系决定。

# 2. 安装

**ZMake**依赖于`Python3`，此外`GNU Make`或者`Ninja-build`至少应当装一个，否则生成的编译文件也无法使用。

**ZMake**依赖于`Kconfiglib`，可以使用`pip3`安装:

```bash
<path/of/demo>$ pip3 install kconfiglib
```

**注意**：`Kconfiglib`的路径可能需要被添加到`PATH `环境变量中; 对于`Linux`, 可以在`shell`中执行 `export PATH=$PATH:~/.local/bin`或添加到`~/.bashrc`或`~/.bash_profile`中。

**ZMake**可以使用`pip3`安装:

```bash
pip3 install zmake
```

另外，**ZMake**也可以直接从源码安装:

```bash
$ git clone https://github.com/matthewzu/zmake.git
$ cd zmake
zmake $ python setup.py sdist bdist_wheel
zmake $ pip3 install dist/zmake-0.1.0.tar.gz
```

# 3. 使用

1. **ZMake**提供一个命令，可以直接生成一个作为demo的源码目录`<path/of/demo>`:

    ```bash
    $ zmake-demo <path/of/demo>
    ```

2. 使用下面命令从demo目录生成工程`<path/of/project>`:

    ```bash
    <path/of/demo>$ zmake <path/of/project>                     # 生成Makefile
    <path/of/demo>$ zmake <path/of/project> -g ninja            # 生成build.ninja
    <path/of/demo>$ zmake <path/of/project> -V                  # 生成Makefile同时使能调试输出
    <path/of/demo>$ zmake <path/of/project> -d test_defconfig   # 基于defconfig文件生成Makefile
    <path/of/demo>$ zmake <path/of/project> -k xxx.config       # 采用指定的`xxx.config`根文件生成Makefile
    <path/of/demo>$ zmake <path/of/project> -y xxx.yml          # 采用指定的`xxx.yml`根文件生成Makefile
    ```

    **注意**:

      * 编译日志为`<path/of/project>/zmake.log`;
      * `Makefile`或`build.ninja`会生成在<path/of/project>中;
      * 可以使用如下命令查看帮助信息:

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

3. 配置、编译和清理工程:

    ```bash
    <path/of/project>$ make config     # 使用menuconfig界面配置工程
    <path/of/project>$ make            # 编译工程
    <path/of/project>$ make clean      # 清理工程
    <path/of/project>$ make config V=1 # 配置工程同时包含调试信息
    <path/of/project>$ make V=1        # 编译工程同时包含调试信息
    <path/of/project>$ make clean V=1  # 清理工程同时包含调试信息
    <path/of/project>$
    <path/of/project>$ ninja config    # 使用menuconfig界面配置工程
    <path/of/project>$ ninja           # 编译工程
    <path/of/project>$ ninja clean     # 清理工程
    <path/of/project>$ ninja config -v # 配置工程同时包含调试信息
    <path/of/project>$ ninja -v        # 编译工程同时包含调试信息
    <path/of/project>$ ninja clean -v  # 清理工程同时包含调试信息
    ```

# 4. YAML配置

源码目录应当包含一个`YAML`根配置文件（默认是根目录下的 `top.yml`）。`YAML`根配置文件包含各个模块的配置文件，如下所示：

```yaml
# ZMake根配置文件

# includes, 文件内容不能重叠，否则前面文件的内容会被覆盖。

includes:
  - mod1/mod11/mod11.yml  # mod11库的配置文件
  - mod1/mod12/mod12.yml  # mod12库的配置文件
  - mod2/mod2.yml         # mod2库的配置文件
  - main/main.yml         # 应用程序的的配置文件

# 实体定义:
#   1)'var':    变量，用于存放编译参数或者中间变量，可以使用'$(变量名)'方式引用;
#   2)'target': GNU Make/Ninja Build的编译目标;
#   3)'app':    可以被执行的应用程序;
#   4)'lib':    可以被连接到应用程序的库。

# 系统变量
#   1)SRC_PATH: 源码路径，ZMake预定义变量
#   2)PRJ_PATH: 工程路径, ZMake预定义变量
#   3)CC:       目标文件编译器，包含编译器名称和必须的参数，必须被指定
#   3)AR:       库文件打包器，包含打包器名称和必须的参数，必须被指定
#   3)LD:       应用程序链接器，包含链接器名称和必须的参数，必须被指定

CC:
  type: var
  desc: compiler for objects, must be defined
  val:  gcc -MD

AR:
  type: var
  desc: archiver for libraries, must be defined
  val:  ar

LD:
  type: var
  desc: linker for applications, must be defined
  val:  gcc

# 用户变量
#
# 例子:
#
#   变量名称:   # 必须在所有实体中保持唯一
#     type: var
#     desc: xxx # 可选的描述信息字符串，仅用以显示
#     val:  xxx # 变量的值，可以是任意类型；如果是字符串，则可以包含对其他变量的引用。
#

MOD11_PATH:
  type: var
  desc: path for moudle11 library
  val:  $(SRC_PATH)/mod1/mod11

# 库
#
# 例子:
#
# 库名称:                   # 必须在所有实体中保持唯一
#   type:       lib
#   desc:       xxx         # 可选的描述信息字符串，仅用以显示
#   opt:        CONFIG_XXX  # 可选的'Kconfig'选项，用以决定库是否被使能；
#                           #   如果存在，必须是一个'Kconfig'选项，值可以是'y'或者'n'；
#                           #   如果不存在，那么库默认使能。
#   src:                    # 源文件列表, 包含若干个源文件或者源文件目录，例如:
#     - $(ZMake variable name)/xxx/xxx.c
#     - $(ZMake variable name)/xxx  # 对于目录，目录下（含子目录）的所有源文件都会被包含
#   hdrdirs:                # 可选的公用头文件列表, 包含若干个公用头文件目录，例如:
#     - $(ZMake variable name)/xxx
#   cflags:                 # 可选的C文件编译参数列表, 包含额外的C文件编译参数
#     all:      xxx         # 用于库里面所有C文件的编译参数
#     xxx.c:    xxx         # 用于库里面指定C文件'xxx.c'的编译参数
#   cppflags:               # 可选的C++文件编译参数列表, 包含额外的C++文件编译参数
#     all:      xxx         # 用于库里面所有C++文件的编译参数
#     xxx.cpp:  xxx         # 用于库里面指定C++文件'xxx.cpp'的编译参数
#   asmflags:   xxx         # 可选的汇编文件编译参数列表, 包含额外的汇编文件编译参数
#     all:      xxx         # 用于库里面所有汇编文件的编译参数
#     xxx.s:    xxx         # 用于库里面指定汇编文件'xxx.s'的编译参数
#     xxx.S:    xxx         # 用于库里面指定汇编文件'xxx.S'的编译参数

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

# 应用程序
#
# 例子:
#
# 应用程序名称:             # 必须在所有实体中保持唯一
#   type:       app
#   desc:       xxx         # 可选的描述信息字符串，仅用以显示
#   opt:        CONFIG_XXX  # 可选的'Kconfig'选项，用以决定应用程序是否被使能；
#                           #   如果存在，必须是一个'Kconfig'选项，值可以是'y'或者'n'；
#                           #   如果不存在，那么应用程序默认使能。
#   src:                    # 源文件列表, 包含若干个源文件或者源文件目录，例如:
#     - $(ZMake variable name)/xxx/xxx.c
#     - $(ZMake variable name)/xxx  # 对于目录，目录下（含子目录）的所有源文件都会被包含
#   cflags:                 # 可选的C文件编译参数列表, 包含额外的C文件编译参数
#     all:      xxx         # 用于库里面所有C文件的编译参数
#     xxx.c:    xxx         # 用于库里面指定C文件'xxx.c'的编译参数
#   cppflags:               # 可选的C++文件编译参数列表, 包含额外的C++文件编译参数
#     all:      xxx         # 用于库里面所有C++文件的编译参数
#     xxx.cpp:  xxx         # 用于库里面指定C++文件'xxx.cpp'的编译参数
#   asmflags:   xxx         # 可选的汇编文件编译参数列表, 包含额外的汇编文件编译参数
#     all:      xxx         # 用于库里面所有汇编文件的编译参数
#     xxx.s:    xxx         # 用于库里面指定汇编文件'xxx.s'的编译参数
#     xxx.S:    xxx         # 用于库里面指定汇编文件'xxx.S'的编译参数
#   linkflags:  xxx         # 可选的链接参数字符串, 包含额外的链接参数
#   libs:       xxx         # 可选的库依赖列表:
#     - xxx                 #   之前定义过的库

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

# 系统目标
#
#   1)config:     配置工程中的Kconfig选项
#   2)all:        编译所有应用程序和库，默认目标
#   3)clean:      清理所有编译出来的文件
#
#   为了使能调试信息输出, 可以添加 "V=1" 选项（'GNU Make'）或者"-v" （'Ninja build'）.

# 用户目标
#
# 例子:
#
# 目标名称:      # 必须在所有实体中保持唯一
#   type: target
#   desc: xxx   # 可选的描述信息字符串，仅用以显示
#   cmd:  xxx   # 可选, 需要执行的命令字符串
#   deps: xxx   # 可选的应用程序/库/目标依赖列表:
#     - xxx     #   之前定义过的应用程序/库/目标
#
# **注意**：'cmd'和'deps'不能同时为空。

info:
  type: target
  desc: display hello world
  cmd:  echo hello world
```

## 5. How to add one module

1. 在框架中为该模块创建一个为目录；
2. 在该目录中为模块添加源文件和 "YAML 配置文件"；
3. 根据需要在该目录中添加公共头文件目录；
4. 根据需要在该目录中添加私有头文件；
5. 在该目录中添加 `Kconfig`文件（`*.config`），并在根目录中的`Kconfig`文件中包含该文件。

## 6. TODO

1. 添加动态库、动态模块和预编译库支持。
