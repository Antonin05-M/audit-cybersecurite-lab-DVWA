# Audit de sécurité — Plateforme « Code un max »

Projet de formation **Cybersécurité** : audit d'un clone vulnérable de la plateforme de cours (DVWA) monté en laboratoire Docker isolé.

> ⚠️ Usage pédagogique uniquement. Aucun système de production n'a été touché ; toutes les attaques ont été menées dans un lab isolé (`10.40.0.0/16`).

## Contenu

| Fichier | Rôle |
|---|---|
| `rapport-final.md` | **Rapport d'audit** : synthèses, constats priorisés, plan d'action |
| `rapport-audit.md` | **Dossier technique** : 16 sections, méthodologie et preuves par exercice |
| `cves.csv` | Registre des vulnérabilités (CVSS, priorité, responsable, statut) |
| `cvss-audit.txt` | Vecteurs CVSS v3.1 et justifications |
| `captures/` | Captures d'écran des démonstrations (les preuves) |
| `crack/` | Audit des mots de passe (exercice 05) |
| `csp-demo/server.py` | Démonstrateur CSP (exercice 07, bonus) |
| `charge.sh`, `slowloris.py` | Scripts de démonstration du déni de service applicatif |
| `capture-*.pcap` | Captures réseau (reconnaissance, C2, ransomware) |
| `analyse-ransomware.md` | Fiche d'IoC du ransomware simulé (exercice 04) |
| `courriel-suspect.txt`, `urls-suspectes.txt` | Support d'analyse du spear phishing (exercice 08) |
| `docker-compose.yml` | Le laboratoire complet |

## Reproduire le lab

```bash
docker compose up -d
docker exec attaquant ping -c 3 10.40.0.10   # cible joignable
# plateforme : http://127.0.0.1:8088 (admin / password, niveau « low »)
```

Deux conteneurs : `dvwa-cible` (10.40.0.10) et `attaquant` (10.40.0.20), sur le réseau dédié `cyberlab-net`. Le dossier courant est monté dans `/data` du conteneur attaquant.

## Reproduire l'audit

Chaque démonstration (reconnaissance, SQLi, XSS, phishing, MITM, DoS, mots de passe) est décrite pas à pas — commande exacte + sortie — dans `rapport-audit.md`, avec ses captures dans `captures/`. Les scores et priorités sont dans `cves.csv` et `cvss-audit.txt`.

---
*Antonin Moisan — Master Cybersécurité, formation « Code un max ».*