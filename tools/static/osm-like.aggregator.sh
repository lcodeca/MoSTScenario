#!/bin/bash

# Monaco SUMO Traffic (MoST) Scenario
# Author: Lara CODECA

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

echo "OSM deep cleanup..."
bash osmcleaner.sh

# ######### FIX AREA and CENTROID of the POLYGONS
python3 scripts/xml2pickle.py -i data/polygons.osm -o tmp.polygons.pkl
python3 scripts/compute.area.poly.py -i tmp.polygons.pkl -o data/polygons.osm
rm tmp.polygons.pkl

# ## ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ MERGING OSM FILES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ##
echo "Merging all the files..."
cd scripts/merger
mkdir -p picklesToMerge
touch picklesToMerge/saferm
rm -v picklesToMerge/*
python3 ../xml2pickle.py -i ../../data/boundaries.osm   -o picklesToMerge/boundaries.pkl
python3 ../xml2pickle.py -i ../../data/pois.osm         -o picklesToMerge/pois.pkl
python3 ../xml2pickle.py -i ../../data/polygons.osm     -o picklesToMerge/polygons.pkl
python3 ../xml2pickle.py -i ../../data/parkings.osm     -o picklesToMerge/parkings.pkl
python3 ../xml2pickle.py -i ../../data/network.osm      -o picklesToMerge/network.pkl
python3 ../xml2pickle.py -i ../../data/pt.osm           -o picklesToMerge/pt.pkl
python3 ../xml2pickle.py -i ../../data/gateways.osm     -o picklesToMerge/gateways.pkl

python3 merge.osm.pickles.py -d picklesToMerge -o merged.pickles.osm
mv -v merged.pickles.osm $STATIC/most.raw.osm
