# GETTING STARTED

This walks you thru system requirments
then installation.

## SYSTEM RECOMMENDATIONS

### HARDWARE MINIMUMS

Hardware minimums are presented as recommendations
and not requirements because
there has been no effort made on a proper assessment.
Proper assessment take much effort.
Minimums based on merely installed
a software system then working with a small first data load
is not sufficient for producing a proper requirement.

The hardware minimums will also vary depending on
the configuration of this agent. When the configuration
demands more local computing, then the hardware minimums
will be significantly larger.

With guidances not provided, one working system will be described instead.
With the out-of-box configuration,
reasonable response times are observed with
about 100 GB disk space,
8 GB RAM memory, 8 or more GB GPU memory on a CUDA 12 compatible NVidia GPU, and an 8-core Xeon processor.


### SUPPORTED OPERATING SYSTEMS

#### Debian 12 (Bookworm)

Debian 12 is the "soft" required operating system.
Both the native install and the WSL2 installation are used in testing.

#### Other Linux Flavors

There are two reasons that only Debian 12 is supported: 1. documentation. and 2. testing. This especially applies to Ubuntu 22.04 LTS (Jammy)

Regarding documentation:
there might be differ with Ubuntu because specific instructions might differ.
Sometimes software packages are delivered inseparate streams for Ubuntu and Debian
(for example, NVIDIA delivers on separate streams, which handles the situation that
Ubuntu and Debian are based on different versions of libc6).

Regarding testing: documentation must be tested by following
the written instructions exactly, then the installed software must
be tested for operation-readiness.
Proper testing consumes additional machines and time.
It is better to not claim something than to disrespect testing.

#### Ubuntu Jammy, Kinetic and Lunar

