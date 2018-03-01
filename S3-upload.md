
# How to upload large OSM files to Amazon S3

## install s3cmd

```bash
$ wget -O- -q http://s3tools.org/repo/deb-all/stable/s3tools.key | sudo apt-key 
add -
$ sudo wget -O/etc/apt/sources.list.d/s3tools.list http://s3tools.org/repo/deb-a
ll/stable/s3tools.list
$ sudo apt-get update && sudo apt-get install s3cmd
```

## configure s3cmd

```bash
# asks configuration parameters and writes  ~/.s3cfg
# when asked for the encryption key, just press Enter
$ s3cmd --configure
```

## upload file

```bash
# uplad a large OSM file, i.e. switzerland-latest.osm.pbf
# for instance:
# s3cmd put switzerland-latest.osm.pbf s3://cockroach-import/switzerland-latest.osm.pbf
#
$ s3cmd put <file-name> s3://<bucket-name>/<file-name>
```
