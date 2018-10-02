#!/usr/bin/env python3

""" Person Trip Activity-based Mobility Generation with PoIs and TAZ.

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
import csv
import json
import logging
import os
import xml.etree.ElementTree
import random
import sys
import cProfile
import pstats
import io
import numpy
from tqdm import tqdm

# """ Import SUMOLIB """
if 'SUMO_DEV_TOOLS' in os.environ:
    sys.path.append(os.environ['SUMO_DEV_TOOLS'])
    import sumolib
    import traci
    import traci.constants as tc
else:
    sys.exit("Please declare environment variable 'SUMO_DEV_TOOLS'")

BASE_DIR = None
# """ Import SUMOLIB """
if 'MOST_SCENARIO' in os.environ:
    BASE_DIR = os.environ['MOST_SCENARIO']
else:
    sys.exit("Please declare environment variable 'MOST_SCENARIO'")

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
    """
    Argument Parser
    ret: parsed arguments.
    """
    parser = argparse.ArgumentParser(
        prog='{}'.format(sys.argv[0]),
        usage='%(prog)s -c configuration.json',
        description='Generate trips based on a symplified acrtivity-based '
                    'mobility generation based on PoIs and TAZ.')
    parser.add_argument(
        '-c', type=str, dest='config', required=True,
        help='JSON configuration file.')
    return parser.parse_args()

def _load_configurations(filename):
    """
    Load JSON configuration file in a dict.
        :param filename: name of the JSON file containing the configuarions.
    """
    return json.loads(open(filename).read())

class MobilityGenerator(object):
    """ Generates intermodal mobility for SUMO starting from a synthetic population. """

    _conf = None
    _profiling = None

    _sumo_network = None
    _sumo_parkings = collections.defaultdict(list)
    _parking_cache = dict()
    _parking_position = dict()
    _taz_weights = dict()
    _buildings_by_taz = dict()
    _edges_by_taz = dict()

    _blacklisted_edges = set()

    _all_trips = collections.defaultdict(dict)

    def __init__(self, conf, profiling=False):
        """
         Initialize the synthetic population.
            :param conf: distionary with the configurations
            :param profiling=False: enable cProfile
        """

        self._conf = conf
        self._profiling = profiling

        logging.info('Starting TraCI with file %s.', conf['sumocfg'])
        sumocfg = '{}/{}'.format(BASE_DIR, conf['sumocfg'])
        traci.start(['sumo', '-c', sumocfg])

        logging.info('Loading SUMO net file %s%s', BASE_DIR, conf['SUMOnetFile'])
        self._sumo_network = sumolib.net.readNet(
            '{}/{}'.format(BASE_DIR, conf['SUMOnetFile']))

        logging.info('Loading SUMO parking lots from file %s%s',
                     BASE_DIR, conf['SUMOadditionals']['parkings'])
        self._load_parkings('{}/{}'.format(BASE_DIR, conf['SUMOadditionals']['parkings']))

        logging.info('Loading TAZ weights from %s%s',
                     BASE_DIR, conf['population']['tazWeights'])
        self._load_weights_from_csv(
            '{}/{}'.format(BASE_DIR, conf['population']['tazWeights']))

        logging.info('Loading buildings weights from %s%s',
                     BASE_DIR, conf['population']['buildingsWeight'])
        self._load_buildings_weight_from_csv_dir(
            '{}/{}'.format(BASE_DIR, conf['population']['buildingsWeight']))

        logging.info('Loading edges in each TAZ from %s%s',
                     BASE_DIR, conf['population']['tazDefinition'])
        self._load_edges_from_taz(
            '{}/{}'.format(BASE_DIR, conf['population']['tazDefinition']))

        logging.info('Computing the number of entities for each vType..')
        self._compute_vehicles_per_type()

    def mobility_generation(self):
        """ Generate the mobility for the synthetic population. """
        logging.info('Generating trips for each vType..')
        self._compute_trips_per_type()

    def save_mobility(self):
        """ Save the generated trips to files. """
        logging.info('Saving trips files..')
        self._saving_trips_to_files()

    @staticmethod
    def close_traci():
        """ Artefact to close TraCI properly. """
        logging.info('Closing TraCI.')
        traci.close()

    ## ---------------------------------------------------------------------------------------- ##
    ##                                          Loaders                                         ##
    ## ---------------------------------------------------------------------------------------- ##

    def _load_parkings(self, filename):
        """ Load parkings ids from XML file. """
        xml_tree = xml.etree.ElementTree.parse(filename).getroot()
        for child in xml_tree:
            if (child.tag == 'parkingArea' and
                    child.attrib['id'] in self._conf['intermodalOptions']['parkingAreaWhitelist']):
                edge = child.attrib['lane'].split('_')[0]
                position = float(child.attrib['startPos']) + 2.5
                self._sumo_parkings[edge].append(child.attrib['id'])
                self._parking_position[child.attrib['id']] = position

    def _load_weights_from_csv(self, filename):
        """ Load the TAZ weight from a CSV file. """
        with open(filename, 'r') as csvfile:
            weightreader = csv.reader(csvfile)
            header = None
            for row in weightreader:
                if not header:
                    header = row
                else:
                    self._taz_weights[int(row[0])] = {
                        header[0]: int(row[0]),
                        header[1]: row[1],
                        header[2]: int(row[2]),
                        header[3]: float(row[3]),
                        'weight': (int(row[2])/float(row[3])),
                    }

    def _load_buildings_weight_from_csv_dir(self, directory):
        """ Load the buildings weight from multiple CSV files. """

        allfiles = [os.path.join(directory, f)
                    for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        for filename in sorted(allfiles):
            logging.debug('Loding %s', filename)
            with open(filename, 'r') as csvfile:
                weightreader = csv.reader(csvfile)
                header = None
                taz = None
                buildings = []
                for row in weightreader:
                    if not header:
                        header = row
                    else:
                        taz = row[0]
                        buildings.append((float(row[3]),    # weight
                                          row[4],           # generic edge
                                          row[5]))          # pedestrian edge

                if len(buildings) < 10:
                    logging.debug('Dropping %s, only %d buildings found.', filename, len(buildings))
                    continue

                weighted_buildings = []
                cum_sum = 0.0
                for weight, g_edge, p_edge in sorted(buildings):
                    cum_sum += weight
                    weighted_buildings.append((cum_sum, g_edge, p_edge, weight))
                self._buildings_by_taz[taz] = weighted_buildings

    def _load_edges_from_taz(self, filename):
        """ Load edges from the TAZ file. """
        xml_tree = xml.etree.ElementTree.parse(filename).getroot()
        for child in xml_tree:
            if child.tag == 'taz':
                self._edges_by_taz[child.attrib['id']] = child.attrib['edges'].split(' ')

    ## ---------------------------------------------------------------------------------------- ##
    ##                                Mobility Generation                                       ##
    ## ---------------------------------------------------------------------------------------- ##

    def _compute_vehicles_per_type(self):
        """
        Compute the absolute number of trip that are going to be created
        for each vechile type, given a population.
        """
        logging.info('Population: %d', self._conf['population']['entities'])

        for v_type in self._conf['distribution'].keys():
            self._conf['distribution'][v_type]['tot'] = int(
                self._conf['population']['entities'] * self._conf['distribution'][v_type]['perc'])
            logging.info('\t %s: %d', v_type, self._conf['distribution'][v_type]['tot'])

    def _normal_departure_time(self):
        """ Return the departure time, comuted using a normal distribution. """
        departure = int(numpy.random.normal(loc=self._conf['peak']['mean'],
                                            scale=self._conf['peak']['std'], size=1))
        while (departure < self._conf['interval']['begin'] or
               departure > self._conf['interval']['end']):
            departure = int(numpy.random.normal(loc=self._conf['peak']['mean'],
                                                scale=self._conf['peak']['std'], size=1))
        return departure

    def _compute_trips_per_type(self):
        """ Compute the trips for the synthetic population for each vType. """

        for v_type in self._conf['distribution'].keys():
            total = 0
            for key, area in  self._conf['distribution'][v_type]['composition'].items():
                vehicles = int(self._conf['distribution'][v_type]['tot'] * area['perc'])
                logging.info('[%s] Computing %d trips from %s to %s ... ',
                             v_type, vehicles, area['from'], area['to'])

                if self._profiling:
                    _pr = cProfile.Profile()
                    _pr.enable()

                for veh_id in tqdm(range(vehicles)):
                    ## Generating departure time
                    _depart = self._normal_departure_time()
                    if _depart not in self._all_trips[v_type].keys():
                        self._all_trips[v_type][_depart] = []

                    ## Trip generation

                    # Parking lot at the end of the trip.
                    with_parking = 'withParking' in area.keys() and area['withParking']

                    # Modes for intermodal trips.
                    modes = None
                    if 'modes' in area.keys() and area['modes']:
                        modes = area['modes']

                    _from = None
                    _to = None

                    # (Intermodal) trip
                    _from, _to, _mode, _stages = self._find_allowed_pair_traci(
                        v_type, modes, _depart,
                        self._conf['taz'][area['from']], self._conf['taz'][area['to']],
                        with_parking)
                    modes = _mode

                    # Fixing the parking lots stops from the configuration.
                    parking_id = None
                    if with_parking:
                        parking_id = self._has_parking_lot(_to)
                    if not parking_id:
                        with_parking = False

                    # Trip creation
                    self._all_trips[v_type][_depart].append({
                        'id': '{}_{}_{}'.format(v_type, key, veh_id),
                        'depart': _depart,
                        'from': _from,
                        'to': _to,
                        'type': v_type,
                        'mode': modes,
                        'withParking': with_parking,
                        'PLid': parking_id,
                        'stages': _stages
                        })
                    total += 1

                if self._profiling:
                    _pr.disable()
                    _s = io.StringIO()
                    _ps = pstats.Stats(_pr, stream=_s).sort_stats('cumulative')
                    _ps.print_stats(10)
                    print(_s.getvalue())
                    input("Press any key to continue..")

            logging.info('Generated %d trips for %s.', total, v_type)

    ## ---- PARKING AREAS: location and selection ---- ##

    def _get_parking_id(self, edge):
        """ Randomly select one of the parkings. """
        if not self._sumo_parkings[edge]:
            return None
        pos = random.randint(0, len(self._sumo_parkings[edge]) - 1)
        return self._sumo_parkings[edge][pos]

    def _has_parking_lot(self, edge):
        """ Retrieve the parking area ID. """
        parking_id = None
        if edge in self._sumo_parkings.keys():
            parking_id = self._get_parking_id(edge)
        return parking_id

    def _check_parkings_cache(self, edge):
        """ Check among the previously computed results of _find_closest_parking """
        if edge in self._parking_cache.keys():
            return self._parking_cache[edge]
        return None

    def _find_closest_parking(self, edge):
        """ Given and edge, find the closest parking area. """
        distance = sys.float_info.max

        ret = self._check_parkings_cache(edge)
        if ret:
            return ret

        for p_edge, parkings in self._sumo_parkings.items():
            _is_allowed = False
            for parking in parkings:
                if parking in self._conf['intermodalOptions']['parkingAreaWhitelist']:
                    _is_allowed = True
                    break
            if not _is_allowed:
                continue

            try:
                route = traci.simulation.findIntermodalRoute(
                    p_edge, edge, walkFactor=.9, pType="pedestrian")
            except traci.exceptions.TraCIException:
                logging.error('_find_closest_parking: findIntermodalRoute %s -> %s failed.',
                              p_edge, edge)
                route = None

            if route:
                cost = self._cost_from_route(route)
                if distance > cost:
                    distance = cost
                    ret = p_edge, route

        if ret:
            self._parking_cache[edge] = ret
            return ret

        logging.fatal('Edge %s is not reachable from any parking lot.', edge)
        self._blacklisted_edges.add(edge)
        return None, None

    ## ----     Functions for _compute_trips_per_type: _find_allowed_pair_traci            ---- ##

    def _find_allowed_pair_traci(self, v_type, modes, departure, from_area, to_area, with_parking):
        """ Return an origin ad an allowed destination, with mode and route stages.

            findRoute(self, fromEdge, toEdge, vType="", depart=-1., routingMode=0)

            findIntermodalRoute(
                self, fromEdge, toEdge, modes="", depart=-1., routingMode=0, speed=-1.,
                walkFactor=-1., departPos=-1., arrivalPos=-1., departPosLat=-1.,
                pType="", vType="", destStop=""):
        """

        counter = 0
        _is_intermodal = False
        selected_mode = None
        selected_route = None
        if modes:
            _is_intermodal = True

        if _is_intermodal:
            od_found = False
            while not od_found:
                ## Origin and Destination Selection
                from_edge, to_edge = self._select_pair(from_area, to_area, True)

                ## Evaluate all the possible (intermodal) routes
                solutions = self._find_intermodal_route(
                    from_edge, to_edge, modes, departure, with_parking)
                if solutions:
                    winner = sorted(solutions)[0] # let the winner win
                    selected_mode = winner[1]
                    selected_route = winner[2]
                    od_found = True

                counter += 1
                if counter % 10 == 0:
                    logging.debug('%d pairs done, still looking for the good one..', counter)

        else:
            route = None
            while not self._is_valid_route(None, route):
                ## Origin and Destination Selection
                from_edge, to_edge = self._select_pair(from_area, to_area)
                try:
                    route = traci.simulation.findRoute(from_edge, to_edge, vType=v_type)
                except traci.exceptions.TraCIException:
                    logging.debug('_find_allowed_pair_traci: findRoute FAILED.')
                    route = None

                counter += 1
                if counter % 10 == 0:
                    logging.debug('%d pairs done, still looking for the good one..', counter)

            selected_mode = v_type
            selected_route = route

        if counter >= 10:
            logging.debug('It required %d iterations to find a valid pair.', counter)
        return from_edge, to_edge, selected_mode, selected_route

    def _find_intermodal_route(self, from_edge, to_edge, modes, departure, with_parking):
        """ Evaluate all the possible (intermodal) routes. """
        solutions = list()
        for mode, weight in modes:
            _last_mile = None
            _modes, _ptype, _vtype = self._get_mode_parameters(mode)

            if with_parking and _vtype in self._conf['intermodalOptions']['vehicleAllowedParking']:
                ## Find the closest parking area
                p_edge, _last_mile = self._find_closest_parking(to_edge)
                if _last_mile:
                    try:
                        route = traci.simulation.findIntermodalRoute(
                            from_edge, p_edge, depart=departure, walkFactor=.9, # speed=1.0
                            modes=_modes, pType=_ptype, vType=_vtype)
                    except traci.exceptions.TraCIException:
                        logging.error(
                            '_find_intermodal_route: findIntermodalRoute w parking FAILED.')
                        route = None
                    if (self._is_valid_route(_modes, route) and
                            route[-1].stageType == tc.STAGE_DRIVING):
                        route[-1] = route[-1]._replace(destStop=self._get_parking_id(p_edge))
                        route.extend(_last_mile)
                        solutions.append((self._cost_from_route(route) * weight, mode, route))
            else:
                try:
                    route = traci.simulation.findIntermodalRoute(
                        from_edge, to_edge, depart=departure, walkFactor=.9, # speed=1.0
                        modes=_modes, pType=_ptype, vType=_vtype)
                except traci.exceptions.TraCIException:
                    logging.error(
                        '_find_intermodal_route: findIntermodalRoute wout parking FAILED.')
                    route = None

                if self._is_valid_route(_modes, route):
                    solutions.append((self._cost_from_route(route) * weight, mode, route))

        return solutions

    ## ---- PAIR SELECTION: origin - destination - mode ---- ##

    def _select_pair(self, from_area, to_area, pedestrian=False):
        """ Randomly select one pair, chosing between buildings and TAZ. """
        from_taz = str(self._select_taz_from_weighted_area(from_area))
        to_taz = str(self._select_taz_from_weighted_area(to_area))

        if from_taz in self._buildings_by_taz.keys() and to_taz in self._buildings_by_taz.keys():
            return self._select_pair_from_taz_wbuildings(
                self._buildings_by_taz[from_taz][:], self._buildings_by_taz[to_taz][:], pedestrian)
        return self._select_pair_from_taz(
            self._edges_by_taz[from_taz][:], self._edges_by_taz[to_taz][:])

    def _select_taz_from_weighted_area(self, area):
        """ Select a TAZ from an area using its weight. """
        selection = random.uniform(0, 1)
        total_weight = sum([self._taz_weights[taz]['weight'] for taz in area])
        cumulative = 0.0
        for taz in area:
            cumulative += self._taz_weights[taz]['weight'] / total_weight
            if selection <= cumulative:
                return taz
        return None # this is matematically impossible,
                    # if this happens, there is a mistake in the weights.

    def _valid_pair(self, from_edge, to_edge):
        """ This is just to avoid a HUGE while condition.
            sumolib.net.edge.is_fringe()
        """
        from_edge_sumo = self._sumo_network.getEdge(from_edge)
        to_edge_sumo = self._sumo_network.getEdge(to_edge)

        if from_edge_sumo.is_fringe(from_edge_sumo.getOutgoing()):
            return False
        if to_edge_sumo.is_fringe(to_edge_sumo.getIncoming()):
            return False
        if from_edge == to_edge:
            return False
        if to_edge in self._blacklisted_edges:
            return False
        if not to_edge_sumo.allows('pedestrian'):
            return False
        return True

    def _select_pair_from_taz(self, from_taz, to_taz):
        """ Randomly select one pair from a TAZ.
            Important: from_taz and to_taz MUST be passed by copy.
            Note: sumonet.getEdge(from_edge).allows(v_type) does not support distributions.
        """

        from_edge = from_taz.pop(random.randint(0, len(from_taz) - 1))
        to_edge = to_taz.pop(random.randint(0, len(to_taz) - 1))

        _to = False
        while not self._valid_pair(from_edge, to_edge) and from_taz and to_taz:
            if not self._sumo_network.getEdge(to_edge).allows('pedestrian') or _to:
                to_edge = to_taz.pop(random.randint(0, len(to_taz) - 1))
                _to = False
            else:
                from_edge = from_taz.pop(random.randint(0, len(from_taz) - 1))
                _to = True

        return from_edge, to_edge

    def _select_pair_from_taz_wbuildings(self, from_buildings, to_buildings, pedestrian):
        """ Randomly select one pair from a TAZ.
            Important: from_buildings and to_buildings MUST be passed by copy.
            Note: sumonet.getEdge(from_edge).allows(v_type) does not support distributions.
        """

        from_edge, _index = self._get_weighted_edge(from_buildings, random.random(), False)
        del from_buildings[_index]
        to_edge, _index = self._get_weighted_edge(to_buildings, random.random(), pedestrian)
        del to_buildings[_index]

        _to = True
        while not self._valid_pair(from_edge, to_edge) and from_buildings and to_buildings:
            if not self._sumo_network.getEdge(to_edge).allows('pedestrian') or _to:
                to_edge, _index = self._get_weighted_edge(to_buildings, random.random(), pedestrian)
                del to_buildings[_index]
                _to = False
            else:
                from_edge, _index = self._get_weighted_edge(from_buildings, random.random(), False)
                del from_buildings[_index]
                _to = True

        return from_edge, to_edge

    @staticmethod
    def _get_weighted_edge(edges, double, pedestrian):
        """ Return an edge and its position using the cumulative sum of the weigths in the area. """
        pos = -1
        ret = None
        for cum_sum, g_edge, p_edge, _ in edges:
            if ret and cum_sum > double:
                return ret, pos
            if pedestrian and p_edge:
                ret = p_edge
            elif not pedestrian and g_edge:
                ret = g_edge
            elif g_edge:
                ret = g_edge
            else:
                ret = p_edge
            pos += 1

        return edges[-1][1], len(edges) - 1

    ## ---- INTERMODAL: modes and route validity ---- ##

    @staticmethod
    def _get_mode_parameters(mode):
        """ Return the correst TraCI parameters for the requested mode.
            Parameters: _modes, _ptype, _vtype
        """
        if mode == 'public':
            return 'public', '', ''
        elif mode == 'bicycle':
            return 'bicycle', '', 'bicycle'
        elif mode == 'walk':
            return '', 'pedestrian', ''
        return 'car', '', mode

    @staticmethod
    def _is_valid_route(mode, route):
        """ Handle simultaneously findRoute and findIntermodalRoute results. """
        if route is None:
            # traci failed
            return False
        elif mode is None:
            # only for findRoute
            if route.edges:
                return True
        elif mode == 'public':
            for stage in route:
                if stage.line:
                    return True
        elif mode == 'car':
            for stage in route:
                if stage.stageType == tc.STAGE_DRIVING and stage.edges:
                    return True
        else:
            for stage in route:
                if stage.edges:
                    return True
        return False

    @staticmethod
    def _cost_from_route(route):
        """ Compute the route cost. """
        cost = 0.0
        for stage in route:
            cost += stage.cost
        return cost

    ## ---------------------------------------------------------------------------------------- ##
    ##                                Saving trips to files                                     ##
    ## ---------------------------------------------------------------------------------------- ##

    ROUTES_TPL = """<?xml version="1.0" encoding="UTF-8"?>

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

