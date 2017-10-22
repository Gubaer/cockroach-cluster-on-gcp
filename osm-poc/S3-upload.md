# install s3cmd

```bash
$ wget -O- -q http://s3tools.org/repo/deb-all/stable/s3tools.key | sudo apt-key 
add -
$ sudo wget -O/etc/apt/sources.list.d/s3tools.list http://s3tools.org/repo/deb-a
ll/stable/s3tools.list
$ sudo apt-get update && sudo apt-get install s3cmd
```

# configure s3cmd

```
# asks configuration parameters and writes  ~/.s3cfg
# when asked for the encryption key, just press Enter
$ s3cmd --configure
```

# upload file

```bash
# uplad a csv file to the S3 bucket
# for instance:
# s3cmd put s3://cockroach-import/nodes.csv nodes.csv
$ s3cmd put s3://<bucket-name>/<file-name> <file-name>
```
