# Frontend — CLAUDE.md

React + TypeScript SPA for the **math-animate** project, built with Vite.

## Stack

- **Framework:** React 19, React Router 7
- **Language:** TypeScript 5.9
- **Build tool:** Vite 7
- **Styling:** Tailwind CSS 4, shadcn/ui (Base UI), `tw-animate-css`
- **Animation:** Framer Motion 12, GSAP 3, OGL (WebGL)
- **Icons:** Lucide React, React Icons
- **Fonts:** Geist (variable), Inter
- **Video:** React Player
- **Linting:** ESLint 9 + typescript-eslint
- **Testing:** Playwright

## Directory Layout

```
frontend/
├── src/
│   ├── main.tsx          # Entry point
│   ├── App.tsx           # Router setup
│   ├── index.css         # Global styles
│   ├── components/       # Shared/reusable components
│   │   ├── create/
│   │   ├── home/
│   │   ├── jobs/
│   │   ├── layout/
│   │   ├── lessons/
│   │   ├── ui/
│   │   └── usage/
│   ├── pages/            # Route-level page components
│   │   ├── AboutPage.tsx
│   │   ├── CreatePage.tsx
│   │   ├── HomePage.tsx
│   │   ├── JobsPage.tsx
│   │   ├── LessonsPage.tsx
│   │   └── UsagePage.tsx
│   ├── context/          # React context providers
│   ├── hooks/            # Custom hooks
│   ├── lib/              # Utility libraries / helpers
│   ├── services/         # API client / service layer
│   └── utils/            # Pure utility functions
├── public/               # Static assets
├── Dockerfile            # Production Docker image
├── nginx.conf            # Nginx config served inside Docker
├── index.html
├── vite.config.ts
└── tsconfig*.json
```

## Common Commands

```bash
# Install dependencies
npm install

# Dev server (hot reload)
npm run dev

# Type-check + production build
npm run build

# Preview production build locally
npm run preview

# Lint
npm run lint
```

## Docker

The `Dockerfile` builds a static bundle and serves it via Nginx. The `nginx.conf` handles SPA routing (all routes fall back to `index.html`).

```bash
docker build -t math-animate-frontend .
docker run -p 80:80 math-animate-frontend
```

## Conventions

- Components follow a feature-folder structure under `src/components/`.
- Page components in `src/pages/` are thin — logic lives in hooks/services.
- API calls go through `src/services/`; never call `fetch`/`axios` directly in components.
- Use `clsx` + `tailwind-merge` (via `lib/utils`) for conditional class names.
- Avoid adding raw `<style>` blocks; prefer Tailwind utility classes.
