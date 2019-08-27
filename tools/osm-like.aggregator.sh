#!/bin/bash

# Monaco SUMO Traffic (MoST) Scenario
# Author: Lara CODECA

# exit on error
set -e

ROOT=$(pwd)

echo "OSM deep cleanup..."
bash $ROOT/osmcleaner.sh

# ######### FIX AREA and CENTROID of the POLYGONS
python3 $ROOT/xml2pickle.py -i data/polygons.osm -o tmp.polygons.pkl
python3 $ROOT/compute.area.poly.py -i tmp.polygons.pkl -o data/polygons.osm
rm tmp.polygons.pkl

# ## ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ MERGING OSM FILES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ##
echo "Merging all the files..."
cd $ROOT/merger
mkdir -p picklesToMerge
touch picklesToMerge/saferm
rm -v picklesToMerge/*
python3 $ROOT/xml2pickle.py -i $ROOT/data/boundaries.osm   -o picklesToMerge/boundaries.pkl
python3 $ROOT/xml2pickle.py -i $ROOT/data/pois.osm         -o picklesToMerge/pois.pkl
python3 $ROOT/xml2pickle.py -i $ROOT/data/polygons.osm     -o picklesToMerge/polygons.pkl
python3 $ROOT/xml2pickle.py -i $ROOT/data/parkings.osm     -o picklesToMerge/parkings.pkl
python3 $ROOT/xml2pickle.py -i $ROOT/data/network.osm      -o picklesToMerge/network.pkl
python3 $ROOT/xml2pickle.py -i $ROOT/data/pt.osm           -o picklesToMerge/pt.pkl
python3 $ROOT/xml2pickle.py -i $ROOT/data/gateways.osm     -o picklesToMerge/gateways.pkl
python3 merge.osm.pickles.py -d picklesToMerge -o merged.pickles.osm
mv -v merged.pickles.osm $ROOT/most.raw.osm
