# ShipReady UI

The React dashboard displays real `report.json` files produced by ShipReady.
It intentionally uses a local file picker instead of a backend API so it
cannot invent or silently alter assessment results.

From this directory:

```powershell
npm install
npm run dev
```

Open the Vite URL, usually `http://localhost:5173`, then choose a report such
as `artifacts\phase3-final\<run-id>\report.json`.

Build a production bundle with:

```powershell
npm run build
```
