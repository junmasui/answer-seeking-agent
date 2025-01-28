
nslookup fastapi-dev-server

until [ $? -eq 0 ]
do
    sleep 2
    nslookup fastapi-dev-server
done

nslookup vite-dev-server

until [ $? -eq 0 ]
do
    sleep 2
    nslookup vite-dev-server
done

