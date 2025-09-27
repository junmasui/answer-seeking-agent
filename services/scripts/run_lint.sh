
COMPOSE_FILE=./common.compose.yml docker compose --profile=all exec api-server-autotest sh -c "/app/run_lint.sh | tee /app/run_lint.log"
COMPOSE_FILE=./common.compose.yml docker compose --profile=all exec webui-server-autotest sh -c "/app/run_lint.sh | tee /app/run_lint.log"
