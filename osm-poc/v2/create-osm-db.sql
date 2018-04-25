--
-- derived from the OSM database schema
-- https://github.com/openstreetmap/openstreetmap-website/blob/master/db/structure.sql
--
CREATE DATABASE IF NOT EXISTS osm;

CREATE TABLE IF NOT EXISTS osm.nodes (
    id INT PRIMARY KEY,
    version INT NOT NULL,
    lat DECIMAL NOT NULL,
    lon DECIMAL NOT NULL,
    changeset_id INT NOT NULL,
    visible BOOLEAN NOT NULL,
    "timestamp" TIMESTAMP NOT NULL,
    tags JSONB,
    INVERTED INDEX node_tags_index (tags)
);

CREATE TABLE IF NOT EXISTS osm.ways (
    id INT PRIMARY KEY,
    version INT NOT NULL,
    changeset_id INT NOT NULL,
    visible BOOLEAN not null,
    "timestamp" TIMESTAMP NOT NULL,
    tags JSONB,
    nodes JSONB,
    INVERTED INDEX way_tags_index (tags),
    INVERTED INDEX way_nodes_index (nodes)
);

CREATE TABLE IF NOT EXISTS osm.relations (
    id INT PRIMARY KEY,
    version INT NOT NULL,
    changeset_id INT NOT NULL,
    visible BOOLEAN NOT NULL,
    "timestamp" TIMESTAMP NOT NULL,
    tags JSONB,
    members JSONB,
    INVERTED INDEX relation_tags_index (tags),
    INVERTED INDEX relation_members_index (members)
);