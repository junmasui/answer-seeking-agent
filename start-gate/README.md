README
======

Description
-----------

The ReadinessChecker is a small Docker image that
runs and exits when specified infrastructure resources
are ready.

The implementation is
a run-and-exit bash script
and
some installed utilities (`curl`, `pg_isready`, `redis-cli`, etc).

Design Discussion
-----------------

When starting a local Docker-based system, there are a few considerations
for a mass start.
We are specifically interested in the following group of considerations.

* Docker service names are not immediately registered with the internal Docker DNS resolver.
* Databases and user accounts are not immediately created.
* Other higher-level infrastructure are not immediately available. (For example, they themselves might be waiting
  for database and user account creation)

These consideration can be summarized as the need to wait for pre-requiste
components to become available.
The reasoning is simple: not all applications and higher-level infrastructure
are fully robust against unavailable pre-requistes. There are myriads of possiblities,
the root-cause might be buried deep in its dependencies and specific to Docker,
and start-up is a chain of partial application states that could be difficult to catch.

Another consideration is that
the demands of pre-requiste checking will be different between a local Docker-based system
and a large cloud-based system.
A large cloud-based system will have its own health-checking system that could be a better solution.
But this is very much vendor-dependent.
