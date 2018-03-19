#
# imports OSM nodes into a crdb cluster
#
import re
import json
import subprocess
from osm_importer.parallel import Reader
import argparse


DEFAULT_IMPORT_FILE='switzerland-latest.osm.pbf'
DEFAULT_GCE_PY_COMMAND="../ansible/gce.py"

def cluster_ip_addresses(gce_py_command=DEFAULT_GCE_PY_COMMAND):
    """Reads and replies the list of public crdb ip addresses in
    the remote crdb cluster"""
    ip_addresses = []
    inventory = json.loads(subprocess.check_output([gce_py_command, "--pretty"]))
    nodes = inventory["tag_cockroachdb-cluster-node"]
    ip_addresses = []
    for node in nodes:
        ip_addresses.append(inventory["_meta"]["hostvars"][node]["gce_public_ip"])
    return ip_addresses


def main():
    parser = argparse.ArgumentParser(
        prog="python import-osm-parallel.py")
    parser.add_argument("-i", "--input-file", dest="input_file",
        help="input file",
        default=DEFAULT_IMPORT_FILE, required=False, metavar="file")
    parser.add_argument("-c", "--gce-py-command", dest="gce_py_command",
        help="full path to the 'gce.py' command",
        default=DEFAULT_GCE_PY_COMMAND, required=False, metavar="path")
    args = parser.parse_args()
    ip_addresses = cluster_ip_addresses(args.gce_py_command)
    print("cluster ip addresses: {}".format(ip_addresses))

    reader = Reader()
    reader.setup(ip_addresses)
    reader.import_file(args.input_file)
    reader.tear_down()

if __name__ == "__main__":
    main()

