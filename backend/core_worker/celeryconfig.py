
# NOTE: Use underscore to mark variables as private to this module. Non-private
# variables will show up in Flower's Config tab for the worker process.

from global_config import get_global_config as _get_global_config


# For complete list of customizable settings, see:
# https://docs.celeryq.dev/en/stable/userguide/configuration.html

#
# Redis backend settings
#
# See: https://docs.celeryq.dev/en/stable/userguide/configuration.html#redis-backend-settings
#

## The backend used to store task results (tombstones)
result_backend = str(_get_global_config().redis_dsn)

#
# Broker settings
#
# See: https://docs.celeryq.dev/en/stable/userguide/configuration.html#broker-settings
#

## Default broker URL. Must be in the form: transport://userid:password@hostname:port/virtual_host
broker_url = str(_get_global_config().redis_dsn)

#
# Worker settings
#
# See https://docs.celeryq.dev/en/stable/userguide/configuration.html#worker
#

## The number of concurrent worker processes/threads/green threads executing tasks.
worker_concurrency=2

## Maximum number of tasks a pool worker process can execute before it’s replaced with a new one.
worker_max_tasks_per_child=100

## Maximum amount of resident memory, in kilobytes, that may be consumed by a worker before it will be replaced by a new worker.
# worker_max_memory_per_child=4_096_000 # 4 Gb
worker_max_memory_per_child=8_192_000 # 8 Gb

#
# Event settings
#
# See https://docs.celeryq.dev/en/stable/userguide/configuration.html#events
#

## Send task-related events so that tasks can be monitored
##
## True is required by the celery-exporter
worker_send_task_events = True

## When enabled, a task-sent event will be sent for every task so that
## tasks can be tracked before they’re consumed by a worker.
##
## True is required by the celery-exporter
task_send_sent_event = True
