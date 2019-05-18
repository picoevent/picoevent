# picoevent business intelligence microplatform

The initial goal of this project is to provide a simple, scalable, extendable business intelligence solution for smaller platforms, especially Django projects. The idea for this project came out of recurring problems with Django scalability.

Like the Flask framework picoevent is initially written against, it's limitations in functionality provide a trade off for flexibility and straightforward, virtually unlimited, scalability.

An [Ubuntu 18.04 LTS runbook](https://github.com/picoevent/picoevent/blob/master/runbook.md) is written for Ubuntu 18.04 LTS (recommended because of ZFS support, although one great thing about Python is that you could probably deploy this on any Unix-type system. I don't know much about Windows)

The PicoEvent/config directory provides sample configuration files for nginx and uwsgi. The intended deployment environment is two small (2GB RAM) database/cache instances with the redundant Flask microservices concurrently running on each with the load distributed between the instances with a virtual load balancer which handles HTTPS/SSL.

The recommended scaling from this configuration is to bare metal dedicated servers, ideally no more than two (because synchronization complicates horizontal scalability on the write side) running Ubuntu or ideally FreeBSD for maximum performance using ZFS (as is recommended by the official [MySQL 5.6 manual](https://dev.mysql.com/doc/refman/5.6/en/ha-zfs-replication.html)

For more information: https://picoevent.io
