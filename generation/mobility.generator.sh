#!/bin/bash

# Monaco SUMO Traffic (MoST) Scenario
#     Copyright (C) 2018 
#     Lara CODECA

# exit on error
set -e

INPUT="../scenario/in"
ROUTES="$INPUT/route"
ADD="$INPUT/add"

OUTPUT="out"
mkdir -p $OUTPUT
touch $OUTPUT/test
rm $OUTPUT/*

TARGET=$ROUTES      # change here to decide where to save the final files
                    # if in $ROUTES, the original files will be overwritten
mkdir -p $TARGET

## ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ PUBLIC TRANSPORTS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ##

# https://github.com/eclipse/sumo/issues/3803
#  Depending on the SUMO version, it's possible that the -b parameter is not really working.

echo "Generate bus trips..."
python $SUMO_DEV_TOOLS/ptlines2flows.py -n $INPUT/most.net.xml -b 18000 -e 43200 -p 1200 \
    --random-begin --seed 42 --no-vtypes \
    --ptstops $ADD/most.busstops.add.xml --ptlines pt/most.buslines.add.xml \
    -o $OUTPUT/most.buses.flows.xml

sed -e s/:0//g -i $OUTPUT/most.buses.flows.xml
if [[ $OUTPUT != $TARGET ]] 
    then cp -u $OUTPUT/most.buses.flows.xml $TARGET/most.buses.flows.xml  
fi

echo "Generate train trips..."
python $SUMO_DEV_TOOLS/ptlines2flows.py -n $INPUT/most.net.xml -b 18000 -e 43200 -p 1200 \
    -d 300 --random-begin --seed 42 --no-vtypes \
    --ptstops $ADD/most.trainstops.add.xml --ptlines pt/most.trainlines.add.xml \
    -o $OUTPUT/most.trains.flows.xml

sed -e s/:0//g -i $OUTPUT/most.trains.flows.xml
if [[ $OUTPUT != $TARGET ]] 
    then cp -u $OUTPUT/most.trains.flows.xml $TARGET/most.trains.flows.xml
fi

## ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ MOBILITY GENERATION ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ##

echo "Generate mobility..."
python3 mobilitygen.trips.py -c mobilitygen.trips.json

echo "Generate the routes from the trips for all vTypes..."
duarouter -c routes.person.duacfg   --output-file $TARGET/most.pedestrian.rou.xml

duarouter -c routes.vehicle.duacfg  --route-files $OUTPUT/most.bicycle.trips.xml \
    --output-file $TARGET/most.bicycle.rou.xml
duarouter -c routes.vehicle.duacfg --route-files $OUTPUT/most.2wheeler.trips.xml \
    --output-file $TARGET/most.2wheeler.rou.xml

duarouter -c routes.vehicle.duacfg --route-files $OUTPUT/most.passenger.trips.xml \
    --output-file $TARGET/most.passenger.rou.xml
duarouter -c routes.vehicle.duacfg --route-files $OUTPUT/most.evehicle.trips.xml \
    --output-file $TARGET/most.evehicle.rou.xml
duarouter -c routes.vehicle.duacfg --route-files $OUTPUT/most.other.trips.xml \
    --output-file $TARGET/most.other.rou.xml
