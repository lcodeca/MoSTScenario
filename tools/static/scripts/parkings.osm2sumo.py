#!/usr/bin/env python3

""" Extract Parking Lots from OSM and import them in a SUMO network.

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

import argparse
import collections
import logging
import os
import pickle
import sys
from tqdm import tqdm

# """ Import SUMOLIB """
if 'SUMO_DEV_TOOLS' in os.environ:
    sys.path.append(os.environ['SUMO_DEV_TOOLS'])
    import traci
    import sumolib
    from sumolib.miscutils import euclidean

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
        prog='{}'.format(sys.argv[0]), usage='%(prog)s [options]',
        description='Extract parking lots from OSM for a SUMO network.')
    parser.add_argument(
        '--osm', type=str, dest='osmstruct', required=True,
        help='Pickle-OSM object.')
    parser.add_argument(
        '--net', type=str, dest='netstruct', required=True,
        help='Pickle-NET object.')
    parser.add_argument(
        '--cfg', type=str, dest='sumocfg', required=True,
        help='SUMO configuration file for TraCI.')
    parser.add_argument(
        '-o', type=str, dest='output', required=True,
        help='Prefix for the output files.')

    return parser.parse_args()

def _read_from_pickle(filename):
    """ Dump the object into a binary pickle file. """
    with open(filename, 'rb') as pickle_obj:
        obj = pickle.load(pickle_obj)
    return obj

class ParkingGeneration(object):
    """ Generate the SUMO additional file for parkings based on OSM. """

    _osm = None
    _net = None

    _sumocfg = None

    _parkings_edges_dict = dict()

    _osm_parkings = dict()
    _sumo_parkings = dict()
    _sumo_rerouters = dict()

    def __init__(self, osm_struct, sumo_network, sumocfg):

        self._osm = osm_struct
        self._net = sumo_network
        self._sumocfg = sumocfg

    def parkings_generation(self):
        """ Main finction to generate all the parking areas. """

        logging.info("Filtering OSM for parking lot..")
        self._filter_parkings()

        logging.info("Create parkings for SUMO..")
        self._parkings_to_edges()
        self._parkings_sumo()

        logging.info("Create parkings rerouters for SUMO..")
        self._rerouters_sumo()

    def save_parkings_to_file(self, filename):
        """ Save all the generated parkings to file. """
        self._save_parkings_to_file(filename)

    ## ---------------------------------------------------------------------------------------- ##
    ##                                   Parking Generation                                     ##
    ## ---------------------------------------------------------------------------------------- ##

    _BUFFER = 5.0
    _PARKING_LEN = 5.0
    _PARKING_ANGLE = 45

    def _filter_parkings(self):
        """ Retrieve all the parking lots from a OSM structure. """

        for node in tqdm(self._osm['node']):
            parking = False
            if 'tag' not in list(node.keys()):
                continue
            for tag in node['tag']:
                if self._is_parkings(tag):
                    parking = True
            if parking:
                x_coord, y_coord = self._net.convertLonLat2XY(node['lon'], node['lat'])
                node['x'] = x_coord
                node['y'] = y_coord
                self._osm_parkings[node['id']] = node

        logging.info('Gathered %d parking lots.', len(list(self._osm_parkings.keys())))

    _PARKING_DICT = {
        'amenity': ['parking', 'motorcycle_parking', 'parking_entrance'],
        'parking': ['surface', 'underground', 'multi-storey'],
        'name': ['underground parking']
    }

    def _is_parkings(self, tag):
        """ Check if the tag matches to one of the possible parking lots. """
        for key, value in self._PARKING_DICT.items():
            if tag['k'] == key and tag['v'] in value:
                return True
        return False

    def _parkings_to_edges(self):
        """ Associate the parking-id to and edge-id in a dictionary. """
        for parking in tqdm(self._osm_parkings.values()):
            self._parkings_edges_dict[parking['id']] = self._parking_to_edge(parking)

    def _parking_to_edge(self, parking):
        """ Given a parking lot, return the closest edge (lane_0) and all the other info
            required by SUMO for the parking areas:
            (edge_info, lane_info, location, parking.coords, parking.capacity)
        """

        edge_info = None
        lane_info = None
        dist_edge = sys.float_info.max # distance.euclidean(a,b)
        location = None

        for edge in self._net.getEdges():
            if not (edge.allows('passenger') and edge.allows('pedestrian')):
                continue

            if self._is_too_short(edge.getLength()):
                continue

            stop_lane = None
            try:
                stop_lane = edge.getLane(1)
            except IndexError:
                stop_lane = edge.getLane(0)

            if stop_lane:
                # compute all the distances
                counter = 0
                for point in stop_lane.getShape():
                    dist = euclidean((float(parking['x']), float(parking['y'])), point)
                    if dist < dist_edge:
                        edge_info = edge
                        lane_info = stop_lane
                        dist_edge = dist
                        location = counter
                    counter += 1

        if dist_edge > 50.0:
            logging.info("Alert: parking lots %s is %d meters from edge %s.",
                         parking['id'], dist_edge, edge_info.getID())

        return (edge_info, lane_info, location)

    def _is_too_short(self, edge_len):
        """ Check if the edge type is appropriate for a parking lot. """
        if edge_len < (self._PARKING_LEN + 2*self._BUFFER):
            return True
        return False

    def _get_capacity(self, parking_id):
        """ Retrieve parking lot capacity from OSM. """
        for tag in self._osm_parkings[parking_id]['tag']:
            if tag['k'] == 'capacity':
                return int(tag['v'])
        logging.fatal("Parking %s has no capacity tag.", parking_id)
        sys.exit()

    def _parkings_sumo(self):
        """ Compute the parking lots stops location for SUMO. """
        for plid, (_, lane, location) in self._parkings_edges_dict.items():
            new_pl = {
                'id': plid,
                'lane': lane.getID(),
                'start': - self._PARKING_LEN/2,
                'end': self._PARKING_LEN/2,
                'capacity': self._get_capacity(plid),
                'coords': (float(self._osm_parkings[plid]['x']),
                           float(self._osm_parkings[plid]['y'])),
            }

            _prec = None
            _counter = 0

            for point in lane.getShape():
                if _prec is None:
                    _prec = point
                    _counter += 1
                    continue
                if _counter <= location:
                    dist = euclidean(_prec, point)
                    new_pl['start'] += dist
                    new_pl['end'] += dist
                    _prec = point
                    _counter += 1
                else:
                    break

            if new_pl['start'] < self._BUFFER:
                new_pl['start'] = self._BUFFER
                new_pl['end'] = new_pl['start'] + self._PARKING_LEN

            if new_pl['end'] > lane.getLength() - self._BUFFER:
                new_pl['end'] = lane.getLength() - self._BUFFER
                new_pl['start'] = new_pl['end'] - self._PARKING_LEN

            self._sumo_parkings[plid] = new_pl

    ## ---------------------------------------------------------------------------------------- ##
    ##                                 Rerouters Generation                                     ##
    ## ---------------------------------------------------------------------------------------- ##


    def _rerouters_sumo(self):
        """ Compute the rerouters for each parking lot for SUMO. """

        parkings = {}
        for plid, (edge, _, _) in self._parkings_edges_dict.items():
            parkings[plid] = {
                'id': plid,
                'edge': edge.getID(),
                'coords': (float(self._osm_parkings[plid]['x']),
                           float(self._osm_parkings[plid]['y'])),
            }
        logging.debug('Selected %d parkings.', len(parkings.keys()))

        traci.start(['sumo', '-c', self._sumocfg])

        distances = collections.defaultdict(dict)
        for parking_a in tqdm(parkings.values()):
            for parking_b in parkings.values():
                if parking_a['id'] == parking_b['id']:
                    continue
                if (parking_a['id'] in distances.keys() and
                        parking_b['id'] in distances[parking_a['id']].keys()):
                    continue
                if parking_a['edge'] == parking_b['edge']:
                    continue

                route = None
                try:
                    route = traci.simulation.findRoute(
                        parking_a['edge'], parking_b['edge'], vtype='passenger')
                except traci.exceptions.TraCIException:
                    route = None

                cost = None
                if route and route.edges:
                    cost = route.travelTime
                else:
                    cost = None

                distances[parking_a['id']][parking_b['id']] = cost

        traci.close()

        ## select closest 3 - three
        for plid, dists in distances.items():
            list_of_dist = [tuple(reversed(x)) for x in dists.items() if x[1] is not None]
            list_of_dist = sorted(list_of_dist)
            rerouters = [plid]
            for time, parking in list_of_dist:
                if time < 600 and len(rerouters) < 10:
                        rerouters.append(parking)
                else:
                    break
            if not list_of_dist:
                logging.fatal('Parking %s has 0 neighbours!', plid)
            elif len(rerouters) == 1:
                ## adding one alternative anyway
                rerouters.append(list_of_dist[0][1])
                logging.critical("Parking %s has no neighbours in a 10' range, %s [%0.2f] added.",
                                  plid, list_of_dist[0][1], list_of_dist[0][1])


            self._sumo_rerouters[plid] = {
                'rid': plid,
                'edge': parkings[plid]['edge'],
                'rerouters': rerouters,
            }

        logging.debug('Computed %d rerouters.', len(self._sumo_rerouters.keys()))

    ## ---------------------------------------------------------------------------------------- ##
    ##                             Save SUMO Additionals to File                                ##
    ## ---------------------------------------------------------------------------------------- ##

    _ADDITIONALS_TPL = """<?xml version="1.0" encoding="UTF-8"?>

    <!--
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
    -->

    <additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd"> {content}
    </additional>
    """

    _PARKINGS_TPL = """
        <parkingArea id="{id}" lane="{lane}" startPos="{start}" endPos="{end}" roadsideCapacity="{capacity} length="{len}" angle="{angle}" friendlyPos="true"/>""" # pylint: disable=C0301

    _SIDE_PARKINGS_TPL = """
        <parkingArea id="{id}" lane="{lane}" startPos="{start}" endPos="{end}" roadsideCapacity="{capacity}" friendlyPos="true"/>""" # pylint: disable=C0301

    _AREA_PARKINGS_TPL = """
        <parkingArea id="{id}" lane="{lane}" startPos="{start}" endPos="{end}" friendlyPos="true"> {spaces}
        </parkingArea>"""

    _AREA_SPACE_TPL = """
            <space x="{x}" y="{y}" length="{len}" angle="{angle}"/>"""

    _REROUTER_TPL = """
        <rerouter id="{rid}" edges="{edges}">
            <interval begin="0.0" end="86400">
                <!-- in order of distance --> {parkings}
            </interval>
        </rerouter>"""
    _RR_PARKING_TPL = """
                <parkingAreaReroute id="{pid}" visible="{visible}"/>"""

    def _save_parkings_to_file(self, prefix):
        """ Save the parking lots into a SUMO XML additional file. """
        filename = '{}parkings.add.xml'.format(prefix)
        logging.info("Creation of %s", filename)
        with open(filename, 'w') as outfile:
            list_of_parkings = ''
            for parking in self._sumo_parkings.values():
                list_of_parkings += self._SIDE_PARKINGS_TPL.format(
                    id=parking['id'], lane=parking['lane'], start=parking['start'],
                    end=parking['end'], capacity=parking['capacity'])

            list_of_routers = ''
            for rerouter in self._sumo_rerouters.values():
                alternatives = ''
                for alt in rerouter['rerouters']:
                    _visibility = 'false'
                    if alt == rerouter['rid']:
                        _visibility = 'true'
                    if int(self._sumo_parkings[alt]['capacity']) >= 1000:
                        _visibility = 'true'
                    alternatives += self._RR_PARKING_TPL.format(pid=alt, visible=_visibility)
                list_of_routers += self._REROUTER_TPL.format(
                    rid=rerouter['rid'], edges=rerouter['edge'], parkings=alternatives)

            content = list_of_parkings + list_of_routers
            outfile.write(self._ADDITIONALS_TPL.format(content=content))
        logging.info("%s created.", filename)


def _main():
    """ Extract STOPS and LINES from OSM public transports and a SUMO network. """
    args = _args()
    logging.info('Loading from %s..', args.osmstruct)
    osm = _read_from_pickle(args.osmstruct)
    logging.info('Loading from %s..', args.netstruct)
    net = sumolib.net.readNet(args.netstruct)

    parkings = ParkingGeneration(osm, net, args.sumocfg)
    parkings.parkings_generation()
    parkings.save_parkings_to_file(args.output)

    logging.info('Done.')

if __name__ == "__main__":
    _logs()
    _main()
