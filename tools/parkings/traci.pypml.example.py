#!/usr/bin/env python3

""" Example of Live monitor for SUMO simulations.

    Monaco SUMO Traffic (MoST) Scenario
    Author: Lara CODECA

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
import csv
import json
import logging
import os
import pprint
import sys
import traceback
from tqdm import tqdm
from pypml import ParkingMonitor

# """ Import SUMOLIB """
if 'SUMO_TOOLS' in os.environ:
    sys.path.append(os.environ['SUMO_TOOLS'])
    import traci
    import traci.constants as tc
else:
    sys.exit("Please declare environment variable 'SUMO_TOOLS'")

def _args():
    """ Argument Parser
    ret: parsed arguments.
    """
    parser = argparse.ArgumentParser(
        prog='{}'.format(sys.argv[0]),
        usage='%(prog)s -c configuration.json',
        description='Live monitor for SUMO simulations.')
    parser.add_argument(
        '-c', type=str, dest='config', required=True,
        help='JSON configuration file.')
    return parser.parse_args()

def _load_json(filename):
    """ Load JSON configuration file in a dict. """
    return json.loads(open(filename).read())

def _save_occupancy_to_csv(monitor, prefix):
    """ Save the occupancy over time to a CSV file. """
    filename = '{}.occupancy.csv'.format(prefix)
    series = []
    for parking in monitor.get_parking_iterator():
        for value, step in parking['occupancy_series']:
            data = {
                'parking': parking['sumo']['id'],
                'time': step,
                'occupancy': value,
                'used': float(value / parking['total_capacity'])
            }
            series.append(data)

    with open(filename, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, series[0].keys())
        writer.writeheader()
        writer.writerows(series)
    logging.info('Parking occupancy over time saved to %s', filename)

def _save_travel_time_to_csv(monitor, prefix):
    """ Save the occupancy over time to a CSV file. """
    filename = '{}.vehicle.ett.csv'.format(prefix)
    series = []
    for vehicle in monitor.get_vehicle_iterator():
        data = {
            'id': vehicle['id'],
            'departure': vehicle['departure'],
            'stop_changes': len(vehicle['history']),
            'vClass': vehicle['vClass'],
        }
        if 'final_stop_arrival' in vehicle.keys():
            data['final_stop_arrival'] = vehicle['final_stop_arrival']
        else:
            data['final_stop_arrival'] = None
        if 'arrival' in vehicle.keys():
            data['arrival'] = vehicle['arrival']
        else:
            data['arrival'] = None
        series.append(data)

    with open(filename, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, series[0].keys())
        writer.writeheader()
        writer.writerows(series)
    logging.info('Vehicle ETT saved to %s', filename)

def _save_ett_person_to_csv(monitor, people, prefix):
    """ Save the occupancy over time to a CSV file. """
    filename = '{}.person.ett.csv'.format(prefix)
    with open(filename, 'w') as csvfile:
        keys = ['id', 'departed', 'arrived']
        writer = csv.DictWriter(csvfile, keys)
        writer.writeheader()
        for pid in monitor.get_passenger_iterator():
            if pid in people.keys():
                if 'arrived' not in people[pid].keys():
                    people[pid]['arrived'] = None
                writer.writerow(people[pid])
            else:
                print('Missing ', pid)

    logging.info('Person ETT saved to %s', filename)

def _main():
    """ Live monitor for SUMO simulations. """
    args = _args()
    conf = _load_json(args.config)

    _begin_sec = conf['interval']['begin']
    _end_sec = conf['interval']['end']

    traci.start(['sumo', '-c', conf['sumocfg']], port=conf['traci_port'])

    parking_monitor_options = {
        'seed': 42,
        'addStepListener': True,
        'logging': {
            'stdout': False,
            'filename': '{}.log'.format(sys.argv[0]),
            'level': logging.DEBUG,
        },
        'sumo_parking_file': '../../scenario/in/add/most.parking.norerouters.add.xml',
        'blacklist': [],
        'vclasses': {'delivery', 'taxi', 'truck', 'coach', 'trailer', 'evehicle',
                     'passenger', 'motorcycle', 'moped', 'bicycle', 'bus',
                     'emergency', 'authority', 'army'},
        'generic_conf': [
            {
                'cond': ['<', 'total_capacity', 500],
                'set_to': [
                    ['uncertainty', {
                        'mu': 0.0,
                        'sigma': ['*', 'total_capacity', 0.25]
                        }
                    ],
                ],
            },
        ],
        'specific_conf': {},
        'subscriptions': {
            'only_parkings': False,
        },
    }

    monitor = ParkingMonitor(traci, parking_monitor_options)

    ett_people = dict()

    # parking travel time structure initialized
    monitor.compute_parking_travel_time()

    _time = _begin_sec
    try:
        running_people = set()

        for step in tqdm(range(_begin_sec, _end_sec, 1)):
            _time = float(step)
            traci.simulationStep()

            ## STATS:
            arrived = traci.simulation.getArrivedIDList()
            for eid in arrived:
                monitor.set_vehicle_param(eid, 'arrival', step)

            ## PPL:
            people = set(traci.person.getIDList())
            departed_people = people - running_people
            arrived_people = running_people - people
            for pid in departed_people:
                if pid in ett_people:
                    sys.exit('Person {} is already departed!'.format(pid))
                ett_people[pid] = {
                    'id': pid,
                    'departed': step,
                }
            for pid in arrived_people:
                if 'arrived' in ett_people[pid]:
                    sys.exit('Person {} is already arrived!'.format(pid))
                ett_people[pid]['arrived'] = step
            running_people = people

            if _time % 60 != 0:
                continue

            ## PARKING OPTIMIZATION
            for vehicle in monitor.get_vehicle_iterator():
                if not vehicle['edge'] or ':' in vehicle['edge']:
                    ## the vehicle is on an intersection and the change would not be safe.
                    continue
                if vehicle['stops']:
                    _, _, stopping_place, stop_flags, _, _ = vehicle['stops'][0]
                    if monitor.is_parking_area(stop_flags):
                        ### OPTIMIZE VEHICLE
                        availability = monitor.get_free_places(stopping_place,
                                                               vclass=vehicle['vClass'],
                                                               with_projections=True,
                                                               with_uncertainty=True)
                        if availability < 10:
                            alternatives = monitor.get_closest_parkings(stopping_place, num=25)
                            for trtime, alt in alternatives:
                                alt_availability = monitor.get_free_places(
                                    alt, vclass=vehicle['vClass'],
                                    with_projections=True, with_uncertainty=True)
                                print(step, trtime, alt, alt_availability)
                                if alt_availability > 10:
                                    ## reroute vehicle
                                    route = None
                                    try:
                                        edge = monitor.get_parking_access(alt).split('_')[0]
                                        route = traci.simulation.findRoute(
                                            vehicle['edge'], edge, vType=vehicle['vClass'])
                                    except traci.exceptions.TraCIException:
                                        route = None

                                    if route and len(route.edges) >= 2:
                                        try:
                                            traci.vehicle.rerouteParkingArea(vehicle['id'], alt)
                                            print("""Vehicle {} is going to be rerouted from {} """
                                                  """[{}] to {} [{}].""".format(vehicle['id'],
                                                                                stopping_place,
                                                                                availability, alt,
                                                                                alt_availability))
                                        except traci.exceptions.TraCIException:
                                            pprint.pprint([monitor.get_parking_access(alt), route])
                                            raise
                                        break

    except traci.exceptions.TraCIException:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        logging.fatal('Fatal error at timestamp %.2f', _time)
        traceback.print_exception(exc_type, exc_value, exc_traceback, limit=10, file=sys.stdout)

    finally:
        ### Save results!
        _save_occupancy_to_csv(monitor, conf['saveToPrefix'])
        _save_travel_time_to_csv(monitor, conf['saveToPrefix'])
        _save_ett_person_to_csv(monitor, ett_people, conf['saveToPrefix'])
        traci.close()

if __name__ == '__main__':

    ## ========================              PROFILER              ======================== ##
    import cProfile, pstats, io
    profiler = cProfile.Profile()
    profiler.enable()
    ## ========================              PROFILER              ======================== ##

    try:
        _main()
    finally:
        ## ========================              PROFILER              ======================== ##
        profiler.disable()
        results = io.StringIO()
        pstats.Stats(profiler, stream=results).sort_stats('cumulative').print_stats(25)
        print(results.getvalue())
        ## ========================              PROFILER              ======================== ##
