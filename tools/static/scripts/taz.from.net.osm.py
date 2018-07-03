#!/usr/bin/python3

""" Extract TAZ from a SUMO netfile and OSM-like boundaries.

    Monaco SUMO Traffic (MoST) Scenario
    Copyright (C) 2018
    Lara CODECA

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import sys
import argparse
import pickle
import logging
import csv
import shapely.geometry as geometry
import gmplot
from tqdm import tqdm

# """ Import SUMOLIB """
if 'SUMO_DEV_TOOLS' in os.environ:
    sys.path.append(os.environ['SUMO_DEV_TOOLS'])
    import sumolib
else:
    sys.exit("Please declare environment variable 'SUMO_DEV_TOOLS'")

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
        usage='%(prog)s --net netfile --osm osmfile --taz filename --od filename',
        description='Extract TAZ from a SUMO netfile and OSM-like boundaries.')
    parser.add_argument(
        '--osm', type=str, dest='osmstruct', required=True,
        help='Pickle-OSM object.')
    parser.add_argument(
        '--net', type=str, dest='netfile', required=True,
        help='SUMO NET xml definition.')
    parser.add_argument(
        '--taz', type=str, dest='tazoutput', required=True,
        help='Prefix for the TAZ output file (XML).')
    parser.add_argument(
        '--od', type=str, dest='odoutput', required=True,
        help='Prefix for the OD output file (CSV).')
    parser.add_argument(
        '--poly', type=str, dest='polyoutput', required=True,
        help='Prefix for the POLY output files (CSV).')

    return parser.parse_args()

def _read_from_pickle(filename):
    """ Dump the object into a binary pickle file. """
    with open(filename, 'rb') as pickle_obj:
        obj = pickle.load(pickle_obj)
    return obj

class TAZandWeights(object):
    """ TAZ and weights extractor."""

    _osm = None
    _net = None

    _osm_boundaries = {
        'relation': {},
        'way': {},
        'node': {},
    }

    _taz = dict()

    def __init__(self, osm, net):

        self._osm = osm
        self._net = net

        logging.info('Filtering administrative boudaries from OSM..')
        self._filter_boundaries_from_osm()

        logging.info("Extracting TAZ from OSM-like boundaries.")
        self._build_taz_from_osm()

        logging.info("Computing TAZ areas...")
        self._taz_areas()

    def generate_taz(self):
        """ Generate TAZ by filtering edges,
            additionally computing TAZ weight through nodes and area. """

        logging.info("Filtering edges...")
        self._edges_filter()

        logging.info("Filtering nodes...")
        self._nodes_filter()

    def generate_buildings(self):
        """ Generate the buildings weight with edge and TAZ association."""

        logging.info("Filtering polygons...")
        self._polygons_filter()

    def save_sumo_taz(self, filename):
        """ Save TAZ to file. """
        logging.info("Creation of %s", filename)
        self._write_taz_file(filename)

    def save_taz_weigth(self, filename):
        """ Save weigths to file."""
        logging.info("Creation of %s", filename)
        self._write_csv_file(filename)

    def save_buildings_weigth(self, filename):
        """ Save building weights to file."""
        logging.info("Creation of %s", filename)
        self._write_poly_files(filename)

    def plot_taz_to_gmap(self, filename):
        """ Plot the boundaries using GoogleMapPlotter to html file."""

        logging.info("Plotting TAZ to Google Maps in file %s.", filename)

        # https://www.google.com/maps/@43.7373026,7.4272091,14z
        gmap = gmplot.GoogleMapPlotter(43.7373026, 7.4272091, 13)

        for _, value in self._taz.items():

            lons = [val.x for val in value['raw_points']]
            lats = [val.y for val in value['raw_points']]
            gmap.scatter(lats, lons, 'black', size=10, marker=False)

            lons, lats = value['convex_hull'].exterior.xy
            gmap.plot(lats, lons, 'blue', edge_width=2)

        gmap.draw(filename)


    ## ---------------------------------------------------------------------------------------- ##
    ##                                       OSM Filetrs                                        ##
    ## ---------------------------------------------------------------------------------------- ##

    @staticmethod
    def _is_boundary(tags):
        """ Check tags to find {'k': 'boundary', 'v': 'administrative'} """
        for tag in tags:
            if tag['k'] == 'boundary' and tag['v'] == 'administrative':
                return True
        return False

    def _filter_boundaries_from_osm(self):
        """ Extract boundaries from OSM-like structure. """

        for relation in tqdm(self._osm['relation']):
            if self._is_boundary(relation['tag']):
                self._osm_boundaries['relation'][relation['id']] = relation
                for member in relation['member']:
                    self._osm_boundaries[member['type']][member['ref']] = {}

        for way in tqdm(self._osm['way']):
            if way['id'] in self._osm_boundaries['way'].keys():
                self._osm_boundaries['way'][way['id']] = way
                for ndid in way['nd']:
                    self._osm_boundaries['node'][ndid['ref']] = {}

        for node in tqdm(self._osm['node']):
            if node['id'] in self._osm_boundaries['node'].keys():
                self._osm_boundaries['node'][node['id']] = node

        logging.info('Found %d administrative boundaries.',
                     len(self._osm_boundaries['relation'].keys()))

    ## ---------------------------------------------------------------------------------------- ##
    ##                                     TAZ generator                                        ##
    ## ---------------------------------------------------------------------------------------- ##

    def _build_taz_from_osm(self):
        """ Extract TAZ from OSM-like boundaries. """

        for id_boundary, boundary in tqdm(self._osm_boundaries['relation'].items()):
            list_of_nodes = []
            for member in boundary['member']:
                if member['type'] == 'way':
                    for node in self._osm_boundaries['way'][member['ref']]['nd']:
                        coord = self._osm_boundaries['node'][node['ref']]
                        list_of_nodes.append((float(coord['lon']), float(coord['lat'])))

            name = ''
            ref = ''
            for tag in boundary['tag']:
                if tag['k'] == 'name':
                    name = tag['v']
                elif tag['k'] == 'ref':
                    ref = tag['v']
            self._taz[id_boundary] = {
                'name': name,
                'ref': ref,
                'convex_hull': geometry.MultiPoint(list_of_nodes).convex_hull,
                'raw_points': geometry.MultiPoint(list_of_nodes),
                'edges': set(),
                'nodes': set(),
                'buildings': set(),
                'buildings_cumul_area': 0,
            }

    def _taz_areas(self):
        """ Compute the area in "shape" for each TAZ """

        for id_taz in tqdm(self._taz.keys()):
            x_coords, y_coords = self._taz[id_taz]['convex_hull'].exterior.coords.xy
            length = len(x_coords)
            poly = []
            for pos in range(length):
                x_coord, y_coord = self._net.convertLonLat2XY(x_coords[pos], y_coords[pos])
                poly.append((x_coord, y_coord))
            self._taz[id_taz]['area'] = geometry.Polygon(poly).area

    ## ---------------------------------------------------------------------------------------- ##
    ##                                     TAZ filler                                           ##
    ## ---------------------------------------------------------------------------------------- ##

    def _edges_filter(self):
        """ Sort edges to the right TAZ """
        for edge in tqdm(self._net.getEdges()):
            for coord in edge.getShape():
                lon, lat = self._net.convertXY2LonLat(coord[0], coord[1])
                for id_taz in list(self._taz.keys()):
                    if self._taz[id_taz]['convex_hull'].contains(geometry.Point(lon, lat)):
                        self._taz[id_taz]['edges'].add(edge.getID())

    def _nodes_filter(self):
        """ Sort nodes to the right TAZ """
        for node in tqdm(self._osm['node']):
            for id_taz in list(self._taz.keys()):
                if self._taz[id_taz]['convex_hull'].contains(
                        geometry.Point(float(node['lon']), float(node['lat']))):
                    self._taz[id_taz]['nodes'].add(node['id'])

    ## ---------------------------------------------------------------------------------------- ##
    ##                           TAZ filler: Buildings and weights                              ##
    ## ---------------------------------------------------------------------------------------- ##

    @staticmethod
    def _is_building(way):
        """ Return if a way is a building """
        for tag in way['tag']:
            if tag['k'] == 'building':
                return True
        return False

    @staticmethod
    def _get_centroid(way):
        """ Return lat lon of the centroid. """
        for tag in way['tag']:
            if tag['k'] == 'centroid':
                splitted = tag['v'].split(',')
                return splitted[0], splitted[1]
        return None

    @staticmethod
    def _get_approx_area(way):
        """ Return approximated area of the building. """
        for tag in way['tag']:
            if tag['k'] == 'approx_area':
                return float(tag['v'])
        return None

    def _building_to_edge(self, coords, id_taz):
        """ Given the coords of a building, return te closest edge """

        centroid = coords = (float(coords[0]), float(coords[1]))

        pedestrian_edge_info = None
        pedestrian_dist_edge = sys.float_info.max # distance.euclidean(a,b)

        generic_edge_info = None
        generic_dist_edge = sys.float_info.max # distance.euclidean(a,b)

        for id_edge in self._taz[id_taz]['edges']:
            edge = self._net.getEdge(id_edge)
            if edge.allows('rail'):
                continue
            _, _, dist = edge.getClosestLanePosDist(centroid)
            if edge.allows('passenger') and dist < generic_dist_edge:
                generic_edge_info = edge
                generic_dist_edge = dist
            if edge.allows('pedestrian') and dist < pedestrian_dist_edge:
                pedestrian_edge_info = edge
                pedestrian_dist_edge = dist

        if generic_edge_info and generic_dist_edge > 500.0:
            logging.info("A building entrance [passenger] is %d meters away.",
                         generic_dist_edge)
        if pedestrian_edge_info and pedestrian_dist_edge > 500.0:
            logging.info("A building entrance [pedestrian] is %d meters away.",
                         pedestrian_dist_edge)

        return generic_edge_info, pedestrian_edge_info

    def _polygons_filter(self):
        """ Sort polygons to the right TAZ based on centroid. """

        for way in tqdm(self._osm['way']):
            if not self._is_building(way):
                continue
            lat, lon = self._get_centroid(way)
            area = int(self._get_approx_area(way))
            for id_taz in list(self._taz.keys()):
                if self._taz[id_taz]['convex_hull'].contains(
                        geometry.Point(float(lon), float(lat))):
                    generic_edge, pedestrian_edge = self._building_to_edge(
                        self._net.convertLonLat2XY(lon, lat), id_taz)
                    if generic_edge or pedestrian_edge:
                        gen_id = None
                        ped_id = None
                        if generic_edge:
                            gen_id = generic_edge.getID()
                        if pedestrian_edge:
                            ped_id = pedestrian_edge.getID()
                        self._taz[id_taz]['buildings'].add((way['id'], area, gen_id, ped_id))
                        self._taz[id_taz]['buildings_cumul_area'] += area

    ## ---------------------------------------------------------------------------------------- ##
    ##                              Save results to files ...                                   ##
    ## ---------------------------------------------------------------------------------------- ##

    _TAZS = """
