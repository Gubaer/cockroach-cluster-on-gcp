#
# import-nodes.py - imports the nodes in an OSM export file into a cockroach
# database
#
from imposm.parser import OSMParser
import psycopg2
import psycopg2.extras
import json

DEFAULT_IMPORT_FILE='switzerland-latest.osm.pbf'
BATCH_SIZE=1000

class ImportHandler(object):
    """Provides methods for importing nodes, ways, or relations. They are invoked
    as callback methods by the OSM parser."""
    conn = None
    cur = None
    node_batch = []
    # a list of tuples with entries for the table node_tags, 
    # (osmid, key, value)
    tag_batch = []
    total_count = 0

    def __init__(self, conn):
        self.conn = conn
        self.conn.set_session(autocommit=False)
        self.cur = conn.cursor()

    def tearDown(self):
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

    def cache(self, osmid, tags, coords):
        (lat, lon) = coords
                    # id, version, lat, changeset_id, visible, timestamp
        values = """({}, 1, {},  {},  1, true, NOW())""".format(osmid, lat, lon)
        self.node_batch.append(values)
        for key, value in tags.items():
            self.tag_batch.append((osmid, key, value))

    def submit_cache(self):
        print("Inserting {} nodes with {} tags, total {} nodes  ...".format(
            len(self.node_batch), len(self.tag_batch), self.total_count))

        # insert the nodes
        statement = """
               INSERT INTO osm.nodes 
                  (id, version, lat, lon, changeset_id, visible, \"timestamp\")
                VALUES
        """
        statement += ",".join(self.node_batch) + ";\n"
        self.cur.execute(statement)

        # insert the node tags
        insert_query = """
            INSERT INTO osm.node_tags
              (node_id, key, value)
            VALUES %s
        """
        #psycopg2.extras.execute_values(
        #    self.cur, insert_query, self.tag_batch, page_size=BATCH_SIZE
        #)
        self.conn.commit()

    def nodes(self, nodes):
        for osmid, tags, coords in nodes:
            self.cache(osmid, tags, coords)
            if len(self.node_batch) >= BATCH_SIZE:
                self.submit_cache()
                self.total_count += len(self.node_batch)
                self.node_batch = []
                self.tag_batch = []

host = "104.196.112.216"
conn = psycopg2.connect(
    database='osm',
    host=host, port=26257, user="root",
    sslcert="../ansible/certs/{}/node.crt".format(host),
    sslkey="../ansible/certs/{}/node.key".format(host),
    sslrootcert="../ansible/certs/{}/ca.crt".format(host)
    )
handler = ImportHandler(conn)
parser = OSMParser(concurrency=10, nodes_callback=handler.nodes)
parser.parse(DEFAULT_IMPORT_FILE)
handler.tearDown()
