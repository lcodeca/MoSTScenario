#!/usr/bin/env python3

""" Compute the area of the polygon and tag it in a OSM-like file. """

import argparse
import logging
import sys
import pickle
import numpy
import pyproj

from functools import partial
from shapely.geometry import shape, MultiPoint
from shapely.ops import transform
from tqdm import tqdm

HEADER_TPL = """<?xml version='1.0' encoding='UTF-8'?>
<osm version="0.6">
    <bounds minlat="{minlat}" minlon="{minlon}" maxlat="{maxlat}" maxlon="{maxlon}"/>""" # pylint: disable=C0301

NODE_TPL = """
    <node id="{id}" lat="{lat}" lon="{lon}" ele="{ele}" version="1"> {tags}
    </node>"""

WAY_TPL = """
    <way id="{id}" version="1"> {nds} {tags}
    </way>"""

ND_TPL = """
        <nd ref="{ref}"/>"""

TAG_TPL = """
        <tag k="{k_val}" v="{v_val}"/>"""

FOOTER_TPL = """
</osm>
"""

def _logs():
    """ Log init. """
    file_handler = logging.FileHandler(filename='{}.log'.format(sys.argv[0]),
                                       mode='w')
    stdout_handler = logging.StreamHandler(sys.stdout)
    handlers = [file_handler, stdout_handler]
    logging.basicConfig(handlers=handlers, level=logging.DEBUG,
                        format='[%(asctime)s] %(levelname)s: %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p')

def _args():
    """ Argument Parser
    ret: parsed arguments.
    """
    parser = argparse.ArgumentParser(
        prog='{}'.format(sys.argv[0]),
        usage='%(prog)s -i osmstruct -o osmfile -f factor',
        description='Shrink the polygons in a OSM-like file.')
    parser.add_argument(
        '-i', type=str, dest='input', required=True,
        help='OSM-like input in pickle format.')
    parser.add_argument(
        '-o', type=str, dest='output', required=True,
        help='OSM-like output file.')
    return parser.parse_args()

def _read_from_pickle(filename):
    """ Dump the object into a binary pickle file. """
    with open(filename, 'rb') as pickle_obj:
        obj = pickle.load(pickle_obj)
    return obj

def _compute_area_from_osm(osm):
    """ Compute the are of the polygons OSM-like structure. """

    osm_nodes = dict()
    for node in osm['node']:
        osm_nodes[node['id']] = node

    poly = list()
    for way in tqdm(osm['way']):
        centroid = _poly_centroid(way, osm_nodes)
        centroid_str = '{}, {}'.format(centroid[0], centroid[1])
        area = _poly_area_approximation(way, osm_nodes)

        ## Update the tags for the way
        way['tag'] = _update_tag(way['tag'], 'centroid', centroid_str)
        way['tag'] = _update_tag(way['tag'], 'approx_area', str(area))
        poly.append(way)

    ## Update the ways in the OSM-like structure.
    osm['way'] = poly

    return osm

def _update_tag(tags, key, value):
    """ Update the tag value, to avoid duplication. """

    found = False
    length = len(tags)
    for pos in range(length):
        if tags[pos]['k'] == key:
            tags[pos]['v'] = value
            found = True
            break

    if not found:
        tags.append({"k": key, "v": value})

    return tags

def _poly_centroid(way, nodes):
    """ Compute the centroid of a OSM polygon. """
    points = []
    for node in way['nd']:
        points.append([float(nodes[node['ref']]['lat']), float(nodes[node['ref']]['lon'])])
    return numpy.mean(numpy.array(points), axis=0)

def _poly_area_shapely(way, nodes):
    """ Compute the area of an irregular OSM polygon.
        see: https://arachnoid.com/area_irregular_polygon/
             https://gist.github.com/robinkraft/c6de2f988c9d3f01af3c
    """
    points = []
    for node in way['nd']:
        points.append([float(nodes[node['ref']]['lat']), float(nodes[node['ref']]['lon'])])

    geom = {'type': 'Polygon',
            'coordinates': [points]}

    s = shape(geom)
    # http://openstreetmapdata.com/info/projections
    proj = partial(pyproj.transform, pyproj.Proj(init='epsg:4326'),
                   pyproj.Proj(init='epsg:3857'))

    newshape = transform(proj, s)

    return newshape.area

def _poly_area_approximation(way, nodes):
    """ Compute the approximated area of an irregular OSM polygon.
        see: https://arachnoid.com/area_irregular_polygon/
             https://gist.github.com/robinkraft/c6de2f988c9d3f01af3c
    """
    points = []
    for node in way['nd']:
        points.append([float(nodes[node['ref']]['lat']), float(nodes[node['ref']]['lon'])])

    approx = MultiPoint(points).convex_hull
    # http://openstreetmapdata.com/info/projections
    proj = partial(pyproj.transform, pyproj.Proj(init='epsg:4326'),
                   pyproj.Proj(init='epsg:3857'))

    converted_approximation = transform(proj, approx)

    return converted_approximation.area

def _write_all_nodes(osm, filebuffer):
    """ Write all the nodes to OSM-like file. """

    for node in osm['node']:
        string_of_tags = ""
        for value in node['tag']:
            val = value['v'].replace('"', '')
            val = val.replace('&', 'and')
            string_of_tags += TAG_TPL.format(
                k_val=value['k'],
                v_val=val) # .encode('utf-8')
            if value['k'] == 'ele':
                node['ele'] = val

        filebuffer.write(NODE_TPL.format(id=node['id'], lat=node['lat'],
                                         lon=node['lon'], ele=node['ele'],
                                         tags=string_of_tags))

def _write_all_ways(osm, filebuffer):
    """ Write all the ways to OSM-like file. """
    for way in osm['way']:
        string_of_nodes = ""
        for nid in way['nd']:
            string_of_nodes += ND_TPL.format(ref=nid['ref'])
        string_of_tags = ""
        for tag in way['tag']:
            value = tag['v'].replace('"', '')
            value = value.replace('&', 'and')
            string_of_tags += TAG_TPL.format(
                k_val=tag['k'],
                v_val=value) # .encode('utf-8')

        filebuffer.write(WAY_TPL.format(
            id=way['id'], nds=string_of_nodes, tags=string_of_tags))

def _write_osm_file(boundaries, polygons, filename):
    """ Write the OSM-like file. """

    with open(filename, 'w') as outfile:
        outfile.write(HEADER_TPL.format(
            minlat=boundaries['minlat'], minlon=boundaries['minlon'],
            maxlat=boundaries['maxlat'], maxlon=boundaries['maxlon']))

        _write_all_nodes(polygons, outfile)
        _write_all_ways(polygons, outfile)

        outfile.write(FOOTER_TPL)

def _main():
    """ Fixes the elevation of polygons in an OSM-like file. """

    args = _args()

    logging.info("Loading %s", args.input)
    osm = _read_from_pickle(args.input)

    logging.info("Parsing polygons..")
    polygons = _compute_area_from_osm(osm)

    logging.info("Creation of %s", args.output)
    _write_osm_file(osm['bounds'][0], polygons, args.output)

if __name__ == "__main__":
    _logs()
    _main()
