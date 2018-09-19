#!/bin/bash

# Monaco SUMO Traffic (MoST) Scenario
#     Copyright (C) 2018
#     Lara CODECA

if [ -z "$MOST_SCENARIO" ]
then
    echo "Environment variable MOST_SCENARIO is not set."
    echo "Please set MOST_SCENARIO to the root directory."
    echo "Bash example:"
    echo "      in MoSTScenario exec"
    echo '      export MOST_SCENARIO=$(pwd)'
    exit
fi

# cleanup first
rm -v $MOST_SCENARIO/tools/mobility/taz/*
rm -v $MOST_SCENARIO/tools/mobility/taz/buildings/*
rm -v $MOST_SCENARIO/tools/mobility/pt/*

# copy files around
cp -v out/*.taz.* 	        $MOST_SCENARIO/tools/mobility/taz/.
cp -v out/*.poly.weight.* 	$MOST_SCENARIO/tools/mobility/taz/buildings/.
cp -v out/*lines*           $MOST_SCENARIO/tools/mobility/pt/.
cp -v out/*stops*           $MOST_SCENARIO/scenario/in/add/.
cp -v out/*parking*         $MOST_SCENARIO/scenario/in/add/.
cp -v most.poly.xml         $MOST_SCENARIO/scenario/in/add/.
cp -v most.net.xml          $MOST_SCENARIO/scenario/in/.
