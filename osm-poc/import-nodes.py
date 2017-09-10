#
# import-nodes.py - imports the nodes in an OSM export file into a cockroach
# database; bare nodes only, without tags
#
from imposm.parser import OSMParser
import psycopg2

DEFAULT_IMPORT_FILE='switzerland-latest.osm.pbf'
BATCH_SIZE=1000

class ImportHandler(object):
    """Provides methods for importing nodes, ways, or relations. They are invoked
    as callback methods by the OSM parser."""
    conn = None
    cur = None
    batch_count = 0
    total_count = 0
    batch = []

    def __init__(self, conn):
        self.conn = conn
        conn.set_session(autocommit=True)
        self.cur = conn.cursor()

    def tearDown(self):
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

    def nodes(self, nodes):
        for osmid, tags, coords in nodes:
            (lat, lon) = coords
                        # id, version, lat, changeset_id, visible, timestamp
            values = """({}, 1, {},  {},  1, true, NOW())""".format(osmid, lat, lon)
            self.batch.append(values)
            self.batch_count +=1
            if self.batch_count >= BATCH_SIZE:
                statement = """
                   INSERT INTO osm.nodes 
                      (id, version, lat, lon, changeset_id, visible, \"timestamp\")
                    VALUES
                """
                statement += ",".join(self.batch)
                statement += ";"
                print("Inserting {} nodes, total {} nodes ..."
                    .format(BATCH_SIZE, self.total_count))
                self.cur.execute(statement)
                self.batch = []
                self.batch_count = 0
                self.total_count += BATCH_SIZE

conn = psycopg2.connect(
    database='osm',
    host='35.196.25.50', port=26257, user="root",
    sslcert="../ansible/certs/35.196.25.50/node.crt",
    sslkey="../ansible/certs/35.196.25.50/node.key",
    sslrootcert="../ansible/certs/35.196.25.50/ca.crt"
    )
handler = ImportHandler(conn)
parser = OSMParser(concurrency=10, nodes_callback=handler.nodes)
parser.parse(DEFAULT_IMPORT_FILE)
handler.tearDown()
