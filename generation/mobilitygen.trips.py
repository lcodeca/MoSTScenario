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
import heapq
import json
import logging
import os
import xml.etree.ElementTree
import random
import sys
import numpy

# """ Import SUMOLIB """
if 'SUMO_TOOLS' in os.environ:
    sys.path.append(os.environ['SUMO_DEV_TOOLS'])
else:
    sys.exit("Please declare environment variable 'SUMO_TOOLS'")
import sumolib

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

PERSON_TPL = """
    <person id="{id}" depart="{depart}">{trip}
    </person>"""

PERSON_PUBLIC_TPL = """
    <person id="{id}" depart="{depart}">
        <personTrip from="{from_edge}" to="{to_edge}" modes="public"/>
    </person>"""

PERSON_SHARED_TPL = """
    <person id="{id}" depart="{depart}">
        <personTrip from="{from_edge}" to="{to_edge}" vTypes="shared"/>
    </person>"""

WALK_TPL = """
        <walk from="{from_edge}" to="{to_edge}"/>"""

WALK_POS_TPL = """
        <walk from="{from_edge}" to="{to_edge}" arrivalPos="{to_pos}"/>"""

RIDE_TPL = """
        <ride from="{from_edge}" to="{to_edge}" lines="{lines}"/>"""

TRIP_TPL = """
    <trip id="{id}" depart="{depart}" departLane="best" from="{from_edge}" to="{to_edge}" type="{vType}"/>"""

STOP_TPL = """
    <trip id="{id}" depart="{depart}" departLane="best" from="{from_edge}" to="{to_edge}" type="{vType}">
        <stop parkingArea="{parking}" duration="{duration}"/>
    </trip>"""

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
        usage='%(prog)s -c configuration.json',
        description='Generate trips based on a symplified acrtivity-based '
                    'mobility generation based on PoIs and TAZ.')
    parser.add_argument(
        '-c', type=str, dest='config', required=True,
        help='JSON configuration file.')
    return parser.parse_args()

def _load_configurations(filename):
    """ Load JSON configuration file in a dict. """
    return json.loads(open(filename).read())

def _load_parkings(filename):
    """ Load parkings ids from XML file. """
    parkings = collections.defaultdict(list)
    xml_tree = xml.etree.ElementTree.parse(filename).getroot()
    for child in xml_tree:
        if child.tag == 'parkingArea':
            edge = child.attrib['lane'].split('_')[0]
            parkings[edge].append(child.attrib['id'])
    return parkings

def _convert_sumo_net_to_dijkstra_graph(network, edges_by_taz):
    """ Extract the graph from a SUMO net, filtering by allowed edges."""

    edges = set()
    for taz in edges_by_taz.keys():
        for edge in edges_by_taz[taz]:
            edges.add(edge)

    graph = collections.defaultdict(list)
    for edge in network.getEdges():
        if edge.getID() not in edges:
            continue
        graph[edge.getFromNode().getID()].append((1, edge.getToNode().getID()))

    return graph

def _load_weights_from_csv(filename):
    """ Load the TAZ weight froma CSV file. """
    weights = {}
    with open(filename, 'r') as csvfile:
        weightreader = csv.reader(csvfile)
        header = None
        for row in weightreader:
            if not header:
                header = row
            else:
                weights[int(row[0])] = {
                    header[0]: int(row[0]),
                    header[1]: row[1],
                    header[2]: int(row[2]),
                    header[3]: float(row[3]),
                    'weight': (int(row[2])/float(row[3])),
                }
    return weights

def _compute_vehicles_per_type(config):
    """
    Compute the absolute number of trip that are going to be created
    for each vechile type, given a population.
    """
    logging.debug('Population: %d', config['population'])

    for v_type in config['distribution'].keys():
        config['distribution'][v_type]['tot'] = int(
            config['population'] * config['distribution'][v_type]['percentage'])
        if config['distribution'][v_type]['withDUAerror']:
            config['distribution'][v_type]['surplus'] = int(
                config['distribution'][v_type]['tot'] * config['duarouterError'])
        else:
            config['distribution'][v_type]['surplus'] = 0
        logging.debug('\t %s: %d [%d]', v_type, config['distribution'][v_type]['tot'], 
                      config['distribution'][v_type]['surplus'])
    return config

def _load_edges_from_taz(filename):
    """ Load edges from the TAZ file. """
    edges = {}
    xml_tree = xml.etree.ElementTree.parse(filename).getroot()
    for child in xml_tree:
        if child.tag == 'taz':
            edges[child.attrib['id']] = child.attrib['edges'].split(' ')
    return edges

