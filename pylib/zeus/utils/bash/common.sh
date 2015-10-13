#!/bin/bash -e

# Copyright 2011 Room77, Inc.
# Author: oztekin@room77.com (Uygar Oztekin)

# for cron scripts where env variable may not be set.
[[ -z "$USER" ]] && export USER=`whoami`

# Set color mode only if we are running in a terminal.
if [ -t 1 ] ; then
  RED="\033[;31m"
  GREEN="\033[;32m"
  YELLOW="\033[;33m"
  BLUE="\033[;36m"
  BOLD="\033[1m"
  RESET="\033[0m"
else
  BOLD=""
  RED=""
  GREEN=""
  YELLOW=""
  BLUE=""
  RESET=""
fi

function Success {
  echo -e $GREEN"Success:"$RESET $*
}

function Warning {
  echo -e $YELLOW"Warning:"$RESET $* >&2
}

function Failure {
  echo -e $RED"Failure:"$RESET $* >&2
}

function Abort {
  Failure $*
  exit 1
}

# Debug echo.
function decho {
  [[ -z "$DEBUG" ]] && return
  echo -ne $BLUE
  echo $@
  echo -ne $RESET
}

# Dumps all the pipeline vars.
function DumpVars {
  decho "Script: $0"
  printenv | grep "PIPELINE"
}

# Builds and executes a binary.
# Deprecated: Use flash run directly.
function BuildAndRun {
  local args=""
  local i
  for i in "${@:2}"; do
    args="${args}\"$i\" "
  done
  flash run --args="${args}" /$1
}

# If debug is enabled, dump the vars.
[[ -n "$DEBUG" ]] && DumpVars || true
