
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
   for the project
3. Create a key for the new user, download the credentials. You will need this file
   als credentials when you run the ansible playbooks.
