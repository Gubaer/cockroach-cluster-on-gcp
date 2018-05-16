# Execution environement for the PoC in this repository


## build the container
```bash
# builds the docker container and assigns it the label 'crdb-cluster-control-node'
$ sudo docker build  \
    -t crdb-cluster-control-node \
    -f crdb-cluster-control-node.docker \
    .
```

## run the container
```bash
# change to the repository root
$ cd <root directory of this repository>

# launch the container
$ sudo docker run \
    -ti \
    -v $(pwd):/control-node-home \
    crdb-cluster-control-node
# shell prompt in the container 
root@dc2fb7dce0e2:/#
```

## Example: create a crdb cluster with 10 nodes using the container

Launch the docker container as described above.

```bash
# shell prompt in the container 
root@dc2fb7dce0e2:/# cd ansible

# edit gce.env. configure the credentials to access the Google Cloud
# Plattform
root@dc2fb7dce0e2:/# source gce.env
# run the ansible script to create a crdb cluster
root@dc2fb7dce0e2:/# ansible-playbook create-cluster.yml
Number of cluster nodes (n>=2, choose an even number) [default=2] [2]: 10
```
