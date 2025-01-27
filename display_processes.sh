

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
