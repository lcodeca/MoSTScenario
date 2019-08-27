#!/usr/bin/env python3

""" Load a XML file into a dict and save it to a binary pickle file.

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
import logging
import pickle
import sys
import xml.etree.ElementTree

def _logs():
    """ Log init. """
    file_handler = logging.FileHandler(filename='xml2pickle.log', mode='w')
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
        prog='xml2pickle.py', usage='%(prog)s [options]',
        description='Load a XML file  into a dict and save it to a binary pickle file.')
    parser.add_argument(
        '-i', type=str, dest='input', required=True,
        help='XML file.')
    parser.add_argument(
        '-o', type=str, dest='output', required=True,
        help='Pickle file.')

    return parser.parse_args()

def _parse_xml_file(xml_file):
    """ Extract nodes and ways from XML file. """
    xml_tree = xml.etree.ElementTree.parse(xml_file).getroot()
    dict_xml = {}
    for child in xml_tree:
        parsed = {}
        for key, value in child.attrib.items():
            parsed[key] = value

        for attribute in child:
            if attribute.tag in list(parsed.keys()):
                parsed[attribute.tag].append(attribute.attrib)
            else:
                parsed[attribute.tag] = [attribute.attrib]

        if child.tag in list(dict_xml.keys()):
            dict_xml[child.tag].append(parsed)
        else:
            dict_xml[child.tag] = [parsed]
    return dict_xml

def _dump_to_pickle(obj, filename):
    """ Dump the object into a binary pickle file. """
    with open(filename, 'wb') as dump:
        pickle.dump(obj, dump, pickle.HIGHEST_PROTOCOL)

def _main():
    """ Load a XML file into a dict and save it to a binary pickle file. """

    args = _args()
    logging.info('Loading from %s', args.input)
    xml_data = _parse_xml_file(args.input)
    logging.info('Dumping to %s', args.output)
    _dump_to_pickle(xml_data, args.output)
    logging.info('Done.')

if __name__ == "__main__":
    _logs()
    _main()
