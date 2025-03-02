
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

for RELPATH in "frontend/" "backend/"
do
    sudo find $RELPATH -type d \
        -exec chown rootless-1000:rootless-1000 \{\} \; \
        -exec chmod ugo+srwx \{\}  \;
    sudo find $RELPATH -type f \
        -exec chown rootless-1000:rootless-1000 \{\} \; \
        -exec chmod ug+rw \{\}  \; \
        -exec chmod o+r \{\}  \;
done


for RELPATH in "clickhouse/"
do
    sudo find clickhouse/ -iname '*.xml' -type f \
        -exec chown rootless-101:rootless-101 \{\} \; \
        -exec chmod ug+w \{\}  \; \
        -exec chmod o+r \{\}  \;
done

sudo find postgres/ -iname '*.sql.template' -type f \
    -exec chown rootless-999:rootless-999 \{\} \; \
    -exec chmod ug+w \{\}  \; \
    -exec chmod o+r \{\}  \;

sudo find postgres/ -iname '*.sh' -type f \
    -exec chown rootless-999:rootless-999 \{\} \; \
    -exec chmod ug+w \{\}  \; \
    -exec chmod o+r \{\}  \;

sudo find redis/ -iname '*.conf' -type f \
    -exec chown rootless-999:rootless-999 \{\} \; \
    -exec chmod ug+w \{\}  \; \
    -exec chmod o+r \{\}  \;

sudo find clickhouse/ -iname '*admin-user.xml' -type f \
    -exec chown rootless-101:rootless-101 \{\} \; \
    -exec chmod ug+w \{\}  \; \
    -exec chmod o+r \{\}  \;
