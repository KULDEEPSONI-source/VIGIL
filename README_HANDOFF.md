# VIGIL Frontend Redesign Handoff

This package contains the redesigned frontend files for the VIGIL project.

## Replace these files/folders

Copy the `src/` contents into:
`VIGIL/frontend/src/`

The redesign keeps the existing frontend behavior/data flow and focuses on visual/UI changes.

## Important

Do NOT replace the backend or telemetry source files.

The existing:
- `src/data/`
- `src/hooks/`
- `src/types/`
- `src/config/`
remain the project's original functionality.

The files in this package are the UI files to replace:
- `App.tsx`
- `App.css`
- `index.css`
- `styles/tokens.css`
- `pages/Dashboard.tsx`
- `pages/Analytics.tsx`
- `pages/History.tsx`
- `pages/Profile.tsx`
- `pages/Settings.tsx`
- `components/monitor/CameraPanel.tsx`
- `components/monitor/DemoControls.tsx`

## After copying

From `VIGIL/frontend`:

npm run build

If the build succeeds:

git add src
git commit -m "Redesign VIGIL frontend UI"
git push origin main
