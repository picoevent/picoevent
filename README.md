# picoevent business intelligence microplatform

The initial goal of this project is to provide a simple, scalable, extendable business intelligence solution for smaller platforms, especially Django projects.

Like the Flask framework picoevent is initially written against, it's limitations in functionality provide a trade off for flexibility and straightforward, virtually unlimited, scalability.

The PicoEvent/config directory provides a detailed runbook for Ubuntu 18 LTS, running on nginx/uWSGI/Flask/Python 3 with MySQL for persistent storage and Redis for caching.

Additionally there are example configuration files for nginx and uwsgi. The intended deployment environment is two small (2GB RAM) database/cache instances with the redundant Flask microservices concurrently running on each with the load distributed between the instances with a virtual load balancer which handles HTTPS/SSL.

The recommended scaling from this configuration is to bare metal dedicated servers, ideally no more than two (because synchronization complicates horizontal scalability on the write side) running Ubuntu or ideally FreeBSD for maximum performance using ZFS (as is recommended by the officialaa MySQL manual)

For more information: https://picoevent.io