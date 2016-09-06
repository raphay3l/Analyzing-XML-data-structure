
#Author: Rafal Jankowski, UDACITY
# Parsing through XML file, exploring the data step by step
# Take each Part in turn and run in the emulator 
# Parse through the map and identify key elements

# Part 1 - Count tags  ----------------------
import xml.etree.cElementTree as ET
from collections import defaultdict
import pprint
types = defaultdict(int)

def count_tags(filename):
    filename = open(filename, 'r')
    for event, elem in ET.iterparse(filename):
        types[elem.tag] += 1
    return types

# Part 2 ----------------------
#Check the "k" value for each "<tag>" and see if they can be valid keys in MongoDB,
#as well as see if there are any other potential problems.
#So, we have to see if we have such tags, and if we have any tags with problematic characters.

import xml.etree.cElementTree as ET
import pprint
import re
lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

def key_type(element, keys):
    if element.tag == "tag":
        
        if lower.search(element.attrib['k']):
            keys['lower'] += 1
        elif lower_colon.search(element.attrib['k']):
            keys['lower_colon'] += 1
        elif problemchars.search(element.attrib['k']):
            keys['problemchars'] += 1
        else:
            keys['other'] += 1
    return keys

def process_map(filename):
    keys = {"lower": 0, "lower_colon": 0, "problemchars": 0, "other": 0}
    for _, element in ET.iterparse(filename):
        keys = key_type(element, keys)
    return keys


# Part 3 - exploring users unique  ----------------------
import xml.etree.cElementTree as ET
import pprint
import re

def process_map(filename):
    users = set()
    for _, element in ET.iterparse(filename):
        if element.tag == 'node':
            users.add(element.attrib['user'])
    return users

# Part 4 - improving street names  ----------------------

import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint

OSMFILE = "sample.osm"
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road",
            "Trail", "Parkway", "Commons"]

# UPDATE THIS VARIABLE
mapping = { "St": "Street",
    "St.": "Street",
        "Rd.": "Road",
            'Ave': 'Avenue'
        }
def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)

def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")

def audit(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    return street_types


def update_name(name, mapping):
    for street in  street_type_re.findall(name):
        if street in mapping:
            name = name[:-len(street)]
            name = name + mapping[street]
    return name



# Part 5 - Loading into database   ----------------------

import xml.etree.cElementTree as ET
import pprint
import re
import codecs
import json
import ast

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]

def shape_element(element):
    node = {}
    '''
        node = {
        "id": None,
        "visible": None,
        "type": None,
        "pos": [None, None],
        "created": {
        "changeset": None,
        "user": None,
        "version": None,
        "uid": None,
        "timestamp": None
        },
        "address": {
        "housenumber": None,
        "postcode": None,
        "street": None
        },
        "amenity": None,
        "cuisine": None,
        "name": None,
        "phone": None
        }
        '''
    if element.tag == "node" or element.tag == "way" :
        node_refs = []
        created = {}
        address = {}
        for tag in element.iter("tag"):
            temp = tag.attrib['k']
            if temp[:5] == 'addr:':
                rest = temp[5:]
                if problemchars.search(rest) or lower_colon.search(rest):
                    pass
                else:
                    address[rest] = tag.attrib['v']
        try:
            node['id'] = element.attrib['id']
            node['visible'] = element.attrib['visible']
            
            node['type'] = element.tag
            node['pos'] = [ast.literal_eval(element.attrib['lat']), ast.literal_eval(element.attrib['lon'])]
            created['changeset'] =  element.attrib['changeset']
            created['user'] = element.attrib['user']
            created['version'] = element.attrib['version']
            created['uid'] = element.attrib['uid']
            created['timestamp'] = element.attrib['timestamp']
        except:
            pass
node['created'] = created
    if address != {}:
        node['address'] = address
        if element.tag == "way":
            
            for nd in element.iter("nd"):
                if nd.attrib['ref']:
                    node_refs.append(nd.attrib['ref'])
        node['node_refs'] = node_refs
        return node
    else:
        return None

def process_map(file_in, pretty = False):
    file_out = "{0}.json".format(file_in)
    data = []
    with codecs.open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in):
            el = shape_element(element)
            if el:
                data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")
    return data


# --------------------- EXTRA CODE ------------------------
# get list of amenities -------

def audit_street_type(street_types, amenity):
    street_types[amenity] += 1

def is_street_name(elem):
    return (elem.attrib['k'] == "amenity")

def audit(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(int)
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])

return street_types

#get more details of those amenities
def add_to_dict(data_dict, item):
    data_dict[item] += 1

def get_details(element):
    attr_list = []
    for tag in element:
        attr_list.append(tag.attrib['k'])
        if (tag.attrib['k'] == "building"):
            print tag.attrib['v']
        if tag.attrib['k'] == "addr:street":
            postcode = tag.attrib['v']
            return postcode
    print attr_list
    return ''

def audit(osmfile):
    osm_file = open(osmfile, "r")
    data_dict = defaultdict(int)
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if (tag.attrib['k'] == "amenity"):
                    if (tag.attrib['v'] == "university"):
                        detail = get_details(elem.iter("tag"))
                        add_to_dict(data_dict, detail)

    return data_dict

def compress_postcodes(food_dict, pub_dict):
    a = defaultdict(int)
    b = defaultdict(int)
    for each in food_dict:
        add_to_dict(a, each[:3])
    for each in pub_dict:
        add_to_dict(b, each[:3])
    return (a,b)

#print all street names
def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        street_types[street_type].add(street_name)

def get_all_street_names(a):
    b = {}
    for key, value in sorted(a.items()):
        b[key] = len([item for item in value if item])
    return b

