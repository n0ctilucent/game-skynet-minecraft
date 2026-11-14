dnl configure.ac for game-skynet-minecraft
dnl bitsmasher.net Skynet & Stargate Node Orchestration
dnl Process this file with autoconf to produce a configure script.

AC_PREREQ([2.69])
AC_INIT([game-skynet-minecraft], [1.1], [franklin@bitsmasher.net])
AC_CONFIG_SRCDIR([src/skynet/npu_spatial_engine.py])

AC_CANONICAL_HOST

case $host in
  aarch64-*-linux*)
    AC_MSG_NOTICE([Target architecture identified: Raspberry Pi 5 (aarch64).])
    AC_DEFINE([STALKER_NODE_ARM64], [1], [Architecture is aarch64])
    IS_STARK_HARDWARE=yes
    ;;
  x86_64-*-linux*)
    AC_MSG_NOTICE([Target architecture identified: x86_64. Simulation mode enabled for T2BM logic.])
    IS_STARK_HARDWARE=no
    ;;
  *)
    AC_MSG_ERROR([Unsupported host: $host. Stargate orchestration requires aarch64 or x86_64.])
    ;;
esac

AC_CHECK_PROGS([PYTHON3], [python3.13 python3.12 python3.11 python3], [none])
if test "$PYTHON3" = "none"; then
    AC_MSG_ERROR([Python 3.11+ is required for Skynet orchestration logic.])
fi

AC_CHECK_PROGS([GO], [go], [none])
if test "$GO" = "none"; then
    AC_MSG_WARN([Go toolchain not found. Schematic generation via schem-gen will be disabled.])
fi

AC_CHECK_PROGS([MCRCON], [mcrcon], [none], [/home/minecraft/bin:$PATH])

if test "$IS_STARK_HARDWARE" = "yes"; then
    AC_CHECK_FILE([/dev/hailo0], 
        [AC_MSG_NOTICE([Hailo-8L NPU detected. Hub 00 logic core ready.])],
        [AC_MSG_WARN([Hailo-8L driver not found at /dev/hailo0. Inference Nexus will default to CPU fallback.])]
    )

    AC_CHECK_FILE([/dev/apex_0],
        [AC_MSG_NOTICE([Edge TPU detected. Hub 06 surveillance node ready.])],
        [AC_MSG_WARN([Edge TPU driver not found at /dev/apex_0. Sense/Net vision may be limited.])]
    )
fi

AC_ARG_WITH([server-dir],
    [AS_HELP_STRING([--with-server-dir=DIR], [Path to the Paper Minecraft server directory (default: /home/minecraft)])],
    [SERVER_DIR=$withval],
    [SERVER_DIR="/home/minecraft"]
)

AC_ARG_WITH([venv],
    [AS_HELP_STRING([--with-venv=DIR], [Virtual environment directory (default: .venv313 or .venv)])],
    [VENV_DIR=$withval],
    [
        if test -d "$srcdir/.venv313"; then
            VENV_DIR=".venv313"
        elif test -d "$srcdir/.venv"; then
            VENV_DIR=".venv"
        else
            VENV_DIR=".venv"
        fi
    ]
)

AC_ARG_WITH([node901],
    [AS_HELP_STRING([--with-node901=HOST], [NVIDIA Jetson node901 hostname or IP (default: node901)])],
    [NODE901_HOST=$withval],
    [NODE901_HOST="node901"]
)

AC_SUBST([SERVER_DIR])
AC_SUBST([VENV_DIR])
AC_SUBST([PYTHON3])
AC_SUBST([IS_STARK_HARDWARE])
AC_SUBST([MCRCON])
AC_SUBST([NODE901_HOST])

AM_INIT_AUTOMAKE

AC_CONFIG_FILES([
  Makefile
  docs/grimoire/Makefile
  docs/slides/Makefile
])

AC_OUTPUT
