# How to re-generate MoST Scenario

It is possible to re-generate the scenario using [SAGA - SUMO Activity GenerAtion](https://github.com/lcodeca/SUMOActivityGen), also available in the SUMO contributed tools <https://github.com/eclipse/sumo/tree/master/tools/contributed>.

## Tools

* `tools/osmcleaner.sh` uses `osmfilter` to cleanup the OSM-like files.
* `tools/xml2pickle.py` loads an XML file and dumps a cPickle structure, used to speed-up processing.
* `tools/compute.area.poly.py` computes the centroid and the approximated area for the buildings, it runs on a file containing buildings only.
* `tools/merger/merge.osm.pickles.py` merges all the pickle files in a folder and create the complete OSM-like file.
* `tools/pt.osm2sumo.py` looks for public transports in the OSM-like file and produces the additional files required by SUMO and the activity generation.

## Raw OSM-like files

MoST Scenario is based on data gathered from different sources and aggregated in an OSM-like format in order to be easily used with SUMO tools.
The raw data are in `tools/data` and they are divided by topic.
All the files can be open with [JOSM](https://josm.openstreetmap.de/), modified, saved and then processed and aggregated using `tools/osm-like.aggregator.sh`. The script requires [osmfilter](https://wiki.openstreetmap.org/wiki/Osmfilter) installed.

### Public Transports

In theory, NETCONVERT should be able to extract the public transports using `--ptstop-files` and `--ptline-files` options. Given that the options are not working with `tools/most.raw.osm`, `tools/pt.osm2sumo.py` produces the same files, split between buses and trains.

## Scenario Generation

`tools/static/most.raw.osm` is an OSM-like file with data merged from different sources and hand-fixed to obtain a complete source for the scenario generation.

The scenario can be regenerated using `tools/scenario.generator.sh`

## IMPORTANT: this wiki page is a work in progress. Do not hesitate to ask for help
