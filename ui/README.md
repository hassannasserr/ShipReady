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
as `artifacts\phase8-corrected-business\<run-id>\report.json`.

Build a production bundle with:

```powershell
npm run build
```

## Recommended UI scenario

1. Start the corrected demo environment from the repository root:

   ```powershell
   docker compose -f .\docker\compose.yaml up --build -d
   ```

2. Generate a complete infrastructure report:

   ```powershell
   .\.venv\Scripts\shipready.exe run --engine infrastructure --config configs\demo-project.yaml --artifacts artifacts\ui-demo --database artifacts\ui-demo\shipready.db --compose-file docker\compose.yaml
   ```

3. Run the UI with `npm run dev`, click **Load report**, and select the printed
   `artifacts\ui-demo\<run-id>\report.json`.

4. Confirm the space-themed mission control screen shows:
   - `BASELINE`, `I-01`, `I-02`, and `I-03` as scenario signals.
   - Four summary cards for scanned signals, clear trajectory, flight risks, and
     telemetry needing attention.
   - Mission details including the run ID, configuration, commit, and cleanup.
   - Expandable evidence and reproduction details for each signal.

5. To see the flight-risk state, recreate the app with
   `$env:DEFECT_MODE="duplicate-payment"` and load a business report. B-01
   should appear as failed while the other configured business scenarios remain
   visible.
