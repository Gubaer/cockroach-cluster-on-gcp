
# Dependencies

In order to run the ansible playbooks provided in this repo you need 
1. [ansible](http://docs.ansible.com/ansible/intro_installation.html)
2. pip 
```
# install python pip
% sudo apt-get install python-pip
```
3. apache-libcloud, Version 1.5.0 (Version 2.0.0 and higher don't work yet)
```
# install apache-libcloud
% sudo pip install apache-libcloud==1.5.0
```

# Prepare Google Compute Plattform

Log into the Google [Clould Plattform console](https://console.cloud.google.com/).

1. Create a project, i.e. `cockroachdb-cluster`
2. Create a service account in the project, i.e. `cockroachdbuser` and assign it the role `owner`
3. Create a key for the new user and download the credentials. You will need this file
   as credentials when you run the ansible playbooks.

# Create and control the cluster

## initialize the required environment variables

```bash
# make sure the required environment variables are set
$ cp ./gce.env.distrib gce.env
# launch an editor and configure the environment variables in gce.env
# vi ./gce.env

# make the environment variables available in the current shell
$ source ./gce.env
```
## create the cluster
The following playbook will create the disk, the virtual network, and the GCE virtual machines for
the cluster. Machines will be prepared to run as cockroachdb node.

```bash
# start the playbook and enter the number of nodes in the cluster. Should be an even
# number >=2 
$ ansible-playbook create-cluster.yml
Number of cluster nodes (n>=2, choose an even number) [default=2] [2]: <enter a number>
```

## terminate the cluster
```bash
# start the playbook and enter the number of nodes in the cluster
$ ansible-playbook terminate-cluster.yml
Number of cluster nodes (n>=2, choose an even number) [default=2] [2]: <enter a number>
```

## stop the cluster
```bash
$ ansible-playbook stop-cluster.yml
Number of cluster nodes (n>=2, choose an even number) [default=2] [2]: <enter a number>
```

## (re-)start the cluster
```bash
# starts a stopped cluster. 
$ ansible-playbook start-cluster.yml
Number of cluster nodes (n>=2, choose an even number) [default=2] [2]: <enter a number>
```


# Connect to the cluster from a local cockroach sql client

Every cockroach node in the cluster is accessible from outside using the
built-in [cockroach sql client](https://www.cockroachlabs.com/docs/stable/use-the-built-in-sql-client.html).

The cluster is configured as secure cluster. When you point the local sql client
to one of the cluster nodes using the command line option `--host <public-ip-address>`, you have 
to pass in the `certs` directory where the CA certificate and the user certificates are stored, see command line option `--certs-dir`.

The public ip addresses of the cockroach db nodes are available either

* in the [instance list](https://console.cloud.google.com/compute/instances) in the GCP console

* in the dynamic ansible repository 
  ```bash
  # look for 'gce_public_ip' in the output of this command
  % ./gce.py --refresh-cache --pretty
  ```

```bash
# connect to a cockroacĥ node with the user root (root is assumed if no other user is 
# specified on the command line)
# in path/to/certs/file cockroach should find
#  - ca.crt
#  - client.root.crt
% cockroach sql \
    --host=<public-ip-address> \
    --certs-dir=path/to/certs/dir \
    --database=<database-name>
```

Or, with a specific user:

```bash
# connect to a cockroack node with the user root.
# iIn path/to/certs/file cockroach should find
#  - ca.crt
#  - client.root.crt
% cockroach sql \
    --user=root \
    --host=<public-ip-address> \
    --certs-dir=path/to/certs/dir \
    --database=<database-name>
```

# Run a test scenario

- Select two nodes in the cockroach cluster with the public ip addresses
  - `node-ip-1`
  - `node-ip-2`

- Connect to the first node and create a database `test`
  ```bash
  % cockroach sql --host=<node-ip-1> --certs-dir=path/to/certs/dir
  root@node-ip-1> create database test;
  root@node-ip-1> \q
  ```

- Connect to the first node, create a table and enter some data
  (following [this example](https://www.cockroachlabs.com/docs/stable/use-the-built-in-sql-client.html))

  ```bash
  % cockroach sql --host=<node-ip-1> --certs-dir=path/to/certs/dir --database=test
  root@node-ip-1> CREATE TABLE animals (id SERIAL PRIMARY KEY, name STRING);
  root@node-ip-1> INSERT INTO animals (name) VALUES ('bobcat'), ('barn owl');
  root@node-ip-1> SELECT * FROM animals;
  +--------------------+----------+
  |         id         |   name   |
  +--------------------+----------+
  | 148899952591994881 | bobcat   |
  | 148899952592093185 | barn owl |
  +--------------------+----------+
  root@node-ip-1> \q
  ```

- Connect to the second node and check whether the data is available too

  ```bash
  % cockroach sql --host=<node-ip-2> --certs-dir=path/to/certs/dir --database=test
  root@node-ip-1> SELECT * FROM animals;
  +--------------------+----------+
  |         id         |   name   |
  +--------------------+----------+
  | 148899952591994881 | bobcat   |
  | 148899952592093185 | barn owl |
  +--------------------+----------+
  root@node-ip-1> \q
  ```

