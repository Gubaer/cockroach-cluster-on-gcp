#
# imports OSM nodes into a crdb cluster
#
import re
import subprocess
from osm_importer.parallel import Reader


DEFAULT_IMPORT_FILE='switzerland-latest.osm.pbf'

def cluster_ip_addresses():
    """Reads and replies the list of public crdb ip addresses in
    the remote crdb cluster"""
    ip_addresses = []
    inventory = subprocess.check_output(["../ansible/gce.py", "--pretty"])
    for line in inventory.splitlines():
        if not re.search("gce_public_ip", line):
            continue
        match = re.search('\d+\.\d+\.\d+\.\d+',line)
        ip_addresses.append(match.group())
    return ip_addresses


ip_addresses = cluster_ip_addresses()
print("cluster ip addresses: {}",ip_addresses)

reader = Reader()
reader.setup(ip_addresses)
#reader.import_nodes(DEFAULT_IMPORT_FILE)
#reader.tear_down()



