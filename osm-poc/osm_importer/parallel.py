from multiprocessing import Process, Queue
import psycopg2
import psycopg2.sql
from threading import Thread
from imposm.parser import OSMParser

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
          (id, version, lat, lon, changeset_id, visible, \"timestamp\")
       VALUES
       {}
       RETURNING NOTHING;
    """
    INSERT_TEMPLATE_NODE_TAGS = """
       INSERT INTO osm.node_tags
          (node_id, key, value)
       VALUES
       {}
       RETURNING NOTHING;
    """

    def _insert_nodes(self, values):
        def make_node_row(node):
            (osmid, lat, lon) = node
            return "({}, 1, {},  {},  1, true, NOW())".format(osmid, lat, lon)

        def make_node_tag_row(node_tag):
            (node_id, key, value) = node_tag
            return psycopg2.sql.SQL("({}, {}, {})").format(
                psycopg2.sql.Literal(node_id),
                psycopg2.sql.Literal(key), 
                psycopg2.sql.Literal(value)).as_string(self.cursor)

        (value_type, nodes, node_tags) = values
        print("{}/{}: inserting {} nodes ...".format(
            self.target_node, self.id, len(nodes)))
        self._insert_data(Feeder.INSERT_TEMPLATE_NODES, make_node_row, nodes)

        # insert node tags into osm.node_tags
        #
        for lower, upper, data in slices(node_tags):
            print("  {}/{}: inserting {}/{} node tags ...".format(
                self.target_node, self.id, upper-lower, len(node_tags)))
            self._insert_data(Feeder.INSERT_TEMPLATE_NODE_TAGS, make_node_tag_row, data)

    INSERT_TEMPLATE_WAYS = """
       INSERT INTO osm.ways
          (id, version, changeset_id, visible, \"timestamp\")
       VALUES
       {}
       RETURNING NOTHING;
    """
    INSERT_TEMPLATE_WAY_TAGS = """
       INSERT INTO osm.way_tags
          (way_id, key, value)
       VALUES
       {}
       RETURNING NOTHING;
    """
    INSERT_TEMPLATE_WAY_NODES = """
       INSERT INTO osm.way_nodes
          (way_id, node_id, sequence_id)
       VALUES
       {}
       RETURNING NOTHING;
    """

    def _insert_ways(self, values):
        def make_way_row(way_id):
            return "({}, 1, 1, true, NOW())".format(way_id)

        def make_way_tag_row(way_tag):
            (way_id, key, value) = way_tag
            return psycopg2.sql.SQL("({}, {}, {})").format(
                psycopg2.sql.Literal(way_id),
                psycopg2.sql.Literal(key), 
                psycopg2.sql.Literal(value)).as_string(self.cursor)

        def make_way_node_row(enumerated_way_node):
            (sequence_id, (way_id, node_id)) = enumerated_way_node
            return "({}, {}, {})".format(way_id, node_id, sequence_id)

        (value_type, ways, way_tags, way_nodes) = values

        # insert ways into osm.ways
        #
        print("{}/{}: inserting {} ways ...".format(
            self.target_node, self.id, len(ways)))
        self._insert_data(Feeder.INSERT_TEMPLATE_WAYS, make_way_row, ways)

        for lower, upper, data in slices(way_tags):
            print("  {}/{}: inserting {}/{} way tags ...".format(
                self.target_node, self.id, upper-lower, len(way_tags)))
            self._insert_data(Feeder.INSERT_TEMPLATE_WAY_TAGS, make_way_tag_row, data)

        # insert ways child nodes into osm.way_nodes
        #
        for lower, upper, data in slices_enumerated(way_nodes):
            print("  {}/{}: inserting {}/{} way nodes ...".format(
                self.target_node, self.id, upper-lower, len(way_nodes)))
            self._insert_data(Feeder.INSERT_TEMPLATE_WAY_NODES, make_way_node_row, data)


    INSERT_TEMPLATE_RELATIONS = """
       INSERT INTO osm.relations
          (id, version, changeset_id, visible, \"timestamp\")
       VALUES
       {}
       RETURNING NOTHING;
    """
    INSERT_TEMPLATE_RELATION_TAGS = """
       INSERT INTO osm.relation_tags
          (relation_id, key, value)
       VALUES
       {}
       RETURNING NOTHING;
    """
    INSERT_TEMPLATE_RELATION_MEMBERS = """
       INSERT INTO osm.relation_members
          (relation_id, sequence_id, member_role, member_type, member_id)
       VALUES
       {}
       RETURNING NOTHING;
    """

    def _insert_relations(self, values):

        def make_relation_row(relation_id):
            return "({}, 1, 1, true, NOW())".format(relation_id)

        def make_relation_tag_row(relation_tag):
            (relation_id, key, value) = relation_tag
            return psycopg2.sql.SQL("({}, {}, {})").format(
                psycopg2.sql.Literal(relation_id),
                psycopg2.sql.Literal(key), 
                psycopg2.sql.Literal(value)).as_string(self.cursor)

        def make_relation_member_row(enumerated_value):
            (sequence_id, (relation_id, osm_id, osm_type, role)) = enumerated_value
            if osm_type == "node":
                numeric_osm_type = 0
            elif osm_type == "way":
                numeric_osm_type = 1
            elif osm_type == "relation":
                numeric_osm_type = 2
            else:
                raise Exception("unsupported osm type, got '{}'".format(osm_type))

            return psycopg2.sql.SQL("({}, {}, {}, {}, {})").format(
                psycopg2.sql.Literal(relation_id),
                psycopg2.sql.Literal(sequence_id), 
                psycopg2.sql.Literal(role),
                psycopg2.sql.Literal(numeric_osm_type),
                psycopg2.sql.Literal(osm_id)).as_string(self.cursor)

        (value_type, relations, relation_tags, relation_members) = values
        
        # insert relations into osm.relations
        #
        print("{}/{}: inserting {} relations ...".format(
            self.target_node, self.id, len(relations)))
        self._insert_data(Feeder.INSERT_TEMPLATE_RELATIONS, make_relation_row, relations)

        # insert relation tags into osm.relation_tags
        #
        for lower, upper, data in slices(relation_tags):
            print("  {}/{}: inserting {}/{} relation tags ...".format(
                self.target_node, self.id, upper-lower, len(relation_tags)))
            self._insert_data(Feeder.INSERT_TEMPLATE_RELATION_TAGS, make_relation_tag_row, data)

        # insert relation members into osm.relation_members
        for lower, upper, data in slices_enumerated(relation_members):
            print("  {}/{}: inserting {}/{} relation members ...".format(
                self.target_node, self.id, upper-lower, len(relation_members)))
            self._insert_data(Feeder.INSERT_TEMPLATE_RELATION_MEMBERS, make_relation_member_row, data)

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
    node_tag_cache = []

    # a cache of ways, with tags and child nodes, to be enqueued
    way_cache = []
    way_tag_cache = []
    way_node_cache = []

    # a cache of relations, with tags and child member nodes, to be enqueued
    relation_cache = []
    relation_tag_cache = []
    relation_member_cache = []

    def setup(self, hosts):
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
            (lat, lon) = coords
            self.node_cache.append([osmid, lat, lon])
            for key, value in tags.items():
                self.node_tag_cache.append([osmid, key, value])

            if len(self.node_cache) >= 1000:
                self.queue.put(["nodes",self.node_cache, self.node_tag_cache])
                self.node_cache = []
                self.node_tag_cache = []

    def _on_ways(self, ways):
        """callback method for the OSM parser. Invoked with a batch of parsed
        osm ways."""
        for way_id, tags, node_ids in ways:
            self.way_cache.append(way_id)
            for key, value in tags.items():
                self.way_tag_cache.append([way_id, key, value])
            for node_id in node_ids:
                self.way_node_cache.append([way_id, node_id])

            if len(self.way_cache) >= 1000:
                self.queue.put(["ways", self.way_cache, 
                    self.way_tag_cache,
                    self.way_node_cache])
                self.way_cache = []
                self.way_tag_cache = []
                self.way_node_cache = []

    def _on_relations(self, relations):
        """callback method for the OSM parser. Invoked with a batch of parsed
        osm relations."""
        for relation_id, tags, members in relations:
            self.relation_cache.append(relation_id)
            for key, value in tags.items():
                self.relation_tag_cache.append([relation_id, key, value])
            for osm_id, osm_type, role in members:
                self.relation_member_cache.append([relation_id, osm_id, osm_type, role])
            if len(self.relation_cache) >= 1000:
                self.queue.put(["relations", self.relation_cache,
                    self.relation_tag_cache,
                    self.relation_member_cache])
                self.relation_cache = []
                self.relation_tag_cache = []
                self.relation_member_cache = []

    def tear_down(self):
        for feeder in self.feeders:
            self.queue.put("DONE")

        for feeder in list(self.feeders.values):
            feeder.process.join()

    def import_file(self, file_name):
        """Parses a file and feeds and imports the parsed osm primitives
        into a remote crdb cluster
        
        Parameters:
        file_name -- the name of the input file
        """
        parser = OSMParser(concurrency=10,
            #nodes_callback=self._on_nodes,
            #ways_callback=self._on_ways,
            relations_callback=self._on_relations
        )
        parser.parse(file_name)
