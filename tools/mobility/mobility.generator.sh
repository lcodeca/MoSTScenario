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
ADD="$INPUT/add"

OUTPUT="out"
mkdir -p $OUTPUT

## ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ PUBLIC TRANSPORTS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ##

# https://github.com/eclipse/sumo/issues/3803
#  Depending on the SUMO version, it's possible that the -b parameter is not really working.

INTERVAL="-b 14400 -e 50400"
# INTERVAL="-b 0 -e 86400"

echo "[$(date)] --> Generate bus trips..."
python $SUMO_TOOLS/ptlines2flows.py -n $INPUT/most.net.xml $INTERVAL -p 900 \
    --random-begin --seed 42 --no-vtypes \
    --ptstops $ADD/most.busstops.add.xml --ptlines pt/most.buslines.add.xml \
    -o $OUTPUT/most.buses.flows.xml

sed -e s/:0//g -i $OUTPUT/most.buses.flows.xml

echo "[$(date)] --> Generate train trips..."
python $SUMO_TOOLS/ptlines2flows.py -n $INPUT/most.net.xml $INTERVAL -p 1200 \
    -d 300 --random-begin --seed 42 --no-vtypes \
    --ptstops $ADD/most.trainstops.add.xml --ptlines pt/most.trainlines.add.xml \
    -o $OUTPUT/most.trains.flows.xml

sed -e s/:0//g -i $OUTPUT/most.trains.flows.xml

## ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ TRACI MOBILITY GENERATION ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ##

echo "[$(date)] --> Generate mobility..."
python3 intermodal.mobilitygen.py -c most.intermodal.mobilitygen.json