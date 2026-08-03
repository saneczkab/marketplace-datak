# frontend

Shared datak frontend built with React, TypeScript, and Vite.

## Local development

```bash
npm install
npm run dev
```

The development server is available at `http://localhost:5173`.

## Checks

```bash
npm run lint
npm run build
```

## Docker

From the repository root:

```bash
docker compose up --build frontend
```

The application is available at `http://localhost:3000` by default. Set `FRONTEND_PORT` to use another host port.
