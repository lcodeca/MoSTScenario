#!/usr/bin/python3

""" Merge OSM-like pickles from a directory.

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
import os
import pickle
import sys
from tqdm import tqdm

HEADER_TPL = """<?xml version='1.0' encoding='UTF-8'?>
<osm version="0.6">
    <bounds minlat="{minlat}" minlon="{minlon}" maxlat="{maxlat}" maxlon="{maxlon}"/>""" # pylint: disable=C0301

NODE_TPL = """
    <node id="{id}" lat="{lat}" lon="{lon}" ele="{ele}" version="1" timestamp="2018-01-01T12:00:00Z"> {tags}
    </node>"""

WAY_TPL = """
    <way id="{id}" version="1" timestamp="2018-01-01T12:00:00Z"> {nds} {tags}
    </way>"""

REL_TPL = """
    <relation id="{id}" version="1" timestamp="2018-01-01T12:00:00Z"> {members} {tags}
    </relation>"""

ND_TPL = """
        <nd ref="{ref}"/>"""

TAG_TPL = """
        <tag k="{k_val}" v="{v_val}"/>"""

MEMB_TPL = """
        <member type="{mtype}" ref="{ref}" role="{role}"/>"""

FOOTER_TPL = """
</osm>
"""

def _logs():
    """ Log init. """
    file_handler = logging.FileHandler(filename='merge_osm_files.log', mode='w')
    stdout_handler = logging.StreamHandler(sys.stdout)
    handlers = [file_handler, stdout_handler]
    logging.basicConfig(handlers=handlers, level=logging.INFO,
                        format='[%(asctime)s] %(levelname)s: %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p')

def _args():
    """ Argument Parser
    ret: parsed arguments.
    """
    parser = argparse.ArgumentParser(
        prog='merge_osm_files.py', usage='%(prog)s [options]',
        description='Merges a list of OSM-like pickles.')
    parser.add_argument(
        '-d', type=str, dest='osmdir', default='toMerge',
        help='Directory containing the OSM-like pickles.')
    parser.add_argument(
        '-o', type=str, dest='output', default='merged.osm',
        help='Merged OSM-like files.')

    return parser.parse_args()

class MergeOSMFiles(object):
    """ Merges all the OSM-like files (in cPickle format) stored in a folder,
        into a single OSM file. """

    _boundaries = {
        'minlat': 360.0,
        'minlon': 360.0,
        'maxlat': -360.0,
        'maxlon': -360.0,
    }

    _global_counter = 1

    _all_nodes = {}
    _all_ways = {}
    _all_relations = {}

    _nodes_mapping = {}
    _ways_mapping = {}

    def __init__(self, folder):
        """ Loads and process all the pickle files in the folder. """

        for filename in os.listdir(folder):
            fname = os.path.join(folder, filename)

            if not os.path.isfile(fname):
                continue

            logging.info("Loading %s", fname)
            self._parse_osm_pickle(fname)
            logging.info("%s done.", fname)

        self._filter_duplicate_tags()

    ## ------------------------------           LOADERS           ------------------------------ ##

    @staticmethod
    def _read_from_pickle(filename):
        """ Dump the object into a binary pickle file. """
        with open(filename, 'rb') as pickle_obj:
            obj = pickle.load(pickle_obj)
        return obj

    ## ------------------------------         PROCESSING          ------------------------------ ##

    def _parse_osm_pickle(self, filename):
        """ Extract nodes and ways from OSM-like file. """
        osm = self._read_from_pickle(filename)

        if 'node' in osm.keys():
            for node in tqdm(osm['node']):
                self._process_osm_node(node)

        if 'way' in osm.keys():
            for way in tqdm(osm['way']):
                self._process_osm_way(way)

        if 'relation' in osm.keys():
            for relation in tqdm(osm['relation']):
                self._process_osm_relation(relation)

    def _process_osm_node(self, node):
        """ Process nodes from OSM-like file. """

        lat = node['lat']
        lon = node['lon']
        ele = '0.0'
        if 'ele' in node.keys():
            ele = node['ele']

        ## look for tags
        tags = []
        if 'tag' in node.keys():
            for tag in node['tag']:
                if tag['k'] == 'ele':
                    ele = tag['v']
                tags.append(tag)

        node_name = ('{:.7f}:{:.7f}:{:.2f}'
                     .format(float(lat), float(lon), float(ele)))

        self._boundaries['minlat'] = min(float(lat), self._boundaries['minlat'])
        self._boundaries['minlon'] = min(float(lon), self._boundaries['minlon'])
        self._boundaries['maxlat'] = max(float(lat), self._boundaries['maxlat'])
        self._boundaries['maxlon'] = max(float(lon), self._boundaries['maxlon'])

        if node_name in self._all_nodes:
            ## UPDATE NODE
            self._all_nodes[node_name]['id'].append(node['id'])
            self._all_nodes[node_name]['tags'].extend(tags)
        else:
            ## SAVE NODE
            self._all_nodes[node_name] = {
                'new_id': self._global_counter,
                'id' : [node['id']],
                'lat' : lat,
                'lon' : lon,
                'ele' : ele,
                'tags' : tags,
            }
            self._global_counter += 1
        self._nodes_mapping[node['id']] = self._all_nodes[node_name]['new_id']

    def _process_osm_way(self, way):
        """ Process ways from OSM-like file. """

        new_way = {
            'id': way['id'],
            'nds': [],
            'tags': [],
        }

        if 'nd' in way.keys():
            for node in way['nd']:
                if node['ref'] in list(self._nodes_mapping.keys()):
                    new_way['nds'].append(self._nodes_mapping[node['ref']])
                else:
                    logging.debug("Dropped node %s.", node['ref'])

        if 'tag' in way.keys():
            for tag in way['tag']:
                new_way['tags'].append(tag)

        if new_way['nds']: # drop ways without nodes
            self._all_ways[self._global_counter] = new_way
            self._ways_mapping[way['id']] = self._global_counter
            self._global_counter += 1

    def _process_osm_relation(self, relation):
        """ Process relations from OSM-like file. """

        new_rel = {
            'id': relation['id'],
            'members': [],
            'tags': [],
        }

        if 'member' in relation.keys():
            for member in relation['member']:

                # Public Transports
                # <member type="node" ref="1776309882" role="stop"/>

                # Road Restrictions
                # <member type="way" ref="1219" role="from"/>
		        # <member type="way" ref="1198" role="to"/>
		        # <member type="node" ref="-41988" role="via"/>

                if member['type'] == 'node':
                    if member['ref'] in list(self._nodes_mapping.keys()): # NODES
                        new_rel['members'].append(
                            (member['type'], self._nodes_mapping[member['ref']], member['role']))
                if member['type'] == 'way':
                    if member['ref'] in list(self._ways_mapping.keys()): # WAYS
                        new_rel['members'].append(
                            (member['type'], self._ways_mapping[member['ref']], member['role']))

        if 'tag' in relation.keys():
            for tag in relation['tag']:
                new_rel['tags'].append(tag)

        if new_rel['members']: # drop relation without members
            self._all_relations[self._global_counter] = new_rel
            self._global_counter += 1

    ## ------------------------------         DUPLICATES         ------------------------------ ##

    @staticmethod
    def _filter_duplicates(tags):
        """ Filter duplicate tags. """
        set_filtered_tags = set()
        for tag in tags:
            set_filtered_tags.add(tuple(tag.items()))
        list_filtered_tags = []
        for item in set_filtered_tags:
            list_filtered_tags.append(dict(item))
        return list_filtered_tags

    def _filter_duplicate_tags(self):
        """ Filter duplicate tags from NODES and WAYS. """

        logging.info("Filtering duplicate tags in nodes.")
        for nid, node in self._all_nodes.items():
            self._all_nodes[nid]['tags'] = self._filter_duplicates(node['tags'])

        logging.info("Filtering duplicate tags in ways.")
        for wid, way in self._all_ways.items():
            self._all_ways[wid]['tags'] = self._filter_duplicates(way['tags'])

        logging.info("Filtering duplicate tags in relations.")
        for rid, rel in self._all_relations.items():
            self._all_relations[rid]['tags'] = self._filter_duplicates(rel['tags'])

        logging.info("Duplicates removed.")

    ## ------------------------------         SAVE FILE         ------------------------------ ##

    def _write_all_nodes(self, filebuffer):
        """ Write all the nodes to OSM-like file. """
        for _, node in self._all_nodes.items():
            string_of_tags = ""
            for value in node['tags']:
                val = value['v'].replace('"', '')
                val = val.replace('&', 'and')
                string_of_tags += TAG_TPL.format(
                    k_val=value['k'],
                    v_val=val) #.encode('utf-8')

            filebuffer.write(NODE_TPL.format(id=node['new_id'], lat=node['lat'],
                                             lon=node['lon'], ele=node['ele'],
                                             tags=string_of_tags))

    def _write_all_ways(self, filebuffer):
        """ Write all the ways to OSM-like file. """
        for wid, way in self._all_ways.items():
            string_of_nodes = ""
            for nid in way['nds']:
                string_of_nodes += ND_TPL.format(ref=nid)
            string_of_tags = ""
            for tag in way['tags']:
                value = tag['v'].replace('"', '')
                value = value.replace('&', 'and')
                string_of_tags += TAG_TPL.format(
                    k_val=tag['k'],
                    v_val=value) #.encode('utf-8')

            filebuffer.write(WAY_TPL.format(
                id=wid, nds=string_of_nodes, tags=string_of_tags))

    def _write_all_relations(self, filebuffer):
        """ Write all the ways to OSM-like file. """
        for rid, rel in self._all_relations.items():
            string_of_members = ""
            for mtype, ref, role in rel['members']:
                string_of_members += MEMB_TPL.format(mtype=mtype, ref=ref,
                                                     role=role)
            string_of_tags = ""
            for tag in rel['tags']:
                value = tag['v'].replace('"', '')
                value = value.replace('&', 'and')
                string_of_tags += TAG_TPL.format(
                    k_val=tag['k'],
                    v_val=value) # .encode('utf-8')

            filebuffer.write(REL_TPL.format(
                id=rid, members=string_of_members, tags=string_of_tags))

    def write_osm_file(self, filename):
        """ Write the OSM-like file. """

        logging.info("Creation of %s", filename)
        with open(filename, 'w') as outfile:
            outfile.write(HEADER_TPL.format(
                minlat=self._boundaries['minlat'], minlon=self._boundaries['minlon'],
                maxlat=self._boundaries['maxlat'], maxlon=self._boundaries['maxlon']))

            self._write_all_nodes(outfile)
            self._write_all_ways(outfile)
            self._write_all_relations(outfile)

            outfile.write(FOOTER_TPL)
        logging.info("%s created.", filename)

    ## ---------------------------------------------------------------------------------------- ##

def _main():
    """ Merge OSM-like files from a directory. """

    ## ========================              PROFILER              ======================== ##
    # import cProfile, pstats, io
    # profiler = cProfile.Profile()
    # profiler.enable()
    ## ========================              PROFILER              ======================== ##

    args = _args()

    merger = MergeOSMFiles(args.osmdir)
    merger.write_osm_file(args.output)

    ## ========================              PROFILER              ======================== ##
    # profiler.disable()
    # results = io.StringIO()
    # pstats.Stats(profiler, stream=results).sort_stats('cumulative').print_stats(25)
    # print(results.getvalue())
    ## ========================              PROFILER              ======================== ##

if __name__ == "__main__":
    _logs()
    _main()
