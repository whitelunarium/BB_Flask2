# Beasts_Flask

**NOT AN ACTIVE FORK.** This repo is kept around for reference and handoff context. Do not assume changes here ship anywhere automatically.

Backend API for the Poway Neighborhood Emergency Corps (PNEC) website. PNEC is a volunteer-run emergency preparedness group in Poway, California. The public site lives at https://pnec.opencodingsociety.com and serves residents with FAQs, event listings, live hazard data, a chatbot, and a coordinator/staff area for managing content.

This repo is the Flask side of a two-repo setup:

| Repo | What it is | Where it runs |
|---|---|---|
| `Beasts_Flask` (this repo) | Python Flask API. Everything dynamic lives here. | EC2 host behind nginx at `beasts.opencodingsociety.com` |
| `Beasts_FrontEnd` | Jekyll static site, layouts, theme files. | GitHub Pages |

The frontend calls this backend at `/api/*`. There is no other server-side code anywhere. If a page on the frontend hydrates data after load, it is talking to this Flask app.

## Quick start

You need Python 3.12. Anything 3.9+ probably works but the Docker image pins 3.12.

```
cd ~/Beasts_Flask
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

That starts the dev server on port 8425. Visit http://localhost:8425 for the human-readable status page or http://localhost:8425/api/health for the JSON health check.

First boot creates `instance/volumes/pnec.db` (SQLite), seeds 60+ neighborhoods, 8 FAQ categories with ~30 Q&A entries, and an admin user if `ADMIN_PASSWORD` is set.

There is also `scripts/setup.sh` that does the same thing plus initializes Flask-Migrate.

## Docker

```
docker compose up --build
```

Same port (8425), same code, but runs under gunicorn with 5 workers and 2 threads each. The `instance/` directory is mounted as a volume so the SQLite DB survives container rebuilds.

## Environment variables

The repo has a real `.env` with live credentials. It is gitignored. Do not commit it. The variables you need:

- `SECRET_KEY`: Flask session signing key. Required in prod.
- `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `ADMIN_DISPLAY_NAME`: seeded on first boot. Password must be 12+ characters or the seed is skipped on purpose.
- `DB_ENDPOINT`, `DB_USERNAME`, `DB_PASSWORD`: if all three are set, the app uses MySQL at `mysql+pymysql://{user}:{pass}@{host}:3306/pnec`. Otherwise it falls back to SQLite.
- `GROQ_API_KEY`, `GROQ_MODEL`: **primary AI provider.** Powers both the PNEC chatbot (route `/api/gemini`, despite the URL name) and the Live Theme Editor's prompt engineer. Default model is `llama-3.3-70b-versatile`. We use Groq as primary because its free tier handles many more requests per day than Gemini's free tier, which mattered once real resident traffic started hitting the chatbot.
- `GEMINI_API_KEY`, `GEMINI_MODEL`: **chatbot fallback only.** Used if Groq is unconfigured or errors out. Default model is `gemini-2.5-flash-lite`. Safe to leave unset if you do not need a fallback. Not used by the Live Theme Editor.
- `GITHUB_TOKEN`, `GITHUB_OWNER`, `GITHUB_REPO`, `GITHUB_BRANCH`: the Live Theme Editor commits Jekyll changes directly to the frontend repo using the GitHub REST API. Token needs `Contents: read+write` on `whitelunarium/Beasts_FrontEnd`.
- `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_EMAIL`: for web push notifications. Generate with `python3 scripts/generate_vapid_keys.py`.
- `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`: optional. If blank, mail is logged to stdout in dev.
- `REDIS_URL`: optional but recommended in prod so rate limits work across gunicorn workers.

## Layout

```
main.py                      entry point, also what gunicorn imports
run.py                       same thing, used by a few scripts
app/
  __init__.py                application factory, blueprint registration, CORS, seeding
  config.py                  all config in one file, reads from env
  models/                    SQLAlchemy models, one file per table
  routes/                    HTTP layer, thin, validates input and calls services
  services/                  business logic, returns (result, error_key) tuples
  utils/                     errors.py, auth_decorators.py, auth_helpers.py, security.py
  cms_sections/              CMS v2 section type registry, one folder per type
tests/                       pytest, in-memory SQLite, see conftest.py
scripts/                     setup, redeploy, db migrate, seed, VAPID key gen
instance/                    runtime data, mounted as a volume in Docker
Dockerfile                   Python 3.12 slim, gunicorn, non-root user
docker-compose.yml           single service on port 8425
nginx_for_flask_8425         the nginx config used on the EC2 host
```

## What is actually in the API

Everything is mounted under `/api`. Auth is at `/api/auth`. Admin is at `/api/admin` and `/api/admin/publish`. The interesting areas:

