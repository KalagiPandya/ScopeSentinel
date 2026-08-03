# ScopeSentinel — Deployment Guide (Day 17)

Two free-tier services: **Railway** for the backend + all databases,
**Vercel** for the frontend. Total cost: $0 to start (Railway gives a
free trial credit; both have generous free tiers for a portfolio project).

---

## Option A — Railway (Backend + Databases)

### 1. Push your code to GitHub first
```bash
git init
git add .
git commit -m "ScopeSentinel v2.0 - complete"
git remote add origin https://github.com/YOUR_USERNAME/ScopeSentinel.git
git push -u origin main
```

### 2. Create a Railway project
1. Go to https://railway.app -> New Project -> Deploy from GitHub repo
2. Select your ScopeSentinel repo
3. Railway detects `railway.json` and uses `backend/Dockerfile` automatically

### 3. Add database services (all available as Railway templates)
In your Railway project, click **+ New** and add:
- **PostgreSQL** (Railway plugin — gives you a `DATABASE_URL` automatically)
- **Redis** (Railway plugin)
- For **Qdrant** and **Neo4j**: use Railway's "Deploy from Docker Image":
  - Qdrant image: `qdrant/qdrant:latest`
  - Neo4j image: `neo4j:5.20` (set `NEO4J_AUTH=neo4j/yourpassword` env var)

### 4. Set environment variables
In the backend service's Variables tab, add all keys from your local `.env`:
```
DATABASE_URL          <- copy from Railway's Postgres plugin
REDIS_URL              <- copy from Railway's Redis plugin
QDRANT_HOST            <- your Qdrant service's internal hostname
QDRANT_PORT=6333
NEO4J_URI               <- bolt://<neo4j-service-hostname>:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD          <- whatever you set in NEO4J_AUTH
OPENAI_API_KEY          <- your real key
JWT_SECRET_KEY           <- generate a new random string for production
GITHUB_WEBHOOK_SECRET    <- your webhook secret
CORS_ORIGINS_RAW         <- https://your-app.vercel.app (set after Step 5)
APP_ENV=production
```

### 5. Run migrations + seed on Railway
Railway gives you a shell into the deployed container:
```bash
railway run alembic upgrade head
railway run python ../scripts/seed.py
railway run python ../scripts/setup_neo4j.py
railway run python ../scripts/embed_requirements.py
```
(Or run these once locally pointed at the Railway Postgres URL.)

### 6. Get your backend URL
Railway gives you a public URL like:
`https://scopesentinel-backend-production.up.railway.app`

Test it: visit `<that-url>/docs` — should show all 33 endpoints.

---

## Option B — Vercel (Frontend)

### 1. Set the production API URL
In `frontend/.env` (create if missing):
```
VITE_API_URL=https://scopesentinel-backend-production.up.railway.app
```

### 2. Deploy
```bash
cd frontend
npm install -g vercel
vercel login
vercel --prod
```
Or connect the GitHub repo directly at https://vercel.com/new and set:
- **Root Directory:** `frontend`
- **Build Command:** `npm run build`
- **Output Directory:** `dist`
- **Environment Variable:** `VITE_API_URL` = your Railway backend URL

### 3. Update backend CORS
Go back to Railway, update `CORS_ORIGINS_RAW` to include your Vercel URL:
```
CORS_ORIGINS_RAW=https://scopesentinel.vercel.app
```
Redeploy the backend (Railway auto-redeploys on env var change).

---

## Verify the Live Deployment

1. Open your Vercel URL
2. Log in with `pm@scopesentinel.com` / `password123`
3. Go to Upload Center, run the sample pipeline
4. Confirm Dashboard updates with real data

If login fails with a CORS error in the browser console, double-check
`CORS_ORIGINS_RAW` on Railway exactly matches your Vercel URL (no
trailing slash).

---

## GitHub Webhook for Live PR Reviews (Optional)

Once deployed, point your actual GitHub repo's webhook at:
```
https://scopesentinel-backend-production.up.railway.app/pr-review/webhook
```
Settings -> Webhooks -> Add webhook -> Content type `application/json`,
Secret = your `GITHUB_WEBHOOK_SECRET`, Events = "Pull requests".

---

## Local-Only Alternative (No Deployment Needed)

If you just need this for a placement demo and don't want to manage
cloud infra, running everything locally (as in the main README) and
recording a screen capture is completely acceptable — many recruiters
just want to see it work, not necessarily a live public URL.
