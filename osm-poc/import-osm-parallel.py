#
# imports OSM nodes into a crdb cluster
#
import re
import json
import subprocess
from osm_importer.parallel import Reader


DEFAULT_IMPORT_FILE='switzerland-latest.osm.pbf'

def cluster_ip_addresses():
    """Reads and replies the list of public crdb ip addresses in
    the remote crdb cluster"""
    ip_addresses = []
    inventory = json.loads(subprocess.check_output(["../ansible/gce.py", "--pretty"]))
    nodes = inventory["tag_cockroachdb-cluster-node"]
    ip_addresses = []
    for node in nodes:
        ip_addresses.append(inventory["_meta"]["hostvars"][node]["gce_public_ip"])
    return ip_addresses


ip_addresses = cluster_ip_addresses()
print("cluster ip addresses: {}".format(ip_addresses))

reader = Reader()
reader.setup(ip_addresses)
reader.import_file(DEFAULT_IMPORT_FILE)
reader.tear_down()



