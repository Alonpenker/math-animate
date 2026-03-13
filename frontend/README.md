# MathAnimate — Frontend

React + TypeScript + Vite frontend for the MathAnimate application.

## Development modes

### Option 1 — Vite dev server (fastest iteration)

Requires the backend stack to already be running (`docker-compose up` in the repo root).

```bash
npm install
npm run dev
```

App available at **http://localhost:5174**. Vite's HMR gives instant feedback on component changes.

> The dev server does **not** proxy API calls automatically. The frontend is expected to talk to the backend at `http://localhost:8000` directly, or you can add a proxy to `vite.config.ts` if needed.

### Option 2 — Full stack via Docker Compose

Builds the React app and serves it with NGINX (proxies `/api/` to the backend container). Run from the repo root:

```bash
docker-compose -f docker-compose.yml -f docker-compose.frontend.yml up
```

App available at **http://localhost:80**. Use this to test the full request path (NGINX → API → worker).

After a frontend code change:

```bash
docker compose -f docker-compose.yml -f docker-compose.frontend.yml build frontend
```

## Tech stack

| | |
|---|---|
| Framework | React 18 + TypeScript |
| Build tool | Vite |
| Styling | Tailwind CSS |
| Served by (Docker) | NGINX (SPA fallback + `/api/` proxy) |

## Project structure

```
src/
├── components/   # Shared UI components
├── pages/        # Route-level page components
├── hooks/        # Custom React hooks
└── main.tsx      # App entry point
```