def _select_taz_from_weighted_area(area, weights):
    """ Select a TAZ from an area using its weight. """
    selection = random.uniform(0, 1)
    total_weight = sum([weights[taz]['weight'] for taz in area])
    cumulative = 0.0
    for taz in area:
        cumulative += weights[taz]['weight'] / total_weight
        if selection <= cumulative:
            return taz
    return None # this is matematically impossible,
                # if this happens, there is a mistake in the weights.

def _select_pair_from_list(pairs):
    """ Randomly select one pair from a TAZ. """
    if not pairs:
        return None
    pos = random.randint(0, len(pairs) - 1)
    return pairs[pos]

def _dijkstra(graph, from_node_id, to_node_id):
    """ Return the shortest path, if possible. """
    queue, seen = [(0, from_node_id, ())], set()
    while queue:
        (cost, v_1, path) = heapq.heappop(queue)
        if v_1 not in seen:
            seen.add(v_1)
            path = (v_1, path)
            if v_1 == to_node_id:
                return (cost, path)

            for weight, v_2 in graph.get(v_1, ()):
                if v_2 not in seen:
                    heapq.heappush(queue, (cost + weight, v_2, path))

    return None

def _valid_pair(graph, from_edge, to_edge, net):
    """ Validate the trip route. """
    from_node = net.getEdge(from_edge).getToNode().getID()
    to_node = net.getEdge(to_edge).getToNode().getID()
    if _dijkstra(graph, from_node, to_node):
        return True
    return False

def _find_allowed_pair(edges, weights, from_area, to_area, graph, net, _counter=0):
    """ Return an origin ad an allowed destination. """
    from_taz = str(_select_taz_from_weighted_area(from_area, weights))
    to_taz = str(_select_taz_from_weighted_area(to_area, weights))

    pairs = []
    for edge_1 in edges[from_taz]:
        for edge_2 in edges[to_taz]:
            if edge_1 == edge_2:
                continue
            pairs.append((edge_1, edge_2))
    pair = _select_pair_from_list(pairs)
    from_edge, to_edge = pair
    counter = _counter
    while not _valid_pair(graph, from_edge, to_edge, net):
        pairs.remove(pair)
        pair = _select_pair_from_list(pairs)
        if not pair:
            logging.debug('From TAZ [%s] has %d edges.', from_taz, len(edges[from_taz]))
            logging.debug('To   TAZ [%s] has %d edges.', to_taz, len(edges[to_taz]))
            logging.debug('There is no valid OD pair, looking for others TAZ.')
            return _find_allowed_pair(edges, weights, from_area, to_area, graph, net, counter)
        from_edge, to_edge = pair
        counter += 1
    if counter >= 10:
        logging.debug('It required %d iterations to find a valid pair.', counter)
    return from_edge, to_edge

def _normal_departure_time(mean, std, _min, _max):
    """ Return the departure time, comuted using a normal distribution. """
    departure = int(numpy.random.normal(loc=mean, scale=std, size=1))
    while departure < _min or departure > _max:
        departure = int(numpy.random.normal(loc=mean, scale=std, size=1))
    return departure

def _get_parking_id(parkings):
    """ Randomly select one of the parkings. """
    if not parkings:
        return None
    pos = random.randint(0, len(parkings) - 1)
    return parkings[pos]

def _has_parking_lot(edge, parkings):
    """ Retrieve the parking area ID. """
    parking_id = None
    if edge in parkings.keys():
        parking_id = _get_parking_id(parkings[edge])
    return parking_id

