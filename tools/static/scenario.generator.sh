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

INPUT="$MOST_SCENARIO/scenario/in"
ROUTES="$INPUT/route"
ADD="$INPUT/add"

OUTPUT="out"
mkdir -p $OUTPUT

echo "[$(date)] --> Creating the network..."
netconvert -c most.netcfg

echo "[$(date)] --> Extracting the polygons..."
polyconvert -c most.polycfg

echo "[$(date)] --> Convert osm & net to Pickle..."
python3 scripts/xml2pickle.py -i most.raw.osm -o $OUTPUT/osm.pkl
python3 scripts/xml2pickle.py -i most.net.xml -o $OUTPUT/net.pkl

echo "[$(date)] --> Creating Parking Lots..."
python3 scripts/parkings.osm2sumo.py --osm $OUTPUT/osm.pkl --net most.net.xml \
    --cfg duarouter.sumocfg --visibility-threshold 50 --max-alternatives 15 -o $OUTPUT/most.

echo "[$(date)] --> Creating Public Transports..."
python3 scripts/pt.osm2sumo.py --osm $OUTPUT/osm.pkl --net most.net.xml -o $OUTPUT/most.

echo "[$(date)] --> Extracting the TAZ from the boundaries..."
python3 scripts/taz.from.net.osm.py --osm $OUTPUT/osm.pkl --net most.net.xml \
    --taz $OUTPUT/most.complete.taz.xml --od $OUTPUT/most.complete.taz.weight.csv \
    --poly $OUTPUT/most.poly.weight

echo "[$(date)] --> Generate the TAZ for the AoI..."
python3 $SUMO_TOOLS/edgesInDistricts.py -n most.net.xml -t aoi.taz.shape.xml -o aoi.taz.xml

echo "[$(date)] --> Extract the parkign areas in the AoI..."
python3 scripts/parkings.in.aoi.py -t aoi.taz.xml -p $OUTPUT/most.parking.add.xml \
    -o parkings.aoi.json