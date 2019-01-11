#!/usr/bin/python3

""" Extract STOPS and LINES from OSM public transports and a SUMO network.

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
import unidecode
from tqdm import tqdm

# """ Import SUMOLIB """
if 'SUMO_TOOLS' in os.environ:
    sys.path.append(os.environ['SUMO_TOOLS'])
    import sumolib
    from sumolib.miscutils import euclidean

else:
    sys.exit("Please declare environment variable 'SUMO_TOOLS'")

BUS_PLATFORM_LEN = 15.0
TRAIN_PLATFORM_LEN = 150.0

ADDITIONALS_TPL = """<?xml version="1.0" encoding="UTF-8"?>

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

STOPS_LONG_TPL = """
    <busStop id="{ptid}" name="{name}" lane="{lane}" startPos="{start}" endPos="{end}" lines="{lines}" friendlyPos="true"/> {comment}""" # pylint: disable=C0301

PTLINE_TPL = """
    <ptLine id="{lid}" name="{name}" line="{line}" type="{type}">{route}{stops}
    </ptLine> {comment}"""

ROUTE_TPL = """
        <route edges="{edges}"/>"""

STOPS_SHORT_TPL = """
        <busStop id="{ptid}" name="{name}"/>"""

STOPS_ACCESS_TPL = """
    <busStop id="{ptid}" name="{name}" lane="{lane}" startPos="{start}" endPos="{end}" lines="{lines}" friendlyPos="true"> {comment}
        <access lane="{access_lane}" pos="{access_pos}"/>
    </busStop>"""

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
        description='Extract STOPS and LINES from OSM public transports and a SUMO network.')
    parser.add_argument(
        '--osm', type=str, dest='osmstruct', required=True,
        help='Pickle-OSM object.')
    parser.add_argument(
        '--net', type=str, dest='netstruct', required=True,
        help='Pickle-NET object.')
    parser.add_argument(
        '-o', type=str, dest='output', required=True,
        help='Prefix for the output files.')

    return parser.parse_args()

def _read_from_pickle(filename):
    """ Dump the object into a binary pickle file. """
    with open(filename, 'rb') as pickle_obj:
        obj = pickle.load(pickle_obj)
    return obj