def _compute_trips_per_type(config, weights, net, parkings):
    """ Compute the trips for ~everything~ """
    trips = collections.defaultdict(dict)
    for v_type in config['distribution'].keys():
        edges_by_taz = _load_edges_from_taz(
            '{}{}'.format(config['baseDir'], config['distribution'][v_type]['edges']))

        logging.info('Converting SUMO net file to Dijkstra-like weighted graph for %s.', v_type)
        graph = _convert_sumo_net_to_dijkstra_graph(net, edges_by_taz)

        total = 0
        for key, area in config['distribution'][v_type]['composition'].items():
            vehicles = None
            if config['distribution'][v_type]['withDUAerror']:
                vehicles = int(
                    (config['distribution'][v_type]['tot'] +
                     config['distribution'][v_type]['surplus'])
                    * area['perc'])
            else:
                vehicles = int(config['distribution'][v_type]['tot'] * area['perc'])
            logging.debug('--> %d trips from %s to %s.', vehicles, area['from'], area['to'])

            for veh_id in range(vehicles):
                _depart = _normal_departure_time(config['peak']['mean'], config['peak']['std'],
                                                 config['interval']['begin'],
                                                 config['interval']['end'])
                if _depart not in trips[v_type].keys():
                    trips[v_type][_depart] = []

                with_pt = 'withPT' in area.keys() and area['withPT']
                with_pl = 'withPL' in area.keys() and area['withPL']
                with_shared = 'withShared' in area.keys() and area['withShared']

                _from = None
                _to = None

                _from, _to = _find_allowed_pair(edges_by_taz, weights, config['taz'][area['from']],
                                                config['taz'][area['to']], graph, net)

                parking_id = None
                if with_pl:
                    parking_id = _has_parking_lot(_to, parkings)

                if not parking_id:
                    with_pl = False

                trips[v_type][_depart].append({
                    'id': '{}_{}_{}'.format(v_type, key, veh_id),
                    'depart': _depart,
                    'from': _from,
                    'to': _to,
                    'type': v_type,
                    'withPT': with_pt,
                    'withPL': with_pl,
                    'withShared': with_shared,
                    'PLid': parking_id,
                })

                total += 1
                if total % 100 == 0:
                    logging.debug('... %d trips for %s.', total, v_type)

        logging.info('Generated %d trips for %s.', total, v_type)
    return trips

def _saving_trips_to_files(trips, prefix, end):
    """ Saving all te trips to files divided by vType. """
    for v_type, dict_trips in trips.items():
        filename = '{}{}.trips.xml'.format(prefix, v_type)
        with open(filename, 'w') as tripfile:
            all_trips = ''
            for time in sorted(dict_trips.keys()):
                for vehicle in dict_trips[time]:
                    if v_type == 'pedestrian':
                        if vehicle['withPT']:
                            all_trips += PERSON_PUBLIC_TPL.format(
                                id=vehicle['id'], depart=vehicle['depart'],
                                from_edge=vehicle['from'], to_edge=vehicle['to'])
                        elif vehicle['withShared']:
                            all_trips += PERSON_SHARED_TPL.format(
                                id=vehicle['id'], depart=vehicle['depart'],
                                from_edge=vehicle['from'], to_edge=vehicle['to'])
                        else:
                            walk = WALK_TPL.format(from_edge=vehicle['from'], to_edge=vehicle['to'])
                            all_trips += PERSON_TPL.format(id=vehicle['id'],
                                                           depart=vehicle['depart'],
                                                           trip=walk)
                    else:
                        if vehicle['withPL']:
                            all_trips += STOP_TPL.format(
                                id=vehicle['id'], depart=vehicle['depart'],
                                from_edge=vehicle['from'], to_edge=vehicle['to'],
                                vType=vehicle['type'], parking=vehicle['PLid'],
                                duration=end)
                        else:
                            all_trips += TRIP_TPL.format(
                                id=vehicle['id'], depart=vehicle['depart'],
                                from_edge=vehicle['from'], to_edge=vehicle['to'],
                                vType=vehicle['type'])

            tripfile.write(ROUTES_TPL.format(trips=all_trips))
        logging.info('Saved %s', filename)

def _main():
    """ Person Trip Activity-based Mobility Generation with PoIs and TAZ. """
    args = _args()

    logging.info('Loading configuration file %s.', args.config)
    conf = _load_configurations(args.config)

    logging.info('Loading SUMO net file %s%s', conf['baseDir'], conf['SUMOnetFile'])
    net = sumolib.net.readNet('{}{}'.format(conf['baseDir'], conf['SUMOnetFile']))

    logging.info('Loading SUMO parking lots from file %s%s', conf['baseDir'], conf['parkings'])
    parkings = _load_parkings('{}{}'.format(conf['baseDir'], conf['parkings']))

    logging.info('Load TAZ weights from %s%s', conf['baseDir'], conf['tazWeights'])
    taz_weights = _load_weights_from_csv('{}{}'.format(conf['baseDir'], conf['tazWeights']))

    logging.info('Compute the number of agents for each vType..')
    conf = _compute_vehicles_per_type(conf)

    logging.info('Generating trips for each vType..')
    trips = _compute_trips_per_type(conf, taz_weights, net, parkings)

    logging.info('Saving trips files..')
    _saving_trips_to_files(trips, conf['outputPrefix'], conf['interval']['end'])

if __name__ == "__main__":
    _logs()
    _main()
