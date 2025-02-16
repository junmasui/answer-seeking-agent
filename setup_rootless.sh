
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

grep rootless-1000: /etc/passwd
if [ $? -ne 0 ]
then
    exit 78
fi

grep rootless-1000: /etc/group
if [ $? -ne 0 ]
then
    exit 78
fi


sudo find frontend/ -type d -exec chmod ug+sw \{\}  \; -exec chown rootless-1000:rootless-1000 \{\} \;
sudo find frontend/ -type d -exec chmod ug+s \{\}  \; -exec chown rootless-1000:rootless-1000 \{\} \;

sudo find backend/ -type d -exec chmod ug+sw \{\}  \; -exec chown rootless-1000:rootless-1000 \{\} \;
sudo find backend/ -type f -exec chmod ug+w \{\}  \; -exec chown rootless-1000:rootless-1000 \{\} \;
