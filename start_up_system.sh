
if [ -z "$COMPOSE_FILE" ]
then
    echo "set environment variable COMPOSE_FILE"
    exit 1
fi

if [ -z "$COMPOSE_PROFILES" ]
then
    echo "set environment variable COMPOSE_PROFILES to all"
    exit 1
fi


# Some named volumes need to be initialized (with
# subdirectories) before the true services are launched.
#
# These are run-and-done containers, so we can launch
# not in daemon mode. The simple exit is so much simpler
# than a wait-loop :-)
docker compose --profile init-volumes up

# Start up the system.
#
docker compose --profile infrastructure up -d
docker compose --profile backend up -d
docker compose --profile frontend --profile backend up -d


./display_processes.sh
