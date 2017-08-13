
# Dependencies

In order to run the ansible playbooks provided in this repo you need 
1. [ansible](http://docs.ansible.com/ansible/intro_installation.html)
2. pip 
```
% sudo apt-get install python-pip
```
3. apache-libcloud, Version 1.5.0 (Version 2.0.0 and higher don't work yet)
```
% sudo pip install apache-libcloud==1.5.0
```

# Prepare Google Compute Plattform

Log into the Google [Clould Plattform console](https://console.cloud.google.com/).

1. Create a project, i.e. `cockroachdb-cluster`
2. Create a service account in the project, i.e. `cockroachdbuser` and assign it the role `owner`
3. Create a key for the new user, download the credentials. You will need this file
   als credentials when you run the ansible playbooks.


# Connect to the cluster from a local cockroach sql client

Every cockroach node in the cluster is accessible from outside using the
built-in [cockroach sql client](https://www.cockroachlabs.com/docs/stable/use-the-built-in-sql-client.html).

The cluster is configured as secure cluster. When point the local sql client
to one of the cluster nodes using the command line option `--host <public-ip-address>`, you have pass in the certs directory where the CA 
certificate and the user certificate are stored.

The public ip addresses of the cockroach db nodes are availbe either
- in the [instance list](https://console.cloud.google.com/compute/instances)
  in the GCP console

- in the dynamic ansible repository 
  ```bash
  # look for 'gce_public_ip' in the output of this command
  % ./gce.py --refresh-cache --pretty
  ```

```bash
# connect to a cockroack node with the (implicit) user root
# in path/to/certs/file cockroach should find
#  - ca.crt
#  - client.root.crt
% cockroach sql \
    --host=<public-ip-address> \
    --certs-dir=path/to/certs/dir
    --database=<database-name>
```
Or if you want to be explicit about the user:

```bash
# connect to a cockroack node with the (implicit) user root
# in path/to/certs/file cockroach should find
#  - ca.crt
#  - client.root.crt
% cockroach sql \
    --user=root \
    --host=<public-ip-address> \
    --certs-dir=path/to/certs/dir
    --database=<database-name>
```

# Run a test scenario

- Select two nodes in the cockroach cluster with the public ip addresses
  - `node-ip-1`
  - `node-ip-2`

- Connect to the first node and create a database `test`
  ```bash
  % cockroach sql --host=<node-ip-1> --certs-dir=path/to/certs/dir
  root@node-ip-1> create database test
  root@node-ip-1> \q
  ```

- Connect to the first node, create a table and enter some data
  (following [this example](https://www.cockroachlabs.com/docs/stable/use-the-built-in-sql-client.html)
  ```bash
  % cockroach sql --host=<node-ip-1> --certs-dir=path/to/certs/dir --database=test
  root@node-ip-1> CREATE TABLE animals (id SERIAL PRIMARY KEY, name STRING);
  root@node-ip-1> INSERT INTO animals (name) VALUES ('bobcat'), ('🐢 '), ('barn owl');
  root@node-ip-1> SELECT * FROM animals;
  +--------------------+----------+
  |         id         |   name   |
  +--------------------+----------+
  | 148899952591994881 | bobcat   |
  | 148899952592060417 | 🐢        |
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
  | 148899952592060417 | 🐢        |
  | 148899952592093185 | barn owl |
  +--------------------+----------+
  root@node-ip-1> \q
  ```