<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd"> {trips}
</routes>"""

    VEHICLE = """
    <vehicle id="{id}" type="{v_type}" depart="{depart}" departLane="best" arrivalPos="{arrival}">{route}{stop}
    </vehicle>"""

    ROUTE = """
        <route edges="{edges}"/>"""

    STOP_PARKING = """
        <stop parkingArea="{id}" until="{until}"/>"""

    PERSON = """
    <person id="{id}" depart="{depart}">{stages}
    </person>"""

    WALK = """
        <walk edges="{edges}"/>"""

    WALK_BUS = """
        <walk edges="{edges}" busStop="{busStop}"/>"""

    RIDE_BUS = """
        <ride busStop="{busStop}" lines="{lines}" intended="{intended}" depart="{depart}"/>"""

    RIDE_TRIGGERED = """
        <ride from="{from_edge}" to="{to_edge}" lines="{vehicle_id}"/>"""

    VEHICLE_TRIGGERED = """
    <vehicle id="{id}" type="{v_type}" depart="triggered" departLane="best" arrivalPos="{arrival}">{route}{stop}
    </vehicle>"""

    def _saving_trips_to_files(self):
        """ Saving all te trips to files divided by vType. """

        _begin = self._conf['stopUntil']['begin']
        _end = self._conf['stopUntil']['end']

        for v_type, dict_trips in self._all_trips.items():
            filename = '{}/{}{}.rou.xml'.format(BASE_DIR, self._conf['outputPrefix'], v_type)
            with open(filename, 'w') as tripfile:
                all_trips = ''
                for time in sorted(dict_trips.keys()):
                    for vehicle in dict_trips[time]:
                        if v_type == 'pedestrian':
                            triggered = ''
                            stages = ''
                            for stage in vehicle['stages']:
                                if stage.stageType == tc.STAGE_WALKING:
                                    if stage.destStop:
                                        stages += self.WALK_BUS.format(
                                            edges=' '.join(stage.edges), busStop=stage.destStop)
                                    else:
                                        stages += self.WALK.format(edges=' '.join(stage.edges))
                                elif stage.stageType == tc.STAGE_DRIVING:
                                    if stage.line != stage.intended:
                                        # intended is the transport id, so it must be different
                                        stages += self.RIDE_BUS.format(
                                            busStop=stage.destStop, lines=stage.line,
                                            intended=stage.intended, depart=stage.depart)
                                    else:
                                        # triggered vehicle (line = intended) ask why to SUMO.
                                        _tr_id = '{}_tr'.format(vehicle['id'])
                                        _route = self.ROUTE.format(edges=' '.join(stage.edges))
                                        _stop = ''
                                        if stage.destStop:
                                            _stop = self.STOP_PARKING.format(
                                                id=stage.destStop,
                                                until=random.randint(_begin, _end))
                                        _arrival = 'random'
                                        if _stop:
                                            _arrival = self._parking_position[stage.destStop]
                                        triggered += self.VEHICLE_TRIGGERED.format(
                                            id=_tr_id, v_type=vehicle['mode'], route=_route,
                                            stop=_stop, arrival=_arrival)
                                        stages += self.RIDE_TRIGGERED.format(
                                            from_edge=stage.edges[0], to_edge=stage.edges[-1],
                                            vehicle_id=_tr_id)
                            all_trips += triggered
                            all_trips += self.PERSON.format(
                                id=vehicle['id'], depart=vehicle['depart'], stages=stages)
                        else:
                            _route = self.ROUTE.format(edges=' '.join(vehicle['stages'].edges))
                            _stop = ''
                            if vehicle['withParking']:
                                _stop = self.STOP_PARKING.format(id=vehicle['PLid'],
                                                                 until=random.randint(_begin, _end))
                            _arrival = 'random'
                            if _stop:
                                _arrival = self._parking_position[vehicle['PLid']]
                            all_trips += self.VEHICLE.format(
                                id=vehicle['id'], v_type=vehicle['type'], depart=vehicle['depart'],
                                route=_route, stop=_stop, arrival=_arrival)

                tripfile.write(self.ROUTES_TPL.format(trips=all_trips))
            logging.info('Saved %s', filename)

def _main():
    """ Person Trip Activity-based Mobility Generation with PoIs and TAZ. """

    ## ========================              PROFILER              ======================== ##
    # profiler = cProfile.Profile()
    # profiler.enable()
    ## ========================              PROFILER              ======================== ##

    args = _args()

    logging.info('Loading configuration file %s.', args.config)
    conf = _load_configurations(args.config)

    mobility = MobilityGenerator(conf, profiling=False)
    mobility.mobility_generation()
    mobility.save_mobility()
    mobility.close_traci()

    ## ========================              PROFILER              ======================== ##
    # profiler.disable()
    # results = io.StringIO()
    # pstats.Stats(profiler, stream=results).sort_stats('cumulative').print_stats(25)
    # print(results.getvalue())
    ## ========================              PROFILER              ======================== ##

    logging.info('Done.')

if __name__ == "__main__":
    _logs()
    _main()
