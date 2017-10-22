#
# generates the CVS files to be imported in the cockroach db
#from imposm.parser import OSMParserfrom imposm.parser import OSMParser
from imposm.parser import OSMParser
import csv

DEFAULT_IMPORT_FILE='switzerland-latest.osm.pbf'


class CsvExportHandlerForNodes(object):
    """Generates the CSV file to import nodes"""
    writer = None

    def __init__(self, writer):
        """Initializer
        
        Keyword arguments:
        writer -- a csv writer. Must not be None.
        """
        assert writer != None
        self.writer = writer

    def nodes(self, nodes):
        for osmid, tags, coords in nodes:
            (lat, lon) = coords
            self.writer.writerow([osmid, 1, lat, lon, 1, True])

with open("nodes.csv", "wb") as csvfile:
    nodewriter = csv.writer(csvfile, delimiter=",")
    handler = CsvExportHandlerForNodes(nodewriter)
    parser = OSMParser(concurrency=10, nodes_callback=handler.nodes)
    parser.parse(DEFAULT_IMPORT_FILE)


