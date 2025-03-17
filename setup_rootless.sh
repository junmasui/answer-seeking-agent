
grep ^$(whoami): /etc/subuid
if [ $? -ne 0 ]
then
    exit 78
fi

grep ^$(whoami): /etc/subgid
if [ $? -ne 0 ]
then
    exit 78
fi

for ID in 1000 999 101
do
    grep rootless-$ID: /etc/passwd
    if [ $? -ne 0 ]
    then
        exit 78
    fi

    grep rootless-$ID: /etc/group
    if [ $? -ne 0 ]
    then
        exit 78
    fi
done

for RELPATH in "frontend" "backend"
do
    sudo find $RELPATH -type d \
        -not \( -path "${RELPATH}/docker" \) \
        -exec chown rootless-1000:rootless-1000 \{\} \; \
        -exec chmod ug=rwx,g=srwx,o=rx \{\} \;
    sudo find $RELPATH -type f \
        -not \( -path "${RELPATH}/*.sh" -or -path "${RELPATH}/docker/*" \) \
        -exec chown rootless-1000:rootless-1000 \{\} \; \
        -exec chmod ug=rw,o=r \{\}  \;
    sudo find $RELPATH -type f \
        \( -path "${RELPATH}/run*.sh" \) \
        -exec chown rootless-1000:rootless-1000 \{\} \; \
        -exec chmod ug=rwx,o=r \{\}  \;
done


for RELPATH in "clickhouse"
do
    sudo find $RELPATH -iname '*.xml' -type f \
        -exec chown rootless-101:rootless-101 \{\} \; \
        -exec chmod ug=rw \{\}  \;
    sudo find $RELPATH -iname '*.crt' -type f \
        -exec chown rootless-101:rootless-101 \{\} \; \
        -exec chmod ug=rw \{\}  \;
    sudo find $RELPATH -iname '*.key' -type f \
        -exec chown rootless-101:rootless-101 \{\} \; \
        -exec chmod ug=rw \{\}  \;
done

for RELPATH in "postgres"
do
    sudo find $RELPATH -iname '*.sql.template' -type f \
        -not \( -path "${RELPATH}/docker/*" \) \
        -exec chown rootless-999:rootless-999 \{\} \; \
        -exec chmod ug=rw \{\}  \;

    sudo find $RELPATH -iname '*.sh' -type f \
        -not \( -path "${RELPATH}/docker/*" \) \
        -exec chown rootless-999:rootless-999 \{\} \; \
        -exec chmod ug=rw \{\}  \;
done

sudo find redis -iname '*.conf' -type f \
    -exec chown rootless-999:rootless-999 \{\} \; \
    -exec chmod ug=rw \{\}  \;

