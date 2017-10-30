#
# generates the CVS files to be imported in the cockroach db
#
from imposm.parser import OSMParser
import csv
import os

DEFAULT_IMPORT_FILE='switzerland-latest.osm.pbf'

class CsvExportHandlerForNodes(object):
    """Generates the CSV file to import nodes"""
    nodes_writer = None
    node_keys_writer = None

    def __init__(self, nodes_writer, node_keys_writer):
        """Initializer
        
        Keyword arguments:
        nodes_writer -- a csv writer, target for node enries. Must not be None.
        node_keys_writer -- a csv writer, target for node key entries. Must not be None
        """
        assert nodes_writer != None
        assert node_keys_writer != None
        self.nodes_writer = nodes_writer
        self.node_keys_writer = node_keys_writer

    def nodes(self, nodes):
        for osmid, tags, coords in nodes:
            (lat, lon) = coords
            self.nodes_writer.writerow([osmid, 1, lat, lon, 1, True])
            for key, value in tags.items():
                self.node_keys_writer.writerow(
                    [osmid, key.encode('utf-8'), value.encode('utf-8')]
                )

if not os.path.isdir("csv-files"):
    os.mkdir("csv-files")

with open("csv-files/nodes.csv", "wb") as nodes_csv:
    with open("csv-files/node-keys.csv", "wb") as node_keys_csv:
        print("Writing nodes to '{file}' ...".format(file="csv-files/nodes.csv"))
        print("Writing node keys to '{file}' ...".format(file="csv-files/node-keys.csv"))
        nodes_writer = csv.writer(nodes_csv, delimiter=",")
        node_keys_writer = csv.writer(node_keys_csv, delimiter=",")
        handler = CsvExportHandlerForNodes(nodes_writer, node_keys_writer)
        parser = OSMParser(concurrency=10, nodes_callback=handler.nodes)
        parser.parse(DEFAULT_IMPORT_FILE)


