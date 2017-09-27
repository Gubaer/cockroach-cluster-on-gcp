# Requirements
## pip
```bash
# install pip
% sudo apt install python-pip
# or, if pip is already installed, upgrade it
% sudo pip install -U pip
```

## protoc, the protobuf compiler
```bash
# clone the protobuf git repo
% git clone https://github.com/google/protobuf/
# compile and install it
% sudo apt-get install autoconf automake libtool curl make g++ unzip
% cd protobuf
% ./autogen.sh
% ./configure
% make
% make check
% sudo make install
% sudo ldconfig 
# should display help information after successful installation
% protoc -h
```

## imposm
python module to import osm data from a pbf file
```bash
# you need protoc to run the installation. Install it with the instructions
# above, if missing
% sudo pip install imposm
# if this fails because of missing 'tcutil.h', then install
# libtokyocabinet-dev and run 'pip install' again
% sudo apt install libtokyocabinet-dev
```

# Create or drop the database
You need the public ip address of one of the cluster nodes:
```bash
% cd ansible
% ./gce.py --refresh-cache --pretty | grep gce_public_ip
"gce_public_ip": "<public-ip>", 
"gce_public_ip": "<public-ip>",
```

## Create the database
```bash
% cockroach sql --host <public-ip> --certs-dir ../ansible/certs
root@public-ip> /* run the sql script to create the database */
root@public-ip> \| cat create-osm-db.sql
```

# Drop the database
```bash
% cockroach sql --host <public-ip> --certs-dir ../ansible/certs
root@public-ip> /* drop the database*/
root@public-ip> drop database osm;
```


