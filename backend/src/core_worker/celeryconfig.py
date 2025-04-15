
# NOTE: Use underscore to mark variables as private to this module. Non-private
# variables will show up in Flower's Config tab for the worker process.

import logging as _logging
from global_config import get_global_config as _get_global_config

_logger = _logging.getLogger(__name__)

# For complete list of customizable settings, see:
# https://docs.celeryq.dev/en/stable/userguide/configuration.html

#
# Redis backend settings
#
# See: https://docs.celeryq.dev/en/stable/userguide/configuration.html#redis-backend-settings
#

## The backend used to store task results (tombstones)
backend = str(_get_global_config().redis_dsn)

#
# Broker settings
#
# See: https://docs.celeryq.dev/en/stable/userguide/configuration.html#broker-settings
#

## Default broker URL. Must be in the form: transport://userid:password@hostname:port/virtual_host
broker_url = str(_get_global_config().redis_dsn)

#
# Message routing
#
# See: https://docs.celeryq.dev/en/stable/userguide/configuration.html#message-routing
#

# The name of the default queue used by .apply_async if the message has no route or no custom queue has been specified.
# See https://docs.celeryq.dev/en/stable/userguide/configuration.html#task-default-queue
task_default_queue = _get_global_config().celery_task_queue

#
# Task results backend settings
#
# See: https://docs.celeryq.dev/en/stable/userguide/configuration.html#task-result-backend-settings
#

result_backend_transport_options = {
    # See https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/redis.html#global-keyprefix
    'global_keyprefix': _get_global_config().celery_result_key_prefix
}

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