- **Auth** (`routes/auth.py`): session cookies via Flask-Login plus bearer tokens. Per-IP rate limiting on login and register, per-email lockout after 5 failures, every attempt logged to `security_events`.
- **FAQ** (`routes/faq.py`): categories, items, search, "helpful" votes, public question submission, staff workflow for claiming and answering.
- **Events** (`routes/events.py`): list and calendar view.
- **Neighborhoods** (`routes/neighborhoods.py`): 60+ Poway neighborhoods with coordinator contact info.
- **Risk** (`routes/risk.py`): live fire/flood/heat assessment for Poway. Fetches from Open-Meteo and AQI, caches 30 min, returns stale data if upstream fails. Accepts a `neighborhood_id` query param for zone-specific scoring.
- **Live** (`routes/live.py`): "right now" aggregator for the chatbot. Weather, AQI, NWS alerts, fire-weather composite, sun.
- **Media** (`routes/media.py`): paginated media posts, coordinator+ upload.
- **Volunteer** (`routes/volunteer.py`): interest form submission and admin management.
- **Chatbot proxy** (`routes/gemini.py`, endpoint `/api/gemini`): server-side proxy that calls Groq first (Llama-3.3-70B) and falls back to Gemini if Groq is unconfigured or errors out. The route file and URL are still named `gemini` for backwards compatibility with the deployed frontend, which hits `/api/gemini` from `assets/js/api/gemini.js` and three other places. Provider logic lives in `app/services/chat_service.py`.
- **CMS v2** (`routes/cms_v2.py`, `cms_theme.py`, `cms_ai.py`): the in-browser page editor. Section types are file-based in `app/cms_sections/`, each with an HTML template and a JSON schema.
- **Admin publish** (`routes/admin_publish.py`): commits Jekyll changes from the Live Theme Editor straight to `Beasts_FrontEnd` via the GitHub REST API. GitHub Pages rebuilds in about 5 min.
- **Security** (`routes/security.py`): exposes the `security_events` audit log to admins.
- **Push** (`routes/push.py`): web push subscriptions via VAPID.

The full route list is in `app/__init__.py` under `_register_blueprints`.

Code style follows SRP: routes parse the request and call a service, the service does the work and returns `(result, error_key)`. No SQL in routes, no Flask imports in services where avoidable.

## Roles

`resident` < `coordinator` < `staff` < `admin`. Decorate protected routes with `@requires_role('staff', 'admin')` from `app/utils/auth_decorators.py`. The admin role can also be unlocked from outside the session by sending the `X-PNEC-Admin-Key` header, which the admin editor UIs use.


## Deployment

The prod host is an EC2 instance running nginx in front of the Docker container on port 8425. The nginx config in `nginx_for_flask_8425` proxies traffic and sets the CORS allowlist (powaynec.com, opencodingsociety.com subdomains, and the two GitHub Pages org URLs).

After pushing to `main`, you have to redeploy manually. From the EC2 host:

```
cd ~/Beasts_Flask
./scripts/redeploy.sh
```

That does `git pull`, `docker-compose build`, `docker-compose up -d`, and an optional health check if `PNEC_ADMIN_KEY` is exported. Use `SKIP_PULL=1` or `SKIP_HEALTH=1` to short-circuit the obvious steps.

`scripts/cockpit-shell.py` is a WebSocket helper for kicking off redeploys remotely.

## Things that will trip you up

1. The `.env` file in the repo root is real and gitignored. If you wipe it you lose the Gemini, Groq, GitHub, and admin password values. Back it up before touching it.
2. CORS is hardcoded in `app/__init__.py`. If you stand up a new frontend origin you have to add it to the `CORS(...)` `origins` list and to `nginx_for_flask_8425`. Both. Missing one will look like the API is down.
3. The admin user only seeds if `ADMIN_PASSWORD` is at least 12 characters and not in the bad-sentinel list. If you boot a fresh instance and cannot log in as admin, check the Flask log for `_seed_admin_if_missing: refusing to seed`.
4. The risk service cache lives in process memory. With 5 gunicorn workers you get 5 separate caches and 5x the Open-Meteo traffic. Setting `REDIS_URL` does not fix this yet (it only affects rate limits). If Open-Meteo throttles us, the cache TTL in `RISK_CACHE_SECONDS` is the lever.
5. The CMS section registry is loaded once at boot from `app/cms_sections/`. Adding a new section type means dropping a folder with `<type>.html` and `<type>.schema.json` and restarting the server.
6. `instance/volumes/pnec.db` is the local SQLite file. The Docker compose file mounts `./instance` so the DB survives `docker compose down`, but `rm -rf instance/volumes` will wipe it. There is no automatic backup.
7. `_sync_legacy_sqlite_schema()` in `app/__init__.py` patches missing columns into older local SQLite files. New columns added to the `User` model also need to be listed there or local devs on stale schemas hit `OperationalError` on first request.
8. The Dockerfile chmods `/app/model` and `/app/api` read-only. Those directories do not actually exist in this repo (they are leftovers from an earlier layout). The chmod is a no-op but the build still works.

## Related repos

- **Beasts_FrontEnd** (`~/Beasts_FrontEnd`): Jekyll site, deployed via GitHub Pages. This is what the public sees. The frontend `hydrate.js` calls the Flask `/api/*` endpoints.
- **TM_Flask** (`~/TM_Flask`) and **TM_FrontEnd** (`~/TM_FrontEnd`): a sibling project built on the same Flask + Jekyll pattern but unrelated to PNEC. Same shape, different content.

## License

MIT. See `LICENSE`.
