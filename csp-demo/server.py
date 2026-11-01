#!/usr/bin/env python3
# Serveur de demonstration CSP - Exercice 07 bonus (Audit XSS Code un max)
# Meme page XSS reflechie, avec ou sans Content-Security-Policy.
from http.server import HTTPServer, BaseHTTPRequestHandler

CSP = "script-src 'self'"

PAGE_INTERNE = b"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Demo CSP</title></head>
<body>
<h1>Module XSS reflechi (simulation de xss_r)</h1>
<p>Charge injectee dans la page, comme au niveau low :</p>
<pre>Hello <script>alert('Cookie de la victime : ' + document.cookie)</script></pre>
<p>Ouvre la console du navigateur (F12) pour voir le verdict.</p>
</body></html>"""

PAGE_EXTERNE = b"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Demo CSP - script externe</title></head>
<body>
<h1>Script heberge sur un domaine tiers, avec CSP</h1>
<p>Le navigateur doit refuser de charger ce script d'un autre domaine :</p>
<script src="http://10.40.0.10/script-fictif.js"></script>
<p>Ouvre la console (F12) : chargement bloque par la CSP.</p>
</body></html>"""

PAGE_INDEX = b"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Demo CSP</title></head>
<body>
<h1>Content-Security-Policy : demonstration</h1>
<p>Meme page, meme charge XSS. Seule difference : l'en-tete HTTP.</p>
<ul>
<li><a href="/sans-csp">1. SANS CSP : la charge s'execute (alerte)</a></li>
<li><a href="/avec-csp">2. AVEC CSP script-src 'self' : script inline BLOQUE</a></li>
<li><a href="/externe-csp">3. Script d'un domaine tiers + CSP : BLOQUE aussi</a></li>
</ul>
</body></html>"""

class Demo(BaseHTTPRequestHandler):
    def do_GET(self):
        page, extra = PAGE_INDEX, []
        if self.path.startswith("/sans-csp"):
            page = PAGE_INTERNE
        elif self.path.startswith("/avec-csp"):
            page = PAGE_INTERNE
            extra = [("Content-Security-Policy", CSP)]
        elif self.path.startswith("/externe-csp"):
            page = PAGE_EXTERNE
            extra = [("Content-Security-Policy", CSP)]
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        for k, v in extra:
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(page)

HTTPServer(("0.0.0.0", 8080), Demo).serve_forever()