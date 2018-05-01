from multiprocessing import Process, Queue
import psycopg2
import psycopg2.sql
from threading import Thread
from imposm.parser import OSMParser
import json

_FEEDER_COUNTER=0

def slices(data, slice_size=1000):
    """Generates a sequence of slices of size slice_size for the elements
    in data. A slice is a tuple (lower, upper, data_slice) where data_slice is 
    a slice of the data array"""
    lower = 0
    upper = 0
    while lower < len(data):
        upper = min(upper + slice_size, len(data))
        yield (lower, upper, data[lower:upper])
        lower = upper

def slices_enumerated(data, slice_size=1000):
    """Generates a sequence of slices of size slice_size for the elements
    in data. A slice is a tuple (lower, upper, enumerated_data_slice) where 
    enumerated_data_slice is  a an enumearted slice of the data array"""
    lower = 0
    upper = 0
    while lower < len(data):
        upper = min(upper + slice_size, len(data))
        yield (lower, upper, list(enumerate(data[lower:upper])))
        lower = upper

class Feeder(object):
    """Reads batches of rows to be inserted into crdb tables
    and submits them to the remote crdb cluster it is connected
    to."""

    # the cursor into the remote crdb cluster
    cursor = None

    # the queue this feeder reads values from 
    queue = None

    # the ip address of the target crdb node (used build logging messages 
    # only)
    target_node = None

    # the numeric id of the feeder (to differentiate between readers
    # connected to the same remote crdb host)
    id = 0

    # the process for this feeder
    process = None

    def _insert_data(self, template, row_builder, data):
        sql = template.format(",".join(map(row_builder, data)))
        self.cursor.execute(sql)

    def __init__(self, target_node, cursor, queue):
        """
        Parameters:
        target_node --  the ip address of the target crdb node
        cursor -- the cursor into the remote crdb cluster. Must not be None.
        queue -- the queue this feeder reads values from. Must not be None.
        """
        global _FEEDER_COUNTER
        assert target_node != None
        assert cursor != None
        assert queue != None
        self.target_node = target_node
        self.cursor = cursor
        self.queue = queue
        _FEEDER_COUNTER += 1
        self.id = _FEEDER_COUNTER
        self.process = Process(target=self._run, args=())
        self.process.start()


    INSERT_TEMPLATE_NODES = """
       INSERT INTO osm.nodes 
          (id, version, lat, lon, changeset_id, visible, \"timestamp\", tags)
       VALUES
       {}
       RETURNING NOTHING;
    """

    def _insert_nodes(self, values):
        def make_node_row(node):
            (osmid, lat, lon,tags) = node
            return psycopg2.sql.SQL("({}, 1, {}, {},  1, true, NOW(), {})").format(
                psycopg2.sql.Literal(osmid),
                psycopg2.sql.Literal(lat),
                psycopg2.sql.Literal(lon),
                psycopg2.sql.Literal(json.dumps(tags))).as_string(self.cursor)

        (value_type, nodes) = values
        print("{}/{}: inserting {} nodes ...".format(
            self.target_node, self.id, len(nodes)))
        self._insert_data(Feeder.INSERT_TEMPLATE_NODES, make_node_row, nodes)


    INSERT_TEMPLATE_WAYS = """
       INSERT INTO osm.ways
          (id, version, changeset_id, visible, \"timestamp\", tags, nodes)
       VALUES
       {}
       RETURNING NOTHING;
    """

    def _insert_ways(self, values):
        def make_way_row(way):
            (way_id, tags, node_ids) = way
            return psycopg2.sql.SQL("({}, 1, 1, true, NOW(), {}, {})").format(
                psycopg2.sql.Literal(way_id),
                psycopg2.sql.Literal(json.dumps(tags)),
                psycopg2.sql.Literal(json.dumps(node_ids))).as_string(self.cursor)

        (value_type, ways) = values

        # insert ways into osm.ways
        #
        print("{}/{}: inserting {} ways ...".format(
            self.target_node, self.id, len(ways)))
        self._insert_data(Feeder.INSERT_TEMPLATE_WAYS, make_way_row, ways)


    INSERT_TEMPLATE_RELATIONS = """
       INSERT INTO osm.relations
          (id, version, changeset_id, visible, \"timestamp\", tags, members)
       VALUES
       {}
       RETURNING NOTHING;
    """

    def _insert_relations(self, values):

        def make_relation_row(relation):
            (relation_id, tags, members) = relation
            return psycopg2.sql.SQL("({}, 1, 1, true, NOW(), {}, {})").format(
                psycopg2.sql.Literal(relation_id),
                psycopg2.sql.Literal(json.dumps(tags)), 
                psycopg2.sql.Literal(json.dumps(members))).as_string(self.cursor)

        (value_type, relations) = values
        
        # insert relations into osm.relations
        #
        print("{}/{}: inserting {} relations ...".format(
            self.target_node, self.id, len(relations)))
        #TODO: catch InternalError: transaction is too large to complete; try splitting into pieces
        #split into two halfs and retry
        self._insert_data(Feeder.INSERT_TEMPLATE_RELATIONS, make_relation_row, relations)

    def _insert_values(self, values):
        value_type = values[0]
        if value_type == "nodes":
            self._insert_nodes(values)
        elif value_type == "ways":
            self._insert_ways(values)
        elif value_type == "relations":
            self._insert_relations(values)
        else:
            raise Exception("Illegal value type: {}".format(value_type))

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
    # a cache of ways, with tags and child nodes, to be enqueued
    way_cache = []
    # a cache of relations, with tags and child member nodes, to be enqueued
    relation_cache = []

    def setup(self, hosts, certs_dir="../../ansible/certs"):
        """Setup the connection to the remote crdb cluster.

        Parameters:
        hosts -- a list of public IP addresses exposed by the cluster
        """
        self.queue = Queue(len(hosts))
        self.cursors = {}
        self.feeders = {}

        # open the connections and launch the feeder
        for host in hosts:
            connection = psycopg2.connect(
                database='osm',
                host=host, port=26257, user="root",
                sslcert="{}/{}/node.crt".format(certs_dir,host),
                sslkey="{}/{}/node.key".format(certs_dir,host),
                sslrootcert="{}/{}/ca.crt".format(certs_dir,host)
            )
            connection.set_session(autocommit=True)
            self.cursors[host] = connection.cursor()
            self.feeders[host] = Feeder(host, self.cursors[host], self.queue)

    def _on_nodes(self, nodes):
        """callback method for the OSM parser. Invoked with a batch of parsed
        osm nodes."""
        for osmid, tags, coords in nodes:
            (lat, lon) = coords
            self.node_cache.append([osmid, lat, lon, tags])

            if len(self.node_cache) >= 1000:
                self.queue.put(["nodes",self.node_cache])
                self.node_cache = []

    def _way_cache_weight(self):
        return sum(
            map(lambda entry: 1 + len(entry[1]) + len(entry[2]), self.way_cache)
        )

    def _on_ways(self, ways):
        """callback method for the OSM parser. Invoked with a batch of parsed
        osm ways."""
        for way_id, tags, node_ids in ways:
            self.way_cache.append([way_id, tags, node_ids])

            if self._way_cache_weight() >= 5000:
                self.queue.put(["ways", self.way_cache])
                self.way_cache = []

    def _relation_cache_weight(self):
        return sum(
            map(lambda entry: 1 + len(entry[1]) + len(entry[2]), self.relation_cache)
        )

    def _on_relations(self, relations):
        """callback method for the OSM parser. Invoked with a batch of parsed
        osm relations."""
        for relation_id, tags, members in relations:
            self.relation_cache.append((relation_id, tags, members))

            # 3000: estimated, 5000 results in spurious "transaction too large"
            # errors
            if self._relation_cache_weight() >= 3000:
                self.queue.put(["relations", self.relation_cache])
                self.relation_cache = []

    def tear_down(self):
        for feeder in self.feeders:
            self.queue.put("DONE")

        for feeder in self.feeders.values():
            feeder.process.join()

    def import_file(self, file_name):
        """Parses a file, feeds and imports the parsed osm primitives
        into a remote crdb cluster
        
        Parameters:
        file_name -- the name of the input file
        """
        parser = OSMParser(concurrency=10,
            nodes_callback=self._on_nodes,
            ways_callback=self._on_ways,
            relations_callback=self._on_relations
        )
        parser.parse(file_name)
