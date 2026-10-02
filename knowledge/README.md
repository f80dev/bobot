# Base de connaissances du Psybot

Ce dossier contient le corpus indexé par le moteur de RAG TF-IDF du psybot (voir `server/rag.py`).

## Structure

Chaque fichier `.md` = un thème. Les sections délimitées par `## ` deviennent des passages unitaires indexés.

## Thèmes actuels

| Fichier | Sujet |
|---|---|
| `emdr.md` | Définition, principes, indications, limites de l'EMDR |
| `intelligence-relationnelle.md` | L'IR du Dr François Le Doze, engagement thérapeutique conscient |
| `theorie-polyvagale.md` | Système nerveux autonome selon S. Porges |
| `theorie-attachement.md` | Bowlby, Ainsworth, styles d'attachement |
| `blessure-psychique.md` | Types de trauma, dissociation, M. Salmona |
| `deontologie-limits.md` | Cadre déontologique, numéros d'urgence, périmètre |

## Ajouter une fiche

1. Créer un fichier `mon-sujet.md` dans ce dossier
2. Structurer avec des `## ` headings (un passage = une section)
3. Commit + redéploiement (le RAG rebuild à chaque boot du container)

## Règles éditoriales

- Ton factuel, vulgarisé, jamais prescriptif
- Sources nommées en fin de fiche
- Pas de conseil individuel, pas de diagnostic
- Longueur conseillée : 200-400 mots