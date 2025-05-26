##set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

grep "^$(whoami)": /etc/subuid
if [ $? -ne 0 ]
then
    exit 78
fi

grep "^$(whoami)": /etc/subgid
if [ $? -ne 0 ]
then
    exit 78
fi

for ID in 1000 999 101
do
    grep "rootless-$ID": /etc/passwd
    if [ $? -ne 0 ]
    then
        exit 78
    fi

    grep "rootless-$ID": /etc/group
    if [ $? -ne 0 ]
    then
        exit 78
    fi
done

# Define an array for application paths to allow easy extension
APP_PATHS=("frontend" "backend")
# To add more paths in the future, modify the array like so:
# APP_PATHS=("frontend" "backend" "another/app/path")

for RELPATH in "${APP_PATHS[@]}"
do
    sudo find "$RELPATH" -type d \
        -not \( -path "${RELPATH}/docker" \) \
        -exec chown rootless-1000:rootless-1000 {} \; \
        -exec chmod ug=rwx,g=srwx,o=rx {} \;
    sudo find "$RELPATH" -type f \
        -not \( -path "${RELPATH}/*.sh" -or -path "${RELPATH}/docker/*" \) \
        -exec chown rootless-1000:rootless-1000 {} \; \
        -exec chmod ug=rw,o=r {}  \;
    sudo find "$RELPATH" -type f \
        \( -path "${RELPATH}/run*.sh" \) \
        -exec chown rootless-1000:rootless-1000 {} \; \
        -exec chmod ug=rwx,o=r {}  \;
done


# Define an array for clickhouse paths to allow easy extension and resolve SH-2043
CLICKHOUSE_PATHS=("clickhouse")
# To add more paths in the future, modify the array like so:
# CLICKHOUSE_PATHS=("clickhouse" "another/path" "yet/another/path")

for RELPATH in "${CLICKHOUSE_PATHS[@]}"
do
    # Corrected -exec to use {} (filename placeholder) instead of literal \{\}
    sudo find "$RELPATH" -iname '*.xml' -type f \
        -exec chown rootless-101:rootless-101 {} \; \
        -exec chmod ug=rw {} \;
    sudo find "$RELPATH" -iname '*.crt' -type f \
        -exec chown rootless-101:rootless-101 {} \; \
        -exec chmod ug=rw {} \;
    sudo find "$RELPATH" -iname '*.key' -type f \
        -exec chown rootless-101:rootless-101 {} \; \
        -exec chmod ug=rw {} \;
done

# Define an array for postgres paths to allow easy extension
POSTGRES_PATHS=("postgres")
# To add more paths in the future, modify the array like so:
# POSTGRES_PATHS=("postgres" "another/pg/path")

for RELPATH in "${POSTGRES_PATHS[@]}"
do
    sudo find "$RELPATH" -iname '*.sql.template' -type f \
        -not \( -path "${RELPATH}/docker/*" \) \
        -exec chown rootless-999:rootless-999 {} \; \
        -exec chmod ug=rw {}  \;

    sudo find "$RELPATH" -iname '*.sh' -type f \
        -not \( -path "${RELPATH}/docker/*" \) \
        -exec chown rootless-999:rootless-999 {} \; \
        -exec chmod ug=rwx {}  \;
done

# Define an array for redis paths to allow easy extension
REDIS_PATHS=("redis")
# To add more paths in the future, modify the array like so:
# REDIS_PATHS=("redis" "another/redis/path")

for RELPATH in "${REDIS_PATHS[@]}"
do
    sudo find "$RELPATH" -iname \'*.conf\' -type f \
        -exec chown rootless-999:rootless-999 {} \; \
        -exec chmod ug=rw {}  \;
done

