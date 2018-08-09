#!/usr/bin/env python3

""" Live monitor for SUMO simulations. """

import argparse
import csv
import json
import logging
import os
import pprint
import random
import sys
import traceback
from tqdm import tqdm
from parkingmonitor import ParkingMonitor

# """ Import SUMOLIB """
if 'SUMO_DEV_TOOLS' in os.environ:
    sys.path.append(os.environ['SUMO_DEV_TOOLS'])
    # import sumolib
    import traci
    import traci.constants as tc
else:
    sys.exit("Please declare environment variable 'SUMO_DEV_TOOLS'")

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

    _begin_sec = float(conf['interval']['begin'])
    _end_sec = float(conf['interval']['end'])

    _begin_msec = int(_begin_sec*1000)
    _end_msec = int(_end_sec*1000)

    traci.start(['sumo', '-c', conf['sumocfg'], conf['sumoaddopt']],
                port=conf['traci_port'])
    # traci.init(port=conf['traci_port'])

    # main_traci = traci.connect(port=conf['traci_main_port'])
    # monitor_traci = traci.connect(port=conf['traci_monitor_port'])

    parking_monitor_options = {
        'logging': {
            'stdout': False,
            'filename': '{}.log'.format(sys.argv[0]),
            'level': logging.DEBUG,
        },
        'sumo_parking_file': '../../scenario/in/add/most.parkings.add.xml',
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

    monitor = ParkingMonitor(traci, parking_monitor_options, _begin_msec)

    ett_people = dict()

    # parking travel time structure initialized
    monitor.compute_parking_travel_time()

    _time = _begin_sec
    try:
        counter = 0
        running_people = set()

        for step in tqdm(range(_begin_msec, _end_msec, 1000)):
            _time = float(step)/1000
            traci.simulationStep(step)

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

            counter += 1
            # if counter == 2*3600: break

            if _time % 60 != 0:
                continue

            ## PARKING OPTIMIZATION once every XX seconds

            for parking in monitor.get_parking_iterator():

                availability = monitor.get_free_places(parking['sumo']['id'], with_projections=True)
                # print(parking['sumo']['id'], availability)

                if availability >= 0:
                    continue

                projections = set()
                for pj_vclass in parking['projections_by_class'].values():
                    projections |= pj_vclass

                # print(projections)

                ## redistribute the problem
                to_reroute = random.sample(projections, abs(availability))
                print(to_reroute)

                for vid in to_reroute:
                    vehicle = monitor.get_vehicle(vid)
                    if not vehicle['edge'] or ':' in vehicle['edge']:
                        ## the vehicle is on an intersection and the change would not be safe.
                        continue
                    _, _, stopping_place, _, _, _ = vehicle['stops'][0]

                    alternatives = monitor.get_closest_parkings(stopping_place, num=25)
                    for trtime, alt in alternatives:
                        alt_availability = monitor.get_free_places(alt, vclass=vehicle['vClass'],
                                                                   with_projections=True)
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
                                          """to {} [{}].""".format(vehicle['id'], stopping_place,
                                                                   alt, alt_availability))
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

# subscription initialization
# for parking in monitor.get_parking_iterator():
#     parea = parking['sumo']['id']
#     capacity = parking['total_capacity']
#     capacity_vclasses = monitor.get_parking_capacity_vclass(parea)
#     if not capacity_vclasses:
#         capacity_vclasses = {
#             'coach': round(capacity * 0.01),
#             'delivery': round(capacity * 0.02),
#             'ptw': round(capacity * 0.10),
#             'truck': round(capacity * 0.03),
#         }
#         tot = 0
#         for val in capacity_vclasses.values():
#             tot += val
#         capacity_vclasses['passenger'] = capacity - tot
#         monitor.set_parking_capacity_vclass(parea, capacity_vclasses)
#     if capacity < 250:
#         continue
#     subscriptions = monitor.get_parking_subscriptions(parea)
#     if not subscriptions:
#         subscriptions = {
#             'coach': [0, set()],
#             'delivery': [0, set()],
#             'passenger': [round(capacity * 0.2), set()],
#             'ptw': [round(capacity * 0.05), set()],
#             'truck': [0, set()],
#         }
#         monitor.set_parking_subscriptions(parea, subscriptions)
