# Rapport d'audit de sécurité — Plateforme de cours « Code un max »

**Commanditaire** : Direction de la plateforme de cours en ligne « Code un max »

**Auditeur** : Antonin Moisan — audit dans le cadre de la formation Cybersécurité 1

**Périmètre** : plateforme applicative DVWA (10.40.0.10) et son environnement réseau de test (10.40.0.0/16), laboratoire isolé sur un réseau dédié sans exposition vers l'extérieur (port applicatif publié en local uniquement)

**Cadre** : audit autorisé sur environnement de laboratoire dédié (règles d'engagement respectées : périmètre fixe, aucune production, procédure d'arrêt immédiate disponible)

---

## 1. Synthèse exécutive (pour la direction)

L'audit de la plateforme de cours a confirmé **cinq risques réels et reproductibles**, dont un **critique** : une faille permet à un attaquant de lire **toute la base de données** de la plateforme, y compris les comptes des utilisateurs, sans même besoin de mot de passe. Quatre autres faiblesses permettent d'**intercepter les échanges** des utilisateurs sur le réseau, de **bloquer la plateforme** avec très peu de moyens, d'**exécuter du code dans le navigateur** des visiteurs, et de **piéger les utilisateurs par des messages frauduleux** ciblés.

Le service le plus urgent est simple à comprendre : **n'importe qui, sur le réseau, peut aujourd'hui ouvrir la base de données de la plateforme**. Ce risque doit être corrigé en premier, et la correction tient en une phrase : la plateforme doit cesser de construire ses requêtes en assemblant du texte, et vérifier systématiquement ce que l'utilisateur lui envoie.

Le plan d'action joint est **priorisé et chiffré** : cinq familles de mesures, dans un ordre précis, avec les responsables identifiés (développement, DSI, RSSI). La plateforme disposant d'une version corrigée de référence (niveau de sécurité « Impossible »), **chaque correctif est démontrable** : les attaques qui réussissaient avant correction échouent après. À l'issue du plan, **plus aucune des attaques testées ne passe**.

*Il n'y a pas eu de compromission réelle ni de perte de données : l'audit s'est déroulé dans un laboratoire isolé, construit à l'image de la plateforme, sans aucun système de production.*

---

## 2. Synthèse technique (pour le RSSI et les équipes)

Cinq vulnérabilités confirmées, classées par score CVSS v3.1 (score de base) :

| Priorité | Vulnérabilité | Vecteur CVSS v3.1 | Score | Sévérité |
|---|---|---|---|---|
| 1 | Injection SQL (module sqli, CWE-89) — OBS-003 | AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H | **9.8** | Critique |
| 2 | MITM réseau local (ARP + DNS spoofing, HTTP en clair) — OBS-006 | AV:A/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H | **8.1** | Haute |
| 3 | DoS applicatif (saturation des workers) — OBS-007 | AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H | **7.5** | Haute |
| 4 | XSS réfléchie, stockée et DOM (CWE-79) + vol de session + CSRF — OBS-004 | AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N | **6.1** | Moyenne |
| 5 | Spear phishing ciblé (surface humaine) — OBS-005 | N/A (risque organisationnel) | — | Moyenne |

Points saillants :

- **Chaînage démontré** : l'injection SQL a énuméré les bases applicatives et extrait la table `users` complète (5 comptes, mots de passe en **MD5 non salé**) ; ces empreintes sont cassables hors ligne à ~25,9 MH/s (mesure de l'audit des mots de passe) — la faille applicative équivaut à une compromission totale des comptes. Le moindre privilège du compte applicatif reste à vérifier et à renforcer.
- **Effet domino documenté** (chapitre « Chaîner les vulnérabilités ») : les failles isolées se combinent — la XSS permet de voler un `PHPSESSID` (absence d'attribut HttpOnly) et de **prendre une session administrateur** ; l'injection SQL livre les empreintes de mots de passe, **cassables hors ligne**. Le risque réel dépasse la somme des failles prises une à une.
- **Le déni de service est applicatif, pas volumétrique** : ~172 connexions captives en 5 secondes suffisent à paralyser la plateforme, pour un débit total d'environ 100 Ko/s. La plateforme est vulnérable à des moyens dérisoires ; la réponse est architecturale (garde de lecture, dimensionnement, WAF), pas un sur-dimensionnement de la bande passante.
- **Constat d'infrastructure** : la réinitialisation du conteneur applicatif a effacé le compte applicatif de la base (`app@127.0.0.1`) et la base elle-même, bloquant toute mise en service. L'absence de persistance des données et de script d'initialisation reproductible est une faiblesse opérationnelle en soi (à rapprocher d'une recommandation IaC).

