
from global_config import get_global_config as _get_global_config

# Use underscore to mark variables as private to this module. Non-private
# variables will show up in Flower's Config tab for the worker process.
#
_redis_url = str(_get_global_config().redis_dsn)

# For complete list of customizable settings, see:
# https://docs.celeryq.dev/en/stable/userguide/configuration.html

#
# Broker settings
#

## Default broker URL. Must be in the form: transport://userid:password@hostname:port/virtual_host
broker_url = _redis_url

#
# Backend settings
#

## The backend used to store task results (tombstones)
result_backend = _redis_url

#
# Worker settings
#

## The number of concurrent worker processes/threads/green threads executing tasks.
worker_concurrency=2

## Maximum number of tasks a pool worker process can execute before it’s replaced with a new one.
worker_max_tasks_per_child=100

## Maximum amount of resident memory, in kilobytes, that may be consumed by a worker before it will be replaced by a new worker.
# worker_max_memory_per_child=4096000 # 4 Gb
worker_max_memory_per_child=8192000 # 8 Gb
