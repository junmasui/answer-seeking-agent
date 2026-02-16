FROM ghcr.io/mlflow/mlflow:v2.21.3

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install psycopg2-binary for Postgres backend store
# Install boto3 for S3-compatible artifact store (SeaweedFS)
RUN pip install psycopg2-binary boto3

