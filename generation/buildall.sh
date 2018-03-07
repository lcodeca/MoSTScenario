#!/bin/bash

# exit on error
set -e

INPUT="../scenario/in"
ROUTES="$INPUT/route"
ADD="$INPUT/add"
OUTPUT="out"

TARGET=$OUTPUT      # change here to decide where to save the final files
                    # if in $ROUTES, the original files will be overwritten

mkdir -p $OUTPUT

## ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ PUBLIC TRANSPORTS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ##

echo "Generate bus trips..."
python $SUMO_TOOLS/ptlines2flows.py -n $INPUT/most.net.xml -b 18000 -e 43200 -p 600 \
    --random-begin --seed 42 --no-vtypes \
    --ptstops $ADD/most.busstops.add.xml --ptlines pt/most.buslines.add.xml \
    -o $OUTPUT/most.buses.flows.xml

sed -e s/:0//g -i $OUTPUT/most.buses.flows.xml

echo "Generate train trips..."
python $SUMO_TOOLS/ptlines2flows.py -n $INPUT/most.net.xml -b 18000 -e 43200 -p 900 \
    -d 300 --random-begin --seed 42 --no-vtypes \
    --ptstops $ADD/most.trainstops.add.xml --ptlines pt/most.trainlines.add.xml \
    -o $OUTPUT/most.trains.flows.xml

sed -e s/:0//g -i $OUTPUT/most.trains.flows.xml

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

duarouter -c routes.vehicle.duacfg --route-files $OUTPUT/most.gateways.trips.xml \
    --output-file $TARGET/most.gateways.rou.xml