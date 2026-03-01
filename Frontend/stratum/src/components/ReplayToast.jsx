// components/ReplayToast.jsx
// Responsibility: Transient top-right toast notification for replay events.

export default function ReplayToast({ message }) {
  if (!message) return null;

  return (
    <div className="fixed top-4 right-4 z-50 border border-orange-700 bg-orange-950/80 text-orange-300 text-xs font-mono px-4 py-2.5 rounded backdrop-blur-sm shadow-lg">
      ↺ {message}
    </div>
  );
}