<tazs> {list_of_tazs}
</tazs>
"""

    _TAZ = """
    <!-- id="{taz_id}" name="{taz_name}" -->
    <taz id="{taz_id}" edges="{list_of_edges}"/>"""

    def _write_taz_file(self, filename):
        """ Write the SUMO file. """
        with open(filename, 'w') as outfile:
            string_of_tazs = ''
            for value in self._taz.values():
                string_of_edges = ''
                for edge in value['edges']:
                    string_of_edges += str(edge) + ' '
                string_of_edges = string_of_edges.strip()
                string_of_tazs += self._TAZ.format(
                    taz_id=value['ref'], taz_name=value['name'], #.encode('utf-8'),
                    list_of_edges=string_of_edges)
            outfile.write(self._TAZS.format(list_of_tazs=string_of_tazs))

    def _write_poly_files(self, prefix):
        """ Write the CSV file. """
        for value in self._taz.values():
            filename = '{}.{}.csv'.format(prefix, value['ref'])
            with open(filename, 'w') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=',')
                csvwriter.writerow(['TAZ', 'Poly', 'Area', 'Weight', 'GenEdge', 'PedEdge'])
                for poly, area, g_edge, p_edge in value['buildings']:
                    csvwriter.writerow([value['ref'], poly, area,
                                        area/value['buildings_cumul_area'], g_edge, p_edge])

    def _write_csv_file(self, filename):
        """ Write the CSV file. """
        with open(filename, 'w') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=',')
            csvwriter.writerow(['TAZ', 'Name', '#Nodes', 'Area'])
            for value in self._taz.values():
                csvwriter.writerow([value['ref'], value['name'], len(value['nodes']),
                                    value['area']])

def _main():
    """ TAZ extractor. """

    args = _args()
    logging.info('Loading from %s..', args.osmstruct)
    osm = _read_from_pickle(args.osmstruct)

    logging.info("Loading %s...", args.netfile)
    net = sumolib.net.readNet(args.netfile)

    ## ========================              PROFILER              ======================== ##
    # import cProfile, pstats, io
    # profiler = cProfile.Profile()
    # profiler.enable()
    ## ========================              PROFILER              ======================== ##

    taz_generator = TAZandWeights(osm, net)
    # taz_generator.plot_taz_to_gmap('MoSTScenario.TAZ.html')
    taz_generator.generate_taz()
    taz_generator.save_sumo_taz(args.tazoutput)
    taz_generator.save_taz_weigth(args.odoutput)
    taz_generator.generate_buildings()
    taz_generator.save_buildings_weigth(args.polyoutput)

    ## ========================              PROFILER              ======================== ##
    # profiler.disable()
    # results = io.StringIO()
    # pstats.Stats(profiler, stream=results).sort_stats('cumulative').print_stats(25)
    # print(results.getvalue())
    ## ========================              PROFILER              ======================== ##

    logging.info("Done.")


if __name__ == "__main__":
    _logs()
    _main()
