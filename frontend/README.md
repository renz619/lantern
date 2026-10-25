# Lantern frontend

Run it from this folder:

```
cd frontend
cp .env.example .env.local   # mock data on; edit and restart to use B's server
npm install
npm run dev
```

Open http://localhost:5173. With `VITE_USE_MOCKS=true` (the default in `.env.example`) the app uses fake data. Adding `?mock=1` to the address forces fake data too, which is the demo fallback if the server is down. Set `VITE_USE_MOCKS=false` and `VITE_API_URL` to use the real server. Restart `npm run dev` after editing `.env.local`.

---

# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
