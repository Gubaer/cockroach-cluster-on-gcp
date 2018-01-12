--
-- derived from the OSM database schema
-- https://github.com/openstreetmap/openstreetmap-website/blob/master/db/structure.sql
--
CREATE DATABASE IF NOT EXISTS osm;

-- have to set DATABASE, because cockroachdb doesn't accept fully qualified
-- table names in INTERLEAVE statements. Example: 
--    ... INTERLEAVE IN PARENT nodes (node_id);
-- leads to
--    pq: no database specified: "nodes"
-- and ... INTERLEAVE IN PARENT osm.nodes (node_id);
-- results in an SQL parsing error.
SET DATABASE = "osm";

CREATE TABLE IF NOT EXISTS osm.nodes (
    id INT PRIMARY KEY,
    version INT NOT NULL,
    lat DECIMAL NOT NULL,
    lon DECIMAL NOT NULL,
    changeset_id INT NOT NULL,
    visible BOOLEAN NOT NULL,
    "timestamp" TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS osm.node_tags (
    id SERIAL NOT NULL,
    node_id INT NOT NULL,
    key STRING NOT NULL,
    value STRING NOT NULL,
    PRIMARY KEY (node_id, id),
    CONSTRAINT fk_node_tags FOREIGN KEY (node_id) REFERENCES osm.nodes,
    INDEX key_value_idx (key, value)
);
--) INTERLEAVE IN PARENT nodes (node_id);

CREATE TABLE IF NOT EXISTS osm.ways (
    id INT PRIMARY KEY,
    version INT NOT NULL,
    changeset_id INT NOT NULL,
    visible BOOLEAN not null,
    "timestamp" TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS osm.way_tags (
    id SERIAL NOT NULL,
    way_id INT NOT NULL,
    key STRING NOT NULL,
    value STRING NOT NULL,
    PRIMARY KEY (way_id, id),
    CONSTRAINT fk_way_tags FOREIGN KEY (way_id) REFERENCES osm.ways,
    INDEX key_value_idx (key, value)
);
--) INTERLEAVE IN PARENT ways (way_id);

CREATE TABLE IF NOT EXISTS osm.way_nodes (
    way_id INT NOT NULL,
    node_id INT NOT NULL,
    sequence_id INT NOT NULL,
    PRIMARY KEY (way_id, node_id, sequence_id),
    CONSTRAINT fk_way FOREIGN KEY (way_id) REFERENCES osm.ways,
    --TODO: enable after tests
    --CONSTRAINT fk_node FOREIGN KEY (node_id) REFERENCES osm.nodes,
    INDEX parent_ways (node_id, way_id, sequence_id)
);
--TODO: wirklich INTERLEAVE? Was bringt das?
--) INTERLEAVE IN PARENT ways (way_id);

CREATE TABLE IF NOT EXISTS osm.relations (
    id INT PRIMARY KEY,
    version INT NOT NULL,
    changeset_id INT NOT NULL,
    visible BOOLEAN NOT NULL,
    "timestamp" TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS osm.relation_members (
    -- TODO: serial id? necessary?
    id SERIAL NOT NULL,
    relation_id INT NOT NULL,
    sequence_id INT NOT NULL DEFAULT 0,
    member_role STRING NOT NULL,
    -- 0: node, 1: way, 2: relation
    member_type INT NOT NULL,
    member_id INT NOT NULL,
    PRIMARY KEY (relation_id, sequence_id, id)
    -- disabled for testing, enable later
    -- CONSTRAINT fk_relation FOREIGN KEY (relation_id) REFERENCES osm.relations
);
-- TODO: wirlich INTERLEAVE? Was bringt das?
-- ) INTERLEAVE IN PARENT relations (relation_id);

CREATE TABLE IF NOT EXISTS osm.relation_tags (
    id SERIAL NOT NULL,
    relation_id INT NOT NULL,
    key STRING NOT NULL,
    value STRING NOT NULL,
    PRIMARY KEY (relation_id, id),
    -- disabled for testing, enabled later
    -- CONSTRAINT fk_relation_tags FOREIGN KEY (relation_id) REFERENCES osm.relations,
    INDEX key_value_idx (key, value)
);
-- TODO: wirklich INTERLEAVE? Was bringt das?
-- ) INTERLEAVE IN PARENT relations (relation_id);