class PublicTransportsGenerator(object):
    """ Generates STOPS and LINES from OSM public transports and a SUMO network. """

    _osm = None
    _net = None

    _osm_bus_stops = dict()
    _osm_bus_lines = dict()
    _osm_train_stops = dict()
    _osm_train_lines = dict()

    _sumo_bus_stops = dict()
    _sumo_bus_lines = dict()
    _sumo_train_stops = dict()
    _sumo_train_lines = dict()

    def __init__(self, osm, net):
        """ Initialize the public transports generator. """

        self._osm = osm
        self._net = net

        logging.info("Filtering OSM for public transports stop..")
        self._filter_ptstops()

        logging.info("Filtering OSM for public transports lines..")
        self._filter_ptlines()

    def generate_buses(self):
        """ Generate the SUMO stops for buses. """

        logging.info("Create bus stops for SUMO..")
        bus_stops_to_edges = self._bus_stops_to_edges()
        self._bus_stops_for_sumo(bus_stops_to_edges)
        self._sumo_bus_stops, bus_stop_mapping = self._unify_sumo_ptstops(self._sumo_bus_stops)

        logging.info("Create bus lines for SUMO..")
        self._sumo_bus_lines, self._sumo_bus_stops = self._ptlines_sumo(
            self._osm_bus_lines, bus_stop_mapping, bus_stops_to_edges,
            self._osm_bus_stops, self._sumo_bus_stops)

    def generate_trains(self):
        """ Generate the SUMO stops for trains. """

        logging.info("Create trains stops for SUMO..")
        train_stops_to_edges = self._train_stops_to_edges()
        self._train_stops_for_sumo(train_stops_to_edges)
        self._sumo_train_stops, train_stop_mapping = self._unify_sumo_ptstops(
            self._sumo_train_stops)

        logging.info("Create train lines for SUMO..")
        self._sumo_train_lines, self._sumo_train_stops = self._ptlines_sumo(
            self._osm_train_lines, train_stop_mapping, train_stops_to_edges,
            self._osm_train_stops, self._sumo_train_stops)

    def save_buses_to_file(self, prefix):
        """ Save bus STOPS and LINES to SUMO files. """

        logging.info("Saving bus lines and stops to files..")
        self._save_ptstops_to_file(prefix, self._sumo_bus_stops, 'bus')
        self._save_ptlines_to_file(prefix, self._sumo_bus_lines, 'bus')

    def save_trains_to_file(self, prefix):
        """ Save train STOPS and LINES to SUMO files. """

        logging.info("Saving train lines and stops to files..")
        self._save_ptstops_to_file(prefix, self._sumo_train_stops, 'train')
        self._save_ptlines_to_file(prefix, self._sumo_train_lines, 'train')

    ## ---------------------------------------------------------------------------------------- ##
    ##                                       OSM Filters                                        ##
    ## ---------------------------------------------------------------------------------------- ##

    @staticmethod
    def _is_pt_train(tag):
        """ Check if the tag matches to one of the possible public transports. """
        pt_dict = {
            'railway': ['station'], #'subway_entrance'
            'route': ['train'],
        }
        for key, value in pt_dict.items():
            if tag['k'] == key and tag['v'] in value:
                return True
        return False

    @staticmethod
    def _is_pt_bus(tag):
        """ Check if the tag matches to one of the possible public transports. """
        pt_dict = {
            'bus': ['yes'],
            'highway': ['bus_stop'],
            'public_transport': ['stop_position', 'stop_area'],
            'amenity': ['bus_station'],
            'route': ['bus'],
            'type': ['public_transport'],
        }
        for key, value in pt_dict.items():
            if tag['k'] == key and tag['v'] in value:
                return True
        return False

    def _filter_ptstops(self):
        """ Retrieve all public transports from a OSM structure. """

        for node in tqdm(self._osm['node']):
            bus = False
            train = False
            if 'tag' not in list(node.keys()):
                continue
            for tag in node['tag']:
                if self._is_pt_bus(tag):
                    bus = True
                elif self._is_pt_train(tag):
                    train = True

            if bus or train:
                x_coord, y_coord = self._net.convertLonLat2XY(node['lon'], node['lat'])
                node['x'] = x_coord
                node['y'] = y_coord
                if bus:
                    node['pt_type'] = 'bus'
                    self._osm_bus_stops[node['id']] = node
                else:
                    node['pt_type'] = 'train'
                    self._osm_train_stops[node['id']] = node

        logging.info('Gathered %d bus stops.', len(list(self._osm_bus_stops.keys())))
        logging.info('Gathered %d train stops.', len(list(self._osm_train_stops.keys())))

    def _filter_ptlines(self):
        """ Retrieve all bus lines from a OSM structure. """

        for rel in tqdm(self._osm['relation']):
            bus = False
            train = False
            if 'tag' not in list(rel.keys()):
                continue
            for tag in rel['tag']:
                if self._is_pt_bus(tag):
                    bus = True
                elif self._is_pt_train(tag):
                    train = True
            if bus:
                rel['pt_type'] = 'bus'
                self._osm_bus_lines[rel['id']] = rel
            if train:
                rel['pt_type'] = 'train'
                self._osm_train_lines[rel['id']] = rel

        logging.info('Gathered %d bus lines.', len(list(self._osm_bus_lines.keys())))
        logging.info('Gathered %d train lines.', len(list(self._osm_train_lines.keys())))

    ## ---------------------------------------------------------------------------------------- ##
    ##                               SUMO ptransports generation                                ##
    ## ---------------------------------------------------------------------------------------- ##

    def _bus_stops_to_edges(self):
        """ Return the association stop-id to edge-id in a dictionary. """
        stops_to_edges = {}
        for stop in tqdm(self._osm_bus_stops.values()):
            stops_to_edges[stop['id']] = self._bus_stop_to_lane(stop)
        return stops_to_edges

    def _train_stops_to_edges(self):
        """ Return the association stop-id to edge-id in a dictionary. """
        stops_to_edges = {}
        for stop in tqdm(self._osm_train_stops.values()):
            stops_to_edges[stop['id']] = self._train_stop_to_lane(stop)
        return stops_to_edges

    def _bus_stop_to_lane(self, stop):
        """ Given the coords of a bus stop, return te closest lane_0. """

        lane_info = None
        dist_edge = sys.float_info.max # distance.euclidean(a,b)
        location = None

        for edge in self._net.getEdges():
            if not (edge.allows('bus') and edge.allows('pedestrian')):
                continue

            if edge.getLength() < (BUS_PLATFORM_LEN * 1.5):
                continue

            stop_lane = None
            try:
                stop_lane = edge.getLane(1)
            except IndexError:
                stop_lane = edge.getLane(0)

            # compute all the distances
            counter = 0
            for point in stop_lane.getShape():
                dist = euclidean((float(stop['x']), float(stop['y'])), point)
                if dist < dist_edge:
                    lane_info = stop_lane
                    dist_edge = dist
                    location = counter
                counter += 1

        if dist_edge > 50.0:
            logging.info("Alert: stop %s [%s] is %d meters from lane %s.",
                         stop['id'], stop['pt_type'], dist_edge, lane_info.getID())

        return (lane_info, location)

    def _train_stop_to_lane(self, stop):
        """ Given the coords of a stop, return te closest lane_0 """

        lane_info = None
        dist_edge = None
        location = None

        railway_lane_info = None
        railway_dist_edge = sys.float_info.max # distance.euclidean(a,b)
        railway_location = None

        street_lane_info = None
        street_dist_edge = sys.float_info.max # distance.euclidean(a,b)
        street_location = None

        for edge in self._net.getEdges():
            if edge.allows('rail'):
                if edge.getLength() < (TRAIN_PLATFORM_LEN * 1.5):
                    continue
                lane_info = railway_lane_info
                dist_edge = railway_dist_edge
                location = railway_location
            elif edge.allows('pedestrian'):
                lane_info = street_lane_info
                dist_edge = street_dist_edge
                location = street_location
            else:
                continue

            stop_lane = None
            try:
                stop_lane = edge.getLane(1)
            except IndexError:
                stop_lane = edge.getLane(0)

            # compute all the distances
            counter = 0
            for point in stop_lane.getShape():
                dist = euclidean((float(stop['x']), float(stop['y'])), point)
                if dist < dist_edge:
                    lane_info = stop_lane
                    dist_edge = dist
                    location = counter
                counter += 1

            if edge.allows('rail'):
                railway_lane_info = lane_info
                railway_dist_edge = dist_edge
                railway_location = location
            else:
                street_lane_info = lane_info
                street_dist_edge = dist_edge
                street_location = location

        railway_access = (railway_lane_info, railway_location)

        if railway_dist_edge > 50.0:
            logging.info("Alert: stop %s [%s] is %d meters from lane %s.",
                         stop['id'], stop['pt_type'], railway_dist_edge, railway_lane_info.getID())

        street_access = (street_lane_info, street_location)
        logging.info("Alert: Street access for stop %s [%s] is %d meters from edge %s.",
                     stop['id'], stop['pt_type'], street_dist_edge, street_lane_info.getID())

        if street_dist_edge > 500.0:
            street_access = None
            logging.info(
                "Alert: Street access for stop %s too far and it will be removed.", stop['id'])

        return (railway_access, street_access)

    @staticmethod
    def _get_stop_name(stop):
        """ Get the stop name, if possible."""
        for tag in stop['tag']:
            if tag['k'] == 'name':
                return unidecode.unidecode(tag['v'])
        return ''

    def _bus_stops_for_sumo(self, stops_to_edges):
        """ Compute the bus stops location for SUMO. """
        for ptid, (lane, location) in tqdm(stops_to_edges.items()):
            new_pt = {
                'id': ptid,
                'name': self._get_stop_name(self._osm_bus_stops[ptid]),
                'pt_type': self._osm_bus_stops[ptid]['pt_type'],
                'lane': lane.getID(),
            }

            _start = - BUS_PLATFORM_LEN/2
            _end = BUS_PLATFORM_LEN/2

            _prec = None
            _counter = 0

            for point in lane.getShape():
                if _prec is None:
                    _prec = point
                    _counter += 1
                    continue
                if _counter <= location:
                    dist = euclidean(_prec, point)
                    _start += dist
                    _end += dist
                    _prec = point
                    _counter += 1
                else:
                    break

            if _start < 5.0:
                _start = 5.0
                _end = _start + BUS_PLATFORM_LEN
            if _end > lane.getLength() - 5.0:
                _end = lane.getLength() - 5.0
                _start = _end - BUS_PLATFORM_LEN

            new_pt['start'] = _start
            new_pt['end'] = _end

            self._sumo_bus_stops[ptid] = new_pt

    def _train_stops_for_sumo(self, stops_to_edges):
        """ Compute the train stops location for SUMO. """
        for ptid, values in tqdm(stops_to_edges.items()):

            railway_access, street_access = values

            railway_lane_info, railway_location = railway_access

            new_pt = {
                'id': ptid,
                'name': self._get_stop_name(self._osm_train_stops[ptid]),
                'pt_type': self._osm_train_stops[ptid]['pt_type'],
                'lane': railway_lane_info.getID(),
            }

            ### Compute the position for the railway
            _start = - TRAIN_PLATFORM_LEN/2
            _end = TRAIN_PLATFORM_LEN/2

            _prec = None
            _counter = 0
            for point in railway_lane_info.getShape():
                if _prec is None:
                    _prec = point
                    _counter += 1
                    continue
                if _counter <= railway_location:
                    dist = euclidean(_prec, point)
                    _start += dist
                    _end += dist
                    _prec = point
                    _counter += 1
                else:
                    break

            if _start < 5.0:
                _start = 5.0
                _end = _start + TRAIN_PLATFORM_LEN
            if _end > railway_lane_info.getLength() - 5.0:
                _end = railway_lane_info.getLength() - 5.0
                _start = _end - TRAIN_PLATFORM_LEN
            if railway_lane_info.getLength() <= TRAIN_PLATFORM_LEN:
                _start = 5.0
                _end = railway_lane_info.getLength() - 5.0

            new_pt['start'] = _start
            new_pt['end'] = _end

            street_lane_info, street_location = (None, None)

            if street_access:
                street_lane_info, street_location = street_access
                new_pt['access'] = {'lane': street_lane_info.getID()}

                ### Compute the position for the street
                _start = - TRAIN_PLATFORM_LEN/2
                _end = TRAIN_PLATFORM_LEN/2

                _prec = None
                _counter = 0
                for point in street_lane_info.getShape():
                    if _prec is None:
                        _prec = point
                        _counter += 1
                        continue
                    if _counter <= street_location:
                        dist = euclidean(_prec, point)
                        _start += dist
                        _end += dist
                        _prec = point
                        _counter += 1
                    else:
                        break

                if _start < 5.0:
                    _start = 5.0
                    _end = _start + TRAIN_PLATFORM_LEN
                if _end > street_lane_info.getLength() - 5.0:
                    _end = street_lane_info.getLength() - 5.0
                    _start = _end - TRAIN_PLATFORM_LEN
                if street_lane_info.getLength() <= TRAIN_PLATFORM_LEN:
                    _start = 5.0
                    _end = street_lane_info.getLength() - 5.0

                new_pt['access']['pos'] = (_start + _end) / 2

            self._sumo_train_stops[ptid] = new_pt

    @staticmethod
    def _unify_sumo_ptstops(stops):
        """ Merge and discard overlapping ptstops. """

        stop_mapping = {}

        stops_to_merge = collections.defaultdict(list)
        for stop in stops.values():
            new_name = '{}_{}_{}'.format(stop['lane'], stop['start'], stop['end'])
            stops_to_merge[new_name].append(stop['id'])

        merged_stops = {}
        for ids in stops_to_merge.values():
            merged_id = ''
            merged_names = []
            for sid in ids:
                stop_mapping[sid] = ids[0]
                merged_id += sid + ' '
                if stops[sid]['name']:
                    if stops[sid]['name'] not in merged_names:
                        merged_names.append(stops[sid]['name'])
            merged_stop = stops[ids[0]]
            merged_stop['name'] = ' | '.join(merged_names)
            merged_stop['merged'] = merged_id.strip()
            merged_stop['lines'] = []
            merged_stops[ids[0]] = merged_stop
            if len(ids) > 1:
                logging.info('Merged stops %s [%s].', merged_stop['merged'], merged_stop['name'])

        return merged_stops, stop_mapping

    @staticmethod
    def _get_line_name(line):
        """ Get the stop name, if possible."""
        for tag in line:
            if tag['k'] == 'name':
                return unidecode.unidecode(tag['v'])
        return ''

    @staticmethod
    def _get_line_number(line):
        """ Get the stop name, if possible."""
        for tag in line:
            if tag['k'] == 'ref':
                return tag['v']
        return ''

    def _ptlines_sumo(self, lines, mapping, stops_to_edges, stops, sumo_stops):
        """  """
        sumo_lines = {}
        for line_id, line in lines.items():
            new_line = {
                'id': line_id,
                'name': self._get_line_name(line['tag']),
                'line': self._get_line_number(line['tag']),
                'type': line['pt_type'],
                'route': [],
                'stops': [],
                'substitutions': [],
            }
            for member in line['member']:
                if member['ref'] in list(mapping.keys()):
                    if line['pt_type'] == 'train':
                        new_line['route'].append(stops_to_edges[member['ref']][0][0].getID())
                    else:
                        new_line['route'].append(stops_to_edges[member['ref']][0].getID())
                    new_line['stops'].append((mapping[member['ref']],
                                              self._get_stop_name(stops[mapping[member['ref']]])))
                    sumo_stops[mapping[member['ref']]]['lines'].append(new_line['line'])
                    if mapping[member['ref']] != member['ref']:
                        new_line['substitutions'].append('{}:{}'.format(member['ref'],
                                                                        mapping[member['ref']]))
            sumo_lines[line_id] = new_line
        return sumo_lines, sumo_stops

    ## ---------------------------------------------------------------------------------------- ##
    ##                             Save SUMO Additionals to File                                ##
    ## ---------------------------------------------------------------------------------------- #

    @staticmethod
    def _save_ptstops_to_file(prefix, stops, pt_type):
        """ Save the bus stops into a SUMO XML additional file. """
        filename = '{}{}stops.add.xml'.format(prefix, pt_type)
        logging.info("Creation of %s", filename)
        with open(filename, 'w') as outfile:
            list_of_stops = ''
            for stop in stops.values():
                comment = ''
                if 'merged' in stop.keys():
                    comment = '<!-- {} -->'.format(stop['merged'])
                if not stop['name']:
                    stop['name'] = stop['id']
                list_of_lines = ' '.join(stop['lines'])

                if 'access' in stop.keys():
                    list_of_stops += STOPS_ACCESS_TPL.format(
                        ptid=stop['id'], name=stop['name'], lines=list_of_lines, comment=comment,
                        lane=stop['lane'], start=stop['start'], end=stop['end'],
                        access_lane=stop['access']['lane'], access_pos=stop['access']['pos'])
                else:
                    list_of_stops += STOPS_LONG_TPL.format(
                        ptid=stop['id'], name=stop['name'], lines=list_of_lines, comment=comment,
                        lane=stop['lane'], start=stop['start'], end=stop['end'])


            outfile.write(ADDITIONALS_TPL.format(content=list_of_stops))
        logging.info("%s created.", filename)

    @staticmethod
    def _save_ptlines_to_file(prefix, lines, pt_type):
        """ Save the PT Lines into a SUMO XML additional file. """
        filename = '{}{}lines.add.xml'.format(prefix, pt_type)
        logging.info("Creation of %s", filename)
        with open(filename, 'w') as outfile:
            list_of_lines = ''
            for line in lines.values():
                edges = ''
                for edge in line['route']:
                    edges += edge + ' '
                edges = edges.strip()
                list_of_stops = ''
                for stop_id, stop_name in line['stops']:
                    if stop_name:
                        list_of_stops += STOPS_SHORT_TPL.format(ptid=stop_id, name=stop_name)
                    else:
                        list_of_stops += STOPS_SHORT_TPL.format(ptid=stop_id, name=stop_id)
                route = ROUTE_TPL.format(edges=edges)
                comment = ''
                substitutions = ' - '.join(line['substitutions'])
                if substitutions:
                    comment = '<!-- {} -->'.format(substitutions)
                list_of_lines += PTLINE_TPL.format(
                    lid=line['id'], name=line['name'], line=line['line'], type=line['type'],
                    route=route, stops=list_of_stops, comment=comment)

            outfile.write(ADDITIONALS_TPL.format(content=list_of_lines))
        logging.info("%s created.", filename)

def _main():
    """ Extract STOPS and LINES from OSM public transports and a SUMO network. """

    args = _args()
    logging.info('Loading from %s..', args.osmstruct)
    osm = _read_from_pickle(args.osmstruct)
    logging.info('Loading from %s..', args.netstruct)
    net = sumolib.net.readNet(args.netstruct)

    ptransports = PublicTransportsGenerator(osm, net)
    ptransports.generate_buses()
    ptransports.save_buses_to_file(args.output)
    ptransports.generate_trains()
    ptransports.save_trains_to_file(args.output)

    logging.info('Done.')

if __name__ == "__main__":
    _logs()
    _main()
