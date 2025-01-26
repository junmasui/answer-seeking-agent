
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
docker compose --profile frontend up -d

sleep 5

echo "All processes:"
JQ_1=$(cat << EOS
. 
  |  {Name: .Name, Health: .Health, State: .State, ExitCode: .ExitCode, Status: .Status}
EOS
)
docker compose ps --all --format json \
  | jq --compact-output "$JQ_1"

echo "Failed processes:"
JQ_2=$(cat << EOS
. 
  | select( ( .Health == "healthy" ) | not )
  | select( ( .State == "exited" and .ExitCode == 0 ) | not )
  | select( ( .State == "running" and .Name == "agent-vite-dev-server-1" ) | not )
  |  {Name: .Name, Health: .Health, State: .State, ExitCode: .ExitCode, Status: .Status}
EOS
)
docker compose ps --all --format json \
  | jq --compact-output "$JQ_2"

echo "Manually inspect. Retry failed processes with 'docker compose up -d <service>'"