#
# generates the CVS files to be imported in the cockroach db
#
from imposm.parser import OSMParser
import csv
import os

DEFAULT_IMPORT_FILE='switzerland-latest.osm.pbf'

class CsvExportHandler(object):
    """Generates the CSV file to import nodes"""
    nodes_writer = None
    node_keys_writer = None
    ways_writer = None
    way_keys_writer = None
    way_nodes_writer = None

    def __init__(self, 
        nodes_writer, node_keys_writer,
        ways_writer, way_keys_writer, way_nodes_writer
        ):
        """Initializer
        
        Keyword arguments:
        nodes_writer -- a csv writer, target for node enries. Must not be None.
        node_keys_writer -- a csv writer, target for node key entries. Must not be None
        ways_writer -- a csv writer, target for way enteries. Must not be None.
        way_keys_writer -- a csv writer, target for way key entries. Must not be None.
        way_nodes_writer -- a csv writer, taarget for way nodes. Must not be None 
        """
        assert nodes_writer != None
        assert node_keys_writer != None
        assert ways_writer != None
        assert way_keys_writer != None
        assert way_nodes_writer != None

        self.nodes_writer = nodes_writer
        self.node_keys_writer = node_keys_writer
        self.ways_writer = ways_writer
        self.way_keys_writer = way_keys_writer
        self.way_nodes_writer = way_nodes_writer

    def nodes(self, nodes):
        for osmid, tags, coords in nodes:
            (lat, lon) = coords
            self.nodes_writer.writerow([osmid, 1, lat, lon, 1, True])
            for key, value in tags.items():
                self.node_keys_writer.writerow(
                    [osmid, key.encode('utf-8'), value.encode('utf-8')]
                )

    def ways(self, ways):
        for osmid, tags, refs in ways:
            self.ways_writer.writerow(
                [osmid, 1, 1, True]
            )
            for key, value in tags.items():
                self.way_keys_writer.writerow(
                    [osmid, key.encode('utf-8'), value.encode('utf-8')]
                )
            for idx, ref in enumerate(refs):
                self.way_nodes_writer.writerow(
                    [osmid, ref, idx]
                )

if not os.path.isdir("csv-files"):
    os.mkdir("csv-files")

with open("csv-files/nodes.csv", "wb") as nodes_csv, \
    open("csv-files/node-keys.csv", "wb") as node_keys_csv, \
    open("csv-files/ways.csv", "wb") as ways_csv, \
    open("csv-files/way_keys.csv", "wb") as way_keys_csv, \
    open("csv-files/way_nodes.csv", "wb") as way_nodes_csv:
        handler = CsvExportHandler(
            csv.writer(nodes_csv, delimiter=","),
            csv.writer(node_keys_csv, delimiter=","),
            csv.writer(ways_csv, delimiter=","),
            csv.writer(way_keys_csv, delimiter=","),
            csv.writer(way_nodes_csv, delimiter=",")
        )
        parser = OSMParser(concurrency=10, 
            nodes_callback=handler.nodes,
            ways_callback=handler.ways
        )
        parser.parse(DEFAULT_IMPORT_FILE)


