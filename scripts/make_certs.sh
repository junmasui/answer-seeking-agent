
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout traefik/certs/traefik-local.key -out traefik/certs/traefik-local.crt \
  -subj "/CN=*.localhost"
