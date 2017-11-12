#!/bin/bash

HOST=35.196.44.230
AWS_ACCESS_KEY_ID=AKIAIDWJOSVCATM2WRDQ
AWS_SECRET_ACCESS_KEY="QPqWa0VZerNLfwmR52oKjVFZF%2F6ct%2B4d1bifSkXL"

cockroach sql --host $HOST --certs-dir ../ansible/certs <<EOC
SET CLUSTER SETTING experimental.importcsv.enabled = true;
drop database if exists osm cascade;
create database osm;
set database = osm;

/*
IMPORT TABLE osm.nodes (
    id INT PRIMARY KEY,
    version INT NOT NULL,
    lat DECIMAL NOT NULL,
    lon DECIMAL NOT NULL,
    changeset_id INT NOT NULL,
    visible BOOLEAN NOT NULL
)
CSV DATA ('s3://cockroach-import/nodes.csv?AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}&AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}')
WITH
    temp = 's3://cockroach-import/?AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}&AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}',
    delimiter = ','
;

CREATE TABLE IF NOT EXISTS osm.nodes (
    id INT PRIMARY KEY,
    version INT NOT NULL,
    lat DECIMAL NOT NULL,
    lon DECIMAL NOT NULL,
    changeset_id INT NOT NULL,
    visible BOOLEAN NOT NULL
);

INSERT INTO osm.nodes (id, version, lat, lon, changeset_id, visible) 
SELECT id, version, lat, lon, changeset_id, visible FROM osm.nodes_csv;
*/


IMPORT TABLE osm.node_tags (
    id SERIAL NOT NULL,
    node_id INT NOT NULL,
    key STRING NOT NULL,
    value STRING NOT NULL,
    PRIMARY KEY (id)
)
CSV DATA ('s3://cockroach-import/node-keys.csv?AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}&AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}')
WITH
    temp = 's3://cockroach-import/?AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}&AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}',
    delimiter = ','
;

EOC