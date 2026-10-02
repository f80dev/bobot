# bobot

Assistant conversationnel Psybot (RAG + ReAct) pour le cabinet d'Emilie Pommier.

**Statut** : isolé du backend prod `emiliepommier.fr`. Ce projet est self-contained :
il ne dépend pas de `~/psy-site/server/`. Il sert de bac à sable pour itérer sur le
RAG (TF-IDF sur `knowledge/`) et la boucle d'agent ReAct (DeepSeek).

```
bobot/
├── bobot.py           # FastAPI app, boucle ReAct, system prompt, routes
├── llm.py            # Client DeepSeek (réel + mock)
├── rag.py            # RAG TF-IDF stdlib sur knowledge/
├── knowledge/        # Fiches .md indexées par le RAG (6 passages)
├── frontend/         # Angular 21 + Material UI (chat, history, admin)
├── tests/            # Pytest (mocks, contrat HTTP, anti-régression)
├── requirements.txt
├── .env.example
└── README.md
```

## Quick start

```bash
cd ~/bobot
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# édite .env pour mettre ta vraie DEEPSEEK_API_KEY

# Lancer le serveur en local
DEEPSEEK_API_KEY=sk-... python3 -m bobot          # http://127.0.0.1:8000
# ou avec autoreload
DEEPSEEK_API_KEY=sk-... uvicorn bobot:app --port 8000 --reload
```

## Endpoints

| Méthode | Path | Description |
|---|---|---|
| GET | `/api/health/psybot` | Health check (charge la KB, init le client LLM) |
| POST | `/api/psybot/chat` | Conversation. Body: `{message, session_id?, history?}` → `{answer, sources, emergency, trajectory}` |

Contrat identique à la prod (`unified_proxy.py` côté `~/psy-site`) : le front Angular
`/psybot` peut pointer ici pour des tests UI en local.

## Tests

```bash
cd ~/bobot
DEEPSEEK_MOCK=1 DEEPSEEK_API_KEY=test python3 -m pytest tests/ -v
```

Tests offline uniquement (sans clé DeepSeek) : mocks + contrat HTTP + anti-régression
sur les few-shots du `_DECISION_PROMPT`.

## Architecture

- **RAG** : `rag.py` indexe `knowledge/*.md` (6 passages par défaut), section-aware
  via les titres `## `, scoring TF-IDF stdlib.
- **Boucle agent** : `bobot.py:_run_agent()` fait un ReAct hand-rolled (pas de DSPy).
  3 actions possibles : `search_knowledge`, `detect_emergency`, `finish`.
  `max_iters=3` (env `PSYBOT_MAX_ITERS`).
- **LLM** : `llm.py` wrapper OpenAI SDK vers DeepSeek (`https://api.deepseek.com/v1`,
  modèle `deepseek-chat`). Mock client via `DEEPSEEK_MOCK=1`.
- **Urgence** : `_EMERGENCY_RE` (regex) court-circuite avant tout appel LLM.
  Message verbatim 3114/15/114.

## Variables d'env

Voir `.env.example`.

## Roadmap

- (a) Enrichir `knowledge/emdr.md` avec un paragraphe sur le déroulé d'une séance.
- (b) Migrer vers `dspy.ReAct` + `BootstrapFewShot` pour l'optimisation auto des few-shots.
- (c) Ajouter un eval set (10-30 questions EMDR/IR/attachement avec vérité terrain).

## Frontend Angular (frontend/)

Scaffold Angular 21 + Material 21. Standalone components, routing, sidenav
navigation, signal-based state.

### Quick start

```bash
cd ~/bobot/frontend
npm install                                    # one-time
npm start                                      # http://localhost:4200
```

Le frontend cible l'API bobot sur `http://localhost:8000` (CORS autorisé côté
backend — voir `bobot.py:_ALLOWED_ORIGINS`).

### Pages

| Route | Page | Description |
|---|---|---|
| `/chat` | `Chat` | Conversation signal-based, historique de session en mémoire, expansion panels pour la trajectoire ReAct, badges d'urgence. |
| `/history` | `History` | Placeholder — l'historique n'est pas persisté côté serveur. |
| `/admin` | `Admin` | Health check live : statut, mode mock/réel, max iters, chemin du KB. |

### Structure

```
frontend/src/app/
├── app.config.ts        # provideAnimationsAsync, provideHttpClient(withFetch()), zoneless
├── app.routes.ts        # lazy-loaded chat/history/admin
├── app.{ts,html,scss}   # Layout : mat-sidenav + mat-toolbar + nav-list
├── bot-api.service.ts   # HttpClient wrapper (POST /chat, GET /health)
├── bot-api.types.ts     # Interfaces TypeScript du contrat
└── pages/
    ├── chat/            # Signal-based chat UI (FormControl via ngModel + signal)
    ├── history/         # Stateless placeholder
    └── admin/           # Health check display
```

### Configuration

Pour overrider l'URL de l'API (par exemple pointer vers un bot déployé) :

```ts
// Dans un component ou un service, ajuste l'instance :
constructor() {
  inject(BotApiService).apiBase = 'https://bobot.example.com';
}
```