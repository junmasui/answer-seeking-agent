
#
# Wait for DNS /etc/resolv.conf to be correctly populated by Docker
#
while true
do
    grep -qE "nameserver[ \t]+127\.0\.0\.11" /etc/resolv.conf
    if [ $? -eq 0 ]
    then
        echo "/etc/resolv.conf is populated"
        break
    fi
    sleep 2
done

#
# Wait for DNS resolution of fastapi-dev-server and vite-dev-server
#
for LOOKUP in fastapi-dev-server vite-dev-server
do
    while true
    do
        nslookup $LOOKUP
        if [ $? -eq 0 ]
        then
            break
        fi
        sleep 2
    done
done
