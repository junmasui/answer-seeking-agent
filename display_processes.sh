#!/usr/bin/env bash

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
              | [ "agent-vite-dev-server-1",
                  "agent-celery-exporter-1",
                  "agent-langfuse-worker-1" ]
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
                | [ "agent-vite-dev-server-1",
                    "agent-celery-exporter-1",
                    "agent-langfuse-worker-1" ]
                | index(\$name)
              ) ) | not )
  | select( ( .State == "exited" and .ExitCode != 0 ) | not )
  |  {Name: .Name, Health: .Health, State: .State, ExitCode: .ExitCode, Status: .Status}
EOS
)

jq --compact-output "$JQ_2" <<< "$PROCESSES"

echo "Examine suspicious or failed processes"

SUSPICIOUS=$( ( jq --compact-output "$JQ_2" <<< "$PROCESSES" ) | wc -l )
if [ "$SUSPICIOUS" -ne 0 ]
then
  exit 1 # Generic Error 
else
  exit 0 # Success
fi