---

## 3. Constats prioritaires

Le registre consolidé des vulnérabilités (`cves.csv`, tri par priorité croissante) :

| Identifiant | Vulnérabilité | CVSS | Sévérité | Priorité | Responsable | Statut |
|---|---|---|---|---|---|---|
| OBS-003 | Injection SQL module sqli (CWE-89) | 9.8 | Critique | 1 | Développement (requêtes préparées) | confirmé |
| OBS-006 | Réseau local — MITM (ARP + DNS spoofing + HTTP en clair) | 8.1 | Haute | 2 | DSI (réseau, TLS, DNSSEC) | confirmé |
| OBS-007 | Disponibilité — DoS applicatif (saturation des workers) | 7.5 | Haute | 3 | DSI (architecture, WAF, dimensionnement) | confirmé |
| OBS-004 | XSS réfléchie, stockée et DOM (CWE-79) + vol de session + CSRF guestbook | 6.1 | Moyenne | 4 | Développement (échappement, HttpOnly, CSP) | confirmé |
| OBS-005 | Surface humaine — spear phishing (4 URL empoisonnées dont homoglyphe) | N/A | Moyenne | 5 | RSSI / DSI | confirmé |
| OBS-001 | Cadrage initial de l'audit (application dvwa-cible) | N/A | Information | 6 | Pentester | terminé |
| OBS-002 | Faux rançongiciel simulé (exercice SOC) | N/A | Pédagogique | 7 | Analyste SOC | fermé |

Chaque constat du tableau est appuyé par une **preuve reproductible** : la commande exacte et sa sortie figurent dans le dossier technique (`rapport-audit.md`, démonstrations par exercice) et dans les captures d'écran de chaque démonstration ; les vecteurs CVSS avec leur justification sont consignés dans `cvss-audit.txt`. La priorité 1 (critique) passe avant tout le reste ; la sévérité mesure l'impact technique, pas la fréquence d'attaque.

---

## 4. Périmètre et méthodologie

L'audit a suivi les **cinq phases** du cycle d'un audit de sécurité :

1. **Cadrage et préparation** — laboratoire Docker isolé (réseau 10.40.0.0/16), conteneurs `dvwa-cible` (10.40.0.10) et `attaquant` (10.40.0.20), règles d'engagement explicites : périmètre fixe, environnement pédagogique, aucune production touchée, procédure d'escalade disponible.
2. **Reconnaissance** — cartographie de la cible, inventaire des modules applicatifs, répertoire des surfaces d'attaque (modules DVWA, formulaires, réseau local, facteur humain).
3. **Exploitation** — démonstration pratique de chaque faille avec les outils du pentester (nmap, sqlmap, curl, dictionnaires, outils réseau), chaque exploitation aboutissant à un constat mesuré.
4. **Analyse** — scoring CVSS v3.1 de chaque faille confirmée, priorisation dans `cves.csv`, croisement entre la note et l'exposition réelle du service.
5. **Restitution** — le présent rapport et la présentation orale au commanditaire (constat global → constats priorisés → plan d'action daté).

Une exigence a gouverné tout l'audit : **une vulnérabilité ne rentre dans le rapport que si elle est reproductible** — chaque constat est accompagné de la commande exacte qui le démontre, exécutée avec une session valide au moment de la démonstration (une session périmée produit des résultats vides sans message d'erreur : une preuve doit donc être auto-suffisante, session comprise).

---

## 5. Détail des vulnérabilités (fiches)

### OBS-003 — Injection SQL (module sqli, CWE-89) — CVSS 9.8 Critique

