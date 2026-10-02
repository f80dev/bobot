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
| `emdr-neurobiologie-imagerie.md` | Boukezzi, Rousseau, Verger : IRMf, PET-FDG, substrats biologiques |
| `emdr-trauma-complexe-cptsd.md` | TSPT-c, dissociation, Lavandier 2023, Rolling 2024, Dellucci 2016 |
| `emdr-urgence-catastrophe.md` | Protocoles immédiats (R-TEP, URG-EMDR), attentat, urgences, COVID |
| `emdr-migrants-deplaces.md` | Chauliac 2025, Vignaud 2023, Zampieri 2023, EMDR-SP |
| `emdr-accouchement-postpartum.md` | ESPT du post-partum, Merg-Essadi 2025, Krings-George 2013 |
| `emdr-therapies-integrees-comparaison.md` | Brainspotting, MOSAIC, hypnose, intégrative |
| `emdr-enfants-adolescents.md` | Rolling 2024, Sorel 2022, Bozkurt, protocoles adaptés |
| `emdr-english-corpus.md` | Index des articles en langue anglaise (Frontiers, Healthcare, EJPT…) |

## Ajouter une fiche

1. Créer un fichier `mon-sujet.md` dans ce dossier
2. Structurer avec des `## ` headings (un passage = une section)
3. Commit + redéploiement (le RAG rebuild à chaque boot du container)

## Règles éditoriales

- Ton factuel, vulgarisé, jamais prescriptif
- Sources nommées en fin de fiche
- Pas de conseil individuel, pas de diagnostic
- Longueur conseillée : 200-400 mots