# Requirements
## pip
```bash
# install pip
$ sudo apt install python-pip
# or, if pip is already installed, upgrade it
$ sudo pip install -U pip
```

## protoc, the protobuf compiler
```bash
# clone the protobuf git repo
$ git clone https://github.com/google/protobuf/
# compile and install it
$ sudo apt-get install autoconf automake libtool curl make g++ unzip
$ cd protobuf
$ ./autogen.sh
$ ./configure
$ make
$ make check
$ sudo make install
$ sudo ldconfig 
# should display help information after successful installation
$ protoc -h
```

## imposm
python module to import osm data from a pbf file
```bash
# you need protoc to run the installation. Install it with the instructions
# above, if missing
$ sudo pip install imposm
# if this fails because of missing 'tcutil.h', then install
# libtokyocabinet-dev and run 'pip install' again
$ sudo apt install libtokyocabinet-dev
```


# Create or drop the database
You need the public ip address of one of the cluster nodes:
```bash
$ cd ansible
$ ./gce.py --refresh-cache --pretty | grep gce_public_ip
"gce_public_ip": "<public-ip>", 
"gce_public_ip": "<public-ip>",
```

## Create the database
```bash
$ cd osm-poc
$ cockroach sql --host <public-ip> --certs-dir ../ansible/certs
root@public-ip> /* run the sql script to create the database */
root@public-ip> \| cat create-osm-db.sql
```

## Drop the database
```bash
$ cd osm-poc
$ cockroach sql --host <public-ip> --certs-dir ../ansible/certs
root@public-ip> /* drop the database*/
root@public-ip> drop database if exists osm cascade;
```

# Access the admin web UI for the cluster

The admin web UI is exposed by every node in the cluster, but you have to use a port forwarding SSH
tunnel to access it

```bash
# you can find the required IP addresses in the output of
#  gce.py --refresh-cache --pretty
#

$ NODE_PUBLIC_IP=<the public ip of cluster node>
$ NODE_PRIVATE_IP=<the private ip of the same node>

# -i ... : the path to the private key of the used identity (replace with you path)
# -L ... : port forwarding from remote 8080 to local 8080
# kgkacon@... : the remote ssh user (replace with your user)
#
$ ssh -i ~/.ssh/kgkacon -L 8080:${NODE_PRIVATE_IP}:8080 kgkacon@${NODE_PUBLIC_IP}

# launch a local browser with http://localhost:8080 to access the admin web UI exposed
# by the cluster node ${NODE_PUBLIC_IP}
```

# Using a docker container 
## build the container
```bash
# this will build the cocker container with the tag 'gubaer/crdb-cluster-control-node'
# run this in the root directory of this repository
$ sudo docker build -t gubaer/crdb-cluster-control-node -f docker/crdb-cluster-control-node.docker .
```

## run the container 
```bash
# launch the container
$ sudo docker run \
    -ti \
    -v $(pwd):/control-node-home \
    gubaer/crdb-cluster-control-node
# shell prompt in the container 
root@dc2fb7dce0e2:/#
```

# Load the cluster with OSM data
```bash
# loads the data from `switzerland-latest.osm.pbf` into the crdb cluster
$ python import-osm-parallel.py
```
