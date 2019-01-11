#!/bin/bash

# Monaco SUMO Traffic (MoST) Scenario
#     Copyright (C) 2018
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

STATIC=$MOST_SCENARIO/tools/static
MOBILITY=$MOST_SCENARIO/tools/mobility
SCENARIO=$MOST_SCENARIO/scenario

cd $STATIC
echo "[$(date)] ~~~ Scenario Generation ~~~ "
bash osm-like.aggregator.sh
bash scenario.generator.sh
bash mover.sh

cd $MOBILITY
echo "[$(date)] ~~~ Mobility Generation ~~~ "
bash mobility.generator.sh
bash mover.sh

cd $SCENARIO
echo "[$(date)] ~~~ SUMO Simulation ~~~ "
bash run.sh

echo "Done."