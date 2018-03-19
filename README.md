# Load OSM data into a cockroachdb cluster on the Google Cloud Platform

This repository provides ressources to

* create a [cockroachdb](https://www.cockroachlabs.com) cluster on the [Google Cloud Platform ](https://cloud.google.com/?)

* [ansible](https://www.ansible.com/) playbooks to create, terminate, stop, and start the cluster

* load the cluster with a subset of the Open Street Map data 

    * DML script to create the database schema in the cockroachdb cluster
    * python scripts to upload a subset of the OSM data. Our tests used the OSM subset for Switzerland.




