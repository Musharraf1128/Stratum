# Stratum — Frontend

> Multi-agent orchestration control plane dashboard.

## Stack
- React 18 (hooks only)
- Tailwind CSS (utility classes, no custom config needed)
- Plain SVG for the workflow graph (swap React Flow in later)

---

## Folder Structure

```
Frontend/
└── src/
    ├── Dashboard.jsx               ← Root orchestrator (state + composition only)
    ├── data/
    │   └── mockData.js             ← DEMO_WORKFLOW + RUNS (single source of truth)
    ├── utils/
    │   └── statusHelpers.js        ← statusColor / statusDot / statusBadge helpers
    └── components/
        ├── TopNav.jsx              ← Nav bar: logo, workflow label, live indicator
        ├── StatsBar.jsx            ← 6-metric aggregate stats strip
        ├── RunSidebar.jsx          ← Collapsible run list sidebar (hover/click to expand)
        ├── CenterPane.jsx          ← Tabbed container: Graph View | Diff View
        ├── WorkflowGraph.jsx       ← SVG graph: nodes, edges, status coloring
        ├── ExecutionStepList.jsx   ← Step-by-step table docked below the graph
        ├── StepDetailPanel.jsx     ← Right drawer: input / output / tokens / error
        ├── DiffView.jsx            ← Side-by-side run output comparison
        └── ReplayToast.jsx         ← Transient replay notification toast
```

## SRP map (one job per file)

| File | Single Responsibility |
|---|---|
| `Dashboard.jsx` | State ownership + component wiring |
| `TopNav.jsx` | Navigation chrome |
| `StatsBar.jsx` | Aggregate metrics display |
| `RunSidebar.jsx` | Collapsible run navigation rail |
| `WorkflowGraph.jsx` | SVG graph rendering |
| `ExecutionStepList.jsx` | Step table rendering |
| `StepDetailPanel.jsx` | Step detail drawer |
| `DiffView.jsx` | Run comparison UI |
| `ReplayToast.jsx` | Toast notification |
| `mockData.js` | Data layer |
| `statusHelpers.js` | Status → Tailwind class mapping |

---

## Quick Start

```bash
# In a new Vite + React project:
npm create vite@latest stratum -- --template react
cd stratum
npm install
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# Copy this src/ folder in, then:
npm run dev
```

In `tailwind.config.js` ensure content includes `./src/**/*.{js,jsx}`.

In `index.css` add:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

In `main.jsx`:
```jsx
import './index.css'
import Dashboard from './Dashboard'
ReactDOM.createRoot(document.getElementById('root')).render(<Dashboard />)
```

---

## Sidebar Behavior

The **RunSidebar** is collapsed by default to a `36px` icon rail showing:
- A vertical "RUNS" label
- One status dot per run
- A `>` expand hint

**Hover** over the rail → smooth CSS transition expands to `260px` full panel.  
**Mouse leave** → collapses back.  
The `×` button inside also collapses it manually.

This gives the graph maximum screen real estate by default.
