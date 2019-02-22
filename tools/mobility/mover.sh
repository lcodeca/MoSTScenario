#!/bin/bash

# Monaco SUMO Traffic (MoST) Scenario
#     Copyright (C) 2019
#     Lara CODECA

# exit on error
set -e

if [ -z "$MOST_SCENARIO" ]
then
    echo "Environment variable MOST_SCENARIO is not set."
    echo "Please set MOST_SCENARIO to the root directory."
    echo "Bash example:"
    echo "      in MoSTScenario exec"
    echo '      export MOST_SCENARIO=$(pwd)'
    exit
fi

SCENARIO="$MOST_SCENARIO/scenario"
INPUT="$SCENARIO/in"
ROUTES="$INPUT/route"

OUTPUT="out"
mkdir -p $OUTPUT

TARGET=$ROUTES$1      # change here to decide where to save the final files
                      # if in $ROUTES, the original files will be overwritten
                      # if something is passed by command line, it appends to the route dir
mkdir -p $TARGET

cp -v $OUTPUT/*.flows.xml $TARGET/.
cp -v $OUTPUT/*.rou.xml $TARGET/.