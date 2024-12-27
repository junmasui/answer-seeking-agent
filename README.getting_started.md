# GETTING STARTED

This walks you thru system requirments
then installation.

## SYSTEM RECOMMENDATIONS

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

### Launch

Start all Docker services simultaneously:

```bash
docker compose --profile all up -d
```

Wait half-minute.
When services are launched for the first time,
named Docker volumes are created.
The named volumes for the front and back ends
hold the package installations for VueJS and for Python.
These take a number of seconds to populate because
the package managers have to actually install packages.

```bash
docker compose ps --format "table {{.Name}}\t{{.Service}}\t{{.Status}}"
```

```console
NAME                         SERVICE              STATUS
agent-celery-worker-1        celery-worker        Up 42 seconds
agent-fastapi-dev-server-1   fastapi-dev-server   Up 42 seconds
agent-minio-1                minio                Up 42 seconds
agent-pgvector-1             pgvector             Up 42 seconds
agent-proxy-1                proxy                Up 42 seconds
agent-redis-1                redis                Up 42 seconds
agent-vite-dev-server-1      vite-dev-server      Up 42 seconds
```

For more detailed information about running containers, 
run the following command.

```bash
docker compose ps
```

Next verify that the services came up without errors:

```bash
docker compose logs pgvector
```

Check that Postgres is running and internally listening on port 5432.

```bash
docker compose logs redis
```

Check that Redis is running and internally listening on port 6379.

```bash
docker compose logs minio
```

Check that Redis is running and internally listening on ports 9000 and 9001.


```bash
docker compose logs fastapi-dev-server
```

Check that the Python virtual environment was installed and `uvicorn` started and is listening.

```bash
docker compose logs celery-worker
```

Check that the Python virtual environment was installed and `celery` started and is listening.

```bash
docker compose logs vite-dev-server
```

Check that the node modules were installed and `vite` started and is internally listening on port 5173.

```bash
docker compose logs proxy
```

Check that nginx is running.


## Use the Application

In Chrome, go to the URL `http://localhost:15173/health`.

It should show a status of `healthy`.

