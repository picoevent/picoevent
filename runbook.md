# Ubuntu 18 LTS Runbook

It is strongly recommended that you configure at least two instances running all three
services. Small VM's (2GB of memory) work great for even a lot of data as long you aren't running anything else.

As an aside, one reason I think Docker is overrated for microservice development, is that if "Data is the new oil", it seems irresponsible to not use at least master/slave replication. (At least to the extent that it is sold, *I think Docker is a great tool for getting services running on a MacBook for those that aren't Unix admins.*)

But the idea that you can just push a container out and deploy it to production? I mean if your data is of any importance, you want at least one replica, which can't take writes. But now with big data you have some huge read loads... Anyway it's a good tool to get everyone running the same version of Postgres or whatever.

My favorite buzzword is currently **cloud agnostic** meaning using Docker. I've personally setup Wordpress hundreds of times over the years, and was really excited how fast it was working on my local machine. But aside from using some sort of service like Amazon Container Service (now that doesn't sound **agnostic** to me) it's like a ship on a bottle from an administration perspective.

In my opinion, the only remotely difficult thing about this setup is the replication configuration for MySQL, and Docker won't help you with that.

##### HTTPS/SSL

Since the current reality is that you need to use SSL for any and all services, I would recommend some sort of virtual load balancer to setup certificates against. I've found AWS to be completely unsuitable for this type of application because first, it was quite difficult to create two suitable instances in different availability zones (required) and then open the MySQL port between them even though they were
in the same VPC. After all that, I finally get the elastic load balancer set up and they're trying to give me a domain instead of an IP address. *So the solution was for me to use Amazon Route 56 DNS or whatever.* I ended up going with an alternative provider. I'm planning on using Kinesis mostly for archiving to S3, I think that's a pretty great service (S3 is really a great deal, in my opinion). I have no bias against AWS, just the ability to calculate costs.

##### Set up ssh keying (recommended)
https://debian-administration.org/article/530/SSH_with_authentication_key_instead_of_password

After you're sure you've set this up disable password login for root.

`# passwd -l root`

## Install MySQL 5.7

`# apt-get install mysql-server`

#### For ZFS datadir (optional, recommended by the MySQL Official Manual under High Availability)

`# zfs create pool/mysql_db`

`# chown mysql /pool/mysql_db`

`# chgrp mysql /pool/mysql_db`

`# chmod 700 /pool/mysql_db`

#### Configure AppArmor to allow this in Ubuntu

`# mysqld --initalize --user=mysql --datadir=/pool/mysql_db`

**Change this in my.cnf**

datadir=/pool/mysqldb

### Recommended my.cnf settings for MySQL master

*I would strongly advise against replicating over the Internet if you're using this as a guide to MySQL config. Interestingly enough, whichever cloud provider I used instead of Amazon made it easier to replicate an instance in Dallas and an instance in New Jersey than two instances in Northern VA in different availability groups, but the same VPC.*

bind-address=<private_ip>

symbolic-links=0

log-bin=mysql-bin

server-id=1

innodb_flush_log_at_trx_commit=1

sync_binlog=1

**I've done replication both ways, I think gtid is a little simpler to setup.**

gtid_mode=ON

enforce_gtid_consistency=true

*If you use mysqldump you might have some issues with gtid mode on when trying to reimport. simply remove the gtid line at the top of the dumpfile and you should be good.*

### If you're using a relatively small setup (2 x 2GB RAM virtual machines) I would recommend the following:

**Turning off performance schema will save about 400MB alone**

performance_schema=off

*These will help too, it's better to have more RAM for Redis anyway.*

key_buffer_size = 16K

max_allowed_packet = 1M

table_open_cache = 4

sort_buffer_size = 64K

net_buffer_length = 8K

read_buffer_size = 256K

read_rnd_buffer_size = 512K

### For a slave database, use unique server id greater than 1
*Otherwise, the same settings as for the master are recommended.*

server_id=2, or 3, etc.

### /etc/hosts

It's helpful for configuring MySQL replication to add a short entry
like mysite_primary <private-ip> to /etc/hosts
You can also use it for you configuration files. You should add entries
for both primary and secondary hosts on all hosts.

#### Some Advice

**I would strongly recommend getting the two database instances configured and synchronized before proceeding further,
it's one of those things that is much easier to do with an empty database. You can easily add and reconfigure the nginx instances all day once you have some, uh, kinesis going.**

Honestly, from working at corporations with huge traffic, the scaling move for this application is not to a bigger instance, but to dedicated hardware, at least for the two nodes that would be handling the writes. Using Kinesis for archiving to S3 would seem like a good hedge, but if you have that much data, odds are you have an architect that is way smarter than me. Scaling for reads is easy, but with writes, you have problem of synchronization that only increases as you scale horizontally.

Might be able to do some cool machine learning stuff with your data and some AWS images though.
## nginx

`# apt-get install nginx`

*Configure nginx to connect to uwsgi through sockets instead of TCP/IP
see config/nginx.config for an example. This will save you some overhead, running three services on an instance, every little bit helps.*

## Python 3 stack

`# apt-get install python3-venv gcc python3-dev libmysqlclient-dev`

## Redis

You can probably get this from a repo but it's really easy to just download
and build the code. (now that you have gcc installed...)

https://redis.io/download

#### Building Redis from source

`~$ wget http://download.redis.io/releases/redis-5.0.4.tar.gz`

`~$ gzip -d redis-5.0.4.tar.gz `

`~$ tar -xvf redis-5.0.4.tar `

`~$ cd redis-5.0.4`

`~$ make`

**As root user:**

`~# make install`

Redis configuration will be left as an exercise to the reader and heavily
depends on what sort of server/instance you're running it on. PicoEvent works fine with
no special configuration. *Note that when configuring the REDIS_SLAVE variable for *picoevent* it's OK to use the redis master instance for this. All this means that only reads will be directed to this instance.

## Service user
`# createuser service`

`# su service`


`~ $ git clone https://github.com/picoevent/picoevent.git`

`cd picoevent`

#### Important: add your configuration files to this instance folder

`$ mkdir instance`

Make sure you add every variable required by the Environment Object, as
well as a SECRET_KEY. You might want to read up the Flask docs regarding
how configuration works. A lot of different ways you can do this.

#### Setting up your service venv

`~/picoevent/ $ python3 -m venv venv`

`~/picoevent/ $ . venv/bin/activate`

`(venv) ~/picoevent/ $ pip install -r PicoEvent/config/requirements.txt`

#### Database schema installation (you do this with command line.)

* First change the settings in PicoEvent/config.json to reflect DB configuration (make mysql_host the 'master' instance!')
* mysql_test_db is optional, just make sure you don't set it as the same as the regular db, and then run unittests because you will wipe out your database.
* Change the PYTHONPATH. This isn't Django, there is no heavyweight built in user interface. export PYTHONPATH=/home/service/picoevent
* Otherwise you will get ModuleNotFound exception.
* `(venv) ~/picoevent/PicoEvent/Database.py`


#### Running the service.

`(venv) ~/picoevent/ $ uwsgi --ini PicoEvent/config/uwsgi.ini`

Interestingly, I have found that this Flask/uwsgi/nginx stack is so *rock solid* there is not really a need for systemd to manage this.

Incredibly, even when doing a *deployment of new code* simply sending a HUP signal to the uwsgi master process works flawlessly. Some software you pay for doesn't work as well.