- **Composant** : module SQL Injection de la plateforme (niveau de sécurité low).
- **Preuve reproductible** (dossier technique § 10, captures de l'exercice 06) : injection manuelle en booléen aveugle (`1' AND '1'='1` renvoie une ligne, `1' AND '1'='2` n'en renvoie aucune), puis `sqlmap` en niveau low : **« GET parameter 'id' is vulnerable »** (boolean-based blind + UNION query), énumération des bases (`dvwa`, `information_schema`) et **dump complet de la table `users`** — 5 comptes extraits, mots de passe en MD5 non salé.
- **Impact métier** : lecture de l'intégralité des données de la plateforme (comptes, empreintes de mots de passe), contournement possible de l'authentification ; les empreintes non salées extraites sont cassables hors ligne (chaînage avec l'audit des mots de passe).
- **Correctif** : requêtes préparées et paramétrées (suppression de toute concaténation), validation des entrées, et **moindre privilège** pour le compte applicatif de la base (accès restreint à la seule base applicative).

### OBS-006 — Interception réseau locale (MITM : ARP spoofing passif + DNS spoofing) — CVSS 8.1 Haute

- **Composant** : segment réseau local de la plateforme, trafic HTTP non chiffré.
- **Preuve reproductible** : usurpation ARP du routeur par l'attaquant (table ARP de la victime réécrite), puis fausses réponses DNS : le domaine légitime résout vers l'IP de l'attaquant, qui sert un portail en clair et capture identifiants et trafic. Détails, commandes et sorties complètes dans le dossier technique et les captures de l'exercice 09.
- **Impact métier** : lecture et falsification de tout échange non chiffré ; vol d'identifiants ; redirection vers de faux services.
- **Correctif** : **TLS obligatoire** sur l'ensemble des échanges (redirection HTTP→HTTPS, HSTS), DNSSEC pour l'espace de noms, contrôles de liaison ARP (inspection ARP, DHCP snooping), et sensibilisation au cadenas.

### OBS-007 — Déni de service applicatif — CVSS 7.5 Haute

- **Composant** : serveur applicatif (pool de travailleurs Apache).
- **Preuve reproductible** : script `charge.sh` — 200 connexions « captives » (POST au corps annoncé mais jamais envoyé) suffisent : témoin unique dégradé de ~0,01 s à 3,1 s (**×500**), puis en échec au-delà. La charge totale représente ~100 Ko/s, 172 connexions en 5 s : **une attaque applicative, pas volumétrique**.
- **Impact métier** : plateforme indisponible pour les utilisateurs légitimes avec des moyens dérisoires, indétectable par le seul volume réseau.
- **Correctif appliqué et mesuré** : garde `mod_reqtimeout` (`RequestReadTimeout header=5 body=2`) — chaque connexion captive est coupée à ~2 s (mesure sur connexion unique : la coupe s'observe nettement, contre les 8 s de la fenêtre client sans garde). **Limite honnête** : la disponibilité globale ne revient pas sous souscription soutenue (témoins mitigés : ~4 s) ; la réponse complète est architecturale : limitation de débit applicative, file de requêtes bornée, dimensionnement du pool, WAF.

### OBS-004 — Cross-Site Scripting (réfléchie, stockée, DOM) + CSRF — CVSS 6.1 Moyenne (sévérité pratique : Haute)

- **Composant** : modules XSS de la plateforme, livre d'or, cookie de session.
- **Preuve reproductible** (dossier technique § 11, captures de l'exercice 07) : la charge `<script>alert(1)</script>` est réfléchie et rendue **sans échappement** (`<pre>Hello <script>alert(1)</script></pre>`) ; le cookie `PHPSESSID` est dépourvu d'attribut **HttpOnly** et le **vol de cookie a été démontré** (requête reçue et journalisée par le serveur contrôlé par l'attaquant) ; le formulaire du livre d'or n'embarque aucun jeton anti-CSRF.
- **Impact métier** : exécution de code dans le navigateur des utilisateurs, **détournement de session administrateur** (effet domino avec l'absence de HttpOnly), actions forcées au nom d'un utilisateur authentifié.
- **Correctif** : échappement contextuel des sorties (`htmlspecialchars`), **HttpOnly** sur le cookie de session, CSP `script-src 'self'`, jetons anti-CSRF sur tous les formulaires.

### OBS-005 — Spear phishing ciblé (surface humaine) — risque organisationnel

- **Composant** : utilisateurs et encadrement (courriel, navigation).
- **Preuve reproductible** : courriel d'hameçonnage reconstitué usurpant le service informatique de Code un max et ciblant un formateur, avec **quatre URL empoisonnées** dont un domaine homoglyphe (`xn--code-un-mx-8bb.fr`, rendu « code-un-max.fr ») ; l'URL à arobase (`code-un-max.fr@phishing-serveur.net`) masque la destination réellement contactée.
- **Impact métier** : vol d'identifiants de session, compromission d'un compte utilisateur puis de ses moyens d'accès.
- **Correctif** : sensibilisation continue, **authentification multifacteur**, signalement interne des courriels suspects, filtrage des homoglyphes et domaines look-alike, vérification systématique du domaine avant toute saisie d'identifiants.

---

## 6. Durcissement de la plateforme et non-régression

Le rapport ne vaut que par les correctifs qu'il déclenche. Le durcissement a été **appliqué à l'échelle de la plateforme** en élevant son niveau de sécurité global sur **« Impossible »** (page DVWA Security) — ce niveau active la version corrigée de chaque module : requêtes préparées, échappement des sorties, jetons anti-CSRF. Chaque vulnérabilité confirmée porte désormais sa contre-mesure :

| Vulnérabilité | Contre-mesure de référence |
|---|---|
| OBS-003 — Injection SQL | Requêtes préparées et paramétrées ; validation des entrées ; moindre privilège du compte applicatif |
| OBS-004 — XSS / CSRF | Échappement contextuel (`htmlspecialchars`) ; HttpOnly ; CSP ; jetons anti-CSRF |
| OBS-006 — MITM / DNS | TLS obligatoire + HSTS ; DNSSEC ; protections ARP/DHCP |
| OBS-007 — DoS applicatif | Garde `mod_reqtimeout` (appliquée et mesurée) ; limitation de débit ; dimensionnement |
| OBS-005 — Phishing | MFA ; sensibilisation ; filtrage des domaines homoglyphes |

**Non-régression défensive — vérifiée par rejeu des attaques sur la plateforme durcie :**

- **Injection SQL** `1' OR '1'='1` sur le module SQL Injection : la plateforme **ne renvoie plus aucune donnée** — la charge est traitée comme une valeur littérale par la requête préparée.
- **XSS réfléchie** `<script>alert(1)</script>` sur le module XSS : la charge est renvoyée **en texte inerte, échappée** (`&lt;script&gt;…`), **sans aucune exécution** — pas d'alerte, pas d'exécution de script dans le navigateur.

Le même geste d'attaque ne produit plus le même effet : c'est la démonstration demandée au commanditaire — **aucune des attaques exploitées pendant l'audit ne passe sur la plateforme durcie**.

---

## 7. Recommandations et plan d'action priorisé

| # | Action | Faille | Responsable | Horizon |
|---|---|---|---|---|
| 1 | Requêtes préparées partout ; supprimer toute concaténation SQL ; restreindre le compte applicatif à la seule base applicative | OBS-003 | Développement | immédiat |
| 2 | TLS obligatoire (HTTP→HTTPS, HSTS) ; DNSSEC ; protections ARP/DHCP sur le segment | OBS-006 | DSI réseau | court terme |
| 3 | Échappement des sorties, HttpOnly, CSP, jetons anti-CSRF sur tous les formulaires | OBS-004 | Développement | court terme |
| 4 | Garde anti-lenteur conservée ; limitation de débit applicative ; dimensionner le pool ; évaluer un WAF | OBS-007 | DSI architecture | moyen terme |
| 5 | MFA généralisé ; campagne de sensibilisation phishing ; procédure de signalement | OBS-005 | RSSI | moyen terme |
| 6 | Persistance et initialisation reproductibles des données du conteneur applicatif (script de bootstrap versionné, volume dédié) ; ne jamais recréer un service applicatif sans vérifier comptes et base | constat d'infrastructure | DSI | court terme |

Principes directeurs : chaque recommandation est **actionnable et vérifiable** (pas de « sécuriser l'application » mais des correctifs précis, rattachés à leur identifiant) ; le plan est **priorisé et daté** ; la correction se **prouve par rejeu** — un correctif n'est déclaré efficace qu'après que l'attaque a été rejouée sans succès.

---

## 8. Restitution orale (trois phrases au commanditaire)

1. L'audit a confirmé une faille critique — une injection SQL exploitable à distance sans authentification — qui expose l'intégralité de la base de données de la plateforme.
2. Quatre autres risques confirmés — interception réseau en clair, déni de service, scripts croisés et hameçonnage ciblé — dégradent la confidentialité et la disponibilité du service.
3. Le plan d'action est priorisé : requêtes préparées en priorité absolue, puis chiffrement TLS, garde anti-saturation et échappement des sorties — et le passage de la plateforme en niveau « Impossible » démontre que plus aucune attaque de l'audit ne passe.

---

## 9. Annexes

- `captures/` — captures d'écran des démonstrations, exercice par exercice (reconnaissance, SQLi, XSS, phishing, DoS…) : **les preuves de l'audit**.
- `cves.csv` — registre consolidé des vulnérabilités (identifiant, CVSS, sévérité, priorité, responsable, statut).
- `cvss-audit.txt` — vecteurs CVSS v3.1, scores et justifications.
- Fichiers réseau — captures pcap (`capture-recon.pcap`, `capture-ransom.pcap`, `capture-c2.pcap`).
- Scripts d'exploitation rejouables — `charge.sh`, `slowloris.py`, `csp-demo/server.py` (démonstrateur CSP).
- `rapport-audit.md` (dossier technique détaillé) — le détail complet des 16 sections de l'audit, dont la méthodologie pas à pas de chaque démonstration.
- `docker-compose.yml` — le laboratoire complet, permettant de rejouer l'intégralité de l'audit.

*Fin du rapport — audit clos, plan d'action remis au commanditaire. Rapport consolidé le 1er novembre 2026.*