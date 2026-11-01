

# Analyse de ransomware simulé - Fiche d'indicateurs de compromission

> **Projet fil rouge :** Code un max - Audit de sécurité de la plateforme de cours

> **Exercice 04** - Chaîne d'infection d'un faux ransomware

> **Auteur :** Antonin Moisan - Master Cybersécurité

> **Date d'analyse :** 27/10/2026

> **Environnement :** lab `cyberlab-net` (10.40.0.0/16) - poste d'audit `attaquant` (10.40.0.20) - cible `dvwa-cible` (10.40.0.10)

---

## 1. Scénario et vecteur de compromission

**Scénario reconstitué :** un employé de « Code un max » ouvre une pièce jointe
piégée (vecteur de compromission n° 1 du chapitre) contenant un rançongiciel.
Le malware chiffre ses fichiers, dépose une note de rançon et tente de contacter
une infrastructure distante pour l'extorsion.

Important : aucun code malveillant réel n'a été manipulé.
L'échantillon `sample-ransom.txt` est un simple fichier texte qui **imite** les
traces laissées par un ransomware ; il n'est **pas exécutable** (droits
`rw-r--r--`, aucun bit d'exécution) et n'a jamais été rendu exécutable. Le trafic
de « commande et contrôle » est simulé par une requête HTTP vers la cible du lab
pendant une capture réseau.

## 2. Chaîne d'infection reconstituée (kill chain)

| # | Phase de la kill chain | Traduction dans le scénario simulé | Élément observé |
|---|---|---|---|
| 1 | **Reconnaissance** | L'attaquant repère la cible et ses failles (employé, poste de travail) | (pré-attaque, non simulée) |
| 2 | **Intrusion** | Pièce jointe piégée ouverte par l'employé (clic piégé) | échantillon `sample-ransom.txt` |
| 3 | **Installation** | Le malware s'implante et persiste sur le poste | (non simulée) |
| 4 | **Command & Control** | La machine compromise contacte l'infrastructure de l'attaquant | requête HTTP observée vers `http://10.40.0.10/` dans `capture-ransom.pcap` |
| 5 | **Actions** | Chiffrement des fichiers puis demande de rançon | extension `.codemaxlocked`, note de rançon, contact `pay@codemax-ransom.example` |

## 3. Indicateurs de compromission (IoC)

Analyse statique de l'échantillon (`sha256sum`, `grep`) puis analyse de trafic
(`tshark`). Indicateurs relevés, exploitables par une équipe de réponse :

| Indicateur | Type | Valeur |
|---|---|---|
| **Empreinte SHA-256** de `sample-ransom.txt | Fichier (signature) | `3791e0f8569903aa5b345c1df100cd4047710b6aca8fd404aea80ee5dcee010a` |
| **Extension chiffrée simulée** | Comportement (système de fichiers) | `.codemaxlocked` |
| **Note de rançon** | Comportement (extorsion) | « Vos fichiers ont été chiffrés. Payez pour récupérer la clé. » |
| **Adresse de contact** | Infrastructure (extorsion / C2) | `pay@codemax-ransom.example` |
| **URL observée dans la capture** | Réseau (C2 simulé) | `http://10.40.0.10/` (code HTTP 302) |
| **Preuve de capture** | Réseau | `capture-ransom.pcap` — filtre d'affichage `ip.dst == 10.40.0.10 && http.request` |

**Méthode de relevé (reproductible) :**

```bash
docker exec attaquant sha256sum /data/sample-ransom.txt
docker exec attaquant grep -E "ext|note|contact" /data/sample-ransom.txt
docker exec -d attaquant tshark -i eth0 -f 'host 10.40.0.10' -a duration:15 -w /data/capture-ransom.pcap
docker exec attaquant curl -s -o /dev/null -w "%{http_code}\n" http://10.40.0.10/
docker exec attaquant tshark -r /data/capture-ransom.pcap -Y "ip.dst == 10.40.0.10 && http.request" -T fields -e http.request.full_uri
```

Ces IoC sont partageables : une équipe SOC peut les rechercher ailleurs
(empreinte dans les bases de signatures, adresse et URL dans les journaux de
passerelle, extension dans les inventaires de fichiers).

## 4. Recommandations

### 4.1 Prévention - avant l'incident

