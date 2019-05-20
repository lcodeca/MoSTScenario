#!/usr/bin/env python3

""" Extract Parking Lots from a SUMO TAZ.

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
import json
import logging
import sys
import xml.etree.ElementTree

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
        description='Extract Parking Lots from a SUMO TAZ.')
    parser.add_argument(
        '-t', type=str, dest='tazfile', required=True,
        help='SUMO TAZ file.')
    parser.add_argument(
        '-p', type=str, dest='parkingsfile', required=True,
        help='SUMO additional file for parkings.')
    parser.add_argument(
        '-o', type=str, dest='output', required=True,
        help='Prefix for the JSON output file.')

    return parser.parse_args()

class ParkingFilter(object):
    """ Generate the SUMO additional file for parkings based on OSM. """

    _taz_edges = list()
    _parkings = dict()
    _selected_parkings = dict()

    def __init__(self, taz, parkings):

        self._load_edges_from_taz(taz)
        self._load_parkings(parkings)

    def filter_parkings(self):
        """ Main finction to generate all the parking areas. """
        for plid, parking in self._parkings.items():
            if parking in self._taz_edges:
                self._selected_parkings[plid] = parking

    def dump_parkings_to_josm(self, filename):
        """ Dump the parkings in a JSON file. """
        with open(filename, 'w') as outfile:
            json.dump(list(self._selected_parkings.keys()), outfile)

    def _load_edges_from_taz(self, filename):
        """ Load edges from the TAZ file. """
        xml_tree = xml.etree.ElementTree.parse(filename).getroot()
        for child in xml_tree:
            if child.tag == 'taz':
                self._taz_edges.extend(child.attrib['edges'].split(' '))

    def _load_parkings(self, filename):
        """ Load parkings ids from XML file. """
        xml_tree = xml.etree.ElementTree.parse(filename).getroot()
        for child in xml_tree:
            if child.tag == 'parkingArea':
                self._parkings[child.attrib['id']] = child.attrib['lane'].split('_')[0]


def _main():
    """ Extract Parking Lots from a SUMO TAZ. """
    args = _args()

    parkings = ParkingFilter(args.tazfile, args.parkingsfile)
    parkings.filter_parkings()
    parkings.dump_parkings_to_josm(args.output)

    logging.info('Done.')

if __name__ == "__main__":
    _logs()
    _main()
