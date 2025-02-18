
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

sudo find frontend/ -type d -exec chmod ug+sw \{\}  \; -exec chown rootless-1000:rootless-1000 \{\} \;
sudo find frontend/ -type d -exec chmod ug+s \{\}  \; -exec chown rootless-1000:rootless-1000 \{\} \;

sudo find backend/ -type d -exec chmod ug+sw \{\}  \; -exec chown rootless-1000:rootless-1000 \{\} \;
sudo find backend/ -type f -exec chmod ug+w \{\}  \; -exec chown rootless-1000:rootless-1000 \{\} \;

sudo find clickhouse/ -iname '*.xml' -type f -exec chmod ug+w \{\}  \; -exec chown rootless-101:rootless-101 \{\} \;

sudo find postgres/ -iname '*.sql.template' -type f -exec chmod ug+w \{\}  \; -exec chown rootless-999:rootless-999 \{\} \;
sudo find postgres/ -iname '*.sh' -type f -exec chmod ug+w \{\}  \; -exec chown rootless-999:rootless-999 \{\} \;

sudo find redis/ -iname '*.conf' -type f -exec chmod ug+w \{\}  \; -exec chown rootless-999:rootless-999 \{\} \;
