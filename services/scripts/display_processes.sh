#!/usr/bin/env bash

GPU_MODE=""

# Parse GNU-style long options
while [[ $# -gt 0 ]]; do
    case "$1" in
        --gpu-mode=* )
        # This extracts the option value from $1.
        #   '#' is the parameter expansion operator for removing a prefix
        #   '*=' matches everything up to and including the first '='
        GPU_MODE="${1#*=}"
        ;;
        # Add more long options here as needed
        * )
        echo "Unknown option: $1" >&2
        exit 1
        ;;
    esac
    shift
done

if [ -z "${GPU_MODE:-}" ]; then
    echo "GPU mode missing"
    exit 1
elif [ "$GPU_MODE" == "cuda13" ]; then
    export COMPOSE_FILE=common.compose.yml:cuda.compose.yml
elif [ "$GPU_MODE" == "cpu" ]; then
    export COMPOSE_FILE=common.compose.yml:cpu-only.compose.yml
else
    echo "invalid GPU mode: ${GPU_MODE}"
    exit 1
fi


PROCESSES=$( docker compose ps --all --format json )

echo "Healthy processes:"
JQ_1=$(cat << EOS
. 
  | select( .Health == "healthy" )
  |  {Name: .Name, Health: .Health, State: .State, ExitCode: .ExitCode, Status: .Status}
EOS
)

jq --compact-output "$JQ_1" <<< "$PROCESSES"

echo "Completed processes (exit code 0 only):"
JQ_2=$(cat << EOS
. 
  | select( .Health == "" and .State == "exited" and .ExitCode == 0 )
  |  {Name: .Name, Health: .Health, State: .State, ExitCode: .ExitCode, Status: .Status}
EOS
)
jq --compact-output "$JQ_2" <<< "$PROCESSES"

echo "Running processes known to be without health checks:"
JQ_3=$(cat << EOS
. 
  | select( .State == "running"
            and
            ( .Name as \$name 
              | [ "agent-webui-server-1",
                  "agent-webui-server-autotest-1",
                  "agent-otel-collector-1",
                  "agent-otel-collector-docker-1",
                  "agent-automated-pytest-1",
                  "agent-loki-1" ]
              | index(\$name)
            ) )
  |  {Name: .Name, Health: .Health, State: .State, ExitCode: .ExitCode, Status: .Status}
EOS
)
jq --compact-output "$JQ_3" <<< "$PROCESSES"

echo "Failed processes:"
JQ_4=$(cat << EOS
. 
  | select( .State == "exited" and .ExitCode != 0 )
  |  {Name: .Name, Health: .Health, State: .State, ExitCode: .ExitCode, Status: .Status}
EOS
)
jq --compact-output "$JQ_4" <<< "$PROCESSES"


echo "Suspicious processes:"
JQ_2=$(cat << EOS
. 
  | select( ( .Health == "healthy" ) | not )
  | select( ( .Health == "" and .State == "exited" and .ExitCode == 0 ) | not )
  | select( ( .State == "running"
              and
              ( .Name as \$name 
                | [ "agent-webui-server-1",
                    "agent-webui-server-autotest-1",
                    "agent-otel-collector-1",
                    "agent-otel-collector-docker-1",
                    "agent-automated-pytest-1",
                    "agent-nfs-1",
                    "agent-loki-1" ]
                | index(\$name)
              ) ) | not )
  | select( ( .State == "exited" and .ExitCode != 0 ) | not )
  |  {Name: .Name, Health: .Health, State: .State, ExitCode: .ExitCode, Status: .Status}
EOS
)

jq --compact-output "$JQ_2" <<< "$PROCESSES"

echo "Examine suspicious or failed processes"

SUSPICIOUS=$( ( jq --compact-output "$JQ_2" <<< "$PROCESSES" ) | wc -l )
FAILED=$( ( jq --compact-output "$JQ_4" <<< "$PROCESSES" ) | wc -l )
if [ "$SUSPICIOUS" -ne 0 ] || [ "$FAILED" -ne 0 ]
then
  exit 1 # Generic Error 
else
  exit 0 # Success
fi
