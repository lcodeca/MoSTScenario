#!/bin/bash

# Monaco SUMO Traffic (MoST) Scenario
# Author: Lara CODECA

# exit on error
set -e

ROOT=$(pwd)
OUTPUT=$ROOT/out
mkdir -p $OUTPUT

echo "[$(date)] --> Creating the network..."
netconvert -c most.netcfg --output-prefix $OUTPUT/most.

echo "[$(date)] --> Extracting the polygons..."
polyconvert -c most.polycfg --net-file $OUTPUT/most.net.xml --output-prefix $OUTPUT/most.

echo "[$(date)] --> Convert osm & net to Pickle..."
python3 xml2pickle.py -i most.raw.osm -o $OUTPUT/osm.pkl
python3 xml2pickle.py -i $OUTPUT/most.net.xml -o $OUTPUT/net.pkl

echo "[$(date)] --> Creating Public Transports..."
python3 pt.osm2sumo.py --osm $OUTPUT/osm.pkl --net $OUTPUT/most.net.xml -o $OUTPUT/most.

INTERVAL="-b 0 -e 86400"
echo "[$(date)] --> Generate bus trips..."
python $SUMO_TOOLS/ptlines2flows.py -n $OUTPUT/most.net.xml $INTERVAL -p 900 \
    --random-begin --seed 42 --no-vtypes \
    --ptstops $OUTPUT/most.busstops.add.xml --ptlines $OUTPUT/most.buslines.add.xml \
    -o $OUTPUT/most.buses.flows.xml
sed -e s/:0//g -i'' $OUTPUT/most.buses.flows.xml

echo "[$(date)] --> Generate train trips..."
python $SUMO_TOOLS/ptlines2flows.py -n $OUTPUT/most.net.xml $INTERVAL -p 1200 \
    -d 300 --random-begin --seed 42 --no-vtypes \
    --ptstops $OUTPUT/most.trainstops.add.xml --ptlines $OUTPUT/most.trainlines.add.xml \
    -o $OUTPUT/most.trains.flows.xml
sed -e s/:0//g -i'' $OUTPUT/most.trains.flows.xml

echo "[$(date)] --> Creating Parking Areas..."
python3 $SUMO_TOOLS/contributed/saga/generateParkingAreasFromOSM.py \
    --osm most.raw.osm --net $OUTPUT/most.net.xml --out $OUTPUT/most.parking.add.xml 

echo "[$(date)] --> Creating Parking Areas Rerouters..."
python3 $SUMO_TOOLS/generateParkingAreaRerouters.py --processes 4 \
    -n $OUTPUT/most.net.xml -a $OUTPUT/most.parking.add.xml --max-number-alternatives 15 \
    --min-capacity-visibility-true 50 -o $OUTPUT/most.rerouters.add.xml --tqdm

echo "[$(date)] --> Extracting the TAZ from the boundaries..."
mkdir -p $OUTPUT/taz/buildings
python3 $SUMO_TOOLS/contributed/saga/generateTAZBuildingsFromOSM.py --processes 2 \
    --osm most.raw.osm --net $OUTPUT/most.net.xml --taz-output $OUTPUT/taz/most.complete.taz.xml \
    --weight-output $OUTPUT/taz/most.complete.taz.weight.csv \
    --poly-output $OUTPUT/taz/buildings/most.poly.weight

echo "[$(date)] --> Activity-based Mobility Generation..."
python3 $SUMO_TOOLS/contributed/saga/activitygen.py -c most.activitygen.json

echo "[$(date)] --> Run SUMO..."
mkdir -p $OUTPUT/res
sumo -c most.test.sumocfg