1. **Sauvegardes isolées, hors ligne et testées** (règle 3-2-1 : 3 copies, 2
   supports, 1 hors ligne) : c'est la seule contre-mesure qui rend la rançon
   inopérante. Restaurations testées régulièrement.
2. **Filtrage des pièces jointes et des liens** : passerelle de messagerie
   (sandboxing des pièces jointes, blocage des extensions dangereuses),
   filtrage web des URL de contact connues.
3. **Correctifs à jour** : dans le lab lui-même, Apache 2.4.25 est une version
   obsolète — un système non corrigé est une porte d'entrée (vecteur « faille
   non corrigée exploitée à distance »).
4. **Antivirus / EDR** avec signatures et bases d'IoC à jour, couplé à une
   supervision (SOC) pour détecter les comportements typiques (modifications
   massives de fichiers, trafic périodique sortant).
5. **Sensibilisation des utilisateurs** : le clic piégé reste le vecteur
   dominant ; moindre privilège et MFA limitent la portée d'une compromission.

### 4.2 Réponse - pendant et après l'incident

1. **Identifier** l'incident et son périmètre (quels postes, quels partages).
2. **Isoler** les machines infectées du réseau (débrancher le réseau, couper
   les partages) pour stopper le chiffrement et la propagation.
3. **Bloquer l'adresse de contact** `pay@codemax-ransom.example` au filtrage
   DNS/messagerie et l'URL/l'IP observée au pare-feu, pour couper le canal
   d'extorsion et de commande.
4. **Éradiquer** le malware, puis **restaurer** depuis les sauvegardes saines
   (hors ligne) après nettoyage complet.
5. **Ne pas payer** : payer ne garantit jamais la restitution et finance la
   filière ; préférer la restauration.
6. **Préserver les preuves** (échantillon, `capture-ransom.pcap`, journaux)
   pour l'analyse post-incident par le Forensic Expert et d'éventuelles suites
   judiciaires ; déclaration aux autorités (et à la CNIL si données
   personnelles touchées).
7. **Retour d'expérience** : mettre à jour les IoC dans les outils de
   détection, réviser les filtres, alimenter le registre `cves.csv`.

## 5. Bonus - Familles de malware : vecteur typique et IoC représentatif

| Famille | Définition (cours, ch. 5) | Vecteur de compromission typique | IoC représentatif |
|---|---|---|---|
| **Virus** | S'attache à un fichier et se propage à l'exécution | Fichier infecté partagé (clé USB, pièce jointe) exécuté par l'utilisateur | Empreinte / signature de fichier connue (antivirus) |
| **Ver** | Se réplique seul sur le réseau, sans action humaine | Faille non corrigée exposée (SMB, RDP), puis propagation autonome | Pic de trafic réseau anormal, scans internes massifs |
| **Cheval de Troie** | Se cache dans un logiciel d'apparence saine | Téléchargement d'un logiciel modifié ou d'un crack | Connexion sortante inattendue vers un serveur distant |
| **Ransomware** | Chiffre les données et extorse une rançon (double extorsion : vol + chiffrement) | Email piégé, accès initial (RDP/VPN) puis mouvement latéral | Extension inconnue + note de rançon + modifications massives de fichiers |
| **Botnet** | Pilote des machines zombies via un serveur Command & Control | Machine compromise enrôlée (via un des vecteurs ci-dessus) | Trafic périodique (beacon) vers l'URL/IP du serveur C&C |

Lecture du tableau : tout malware est un **payload + un mode de propagation**, et
on le détecte soit par **signature connue**, soit par **IoC observable** (les
deux approches utilisées dans cette fiche).

## 6. Conclusion

La chaîne d'infection d'un ransomware a été reconstituée sans aucun risque :
vecteur simulé (pièce jointe), empreinte SHA-256 relevée et consignée, motifs
caractéristiques extraits par analyse statique, trafic de commande et contrôle
capturé et prouvé dans `capture-ransom.pcap`. La fiche d'IoC est directement
exploitable par une équipe de réponse (recherche de l'empreinte, blocage de
l'adresse et de l'URL, isolement).

**Livrables de l'exercice :** `analyse-ransomware.md` (cette fiche),
`sample-ransom.txt` (échantillon inoffensif), `capture-ransom.pcap` (preuve
réseau). Le constat est ajouté au registre du fil rouge (cves.csv):
`OBS-002;faux ransomware simulé;pedagogique;Analyste SOC;ferme`.