Ubuntu Jammy, Kinetic and Lunar should "just work". They are based on Debian Bookworm (aka Debian 12).
There is an Web-version [table that maps Ubuntu versions to Debian versions](https://askubuntu.com/questions/445487/what-debian-version-are-the-different-ubuntu-versions-based-on).

#### Ubuntu Minotaur and Noble

Ubuntu Minotaur and Noble are not tested. These based on Debian 13.

## SYSTEM REQUIREMENTS

### Software: Docker

Docker Community Edition is required. Specifically, the supported software stack is:

* Docker Community Edition engine
* Docker Community Edition CLI (command-line interface)
* Docker buildx plugin
* Docker compose plugin


See [Install Docker Engine on Debian](https://docs.docker.com/engine/install/debian/)

The minimalist instructions from the Docker documentation are now explained.

Any existing Docker installation is removed:

```bash
apt search docker
sudo apt remove docker.io
sudo apt remove docker-compose
```

Following packages are installed:
docker-ce, docker-ce-cli, containerd.io, docker-buildx-plugin, and docker-compose-plugin.
They are pulled from Docker's repository.

```bash
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo   "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" |   sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

The installation is tested with the "Hello World" image.

```bash
sudo docker run hello-world
```

The current Debian user is added to the `docker` group
so that the `docker` CLI (command-line-interface)
has permissions to the local Docker engine.

```bash
sudo usermod -aG docker jmasui
sudo systemctl restart docker
```

### Software: Nvidia Container Toolkit

This is optional but highly recommended on systems with newer Nvidia GPU's.

### Software: Visual Studo Code

Only one IDE is supported in this repository.


### Software: Debian Packages

#### Install gettext-base

The command line utility `envsubst` is used by a few installation steps.

Install the Debian package that includes the command line utility `envsubst`.

```bash
sudo apt update
sudo apt-get install gettext-base
```

#### Verify openssl

The command line utility `openssl` is used in an installation step
to generate a key.

Verify that it is installed with the following command.

```bash
apt list --installed openssl
```

The output should contain a line with the installed package.

```console
openssl/stable,now 3.0.15-1~deb12u1 amd64 [installed,automatic]
```

#### Verify gpg

```bash
apt list --installed gpg
```

The output should contain a line with the installed package.

```console
gpg/stable,now 2.2.40-1.1 amd64 [installed]
```

## CLOUD SERVICE REQUIREMENTS

### HuggingFace

Get an API key for HuggingFace Hub.

Go to [Hugging Face Hub](https://huggingface.co/pricing#hub)
to get started.

### OpenAI

Get an API key for OpenAI.

Go to [OpenAI platform overview](https://platform.openai.com/docs/overview)
to get started.

### Unstructured (Optional)

Go to [Getting started with API services](https://docs.unstructured.io/api-reference/api-services/free-api)
to get started.

### LangChain and LangSmith (Optional)

LangSmith provides LangChain-specific application tracing and performance evaluation.

To optionally use LangSmith, get an API key for LangSmith.

Go to [smith.langchain.com/](https://smith.langchain.com/) to create an account.

## INSTALLATION

### Build Custom Images

Run `./build_images.sh`.

### Configure Secrets

Create the following files:

* backend/backend.secrets.env based on backend/backend.secrets.env.template
* minio/minio.secrets.env based on minio/minio.secrets.env.template
* minio/minio-init.secrets.env based on minio/minio-init.secrets.env.template
* postgres/pgvector.secrets.env based on  postgres/pgvector.secrets.env.template
* postgres/pgvector-init.secrets.env based on postgres/pgvector-init.secrets.env.template

These `.secrets.env` are listed in `.gitignore` to prevent accidental commits
of API keys.

For convinience, you can create a `./quick_fill.secrets.env` files from the following
template:

```text
HF_TOKEN=
HUGGINGFACEHUB_API_TOKEN=

UNSTRUCTURED_API_KEY=

OPENAI_API_KEY=

LANGCHAIN_API_KEY=
```

Then run:

```bash
./quick_fill_secrets.sh
```

## FIRST TIME START

### Choose between GPU and CPU-only

There are two modes for local computational resources: CUDA 12, and CPU only.

To run with Nvidia CUDA 12 computational resources, set the shell environment
variable as follows:

```bash
export COMPOSE_FILE=cuda.compose.yml
```

To run with CPU-only computational resources, set the shell environment
variable as follows:

```bash
export COMPOSE_FILE=cpu-only.compose.yml
```

### Create Named Volumes

The desired objective is that this step is automatic.
The current reality is that this step requires a manual push.

Run the following command.
This command will create Docker named volumes provisioned with requiste
empty subdirectories, ownership, and mod flags.

```bash
docker compose --profile init-volumes up -d
```

The compose.yml definition do have dependencies for a future automatic creation.
Currently, there is an un-understood timing issue where the subpath mounts
on the dependents are not seeing the subdirectories in the named volumes
until a latter time. So the work-around is to manually push this step.


### Start Infrastructure Layer

Run the following command.
This command will start the Redis, Postgres, and MinIO services.
Also, the database initialize scripts will be run
in run-and-done containers.

```bash
docker compose --profile infrastructure up -d
```

### Verify Infrastructure Layer

#### Verify Redis Service

Run the following command.
This will show logging output from the Redis service.

```bash
docker compose logs redis
```

Read the output.
Verify that there are no errors (self-correction is acceptable),
and
that the service is listening on port 6379 within the container.

```console
redis-1  | 1:C 12 Jan 2025 16:39:57.498 * oO0OoO0OoO0Oo Redis is starting oO0OoO0OoO0Oo
redis-1  | 1:C 12 Jan 2025 16:39:57.498 * Redis version=7.2.5, bits=64, commit=00000000, modified=0, pid=1, just started

...

redis-1  | 1:M 12 Jan 2025 16:39:57.499 * Running mode=standalone, port=6379.
redis-1  | 1:M 12 Jan 2025 16:39:57.500 * Server initialized
redis-1  | 1:M 12 Jan 2025 16:39:57.500 * Ready to accept connections tcp
```

#### Verify MinIO Service

Run the following command.
This will show logging output from the MinIO service.

```bash
docker compose logs minio
```

Read the output.
Verify that there are no errors (self-correction is acceptable),
and
that the service is listening on ports 9000 and 9001 within the container.

```console
minio-1  | INFO: Formatting 1st pool, 1 set(s), 1 drives per set.
minio-1  | INFO: WARNING: Host local has more than 0 drives of set. A host failure will result in data becoming unavailable.
minio-1  | MinIO Object Storage Server
minio-1  | Copyright: 2015-2025 MinIO, Inc.
minio-1  | License: GNU AGPLv3 - https://www.gnu.org/licenses/agpl-3.0.html
minio-1  | Version: RELEASE.2024-12-13T22-19-12Z (go1.23.4 linux/amd64)
minio-1  | 
minio-1  | API: http://172.31.1.3:9000  http://127.0.0.1:9000 
minio-1  | WebUI: http://172.31.1.3:9001 http://127.0.0.1:9001  

...
```

Run the following command.
This will show logging output from
the initialization of the MinIO storage.

```bash
docker compose logs minio-init
```

```console
minio-init-1  | Waiting for Minio server to be ready...
minio-init-1  | mc: <ERROR> Unable to initialize new alias from the provided credentials. Get "http://minio:9000/probe-bsign-ojanuc24grlq5mpejvnfw319ustmvk/?location=": dial tcp 172.31.1.3:9000: connect: connection refused.
minio-init-1  | Added `local_server` successfully.

...

minio-init-1  | Bucket created successfully `local_server/documents`.
minio-init-1  | Added user `langchain` successfully.
minio-init-1  | Attached Policies: [readwrite]
minio-init-1  | To User: langchain
```

#### Verify Postgres Service

Run the following command.
This will show logging output from the Postgres service.

```
docker compose logs pgvector
```

Read the output.
Verify that there are no errors (self-correction is acceptable),
and
that the service is listening on port 5432 within the container.

```console
...

pgvector-1  | Success. You can now start the database server using:
pgvector-1  | 
pgvector-1  |     pg_ctl -D /var/lib/postgresql/data/pgdata -l logfile start
pgvector-1  | 
pgvector-1  | waiting for server to start....2025-01-12 16:39:59.593 UTC [49] LOG:  starting PostgreSQL 17.2 (Debian 17.2-1.pgdg120+1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 12.2.0-14) 12.2.0, 64-bit

...

pgvector-1  | 
pgvector-1  | PostgreSQL init process complete; ready for start up.
pgvector-1  | 

...

pgvector-1  | 2025-01-12 16:39:59.950 UTC [1] LOG:  starting PostgreSQL 17.2 (Debian 17.2-1.pgdg120+1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 12.2.0-14) 12.2.0, 64-bit
pgvector-1  | 2025-01-12 16:39:59.951 UTC [1] LOG:  listening on IPv4 address "0.0.0.0", port 5432

...

pgvector-1  | 2025-01-12 16:39:59.989 UTC [1] LOG:  database system is ready to accept connections
```

Run the following command.
This will show logging output from the initialization
of the Postgres database.

```bash
docker compose logs pgvector-init
```

```console
pgvector-init-1  | DO
pgvector-init-1  | DO
pgvector-init-1  | CREATE DATABASE
pgvector-init-1  | You are now connected to database "langchain" as user "postgres".
pgvector-init-1  | CREATE EXTENSION

```

### Start Backend Layer

Run the following command:

```bash
docker compose --profile backend up -d
```

### Verify Backend Layer

#### Verify FastAPI Server

Run the following command.
This will show logging output from
the FastAPI developement-mode server.

```bash
docker compose logs fastapi-dev-server
```

Read the output.
Verify that there are no errors (self-correction is acceptable),
and
that the server is listening on port 8100 within the container.

```console
fastapi-dev-server-1  | Using Python 3.12.8 environment at: .local/venv
fastapi-dev-server-1  | Resolved 221 packages in 4.94s
fastapi-dev-server-1  | Prepared 221 packages in 2m 07s
fastapi-dev-server-1  | Installed 221 packages in 12.83s

...

fastapi-dev-server-1  | Uninstalled 26 packages in 254ms
fastapi-dev-server-1  | Installed 32 packages in 367ms
fastapi-dev-server-1  | INFO:     Started server process [118]
fastapi-dev-server-1  | INFO:     Waiting for application startup.
fastapi-dev-server-1  | INFO:     Application startup complete.
fastapi-dev-server-1  | INFO:     Uvicorn running on http://0.0.0.0:8100 (Press CTRL+C to quit)
```

#### Verify Celery Worker

Run the following command.
This will show logging output from
the Celery worker.

```bash
docker compose logs celery-worker
```

Read the output.
Verify that there are no errors (self-correction is acceptable),
and
that the worker is connected to Redis
and running within the container.

```console
celery-worker-1  | Using Python 3.12.8 environment at: .local/venv
celery-worker-1  | Resolved 221 packages in 4.90s
celery-worker-1  | Prepared 221 packages in 2m 06s
celery-worker-1  | Installed 221 packages in 8.05s

...

celery-worker-1  | [2025-01-12 16:49:40,344: INFO/MainProcess] Connected to redis://agent-redis-1:6379/0

...

celery-worker-1  | [2025-01-12 16:49:39,421: DEBUG/MainProcess] | Worker: Preparing bootsteps.
celery-worker-1  | [2025-01-12 16:49:39,428: DEBUG/MainProcess] | Worker: Building graph...
celery-worker-1  | [2025-01-12 16:49:39,428: DEBUG/MainProcess] | Worker: New boot order: {StateDB, Beat, Timer, Hub, Pool, Autoscaler, Consumer}

...

celery-worker-1  | [2025-01-12 16:49:41,390: DEBUG/MainProcess] | Consumer: Starting event loop
celery-worker-1  | [2025-01-12 16:49:41,390: DEBUG/MainProcess] | Worker: Hub.register Pool...
celery-worker-1  | [2025-01-12 16:49:41,391: INFO/MainProcess] celery@476c184cd474 ready.
```

### Start Frontend Layer

Run the following command:

```bash
docker compose --profile frontend up -d
```

### Verify Frontend Layer

#### Verify ViteJS Server

Run the following command.
This will show logging output from
the ViteJS developement-mode server.

```bash
docker compose logs vite-dev-server
```

Read the output.
Verify that there are no errors (self-correction is acceptable),
and
that the server
is listening on post 5173 within the container.

```console
vite-dev-server-1  | 
vite-dev-server-1  | added 252 packages, and audited 253 packages in 7s
vite-dev-server-1  | 

...

vite-dev-server-1  | > vite --host 0.0.0.0 --logLevel info
vite-dev-server-1  | 
vite-dev-server-1  | 
vite-dev-server-1  |   VITE v5.4.11  ready in 885 ms
vite-dev-server-1  | 
vite-dev-server-1  |   ➜  Local:   http://localhost:5173/
vite-dev-server-1  |   ➜  Network: http://172.31.1.7:5173/
vite-dev-server-1  |   ➜  Vue DevTools: Open http://localhost:5173/__devtools__/ as a separate window
vite-dev-server-1  |   ➜  Vue DevTools: Press Alt(⌥)+Shift(⇧)+D in App to toggle the Vue DevTools

...
```

#### Verify NginX Server

Run the following command.
This will show logging output from
the NginX reverse proxy server.

```bash
docker compose logs proxy
```

Read the output.
Verify that there are no errors (self-correction is acceptable),
and
that the NginX service has started its NginX workers.

```console
...

proxy-1  | 2025/01/12 17:17:20 [notice] 1#1: using the "epoll" event method
proxy-1  | 2025/01/12 17:17:20 [notice] 1#1: nginx/1.27.3
proxy-1  | 2025/01/12 17:17:20 [notice] 1#1: built by gcc 12.2.0 (Debian 12.2.0-14) 

...

proxy-1  | 2025/01/12 17:17:20 [notice] 1#1: start worker processes

...
```

## CONTINUOUS LOGGING

To start continuous logging
of the ViteJS server, the FastAPI server, and
the Celery worker,
run the following command.

```bash
docker compose logs -f vite-dev-server fastapi-dev-server celery-worker
```

## CHECK DOCKER HEALTH

To get a list of running services,
run the following command.

```bash
docker compose ps --format "table {{.Name}}\t{{.Service}}\t{{.Status}}"
```

The output should list all of the expected services

```console
agent-celery-worker-1        celery-worker        Up About an hour
agent-fastapi-dev-server-1   fastapi-dev-server   Up About an hour
agent-minio-1                minio                Up About an hour
agent-pgvector-1             pgvector             Up About an hour
agent-proxy-1                proxy                Up About an hour
agent-redis-1                redis                Up About an hour
agent-vite-dev-server-1      vite-dev-server      Up About an hour
```

## SECOND TIME AND ADDITIONAL START UP

Start all Docker services simultaneously:

```bash
docker compose --profile init-volumes up -d
docker compose --profile all up -d
```

## CPU ONLY SYSTEMS

As stated above, CPU-only systems are now managed with a single
environment variable: `export COMPOSE_FILE=cpu-only.compose.yml`.

## TEST THE APPLICATION

### Go To Health Check

In Chrome, go to the URL `http://localhost:15173/health`.

It should show a status of `healthy`.

### Go To Document Manager

Upload some documents thru the user interface. Then use the UI to ingest them.

### Go To Conversation

Ask some questions in the user interface.

## SOME OPERATIONAL NOTES

### Prune Docker Filesystem Footprint

To view the current footprint, run the below command.
This command is explained in [docker system df](https://docs.docker.com/reference/cli/docker/system/df/)

```bash
docker system df
```

To reduce the unnecessary footprint from multiple causes, run the below command.
This command is explained in [docker system prune](https://docs.docker.com/reference/cli/docker/system/prune/)

```bash
 docker system prune --all --volumes
```

The output starts with:

```console
WARNING! This will remove:
  - all stopped containers
  - all networks not used by at least one container
  - all anonymous volumes not used by at least one container
  - all images without at least one container associated to them
  - all build cache
...
```

As explained in the output, this command removes multiple sources of unused footprint.
Typically, the largest footprints are from stopped containers, unused images, the build cache,
and anonymous volumes. This command does not remove unused local volumes.

To remove unused local volumes, run the below command.
This command is explained in [docker volume prune](https://docs.docker.com/reference/cli/docker/volume/prune/)

```bash
docker volume prune --all
```

The output starts with:

```console
WARNING! This will remove all local volumes not used by at least one container.
...
```

This will remove the last large cause of unnecessary filesystem footprint.
