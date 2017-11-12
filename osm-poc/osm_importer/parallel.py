from Queue import Queue
import psycopg2
import psycopg2.sql
from threading import Thread
from imposm.parser import OSMParser

class Feeder(object):
    """Reads batches of rows to be inserted into a crdb table
    and submits them to the remote crdb cluster it is connected
    to."""

    INSERT_TEMPLATE_NODES = """
       INSERT INTO osm.nodes 
          (id, version, lat, lon, changeset_id, visible, \"timestamp\")
       VALUES
    """
    INSERT_TEMPLATE_NODE_TAGS = """
       INSERT INTO osm.node_tags 
          (node_id, key, value)
       VALUES
    """

    # the cursor into the remote crdb cluster
    cursor = None

    # the queue this feeder reads values from 
    queue = None

    # the ip address of the target crdb node
    target_node = None

    def __init__(self, target_node, cursor, queue):
        """
        Parameters:
        target_node --  the ip address of the target crdb node
        cursor -- the cursor into the remote crdb cluster. Must not be None.
        queue -- the queue this feeder reads values from. Must not be None.
        """
        assert target_node != None
        assert cursor != None
        assert queue != None
        self.target_node = target_node
        self.cursor = cursor
        self.queue = queue
        thread = Thread(target=self._run, args=())
        thread.start()

    def _insert_values(self, values):
        def make_node_row(node):
            (osmid, lat, lon) = node
            return "({}, 1, {},  {},  1, true, NOW())".format(osmid, lat, lon)

        def make_node_tag_row(node_tag):
            (node_id, key, value) = node_tag
            return psycopg2.sql.SQL("({}, {}, {})").format(
                psycopg2.sql.Literal(node_id),
                psycopg2.sql.Literal(key), 
                psycopg2.sql.Literal(value)).as_string(self.cursor)

        (nodes, node_tags) = values
        sql = Feeder.INSERT_TEMPLATE_NODES
        sql += ",".join(map(make_node_row, nodes)) + ";\n"
        print("{}: inserting {} nodes ...".format(self.target_node, len(nodes)))
        self.cursor.execute(sql)

        sql = Feeder.INSERT_TEMPLATE_NODE_TAGS
        sql += ",".join(map(make_node_tag_row, node_tags)) + ";\n"
        print("{}: inserting {} node tags ...".format(self.target_node, len(node_tags)))
        self.cursor.execute(sql)

    def _run(self):
        """Reads values from the queue and and feeds them to the remote
        crdb cluster"""
        print("{}: feeder is running ...".format(self.target_node))
        while True:
            msg = self.queue.get()
            if msg == "DONE":
                print("{}: shutting down ...".format(self.target_node))
                break
            elif isinstance(msg, list):
                self._insert_values(msg)
            else:
                # unexpected value. Report and break.
                print("FATAL: unexpected value in queue: {}".format(msg))
                break

class Reader(object):
    """Reads osm data from an file and submits it to a collection
    of concurrent feeders. 
    """
    # a dictionary of open crdb cursors. The key is the ip address of a crdb
    # node in the remote crdb cluster
    cursors = None
    # the queue to communicate between the reader and the feeders
    queue = None
    # a dictionary of feeders. The key is the is the ip address of a crdb node
    # in the remote crdb cluster
    feeders = None
    # a cache of nodes pending to be submitted to the queue
    node_cache = []
    node_tag_cache = []

    def __init__(self):
        pass

    def setup(self, hosts):
        """Setup the connection to the remote crdb cluster.

        Parameters:
        hosts -- a list of public IP addresses exposed by the cluster
        """

        self.queue = Queue(10)
        self.cursors = {}
        self.feeders = {}

        # open the connections and launch the feeder
        for host in hosts: 
            connection = psycopg2.connect(
                database='osm',
                host=host, port=26257, user="root",
                sslcert="../ansible/certs/{}/node.crt".format(host),
                sslkey="../ansible/certs/{}/node.key".format(host),
                sslrootcert="../ansible/certs/{}/ca.crt".format(host)
            )
            connection.set_session(autocommit=True)
            self.cursors[host] = connection.cursor()
            self.feeders[host] = Feeder(host, self.cursors[host], self.queue)

    def _on_nodes(self, nodes):
        """callback method for the OSM parser. Invoked with a batch of parsed
        osm nodes."""
        for osmid, tags, coords in nodes:
            #print("processing node {} ...".format(osmid))
            (lat, lon) = coords
            self.node_cache.append([osmid, lat, lon])
            for key, value in tags.items():
                self.node_tag_cache.append([osmid, key, value])

            if len(self.node_cache) >= 1000:
                self.queue.put([self.node_cache, self.node_tag_cache])
                self.node_cache = []
                self.node_tag_cache = []

    def tear_down(self):
        for feeder in self.feeders:
            self.queue.put("DONE")

    def import_nodes(self, file_name):
        """Parses a file and feeds and imports the parsed nodes into a
        remote crdb cluster
        
        Parameters:
        file_name -- the name of the input file
        """
        parser = OSMParser(concurrency=10, nodes_callback=self._on_nodes)
        parser.parse(file_name)
